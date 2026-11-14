#!/usr/bin/env python3
"""cetusproEQ v0.5.17: frequency-selective dynamic detector, soft knee, ratio,
responsive per-sample envelope, true GR meter and new per-band controls.

Runs AFTER apply_0516.py against the generated source. Preserve the audio
filter topology, channel modes, preset serialization and original GUI layout.
"""
from pathlib import Path
import hashlib
p=Path("Source/PluginProcessor.cpp")
h=Path("Source/PluginProcessor.h")
e=Path("Source/PluginEditor.cpp")
eh=Path("Source/PluginEditor.h")
cm=Path("CMakeLists.txt")
proc=p.read_text(encoding="utf8")
header=h.read_text(encoding="utf8")
gui=e.read_text(encoding="utf8")
guih=eh.read_text(encoding="utf8")
def swap(src,old,new,label):
    count=src.count(old)
    if count!=1:
        raise RuntimeError(f"{label}: expected one exact match, found {count}: {old[:120]!r}")
    return src.replace(old,new,1)

# New APVTS parameters are ADDITIVE; existing parameter IDs and serialization
# are unchanged. All existing presets/DAW automation retain their old fields.
proc=swap(proc,
    '        makeF(id("rel"), 5.0f, 1000.0f, 150.0f, 0.1f, 0.45f);',
    '''        makeF(id("rel"), 5.0f, 1000.0f, 150.0f, 0.1f, 0.45f);
        makeF(id("ratio"), 1.0f, 12.0f, 2.0f, 0.1f);
        makeF(id("knee"), 0.0f, 24.0f, 6.0f, 0.1f);
        layout.add(std::make_unique<juce::AudioParameterChoice>(
            juce::ParameterID(id("detmode"),1), id("detmode"),
            juce::StringArray { "Wide", "Split" }, 1));''',
    "new dynamic APVTS parameters")

header=swap(header,
    '''        float envelope = 0.0f;
        float smoothedGain = 0.0f;
        bool wasActive = false;''',
    '''        float envelope = 0.0f;
        float smoothedGain = 0.0f;
        bool wasActive = false;
        bool detectorWasSplit = false;
        int detectorWasType = -1;
        // Fixed-size real-time safe gain-reduction frames (max 65536 samples
        // per host block at 32-sample intervals; no audio-thread allocations).
        std::array<float, 2048> dynamicFrames {};
        std::array<juce::dsp::IIR::Filter<float>, 2> detectorFilters;''',
    "DSP band detector state")

proc=swap(proc,
    '''        band.smoothedGain = 0.0f;
        band.wasActive = false;
        resetBandFilters(band);''',
    '''        band.smoothedGain = 0.0f;
        band.wasActive = false;
        band.detectorWasSplit = false;
        band.detectorWasType = -1;
        band.dynamicFrames.fill(0.0f);
        for (auto& detector : band.detectorFilters) detector.reset();
        resetBandFilters(band);''',
    "prepareToPlay reset detector")

