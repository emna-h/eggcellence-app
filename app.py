"""
app.py — Eggcellence API, rewired to SQL Server (via db.py) with real
sessions and real access keys.
Run:  python app.py            (serves http://localhost:5000)
"""
import os
import uuid
from functools import wraps

import bcrypt
import pyodbc
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from db import get_db_connection, row_to_dict
from email_utils import send_signup_confirmation, send_password_change_confirmation

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-this-in-production")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# supports_credentials=True is required for the session cookie to work
# across origins if your frontend is served separately (e.g. Live Server
# on :5500). Add every origin you actually use here.
CORS(app, supports_credentials=True, origins=[
    "http://127.0.0.1:5500", "http://localhost:5500",
    "http://127.0.0.1:5000", "http://localhost:5000",
])


# ======================================================================
# Helpers
# ======================================================================
def hash_secret(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_secret(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False  # malformed/placeholder hash in DB — never crash on it


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not authenticated"}), 401
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "Admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper


# ======================================================================
# AUTH — Login.html, VerifyRole.html, ResetPassword.html
# ======================================================================

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    required = ["fullName", "email", "role", "departement", "password"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "Missing required fields"}), 400

    pw_hash = hash_secret(data["password"])
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO users (full_name, email, password_hash, role, department)
               OUTPUT INSERTED.user_id
               VALUES (?, ?, ?, ?, ?)""",
            data["fullName"], data["email"], pw_hash, data["role"], data["departement"],
        )
        new_id = cur.fetchone()[0]
        conn.commit()
    except pyodbc.IntegrityError:
        conn.close()
        return jsonify({"error": "An account with that email already exists"}), 409
    conn.close()

    send_signup_confirmation(data["email"], data["fullName"], data["role"], data["departement"])

    session["user_id"] = new_id
    session["role"] = data["role"]
    return jsonify({"user_id": new_id, "role": data["role"], "email": data["email"]}), 201


@app.route("/api/auth/verify", methods=["POST"])
@login_required
def verify_role():
    data = request.get_json()
    submitted_key = data.get("key", "")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT TOP 1 key_hash FROM access_keys WHERE role = ? ORDER BY created_at DESC",
        session["role"],
    )
    row = cur.fetchone()

    if not row or not check_secret(submitted_key, row[0]):
        conn.close()
        return jsonify({"error": "Invalid access key"}), 401

    cur.execute("UPDATE users SET is_verified = 1 WHERE user_id = ?", session["user_id"])
    conn.commit()
    conn.close()
    return jsonify({"verified": True}), 200


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT user_id, full_name, password_hash, role, job_title, department, status, is_verified
           FROM users WHERE email = ?""",
        email,
    )
    row = cur.fetchone()
    conn.close()

    if not row or not check_secret(password, row.password_hash):
        return jsonify({"error": "Invalid email or password"}), 401
    if row.status == "Deactivated":
        return jsonify({"error": "This account has been deactivated"}), 403

    session["user_id"] = row.user_id
    session["role"] = row.role
    return jsonify({
        "user_id": row.user_id, "full_name": row.full_name, "role": row.role,
        "job_title": row.job_title, "department": row.department,
        "is_verified": bool(row.is_verified),
    }), 200


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True}), 200


