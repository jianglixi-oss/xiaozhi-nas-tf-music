$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\enter-idf.ps1"
python scripts/build.py waveshare/esp32-s3-audio-board --name esp32-s3-audio-board-music --zip
if ($LASTEXITCODE -ne 0) { throw "Firmware build failed ($LASTEXITCODE)." }
