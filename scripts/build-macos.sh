#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S . -B build-mac -G Xcode \
  -DCMAKE_OSX_ARCHITECTURES='x86_64;arm64' \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
cmake --build build-mac --config Release --target cetusproEQ_VST3 cetusproEQ_AU --parallel 4
printf '\nBuild finished. Look for .vst3/.component in build-mac/cetusproEQ_artefacts/Release\n'
find build-mac/cetusproEQ_artefacts -type d \( -name '*.vst3' -o -name '*.component' \) -print
