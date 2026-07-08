@echo off
chcp 65001 >nul
title Importar Rede (.drawio) - Inventario de TI
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Importar pontos de rede do diagrama .drawio
echo   (procura um arquivo .drawio nesta pasta)
echo ============================================================
echo.

"%PY%" importar_rede.py %1

echo.
echo ------------------------------------------------------------
pause
