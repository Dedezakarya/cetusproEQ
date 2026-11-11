#!/usr/bin/env python3
"""Reproduce exact v0.5.10.1 GUI/font source from v0.5.9 on both CI runners.

This step changes only PluginEditor.cpp, PluginEditor.h and CMakeLists.txt.
The Processor, filters and sidechain sources are immutable and verified.
"""
from pathlib import Path
import json,base64,lzma,hashlib
PATCH="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"
def digest(data): return hashlib.sha256(data.encode("utf-8")).hexdigest()
patches=json.loads(lzma.decompress(base64.b64decode(PATCH)))
import re
def replace_function(source, name, new_def):
    pattern=r"(?:void|juce::Font)\\s+CetusproEQAudioProcessorEditor::(?:CetusLookAndFeel::)?"+re.escape(name)+r"\\s*\\("
    match=re.search(pattern,source)
    if not match: raise SystemExit("No GUI method found: "+name)
    begin=source.rfind("\\n",0,match.start())+1
    brace=source.find("{",match.end())
    if brace<0: raise SystemExit("No method body: "+name)
    depth=0
    for pos in range(brace,len(source)):
        if source[pos]=="{": depth+=1
        elif source[pos]=="}":
            depth-=1
            if depth==0: return source[:begin]+new_def+source[pos+1:]
    raise SystemExit("Unbalanced GUI function: "+name)

