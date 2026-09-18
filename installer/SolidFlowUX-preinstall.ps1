param(
    [Parameter(Mandatory = $true)]
    [string]$TargetDirectory
)

$ErrorActionPreference = 'Stop'
$target = [System.IO.Path]::GetFullPath($TargetDirectory).TrimEnd('\', '/')
$mod = Split-Path -Parent $target
$profile = Split-Path -Parent $mod
if ((Split-Path -Leaf $target) -ne 'SolidFlowUX' -or (Split-Path -Leaf $mod) -ne 'Mod') {
    throw 'Destinazione non valida: deve terminare con Mod\SolidFlowUX.'
}

foreach ($path in @($mod, $target)) {
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path -Force
        if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Destinazione non supportata (file o collegamento): $path"
        }
    }
}

# Use the actual wizard destination, including custom/portable profiles.
# Do not move an unrelated non-versioned installation: it may serve another FreeCAD.
New-Item -ItemType Directory -Path $profile -Force | Out-Null
$probe = Join-Path $profile ('.solidflow-write-' + [guid]::NewGuid().ToString('N'))
try {
    [System.IO.File]::WriteAllText($probe, 'write-check')
} finally {
    if (Test-Path -LiteralPath $probe) { Remove-Item -LiteralPath $probe -Force }
}

if (Test-Path -LiteralPath $target) {
    $backupRoot = Join-Path $profile 'SolidFlowUX_Backups'
    if (Test-Path -LiteralPath $backupRoot) {
        $backupItem = Get-Item -LiteralPath $backupRoot -Force
        if (-not $backupItem.PSIsContainer -or ($backupItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Cartella backup non valida.'
        }
    }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $backupDir = Join-Path $backupRoot ('before_beta13_' + $stamp + '_' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    # Copy before the Inno install phase. A failure propagates and stops the setup.
    Get-ChildItem -LiteralPath $target -Force |
        Where-Object { $_.Name -notin @('__pycache__', '_backup') } |
        ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $backupDir -Recurse -Force }
    Write-Output "Backup completato: $backupDir"
}
exit 0
