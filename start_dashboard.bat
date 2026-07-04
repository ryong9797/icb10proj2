@echo off
chcp 65001 > nul
echo ========================================================
echo 버거지수 대시보드 실행 스크립트
echo ========================================================
echo.

echo 1. 필요한 패키지(folium 등)를 설치하고 있습니다. 잠시만 기다려주세요...
uv pip install folium streamlit-folium geopandas requests koreanize-matplotlib

echo.
echo 2. 설치 완료! 곧 대시보드가 브라우저에서 자동으로 열립니다.
echo (만약 오류가 나면 이 창에 에러 메시지가 뜹니다.)
echo.

.\.venv\Scripts\python -m streamlit run burger_index\app.py

echo.
echo 대시보드가 종료되었거나 실행 중 오류가 발생했습니다.
pause
