@echo off
REM SmartCondo - clique duas vezes neste arquivo para preparar e subir o sistema.
REM Ele so chama o configurar.ps1 sem esbarrar na politica de execucao do PowerShell.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0configurar.ps1"
pause
