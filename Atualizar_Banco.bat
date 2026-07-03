@echo off
chcp 65001 >nul
title Atualizar Banco - Inventario de TI
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Atualizando o schema do banco (settings + preferences)
echo   Seguro rodar mais de uma vez.
echo ============================================================
echo.

"%PY%" "upgrade_schema.py"

echo.
echo ------------------------------------------------------------
pause
