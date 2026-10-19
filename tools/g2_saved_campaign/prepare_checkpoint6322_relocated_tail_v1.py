"""Finite four-row relocation for the unloaded C15 Queue only.

The live supervisor's original cold contract and the original frontier are
immutable. This emits an isolated Queue contract and one changed import.
"""
import hashlib
import json
from pathlib import Path

T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
F = T.parent.parent/'p51-fresh1066-v20261019-prepare01/c13-auto6356-failure88/display-closed/CHECKPOINT6322-FRONTIER.json'
ARCHIVE = T/'p37-queue-closed-C13-before-C15-6358'
TAIL_HELPER = '''

def _queue_tail_reference(item, relocated):
    require(isinstance(relocated, dict) and set(relocated) == {'3034', '3035', '3036', '3037'},
        'only four exact original C13 tail rows may relocate')
    turn = item['global_turn']
    original = item['source']
    if turn not in (3034, 3035, 3036, 3037):
        return original
    root = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime').resolve()
    basename = 'CUMULATIVE-TURN-' + str(turn).zfill(6) + '.json'
    require(Path(original['path']).resolve() == root/'p37-queue'/basename,
        'original frontier must bind the exact former C13 Queue row')
    moved = relocated[str(turn)]
    require(set(moved) == {'path', 'bytes', 'sha256'}
        and Path(moved['path']).resolve() == root/'p37-queue-closed-C13-before-C15-6358'/basename
        and moved['bytes'] == original['bytes'] and moved['sha256'] == original['sha256'],
        'different archive, basename, byte count or original digest')
    return moved
'''


def require(ok, message):
    if not ok:
        raise ValueError('checkpoint6322 relocation denied: ' + message)


def read_exact(path, digest):
    raw = path.read_bytes()
    require(len(raw) <= 262144 and hashlib.sha256(raw).hexdigest() == digest,
        'exact unloaded source or closed frontier differs')
    return raw


def relocated_admission_refs():
    frontier = json.loads(read_exact(F, '0052ae0b2dfc7858b53271022adde77ebb156c3bb34fd6b5fbec7ddc039470fd'))
    result = {}
    for item in frontier['post_SAVE_tail']:
        turn = item['global_turn']
        if turn in (3034, 3035, 3036, 3037):
            original = item['source']
            basename = 'CUMULATIVE-TURN-' + str(turn).zfill(6) + '.json'
            require(Path(original['path']).resolve() == (T/'p37-queue'/basename).resolve(),
                'different original frontier path')
            result[str(turn)] = {'path':str(ARCHIVE/basename),
                'bytes':original['bytes'], 'sha256':original['sha256']}
    require(set(result) == {'3034', '3035', '3036', '3037'}, 'four original rows required')
    return result


def build_sources():
    contract = read_exact(T/'root_checkpoint6322_cold_contract_c15.py',
        'e488b5c57144bf153898efdb24de0f2b14286cc46e4f71da118caf786e5fd4d2').decode('utf8')
    old = "        exact(item['source'], (item['source']['bytes'], item['source']['sha256']))"
    new = "        exact(_queue_tail_reference(item, admission['relocated_post_save_tail']), (item['source']['bytes'], item['source']['sha256']))"
    require(contract.count(old) == 1, 'one original tail validation seam required')
    queue_contract = contract.replace(old, new, 1) + TAIL_HELPER
    cold = read_exact(T/'root_p37c15_cold_resume.py',
        'a11ed9e2a19c95f9b347c9cc577ecb8bfb48bc7f02e8c2a68b33c984015e0f03').decode('utf8')
    old_import = 'from root_checkpoint6322_cold_contract_c15 import validate_rollback'
    require(cold.count(old_import) == 1, 'one unloaded cold Queue import seam required')
    cold = cold.replace(old_import, 'from root_checkpoint6322_queue_contract_c15 import validate_rollback', 1)
    outputs = {'root_checkpoint6322_queue_contract_c15.py':queue_contract.encode('utf8'),
        'root_p37c15_cold_resume.py':cold.encode('utf8')}
    for name,raw in outputs.items():
        compile(raw, name, 'exec')
    return outputs