# Per-band detector modes are only split for Self / DAW SC, because Cetus
# Link currently transfers a block envelope, not full-band audio samples.
start=proc.index("    constexpr int controlBlock = 32;")
end=proc.index('    const float output = readParam("output");', start)
engine=r'''    constexpr int controlBlock = 32;
    constexpr int maxControlFrames = 2048;
    const float maxFrequency = static_cast<float>(currentSampleRate * 0.475);
    const int controlCount = (samples + controlBlock - 1) / controlBlock;

    // PASS 1 - Analyze untouched input for every band BEFORE any EQ is applied.
    // This prevents earlier EQ bands from affecting later band detectors.
    const juce::AudioBuffer<float>* sidechainBuffer = nullptr;
    const bool hasSidechain = source==5 && getBusCount(true)>1 && getBus(true,1)->isEnabled();
    // Construct a non-owning JUCE bus view; avoid AudioBuffer copy assignment
    // or allocations on the real-time audio thread.
    auto sidechainView = hasSidechain ? getBusBuffer(buffer,true,1) : juce::AudioBuffer<float>();
    if (sidechainView.getNumChannels()>0) sidechainBuffer=&sidechainView;
    for (int i=0; i<numBands; ++i) {
        auto& b = bands[static_cast<size_t>(i)];
        if (!isBandEnabled(i) || !isBandDynamicEnabled(i)) {
            b.dynamicFrames.fill(0.0f);
            continue;
        }
        const int type = getBandType(i);
        const int mode = getBandMode(i);
        const float freq = juce::jlimit(20.0f, juce::jmax(21.0f,maxFrequency),getBandFrequency(i));
        const float q = juce::jlimit(0.25f, 12.0f, getBandQ(i));
        const bool split = readParam(param(i,"detmode")) > 0.5f && (source == 0 || source == 5);
        if (split != b.detectorWasSplit || type != b.detectorWasType) {
            for (auto& f:b.detectorFilters) f.reset();
            b.detectorWasSplit = split;
            b.detectorWasType = type;
        }
        if (split) {
            using Coeff = juce::dsp::IIR::Coefficients<float>;
            Coeff::Ptr coeff;
            if (type == 1)
                coeff = Coeff::makeLowPass(currentSampleRate,freq,0.70710678f);
            else if (type == 2)
                coeff = Coeff::makeHighPass(currentSampleRate,freq,0.70710678f);
            else
                coeff = Coeff::makeBandPass(currentSampleRate,freq,q);
            for (auto& f:b.detectorFilters) f.coefficients = coeff;
        }
        const float attackSeconds = juce::jmax(0.0001f,readParam(param(i,"atk"))*0.001f);
        const float releaseSeconds = juce::jmax(0.0001f,readParam(param(i,"rel"))*0.001f);
        const float aCoeff = std::exp(-1.0f/(static_cast<float>(currentSampleRate)*attackSeconds));
        const float rCoeff = std::exp(-1.0f/(static_cast<float>(currentSampleRate)*releaseSeconds));
        const float threshold = getBandThreshold(i);
        const float range = getBandRange(i);
        const float ratio = juce::jmax(1.0f,readParam(param(i,"ratio")));
        const float knee = juce::jmax(0.0f,readParam(param(i,"knee")));
        const float slope = 1.0f-1.0f/ratio;
        for (int block=0;block<controlCount;++block) {
            const int offset=block*controlBlock;
            const int length=juce::jmin(controlBlock,samples-offset);
            for (int n=offset;n<offset+length;++n) {
                float detectorLevel=0.0f;
                if (source>=1 && source<=4) {
                    // Cetus Link provides a scalar detector level, so Split
                    // automatically behaves as Wide for linked sources.
                    detectorLevel=juce::jmax(0.0f,detectorPeak);
                } else if (source == 5 && sidechainBuffer == nullptr) {
                    detectorLevel=0.0f;
                } else {
                    const auto& input = source==5 ? *sidechainBuffer : main;
                    const int nc=input.getNumChannels();
                    const float left=input.getSample(0,n);
                    const float right=nc>1?input.getSample(1,n):left;
                    if (mode == CetusEQ::mid && nc>1) {
                        float mid=0.5f*(left+right);
                        if (split) mid=b.detectorFilters[0].processSample(mid);
                        detectorLevel=std::abs(mid);
                    } else if (mode == CetusEQ::side && nc>1) {
                        float side=0.5f*(left-right);
                        if (split) side=b.detectorFilters[0].processSample(side);
                        detectorLevel=std::abs(side);
                    } else {
                        const float l=split?b.detectorFilters[0].processSample(left):left;
                        const float r=nc>1?
                            (split?b.detectorFilters[1].processSample(right):right):l;
                        // Stereo RMS-like sample level (not block-wide peak).
                        detectorLevel=std::sqrt(0.5f*(l*l+r*r));
                    }
                }
                const float k=detectorLevel>b.envelope ? aCoeff : rCoeff;
                b.envelope=k*b.envelope+(1.0f-k)*detectorLevel;
            }
            const float levelDb=juce::Decibels::gainToDecibels(
                juce::jmax(1.0e-9f,b.envelope),-120.0f);
            const float over=levelDb-threshold;
            float compression=0.0f;
            if (knee<0.001f)
                compression=juce::jmax(0.0f,over)*slope;
            else if (over>=0.5f*knee)
                compression=over*slope;
            else if (over>-0.5f*knee) {
                const float transition=over+0.5f*knee;
                compression=slope*transition*transition/(2.0f*knee);
            }
            const float reduction=juce::jlimit(0.0f,std::abs(range),compression);
            b.dynamicFrames[static_cast<size_t>(juce::jmin(block,maxControlFrames-1))]
                =std::copysign(reduction,range);
        }
    }

    // PASS 2 - Equalize with detector-derived GR at 32-sample intervals.
    // 4 ms smoothing is for coefficient continuity, not added lookahead.
    for (int i = 0; i < numBands; ++i) {
        auto& b = bands[static_cast<size_t>(i)];
        if (!isBandEnabled(i)) {
            if (b.wasActive) resetBandFilters(b);
            b.wasActive=false;
            b.smoothedGain=0.0f;
            meterDynGain[static_cast<size_t>(i)].store(0.0f,std::memory_order_relaxed);
            continue;
        }
        const float freq=juce::jlimit(20.0f,juce::jmax(21.0f,maxFrequency),getBandFrequency(i));
        const float q=getBandQ(i);
        const float staticGain=getBandGain(i);
        const int filterType=getBandType(i);
        const int mode=getBandMode(i);
        const int slopeIndex=getBandSlopeIndex(i);
        const bool dynamicEnabled=isBandDynamicEnabled(i);
        const bool gainFilter=CetusEQ::isGainFilter(filterType);
        const int stages=CetusEQ::stageCountForTypeAndSlope(filterType,slopeIndex);
        if (gainFilter && std::abs(staticGain)<0.0001f && !dynamicEnabled
            && std::abs(b.smoothedGain)<0.0005f) {
            if (b.wasActive) resetBandFilters(b);
            b.wasActive=false;b.smoothedGain=0.0f;
            meterDynGain[static_cast<size_t>(i)].store(0.0f,std::memory_order_relaxed);
            continue;
        }

        for (int offset=0,block=0;offset<samples;offset+=controlBlock,++block) {
            const int length=juce::jmin(controlBlock,samples-offset);
            const float dt=static_cast<float>(length/currentSampleRate);
            const float dynamic=dynamicEnabled
                ? b.dynamicFrames[static_cast<size_t>(juce::jmin(block,maxControlFrames-1))] : 0.0f;
            const float desiredGain=staticGain+dynamic;
            const float k=std::exp(-dt/0.004f);
            b.smoothedGain=k*b.smoothedGain+(1.0f-k)*desiredGain;
            auto coeff=CetusEQ::makeCoefficients(currentSampleRate,freq,q,b.smoothedGain,filterType);
            for (int stage=0;stage<stages;++stage)
                for (int lane=0;lane<2;++lane)
                    b.filters[static_cast<size_t>(lane)][static_cast<size_t>(stage)].coefficients=coeff;
            if (mode == CetusEQ::stereo || channels<2) {
                for (int c=0;c<channels;++c) {
                    auto* data=main.getWritePointer(c)+offset;
                    for (int n=0;n<length;++n) {
                        float sample=data[n];
                        for (int stage=0;stage<stages;++stage)
                            sample=b.filters[static_cast<size_t>(c)][static_cast<size_t>(stage)].processSample(sample);
                        data[n]=sample;
                    }
                }
            } else {
                auto* left=main.getWritePointer(0)+offset;
                auto* right=main.getWritePointer(1)+offset;
                for (int n=0;n<length;++n) {
                    const float mid=0.5f*(left[n]+right[n]);
                    const float side=0.5f*(left[n]-right[n]);
                    float midOut=mid,sideOut=side;
                    if (mode==CetusEQ::mid) {
                        for (int stage=0;stage<stages;++stage)
                            midOut=b.filters[0][static_cast<size_t>(stage)].processSample(midOut);
                    } else {
                        for (int stage=0;stage<stages;++stage)
                            sideOut=b.filters[0][static_cast<size_t>(stage)].processSample(sideOut);
                    }
                    left[n]=midOut+sideOut;
                    right[n]=midOut-sideOut;
                }
            }
            b.wasActive=true;
        }
        // Actual gain reduction AFTER smoothing, not raw target detector gain.
        meterDynGain[static_cast<size_t>(i)].store(
            dynamicEnabled ? b.smoothedGain-staticGain : 0.0f,
            std::memory_order_relaxed);
    }

'''
proc=proc[:start]+engine+proc[end:]
proc=swap(proc,
    '''        setParameterActual(param(b, "rel"), 150.0f);''',
    '''        setParameterActual(param(b, "rel"), 150.0f);
        setParameterActual(param(b, "ratio"), 2.0f);
        setParameterActual(param(b, "knee"), 6.0f);
        setParameterActual(param(b, "detmode"), 1.0f);''',
    "factory init new dynamics defaults")

