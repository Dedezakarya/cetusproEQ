#pragma once
#include "PluginProcessor.h"
#include <memory>
#include <vector>

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
    juce::DrawableButton undoButton {"Undo", juce::DrawableButton::ImageFitted};
    juce::DrawableButton redoButton {"Redo", juce::DrawableButton::ImageFitted};
    juce::Label sendLabel, listenLabel, outLabel;
    std::unique_ptr<ButtonAttachment> onAttachment, dynamicAttachment, bypassAttachment;
    std::unique_ptr<ComboAttachment> sendAttachment, listenAttachment;
    std::unique_ptr<SliderAttachment> outAttachment;
    int selectedBand=0;
    void buttonClicked(juce::Button*) override;
    void comboBoxChanged(juce::ComboBox*) override {}
    void selectBand(int);
    void timerCallback() override { repaint(30,82,getWidth()-60,280); }
    void drawGraph(juce::Graphics&,juce::Rectangle<int>);
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CetusproEQAudioProcessorEditor)
};
