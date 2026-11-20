#!/usr/bin/env python3
"""v0.5.20: stronger brushed metal panel + analog machined knobs.
GUI painting only. Runs after the verified v0.5.19 generated GUI.
Does not touch audio code, filter coefficients, parameter state or layout.
"""
from pathlib import Path
import hashlib

editor=Path("Source/PluginEditor.cpp")
skin=Path("Source/CetusMetalSkin.h")
cm=Path("CMakeLists.txt")
sources=[Path(x) for x in ("Source/PluginProcessor.cpp","Source/PluginProcessor.h",
                           "Source/CetusEQFilters.h","Source/CetusLink.h")]
dsp_before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
cpp=editor.read_text(encoding="utf-8")
metal=skin.read_text(encoding="utf-8")

def change_once(source,old,new,why):
    n=source.count(old)
    if n!=1:
        raise RuntimeError(f"{why}: expected one anchor, found {n}: {old[:130]!r}")
    return source.replace(old,new,1)

start=metal.index("inline void brushedSurface(")
stop=metal.index("inline void buttonBevel(",start)
new_brush=r'''inline void brushedSurface(juce::Graphics& g, juce::Rectangle<float> bounds,
                           float radius, float opacity = 1.0f) {
    if (bounds.isEmpty() || opacity <= 0.0f) return;
    opacity = juce::jlimit(0.0f,1.0f,opacity);
    g.saveState();
    juce::Path mask;
    mask.addRoundedRectangle(bounds, radius);
    g.reduceClipRegion(mask);

    // Satin-black aluminium, milled horizontally. Directional room lighting
    // is deterministic; no texture file decoding or pixels touched in paint.
    juce::ColourGradient light(
        juce::Colour::fromRGB(182,202,217).withAlpha(0.20f*opacity),
        bounds.getX()+bounds.getWidth()*0.16f,bounds.getY(),
        juce::Colour::fromRGB(2,9,18).withAlpha(0.25f*opacity),
        bounds.getRight(),bounds.getBottom(),false);
    light.addColour(0.27,juce::Colour::fromRGB(115,140,158).withAlpha(0.11f*opacity));
    light.addColour(0.62,juce::Colour::fromRGB(26,43,58).withAlpha(0.09f*opacity));
    g.setGradientFill(light);
    g.fillRect(bounds);

    // Linear abrasive grain: a restrained dense field of 0.5px micro-strokes
    // broken up by sparse brighter machining passes. Fully clipped to panel.
    const int first=juce::roundToInt(bounds.getY());
    const int last=juce::roundToInt(bounds.getBottom());
    const float x1=bounds.getX()+radius*.40f;
    const float x2=bounds.getRight()-radius*.40f;
    for(int y=first+2;y<last-2;y+=2) {
        const unsigned v=static_cast<unsigned>((y-first)*37+17);
        const float variation=static_cast<float>(v%9)/9.0f;
        const bool polished=(v%7)==0;
        const float alpha=(polished ? .115f : .073f)
            +.032f*variation;
        g.setColour((polished ? juce::Colours::white : juce::Colours::black)
            .withAlpha(alpha*opacity));
        g.drawHorizontalLine(y,x1,x2);
        if (((y-first)%10)==2) {
            g.setColour(juce::Colour::fromRGB(197,215,225).withAlpha(.095f*opacity));
            g.drawLine(x1+5.0f,(float)y+.55f,x2-4.0f,(float)y+.55f,.52f);
        }
    }

    // Raised metal lip and narrow lower shadow give a physical cabinet edge.
    g.setColour(juce::Colours::white.withAlpha(.30f*opacity));
    g.drawLine(bounds.getX()+radius,bounds.getY()+1.6f,
               bounds.getRight()-radius,bounds.getY()+1.6f,0.75f);
    g.setColour(juce::Colours::black.withAlpha(.38f*opacity));
    g.drawLine(bounds.getX()+radius,bounds.getBottom()-2.4f,
               bounds.getRight()-radius,bounds.getBottom()-2.4f,1.15f);
    g.restoreState();
}

// A machined anodised knob face. Called after the graphite base face but
// before the pointer/coloured ring, so control readability remains intact.
inline void analogKnobTexture(juce::Graphics& g, juce::Point<float> centre,
                              float faceRadius, float outerRadius) {
    if (faceRadius <= 2.0f) return;
    const float x=centre.x,y=centre.y;
    // A radial knurled rim outside the face (40 faint alternating cuts).
    for(int i=0;i<48;++i) {
        const float angle=juce::MathConstants<float>::twoPi*(float)i/48.0f;
        const float dx=std::sin(angle),dy=-std::cos(angle);
        const float inner=outerRadius*.825f,outer=outerRadius*.969f;
        g.setColour((i%2==0 ? juce::Colours::white : juce::Colours::black)
                    .withAlpha(i%2==0 ? .20f : .32f));
        g.drawLine(x+dx*inner,y+dy*inner,x+dx*outer,y+dy*outer,.62f);
    }

    g.saveState();
    juce::Path disc;
    disc.addEllipse(x-faceRadius,y-faceRadius,2*faceRadius,2*faceRadius);
    g.reduceClipRegion(disc);
    // Lathe-brushed dark graphite face with upward soft reflection.
    juce::ColourGradient sheen(juce::Colour::fromRGB(175,194,204).withAlpha(.31f),
                               x-faceRadius*.65f,y-faceRadius*.9f,
                               juce::Colour::fromRGB(12,20,29).withAlpha(.08f),
                               x+faceRadius*.72f,y+faceRadius*.8f,false);
    sheen.addColour(.39,juce::Colour::fromRGB(96,120,137).withAlpha(.15f));
    g.setGradientFill(sheen);
    g.fillEllipse(x-faceRadius,y-faceRadius,2*faceRadius,2*faceRadius);
    // Fine machining traces catch the light as the knob moves.
    for(int i=-18;i<=18;++i) {
        const float yy=y+faceRadius*(float)i/19.0f;
        const bool bright=(i%3==0);
        g.setColour((bright ? juce::Colours::white : juce::Colours::black)
            .withAlpha(bright ? .092f : .057f));
        g.drawLine(x-faceRadius,yy,x+faceRadius,yy,.48f);
    }
    // Concentric tool paths, plus a very subtle bevel at the inner circle.
    for(int ring=0;ring<5;++ring) {
        const float rad=faceRadius*(.32f+.12f*(float)ring);
        g.setColour(juce::Colours::white.withAlpha((ring%2==0)? .083f:.042f));
        g.drawEllipse(x-rad,y-rad,2*rad,2*rad,.50f);
    }
    g.restoreState();
    g.setColour(juce::Colour::fromRGB(210,224,232).withAlpha(.36f));
    g.drawEllipse(x-faceRadius+.6f,y-faceRadius+.6f,
                  2*faceRadius-1.2f,2*faceRadius-1.2f,.86f);
    g.setColour(juce::Colours::black.withAlpha(.50f));
    g.drawEllipse(x-faceRadius-1.0f,y-faceRadius-1.0f,
                  2*faceRadius+2.0f,2*faceRadius+2.0f,1.1f);
}

'''
metal=metal[:start]+new_brush+metal[stop:]
assert metal.count("inline void analogKnobTexture")==1

