@echo off
chcp 65001 >nul
title Importar Certificados (crt.sh) - Centralizador Warren
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

REM Aceita o arquivo por arrastar-e-soltar no .bat; senão usa certificados.json
set "JSON=%~1"
if "%JSON%"=="" set "JSON=%~dp0certificados.json"

echo ============================================================
echo   Importando certificados do JSON (idempotente, dedup por serial)
echo   Arquivo: %JSON%
echo ============================================================
echo.

if not exist "%JSON%" (
  echo ERRO: arquivo nao encontrado.
  echo   - Arraste o arquivo .json sobre este .bat, OU
  echo   - Salve como "certificados.json" nesta pasta.
  echo.
  pause
  goto :eof
)

"%PY%" -m flask --app run:app import-certs "%JSON%"

echo.
echo ------------------------------------------------------------
pause
