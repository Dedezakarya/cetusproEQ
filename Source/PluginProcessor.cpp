#include "PluginProcessor.h"
#include "PluginEditor.h"
#include <cmath>
#include <algorithm>

CetusproEQAudioProcessor::CetusproEQAudioProcessor()
: juce::AudioProcessor(juce::AudioProcessor::BusesProperties()
    .withInput("Input", juce::AudioChannelSet::stereo(), true)
    .withInput("Sidechain", juce::AudioChannelSet::stereo(), false)
    .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
  parameters(*this, nullptr, "PARAMETERS", createLayout()) {}

juce::AudioProcessorValueTreeState::ParameterLayout CetusproEQAudioProcessor::createLayout() {
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    using APF = juce::AudioParameterFloat;
    using API = juce::AudioParameterInt;
    using APB = juce::AudioParameterBool;
    auto makeF = [&layout](const juce::String& id, float low, float high, float def, float step = 0.01f, float skew = 1.0f) {
        layout.add(std::make_unique<APF>(juce::ParameterID(id,1), id,
            juce::NormalisableRange<float>(low, high, step, skew), def));
    };
    for (int b=0; b<numBands; ++b) {
        auto id = [b](const char* s) { return param(b,s); };
        const float freqs[numBands] = { 35, 80, 180, 420, 1000, 2500, 6000, 12000 };
        makeF(id("freq"), 20, 20000, freqs[b], 0.01f, 0.28f);
        makeF(id("gain"), -18, 18, 0);
        makeF(id("q"), 0.2f, 12, 1, 0.01f, 0.5f);
        makeF(id("thr"), -60, 0, -24);
        makeF(id("range"), -18, 18, 0);
        makeF(id("atk"), 0.1f, 200, 10, 0.1f, 0.45f);
        makeF(id("rel"), 5, 1000, 150, 0.1f, 0.45f);
        layout.add(std::make_unique<juce::AudioParameterChoice>(juce::ParameterID(id("type"),1), id("type"),
            juce::StringArray{"Bell","Low Shelf","High Shelf","High Pass","Low Pass","Notch"},0));
        layout.add(std::make_unique<APB>(juce::ParameterID(id("on"),1), id("on"), true));
        layout.add(std::make_unique<APB>(juce::ParameterID(id("dyn"),1), id("dyn"), false));
    }
    layout.add(std::make_unique<API>(juce::ParameterID("send",1), "Cetus Link Send", 0, 4, 0));
    layout.add(std::make_unique<API>(juce::ParameterID("listen",1), "Detector Source (0=Self, 1-4=Link, 5=DAW)", 0, 5, 0));
    makeF("output", -24, 24, 0);
    layout.add(std::make_unique<APB>(juce::ParameterID("bypass",1), "Bypass", false));
    return layout;
}

bool CetusproEQAudioProcessor::isBusesLayoutSupported(const BusesLayout& layout) const {
    auto main = layout.getMainOutputChannelSet();
    if (main != juce::AudioChannelSet::mono() && main != juce::AudioChannelSet::stereo()) return false;
    if (layout.getMainInputChannelSet() != main) return false;
    if (layout.inputBuses.size() > 1) {
        auto sc = layout.inputBuses[1];
        if (sc != juce::AudioChannelSet::disabled() && sc != juce::AudioChannelSet::mono() && sc != juce::AudioChannelSet::stereo()) return false;
    }
    return true;
}

void CetusproEQAudioProcessor::prepareToPlay(double rate, int) {
    currentSampleRate = rate > 0 ? rate : 48000.0;
    visualSampleRate.store(currentSampleRate, std::memory_order_relaxed);
    spectrumBeforeCount.store(0, std::memory_order_relaxed);
    spectrumAfterCount.store(0, std::memory_order_relaxed);
    lastLinkUpdate = 0;
    outputLevel = 0.0f;
    for (auto& gain : meterDynamicGain) gain.store(0.0f, std::memory_order_relaxed);
    for (auto& band : bands) {
        band.envelope=0;
        band.smoothedGain=0;
        for (auto& f : band.filter) f.reset();
    }
}

static float peakValue(const juce::AudioBuffer<float>& buf, int channels, int samples) noexcept {
    float peak = 0;
    for (int c=0; c<channels; ++c) {
        auto* data=buf.getReadPointer(c);
        for (int n=0; n<samples; ++n) peak = juce::jmax(peak,std::abs(data[n]));
    }
    return peak;
}

void CetusproEQAudioProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&) {
    juce::ScopedNoDenormals noDenormals;
    const int samples = buffer.getNumSamples();
    const int channels = getMainBusNumInputChannels();
    if (samples == 0 || channels == 0) return;
    auto main = getBusBuffer(buffer, true, 0);
    const float inputPeak = peakValue(main, channels, samples);
    captureSpectrum(main, channels, false);
    const int sendBus = juce::roundToInt(parameters.getRawParameterValue("send")->load());
    if (sendBus > 0) CetusLink::send(sendBus, inputPeak);
    if (parameters.getRawParameterValue("bypass")->load() > 0.5f) {
        for (auto& gain : meterDynamicGain) gain.store(0.0f, std::memory_order_relaxed);
        captureSpectrum(main, channels, true);
        return;
    }

    float detectorPeak = inputPeak;
    const int listenBus = juce::roundToInt(parameters.getRawParameterValue("listen")->load());
    if (listenBus >= 1 && listenBus <= 4) {
        bool fresh=false;
        const float fromLink = CetusLink::read(listenBus, lastLinkUpdate, fresh);
        // A sender may be processed after a receiver, so the last published
        // block can persist. Never fall back to the local source silently.
        detectorPeak = fromLink; // zero when no new sender block
    } else if (listenBus == 5) {
        detectorPeak = 0.0f;
        if (getBusCount(true) > 1 && getBus(true,1)->isEnabled()) {
            auto side = getBusBuffer(buffer, true, 1);
            detectorPeak = peakValue(side, side.getNumChannels(), samples);
        }
    }
    const float blockDuration = static_cast<float>(samples / currentSampleRate);
        const float nyquist = static_cast<float>(currentSampleRate * 0.5);

    for (int i=0; i<numBands; ++i) {
        auto& b = bands[static_cast<size_t>(i)];
        if (parameters.getRawParameterValue(param(i,"on"))->load() < 0.5f) {
            meterDynamicGain[static_cast<size_t>(i)].store(0.0f, std::memory_order_relaxed);
            b.smoothedGain = 0;
            for (auto& f : b.filter) f.reset();
            continue;
        }
        const float freq=juce::jlimit(20.0f,nyquist*0.95f,parameters.getRawParameterValue(param(i,"freq"))->load());
        const float q=parameters.getRawParameterValue(param(i,"q"))->load();
        const float staticGain=parameters.getRawParameterValue(param(i,"gain"))->load();
        const float threshold=parameters.getRawParameterValue(param(i,"thr"))->load();
        const float range=parameters.getRawParameterValue(param(i,"range"))->load();
        const int type=juce::roundToInt(parameters.getRawParameterValue(param(i,"type"))->load());
        const bool dynamicEnabled = CetusEQ::canProcessDynamics(type)
            && parameters.getRawParameterValue(param(i,"dyn"))->load() > 0.5f && std::abs(range) > 0.0001f;
        // A genuinely flat band MUST NOT colour audio. Skip the IIR entirely.
        if (CetusEQ::canProcessDynamics(type) && std::abs(staticGain) < 0.0001f && !dynamicEnabled && std::abs(b.smoothedGain) < 0.001f) {
            b.smoothedGain = 0.0f;
            meterDynamicGain[static_cast<size_t>(i)].store(0.0f, std::memory_order_relaxed);
            for (auto& filter : b.filter) filter.reset();
            continue;
        }
        const float attack=parameters.getRawParameterValue(param(i,"atk"))->load() * .001f;
        const float release=parameters.getRawParameterValue(param(i,"rel"))->load() * .001f;
        const float coefficient = std::exp(-blockDuration / juce::jmax(0.0001f, (detectorPeak > b.envelope ? attack : release)));
        b.envelope = coefficient*b.envelope + (1.0f-coefficient)*detectorPeak;
        const float envelopeDb = juce::Decibels::gainToDecibels(juce::jmax(1.0e-9f,b.envelope),-120.0f);
        float dynamicGain=0.0f;
        if (dynamicEnabled) {
            // 2:1 soft-ish knee (6 dB) with range cap. Range sign selects
            // downward cut (negative) or upward boost (positive) above threshold.
            const float over = envelopeDb - threshold;
            const float amount = juce::jlimit(0.0f, std::abs(range), (over + 3.0f) * 0.5f);
            dynamicGain = std::copysign(amount, range);
        }
        const float desiredGain = staticGain + dynamicGain;
        // Smoothing avoids abrupt jumps on transport and automation edits.
        const float smoothing = std::exp(-blockDuration / 0.015f);
        b.smoothedGain = smoothing*b.smoothedGain + (1.0f-smoothing)*desiredGain;
        meterDynamicGain[static_cast<size_t>(i)].store(dynamicEnabled ? (b.smoothedGain - staticGain) : 0.0f,
            std::memory_order_relaxed);
        auto coeff = CetusEQ::makeCoefficients(currentSampleRate, freq, q, b.smoothedGain, type);
        for (int c=0;c<channels;++c) {
            b.filter[static_cast<size_t>(c)].coefficients = coeff;
            auto* data=main.getWritePointer(c);
            for (int n=0;n<samples;++n)
                data[n] = b.filter[static_cast<size_t>(c)].processSample(data[n]);
        }
    }
    const float target = parameters.getRawParameterValue("output")->load();
    const float gain = juce::Decibels::decibelsToGain(target);
    if (std::abs(target) > 0.0001f) main.applyGain(gain);
    captureSpectrum(main, channels, true);
}

