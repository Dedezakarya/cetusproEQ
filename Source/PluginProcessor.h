#pragma once
#include <JuceHeader.h>
#include "CetusLink.h"
#include <array>

class CetusproEQAudioProcessor final : public juce::AudioProcessor {
public:
    CetusproEQAudioProcessor();
    ~CetusproEQAudioProcessor() override = default;
    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }
    const juce::String getName() const override { return "cetusproEQ"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return "Default"; }
    void changeProgramName(int, const juce::String&) override {}
    bool isBusesLayoutSupported(const BusesLayout&) const override;
    void getStateInformation(juce::MemoryBlock&) override;
    void setStateInformation(const void*, int) override;
    juce::AudioProcessorValueTreeState parameters;
    static juce::AudioProcessorValueTreeState::ParameterLayout createLayout();
    static juce::String param(int band, const char* suffix) { return "b" + juce::String(band + 1) + suffix; }
    float getBandFrequency(int b) const { return *parameters.getRawParameterValue(param(b,"freq")); }
    float getBandGain(int b) const { return *parameters.getRawParameterValue(param(b,"gain")); }
    float getBandQ(int b) const { return *parameters.getRawParameterValue(param(b,"q")); }
private:
    struct Band {
        std::array<juce::dsp::IIR::Filter<float>, 2> filter;
        float envelope = 0.0f;
        float smoothedGain = 0.0f;
    };
    std::array<Band,6> bands;
    double currentSampleRate = 48000.0;
    uint64_t lastLinkUpdate = 0;
    float outputLevel = 0.0f;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CetusproEQAudioProcessor)
};
