#!/usr/bin/env python3
"""v0.5.5: portable checksum-checked surface changes and byte-safe editor patch."""
from pathlib import Path
import base64,hashlib,json,lzma

PATCH = "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"
changes=json.loads(lzma.decompress(base64.b64decode(PATCH)))
for filename,meta in changes.items():
    if filename=="Source/PluginEditor.cpp":
        continue  # source may include Windows-1252 characters; use byte-safe anchors
    path=Path(filename)
    old=path.read_text(encoding="utf-8")
    digest=hashlib.sha256(old.encode("utf-8")).hexdigest()
    if digest != meta["before"]:
        raise SystemExit("Unexpected v0.5.4 input in "+filename+": "+digest)
    updated=old
    for start,end,value in reversed(meta["ops"]):
        updated=updated[:start]+value+updated[end:]
    if hashlib.sha256(updated.encode("utf-8")).hexdigest()!=meta["after"]:
        raise SystemExit("Output checksum mismatch: "+filename)
    path.write_text(updated,encoding="utf-8")
    print("Patched:",filename)

path=Path("Source/PluginEditor.cpp")
source=path.read_bytes()
def replace_exact(a,b):
    global source
    x=a.encode("utf-8"); y=b.encode("utf-8")
    if source.count(x)!=1:
        raise SystemExit("Expected exactly one GUI target: "+a[:65]+" count="+str(source.count(x)))
    source=source.replace(x,y,1)

start=source.index(b"void drawGlass(")
end=source.index(b"bool equalBlocks(",start)
source=source[:start]+b"""void drawGlass(juce::Graphics& g, juce::Rectangle<float> area, float radius,
               juce::Colour tint, float opacity = 1.0f) {
    // Vertical light, fine brushed steel; no diagonal highlights or stripes.
    g.setColour(juce::Colours::black.withAlpha(.30f * opacity));
    g.fillRoundedRectangle(area.translated(0.0f, 2.0f), radius);
    const auto steelTop = juce::Colour::fromRGB(65, 79, 90).interpolatedWith(tint, 0.14f);
    const auto steelBottom = juce::Colour::fromRGB(24, 37, 49).interpolatedWith(tint, 0.12f);
    juce::ColourGradient material(steelTop.withAlpha(.92f * opacity), area.getCentreX(), area.getY(),
                                   steelBottom.withAlpha(.98f * opacity), area.getCentreX(), area.getBottom(), false);
    material.addColour(.16, juce::Colour::fromRGB(55, 69, 81).withAlpha(.93f * opacity));
    material.addColour(.58, juce::Colour::fromRGB(37, 52, 64).withAlpha(.96f * opacity));
    g.setGradientFill(material);
    g.fillRoundedRectangle(area,radius);
    CetusMetal::brushedSurface(g,area,radius,0.55f * opacity);
    g.setColour(juce::Colour::fromRGB(155, 174, 187).withAlpha(.33f * opacity));
    g.drawRoundedRectangle(area.reduced(.5f),radius,1.0f);
    g.setColour(juce::Colours::black.withAlpha(.27f * opacity));
    g.drawRoundedRectangle(area.reduced(1.7f),radius-1.0f,.7f);
}

"""+source[end:]

replace_exact('''    g.setColour(white.withAlpha(down ? .15f : .35f));
    g.drawHorizontalLine(juce::roundToInt(r.getY()+1.3f),r.getX()+5.0f,r.getRight()-5.0f);
    CetusMetal::buttonBevel(g,r,0.82f);''','''    CetusMetal::buttonBevel(g,r,0.68f);''')

replace_exact('''    // Brushed-metal top-left catchlight / cyan luminous rim (purely decorative).
    juce::ColourGradient specular(white.withAlpha(.31f),c.x-radius*.65f,c.y-radius*.7f,
                                  white.withAlpha(0.0f),c.x+radius*.48f,c.y+radius*.55f,true);
    g.setGradientFill(specular);
    g.fillEllipse(c.x-faceRadius*.8f,c.y-faceRadius*.82f,faceRadius*1.25f,faceRadius*.87f);
    g.setColour(cyan.withAlpha(.19f));
    g.drawEllipse(c.x-radius*1.09f,c.y-radius*1.09f,2.18f*radius,2.18f*radius,1.5f);''',
'''    g.setColour(cyan.withAlpha(.13f));
    g.drawEllipse(c.x-radius*1.09f,c.y-radius*1.09f,2.18f*radius,2.18f*radius,1.25f);''')
replace_exact('''    g.drawVerticalLine(133,(float)lower.getY()+10,(float)lower.getBottom()-10);
    g.drawVerticalLine(953,(float)lower.getY()+10,(float)lower.getBottom()-10);
''','')
replace_exact('''    g.setColour(juce::Colour::fromRGB(63,80,93).withAlpha(.5f));
    g.drawHorizontalLine(532,144.0f,949.0f);
''','')
replace_exact('g.drawText("CETUS LINK SEND",519,374,112,13,juce::Justification::centredLeft);',
              'g.drawText("CETUS LINK SEND",519,374,116,12,juce::Justification::centredLeft);')
replace_exact('g.drawText("DETECTOR",644,374,106,13,juce::Justification::centredLeft);',
              'g.drawText("DETECTOR SOURCE",644,374,118,12,juce::Justification::centredLeft);')
replace_exact('g.drawText("OUTPUT",966,376,78,13,juce::Justification::centred);',
              'g.drawText("OUTPUT",966,375,78,12,juce::Justification::centred);')
replace_exact('CETUS PRODUCTION  /  cetusproEQ v0.5.4','CETUS PRODUCTION  /  cetusproEQ v0.5.5')
assert b'brushedSurface(g,area,radius,0.55f' in source
path.write_bytes(source)
print("Byte-safe GUI patch verified:",len(source),"bytes")
for item in ["Source/PluginProcessor.cpp","Source/PluginProcessor.h","Source/CetusEQFilters.h","Source/CetusLink.h"]:
    assert Path(item).exists(),item
print("v0.5.5 editor patched without touching DSP source files")
