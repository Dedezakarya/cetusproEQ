#!/usr/bin/env python3
"""v0.5.8: fix scaled GUI layout only; preserve DSP source byte-for-byte."""
from pathlib import Path
import hashlib

h=Path("Source/PluginEditor.h")
a=h.read_bytes()
old=b'''        child.setBounds(juce::roundToInt(designBounds.getX()*uiScale),
                        juce::roundToInt(designBounds.getY()*uiScale),
                        designBounds.getWidth(), designBounds.getHeight());
        child.setTransform(juce::AffineTransform::scale(uiScale));'''
new=b'''        // JUCE scales child positions too: never scale x/y twice.
        child.setBounds(designBounds);
        child.setTransform(juce::AffineTransform::scale(uiScale));'''
if a.count(old)!=1: raise RuntimeError("Header GUI scale anchor mismatch")
h.write_bytes(a.replace(old,new,1))

p=Path("Source/PluginEditor.cpp")
data=p.read_bytes()
start=b"void CetusproEQAudioProcessorEditor::resized() {"
end=b"void CetusproEQAudioProcessorEditor::updateSpectrum() {"
assert data.count(start)==data.count(end)==1
a=data.index(start); b=data.index(end,a)
layout=r"""void CetusproEQAudioProcessorEditor::resized() {
    // All bounds below are 1080 x 594 DESIGN positions. Component transform
    // maps them ONCE to the 960 x 528 window, including text & click targets.
    placeDesignChild(presets, {278,22,222,28});
    placeDesignChild(applyPresetButton,{507,22,46,28});
    placeDesignChild(savePresetButton,{560,22,30,28});
    placeDesignChild(openPresetButton,{596,22,30,28});
    placeDesignChild(undoButton,{637,22,30,28});
    placeDesignChild(redoButton,{673,22,30,28});
    placeDesignChild(initButton,{720,22,82,28});
    placeDesignChild(analyzerButton,{808,22,103,28});
    placeDesignChild(prePostButton,{917,22,62,28});
    const auto lower=bottomRect();
    const int listX=lower.getX()+12, listY=lower.getY()+38;
    for(int i=0;i<CetusproEQAudioProcessor::numBands;++i)
        placeDesignChild(bandButtons[(size_t)i],{listX+(i%2)*49,listY+(i/2)*27,44,23});
    placeDesignChild(bandType,{147,388,133,28});
    placeDesignChild(bandMode,{286,388,112,28});
    placeDesignChild(dynamicOn,{407,389,96,26});
    placeDesignChild(sendLabel,{519,373,110,15});sendLabel.setVisible(false);
    placeDesignChild(send,{519,388,115,28});
    placeDesignChild(listenLabel,{644,373,122,15});listenLabel.setVisible(false);
    placeDesignChild(listen,{644,388,122,28});
    placeDesignChild(outputLabel,{962,388,88,19});outputLabel.setVisible(false);
    placeDesignChild(output,{962,410,87,116});
    for(int i=0;i<7;++i) {
        auto& k=knobs[(size_t)i];
        const int x=142+i*115;
        placeDesignChild(k.label,{x,423,102,15});
        placeDesignChild(k.slider,{x+5,438,90,86});
    }
    placeDesignChild(bandOn,{150,537,68,22});
    placeDesignChild(bypass,{225,537,85,22});
    placeDesignChild(holdButton,{340,536,106,23});
    placeDesignChild(smoothButton,{453,536,92,23});
    updateHudPosition();
#if JUCE_DEBUG
    jassert(presets.getBoundsInParent().getRight()<=applyPresetButton.getBoundsInParent().getX()+2);
    jassert(bandType.getBoundsInParent().getY()>=juce::roundToInt(bottomRect().getY()*uiScale));
#endif
}
""".encode("utf-8")
data=data[:a]+layout+data[b:]
data=data.replace(b"v0.5.7",b"v0.5.8")
data=data.replace("8-BAND / STEREO · MID · SIDE".encode(),b"8-BAND / STEREO - MID - SIDE")
p.write_bytes(data)
cm=Path("CMakeLists.txt")
d=cm.read_bytes()
if d.count(b"VERSION 0.5.7")!=1: raise RuntimeError("Version mismatch")
cm.write_bytes(d.replace(b"VERSION 0.5.7",b"VERSION 0.5.8"))
checks={
"Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
"Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
"Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
"Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}
for file, expected in checks.items():
    actual=hashlib.sha256(Path(file).read_bytes()).hexdigest()
    if actual!=expected: raise RuntimeError("DSP CHANGED: "+file)
print("v0.5.8 compact layout fixed; 4 immutable DSP hashes verified")
