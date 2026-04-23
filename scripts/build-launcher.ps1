param(
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pyiDist = Join-Path $root "dist\\pyinstaller"
$portableDist = Join-Path $root "dist\\OpenClaw-Portable"
$buildDir = Join-Path $root "build\\pyinstaller"
$nodeRuntime = Join-Path $root "runtime\\node\\node.exe"
$openclawRuntime = Join-Path $root "runtime\\openclaw\\openclaw.mjs"
$iconIco = Join-Path $root "assets\\app-icon.ico"

function Assert-PathInsideRoot {
  param([string]$Path)
  $rootPath = (Resolve-Path -LiteralPath $root).Path
  $resolvedPath = (Resolve-Path -LiteralPath $Path).Path
  if (-not $resolvedPath.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside project root: $resolvedPath"
  }
}

function Remove-DirectoryRobust {
  param([string]$Path)
  if (-not (Test-Path $Path)) {
    return
  }
  Assert-PathInsideRoot $Path
  $emptyDir = Join-Path $root "tmp\\robocopy-empty"
  if (Test-Path $emptyDir) {
    Remove-Item -LiteralPath $emptyDir -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path $emptyDir | Out-Null
  robocopy $emptyDir $Path /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed while cleaning $Path with exit code $LASTEXITCODE"
  }
  Remove-Item -LiteralPath $Path -Recurse -Force
  Remove-Item -LiteralPath $emptyDir -Recurse -Force
}

function Copy-DirectoryRobust {
  param(
    [string]$Source,
    [string]$Destination
  )
  New-Item -ItemType Directory -Force -Path $Destination | Out-Null
  robocopy $Source $Destination /E /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed while copying $Source to $Destination with exit code $LASTEXITCODE"
  }
}

Remove-DirectoryRobust $pyiDist
Remove-DirectoryRobust $portableDist
Remove-DirectoryRobust $buildDir

if (-not (Test-Path $openclawRuntime)) {
  throw "Missing runtime\\openclaw. Run scripts\\prepare-openclaw-runtime.ps1 before building the portable package."
}
if (-not (Test-Path $nodeRuntime)) {
  throw "Missing runtime\\node\\node.exe. Run scripts\\prepare-node-runtime.ps1 before building the portable package."
}

$pyInstallerArgs = @(
  "-m", "PyInstaller",
  "--noconfirm",
  "--clean",
  "--windowed",
  "--onedir",
  "--hidden-import", "_cffi_backend",
  "--name", "OpenClawLauncher",
  "--distpath", $pyiDist,
  "--workpath", $buildDir
)
if (Test-Path $iconIco) {
  $pyInstallerArgs += @("--icon", $iconIco)
}
$pyInstallerArgs += (Join-Path $root "main.py")

& $PythonExe @pyInstallerArgs

New-Item -ItemType Directory -Force -Path $portableDist | Out-Null
Copy-Item (Join-Path $pyiDist "OpenClawLauncher\\*") $portableDist -Recurse -Force
Copy-DirectoryRobust (Join-Path $root "runtime") (Join-Path $portableDist "runtime")
Copy-DirectoryRobust (Join-Path $root "assets") (Join-Path $portableDist "assets")
Copy-DirectoryRobust (Join-Path $root "tools") (Join-Path $portableDist "tools")
Copy-Item (Join-Path $root "README.txt") $portableDist -Force
Copy-Item (Join-Path $root "version.json") $portableDist -Force
Copy-DirectoryRobust (Join-Path $root "state\\provider-templates") (Join-Path $portableDist "state\\provider-templates")
& $PythonExe (Join-Path $root "scripts\\prune-portable-runtime.py") --runtime-path (Join-Path $portableDist "runtime\\openclaw")
& $PythonExe (Join-Path $root "scripts\\generate-update-manifest.py") --package-root $portableDist
