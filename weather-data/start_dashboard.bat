@echo off
chcp 65001 > nul
echo ========================================================
echo   🌾 AgroMetric 대시보드 로컬 서버 시작
echo ========================================================
echo.
echo 브라우저를 자동으로 엽니다...
start http://localhost:8080/report/dashboard.html
echo.
echo 서버가 실행 중입니다. 이 창을 닫으면 서버가 종료됩니다.
python -m http.server 8080
