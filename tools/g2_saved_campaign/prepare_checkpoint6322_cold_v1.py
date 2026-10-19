"""Prepare the finite C15 cold control sources in memory from exact C14/C11.

The sole runtime owner may export these bytes only under a new named metadata
card. No SDK source pair, Driver, SAVE, Game or recording is created here.
"""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
OWN = Path(__file__).resolve().parent
C14 = {
    'queue': ('root_p37c14_sdk_queue.py', '2a3b6b8faba7e2618c9e69864aa5c32cc2567a4396a9b09a76fdc08f9cd1fb1c'),
    'entry': ('root_p37c14_mcp_entry.py', 'dceea651637000f2f73ed0b53bb395e104d80f7ecb146b80a2514e0b9b8bc161'),
    'binder': ('root_native_build_binding_p37c14.py', 'd7084acd0685d88c6fb51b896f182407305232570c981c3ce5c073bd2a36845b'),
    'handoff': ('root_p37c14_automatic_natural_succession_handoff.py', '1b704a60b7b0e96ccd54a8aa0eae6be99112a7032d0a971073e07aa7fd6cdb29'),
    'resident': ('p51_resident_successor_adoption_c14.py', 'ee5e4183ce05cf0d5cd7173d3ae9c5f89fdc82a47891c6e9c11c1f906cfb2f2d'),
    'owner': ('launch_sdk_p37c14_owner.py', 'f574e98e5da19daa58491fb0bae86fb8895e897ded46f9bc8319c1eafdda9feb'),
}


def require(ok, message):
    if not ok:
        raise ValueError('C15 source composition denied: ' + message)


def text(path, expected):
    raw = Path(path).read_bytes()
    require(len(raw) <= 1024**2 and hashlib.sha256(raw).hexdigest() == expected, 'exact template differs: ' + str(path))
    return raw.decode('utf-8-sig').replace('\r\n', '\n')


def replace_once(value, old, new):
    require(value.count(old) == 1, 'unique reviewed source seam absent: ' + old[:80])
    return value.replace(old, new, 1)


