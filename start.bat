@echo off
echo.
echo  VidyAI - AI Education Platform
echo  ================================
echo.

:: Check if .env exists
if not exist ".env" (
    echo [!] .env file not found. Copying from .env.example...
    copy .env.example .env
    echo [!] Please edit .env and set your GROQ_API_KEY before continuing.
    pause
    exit /b 1
)

:: Check if DB exists, if not seed it
if not exist "vidyai.db" (
    echo [*] Setting up database...
    python seed.py
)

echo [*] Starting VidyAI...
echo.
echo  Open http://localhost:5000 in your browser
echo  Demo Student: student@demo.com / demo123
echo  Demo Teacher: teacher@demo.com / demo123
echo.
python app.py
pause
