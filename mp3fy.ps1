[CmdletBinding()]
param()

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) {
    $scriptDir = $PSScriptRoot
}

$pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
$mainPy = Join-Path $scriptDir "main.py"

if (Test-Path $pythonExe) {
    & $pythonExe $mainPy @args
} else {
    & python $mainPy @args
}
exit $LASTEXITCODE
