from pathlib import Path
import shutil
dst=Path('.')
h=dst/'Source/PluginEditor.h'
c=dst/'Source/PluginEditor.cpp'
hs=h.read_text(encoding='utf-8')
cs=c.read_text(encoding='utf-8')
def repl(s, a,b):
 if a not in s: raise RuntimeError('NOT FOUND '+a[:120])
 return s.replace(a,b,1)
hs=repl(hs, 'void drawButtonBackground(juce::Graphics&, juce::Button&, const juce::Colour&, bool, bool) override;', 'void drawButtonBackground(juce::Graphics&, juce::Button&, const juce::Colour&, bool, bool) override;\n        void drawButtonText(juce::Graphics&, juce::TextButton&, bool, bool) override;')
hs=repl(hs, 'juce::Rectangle<int> headerRect() const { return {14, 12, getWidth()-28, 62}; }', 'juce::Rectangle<int> headerRect() const { return {12, 10, getWidth()-24, 52}; }')
hs=repl(hs, 'juce::Rectangle<int> graphRect() const { return {17, 84, getWidth()-102, 327}; }', 'juce::Rectangle<int> graphRect() const { return {14, 74, getWidth()-123, 286}; }')
hs=repl(hs, 'juce::Rectangle<int> meterRect() const { return {getWidth()-79, 84, 62, 327}; }', 'juce::Rectangle<int> meterRect() const { return {getWidth()-101, 74, 86, 286}; }')
hs=repl(hs, 'juce::Rectangle<int> bottomRect() const { return {17, 423, getWidth()-34, 184}; }', 'juce::Rectangle<int> bottomRect() const { return {14, 373, getWidth()-28, 193}; }')
cs=repl(cs,'setSize(1180, 642);','setSize(1080, 594);')
# Make header icon buttons: retain functional actions through click handlers.
cs=repl(cs, '''    hudCloseButton.setVisible(false);''', '''    // Icons are drawn by the custom LookAndFeel; commands keep their existing handlers.
    for (auto* btn : { &savePresetButton, &openPresetButton, &undoButton, &redoButton }) {
        btn->setComponentID(btn == &savePresetButton ? "cetus-save" :
                            btn == &openPresetButton ? "cetus-open" :
                            btn == &undoButton ? "cetus-undo" : "cetus-redo");
        btn->setButtonText(juce::String());
    }
    savePresetButton.setTooltip("Save user preset");
    openPresetButton.setTooltip("Open user preset");
    undoButton.setTooltip("Undo last parameter edit");
    redoButton.setTooltip("Redo parameter edit");
    hudCloseButton.setVisible(false);''')
