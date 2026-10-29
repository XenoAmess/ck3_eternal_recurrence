package org.xar.ck3.control.wave3.planning.constructionrelease;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** Shared-owner actual original helper and complete query-consumer capture. Default tests never launch Python. */
public final class CaptureConstructionReleaseGolden {
    private CaptureConstructionReleaseGolden() { }
    private static final int MAXIMUM_BYTES = 98304;
    private static final String SCRIPT = """
import sys,json,hashlib,datetime,copy,types
from pathlib import Path
from unittest import mock
root=Path(sys.argv[1]);scratch=Path(sys.argv[2])
if scratch.exists():raise ValueError('new bounded fixture root required')
scratch.mkdir(parents=True)
sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.m5_peacetime_proposal_sources_v1 import _prior_construction_blocks_candidate,query_m5_peacetime_proposal_sources_v1
from test_m5_peacetime_proposal_sources_v1 import _snapshot,_history,_construction,_Driver,_FRAME
frame=copy.deepcopy(_FRAME);cases=[];corrections=[];consumers=[]
def receipt():return dict(status='applied',postcondition_verified=True,episode_run_id=frame['episode_run_id'],actor_character_id=frame['played_character_id'],post_bridge_pid=123,post_bridge_creation_date='t1',post_native_revision=frame['native_revision']-1,post_date_raw=frame['date_raw']-24,completion_status='in_progress',completion_last_check_date_raw=frame['date_raw'])
def observation(pid=123,birth='t1'):return dict(kind='observed',pid=pid,creation_date=birth)
def capture(name,applied,process=None,correction=False):
 process=observation() if process is None else process
 kwargs=dict(side_effect=BridgeUnavailableError('identity unavailable')) if process['kind']=='unavailable' else dict(return_value=(process['pid'],process['creation_date']))
 with mock.patch('xar_autoplayer.m5_peacetime_proposal_sources_v1.construction_process_identity',**kwargs) as identity:
  blocked=_prior_construction_blocks_candidate(types.SimpleNamespace(),applied=applied,frame=frame)
 item=dict(name=name,input=dict(schema='xar.java.m5-construction-release.v1',frame=copy.deepcopy(frame),applied=copy.deepcopy(applied),process_observation=copy.deepcopy(process)),expected_blocks_candidate=blocked,original_identity_reads=identity.call_count)
 if correction:item['java_expected_reject']=True;item['correction']='Original Python identity equality accepted a float or boolean alias; Java requires integer tokens.'
 (corrections if correction else cases).append(item);return item
capture('no-applied-receipt',None)
capture('nonmapping-applied-receipt',[])
r=receipt();r['episode_run_id']='foreign-episode';capture('foreign-episode-does-not-read-process',r)
capture('missing-episode-does-not-read-process',{})
capture('later-native-and-date-release',receipt())
capture('process-reader-unavailable-holds',receipt(),dict(kind='unavailable'))
capture('different-process-pid-holds',receipt(),observation(pid=124))
capture('different-opaque-birth-holds',receipt(),observation(birth='t2'))
for key,value in [('status','action_state_unknown'),('postcondition_verified',False),('actor_character_id',frame['played_character_id']+1),('post_native_revision',frame['native_revision']),('post_native_revision',frame['native_revision']+1),('post_date_raw',frame['date_raw']),('post_date_raw',frame['date_raw']+24)]:
 r=receipt();r[key]=value;capture('hold-'+key+'-'+str(value),r)
for key in ['status','postcondition_verified','actor_character_id','post_bridge_pid','post_bridge_creation_date','post_native_revision','post_date_raw']:
 r=receipt();r.pop(key);capture('missing-'+key+'-holds',r)
r=receipt();r['status']=None;r['postcondition_verified']=None;capture('null-status-and-postcondition-hold',r)
r=receipt();r['post_bridge_creation_date']='20261022223000.123456+480';capture('different-spelling-same-process-instant',r,observation(birth='2026-10-22T14:30:00.1234560Z'))
r=receipt();r['post_bridge_creation_date']='2026-10-22T14:30:00.1234561Z';capture('unrepresentable-100ns-is-not-normalized-away',r,observation(birth='20261022223000.123456+480'))
r=receipt();r['actor_character_id']=float(frame['played_character_id']);capture('float-actor-alias',r,correction=True)
r=receipt();r['post_bridge_pid']=True;capture('boolean-pid-alias',r,observation(pid=1),correction=True)
# The whole real query consumer receives the same receipt and existing transport fixtures.
# Its original candidate/ledger/frame checks all execute. Only the native read adapters are fixture boundaries.
for name,applied,process in [('no-receipt-query-keeps-construction',None,observation()),('same-frame-receipt-defers-only-construction',receipt(),observation()),('later-frame-receipt-releases-construction',receipt(),observation()),('unavailable-process-defers-only-construction',receipt(),dict(kind='unavailable'))]:
 if name.startswith('same-frame'):
  applied['post_native_revision']=frame['native_revision'];applied['post_date_raw']=frame['date_raw']
 state=scratch/name;state.mkdir()
 if applied is not None:(state/'construction-formal-pending-v1.json').write_text(json.dumps(dict(schema='xar.ck3.construction_formal_pending_v1',pending=None,applied=applied)),encoding='utf-8')
 driver=_Driver(state)
 kwargs=dict(side_effect=BridgeUnavailableError('identity unavailable')) if process['kind']=='unavailable' else dict(return_value=(process['pid'],process['creation_date']))
 with mock.patch('xar_autoplayer.m5_peacetime_proposal_sources_v1.construction_process_identity',**kwargs),mock.patch('xar_autoplayer.bridge.domain_construction_private_transport_v1._identity',**kwargs),mock.patch('xar_autoplayer.m5_peacetime_proposal_sources_v1.query_construction_private',return_value=_construction()) as construction:
  result=query_m5_peacetime_proposal_sources_v1(driver,snapshot=driver.take_snapshot(),history=_history(),baseline_plan=dict(policy='one-life-turn-v1',phase='peace_growth',selected_step='life-advance'),expected_revision=frame['revision'])
 raw=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()
 consumers.append(dict(name=name,input=dict(schema='xar.java.m5-construction-release.v1',frame=copy.deepcopy(frame),applied=applied,process_observation=process),expected_consumer=dict(domains=list(result['domains']),construction_status=result['producer']['construction_status'],construction_query_calls=construction.call_count,original_full_result_bytes=len(raw),original_full_result_sha256=hashlib.sha256(raw).hexdigest()),projection_not_original=True))
refs=[]
for relative in ['ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py','ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py']:
 raw=(root/relative).read_bytes();refs.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
out=dict(schema='xar.ck3.java-construction-release.original-producer-golden.v1',machine_id='xenoamess-full-tower-eb9d2c1186',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_scope='Actual unchanged helper and whole query_m5_peacetime_proposal_sources_v1 consumer on existing synthetic domain/native-read fixture boundaries. The four consumer projections preserve complete-result SHA/size and original branch calls. No real process, native query, canonical ledger, action, deployment or Game qualification.',sources=refs,cases=cases,contract_corrections=corrections,consumer_cases=consumers)
sys.stdout.buffer.write(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode())
""";
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repository, existing Python, new fixture root, new output required"); }
        Path output = Path.of(args[3]); if (Files.exists(output)) { throw new IOException("new output required"); }
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-", args[0], args[2]);
        builder.directory(Path.of(args[0]).toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        Process process = builder.start();
        CompletableFuture<byte[]> read = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(MAXIMUM_BYTES + 1); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        });
        try (OutputStream stdin = process.getOutputStream()) { stdin.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
        if (!process.waitFor(60, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original construction closure capture timeout"); }
        byte[] raw = read.get(10, TimeUnit.SECONDS);
        if (process.exitValue() != 0 || raw.length == 0 || raw.length > MAXIMUM_BYTES) { throw new IOException("original query consumer failed or exceeded allowance"); }
        Files.write(output, raw, StandardOpenOption.CREATE_NEW); System.out.println("Captured original construction release and query consumer: " + raw.length + " bytes");
    }
}
