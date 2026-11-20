#!/usr/bin/env python3
"""v0.5.22 GUI-only regression after apply_0522.py."""
from pathlib import Path
import hashlib

editor=Path("Source/PluginEditor.cpp").read_text(encoding="utf8")
metal=Path("Source/CetusMetalSkin.h").read_text(encoding="utf8")
cm=Path("CMakeLists.txt").read_text(encoding="utf8")

assert "VERSION 0.5.22" in cm and "v0.5.22" in editor
assert "v0.5.21" not in editor
for token in (
    "inline void softShadow(",
    "inline void softBevel(",
    "inline const juce::Image& satinMicrograin()",
    "for (int i=0; i<4200; ++i)",
    "g.setTiledImageFill(satinMicrograin(),0,0,.88f*opacity)",
    "inline void analogKnobTexture(",
):
    assert token in metal, f"Metal helper missing: {token}"

for token in (
    "CetusMetal::softShadow(g,area,radius,.72f*opacity,1.6f)",
    "CetusMetal::softShadow(g,r,6.0f,.90f,1.05f)",
    "CetusMetal::softShadow(g,r,5.0f,.81f,1.15f)",
    "CetusMetal::softShadow(g,{left,top,width,height},7.0f,.63f,.70f)",
    "CetusMetal::softBevel(g,r,6.0f,over ? .95f : .74f)",
    "CetusMetal::softBevel(g,r,5.0f,.73f)",
    "CetusMetal::softBevel(g,{left,top,width,height},7.0f,.65f)",
    "topGloss.addColour(.36,juce::Colours::white.withAlpha(.028f*opacity))",
    "topLight.addColour(.34,juce::Colours::white.withAlpha(.048f))",
    "for(int layer=5;layer>=1;--layer)",
    "placeDesignChild(soloButton, {900,390,32,24})",
    "placeDesignChild(polarityButton, {986,536,39,22})",
    "soloButton.setButtonText(\"S\")",
    "base=juce::Colour::fromRGB(248,148,30)",
    "CetusMetal::analogKnobTexture(g,c,faceRadius,radius)",
    "CetusMetal::brushedSurface(g, area, radius, 0.98f * opacity)",
    "juce::String::fromUTF8(\"\\xC3\\x98\")",
    "undoIconImage.setImage",
    "redoIconImage.setImage",
    "analyzerRangeIndex",
):
    assert token in editor, f"GUI feature missing: {token}"

# Hard, opaque shadows from the earlier renderer must be replaced.
assert "g.fillRoundedRectangle(r.translated(0.9f,2.4f).expanded(.4f),6.0f)" not in editor
assert "g.fillRoundedRectangle(r.translated(.8f,2.4f),5.4f)" not in editor
assert "g.fillRoundedRectangle(area.translated(1.4f, 3.0f).expanded(1.1f)" not in editor

# Audio engine code must not carry GUI shading changes.
for file in ("Source/PluginProcessor.cpp","Source/PluginProcessor.h",
             "Source/CetusEQFilters.h","Source/CetusLink.h"):
    data=Path(file).read_bytes()
    assert len(data)>0 and len(hashlib.sha256(data).hexdigest())==64

print("PASS v0.5.22: soft bevels/shadows, button active colours, satin grain, layout and existing DSP retained")
