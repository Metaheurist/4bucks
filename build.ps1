# Build 4Bucks - Windows onefile EXE via flet pack (x64 and/or x86)
param(
    [switch]$SkipChecks,
    [ValidateSet('All', 'x64', 'x86')]
    [string]$Arch = 'All',
    [string]$PythonX64 = '',
    [string]$PythonX86 = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Test-PythonArch {
    param([string]$PythonExe, [ValidateSet('x64', 'x86')][string]$Expected)
    $bits = & $PythonExe -c "import struct; print(struct.calcsize('P') * 8)"
    if ($LASTEXITCODE -ne 0) { throw "Failed to probe arch: $PythonExe" }
    $want = if ($Expected -eq 'x64') { '64' } else { '32' }
    if ($bits.Trim() -ne $want) {
        throw "Python at $PythonExe is $($bits.Trim())-bit; need $want-bit for $Expected"
    }
}

function Resolve-PythonX64 {
    if ($PythonX64) { return $PythonX64 }
    $venvPy = Join-Path $root '.venv\Scripts\python.exe'
    if (Test-Path $venvPy) { return $venvPy }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw 'No 64-bit Python found. Install Python 3.11+ x64 or pass -PythonX64'
}

function Resolve-PythonX86 {
    if ($PythonX86) { return $PythonX86 }
    $venvPy = Join-Path $root '.venv-x86\Scripts\python.exe'
    if (Test-Path $venvPy) { return $venvPy }

    $candidates = @(
        "${env:LOCALAPPDATA}\Programs\Python\Python311-32\python.exe",
        "${env:LOCALAPPDATA}\Programs\Python\Python312-32\python.exe",
        "${env:LOCALAPPDATA}\Programs\Python\Python313-32\python.exe",
        "${env:ProgramFiles(x86)}\Python311-32\python.exe",
        "${env:ProgramFiles(x86)}\Python312-32\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $probe = & py -3.11-32 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $probe) { return $probe.Trim() }
        $probe = & py -3-32 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $probe) { return $probe.Trim() }
    }

    throw @'
No 32-bit Python found. Install Python 3.11 x86 from python.org, or pass -PythonX86.
PyInstaller bitness matches the interpreter - a 64-bit Python cannot produce a 32-bit EXE.
'@
}

function Ensure-Venv {
    param([string]$VenvDir, [string]$BootstrapPython)
    $venvPython = Join-Path $VenvDir 'Scripts\python.exe'
    if (-not (Test-Path $venvPython)) {
        Write-Host "Creating venv $VenvDir ..."
        & $BootstrapPython -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) { throw "venv failed: $VenvDir" }
    }
    return $venvPython
}

function Ensure-Icon {
    param([string]$PythonExe)
    $ico = Join-Path $root 'assets\icon.ico'
    $png = Join-Path $root 'assets\icon.png'
    if (Test-Path $ico) { return }
    if (-not (Test-Path $png)) { throw 'Missing assets\icon.png and icon.ico' }
    Write-Host 'Generating icon.ico from icon.png ...'
    & $PythonExe -c @"
from pathlib import Path
from PIL import Image
src = Path(r'$png')
img = Image.open(src).convert('RGBA')
img.save(Path(r'$ico'), format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('ok')
"@
    if ($LASTEXITCODE -ne 0) { throw 'icon.ico generation failed' }
}

function Install-Deps {
    param([string]$PythonExe)
    & $PythonExe -m pip install --upgrade pip -q
    if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
    & $PythonExe -m pip install -r requirements.txt -r requirements-dev.txt -q
    if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }
}

function Invoke-Checks {
    param([string]$PythonExe)
    Write-Host 'Running unit tests ...'
    & $PythonExe -m pytest tests/unit -q
    if ($LASTEXITCODE -ne 0) { throw 'pytest failed' }

    Write-Host 'Running pip-audit ...'
    & $PythonExe -m pip_audit -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'pip-audit failed on requirements.txt' }
    & $PythonExe -m pip_audit -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw 'pip-audit failed on requirements-dev.txt' }
}

