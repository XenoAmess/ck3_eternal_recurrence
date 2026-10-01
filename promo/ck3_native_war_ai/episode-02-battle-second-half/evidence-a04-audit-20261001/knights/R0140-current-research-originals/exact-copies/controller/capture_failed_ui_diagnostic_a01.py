"""Read the preserved failed action's original pixels; never repeat the action."""
from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parent

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def main():
    helper = ROOT / 'scoped_ui_research_a05.py'
    with helper.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    require(digest == 'BF88D05E946233993F64F5F3275C11A20AE1297105F4194A0699586F45E90A6E', 'Controller bytes changed')
    spec = importlib.util.spec_from_file_location('_original_failed_ui_consumer', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bindings_path = ROOT / 'current-run-bindings.json'
    config = module.read(bindings_path)
    live, output, evidence, transport, steps = module.bind(config)
    label = 'failed-victim-ui-diagnostic'
    before, br, values = module.snapshot(output, transport, steps, label + '-before-pixels', config['before_date_raw'])
    image = module.capture_window(live, evidence, label)
    after, ar, av = module.snapshot(output, transport, steps, label + '-after-pixels', config['before_date_raw'])
    require(values == av, 'Paused source changed during failed-action diagnosis')
    destination = evidence / (label + '.json')
    module.write(destination, {'source_binding': module.identity(bindings_path), 'before_values': values,
        'after_values': av, 'before_snapshot': br, 'after_snapshot': ar, 'image': image,
        'original_open_action_retry_count': 0, 'day_advance_count': 0, 'ui_identity_semantics': 'pending original pixels and native contract correction',
        'purpose': 'Diagnose date_raw action validation failure without treating failed ACK as accepted'})
    print(json.dumps({'diagnostic': str(destination), 'image': image['image']}))

if __name__ == '__main__':
    main()
