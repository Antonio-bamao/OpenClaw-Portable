param(
  [string]$OpenClawVersion = "2026.4.8",
  [string]$NpmExe = "npm.cmd",
  [string]$NodeExe = "node",
  [switch]$SkipInstall,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runtimeRoot = Join-Path $root "runtime"
$openclawRuntime = Join-Path $runtimeRoot "openclaw"
$workRoot = Join-Path $root "tmp\\prepare-openclaw-runtime"
$packDir = Join-Path $workRoot "pack"
$expandedDir = Join-Path $workRoot "expanded"
$tgzName = "openclaw-$OpenClawVersion.tgz"
$tgzPath = Join-Path $packDir $tgzName

function Resolve-CommandPath {
  param([string]$Command)
  $resolved = Get-Command $Command -ErrorAction SilentlyContinue
  if (-not $resolved) {
    throw "Required command not found: $Command"
  }
  return $resolved.Source
}

if ((Test-Path $openclawRuntime) -and -not $Force) {
  throw "runtime\\openclaw already exists. Pass -Force to replace it."
}

$npmPath = Resolve-CommandPath $NpmExe
$nodePath = Resolve-CommandPath $NodeExe

if (Test-Path $workRoot) {
  Remove-Item -LiteralPath $workRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $packDir, $expandedDir, $runtimeRoot | Out-Null

Write-Host "Downloading openclaw@$OpenClawVersion from npm..."
& $npmPath pack "openclaw@$OpenClawVersion" --pack-destination $packDir

if (-not (Test-Path $tgzPath)) {
  throw "Expected npm pack output not found: $tgzPath"
}

Write-Host "Expanding npm package..."
tar -xzf $tgzPath -C $expandedDir
$packageDir = Join-Path $expandedDir "package"
if (-not (Test-Path (Join-Path $packageDir "openclaw.mjs"))) {
  throw "Expanded package is missing openclaw.mjs"
}
if (-not (Test-Path (Join-Path $packageDir "dist\\entry.js"))) {
  throw "Expanded package is missing dist\\entry.js. This is not a built runtime package."
}

if (Test-Path $openclawRuntime) {
  Remove-Item -LiteralPath $openclawRuntime -Recurse -Force
}
Move-Item -LiteralPath $packageDir -Destination $openclawRuntime

if (-not $SkipInstall) {
  Write-Host "Installing production dependencies in runtime\\openclaw..."
  Push-Location $openclawRuntime
  try {
    & $npmPath install --omit=dev
  }
  finally {
    Pop-Location
  }
}

Write-Host "Verifying OpenClaw runtime..."
& $nodePath (Join-Path $openclawRuntime "openclaw.mjs") --version
& $nodePath (Join-Path $openclawRuntime "openclaw.mjs") gateway --help | Out-Null

Write-Host "OpenClaw runtime prepared at $openclawRuntime"
