@echo off
REM Simple script to run YTP Deluxe on legacy Windows with Python 2.7 or Python 3.x
REM Place ffmpeg.exe and ffplay.exe in the same folder as this script for best compatibility.

if exist "%~dp0\python.exe" (
  "%~dp0\python.exe" main.py
) else (
  python main.py
)
pause