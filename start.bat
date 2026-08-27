@echo off
cd /d "%~dp0"
start "" "C:\Users\Shaan\AppData\Local\Programs\Python\Python312\python.exe" manage.py runserver 0.0.0.0:8000 --noreload
echo Server started at http://localhost:8000
timeout /t 5 /nobreak >nul
exit
