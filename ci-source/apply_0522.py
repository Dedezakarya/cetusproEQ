#!/usr/bin/env python3
"""v0.5.22 soft shading of controls, panels and meters, GUI-only.

Run immediately after ci-source/apply_0521.py. The v0.5.21 irregular satin
micrograin, all 8 bands, UI layout, Solo and Ø, FFT and the full audio DSP are
preserved. All changes are in Source/PluginEditor.cpp and CetusMetalSkin.h.
"""
from pathlib import Path
import hashlib

editor = Path("Source/PluginEditor.cpp")
skin = Path("Source/CetusMetalSkin.h")
cmake = Path("CMakeLists.txt")
dsp_files = [Path(v) for v in (
    "Source/PluginProcessor.cpp", "Source/PluginProcessor.h",
    "Source/CetusEQFilters.h", "Source/CetusLink.h")]
dsp_sha = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in dsp_files}

src = editor.read_text(encoding="utf8")
metal = skin.read_text(encoding="utf8")

def once(content, old, new, label):
    n=content.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: anchor count {n} (expected one): {old[:100]!r}")
    return content.replace(old,new,1)

# A 5-pass low-opacity shadow, rather than a single black slab. Only rendered
# in GUI; deterministic, no allocations, no blur filter and no bitmap grain loss.
soft_helper = r'''// Approximate a blurred contact shadow with layered anti-aliased contours.
// All strokes are outside the component surface, so brushed grain is intact.
inline void softShadow(juce::Graphics& g, juce::Rectangle<float> r,
                       float radius, float opacity=1.0f, float depth=1.5f) {
    if (r.isEmpty() || opacity<=0.0f) return;
    opacity=juce::jlimit(0.0f,1.0f,opacity);
    for (int layer=5; layer>=1; --layer) {
        const float spread=(float)layer*.67f;
        const float alpha=(.026f + (5-layer)*.012f)*opacity;
        g.setColour(juce::Colours::black.withAlpha(alpha));
        g.drawRoundedRectangle(r.expanded(spread).translated(.0f,depth+.38f),
                               radius+spread,1.15f);
    }
    g.setColour(juce::Colours::black.withAlpha(.145f*opacity));
    g.fillRoundedRectangle(r.translated(.25f,depth),radius);
}

// Subtle face-light reflection and edge diffusion for metal/glass controls.
// No additional stripes: use a continuous smooth gradient only.
inline void softBevel(juce::Graphics& g, juce::Rectangle<float> r,
                      float radius, float opacity=1.0f) {
    if (r.isEmpty() || opacity<=0.0f) return;
    opacity=juce::jlimit(0.0f,1.0f,opacity);
    auto inside=r.reduced(.70f);
    const float innerRadius=juce::jmax(1.0f,radius-.7f);
    juce::ColourGradient glow(juce::Colours::white.withAlpha(.125f*opacity),
                              inside.getCentreX(),inside.getY(),
                              juce::Colours::white.withAlpha(.008f*opacity),
                              inside.getCentreX(),inside.getBottom(),false);
    glow.addColour(.36,juce::Colours::white.withAlpha(.035f*opacity));
    g.setGradientFill(glow);
    g.drawRoundedRectangle(inside,innerRadius,.95f);
    g.setColour(juce::Colours::black.withAlpha(.17f*opacity));
    g.drawRoundedRectangle(r.reduced(1.45f),juce::jmax(1.0f,radius-1.4f),.75f);
}

'''
metal=once(metal,"inline void buttonBevel(",soft_helper+"inline void buttonBevel(",
           "Add reusable soft-shadow helpers")
start=metal.index("inline void buttonBevel(")
end=metal.index("inline void machinedKnob(",start)
new_button=r'''inline void buttonBevel(juce::Graphics& g, juce::Rectangle<float> bounds,
                        float opacity=1.0f) {
    if (bounds.isEmpty()) return;
    softBevel(g,bounds,5.5f,.80f*opacity);
    // Existing satin micrograin remains at the same, discreet strength.
    brushedSurface(g,bounds.reduced(1.0f),5.0f,.24f*opacity);
}

'''
metal=metal[:start]+new_button+metal[end:]

# Keep the v0.5.21 irregular micrograin strictly unchanged; soften only its
# light/shadow surroundings, not the grain generation or alpha tiling.
assert "inline const juce::Image& satinMicrograin()" in metal
assert "for (int i=0; i<4200; ++i)" in metal

