#!/usr/bin/env python3
"""cetusproEQ v0.5.13: filter Q default, interpolated analyzer, coefficient-aligned curve.
Only changes the generated PluginEditor.cpp and CMake version; DSP remains byte-identical.
Run after ci-source/apply_05122.py.
"""
from pathlib import Path
import hashlib

editor = Path("Source/PluginEditor.cpp")
source = editor.read_text(encoding="utf-8")

def swap_once(old, new, reason):
    global source
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{reason}: expected exactly one anchor; found {count}: {old[:100]!r}")
    source = source.replace(old, new, 1)

# 1. Selecting a HP / LP filter starts at maximally-flat Butterworth Q.
# The host parameter choice list uses indexes 3=High Pass and 4=Low Pass;
# do not reference enum names that are not exported by CetusEQFilters.h.
# Explicitly changing filter type is the user action; preset loads/undo retain custom Q.
swap_once(
    '''    if(c==&hudType && attachedHudBand>=0) {
        processor.setParameterActual(CetusproEQAudioProcessor::param(attachedHudBand,"type"),
            (float)juce::jmax(0,hudType.getSelectedId()-1));
        if(attachedHudBand==selectedBand){setKnobType();if(hudPinned)bindFloatingControls(selectedBand);}
        requestHistorySnapshot();
    } else if(c==&bandType) {
        setKnobType();if(hudPinned)bindFloatingControls(selectedBand);requestHistorySnapshot();syncHud();
    } else if(c==&bandMode||c==&send||c==&listen)requestHistorySnapshot();''',
    '''    if(c==&hudType && attachedHudBand>=0) {
        const int previousType = processor.getBandType(attachedHudBand);
        const int newType = juce::jmax(0, hudType.getSelectedId()-1);
        processor.setParameterActual(CetusproEQAudioProcessor::param(attachedHudBand,"type"),
            (float)newType);
        if (!restoringHistory && newType != previousType &&
            (newType == 3 || newType == 4))
            processor.setParameterActual(CetusproEQAudioProcessor::param(attachedHudBand,"q"),
                0.70710678f);
        if(attachedHudBand==selectedBand){setKnobType();if(hudPinned)bindFloatingControls(selectedBand);}
        requestHistorySnapshot();
    } else if(c==&bandType) {
        const int newType = juce::jmax(0,bandType.getSelectedId()-1);
        if (!restoringHistory && (newType == 3 || newType == 4))
            processor.setParameterActual(CetusproEQAudioProcessor::param(selectedBand,"q"),
                0.70710678f);
        setKnobType();if(hudPinned)bindFloatingControls(selectedBand);requestHistorySnapshot();syncHud();
    } else if(c==&bandMode||c==&send||c==&listen)requestHistorySnapshot();''',
    "Set HP/LP default Q only on selection"
)

# 2a. Gentle time smoothing of FFT attack; preserve hold and the existing release.
swap_once(
    '''        if(db>=spectrumDb[i]) {spectrumDb[i]=db;spectrumHoldFrames[i]=targetHoldFrames;}
        else if(spectrumHoldFrames[i]>0) --spectrumHoldFrames[i];
        else spectrumDb[i]=juce::jmax(-96.0f,spectrumDb[i]-2.6f);''',
    '''        if(db>=spectrumDb[i]) {
            // 30Hz GUI timer: fast but non-jittery attack; no DSP audio latency.
            spectrumDb[i] += (db-spectrumDb[i])*0.52f;
            spectrumHoldFrames[i]=targetHoldFrames;
        }
        else if(spectrumHoldFrames[i]>0) --spectrumHoldFrames[i];
        else spectrumDb[i]=juce::jmax(-96.0f,spectrumDb[i]-2.0f);''',
    "Smooth temporal analyzer magnitude"
)

