#!/usr/bin/env python3
"""cetusproEQ v0.5.18: Band Solo audition and polarity invert.

Append after apply_0517.py; original eight-band Dynamic EQ, detector, presets,
Cetus Link, and FFT analyzer remain unchanged. New parameters are additive.
"""
from pathlib import Path
p=Path("Source/PluginProcessor.cpp")
h=Path("Source/PluginProcessor.h")
e=Path("Source/PluginEditor.cpp")
eh=Path("Source/PluginEditor.h")
cm=Path("CMakeLists.txt")
proc=p.read_text(encoding="utf8")
header=h.read_text(encoding="utf8")
gui=e.read_text(encoding="utf8")
guih=eh.read_text(encoding="utf8")
def swap(src,old,new,why):
    n=src.count(old)
    if n!=1:raise RuntimeError(f"{why}: unique anchor expected; got {n}: {old[:100]!r}")
    return src.replace(old,new,1)

# 1. Additive DAW automatable and preset-persistent parameters.
proc=swap(proc,
    '''    layout.add(std::make_unique<juce::AudioParameterBool>(juce::ParameterID("bypass",1), "Bypass", false));
    return layout;''',
    '''    layout.add(std::make_unique<juce::AudioParameterBool>(juce::ParameterID("bypass",1), "Bypass", false));
    // 0 = audition disabled, 1..8 = band being monitored.
    layout.add(std::make_unique<juce::AudioParameterInt>(
        juce::ParameterID("soloBand",1), "Band Solo", 0, numBands, 0));
    layout.add(std::make_unique<juce::AudioParameterBool>(
        juce::ParameterID("polarity",1), "Polarity Invert", false));
    return layout;''',"APVTS Band Solo and polarity")

# Zero allocations occur in processBlock. Scratch storage and all IIR filter
# state are members initialized by prepareToPlay.
header=swap(header,
    '''    double currentSampleRate = 48000.0;
    uint64_t lastLinkUpdate = 0;''',
    '''    double currentSampleRate = 48000.0;
    uint64_t lastLinkUpdate = 0;
    juce::AudioBuffer<float> soloScratch;
    std::array<std::array<juce::dsp::IIR::Filter<float>,maxStagesPerBand>,2> soloFilters;
    int activeSoloBand = 0;
    float soloMix = 0.0f;      // 0: normal EQ, 1: band audition
    float polarityMix = 0.0f;  // 0: normal, 1: inverted, smooth transitions
    void renderBandAudition(int band, int channels, int samples);''',
    "processor audition scratch members")

proc=swap(proc,
    '''void CetusproEQAudioProcessor::prepareToPlay(double rate, int) {
    currentSampleRate = rate > 0.0 ? rate : 48000.0;''',
    '''void CetusproEQAudioProcessor::prepareToPlay(double rate, int samplesPerBlock) {
    currentSampleRate = rate > 0.0 ? rate : 48000.0;
    // Fixed scratch buffer, never resized/allocated on the audio thread.
    soloScratch.setSize(2,juce::jmax(65536,samplesPerBlock),false,false,true);
    soloScratch.clear();
    activeSoloBand = 0;
    soloMix = 0.0f;
    polarityMix = 0.0f;
    for (auto& lane:soloFilters) for (auto& filter:lane) filter.reset();''',
    "prepare scratch and avoid clicks")

