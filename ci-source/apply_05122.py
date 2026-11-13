#!/usr/bin/env python3
"""cetusproEQ v0.5.12.2 GUI-only: undo/redo, brand contrast, band order, value spacing."""
from pathlib import Path
import hashlib

p = Path("Source/PluginEditor.cpp")
source = p.read_text(encoding="utf-8")

def swap_once(old, new):
    global source
    n = source.count(old)
    if n != 1:
        raise RuntimeError(f"Expected exactly one GUI anchor: {old[:80]!r}; found {n}")
    source = source.replace(old, new, 1)

# 1: Arrow heads point in the actual undo/redo direction, without mirrored transforms.
begin = "        // Compact curled arrow icons, mirrored for Redo (reference-style)."
finish = "        g.restoreState();"
assert source.count(begin) == 1
a = source.index(begin)
b = source.index(finish, a) + len(finish)
icons = r"""        // Small curved arrows; correctly oriented arrowheads.
        const bool redo = id == "cetus-redo";
        juce::Path body, arrow;
        if (!redo) {
            body.startNewSubPath(cx + 5.5f, cy - 5.2f);
            body.cubicTo(cx + 0.5f, cy - 8.8f, cx - 5.8f, cy - 6.0f, cx - 6.1f, cy - 0.6f);
            body.cubicTo(cx - 6.2f, cy + 4.5f, cx - 1.2f, cy + 7.4f, cx + 3.2f, cy + 5.7f);
            arrow.startNewSubPath(cx - 1.8f, cy - 6.0f);
            arrow.lineTo(cx - 7.0f, cy - 1.0f);
            arrow.lineTo(cx - 1.5f, cy + 3.6f);
        } else {
            body.startNewSubPath(cx - 5.5f, cy - 5.2f);
            body.cubicTo(cx - 0.5f, cy - 8.8f, cx + 5.8f, cy - 6.0f, cx + 6.1f, cy - 0.6f);
            body.cubicTo(cx + 6.2f, cy + 4.5f, cx + 1.2f, cy + 7.4f, cx - 3.2f, cy + 5.7f);
            arrow.startNewSubPath(cx + 1.8f, cy - 6.0f);
            arrow.lineTo(cx + 7.0f, cy - 1.0f);
            arrow.lineTo(cx + 1.5f, cy + 3.6f);
        }
        const auto stroke = juce::PathStrokeType(1.85f,
            juce::PathStrokeType::curved, juce::PathStrokeType::rounded);
        g.strokePath(body, stroke);
        g.strokePath(arrow, stroke);"""
source = source[:a] + icons + source[b:]

# 2: Use the embedded reference wordmark. Restore brighter logo and consistent title alignment.
header_start = "void CetusproEQAudioProcessorEditor::drawHeader(juce::Graphics& g) {"
header_end = "\nvoid CetusproEQAudioProcessorEditor::drawSpectrumAndCurve"
assert source.count(header_start) == source.count(header_end) == 1
a = source.index(header_start)
b = source.index(header_end, a)
header = r"""void CetusproEQAudioProcessorEditor::drawHeader(juce::Graphics& g) {
    const auto h = headerRect().toFloat();
    drawGlass(g, h, 10.0f, top, 0.84f);

    // Do not mutate PNG pixel data while opening the plugin editor. On Windows,
    // the previous per-pixel GUI-only brightness lift caused an editor crash.
    // Multiple composited passes lift the existing low-alpha reference artwork
    // without changing its silhouette, using only JUCE's normal image renderer.
    const auto& logo = CetusBrandAssets::mark();
    if (logo.isValid()) {
        for (int n = 0; n < 6; ++n)
            g.drawImageWithin(logo, 18, 12, 46, 46, juce::RectanglePlacement::centred);
    }
    const auto& brand = CetusBrandAssets::wordmark();
    if (brand.isValid()) {
        for (int n = 0; n < 7; ++n)
            g.drawImageWithin(brand, 69, 16, 150, 40, juce::RectanglePlacement::centred);
    }

    g.setColour(juce::Colour::fromRGB(119, 151, 171).withAlpha(.58f));
    g.fillRect(225, 21, 1, 29);
    g.setColour(white.withAlpha(.80f));
    g.setFont(juce::FontOptions(8.4f));
    g.drawText("v0.5.12.2", 995, 29, 65, 16, juce::Justification::centredRight);
}
"""
source = source[:a] + header + source[b:]

# 3: Left column = 1,2,3,4; right column = 5,6,7,8.
swap_once(
    """    for(int i=0;i<CetusproEQAudioProcessor::numBands;++i)
        placeDesignChild(bandButtons[(size_t)i],{listX+(i%2)*49,listY+(i/2)*27,44,23});""",
    """    for (int i = 0; i < CetusproEQAudioProcessor::numBands; ++i) {
        const int column = i / 4;
        const int row = i % 4;
        placeDesignChild(bandButtons[(size_t)i],
            {listX + column * 49, listY + row * 27, 44, 23});
    }""")

