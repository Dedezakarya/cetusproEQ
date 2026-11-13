#!/usr/bin/env python3
"""v0.5.13 GUI regression contract: preserve the prior host/DSP/API compatibility."""
from pathlib import Path
import hashlib

source=Path("Source/PluginEditor.cpp").read_text(encoding="utf-8")
header=Path("Source/PluginEditor.h").read_text(encoding="utf-8")
cm=Path("CMakeLists.txt").read_text(encoding="utf-8")
assert "VERSION 0.5.13" in cm
assert "v0.5.13" in source
assert "0.70710678f" in source
assert "newType == 3 || newType == 4" in source
assert "spectrumAt(juce::jmap(fraction,lowBin,highBin))" in source
assert "const float p = juce::jlimit(1.0f,maxBin-0.001f,position)" in source
assert "spectrumDb[i] += (db-spectrumDb[i])*0.52f" in source
assert "CetusEQ::makeCoefficients(sr,freq,q,gain,type)" in source
assert "CetusEQ::makeCoefficients(sr,freq,q,gain+dynamicOffset,type)" in source
assert "coeff->getMagnitudeForFrequency" in source
assert "CetusEQ::stageCountForTypeAndSlope" in source
assert "baseDb+=magnitudeDb(baseFilters" in source
assert "nowDb+=magnitudeDb(activeFilters" in source
assert "processor.isBandDynamicEnabled(i)" in source
assert "juce::ImageComponent undoIconImage" in header
assert "juce::ImageComponent" in header and "redoIconImage" in header
assert "undoIconImage.setImage" in source and "redoIconImage.setImage" in source
assert Path("assets/CetusUndo.png").exists() and Path("assets/CetusRedo.png").exists()
for filename, expected in {
    "PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}.items():
    actual=hashlib.sha256(Path("Source",filename).read_bytes()).hexdigest()
    assert actual==expected,f"DSP changed {filename} {actual}"
print("PASS: v0.5.13 version, HP/LP Q, interpolated smoothed FFT, coefficient response, original assets, immutable DSP")
