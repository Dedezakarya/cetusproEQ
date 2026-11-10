# cetusproEQ v0.2 — Cetus Production

> **Build otomatis Windows/macOS:** baca [`docs/NATIVE-BUILD.md`](docs/NATIVE-BUILD.md). Workflow GitHub Actions ada di `.github/workflows/build-plugins.yml`. Arsip source ini **bukan** binary `.vst3`/`.component`.

Cross-platform 6-band dynamic peak EQ with **Cetus Link** in-process detector sidechain, optional DAW sidechain bus, AU (macOS), VST3 (macOS/Windows) and Standalone.

## Build requirements
- JUCE 8 (project fetch defaults to tag 8.0.10; alternatively pass `-DJUCE_PATH=/path/to/JUCE`)
- CMake 3.22+, C++17 compiler
- macOS: Xcode and command-line tools; Windows: Visual Studio 2022 with Desktop C++ workload
- Internet to fetch JUCE, unless `JUCE_PATH` provided

### Windows PowerShell
```powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release --target cetusproEQ_VST3 cetusproEQ_Standalone
```
Build artifacts: `build/cetusproEQ_artefacts/Release/VST3/` and `.../Standalone/`.

### macOS
```bash
cmake -S . -B build -G Xcode -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64"
cmake --build build --config Release --target cetusproEQ_VST3 cetusproEQ_AU cetusproEQ_Standalone
```
If you only have an Intel Mac, use `-DCMAKE_OSX_ARCHITECTURES=x86_64`. Artifacts: `build/cetusproEQ_artefacts/Release/`.

### Install (manual)
- Windows VST3: copy `cetusproEQ.vst3` folder to `C:\Program Files\Common Files\VST3\`
- macOS VST3: copy to `~/Library/Audio/Plug-Ins/VST3/`
- macOS AU: copy `cetusproEQ.component` to `~/Library/Audio/Plug-Ins/Components/`
- Restart DAW or rescan plugins. Unsigned macOS bundles may require local development signing and Gatekeeper handling.

## Using Cetus Link across tracks
1. Track A: insert cetusproEQ; set SEND = Link 1. The source detector is the **incoming** audio peak before processing.
2. Track B: insert cetusproEQ; set DETECTOR SOURCE = Link 1.
3. In Track B choose a band, enable DYNAMIC and set threshold, range **negative** to attenuate when A rises, attack/release.
4. Set other bands or use different links (1–4). One transmitter per link. **Cross-instance operation works only when both plugin instances reside in the same DAW process/plugin binary module.** It will not work across sandboxed AU processes or separated plugin bridge processes.
5. Processing order is host-controlled; detector communication is block-oriented and can incur a block of offset. This is not guaranteed sample-accurate, and DAW delay compensation does not account for the link.

## DAW sidechain alternative
Set DETECTOR SOURCE = DAW sidechain, enable the second input bus in the host, and route audio to it. Host support varies. This can work where in-process Cetus Link cannot. This plugin does not intentionally pass sidechain audio into output.

## Controls and DSP
Each of 6 **bell/peaking** bands has: frequency, static gain, Q, threshold, signed dynamic range, attack, release, enable and dynamic switch. All bands share one detector source (Self / Link 1–4 / DAW sidechain). Signed range: negative = downward dynamic cut, positive = dynamic boost *above* threshold. State saved/restored with host project. Bypass and output gain included.

DSP is a prototype: block-level peak detection and coefficient update, not sample-accurate automation or production-grade artifact suppression. The GUI now includes a real FFT analyzer (pre/post) and approximate static EQ curve. No external sidechain audio streaming, no cross-process link, no AAX, no HPF/shelf/notch, no linear phase, no oversampling, no factory preset browser yet.

## Known limitations and test checklist
- Link bus stores the latest peak only. If no sender posts before a receiver callback, the receiver reads 0 for that callback; host processing order influences behavior. No multiple concurrent senders per bus.
- Verify builds, plugin scan, mono/stereo, sample rates (44.1/48/96 kHz), silent input, high Q, rapid parameter automation, project save/reopen, standalone.
- Ensure host sidechain bus is enabled when using DAW mode.
- JUCE licensing and third-party dependencies must be reviewed before commercial release: https://juce.com/legal/juce-8-licence/
- For shipping: parameter smoothing per sample, gain/lookahead options, frequency-selective detectors, analyzer, stress tests, and validation/codesigning are recommended.

Copyright © 2026 Cetus Production. Source supplied for project development; see JUCE licensing for the framework.

## v0.2 review notes
- New inserts default to dynamic OFF and dynamic range 0 dB to avoid unexpected colouring.
- When output gain is zero and all bands are flat/inactive, filter processing is skipped to preserve input samples.
- Existing Logic projects can restore v0.1 settings: click **INIT FLAT** when testing.
- FFT analyzer is live with PRE/POST toggle; the EQ response line remains an approximation, not the exact biquad transfer function.
- Validate plugin builds in GitHub Actions and perform a sample-aligned null test before production use.
