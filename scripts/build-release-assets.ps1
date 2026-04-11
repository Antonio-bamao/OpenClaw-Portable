param(
  [string]$PythonExe = "python",
  [string]$Repository = "Antonio-bamao/OpenClaw-Portable",
  [string]$SigningPrivateKeyPath = "",
  [string[]]$Note = @()
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$packageRoot = Join-Path $root "dist\\OpenClaw-Portable"
$outputDir = Join-Path $root "dist\\release"
if (-not $SigningPrivateKeyPath) {
  $SigningPrivateKeyPath = Join-Path $root ".local\\update-signing-private-key.txt"
}

& (Join-Path $root "scripts\\build-launcher.ps1") -PythonExe $PythonExe
& $PythonExe (Join-Path $root "scripts\\sign-update-manifest.py") `
  --package-root $packageRoot `
  --private-key-path $SigningPrivateKeyPath

$command = @(
  (Join-Path $root "scripts\\build-release-assets.py"),
  "--package-root", $packageRoot,
  "--output-dir", $outputDir,
  "--repository", $Repository
)
foreach ($item in $Note) {
  $command += @("--note", $item)
}

& $PythonExe @command
