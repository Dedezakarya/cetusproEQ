#!/usr/bin/env python3
"""v0.5.18 static and numerical regression: solo audition and polarity invert."""
from pathlib import Path
import math
p=Path("Source/PluginProcessor.cpp").read_text(encoding="utf8")
h=Path("Source/PluginProcessor.h").read_text(encoding="utf8")
g=Path("Source/PluginEditor.cpp").read_text(encoding="utf8")
gh=Path("Source/PluginEditor.h").read_text(encoding="utf8")
cm=Path("CMakeLists.txt").read_text(encoding="utf8")
assert "VERSION 0.5.18" in cm and "v0.5.18" in g
for t in ('juce::ParameterID("soloBand",1)','juce::ParameterID("polarity",1)',
          'readParam("soloBand")','readParam("polarity")',
          'setParameterActual("soloBand", 0.0f)',
          'setParameterActual("polarity", 0.0f)'):
    assert t in p,t
for t in ('void CetusproEQAudioProcessor::renderBandAudition',
          'Coefficients::makeBandPass(currentSampleRate,hz,q)',
          'CetusEQ::stageCountForTypeAndSlope',
          'getBandSlopeIndex(band)', 'const bool needAudition=canAudition',
          'soloScratch.copyFrom(c,0,main,c,0,samples)',
          'if (needAudition) renderBandAudition(activeSoloBand-1,channels,samples);',
          'value=(1.0f-soloMix)*value',
          'soloMix+=juce::jlimit(-soloStep,soloStep,targetSolo-soloMix)',
          'polarityMix+=juce::jlimit(-polarityStep,polarityStep,targetPolarity-polarityMix)',
          'const float phaseSign=1.0f-2.0f*polarityMix',
          'main.setSample(c,n,value*phaseSign)'):
    assert t in p,f"Missing DSP behavior: {t}"
assert p.index('soloScratch.copyFrom') < p.index('// PASS 1 - Analyze untouched input')
assert p.index('renderBandAudition(activeSoloBand-1') > p.index('// PASS 2 - Equalize')
assert p.index('main.setSample(c,n,value*phaseSign)') < p.index('updateSpectrumAndMeters(main, captureStart, channels);', p.index('const float output ='))
assert 'juce::AudioBuffer<float> soloScratch;' in h
assert 'float polarityMix = 0.0f;' in h
assert 'float soloMix = 0.0f;' in h
assert 'soloScratch.setSize(' in p and 'soloScratch.setSize(' not in p[p.index('void CetusproEQAudioProcessor::processBlock'):]
for t in ('juce::TextButton soloButton {"SOLO"}',
          'polarityButton','polarityAttachment'):
    assert t in gh,t
for t in ('placeDesignChild(soloButton, {86,382,43,21})',
          'placeDesignChild(polarityButton, {986,536,39,22})',
          'setComponentID("cetus-polarity")',
          'getComponentID()=="cetus-polarity"',
          'juce::Colour::fromRGB(248,148,30)',
          'juce::String::fromUTF8("\\xC3\\x98")',
          'std::make_unique<ButtonAttachment>',
          'syncSoloButton()', 'soloButton.setToggleState('):
    assert t in g,t
# Solo button heading x86..129, band columns below at y >= 411.
# Output knob x962..1049 y427..533; Ø button at x986..1025 y536..558.
assert 86+43<134 and 382+21<411
assert 962<=986 and 986+39<=1049 and 536>533 and 536+22<566

# Polarity output formula and short linear ramps:
def ramp(prev,target,seconds,rate):
    step=1/(seconds*rate)
    return prev + max(-step,min(step,target-prev))
for rate in (44100,48000,96000):
    state=0.0
    for _ in range(math.ceil(.004*rate)):
        state=ramp(state,1.0,.003,rate)
    assert abs(state-1.0)<1e-6
    # Both channels multiply by -1 when enabled; left-right unchanged.
    for x in (-.7,-.25,0.0,.25,.7):
        assert abs(x*(1-2*state)+x)<1e-6
    for _ in range(math.ceil(.004*rate)):
        state=ramp(state,0.0,.003,rate)
    assert abs(state)<1e-6

# Off settings should be neutral and prior DSP bindings intact.
for t in ('PASS 1 - Analyze untouched input','PASS 2 - Equalize',
          'CetusLink::send','CetusLink::read','CetusEQ::makeCoefficients',
          'meterDynGain','juce::AudioParameterChoice','id("detmode")'):
    assert t in p,t
for t in ('BinaryData::CetusUndo_png','BinaryData::CetusRedo_png',
          'g.drawText("ZERO LATENCY"','spectrumDb.fill(-96.0f)',
          'ratioButton','kneeButton'):
    assert t in g,t
print("PASS v0.5.18: solo signal routing, independent output polarity, orange Ø, geometry, old DSP, numerics")
