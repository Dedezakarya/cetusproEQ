$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
cmake -S . -B build-win -G 'Visual Studio 17 2022' -A x64
if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed' }
cmake --build build-win --config Release --target cetusproEQ_VST3 --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
Get-ChildItem build-win/cetusproEQ_artefacts -Recurse -Directory -Filter '*.vst3' | Select-Object -ExpandProperty FullName
