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

function Invoke-Native {
  param(
    [string]$Command,
    [string[]]$Arguments
  )
  & $Command @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$Command failed with exit code $LASTEXITCODE"
  }
}

function Assert-OpenClawRuntimeManifest {
  param([string]$RuntimePath)
  $manifestPath = Join-Path $RuntimePath "package.json"
  $pluginRuntime = Join-Path $RuntimePath "dist\\plugins\\runtime\\index.js"
  if (-not (Test-Path $manifestPath)) {
    throw "Packaged OpenClaw runtime is missing package.json: $manifestPath"
  }
  if (-not (Test-Path $pluginRuntime)) {
    throw "Packaged OpenClaw runtime is missing plugin runtime module: $pluginRuntime"
  }
  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  $exports = $manifest.exports
  $hasPluginSdkEntry = $false
  $hasCliEntry = $false
  if ($exports) {
    $exportNames = $exports.PSObject.Properties.Name
    $hasPluginSdkEntry = $exportNames -contains "./plugin-sdk"
    $hasCliEntry = $exportNames -contains "./cli-entry"
  }
  $hasOpenClawBin = $false
  if ($manifest.bin) {
    if ($manifest.bin -is [string]) {
      $hasOpenClawBin = $manifest.bin -like "*openclaw*"
    } else {
      $hasOpenClawBin = ($manifest.bin.PSObject.Properties.Name -contains "openclaw")
    }
  }
  if (-not ($hasPluginSdkEntry -and ($hasCliEntry -or $hasOpenClawBin))) {
    throw "Packaged OpenClaw runtime package.json is incomplete; plugin runtime discovery would fail."
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

Invoke-Native $PythonExe $pyInstallerArgs

New-Item -ItemType Directory -Force -Path $portableDist | Out-Null
Copy-Item (Join-Path $pyiDist "OpenClawLauncher\\*") $portableDist -Recurse -Force
Copy-DirectoryRobust (Join-Path $root "runtime") (Join-Path $portableDist "runtime")
Copy-DirectoryRobust (Join-Path $root "assets") (Join-Path $portableDist "assets")
Copy-DirectoryRobust (Join-Path $root "tools") (Join-Path $portableDist "tools")
Copy-Item (Join-Path $root "README.txt") $portableDist -Force
Copy-Item (Join-Path $root "version.json") $portableDist -Force
Copy-DirectoryRobust (Join-Path $root "state\\provider-templates") (Join-Path $portableDist "state\\provider-templates")

Write-Host "Downloading @openclaw/feishu plugin for portable bundle..."
$feishuExtDir = Join-Path $portableDist "runtime\\openclaw\\dist\\extensions\\feishu"
New-Item -ItemType Directory -Force -Path $feishuExtDir | Out-Null
$previousLocation = Get-Location
Set-Location $feishuExtDir
Invoke-Native "npm" @("pack", "@openclaw/feishu@latest")
$tarball = Get-ChildItem -Filter "*.tgz" | Select-Object -First 1
if ($tarball) {
    tar -xf $tarball.Name
    Copy-Item "package\\*" -Destination "." -Recurse -Force
    Remove-Item "package" -Recurse -Force
    Remove-Item $tarball.Name -Force
}
Set-Location $previousLocation

Invoke-Native $PythonExe @((Join-Path $root "scripts\\prune-portable-runtime.py"), "--runtime-path", (Join-Path $portableDist "runtime\\openclaw"))
Copy-Item (Join-Path $root "runtime\\openclaw\\package.json") (Join-Path $portableDist "runtime\\openclaw\\package.json") -Force
Assert-OpenClawRuntimeManifest (Join-Path $portableDist "runtime\\openclaw")
Invoke-Native $PythonExe @((Join-Path $root "scripts\\generate-update-manifest.py"), "--package-root", $portableDist)
