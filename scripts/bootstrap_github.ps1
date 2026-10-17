# Run in a Windows PowerShell terminal on your own authenticated computer.
param([string]$Name = 'universe')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw 'GitHub CLI not found. Install from https://cli.github.com and run gh auth login.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw 'Git is not installed; install Git for Windows.'
}
& gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Authenticate interactively using gh auth login first.' }
if (-not (Test-Path '.git')) {
  & git init -b main
  if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
}
& git add -A
if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
$changed = & git status --porcelain
if ($changed) {
  & git commit -m 'Baseline: Universe V0 R0.3 with collaborative review gates'
  if ($LASTEXITCODE -ne 0) { throw 'Commit failed. Configure git user.name and user.email and retry.' }
}
$remotes = @(& git remote)
if ($remotes -contains 'origin') { throw 'Origin remote already exists. Not modifying it; review git remote -v.' }
& gh repo create $Name --private --source=. --remote=origin --push --description 'Evidence-driven persistent digital universe for independent agents'
if ($LASTEXITCODE -ne 0) { throw 'GitHub repo creation or push failed.' }
Write-Host 'Private repository created; next follow docs/GITHUB_SETUP.md for protections and model credentials.'
