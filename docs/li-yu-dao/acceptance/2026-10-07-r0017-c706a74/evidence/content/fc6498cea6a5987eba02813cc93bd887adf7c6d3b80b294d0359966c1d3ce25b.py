"""Only the packaging/import behavior affected by this candidate; no game."""
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent / "after"
TOOLS = ROOT / "mod_li_yu_dao/tools"
sys.path.insert(0, str(TOOLS))
import build_release
import validate_static
assert Path(build_release.__file__).resolve() == (TOOLS / "build_release.py").resolve()
assert Path(validate_static.__file__).resolve() == (TOOLS / "validate_static.py").resolve()
import test_build_release
import workshop_compatibility_tags as compatibility
assert Path(compatibility.registry.__file__).resolve() == (ROOT / "ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py").resolve()
names = ["test_reproducible_archive_and_fixture_exclusion"]
suite = unittest.TestSuite(test_build_release.BuildTests(name) for name in names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