# Replace appearance methods block
start=cs.index('void CetusproEQAudioProcessorEditor::CetusLookAndFeel::drawButtonBackground(')
end=cs.index('\nCetusproEQAudioProcessorEditor::CetusproEQAudioProcessorEditor(',start)
look=r'''void CetusproEQAudioProcessorEditor::CetusLookAndFeel::drawButtonBackground(
    juce::Graphics& g, juce::Button& button, const juce::Colour&, bool over, bool down) {
    const auto r = button.getLocalBounds().toFloat().reduced(0.6f);
    const bool selected = button.getToggleState();
    const auto face = selected ? cyan : panel2;
    g.setColour(bg.withAlpha(.65f));
    g.fillRoundedRectangle(r.translated(0.0f,1.5f),6.0f);
    juce::ColourGradient grad(face.brighter(over ? .25f : .11f),r.getCentreX(),r.getY(),
                              face.darker(down ? .38f : .24f),r.getCentreX(),r.getBottom(),false);
    g.setGradientFill(grad);g.fillRoundedRectangle(r,6.0f);
    g.setColour(selected ? cyan.brighter(.55f) : juce::Colour::fromRGB(75,96,113));
    g.drawRoundedRectangle(r,6.0f,0.9f);
    g.setColour(white.withAlpha(down ? .15f : .35f));
    g.drawHorizontalLine(juce::roundToInt(r.getY()+1.3f),r.getX()+5.0f,r.getRight()-5.0f);
}
void CetusproEQAudioProcessorEditor::CetusLookAndFeel::drawButtonText(
    juce::Graphics& g, juce::TextButton& button, bool over, bool down) {
    const juce::String id=button.getComponentID();
    if(id.isEmpty() || !id.startsWith("cetus-")) {
        juce::LookAndFeel_V4::drawButtonText(g,button,over,down);return;
    }
    const float cx=button.getWidth()*.5f,cy=button.getHeight()*.5f;
    g.setColour(over ? cyan : white.withAlpha(.88f));
    if(id=="cetus-save") {
        const auto r=juce::Rectangle<float>(cx-8.0f,cy-8.0f,16.0f,16.0f);
        g.drawRoundedRectangle(r,2.0f,1.7f);
        g.drawRect(cx-4.0f,cy-8.0f,8.0f,6.0f,1.3f);
        g.fillRect(cx-5.0f,cy+1.0f,10.0f,5.0f);
    } else if(id=="cetus-open") {
        juce::Path folder;
        folder.startNewSubPath(cx-9.0f,cy-4.0f);
        folder.lineTo(cx-9.0f,cy-7.0f);folder.lineTo(cx-2.0f,cy-7.0f);
        folder.lineTo(cx+1.0f,cy-4.0f);folder.lineTo(cx+8.0f,cy-4.0f);
        folder.lineTo(cx+8.0f,cy+6.0f);folder.lineTo(cx-9.0f,cy+6.0f);folder.closeSubPath();
        g.strokePath(folder,juce::PathStrokeType(1.65f));
        g.drawLine(cx-5.0f,cy-1.0f,cx+4.0f,cy-1.0f,1.2f);
    } else {
        const bool redo=id=="cetus-redo";
        juce::Path arc;
        const float left=cx-8.0f,topY=cy-7.0f;
        arc.addArc(left,topY,16.0f,14.0f,redo?-1.1f:0.7f,
                   redo?2.55f:4.45f,true);
        g.strokePath(arc,juce::PathStrokeType(1.9f,juce::PathStrokeType::curved,juce::PathStrokeType::rounded));
        juce::Path tip;
        const float dir=redo ? 1.0f : -1.0f;
        tip.startNewSubPath(cx+dir*7.3f,cy-4.6f);
        tip.lineTo(cx+dir*2.9f,cy-7.0f);
        tip.lineTo(cx+dir*4.6f,cy-1.4f);
        g.strokePath(tip,juce::PathStrokeType(1.85f));
    }
}
void CetusproEQAudioProcessorEditor::CetusLookAndFeel::drawRotarySlider(
    juce::Graphics& g, int x, int y, int w, int h, float t, float from, float to, juce::Slider&) {
    auto bounds=juce::Rectangle<float>((float)x,(float)y,(float)w,(float)h).reduced(7.0f);
    const auto c=bounds.getCentre();
    const float radius=juce::jmin(bounds.getWidth(),bounds.getHeight())*.33f;
    const float angle=from+(to-from)*t;
    g.setColour(juce::Colours::black.withAlpha(.5f));
    g.fillEllipse(c.x-radius*1.2f+1.3f,c.y-radius*1.2f+2.2f,2.4f*radius,2.4f*radius);
    juce::ColourGradient body(juce::Colour::fromRGB(90,103,116),c.x-radius,c.y-radius,
                              juce::Colour::fromRGB(18,24,33),c.x+radius,c.y+radius,false);
    body.addColour(.4,juce::Colour::fromRGB(50,61,72));
    g.setGradientFill(body);
    g.fillEllipse(c.x-radius*1.05f,c.y-radius*1.05f,2.1f*radius,2.1f*radius);
    g.setColour(juce::Colour::fromRGB(122,139,152).withAlpha(.58f));
    g.drawEllipse(c.x-radius*1.05f,c.y-radius*1.05f,2.1f*radius,2.1f*radius,1.1f);
    const float faceRadius=radius*.77f;
    juce::ColourGradient face(juce::Colour::fromRGB(79,92,104),c.x-faceRadius,c.y-faceRadius,
                              juce::Colour::fromRGB(27,37,48),c.x+faceRadius,c.y+faceRadius,false);
    g.setGradientFill(face);
    g.fillEllipse(c.x-faceRadius,c.y-faceRadius,faceRadius*2.0f,faceRadius*2.0f);
    juce::Path track,active;
    const float ring=radius*1.25f;
    track.addCentredArc(c.x,c.y,ring,ring,0.0f,from,to,true);
    active.addCentredArc(c.x,c.y,ring,ring,0.0f,from,angle,true);
    g.setColour(juce::Colour::fromRGB(62,82,95));
    g.strokePath(track,juce::PathStrokeType(4.4f,juce::PathStrokeType::curved,juce::PathStrokeType::rounded));
    g.setColour(cyan);g.strokePath(active,juce::PathStrokeType(4.2f,juce::PathStrokeType::curved,juce::PathStrokeType::rounded));
    const float pX=c.x+std::sin(angle)*faceRadius*.76f;
    const float pY=c.y-std::cos(angle)*faceRadius*.76f;
    g.setColour(white.withAlpha(.90f));g.drawLine(c.x,c.y,pX,pY,1.8f);
    g.setColour(white.withAlpha(.85f));g.fillEllipse(pX-1.8f,pY-1.8f,3.6f,3.6f);
}'''
cs=cs[:start]+look+cs[end:]
# Replace resized layout
start=cs.index('void CetusproEQAudioProcessorEditor::resized() {')
end=cs.index('\nvoid CetusproEQAudioProcessorEditor::updateSpectrum()',start)
newresize=r'''void CetusproEQAudioProcessorEditor::resized() {
    // Compact 1080 x 594 layout: all controls remain within the plugin bounds.
    presets.setBounds(252,22,252,28);
    applyPresetButton.setBounds(510,22,46,28);
    savePresetButton.setBounds(562,22,30,28);
    openPresetButton.setBounds(596,22,30,28);
    undoButton.setBounds(641,22,30,28);
    redoButton.setBounds(675,22,30,28);
    initButton.setBounds(723,22,78,28);
    analyzerButton.setBounds(807,22,104,28);
    prePostButton.setBounds(917,22,62,28);
    const auto lower=bottomRect();
    const int listX=lower.getX()+12,listY=lower.getY()+38;
    for(int i=0;i<CetusproEQAudioProcessor::numBands;++i)
        bandButtons[(size_t)i].setBounds(listX+(i%2)*49,listY+(i/2)*27,44,23);
    bandType.setBounds(147,388,133,28);
    bandMode.setBounds(286,388,112,28);
    dynamicOn.setBounds(407,389,96,26);
    sendLabel.setBounds(519,373,103,15);
    send.setBounds(519,388,115,28);
    listenLabel.setBounds(644,373,116,15);
    listen.setBounds(644,388,122,28);
    outputLabel.setBounds(962,388,88,19);
    output.setBounds(962,410,87,116);
    for(int i=0;i<7;++i){
        auto& k=knobs[(size_t)i];
        const int x=142+i*115;
        k.label.setBounds(x,423,102,15);
        k.slider.setBounds(x+5,438,90,86);
    }
    bandOn.setBounds(150,537,68,22);
    bypass.setBounds(225,537,85,22);
    holdButton.setBounds(340,536,106,23);
    smoothButton.setBounds(453,536,92,23);
    updateHudPosition();
}'''
cs=cs[:start]+newresize+cs[end:]
# drawHeader updated
start=cs.index('void CetusproEQAudioProcessorEditor::drawHeader(')
end=cs.index('\nvoid CetusproEQAudioProcessorEditor::drawSpectrumAndCurve(',start)
header=r'''void CetusproEQAudioProcessorEditor::drawHeader(juce::Graphics& g) {
    const auto h=headerRect().toFloat();
    g.setColour(juce::Colours::black.withAlpha(.55f));
    g.fillRoundedRectangle(h.translated(0.0f,2.0f),10.0f);
    juce::ColourGradient chrome(juce::Colour::fromRGB(51,62,74),h.getCentreX(),h.getY(),
                                juce::Colour::fromRGB(17,25,36),h.getCentreX(),h.getBottom(),false);
    chrome.addColour(.20,juce::Colour::fromRGB(31,42,55));
    g.setGradientFill(chrome);g.fillRoundedRectangle(h,10.0f);
    g.setColour(juce::Colour::fromRGB(90,112,129).withAlpha(.65f));g.drawRoundedRectangle(h,10.0f,1.0f);
    juce::ColourGradient glow(cyan.withAlpha(.84f),h.getX()+175,h.getY(),cyan.withAlpha(0.0f),h.getX()+575,h.getY(),false);
    g.setGradientFill(glow);g.fillRect(h.getX()+175,h.getY(),400.0f,1.3f);
    g.setColour(juce::Colour::fromRGB(64,220,223));g.fillEllipse(24.0f,22.0f,28.0f,28.0f);
    g.setColour(juce::Colour::fromRGB(23,31,42));g.fillEllipse(35.0f,16.0f,28.0f,28.0f);
    g.setColour(white);g.setFont(juce::FontOptions(10.6f,juce::Font::bold));
    g.drawText("CETUS",63,21,65,14,juce::Justification::centredLeft);
    g.setFont(juce::FontOptions(8.3f));g.drawText("PRODUCTION",63,34,82,14,juce::Justification::centredLeft);
    g.setColour(juce::Colour::fromRGB(111,130,146));g.fillRect(145,20,1,28);
    g.setColour(white);g.setFont(juce::FontOptions(18.5f,juce::Font::bold));
    g.drawText("cetuspro",154,18,99,24,juce::Justification::centredLeft);
    g.setColour(cyan);g.drawText("EQ",240,18,32,24,juce::Justification::centredLeft);
    g.setColour(muted);g.setFont(juce::FontOptions(9.0f));
    g.drawText("Dynamic EQ",154,41,86,12,juce::Justification::centredLeft);
    g.setColour(muted);g.setFont(juce::FontOptions(9.0f));
    g.drawText("v0.5.2",995,29,65,16,juce::Justification::centredRight);
}'''
cs=cs[:start]+header+cs[end:]
# meter replace
start=cs.index('void CetusproEQAudioProcessorEditor::drawMeter(')
end=cs.index('\nvoid CetusproEQAudioProcessorEditor::drawHud(',start)
meter=r'''void CetusproEQAudioProcessorEditor::drawMeter(juce::Graphics& g) {
    const auto r=meterRect();
    g.setColour(panel);g.fillRoundedRectangle(r.toFloat(),10.0f);
    g.setColour(white);g.setFont(juce::FontOptions(11.0f,juce::Font::bold));
    g.drawText("OUT",r.getX(),r.getY()+7,r.getWidth(),16,juce::Justification::centred);
    const int barTop=r.getY()+33,barBottom=r.getBottom()-44;
    const float peaks[2]={meterLeft,meterRight};
    for(int channel=0;channel<2;++channel){
        const int x=r.getX()+10+channel*19;
        g.setColour(inner);g.fillRoundedRectangle((float)x,(float)barTop,13.0f,(float)(barBottom-barTop),3.0f);
        const float frac=juce::jlimit(0.0f,1.0f,(peaks[channel]+60.0f)/60.0f);
        const float height=frac*(float)(barBottom-barTop);
        if(height>0.0f){
            juce::ColourGradient grad(juce::Colour::fromRGB(53,225,163),(float)x,(float)barBottom,
                                     juce::Colour::fromRGB(249,208,77),(float)x,(float)barTop,false);
            grad.addColour(.83,juce::Colour::fromRGB(246,100,88));
            g.setGradientFill(grad);g.fillRoundedRectangle((float)x,(float)barBottom-height,13.0f,height,2.0f);
        }
        g.setColour(muted);g.setFont(juce::FontOptions(9.0f));
        g.drawText(channel==0?"L":"R",x-1,barBottom+3,14,13,juce::Justification::centred);
    }
    for(int db : {0,-6,-12,-24,-36,-48,-60}) {
        const float y=barTop+(float)(-db)/60.0f*(barBottom-barTop);
        g.setColour(juce::Colour::fromRGB(117,143,157));
        g.drawHorizontalLine(juce::roundToInt(y),r.getX()+48,r.getX()+51);
        g.setColour(muted);g.setFont(juce::FontOptions(8.6f));
        g.drawText(juce::String(db),r.getX()+54,juce::roundToInt(y)-7,24,14,juce::Justification::centredRight);
    }
    const float peak=juce::jmax(meterLeft,meterRight);
    const juce::String value=peak<=-89.0f?"-inf":juce::String(peak,1);
    g.setColour(white);g.setFont(juce::FontOptions(9.0f,juce::Font::bold));
    g.drawText(value+" dB",r.getX()+2,r.getBottom()-23,r.getWidth()-4,16,juce::Justification::centred);
}'''
cs=cs[:start]+meter+cs[end:]
# lower drawing replace
start=cs.index('void CetusproEQAudioProcessorEditor::drawBottom(')
end=cs.index('\nvoid CetusproEQAudioProcessorEditor::paint(',start)
lower=r'''void CetusproEQAudioProcessorEditor::drawBottom(juce::Graphics& g) {
    const auto lower=bottomRect();
    g.setColour(juce::Colours::black.withAlpha(.45f));
    g.fillRoundedRectangle(lower.toFloat().translated(0,1),10.0f);
    juce::ColourGradient body(juce::Colour::fromRGB(23,35,48),lower.getCentreX(),(float)lower.getY(),
                             juce::Colour::fromRGB(12,22,33),lower.getCentreX(),(float)lower.getBottom(),false);
    g.setGradientFill(body);g.fillRoundedRectangle(lower.toFloat(),10.0f);
    g.setColour(grid.withAlpha(.63f));
    g.drawRoundedRectangle(lower.toFloat(),10.0f,1.0f);
    g.drawVerticalLine(133,(float)lower.getY()+10,(float)lower.getBottom()-10);
    g.drawVerticalLine(953,(float)lower.getY()+10,(float)lower.getBottom()-10);
    g.setColour(muted);g.setFont(juce::FontOptions(10.0f,juce::Font::bold));
    g.drawText("BANDS",lower.getX()+12,lower.getY()+11,85,13,juce::Justification::centredLeft);
    g.setFont(juce::FontOptions(9.5f));
    g.drawText("FILTER",147,374,78,13,juce::Justification::centredLeft);
    g.drawText("MODE",286,374,60,13,juce::Justification::centredLeft);
    g.drawText("CETUS LINK SEND",519,374,112,13,juce::Justification::centredLeft);
    g.drawText("DETECTOR",644,374,106,13,juce::Justification::centredLeft);
    g.drawText("OUTPUT",966,376,78,13,juce::Justification::centred);
    g.setColour(juce::Colour::fromRGB(63,80,93).withAlpha(.5f));
    g.drawHorizontalLine(532,144.0f,949.0f);
    g.setColour(muted);g.setFont(juce::FontOptions(9.0f));
    g.drawText("Analyzer",308,541,63,14,juce::Justification::centredLeft);
    g.setColour(cyan);g.setFont(juce::FontOptions(9.3f,juce::Font::bold));
    g.drawText("ZERO LATENCY",558,541,102,14,juce::Justification::centredLeft);
    g.setColour(muted);g.setFont(juce::FontOptions(8.8f));
    g.drawText("8-BAND / STEREO · MID · SIDE",704,541,231,14,juce::Justification::centredRight);
}'''
cs=cs[:start]+lower+cs[end:]
cs=repl(cs,'''    g.setColour(grid);g.drawHorizontalLine(615,20.0f,(float)getWidth()-20.0f);
    g.setColour(muted);g.setFont(juce::FontOptions(9.2f));
    g.drawText("CETUS PRODUCTION    •    cetusproEQ 0.5.1",25,621,290,14,juce::Justification::centredLeft);
    g.drawText("8 BANDS   /   DYNAMIC EQ   /   STEREO · MID · SIDE",getWidth()-435,621,405,14,
               juce::Justification::centredRight);''', '''    g.setColour(muted.withAlpha(.8f));g.setFont(juce::FontOptions(8.6f));
    g.drawText("CETUS PRODUCTION  /  cetusproEQ v0.5.2",20,574,290,13,juce::Justification::centredLeft);
    g.drawText("DYNAMIC EQ  •  8 BANDS",getWidth()-235,574,213,13,juce::Justification::centredRight);''')
