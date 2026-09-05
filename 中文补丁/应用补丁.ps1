# Sparrow 2.5.4 中文补丁 —— 应用补丁脚本

# 用法：右键“使用 PowerShell 运行”，或：powershell -ExecutionPolicy Bypass -File "应用补丁.ps1"

# 作用：将本目录 patch\modules.patched 安装到 Sparrow 安装目录，并自动备份原版镜像。

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$sparrowRoot = Split-Path -Parent $root                     # Sparrow 程序根目录

$runtimeModules = Join-Path $sparrowRoot "runtime\lib\modules"

$backupDir = Join-Path $root "backup"

$patchFile = Join-Path $root "patch\modules.patched"

# 0) 前置检查

if (-not (Test-Path $runtimeModules)) { Write-Host "[错误] 找不到 $runtimeModules，请检查 Sparrow 安装路径。" -ForegroundColor Red; exit 1 }

if (-not (Test-Path $patchFile))      { Write-Host "[错误] 找不到补丁文件 $patchFile" -ForegroundColor Red; exit 1 }

# 1) 备份原版（仅当 backup 中还没有原始镜像时备份）

if (-not (Test-Path (Join-Path $backupDir "modules.original"))) {

    New-Item -ItemType Directory -Force $backupDir | Out-Null

    Copy-Item $runtimeModules (Join-Path $backupDir "modules.original") -Force

    Write-Host "[备份] 已保存原始镜像 -> backup\modules.original"

} else {

    Write-Host "[备份] backup\modules.original 已存在，跳过备份。"

}

# 2) 结束正在运行的 Sparrow（否则镜像文件被占用无法替换）

$procs = Get-Process | Where-Object { $_.ProcessName -match "^Sparrow$" -or $_.ProcessName -eq "javaw" }

if ($procs) {

    $procs | Stop-Process -Force

    Write-Host "[关闭] 已结束 Sparrow 进程，等待文件释放..."

    Start-Sleep -Seconds 2

}

# 3) 应用补丁

Copy-Item $patchFile $runtimeModules -Force

$hash = (Get-FileHash $runtimeModules -Algorithm SHA256).Hash

Write-Host "[完成] 中文补丁已安装。" -ForegroundColor Green

Write-Host "       新镜像 SHA256: $hash"

Write-Host "       现在可以启动 Sparrow.exe 查看中文界面。"