# Solo monitors an EQ band in isolation. Bell/shelf/notch audition a band-pass;
# HP/LP audition the actual pass-filter slope. Solo audio is from the original
# input (before other EQ bands) and never feeds the dynamic sidechain detector.
anchor='static float peakValue(const juce::AudioBuffer<float>& buffer, int count, int samples) noexcept {'
if proc.count(anchor)!=1:raise RuntimeError("Audition helper insertion point missing")
audition=r'''void CetusproEQAudioProcessor::renderBandAudition(int band, int channels, int samples) {
    if (band < 0 || band >= numBands) return;
    const int type = getBandType(band);
    const int mode = getBandMode(band);
    const float maxHz = static_cast<float>(currentSampleRate*0.475);
    const float hz = juce::jlimit(20.0f,juce::jmax(21.0f,maxHz),getBandFrequency(band));
    const float q = juce::jlimit(0.2f,12.0f,getBandQ(band));
    const bool slopeFilter = CetusEQ::isSlopeFilter(type);
    const int stages = slopeFilter ?
        CetusEQ::stageCountForTypeAndSlope(type,getBandSlopeIndex(band)) : 1;
    using Coefficients = juce::dsp::IIR::Coefficients<float>;
    auto coefficients = slopeFilter
        ? CetusEQ::makeCoefficients(currentSampleRate,hz,q,0.0f,type)
        : Coefficients::makeBandPass(currentSampleRate,hz,q);
    for (int c=0;c<channels;++c)
        for (int stage=0;stage<stages;++stage)
            soloFilters[static_cast<size_t>(c)][static_cast<size_t>(stage)].coefficients=coefficients;

    // Mid/Side monitoring is routed to both speakers as mono so the selected
    // component can actually be heard instead of disappearing in mono.
    if (channels==2 && mode!=CetusEQ::stereo) {
        auto* left=soloScratch.getWritePointer(0);
        auto* right=soloScratch.getWritePointer(1);
        for (int n=0;n<samples;++n) {
            float x=mode==CetusEQ::mid ? 0.5f*(left[n]+right[n])
                                       : 0.5f*(left[n]-right[n]);
            for (int stage=0;stage<stages;++stage)
                x=soloFilters[0][static_cast<size_t>(stage)].processSample(x);
            left[n]=x;right[n]=x;
        }
    } else {
        for (int c=0;c<channels;++c) {
            auto* data=soloScratch.getWritePointer(c);
            for (int n=0;n<samples;++n) {
                float x=data[n];
                for (int stage=0;stage<stages;++stage)
                    x=soloFilters[static_cast<size_t>(c)][static_cast<size_t>(stage)].processSample(x);
                data[n]=x;
            }
        }
    }
}

'''
proc=proc.replace(anchor,audition+anchor,1)

# Capture before EQ. Off => no raw copy and no change to existing DSP path.
proc=swap(proc,
    '''    auto main = getBusBuffer(buffer, true, 0);
    const float inputPeak = peakValue(main, channels, samples);''',
    '''    auto main = getBusBuffer(buffer, true, 0);
    const int requestedSolo=juce::jlimit(0,numBands,juce::roundToInt(readParam("soloBand")));
    // Continue rendering the last solo during fade-out for click-free release.
    const bool canAudition=samples<=soloScratch.getNumSamples()
        && channels<=soloScratch.getNumChannels();
    if (requestedSolo>0 && requestedSolo!=activeSoloBand) {
        activeSoloBand=requestedSolo;
        soloMix=0.0f;
        for (auto& lane:soloFilters) for (auto& filter:lane) filter.reset();
    }
    const bool needAudition=canAudition && activeSoloBand>0
        && (requestedSolo>0 || soloMix>0.00001f);
    if (needAudition)
        for (int c=0;c<channels;++c)
            soloScratch.copyFrom(c,0,main,c,0,samples);
    const float inputPeak = peakValue(main, channels, samples);''',
    "capture raw band monitor source")

# Process the original EQ engine and final output first. Solo mixes in after EQ,
# then global polarity is applied to both L/R channels. Crossfades avoid pops.
proc=swap(proc,
    '''    const float output = readParam("output");
    if (std::abs(output) >= 0.0001f) main.applyGain(juce::Decibels::decibelsToGain(output));
    updateSpectrumAndMeters(main, captureStart, channels);''',
    '''    const float output = readParam("output");
    if (std::abs(output) >= 0.0001f) main.applyGain(juce::Decibels::decibelsToGain(output));

    if (needAudition) renderBandAudition(activeSoloBand-1,channels,samples);
    const float outputLinear=juce::Decibels::decibelsToGain(output);
    const float targetSolo=(needAudition && requestedSolo>0) ? 1.0f : 0.0f;
    const float targetPolarity=readParam("polarity")>0.5f ? 1.0f : 0.0f;
    const float soloStep=1.0f/juce::jmax(1.0f,
        static_cast<float>(currentSampleRate)*0.006f);
    const float polarityStep=1.0f/juce::jmax(1.0f,
        static_cast<float>(currentSampleRate)*0.003f);
    for (int n=0;n<samples;++n) {
        soloMix+=juce::jlimit(-soloStep,soloStep,targetSolo-soloMix);
        polarityMix+=juce::jlimit(-polarityStep,polarityStep,targetPolarity-polarityMix);
        const float phaseSign=1.0f-2.0f*polarityMix;
        for (int c=0;c<channels;++c) {
            float value=main.getSample(c,n);
            if (needAudition)
                value=(1.0f-soloMix)*value
                    +soloMix*soloScratch.getSample(c,n)*outputLinear;
            main.setSample(c,n,value*phaseSign);
        }
    }
    if (requestedSolo==0 && soloMix<=0.00001f) activeSoloBand=0;
    updateSpectrumAndMeters(main, captureStart, channels);''',
    "separate solo audition and global output polarity")

