@echo off
chcp 65001 >nul
title Instalar dependencias - Inventario de TI
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Instalando dependencias (requirements.txt)
echo ============================================================
echo.

"%PY%" -m pip install -r requirements.txt

echo.
echo ------------------------------------------------------------
echo Concluido. Se instalou pacotes novos, reinicie o servidor Flask.
pause
