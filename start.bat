@echo off
echo 🌾 Starting Crop Yield Estimator System...

echo.
echo Starting FastAPI Backend...
start cmd /k "python main.py"

echo.
echo Starting React Frontend...
cd frontend
start cmd /k "npm run dev"

echo.
echo System started! 
echo Backend running on: http://localhost:8000
echo Frontend running on: http://localhost:5173 (or similar port, check frontend console)
echo.
echo You can log in with:
echo Username: semicolon
echo Password: semicolon123
