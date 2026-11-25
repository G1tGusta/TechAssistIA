@echo off
rem Remove o inicio automatico do TechAssist AI e fecha a porta 8501. Execute como administrador.
net session >nul 2>&1
if errorlevel 1 (
    echo Execute este arquivo como Administrador.
    pause
    exit /b 1
)
schtasks /End /TN "TechAssistAI" >nul 2>&1
schtasks /Delete /TN "TechAssistAI" /F
netsh advfirewall firewall delete rule name="TechAssist AI (8501)"
echo.
echo Inicio automatico removido. Se o sistema ainda estiver aberto, feche a janela dele ou reinicie o computador.
pause
