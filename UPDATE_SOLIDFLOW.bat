@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

title SolidFlow UX - Aggiornatore automatico

set "TARGET=%APPDATA%\FreeCAD\v1-1\Mod\SolidFlowUX"
set "BASE=https://raw.githubusercontent.com/samael1974/FREECAD-IMPLEMENTAZIONE-UX/main/SolidFlowUX"
set "TMP=%TEMP%\SolidFlowUX_Rolling_Update"

cls
echo ================================================================
echo  SolidFlow UX - Aggiornatore automatico
echo ================================================================
echo.
echo Cartella destinazione:
echo %TARGET%
echo.

if not exist "%TARGET%\solidflow_ui.py" (
    echo [ERRORE] Non trovo una installazione SolidFlow valida.
    echo Manca: %TARGET%\solidflow_ui.py
    echo.
    pause
    exit /b 10
)

tasklist /FI "IMAGENAME eq FreeCAD.exe" 2>nul | find /I "FreeCAD.exe" >nul
if not errorlevel 1 (
    echo [ERRORE] FreeCAD e' aperto.
    echo Chiudi completamente FreeCAD e riesegui l'aggiornatore.
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

echo [1/6] Scarico il manifest della versione corrente...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; Invoke-WebRequest -UseBasicParsing '%BASE%/manifest.txt' -OutFile '%TMP%\manifest.txt'"
if errorlevel 1 goto :download_error

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $m=Get-Content '%TMP%\manifest.txt' ^| ForEach-Object {$_.Trim()} ^| Where-Object {$_ -and -not $_.StartsWith('#')}; if(-not $m){throw 'Manifest vuoto'}; $m ^| Set-Content -Encoding ASCII '%TMP%\files.txt'"
if errorlevel 1 goto :validation_error

echo [2/6] Scarico i moduli richiesti dal manifest...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$base='%BASE%'; $tmp='%TMP%';" ^
  "$files=Get-Content ($tmp+'\files.txt') ^| ForEach-Object {$_.Trim()} ^| Where-Object {$_};" ^
  "foreach($f in $files){ if($f.Contains('..') -or $f.Contains('/') -or $f.Contains('\')){throw 'Nome file non valido nel manifest: '+$f}; Invoke-WebRequest -UseBasicParsing ($base+'/'+$f) -OutFile ($tmp+'\'+$f) }"
if errorlevel 1 goto :download_error

rem Identity checks for the essential bootstrap/layers.
findstr /C:"plain ``S`` key is intentionally owned only" "%TMP%\InitGui.py" >nul || goto :validation_error
findstr /C:"VERSION = \"0.4.0-beta.4\"" "%TMP%\solidflow_beta4.py" >nul || goto :validation_error
findstr /C:"VERSION = \"0.4.0-beta.5\"" "%TMP%\solidflow_beta5.py" >nul || goto :validation_error
findstr /C:"solidflow_beta5.install()" "%TMP%\InitGui.py" >nul || goto :validation_error

echo [3/6] Controllo la sintassi Python...
set "FCPY=%ProgramFiles%\FreeCAD 1.1\bin\python.exe"
if exist "%FCPY%" (
    for /f "usebackq delims=" %%F in ("%TMP%\files.txt") do (
        set "ITEM=%%F"
        if /I "!ITEM:~-3!"==".py" (
            "%FCPY%" -m py_compile "%TMP%\!ITEM!"
            if errorlevel 1 goto :validation_error
        )
    )
) else (
    echo       Python di FreeCAD non trovato nel percorso standard.
    echo       Il controllo locale viene saltato; resta attivo il controllo GitHub CI.
)

for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%T"
set "BACKUP=%TARGET%\_backup\rolling_%STAMP%"
mkdir "%BACKUP%" >nul 2>&1
if errorlevel 1 goto :backup_error

echo [4/6] Creo il backup dei soli file che verranno sostituiti...
for /f "usebackq delims=" %%F in ("%TMP%\files.txt") do (
    if exist "%TARGET%\%%F" copy /Y "%TARGET%\%%F" "%BACKUP%\%%F" >nul
)
if exist "%TARGET%\manifest.txt" copy /Y "%TARGET%\manifest.txt" "%BACKUP%\manifest.txt" >nul

echo [5/6] Installo i moduli validati...
for /f "usebackq delims=" %%F in ("%TMP%\files.txt") do (
    copy /Y "%TMP%\%%F" "%TARGET%\%%F" >nul
    if errorlevel 1 goto :install_error
)
copy /Y "%TMP%\manifest.txt" "%TARGET%\manifest.txt" >nul

if exist "%TARGET%\__pycache__" rmdir /S /Q "%TARGET%\__pycache__" >nul 2>&1

echo [6/6] Verifica finale...
findstr /C:"VERSION = \"0.4.0-beta.5\"" "%TARGET%\solidflow_beta5.py" >nul || goto :install_error
findstr /C:"solidflow_beta5.install()" "%TARGET%\InitGui.py" >nul || goto :install_error

rmdir /S /Q "%TMP%" >nul 2>&1

echo.
echo ================================================================
echo  AGGIORNAMENTO COMPLETATO
echo ================================================================
echo.
echo Backup automatico:
echo %BACKUP%
echo.
echo Da ora questo stesso UPDATE_SOLIDFLOW.bat puo' essere riutilizzato
echo per le versioni successive: legge automaticamente il manifest GitHub.
echo.
echo Avvia FreeCAD e verifica:
echo   1. tasto S
echo   2. menu SolidFlow ^> Fillet Doctor...
echo   3. menu SolidFlow ^> Rivoluzione+...
echo   4. pulsante Ombre vicino agli stili di visualizzazione
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
echo [ERRORE] Non riesco a creare il backup. Aggiornamento annullato.
goto :fail

:install_error
echo.
echo [ERRORE] Installazione incompleta.
echo Il backup e' disponibile in:
echo %BACKUP%
echo.
echo Puoi ripristinare i file da quella cartella.
goto :fail

:fail
if exist "%TMP%" rmdir /S /Q "%TMP%" >nul 2>&1
echo.
pause
exit /b 1
