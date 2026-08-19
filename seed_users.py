"""
seed_users.py — run ONCE after 01_schema.sql + 03_seed_data.sql.

03_seed_data.sql inserts users with password_hash = 'placeholder',
because valid bcrypt/werkzeug hashes can't be generated in T-SQL (they
need a random salt from Python). This script overwrites those
placeholders with real hashes, and seeds the two access_keys rows that
VerifyRole.html checks against.
"""
import bcrypt
from db import get_db_connection

DEFAULT_PASSWORD = "Admin123!"   # all seeded demo accounts share this — change after first login
ADMIN_KEY = "Egg-Admin-2026!"
USER_KEY = "Egg-User-2026!"


def hash_secret(plain):
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


conn = get_db_connection()
cur = conn.cursor()

pw_hash = hash_secret(DEFAULT_PASSWORD)
cur.execute("UPDATE users SET password_hash = ? WHERE password_hash = 'placeholder'", pw_hash)
print(f"Updated {cur.rowcount} seeded user(s) — default password: {DEFAULT_PASSWORD}")

for role, key in [("Admin", ADMIN_KEY), ("User", USER_KEY)]:
    cur.execute("INSERT INTO access_keys (role, key_hash) VALUES (?, ?)", role, hash_secret(key))

conn.commit()
conn.close()

print(f"Admin access key: {ADMIN_KEY}")
print(f"User access key:  {USER_KEY}")