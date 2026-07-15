@echo off
chcp 65001 >nul
setlocal
title Criando Rouge portátil
cd /d "%~dp0"

set "PY=%~dp0.build-venv\Scripts\python.exe"

echo [1/4] Preparando o empacotador...
if not exist "%PY%" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.12 -m venv ".build-venv"
    ) else (
        python -m venv ".build-venv"
    )
)
if not exist "%PY%" (
    echo ERRO: instale o Python 3.12 para criar a versão portátil.
    pause
    exit /b 1
)
"%PY%" -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 goto :error

echo [2/4] Criando o executável...
"%PY%" -m PyInstaller --noconfirm --clean --onedir --name Rouge ^
    --add-data "templates:templates" ^
    --add-data "static:static" ^
    app.py
if errorlevel 1 goto :error

echo [3/4] Copiando sua coleção e histórico...
if exist "nhentai_out" robocopy "nhentai_out" "dist\Rouge\nhentai_out" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :error
if not exist "dist\Rouge\nhentai_out" mkdir "dist\Rouge\nhentai_out"
if exist "tag_history.json" copy /Y "tag_history.json" "dist\Rouge\tag_history.json" >nul
if exist "README.md" copy /Y "README.md" "dist\Rouge\LEIA-ME.md" >nul
if exist "COMO_USAR.txt" copy /Y "COMO_USAR.txt" "dist\Rouge\COMO_USAR.txt" >nul

echo [4/4] Pronto.
echo.
echo Pasta portátil: %~dp0dist\Rouge
echo Abra Rouge.exe para iniciar.
pause
exit /b 0

:error
echo.
echo ERRO: não foi possível criar a pasta portátil.
pause
exit /b 1