# font and button model: ensure selected buttons show fill: custom drawButtonBackground uses toggle state, actual colours from button normal perhaps gradient accent. Color overrides currently unhandled, but selected difference via draw band numbers text face? handle later
# ensure removed old positions
assert '1180, 642' not in cs
assert '621,290' not in cs
# drop redundant output label if double overlay: outputLabel is a component and drawBottom also draws OUTPUT; hide outputLabel.
cs=cs.replace('outputLabel.setBounds(962,388,88,19);','outputLabel.setBounds(962,388,88,19);outputLabel.setVisible(false);')
# hide send/listen labels since drawn by drawBottom
cs=cs.replace('sendLabel.setBounds(519,373,103,15);','sendLabel.setBounds(519,373,103,15);sendLabel.setVisible(false);')
cs=cs.replace('listenLabel.setBounds(644,373,116,15);','listenLabel.setBounds(644,373,116,15);listenLabel.setVisible(false);')
# Final layout adjustments.
cs=cs.replace('presets.setBounds(252,22,252,28);', 'presets.setBounds(264,22,240,28);')
cs=cs.replace('g.drawText("Analyzer",308,541,63,14,juce::Justification::centredLeft);', '')
cs=cs.replace('const auto face = selected ? cyan : panel2;', '''auto face = selected ? cyan : panel2;
    if(button.getButtonText().length()==1) {
        const auto marker=button.getButtonText()[0];
        if(marker>='1' && marker<='8') {
            const auto bandFill=button.findColour(juce::TextButton::buttonColourId);
            if(bandFill!=panel2)face=bandFill;
        }
    }''')
