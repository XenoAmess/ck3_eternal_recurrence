package org.xar.ck3.control.wave2.planning.rootavailability;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** Shared-owner one-shot capture of the unchanged active planner helper. Never invoked by default JUnit. */
public final class CaptureRootAvailabilityGolden {
    private CaptureRootAvailabilityGolden() { }
    private static final int MAXIMUM_BYTES = 32768;
    private static final String SCRIPT = """
import sys,json,hashlib,datetime,copy
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from xar_autoplayer.m5_formal_proposal_collector import _same_frame_root_returned_unavailable
from xar_autoplayer.lifestyle_formal_consumer import ROOT_QUERY_STEP
snapshot={'native_revision':3,'date_raw':53178264}
def row():
 return dict(command=ROOT_QUERY_STEP,ok=True,result=dict(step=ROOT_QUERY_STEP,accepted=True,status='unavailable',snapshot_revision=3,campaign_root_context=dict(status='unavailable',snapshot_revision=3,date_raw=53178264)))
cases=[]
def capture(name,history):
 result=_same_frame_root_returned_unavailable(snapshot,history)
 index=next((index for index in reversed(range(len(history))) if _same_frame_root_returned_unavailable(snapshot,[history[index]])),None)
 cases.append(dict(name=name,input=dict(snapshot=copy.deepcopy(snapshot),history=history),expected_same_frame_unavailable=result,expected_history_index=index))
capture('empty-history',[])
capture('completed-unavailable-current-frame',[row()])
r=row();r['command']='different-query';capture('other-command',[r])
r=row();r['ok']=False;capture('failed-transport',[r])
r=row();r['ok']=1;capture('integer-is-not-true-transport',[r])
r=row();r['result']['accepted']=False;capture('not-accepted',[r])
r=row();r['result']['accepted']=1;capture('integer-is-not-true-acceptance',[r])
r=row();r['result']['status']='available';capture('available-result-not-unavailable',[r])
r=row();r['result']['campaign_root_context']['status']='available';capture('context-status-different',[r])
r=row();r['result']['snapshot_revision']=4;capture('result-revision-drift',[r])
r=row();r['result']['campaign_root_context']['snapshot_revision']=4;capture('context-revision-drift',[r])
r=row();r['result']['campaign_root_context']['date_raw']+=24;capture('date-drift',[r])
r=row();r['result'].pop('campaign_root_context');capture('missing-context',[r])
r=row();r['result']=None;capture('null-result',[r])
r=row();r.pop('result');capture('missing-result',[r])
r=row();r['result']['status']='available';capture('older-unavailable-survives-later-nonmatching',[row(),r])
r=row();r['result']['snapshot_revision']=4;capture('most-recent-matching-index',[row(),r,row()])
refs=[]
for relative in ['ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/lifestyle_formal_consumer.py','ck3_autonomous_player/tests/unit/test_m5_formal_proposal_collector.py','ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py']:
 raw=(root/relative).read_bytes();refs.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
out=dict(schema='xar.ck3.java-rootavailability.original-producer-golden.v1',machine_id='xenoamess-full-tower-eb9d2c1186',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_scope='Actual original active planner history helper on synthetic completed-read rows; matching index is independently measured by invoking the original helper on each singleton row. No native query or source qualification.',sources=refs,cases=cases)
sys.stdout.buffer.write(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode())
""";
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository, existing Python, new output path required"); }
        Path output = Path.of(args[2]); if (Files.exists(output)) { throw new IOException("new capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-c", SCRIPT, args[0]);
        builder.directory(Path.of(args[0]).toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process process = builder.start();
        CompletableFuture<byte[]> read = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(MAXIMUM_BYTES + 1); }
            catch (IOException error) { throw new java.io.UncheckedIOException(error); }
        });
        if (!process.waitFor(60, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original helper capture timeout"); }
        byte[] raw = read.get(10, TimeUnit.SECONDS);
        if (process.exitValue() != 0 || raw.length == 0 || raw.length > MAXIMUM_BYTES) { throw new IOException("original helper failed or exceeded output allowance"); }
        Files.write(output, raw, StandardOpenOption.CREATE_NEW); System.out.println("Captured original planner history helper: " + raw.length + " bytes");
    }
}
