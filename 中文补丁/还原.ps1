# Sparrow 2.5.4 中文补丁 —— 还原原版脚本

# 用法：右键“使用 PowerShell 运行”，或：powershell -ExecutionPolicy Bypass -File "还原.ps1"

# 作用：用 backup\modules.original 恢复 Sparrow 原始英文界面。

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$sparrowRoot = Split-Path -Parent $root                     # Sparrow 程序根目录

$runtimeModules = Join-Path $sparrowRoot "runtime\lib\modules"

$original = Join-Path $root "backup\modules.original"

if (-not (Test-Path $original)) {

    Write-Host "[错误] 找不到备份 backup\modules.original，无法还原。" -ForegroundColor Red

    exit 1

}

# 结束正在运行的 Sparrow

$procs = Get-Process | Where-Object { $_.ProcessName -match "^Sparrow$" -or $_.ProcessName -eq "javaw" }

if ($procs) {

    $procs | Stop-Process -Force

    Write-Host "[关闭] 已结束 Sparrow 进程，等待文件释放..."

    Start-Sleep -Seconds 2

}

Copy-Item $original $runtimeModules -Force

$hash = (Get-FileHash $runtimeModules -Algorithm SHA256).Hash

Write-Host "[完成] 已还原为原始英文界面。" -ForegroundColor Green

Write-Host "       还原后镜像 SHA256: $hash"

Write-Host "       如需再次汉化，运行 应用补丁.ps1 即可。"
