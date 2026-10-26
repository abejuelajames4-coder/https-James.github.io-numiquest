# NumiQuest

Responsive Grade 11 General Mathematics learning app using the original blue-and-orange design, a Python standard-library backend, and SQLite storage.

## Run locally

1. Install Python 3.10 or newer.
2. In VS Code, open this project folder and run **Terminal → Run Task → NumiQuest: Start website**. You can also double-click `start.bat` (this local launcher enables the demo account).
3. Keep the VS Code terminal or server window open, then open http://127.0.0.1:8000 in your browser. Do not open `index.html` directly; the login and learning features need the Python server.

The SQLite database is created automatically as `numiquest.sqlite3` beside the app. Keep the server running while using the website. Press Ctrl+C in the VS Code terminal or server window to stop it. If the login page reports that it cannot connect, start the task again and reload the page.

## Local demo teacher

- Email: `teacher.demo@numiquest.test`
- Password: `NumiQuestDemo2026!`

This is a local-only demonstration account and is not a real DepEd email address. It is enabled by `start.bat`; server deployments default to demo disabled.

Teacher sign-ups are always pending until an administrator verifies the teacher out-of-band. After registration, set the verified address on the authorized list and approve it. For example, in PowerShell:

```powershell
$env:NUMIQUEST_DEMO = "0"
$env:NUMIQUEST_TEACHER_EMAILS = "your.authorized.address@deped.gov.ph"
py -3 server.py
```

In a second PowerShell window, after the teacher has registered, run:

```powershell
$env:NUMIQUEST_TEACHER_EMAILS = "your.authorized.address@deped.gov.ph"
py -3 approve_teacher.py your.authorized.address@deped.gov.ph
```

Teacher registration requires an `@deped.gov.ph` address. Registration alone does not grant teacher access. The app cannot create or verify a real DepEd mailbox.

## Features

- Student and teacher sign-in, registration, role separation, and secure server-side password hashing.
- SQLite persistence for accounts, sessions, learning progress, quiz attempts, XP transactions, settings, and garden plots.
- Six General Mathematics lessons, fixed 10-question quizzes, answer review, 70% passing threshold, and one saved attempt per quiz.
- Server-side XP, lesson unlocks, game access, and garden spending checks.
- Teacher class dashboard, searchable student records, student progress details, profile editing, and password changes.
- English/Tagalog setting, light/dark theme, and responsive layout.

## Free Render deployment

`render.yaml` describes a free Python web service in Singapore with HTTPS-secure cookies and the shared teacher demo account disabled. Render connects to the GitHub repository and deploys the Blueprint, then provides a public `onrender.com` link that anyone can open. The first deployment may take a few minutes.

This free preview stores its SQLite database in `/tmp`. Render Free services can sleep after inactivity, and their local files can be erased after a restart, redeploy, or spin-down. The login page displays a notice that accounts and learning progress may reset. Use fictional/demo learner information only; do not enter real student records.

To publish, connect your GitHub repository to Render, select **New + → Blueprint**, choose the repository, and apply the `render.yaml` settings. Keep `NUMIQUEST_DEMO` set to `0`. Add the official teacher addresses to `NUMIQUEST_TEACHER_EMAILS` in the Render service environment. The app does not provide a shared teacher password. Teachers register with their real `@deped.gov.ph` address; registration remains pending until an administrator verifies and approves them.

Set `NUMIQUEST_TEACHER_EMAILS` in the Render service environment to the verified official teacher addresses. After a teacher registers and you verify their identity out of band, set these variables locally and run the approval helper:

```powershell
$env:NUMIQUEST_BASE_URL = "https://your-service.onrender.com"
$env:NUMIQUEST_TEACHER_EMAILS = "verified.teacher@deped.gov.ph"
$env:NUMIQUEST_ADMIN_APPROVAL_TOKEN = "the value generated for the Render service"
py -3 approve_teacher.py verified.teacher@deped.gov.ph
```

Keep the approval token private. Never upload the local SQLite database. For real student records, use school-approved hosting with persistent storage, backups, and appropriate data-handling arrangements.