void CetusproEQAudioProcessor::captureSpectrum(const juce::AudioBuffer<float>& data, int channels, bool post) noexcept {
    auto& ring = post ? spectrumAfter : spectrumBefore;
    auto& count = post ? spectrumAfterCount : spectrumBeforeCount;
    const auto write = count.load(std::memory_order_relaxed);
    const int samples = data.getNumSamples();
    const float* left = data.getReadPointer(0);
    const float* right = channels > 1 ? data.getReadPointer(1) : left;
    for (int i = 0; i < samples; ++i) {
        const auto offset = static_cast<size_t>((write + static_cast<uint64_t>(i)) % spectrumSize);
        ring[offset].store(0.5f * (left[i] + right[i]), std::memory_order_relaxed);
    }
    count.store(write + static_cast<uint64_t>(samples), std::memory_order_release);
}

bool CetusproEQAudioProcessor::copySpectrum(std::array<float,spectrumSize>& samples, bool post) const noexcept {
    const auto& ring = post ? spectrumAfter : spectrumBefore;
    const auto& count = post ? spectrumAfterCount : spectrumBeforeCount;
    const uint64_t end = count.load(std::memory_order_acquire);
    if (end < spectrumSize) return false;
    for (int i = 0; i < spectrumSize; ++i) {
        const auto index = static_cast<size_t>((end - spectrumSize + static_cast<uint64_t>(i)) % spectrumSize);
        samples[static_cast<size_t>(i)] = ring[index].load(std::memory_order_relaxed);
    }
    return true;
}

