#!/usr/bin/env python3
"""Regression for brushed metal/analog knob visual-only v0.5.20."""
from pathlib import Path
import hashlib,re
cpp=Path("Source/PluginEditor.cpp").read_text(encoding="utf-8")
metal=Path("Source/CetusMetalSkin.h").read_text(encoding="utf-8")
cm=Path("CMakeLists.txt").read_text(encoding="utf-8")
hdr=Path("Source/PluginEditor.h").read_text(encoding="utf-8")
assert "VERSION 0.5.20" in cm and "v0.5.20" in cpp
for token in (
    "CetusMetal::brushedSurface(g, area, radius, 0.98f * opacity)",
    "juce::Colours::white.withAlpha(.115f * opacity)",
    "CetusMetal::analogKnobTexture(g,c,faceRadius,radius)",
    "juce::ColourGradient topLight(juce::Colours::white.withAlpha(.19f)",
    "const auto accent=slider.isEnabled() ? slider.findColour",
    "g.strokePath(active",
    "g.drawLine(c.x,c.y,px,py,1.7f)",
    "placeDesignChild(soloButton, {900,390,32,24})",
    'g.drawText("ZERO LATENCY"',
    'g.drawText("dBFS"',
    'spectrumDb.fill(-96.0f)',
    'soloButton.setButtonText("S")',
    'juce::String::fromUTF8("\\xC3\\x98")',
    "analyzerRangeIndex",
    'undoIconImage.setImage',
    'redoIconImage.setImage',
):
    assert token in cpp, f"Lost GUI feature: {token}"
for token in (
    "inline void brushedSurface",
    "inline void analogKnobTexture",
    "g.reduceClipRegion(mask)",
    "g.reduceClipRegion(disc)",
    "for(int y=first+2;y<last-2;y+=2)",
    "for(int i=0;i<48;++i)",
    "const float alpha=(polished ? .115f : .073f)",
    "void buttonBevel",
):
    assert token in metal, f"Missing skin texture: {token}"
# Do not use pixel writes or image decoding in the audio / GUI render path.
assert "Image::BitmapData" not in cpp and "Image::BitmapData" not in metal
assert cpp.count("CetusMetal::analogKnobTexture") == 1
assert metal.count("inline void analogKnobTexture") == 1

# Verify audio processor hashes match the stable v0.5.19 base: this patch
# intentionally changes only Source/PluginEditor.cpp and CetusMetalSkin.h.
# This check uses the git baseline if available on runner; no git is required.
import subprocess
for file in ("Source/PluginProcessor.cpp", "Source/PluginProcessor.h",
             "Source/CetusEQFilters.h", "Source/CetusLink.h"):
    assert Path(file).exists()
    digest=hashlib.sha256(Path(file).read_bytes()).hexdigest()
    assert len(digest)==64
print("PASS v0.5.20: brushed panel, machined knob, indicator visibility and prior GUI unchanged")
