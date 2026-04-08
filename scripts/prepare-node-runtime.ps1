param(
  [string]$NodeExe = "node",
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$nodeRuntime = Join-Path $root "runtime\node"
$targetNode = Join-Path $nodeRuntime "node.exe"
$versionFile = Join-Path $nodeRuntime "VERSION.txt"

function Resolve-CommandPath {
  param([string]$Command)
  $resolved = Get-Command $Command -ErrorAction SilentlyContinue
  if (-not $resolved) {
    throw "Required command not found: $Command"
  }
  return $resolved.Source
}

if ((Test-Path $targetNode) -and -not $Force) {
  throw "runtime\node\node.exe already exists. Pass -Force to replace it."
}

$sourceNode = Resolve-CommandPath $NodeExe
$nodeVersion = (& $sourceNode --version).Trim()
if (-not $nodeVersion.StartsWith("v24.")) {
  throw "Node 24 is required for the bundled portable runtime. Found $nodeVersion at $sourceNode."
}

New-Item -ItemType Directory -Force -Path $nodeRuntime | Out-Null
Copy-Item -LiteralPath $sourceNode -Destination $targetNode -Force
Set-Content -Path $versionFile -Value $nodeVersion -Encoding UTF8

Write-Host "Bundled Node runtime prepared at $targetNode"
Write-Host "Version: $nodeVersion"