# 2b. Sample fractional FFT bins. Averaging integer-index bins produced
# staircases at low frequencies because several plot points shared one bin.
swap_once(
    '''        const int pointCount=juce::jmin(900,plot.getWidth());
        for(int i=0;i<=pointCount;++i) {''',
    '''        const int pointCount=juce::jmin(900,plot.getWidth());
        const float maxBin = (float)(CetusproEQAudioProcessor::fftSize/2);
        const auto spectrumAt = [this,maxBin](float position) -> float {
            const float p = juce::jlimit(1.0f,maxBin-0.001f,position);
            const int first = (int)std::floor(p);
            const float fraction = p-(float)first;
            return juce::jmap(fraction,spectrumDb[(size_t)first],
                             spectrumDb[(size_t)(first+1)]);
        };
        for(int i=0;i<=pointCount;++i) {''',
    "Add fractional FFT interpolation"
)
swap_once(
    '''            const int lo=juce::jlimit(1,CetusproEQAudioProcessor::fftSize/2,
                juce::roundToInt(frequency*std::pow(2.0f,-octaves)*CetusproEQAudioProcessor::fftSize/sr));
            const int hi=juce::jlimit(lo,CetusproEQAudioProcessor::fftSize/2,
                juce::roundToInt(frequency*std::pow(2.0f,octaves)*CetusproEQAudioProcessor::fftSize/sr));
            float dB=0;
            for(int bin=lo;bin<=hi;++bin)dB+=spectrumDb[(size_t)bin];
            dB/=(float)(hi-lo+1);''',
    '''            const float lowBin = juce::jlimit(1.0f,maxBin-0.001f,
                (float)(frequency*std::pow(2.0f,-octaves)*CetusproEQAudioProcessor::fftSize/sr));
            const float highBin = juce::jlimit(lowBin,maxBin-0.001f,
                (float)(frequency*std::pow(2.0f,octaves)*CetusproEQAudioProcessor::fftSize/sr));
            // Seven frequency-domain taps, including fractional bin positions.
            // Retain the user's existing 1/6-oct, 1/3-oct and smooth-off modes.
            float dB=0.0f;
            constexpr int tapCount=7;
            for(int tap=0;tap<tapCount;++tap) {
                const float fraction=(float)tap/(float)(tapCount-1);
                dB += spectrumAt(juce::jmap(fraction,lowBin,highBin));
            }
            dB /= (float)tapCount;''',
    "Replace rounded FFT bins with interpolated spectrum sampling"
)

# 3. Same processor-filter constructor, Q, type, slope stage count and
# current sample rate are used for the graphical frequency response.
# The visual dynamic offset is read only when dynamics are active.
swap_once(
    '''        baseFilters[(size_t)i]=CetusEQ::makeCoefficients(sr,freq,q,gain,type);
        activeFilters[(size_t)i]=CetusEQ::makeCoefficients(sr,freq,q,gain+visualDynamicGain[(size_t)i],type);''',
    '''        // Use exactly the same coefficient factory as the real audio DSP.
        baseFilters[(size_t)i]=CetusEQ::makeCoefficients(sr,freq,q,gain,type);
        const float dynamicOffset = processor.isBandDynamicEnabled(i)
            ? visualDynamicGain[(size_t)i] : 0.0f;
        activeFilters[(size_t)i]=CetusEQ::makeCoefficients(sr,freq,q,gain+dynamicOffset,type);''',
    "Align static/live EQ curves with active DSP coefficients"
)
assert 'coeff->getMagnitudeForFrequency' in source
assert 'CetusEQ::stageCountForTypeAndSlope' in source
assert 'baseDb+=magnitudeDb(baseFilters' in source
assert 'nowDb+=magnitudeDb(activeFilters' in source
assert 'juce::ImageComponent undoIconImage' not in source  # members are in the .h, not .cpp
# Original user-supplied images and all 8 bands are carried forward unchanged.
assert 'undoIconImage.setImage(' in source
assert 'redoIconImage.setImage(' in source

# Display version and metadata only; don't rename parameter IDs or host state.
assert source.count('v0.5.12.2') >= 2
source = source.replace('v0.5.12.2','v0.5.13')
editor.write_text(source,encoding="utf-8")

cm=Path("CMakeLists.txt")
cmSource=cm.read_text(encoding="utf-8")
assert cmSource.count("VERSION 0.5.12.2")==1
cm.write_text(cmSource.replace("VERSION 0.5.12.2","VERSION 0.5.13",1),encoding="utf-8")

# Guardrail: all four original audio/DSP files must remain bit-identical.
dsp = {
    "Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}
for file,expected in dsp.items():
    actual=hashlib.sha256(Path(file).read_bytes()).hexdigest()
    if actual!=expected:
        raise RuntimeError(f"DSP changed unexpectedly in {file}: {actual}")
print("cetusproEQ v0.5.13: 3 EQ/analyzer GUI adjustments applied; DSP SHA256 unchanged")
