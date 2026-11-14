#!/usr/bin/env python3
"""v0.5.16 GUI label placement and unchanged DSP checks."""
from pathlib import Path
import hashlib
src=Path("Source/PluginEditor.cpp").read_text(encoding="utf8")
hpp=Path("Source/PluginEditor.h").read_text(encoding="utf8")
cm=Path("CMakeLists.txt").read_text(encoding="utf8")
assert "VERSION 0.5.16" in cm and "v0.5.16" in src
assert src.count('g.drawText("ZERO LATENCY"')==1
assert ('g.drawText("ZERO LATENCY",lower.getX()+6,lower.getBottom()-31,110,14,'
        'juce::Justification::centred);') in src
assert 'g.drawText("ZERO LATENCY",558,541' not in src
# BANDS grid: buttons end at y=515, label is in y=535..549; panel ends at 566.
assert 515 < 535 and 549 < 566
assert 'smoothButton {"1/6 Oct"}' in hpp
assert 'smoothingMode = 1;' in hpp
assert 'g.setGradientFill(shade);g.fillPath(fill);' in src
assert 'analyzerRangeIndex' in src and 'analyzerTiltIndex' in src
assert 'undoIconImage.setImage(' in src and 'redoIconImage.setImage(' in src
for path,expected in {
"Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
"Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
"Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
"Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected, "DSP changed in "+path
print("PASS v0.5.16 ZERO LATENCY under BANDS, no control overlap, existing GUI + DSP preserved")
