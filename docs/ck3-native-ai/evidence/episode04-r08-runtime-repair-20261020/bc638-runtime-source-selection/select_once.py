"""Invoke the unchanged component selector on the actual clean bc638 checkout.

No compiler, native executable, SDK, runtime assembly or source checkout runs.
The existing compressed 4770-entry closure is referenced, never copied/exported.
"""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
REPO = Path('D:/workspace/ck3_eternal_recurrence')
CURRENT = 'bc63851081462413d0cc6ebe62e37490707ee6a9'
MACHINE = 'desktop-3fevhd2-1c74096080'
OLD = BASE / 'r08-runtime-reuse-qualification-a01'
CAP = BASE / 'capacity/offline-1515-a01/OFFLINE-1515-C2M-D24-GIT-ADMISSION.actual-a01.json'

def pin(path):
    raw = path.read_bytes()
    assert len(raw) <= 1024 * 1024
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def read(path):
    return json.loads(path.read_bytes())

def write(path, value):
    raw = (json.dumps(value, indent=2) + '\n').encode()
    total = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    assert total + len(raw) <= 96 * 1024
    with path.open('xb') as stream:
        stream.write(raw)
    return pin(path)

capacity_ref = pin(CAP)
assert capacity_ref['bytes'] == 4881 and capacity_ref['sha256'] == '26816c35109848d2ab756f446042bff25f9b4503b877810b4162b962fae0aebe'
capacity = read(CAP)
assert capacity['admitted'] is True and capacity['budget_status'] == 'GREEN'
assert capacity['machine_id'] == MACHINE and capacity['D_current_source_HEAD'] == CURRENT
assert datetime.now(timezone.utc) < datetime.fromisoformat(capacity['hard_deadline_utc'].replace('Z', '+00:00'))
selector_path = OLD / 'native_component_reuse.py'
selector_ref = pin(selector_path)
assert selector_ref['bytes'] == 8605 and selector_ref['sha256'] == '89c52fe9358d02258f57fc6c805f700acafa321c6ffb7a02666d30231a5fb15b'
spec = importlib.util.spec_from_file_location('unchanged_e04_component_selector', selector_path)
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)
swap_path = BASE / 'source-swap-bc638-a01/SOURCE-SWAP.actual.json'
swap_ref = pin(swap_path)
assert swap_ref['bytes'] == 1661 and swap_ref['sha256'] == '1e6b9ecf514169fc83966d07e63beee1cba7098ff3c4a342a838deb97bd80314'
swap = read(swap_path)
assert swap['machine_id'] == MACHINE and swap['actual_head'] == swap['requested_head'] == CURRENT
assert swap['actual_native_tree'] == '6b91a527758357c1844bf9eb5647c1063ad7fdd8'
assert swap['dirty_porcelain'] == '' and swap['checkout_original_wait']['returncode'] == 0
assert swap['checkout_original_wait']['actual_original_popen_wait'] is True
assert swap['archive_remote_peeled_commit'] == CURRENT
assert selector.git(REPO, 'rev-parse', swap['runtime_archive_tag'] + '^{commit}') == CURRENT
old_ref = pin(OLD / 'GIT-EQUIVALENCE.actual-a01.json')
assert old_ref['sha256'] == 'b18c793a4fc03caf326a3295affca3eae6753bf1da81ed58ea25d3015be19275'
old = read(OLD / 'GIT-EQUIVALENCE.actual-a01.json')
equivalence = selector.observe_equivalence(REPO, old['base_commit'], CURRENT)
assert equivalence['nonpy_input_count'] == old['nonpy_input_count'] == 4770
assert equivalence['nonpy_git_blob_map_sha256'] == old['closure_sha256']
closure_ref = old['complete_nonpy_closure']
assert Path(closure_ref['path']).stat().st_size == closure_ref['bytes'] == 196478
# Do not serialize the in-memory complete list or re-read/copy its gzip payload.
proof = {key: value for key, value in equivalence.items() if key != 'closure'}
proof.update(schema='xar.e04.native-nonpy-git-equivalence.v1', machine_id=MACHINE,
    observed_at_utc=datetime.now(timezone.utc).isoformat(),
    complete_nonpy_closure=closure_ref, original_equivalence=old_ref,
    closure_reference_reused_without_copy=True, closure_payload_rehashed_here=False,
    source_swap=swap_ref, actual_runtime_checkout_qualified=True,
    source_swap_pending=False, whole_native_tree_equal=False, binary_payload_bodies_read=0)
proof_ref = write(ROOT / 'GIT-EQUIVALENCE.actual-a01.json', proof)
carrier_ref = pin(Path('C:/w/e04a41/ROOT-A41-COHERENT-QUALIFICATION.actual-a01.json'))
writer_ref = pin(Path('C:/w/e04r08a08/R08-A08-STANDALONE-QUALIFICATION.actual-a01.json'))
assert carrier_ref['sha256'] == '5cd13e6551c5646bdc57328c3a3bb34f7d069dcbb34da91d91f723e3c5f2e6b5'
assert writer_ref['sha256'] == '6e956a2b2d70f4c18e69426b76753e59cc5e14c4440e68a56e29875c53bd3f5c'
selection = selector.select_components(REPO, CURRENT, MACHINE, carrier_ref, writer_ref, equivalence, swap_ref)
assert selection['runtime_native_tree'] == old['runtime_native_tree']
selection.update(equivalence_receipt=proof_ref, complete_nonpy_closure=closure_ref,
    component_selector=selector_ref, metadata_capacity=capacity_ref,
    all_non_python_tracked_blobs_equal=True,
    current_runtime_repair_sources=[pin(REPO / path) for path in [
        'tools/ck3_mod_acceptance_cases/r08_writer_one_day.py',
        'ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_observations_v1.py']],
    official_CI_pass_claimed=False,
    CI_scope='This component selection does not qualify CI. Root reported the real MCP-not-installed CI failure; later workflow ordering fix/status is a separate published-master/CI record, not rerun or claimed PASS here.',
    published_master_native_tree_not_claimed_compiled=True,
    runtime_assembly_performed=False, SDK_game_Steam_actions=0,
    retention_review_utc='2026-10-20T15:15:00Z')
selection_ref = write(ROOT / 'CURRENT-SOURCE-COMPONENT-SELECTION.actual-a01.json', selection)
closed = dict(schema='xar.e04.bc638-native-component-selection-closed.v1',
    machine_id=MACHINE, observed_at_utc=datetime.now(timezone.utc).isoformat(),
    selection=selection_ref, equivalence=proof_ref, source_swap=swap_ref,
    unchanged_selector=selector_ref, capacity=capacity_ref,
    full_closure_reexported=False, binary_body_bytes_read=0,
    new_compilation=False, native_or_SDK_requests=0, runtime_assembly_performed=False,
    source_files_modified=0, original_Q_modified=False, official_CI_pass_claimed=False,
    remaining_heavy_write_bytes=0, retention_review_utc='2026-10-20T15:15:00Z')
closed_ref = write(ROOT / 'SELECTED-SCOPE-CLOSED.actual-a01.json', closed)
print(json.dumps(dict(selection=selection_ref, equivalence=proof_ref, closed=closed_ref,
    aggregate_bytes=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()), ceiling_bytes=98304)))
