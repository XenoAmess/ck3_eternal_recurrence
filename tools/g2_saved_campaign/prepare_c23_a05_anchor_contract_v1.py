"""Pure RAM repair of the exact installed A05 helper's Source26 contract."""
import ast
import hashlib
import json
from pathlib import Path

OWN = Path(__file__).resolve().parent
REPO = OWN.parents[1]
T5 = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime-a05')
HELPER = 'root_c23_a03_source_abort_checkpoint_inputs.py'
ANCHOR = REPO / '_runtime/source26-integration17/SOURCE26-CANONICAL-ANCHOR.json'
OLD = (15280, '4778f4b406d5c33bc3cb6c52dfb5cea2fa744590d8404c607c9cb86c98d37d3e')
ANCHOR_PIN = (7045, 'd2bf903d4a0f18cc819721451d42e390a58529f76a19ad2df301e85df5b78e85')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def exact(path, expected):
    with Path(path).open('rb') as stream:
        raw = stream.read(expected[0] + 1)
    if (len(raw), sha(raw)) != expected:
        raise ValueError('A05 anchor candidate source differs: ' + str(path))
    return raw


def build_source(*, helper_raw=None, helper_ref=None):
    """Require an explicit exact preimage; accept union RAM or an archived ref.

    The installed U5 path is deliberately not a default input: after the cold
    amendment that path contains the replacement, while the preimage survives
    under its Root-owned archive reference.
    """
    if (helper_raw is None) == (helper_ref is None):
        raise ValueError('one explicit pinned RAM helper or original helper ref required')
    if helper_ref is not None:
        if (helper_ref.get('bytes'), helper_ref.get('sha256')) != OLD:
            raise ValueError('explicit original helper reference pin differs')
        old = exact(helper_ref['path'], OLD)
        preimage = dict(helper_ref)
    else:
        if type(helper_raw) is not bytes or (len(helper_raw), sha(helper_raw)) != OLD:
            raise ValueError('exact original RAM helper preimage required')
        old = helper_raw
        preimage = {'source_kind': 'explicit caller RAM preimage', 'bytes': OLD[0], 'sha256': OLD[1]}
    anchor = json.loads(exact(ANCHOR, ANCHOR_PIN))
    provenance = {key: anchor[key] for key in ('writer', 'composer', 'source_plan', 'actual_Source25_anchor')}
    for item in provenance.values():
        exact(item['path'], (item['bytes'], item['sha256']))
    plan = json.loads(Path(anchor['source_plan']['path']).read_bytes())
    if plan['output'] != {'files': 1462, 'source_bytes': 59253402,
                         'canonical_rows_JSON': anchor['complete_rows_JSON']}:
        raise ValueError('actual Source26 plan complete rows differ')
    if len(anchor['output_pins']) != len(plan['delta']) or len(plan['delta']) != 12:
        raise ValueError('actual Source26 twelve-output writer contract differs')
    replacement = f'''def validate_business_anchor(anchor):
    """Accept the actual Source26 writer receipt; it declares no Native binding."""
    require(isinstance(anchor,dict) and anchor.get('schema')=='xar.source26.canonical-git-anchor/v1'
        and anchor.get('machine_id')==MACHINE and anchor.get('status')=='CANONICAL_REF_CREATED_NOT_DEPLOYED'
        and anchor.get('execution_owner')=='Root' and anchor.get('root_direct_execution_release') is True
        and anchor.get('parent')=={anchor['parent']!r} and anchor.get('commit')=={anchor['commit']!r}
        and anchor.get('tree')=={anchor['tree']!r} and anchor.get('ref')=={anchor['ref']!r},
        'actual Source26 canonical source identity required')
    require(anchor.get('source_file_count')==1462 and anchor.get('source_bytes')==59253402
        and anchor.get('complete_rows_JSON')=={anchor['complete_rows_JSON']!r}
        and type(anchor.get('output_pins')) is list and len(anchor['output_pins'])==12
        and hashlib.sha256(json.dumps(anchor['output_pins'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()=={sha(canonical(anchor['output_pins']))!r}
        and anchor.get('changed_SHA256_bodies_read_back')==12 and anchor.get('all_Git_mode_blob_size_verified') is True,
        'actual Source26 twelve changed leaves and 1462 complete rows required')
    require(all(anchor.get(key)==0 for key in ('Git_export_runtime_Task_Game_Native_RPC_calls_before_writer',
            'runtime_calls','SDK_export_calls','push_calls','index_or_tracked_worktree_mutations','future_writes'))
        and anchor.get('actual_loaded_provider') is False and anchor.get('actual_H')=='unknown'
        and anchor.get('source_epoch_actual_filesystem_authority') is False,
        'Source26 writer grants no runtime, export, Native, H or loaded-provider credit')
    require(all(anchor.get(key)==value for key,value in {provenance!r}.items())
        and hashlib.sha256(json.dumps(anchor,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()=={sha(canonical(anchor))!r},
        'actual immutable Source26 writer/composer/plan/predecessor receipt required')
    return anchor
'''
    frozen = f'''def validate_frozen_business(admission,freeze,checked):
    require(content_ref(admission['business_anchor'],{{'bytes':{ANCHOR_PIN[0]},'sha256':{ANCHOR_PIN[1]!r}}}),
        'exact actual Source26 anchor reference required')
    anchor=validate_business_anchor(checked(admission['business_anchor'],65536))
    rows=freeze['files'];raw=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    require(freeze.get('machine_id')==MACHINE
        and freeze.get('business_source_commit')==admission.get('business_source_commit')==anchor['commit']
        and freeze.get('source_file_count')==len(rows)==anchor['source_file_count']==1462
        and freeze.get('source_bytes')==sum(row['bytes'] for row in rows)==anchor['source_bytes']==59253402
        and {{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}}==anchor['complete_rows_JSON'],
        'actual Source26 full canonical rows and runtime freeze must be identical')
    by_name={{row['relative']:row for row in rows}}
    require(len(by_name)==1462 and all(by_name.get(row['relative'])==row for row in anchor['output_pins']),
        'all twelve Source26 changed leaves must be exact complete-row members')
    return anchor
'''
    text = old.decode('utf-8')
    tree = ast.parse(text)
    for name, new in (('validate_business_anchor', replacement), ('validate_frozen_business', frozen)):
        node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
        before = ast.get_source_segment(old.decode('utf-8'), node)
        if text.count(before) != 1:
            raise ValueError('unique helper function seam differs')
        text = text.replace(before, new.rstrip(), 1)
    result = text.encode('utf-8')
    compile(result, 'A05-actual-Source26-anchor-helper-RAM', 'exec')
    untouched = lambda data: [ast.dump(node, include_attributes=False) for node in ast.parse(data).body
        if not isinstance(node, ast.FunctionDef) or node.name not in ('validate_business_anchor', 'validate_frozen_business')]
    if untouched(old) != untouched(result):
        raise ValueError('helper changed outside the two exact Source26 validators')
    return result, {'schema': 'xar.C23-A05-actual-Source26-anchor-helper-RAM/v1',
        'machine_id': anchor['machine_id'], 'old_helper': preimage,
        'actual_anchor': {'path': str(ANCHOR.resolve()), 'bytes': ANCHOR_PIN[0], 'sha256': ANCHOR_PIN[1]},
        'output': {'name': HELPER, 'bytes': len(result), 'sha256': sha(result)},
        'changed_functions': ['validate_business_anchor', 'validate_frozen_business'],
        'all_other_AST_unchanged': True, 'runtime_Git_Task_Game_writes_or_calls': 0}