@app.route("/api/auth/me", methods=["GET"])
def whoami():
    def no_cache(resp):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return resp

    if "user_id" not in session:
        return no_cache(jsonify({"user": None})), 200
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT user_id, full_name, email, role, job_title, department, status, is_verified
           FROM users WHERE user_id = ?""",
        session["user_id"],
    )
    row = cur.fetchone()
    if not row or row.status == "Deactivated":
        conn.close()
        session.clear()
        return no_cache(jsonify({"user": None})), 200
    result = row_to_dict(cur, row)
    conn.close()
    return no_cache(jsonify({"user": result})), 200


@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email, new_password = data.get("email"), data.get("newPassword")
    if not email or not new_password:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password_hash = ? WHERE email = ?", hash_secret(new_password), email)
    updated = cur.rowcount
    conn.commit()
    conn.close()

    if updated == 0:
        return jsonify({"error": "No account found with that email"}), 404

    send_password_change_confirmation(email)
    return jsonify({"ok": True}), 200


# ======================================================================
# SUPPORT TICKETS — contact.html
# ======================================================================

@app.route("/api/support/tickets", methods=["POST"])
def create_ticket():
    form = request.form
    required = ["fullName", "email", "facility", "role", "category", "message"]
    if not all(form.get(f) for f in required):
        return jsonify({"error": "Missing required fields"}), 400

    attachment_path = None
    file = request.files.get("attachment")
    if file and file.filename:
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed (png, jpg, jpeg, pdf only)"}), 400
        safe_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], safe_name))
        attachment_path = f"/uploads/{safe_name}"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO support_tickets
           (full_name, email, department, role, category, priority, message, attachment_path)
           OUTPUT INSERTED.ticket_id
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        form["fullName"], form["email"], form["facility"], form["role"],
        form["category"], form.get("priority", "Low"), form["message"], attachment_path,
    )
    ticket_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({"ticket_id": ticket_id}), 201


@app.route("/uploads/<path:filename>")
@login_required
@admin_required
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/api/admin/support/tickets", methods=["GET"])
@login_required
@admin_required
def list_tickets():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM support_tickets ORDER BY created_at DESC")
    tickets = [row_to_dict(cur, r) for r in cur.fetchall()]
    conn.close()
    return jsonify(tickets), 200


@app.route("/api/admin/support/tickets/<int:ticket_id>", methods=["PATCH"])
@login_required
@admin_required
def update_ticket_status(ticket_id):
    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ("Open", "In Progress", "Resolved"):
        return jsonify({"error": "Invalid status"}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE support_tickets SET status = ? WHERE ticket_id = ?", new_status, ticket_id)
    updated = cur.rowcount
    conn.commit()
    conn.close()
    if updated == 0:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify({"ok": True}), 200


# ======================================================================
# INSPECTIONS — UserDashboard.html
# ======================================================================

@app.route("/api/inspections", methods=["POST"])
@login_required
def create_inspection():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO inspections
           (user_id, inspection_datetime, poids, hauteur, coloration, fraicheur, classement, charge_rupture)
           OUTPUT INSERTED.inspection_id
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        session["user_id"], data["datetime"], data["poids"], data["hauteur"],
        data["coloration"], data["fraicheur"], data["classement"], data["charge"],
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({"inspection_id": new_id}), 201


@app.route("/api/inspections/mine", methods=["GET"])
@login_required
def my_inspections():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM inspections WHERE user_id = ? ORDER BY inspection_datetime DESC",
        session["user_id"],
    )
    rows = [row_to_dict(cur, r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route("/api/inspections/<int:inspection_id>", methods=["PUT"])
@login_required
def update_inspection(inspection_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE inspections SET
             inspection_datetime = ?, poids = ?, hauteur = ?, coloration = ?,
             fraicheur = ?, classement = ?, charge_rupture = ?
           WHERE inspection_id = ? AND user_id = ?""",
        data["datetime"], data["poids"], data["hauteur"], data["coloration"],
        data["fraicheur"], data["classement"], data["charge"],
        inspection_id, session["user_id"],
    )
    updated = cur.rowcount
    conn.commit()
    conn.close()
    if updated == 0:
        return jsonify({"error": "Not found or not yours"}), 404
    return jsonify({"ok": True}), 200


