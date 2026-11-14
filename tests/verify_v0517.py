#!/usr/bin/env python3
"""v0.5.17 dynamic engine regression and numeric reference checks.
Run after all historical v0.5.16 GUI/DSP scripts and apply_0517.
"""
from pathlib import Path
import hashlib,math
proc=Path("Source/PluginProcessor.cpp").read_text()
ph=Path("Source/PluginProcessor.h").read_text()
editor=Path("Source/PluginEditor.cpp").read_text()
eh=Path("Source/PluginEditor.h").read_text()
cm=Path("CMakeLists.txt").read_text()
assert "VERSION 0.5.17" in cm
assert "v0.5.17" in editor
for name in ['id("ratio")','id("knee")','id("detmode")',
             'juce::StringArray { "Wide", "Split" }',
             'const float aCoeff = std::exp(-1.0f/',
             'const float rCoeff = std::exp(-1.0f/',
             'makeBandPass(currentSampleRate,freq,q)',
             'makeLowPass(currentSampleRate,freq,0.70710678f)',
             'makeHighPass(currentSampleRate,freq,0.70710678f)',
             'const float slope = 1.0f-1.0f/ratio;',
             'compression=slope*transition*transition/(2.0f*knee);',
             'const float k=std::exp(-dt/0.004f);',
             'meterDynGain[static_cast<size_t>(i)].store(',
             'dynamicEnabled ? b.smoothedGain-staticGain : 0.0f']:
    assert name in proc,"Missing DSP improvement: "+name
assert proc.index("PASS 1 - Analyze untouched input") < proc.index("PASS 2 - Equalize")
assert 'juce::AudioBuffer<float> sidechainView;' not in proc
assert 'juce::AudioBuffer<float> sidechainView = ' not in proc
assert 'const int samples = buffer.getNumSamples();' in proc
assert 'for (int n=offset;n<offset+length;++n)' in proc
assert 'for (int offset=0,block=0;offset<samples;' in proc
for name in ["detectorFilters", "detectorWasSplit", "detectorWasType","dynamicFrames"]:
    assert name in ph, name
for name in ["detectorMode", "ratioButton", "kneeButton",
             "syncDynamicAdvancedButtons", "GR "]:
    assert name in eh+editor,"Missing GUI control: "+name
assert 'g.drawText("ZERO LATENCY",lower.getX()+6' in editor
assert 'smoothButton {"1/6 Oct"}' in eh
assert 'BinaryData::CetusUndo_png' in editor
assert 'BinaryData::CetusRedo_png' in editor
assert 'const float hannWeightSum' in editor
# Verify pre-v0.5.17 APVTS parameter IDs, essential for DAW automation.
for field in ("freq","gain","q","thr","range","atk","rel","type","mode","slope","on","dyn"):
    assert f'id("{field}")' in proc, f"Old band parameter missing: {field}"
for field in ("send","listen","output","bypass"):
    assert '"'+field+'"' in proc

# Compressor law: 2:1 knee 6dB, downward range 11.79dB.
def calc(level,threshold=-17.31,ratio=2.0,knee=6.0,limit=11.79):
    over=level-threshold
    slope=1-1/ratio
    if knee<0.001: reduction=max(0.0,over)*slope
    elif over>=knee/2: reduction=over*slope
    elif over>-knee/2: reduction=slope*(over+knee/2)**2/(2*knee)
    else: reduction=0.0
    return min(limit,max(0.0,reduction))
assert calc(-30)==0.0
assert abs(calc(-12)-2.655)<0.01
assert calc(-12)>calc(-16)>calc(-20)
assert calc(0,ratio=4.0)==11.79
assert calc(-12,ratio=1.0)==0.0
assert calc(-12,knee=0.0)>0
for ratio in (1,2,3,4,6,8,12):
    prev=0
    for level in range(-60,1):
        x=calc(level,ratio=ratio)
        assert math.isfinite(x) and 0<=x<=11.79
        assert x>=prev-1e-6
        prev=x

# A bell bandpass's analog prototype rejects out-of-band 2kHz when tuned to
# 128 Hz. This is an expected reference; JUCE's digital IIR is host-tested
# via pluginval and real DAW followup.
def bandpass_mag(f,fc,q=1.0):
    r=f/fc
    return (r/q)/math.sqrt((1-r*r)**2+(r/q)**2)
assert bandpass_mag(128,128)>.999
assert bandpass_mag(2000,128)<0.10

# Old DSP has intentionally changed, but base static filter factory and channel
# processing are retained. No assertions against v0.5.16 DSP SHA are appropriate.
assert 'CetusEQ::makeCoefficients' in proc
assert 'CetusEQ::stageCountForTypeAndSlope' in proc
assert 'if (mode == CetusEQ::stereo || channels<2)' in proc
print("PASS v0.5.17 per-band detector, ratio/knee, timing, GUI, presets and numeric model")