proc=swap(proc,
    '''    setParameterActual("bypass", 0.0f);
}''',
    '''    setParameterActual("bypass", 0.0f);
    setParameterActual("soloBand", 0.0f);
    setParameterActual("polarity", 0.0f);
}''',
    "factory reset clears temporary audition and polarity")

# 2. GUI controls, keeping the 8-band grid and output knob untouched.
guih=swap(guih,
    '''    juce::TextButton undoButton {"Undo"}, redoButton {"Redo"};''',
    '''    juce::TextButton undoButton {"Undo"}, redoButton {"Redo"};
    juce::TextButton soloButton {"SOLO"};
    juce::TextButton polarityButton {"\\xC3\\x98"};''',
    "new controls in header")
guih=swap(guih,
    '''    std::unique_ptr<ButtonAttachment> enabledAttachment, dynamicAttachment, bypassAttachment;''',
    '''    std::unique_ptr<ButtonAttachment> enabledAttachment, dynamicAttachment, bypassAttachment, polarityAttachment;''',
    "polarity host parameter attachment")
guih=swap(guih,
    '''    void syncDynamicAdvancedButtons();''',
    '''    void syncDynamicAdvancedButtons();
    void syncSoloButton();''',
    "solo indicator method")

gui=swap(gui,
    '''    setSize(886, 487);''',
    '''    setSize(886, 487);
    polarityButton.setComponentID("cetus-polarity");
    polarityButton.setClickingTogglesState(true);
    polarityButton.setTooltip("Invert both output channels (180 degrees); orange when enabled.");
    polarityAttachment=std::make_unique<ButtonAttachment>(
        processor.parameters,"polarity",polarityButton);
    soloButton.setTooltip("Audition only the selected band's frequency range. Click again to return to full EQ.");''',
    "GUI initial host attachment and tooltips")

gui=swap(gui,
    '''                  &analyzerRangeButton,&analyzerTiltButton,&analyzerReferenceButton,
                  &ratioButton,&kneeButton}) addButton(*b);''',
    '''                  &analyzerRangeButton,&analyzerTiltButton,&analyzerReferenceButton,
                  &ratioButton,&kneeButton,&soloButton,&polarityButton}) addButton(*b);''',
    "add new interactive buttons")
gui=swap(gui,
    '''    placeDesignChild(output,    {962,427, 87,106});''',
    '''    placeDesignChild(output,    {962,427, 87,106});
    // Small polarity button centered below the Output knob.
    placeDesignChild(polarityButton, {986,536,39,22});''',
    "under-output Ø placement")
gui=swap(gui,
    '''    placeDesignChild(bandType,  {147,388,133,28});''',
    '''    // Band Solo lives in the BANDS heading and does not cover band buttons.
    placeDesignChild(soloButton, {86,382,43,21});
    placeDesignChild(bandType,  {147,388,133,28});''',
    "solo button beside BANDS heading")

