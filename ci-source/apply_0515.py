#!/usr/bin/env python3
"""v0.5.15: GUI-only filled spectrum, compact analyzer buttons, 1/6 octave default.
Runs immediately after apply_0514.py. All DSP files and parameter IDs unchanged.
"""
from pathlib import Path
import hashlib
editor=Path("Source/PluginEditor.cpp")
header=Path("Source/PluginEditor.h")
cm=Path("CMakeLists.txt")
cpp=editor.read_text(encoding="utf8")
hpp=header.read_text(encoding="utf8")
def swap(old,new,where="CPP"):
    global cpp,hpp
    original=cpp if where=="CPP" else hpp
    count=original.count(old)
    if count!=1:
        raise RuntimeError(f"{where}: expected one exact anchor; found {count}: {old[:130]!r}")
    result=original.replace(old,new,1)
    if where=="CPP": cpp=result
    else: hpp=result

# Keep smoothing user-selectable; only the initial GUI selection is 1/6 Oct.
swap('smoothButton {"1/3 Oct"}','smoothButton {"1/6 Oct"}',"HPP")
swap('holdMs = 150, smoothingMode = 2;', 'holdMs = 150, smoothingMode = 1;',"HPP")

# Visible filled spectrum (Pro-Q-like translucent neutral/violet shading).
# Existing trace/path and dBFS mapping remain identical; fill is purely GUI.
swap(
    '''        juce::ColourGradient shade(juce::Colour::fromRGB(82,190,244).withAlpha(.16f),plot.getCentreX(),(float)plot.getY(),
                                   cyan.withAlpha(.02f),plot.getCentreX(),(float)plot.getBottom(),false);
        shade.addColour(.44,ice.withAlpha(.08f));
        shade.addColour(.80,juce::Colour::fromRGB(38,119,168).withAlpha(.03f));
        g.setGradientFill(shade);g.fillPath(fill);
        g.setColour(cyan.withAlpha(.05f));g.strokePath(trace,juce::PathStrokeType(4.2f));
        g.setColour(ice.withAlpha(.18f));g.strokePath(trace,juce::PathStrokeType(1.8f));
        g.setColour(white.withAlpha(.44f));g.strokePath(trace,juce::PathStrokeType(1.0f));''',
    '''        // Spectrum has a clearly visible translucent area fill distinct from
        // the cyan/white outline and the EQ response curves; no DSP changes.
        juce::ColourGradient shade(
            juce::Colour::fromRGB(182,177,201).withAlpha(.53f),
            plot.getCentreX(),(float)plot.getY(),
            juce::Colour::fromRGB(122,123,151).withAlpha(.11f),
            plot.getCentreX(),(float)plot.getBottom(),false);
        shade.addColour(.35,juce::Colour::fromRGB(175,171,193).withAlpha(.35f));
        shade.addColour(.73,juce::Colour::fromRGB(135,145,171).withAlpha(.19f));
        g.setGradientFill(shade);g.fillPath(fill);
        g.setColour(cyan.withAlpha(.10f));g.strokePath(trace,juce::PathStrokeType(3.3f));
        g.setColour(ice.withAlpha(.40f));g.strokePath(trace,juce::PathStrokeType(1.65f));
        g.setColour(white.withAlpha(.68f));g.strokePath(trace,juce::PathStrokeType(.95f));''',
    "CPP"
)

# Compact button group with consistent 6px horizontal gaps.
swap('''    placeDesignChild(holdButton, {340,536,106,23});
    placeDesignChild(smoothButton,{453,536, 92,23});
    placeDesignChild(analyzerRangeButton, {553,536,104,23});
    placeDesignChild(analyzerTiltButton, {663,536,91,23});
    placeDesignChild(analyzerReferenceButton, {760,536,104,23});''',
    '''    placeDesignChild(holdButton,             {340,536,88,23});
    placeDesignChild(smoothButton,           {434,536,84,23});
    placeDesignChild(analyzerRangeButton,    {524,536,86,23});
    placeDesignChild(analyzerTiltButton,     {616,536,74,23});
    placeDesignChild(analyzerReferenceButton,{696,536,82,23});''')

# Only update product metadata and GUI footer, not plugin IDs or audio params.
assert cpp.count("v0.5.14")>=2
cpp=cpp.replace("v0.5.14","v0.5.15")
cmdata=cm.read_text(encoding="utf8")
assert cmdata.count("VERSION 0.5.14")==1
cmdata=cmdata.replace("VERSION 0.5.14","VERSION 0.5.15",1)

# Validate all previously built GUI components are still present.
for token in ["undoIconImage.setImage(", "redoIconImage.setImage(",
              'g.drawText("dBFS"', "hannWeightSum",
              "analyzerRangeIndex", "analyzerReferenceIndex",
              "analyzerTiltIndex","CetusEQ::makeCoefficients"]:
    if token not in cpp: raise RuntimeError("Previous GUI feature missing: "+token)

expected_dsp={
    "Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}
for file,sha in expected_dsp.items():
    actual=hashlib.sha256(Path(file).read_bytes()).hexdigest()
    if actual!=sha: raise RuntimeError("DSP changed unexpectedly: "+file)
editor.write_text(cpp,encoding="utf8")
header.write_text(hpp,encoding="utf8")
cm.write_text(cmdata,encoding="utf8")
print("cetusproEQ v0.5.15: visible spectrum fill, compact controls, 1/6 Oct startup; DSP byte-identical")
