param(
    [switch]$SkipCheck
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$check = Join-Path $root 'CHECK_SOURCE.ps1'
$iss = Join-Path $root 'installer\SolidFlowUX.iss'
$dist = Join-Path $root 'dist'

Write-Host '============================================================'
Write-Host ' SolidFlow UX - Build installer locale'
Write-Host '============================================================'

if (-not $SkipCheck) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $check -Strict
    if ($LASTEXITCODE -ne 0) {
        throw "CHECK_SOURCE.ps1 non superato (codice $LASTEXITCODE)."
    }
}

$isccCandidates = @(
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe'
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    Write-Host ''
    Write-Host '[ERRORE] Inno Setup 6 non è installato.' -ForegroundColor Red
    Write-Host 'Installa Inno Setup 6, poi riesegui questo script.'
    exit 20
}

if (-not (Test-Path $iss)) { throw "File installer mancante: $iss" }

if (Test-Path $dist) {
    Get-ChildItem $dist -Filter 'SolidFlowUX-Setup-v*.exe' -ErrorAction SilentlyContinue | Remove-Item -Force
    Remove-Item (Join-Path $dist 'SHA256SUMS.txt') -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $dist | Out-Null
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3.11 richiesto per preparare il pacchetto tester.' }
& $python.Source (Join-Path $root 'tools\build_tester_package.py')
if ($LASTEXITCODE -ne 0) { throw 'Preparazione pacchetto tester fallita.' }

Write-Host "[INFO] Compilatore: $iscc"
& $iscc $iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup ha restituito codice $LASTEXITCODE." }

$exe = Get-ChildItem $dist -Filter 'SolidFlowUX-Setup-v*.exe' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $exe) { throw 'Installer EXE non trovato dopo la compilazione.' }

$hash = (Get-FileHash $exe.FullName -Algorithm SHA256).Hash.ToLower()
$checksum = "$hash  $($exe.Name)"
$checksum | Set-Content -Encoding ascii (Join-Path $dist 'SHA256SUMS.txt')

Write-Host ''
Write-Host 'BUILD COMPLETATA' -ForegroundColor Green
Write-Host "EXE:    $($exe.FullName)"
Write-Host "SHA256: $hash"
Write-Host ''
Write-Host 'Nessuna installazione è stata eseguita automaticamente.'
