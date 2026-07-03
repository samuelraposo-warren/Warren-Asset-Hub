@echo off
chcp 65001 >nul
title Popular Banco - Inventario de TI
cd /d "%~dp0"

REM Usa o Python do venv do projeto; se nao existir, tenta o Python do sistema.
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo   Populando o banco com dados de demonstracao
echo   (fornecedores, maquinas, funcionarios, etc.)
echo ============================================================
echo.

"%PY%" "run_seed.py"

echo.
echo ------------------------------------------------------------
pause
