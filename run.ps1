$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Run the installation steps in README.md first.'
}
& $pythonPath -m typr @args
exit $LASTEXITCODE
