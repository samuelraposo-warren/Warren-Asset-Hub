@echo off
chcp 65001 >nul
title Remover Monitores - Inventario de TI
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Remover o tipo Monitor e os ativos monitor do banco
echo   ATENCAO: acao definitiva (apaga os monitores).
echo ============================================================
echo.
set /p CONF="Digite SIM para confirmar: "
if /I not "%CONF%"=="SIM" (
  echo Cancelado.
  pause
  exit /b
)

"%PY%" "remover_monitores.py"

echo.
echo ------------------------------------------------------------
pause
