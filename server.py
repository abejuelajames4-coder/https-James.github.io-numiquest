"""NumiQuest local learning app backend (Python standard library only)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from http import cookies
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("NUMIQUEST_DB", ROOT / "numiquest.sqlite3"))
HOST = os.environ.get("NUMIQUEST_HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
PORT = int(os.environ.get("PORT", os.environ.get("NUMIQUEST_PORT", "8000")))
DEMO_ENABLED = os.environ.get("NUMIQUEST_DEMO", "0") == "1"
SESSION_SECONDS = 60 * 60 * 24 * 7
PASS_MARK = 70
UNLOCK_XP = [0, 100, 250, 450, 700, 1000]
LESSONS = [
    {"id": 1, "title": "Integers and Their Properties", "xp": 10,
     "objectives": ["Represent positive and negative quantities", "Use absolute value", "Apply integer operation rules"],
     "concept": "Integers are whole numbers, their opposites, and zero. The absolute value |a| is the distance of a from zero, so it is never negative. Addition of same-sign integers adds magnitudes and keeps the sign; different signs subtract magnitudes and keep the sign of the number with the larger magnitude. Multiplying or dividing same-sign integers gives a positive result; different signs give a negative result.",
     "formula": "|a| ≥ 0 · (−a)(−b)=ab · a(−b)=−ab",
     "example": "Compute −8 + 13 − 4. First, −8 + 13 = 5 because the signs differ and 13 has the greater magnitude. Then 5 − 4 = 1. Answer: 1."},
    {"id": 2, "title": "Rational Numbers and Their Properties", "xp": 10,
     "objectives": ["Identify rational numbers", "Simplify fractions", "Perform operations with rational numbers"],
     "concept": "A rational number can be written as p/q, where p and q are integers and q ≠ 0. Equivalent fractions name the same value. To add or subtract fractions, use a common denominator. To multiply, multiply numerators and denominators. To divide by a fraction, multiply by its reciprocal.",
     "formula": "a/b + c/d = (ad+bc)/bd · (a/b) ÷ (c/d) = ad/bc",
     "example": "Compute 2/3 + 1/4. A common denominator is 12, so 2/3 = 8/12 and 1/4 = 3/12. Add the numerators: 8/12 + 3/12 = 11/12."},
    {"id": 3, "title": "Percentages", "xp": 10,
     "objectives": ["Convert among fractions, decimals, and percents", "Find a percent of a quantity", "Solve percent change problems"],
     "concept": "Percent means per hundred. Convert a decimal to a percent by multiplying by 100; convert a percent to a decimal by dividing by 100. To find a percent of a number, write the percent as a decimal and multiply. Percent increase or decrease compares the change with the original amount.",
     "formula": "part = rate × whole · percent change = (change/original) × 100%",
     "example": "Find 15% of ₱800. Convert 15% to 0.15, then multiply: 0.15 × 800 = 120. So 15% of ₱800 is ₱120."},
    {"id": 4, "title": "Algebraic Expressions", "xp": 10,
     "objectives": ["Translate phrases into expressions", "Identify terms and coefficients", "Simplify by combining like terms"],
     "concept": "An algebraic expression combines variables, numbers, and operations. A term is separated by addition or subtraction. Like terms have the same variable part and exponents. Combine like terms by adding or subtracting their coefficients; unlike terms stay separate.",
     "formula": "ax + bx = (a+b)x",
     "example": "Simplify 3x + 5 − 2x + 7. Combine variable terms: 3x − 2x = x. Combine constants: 5 + 7 = 12. The result is x + 12."},
    {"id": 5, "title": "Linear Equations", "xp": 10,
     "objectives": ["Solve one-variable linear equations", "Use inverse operations", "Check solutions by substitution"],
     "concept": "A linear equation has a variable with exponent one. Keep an equation balanced by performing the same operation on both sides. Use inverse operations to isolate the variable, then substitute the result into the original equation to check it.",
     "formula": "ax + b = c → x = (c−b)/a, a ≠ 0",
     "example": "Solve 3x + 5 = 20. Subtract 5 from both sides: 3x = 15. Divide both sides by 3: x = 5. Check: 3(5)+5 = 20."},
    {"id": 6, "title": "Problem Solving", "xp": 10,
     "objectives": ["Represent word problems with equations", "Choose an appropriate strategy", "Check whether an answer is reasonable"],
     "concept": "Read a problem carefully, identify what is known and what is unknown, and define a variable for the unknown. Translate relationships into an equation, solve it, and interpret the result with units. Check the answer against the original situation.",
     "formula": "Understand → Plan → Solve → Check",
     "example": "A number plus 9 is 23. Let x be the number. Write x + 9 = 23. Subtract 9 from both sides to get x = 14. Check: 14 + 9 = 23."},
]

QUIZZES = [
    [("What is |−7|?", ["−7", "7", "0", "14"], 1, "Absolute value is distance from zero."), ("Which is greater?", ["−3", "−5", "Equal", "Neither"], 0, "−3 is closer to zero and therefore greater."), ("What is 6 × (−2)?", ["12", "−12", "−8", "8"], 1, "Different signs give a negative product."), ("Which is an integer?", ["2.5", "3/4", "−9", "√2"], 2, "−9 is a whole number with a negative sign."), ("What is −4 + 9?", ["−13", "−5", "5", "13"], 2, "Subtract magnitudes: 9−4=5, with the sign of 9."), ("What is 3²?", ["6", "9", "12", "32"], 1, "3² means 3×3."), ("What is −8−2?", ["−10", "−6", "6", "10"], 0, "Subtracting 2 moves two units left."), ("What is the additive identity?", ["1", "−1", "0", "10"], 2, "Adding zero leaves a number unchanged."), ("What is 15÷(−3)?", ["5", "−5", "−12", "12"], 1, "Different signs give a negative quotient."), ("Which is greatest?", ["−1", "−8", "−4", "−12"], 0, "Among negatives, the one closest to zero is greatest.")],
    [("Which is rational?", ["√2", "π", "−3/5", "√7"], 2, "A ratio of integers is rational."), ("Simplify 6/8.", ["2/3", "3/4", "4/6", "6/4"], 1, "Divide numerator and denominator by 2."), ("1/2 + 1/3 = ?", ["2/5", "5/6", "1/6", "1"], 1, "Use denominator 6: 3/6+2/6=5/6."), ("2/5 × 3/4 = ?", ["6/20", "5/9", "6/9", "1/2"], 0, "Multiply numerators and denominators; 6/20 simplifies to 3/10."), ("3/4 ÷ 1/2 = ?", ["3/8", "2/3", "3/2", "1/4"], 2, "Multiply by the reciprocal: 3/4×2/1=3/2."), ("Which equals 0.25?", ["1/2", "1/3", "1/4", "2/5"], 2, "One fourth is one quarter, or 0.25."), ("−2/3 + 1/3 = ?", ["−1", "−1/3", "1/3", "1"], 1, "Same denominator: (−2+1)/3=−1/3."), ("What is the reciprocal of 5/7?", ["5/7", "−7/5", "7/5", "1/5"], 2, "Swap numerator and denominator."), ("Which denominator is invalid?", ["1", "−2", "0", "9"], 2, "A rational number denominator cannot be zero."), ("2/3 as a decimal is…", ["0.23", "0.6 repeating", "0.67 exact", "1.5"], 1, "2 divided by 3 is 0.666… .")],
    [("25% as a decimal is…", ["2.5", "0.25", "0.025", "25"], 1, "Divide 25 by 100."), ("10% of 90 is…", ["9", "10", "80", "900"], 0, "0.10×90=9."), ("50% as a fraction is…", ["1/5", "1/4", "1/2", "2/3"], 2, "50/100 simplifies to 1/2."), ("20 is what percent of 80?", ["20%", "25%", "40%", "60%"], 1, "20/80×100%=25%."), ("₱200 increased by 10% is…", ["₱210", "₱220", "₱190", "₱180"], 1, "10% of 200 is 20; add it to 200."), ("0.8 as a percent is…", ["8%", "18%", "80%", "800%"], 2, "Multiply 0.8 by 100."), ("15% of 300 is…", ["15", "30", "45", "60"], 2, "0.15×300=45."), ("A ₱500 item is 20% off. Sale price?", ["₱100", "₱400", "₱480", "₱600"], 1, "Discount is ₱100; 500−100=400."), ("Increase from 40 to 50 is…", ["10%", "20%", "25%", "50%"], 2, "10/40×100%=25%."), ("3/5 as a percent is…", ["30%", "50%", "60%", "80%"], 2, "3÷5=0.6=60%.")],
    [("Simplify 3x+2x.", ["5x", "6x", "5x²", "x"], 0, "Add coefficients of like terms."), ("In 7y, the coefficient is…", ["y", "7", "0", "7y"], 1, "The number multiplying the variable is its coefficient."), ("Which are like terms?", ["2x and 2y", "3a and −a", "x and x²", "4 and 4b"], 1, "Both terms have variable a to the first power."), ("Simplify 4m+3−m.", ["3m+3", "5m", "3m−3", "4m+2"], 0, "4m−m=3m; keep the constant 3."), ("Translate: 5 more than n.", ["5n", "n−5", "n+5", "5−n"], 2, "More than means add."), ("Evaluate 2x+1 when x=3.", ["5", "7", "9", "12"], 1, "2(3)+1=7."), ("Simplify 6p−2p+4.", ["4p+4", "8p+4", "4p", "8p"], 0, "Combine the p terms: 6p−2p=4p."), ("How many terms in 3x+2y−8?", ["1", "2", "3", "4"], 2, "The terms are 3x, 2y, and −8."), ("The constant in 9a−6 is…", ["9", "a", "−6", "6a"], 2, "A constant has no variable."), ("Simplify 2(x+4).", ["2x+4", "2x+8", "x+8", "6x"], 1, "Distribute 2 to both terms.")],
    [("Solve x+7=12.", ["x=5", "x=19", "x=7", "x=84"], 0, "Subtract 7 from both sides."), ("Solve 3x=18.", ["x=6", "x=15", "x=21", "x=3"], 0, "Divide both sides by 3."), ("Solve 2x+4=10.", ["x=3", "x=7", "x=2", "x=14"], 0, "Subtract 4, then divide by 2."), ("Solve 5−x=2.", ["x=3", "x=7", "x=−3", "x=−7"], 0, "Subtract 5: −x=−3, so x=3."), ("Solve 4(x−1)=12.", ["x=2", "x=3", "x=4", "x=5"], 2, "Divide by 4: x−1=3; add 1."), ("Which operation undoes ×7?", ["Add 7", "Subtract 7", "Divide by 7", "Multiply by 7"], 2, "Division by 7 is the inverse."), ("Solve x/4=3.", ["x=7", "x=12", "x=1", "x=¾"], 1, "Multiply both sides by 4."), ("Check x=2 in 3x+1=7.", ["True", "False", "Cannot tell", "x=3"], 0, "3(2)+1=7."), ("Solve 2x−6=0.", ["x=−3", "x=0", "x=3", "x=6"], 2, "Add 6, then divide by 2."), ("Solve 7x+2=23.", ["x=3", "x=5", "x=21", "x=25"], 0, "Subtract 2 to get 21; divide by 7.")],
    [("A number plus 9 is 23. Number?", ["12", "14", "32", "207"], 1, "Subtract 9 from 23."), ("Twice a number is 18. Number?", ["8", "9", "16", "36"], 1, "18 divided by 2 is 9."), ("₱5 each for 4 items costs…", ["₱9", "₱15", "₱20", "₱25"], 2, "Multiply 5 by 4."), ("Perimeter of a square with side 6?", ["12", "24", "30", "36"], 1, "A square has four equal sides: 4×6."), ("A fare is ₱15 plus ₱8/km for 3 km.", ["₱24", "₱39", "₱45", "₱69"], 1, "15+8×3=39."), ("Three consecutive integers sum to 24. Middle?", ["6", "7", "8", "9"], 2, "They are 7, 8, 9; their sum is 24."), ("A 20% discount on ₱1000 is…", ["₱20", "₱100", "₱200", "₱800"], 2, "0.20×1000=200."), ("5 notebooks cost ₱150. One notebook?", ["₱25", "₱30", "₱35", "₱45"], 1, "Divide 150 by 5."), ("A number decreased by 4 is 10.", ["6", "14", "−6", "40"], 1, "Add 4 to both sides."), ("12 is 30% of what number?", ["36", "40", "42", "60"], 1, "12÷0.30=40.")],
]

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240000)
    return base64.b64encode(salt + digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        raw = base64.b64decode(stored)
        return hmac.compare_digest(raw[16:], hashlib.pbkdf2_hmac("sha256", password.encode(), raw[:16], 240000))
    except Exception:
        return False

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE, role TEXT NOT NULL CHECK(role IN ('student','teacher')), password_hash TEXT NOT NULL, grade TEXT NOT NULL DEFAULT '', section TEXT NOT NULL DEFAULT '', approved INTEGER NOT NULL DEFAULT 1, avatar TEXT NOT NULL DEFAULT '', language TEXT NOT NULL DEFAULT 'English', theme TEXT NOT NULL DEFAULT 'Light', created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS lesson_progress(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, lesson_id INTEGER NOT NULL, completed_at INTEGER, PRIMARY KEY(user_id,lesson_id));
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, lesson_id INTEGER NOT NULL, answers TEXT NOT NULL, correct INTEGER NOT NULL, total INTEGER NOT NULL, score INTEGER NOT NULL, passed INTEGER NOT NULL, submitted_at INTEGER NOT NULL, UNIQUE(user_id,lesson_id));
        CREATE TABLE IF NOT EXISTS xp_ledger(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, delta INTEGER NOT NULL, reason TEXT NOT NULL, ref TEXT UNIQUE, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS garden(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, plot INTEGER NOT NULL, plant TEXT NOT NULL DEFAULT '', stage INTEGER NOT NULL DEFAULT 0, fruit_claimed INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id,plot));
        CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, event TEXT NOT NULL, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS game_rewards(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, game_id INTEGER NOT NULL, day TEXT NOT NULL, PRIMARY KEY(user_id,game_id,day));
        """)
        if DEMO_ENABLED:
            email = "teacher.demo@numiquest.test"
            row = c.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if not row:
                c.execute("INSERT INTO users(name,email,role,password_hash,approved,created_at) VALUES(?,?,?,?,1,?)", ("Ms. Cruz (Demo)", email, "teacher", hash_password("NumiQuestDemo2026!"), int(time.time())))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def _json(self, status, payload, headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(body)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
        super().end_headers()

    def _body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000: raise ValueError("Request is too large.")
        return json.loads(self.rfile.read(length) or b"{}")

    def _session(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        raw = jar.get("nq_session")
        if not raw: return None
        digest = hashlib.sha256(raw.value.encode()).hexdigest()
        with db() as c:
            row = c.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>? AND u.approved=1", (digest, int(time.time()))).fetchone()
        return dict(row) if row else None

    def _require(self, role=None):
        user = self._session()
        if not user: self._json(401, {"error":"Please sign in again."}); return None
        if role and user["role"] != role: self._json(403, {"error":"You do not have permission to view this page."}); return None
        return user

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            try: self.api_get(path)
            except Exception as e: self._json(500, {"error":"The request could not be completed."}); print("API error:", repr(e))
            return
        if path.lower().endswith((".sqlite3", ".sqlite", ".db", ".sqlite3-wal", ".sqlite3-shm", ".sqlite3-journal", ".db-wal", ".db-shm", ".db-journal")) or path == "/__pycache__":
            self.send_error(404); return
        if path == "/": self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        try: body = self._body()
        except Exception as e: self._json(400, {"error":str(e)}); return
        try: self.api_post(urlparse(self.path).path, body)
        except Exception as e: self._json(500, {"error":"The request could not be completed."}); print("API error:", repr(e))

    def api_get(self, path):
        if path == "/api/health":
            self._json(200,{"status":"ok"});return
        if path == "/api/session":
            u=self._session(); self._json(200,{"user":public_user(u) if u else None,"demo_enabled":DEMO_ENABLED,"volatile_data":os.environ.get("NUMIQUEST_VOLATILE_DATA")=="1"}); return
        user=self._require()
        if not user:return
        if path == "/api/lessons":
            with db() as c:
                xp=total_xp(c,user["id"]); completed={r[0]:r[1] for r in c.execute("SELECT lesson_id,completed_at FROM lesson_progress WHERE user_id=?",(user["id"],))}; attempts={r[0]:dict(r) for r in c.execute("SELECT lesson_id,score,passed,submitted_at,answers,correct,total FROM attempts WHERE user_id=?",(user["id"],))}
            res=[]
            for l in LESSONS:
                a=attempts.get(l["id"]); done=l["id"] in completed; unlocked=xp>=UNLOCK_XP[l["id"]-1]
                attempt=None
                if a:
                    attempt={k:v for k,v in a.items() if k!="answers"}
                    attempt["answers"]=json.loads(a["answers"])
                    attempt["key"]=[q[2] for q in QUIZZES[l["id"]-1]]
                    attempt["explanations"]=[q[3] for q in QUIZZES[l["id"]-1]]
                res.append({**l,"completed":done,"completed_at":completed.get(l["id"]),"unlocked":unlocked,"attempt":attempt,"attempted":bool(a)})
            self._json(200,{"lessons":res,"xp":xp,"thresholds":UNLOCK_XP}); return
        m=re.fullmatch(r"/api/lessons/(\d+)/quiz",path)
        if m:
            if user["role"]!="student":self._json(403,{"error":"Student access required."});return
            lid=int(m.group(1))
            if not 1<=lid<=len(LESSONS):self._json(404,{"error":"Lesson not found."});return
            with db() as c:
                xp=total_xp(c,user["id"]);done=c.execute("SELECT 1 FROM lesson_progress WHERE user_id=? AND lesson_id=?",(user["id"],lid)).fetchone();attempted=c.execute("SELECT 1 FROM attempts WHERE user_id=? AND lesson_id=?",(user["id"],lid)).fetchone()
            if not done:self._json(403,{"error":"Complete the lesson before taking its quiz."});return
            if xp<UNLOCK_XP[lid-1]:self._json(403,{"error":"This lesson is still locked."});return
            if attempted:self._json(409,{"error":"This quiz has already been submitted."});return
            self._json(200,{"lesson_id":lid,"questions":[{"text":q[0],"options":q[1]} for q in QUIZZES[lid-1]]});return
        m=re.fullmatch(r"/api/lessons/(\d+)/quiz-review",path)
        if m:
            if user["role"]!="student":self._json(403,{"error":"Student access required."});return
            lid=int(m.group(1))
            with db() as c: attempt=c.execute("SELECT answers,correct,total,score,passed,submitted_at FROM attempts WHERE user_id=? AND lesson_id=?",(user["id"],lid)).fetchone()
            if not attempt:self._json(404,{"error":"No submitted quiz was found."});return
            self._json(200,{"lesson_id":lid,"questions":[{"text":q[0],"options":q[1]} for q in QUIZZES[lid-1]],"attempt":{**dict(attempt),"answers":json.loads(attempt["answers"]),"key":[q[2] for q in QUIZZES[lid-1]],"explanations":[q[3] for q in QUIZZES[lid-1]]}});return
        if path == "/api/profile":
            with db() as c: row=c.execute("SELECT * FROM users WHERE id=?",(user["id"],)).fetchone(); attempts=c.execute("SELECT score,passed,submitted_at,lesson_id FROM attempts WHERE user_id=? ORDER BY submitted_at",(user["id"],)).fetchall(); completed=c.execute("SELECT lesson_id FROM lesson_progress WHERE user_id=?",(user["id"],)).fetchall(); xp=total_xp(c,user["id"])
            self._json(200,{"user":public_user(dict(row)),"attempts":[dict(x) for x in attempts],"completed":[x[0] for x in completed],"xp":xp}); return
        if path == "/api/garden":
            with db() as c:
                plots={r["plot"]:dict(r) for r in c.execute("SELECT * FROM garden WHERE user_id=?",(user["id"],))}; xp=total_xp(c,user["id"])
            names=["Mango","Rambutan","Lanzones"]
            self._json(200,{"xp":xp,"plots":[plots.get(i,{"plot":i,"plant":"","stage":0,"fruit_claimed":0}) for i in range(3)],"names":names});return
        if path == "/api/teacher/students":
            if user["role"]!="teacher":self._json(403,{"error":"Teacher access required."});return
            with db() as c:
                students=c.execute("SELECT u.id,u.name,u.email,u.grade,u.section,u.avatar,u.created_at,COALESCE((SELECT SUM(delta) FROM xp_ledger WHERE user_id=u.id),0) xp,(SELECT COUNT(*) FROM lesson_progress WHERE user_id=u.id) completed,(SELECT COUNT(*) FROM attempts WHERE user_id=u.id) quizzes,(SELECT AVG(score) FROM attempts WHERE user_id=u.id) avg_score,(SELECT MAX(created_at) FROM activity WHERE user_id=u.id AND event='login') last_active,(SELECT COUNT(*) FROM activity WHERE user_id=u.id AND event='login') login_events FROM users u WHERE role='student' ORDER BY name COLLATE NOCASE").fetchall()
            self._json(200,{"students":[dict(x) for x in students],"total":len(students)});return
        m=re.fullmatch(r"/api/teacher/students/(\d+)",path)
        if m:
            if user["role"]!="teacher":self._json(403,{"error":"Teacher access required."});return
            sid=int(m.group(1))
            with db() as c:
                student=c.execute("SELECT id,name,email,grade,section,avatar,created_at FROM users WHERE id=? AND role='student'",(sid,)).fetchone()
                if not student:self._json(404,{"error":"Student not found."});return
                attempts=c.execute("SELECT lesson_id,score,total,correct,passed,submitted_at FROM attempts WHERE user_id=? ORDER BY lesson_id",(sid,)).fetchall();completed=[x[0] for x in c.execute("SELECT lesson_id FROM lesson_progress WHERE user_id=?",(sid,))];xp=total_xp(c,sid)
            scores=[a["score"] for a in attempts]
            self._json(200,{"student":dict(student),"attempts":[dict(a) for a in attempts],"completed":completed,"xp":xp,"average":round(sum(scores)/len(scores)) if scores else None,"average_count":len(scores)});return
        self._json(404,{"error":"Not found."})

    def api_post(self,path,b):
        if path == "/api/admin/approve-teacher":
            secret=os.environ.get("NUMIQUEST_ADMIN_APPROVAL_TOKEN","")
            auth=self.headers.get("Authorization","")
            if not secret or not hmac.compare_digest(auth,"Bearer "+secret):self._json(403,{"error":"Administrator authorization required."});return
            email=str(b.get("email","")).strip().lower()
            allowed={x.strip().lower() for x in os.environ.get("NUMIQUEST_TEACHER_EMAILS","").split(",") if x.strip()}
            if not email.endswith("@deped.gov.ph") or email not in allowed:self._json(403,{"error":"The address is not on the authorized teacher list."});return
            with db() as c: changed=c.execute("UPDATE users SET approved=1 WHERE email=? AND role='teacher'",(email,)).rowcount
            if not changed:self._json(404,{"error":"No pending teacher registration found for that address."});return
            self._json(200,{"ok":True,"message":"Teacher account approved."});return
        if path == "/api/register":
            role=b.get("role","student"); name=str(b.get("name","")).strip(); email=str(b.get("email","")).strip().lower(); password=str(b.get("password","")); grade=str(b.get("grade", "")); section=str(b.get("section", ""))
            if not name or len(name)>100 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email) or len(password)<8 or len(password)>256: self._json(400,{"error":"Enter a name, valid email, and password between 8 and 256 characters."});return
            if not b.get("terms"):self._json(400,{"error":"Please accept the Terms and Conditions."});return
            if role not in ("student","teacher"):self._json(400,{"error":"Invalid account type."});return
            approved=1
            if role=="student":
                if not email.endswith("@gmail.com"):self._json(400,{"error":"Students must register with a Gmail address."});return
                if not grade or not section:self._json(400,{"error":"Enter your Grade Level and Section."});return
            else:
                if not email.endswith("@deped.gov.ph"):self._json(400,{"error":"Teacher accounts must use an official @deped.gov.ph address."});return
                # Registration never grants teacher access by itself. An administrator
                # approves the account after verifying the teacher's identity.
                approved=0
            try:
                with db() as c:
                    c.execute("INSERT INTO users(name,email,role,password_hash,grade,section,approved,created_at) VALUES(?,?,?,?,?,?,?,?)",(name,email,role,hash_password(password),grade,section,approved,int(time.time())))
                    uid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
                    if role=="student":
                        c.execute("INSERT INTO xp_ledger(user_id,delta,reason,ref,created_at) VALUES(?,0,'account_created',?,?)",(uid,"create:"+str(uid),int(time.time())))
                        for i in range(3):c.execute("INSERT INTO garden(user_id,plot) VALUES(?,?)",(uid,i))
            except sqlite3.IntegrityError:self._json(409,{"error":"An account already uses that email."});return
            self._json(201,{"message":"Account created. Sign in to continue." if approved else "Registration received. Your teacher account is pending administrator approval.","pending":not bool(approved)});return
        if path == "/api/login":
            email=str(b.get("email","")).strip().lower(); password=str(b.get("password","")); role=b.get("role","student")
            if len(password)>256:self._json(401,{"error":"Email or password is incorrect."});return
            with db() as c: user=c.execute("SELECT * FROM users WHERE email=? AND role=?",(email,role)).fetchone()
            if not user or not verify_password(password,user["password_hash"]):self._json(401,{"error":"Email or password is incorrect."});return
            if not user["approved"]:self._json(403,{"error":"This teacher account is pending administrator approval."});return
            raw=secrets.token_urlsafe(32); now=int(time.time())
            with db() as c:
                c.execute("INSERT INTO sessions(token_hash,user_id,expires_at,created_at) VALUES(?,?,?,?)",(hashlib.sha256(raw.encode()).hexdigest(),user["id"],now+SESSION_SECONDS,now));c.execute("INSERT INTO activity(user_id,event,created_at) VALUES(?,?,?)",(user["id"],"login",now))
            ck=cookies.SimpleCookie();ck["nq_session"]=raw;ck["nq_session"]["path"]="/";ck["nq_session"]["httponly"]=True;ck["nq_session"]["samesite"]="Lax";ck["nq_session"]["max-age"]=SESSION_SECONDS
            if os.environ.get("NUMIQUEST_SECURE_COOKIE")=="1":ck["nq_session"]["secure"]=True
            self._json(200,{"user":public_user(dict(user))},{"Set-Cookie":ck.output(header="").strip()});return
        if path == "/api/logout":
            jar=cookies.SimpleCookie(self.headers.get("Cookie",""));raw=jar.get("nq_session")
            if raw:
                with db() as c:c.execute("DELETE FROM sessions WHERE token_hash=?",(hashlib.sha256(raw.value.encode()).hexdigest(),))
            ck=cookies.SimpleCookie();ck["nq_session"]="";ck["nq_session"]["path"]="/";ck["nq_session"]["httponly"]=True;ck["nq_session"]["samesite"]="Lax";ck["nq_session"]["max-age"]=0
            self._json(200,{"ok":True},{"Set-Cookie":ck.output(header="").strip()});return
        user=self._require()
        if not user:return
        now=int(time.time())
        if path == "/api/settings":
            language=b.get("language");theme=b.get("theme")
            if language not in ("English","Tagalog") or theme not in ("Light","Dark"):self._json(400,{"error":"Choose a supported language and theme."});return
            with db() as c:c.execute("UPDATE users SET language=?,theme=? WHERE id=?",(language,theme,user["id"]))
            self._json(200,{"ok":True});return
        if path == "/api/profile":
            name=str(b.get("name","")).strip(); grade=str(b.get("grade", ""));section=str(b.get("section", ""));avatar=str(b.get("avatar", ""))
            if not name or len(name)>100:self._json(400,{"error":"Enter a name under 100 characters."});return
            if avatar and (len(avatar)>700000 or not re.fullmatch(r"data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+",avatar)):self._json(400,{"error":"Use a PNG, JPG, or WebP image under 500 KB."});return
            if user["role"]=="student" and (not grade or not section):self._json(400,{"error":"Grade and Section are required."});return
            with db() as c:c.execute("UPDATE users SET name=?,grade=?,section=?,avatar=? WHERE id=?",(name,grade,section,avatar,user["id"]))
            self._json(200,{"ok":True});return
        if path == "/api/password":
            old=str(b.get("current_password",""));new=str(b.get("new_password",""))
            if len(new)<8:self._json(400,{"error":"New password must be at least 8 characters."});return
            with db() as c:
                row=c.execute("SELECT password_hash FROM users WHERE id=?",(user["id"],)).fetchone()
                if not verify_password(old,row[0]):self._json(400,{"error":"Current password is incorrect."});return
                c.execute("UPDATE users SET password_hash=? WHERE id=?",(hash_password(new),user["id"]))
            self._json(200,{"ok":True});return
        m=re.fullmatch(r"/api/lessons/(\d+)/complete",path)
        if m:
            if user["role"]!="student":self._json(403,{"error":"Student access required."});return
            lid=int(m.group(1))
            if not 1<=lid<=len(LESSONS):self._json(404,{"error":"Lesson not found."});return
            with db() as c:
                if total_xp(c,user["id"])<UNLOCK_XP[lid-1]:self._json(403,{"error":"This lesson is still locked."});return
                c.execute("INSERT OR IGNORE INTO lesson_progress(user_id,lesson_id,completed_at) VALUES(?,?,?)",(user["id"],lid,now))
                if c.execute("SELECT changes()").fetchone()[0]:
                    c.execute("INSERT INTO xp_ledger(user_id,delta,reason,ref,created_at) VALUES(?,?,?,?,?)",(user["id"],100,"lesson_read",f"lesson-read:{user['id']}:{lid}",now))
            self._json(200,{"ok":True});return
        m=re.fullmatch(r"/api/lessons/(\d+)/quiz",path)
        if m:
            if user["role"]!="student":self._json(403,{"error":"Student access required."});return
            lid=int(m.group(1)); answers=b.get("answers")
            if not 1<=lid<=len(LESSONS):self._json(404,{"error":"Lesson not found."});return
            if not isinstance(answers,list) or len(answers)!=10 or any(type(a)!=int or a<0 or a>3 for a in answers):self._json(400,{"error":"Answer all 10 questions before submitting."});return
            with db() as c:
                if c.execute("SELECT 1 FROM attempts WHERE user_id=? AND lesson_id=?",(user["id"],lid)).fetchone():self._json(409,{"error":"This quiz has already been submitted."});return
                if not c.execute("SELECT 1 FROM lesson_progress WHERE user_id=? AND lesson_id=?",(user["id"],lid)).fetchone():self._json(403,{"error":"Complete the lesson before taking its quiz."});return
                if total_xp(c,user["id"])<UNLOCK_XP[lid-1]:self._json(403,{"error":"This lesson is still locked."});return
                key=[q[2] for q in QUIZZES[lid-1]];correct=sum(1 for a,k in zip(answers,key) if a==k);score=correct*10;passed=score>=PASS_MARK
                c.execute("INSERT INTO attempts(user_id,lesson_id,answers,correct,total,score,passed,submitted_at) VALUES(?,?,?,?,?,?,?,?)",(user["id"],lid,json.dumps(answers),correct,10,score,int(passed),now))
                xp=correct*LESSONS[lid-1]["xp"]
                if xp:
                    c.execute("INSERT INTO xp_ledger(user_id,delta,reason,ref,created_at) VALUES(?,?,?,?,?)",(user["id"],xp,"quiz_answers",f"quiz:{user['id']}:{lid}",now))
                if passed:
                    c.execute("INSERT OR IGNORE INTO lesson_progress(user_id,lesson_id,completed_at) VALUES(?,?,?)",(user["id"],lid,now))
                c.execute("INSERT INTO activity(user_id,event,created_at) VALUES(?,?,?)",(user["id"],f"quiz:{lid}:{score}",now))
            self._json(201,{"score":score,"correct":correct,"total":10,"passed":bool(passed),"submitted_at":now,"answers":answers,"key":key,"explanations":[q[3] for q in QUIZZES[lid-1]],"xp_earned":correct*LESSONS[lid-1]["xp"]});return
        if path == "/api/garden/action":
            if user["role"]!="student":self._json(403,{"error":"Student access required."});return
            plot=b.get("plot");action=b.get("action")
            if type(plot)!=int or plot not in range(3):self._json(400,{"error":"Choose a valid garden plot."});return
            with db() as c:
                g=c.execute("SELECT * FROM garden WHERE user_id=? AND plot=?",(user["id"],plot)).fetchone()
                if not g:self._json(404,{"error":"Garden plot not found."});return
                if action=="plant":
                    if g["stage"]>0:self._json(409,{"error":"This plot already has a plant."});return
                    if total_xp(c,user["id"])<100:self._json(400,{"error":"You need 100 XP to plant a seed."});return
                    name=["Mango","Rambutan","Lanzones"][plot];c.execute("UPDATE garden SET plant=?,stage=1 WHERE user_id=? AND plot=?",(name,user["id"],plot));c.execute("INSERT INTO xp_ledger(user_id,delta,reason,ref,created_at) VALUES(?,?,?,?,?)",(user["id"],-100,"garden_seed",f"garden:plant:{user['id']}:{plot}",now))
                elif action=="water":
                    if g["stage"]==0:self._json(400,{"error":"Plant a seed first."});return
                    if g["stage"]>=6:self._json(400,{"error":"This tree has reached its final stage."});return
                    if total_xp(c,user["id"])<10:self._json(400,{"error":"Watering costs 10 XP."});return
                    stage=g["stage"]+1;c.execute("UPDATE garden SET stage=? WHERE user_id=? AND plot=?",(stage,user["id"],plot));c.execute("INSERT INTO xp_ledger(user_id,delta,reason,ref,created_at) VALUES(?,?,?,?,?)",(user["id"],-10,"garden_water",f"garden:water:{user['id']}:{plot}:{stage}",now))
                    if stage==6 and not g["fruit_claimed"]:
                        c.execute("UPDATE garden SET fruit_claimed=1 WHERE user_id=? AND plot=?",(user["id"],plot));c.execute("INSERT INTO xp_ledger(user_id,delta,reason,ref,created_at) VALUES(?,?,?,?,?)",(user["id"],30,"garden_fruit",f"garden:fruit:{user['id']}:{plot}",now))
                else:self._json(400,{"error":"Choose plant or water."});return
            with db() as c: xp=total_xp(c,user["id"])
            self._json(200,{"ok":True,"xp":xp});return
        if path == "/api/games/answer":
            if user["role"]!="student":self._json(403,{"error":"Student access required."});return
            game=b.get("game");answer=b.get("answer")
            if type(game)!=int or game not in range(6):self._json(400,{"error":"Choose a valid game."});return
            now=time.time();day=time.strftime("%Y-%m-%d",time.localtime(now))
            with db() as c:
                eligible=c.execute("SELECT passed FROM attempts WHERE user_id=? AND lesson_id=?",(user["id"],game+1)).fetchone()
                if not eligible or not eligible[0]:self._json(403,{"error":"Pass the matching lesson quiz to unlock this game."});return
                if str(answer)!="56":self._json(400,{"error":"Not quite. Try again!"});return
                try:c.execute("INSERT INTO game_rewards(user_id,game_id,day) VALUES(?,?,?)",(user["id"],game,day))
                except sqlite3.IntegrityError:self._json(409,{"error":"You have already earned today's reward for this game."});return
                c.execute("INSERT INTO xp_ledger(user_id,delta,reason,ref,created_at) VALUES(?,?,?,?,?)",(user["id"],10,"game_reward",f"game:{user['id']}:{game}:{day}",int(now)))
            self._json(200,{"ok":True,"earned":10,"xp":total_xp(db(),user["id"])});return
        self._json(404,{"error":"Not found."})

def total_xp(c,user_id):
    return int(c.execute("SELECT COALESCE(SUM(delta),0) FROM xp_ledger WHERE user_id=?",(user_id,)).fetchone()[0])

def public_user(u):
    if not u:return None
    return {k:u.get(k,"" if k not in ("id",) else None) for k in ("id","name","email","role","grade","section","avatar","language","theme")}

if __name__ == "__main__":
    init_db()
    print(f"NumiQuest is running at http://{HOST}:{PORT}")
    print(f"Database: {DB_PATH}")
    if DEMO_ENABLED: print("Local demo teacher: teacher.demo@numiquest.test / NumiQuestDemo2026!")
    try: ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
    except KeyboardInterrupt: print("\nNumiQuest server stopped.")

