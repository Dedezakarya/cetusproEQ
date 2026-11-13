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
icons = r"""        // Exact 48x48 white transparent PNG silhouettes supplied by the user.
        // Decode once at first paint, not on the audio thread.
        static const auto decodeIcon = [](const char* encoded) {
            juce::MemoryOutputStream pngBytes;
            if (!juce::Base64::convertFromBase64(pngBytes, encoded))
                return juce::Image();
            return juce::ImageFileFormat::loadFrom(pngBytes.getData(), pngBytes.getDataSize());
        };
        static const juce::Image undoIcon = decodeIcon("iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAA7EAAAOxAGVKw4bAAADyUlEQVRogc2aS4gcVRSGvzsMIUgITQhBJIQoLsYhiyBjI7NIoqALyUpcZOELERcGt3HjRkTcJYsQg0QFIyhBxI1RQnwtYiTgYwyCEh8RGSUESchMQtpx0p+LWxV7uqe7b3V1z9S/6a6qU3XOf++59zyqAgNCHQduA24F7gTuAe7Izm0ExoAF4G9gFjgHnAH+AC4CF0IIzUH15wgDGH4LUAd2ADuBbS0G98MikcwPwOfAKWAmhLBQ1I7CUMfUuvqBel79x3K4rv6svq1OqqWMq6v1LtfG1R3qe5nSUWBefU3drqbMZIeRT6pfqlOtI6FuUJ8xjviocUP9Xn3E6KaFCVzOSNRV1E3qoez8SuJPdZ+6bhACqj+qe9SvVtjwVtxQ31I3pBJ43KUjPb8qZnfigLqpl+1jbb850qdvtHga2GsPdxofkqImMWBdAuaIAaxJHJg1QI0YK9Jc4n+sA/YBV9T9IXSGrZzAoBFxkRhhvyAGpp+Av4gkcgI1YAswCdwH3J8dp26Xa4Hngc+AmWUlXLqIU3FNfUHd1muK2/TUjLvcIeNCLYJj6vpuD25fxL1wXT2ubk8cwW46H1K/Uf9N1HtFfdaYg5WagePqVsuEfm6mJlPqiUS9qifVLa3Pyf2wyBrIM9BSyDLRr4HngF8Sb5sGpjrOWsyFNAa7B8vOQov+aWNil4JPW/V2iwP9MAEcIKbVw8C3wBHgaoLsNLA5PwgA6iSwi7hlFcEMcGoY+Xzm2++znIt04okQwtGyOocO9alENzpmlnYXz71Hiw9Jc6OtxMheOQIX6RZtl2I9cTesFoEs1zmdIFpNAhnOJ8isIcuYq0jgUoLMONmOWUUChTLjKhKoJcgsAg2oJoHbE2QWiDVHJQlMJ8jMARegYgSMXYi7E0TniJVftQgAu4l7fD/8RqzBq0MgS+b2Jop/nHe2K0FAXQvsIRb+/dAAPhmtRQWRFTS/JmaiJ4dVSJWGsS6eML15fE19eLXtBm4af6+xREzFCXVz/6evANTd6nemt1UuG1v9w+omDmR0LRv1wxZvbL3rMg20wu/IChgLMWvcSGwlThBbi7so1lqEWOg8EEI4235hJNORTfOjwGPEwJQ3d1MStXY0gFeADuNhRASIo3sXsZFbBleB/cDry3Wmc0VVxpvA4RBC10J/9VZ0bzSBd4AXQwg9K7QqEpgFDgKv9hr5HFUi0CQu1JeAj0IIjZSbqkJgDjgKvAGcLfINxWoSaBDd5TTwcgjh3CAPWWkCQ//YY1QEmsA88DvR4FniS4wz2f+hfW7zH0Zyx0MELhWiAAAAAElFTkSuQmCC");
        static const juce::Image redoIcon = decodeIcon("iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAD+UlEQVRogc2aTWhcVRTHfzcEKSEEKSGUIEGllFJEQgkaS6hx05W4cOGiFLF+g4ob0aILVy61C3EhUhC/oMWNgpRS1KBiFasLP6sQLa1oEE00jTE1dn4u7ptkmGQy9715b5ofDMMMd975n3PPnHvufS9QAmovsC17bQduAnYAVwFXZsP+A+aB34CzwCngDDAD/BxC+LeI7dCh8D5gNzAB3AJcR3SiJ+HnNWCW6MQU8CHwcQhhoRNNSaioo+pRdVq9aGcsq+fVd9QJNSUAhYT3qGPqEfXvDkW34qL6ljppTM31grdHHc8rvk+9Q/1KvVSR+EbOqw+rg03ix9VT6p15xA+oT6q/dkF4I3Pqi+q2JvFzyQ6og+qrdifqrfhc3a9+l32eU+8CWJNjTeKHgKeAA8nTVQ27gZeAvobvarBBuVP7gUeAuyuVlk5f0+ceaDEDKsD9wOPAFQWMzRIXrHlgkbiI9QJbgAFgMHt1XC5bpdAo8AT5xNeIK+wU8C7wLXCO6ESNKLYfGAZ2AjcDk8CuDXS0s7cWY8U5mvNPdkl9Qb1BHUixbizLu9RD6oWc9lb+xM0X7VUfVP9KvNCysULcWiCCjXavNy5e/+RwYG0ZVUfUkzkicdIY9Y5y2Vjjrza2ErkcaM69MWBPot2zwEPADyF01BPWGSI2gsXIopAa/Wl1ogzVmd196jc5Zn5lBhqnfpjYFrdjATgCnC5DPDAOHCZWo9w0ptAksU634wzwRghhqYjBdez3EQOShyUaA2hsk19PnL57SxBeGvUU2gpcmzB+EXi7Ojn5qTswzOredSO+ILYIm4ZGB/oTxn9QUsksjboD/aT1PT9VqKUQdQe2kNZQzVaopRDV7P67SN2BJWLP3o6tFWopRN2BBSDlZOyaCrUUou7AL0Qn2rE3W/43DY0O/JkwfpTYNW4a6g7MAj8mjO8HbqtOTn56AEIINeB44m8eUEeqk5SPxjL6HrEatWMnsF9N6Vy7R4ENTerOrXuot5t+6jyt7thUVcm4qT+R6IDZjI1Z1Xl+Xlw9VplLdGBZ/Uzdd7m1r2Cxg61l9XA2G0kHW2WxbnOvjgInyLdo1YhryRTwPnHvfA6Yzcp09zBWpMcsfu/rD/V79VP1uHrAdW4XVe3EgPqM+c8t1+NZtcgpd1taVo8QwjzwPPBKCXYqS6ENy18IYQZ4GjjWoYjKymzbC4cQfgfuIzoyU5WQoiRFJkun54BHga/JPxuXJ4UaCSEsAm8CB4GXiYdcpdvJS64LhxBqIYTTwD3EBzqOEWt/oQc1yqBQbc4Ot75UDxJvge5l9WGPIdYGprIU6mhxydLqI/UT4DWi+O3Ajdn7CPFu5IUOdbbkfz4UylrKrxF0AAAAAElFTkSuQmCC");
        const auto& icon = id == "cetus-redo" ? redoIcon : undoIcon;
        if (icon.isValid())
            g.drawImageWithin(icon, juce::roundToInt(cx - 10.5f), juce::roundToInt(cy - 10.5f),
                              21, 21, juce::RectanglePlacement::centred);
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

    static const juce::Image brightLogo = [] {
        auto image = CetusBrandAssets::mark().createCopy();
        if (!image.isValid()) return image;
        juce::Image::BitmapData pixels(image, juce::Image::BitmapData::readWrite);
        const auto cyanLift = juce::Colour::fromRGB(91, 251, 246);
        for (int y = 0; y < image.getHeight(); ++y)
            for (int x = 0; x < image.getWidth(); ++x) {
                const auto original = pixels.getPixelColour(x, y);
                if (original.getAlpha() == 0) continue;
                const auto lifted = original.interpolatedWith(cyanLift, .94f);
                pixels.setPixelColour(x, y, lifted.withAlpha((juce::uint8) juce::jmin(255, (int) original.getAlpha() * 2)));
            }
        return image;
    }();
    if (brightLogo.isValid())
        g.drawImageWithin(brightLogo, 18, 12, 46, 46, juce::RectanglePlacement::centred);

    static const juce::Image brightWordmark = [] {
        auto image = CetusBrandAssets::wordmark().createCopy();
        if (!image.isValid()) return image;
        juce::Image::BitmapData pixels(image, juce::Image::BitmapData::readWrite);
        for (int y = 0; y < image.getHeight(); ++y)
            for (int x = 0; x < image.getWidth(); ++x) {
                const auto original = pixels.getPixelColour(x, y);
                if (original.getAlpha() == 0) continue;
                pixels.setPixelColour(x, y,
                    original.interpolatedWith(
                        x > image.getWidth() * .73f ? juce::Colour::fromRGB(73, 246, 239)
                                                     : juce::Colour::fromRGB(246, 252, 255),
                        .94f).withAlpha((juce::uint8) juce::jmin(255, (int) original.getAlpha() * 2)));
            }
        return image;
    }();
    if (brightWordmark.isValid())
        g.drawImageWithin(brightWordmark, 69, 16, 150, 40, juce::RectanglePlacement::centred);

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
