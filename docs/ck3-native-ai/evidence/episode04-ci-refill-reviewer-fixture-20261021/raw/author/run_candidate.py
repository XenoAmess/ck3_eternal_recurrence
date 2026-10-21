"""Run the candidate as installed in the exact minimal 58d test source layout."""
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parent
candidate = ROOT / 'candidate/tools/test_ck3_mod_acceptance_r06_scope.py'
module = types.ModuleType('__main__')
# The source is the external candidate; only its repository-relative resource
# lookup is mapped to the immutable exact-58d helper/config shadow.
module.__file__ = str(ROOT / 'shadow/tools/test_ck3_mod_acceptance_r06_scope.py')
module.__package__ = None
sys.modules['__main__'] = module
sys.argv = [str(candidate), '--scratch-root', str(ROOT / 'tmp')]
exec(compile(candidate.read_bytes(), str(candidate), 'exec'), module.__dict__)
