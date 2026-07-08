@echo off
chcp 65001 >nul
title Popular Acessos - Centralizador Warren
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Populando sub-setores, modulos e usuarios de exemplo
echo   (rode DEPOIS do Atualizar_Banco.bat)
echo ============================================================
echo.

"%PY%" seed_acessos.py

echo.
echo ------------------------------------------------------------
pause
