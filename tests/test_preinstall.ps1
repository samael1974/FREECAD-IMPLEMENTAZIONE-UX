$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $root 'installer\SolidFlowUX-preinstall.ps1'
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('solidflow-test-' + [guid]::NewGuid().ToString('N'))
$target = Join-Path $testRoot 'custom profile\Mod\SolidFlowUX'
try {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -TargetDirectory $target
    if ($LASTEXITCODE -ne 0) { throw 'Fresh profile check failed' }
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Set-Content (Join-Path $target 'InitGui.py') 'original'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -TargetDirectory $target
    if ($LASTEXITCODE -ne 0) { throw 'Custom profile backup failed' }
    $backups = @(Get-ChildItem (Join-Path $testRoot 'custom profile\SolidFlowUX_Backups') -Directory)
    if ($backups.Count -ne 1) { throw 'Backup was not created in the selected profile' }
    if ((Get-Content (Join-Path $backups[0].FullName 'InitGui.py')) -ne 'original') { throw 'Wrong backup contents' }
    Remove-Item (Join-Path $testRoot 'custom profile\SolidFlowUX_Backups') -Recurse -Force
    Set-Content (Join-Path $testRoot 'custom profile\SolidFlowUX_Backups') 'blocking file'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -TargetDirectory $target
    if ($LASTEXITCODE -eq 0) { throw 'Backup failure did not propagate' }
    if ((Get-Content (Join-Path $target 'InitGui.py')) -ne 'original') { throw 'Failed backup changed original files' }
    Write-Host 'PASS: profile selection, backup contents and backup failure propagation.'
} finally {
    if (Test-Path $testRoot) { Remove-Item $testRoot -Recurse -Force }
}

exit 0
