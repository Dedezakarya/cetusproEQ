#!/usr/bin/env python3
"""cetusproEQ v0.5.16: move ZERO LATENCY under the left BANDS grid.
GUI-only; DSP and analyzer remain exactly as v0.5.15.
Run after ci-source/apply_0515.py.
"""
from pathlib import Path
import hashlib
p=Path("Source/PluginEditor.cpp")
src=p.read_text(encoding="utf8")
old='g.drawText("ZERO LATENCY",558,541,102,14,juce::Justification::centredLeft);'
new=('g.drawText("ZERO LATENCY",lower.getX()+6,lower.getBottom()-31,110,14,'
     'juce::Justification::centred);')
if src.count(old)!=1:raise RuntimeError("Expected exactly one ZERO LATENCY GUI text")
assert "void CetusproEQAudioProcessorEditor::drawBottom(juce::Graphics& g)" in src
src=src.replace(old,new,1)
assert src.count(new)==1
assert "smoothingMode" in src
assert src.count("v0.5.15")>=2
src=src.replace("v0.5.15","v0.5.16")
cm=Path("CMakeLists.txt")
config=cm.read_text(encoding="utf8")
assert config.count("VERSION 0.5.15")==1
config=config.replace("VERSION 0.5.15","VERSION 0.5.16",1)
expected={
    "Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}
for path,sha in expected.items():
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual!=sha: raise RuntimeError("DSP changed: "+path)
p.write_text(src,encoding="utf8")
cm.write_text(config,encoding="utf8")
print("v0.5.16 label centered under BANDS grid (x=20..130, y=535..549); untouched DSP")
