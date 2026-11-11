#!/usr/bin/env python3
"""Build v0.5.9 from v0.5.8 native CI source; strictly no DSP changes."""
import base64, hashlib, json, lzma, re
from pathlib import Path
PATCH_B64="""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"""
patch=json.loads(lzma.decompress(base64.b64decode(PATCH_B64)))
for filename,operations in patch["ops"].items():
    path=Path(filename)
    text=path.read_bytes().decode('utf-8',errors='replace')
    for before,after in operations:
        count=text.count(before)
        if count==1:
            text=text.replace(before,after,1)
            continue
        if filename != "Source/PluginEditor.cpp":
            raise SystemExit('v0.5.9 GUI patch mismatch: '+filename+' / '+before[:85]+': '+str(count))
        # Older source variants differ slightly in punctuation and spacing.
        if "getTextButtonFont" in after:
            anchor="void CetusproEQAudioProcessorEditor::CetusLookAndFeel::drawComboBox("
            if anchor not in text: raise SystemExit("Missing drawComboBox anchor")
            extra=after[after.index("juce::Font "):].rstrip()+"\n"
            if "CetusLookAndFeel::getTextButtonFont" not in text:
                text=text.replace(anchor,extra+anchor,1)
            print("Compatibility fix: font methods inserted at class boundary")
        elif before.startswith("void CetusproEQAudioProcessorEditor::drawHeader("):
            first="void CetusproEQAudioProcessorEditor::drawHeader(juce::Graphics& g) {"
            next_fn="void CetusproEQAudioProcessorEditor::drawSpectrumAndCurve(juce::Graphics& g) {"
            if first not in text or next_fn not in text: raise SystemExit("Missing header renderer boundary")
            i=text.index(first);j=text.index(next_fn,i)
            text=text[:i]+after+text[j:]
            print("Compatibility fix: header renderer replaced by function range")
        elif "Undo and Redo as matched vector arrows" in before:
            first="void CetusproEQAudioProcessorEditor::CetusLookAndFeel::drawButtonText("
            next_fn="void CetusproEQAudioProcessorEditor::CetusLookAndFeel::drawRotarySlider("
            if first not in text or next_fn not in text: raise SystemExit("Missing button text renderer")
            i=text.index(first);j=text.index(next_fn,i)
            piece=text[i:j]
            k=piece.rfind("    } else {")
            if k<0: raise SystemExit("Missing undo/redo branch")
            # 'after' replaces the closing else branch and function brace.
            text=text[:i]+piece[:k]+after+"\n"+text[j:]
            print("Compatibility fix: undo/redo vector branch replaced")
        elif "g.drawRoundedRectangle(lower.toFloat()" in before:
            anchor="g.drawRoundedRectangle(lower.toFloat(),10.0f,1.0f);"
            if anchor not in text: raise SystemExit("Missing bottom panel renderer")
            # Insert decorative separators without changing existing controls.
            text=text.replace(anchor,anchor+after.split(anchor,1)[1],1)
            print("Compatibility fix: separators inserted")
        elif before.strip().startswith("setSize("):
            text,n=re.subn(r"setSize\s*\(\s*960\s*,\s*528\s*\)", "setSize(886, 487)",text,count=1)
            if n!=1:raise SystemExit("Missing GUI size")
        else:
            print("Optional appearance anchor skipped:",before[:80],count)
    if filename=="Source/PluginEditor.cpp":
        for required in ["CetusBrandAssets::mark()", "CetusBrandAssets::wordmark()",
                         "CetusLookAndFeel::getTextButtonFont", "setSize(886, 487)"]:
            if required not in text:raise SystemExit("Missing required v0.5.9 UI: "+required)
    path.write_text(text,encoding='utf-8')
    print('v0.5.9 patched',filename,'operations:',len(operations))
for filename,content in patch['new_files'].items():
    path=Path(filename)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')
    print('v0.5.9 brand asset header',filename)
for filename,expected in patch['sha256_dsp'].items():
    actual=hashlib.sha256(Path(filename).read_bytes()).hexdigest()
    if actual!=expected:raise SystemExit('DSP file checksum mismatch: '+filename)
print('v0.5.9: DSP identical, UI assets embedded, patch verified')
