#include "PluginEditor.h"
#include <algorithm>
#include <cmath>

namespace {
const auto bg=juce::Colour::fromRGB(9,15,23);
const auto panel=juce::Colour::fromRGB(18,29,42);
const auto graph=juce::Colour::fromRGB(13,23,35);
const auto grid=juce::Colour::fromRGB(42,61,74);
const auto cyan=juce::Colour::fromRGB(47,226,220);
const auto ivory=juce::Colour::fromRGB(240,247,249);
const auto muted=juce::Colour::fromRGB(142,166,182);
const auto amber=juce::Colour::fromRGB(245,197,70);
const std::array<juce::Colour,CetusproEQAudioProcessor::numBands> colors {
    juce::Colour::fromRGB(192,145,232),juce::Colour::fromRGB(54,220,224),
    juce::Colour::fromRGB(86,168,245),juce::Colour::fromRGB(94,208,144),
    juce::Colour::fromRGB(245,213,92),juce::Colour::fromRGB(251,160,80),
    juce::Colour::fromRGB(238,100,108),juce::Colour::fromRGB(194,113,242)
};
}

CetusproEQAudioProcessorEditor::CetusproEQAudioProcessorEditor(CetusproEQAudioProcessor& p)
 : juce::AudioProcessorEditor(&p),processor(p) {
    setSize(1280,790);
    for(int i=0;i<CetusproEQAudioProcessor::numBands;++i) {
        auto& b=bandButtons[static_cast<size_t>(i)];
        b.setButtonText(juce::String(i+1));
        b.addListener(this);addAndMakeVisible(b);
    }
    const char* labels[]={"Frequency","Gain","Q","Threshold","Range","Attack","Release"};
    for(int k=0;k<7;++k){
        auto& c=knobs[static_cast<size_t>(k)];
        c.label.setText(labels[k],juce::dontSendNotification);
        c.label.setColour(juce::Label::textColourId,muted);
        c.label.setJustificationType(juce::Justification::centred);
        c.slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        c.slider.setTextBoxStyle(juce::Slider::TextBoxBelow,false,85,22);
        c.slider.setColour(juce::Slider::rotarySliderFillColourId,cyan);
        c.slider.setColour(juce::Slider::rotarySliderOutlineColourId,grid);
        c.slider.setColour(juce::Slider::textBoxTextColourId,ivory);
        c.slider.setColour(juce::Slider::textBoxBackgroundColourId,graph);
        addAndMakeVisible(c.label);addAndMakeVisible(c.slider);
    }
    for(auto* b : {&enabled,&dynamic,&bypass}){
        b->setColour(juce::ToggleButton::textColourId,ivory);
        b->setColour(juce::ToggleButton::tickColourId,cyan);
        addAndMakeVisible(*b);
    }
    for(auto* b : {&reset,&analyzer,&togglePrePost}){
        b->setColour(juce::TextButton::buttonColourId,panel);
        b->setColour(juce::TextButton::textColourOffId,ivory);
        b->addListener(this);addAndMakeVisible(*b);
    }
    send.addItem("Off",1);listen.addItem("Self",1);
    for(int i=1;i<=4;++i){send.addItem("Link "+juce::String(i),i+1);listen.addItem("Link "+juce::String(i),i+1);}
    listen.addItem("DAW Sidechain",6);
    for(int i=0;i<6;++i) {
        const char* kinds[]={"Bell","Low Shelf","High Shelf","High Pass","Low Pass","Notch"};
        type.addItem(kinds[i],i+1);
    }
    for(auto* c : {&send,&listen,&type}){
        c->setColour(juce::ComboBox::backgroundColourId,panel);
        c->setColour(juce::ComboBox::textColourId,ivory);
        c->setColour(juce::ComboBox::outlineColourId,grid);
        addAndMakeVisible(*c);
    }
    sendLabel.setText("CETUS LINK SEND",juce::dontSendNotification);
    listenLabel.setText("DETECTOR SOURCE",juce::dontSendNotification);
    outLabel.setText("OUTPUT",juce::dontSendNotification);
    for(auto* l : {&sendLabel,&listenLabel,&outLabel}){
        l->setColour(juce::Label::textColourId,muted);
        addAndMakeVisible(*l);
    }
    output.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
    output.setTextBoxStyle(juce::Slider::TextBoxBelow,false,74,22);
    output.setColour(juce::Slider::rotarySliderFillColourId,cyan);
    addAndMakeVisible(output);
    auto& params=processor.parameters;
    sendAttachment=std::make_unique<ComboAttachment>(params,"send",send);
    listenAttachment=std::make_unique<ComboAttachment>(params,"listen",listen);
    bypassAttachment=std::make_unique<ButtonAttachment>(params,"bypass",bypass);
    outputAttachment=std::make_unique<SliderAttachment>(params,"output",output);
    dbSpectrum.fill(-96.0f);
    selectBand(0);
    startTimerHz(24);
}
CetusproEQAudioProcessorEditor::~CetusproEQAudioProcessorEditor(){
    stopTimer();
    for(auto& b : bandButtons)b.removeListener(this);
    for(auto* b:{&reset,&analyzer,&togglePrePost})b->removeListener(this);
    for(auto& k:knobs) k.attachment.reset();
    enabledAttachment.reset();dynamicAttachment.reset();typeAttachment.reset();
    outputAttachment.reset();bypassAttachment.reset();sendAttachment.reset();listenAttachment.reset();
}
void CetusproEQAudioProcessorEditor::selectBand(int i){
    selected=juce::jlimit(0,CetusproEQAudioProcessor::numBands-1,i);
    constexpr const char* fields[]={"freq","gain","q","thr","range","atk","rel"};
    for(int j=0;j<7;++j){
        auto& k=knobs[static_cast<size_t>(j)];
        k.attachment.reset();
        k.attachment=std::make_unique<SliderAttachment>(processor.parameters,
            CetusproEQAudioProcessor::param(selected,fields[j]),k.slider);
    }
    enabledAttachment.reset();dynamicAttachment.reset();typeAttachment.reset();
    enabledAttachment=std::make_unique<ButtonAttachment>(processor.parameters,
      CetusproEQAudioProcessor::param(selected,"on"),enabled);
    dynamicAttachment=std::make_unique<ButtonAttachment>(processor.parameters,
      CetusproEQAudioProcessor::param(selected,"dyn"),dynamic);
    typeAttachment=std::make_unique<ComboAttachment>(processor.parameters,
      CetusproEQAudioProcessor::param(selected,"type"),type);
    dynamic.setEnabled(CetusEQ::canProcessDynamics(processor.getBandType(selected)));
    for(int b=0;b<CetusproEQAudioProcessor::numBands;++b){
        const bool sel=b==selected;
        bandButtons[static_cast<size_t>(b)].setColour(juce::TextButton::buttonColourId,sel?colors[static_cast<size_t>(b)]:panel);
        bandButtons[static_cast<size_t>(b)].setColour(juce::TextButton::textColourOffId,sel?bg:ivory);
    }
    updateFloatingPanel();repaint();
}
void CetusproEQAudioProcessorEditor::buttonClicked(juce::Button* sender) {
    for(int i=0;i<CetusproEQAudioProcessor::numBands;++i){
        if(sender==&bandButtons[static_cast<size_t>(i)]){selectBand(i);return;}
    }
    if(sender==&reset){processor.resetFlat();selectBand(0);}
    else if(sender==&analyzer){analyzerOn=!analyzerOn;analyzer.setButtonText(analyzerOn?"Spectrum":"Spectrum OFF");}
    else if(sender==&togglePrePost){postSpectrum=!postSpectrum;togglePrePost.setButtonText(postSpectrum?"POST":"PRE");dbSpectrum.fill(-96);hasSpectrum=false;}
    repaint();
}
void CetusproEQAudioProcessorEditor::resized(){
    reset.setBounds(getWidth()-334,28,104,31);
    analyzer.setBounds(getWidth()-223,28,128,31);
    togglePrePost.setBounds(getWidth()-87,28,58,31);
    const auto x0=35;
    for(int b=0;b<CetusproEQAudioProcessor::numBands;++b)
        bandButtons[static_cast<size_t>(b)].setBounds(x0+b*144,518,132,34);
    for(int i=0;i<7;++i){
        auto& k=knobs[static_cast<size_t>(i)];
        const int x=43+i*153;
        k.label.setBounds(x,572,137,21);
        k.slider.setBounds(x+15,595,108,96);
    }
    enabled.setBounds(36,711,116,27);
    dynamic.setBounds(164,711,116,27);
    bypass.setBounds(291,711,100,27);
    sendLabel.setBounds(430,700,160,18);send.setBounds(430,720,158,30);
    listenLabel.setBounds(610,700,182,18);listen.setBounds(610,720,186,30);
    outLabel.setBounds(1040,694,100,18);output.setBounds(1050,704,105,69);
    updateFloatingPanel();
}
juce::Rectangle<int> CetusproEQAudioProcessorEditor::hudBounds() const{
    const auto plot=graphPlot().toFloat();
    const int w=246,h=96;
    const float nx=freqX(processor.getBandFrequency(selected));
    const float ny=gainY(processor.getBandGain(selected)+processor.getBandDynGain(selected));
    const int x=juce::jlimit(juce::roundToInt(plot.getX()),juce::roundToInt(plot.getRight())-w,
         juce::roundToInt(nx-w*0.5f));
    const float desired=(ny>plot.getCentreY()?ny-h-20.0f:ny+23.0f);
    const int y=juce::jlimit(juce::roundToInt(plot.getY()),juce::roundToInt(plot.getBottom())-h,juce::roundToInt(desired));
    return {x,y,w,h};
}
void CetusproEQAudioProcessorEditor::updateFloatingPanel(){
    const auto r=hudBounds();
    type.setBounds(r.getX()+12,r.getY()+34,r.getWidth()-24,28);
}
void CetusproEQAudioProcessorEditor::updateSpectrum(){
    if(!analyzerOn||!processor.copySpectrum(fftTime,postSpectrum))return;
    hasSpectrum=true;
    std::fill(fftData.begin(),fftData.end(),0.0f);
    std::copy(fftTime.begin(),fftTime.end(),fftData.begin());
    window.multiplyWithWindowingTable(fftData.data(),CetusproEQAudioProcessor::spectrumSize);
    fft.performFrequencyOnlyForwardTransform(fftData.data(),true);
    for(size_t i=0;i<dbSpectrum.size();++i){
        const float magnitude=juce::jmax(1.0e-8f,fftData[i]*4.0f/CetusproEQAudioProcessor::spectrumSize);
        const float current=juce::Decibels::gainToDecibels(magnitude,-96.0f);
        dbSpectrum[i]=juce::jmax(current,dbSpectrum[i]-2.5f);
    }
}
void CetusproEQAudioProcessorEditor::timerCallback(){
    updateSpectrum();
    dynamic.setEnabled(CetusEQ::canProcessDynamics(processor.getBandType(selected)));
    const auto decay=[](float prev,float sample){return juce::jmax(sample,prev-2.5f);};
    meterL=decay(meterL,juce::Decibels::gainToDecibels(processor.getOutputPeak(0),-90.0f));
    meterR=decay(meterR,juce::Decibels::gainToDecibels(processor.getOutputPeak(1),-90.0f));
    updateFloatingPanel();repaint();
}
float CetusproEQAudioProcessorEditor::freqX(float f)const{
    const auto plot=graphPlot().toFloat();
    return plot.getX()+juce::jlimit(0.0f,1.0f,std::log(juce::jlimit(20.0f,20000.0f,f)/20.0f)/std::log(1000.0f))*plot.getWidth();
}
float CetusproEQAudioProcessorEditor::xFreq(float x)const{
    const auto plot=graphPlot().toFloat();
    return 20.0f*std::pow(1000.0f,juce::jlimit(0.0f,1.0f,(x-plot.getX())/plot.getWidth()));
}
float CetusproEQAudioProcessorEditor::gainY(float db)const{
    const auto plot=graphPlot().toFloat();
    return plot.getCentreY()-juce::jlimit(-18.0f,18.0f,db)*plot.getHeight()/36.0f;
}
float CetusproEQAudioProcessorEditor::yGain(float y)const{
    const auto plot=graphPlot().toFloat();
    return juce::jlimit(-18.0f,18.0f,(plot.getCentreY()-y)*36.0f/plot.getHeight());
}
void CetusproEQAudioProcessorEditor::setFromGraph(juce::RangedAudioParameter* p,float val){
    if(p)p->setValueNotifyingHost(p->convertTo0to1(val));
}
void CetusproEQAudioProcessorEditor::mouseDown(const juce::MouseEvent& e){
    if(!graphPlot().contains(e.getPosition()))return;
    int pick=-1;float best=28*28;
    for(int b=0;b<CetusproEQAudioProcessor::numBands;++b){
        if(!processor.isBandEnabled(b))continue;
        const float dx=e.position.x-freqX(processor.getBandFrequency(b));
        const float dy=e.position.y-gainY(processor.getBandGain(b)+processor.getBandDynGain(b));
        const float dist=dx*dx+dy*dy;
        if(dist<best){pick=b;best=dist;}
    }
    if(pick<0)return;
    selectBand(pick);dragging=true;
    dragFreq=processor.parameters.getParameter(CetusproEQAudioProcessor::param(pick,"freq"));
    dragGain=processor.parameters.getParameter(CetusproEQAudioProcessor::param(pick,"gain"));
    if(dragFreq)dragFreq->beginChangeGesture();
    if(dragGain)dragGain->beginChangeGesture();
    mouseDrag(e);
}
void CetusproEQAudioProcessorEditor::mouseDrag(const juce::MouseEvent& e){
    if(!dragging)return;
    setFromGraph(dragFreq,xFreq(e.position.x));
    setFromGraph(dragGain,yGain(e.position.y)-processor.getBandDynGain(selected));
    updateFloatingPanel();
}
void CetusproEQAudioProcessorEditor::mouseUp(const juce::MouseEvent&){
    if(dragging){
        if(dragFreq)dragFreq->endChangeGesture();
        if(dragGain)dragGain->endChangeGesture();
    }
    dragging=false;dragFreq=nullptr;dragGain=nullptr;
}
void CetusproEQAudioProcessorEditor::mouseDoubleClick(const juce::MouseEvent& e){
    if(!graphPlot().contains(e.getPosition()))return;
    int target=-1;
    for(int b=0;b<CetusproEQAudioProcessor::numBands;++b)
        if(!processor.isBandEnabled(b)){target=b;break;}
    if(target<0)target=selected;
    auto set=[this,target](const char* field,float value) {
        if(auto* p=processor.parameters.getParameter(CetusproEQAudioProcessor::param(target,field))){
            p->beginChangeGesture();p->setValueNotifyingHost(p->convertTo0to1(value));p->endChangeGesture();
        }
    };
    set("on",1.0f);set("freq",xFreq(e.position.x));set("gain",yGain(e.position.y));
    selectBand(target);
}
void CetusproEQAudioProcessorEditor::mouseWheelMove(const juce::MouseEvent& e,const juce::MouseWheelDetails& wheel){
    if(!graphPlot().contains(e.getPosition()))return juce::AudioProcessorEditor::mouseWheelMove(e,wheel);
    if(auto* p=processor.parameters.getParameter(CetusproEQAudioProcessor::param(selected,"q"))){
        const float q=juce::jlimit(0.2f,12.0f,processor.getBandQ(selected)*std::pow(1.16f,wheel.deltaY*5.0f));
        p->beginChangeGesture();p->setValueNotifyingHost(p->convertTo0to1(q));p->endChangeGesture();
    }
}
void CetusproEQAudioProcessorEditor::paint(juce::Graphics& g){
    g.fillAll(bg);
    g.setColour(panel);g.fillRoundedRectangle(16.0f,16.0f,1248.0f,58.0f,11.0f);
    g.fillRoundedRectangle(24.0f,500.0f,1232.0f,264.0f,11.0f);
    g.setColour(cyan);g.fillEllipse(28.0f,31.0f,30.0f,30.0f);
    g.setColour(bg);g.fillEllipse(36.0f,25.0f,30.0f,30.0f);
    g.setColour(ivory);g.setFont(juce::FontOptions(13.0f,juce::Font::bold));
    g.drawText("CETUS PRODUCTION",70,28,180,20,juce::Justification::centredLeft);
    g.setFont(juce::FontOptions(25.0f,juce::Font::bold));
    g.drawText("cetuspro",254,23,170,34,juce::Justification::centredLeft);
    g.setColour(cyan);g.drawText("EQ",418,23,45,34,juce::Justification::centredLeft);
    g.setColour(muted);g.setFont(juce::FontOptions(11.0f));
    g.drawText("8 BAND   /   DYNAMIC EQUALIZER   v0.4",478,33,302,23,juce::Justification::centredLeft);
    drawGraph(g);drawOutput(g);
    g.setColour(ivory);g.setFont(juce::FontOptions(12.0f));
    g.drawText("8 BAND FILTERS    •    DRAG NODE TO EDIT     •    MOUSE WHEEL = Q",32,486,845,16,juce::Justification::centredLeft);
    g.setColour(muted);
    g.drawText("CETUS LINK SIDECHAIN: SEND on source track, LISTEN on destination",33,755,735,18,juce::Justification::centredLeft);
    g.setColour(cyan);
    g.drawText("CETUS PRODUCTION  /  v0.4",994,755,247,18,juce::Justification::centredRight);
}
void CetusproEQAudioProcessorEditor::drawGraph(juce::Graphics& g){
    const auto region=graphBounds();const auto plot=graphPlot().toFloat();
    g.setColour(graph);g.fillRoundedRectangle(region.toFloat(),10.0f);
    g.saveState();g.reduceClipRegion(plot.toNearestInt());
    const double rate=processor.spectrumSampleRate();
    using Ptr=juce::dsp::IIR::Coefficients<float>::Ptr;
    std::array<Ptr,CetusproEQAudioProcessor::numBands> staticCoeffs{},dynamicCoeffs{};
    for(int b=0;b<CetusproEQAudioProcessor::numBands;++b){
        if(!processor.isBandEnabled(b))continue;
        const float freq=processor.getBandFrequency(b),q=processor.getBandQ(b);
        const float gain=processor.getBandGain(b);
        const int typeId=processor.getBandType(b);
        staticCoeffs[static_cast<size_t>(b)]=CetusEQ::makeCoefficients(rate,freq,q,gain,typeId);
        dynamicCoeffs[static_cast<size_t>(b)]=CetusEQ::makeCoefficients(rate,freq,q,gain+processor.getBandDynGain(b),typeId);
    }
    const auto response=[rate](const Ptr& coeff,double freq){
        return coeff==nullptr?0.0f:(float)juce::Decibels::gainToDecibels(
             juce::jmax(1.0e-9,coeff->getMagnitudeForFrequency(juce::jlimit(1.0,rate*0.49,freq),rate)),-160.0);
    };
    for(float f:{20.f,50.f,100.f,200.f,500.f,1000.f,2000.f,5000.f,10000.f,20000.f}){
        g.setColour(grid.withAlpha(0.48f));g.drawVerticalLine(juce::roundToInt(freqX(f)),plot.getY(),plot.getBottom());
    }
    for(float d=-18;d<=18;d+=3){
        g.setColour(grid.withAlpha(std::fmod(std::abs(d),6.0f)<.1f?.57f:.26f));
        g.drawHorizontalLine(juce::roundToInt(gainY(d)),plot.getX(),plot.getRight());
    }
    if(analyzerOn&&hasSpectrum){
        juce::Path spectrum;
        for(int i=0;i<=640;++i){
            const float x=plot.getX()+i/640.0f*plot.getWidth();
            const float hz=xFreq(x);
            const int bin=juce::jlimit(1,CetusproEQAudioProcessor::spectrumSize/2,
                juce::roundToInt(hz*CetusproEQAudioProcessor::spectrumSize/rate));
            const float db=juce::jlimit(-96.0f,-6.0f,dbSpectrum[static_cast<size_t>(bin)]);
            const float y=plot.getBottom()-(db+96.0f)/90.0f*plot.getHeight();
            if(i==0)spectrum.startNewSubPath(x,y);else spectrum.lineTo(x,y);
        }
        juce::Path fill=spectrum;fill.lineTo(plot.getRight(),plot.getBottom());fill.lineTo(plot.getX(),plot.getBottom());fill.closeSubPath();
        g.setColour(ivory.withAlpha(0.11f));g.fillPath(fill);
        g.setColour(muted.withAlpha(0.48f));g.strokePath(spectrum,juce::PathStrokeType(1.2f));
    }
    for(int b=0;b<CetusproEQAudioProcessor::numBands;++b){
        if(!processor.isBandEnabled(b)||!processor.isBandDynamic(b)||std::abs(processor.getBandDynGain(b))<.02f)continue;
        juce::Path fill;
        for(int i=0;i<=220;++i){
            const float x=plot.getX()+i/220.0f*plot.getWidth();
            const float y=gainY(response(staticCoeffs[static_cast<size_t>(b)],xFreq(x)));
            if(i==0)fill.startNewSubPath(x,y);else fill.lineTo(x,y);
        }
        for(int i=220;i>=0;--i){
            const float x=plot.getX()+i/220.0f*plot.getWidth();
            fill.lineTo(x,gainY(response(dynamicCoeffs[static_cast<size_t>(b)],xFreq(x))));
        }
        fill.closeSubPath();g.setColour(colors[static_cast<size_t>(b)].withAlpha(b==selected?.34f:.17f));g.fillPath(fill);
    }
    juce::Path flat,live;
    for(int i=0;i<=640;++i){
        const float x=plot.getX()+i/640.0f*plot.getWidth();const float hz=xFreq(x);
        float base=0,now=0;
        for(int b=0;b<CetusproEQAudioProcessor::numBands;++b){
            base+=response(staticCoeffs[static_cast<size_t>(b)],hz);
            now+=response(dynamicCoeffs[static_cast<size_t>(b)],hz);
        }
        if(i==0){flat.startNewSubPath(x,gainY(base));live.startNewSubPath(x,gainY(now));}
        else {flat.lineTo(x,gainY(base));live.lineTo(x,gainY(now));}
    }
    g.setColour(amber.withAlpha(.79f));g.strokePath(flat,juce::PathStrokeType(1.6f));
    g.setColour(cyan);g.strokePath(live,juce::PathStrokeType(2.4f));
    g.restoreState();
    for(int b=0;b<CetusproEQAudioProcessor::numBands;++b){
        if(!processor.isBandEnabled(b))continue;
        const float x=freqX(processor.getBandFrequency(b));
        const float y=gainY(processor.getBandGain(b)+processor.getBandDynGain(b));
        const auto color=colors[static_cast<size_t>(b)];
        if(b==selected){g.setColour(color.withAlpha(.19f));g.fillEllipse(x-17,y-17,34,34);}
        g.setColour(color);g.fillEllipse(x-9,y-9,18,18);
        g.setColour(bg);g.setFont(juce::FontOptions(11.0f,juce::Font::bold));
        g.drawText(juce::String(b+1),juce::roundToInt(x)-9,juce::roundToInt(y)-9,18,18,juce::Justification::centred);
    }
    g.setColour(muted);g.setFont(juce::FontOptions(10.0f));
    for(float f:{20.f,50.f,100.f,200.f,500.f,1000.f,2000.f,5000.f,10000.f,20000.f}){
        const auto str=f>=1000?juce::String(f/1000.0f,0)+"k":juce::String(f,0);
        g.drawText(str,juce::roundToInt(freqX(f))-18,region.getBottom()-22,36,16,juce::Justification::centred);
    }
    for(float d:{18.f,12.f,6.f,0.f,-6.f,-12.f,-18.f})
        g.drawText((d>0?"+":"")+juce::String(d,0),region.getX()+2,juce::roundToInt(gainY(d))-8,30,17,juce::Justification::centred);
    const auto hud=hudBounds();
    g.setColour(bg.withAlpha(.85f));g.fillRoundedRectangle(hud.translated(0,4).toFloat(),10.0f);
    g.setColour(juce::Colour::fromRGB(34,48,62));g.fillRoundedRectangle(hud.toFloat(),10.0f);
    g.setColour(colors[static_cast<size_t>(selected)]);g.drawRoundedRectangle(hud.toFloat(),10.0f,1.0f);
    g.setColour(ivory);g.setFont(juce::FontOptions(12.0f,juce::Font::bold));
    g.drawText("BAND "+juce::String(selected+1)+"   /  "+juce::String(processor.getBandFrequency(selected),0)+" Hz",
         hud.getX()+12,hud.getY()+6,hud.getWidth()-22,20,juce::Justification::centredLeft);
    g.setColour(muted);g.setFont(juce::FontOptions(10.5f));
    g.drawText("DYNAMIC "+juce::String(processor.getBandDynGain(selected),1)+" dB",
         hud.getX()+12,hud.getBottom()-23,hud.getWidth()-22,18,juce::Justification::centredLeft);
    g.drawText("STATIC",region.getX()+15,region.getY()+7,62,14,juce::Justification::centredLeft);
    g.setColour(amber);g.fillRect(region.getX()+72,region.getY()+12,32,2);
    g.setColour(cyan);g.fillRect(region.getX()+109,region.getY()+12,32,2);
}
void CetusproEQAudioProcessorEditor::drawOutput(juce::Graphics& g){
    const int left=getWidth()-112,top=graphBounds().getY(),height=graphBounds().getHeight();
    g.setColour(panel);g.fillRoundedRectangle((float)left,(float)top,88.0f,(float)height,10.0f);
    g.setColour(ivory);g.setFont(juce::FontOptions(13.0f,juce::Font::bold));
    g.drawText("OUT",left+10,top+12,68,18,juce::Justification::centred);
    for(int c=0;c<2;++c){
        const int x=left+23+c*27;
        g.setColour(graph);g.fillRoundedRectangle((float)x,(float)top+46,15.0f,(float)height-104,3.0f);
        const float db=c==0?meterL:meterR;
        const float portion=juce::jlimit(0.0f,1.0f,(db+60.0f)/60.0f);
        const float barH=portion*(height-104);
        g.setColour(cyan);g.fillRoundedRectangle((float)x,(float)(top+height-58)-barH,15.0f,barH,2.0f);
        g.setColour(muted);g.drawText(c==0?"L":"R",x-3,top+height-39,21,15,juce::Justification::centred);
    }
}