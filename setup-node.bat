@echo off
rem ZipHive - siapkan laptop ini sebagai node (Windows). Klik dua kali dari Explorer.
setlocal
cd /d "%~dp0"

set PYEXE=python
if exist ".venv\Scripts\python.exe" set PYEXE=.venv\Scripts\python.exe
where py >nul 2>nul
if %errorlevel%==0 if not exist ".venv\Scripts\python.exe" set PYEXE=py -3

%PYEXE% scripts\bootstrap_node.py %*

set STATUS=%errorlevel%
echo.
echo Selesai dengan kode %STATUS%.
pause
exit /b %STATUS%
