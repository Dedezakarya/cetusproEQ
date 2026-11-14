#!/usr/bin/env python3
"""v0.5.14 regression tests: display calibration only, audio DSP unchanged."""
from pathlib import Path
import hashlib,math,cmath
cpp=Path("Source/PluginEditor.cpp").read_text()
hpp=Path("Source/PluginEditor.h").read_text()
cm=Path("CMakeLists.txt").read_text()
assert "VERSION 0.5.14" in cm and "v0.5.14" in cpp
for text in [
    "spectrumDb.fill(-96.0f);",
    "hannWeightSum",
    "const float factor=2.0f/hannWeightSum;",
    'g.drawText("dBFS"',
    "const float displayDb = dB + tiltDbPerOct",
    "const int spectrumAxisX = plot.getRight()+4;",
    "analyzerRangeIndex==1 ? 90.0f",
    "analyzerReferenceIndex==0 ? 0.0f",
    "analyzerTiltIndex==0 ? 0.0f",
    "undoIconImage.setImage",
    "redoIconImage.setImage"
]:
    assert text in cpp, f"Missing GUI feature {text}"
for text in ["analyzerRangeButton","analyzerTiltButton","analyzerReferenceButton",
             "analyzerRangeIndex = 1","analyzerReferenceIndex = 0",
             "analyzerTiltIndex = 0"]:
    assert text in hpp,f"Missing GUI control {text}"

# Reference: full-scale sinusoidal peak amplitude 1 is 0 dBFS at a centred
# DFT bin with a symmetric Hann window. This tests the proposed coherent
# gain normalization, not a substitute for testing DAW behavior.
N=4096
sumw=0.0
spec=0j
amplitude=0.5
k=128
for n in range(N):
    w=0.5*(1-math.cos(2*math.pi*n/(N-1)))
    value=amplitude*math.sin(2*math.pi*k*n/N)
    spec+=w*value*cmath.exp(-2j*math.pi*k*n/N)
    sumw+=w
computed=20*math.log10(2*abs(spec)/sumw)
expected=20*math.log10(amplitude)
assert abs(computed-expected)<0.02, f"Hann calibration error: {computed} vs {expected}"

expected_dsp={
"Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
"Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
"Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
"Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc"}
for f,sha in expected_dsp.items():
    actual=hashlib.sha256(Path(f).read_bytes()).hexdigest()
    assert actual==sha,f"DSP was changed: {f}"
print(f"v0.5.14 regression PASS: FFT 0.5FS reference {computed:.3f} dBFS, independent scale, controls, immutable DSP")
