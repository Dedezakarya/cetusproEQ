#!/usr/bin/env python3
"""v0.5.14 - calibrated analyzer display and independent dBFS axis.
Runs after apply_0513.py. GUI-only changes: processor DSP remains byte identical.
"""
from pathlib import Path
import hashlib
editor=Path("Source/PluginEditor.cpp")
header=Path("Source/PluginEditor.h")
cm=Path("CMakeLists.txt")
cpp=editor.read_text(encoding="utf8")
hpp=header.read_text(encoding="utf8")
def replace_once(old,new,field="CPP"):
    global cpp,hpp
    s=cpp if field=="CPP" else hpp
    hits=s.count(old)
    if hits!=1:raise RuntimeError(f"{field}: expected one anchor, got {hits}: {old[:120]!r}")
    s=s.replace(old,new,1)
    if field=="CPP":cpp=s
    else:hpp=s

replace_once(
    '    juce::TextButton hudCloseButton {"x"}, holdButton {"Hold 150ms"}, smoothButton {"1/3 Oct"};',
    '''    juce::TextButton hudCloseButton {"x"}, holdButton {"Hold 150ms"}, smoothButton {"1/3 Oct"};
    // GUI-only analyzer controls; never modify EQ coefficients or audio buffers.
    juce::TextButton analyzerRangeButton {"Range 90dB"};
    juce::TextButton analyzerTiltButton {"Tilt 0"};
    juce::TextButton analyzerReferenceButton {"Ref 0dB"};''',
    "HPP"
)
replace_once(
    '    int draggingBand = -1, holdMs = 150, smoothingMode = 2;',
    '''    int draggingBand = -1, holdMs = 150, smoothingMode = 2;
    int analyzerRangeIndex = 1;      // 60, 90 (default), 120 dB
    int analyzerTiltIndex = 0;       // 0 (accurate), 3, 4.5, 6 dB/oct
    int analyzerReferenceIndex = 0;  // top display value: 0, -12, -24 dBFS''',
    "HPP"
)
replace_once(
    '''                  &hudCloseButton,&holdButton,&smoothButton}) addButton(*b);''',
    '''                  &hudCloseButton,&holdButton,&smoothButton,
                  &analyzerRangeButton,&analyzerTiltButton,&analyzerReferenceButton}) addButton(*b);'''
)
replace_once(
    '''    undoIconImage.setImage(juce::ImageFileFormat::loadFrom(''',
    '''    // FFT magnitudes must start at the noise floor, not at 0 dBFS.
    spectrumDb.fill(-96.0f);
    analyzerRangeButton.setTooltip("Analyzer display span: 60, 90 or 120 dB. EQ gain scale is independent.");
    analyzerTiltButton.setTooltip("Visual spectrum tilt: 0, +3, +4.5 or +6 dB/oct. 0 is un-tilted dBFS.");
    analyzerReferenceButton.setTooltip("Top of analyzer scale: 0, -12 or -24 dBFS. Display only; audio unchanged.");
    undoIconImage.setImage(juce::ImageFileFormat::loadFrom('''
)
replace_once(
    '''    else if(button==&smoothButton){smoothingMode=(smoothingMode+1)%3;updateSmoothingText();}''',
    '''    else if(button==&smoothButton){smoothingMode=(smoothingMode+1)%3;updateSmoothingText();}
    else if(button==&analyzerRangeButton) {
        analyzerRangeIndex=(analyzerRangeIndex+1)%3;
        const int spans[]={60,90,120};
        analyzerRangeButton.setButtonText("Range "+juce::String(spans[analyzerRangeIndex])+"dB");
    }
    else if(button==&analyzerTiltButton) {
        analyzerTiltIndex=(analyzerTiltIndex+1)%4;
        const float tilts[]={0.0f,3.0f,4.5f,6.0f};
        analyzerTiltButton.setButtonText("Tilt "+juce::String(tilts[analyzerTiltIndex],1));
    }
    else if(button==&analyzerReferenceButton) {
        analyzerReferenceIndex=(analyzerReferenceIndex+1)%3;
        const int references[]={0,-12,-24};
        analyzerReferenceButton.setButtonText("Ref "+juce::String(references[analyzerReferenceIndex])+"dB");
    }'''
)
replace_once(
    '''    placeDesignChild(smoothButton,{453,536, 92,23});''',
    '''    placeDesignChild(smoothButton,{453,536, 92,23});
    placeDesignChild(analyzerRangeButton, {553,536,104,23});
    placeDesignChild(analyzerTiltButton, {663,536,91,23});
    placeDesignChild(analyzerReferenceButton, {760,536,104,23});'''
)
replace_once(
    '''    const float factor=4.0f/CetusproEQAudioProcessor::fftSize;''',
    '''    // Hann coherent-gain normalization: for a bin-centred full-scale
    // sine (peak amplitude 1), magnitude*2/sum(window) is ~1 => 0 dBFS.
    // Symmetric Hann sum = (fftSize-1)/2. DC is not used for plotted bins.
    const float hannWeightSum = (float)(CetusproEQAudioProcessor::fftSize-1)*0.5f;
    const float factor=2.0f/hannWeightSum;'''
)
replace_once(
    '''            const float y=juce::jmap(juce::jlimit(-96.0f,-6.0f,dB),-96.0f,-6.0f,
                                    (float)plot.getBottom(),(float)plot.getY());
            points.push_back({x,y});''',
    '''            const float displaySpan = analyzerRangeIndex==0 ? 60.0f
                                    : analyzerRangeIndex==1 ? 90.0f : 120.0f;
            const float displayTop = analyzerReferenceIndex==0 ? 0.0f
                                   : analyzerReferenceIndex==1 ? -12.0f : -24.0f;
            const float tiltDbPerOct = analyzerTiltIndex==0 ? 0.0f
                                     : analyzerTiltIndex==1 ? 3.0f
                                     : analyzerTiltIndex==2 ? 4.5f : 6.0f;
            // Display tilt pivots at 1 kHz; spectrumDb is always calibrated dBFS.
            const float displayDb = dB + tiltDbPerOct *
                std::log2(juce::jmax(20.0f,frequency)/1000.0f);
            const float y=juce::jmap(
                juce::jlimit(displayTop-displaySpan,displayTop,displayDb),
                displayTop-displaySpan,displayTop,
                (float)plot.getBottom(),(float)plot.getY());
            points.push_back({x,y});'''
)
replace_once(
    '''    g.restoreState();
    // Interactive 1-8 band nodes. Mono/Mid/Side have concise channel marks.''',
    '''    g.restoreState();
    // The right-hand labels are a separate calibrated spectrum axis. Left
    // ±18 dB labels remain EQ gains and are deliberately not used for FFT.
    const float displaySpan = analyzerRangeIndex==0 ? 60.0f
                            : analyzerRangeIndex==1 ? 90.0f : 120.0f;
    const float displayTop = analyzerReferenceIndex==0 ? 0.0f
                           : analyzerReferenceIndex==1 ? -12.0f : -24.0f;
    const int spectrumAxisX = plot.getRight()+4;
    g.setFont(juce::FontOptions(8.2f));
    g.setColour(muted.withAlpha(.84f));
    g.drawText("dBFS",spectrumAxisX,plot.getY()-17,32,13,juce::Justification::centredLeft);
    for(int tick=0;tick<=6;++tick) {
        const float dB = displayTop-displaySpan*(float)tick/6.0f;
        const int yTick=juce::roundToInt(plot.getY()+plot.getHeight()*(float)tick/6.0f);
        g.drawText(juce::String(juce::roundToInt(dB)),spectrumAxisX,yTick-6,
                   32,12,juce::Justification::centredLeft);
    }
    // Interactive 1-8 band nodes. Mono/Mid/Side have concise channel marks.'''
)
# Keep UI and audio versions in agreement.
assert cpp.count("v0.5.13")>=2
cpp=cpp.replace("v0.5.13","v0.5.14")
editor.write_text(cpp,encoding="utf8")
header.write_text(hpp,encoding="utf8")
source=cm.read_text(encoding="utf8")
assert source.count("VERSION 0.5.13")==1
cm.write_text(source.replace("VERSION 0.5.13","VERSION 0.5.14",1),encoding="utf8")

# Immutable audio DSP: keep full processing, parameter IDs and sidechain untouched.
expected={
"Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
"Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
"Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
"Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc"}
for file,sha in expected.items():
    actual=hashlib.sha256(Path(file).read_bytes()).hexdigest()
    if actual!=sha:raise RuntimeError("DSP changed: "+file)
print("v0.5.14 display calibration, right dBFS axis, Range/Tilt/Reference controls; DSP identical")
