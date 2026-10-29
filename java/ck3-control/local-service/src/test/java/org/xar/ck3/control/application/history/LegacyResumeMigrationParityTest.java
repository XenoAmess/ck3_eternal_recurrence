package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.LegacyResumeMigration.*;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.Loaded;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Independent actual Python methods versus the sole Java migration producer. No real Driver, Game,
 * writer, profile, bridge or provider is constructed; private source/cold admission remains a separate Root test. */
final class LegacyResumeMigrationParityTest {
    @TempDir Path directory;
    private static final String PIPE="software-legacy-migration",SHA="a".repeat(64);
    private record Case(String name,Obj payload,BigInteger pid,SuccessionLifecycleBinding lifecycle,
            SaveDirectoryState save,Optional<Obj> snapshot,Optional<ManagedQueueData> queue) {
        Request request(){return new Request(loaded(payload),pid,lifecycle,save,snapshot,queue);}
        Obj toJson(){return new Obj(Map.of("name",new Text(name),"payload",payload,"pid",new IntegerValue(pid),
                "lifecycle",lifecycleJson(lifecycle),"save_configured",new Bool(save==SaveDirectoryState.CONFIGURED),
                "snapshot",snapshot.<Value>map(x->x).orElse(Nil.INSTANCE),"queue",queue.<Value>map(q->new Text(q.status().name().toLowerCase())).orElse(Nil.INSTANCE)));}
    }
    private static final String ORIGINAL="""
        import copy,hashlib,json,pathlib,sys,threading,types
        sys.dont_write_bytecode=True
        root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
        from xar_autoplayer.bridge import native_driver as n
        request=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
        out=[];cls=n.NativeHeadlessGameplayDriver
        for c in request['cases']:
            source=n.load_native_driver_state_for_resume_payload(c['payload'],request['pipe'])
            assert source is not None
            d=types.SimpleNamespace(_driver_state_lock=threading.RLock(),_session_bridge_pid=None,
                _succession_lifecycle=c['lifecycle'],_driver_state_wal_replay_status='base_only',
                _episode_transition=None,save_dir=pathlib.Path('software-unused-save') if c['save_configured'] else None)
            d._read_driver_state=lambda:copy.deepcopy(source)
            d._invalidate_player_heir_provider_v1=lambda reason:None
            d._persist_driver_state=lambda **kw:None
            d._managed_restore_request_state=lambda transaction:c['queue']
            for name in ('_upgrade_checkpoint_anchor','_matching_checkpoint_history_index','_cold_candidate_ready'):
                setattr(d,name,types.MethodType(getattr(cls,name),d))
            try:
                cls._adopt_bridge_session(d,c['pid'])
            except n._NativeBridgeAdoptionRefusedError as failure:
                row={'name':c['name'],'outcome':'rejected','reason':failure.reason}
            else:
                crossed=isinstance(source.get('managed_restore_transaction'),dict) and (
                    source['managed_restore_transaction'].get('replacement_bridge_pid')==c['pid'] or
                    source['managed_restore_transaction'].get('source_bridge_pid')!=c['pid'])
                if source['bridge_pid']!=c['pid'] or crossed:
                    row={'name':c['name'],'outcome':'cold','payload':source,'anchor_ready':d._cold_candidate_ready(source)}
                else:
                    if c['snapshot'] is not None:cls._migrate_legacy_rollback_war_failures(d,c['snapshot'])
                    expected=copy.deepcopy(source)
                    expected.update(format_version=2,bridge_pid=c['pid'],command_history=d._command_history,
                        episode_character_id=d._episode_character_id,episode_run_id=d._episode_run_id,
                        last_checkpoint=d._last_checkpoint,rollback_war_failures=d._rollback_war_failures,
                        rollback_war_failure=d._rollback_war_failures[0] if d._rollback_war_failures else None,
                        rollback_war_failures_migration_required=d._rollback_war_failures_migration_required,
                        managed_restore_transaction=d._managed_restore_transaction,
                        succession_lifecycle=d._succession_lifecycle,succession_lifecycle_migration_required=False)
                    row={'name':c['name'],'outcome':'same','payload':expected,'anchor_ready':d._cold_candidate_ready(expected)}
            if row['outcome']!='rejected':
                document=row['payload'];cp=document.get('last_checkpoint')
                row['retained']=n._checkpoint_history_with_restore_lineage(cp,document['command_history'])
                if c['snapshot'] is not None:
                    row['current_failure']=n._derive_rollback_war_failure(document['command_history'],checkpoint=cp,
                        restored_snapshot=c['snapshot'],episode_run_id=document['episode_run_id'],completed_restore_epoch_limit=2)
            out.append(row)
        source=root/'ck3_autonomous_player'/'src'/'xar_autoplayer'/'bridge'/'native_driver.py'
        pathlib.Path(sys.argv[3]).write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':out},ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
        """;

