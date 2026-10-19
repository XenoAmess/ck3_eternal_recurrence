"""Future C21 controls: exact namespace port plus one explicit WAL env key.

Only RAM source bytes are returned. This does not export an SDK, create a Task,
start a process, or admit runtime use. Public composition needs the later actual
Root Git record; source qualification uses the separate private source builder.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
KEY = 'XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1'
PLAN = REPO/'docs/ck3-native-ai/evidence/source21-longterm-sdk-source-plan-2026-10-20.json'
PLAN_SHA = '9fdb39ffa6d1eb92ef47733f943477ad40110238d1b378209d71c5aa6f286ed2'
ROWS_SHA = 'c4b506600cca3f78b90b41e9daf8475bf337c350d9dff6eebc661ea273f602ba'
PARENT = 'f19864de1cc073eed62617faad2307c57ad45a97'
PORT = REPO/'_runtime/compose_C18_warm_controls93.py'
PORT_SHA = '2bbdee3dc30521aca2b4f774d75b8f1df9e73b5816be3d3d6d880dac20e63fa6'
BASE = {
 'root_p37c20_sdk_queue.py':(267957,'ed5f8b77b5fbb69b27be204d36f28e1a2e45acd572ff7fae2658444f07f9a09d'),
 'root_p37c20_mcp_entry.py':(12630,'a00aa55f62ec6184a31f4a6f4f9957ed95dfaceb55094352adc70af89bb68a6f'),
 'root_native_build_binding_p37c20.py':(4090,'93468a9628b2b3f7a24c5dbd7013ceb6eb1d3f6bbb32a8adb4240e0a4b30b50f'),
 'root_p37c20_automatic_natural_succession_handoff.py':(38624,'dca34aee98f396da3a8593c10df8618643e16022a294e3b956585266adf2ca85'),
 'p51_resident_successor_adoption_c20.py':(24607,'af99ff1943c46cf053ac19e9244152251f541973c2ee9a6c0f86b6c3a7b357a4'),
 'launch_sdk_p37c20_owner.py':(5462,'e6063206ff45cf7d5f7da42e0534bc058adc51798bcf7cc19e8f0d3370272630'),
 'root_p37c20_warm_resume.py':(14752,'b4abc2203eaeaef17f1b058cdaf416c39b31262654a90450e31f2e583d0894c7')}
PAIRS = (('P37C20','P37C21'),('p37c20','p37c21'),('-C20','-C21'),
 ('SDKC20','SDKC21'),('p51_resident_successor_adoption_c20','p51_resident_successor_adoption_c21'))
CLASSIFIER_SHA = '0bff8fae24c072d5f05285ba62c503dfed408f8095690fb8dffec16fe72ec28b'
ANCHOR = '    hold_ab_speed = os.environ.get("XAR_STATIONARY_HOLD_AB_SPEED", "5")\n'
WAL_HUNK = '''    wal_value = os.environ.get("XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1")
    if wal_value is not None:
        if type(wal_value) is not str or wal_value not in {"0", "1"}:
            raise ValueError("driver state WAL env must be absent, 0 or 1")
        child_env["XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1"] = wal_value
'''


def require(ok, reason):
    if not ok:
        raise ValueError('C21 controls denied: '+reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, size, digest):
    raw = path.read_bytes()
    require(len(raw) == size and sha(raw) == digest, 'frozen source differs: '+str(path))
    return raw


def business_plan_v1():
    plan = json.loads(checked(PLAN, 9446, PLAN_SHA))
    require(plan.get('machine_id') == MACHINE
        and plan.get('schema') == 'xar.source21.longterm-five-leaf-frozen-source-plan/v1'
        and plan['base']['business_commit'] == PARENT, 'Source21 provenance differs')
    output = plan['output']
    require(output['file_count'] == 1447 and output['source_bytes'] == 59074855
        and output['canonical_rows_JSON']['sha256'] == ROWS_SHA
        and plan['delta']['existing'] == 5 and plan['delta']['new'] == 0,
        'complete Source21 rows differ')
    return {'path':str(PLAN), 'bytes':9446, 'sha256':PLAN_SHA,
        'file_count':1447, 'source_bytes':59074855, 'rows_sha256':ROWS_SHA,
        'parent':PARENT}


def bind_actual_business_anchor_v1(raw, ref):
    """Bind a future Root actual Git record; never mint an anchor or authority."""
    require(type(raw) is bytes and isinstance(ref, dict)
        and type(ref.get('path')) is str and Path(ref['path']).is_absolute()
        and type(ref.get('bytes')) is int and len(raw) == ref['bytes'] <= 65536
        and sha(raw) == ref.get('sha256'), 'actual Root record pin required')
    record = json.loads(raw)
    require(record.get('machine_id') == MACHINE and isinstance(record.get('actual'), dict),
        'actual Root Git record required')
    actual = record['actual']; commit = actual.get('commit')
    require(type(commit) is str and len(commit) == 40
        and all(c in '0123456789abcdef' for c in commit) and len(set(commit)) > 1
        and commit != PARENT and actual.get('parent') == PARENT,
        'unknown/placeholder/predecessor is not the new actual Git anchor')
    manifest = actual.get('complete_manifest') or {}
    require(manifest.get('file_count') == 1447 and manifest.get('source_bytes') == 59074855
        and (manifest.get('canonical_rows_JSON') or {}).get('sha256') == ROWS_SHA,
        'actual Git record must bind the complete Source21 rows')
    require(type(actual.get('ref')) is str and actual['ref'].startswith('refs/heads/campaign/')
        and type(actual.get('tree')) is str and len(actual['tree']) == 40
        and all(c in '0123456789abcdef' for c in actual['tree']), 'actual tree/ref missing')
    return {'record':copy.deepcopy(ref), 'commit':commit, 'parent':PARENT,
        'tree':actual['tree'], 'ref':actual['ref'], 'rows_sha256':ROWS_SHA,
        'runtime_admitted':False, 'separate_export_Task_and_runtime_admissions_required':True}


def _source_graph_v1():
    """Private qualification builder; output is not an admitted runtime graph."""
    plan = business_plan_v1()
    raw = checked(PORT,6120,PORT_SHA)
    text = raw.decode().replace('P37C18oldReadyQueue','P37C21oldReadyQueue').replace('P37C17oldReadyQueue','P37C20oldReadyQueue')
    scope = {'__name__':'C21_source_namespace_only', '__file__':str(PORT)}
    exec(compile(text,str(PORT),'exec'),scope)
    scope['PAIRS'] = PAIRS
    graph = {}; protected = 0
    for name,(size,digest) in BASE.items():
        original = checked(T/name,size,digest)
        namespace = scope['port'](original.decode())
        candidate = namespace
        if name == 'root_p37c20_sdk_queue.py':
            require(namespace.count(ANCHOR) == 1 and WAL_HUNK not in namespace, 'one new WAL seam required')
            candidate = namespace.replace(ANCHOR,WAL_HUNK+ANCHOR,1)
            require(candidate.replace(WAL_HUNK,'',1) == namespace,
                'WAL hunk changed original statements')
        new_name = scope['mapped'](name)
        compile(candidate,new_name,'exec')
        old_values = [n.value for n in ast.walk(ast.parse(original)) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        new_values = [n.value for n in ast.walk(ast.parse(candidate)) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        for value in old_values:
            if value == MACHINE or value.startswith('native-') or (len(value)==64 and all(c in '0123456789abcdef' for c in value)) or 'C16' in value or 'c16' in value:
                require(old_values.count(value) == new_values.count(value), 'protected constant changed')
                protected += 1
        graph[new_name] = candidate.encode()
    require(protected == 45 and len(graph) == 7, 'original seven-source namespace shape differs')
    checked(T/'root_p37c11_prisoner_epoch_classifier.py',260570,CLASSIFIER_SHA)
    factory = graph['root_p37c21_warm_resume.py'].decode()
    require(factory.count("self.flags = [flag for flag in self.flags if flag != '--private-active-scheme-sway-completion-execution-query']") == 1,
        'Native29 execution-query mask lost')
    require(graph['root_p37c21_sdk_queue.py'].decode().count('from root_p37c16_overlay_relay import relay_compact, error_projection') == 3
        and 'from root_p37c16_compact_decision_feed import publish_before_submit' in graph['root_p37c21_mcp_entry.py'].decode()
        and 'ROOT-SAVED-MAP-RECORDING-ADMITTED-C16.json' in graph['launch_sdk_p37c21_owner.py'].decode(),
        'retained physical C16 publication/record binding changed')
    return graph, {'business_plan':plan, 'runtime_admitted':False,
        'protected_constants':protected, 'WAL_policy':'strict absent/0/1; only this key forwarded; no implicit opt-in',
        'physical_generation':'C16', 'native_execution_query':False,
        'classifier_sha256':CLASSIFIER_SHA, 'control_probe_enabled':False}


def compose(*, anchor_raw, anchor_ref):
    """Future runtime producer API: actual source anchor first, RAM bytes only."""
    binding = bind_actual_business_anchor_v1(anchor_raw,anchor_ref)
    graph, report = _source_graph_v1()
    return graph, {**report, 'actual_business_anchor':binding}
