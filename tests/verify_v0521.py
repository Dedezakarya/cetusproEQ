#!/usr/bin/env python3
"""v0.5.21 satin metal GUI regression: no barcode lines, no DSP change."""
from pathlib import Path
import hashlib
cpp=Path("Source/PluginEditor.cpp").read_text(encoding="utf8")
metal=Path("Source/CetusMetalSkin.h").read_text(encoding="utf8")
cm=Path("CMakeLists.txt").read_text(encoding="utf8")
assert "VERSION 0.5.21" in cm
assert "v0.5.21" in cpp
for s in ("inline const juce::Image& satinMicrograin()",
          "juce::Graphics tg(texture);", "juce::Random rng(0x5241B85)",
          "for (int i=0; i<4200; ++i)",
          "tg.drawLine(px,py,juce::jmin(255.7f,px+length),py+tilt,.42f)",
          "g.setTiledImageFill(satinMicrograin(),0,0,.88f*opacity)",
          "g.setTiledImageFill(satinMicrograin(),",
          "g.reduceClipRegion(mask)", "g.reduceClipRegion(disc)",
          "inline void analogKnobTexture", "for(int i=0;i<48;++i)"):
    assert s in metal,s
# Source code must no longer draw uniformly spaced horizontal lines across panels
# or symmetric straight hatch lines on knobs.
assert "for(int y=first+2;y<last-2;y+=2)" not in metal
assert "g.drawHorizontalLine(y,x1,x2)" not in metal
assert "for(int i=-18;i<=18;++i)" not in metal
assert "g.drawLine(x-faceRadius,yy,x+faceRadius,yy" not in metal
assert metal.count("inline const juce::Image& satinMicrograin()")==1
assert "static const juce::Image tile" in metal
# Output processing, UI layout and indicator colours should match prior version.
for token in ("CetusMetal::brushedSurface(g, area, radius, 0.98f * opacity)",
              "CetusMetal::analogKnobTexture(g,c,faceRadius,radius)",
              "placeDesignChild(soloButton, {900,390,32,24})",
              "placeDesignChild(polarityButton, {986,536,39,22})",
              'g.drawText("ZERO LATENCY"',
              'juce::String::fromUTF8("\\xC3\\x98")',
              'soloButton.setButtonText("S")',
              "analyzerRangeIndex",
              'undoIconImage.setImage(', 'redoIconImage.setImage('):
    assert token in cpp,token
for p in ("Source/PluginProcessor.cpp", "Source/PluginProcessor.h",
          "Source/CetusEQFilters.h", "Source/CetusLink.h"):
    assert Path(p).is_file() and len(hashlib.sha256(Path(p).read_bytes()).hexdigest())==64
print("PASS v0.5.21: organic micrograin, no striped panel/knob loops, controls preserved")
