@echo off
rem Inicia o TechAssist AI em modo servidor (acessivel por outros computadores da rede).
rem PARA DEPOIS: veja servidor\LEIA-ME.md
setlocal
cd /d "%~dp0.."
title TechAssist AI (servidor)
if not exist ".venv\Scripts\python.exe" (
    echo Antes, execute IniciarTechAssist.bat uma vez para preparar o ambiente.
    exit /b 1
)
if not exist ".env" (
    echo Antes, execute IniciarTechAssist.bat uma vez para criar o arquivo .env.
    exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --browser.gatherUsageStats false
