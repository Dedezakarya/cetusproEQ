#!/usr/bin/env python3
"""v0.5.19 GUI regression. The audio DSP is intentionally unchanged."""
from pathlib import Path
cpp=Path("Source/PluginEditor.cpp").read_text(encoding="utf8")
hpp=Path("Source/PluginEditor.h").read_text(encoding="utf8")
cm=Path("CMakeLists.txt").read_text(encoding="utf8")
assert "VERSION 0.5.19" in cm
assert "v0.5.19" in cpp
for t in (
    'placeDesignChild(detectorMode, {790,388,104,28})',
    'placeDesignChild(soloButton, {900,390,32,24})',
    'soloButton.setComponentID("cetus-solo")',
    'soloButton.setButtonText("S")',
    'button.getComponentID()=="cetus-solo"',
    'if(id=="cetus-solo")',
    'g.drawText("S",button.getLocalBounds(),juce::Justification::centred)',
    'base=juce::Colour::fromRGB(248,148,30)',
    'const bool thisBandIsSolo=audibleBand==selectedBand+1',
    'soloButton.setToggleState(thisBandIsSolo,juce::dontSendNotification)',
    'processor.setParameterActual("soloBand"',
    'placeDesignChild(polarityButton, {986,536,39,22})',
):
    assert t in cpp,t
assert 'juce::TextButton soloButton {"S"}' in hpp
assert 'placeDesignChild(soloButton, {86,382,43,21})' not in cpp
assert 'soloButton.setButtonText(audibleBand' not in cpp
# The dropdown, S button, and Output area must not overlap.
combo_x,combo_w=790,104
solo_x,solo_w=900,32
output_x=962
assert combo_x+combo_w<solo_x
assert solo_x+solo_w<output_x
assert solo_w<=36 and solo_x>=894
for t in ('BinaryData::CetusUndo_png','BinaryData::CetusRedo_png',
          'juce::String::fromUTF8("\\xC3\\x98")',
          'g.drawText("ZERO LATENCY"','analyzerRangeIndex','ratioButton',
          'kneeButton'):
    assert t in cpp,t
# Audio parameters are registered in the processor implementation.
# The processor header holds processing members, not parameter ID literals.
content=Path("Source/PluginProcessor.cpp").read_text(encoding="utf8")
assert 'juce::ParameterID("soloBand",1)' in content
assert 'juce::ParameterID("polarity",1)' in content
assert "renderBandAudition" in content
print("PASS v0.5.19: non-overlapping Detector Mode/S placement, orange-on S, solo and Ø features preserved")
