package org.xar.ck3.control.wave2.military.coalitionreceipt;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Offline real transport pure-boundary capture; shared storage Job owner executes it explicitly. */
public final class CaptureCoalitionReceiptGolden {
    private CaptureCoalitionReceiptGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("repo python new-D-output required");
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        Path root = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1").toRealPath();
        if (!output.startsWith(root) || Files.exists(output)) throw new IllegalArgumentException("new admitted D output required");
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-c", SCRIPT, args[0], output.toString()));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("OPENBLAS_NUM_THREADS", "1"); builder.environment().put("OMP_NUM_THREADS", "1");
        Process child = builder.directory(Path.of(args[0]).toFile()).inheritIO().start();
        if (!child.waitFor(100, TimeUnit.SECONDS)) {
            child.destroyForcibly(); throw new IOException("receipt capture timeout; shared Job owns remaining descendants");
        }
        if (child.exitValue() != 0) throw new IOException("actual transport producer exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 51_200) throw new IOException("receipt golden exceeded 50KiB");
    }
    private static final String SCRIPT = """
import copy,datetime,hashlib,json,pathlib,sys
repo=pathlib.Path(sys.argv[1]);output=pathlib.Path(sys.argv[2])
sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit')]
from ck3_live_run_id import current_machine_id
from xar_autoplayer.bridge.prewar_force_coalition_v2_transport import validate_prewar_force_coalition_v2_execution_receipt,prewar_force_coalition_v2_history_summary,STEP,DOMAIN_KEY
from xar_autoplayer.bridge.prewar_force_coalition_v2_contract import normalize_prewar_force_coalition_v2
from test_ordinary_prewar_force_admission_v2 import _evidence
paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_v2_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_v2_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/tests/unit/test_ordinary_prewar_force_admission_v2.py','ck3_autonomous_player/tests/unit/test_prewar_surrogate_authority_regression.py','tools/ck3_live_run_id.py']
before={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}
snapshot,declaration,domain,envelope=_evidence();request_id=envelope['native_request_id']
snapshot={k:copy.deepcopy(snapshot[k]) for k in ('paused','map_ready','revision','native_revision','date_raw','played_character','diagnostics','declarable_wars')}
result=dict(step=STEP,accepted=True,status='available',private_build=False,read_only=True,advertised=True,domain_key=DOMAIN_KEY,**{DOMAIN_KEY:domain})
frame=dict(type='command_result',protocol_version=1,request_id=request_id,ok=True,execution_receipt=envelope['execution_receipt'],result=result)
base=dict(frame=frame,expected_request_id=request_id,snapshot=snapshot,declaration=declaration)
cases=[]
def edit(path,value):return dict(path=path,value_json=json.dumps(value,ensure_ascii=False,separators=(',',':')))
def remove(path):return dict(path=path,remove=True)
def add(name,edits=(),summary=False):
    data=copy.deepcopy(base)
    for e in edits:
        parent=data
        for key in e['path'][:-1]:parent=parent[key]
        if e.get('remove'):del parent[e['path'][-1]]
        else:parent[e['path'][-1]]=json.loads(e['value_json'])
    untouched=copy.deepcopy(data)
    try:
        receipt,result=validate_prewar_force_coalition_v2_execution_receipt(data['frame'],expected_request_id=data['expected_request_id'])
        expected=dict(accepted=True,receipt=receipt,status=result['status'])
        if summary:
            binding=dict(request_id=data['expected_request_id'],**receipt)
            normalized=normalize_prewar_force_coalition_v2(result[DOMAIN_KEY],snapshot=data['snapshot'],expected_declaration=data['declaration'],expected_request_binding=binding,expected_request_id=data['expected_request_id'])
            if normalized['status']!=result['status']:raise ValueError('outer/domain status mismatch in actual query producer')
            query=dict(result,**{DOMAIN_KEY:normalized},native_request_id=data['expected_request_id'],execution_receipt=receipt)
            expected['summary']=prewar_force_coalition_v2_history_summary(query)
    except ValueError:expected=dict(accepted=False)
    if data!=untouched:raise RuntimeError('original transport pure boundary mutated input')
    cases.append(dict(id=name,summary=summary,edits=list(edits),expected=expected))
add('complete_current_summary',summary=True)
add('partial_envelope_receipt',[edit(['frame','result','status'],'partial')])
add('partial_envelope_body_disagrees',[edit(['frame','result','status'],'partial')],True)
add('body_float_token_preserved',[edit(['frame','result',DOMAIN_KEY,'schema_version'],2.0)])
add('body_null_receipt_only',[edit(['frame','result',DOMAIN_KEY],None)])
add('body_null_cannot_summarize',[edit(['frame','result',DOMAIN_KEY],None)],True)
for path,value in [(['type'],'other'),(['protocol_version'],True),(['protocol_version'],1.0),(['protocol_version'],2),(['request_id'],'another'),(['ok'],False),(['ok'],1),(['execution_receipt'],None),(['execution_receipt','ticket'],True),(['execution_receipt','ticket'],13.0),(['execution_receipt','ticket'],0),(['execution_receipt','ticket'],-1),(['execution_receipt','ticket'],1<<64),(['execution_receipt','ticket'],14),(['execution_receipt','query_sequence'],14),(['execution_receipt','capture_epoch'],0),(['execution_receipt','capture_epoch'],17.0),(['execution_receipt','extra'],0),(['result','step'],'wrong'),(['result','accepted'],False),(['result','accepted'],1),(['result','status'],'available_partial'),(['result','status'],True),(['result','private_build'],True),(['result','private_build'],0),(['result','read_only'],False),(['result','advertised'],False),(['result','domain_key'],'wrong'),(['result','extra'],0),(['extra'],0)]:
    add('reject_'+'.'.join(map(str,path))+'_'+str(len(cases)),[edit(['frame']+path,value)])
for key in list(frame):add('missing_top_'+key,[remove(['frame',key])])
for key in list(result):add('missing_result_'+key,[remove(['frame','result',key])])
for key in list(frame['execution_receipt']):add('missing_receipt_'+key,[remove(['frame','execution_receipt',key])])
add('empty_expected_request_id',[edit(['expected_request_id'],''),edit(['frame','request_id'],'')])
add('whitespace_request_allowed_by_top_contract',[edit(['expected_request_id'],' '),edit(['frame','request_id'],' ')])
for value in [1,(1<<64)-1]:
    add('exact_uint64_receipt_'+str(value),[edit(['frame','execution_receipt','ticket'],value),edit(['frame','execution_receipt','query_sequence'],value),edit(['frame','execution_receipt','capture_epoch'],value)])
partial=[edit(['frame','result','status'],'partial'),edit(['frame','result',DOMAIN_KEY,'status'],'partial'),edit(['frame','result',DOMAIN_KEY,'owner_forces',1,'inventory_upper_ready'],False),edit(['frame','result',DOMAIN_KEY,'owner_forces',1,'inventory_upper_soldiers'],None),edit(['frame','result',DOMAIN_KEY,'owner_forces',1,'unavailable_reasons'],['unknown_enemy']),edit(['frame','result',DOMAIN_KEY,'enemy_upper_soldiers'],None),edit(['frame','result',DOMAIN_KEY,'enemy_force_coverage_complete'],False),edit(['frame','result',DOMAIN_KEY,'missing_required_domains'],['enemy_current_inventory_upper'])]
add('partial_current_summary',partial,True)
add('summary_wrong_independent_receipt',[edit(['frame','execution_receipt','capture_epoch'],18)],True)
add('summary_stale_snapshot',[edit(['snapshot','native_revision'],2)],True)
refs=[]
for p in paths:
    raw=(repo/p).read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=before[p]:raise RuntimeError('source changed during capture: '+p)
    refs.append(dict(path=p,bytes=len(raw),sha256=digest))
data=dict(schema='xar.coalitionreceipt.original-producer-golden/v1',machine_id=current_machine_id(),observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=refs,input_refs=[],scope='projection_not_original; real unchanged TOP receipt validator, V2 normalizer and history summary; synthetic endpoint data from existing fixture; no native send/Game/cache writer/ledger qualification',base=base,cases=cases)
raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
if len(raw)>51200:raise RuntimeError('receipt golden exceeds 50KiB')
with output.open('xb') as handle:handle.write(raw)
print(json.dumps(dict(machine_id=data['machine_id'],observed_at_utc=data['observed_at_utc'],cases=len(cases),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
""";
}
