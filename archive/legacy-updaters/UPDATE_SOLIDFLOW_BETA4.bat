@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

title SolidFlow UX - Aggiornamento sicuro beta.4

set "TARGET=%APPDATA%\FreeCAD\v1-1\Mod\SolidFlowUX"
set "BASE=https://raw.githubusercontent.com/samael1974/FREECAD-IMPLEMENTAZIONE-UX/main/SolidFlowUX"
set "TMP=%TEMP%\SolidFlowUX_Update"

cls
echo ================================================================
echo  SolidFlow UX - Aggiornamento sicuro beta.4
echo ================================================================
echo.
echo Destinazione:
echo %TARGET%
echo.

if not exist "%TARGET%\solidflow_ui.py" (
    echo [ERRORE] Non trovo una installazione SolidFlow valida.
    echo Manca: %TARGET%\solidflow_ui.py
    echo.
    pause
    exit /b 10
)

rem Do not overwrite files while FreeCAD is running.
tasklist /FI "IMAGENAME eq FreeCAD.exe" 2>nul | find /I "FreeCAD.exe" >nul
if not errorlevel 1 (
    echo [ERRORE] FreeCAD e' aperto.
    echo Chiudi completamente FreeCAD e riesegui questo file.
    echo.
    pause
    exit /b 11
)

if exist "%TMP%" rmdir /S /Q "%TMP%" >nul 2>&1
mkdir "%TMP%" >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Impossibile creare la cartella temporanea.
    pause
    exit /b 12
)

echo [1/5] Scarico i file aggiornati da GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "Invoke-WebRequest -UseBasicParsing '%BASE%/InitGui.py' -OutFile '%TMP%\InitGui.py';" ^
  "Invoke-WebRequest -UseBasicParsing '%BASE%/solidflow_beta4.py' -OutFile '%TMP%\solidflow_beta4.py'"
if errorlevel 1 goto :download_error

rem Basic integrity/identity checks before touching user files.
findstr /C:"SolidFlow UX GUI bootstrap" "%TMP%\InitGui.py" >nul || goto :validation_error
findstr /C:"VERSION = \"0.4.0-beta.4\"" "%TMP%\solidflow_beta4.py" >nul || goto :validation_error
findstr /C:"def install" "%TMP%\solidflow_beta4.py" >nul || goto :validation_error

echo [2/5] Controllo sintassi Python...
set "FCPY=%ProgramFiles%\FreeCAD 1.1\bin\python.exe"
if exist "%FCPY%" (
    "%FCPY%" -m py_compile "%TMP%\InitGui.py" "%TMP%\solidflow_beta4.py"
    if errorlevel 1 goto :validation_error
) else (
    echo       Python di FreeCAD non trovato nel percorso standard: controllo saltato.
)

for /f "tokens=1-6 delims=/:. " %%a in ("%date% %time%") do set "STAMP=%%c%%b%%a_%%d%%e%%f"
set "BACKUP=%TARGET%\_backup\beta4_%STAMP%"
mkdir "%BACKUP%" >nul 2>&1
if errorlevel 1 goto :backup_error

echo [3/5] Creo backup...
if exist "%TARGET%\InitGui.py" copy /Y "%TARGET%\InitGui.py" "%BACKUP%\InitGui.py" >nul
if exist "%TARGET%\solidflow_beta4.py" copy /Y "%TARGET%\solidflow_beta4.py" "%BACKUP%\solidflow_beta4.py" >nul

echo [4/5] Installo i file validati...
copy /Y "%TMP%\InitGui.py" "%TARGET%\InitGui.py" >nul || goto :install_error
copy /Y "%TMP%\solidflow_beta4.py" "%TARGET%\solidflow_beta4.py" >nul || goto :install_error

rem Old bytecode can hide what is actually being loaded after development changes.
if exist "%TARGET%\__pycache__" rmdir /S /Q "%TARGET%\__pycache__" >nul 2>&1

echo [5/5] Verifica finale...
findstr /C:"The plain ``S`` key is intentionally owned only" "%TARGET%\InitGui.py" >nul || goto :install_error
findstr /C:"VERSION = \"0.4.0-beta.4\"" "%TARGET%\solidflow_beta4.py" >nul || goto :install_error

rmdir /S /Q "%TMP%" >nul 2>&1

echo.
echo ================================================================
echo  AGGIORNAMENTO COMPLETATO
echo ================================================================
echo.
echo Backup precedente:
echo %BACKUP%
echo.
echo Ora avvia FreeCAD e prova subito il tasto S.
echo Se S non apre la palette, apri Visualizza ^> Pannelli ^> Vista report
echo e inviami le righe che iniziano con "SolidFlow:".
echo.
pause
exit /b 0

:download_error
echo.
echo [ERRORE] Download non riuscito. Nessun file installato.
goto :fail

:validation_error
echo.
echo [ERRORE] I file scaricati non hanno superato la validazione.
echo Nessun file della tua installazione e' stato sostituito.
goto :fail

:backup_error
echo.
echo [ERRORE] Non riesco a creare il backup. Installazione annullata.
goto :fail

:install_error
echo.
echo [ERRORE] Installazione incompleta.
echo Il backup e' disponibile in:
echo %BACKUP%
echo.
echo Ripristina InitGui.py e solidflow_beta4.py da quella cartella.
goto :fail

:fail
if exist "%TMP%" rmdir /S /Q "%TMP%" >nul 2>&1
pause
exit /b 1
