@echo off
rem Faz o TechAssist AI iniciar sozinho com o Windows (modo servidor) e libera a porta 8501.
rem Execute com o botao direito: "Executar como administrador". PARA DEPOIS: veja servidor\LEIA-ME.md
setlocal
cd /d "%~dp0.."
net session >nul 2>&1
if errorlevel 1 (
    echo Execute este arquivo como Administrador ^(botao direito, Executar como administrador^).
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo Antes, execute IniciarTechAssist.bat uma vez para preparar o ambiente e o arquivo .env.
    pause
    exit /b 1
)
if not exist ".env" (
    echo Antes, execute IniciarTechAssist.bat uma vez para criar o arquivo .env.
    pause
    exit /b 1
)
set "TAREFA=TechAssistAI"
schtasks /Create /TN "%TAREFA%" /TR "\"%~dp0IniciarServidor.bat\"" /SC ONSTART /RU SYSTEM /RL HIGHEST /F
if errorlevel 1 (
    echo Nao foi possivel criar a tarefa agendada.
    pause
    exit /b 1
)
netsh advfirewall firewall delete rule name="TechAssist AI (8501)" >nul 2>&1
netsh advfirewall firewall add rule name="TechAssist AI (8501)" dir=in action=allow protocol=TCP localport=8501 profile=private,domain
schtasks /Run /TN "%TAREFA%"
echo.
echo Pronto. O TechAssist AI inicia com o Windows e esta rodando agora.
echo Acesse de outro computador: http://IP-DESTE-COMPUTADOR:8501  ^(descubra o IP com o comando ipconfig^)
echo Para remover: execute RemoverServicoWindows.bat como administrador.
pause
