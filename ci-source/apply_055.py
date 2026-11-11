#!/usr/bin/env python3
"""Apply v0.5.5 subtle metal UI patch to verified v0.5.4 sources; no DSP modifications."""
from pathlib import Path
import base64,hashlib,json,lzma

PATCH = "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"
changes=json.loads(lzma.decompress(base64.b64decode(PATCH)))
for filename, meta in changes.items():
    path=Path(filename)
    old=path.read_text(encoding="utf-8")
    digest=hashlib.sha256(old.encode("utf-8")).hexdigest()
    if digest!=meta["before"]:
        raise SystemExit("Unexpected v0.5.4 input in "+filename+": "+digest)
    updated=old
    for start,end,value in reversed(meta["ops"]):
        updated=updated[:start]+value+updated[end:]
    if hashlib.sha256(updated.encode("utf-8")).hexdigest()!=meta["after"]:
        raise SystemExit("Output SHA256 mismatch: "+filename)
    path.write_text(updated,encoding="utf-8")
    print("Verified v0.5.5 metal UI patch:",filename)
for dsp_file in ["Source/PluginProcessor.cpp","Source/PluginProcessor.h","Source/CetusEQFilters.h","Source/CetusLink.h"]:
    assert Path(dsp_file).exists(), "Missing immutable DSP source: "+dsp_file
print("v0.5.5 purely visual patch applied; DSP files were not modified")
