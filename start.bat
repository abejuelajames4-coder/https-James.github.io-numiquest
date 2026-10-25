@echo off
cd /d "%~dp0"
set NUMIQUEST_DEMO=1
set NUMIQUEST_HOST=127.0.0.1
py -3 --version >nul 2>&1
if not errorlevel 1 goto use_py
python --version >nul 2>&1
if not errorlevel 1 goto use_python
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" goto use_codex_python
echo Python 3 was not found. Install Python 3, then double-click start.bat again.
pause
exit /b 1
:use_py
py -3 server.py
goto end
:use_python
python server.py
goto end
:use_codex_python
"%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" server.py
:end

