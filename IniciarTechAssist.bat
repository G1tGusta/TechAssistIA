@echo off
setlocal
cd /d "%~dp0"
title TechAssist AI

rem --- 1) Python 3.10 ou superior ---
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto :sem_python
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto :sem_python

rem --- 2) Ambiente virtual (recria se foi copiado de outro computador) ---
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
    if errorlevel 1 rmdir /s /q ".venv"
)
if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual ^(somente na primeira vez^)...
    %PY% -m venv .venv
    if errorlevel 1 goto :erro
)

rem --- 3) Bibliotecas ---
".venv\Scripts\python.exe" -c "import streamlit, groq, dotenv" >nul 2>nul
if errorlevel 1 (
    echo Instalando bibliotecas ^(precisa de internet; somente na primeira vez^)...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :erro
)

rem --- 4) Arquivo .env ---
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo Vai abrir o arquivo .env. Preencha TECHNICIAN_PASSWORD ^(senha do tecnico^) e,
    echo se quiser usar a IA, GROQ_API_KEY. Salve, feche o Bloco de Notas e aguarde.
    start /wait notepad ".env"
)

rem --- 5) Iniciar ---
echo.
echo Iniciando o TechAssist AI... Para encerrar, feche esta janela.
".venv\Scripts\python.exe" -m streamlit run app.py
goto :fim

:sem_python
echo.
echo Python 3.10 ou superior nao encontrado.
echo Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".

:erro
echo.
echo A inicializacao nao foi concluida.

:fim
pause