    @Test void actualOriginalAdoptionAnchorOrphanLifecycleAndFirstMapMigrationAgreeAcrossFullDocuments()throws Exception {
        List<Case> cases=cases();Obj result=original(cases);
        List<Value> rows=((Arr)result.get("cases")).items();assertEquals(cases.size(),rows.size());
        for(int i=0;i<cases.size();i++) {
            Case c=cases.get(i);Obj expected=(Obj)rows.get(i);assertEquals(new Text(c.name()),expected.get("name"));
            Plan plan=LegacyResumeMigration.resolve(c.request());String outcome=((Text)expected.get("outcome")).value();
            if(outcome.equals("rejected")) {
                Rejected rejected=assertInstanceOf(Rejected.class,plan,c.name());
                assertEquals(((Text)expected.get("reason")).value(),rejected.reason().name().toLowerCase(),c.name());continue;
            }
            Obj actual;
            if(outcome.equals("cold")) {
                PendingColdData cold=assertInstanceOf(PendingColdData.class,plan,c.name());actual=cold.candidate();
                assertEquals(expected.get("anchor_ready"),new Bool(cold.anchorReady()),c.name());
            }else if(plan instanceof RequiredBinding unbound)actual=unbound.normalizedPayload();
            else {
                SamePidData same=assertInstanceOf(SamePidData.class,plan,c.name());actual=same.normalizedPayload();
                assertEquals(expected.get("anchor_ready"),new Bool(same.anchorReady()),c.name());
                if(same.pending().isEmpty()) {
                    Obj modern=same.modernDriverPayload();assertEquals(new Text(PIPE),modern.get("pipe_name"));
                    assertFalse(modern.members().containsKey("rollback_war_failures_migration_required"));
                }else assertThrows(IllegalStateException.class,same::modernDriverPayload,c.name());
            }
            if(actual.get("last_checkpoint") instanceof Obj saved) {
                var retained=DriverHistoryProjection.retain(saved,objects((Arr)actual.get("command_history")));
                if(expected.get("retained")==Nil.INSTANCE)assertInstanceOf(DriverHistoryProjection.Unavailable.class,retained,c.name());
                else assertEquals(expected.get("retained"),new Arr(new ArrayList<Value>(assertInstanceOf(DriverHistoryProjection.Available.class,retained,c.name()).rows())),c.name()+" actual restore-lineage DATA");
                if(c.snapshot().isPresent()) {
                    String run=actual.get("episode_run_id") instanceof Text id?id.value():null;
                    var failure=RollbackWarFailures.deriveCurrentLegacyDriverFailure(objects((Arr)actual.get("command_history")),saved,c.snapshot().orElseThrow(),run,Optional.empty(),2);
                    assertEquals(expected.get("current_failure"),failure.<Value>map(x->x).orElse(Nil.INSTANCE),c.name()+" actual current/completed rollback DATA");
                }
            }
            assertEquals(DriverJson.toNode(expected.get("payload")),DriverJson.toNode(actual),c.name());
            assertEquals(actual,DriverJson.object(DriverJson.encode(actual),4<<20),c.name()+" JSON type-domain roundtrip");
        }
    }

