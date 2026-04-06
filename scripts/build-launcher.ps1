param(
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pyiDist = Join-Path $root "dist\\pyinstaller"
$portableDist = Join-Path $root "dist\\OpenClaw-Portable"
$buildDir = Join-Path $root "build\\pyinstaller"

if (Test-Path $pyiDist) { Remove-Item -Recurse -Force $pyiDist }
if (Test-Path $portableDist) { Remove-Item -Recurse -Force $portableDist }
if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }

& $PythonExe -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onedir `
  --name OpenClawLauncher `
  --distpath $pyiDist `
  --workpath $buildDir `
  (Join-Path $root "main.py")

New-Item -ItemType Directory -Force -Path $portableDist | Out-Null
Copy-Item (Join-Path $pyiDist "OpenClawLauncher\\*") $portableDist -Recurse -Force
Copy-Item (Join-Path $root "runtime") $portableDist -Recurse -Force
Copy-Item (Join-Path $root "assets") $portableDist -Recurse -Force
Copy-Item (Join-Path $root "tools") $portableDist -Recurse -Force
Copy-Item (Join-Path $root "README.txt") $portableDist -Force
Copy-Item (Join-Path $root "version.json") $portableDist -Force
Copy-Item (Join-Path $root "state\\provider-templates") (Join-Path $portableDist "state\\provider-templates") -Recurse -Force