gui=swap(gui,
    '''    else if(button==&kneeButton) {
        constexpr float knees[]={0.0f,3.0f,6.0f,9.0f,12.0f};
        const float current=processor.readParam(CetusproEQAudioProcessor::param(selectedBand,"knee"));
        int next=0;
        for(int i=0;i<5;++i)if(current>=knees[i]-.05f)next=i+1;
        processor.setParameterActual(CetusproEQAudioProcessor::param(selectedBand,"knee"),knees[next%5]);
        syncDynamicAdvancedButtons();requestHistorySnapshot();
    }''',
    '''    else if(button==&kneeButton) {
        constexpr float knees[]={0.0f,3.0f,6.0f,9.0f,12.0f};
        const float current=processor.readParam(CetusproEQAudioProcessor::param(selectedBand,"knee"));
        int next=0;
        for(int i=0;i<5;++i)if(current>=knees[i]-.05f)next=i+1;
        processor.setParameterActual(CetusproEQAudioProcessor::param(selectedBand,"knee"),knees[next%5]);
        syncDynamicAdvancedButtons();requestHistorySnapshot();
    }
    else if(button==&soloButton) {
        const int oldBand=juce::roundToInt(processor.readParam("soloBand"));
        const int nextBand=oldBand==(selectedBand+1)?0:selectedBand+1;
        processor.setParameterActual("soloBand",(float)nextBand);
        syncSoloButton();requestHistorySnapshot();
    }
    else if(button==&polarityButton) { requestHistorySnapshot(); }''',
    "Solo toggle and Undo state")

gui=swap(gui,
    '''    syncVisualEnableState();
    syncDynamicAdvancedButtons();''',
    '''    syncVisualEnableState();
    syncDynamicAdvancedButtons();
    syncSoloButton();''',
    "solo display updates on band selection/host automation")

gui=swap(gui,
    '''void CetusproEQAudioProcessorEditor::syncDynamicAdvancedButtons() {''',
    '''void CetusproEQAudioProcessorEditor::syncSoloButton() {
    const int audibleBand=juce::jlimit(0,CetusproEQAudioProcessor::numBands,
        juce::roundToInt(processor.readParam("soloBand")));
    const bool thisBandIsSolo=audibleBand==selectedBand+1;
    soloButton.setToggleState(thisBandIsSolo,juce::dontSendNotification);
    soloButton.setButtonText(audibleBand>0
        ? ("S"+juce::String(audibleBand)) : "SOLO");
}
void CetusproEQAudioProcessorEditor::syncDynamicAdvancedButtons() {''',
    "selected band solo indicator")

# The custom look and feel draws all buttons; it overrides buttonOnColourId.
# Set only the Ø button to orange; OFF retains existing graphite.
gui=swap(gui,
    '''    } else if(selected) {
        base=cyan.darker(.38f);
    }''',
    '''    } else if(selected && button.getComponentID()=="cetus-polarity") {
        base=juce::Colour::fromRGB(248,148,30);
    } else if(selected) {
        base=cyan.darker(.38f);
    }''',
    "polarity orange active background")
gui=swap(gui,
    '''    if(id=="cetus-undo" || id=="cetus-redo") return;''',
    '''    if(id=="cetus-undo" || id=="cetus-redo") return;
    if(id=="cetus-polarity") {
        g.setColour(button.getToggleState()
            ? juce::Colours::black : juce::Colour::fromRGB(224,237,244));
        g.setFont(juce::FontOptions(18.0f,juce::Font::bold));
        g.drawText(juce::String::fromUTF8("\\xC3\\x98"),
                   button.getLocalBounds(),juce::Justification::centred);
        return;
    }''',
    "polarity Ø glyph independent of platform encoding")

# Version metadata only; do not change plugin manufacturer IDs.
assert gui.count("v0.5.17")>=2
gui=gui.replace("v0.5.17","v0.5.18")
version=cm.read_text(encoding="utf8")
assert version.count("VERSION 0.5.17")==1
version=version.replace("VERSION 0.5.17","VERSION 0.5.18",1)
for text in ('CetusLink::send','CetusLink::read','meterDynGain',
             'CetusEQ::makeCoefficients','PASS 1 - Analyze untouched input',
             'PASS 2 - Equalize'):
    if text not in proc:raise RuntimeError("Prior DSP component missing: "+text)
for text in ('BinaryData::CetusUndo_png','BinaryData::CetusRedo_png',
             'g.drawText("ZERO LATENCY"','analyzerRangeIndex'):
    if text not in gui:raise RuntimeError("Prior GUI component missing: "+text)
for path,value in [(p,proc),(h,header),(e,gui),(eh,guih),(cm,version)]:
    path.write_text(value,encoding="utf8")
print("v0.5.18: selected-band monitor Solo with fade, Ø global stereo polarity with orange toggle and smooth sign; legacy DSP/UI retained")
