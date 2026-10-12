@echo off
echo Starting CyberGuard Project...

echo [1/2] Starting Backend Server (FastAPI)...
start cmd /k "cd backend && pip install -r requirements.txt && python main.py"

echo [2/2] Starting Frontend Server (Vite)...
start cmd /k "cd frontend && npm install && npm run dev"

echo Project is starting! 
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
pause
