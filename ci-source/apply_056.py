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
    # Normalise three known v0.5.5 CI differences; the result must match
    # the exact original source hash before any GUI patch can be applied.
    if name.endswith("CetusMetalSkin.h"):
        original = original.replace(b"\r\n", b"\n")
    elif name.endswith("PluginEditor.cpp"):
        original = original.replace(
            b"// Vertical light, fine brushed steel; no diagonal highlights or stripes.",
            b"// Evenly lit brushed steel; no diagonal specular reflections or stripe overlays."
        )
        original = original.replace(
            b"if(type!=currentFilterType){setKnobType();if(hudPinned)bindFloatingControls(selectedBand);}",
            b"if(type!=currentFilterType){\n        setKnobType();\n        if(hudPinned)bindFloatingControls(selectedBand);\n    }"
        )
        original = original.replace(b"  \xb7  ", b"  \xc2\xb7  ")
    digest = hashlib.sha256(original).hexdigest()
    if digest != item["before"]:
        raise SystemExit(f"Unexpected v0.5.5 GUI source {name}: {digest}, expected {item['before']}")
    lines = original.splitlines(keepends=True)
    for start, end, replacement in reversed(item["ops"]):
        lines[start:end] = base64.b64decode(replacement).splitlines(keepends=True)
    updated = b"".join(lines)
    if hashlib.sha256(updated).hexdigest() != item["after"]:
        raise SystemExit(f"Output source checksum mismatch: {name}")
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