src=once(src,
    '''    g.setColour(juce::Colours::black.withAlpha(.54f * opacity));
    g.fillRoundedRectangle(area.translated(1.4f, 3.0f).expanded(1.1f), radius + 1.0f);
    g.setColour(juce::Colours::black.withAlpha(.35f * opacity));
    g.drawRoundedRectangle(area.expanded(1.3f).translated(0.5f,1.1f), radius + 1.2f,1.4f);''',
    '''    // Ambient shadow instead of a hard black outline behind the panel.
    CetusMetal::softShadow(g,area,radius,.72f*opacity,1.6f);''',
    "Panel ambient shadow")

src=once(src,
    '''    juce::ColourGradient topGloss(juce::Colours::white.withAlpha(.115f * opacity), area.getCentreX(), area.getY() + 2.0f,
                                  juce::Colours::white.withAlpha(0.0f), area.getCentreX(), area.getY() + area.getHeight() * 0.18f, false);''',
    '''    // Broader, much softer studio reflection across the brushed aluminium.
    juce::ColourGradient topGloss(juce::Colours::white.withAlpha(.072f * opacity),
                                  area.getCentreX(),area.getY() + 1.8f,
                                  juce::Colours::white.withAlpha(0.0f),
                                  area.getCentreX(),area.getY() + area.getHeight()*.40f,false);
    topGloss.addColour(.36,juce::Colours::white.withAlpha(.028f*opacity));''',
    "Panel highlight")
src=once(src,
    '''    g.setColour(juce::Colour::fromRGB(112, 143, 164).withAlpha(.24f * opacity));
    g.drawRoundedRectangle(area.reduced(.5f), radius, 1.0f);
    g.setColour(cyan.withAlpha(.15f * opacity));
    g.drawRoundedRectangle(area.reduced(1.3f), radius - 0.8f, .8f);
    g.setColour(juce::Colours::black.withAlpha(.24f * opacity));
    g.drawRoundedRectangle(area.reduced(2.0f), radius - 1.4f, .7f);''',
    '''    g.setColour(juce::Colour::fromRGB(125,152,168).withAlpha(.16f*opacity));
    g.drawRoundedRectangle(area.reduced(.5f),radius,.82f);
    g.setColour(cyan.withAlpha(.065f*opacity));
    g.drawRoundedRectangle(area.reduced(1.3f),juce::jmax(1.0f,radius-.8f),.65f);
    g.setColour(juce::Colours::black.withAlpha(.13f*opacity));
    g.drawRoundedRectangle(area.reduced(2.0f),juce::jmax(1.0f,radius-1.4f),.65f);''',
    "Panel soft metallic rim")

# Buttons including 1-8, Undo/Redo, S, Ø and analyzer buttons. Their event
# handlers and active colour lookup are completely unchanged.
src=once(src,
    '''    // Muted graphite finish, stronger contact shadow, narrow controlled highlight.
    g.setColour(juce::Colours::black.withAlpha(.82f));
    g.fillRoundedRectangle(r.translated(0.9f,2.4f).expanded(.4f),6.0f);
    juce::ColourGradient face(base.brighter(over ? .12f : .045f),r.getCentreX(),r.getY(),
                              base.darker(down ? .48f : .34f),r.getCentreX(),r.getBottom(),false);
    face.addColour(.31,base.interpolatedWith(juce::Colour::fromRGB(13,23,34),.20f));
    g.setGradientFill(face);g.fillRoundedRectangle(r,6.0f);
    g.setColour(juce::Colours::white.withAlpha(.065f));
    g.drawLine(r.getX()+5.0f,r.getY()+1.4f,r.getRight()-5.0f,r.getY()+1.4f,.7f);
    g.setColour(juce::Colour::fromRGB(91,112,128).withAlpha(.55f));
    g.drawRoundedRectangle(r,6.0f,.9f);
    g.setColour(juce::Colours::black.withAlpha(.45f));
    g.drawLine(r.getX()+4.0f,r.getBottom()-1.2f,r.getRight()-4.0f,r.getBottom()-1.2f,.8f);''',
    '''    // Satin graphite: a low-contrast ambient shadow, curved face reflection
    // and very soft bevel. S/Ø keep their existing orange selected state.
    CetusMetal::softShadow(g,r,6.0f,.90f,1.05f);
    const auto faceTop=base.interpolatedWith(juce::Colours::white,
                                            over ? .115f : .065f);
    const auto faceBottom=base.interpolatedWith(juce::Colours::black,
                                               down ? .27f : .16f);
    juce::ColourGradient face(faceTop,r.getCentreX(),r.getY(),
                              faceBottom,r.getCentreX(),r.getBottom(),false);
    face.addColour(.23,base.interpolatedWith(juce::Colour::fromRGB(62,77,89),.13f));
    face.addColour(.68,base.interpolatedWith(juce::Colours::black,.09f));
    g.setGradientFill(face);
    g.fillRoundedRectangle(r,6.0f);
    CetusMetal::softBevel(g,r,6.0f,over ? .95f : .74f);
    g.setColour(juce::Colour::fromRGB(106,126,143).withAlpha(.23f));
    g.drawRoundedRectangle(r.reduced(.30f),5.8f,.70f);''',
    "Button shading, including band and solo")

