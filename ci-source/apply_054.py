#!/usr/bin/env python3
"""Apply visual-only brushed-metal finish after the verified v0.5.3 source restore."""
from pathlib import Path

editor = Path("Source/PluginEditor.cpp")
data = editor.read_text(encoding="utf-8")

def one(old, new):
    global data
    count = data.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match ({count}) for: {old[:100]}")
    data = data.replace(old, new, 1)

one('#include "PluginEditor.h"\n',
    '#include "PluginEditor.h"\n#include "CetusMetalSkin.h"\n')
one('    g.setGradientFill(glass);g.fillRoundedRectangle(area,radius);',
    '    g.setGradientFill(glass);g.fillRoundedRectangle(area,radius);\n'
    '    CetusMetal::brushedSurface(g,area,radius,0.70f * opacity);')
one('    g.drawHorizontalLine(juce::roundToInt(r.getY()+1.3f),r.getX()+5.0f,r.getRight()-5.0f);',
    '    g.drawHorizontalLine(juce::roundToInt(r.getY()+1.3f),r.getX()+5.0f,r.getRight()-5.0f);\n'
    '    CetusMetal::buttonBevel(g,r,0.82f);')
one('    g.fillEllipse(c.x-faceRadius,c.y-faceRadius,faceRadius*2.0f,faceRadius*2.0f);',
    '    g.fillEllipse(c.x-faceRadius,c.y-faceRadius,faceRadius*2.0f,faceRadius*2.0f);\n'
    '    CetusMetal::machinedKnob(g,c,radius);')
one('    g.setGradientFill(chrome);g.fillRoundedRectangle(h,10.0f);',
    '    g.setGradientFill(chrome);g.fillRoundedRectangle(h,10.0f);\n'
    '    CetusMetal::brushedSurface(g,h,10.0f,0.65f);')
if "v0.5.3" not in data:
    raise RuntimeError("Missing original GUI version")
editor.write_text(data.replace("v0.5.3", "v0.5.4"), encoding="utf-8")

cmake = Path("CMakeLists.txt")
cm = cmake.read_text(encoding="utf-8")
if "VERSION 0.5.3" not in cm:
    raise RuntimeError("Expected v0.5.3 project before patch")
cmake.write_text(cm.replace("VERSION 0.5.3", "VERSION 0.5.4"), encoding="utf-8")

assert Path("Source/CetusMetalSkin.h").is_file()
print("v0.5.4 brushed-metal GUI patch applied; DSP unchanged.")
