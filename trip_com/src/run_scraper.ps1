$python = "C:\Users\admin\Desktop\icb10proj2\.venv\Scripts\python.exe"
$script = "C:\Users\admin\Desktop\icb10proj2\trip_com\src\scraper.py"

& $python -m pip install scrapling playwright
& $python -m playwright install chromium
& $python $script --auto-yes
