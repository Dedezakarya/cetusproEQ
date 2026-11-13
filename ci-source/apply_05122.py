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
icons = r"""        // Original Undo and Redo PNGs resampled with Lanczos to their 21x21
        // display size. Draw the exact alpha silhouettes as tiny rectangles.
        // No image decoder, image memory writes, or dynamically built Paths.
        static constexpr const char undoAlpha[] = "00000300001b6eb5dff2edd09c4f02000300000000251900097ce1ffffffffffffffffc54b00010100005cc03cbffffffdfafcfdfdfbfbffffff80000201004dfffefffcfcfffffffffffffffcfcfdff860002014efefffdfeffffad654b4f7cd0fffffdfbff5c00034cfbfbfafbcc3900000000000b7cfcfefcfee4180152ffffffffd41b0204030303000070fffefcff7300309f9f9f9da9680101000000010300b4fffafec50300000000000000000000000000030148fffcffed230103030302020100000000000002001ceffffffa440000000000000000000000000001000fe0fffeff4e0000000000000000000000000002001aeefffffa4300000000000000000000000000030147fffcffed23000000000000000000000000010300b4fffafec502000000000000000000010303000072fffefcff72000000000000000000000000000c7dfdfefcfee217010000000000000001000f4f7ed1fffffdfbff5b000300000000000000020039fffffffcfcfdff8700020100000000000000020038fbfafaffffff7f0002010000000000000000020038ffffffffc34a000101000000000000000000020036eccf9b4f02000300000000";
        static constexpr const char redoAlpha[] = "0000000002000452a0d5f1f3e3b9721d000003000000000101004dc7ffffffffffffffffe37e0a001a260001020081fffffefbfbfdfdfcfafdffffc23ec15b01020087fffdfcfcfffffffffffffffcfcffffff4d03005cfffbfdffffd07b4e4964acfefffefdfffe4e0117e4fefcfefd7c0b000000000038ccfbfafbfb4c0072fffcfdff71000003030304021bd3ffffffff5202c4fefaffb5000301000000010168a99d9f9f9f3022ecfffcff4901030000000000000000000000000043faffffee1b0002000000000000010202030303014dfefeffdf0f00010000000000000000000000000043faffffee1b00020000000000000000000000000022ecfffcff4901030000000000000000000000000003c4fefaffb40003010000000000000000000000000072fffcfeff7000000303010000000000000000000117e3fefcfefd7a0a00000000000000000000000003005cfffbfdffffce7c4c0e00010000000000000001020089fffdfcfdffffff3a0002000000000000000001020083fffffef9fbfc3900020000000000000000000101004dc7ffffffff390002000000000000000000000002000353a1d4f037000200000000000000";
        const char* alpha = id == "cetus-redo" ? redoAlpha : undoAlpha;
        const int xx = juce::roundToInt(cx - 10.5f);
        const int yy = juce::roundToInt(cy - 10.5f);
        const auto nibble = [](char c) { return c >= '0' && c <= '9' ? c - '0' : c - 'a' + 10; };
        for (int row = 0; row < 21; ++row) {
            for (int col = 0; col < 21; ++col) {
                const int offset = (row * 21 + col) * 2;
                const auto opacity = (juce::uint8) ((nibble(alpha[offset]) << 4) | nibble(alpha[offset + 1]));
                if (opacity < 16) continue;
                g.setColour(juce::Colours::white.withAlpha(opacity));
                g.fillRect(xx + col, yy + row, 1, 1);
            }
        }
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
