@echo off
setlocal
cd /d "%~dp0"
title Diagnostico do TechAssist AI
set "PYEXE="
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
    if not errorlevel 1 set "PYEXE=.venv\Scripts\python.exe"
)
if not defined PYEXE where py >nul 2>nul && set "PYEXE=py -3"
if not defined PYEXE where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
    echo Python nao encontrado.
    echo Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
    pause
    exit /b 1
)
%PYEXE% diagnostico.py
echo.
echo O relatorio foi salvo em diagnostico.txt. Se precisar de ajuda, envie esse arquivo.
pause
