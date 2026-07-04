@echo off
chcp 65001 > nul
echo [서버 구동기] 백엔드 서버를 시작합니다...
cd c:\Users\admin\Desktop\icb10proj2\weather-data
uv pip install fastapi uvicorn pandas python-dotenv scikit-learn requests apscheduler
echo.
echo 서버를 켜는 중입니다...
uv run uvicorn src.api:app --reload --port 8000
pause

