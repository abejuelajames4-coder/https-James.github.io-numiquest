"""Approve a registered teacher after out-of-band identity verification."""
import os
import sys
import json
import urllib.request

from server import DB_PATH, db

if len(sys.argv) != 2:
    print("Usage: py -3 approve_teacher.py teacher@deped.gov.ph")
    raise SystemExit(2)

email = sys.argv[1].strip().lower()
allowed = {x.strip().lower() for x in os.environ.get("NUMIQUEST_TEACHER_EMAILS", "").split(",") if x.strip()}
if not email.endswith("@deped.gov.ph") or email not in allowed:
    print("Refusing approval: add this verified address to NUMIQUEST_TEACHER_EMAILS first.")
    raise SystemExit(1)

base_url = os.environ.get("NUMIQUEST_BASE_URL", "").rstrip("/")
token = os.environ.get("NUMIQUEST_ADMIN_APPROVAL_TOKEN", "")
if base_url:
    if not token:
        print("Set NUMIQUEST_ADMIN_APPROVAL_TOKEN before requesting remote approval.")
        raise SystemExit(1)
    req = urllib.request.Request(
        base_url + "/api/admin/approve-teacher",
        data=json.dumps({"email": email}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result=json.loads(response.read())
        print(result.get("message", "Teacher account approved."))
    except Exception as e:
        print("Approval failed:", e)
        raise SystemExit(1)
else:
    with db() as con:
        cur = con.execute("UPDATE users SET approved=1 WHERE email=? AND role='teacher'", (email,))
        if not cur.rowcount:
            print("No registered pending teacher account was found for that address.")
            raise SystemExit(1)
        print(f"Approved {email} in {DB_PATH}")

