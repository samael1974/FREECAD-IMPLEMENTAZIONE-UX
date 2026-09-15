@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

title SolidFlow UX - Aggiornatore automatico

set "TARGET=%APPDATA%\FreeCAD\v1-1\Mod\SolidFlowUX"
set "LEGACY=%APPDATA%\FreeCAD\Mod\SolidFlowUX"
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

if exist "%LEGACY%" (
    echo [AVVISO] Esiste anche la vecchia cartella non versionata:
    echo %LEGACY%
    echo SolidFlow usera' come destinazione SOLO la cartella v1-1 indicata sopra.
    echo Se la copia legacy non serve piu', potrai archiviarla dopo i test.
    echo.
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

rem Validate the bootstrap and every beta layer listed by the manifest.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $tmp='%TMP%';" ^
  "$init=Get-Content -Raw ($tmp+'\InitGui.py');" ^
  "if(-not $init.Contains('plain ``S`` key is intentionally owned only')){throw 'Bootstrap SolidFlow non riconosciuto'};" ^
  "$files=Get-Content ($tmp+'\files.txt') ^| ForEach-Object {$_.Trim()} ^| Where-Object {$_};" ^
  "foreach($f in $files){ if($f -like 'solidflow_beta*.py'){ $text=Get-Content -Raw ($tmp+'\'+$f); if(-not $text.Contains('VERSION =')){throw 'Versione mancante in '+$f}; $module=[IO.Path]::GetFileNameWithoutExtension($f); $needle='_load_layer(\"'+$module+'\")'; if(-not $init.Contains($needle)){throw 'InitGui non carica '+$module} } }"
if errorlevel 1 goto :validation_error

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
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $target='%TARGET%';" ^
  "$init=Get-Content -Raw ($target+'\InitGui.py'); $files=Get-Content ($target+'\manifest.txt') ^| ForEach-Object {$_.Trim()} ^| Where-Object {$_ -and -not $_.StartsWith('#')};" ^
  "foreach($f in $files){ if(-not (Test-Path ($target+'\'+$f))){throw 'File installato mancante: '+$f}; if($f -like 'solidflow_beta*.py'){ $module=[IO.Path]::GetFileNameWithoutExtension($f); if(-not $init.Contains('_load_layer(\"'+$module+'\")')){throw 'Layer non registrato: '+$module} } }"
if errorlevel 1 goto :install_error

rmdir /S /Q "%TMP%" >nul 2>&1

echo.
echo ================================================================
echo  AGGIORNAMENTO COMPLETATO
echo ================================================================
echo.
echo Backup automatico:
echo %BACKUP%
echo.
echo Questo stesso UPDATE_SOLIDFLOW.bat e' pensato per essere riutilizzato:
echo legge automaticamente il manifest GitHub e valida i layer elencati.
echo.
echo Avvia FreeCAD e verifica per primi:
echo   1. tasto S
echo   2. SolidFlow ^> Feature avanzate ^> Sweep / Loft / Elica
echo   3. Thread Wizard su una faccia cilindrica con asse Z
echo   4. SolidFlow ^> Fillet Doctor... sul problema del raccordo
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