    @Test void unobservedOrUnavailableQueueCannotDisarmOriginalAndExactRequestMustMatch() {
        Loaded actual=loaded(managed(Nil.INSTANCE));Request request=new Request(actual,bi(42),rogue(),SaveDirectoryState.CONFIGURED,Optional.empty(),Optional.empty());
        NeedsManagedQueue waiting=assertInstanceOf(NeedsManagedQueue.class,LegacyResumeMigration.resolve(request));
        assertEquals("restore-original",waiting.requestId());assertEquals(actual.normalizedPayload(),waiting.normalizedPayload());
        assertInstanceOf(NeedsManagedQueue.class,LegacyResumeMigration.withManagedQueue(waiting,new ManagedQueueData("restore-original",QueueStatus.UNAVAILABLE)));
        Rejected mismatch=assertInstanceOf(Rejected.class,LegacyResumeMigration.withManagedQueue(waiting,new ManagedQueueData("other-request",QueueStatus.MISSING)));
        assertEquals(Reason.QUEUE_OBSERVATION_MISMATCH,mismatch.reason());
        SamePidData present=assertInstanceOf(SamePidData.class,LegacyResumeMigration.withManagedQueue(waiting,new ManagedQueueData("restore-original",QueueStatus.PRESENT)));
        assertFalse(present.transactionDisarmed());assertTrue(present.pending().contains(Pending.MANAGED_RESTORE_REQUEST));
        assertThrows(IllegalStateException.class,present::modernDriverPayload);
        SamePidData missing=assertInstanceOf(SamePidData.class,LegacyResumeMigration.withManagedQueue(waiting,new ManagedQueueData("restore-original",QueueStatus.MISSING)));
        assertTrue(missing.transactionDisarmed());assertSame(Nil.INSTANCE,missing.normalizedPayload().get("managed_restore_transaction"));
    }

    @Test void explicitRootBindingPreservesUnboundHistoryAndNeverRetroactivelyUpgradesItsCheckpointOrMintsIdentity() {
        Obj old=anchored().with("format_version",number(1)).with("episode_character_id",Nil.INSTANCE).with("episode_run_id",Nil.INSTANCE)
                .with("last_checkpoint",checkpoint().with("history_index",Nil.INSTANCE));
        Request request=new Request(loaded(old),bi(42),rogue(),SaveDirectoryState.CONFIGURED,Optional.of(snapshot()),Optional.empty());
        RequiredBinding waiting=assertInstanceOf(RequiredBinding.class,LegacyResumeMigration.resolve(request));
        assertEquals(bi(7),waiting.actualCharacterId());assertEquals(loaded(old).commandHistory(),objects((Arr)waiting.normalizedPayload().get("command_history")));
        assertThrows(IllegalArgumentException.class,()->LegacyResumeMigration.bind(waiting,new BindingIdentity(bi(8),"root-once")));
        SamePidData bound=assertInstanceOf(SamePidData.class,LegacyResumeMigration.bind(waiting,new BindingIdentity(bi(7),"root-once")));
        assertEquals(new Text("root-once"),bound.normalizedPayload().get("episode_run_id"));
        assertEquals(old.get("last_checkpoint"),bound.normalizedPayload().get("last_checkpoint"),"the actual old upgrade occurred before unbound first-map identity assignment");
        assertEquals(old.get("command_history"),bound.normalizedPayload().get("command_history"));assertFalse(bound.anchorReady());
        assertEquals(bound.normalizedPayload(),DriverJson.object(DriverJson.encode(bound.normalizedPayload()),4<<20));
        assertFalse(bound.modernDriverPayload().members().containsKey("succession_lifecycle_migration_required"));
        assertThrows(IllegalArgumentException.class,()->new BindingIdentity(bi(0),"invalid"));
    }

