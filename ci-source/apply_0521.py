#!/usr/bin/env python3
"""v0.5.21: replace obviously striped v0.5.20 panels with subtle satin-brushed metal.
Applies after ci-source/apply_0520.py. GUI-only; no DSP edits.
"""
from pathlib import Path
import hashlib

editor=Path("Source/PluginEditor.cpp")
skin=Path("Source/CetusMetalSkin.h")
cm=Path("CMakeLists.txt")
dsp_files=[Path(p) for p in ("Source/PluginProcessor.cpp",
 "Source/PluginProcessor.h", "Source/CetusEQFilters.h", "Source/CetusLink.h")]
checksum={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in dsp_files}
cpp=editor.read_text(encoding="utf8")
metal=skin.read_text(encoding="utf8")

# Replace only v0.5.20 panel grain with a cached small random-field texture.
# Dense, irregular MICRO abrasions give the perceived brush direction; long
# lines regularly spaced every 2px are never painted onto the panel.
start=metal.index("inline void brushedSurface(")
end=metal.index("// A machined anodised knob face.",start)
new_brushed=r'''// A small semi-transparent micrograin tile. Built ONCE at first GUI paint;
// steady-state paint only tiles a cached image, never regenerates scratches.
// Irregular stroke positions and lengths prevent the v0.5.20 barcode effect.
inline const juce::Image& satinMicrograin() {
    static const juce::Image tile = [] {
        juce::Image texture(juce::Image::ARGB, 256, 192, true);
        juce::Graphics tg(texture);
        juce::Random rng(0x5241B85);
        for (int i=0; i<4200; ++i) {
            const float px=rng.nextFloat()*256.0f;
            const float py=rng.nextFloat()*192.0f;
            const float length=3.0f + rng.nextFloat()*26.0f;
            const float tilt=(rng.nextFloat()-.5f)*.34f;
            const float strength=.035f + rng.nextFloat()*.092f;
            const bool reflection=rng.nextFloat()>.55f;
            tg.setColour((reflection
                ? juce::Colour::fromRGB(219,235,245)
                : juce::Colour::fromRGB(3,12,21)).withAlpha(strength));
            tg.drawLine(px,py,juce::jmin(255.7f,px+length),py+tilt,.42f);
        }
        return texture;
    }();
    return tile;
}

inline void brushedSurface(juce::Graphics& g, juce::Rectangle<float> bounds,
                           float radius, float opacity = 1.0f) {
    if (bounds.isEmpty() || opacity<=0.0f) return;
    opacity=juce::jlimit(0.0f,1.0f,opacity);
    g.saveState();
    juce::Path mask;
    mask.addRoundedRectangle(bounds,radius);
    g.reduceClipRegion(mask);

    // Directional satin metal reflectance, not alternating stripes.
    // Panel tint underneath is unchanged, so labels remain readable.
    juce::ColourGradient reflection(
        juce::Colour::fromRGB(186,205,218).withAlpha(.22f*opacity),
        bounds.getX()+bounds.getWidth()*.22f,bounds.getY(),
        juce::Colour::fromRGB(8,17,27).withAlpha(.26f*opacity),
        bounds.getRight(),bounds.getBottom(),false);
    reflection.addColour(.22, juce::Colour::fromRGB(139,162,176).withAlpha(.13f*opacity));
    reflection.addColour(.51, juce::Colour::fromRGB(60,82,98).withAlpha(.072f*opacity));
    reflection.addColour(.79, juce::Colour::fromRGB(20,35,48).withAlpha(.06f*opacity));
    g.setGradientFill(reflection);
    g.fillRect(bounds);

    // Irregular micro-abrasions, with no full-width lines or periodic rows.
    g.setTiledImageFill(satinMicrograin(),0,0,.88f*opacity);
    g.fillRect(bounds);

    // Physical panel edge: highlights only at boundary, not across the body.
    g.setColour(juce::Colours::white.withAlpha(.22f*opacity));
    g.drawRoundedRectangle(bounds.reduced(.7f),juce::jmax(0.0f,radius-.7f),.62f);
    g.setColour(juce::Colours::black.withAlpha(.22f*opacity));
    g.drawRoundedRectangle(bounds.reduced(1.7f),juce::jmax(0.0f,radius-1.7f),.60f);
    g.restoreState();
}

'''
metal=metal[:start]+new_brushed+metal[end:]

# v0.5.20 likewise drew hard evenly spaced straight lines across each knob.
# Keep the knurl, concentric tool paths, bevel, lighting and coloured rings,
# but replace the linear hatch by the SAME organic metallic micrograin.
old_knob=r'''    // Fine machining traces catch the light as the knob moves.
    for(int i=-18;i<=18;++i) {
        const float yy=y+faceRadius*(float)i/19.0f;
        const bool bright=(i%3==0);
        g.setColour((bright ? juce::Colours::white : juce::Colours::black)
            .withAlpha(bright ? .092f : .057f));
        g.drawLine(x-faceRadius,yy,x+faceRadius,yy,.48f);
    }'''
new_knob=r'''    // Fine anisotropic micrograin, no patterned stripes on the knob face.
    g.setTiledImageFill(satinMicrograin(),
                        juce::roundToInt(x-faceRadius),
                        juce::roundToInt(y-faceRadius),.71f);
    g.fillEllipse(x-faceRadius,y-faceRadius,2*faceRadius,2*faceRadius);'''
if metal.count(old_knob)!=1:
    raise RuntimeError("v0.5.20 hard-striped knob loop missing or ambiguous")
metal=metal.replace(old_knob,new_knob,1)
if "for(int y=first+2;y<last-2;y+=2)" in metal:
    raise RuntimeError("striped metal loop still active")
if "inline const juce::Image& satinMicrograin()" not in metal:
    raise RuntimeError("new micrograin tile not inserted")

if cpp.count("v0.5.20")<2:
    raise RuntimeError("Expected v0.5.20 editor footer and header")
cpp=cpp.replace("v0.5.20","v0.5.21")
cmt=cm.read_text(encoding="utf8")
if cmt.count("VERSION 0.5.20")!=1:
    raise RuntimeError("Missing expected v0.5.20 CMake version")
cmt=cmt.replace("VERSION 0.5.20","VERSION 0.5.21",1)
for required in ('CetusMetal::analogKnobTexture', 'CetusMetal::brushedSurface',
                 'placeDesignChild(soloButton, {900,390,32,24})',
                 'g.drawText("ZERO LATENCY"',
                 'juce::String::fromUTF8("\\xC3\\x98")'):
    if required not in cpp:
        raise RuntimeError("Existing GUI feature unexpectedly lost: "+required)

skin.write_text(metal,encoding="utf8")
editor.write_text(cpp,encoding="utf8")
cm.write_text(cmt,encoding="utf8")
for path in dsp_files:
    if hashlib.sha256(path.read_bytes()).hexdigest()!=checksum[str(path)]:
        raise RuntimeError("Audio DSP changed unexpectedly: "+str(path))
print("v0.5.21: satin brushed-metal micrograin without visible horizontal stripes, preserved DSP")