h.write_text(hs, encoding='utf-8')
c.write_text(cs, encoding='utf-8')
cm=dst/'CMakeLists.txt'
cm.write_text(cm.read_text(encoding='utf-8').replace('VERSION 0.5.1','VERSION 0.5.2'), encoding='utf-8')
workflow=dst/'.github/workflows/build-plugins.yml'
w=workflow.read_text(encoding='utf-8').replace('"feature/cetusproeq-v0.5.1-polish"','"feature/cetusproeq-v0.5.2-compact-3d"').replace('v0.5.1','v0.5.2')
workflow.write_text(w, encoding='utf-8')
(dst/'README.md').write_text((dst/'README.md').read_text(encoding='utf-8')+'''\n\n## v0.5.2 compact 3D visual pass\n- Editor resized to 1080 × 594 for laptop screens (original was 1180 × 642).\n- Glossy/gradient 3D header buttons and metallic rotary controls; functional icon Save/Open/Undo/Redo controls.\n- Output meter with labelled 0, −6, −12, −24, −36, −48, −60 dB ticks, plus numeric peak.\n- Lower panel rebuilt with non-overlapping controls and labels.\n- DSP C++ unchanged; stereo, mid/side, 8 bands and filter slopes retained.\n''', encoding='utf-8')
print('Applied compact 3D visual patch v0.5.2:', len(cs), 'chars in editor')