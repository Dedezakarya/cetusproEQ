from pathlib import Path
import base64
import hashlib
import lzma

parts = [Path("ci-source") / f"v053-part-{i}.txt" for i in range(1, 9)]
encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
if len(encoded) != 7480:
    raise RuntimeError(f"Unexpected v0.5.3 encoded patch length: {len(encoded)}")
source = lzma.decompress(base64.b64decode(encoded, validate=True))
expected = "7c30564ca7899ed2335696d94ac8f943dc9570d384fbd6fa5b3bf4a17420d4a1"
actual = hashlib.sha256(source).hexdigest()
if actual != expected:
    raise RuntimeError(f"v0.5.3 patch checksum mismatch: {actual}")
exec(compile(source, "ci-source/patch_053.py", "exec"), {"__name__": "__main__"})
print("v0.5.3 glass GUI patch applied successfully")
