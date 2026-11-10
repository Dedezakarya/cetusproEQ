#pragma once
#include "PluginProcessor.h"
#include <memory>
#include <vector>
#include <array>

class CetusproEQAudioProcessorEditor final : public juce::AudioProcessorEditor,
                                             private juce::Button::Listener,
                                             private juce::ComboBox::Listener,
                                             private juce::Timer {
public:
    explicit CetusproEQAudioProcessorEditor(CetusproEQAudioProcessor&);
    ~CetusproEQAudioProcessorEditor() override;
    void paint(juce::Graphics&) override;
    void resized() override;
private:
    using SliderAttachment = juce::AudioProcessorValueTreeState::SliderAttachment;
    using ButtonAttachment = juce::AudioProcessorValueTreeState::ButtonAttachment;
    using ComboAttachment = juce::AudioProcessorValueTreeState::ComboBoxAttachment;
    struct Knob {
        juce::Slider slider;
        juce::Label label;
        std::unique_ptr<SliderAttachment> attachment;
    };
    CetusproEQAudioProcessor& processor;
    std::array<juce::TextButton,6> selectButtons;
    std::array<Knob,7> knobs;
    juce::ToggleButton bandOn {"Band enabled"}, dynamicOn {"Dynamic"}, bypass {"Bypass"};
    juce::ComboBox send, listen;
    juce::Slider out;
    juce::TextButton initFlat {"INIT FLAT"}, analyzerToggle {"ANALYZER ON"}, spectrumSelector {"POST"};
    bool analyzerEnabled = true, spectrumPost = true, spectrumHasData = false;
    juce::dsp::FFT fft {CetusproEQAudioProcessor::spectrumOrder};
    juce::dsp::WindowingFunction<float> fftWindow {CetusproEQAudioProcessor::spectrumSize, juce::dsp::WindowingFunction<float>::hann, false};
    std::array<float, CetusproEQAudioProcessor::spectrumSize*2> fftBuffer {};
    std::array<float, CetusproEQAudioProcessor::spectrumSize> timeBuffer {};
    std::array<float, CetusproEQAudioProcessor::spectrumSize/2+1> spectrum {};
    void updateFFT();
    juce::Label sendLabel, listenLabel, outLabel;
    std::unique_ptr<ButtonAttachment> onAttachment, dynamicAttachment, bypassAttachment;
    std::unique_ptr<ComboAttachment> sendAttachment, listenAttachment;
    std::unique_ptr<SliderAttachment> outAttachment;
    int selectedBand=0;
    void buttonClicked(juce::Button*) override;
    void comboBoxChanged(juce::ComboBox*) override {}
    void selectBand(int);
    void timerCallback() override;
    void drawGraph(juce::Graphics&,juce::Rectangle<int>);
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CetusproEQAudioProcessorEditor)
};
