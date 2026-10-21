"""Finite offline fixture entry; forbid every real child launcher in the test."""
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SHADOW = ROOT.parent / 'public-repair-a01/shadow/tools'
sys.path[:0] = [str(ROOT / 'deps/tools'), str(SHADOW)]
import ck3_mod_acceptance_cases
ck3_mod_acceptance_cases.__path__.insert(0, str(ROOT / 'deps/tools/ck3_mod_acceptance_cases'))
tempfile.tempdir = str(ROOT / 'tmp')
target = Path(sys.argv[1]).resolve()
if target.parent not in (ROOT / 'baseline', ROOT / 'candidate'):
    raise ValueError('Exact owned fixture required')
sys.argv = [str(target)]
with patch('subprocess.Popen', side_effect=AssertionError('No real launcher/native/SDK/Game children')):
    runpy.run_path(str(target), run_name='__main__')
