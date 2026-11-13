#include "PluginEditor.h"
#include <cmath>

namespace {
const juce::Colour bg=juce::Colour::fromRGB(12,20,29);
const juce::Colour panel=juce::Colour::fromRGB(22,34,45);
const juce::Colour aqua=juce::Colour::fromRGB(47,226,221);
const juce::Colour muted=juce::Colour::fromRGB(143,168,180);

std::unique_ptr<juce::Drawable> historyIcon(bool redo) {
    // Vector silhouettes traced from the supplied 48x48 PNG icons.
    static const juce::Point<float> undo[] = {
        {1,4},{1,16},{2,17},{14,17},{12,14},{14,11},{19,9},{25,9},
        {30,11},{36,19},{36,28},{30,36},{22,38},{22,47},{30,46},
        {36,43},{41,38},{45,30},{46,22},{43,12},{36,4},{26,0},{17,0},{6,6}
    };
    static const juce::Point<float> redoPts[] = {
        {46,4},{41,6},{30,0},{20,0},{11,4},{4,12},{1,22},{2,30},
        {6,38},{11,43},{17,46},{25,47},{25,38},{19,37},{13,32},
        {11,28},{11,19},{17,11},{22,9},{28,9},{33,11},{35,13},
        {33,17},{45,17},{46,16}
    };
    juce::Path shape;
    const auto* pts = redo ? redoPts : undo;
    const int count = redo ? (int) std::size(redoPts) : (int) std::size(undo);
    shape.startNewSubPath(pts[0]);
    for (int i = 1; i < count; ++i) shape.lineTo(pts[i]);
    shape.closeSubPath();
    auto drawable = std::make_unique<juce::DrawablePath>();
    drawable->setPath(shape);
    drawable->setFill(juce::Colours::white);
    return drawable;
}
}
CetusproEQAudioProcessorEditor::CetusproEQAudioProcessorEditor(CetusproEQAudioProcessor& p)
: juce::AudioProcessorEditor(&p), processor(p) {
    setSize(1050,740);
    auto undoArt = historyIcon(false), redoArt = historyIcon(true);
    undoButton.setImages(undoArt.get());
    redoButton.setImages(redoArt.get());
    undoButton.setTooltip("Undo icon - history not connected");
    redoButton.setTooltip("Redo icon - history not connected");
    addAndMakeVisible(undoButton);
    addAndMakeVisible(redoButton);
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
}
void CetusproEQAudioProcessorEditor::resized() {
    undoButton.setBounds(getWidth()-115,22,33,33);
    redoButton.setBounds(getWidth()-72,22,33,33);
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
    // High-contrast header artwork only; DSP remains unchanged.
    g.setColour(juce::Colour::fromRGB(66,239,232));
    juce::Path ring;
    ring.addCentredArc(51.0f,41.0f,23.0f,23.0f,0.0f,0.40f,
                       juce::MathConstants<float>::twoPi-0.38f,true);
    g.strokePath(ring,juce::PathStrokeType(9.0f));
    g.setColour(juce::Colours::white);
    g.setFont(juce::FontOptions(34.0f,juce::Font::bold));
    g.drawText("cetuspro",91,14,192,43,juce::Justification::centredLeft);
    g.setColour(juce::Colour::fromRGB(74,244,235));
    g.drawText("EQ",274,14,64,43,juce::Justification::centredLeft);
    g.setFont(juce::FontOptions(13.0f));
    g.setColour(juce::Colour::fromRGB(213,232,239));
    g.drawText("Dynamic EQ",94,51,200,20,juce::Justification::centredLeft);
    g.setColour(juce::Colour::fromRGB(57,90,103));
    g.drawVerticalLine(getWidth()-135,17.0f,65.0f);
    drawGraph(g,{30,84,getWidth()-60,274});
    g.setColour(muted);g.setFont(juce::FontOptions(11.0f));
    g.drawText("Cross-instance sidechain: SEND Link 1 on the source track; LISTEN Link 1 on the destination track. One sender per link.",30,710,980,18,juce::Justification::centredLeft);
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
        g.setColour(b==selectedBand?aqua:muted);
        g.fillEllipse(x-8,y-8,16,16);
        g.setColour(bg);g.setFont(juce::FontOptions(11,juce::Font::bold));
        g.drawText(juce::String(b+1),juce::roundToInt(x)-8,juce::roundToInt(y)-8,16,16,juce::Justification::centred);
    }
}
