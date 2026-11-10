"""Restore the independently verified cetusproEQ v0.5.1 source bundle.
The four base64 parts are a transfer container, not compiled binaries.
"""
from pathlib import Path
import base64, hashlib, io, lzma, tarfile

chunks = [Path(f"ci-source/part{i}.b64").read_text().strip() for i in range(1, 5)]
compressed = base64.b64decode("".join(chunks), validate=True)
expected = "9149b034a905df3228adb2f5e4d3af1d2c0108e0d31bef419f0964a7d45a3a1c"
actual = hashlib.sha256(compressed).hexdigest()
if actual != expected:
    raise SystemExit(f"Source checksum mismatch: expected {expected}, got {actual}")
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(compressed)), mode="r:") as archive:
    for member in archive.getmembers():
        path = Path(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"Unsafe source path: {member.name}")
    archive.extractall(path=Path("."), filter="data")
cmake = Path("CMakeLists.txt").read_text(encoding="utf-8")
if "VERSION 0.5.1" not in cmake:
    raise SystemExit("Unexpected project version after unpacking")
print("Verified and restored cetusproEQ v0.5.1 source:", actual)

# Portability fixes discovered by the first native Windows/macOS compile.
# Apply only after verifying the exact archived source checksum above.
editor_path = Path("Source/PluginEditor.cpp")
editor = editor_path.read_text(encoding="utf-8")
before = """    for(auto* b:{&initButton,&applyPresetButton,&savePresetButton,&openPresetButton,&undoButton,&redoButton,
                 &analyzerButton,&prePostButton,&hudCloseButton,&holdButton,&smoothButton,&bandOn,&dynamicOn,&bypass})
        b->removeListener(this);"""
after = """    for(auto* b:{&initButton,&applyPresetButton,&savePresetButton,&openPresetButton,&undoButton,&redoButton,
                 &analyzerButton,&prePostButton,&hudCloseButton,&holdButton,&smoothButton})
        b->removeListener(this);
    for(auto* b:{&bandOn,&dynamicOn,&bypass})
        b->removeListener(this);"""
if editor.count(before) != 1:
    raise SystemExit("Expected mixed button cleanup loop not found exactly once")
editor = editor.replace(before, after)
if editor.count("cyan.withAlpha(0)") != 1:
    raise SystemExit("Expected ambiguous alpha literal not found exactly once")
editor = editor.replace("cyan.withAlpha(0)", "cyan.withAlpha(0.0f)")
editor_hash = hashlib.sha256(editor.encode()).hexdigest()
expected_editor_hash = "92a747f377a67e60ee118b686818c8b6ca550dc4b9506d1a2a35423bbd0191ed"
if editor_hash != expected_editor_hash:
    raise SystemExit(f"Corrected source hash mismatch: {editor_hash}")
editor_path.write_text(editor, encoding="utf-8")
print("Applied verified cross-platform GUI compile fixes:", editor_hash)
