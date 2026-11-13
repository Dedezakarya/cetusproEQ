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
icons = r"""        // Exact silhouette contours traced from the two supplied 48x48 PNG icons.
        // Pure vector paint: no image decode or asset initialization when GUI opens.
        const juce::Point<float> undoPoints[] = {
            {2.f,4.f}, {2.f,16.f}, {14.f,16.f}, {12.f,14.f}, {14.f,11.f}, {18.f,9.f},
            {26.f,9.f}, {30.f,11.f}, {36.f,18.f}, {37.f,22.f}, {36.f,29.f}, {30.f,36.f},
            {22.f,39.f}, {22.f,47.f}, {26.f,47.f}, {32.f,45.f}, {40.f,39.f}, {45.f,29.f},
            {45.f,18.f}, {42.f,11.f}, {38.f,6.f}, {34.f,3.f}, {26.f,0.f}, {14.f,1.f},
            {5.f,7.f}
        };
        const juce::Point<float> redoPoints[] = {
            {45.f,4.f}, {42.f,7.f}, {33.f,1.f}, {21.f,0.f}, {10.f,5.f}, {5.f,11.f},
            {2.f,18.f}, {2.f,29.f}, {7.f,39.f}, {17.f,46.f}, {25.f,47.f}, {25.f,39.f},
            {17.f,36.f}, {11.f,29.f}, {10.f,25.f}, {11.f,18.f}, {17.f,11.f}, {21.f,9.f},
            {32.f,10.f}, {35.f,13.f}, {33.f,16.f}, {45.f,16.f}
        };
        const bool redoIcon = (id == "cetus-redo");
        const auto* points = redoIcon ? redoPoints : undoPoints;
        const int count = redoIcon ? (int) std::size(redoPoints) : (int) std::size(undoPoints);
        juce::Path iconPath;
        iconPath.startNewSubPath(points[0]);
        for (int i = 1; i < count; ++i) iconPath.lineTo(points[i]);
        iconPath.closeSubPath();
        g.setColour(juce::Colours::white.withAlpha(.97f));
        g.fillPath(iconPath, juce::AffineTransform::scale(21.0f / 48.0f)
                   .translated(cx - 10.5f, cy - 10.5f));
        g.restoreState();"""
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

# Bump UI footer and metadata only.
source = source.replace('cetusproEQ  /  v0.5.12"', 'cetusproEQ  /  v0.5.12.2"')
source = source.replace('cetusproEQ  /  v0.5.12.1"', 'cetusproEQ  /  v0.5.12.2"')
assert source.count('v0.5.12.2') >= 2
p.write_text(source, encoding="utf-8")

cm = Path("CMakeLists.txt")
c = cm.read_text(encoding="utf-8")
assert c.count("VERSION 0.5.12.1") == 1
cm.write_text(c.replace("VERSION 0.5.12.1", "VERSION 0.5.12.2", 1), encoding="utf-8")

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
