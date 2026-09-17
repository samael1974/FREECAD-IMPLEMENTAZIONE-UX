param(
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $root 'SolidFlowUX'
$manifest = Join-Path $runtimeDir 'manifest.txt'
$iss = Join-Path $root 'installer\SolidFlowUX.iss'

Write-Host '============================================================'
Write-Host ' SolidFlow UX - Controllo sorgenti'
Write-Host '============================================================'

if (-not (Test-Path $manifest)) { throw "Manifest mancante: $manifest" }
if (-not (Test-Path $iss)) { throw "Progetto installer mancante: $iss" }

$files = Get-Content $manifest |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ -and -not $_.StartsWith('#') }

if (-not $files) { throw 'Il manifest è vuoto.' }

$missing = @()
foreach ($file in $files) {
    $path = Join-Path $runtimeDir $file
    if (-not (Test-Path $path)) { $missing += $file }
}

if ($missing.Count -gt 0) {
    Write-Host ''
    Write-Host '[ERRORE] File runtime mancanti:' -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" }
    exit 10
}

Write-Host "[OK] Runtime completo: $($files.Count) file elencati nel manifest."

$pythonCandidates = @(
    (Join-Path $env:ProgramFiles 'FreeCAD 1.1\bin\python.exe'),
    (Join-Path $env:ProgramFiles 'FreeCAD 1.1\bin\python3.exe')
)

$python = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python) {
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}
if (-not $python) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}

if ($python) {
    Write-Host "[INFO] Python: $python"
    foreach ($file in ($files | Where-Object { $_.EndsWith('.py') })) {
        $path = Join-Path $runtimeDir $file
        & $python -m py_compile $path
        if ($LASTEXITCODE -ne 0) { throw "Errore di sintassi Python: $file" }
    }
    Write-Host '[OK] Sintassi Python valida.'
} else {
    $msg = '[AVVISO] Python non trovato: controllo sintassi saltato.'
    if ($Strict) { throw $msg }
    Write-Host $msg -ForegroundColor Yellow
}

$issText = Get-Content $iss -Raw
$notPackaged = @()
foreach ($file in $files) {
    if ($file -eq 'manifest.txt') { continue }
    $needle = 'SolidFlowUX\' + $file
    if ($issText -notmatch [regex]::Escape($needle)) {
        $notPackaged += $file
    }
}
if ($notPackaged.Count -gt 0) {
    Write-Host '[AVVISO] File nel manifest non trovati esplicitamente nel progetto installer:' -ForegroundColor Yellow
    $notPackaged | ForEach-Object { Write-Host "  - $_" }
    if ($Strict) { exit 11 }
} else {
    Write-Host '[OK] File runtime coerenti con il progetto installer.'
}

Write-Host ''
Write-Host 'CONTROLLO COMPLETATO: nessun file è stato installato o modificato.' -ForegroundColor Green
exit 0