void CetusproEQAudioProcessor::resetFlat() {
    const float frequencies[numBands] = { 35, 80, 180, 420, 1000, 2500, 6000, 12000 };
    auto assign = [this](const juce::String& id, float actual) {
        if (auto* p = parameters.getParameter(id)) {
            p->beginChangeGesture();
            p->setValueNotifyingHost(p->convertTo0to1(actual));
            p->endChangeGesture();
        }
    };
    for (int i = 0; i < numBands; ++i) {
        assign(param(i,"freq"),frequencies[i]);
        assign(param(i,"type"),0);
        assign(param(i,"gain"),0);
        assign(param(i,"q"),1);
        assign(param(i,"thr"),-24);
        assign(param(i,"range"),0);
        assign(param(i,"atk"),10);
        assign(param(i,"rel"),150);
        assign(param(i,"on"),1);
        assign(param(i,"dyn"),0);
    }
    assign("output",0);
    assign("send",0);
    assign("listen",0);
    assign("bypass",0);
}

void CetusproEQAudioProcessor::getStateInformation(juce::MemoryBlock& dst) {
    if (auto xml = parameters.copyState().createXml()) copyXmlToBinary(*xml,dst);
}
void CetusproEQAudioProcessor::setStateInformation(const void* data, int size) {
    if (auto xml=getXmlFromBinary(data,size))
        if (xml->hasTagName(parameters.state.getType())) parameters.replaceState(juce::ValueTree::fromXml(*xml));
}
juce::AudioProcessorEditor* CetusproEQAudioProcessor::createEditor() { return new CetusproEQAudioProcessorEditor(*this); }
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new CetusproEQAudioProcessor(); }