# GUI controls use one band attachment and preserve existing preset/history
# machinery (new fields are APVTS parameters).
guih=swap(guih,
    '    juce::ComboBox presets, send, listen, bandType, bandMode, hudType;',
    '    juce::ComboBox presets, send, listen, bandType, bandMode, hudType, detectorMode;',
    "GUI detector mode")
guih=swap(guih,
    '    juce::TextButton analyzerReferenceButton {"Ref 0dB"};',
    '''    juce::TextButton analyzerReferenceButton {"Ref 0dB"};
    juce::TextButton ratioButton {"Ratio 2:1"}, kneeButton {"Knee 6dB"};''',
    "GUI ratio/knee")
guih=swap(guih,
    '    void updateSmoothingText();',
    '''    void updateSmoothingText();
    void syncDynamicAdvancedButtons();''',
    "GUI button sync method")

gui=swap(gui,
    '''                  &analyzerRangeButton,&analyzerTiltButton,&analyzerReferenceButton}) addButton(*b);''',
    '''                  &analyzerRangeButton,&analyzerTiltButton,&analyzerReferenceButton,
                  &ratioButton,&kneeButton}) addButton(*b);''',
    "add ratio knee buttons")
gui=swap(gui,
    '    for(auto* c:{&presets,&send,&listen,&bandType,&bandMode,&hudType}) addCombo(*c);',
    '    for(auto* c:{&presets,&send,&listen,&bandType,&bandMode,&hudType,&detectorMode}) addCombo(*c);',
    "add detector GUI dropdown")
