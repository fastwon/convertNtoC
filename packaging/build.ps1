# Build convertN2C.exe — run from the repo root in PowerShell:
#   .\packaging\build.ps1
#
# Produces dist\convertN2C.exe (single windowed exe). Requires the .venv with
# dev deps installed:  .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host '== 1/2  Building React static assets ==' -ForegroundColor Cyan
Push-Location frontend
npm install
npm run build
Pop-Location

Write-Host '== 2/2  Packaging with PyInstaller ==' -ForegroundColor Cyan
& .\.venv\Scripts\pyinstaller.exe packaging/convertN2C.spec --noconfirm --clean

Write-Host ''
Write-Host 'Done → dist\convertN2C.exe' -ForegroundColor Green
Write-Host 'Double-click it, or run:  .\dist\convertN2C.exe'
