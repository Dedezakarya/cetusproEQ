#pragma once
#include <JuceHeader.h>
#include "CetusLink.h"
#include "CetusEQFilters.h"
#include <cmath>
#include <array>
#include <atomic>
#include <cstdint>

class CetusproEQAudioProcessor final : public juce::AudioProcessor {
public:
    static constexpr int numBands = 8;
    static constexpr int spectrumOrder = 11;
    static constexpr int spectrumSize = 1 << spectrumOrder;
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
    void resetFlat();
    bool copySpectrum(std::array<float,spectrumSize>& samples, bool post) const noexcept;
    double spectrumSampleRate() const noexcept { return visualSampleRate.load(std::memory_order_relaxed); }
    juce::AudioProcessorValueTreeState parameters;
    static juce::AudioProcessorValueTreeState::ParameterLayout createLayout();
    static juce::String param(int band, const char* suffix) { return "b" + juce::String(band + 1) + suffix; }
    int getBandType(int b) const { return juce::roundToInt(parameters.getRawParameterValue(param(b,"type"))->load()); }
    bool isBandEnabled(int b) const { return parameters.getRawParameterValue(param(b,"on"))->load() > 0.5f; }
    bool isBandDynamic(int b) const {
        return CetusEQ::canProcessDynamics(getBandType(b))
            && parameters.getRawParameterValue(param(b,"dyn"))->load() > 0.5f
            && std::abs(parameters.getRawParameterValue(param(b,"range"))->load()) > 0.001f;
    }
    float getOutputPeak(int channel) const { return meterOutputs[static_cast<size_t>(juce::jlimit(0,1,channel))].load(std::memory_order_relaxed); }
    float getBandDynGain(int b) const { return meterDynamicGain[static_cast<size_t>(b)].load(std::memory_order_relaxed); }
    float getBandFrequency(int b) const { return *parameters.getRawParameterValue(param(b,"freq")); }
    float getBandGain(int b) const { return *parameters.getRawParameterValue(param(b,"gain")); }
    float getBandQ(int b) const { return *parameters.getRawParameterValue(param(b,"q")); }
private:
    struct Band {
        std::array<juce::dsp::IIR::Filter<float>, 2> filter;
        float envelope = 0.0f;
        float smoothedGain = 0.0f;
    };
    std::array<Band,numBands> bands;
    std::array<std::atomic<float>,2> meterOutputs {};
    std::array<std::atomic<float>,numBands> meterDynamicGain {};
    std::array<std::atomic<float>,spectrumSize> spectrumBefore {};
    std::array<std::atomic<float>,spectrumSize> spectrumAfter {};
    std::atomic<uint64_t> spectrumBeforeCount {0}, spectrumAfterCount {0};
    std::atomic<double> visualSampleRate {48000.0};
    void captureSpectrum(const juce::AudioBuffer<float>& data, int channels, bool post) noexcept;
    double currentSampleRate = 48000.0;
    uint64_t lastLinkUpdate = 0;
    float outputLevel = 0.0f;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CetusproEQAudioProcessor)
};
