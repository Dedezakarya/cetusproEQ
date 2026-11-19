#!/usr/bin/env python3
"""v0.5.19: move Solo to the right of Detector Mode and use compact orange S.
GUI-only, applied after apply_0518.py; never edits the audio DSP.
"""
from pathlib import Path
import hashlib

editor = Path("Source/PluginEditor.cpp")
header = Path("Source/PluginEditor.h")
cm = Path("CMakeLists.txt")
dsp_paths = [Path("Source/PluginProcessor.cpp"),
             Path("Source/PluginProcessor.h"),
             Path("Source/CetusEQFilters.h"),
             Path("Source/CetusLink.h")]
original_dsp = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in dsp_paths}
cpp=editor.read_text(encoding="utf8")
hpp=header.read_text(encoding="utf8")

def swap_once(text,old,new,reason):
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f"{reason}: expected one anchor, found {count}: {old[:125]!r}")
    return text.replace(old,new,1)

# User-marked slot is the right side of the DETECTOR MODE dropdown.
# Shorten that dropdown to leave the arrow intact and fit a separate S.
cpp=swap_once(cpp,
    '    placeDesignChild(detectorMode, {790,388,142,28});',
    '    placeDesignChild(detectorMode, {790,388,104,28});',
    "Shrink Detector Mode dropdown without covering its arrow")
cpp=swap_once(cpp,
    '    placeDesignChild(soloButton, {86,382,43,21});',
    '    placeDesignChild(soloButton, {900,390,32,24});',
    "Place Solo in red-marked right area, 6px gap from dropdown")

# Letter S only, no band number and no word SOLO.
hpp=swap_once(hpp,
    '    juce::TextButton soloButton {"SOLO"};',
    '    juce::TextButton soloButton {"S"};',
    "Compact S label on first paint")
cpp=swap_once(cpp,
    '''    soloButton.setTooltip("Audition only the selected band's frequency range. Click again to return to full EQ.");''',
    '''    soloButton.setComponentID("cetus-solo");
    soloButton.setTooltip("Band Solo: listen to the selected band. Click again to turn off.");''',
    "Explicit solo-only component ID for look-and-feel")

cpp=swap_once(cpp,
    '''    soloButton.setButtonText(audibleBand>0
        ? ("S"+juce::String(audibleBand)) : "SOLO");''',
    '''    soloButton.setButtonText("S");''',
    "S label stays unchanged as band selection changes")

# Existing normal graphite button style when inactive; orange when active.
cpp=swap_once(cpp,
    '''    } else if(selected && button.getComponentID()=="cetus-polarity") {
        base=juce::Colour::fromRGB(248,148,30);''',
    '''    } else if(selected && (button.getComponentID()=="cetus-polarity"
                            || button.getComponentID()=="cetus-solo")) {
        base=juce::Colour::fromRGB(248,148,30);''',
    "Orange Solo active, normal graphite inactive")

# Existing specialized drawButtonText routes all 'cetus-*' IDs through icon
# rendering. Add a dedicated letter-S path rather than falling into arrows.
cpp=swap_once(cpp,
    '''    if(id.isEmpty() || !id.startsWith("cetus-")) {''',
    '''    if(id=="cetus-solo") {
        g.setColour(button.getToggleState() ? juce::Colours::black
                                             : juce::Colour::fromRGB(224,237,244));
        g.setFont(juce::FontOptions(15.0f,juce::Font::bold));
        g.drawText("S",button.getLocalBounds(),juce::Justification::centred);
        return;
    }
    if(id.isEmpty() || !id.startsWith("cetus-")) {''',
    "Paint a single bold S, not Undo/Redo arrow art")

# Keep the v0.5.18 processing and automatable soloBand unchanged.
for token in ('processor.setParameterActual("soloBand"',
              'const bool thisBandIsSolo=audibleBand==selectedBand+1',
              'soloButton.setToggleState(thisBandIsSolo,juce::dontSendNotification)',
              'BinaryData::CetusUndo_png','BinaryData::CetusRedo_png',
              'placeDesignChild(polarityButton, {986,536,39,22})'):
    if token not in cpp:raise RuntimeError("Previous feature missing: "+token)
assert cpp.count("v0.5.18")>=2
cpp=cpp.replace("v0.5.18","v0.5.19")
configuration=cm.read_text(encoding="utf8")
assert configuration.count("VERSION 0.5.18")==1
configuration=configuration.replace("VERSION 0.5.18","VERSION 0.5.19",1)

editor.write_text(cpp,encoding="utf8")
header.write_text(hpp,encoding="utf8")
cm.write_text(configuration,encoding="utf8")
for p in dsp_paths:
    if hashlib.sha256(p.read_bytes()).hexdigest()!=original_dsp[str(p)]:
        raise RuntimeError("GUI-only build changed audio DSP file "+str(p))
print("v0.5.19 S moved beside Detector Mode, bold glyph, orange ON/graphite OFF; v0.5.18 DSP identical")