def port(value, replacements):
    """Only exact namespace strings/identifiers; machine and hashes stay intact."""
    def mapped(s):
        for old, new in replacements:
            s = s.replace(old, new)
        return s
    class Names(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                return ast.copy_location(ast.Constant(mapped(node.value)), node)
            return node
        def visit_ImportFrom(self, node):
            node.module = mapped(node.module) if node.module else None
            return self.generic_visit(node)
        def visit_alias(self, node):
            node.name = mapped(node.name)
            return node
        def visit_Name(self, node):
            node.id = mapped(node.id)
            return node
        def visit_FunctionDef(self, node):
            node.name = mapped(node.name)
            return self.generic_visit(node)
        visit_AsyncFunctionDef = visit_FunctionDef
        visit_ClassDef = visit_FunctionDef
    changed = mapped(value)
    require(ast.dump(ast.parse(changed), include_attributes=False) ==
        ast.dump(Names().visit(ast.parse(value)), include_attributes=False), 'namespace touched non-namespace syntax')
    # These mappings cannot touch a machine suffix, hex digest, current actor,
    # episode or date. No broad lowercase c14/c11 substitution is permitted.
    for literal in (MACHINE, 'native-40526-1bec95182886'):
        require(value.count(literal) == changed.count(literal), 'protected identity changed')
    return changed


def build_sources():
    current = [('P37C14', 'P37C15'), ('p37c14', 'p37c15'), ('adoption_c14', 'adoption_c15'),
        ('-C14', '-C15'), ('SDKC14', 'SDKC15')]
    new_game = [('_c11', '_c15'), ('-C11', '-C15')]
    source = {key: port(text(T/name, digest), current + new_game) for key, (name, digest) in C14.items()}
    queue = source['queue']
    queue = replace_once(queue, 'from root_p37c15_warm_resume import make_normal_source_warm_queue_v1',
        'from root_p37c15_cold_resume import make_normal_checkpoint_cold_queue_v1')
    queue = replace_once(queue,
        "FreshQueue = make_normal_source_warm_queue_v1(CleanRobertMainMenuQueue, globals(), admission_path=N/'ROOT-P37C15-SOURCE-RESUME-ADMISSION.json')",
        "FreshQueue = make_normal_checkpoint_cold_queue_v1(CleanRobertMainMenuQueue, globals(), admission_path=N/'ROOT-P37C15-COLD-RESUME-ADMISSION.json')")
    queue = replace_once(queue, "queue._normal_source_warm['admission'].get('control_timing')",
        "queue._normal_cold['admission'].get('control_timing')")
    owner = replace_once(source['owner'], 'ROOT-SAVED-MAP-RECORDING-ADMITTED-C13-RECORDING02.json',
        'ROOT-SAVED-MAP-RECORDING-ADMITTED-C15.json')
    owner = replace_once(owner, 'ROOT-P37C15-SOURCE-RESUME-ADMISSION.json', 'ROOT-P37C15-COLD-RESUME-ADMISSION.json')
    owner = replace_once(owner, "admission['old_closed']", "admission['old_sdk_closed']")
    helper = port(text(OWN/'normal_checkpoint_cold_queue_v1.py',
        '6897ec13c0272ad3a39527dc42452514bc907c6e68fce1886d6dd8c250e83b53'),
        new_game + [('P37C11', 'P37C15'), ('p37c11', 'p37c15'), ('xar.c11.', 'xar.c15.')])
    old = """    require(seed == project_checkpoint_seed(original, save, save_response=admission['save_response']['path'],
        semantic_response=admission['saved_semantic_response']['path']), 'cold seed is not the exact actual SAVE projection')
    gov = checked(admission['governance'])"""
    new = """    gov = checked(admission['governance'])
    from root_checkpoint6322_cold_contract_c15 import validate_rollback
    from root_p37_checkpoint_cadence import checkpoint_saved
    require(hashlib.sha256(Path(checkpoint_saved.__code__.co_filename).read_bytes()).hexdigest()
        == 'a017eded18ca03733700fd61b10cace8981e5379e73dbe99b4d281fb97e4ae87', 'retained cadence source differs')
    validate_rollback(admission, seed, gov, checkpoint_saved=checkpoint_saved)"""
    helper = replace_once(helper, old, new)
    bootstrap = port(text(OWN/'native29_checkpoint_bootstrap_v1.py',
        '78b791dead2099fac0906daa8753bd5fa1b429466ff37b14e9448979bdfc6014'),
        new_game + [('P37C11', 'P37C15'), ('xar.c11.', 'xar.c15.')])
    old = """    recording = checked(close['recording_shutdown'])
    require(recording.get('status') == 'CLEANUP_OBSERVED' and recording.get('inputs_unbound') is True
        and recording.get('decision_text_publisher', {}).get('status') == 'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO',
        'old recording inputs and publisher must actually be closed')"""
    bootstrap = replace_once(bootstrap, old, """    from root_checkpoint6322_cold_contract_c15 import validate_abnormal_closure
    validate_abnormal_closure(close)""")
    supervisor = port(text(T/'root_native29_supervisor_c11.py',
        'dea80eef7ffc346a3d6cc36c3e1711461df3fc84db6f2eba79e1bbadcb99d19a'),
        new_game + [('P37C11', 'P37C15'), ('p37c11', 'p37c15')])
    supervisor = replace_once(supervisor, 'promo-runtime/ROOT-PROMO-KEEPER-SOURCE-READY.json',
        'ROOT-PROMO-KEEPER-SOURCE-READY-C15.json')
    supervisor = replace_once(supervisor,
        'KEEPER_PATH = Path("D:/codex-ck3-background-spill/ck3-sdk91/promo/ck3_native_war_ai/integration/screen_bus_lease.py")',
        "KEEPER_PATH = N / 'root_screen_bus_lease_c15.py'")
    supervisor = replace_once(supervisor,
        'KEEPER_SHA = "4a8233bb640d0eeda67150da818f3898a1c9afb0229d54e4d0d39e7a932f27f0"',
        'KEEPER_SHA = "012bb0a2aec9475ca8689bf42adc2e6c2431161814f7531f0710dbb633348780"')
    outputs = {
        'root_p37c15_sdk_queue.py': queue, 'root_p37c15_mcp_entry.py': source['entry'],
        'root_native_build_binding_p37c15.py': source['binder'],
        'root_p37c15_automatic_natural_succession_handoff.py': source['handoff'],
        'p51_resident_successor_adoption_c15.py': source['resident'],
        'launch_sdk_p37c15_owner.py': owner, 'root_p37c15_cold_resume.py': helper,
        'root_checkpoint_bootstrap_c15.py': bootstrap, 'root_native29_supervisor_c15.py': supervisor,
        'root_record_shutdown_c15.py': port(text(T/'root_record_shutdown_c11.py',
            '8f804af9302f86bbba43a3180807cbe995ba17689c0a0e0b6c94fdb0c73f54d1'), new_game),
        'root_score_month_samples_c15.py': port(text(T/'root_score_month_samples_c11.py',
            'a16fafc0c9e7fbb8d690f3e0ab717dc0a8e4481d7082e49d9f324ce22f6f97da'), new_game),
        'root_c15_control_timing_adapter.py': port(text(T/'root_c11_control_timing_adapter.py',
            '4e03b9fa34e00a23d8a9171955f436dcb54b707832e2a0bf4443c61f5c5917be'), new_game),
        'root_c15_queue_control_timing.py': text(T/'root_c11_queue_control_timing.py',
            '3950b3ce7ca1d4de401ba8e176d962c92187c2ad6fd280621e57d1f8f205d96c'),
        'root_screen_bus_lease_c15.py': text(OWN/'screen_bus_lease_lock_wait_v1.py',
            '012bb0a2aec9475ca8689bf42adc2e6c2431161814f7531f0710dbb633348780'),
        'root_checkpoint6322_cold_contract_c15.py': (OWN/'checkpoint6322_cold_contract_v1.py').read_text(encoding='utf-8'),
    }
    for name, value in outputs.items():
        compile(value, name, 'exec')
    # No algorithm transform or second timing instrumentation is applied.
    return {name: value.encode('utf-8') for name, value in outputs.items()}


def build_rollback_metadata():
    """Reconstruct only small current-state metadata from the closed frontier."""
    from checkpoint6322_cold_contract_v1 import project_saved_frontier
    package = T.parent.parent/'p51-fresh1066-v20261019-prepare01'
    closed = package/'c13-auto6356-failure88/display-closed'
    def pin(path):
        raw = path.read_bytes()
        require(len(raw) <= 262144, 'bounded rollback JSON required')
        return {'path':str(path), 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}
    admission = {key:pin(path) for key,path in {
        'original_state': package/'c14-war6356-warm88/clean/ROOT-CUMULATIVE-LOOP-STATE.json',
        'original_governance': package/'c14-war6356-warm88/clean/ROOT-GOVERNANCE-RESULT-STATE.json',
        'rollback_frontier': closed/'CHECKPOINT6322-FRONTIER.json',
        'save_response': T/'p37-responses/6322-1-result.json',
        'saved_semantic_response': T/'p37-responses/6321-1-result.json',
        'abnormal_display_closure': closed/'FROZEN.json',
        'abnormal_supervisor_closure': closed/'GAME-SUPERVISOR-EXIT-FROZEN.json'}.items()}
    cadence = T/'root_p37_checkpoint_cadence.py'
    require(pin(cadence)['sha256'] == 'a017eded18ca03733700fd61b10cace8981e5379e73dbe99b4d281fb97e4ae87',
        'actual original checkpoint cadence required')
    sys.path.insert(0,str(T))
    spec = importlib.util.spec_from_file_location('_c15_original_checkpoint_cadence',cadence)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    seed, gov = project_saved_frontier(admission, checkpoint_saved=module.checkpoint_saved)
    receipt = {'schema':'xar.c15.checkpoint6322-reconstructed-seed/v1','machine_id':MACHINE,
        'source_observed_at_utc':json.loads(Path(admission['rollback_frontier']['path']).read_bytes())['observed_at_utc'],
        'timestamp_basis':'closed source observation; actual export UTC is recorded separately in REVIEW.json',
        'source_inputs':admission,
        'reconstruction':'closed current metadata plus exact saved cumulative turn/save event',
        'saved_cycles':3023,'saved_date_raw':53202384,'historical_later_cycles':3037,
        'historical_later_date_raw':53202696,'old_full_snapshot_claimed':False,
        'future_war_regime_unknown':True,'Driver_or_SAVE_body_read':False,
        'actual_new_Game_cold_SEM_and_CAP_still_required':True}
    metadata = {'CHECKPOINT6322-COLD-SEED.json':seed,'CHECKPOINT6322-COLD-GOVERNANCE.json':gov,
        'CHECKPOINT6322-RECONSTRUCTION.json':receipt}
    return admission,{name:(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
        for name,value in metadata.items()}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--storage-admission', type=Path, required=True)
    args = parser.parse_args()
    card = json.loads(args.storage_admission.read_bytes()); out = args.output.resolve()
    require(card.get('status') == 'ADMITTED' and card.get('machine_id') == MACHINE
        and card.get('generation') == 'C15' and not out.exists()
        and str(out) == card.get('source_review_root'), 'exact new C15 metadata card/output required')
    files = build_sources()
    inputs, metadata = build_rollback_metadata()
    files.update(metadata)
    require(sum(len(raw) for raw in files.values()) + 65536 <= card['source_output_ceiling_bytes'],
        'bounded C15 source metadata output exceeds named ceiling')
    out.mkdir(parents=True)
    pins = []
    for name, raw in files.items():
        with (out/name).open('xb') as stream:
            stream.write(raw)
        pins.append({'path': str(out/name), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    review = {'schema': 'xar.c15.checkpoint6322-cold-source-review/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'files': pins,
        'business_source_commit': 'd804be64838b25c234ef1f805d8e641e4f677450',
        'rollback_admission_inputs': inputs,
        'source_pair_reused': True, 'Game_or_SDK_or_OBS_or_SAVE_body_operations': 0,
        'restored_cycles': 3023, 'restored_date_raw': 53202384,
        'historical_later_cycles': 3037, 'historical_later_date_raw': 53202696,
        'old_publisher_child_numeric_exit_code': None, 'actual_new_Game_and_recording_admissions_required': True}
    with (out/'REVIEW.json').open('x', encoding='utf-8') as stream:
        json.dump(review, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'path': str(out/'REVIEW.json'), 'files': len(files)}))


if __name__ == '__main__':
    main()
