package org.xar.ck3.control.wave2.finance.giftpendingframe;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Captures actual old wait-gate producer and its actual read-only proof consumer using existing fixtures. */
public final class CaptureGiftPendingFrameGolden {
    private CaptureGiftPendingFrameGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repository existing-python new-scratch output-json"); }
        Path root = Path.of(args[0]).toRealPath(); Path scratch = Path.of(args[2]).toAbsolutePath().normalize();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (Files.exists(scratch) || Files.exists(output)) { throw new IllegalArgumentException("capture does not overwrite"); }
        Files.createDirectories(scratch);
        Process child = new ProcessBuilder(List.of(args[1], "-B", "-c", SCRIPT, root.toString(), scratch.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = readers.submit(() -> child.getInputStream().readNBytes(65_537));
            if (!child.waitFor(Duration.ofSeconds(60).toMillis(), TimeUnit.MILLISECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); throw new IllegalStateException("capture timeout");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 65_536) { throw new IllegalStateException("capture failed, exit=" + child.exitValue()); }
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original pending wait/proof chain: " + raw.length + " bytes");
    }
    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,runpy,copy,datetime
            from pathlib import Path
            root=Path(sys.argv[1]);scratch=Path(sys.argv[2]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import faction_gift_formal_route_v1 as route
            from xar_autoplayer.bridge.readonly_planning_retry_v1 import classify_readonly_planning_error_v1 as consume
            from xar_autoplayer.faction_gift_pending_v1 import read_faction_gift_ledger_v1
            test=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_faction_gift_formal_route_v1.py'))
            state=scratch/'state';pending=test['pending'](state)
            source=test['snapshot'](revision=413,native_revision=pending['pre_native_snapshot_revision'])
            fresh=test['snapshot'](revision=414,native_revision=pending['pre_native_snapshot_revision']+1)
            cases=[]
            for name in ('ready','actor','date','episode','pid','generation','regressed_native','regressed_public','timeout','event','unpaused','interaction'):
                current=copy.deepcopy(fresh)
                if name=='actor':current['played_character']={'character_id':123,'alive':True}
                elif name=='date':current['date_raw']+=24
                elif name=='episode':current['episode_run_id']='foreign-episode'
                elif name=='pid':current['diagnostics']['bridge_pid']+=1
                elif name=='generation':current['diagnostics']['connection_generation']+=1
                elif name=='regressed_native':current['native_revision']=pending['pre_native_snapshot_revision']-1
                elif name=='regressed_public':current['revision']=source['revision']
                elif name=='timeout':current=copy.deepcopy(source)
                elif name=='event':current['active_event']={'instance_id':1}
                elif name=='unpaused':current['paused']=False
                elif name=='interaction':current['pending_character_interaction']={'instance_id':1}
                driver=test['Driver'](state,copy.deepcopy(source));trace={}
                def wait(start,predicate,*,timeout_seconds):
                    trace.update(predicate_result=predicate(current),timeout_seconds=timeout_seconds)
                    return current
                driver._wait_for_snapshot=wait
                try:route._wait_for_pending_paused_revision_v1(driver,source,pending)
                except route.FactionGiftPendingFrameReadyError as error:
                    expected={'accepted':True,'proof':error.readonly_faction_pending_frame_v1,'consumer':consume(error)}
                except route.BridgeUnavailableError as error:expected={'accepted':False,'error':str(error)}
                else:raise RuntimeError('old wait path did not signal replan or unavailability')
                cases.append({'name':name,'source_snapshot':source,'fresh_snapshot':current,'trace':trace,'expected':expected})
            refs=[]
            for rel in ('ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/readonly_planning_retry_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py','ck3_autonomous_player/tests/unit/test_faction_gift_formal_route_v1.py'):
                raw=(root/rel).read_bytes();refs.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            result={'schema':'xar.giftpendingframe.original-producer-consumer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual old pure wait gate and typed exception proof consumer; existing fixture supplies wait result, no Game transport or runtime qualification.','source_refs':refs,'pending_ledger':read_faction_gift_ledger_v1(state),'cases':cases}
            print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
            """;
}
