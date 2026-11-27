import getpass
import hashlib
import json
import os
import secrets
from pathlib import Path


credentials_file = Path(
    os.environ.get(
        "TEACHER_CREDENTIALS_FILE",
        Path(__file__).parent / "teacher_credentials.json",
    )
)
iterations = 600_000

username = input("Teacher username: ").strip()
if not username:
    raise SystemExit("Username cannot be empty.")

password = getpass.getpass("Teacher password: ")
if not password:
    raise SystemExit("Password cannot be empty.")

try:
    credentials = json.loads(credentials_file.read_text(encoding="utf-8"))
except FileNotFoundError:
    credentials = {"teachers": []}

teachers = credentials.get("teachers") if isinstance(credentials, dict) else None
if not isinstance(teachers, list):
    raise SystemExit("Teacher credentials file has an invalid format.")
if any(teacher.get("username") == username for teacher in teachers if isinstance(teacher, dict)):
    raise SystemExit("That username already exists.")

salt = secrets.token_hex(16)
password_hash = hashlib.pbkdf2_hmac(
    "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
).hex()
teachers.append(
    {
        "username": username,
        "salt": salt,
        "password_hash": password_hash,
        "iterations": iterations,
    }
)

credentials_file.parent.mkdir(parents=True, exist_ok=True)
credentials_file.write_text(
    json.dumps({"teachers": teachers}, indent=2) + "\n",
    encoding="utf-8",
)
credentials_file.chmod(0o600)
print(f"Credentials saved to {credentials_file}")
