@echo off
chcp 65001 > nul
echo ========================================================
echo   🚀 AgroMetric 원클릭 대시보드 실행기
echo ========================================================
echo.
echo 백엔드 AI 모터와 브라우저를 동시에 켭니다...
cd c:\Users\admin\Desktop\icb10proj2
uv pip install fastapi uvicorn pandas python-dotenv scikit-learn requests apscheduler > nul 2>&1

echo 브라우저를 엽니다...
start http://localhost:8000/

echo.
echo [시스템 가동 중] 이 검은 창을 닫으면 대시보드 실시간 연결이 끊어집니다!
echo ========================================================
cd c:\Users\admin\Desktop\icb10proj2\weather-data
uv run uvicorn src.api:app --reload --port 8000

echo.
echo 서버가 종료되었습니다.
pause
