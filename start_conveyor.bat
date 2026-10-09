@echo off
cd /d C:\AI\conveyor_app

echo ========================================
echo   Conveyor V5.7 - Starting
echo ========================================
echo.

echo [1/3] Starting FastAPI (port 5001)...
start "Conveyor API" cmd /k "cd /d C:\AI\conveyor_app && .venv\Scripts\activate.bat && python -m src.main"

timeout /t 4 /nobreak >nul

echo [2/3] Starting Streamlit (port 8501)...
start "Conveyor UI" cmd /k "cd /d C:\AI\conveyor_app && .venv\Scripts\activate.bat && streamlit run src/ui/streamlit_app.py"

timeout /t 6 /nobreak >nul

echo [3/3] Opening browser...
start http://localhost:8501

echo.
echo ========================================
echo   Conveyor started!
echo ========================================
echo.
echo Two windows opened (API + UI).
echo Close them to stop Conveyor.
echo.
pause