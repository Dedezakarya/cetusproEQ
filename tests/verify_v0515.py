#!/usr/bin/env python3
"""Regression checks for cetusproEQ v0.5.15 after all source patches."""
from pathlib import Path
import hashlib
cpp=Path("Source/PluginEditor.cpp").read_text(encoding="utf8")
hpp=Path("Source/PluginEditor.h").read_text(encoding="utf8")
cm=Path("CMakeLists.txt").read_text(encoding="utf8")
assert "VERSION 0.5.15" in cm and "v0.5.15" in cpp
assert 'smoothButton {"1/6 Oct"}' in hpp
assert "holdMs = 150, smoothingMode = 1;" in hpp
for name in [
    "juce::Colour::fromRGB(182,177,201).withAlpha(.53f)",
    "shade.addColour(.35,juce::Colour::fromRGB(175,171,193).withAlpha(.35f))",
    "g.setGradientFill(shade);g.fillPath(fill);",
    "g.setColour(white.withAlpha(.68f));g.strokePath(trace",
    "placeDesignChild(holdButton,             {340,536,88,23});",
    "placeDesignChild(smoothButton,           {434,536,84,23});",
    "placeDesignChild(analyzerRangeButton,    {524,536,86,23});",
    "placeDesignChild(analyzerTiltButton,     {616,536,74,23});",
    "placeDesignChild(analyzerReferenceButton,{696,536,82,23});",
    'g.drawText("dBFS"', "hannWeightSum",
    "analyzerRangeIndex", "analyzerReferenceIndex","analyzerTiltIndex",
    "undoIconImage.setImage(", "redoIconImage.setImage(",
    "CetusEQ::makeCoefficients",
]:
    assert name in cpp, "Missing or changed GUI feature: "+name
# Ensure distinct, non-overlapping compact buttons.
rects=[(340,88),(434,84),(524,86),(616,74),(696,82)]
assert all(rects[i][0]+rects[i][1]<=rects[i+1][0] for i in range(len(rects)-1))
assert rects[-1][0]+rects[-1][1]<839
expected={
    "Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}
for path,sha in expected.items():
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert actual==sha, f"DSP changed in {path}"
print("PASS v0.5.15: shaded spectrum, compact buttons, 1/6 Oct default, preserved analyzer and DSP")
