@echo off
chcp 65001 >nul
title Limpar tipos fora de escopo - Inventario de TI
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Remover Monitores e Perifericos do banco (definitivo)
echo   Tambem remove as tabelas monitor_specs e peripheral_specs.
echo ============================================================
echo.
set /p CONF="Digite SIM para confirmar: "
if /I not "%CONF%"=="SIM" (
  echo Cancelado.
  pause
  exit /b
)

"%PY%" "limpar_tipos.py"

echo.
echo ------------------------------------------------------------
pause
