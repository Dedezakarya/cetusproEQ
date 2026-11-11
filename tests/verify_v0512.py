#!/usr/bin/env python3
from pathlib import Path
import hashlib
assert 'VERSION 0.5.12' in Path('CMakeLists.txt').read_text()
cpp=Path('Source/PluginEditor.cpp').read_text()
header=Path('Source/PluginEditor.h').read_text()
for needle in ('CetusBrandAssets::mark()', 'drawToggleButton(', 'syncVisualEnableState()', 'k.slider.setEnabled(enabled)', 'processor.parameters.getRawParameterValue("bypass")'):
    assert needle in cpp, needle
assert 'getLabelFont(juce::Label&)' in header
expected={
'PluginProcessor.cpp':'e72d5fda9c31fbc8cdb4223be3c4ddddaa9699d9905ce4e55fe4b7c6735ab6d4',
'PluginProcessor.h':'2e698fc4c3aa124b426add504cca1d8dfd7d4f4340b642b46fdffc56ebf90695',
'CetusEQFilters.h':'7ce62811577d1f78606e1828fa322dc0c8b5da1dc1eff33b26e4d4e720a4f329',
'CetusLink.h':'0d774b5846f22e537a185cea15a96bde3008c2fc28984d9bd593240fc324eefc',
}
for filename,sha in expected.items():
    actual=hashlib.sha256(Path('Source',filename).read_bytes()).hexdigest()
    if actual!=sha: raise SystemExit('DSP modified: '+filename)
print('v0.5.12 GUI contract and DSP verification PASSED')
