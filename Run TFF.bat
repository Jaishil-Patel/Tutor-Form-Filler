@echo off
title Tutor Form Filler
cd /d "%~dp0"
echo Starting Tutor Form Filler...
echo Your browser will open automatically.
echo.
echo Keep this window open while you use the app.
echo To stop, close this window or press Ctrl+C.
echo.
python server.py
echo.
echo The app has stopped. Press any key to close.
pause >nul