gui=swap(gui,
    '''    listen.addItemList({"Self","Link 1","Link 2","Link 3","Link 4","DAW SC"},1);''',
    '''    listen.addItemList({"Self","Link 1","Link 2","Link 3","Link 4","DAW SC"},1);
    detectorMode.addItemList({"Wide","Split"},1);
    detectorMode.setSelectedId(2,juce::dontSendNotification);
    detectorMode.setTooltip("Per-band dynamic detector: Split tracks band frequencies, Wide tracks full-range signal. Cetus Link uses Wide scalar detector.");
    ratioButton.setTooltip("Per-band compression ratio: cycles 1, 2, 3, 4, 6, 8, 12 to 1.");
    kneeButton.setTooltip("Per-band soft-knee width: cycles 0, 3, 6, 9, 12 dB.");''',
    "GUI dropdown options")
gui=swap(gui,
    '''    placeDesignChild(listen,    {644,388,122,28});''',
    '''    placeDesignChild(listen,    {644,388,122,28});
    placeDesignChild(detectorMode, {790,388,142,28});''',
    "place detector mode")
gui=swap(gui,
    '''    placeDesignChild(analyzerReferenceButton,{696,536,82,23});''',
    '''    placeDesignChild(analyzerReferenceButton,{696,536,82,23});
    placeDesignChild(ratioButton,            {784,536,74,23});
    placeDesignChild(kneeButton,             {864,536,76,23});''',
    "place ratio knee buttons")
gui=swap(gui,
    '''    g.drawText("DETECTOR SOURCE",644,374,118,12,juce::Justification::centredLeft);''',
    '''    g.drawText("DETECTOR SOURCE",644,374,118,12,juce::Justification::centredLeft);
    g.drawText("DETECTOR MODE",790,374,142,12,juce::Justification::centredLeft);''',
    "paint detector mode label")
gui=swap(gui,
    '''    g.drawText("8-BAND / STEREO - MID - SIDE",704,541,231,14,juce::Justification::centredRight);''',
    '''    // Former static footer is replaced by actual selected-band gain reduction
    // at the graph, leaving space for ratio and knee controls.''',
    "remove overlapped footer label")
gui=swap(gui,
    '''    g.drawText("STATIC",chart.getX()+16,chart.getY()+7,47,15,juce::Justification::centredLeft);''',
    '''    g.drawText("STATIC",chart.getX()+16,chart.getY()+7,47,15,juce::Justification::centredLeft);
    const float actualGR=processor.getBandDynamicGain(selectedBand);
    g.setColour(juce::Colour::fromRGB(95,239,232));
    g.setFont(juce::FontOptions(10.2f,juce::Font::bold));
    g.drawText("GR "+juce::String(actualGR,1)+" dB",
               chart.getX()+116,chart.getY()+5,122,17,
               juce::Justification::centredRight);''',
    "selected-band real GR readout")
