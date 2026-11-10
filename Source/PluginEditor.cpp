#include "PluginEditor.h"
#include <cmath>

namespace {
const juce::Colour bg=juce::Colour::fromRGB(12,20,29);
const juce::Colour panel=juce::Colour::fromRGB(22,34,45);
const juce::Colour aqua=juce::Colour::fromRGB(47,226,221);
const juce::Colour muted=juce::Colour::fromRGB(143,168,180);
const std::array<juce::Colour,6> bandColors {juce::Colour::fromRGB(188,147,231),juce::Colour::fromRGB(51,225,220),juce::Colour::fromRGB(245,206,76),juce::Colour::fromRGB(63,172,242),juce::Colour::fromRGB(241,139,99),juce::Colour::fromRGB(240,93,107)};
}
CetusproEQAudioProcessorEditor::CetusproEQAudioProcessorEditor(CetusproEQAudioProcessor& p)
: juce::AudioProcessorEditor(&p), processor(p) {
    setSize(1050,740);
    for(int i=0;i<6;++i) {
        selectButtons[static_cast<size_t>(i)].setButtonText("BAND " + juce::String(i+1));
        selectButtons[static_cast<size_t>(i)].addListener(this);
        addAndMakeVisible(selectButtons[static_cast<size_t>(i)]);
    }
    const char* labels[]={"Frequency (Hz)","Gain (dB)","Q","Threshold (dB)","Range (dB)","Attack (ms)","Release (ms)"};
    for(int i=0;i<7;++i) {
        auto& k=knobs[static_cast<size_t>(i)];
        k.slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        k.slider.setTextBoxStyle(juce::Slider::TextBoxBelow,false,110,22);
        k.slider.setColour(juce::Slider::rotarySliderFillColourId,aqua);
        k.slider.setColour(juce::Slider::rotarySliderOutlineColourId,muted.darker(.7f));
        k.slider.setColour(juce::Slider::textBoxTextColourId,juce::Colours::white);
        k.label.setText(labels[i],juce::dontSendNotification);
        k.label.setJustificationType(juce::Justification::centred);
        k.label.setColour(juce::Label::textColourId,muted);
        addAndMakeVisible(k.slider);
        addAndMakeVisible(k.label);
    }
    for(auto* btn : {&bandOn,&dynamicOn,&bypass}) {
        btn->setColour(juce::ToggleButton::textColourId,juce::Colours::white);
        btn->setColour(juce::ToggleButton::tickColourId,aqua);
        addAndMakeVisible(*btn);
    }
    send.addItem("Off",1); listen.addItem("Self",1);
    for(int i=1;i<=4;++i) {send.addItem("Link " + juce::String(i),i+1);listen.addItem("Link " + juce::String(i),i+1);}
    listen.addItem("DAW sidechain",6);
    for(auto* c : {&send,&listen}) {c->addListener(this);addAndMakeVisible(*c);}
    sendLabel.setText("CETUS LINK  SEND",juce::dontSendNotification);
    listenLabel.setText("DETECTOR SOURCE",juce::dontSendNotification);
    outLabel.setText("OUTPUT",juce::dontSendNotification);
    for(auto* l : {&sendLabel,&listenLabel,&outLabel}) {l->setColour(juce::Label::textColourId,muted);addAndMakeVisible(*l);}
    for (auto* button : {&initFlat,&analyzerToggle,&spectrumSelector}) {
        button->setColour(juce::TextButton::buttonColourId,panel);
        button->setColour(juce::TextButton::textColourOffId,juce::Colours::white);
        button->addListener(this);
        addAndMakeVisible(*button);
    }
    spectrum.fill(-96.0f);
    out.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
    out.setTextBoxStyle(juce::Slider::TextBoxBelow,false,80,20);
    out.setColour(juce::Slider::rotarySliderFillColourId,aqua);
    addAndMakeVisible(out);
    auto& a=processor.parameters;
    sendAttachment=std::make_unique<ComboAttachment>(a,"send",send);
    listenAttachment=std::make_unique<ComboAttachment>(a,"listen",listen);
    bypassAttachment=std::make_unique<ButtonAttachment>(a,"bypass",bypass);
    outAttachment=std::make_unique<SliderAttachment>(a,"output",out);
    selectBand(0);
    startTimerHz(15);
}
CetusproEQAudioProcessorEditor::~CetusproEQAudioProcessorEditor() {
    stopTimer();
    for(auto& button:selectButtons) button.removeListener(this);
    send.removeListener(this);listen.removeListener(this);
    for (auto* button : {&initFlat,&analyzerToggle,&spectrumSelector}) button->removeListener(this);
}
void CetusproEQAudioProcessorEditor::selectBand(int index) {
    selectedBand=juce::jlimit(0,5,index);
    const char* fields[]={"freq","gain","q","thr","range","atk","rel"};
    for(int i=0;i<7;++i) {
        auto& k=knobs[static_cast<size_t>(i)];
        k.attachment.reset();
        k.attachment=std::make_unique<SliderAttachment>(processor.parameters,CetusproEQAudioProcessor::param(selectedBand,fields[i]),k.slider);
    }
    onAttachment.reset();dynamicAttachment.reset();
    onAttachment=std::make_unique<ButtonAttachment>(processor.parameters,CetusproEQAudioProcessor::param(selectedBand,"on"),bandOn);
    dynamicAttachment=std::make_unique<ButtonAttachment>(processor.parameters,CetusproEQAudioProcessor::param(selectedBand,"dyn"),dynamicOn);
    for(int i=0;i<6;++i) selectButtons[static_cast<size_t>(i)].setColour(juce::TextButton::buttonColourId,i==selectedBand?aqua:panel);
    for(int i=0;i<6;++i) selectButtons[static_cast<size_t>(i)].setColour(juce::TextButton::textColourOffId,i==selectedBand?bg:juce::Colours::white);
    repaint();
}
void CetusproEQAudioProcessorEditor::buttonClicked(juce::Button* b) {
    for(int i=0;i<6;++i) if(b==&selectButtons[static_cast<size_t>(i)]) {selectBand(i);return;}
    if (b == &initFlat) { processor.resetFlat(); selectBand(0); }
    if (b == &analyzerToggle) { analyzerEnabled = !analyzerEnabled; analyzerToggle.setButtonText(analyzerEnabled ? "ANALYZER ON" : "ANALYZER OFF"); }
    if (b == &spectrumSelector) { spectrumPost = !spectrumPost; spectrumSelector.setButtonText(spectrumPost ? "POST" : "PRE"); }
    repaint();
}
void CetusproEQAudioProcessorEditor::resized() {
    initFlat.setBounds(getWidth()-338,25,115,35);
    analyzerToggle.setBounds(getWidth()-215,25,129,35);
    spectrumSelector.setBounds(getWidth()-80,25,55,35);
    auto bounds=getLocalBounds().reduced(25);
    bounds.removeFromTop(72);
    bounds.removeFromTop(296);
    auto buttons=bounds.removeFromTop(44);
    for(auto& button:selectButtons) button.setBounds(buttons.removeFromLeft(145).reduced(5));
    bounds.removeFromTop(10);
    auto knobRow=bounds.removeFromTop(132);
    int w=knobRow.getWidth()/7;
    for(auto& k:knobs) {
        auto cell=knobRow.removeFromLeft(w);
        k.label.setBounds(cell.removeFromTop(22));
        k.slider.setBounds(cell);
    }
    auto last=bounds.removeFromTop(73);
    bandOn.setBounds(last.removeFromLeft(135).reduced(4));
    dynamicOn.setBounds(last.removeFromLeft(125).reduced(4));
    bypass.setBounds(last.removeFromLeft(105).reduced(4));
    auto sendCell=last.removeFromLeft(173);
    sendLabel.setBounds(sendCell.removeFromTop(24));send.setBounds(sendCell.removeFromTop(30));
    auto listenCell=last.removeFromLeft(190);
    listenLabel.setBounds(listenCell.removeFromTop(24));listen.setBounds(listenCell.removeFromTop(30));
    auto outCell=last.removeFromLeft(110);
    outLabel.setBounds(outCell.removeFromTop(18));out.setBounds(outCell);
}
void CetusproEQAudioProcessorEditor::paint(juce::Graphics& g) {
    g.fillAll(bg);
    g.setColour(juce::Colours::white);
    g.setFont(juce::FontOptions(35.0f,juce::Font::bold));
    g.drawText("cetuspro",25,18,230,47,juce::Justification::centredLeft);
    g.setColour(aqua);g.drawText("EQ",244,18,70,47,juce::Justification::centredLeft);
    g.setFont(juce::FontOptions(13.0f));g.setColour(muted);
    g.drawText("CETUS PRODUCTION   /   DYNAMIC EQUALIZER  v0.2",330,22,480,35,juce::Justification::centredLeft);
    drawGraph(g,{30,84,getWidth()-60,274});
    g.setColour(muted);g.setFont(juce::FontOptions(11.0f));
    g.drawText("Cross-instance sidechain: SEND Link 1 on the source track; LISTEN Link 1 on the destination track. One sender per link.",30,710,980,18,juce::Justification::centredLeft);
}
void CetusproEQAudioProcessorEditor::updateFFT() {
    if (!analyzerEnabled || !processor.copySpectrum(timeBuffer, spectrumPost)) return;
    spectrumHasData = true;
    std::fill(fftBuffer.begin(),fftBuffer.end(),0.0f);
    std::copy(timeBuffer.begin(),timeBuffer.end(),fftBuffer.begin());
    fftWindow.multiplyWithWindowingTable(fftBuffer.data(),CetusproEQAudioProcessor::spectrumSize);
    fft.performFrequencyOnlyForwardTransform(fftBuffer.data(),true);
    const float scale = 4.0f/CetusproEQAudioProcessor::spectrumSize;
    for (size_t i=0; i<spectrum.size(); ++i) {
        const float db = juce::Decibels::gainToDecibels(juce::jmax(1.0e-8f,fftBuffer[i]*scale),-96.0f);
        spectrum[i] = juce::jmax(db,spectrum[i]-2.5f);
    }
}
void CetusproEQAudioProcessorEditor::timerCallback() {
    updateFFT();
    repaint(30,82,getWidth()-60,280);
}
void CetusproEQAudioProcessorEditor::drawGraph(juce::Graphics& g,juce::Rectangle<int> rect) {
    g.setColour(panel);g.fillRoundedRectangle(rect.toFloat(),8);
    const auto left=static_cast<float>(rect.getX()+33), right=static_cast<float>(rect.getRight()-20);
    const auto top=static_cast<float>(rect.getY()+16), bottom=static_cast<float>(rect.getBottom()-26);
    auto xPos=[&](float f) {return left+(std::log(f/20.0f)/std::log(1000.0f))*(right-left);};
    auto yPos=[&](float dB) {return (top+bottom)*.5f - dB*(bottom-top)/36.0f;};
    g.setColour(juce::Colour::fromRGB(46,63,76));
    for(float f : {20.f,50.f,100.f,200.f,500.f,1000.f,2000.f,5000.f,10000.f,20000.f}) {
        float x=xPos(f);g.drawVerticalLine(juce::roundToInt(x),top,bottom);
        g.setFont(juce::FontOptions(10));
        g.drawText(f>=1000?juce::String(f/1000.f,0)+"k":juce::String(f,0),juce::roundToInt(x)-18,juce::roundToInt(bottom)+4,36,14,juce::Justification::centred);
    }
    for(float d=-18;d<=18;d+=6) {float y=yPos(d);g.drawHorizontalLine(juce::roundToInt(y),left,right);}
    // Actual FFT magnitude analysis, computed on the GUI timer (never on the audio thread).
    if (analyzerEnabled && spectrumHasData) {
        const double rate = processor.spectrumSampleRate();
        juce::Path spectralPath;
        for (int i=0; i<=600; ++i) {
            const float frequency = 20.0f * std::pow(1000.0f, static_cast<float>(i)/600.0f);
            const auto bin = juce::jlimit(1, CetusproEQAudioProcessor::spectrumSize/2,
                juce::roundToInt(frequency * CetusproEQAudioProcessor::spectrumSize / rate));
            const float level = juce::jlimit(-96.0f, -6.0f, spectrum[static_cast<size_t>(bin)]);
            const float y = bottom - (level + 96.0f)/90.0f * (bottom-top);
            const float x = xPos(frequency);
            if (i == 0) spectralPath.startNewSubPath(x,y); else spectralPath.lineTo(x,y);
        }
        juce::Path shape = spectralPath;
        shape.lineTo(right,bottom);
        shape.lineTo(left,bottom);
        shape.closeSubPath();
        g.setColour(aqua.withAlpha(0.13f));g.fillPath(shape);
        g.setColour(aqua.withAlpha(0.50f));g.strokePath(spectralPath,juce::PathStrokeType(1.3f));
    }
    g.setColour(juce::Colours::white.withAlpha(.4f));g.drawHorizontalLine(juce::roundToInt(yPos(0)),left,right);
    juce::Path path;
    for(int xi=0;xi<=800;++xi) {
        float f=20.0f*std::pow(1000.0f,xi/800.0f);
        float value=0;
        for(int b=0;b<6;++b) {
            float centre=processor.getBandFrequency(b);
            float octaves=std::log2(f/centre);
            float width=juce::jmax(.07f,1.1f/processor.getBandQ(b));
            value += processor.getBandGain(b)*std::exp(-.5f*(octaves/width)*(octaves/width));
        }
        float x=xPos(f),y=yPos(juce::jlimit(-18.f,18.f,value));
        if(xi==0)path.startNewSubPath(x,y);else path.lineTo(x,y);
    }
    g.setColour(aqua);g.strokePath(path,juce::PathStrokeType(2.6f));
    for(int b=0;b<6;++b) {
        float x=xPos(processor.getBandFrequency(b)),y=yPos(processor.getBandGain(b));
        g.setColour(bandColors[static_cast<size_t>(b)]);
        g.fillEllipse(x-8,y-8,16,16);
        g.setColour(bg);g.setFont(juce::FontOptions(11,juce::Font::bold));
        g.drawText(juce::String(b+1),juce::roundToInt(x)-8,juce::roundToInt(y)-8,16,16,juce::Justification::centred);
    }
}
