param([ValidateSet('codex', 'claude')][string]$Platform = 'codex')
python (Join-Path $PSScriptRoot 'install.py') --platform $Platform