function Build-One {
    param(
        [ValidateSet('x64', 'x86')][string]$TargetArch,
        [string]$PythonExe
    )
    Test-PythonArch -PythonExe $PythonExe -Expected $TargetArch
    $scriptsDir = Split-Path $PythonExe
    $flet = Join-Path $scriptsDir 'flet.exe'
    if (-not (Test-Path $flet)) {
        Write-Host 'Installing flet-cli ...'
        & $PythonExe -m pip install 'flet-cli==1.0.1' -q
        if ($LASTEXITCODE -ne 0) { throw 'flet-cli install failed' }
    }
    if (-not (Test-Path $flet)) { throw "flet.exe not found next to $PythonExe" }

    $name = "Save4Bucks-$TargetArch"
    $icon = Join-Path $root 'assets\icon.ico'
    # Pack into a per-arch folder so a later arch build does not wipe siblings in dist/.
    $archDist = Join-Path $root "dist\$TargetArch"
    if (Test-Path $archDist) { Remove-Item -Recurse -Force $archDist }
    New-Item -ItemType Directory -Force -Path $archDist | Out-Null

    # Bundle menu SVG icons (and window icon PNG) into the onefile EXE.
    $menuIcons = Join-Path $root 'assets\menu'
    $addData = @(
        "$menuIcons;assets/menu",
        "$(Join-Path $root 'assets\icon.png');assets"
    )

    Write-Host "Running flet pack ($TargetArch) -> $name ..."
    & $flet pack (Join-Path $root 'save4bucks.py') `
        -n $name `
        -i $icon `
        --distpath $archDist `
        -y `
        --product-name '4Bucks' `
        --file-description 'GTA IV CE offline PlayerInfo save editor' `
        --add-data $addData[0] `
        --add-data $addData[1] `
        --hidden-import src `
        --hidden-import src.app `
        --hidden-import src.detect `
        --hidden-import src.save_money `
        --hidden-import src.save_weapons `
        --hidden-import src.save_vitality `
        --hidden-import src.playerinfo `
        --hidden-import src.weapons_catalog `
        --hidden-import src.weapon_detect `
        --hidden-import src.versioning `
        --hidden-import src.backup `
        --hidden-import src.settings
    if ($LASTEXITCODE -ne 0) { throw "flet pack failed for $TargetArch" }

    $built = Join-Path $archDist "$name.exe"
    if (-not (Test-Path $built)) { throw "Build failed: $built not found" }

    $distRoot = Join-Path $root 'dist'
    New-Item -ItemType Directory -Force -Path $distRoot | Out-Null
    $exe = Join-Path $distRoot "$name.exe"
    Copy-Item -Force $built $exe
    Write-Host "Built: $exe"
    Get-Item $exe | Format-List Name, Length, LastWriteTime
}

$targets = if ($Arch -eq 'All') { @('x64', 'x86') } else { @($Arch) }

# Resolve / prepare interpreters
$pyForChecks = $null
if ($targets -contains 'x64') {
    $boot64 = Resolve-PythonX64
    Test-PythonArch -PythonExe $boot64 -Expected 'x64'
    if ($boot64 -like '*\.venv\Scripts\python.exe') {
        $script:Py64 = $boot64
    }
    else {
        $script:Py64 = Ensure-Venv -VenvDir (Join-Path $root '.venv') -BootstrapPython $boot64
    }
    Install-Deps -PythonExe $script:Py64
    $pyForChecks = $script:Py64
}
if ($targets -contains 'x86') {
    $boot86 = Resolve-PythonX86
    Test-PythonArch -PythonExe $boot86 -Expected 'x86'
    if ($boot86 -like '*\.venv-x86\Scripts\python.exe') {
        $script:Py86 = $boot86
    }
    else {
        $script:Py86 = Ensure-Venv -VenvDir (Join-Path $root '.venv-x86') -BootstrapPython $boot86
    }
    Install-Deps -PythonExe $script:Py86
    if (-not $pyForChecks) { $pyForChecks = $script:Py86 }
}

if (-not $SkipChecks) {
    Invoke-Checks -PythonExe $pyForChecks
}

Ensure-Icon -PythonExe $pyForChecks

if ($targets -contains 'x64') { Build-One -TargetArch 'x64' -PythonExe $script:Py64 }
if ($targets -contains 'x86') { Build-One -TargetArch 'x86' -PythonExe $script:Py86 }

Write-Host 'Done.'
