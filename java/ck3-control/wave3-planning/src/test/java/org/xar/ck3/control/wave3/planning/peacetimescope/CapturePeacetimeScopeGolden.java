package org.xar.ck3.control.wave3.planning.peacetimescope;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** Explicit unchanged-producer capture submitted to the shared execution owner. Not a default test dependency. */
public final class CapturePeacetimeScopeGolden {
    private CapturePeacetimeScopeGolden() { }
    private static final int MAXIMUM_BYTES = 98304;
    private static final String SCRIPT = """
import sys,json,hashlib,datetime,copy,types
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
from xar_autoplayer.m5_peacetime_proposal_sources_v1 import _require_peaceful_frame,_snapshot_gold,_require_driver_frame
from test_m5_peacetime_proposal_sources_v1 import _snapshot
sentinel=object();cases=[];corrections=[]
def capture(name,before=None,current=sentinel,kind='returned',revision=701,correction=False):
 before=copy.deepcopy(_snapshot() if before is None else before)
 if current is sentinel:current=copy.deepcopy(before)
 reader={'kind':kind}
 if kind=='returned':reader['snapshot']=current
 item=dict(name=name,input=dict(schema='xar.java.m5-peacetime-scope.v1',before=before,expected_revision=revision,reader=reader))
 try:
  frame=_require_peaceful_frame(before,expected_revision=revision);gold=_snapshot_gold(before)
  driver=types.SimpleNamespace()
  if kind=='returned':driver.take_internal_semantic_snapshot=lambda:copy.deepcopy(current)
  _require_driver_frame(driver,frame,expected_gold_raw=gold)
  item['original_accepted']=True;item['expected']=dict(frame=frame,observed_gold_raw=gold)
 except Exception as error:item['original_accepted']=False;item['original_error_type']=type(error).__name__;item['original_error']=str(error)
 if correction:item['java_expected_accepted']=False;item['correction']='Consumed identity/scale must be an integer token; original Python equality accepted a float or boolean alias.'
 (corrections if correction else cases).append(item)
# The actual existing producer fixture controls the revision; no invented GREEN frame is supplied.
base=_snapshot();revision=base['revision']
def run(name,before=None,current=sentinel,kind='returned',correction=False):capture(name,before,current,kind,revision,correction)
run('stable-two-observations')
b=_snapshot();b['played_character_gold']['raw']=0;run('zero-observed-wallet',b)
for key in ['active_event','pending_character_interaction','one_life_terminal_reason']:
 b=_snapshot();b.pop(key);run('missing-clear-'+key,b)
b=_snapshot();b['played_character_id']=None;run('null-top-player-uses-original-nested-identity',b)
b=_snapshot();b.pop('played_character_id');run('missing-top-player-uses-original-nested-identity',b)
b=_snapshot();b['native_revision']=9007199254740997;b['snapshot_id']='native:'+str(b['native_revision']);b['date_raw']=9007199254740995;run('large-exact-frame-integers',b)
for key,value in [('paused',False),('map_ready',False),('active_event',{}),('pending_character_interaction',{'id':1}),('one_life_terminal_reason','dead'),('active_wars',None),('active_wars',[{'war_id':7}]),('player_armies',[{'army_id':0}]),('snapshot_id','native:999')]:
 b=_snapshot();b[key]=value;run('initial-reject-'+key+'-'+str(value),b)
for key in ['active_wars','player_armies']:
 b=_snapshot();b.pop(key);run('missing-is-not-empty-'+key,b)
b=_snapshot();b['played_character']['alive']=False;run('actor-is-not-alive',b)
b=_snapshot();b['played_character']['character_id']+=1;run('nested-actor-conflict',b)
b=_snapshot();b['played_character_gold']=None;run('null-wallet',b)
b=_snapshot();b.pop('played_character_gold');run('missing-wallet',b)
b=_snapshot();b['played_character_gold']['raw']=-1;run('negative-wallet',b)
b=_snapshot();b['played_character_gold']['scale']=10000;run('wrong-wallet-scale',b)
run('missing-internal-reader',kind='unavailable')
run('null-internal-result',current=None)
run('list-internal-result',current=[])
for key,value in [('date_raw',base['date_raw']+24),('episode_run_id','foreign-episode'),('revision',revision+1)]:
 c=_snapshot();c[key]=value;run('current-drift-'+key,current=c)
c=_snapshot();c['played_character_id']+=1;c['played_character']['character_id']+=1;run('current-actor-drift',current=c)
c=_snapshot();c['native_revision']+=1;c['snapshot_id']='native:'+str(c['native_revision']);run('current-native-stamp-drift',current=c)
c=_snapshot();c['played_character_gold']['raw']-=1;run('same-frame-wallet-changed',current=c)
c=_snapshot();c['paused']=False;run('current-unpaused',current=c)
capture('zero-planning-revision',revision=0)
capture('boolean-planning-revision',revision=True)
b=_snapshot();b['played_character_gold']['scale']=100000.0;run('float-scale-alias',b,correction=True)
b=_snapshot();b['played_character']['character_id']=float(b['played_character_id']);run('float-nested-identity-alias',b,correction=True)
b=_snapshot();b['played_character_id']=1;b['played_character']['character_id']=True;run('boolean-nested-identity-alias',b,correction=True)
refs=[]
for relative in ['ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py']:
 raw=(root/relative).read_bytes();refs.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
out=dict(schema='xar.ck3.java-peacetime-scope.original-producer-golden.v1',machine_id='xenoamess-full-tower-eb9d2c1186',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_scope='Actual unchanged peaceful-frame, gold and driver-frame helpers executed on the existing synthetic producer fixture and explicit mutations. The driver adapter returns these observations without Game/native I/O. This is pure observation validation, not a real reader, native legality, Game qualification or saved progress.',sources=refs,cases=cases,contract_corrections=corrections)
sys.stdout.buffer.write(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode())
""";
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository, existing Python, new output required"); }
        Path output = Path.of(args[2]); if (Files.exists(output)) { throw new IOException("new output required"); }
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-c", SCRIPT, args[0]);
        builder.directory(Path.of(args[0]).toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process process = builder.start();
        CompletableFuture<byte[]> read = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(MAXIMUM_BYTES + 1); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        });
        if (!process.waitFor(60, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original helper capture timeout"); }
        byte[] raw = read.get(10, TimeUnit.SECONDS);
        if (process.exitValue() != 0 || raw.length == 0 || raw.length > MAXIMUM_BYTES) { throw new IOException("original capture failed or exceeded allowance"); }
        Files.write(output, raw, StandardOpenOption.CREATE_NEW); System.out.println("Captured original peaceful-frame helpers: " + raw.length + " bytes");
    }
}
