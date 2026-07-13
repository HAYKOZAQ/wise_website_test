# Install a Windows Scheduled Task: daily MLSA corpus re-ingest
# Run in PowerShell (preferably as Administrator):
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\install_scheduled_reingest.ps1
#   .\install_scheduled_reingest.ps1 -Hour 3 -Force
#   .\install_scheduled_reingest.ps1 -Uninstall

param(
    [int]$Hour = 3,
    [int]$Minute = 15,
    [switch]$Force,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$TaskName = "WISE-MLSA-Reingest"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) {
    Write-Error "python not found on PATH"
}

$Args = "`"$Root\backend\reingest.py`""
if ($Force) { $Args = "$Args --force" }

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    $modePath = Join-Path $Root "backend\data\reingest_mode.json"
    New-Item -ItemType Directory -Force -Path (Split-Path $modePath) | Out-Null
    Set-Content -Path $modePath -Value '{"mode":"inprocess"}' -Encoding UTF8
    Write-Host "Removed scheduled task: $TaskName"
    Write-Host "Re-ingest mode reset to inprocess (use start_backend.bat REINGEST_INTERVAL_HOURS=24)"
    exit 0
}

$Action = New-ScheduledTaskAction -Execute $Python -Argument $Args -WorkingDirectory "$Root\backend"
$Trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date -Hour $Hour -Minute $Minute -Second 0)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null

# Single schedule: disable in-process scheduler while Windows task is active
$modePath = Join-Path $Root "backend\data\reingest_mode.json"
New-Item -ItemType Directory -Force -Path (Split-Path $modePath) | Out-Null
Set-Content -Path $modePath -Value '{"mode":"windows","note":"In-process REINGEST_INTERVAL_HOURS ignored while mode=windows"}' -Encoding UTF8

Write-Host "Installed scheduled task: $TaskName"
Write-Host "  Runs daily at ${Hour}:$('{0:D2}' -f $Minute)"
Write-Host "  Command: $Python $Args"
Write-Host "  WorkingDirectory: $Root\backend"
Write-Host ""
Write-Host "IMPORTANT: reingest_mode.json set to windows — API will NOT also run in-process schedule."
Write-Host "To switch back to in-process only: .\install_scheduled_reingest.ps1 -Uninstall"
Write-Host "  then start_backend.bat (REINGEST_MODE=inprocess, REINGEST_INTERVAL_HOURS=24)"
Write-Host ""
Write-Host "After the task runs, if the API is already up, reload the index:"
Write-Host "  curl -X POST http://127.0.0.1:8000/api/admin/reload"
