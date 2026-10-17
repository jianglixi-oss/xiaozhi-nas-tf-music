# Dot-source this file: . .\enter-idf.ps1
$musicWorkspace = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path Q:\)) {
    subst Q: $musicWorkspace
    if ($LASTEXITCODE -ne 0) { throw 'Unable to map workspace to Q: for Windows short paths.' }
}
if (-not (Test-Path Q:\esp-idf-v6.1\export.ps1)) {
    throw 'Q: is in use by another directory. Select a free drive and update this script.'
}
$env:IDF_TOOLS_PATH = 'Q:\esp-tools'
$env:IDF_COMPONENT_CACHE_PATH = 'Q:\component-cache'
$env:CMAKE_NINJA_FORCE_RESPONSE_FILE = '1'
. Q:\esp-idf-v6.1\export.ps1
Set-Location $PSScriptRoot
