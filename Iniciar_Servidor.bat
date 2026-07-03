@echo off
chcp 65001 >nul
title Servidor - Inventario de TI
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Iniciando o servidor (http://127.0.0.1:8080)
echo   Feche esta janela ou pressione Ctrl+C para parar.
echo ============================================================
echo.

"%PY%" run.py

echo.
pause