gui=swap(gui,
    '''    else if(button==&analyzerReferenceButton) {
        analyzerReferenceIndex=(analyzerReferenceIndex+1)%3;
        const int references[]={0,-12,-24};
        analyzerReferenceButton.setButtonText("Ref "+juce::String(references[analyzerReferenceIndex])+"dB");
    }''',
    '''    else if(button==&analyzerReferenceButton) {
        analyzerReferenceIndex=(analyzerReferenceIndex+1)%3;
        const int references[]={0,-12,-24};
        analyzerReferenceButton.setButtonText("Ref "+juce::String(references[analyzerReferenceIndex])+"dB");
    }
    else if(button==&ratioButton) {
        constexpr float ratios[]={1.0f,2.0f,3.0f,4.0f,6.0f,8.0f,12.0f};
        const float current=processor.readParam(CetusproEQAudioProcessor::param(selectedBand,"ratio"));
        int next=0;
        for(int i=0;i<7;++i)if(current>=ratios[i]-.05f)next=i+1;
        processor.setParameterActual(CetusproEQAudioProcessor::param(selectedBand,"ratio"),ratios[next%7]);
        syncDynamicAdvancedButtons();requestHistorySnapshot();
    }
    else if(button==&kneeButton) {
        constexpr float knees[]={0.0f,3.0f,6.0f,9.0f,12.0f};
        const float current=processor.readParam(CetusproEQAudioProcessor::param(selectedBand,"knee"));
        int next=0;
        for(int i=0;i<5;++i)if(current>=knees[i]-.05f)next=i+1;
        processor.setParameterActual(CetusproEQAudioProcessor::param(selectedBand,"knee"),knees[next%5]);
        syncDynamicAdvancedButtons();requestHistorySnapshot();
    }''',
    "ratio knee button callbacks")
gui=swap(gui,
    '''    } else if(c==&bandMode||c==&send||c==&listen)requestHistorySnapshot();''',
    '''    } else if(c==&detectorMode) {
        processor.setParameterActual(CetusproEQAudioProcessor::param(selectedBand,"detmode"),
            (float)juce::jmax(0,detectorMode.getSelectedId()-1));
        requestHistorySnapshot();
    } else if(c==&bandMode||c==&send||c==&listen)requestHistorySnapshot();''',
    "GUI detmode callback")
gui=swap(gui,
    '''void CetusproEQAudioProcessorEditor::updateSmoothingText(){smoothButton.setButtonText(smoothingMode==0?"Smooth Off":smoothingMode==1?"1/6 Oct":"1/3 Oct");}''',
    '''void CetusproEQAudioProcessorEditor::updateSmoothingText(){smoothButton.setButtonText(smoothingMode==0?"Smooth Off":smoothingMode==1?"1/6 Oct":"1/3 Oct");}
void CetusproEQAudioProcessorEditor::syncDynamicAdvancedButtons() {
    const auto id=[this](const char* part){return CetusproEQAudioProcessor::param(selectedBand,part);};
    const float ratio=processor.readParam(id("ratio"));
    const float knee=processor.readParam(id("knee"));
    ratioButton.setButtonText("Ratio "+juce::String(ratio,1)+":1");
    kneeButton.setButtonText("Knee "+juce::String(knee,1)+"dB");
    const int det=juce::jlimit(0,1,juce::roundToInt(processor.readParam(id("detmode"))));
    if(detectorMode.getSelectedId()!=det+1)
        detectorMode.setSelectedId(det+1,juce::dontSendNotification);
}''',
    "advanced button sync method")
gui=swap(gui,
    '''    const int type=processor.getBandType(selectedBand);
    syncVisualEnableState();''',
    '''    const int type=processor.getBandType(selectedBand);
    syncVisualEnableState();
    syncDynamicAdvancedButtons();''',
    "advanced button selection refresh via timer")
assert gui.count("v0.5.16")>=2
gui=gui.replace("v0.5.16","v0.5.17")
config=cm.read_text(encoding="utf8")
assert config.count("VERSION 0.5.16")==1
config=config.replace("VERSION 0.5.16","VERSION 0.5.17",1)

# GUIs and audio are deliberately separated; old exact icon assets, 8-band
# configuration, HQ spectrum and Cetus Link sender/receiver remain present.
for token in ("BinaryData::CetusUndo_png","BinaryData::CetusRedo_png",
              'g.drawText("ZERO LATENCY"', "spectrumDb.fill(-96.0f)",
              'CetusEQ::makeCoefficients', 'CetusLink::send',
              'CetusLink::read', 'getBusBuffer(buffer, true, 0)'):
    if token not in gui+proc:raise RuntimeError("Existing feature lost: "+token)
# This is the first intentional DSP change after v0.5.12.
for path,source in [(p,proc),(h,header),(e,gui),(eh,guih),(cm,config)]:
    path.write_text(source,encoding="utf8")
print("v0.5.17: per-band Split/Wide detector, sample envelope, Ratio/Knee, actual GR, preserved filters/UI")
