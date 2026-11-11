#!/usr/bin/env python3
"""v0.5.12.1: UI-only fix for brand alignment and Dynamic switch availability."""
from pathlib import Path
import hashlib
import re

p = Path("Source/PluginEditor.cpp")
code = p.read_text(encoding="utf-8")
old = "    const bool dynamicOnBand = processor.isBandDynamicEnabled(selectedBand);"
new = """    // Dynamic GUI availability is driven by the switch, not the effective DSP
    // state: the DSP additionally requires a non-zero Range. Otherwise the
    // Range knob gets stuck disabled at 0 dB even when Dynamic is switched ON.
    const auto* dynamicSwitchValue = processor.parameters.getRawParameterValue(
        CetusproEQAudioProcessor::param(selectedBand, "dyn"));
    const bool dynamicOnBand = dynamicSwitchValue != nullptr && dynamicSwitchValue->load() >= 0.5f;"""
if code.count(old) != 1:
    raise SystemExit("Unexpected dynamic state GUI source; refusing unsafe patch")
code = code.replace(old, new, 1)

old_loop = """    for(auto& knob : knobs)
        knob.slider.setColour(juce::Slider::rotarySliderFillColourId,bands[(size_t)selectedBand]);"""
new_loop = """    for (auto& knob : knobs)
        knob.slider.setColour(juce::Slider::rotarySliderFillColourId,
            knob.slider.isEnabled() ? bands[(size_t)selectedBand] : juce::Colour::fromRGB(79,93,104));"""
if old_loop in code:
    code = code.replace(old_loop, new_loop, 1)

start_signature = "void CetusproEQAudioProcessorEditor::drawHeader(juce::Graphics& g) {"
end_signature = "\nvoid CetusproEQAudioProcessorEditor::drawSpectrumAndCurve"
assert code.count(start_signature)==1 and code.count(end_signature)==1
start = code.index(start_signature)
end = code.index(end_signature, start)
header = r"""void CetusproEQAudioProcessorEditor::drawHeader(juce::Graphics& g) {
    const auto h = headerRect().toFloat();
    drawGlass(g, h, 10.0f, top, 0.84f);
    // Retain the supplied C mark; increase contrast without changing shape.
    static const juce::Image legibleMark = [] {
        auto image = CetusBrandAssets::mark().createCopy();
        if (! image.isValid()) return image;
        juce::Image::BitmapData pixels(image, juce::Image::BitmapData::readWrite);
        const auto cyanLogo = juce::Colour::fromRGB(47, 225, 226);
        for (int y = 0; y < image.getHeight(); ++y)
            for (int x = 0; x < image.getWidth(); ++x) {
                const auto original = pixels.getPixelColour(x, y);
                if (original.getAlpha() == 0) continue;
                const auto lifted = original.interpolatedWith(cyanLogo, 0.63f);
                pixels.setPixelColour(x, y, lifted.withAlpha(original.getAlpha()));
            }
        return image;
    }();
    if (legibleMark.isValid())
        g.drawImageWithin(legibleMark, 18, 18, 42, 38, juce::RectanglePlacement::centred);

    // The two text spans share the same baseline; subtitle centres below both.
    const juce::Font titleFont(juce::FontOptions(21.4f, juce::Font::bold | juce::Font::italic));
    const juce::String mainName = "cetuspro", suffix = "EQ";
    const float mainWidth = titleFont.getStringWidthFloat(mainName);
    const float suffixWidth = titleFont.getStringWidthFloat(suffix);
    const float nameWidth = mainWidth + suffixWidth + 1.5f;
    const float titleX = 64.0f + juce::jmax(0.0f, (154.0f - nameWidth) * 0.5f);
    const float titleY = 21.0f;
    g.setFont(titleFont);
    g.setColour(white.withAlpha(.98f));
    g.drawText(mainName, juce::Rectangle<float>(titleX, titleY, mainWidth + 3.0f, 25.0f),
               juce::Justification::centredLeft, false);
    g.setColour(cyan.brighter(.13f));
    g.drawText(suffix, juce::Rectangle<float>(titleX + mainWidth + 1.5f, titleY, suffixWidth + 2.0f, 25.0f),
               juce::Justification::centredLeft, false);
    g.setColour(juce::Colour::fromRGB(192, 214, 225));
    g.setFont(juce::FontOptions(9.3f));
    g.drawText("Dynamic EQ", juce::Rectangle<float>(titleX, 46.0f, nameWidth, 12.0f),
               juce::Justification::centred, false);

    g.setColour(juce::Colour::fromRGB(119, 151, 171).withAlpha(.56f));
    g.fillRect(225, 21, 1, 29);
    g.setColour(white.withAlpha(.80f));
    g.setFont(juce::FontOptions(8.4f));
    g.drawText("v0.5.12.1", 995, 29, 65, 16, juce::Justification::centredRight);
}
"""
code = code[:start] + header + code[end:]
code = code.replace("CETUS PRODUCTION  /  cetusproEQ v0.5.12",
                    "CETUS PRODUCTION  /  cetusproEQ v0.5.12.1")
assert code.count("void CetusproEQAudioProcessorEditor::drawHeader(")==1
p.write_text(code,encoding="utf-8")

cm = Path("CMakeLists.txt")
old_cmake = cm.read_text()
assert old_cmake.count("VERSION 0.5.12")==1
cm.write_text(old_cmake.replace("VERSION 0.5.12","VERSION 0.5.12.1",1))

immutables = {
    "Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}
for name, expected in immutables.items():
    actual = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit("DSP source differs from expected: "+name)
print("v0.5.12.1 GUI patch applied; dynamic availability fixed, DSP source unchanged.")
