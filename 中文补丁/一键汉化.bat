@echo off
chcp 65001 >nul
setlocal
rem 一键汉化入口：自动定位同目录下的构建脚本，任意路径解压均可使用。
cd /d "%~dp0patch\脚本"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [错误] 未检测到 Python。请先安装 Python 3.8 或更高版本，
  echo        安装第一页务必勾选 "Add Python to PATH"，然后重跑本脚本。
  echo        下载地址 https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

echo 正在启动 Sparrow 中文汉化构建器 ...
python build.py %*
echo.
pause
