@echo off
rem ZipHive - jalankan Worker di laptop ini (Windows). Klik dua kali dari Explorer.
setlocal
cd /d "%~dp0"

set PYEXE=python
if exist ".venv\Scripts\python.exe" set PYEXE=.venv\Scripts\python.exe
where py >nul 2>nul
if %errorlevel%==0 if not exist ".venv\Scripts\python.exe" set PYEXE=py -3

%PYEXE% scripts\start_worker.py %*

set STATUS=%errorlevel%
echo.
echo Selesai dengan kode %STATUS%.
pause
exit /b %STATUS%
