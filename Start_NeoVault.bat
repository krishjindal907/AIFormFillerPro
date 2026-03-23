@echo off
title NeoVault AI Server
color 0A
echo ===================================================
echo   Starting NeoVault OSINT Server (Local Network)
echo ===================================================

cd /d "D:\coading\projects\AIFormFillerPro"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo.
echo Server initialized! Your Local Link is http://127.0.0.1:5000
echo You can also open the same link on your Phone (on same Wi-Fi).
echo.
echo Launching Browser...
start http://127.0.0.1:5000

echo.
echo DO NOT CLOSE THIS WINDOW if you want the link to work.
echo Press [Ctrl + C] to shut down safely.
echo ===================================================
python app.py
pause