    @Test void sharedAnchorAndRollbackHistoryProducersRetainExistingTypedBoundariesAndExactDataTypes() {
        Obj cp=checkpoint().with("history_index",new DecimalValue("1.0"));List<Obj> history=objects((Arr)anchored().get("command_history"));
        Obj upgraded=DriverHistoryProjection.upgradeCheckpointAnchor(cp,history,bi(7),"e");
        assertEquals(number(1),upgraded.get("history_index"));assertEquals(number(7),upgraded.get("episode_character_id"));
        Obj wrong=checkpoint().with("history_index",number(2));List<Obj> extended=new ArrayList<>(history);extended.add(row(2,"original-unknown",Nil.INSTANCE).with("ok",new Bool(false)).with("error",new Text("UNKNOWN")));
        assertEquals(number(2),DriverHistoryProjection.upgradeCheckpointAnchor(wrong,extended,bi(7),"e").get("history_index"));
        assertTrue(DriverHistoryProjection.checkpointHistoryIndex(wrong,extended).isEmpty(),"hot index attachment never grants a physical/cold anchor");
        Obj corrupted=snapshot().with("map_ready",number(1));
        Rejected bad=assertInstanceOf(Rejected.class,LegacyResumeMigration.resolve(new Request(loaded(anchored()),bi(42),rogue(),SaveDirectoryState.CONFIGURED,Optional.of(corrupted),Optional.empty())));
        assertEquals(Reason.MALFORMED_INPUT,bad.reason());
        assertThrows(IllegalArgumentException.class,()->new Request(assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(anchored(),PIPE,LegacyResumeNormalizer.HistoryMaterialization.OMIT)),bi(42),rogue(),SaveDirectoryState.CONFIGURED,Optional.empty(),Optional.empty()));
        Obj wide=epochs().with("last_checkpoint",checkpoint().with("episode_character_id",number(7)).with("episode_run_id",new Text("e")));
        List<Obj> epochRows=objects((Arr)wide.get("command_history"));
        List<Obj> completed=RollbackWarFailures.deriveCompletedLegacyDriverFailures(epochRows,(Obj)wide.get("last_checkpoint"),snapshot(),"e",2);
        assertFalse(completed.isEmpty());assertEquals(completed.getFirst(),RollbackWarFailures.deriveCurrentLegacyDriverFailure(epochRows,(Obj)wide.get("last_checkpoint"),snapshot(),"e",Optional.empty(),2).orElseThrow());
    }

    private Obj original(List<Case> cases)throws Exception {
        String configured=System.getProperty("xar.repository.root");assertNotNull(configured,"required canonical xar.repository.root; no skip");assertFalse(configured.isBlank());
        Path repository=Path.of(configured).toRealPath(),production=repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py");
        assertTrue(Files.isRegularFile(production));String python=System.getProperty("xar.python");assertNotNull(python,"required canonical xar.python; no skip");
        assertFalse(python.isBlank());assertTrue(Path.of(python).isAbsolute());
        Path input=directory.resolve("migration-input.json"),output=directory.resolve("migration-original.json"),log=directory.resolve("migration-original.log");
        Files.write(input,DriverJson.encode(new Obj(Map.of("pipe",new Text(PIPE),"cases",new Arr(cases.stream().<Value>map(Case::toJson).toList())))));
        ProcessBuilder command=new ProcessBuilder(python,"-B","-c",ORIGINAL,repository.toString(),input.toString(),output.toString()).directory(repository.toFile()).redirectErrorStream(true).redirectOutput(log.toFile());
        // Set every fixture environment before importing modules that freeze repository/cache paths.
        command.environment().put("PYTHONPATH",repository.resolve("ck3_autonomous_player/src").toString());command.environment().put("XAR_SOURCE_REPOSITORY",repository.toString());
        command.environment().put("PYTHONDONTWRITEBYTECODE","1");command.environment().put("PYTHONUTF8","1");command.environment().put("PYTHONPYCACHEPREFIX",directory.resolve("unwritten-cache").toString());
        Process process=command.start();process.getOutputStream().close();boolean exited=process.waitFor(Duration.ofSeconds(60).toMillis(),TimeUnit.MILLISECONDS);
        if(!exited){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);fail("actual original migration process timed out");}
        assertEquals(0,process.exitValue(),()->"actual original migration process failed: "+readLog(log));
        Obj result=DriverJson.object(Files.readAllBytes(output),4<<20);assertEquals(new Text(DriverJson.sha256(Files.readAllBytes(production))),result.get("source_sha256"));return result;
    }

    private static List<Case> cases() {
        var out=new ArrayList<Case>();
        out.add(test("same-pid-lifecycle-missing",base(),42,rogue(),null,null));
        out.add(test("explicit-UNKNOWN-preserved",base().with("succession_lifecycle",lifecycleJson(SuccessionLifecycleBinding.unknown())),42,SuccessionLifecycleBinding.unknown(),null,null));
        out.add(test("legacy-profile-incompatible",base(),42,SuccessionLifecycleBinding.unknown(),null,null));
        out.add(test("persisted-profile-mismatch",base().with("succession_lifecycle",lifecycleJson(rogue())),42,SuccessionLifecycleBinding.unknown(),null,null));
        out.add(test("anchor-repair-from-SAVE",anchored().with("last_checkpoint",checkpoint().with("history_index",Nil.INSTANCE)),42,rogue(),null,null));
        Obj duplicate=anchored().with("command_history",new Arr(List.of(row(1,"save-checkpoint",new Obj(Map.of("checkpoint",checkpoint()))),row(2,"restore-phase2-span-source-checkpoint-v1",new Obj(Map.of("checkpoint",checkpoint()))))));
        out.add(test("anchor-reverse-last-matching",duplicate.with("last_checkpoint",checkpoint().with("history_index",new Bool(true))),42,rogue(),null,null));
        Obj unknown=row(2,"old-unknown-result",Nil.INSTANCE).with("ok",new Bool(false)).with("error",new Text("UNKNOWN")).with("source_extension",new Arr(List.of(Nil.INSTANCE,new DecimalValue("1.2500"))));
        Obj extended=anchored().with("command_history",new Arr(List.of(row(1,"save-checkpoint",new Obj(Map.of("checkpoint",checkpoint()))),unknown)));
        out.add(test("valid-index-stays-even-wrong-anchor",extended.with("last_checkpoint",checkpoint().with("history_index",number(2))),42,rogue(),null,null));
        out.add(test("no-matching-anchor-stays-original",extended.with("last_checkpoint",checkpoint().with("sha256",new Text("b".repeat(64))).with("history_index",Nil.INSTANCE)),42,rogue(),null,null));
        for(QueueStatus q:List.of(QueueStatus.MISSING,QueueStatus.FAILED,QueueStatus.PRESENT))out.add(test("actual-orphan-"+q.name(),managed(Nil.INSTANCE),42,rogue(),null,q));
        out.add(test("same-pid-managed-crossed-is-cold",managed(number(43)),43,rogue(),null,null));
        out.add(test("different-pid-complete-cold-anchor",anchoredWithEpisode(),43,rogue(),null,null));
        out.add(test("different-pid-unanchored-no-fallback",base(),43,rogue(),null,null));
        out.add(new Case("cold-save-directory-absent",anchoredWithEpisode(),bi(43),rogue(),SaveDirectoryState.ABSENT,Optional.empty(),Optional.empty()));
        out.add(test("v1-no-cold-barrier",anchoredWithEpisode().with("format_version",number(1)),43,rogue(),null,null));
        Obj restart=new Obj(Map.of("step",new Text("restore-checkpoint"),"accepted",new Bool(true),"status",new Text("restored"),"backend_id",new Text("native-headless"),"source",new Text("native-session-cold-start"),"restored_date_raw",number(24000),"map_ready",new Bool(true),"checkpoint",checkpoint(),"lifecycle",new Obj(Map.of("previous_pid",number(41),"pid",number(42)))));
        Obj lineage=extended.with("command_history",new Arr(List.of(row(1,"save-checkpoint",new Obj(Map.of("checkpoint",checkpoint()))),unknown,row(3,"restore-checkpoint",restart),row(4,"old-gameplay",Nil.INSTANCE))));
        out.add(test("real-cold-lineage-retains-only-physical-restarts",lineage,42,rogue(),snapshot(),null));
        var ongoingRows=new ArrayList<Value>(((Arr)epochs().get("command_history")).items().subList(0,6));
        ongoingRows.add(row(7,"unknown-branch-original",Nil.INSTANCE).with("ok",new Bool(false)).with("error",new Text("UNKNOWN")));
        out.add(test("actual-current-epoch-before-completed-fallback",epochs().with("command_history",new Arr(ongoingRows)),42,rogue(),snapshot(),null));
        out.add(test("first-map-real-completed-rollback-migration",epochs(),42,rogue(),snapshot(),null));
        out.add(test("not-playable-preserves-migration",epochs(),42,rogue(),snapshot().with("map_ready",new Bool(false)),null));
        out.add(test("no-snapshot-preserves-migration",epochs(),42,rogue(),null,null));
        out.add(test("unbound-first-map-keeps-history",extended.with("format_version",number(1)).with("episode_character_id",Nil.INSTANCE).with("episode_run_id",Nil.INSTANCE),42,rogue(),snapshot(),null));
        return List.copyOf(out);
    }
    private static Case test(String name,Obj payload,long pid,SuccessionLifecycleBinding lifecycle,Obj snapshot,QueueStatus queue) {
        return new Case(name,payload,bi(pid),lifecycle,SaveDirectoryState.CONFIGURED,Optional.ofNullable(snapshot),
                queue==null?Optional.empty():Optional.of(new ManagedQueueData("restore-original",queue)));
    }
    private static Obj base(){return json("{\"format_version\":2,\"pipe_name\":\""+PIPE+"\",\"bridge_pid\":42,\"episode_character_id\":7,\"episode_run_id\":\"e\",\"command_history\":[],\"last_checkpoint\":null}");}
    private static Obj checkpoint(){return json("{\"name\":\"xar_checkpoint.ck3\",\"sha256\":\""+SHA+"\",\"size\":17,\"date_raw\":24000,\"history_index\":1,\"old_extension\":[null,{},1.25]}");}
    private static Obj anchored(){return base().with("last_checkpoint",checkpoint()).with("command_history",new Arr(List.of(row(1,"save-checkpoint",new Obj(Map.of("checkpoint",checkpoint()))))));}
    private static Obj anchoredWithEpisode(){return anchored().with("last_checkpoint",checkpoint().with("episode_character_id",number(7)).with("episode_run_id",new Text("e")));}
    private static Obj managed(Value replacement) {
        Obj tx=json("{\"status\":\"awaiting_checkpoint_rebind\",\"request_id\":\"restore-original\",\"source_bridge_pid\":42,\"checkpoint_sha256\":\""+SHA+"\",\"checkpoint_size\":17,\"checkpoint_date_raw\":24000,\"history_index\":1,\"episode_character_id\":7,\"episode_run_id\":\"e\",\"original_extension\":[null,{}]}").with("replacement_bridge_pid",replacement);
        return anchoredWithEpisode().with("bridge_pid",replacement==Nil.INSTANCE?number(42):replacement).with("managed_restore_transaction",tx);
    }
    private static Obj epochs() {
        List<Value> rows=new ArrayList<>();rows.add(row(1,"save-checkpoint",new Obj(Map.of("checkpoint",checkpoint()))));
        for(int target:List.of(52,54)) {
            rows.add(row(rows.size()+1,"preview-move-army-304-to-"+target,json("{\"route_preview\":{\"status\":\"available\",\"army_id\":304,\"origin_province_id\":48,\"target_province_id\":"+target+",\"route_province_ids\":[50,"+target+"],\"previewed_date_raw\":24000}}")));
            rows.add(row(rows.size()+1,"move-army-304-to-"+target,json("{\"war_action\":{\"status\":\"moving\",\"army_id\":304,\"target_province_id\":"+target+",\"submitted_date_raw\":24000},\"player_armies\":[{\"army_id\":304,\"move_target_province_id\":"+target+",\"route_province_ids\":["+target+"]}]}")));
            rows.add(row(rows.size()+1,"restore-checkpoint",new Obj(Map.of("status",new Text("restored")))));
        }
        rows.add(row(rows.size()+1,"unknown-failed-original",Nil.INSTANCE).with("ok",new Bool(false)).with("error",new Text("UNKNOWN")));
        return base().with("last_checkpoint",checkpoint()).with("command_history",new Arr(rows));
    }
    private static Obj snapshot(){return json("{\"map_ready\":true,\"date_raw\":24000,\"played_character\":{\"character_id\":7},\"player_armies\":[{\"army_id\":304,\"current_province_id\":48}],\"active_wars\":[{\"war_id\":1208925819614629174706176,\"allied_armies\":[{\"army_id\":304,\"controllable\":true}]}]}");}
    private static Obj row(int index,String command,Value result){return new Obj(Map.of("index",number(index),"command",new Text(command),"ok",new Bool(true),"result",result));}
    private static Loaded loaded(Obj raw){return assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(raw,PIPE));}
    private static SuccessionLifecycleBinding rogue(){return SuccessionLifecycleBinding.legacyRogue();}
    private static Obj lifecycleJson(SuccessionLifecycleBinding lifecycle){return DriverJson.object(SuccessionLifecycleCodec.encode(lifecycle),SuccessionLifecycleCodec.MAX_BYTES);}
    private static List<Obj> objects(Arr rows){return rows.items().stream().map(x->assertInstanceOf(Obj.class,x)).toList();}
    private static BigInteger bi(long n){return BigInteger.valueOf(n);}
    private static IntegerValue number(long n){return new IntegerValue(bi(n));}
    private static Obj json(String raw){return DriverJson.object(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8),4<<20);}
    private static String readLog(Path path){try{byte[] body=Files.readAllBytes(path);return new String(body,0,Math.min(body.length,65536),java.nio.charset.StandardCharsets.UTF_8);}catch(java.io.IOException failure){return failure.toString();}}
}
