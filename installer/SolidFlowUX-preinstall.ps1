$ErrorActionPreference = 'Stop'

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$target = Join-Path $env:APPDATA 'FreeCAD\v1-1\Mod\SolidFlowUX'
$legacy = Join-Path $env:APPDATA 'FreeCAD\Mod\SolidFlowUX'
$backupRoot = Join-Path $env:APPDATA 'FreeCAD\SolidFlowUX_Backups'
$legacyBackupRoot = Join-Path $env:APPDATA 'FreeCAD\SolidFlowUX_Legacy_Backups'

# Backup the currently active v1-1 installation before Inno overwrites it.
if (Test-Path -LiteralPath $target) {
    $backupDir = Join-Path $backupRoot ("before_beta10_r2_" + $stamp)
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

    Get-ChildItem -LiteralPath $target -Force |
        Where-Object { $_.Name -notin @('__pycache__', '_backup') } |
        ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $backupDir -Recurse -Force
        }
}

# A non-versioned FreeCAD\Mod copy can cause duplicate SolidFlow loading.
# Move it outside Mod, preserving it as a safety backup instead of deleting it.
if (Test-Path -LiteralPath $legacy) {
    New-Item -ItemType Directory -Path $legacyBackupRoot -Force | Out-Null
    $legacyDestination = Join-Path $legacyBackupRoot ("SolidFlowUX_" + $stamp)
    Move-Item -LiteralPath $legacy -Destination $legacyDestination
}

exit 0
