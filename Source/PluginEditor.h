#pragma once
#include "PluginProcessor.h"
#include <memory>
#include <array>

class CetusproEQAudioProcessorEditor final : public juce::AudioProcessorEditor,
    private juce::Button::Listener, private juce::Timer {
public:
    explicit CetusproEQAudioProcessorEditor(CetusproEQAudioProcessor&);
    ~CetusproEQAudioProcessorEditor() override;
    void paint(juce::Graphics&) override;
    void resized() override;
    void mouseDown(const juce::MouseEvent&) override;
    void mouseDrag(const juce::MouseEvent&) override;
    void mouseUp(const juce::MouseEvent&) override;
    void mouseDoubleClick(const juce::MouseEvent&) override;
    void mouseWheelMove(const juce::MouseEvent&,const juce::MouseWheelDetails&) override;

private:
    using SliderAttachment=juce::AudioProcessorValueTreeState::SliderAttachment;
    using ButtonAttachment=juce::AudioProcessorValueTreeState::ButtonAttachment;
    using ComboAttachment=juce::AudioProcessorValueTreeState::ComboBoxAttachment;
    struct Knob {
        juce::Slider slider;
        juce::Label label;
        std::unique_ptr<SliderAttachment> attachment;
    };
    CetusproEQAudioProcessor& processor;
    std::array<juce::TextButton, CetusproEQAudioProcessor::numBands> bandButtons;
    std::array<Knob,7> knobs;
    juce::ToggleButton enabled {"Band On"}, dynamic {"Dynamic"}, bypass {"Bypass"};
    juce::ComboBox send, listen, type;
    juce::Label sendLabel, listenLabel, outLabel;
    juce::Slider output;
    juce::TextButton reset {"INIT FLAT"}, analyzer {"Spectrum"}, togglePrePost {"POST"};
    std::unique_ptr<ButtonAttachment> enabledAttachment,dynamicAttachment,bypassAttachment;
    std::unique_ptr<SliderAttachment> outputAttachment;
    std::unique_ptr<ComboAttachment> sendAttachment,listenAttachment,typeAttachment;
    int selected=0;
    bool analyzerOn=true,postSpectrum=true,hasSpectrum=false,dragging=false;
    bool hudVisible=false;
    juce::Point<float> dragOrigin;
    juce::RangedAudioParameter* dragFreq=nullptr;
    juce::RangedAudioParameter* dragGain=nullptr;
    juce::dsp::FFT fft {CetusproEQAudioProcessor::spectrumOrder};
    juce::dsp::WindowingFunction<float> window {CetusproEQAudioProcessor::spectrumSize,
          juce::dsp::WindowingFunction<float>::hann,false};
    std::array<float,CetusproEQAudioProcessor::spectrumSize*2> fftData {};
    std::array<float,CetusproEQAudioProcessor::spectrumSize> fftTime {};
    std::array<float,CetusproEQAudioProcessor::spectrumSize/2+1> dbSpectrum {};
    float meterL=-90,meterR=-90;

    void buttonClicked(juce::Button*) override;
    void timerCallback() override;
    void selectBand(int);
    void updateSpectrum();
    void drawGraph(juce::Graphics&);
    void drawOutput(juce::Graphics&);
    void updateFloatingPanel();
    void setFromGraph(juce::RangedAudioParameter*,float);
    juce::Rectangle<int> graphBounds() const {return {24,84,getWidth()-152,345};}
    juce::Rectangle<int> graphPlot() const {return graphBounds().reduced(36,27).withTrimmedBottom(8);}
    juce::Rectangle<int> hudBounds() const;
    float freqX(float) const;
    float xFreq(float) const;
    float gainY(float) const;
    float yGain(float) const;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CetusproEQAudioProcessorEditor)
};