# The existing panel uses drawGlass with the helper at half opacity.
# Increasing this applies true brushed steel across the lower controls,
# header and any other existing glass-panel calls.
cpp=change_once(cpp,
    "    CetusMetal::brushedSurface(g, area, radius, 0.50f * opacity);",
    "    CetusMetal::brushedSurface(g, area, radius, 0.98f * opacity);",
    "Increase brushed metal opacity")
cpp=change_once(cpp,
    "    juce::ColourGradient topGloss(juce::Colours::white.withAlpha(.042f * opacity),",
    "    juce::ColourGradient topGloss(juce::Colours::white.withAlpha(.115f * opacity),",
    "Enhance high edge of light gradient")

# Preserve the original knob position, arc and colour; overlay a lathe-textured
# face on the existing shape, then keep topLight and the pointer above it.
cpp=change_once(cpp,
    '''    g.setGradientFill(face);
    g.fillEllipse(c.x-faceRadius,c.y-faceRadius,2*faceRadius,2*faceRadius);
    // Preserve the existing graphite knob geometry; add a very soft top-down reflection.''',
    '''    g.setGradientFill(face);
    g.fillEllipse(c.x-faceRadius,c.y-faceRadius,2*faceRadius,2*faceRadius);
    // Satin machined grain, controlled radial edge and studio-light reflections.
    CetusMetal::analogKnobTexture(g,c,faceRadius,radius);
    // Keep the control readable while increasing the physical depth of the face.''',
    "Overlay machined texture in all rotary knobs")

# Less plastic-looking top light, more restrained satin highlight.
cpp=change_once(cpp,
    '''    juce::ColourGradient topLight(juce::Colours::white.withAlpha(.16f),c.x,c.y-faceRadius,
                                  juce::Colours::white.withAlpha(0.0f),c.x,c.y-faceRadius*.05f,false);''',
    '''    juce::ColourGradient topLight(juce::Colours::white.withAlpha(.19f),c.x-faceRadius*.3f,c.y-faceRadius,
                                  juce::Colours::white.withAlpha(0.0f),c.x+faceRadius*.25f,c.y-faceRadius*.08f,false);''',
    "Directional overhead knob specular")

# Metadata and GUI footer only; plugin format/manufacturer IDs unaffected.
if cpp.count("v0.5.19")<2:
    raise RuntimeError("Cannot uniquely identify v0.5.19 editor version")
cpp=cpp.replace("v0.5.19","v0.5.20")
config=cm.read_text(encoding="utf-8")
if config.count("VERSION 0.5.19")!=1:
    raise RuntimeError("CMake version must be v0.5.19")
config=config.replace("VERSION 0.5.19","VERSION 0.5.20",1)

for token in ("CetusMetal::analogKnobTexture","CetusMetal::brushedSurface",
              'g.drawText("ZERO LATENCY"','soloButton.setButtonText("S")',
              'juce::String::fromUTF8("\\xC3\\x98")',
              'spectrumDb.fill(-96.0f)'):
    if token not in cpp:raise RuntimeError("A previous GUI feature was lost: "+token)

editor.write_text(cpp,encoding="utf-8")
skin.write_text(metal,encoding="utf-8")
cm.write_text(config,encoding="utf-8")
for path in sources:
    if hashlib.sha256(path.read_bytes()).hexdigest()!=dsp_before[str(path)]:
        raise RuntimeError("Audio DSP unexpectedly changed: "+str(path))
print("v0.5.20 satin brushed panels + machined knobs; zero DSP changes.")
