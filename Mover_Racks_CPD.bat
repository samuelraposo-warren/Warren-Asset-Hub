@echo off
chcp 65001 >nul
title Mover R02/R03 para CPD - Inventario de TI
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Vincular os racks R02 e R03 ao ambiente CPD
echo ============================================================
echo.

"%PY%" mover_racks_cpd.py

echo.
echo ------------------------------------------------------------
pause
