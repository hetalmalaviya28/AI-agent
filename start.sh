#!/bin/bash
echo ""
echo " VidyAI - AI Education Platform"
echo " ================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[!] .env not found. Copying from .env.example..."
    cp .env.example .env
    echo "[!] Please edit .env and set your GROQ_API_KEY before continuing."
    exit 1
fi

# Seed DB if needed
if [ ! -f "vidyai.db" ]; then
    echo "[*] Setting up database..."
    python3 seed.py
fi

echo "[*] Starting VidyAI..."
echo ""
echo " Open http://localhost:5000 in your browser"
echo " Demo Student: student@demo.com / demo123"
echo " Demo Teacher: teacher@demo.com / demo123"
echo ""
python3 app.py
