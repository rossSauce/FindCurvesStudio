# Builds the FindCurves Studio Windows executable and installer.
#
#   powershell -ExecutionPolicy Bypass -File build.ps1
#
# Steps:
#   1. creates .venv (Python 3.14 via the py launcher) if it does not exist
#   2. installs requirements.txt and PyInstaller
#   3. builds dist\FindCurves\FindCurves.exe with PyInstaller
#   4. if Inno Setup 6 is installed, builds installer\Output\FindCurves-Studio-<ver>-Setup.exe

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path .venv\Scripts\python.exe)) {
    py -3.14 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the virtual environment (is Python 3.14 installed?)' }
}
$python = Resolve-Path .venv\Scripts\python.exe

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }

& $python -m PyInstaller --noconfirm --clean FindCurves.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
Write-Host "Built dist\FindCurves\FindCurves.exe"

$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($iscc) {
    & $iscc installer\FindCurves.iss
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup build failed' }
    Write-Host "Built installer in installer\Output"
} else {
    Write-Warning 'Inno Setup 6 not found - skipping installer. Install it with: winget install JRSoftware.InnoSetup'
}
