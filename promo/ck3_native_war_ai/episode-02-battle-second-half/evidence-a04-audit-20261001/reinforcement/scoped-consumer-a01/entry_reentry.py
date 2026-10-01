"""Fresh sealed paths for the layout consumer. SDK mode is root-only live."""
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result

def bind_inputs():
    bindings = json.loads((ROOT / 'runtime-input-bindings.json').read_text(encoding='utf-8'))
    consumer = load_module(ROOT / 'consumer/paused_join_pair.py', 'paused_join_pair')
    frozen = consumer.load(ROOT / 'variant-freeze.json')
    for row in [frozen['config'], frozen['no_launch_runner'], *frozen['consumer_files'], *frozen['helper_files']]:
        consumer.check_identity(row)
    consumer.check_identity(frozen['runtime_entry'])
    consumer.require(consumer.identity(ROOT / 'runtime-input-bindings.json') == frozen['runtime_bindings'], 'runtime input bindings changed')
    consumer.require(bindings['schema'] == 'xar.jd11.root-review-reentry.runtime-input-bindings/v1'
                     and bindings['source_head'] == consumer.HEAD
                     and Path(bindings['source_checkout']).resolve() == consumer.REPO.resolve(), 'source binding differs')
    consumer.require(bindings['consumer'] == consumer.identity(Path(consumer.__file__))
                     and bindings['consumer'] == frozen['layout_consumer'], 'frozen layout consumer required')
    consumer.require(bindings['allowed_module_path_overrides'] == ['CONFIG', 'SEAL'], 'non-path override refused')
    consumer.CONFIG = consumer.check_identity(bindings['config'])
    consumer.SEAL = Path(bindings['seal_path'])
    consumer.require(consumer.CONFIG.parent.resolve() == ROOT.resolve()
                     and consumer.SEAL.resolve() == (ROOT / 'seal').resolve(), 'reentry config/seal outside this attempt')
    consumer.check_identity(bindings['native_candidate_manifest'])
    consumer.check_identity(bindings['native_pair'])
    return consumer, bindings

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('prepare', 'sdk', 'probe-bindings'):
        raise SystemExit('usage: entry_reentry.py {prepare|sdk|probe-bindings} [arguments]')
    mode = sys.argv[1]
    consumer, bindings = bind_inputs()
    if mode == 'probe-bindings':
        print(json.dumps({'result': 'BOUND_INPUTS_ONLY_NO_LIVE_IO', 'consumer': bindings['consumer'],
                          'config': bindings['config'], 'seal_path': str(consumer.SEAL),
                          'source_head': consumer.HEAD, 'native_unchanged': True}, indent=2))
        return 0
    if mode == 'prepare':
        if '--help' not in sys.argv[2:]:
            import win32api, win32con
            consumer.require_layout_viewport(consumer.load(consumer.CONFIG),
                [win32api.GetSystemMetrics(win32con.SM_CXSCREEN), win32api.GetSystemMetrics(win32con.SM_CYSCREEN)])
        sys.argv = [sys.argv[0], *sys.argv[1:]]
        consumer.main()
        return 0
    # Actual SDK mode starts a managed job only after the root explicitly invokes it.
    consumer.check_identity(bindings['sdk'])
    sdk = load_module(Path(bindings['sdk']['path']), '_fresh_reentry_sdk')
    sys.argv = [sys.argv[0], *sys.argv[2:]]
    return sdk.main()

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
