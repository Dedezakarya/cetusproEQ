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