# Dropdown face/arrow keep same geometry and colours, but bevel gets soft
# lighting and the heavy drop-shadow is eliminated.
src=once(src,
    '''    g.setColour(juce::Colours::black.withAlpha(.87f));
    g.fillRoundedRectangle(r.translated(.8f,2.4f),5.4f);
    juce::ColourGradient face(juce::Colour::fromRGB(22,32,43),r.getCentreX(),r.getY(),
                              juce::Colour::fromRGB(8,16,25),r.getCentreX(),r.getBottom(),false);
    face.addColour(.4,juce::Colour::fromRGB(16,27,39));
    g.setGradientFill(face);g.fillRoundedRectangle(r,5.0f);
    g.setColour(juce::Colour::fromRGB(90,112,130).withAlpha(.68f));
    g.drawRoundedRectangle(r,5.0f,.9f);
    g.setColour(juce::Colours::white.withAlpha(.055f));
    g.drawLine(r.getX()+5.0f,r.getY()+1.2f,r.getRight()-5.0f,r.getY()+1.2f,.7f);''',
    '''    CetusMetal::softShadow(g,r,5.0f,.81f,1.15f);
    juce::ColourGradient face(juce::Colour::fromRGB(27,40,52),
                              r.getCentreX(),r.getY(),
                              juce::Colour::fromRGB(12,21,31),
                              r.getCentreX(),r.getBottom(),false);
    face.addColour(.34,juce::Colour::fromRGB(22,34,46));
    face.addColour(.75,juce::Colour::fromRGB(15,25,36));
    g.setGradientFill(face);
    g.fillRoundedRectangle(r,5.0f);
    CetusMetal::softBevel(g,r,5.0f,.73f);
    g.setColour(juce::Colour::fromRGB(96,119,136).withAlpha(.27f));
    g.drawRoundedRectangle(r.reduced(.25f),5.0f,.72f);''',
    "Dropdown / combo shadow and bevel")

# Analog toggle: reduce opaque black cast-shadow, soften thumb lighting.
src=once(src,
    '''    g.setColour(juce::Colours::black.withAlpha(.72f));
    g.fillRoundedRectangle(left, top + 1.3f, width, height, 7.0f);
    g.setColour(track);
    g.fillRoundedRectangle(left, top, width, height, 7.0f);
    g.setColour((on && enabled ? lit : inactive).withAlpha(.56f));
    g.drawRoundedRectangle(left+.45f, top+.45f, width-.9f, height-.9f, 6.7f, .95f);''',
    '''    CetusMetal::softShadow(g,{left,top,width,height},7.0f,.63f,.70f);
    g.setColour(track);
    g.fillRoundedRectangle(left,top,width,height,7.0f);
    CetusMetal::softBevel(g,{left,top,width,height},7.0f,.65f);
    g.setColour((on && enabled ? lit : inactive).withAlpha(.34f));
    g.drawRoundedRectangle(left+.45f,top+.45f,width-.9f,height-.9f,6.7f,.70f);''',
    "Toggle switch softened")
src=once(src,
    '''    juce::ColourGradient thumb(juce::Colour::fromRGB(210,222,229), thumbX, top+2.0f,
                                juce::Colour::fromRGB(101,118,132), thumbX, top+height-2.0f, false);''',
    '''    juce::ColourGradient thumb(juce::Colour::fromRGB(187,203,214),thumbX,top+2.0f,
                                juce::Colour::fromRGB(111,129,142),thumbX,top+height-2.0f,false);
    thumb.addColour(.42,juce::Colour::fromRGB(155,174,187));''',
    "Switch thumb lighting")

