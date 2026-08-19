"""
email_utils.py — sends transactional emails (signup confirmation,
password-change confirmation) via SMTP.

Uses Python's built-in smtplib, no extra package needed beyond
python-dotenv (already in requirements.txt).

Failure handling: email sending NEVER blocks the actual action (signup,
password reset) 
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Eggcellence")


def send_email(to_email: str, subject: str, body_text: str) -> bool:
    """Returns True if the email was sent, False if it failed (logged,
    never raises — callers should not let this break the main request)."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[email_utils] SMTP not configured — skipped email to {to_email}: {subject}")
        return False

    msg = MIMEMultipart()
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[email_utils] Failed to send email to {to_email}: {e}")
        return False


def send_signup_confirmation(to_email: str, full_name: str, role: str, department: str):
    subject = "Eggcellence — Your account was created"
    body = f"""Hi {full_name},

An Eggcellence account was just created for this email address.

  Role:       {role}
  Department: {department}

If this was you, no action is needed — just complete the security key
verification step to finish activating your account.

If you did NOT create this account, please contact your system
administrator immediately, since someone else may have signed up
using your email address.

— Eggcellence Quality Systems
"""
    send_email(to_email, subject, body)


def send_password_change_confirmation(to_email: str):
    subject = "Eggcellence — Your password was changed"
    body = """Hi,

This is a confirmation that the password on your Eggcellence account
was just changed.

If you made this change, no action is needed.

If you did NOT change your password, your account may be compromised —
contact your system administrator immediately.

— Eggcellence Quality Systems
"""
    send_email(to_email, subject, body)
