#!/usr/bin/env python3
"""Reproduce exact v0.5.10.1 GUI/font source from v0.5.9 on both CI runners.

This step changes only PluginEditor.cpp, PluginEditor.h and CMakeLists.txt.
The Processor, filters and sidechain sources are immutable and verified.
"""
from pathlib import Path
import json,base64,lzma,hashlib
PATCH="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"
def digest(data): return hashlib.sha256(data.encode("utf-8")).hexdigest()
patches=json.loads(lzma.decompress(base64.b64decode(PATCH)))
for filename, spec in patches.items():
    path=Path(filename)
    before=path.read_text(encoding="utf-8")
    if digest(before)!=spec["old_sha"]:
        raise SystemExit("Unexpected base source for "+filename+": "+digest(before))
    after=before
    for begin,end,value in reversed(spec["ops"]):
        after=after[:begin]+value+after[end:]
    if digest(after)!=spec["new_sha"]:
        raise SystemExit("Patch output checksum failure: "+filename)
    path.write_text(after,encoding="utf-8")
    print("Applied v0.5.10.1 GUI:", filename, spec["new_sha"])
for filename,expected in {
    "Source/PluginProcessor.cpp":"e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4",
    "Source/PluginProcessor.h":"2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695",
    "Source/CetusEQFilters.h":"7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329",
    "Source/CetusLink.h":"0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc",
}.items():
    result=hashlib.sha256(Path(filename).read_bytes()).hexdigest()
    if result!=expected: raise SystemExit("DSP checksum mismatch: "+filename)
print("v0.5.10.1 GUI applied; DSP files verified unchanged")
