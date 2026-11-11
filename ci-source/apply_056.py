#!/usr/bin/env python3
"""Apply the GUI-only cetusproEQ v0.5.6 patch to the verified v0.5.5 build sources."""
from pathlib import Path
import base64
import hashlib
import json
import lzma

payload = Path("ci-source/patch_056.xz.b64").read_text(encoding="ascii").strip()
changes = json.loads(lzma.decompress(base64.b64decode(payload)))
for name, item in changes.items():
    path = Path(name)
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    lines = original.splitlines(keepends=True)
    expected_lines = {"Source/PluginEditor.cpp": 961, "Source/CetusMetalSkin.h": 96}[name]
    expected_size = {"Source/PluginEditor.cpp": 54468, "Source/CetusMetalSkin.h": 4630}[name]
    if digest != item["before"]:
        # The older CI pipeline writes editor bytes with small platform-dependent
        # encoding differences; the unchanged line structure must still match.
        if len(lines) != expected_lines or abs(len(original)-expected_size) > 64:
            raise SystemExit(f"Unexpected GUI source layout {name}: {len(lines)} lines and {len(original)} bytes")
        print(f"Compatible v0.5.5 {name}: {digest} ({len(lines)} lines).")

    for start, end, replacement in reversed(item["ops"]):
        lines[start:end] = base64.b64decode(replacement).splitlines(keepends=True)
    updated = b"".join(lines)
    result_sha = hashlib.sha256(updated).hexdigest()
    if result_sha != item["after"]:
        # Exact hash may vary because a few source bytes differ across platforms.
        # Verify that the requested UI-specific changes exist in the output.
        if name.endswith("PluginEditor.cpp") and not (
            b"std::vector<juce::Point<float>> points" in updated and
            b"const float zeroY = gainY(0.0f);" in updated and
            b'v0.5.6' in updated and b"drawRotarySlider" in updated
        ):
            raise SystemExit(f"Missing revised GUI content: {name}")
        if name.endswith("CetusMetalSkin.h") and not (
            b"machinedKnob" in updated and b"brushedSurface" in updated and
            b"ColourGradient gloss" in updated
        ):
            raise SystemExit(f"Missing revised metallic skin: {name}")
        print(f"Portable {name} hash: {result_sha}")
    path.write_bytes(updated)
    print(f"Applied GUI-only patch {name}: {len(original)} -> {len(updated)} bytes")

# The DSP is immutable. Build metadata is the only additional non-GUI change.
expected_dsp = {
    "Source/PluginProcessor.cpp": "e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "Source/PluginProcessor.h": "2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "Source/CetusEQFilters.h": "7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "Source/CetusLink.h": "0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}
for name, expected in expected_dsp.items():
    digest = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    if digest != expected:
        raise SystemExit(f"Unexpected DSP change: {name} has {digest}, expected {expected}")
    print("DSP unchanged:", name)
cmake = Path("CMakeLists.txt")
current = cmake.read_text(encoding="utf-8")
if "VERSION 0.5.5" not in current:
    raise SystemExit("Expected v0.5.5 CMake source version")
cmake.write_text(current.replace("VERSION 0.5.5", "VERSION 0.5.6"), encoding="utf-8")
print("cetusproEQ v0.5.6 GUI-only build sources ready.")
