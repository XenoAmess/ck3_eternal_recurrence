"""Run the actual external test module against a pinned read-only source tree."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
W = Path('C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree')


def main() -> int:
    variant = sys.argv[1]
    attempt = 'a04'
    if variant not in ('baseline', 'candidate'):
        raise ValueError('Named test source required')
    source = ROOT / variant / 'tools/test_ck3_mod_acceptance_r06_scope.py'
    scratch = ROOT / ('scratch-' + variant + '-' + attempt)
    scratch.mkdir(exist_ok=False)
    os.environ['TMP'] = str(scratch)
    os.environ['TEMP'] = str(scratch)
    sys.path[:0] = [str(ROOT / 'dependencies'), str(W / 'tools'), str(W / 'ck3_autonomous_player/src')]
    sys.argv = [str(source), '--scratch-root', str(scratch)]
    spec = importlib.util.spec_from_file_location('r06_scope_' + variant, source)
    if spec is None or spec.loader is None:
        raise ValueError('Actual test module loader absent')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # A normal import executes the exact candidate bytes. Only the existing
    # module globals selecting source inputs and temporary fixtures are bound.
    module.REPO = W
    module.options.scratch_root = scratch
    missing_catalog = W / 'tools/ck3_mod_acceptance_r10_products.json'
    actual_catalog = ROOT / 'dependencies/ck3_mod_acceptance_r10_products.json'
    original_read = module.entry.read_json
    redirected: list[str] = []
    def read_catalog(path: Path):
        if path.resolve() == missing_catalog.resolve():
            redirected.append(str(path))
            return original_read(actual_catalog)
        return original_read(path)
    module.entry.read_json = read_catalog
    original_pin = module.entry.pin
    pin_redirects: list[str] = []
    exact_pin_inputs = {W / 'tools' / name: ROOT / 'dependencies' / name for name in (
        'ck3_mod_acceptance_native_day.py', 'steam_offline_state_contract.py',
        'steam_offline_state_probe.py')}
    def pin_input(path: Path):
        mapped = exact_pin_inputs.get(path.resolve())
        if mapped is not None:
            pin_redirects.append(str(path))
            return original_pin(mapped)
        return original_pin(path)
    module.entry.pin = pin_input
    module.allocator.pin = pin_input
    original_setup = module.PublicR06ScopeTests.setUp
    def setup_catalog(case):
        original_setup(case)
        # Bind the catalog's actual pathname for immutable pinning. The runtime
        # repo_root remains the real W source tree selected by the original setup.
        case.products_path = actual_catalog
    module.PublicR06ScopeTests.setUp = setup_catalog
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(module))
    loaded: list[dict[str, str | int]] = []
    for name, imported in sorted(sys.modules.items()):
        filename = getattr(imported, '__file__', None)
        if not isinstance(filename, str):
            continue
        path = Path(filename).resolve()
        if path.is_relative_to(W) and path.is_file() and path.suffix == '.py':
            raw = path.read_bytes()
            loaded.append({'module': name, 'path': path.relative_to(W).as_posix(),
                           'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    receipt = {'variant': variant, 'test_source': str(source),
               'test_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'repo_override': str(module.REPO), 'scratch_override': str(scratch),
               'pin_read_redirects': pin_redirects, 'catalog_read_redirects': redirected, 'catalog_pin_path': str(actual_catalog),
               'tests_run': result.testsRun, 'errors': len(result.errors),
               'failures': len(result.failures), 'loaded_source': loaded,
               'remaining_scratch_files': [str(p) for p in scratch.rglob('*') if p.is_file()]}
    with (ROOT / (variant + '-focused-' + attempt + '.actual.json')).open('x', encoding='utf-8') as target:
        json.dump(receipt, target, indent=2)
        target.write('\n')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
