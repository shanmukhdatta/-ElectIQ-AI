@echo off
echo.
echo ElectIQ - Election Intelligence Assistant
echo ============================================
echo.

if not exist .env (
    copy .env.example .env
    echo Add your GROQ_API_KEY to .env before continuing!
    echo Optional fallback: add GOOGLE_API_KEY for Gemini.
    echo.
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing dependencies...
pip install -r backend\requirements.txt -q

for /f "tokens=1,* delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" set %%a=%%b
)

echo.
echo Starting ElectIQ on http://localhost:5000
echo ============================================
echo.

python backend\app.py
pause
