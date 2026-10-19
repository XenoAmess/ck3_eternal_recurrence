"""Create-only finite3858 review; no install and no request publication."""
import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
def pin(p):
    p = Path(p); raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, required=True)
    out = parser.parse_args().output_root.resolve()
    if out == T.resolve() or out in T.resolve().parents or T.resolve() in out.parents:
        raise ValueError('review root must be outside runtime')
    helper = Path(__file__).with_name('succession3858_pending_ui_resume_v1.py')
    spec = importlib.util.spec_from_file_location('_resume3858_producer', helper)
    leaf = importlib.util.module_from_spec(spec); spec.loader.exec_module(leaf)
    ui = Path(__file__).with_name('p51_resident_successor_adoption_v1.py').read_bytes()
    source = leaf.checked(leaf.OLD / 'root_p37_automatic_natural_succession_handoff.py', leaf.SOURCE_SHA)
    leaf.original_namespace(source, ui)
    old = (T / 'root_p37_succession_recovery.py').read_bytes()
    candidate = leaf.transform_unused_succession(old)
    request = {'sequence': 3859, 'command': 'recover_partial_life_advance',
               'arguments': {'recovery_kind': 'ordinary_campaign_succession', 'repair_kind': leaf.KIND}}
    files = {'root_p37_succession3858_resume.py': helper.read_bytes(),
             'root_p37_succession3858_ui_contract.py': ui,
             'root_p37_succession_recovery.original.py': old,
             'root_p37_succession_recovery.py': candidate,
             '3859-1-result.json': (json.dumps(request, indent=2) + '\n').encode()}
    out.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        with (out / name).open('xb') as f: f.write(raw)
    review = {'schema': 'xar.succession3858-review/v1', 'machine_id': leaf.MACHINE,
              'observed_at_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Review only; sole runtime installs unused dynamic leaf and publishes one current3859 request',
              'source_package': {'path': str(leaf.FROZEN / 'FROZEN.json'), 'sha256': leaf.FROZEN_SHA},
              'files': {name: pin(out / name) for name in files},
              'success_marker': str(T / 'p37-queue/SUCCESSION3858-RESUME-SETTLED.json'),
              'new_audit': str(T / 'p37-queue/AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3859.json'),
              'original_Queue_or_cached_helpers_changed': False,
              'fresh_first_call': 'unique3860 ordinary AUTO; original six prefix results supply0RPC; no directClose/logicalContinue replay',
              'next_FULL': 'Keep original camera gate; final_semantic_response/final_frame bind new frozen pair and Root primary review'}
    with (out / 'REVIEW.json').open('x', encoding='utf-8') as f:
        json.dump(review, f, ensure_ascii=False, indent=2); f.write('\n')
    print(json.dumps(pin(out / 'REVIEW.json')))
if __name__ == '__main__': main()
