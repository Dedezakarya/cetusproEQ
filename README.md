# cetusproEQ v0.4 — Cetus Production

Experimental 8-band Dynamic EQ, JUCE 8 + C++17, built as AU (macOS) and VST3 (macOS/Windows).

## v0.4 features
- 8 independently adjustable bands
- Bell, Low Shelf, High Shelf, High Pass, Low Pass, Notch selectable per band
- Dynamic gain on Bell / Low Shelf / High Shelf (not on HPF, LPF or Notch)
- Live PRE/POST FFT analyzer, static and active EQ curves from actual biquad response
- Coloured dynamic response overlay, floating selected-band filter selector (HUD)
- Drag node to edit Frequency/Gain, wheel over graph to adjust Q, double-click graph to activate an unused band or retune selected
- Cetus Link Send 1–4, listen to other instance within one DAW process, or DAW external sidechain input
- INIT FLAT transparent default; dynamic is OFF and range is zero on all bands

## Build
Requires CMake >=3.22, JUCE 8 (fetched as 8.0.10) and native C++ build tools.
Windows:
```powershell
cmake -S . -B build-win -G "Visual Studio 17 2022" -A x64
cmake --build build-win --config Release --target cetusproEQ_VST3
```
macOS:
```bash
cmake -S . -B build-mac -G Xcode -DCMAKE_OSX_ARCHITECTURES="x86_64;arm64"
cmake --build build-mac --config Release --target cetusproEQ_AU cetusproEQ_VST3
```

The `.github/workflows/build-plugins.yml` runs native CI builds on GitHub.

## Testing & limitations
- This is prototype audio software, not a FabFilter clone or production-ready replacement.
- Unlike FabFilter Pro-Q, filters are 2nd-order and detector is broadband block-based. No linear-phase mode, per-band detector filters, oversampling or AAX.
- Dynamic graph reflects current smoothed gain, not a sample-accurate waveform history.
- Cetus Link shares detector peak levels only, not audio; it depends on host processing order and same-process plugin instances.
- Windows VST3 and macOS AU/VST3 builds must be tested in a DAW; on macOS builds are ad-hoc signed, not notarized.
- Existing plugin instances can restore old parameters. Use INIT FLAT for a genuinely neutral baseline.
- Review JUCE licensing before commercial distribution.

© 2026 Cetus Production.