# 4: Move readout away from divider and retain label spacing.
swap_once("placeDesignChild(k.slider,{x+12,429,78,104});",
          "placeDesignChild(k.slider,{x+12,423,78,104});")
swap_once("placeDesignChild(k.label,{x+2,497,98,14});",
          "placeDesignChild(k.label,{x+2,492,98,14});")

# Preserve the proven-safe text-button drawing path. Display the exact supplied
# PNG icons as non-interactive overlays so clicks continue reaching the original
# Undo/Redo buttons. Never decode or rasterize inside LookAndFeel paint callbacks.
swap_once(
    '    const juce::String id=button.getComponentID();\n'
    '    if(id.isEmpty() || !id.startsWith("cetus-")) {',
    '    const juce::String id=button.getComponentID();\n'
    '    if(id=="cetus-undo" || id=="cetus-redo") return;\n'
    '    if(id.isEmpty() || !id.startsWith("cetus-")) {'
)
swap_once(
    '    undoButton.setTooltip("Undo last parameter edit");\n'
    '    redoButton.setTooltip("Redo parameter edit");',
    '''    undoButton.setTooltip("Undo last parameter edit");
    redoButton.setTooltip("Redo parameter edit");
    undoIconImage.setImage(juce::ImageFileFormat::loadFrom(
        BinaryData::CetusUndo_png, (size_t) BinaryData::CetusUndo_pngSize));
    redoIconImage.setImage(juce::ImageFileFormat::loadFrom(
        BinaryData::CetusRedo_png, (size_t) BinaryData::CetusRedo_pngSize));
    undoIconImage.setInterceptsMouseClicks(false, false);
    redoIconImage.setInterceptsMouseClicks(false, false);
    addAndMakeVisible(undoIconImage);
    addAndMakeVisible(redoIconImage);'''
)
swap_once(
    '    placeDesignChild(redoButton,        {673, 22, 30,  28});',
    '''    placeDesignChild(redoButton,        {673, 22, 30,  28});
    // Pixel-exact source PNGs, uniformly scaled to fit within the controls.
    placeDesignChild(undoIconImage, {642, 26, 20, 20});
    placeDesignChild(redoIconImage, {678, 26, 20, 20});
    undoIconImage.toFront(false);
    redoIconImage.toFront(false);'''
)
assert '#include <BinaryData.h>' not in source
source = '#include <BinaryData.h>\n' + source
headerPath = Path("Source/PluginEditor.h")
guiHeader = headerPath.read_text(encoding="utf-8")
decl = '    juce::TextButton undoButton {"Undo"}, redoButton {"Redo"};'
assert guiHeader.count(decl) == 1
guiHeader = guiHeader.replace(decl, decl +
    '\n    juce::ImageComponent undoIconImage {"Undo PNG"}, redoIconImage {"Redo PNG"};', 1)
headerPath.write_text(guiHeader, encoding="utf-8")

# Bump UI footer and metadata only.
source = source.replace('cetusproEQ  /  v0.5.12"', 'cetusproEQ  /  v0.5.12.2"')
source = source.replace('cetusproEQ  /  v0.5.12.1"', 'cetusproEQ  /  v0.5.12.2"')
assert source.count('v0.5.12.2') >= 2
p.write_text(source, encoding="utf-8")

cm = Path("CMakeLists.txt")
c = cm.read_text(encoding="utf-8")
assert c.count("VERSION 0.5.12.1") == 1
cm.write_text(c.replace("VERSION 0.5.12.1", "VERSION 0.5.12.2", 1) + """
# Embed the original 48x48 RGBA PNGs as JUCE image assets, without
# modifying DSP or loading external files at runtime.
juce_add_binary_data(cetusproEQIconAssets SOURCES
    assets/CetusUndo.png
    assets/CetusRedo.png)
target_link_libraries(cetusproEQ PRIVATE cetusproEQIconAssets)
""", encoding="utf-8")
for asset, checksum in {
    "assets/CetusUndo.png": "51792fc1be38c4d42a9b372f23f82845bfb76e53692825c5ccff3dbf4a8e0dfa",
    "assets/CetusRedo.png": "1243bd7f8d069e3c3b359413c828f01ec0e1d2dd717d5277add6682b8c261b30"
}.items():
    if hashlib.sha256(Path(asset).read_bytes()).hexdigest() != checksum:
        raise RuntimeError("Uploaded GUI PNG is not byte-identical to supplied image: " + asset)

dsp = {
"Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
"Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
"Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
"Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}
for path, checksum in dsp.items():
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual != checksum:
        raise RuntimeError("DSP file unexpectedly changed: " + path)

assert "RectanglePlacement::centredLeft" not in source
print("v0.5.12.2 editor-only patch verified; DSP checksums match v0.5.12.1")
