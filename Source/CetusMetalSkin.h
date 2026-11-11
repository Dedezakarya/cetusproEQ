#pragma once
#include <JuceHeader.h>
#include <cmath>

// Purely visual JUCE drawing helpers: no DSP, state, or audio-thread work.
namespace CetusMetal {

inline void brushedSurface(juce::Graphics& g, juce::Rectangle<float> bounds,
                           float radius, float opacity = 1.0f) {
    if (bounds.isEmpty()) return;
    g.saveState();
    juce::Path mask;
    mask.addRoundedRectangle(bounds, radius);
    g.reduceClipRegion(mask);

    // Dark anodised aluminium: gentle directional light and fine horizontal grain.
    juce::ColourGradient wash(juce::Colour::fromRGB(205, 219, 230).withAlpha(0.095f * opacity),
                              bounds.getX(), bounds.getY(),
                              juce::Colour::fromRGB(8, 15, 24).withAlpha(0.26f * opacity),
                              bounds.getRight(), bounds.getBottom(), false);
    wash.addColour(0.33, juce::Colour::fromRGB(74, 95, 111).withAlpha(0.07f * opacity));
    g.setGradientFill(wash);
    g.fillRect(bounds);

    const int start = juce::roundToInt(bounds.getY());
    const int end = juce::roundToInt(bounds.getBottom());
    for (int y = start + 1; y < end; y += 2) {
        const bool bright = ((y - start) % 11) == 1;
        g.setColour((bright ? juce::Colours::white : juce::Colours::black)
            .withAlpha((bright ? 0.040f : 0.052f) * opacity));
        g.drawHorizontalLine(y, bounds.getX() + radius * 0.35f,
                              bounds.getRight() - radius * 0.35f);
    }

    // CNC-milled edge: inner top rim, narrow shadow and lower reflected edge.
    g.setColour(juce::Colours::white.withAlpha(0.17f * opacity));
    g.drawHorizontalLine(start + 2, bounds.getX() + radius, bounds.getRight() - radius);
    g.setColour(juce::Colours::black.withAlpha(0.30f * opacity));
    g.drawHorizontalLine(end - 3, bounds.getX() + radius, bounds.getRight() - radius);
    g.restoreState();
}

inline void buttonBevel(juce::Graphics& g, juce::Rectangle<float> bounds, float opacity = 1.0f) {
    if (bounds.isEmpty()) return;
    g.setColour(juce::Colours::white.withAlpha(0.20f * opacity));
    g.drawLine(bounds.getX() + 5.0f, bounds.getY() + 1.4f,
               bounds.getRight() - 5.0f, bounds.getY() + 1.4f, 1.0f);
    g.setColour(juce::Colours::black.withAlpha(0.48f * opacity));
    g.drawLine(bounds.getX() + 5.0f, bounds.getBottom() - 1.2f,
               bounds.getRight() - 5.0f, bounds.getBottom() - 1.2f, 1.0f);
    // Fine stroke texture is clipped to the actual button rectangle.
    brushedSurface(g, bounds.reduced(1.0f), 5.0f, 0.35f * opacity);
}

inline void machinedKnob(juce::Graphics& g, juce::Point<float> centre, float radius) {
    if (radius <= 0.0f) return;
    const auto x = centre.x, y = centre.y;
    // Knurled metallic outer rim and alternating ridges.
    for (int i = 0; i < 36; ++i) {
        const float a = juce::MathConstants<float>::twoPi * (float)i / 36.0f;
        const float s = std::sin(a), c = std::cos(a);
        const float r1 = radius * 0.93f, r2 = radius * 1.035f;
        g.setColour((i % 2 == 0 ? juce::Colours::white : juce::Colours::black)
                        .withAlpha(i % 2 == 0 ? 0.14f : 0.26f));
        g.drawLine(x + s * r1, y - c * r1,
                   x + s * r2, y - c * r2, 0.75f);
    }

    // Machined silver/graphite face, from cool highlight to dark slate.
    const float faceR = radius * 0.72f;
    juce::ColourGradient face(juce::Colour::fromRGB(151, 169, 181),
                              x - faceR * 0.7f, y - faceR * 0.9f,
                              juce::Colour::fromRGB(24, 34, 46),
                              x + faceR * 0.8f, y + faceR * 0.95f, false);
    face.addColour(0.31, juce::Colour::fromRGB(106, 125, 139));
    face.addColour(0.58, juce::Colour::fromRGB(58, 74, 87));
    g.setGradientFill(face);
    g.fillEllipse(x - faceR, y - faceR, faceR * 2.0f, faceR * 2.0f);
    g.setColour(juce::Colours::white.withAlpha(0.28f));
    g.drawEllipse(x - faceR + 1.0f, y - faceR + 1.0f,
                  faceR * 2.0f - 2.0f, faceR * 2.0f - 2.0f, 0.9f);
    g.setColour(juce::Colours::black.withAlpha(0.43f));
    g.drawEllipse(x - faceR - 1.0f, y - faceR - 1.0f,
                  faceR * 2.0f + 2.0f, faceR * 2.0f + 2.0f, 1.0f);

    // Tiny concentric brushing and overhead light reflection.
    for (int i = 0; i < 5; ++i) {
        const float rr = faceR * (0.35f + 0.11f * (float)i);
        g.setColour(juce::Colours::white.withAlpha(i % 2 == 0 ? 0.046f : 0.021f));
        g.drawEllipse(x - rr, y - rr, rr * 2.0f, rr * 2.0f, 0.5f);
    }
    juce::ColourGradient gloss(juce::Colours::white.withAlpha(0.31f),
                               x - faceR * 0.55f, y - faceR * 0.75f,
                               juce::Colours::white.withAlpha(0.0f),
                               x + faceR * 0.6f, y + faceR * 0.3f, true);
    g.setGradientFill(gloss);
    g.fillEllipse(x - faceR * 0.58f, y - faceR * 0.72f,
                  faceR * 1.08f, faceR * 0.70f);
}

} // namespace CetusMetal