# Rotary control keeps original satin grain, coloured arc and pointer.
src=once(src,
    '''    g.setColour(juce::Colours::black.withAlpha(.73f));
    g.fillEllipse(c.x-radius*1.13f+1.0f,c.y-radius*1.10f+2.0f,2.26f*radius,2.26f*radius);''',
    '''    // Wide low-alpha ring replaces a solid dark halo beneath each knob.
    for(int layer=5;layer>=1;--layer) {
        const float expand=radius*(1.035f+.025f*(float)layer);
        g.setColour(juce::Colours::black.withAlpha(.023f+.012f*(5-layer)));
        g.drawEllipse(c.x-expand,c.y-expand+1.0f,2.0f*expand,2.0f*expand,1.1f);
    }
    g.setColour(juce::Colours::black.withAlpha(.20f));
    g.fillEllipse(c.x-radius*1.045f,c.y-radius*1.04f+1.0f,
                  2.09f*radius,2.09f*radius);''',
    "Rotary softened ambient shadow")
src=once(src,
    '''    juce::ColourGradient topLight(juce::Colours::white.withAlpha(.19f),c.x-faceRadius*.3f,c.y-faceRadius,
                                  juce::Colours::white.withAlpha(0.0f),c.x+faceRadius*.25f,c.y-faceRadius*.08f,false);''',
    '''    juce::ColourGradient topLight(juce::Colours::white.withAlpha(.115f),
                                  c.x-faceRadius*.35f,c.y-faceRadius,
                                  juce::Colours::white.withAlpha(0.0f),
                                  c.x+faceRadius*.30f,c.y+faceRadius*.30f,false);
    topLight.addColour(.34,juce::Colours::white.withAlpha(.048f));''',
    "Knob softer studio highlight")
src=once(src,
    '''    g.setColour(juce::Colours::white.withAlpha(.15f));
    g.drawEllipse(c.x-faceRadius,c.y-faceRadius,2*faceRadius,2*faceRadius,.7f);''',
    '''    g.setColour(juce::Colours::white.withAlpha(.095f));
    g.drawEllipse(c.x-faceRadius,c.y-faceRadius,2*faceRadius,2*faceRadius,.65f);''',
    "Knob subtle face rim")

# Cabinet separators are part of the panel finish, not deep grooves.
src=once(src,
    '''    g.setColour(juce::Colours::black.withAlpha(.45f));
    g.fillRoundedRectangle(lower.toFloat().translated(0,1),10.0f);''',
    '''    g.setColour(juce::Colours::black.withAlpha(.13f));
    g.fillRoundedRectangle(lower.toFloat().translated(0,.6f),10.0f);''',
    "Bottom ambient shadow")
src=once(src,
    '''    const auto divider = juce::Colour::fromRGB(113, 143, 164).withAlpha(.37f);
    g.setColour(juce::Colours::black.withAlpha(.31f));''',
    '''    const auto divider = juce::Colour::fromRGB(113,143,164).withAlpha(.22f);
    g.setColour(juce::Colours::black.withAlpha(.16f));''',
    "Bottom panel division shading")
src=once(src,
    '''    g.setColour(juce::Colours::black.withAlpha(.28f));
    g.fillRect(489, 427, 2, 97);''',
    '''    g.setColour(juce::Colours::black.withAlpha(.14f));
    g.fillRect(489, 427, 2, 97);''',
    "Bottom mid separator")

# Preserve brand, spectrum, GUI dimensions and 0.5.21 procedural micrograin.
for token in (
    'satinMicrograin()', "CetusMetal::analogKnobTexture(g,c,faceRadius,radius)",
    'CetusMetal::brushedSurface(g, area, radius, 0.98f * opacity)',
    'placeDesignChild(soloButton, {900,390,32,24})',
    'placeDesignChild(polarityButton, {986,536,39,22})',
    'g.drawText("ZERO LATENCY"',
    'juce::String::fromUTF8("\\xC3\\x98")',
    'BinaryData::CetusUndo_png', 'BinaryData::CetusRedo_png'):
    if token not in src+metal:
        raise RuntimeError("Prior feature removed: "+token)

assert src.count("v0.5.21")>=2
src=src.replace("v0.5.21","v0.5.22")
cm=cmake.read_text(encoding="utf8")
assert cm.count("VERSION 0.5.21")==1
cm=cm.replace("VERSION 0.5.21","VERSION 0.5.22",1)

editor.write_text(src,encoding="utf8")
skin.write_text(metal,encoding="utf8")
cmake.write_text(cm,encoding="utf8")

for path in dsp_files:
    if hashlib.sha256(path.read_bytes()).hexdigest()!=dsp_sha[str(path)]:
        raise RuntimeError("DSP CHANGED: "+str(path))

print("cetusproEQ v0.5.22: softer button, dropdown, switch, knob and cabinet light/shadow; satin grain and DSP unchanged")