@app.route("/api/inspections/<int:inspection_id>", methods=["DELETE"])
@login_required
def delete_inspection(inspection_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM inspections WHERE inspection_id = ? AND user_id = ?",
        inspection_id, session["user_id"],
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        return jsonify({"error": "Not found or not yours"}), 404
    return jsonify({"ok": True}), 200


# ======================================================================
# ADMIN — admin.html
# ======================================================================

@app.route("/api/admin/inspections", methods=["GET"])
@login_required
@admin_required
def admin_all_inspections():
    grade = request.args.get("grade")
    query = """SELECT i.*, u.full_name AS inspector_name
               FROM inspections i JOIN users u ON u.user_id = i.user_id WHERE 1=1"""
    params = []
    if grade and grade != "ALL":
        query += " AND i.classement = ?"
        params.append(grade)
    query += " ORDER BY i.inspection_datetime DESC"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, *params)
    rows = [row_to_dict(cur, r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route("/api/admin/inspections", methods=["POST"])
@login_required
@admin_required
def admin_create_inspection():
    """admin.html's Add Inspection modal lets the admin log a sample on
    behalf of ANY inspector, chosen from a dropdown — so unlike the
    User-facing route, user_id comes from the request body, not the
    admin's own session."""
    data = request.get_json()
    if not data.get("user_id"):
        return jsonify({"error": "user_id (inspector) is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO inspections
           (user_id, inspection_datetime, poids, hauteur, coloration, fraicheur, classement, charge_rupture)
           OUTPUT INSERTED.inspection_id
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        data["user_id"], data["datetime"], data["poids"], data["hauteur"],
        data["coloration"], data["fraicheur"], data["classement"], data["charge"],
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({"inspection_id": new_id}), 201


@app.route("/api/admin/inspections/<int:inspection_id>", methods=["PUT"])
@login_required
@admin_required
def admin_update_inspection(inspection_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE inspections SET
             user_id = ?, inspection_datetime = ?, poids = ?, hauteur = ?, coloration = ?,
             fraicheur = ?, classement = ?, charge_rupture = ?
           WHERE inspection_id = ?""",
        data["user_id"], data["datetime"], data["poids"], data["hauteur"], data["coloration"],
        data["fraicheur"], data["classement"], data["charge"], inspection_id,
    )
    updated = cur.rowcount
    conn.commit()
    conn.close()
    if updated == 0:
        return jsonify({"error": "Inspection not found"}), 404
    return jsonify({"ok": True}), 200


@app.route("/api/admin/inspections/<int:inspection_id>", methods=["DELETE"])
@login_required
@admin_required
def admin_delete_inspection(inspection_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM inspections WHERE inspection_id = ?", inspection_id)
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        return jsonify({"error": "Inspection not found"}), 404
    return jsonify({"ok": True}), 200


@app.route("/api/admin/kpis", methods=["GET"])
@login_required
@admin_required
def admin_kpis():
    """Backs kpiTotal, kpiPassRate, kpiRejectRate, kpiInspectors on admin.html."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN classement IN ('AA','A') THEN 1 ELSE 0 END) AS pass_count,
               SUM(CASE WHEN classement = 'C' THEN 1 ELSE 0 END) AS reject_count
        FROM inspections
    """)
    totals = row_to_dict(cur, cur.fetchone())

    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'User' AND status = 'Active'")
    active_inspectors = cur.fetchone()[0]

    cur.execute("SELECT classement, COUNT(*) AS count FROM inspections GROUP BY classement")
    grade_distribution = [row_to_dict(cur, r) for r in cur.fetchall()]
    conn.close()

    total = totals["total"] or 0
    pass_rate = round((totals["pass_count"] or 0) / total * 100, 1) if total else 0
    reject_rate = round((totals["reject_count"] or 0) / total * 100, 1) if total else 0

    return jsonify({
        "kpiTotal": total, "kpiPassRate": pass_rate, "kpiRejectRate": reject_rate,
        "kpiInspectors": active_inspectors, "grade_distribution": grade_distribution,
    }), 200


@app.route("/api/admin/users", methods=["GET"])
@login_required
@admin_required
def admin_list_users():
    """Samples count is computed via JOIN, not stored — avoids the
    'increment a counter column and hope it never drifts' bug pattern."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.user_id, u.full_name AS name, u.email, u.job_title AS role,
               u.department, u.status, COUNT(i.inspection_id) AS samples
        FROM users u
        LEFT JOIN inspections i ON i.user_id = u.user_id
        WHERE u.role = 'User'
        GROUP BY u.user_id, u.full_name, u.email, u.job_title, u.department, u.status
        ORDER BY u.full_name
    """)
    rows = [row_to_dict(cur, r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route("/api/admin/users", methods=["POST"])
@login_required
@admin_required
def admin_add_user():
    """Matches newInspectorName / newInspectorEmail / newInspectorRole
    from admin.html's Add Inspector modal. 'role' from that form maps
    to job_title here, NOT to the Admin/User auth role."""
    data = request.get_json()
    if not data.get("name") or not data.get("email") or not data.get("role"):
        return jsonify({"error": "Name, email, and role are required"}), 400

    temp_password_hash = hash_secret("Eggcellence#Temp1")  # inspector resets via ResetPassword.html

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO users (full_name, email, password_hash, role, job_title, department, is_verified)
               OUTPUT INSERTED.user_id
               VALUES (?, ?, ?, 'User', ?, ?, 1)""",
            data["name"], data["email"], temp_password_hash, data["role"], data.get("department", "D1"),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
    except pyodbc.IntegrityError:
        conn.close()
        return jsonify({"error": "An inspector with that email already exists"}), 409
    conn.close()
    return jsonify({"user_id": new_id}), 201


@app.route("/api/admin/users/<int:user_id>/status", methods=["PUT"])
@login_required
@admin_required
def admin_toggle_user_status(user_id):
    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ("Active", "Deactivated"):
        return jsonify({"error": "Invalid status"}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET status = ? WHERE user_id = ?", new_status, user_id)
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 200


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Backs the 'Delete' button in the Quality Inspector Management table.
    inspections.user_id has ON DELETE CASCADE, so that inspector's
    historical samples go with them — matches what the mock version did
    (it dropped the inspector from the array with no trace kept)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = ? AND role = 'User'", user_id)
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        return jsonify({"error": "Inspector not found"}), 404
    return jsonify({"ok": True}), 200


@app.route("/api/admin/settings", methods=["GET"])
@login_required
@admin_required
def get_settings():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT TOP 1 * FROM grading_settings ORDER BY updated_at DESC")
    row = cur.fetchone()
    result = row_to_dict(cur, row) if row else {}
    conn.close()
    return jsonify(result), 200


@app.route("/api/admin/settings", methods=["POST"])
@login_required
@admin_required
def update_settings():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO grading_settings (cutoff_aa, cutoff_a, cutoff_b, min_strength, updated_by)
           VALUES (?, ?, ?, ?, ?)""",
        data["cutoffAA"], data["cutoffA"], data["cutoffB"], data["minStrength"], session["user_id"],
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
