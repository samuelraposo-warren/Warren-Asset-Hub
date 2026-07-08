@echo off
chcp 65001 >nul
title Enviar Alertas de Certificados - Centralizador Warren
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Verificando vencimentos e enviando alertas por e-mail
echo   (agende este .bat no Agendador de Tarefas do Windows,
echo    ex.: diariamente as 08:00)
echo ============================================================
echo.

"%PY%" -m flask --app run:app send-cert-alerts

echo.
echo ------------------------------------------------------------
pause