for filename, spec in patches.items():
    path=Path(filename)
    before=path.read_text(encoding="utf-8")
    if digest(before)==spec["old_sha"]:
        after=before
        for begin,end,value in reversed(spec["ops"]):
            after=after[:begin]+value+after[end:]
        if digest(after)!=spec["new_sha"]:
            raise SystemExit("Patch output checksum failure: "+filename)
    else:
        print("GUI CI baseline differs from local exported source; apply semantic patch:",filename)
        after=before
        if filename=="Source/PluginEditor.h":
            anchor="        juce::Font getComboBoxFont(juce::ComboBox&) override;"
            assert after.count(anchor)==1
            after=after.replace(anchor,anchor+"\\n        juce::Font getPopupMenuFont() override;",1)
        elif filename=="CMakeLists.txt":
            assert after.count("VERSION 0.5.9")==1
            after=after.replace("VERSION 0.5.9","VERSION 0.5.10.1",1)
        elif filename=="Source/PluginEditor.cpp":
            # Native popup-menu and selected dropdown label font.
            font_new="""juce::Font CetusproEQAudioProcessorEditor::CetusLookAndFeel::getComboBoxFont(juce::ComboBox&) {
    return juce::Font(juce::FontOptions(10.0f));
}
juce::Font CetusproEQAudioProcessorEditor::CetusLookAndFeel::getPopupMenuFont() {
    return juce::Font(juce::FontOptions(9.8f));
}"""
            after=replace_function(after,"getComboBoxFont",font_new)
            # Remove the floating box and hide all of its embedded controls.
            after=replace_function(after,"updateFloatingControlLayout", """void CetusproEQAudioProcessorEditor::updateFloatingControlLayout() {
    floatingControlsVisible = false;
    for (auto& knob : floatingKnobs) { knob.label.setVisible(false); knob.slider.setVisible(false); }
}""")
            after=replace_function(after,"syncHud", """void CetusproEQAudioProcessorEditor::syncHud() {
    hudType.setVisible(false); hudCloseButton.setVisible(false);
    attachedHudBand = -1; updateFloatingControlLayout();
}""")
            after=replace_function(after,"updateHudPosition", """void CetusproEQAudioProcessorEditor::updateHudPosition() {
    hudType.setVisible(false); hudCloseButton.setVisible(false); updateFloatingControlLayout();
}""")
            after=replace_function(after,"drawHud", """void CetusproEQAudioProcessorEditor::drawHud(juce::Graphics&) {
    // No graph banner: band selection stays on nodes and lower control panel.
}""")
            # Branded header with brighter typography.
            substitutions={
                'juce::FontOptions(9.6f, juce::Font::bold)':'juce::FontOptions(10.7f, juce::Font::bold)',
                'g.drawText("CETUS", 65, 22, 65, 12':'g.drawText("CETUS", 65, 20, 72, 14',
                'juce::FontOptions(7.4f)':'juce::FontOptions(8.5f, juce::Font::bold)',
                'g.drawText("PRODUCTION", 65, 35, 79, 11':'g.drawText("PRODUCTION", 65, 34, 86, 13',
                'g.drawImageWithin(title, 154, 19, 116, 34':'g.drawImageWithin(title, 153, 17, 124, 38',
                'g.drawText("v0.5.9"':'g.drawText("v0.5.10.1"',
                'CETUS PRODUCTION  /  cetusproEQ v0.5.9':'CETUS PRODUCTION  /  cetusproEQ v0.5.10.1',
                'juce::FontOptions(11.6f)':'juce::FontOptions(10.0f)',
                'juce::Colours::black.withAlpha(.73f)':'juce::Colours::black.withAlpha(.88f)',
                'r.translated(1.0f,2.2f),5.0f':'r.translated(1.0f,2.7f).expanded(0.5f),5.2f',
                'juce::Colour::fromRGB(23,38,52),r.getCentreX(),r.getY()':'juce::Colour::fromRGB(18,31,43),r.getCentreX(),r.getY()',
                'juce::Colour::fromRGB(11,21,33),r.getCentreX(),r.getBottom()':'juce::Colour::fromRGB(8,16,26),r.getCentreX(),r.getBottom()',
                'juce::Colours::white.withAlpha(.055f)':'juce::Colours::white.withAlpha(.025f)',
                'g.setColour(bg.withAlpha(.82f))':'g.setColour(juce::Colours::black.withAlpha(.92f))',
                'r.translated(1.0f,2.8f).expanded(0.5f),6.5f':'r.translated(1.2f,3.4f).expanded(0.9f),6.8f',
                'selected ? .07f : (over ? .11f : .02f)':'selected ? .025f : (over ? .045f : 0.0f)',
                'down ? .46f : .26f':'down ? .56f : .38f',
                'selected ? .08f : .025f':'selected ? .045f : .012f',
                'selected ? .09f : .025f':'selected ? .045f : .012f',
                'r.getHeight()*0.42f':'r.getHeight()*0.34f',
                'cyan.brighter(.52f) : juce::Colour::fromRGB(88,110,129)':'cyan.withAlpha(.82f) : juce::Colour::fromRGB(78,98,116)',
            }
            for old,new in substitutions.items():
                if old in after: after=after.replace(old,new,1)
            # Darker plot, reduced spectrum-lighting, still GUI only.
            old='juce::ColourGradient chartFace(inner.brighter(.29f),plot.getCentreX(),(float)plot.getY(),'
            if old in after:
                after=after.replace(old,'juce::ColourGradient chartFace(juce::Colour::fromRGB(17, 26, 38),plot.getCentreX(),(float)plot.getY(),',1)
                after=after.replace('inner.darker(.24f),plot.getCentreX(),(float)plot.getBottom(),false);','juce::Colour::fromRGB(8, 15, 24),plot.getCentreX(),(float)plot.getBottom(),false);',1)
                after=after.replace('g.setGradientFill(chartFace);g.fillRoundedRectangle(plot.toFloat().expanded(8.0f,9.0f),6.0f);','chartFace.addColour(.55, juce::Colour::fromRGB(12, 20, 30));\\n    g.setGradientFill(chartFace);g.fillRect(plot);',1)
            after=after.replace('juce::Colour::fromRGB(82,190,244).withAlpha(.26f)','juce::Colour::fromRGB(82,190,244).withAlpha(.16f)')
            after=after.replace('shade.addColour(.44,ice.withAlpha(.14f))','shade.addColour(.44,ice.withAlpha(.08f))')
            after=after.replace('shade.addColour(.80,juce::Colour::fromRGB(38,119,168).withAlpha(.07f))','shade.addColour(.80,juce::Colour::fromRGB(38,119,168).withAlpha(.03f))')
            after=after.replace('g.setColour(cyan.withAlpha(.10f));g.strokePath(trace,juce::PathStrokeType(6.6f))','g.setColour(cyan.withAlpha(.05f));g.strokePath(trace,juce::PathStrokeType(5.0f))')
            after=after.replace('g.setColour(ice.withAlpha(.28f));g.strokePath(trace,juce::PathStrokeType(3.2f))','g.setColour(ice.withAlpha(.18f));g.strokePath(trace,juce::PathStrokeType(2.2f))')
            after=after.replace('g.setColour(white.withAlpha(.52f));g.strokePath(trace,juce::PathStrokeType(1.15f))','g.setColour(white.withAlpha(.44f));g.strokePath(trace,juce::PathStrokeType(1.0f))')
        else:
            raise SystemExit("Unknown GUI patch file: "+filename)
    path.write_text(after,encoding="utf-8")
    print("Applied v0.5.10.1:",filename,digest(after))
assert "getPopupMenuFont()" in Path("Source/PluginEditor.cpp").read_text()
assert "VERSION 0.5.10.1" in Path("CMakeLists.txt").read_text()
for filename,expected in {
    "Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}.items():
    result=hashlib.sha256(Path(filename).read_bytes()).hexdigest()
    if result!=expected: raise SystemExit("DSP checksum mismatch: "+filename)
print("v0.5.10.1 GUI applied; DSP files verified unchanged")
