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
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.*;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual original Python pure consumer -> one Java complete canonical consumer.
 * Required compatibility environment is explicit; missing Python/repository fails, never skips or passes.
 * No Driver, native bridge, Game, writer, provider or persistent profile is constructed. */
final class LegacyResumeNormalizerParityTest {
    @TempDir Path directory;
    private static final String PIPE="software-canonical-resume",SHA="a".repeat(64);
    private record Case(String name,Obj payload,boolean includeHistory) {
        Obj toJson(){return new Obj(Map.of("name",new Text(name),"payload",payload,"include_history",new Bool(includeHistory)));}
    }
    private static final String ORIGINAL="""
        import hashlib,json,pathlib,sys
        sys.dont_write_bytecode=True
        root=pathlib.Path(sys.argv[1])
        sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
        from xar_autoplayer.bridge.native_driver import load_native_driver_state_for_resume_payload
        request=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
        output=[]
        for case in request['cases']:
            try:
                normalized=load_native_driver_state_for_resume_payload(case['payload'],request['pipe'],include_command_history=case['include_history'])
            except ValueError as failure:
                row={'name':case['name'],'outcome':'rejected','error':str(failure)}
            else:
                row={'name':case['name'],'outcome':'ignored'} if normalized is None else {'name':case['name'],'outcome':'loaded','payload':normalized}
            output.append(row)
        source=root/'ck3_autonomous_player'/'src'/'xar_autoplayer'/'bridge'/'native_driver.py'
        pathlib.Path(sys.argv[3]).write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':output},ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
        """;

    @Test void actualOriginalCanonicalConsumerAndJavaAgreeOnFullPayloadHistoryMigrationManagedRestoreLifecycleAndGoals() throws Exception {
        String configured=System.getProperty("xar.repository.root");
        assertNotNull(configured,"required canonical whole-step property xar.repository.root; never skip");
        assertFalse(configured.isBlank(),"canonical original repository property must be nonempty");
        Path repository=Path.of(configured).toRealPath();
        Path original=repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py");
        assertTrue(Files.isRegularFile(original),"actual original production consumer is required");
        List<Case> cases=cases();Path input=directory.resolve("cases.json"),output=directory.resolve("original-results.json"),log=directory.resolve("original-process.log");
        Files.write(input,DriverJson.encode(new Obj(Map.of("pipe",new Text(PIPE),"cases",new Arr(cases.stream().<Value>map(Case::toJson).toList())))));
        String python=System.getProperty("xar.python");assertNotNull(python,"required canonical whole-step property xar.python; never skip");
        assertFalse(python.isBlank());assertTrue(Path.of(python).isAbsolute(),"canonical Python must identify the exact interpreter");
        var command=new ProcessBuilder(python,"-B","-c",ORIGINAL,repository.toString(),input.toString(),output.toString()).directory(repository.toFile()).redirectErrorStream(true).redirectOutput(log.toFile());
        // The canonical properties are the only repository/interpreter inputs; these private process values
        // are derived before importing any module that can freeze paths.
        command.environment().put("PYTHONPATH",repository.resolve("ck3_autonomous_player/src").toString());
        command.environment().put("XAR_SOURCE_REPOSITORY",repository.toString());
        command.environment().put("PYTHONDONTWRITEBYTECODE","1");command.environment().put("PYTHONUTF8","1");
        command.environment().put("PYTHONPYCACHEPREFIX",directory.resolve("unwritten-source-cache").toString());
        Process process=command.start();process.getOutputStream().close();
        boolean exited=process.waitFor(Duration.ofSeconds(60).toMillis(),TimeUnit.MILLISECONDS);
        if(!exited){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);fail("original canonical compatibility process timed out");}
        assertEquals(0,process.exitValue(),()->"original canonical compatibility process failed: "+readLog(log));
        Obj result=DriverJson.object(Files.readAllBytes(output),4<<20);
        assertEquals(new Text(DriverJson.sha256(Files.readAllBytes(original))),result.get("source_sha256"));
        List<Value> expected=array(result.get("cases"),"original cases");assertEquals(cases.size(),expected.size());
        for(int index=0;index<cases.size();index++) {
            Case test=cases.get(index);Obj row=object(expected.get(index),"original result");assertEquals(new Text(test.name()),row.get("name"));
            Result actual=LegacyResumeNormalizer.normalize(test.payload(),PIPE,test.includeHistory()?HistoryMaterialization.INCLUDE:HistoryMaterialization.OMIT);
            String outcome=text(row.get("outcome"),"original outcome");
            if(outcome.equals("loaded")) {
                Loaded loaded=assertInstanceOf(Loaded.class,actual,test.name());Obj originalPayload=object(row.get("payload"),"original normalized payload");
                assertEquals(DriverJson.toNode(originalPayload),DriverJson.toNode(loaded.normalizedPayload()),test.name());
                assertEquals(loaded.normalizedPayload(),DriverJson.object(loaded.encode(),4<<20),test.name()+" full JSON type-domain roundtrip");
            }else if(outcome.equals("ignored"))assertInstanceOf(Ignored.class,actual,test.name());
            else assertInstanceOf(Rejected.class,actual,test.name());
        }
    }

    @Test void missingNullUnknownAndUnboundEpisodeKeepDifferentCanonicalMeaningsWithoutConstructingComplete() {
        Loaded legacy=loaded(base());assertEquals(Presence.MISSING,legacy.originalPresence().lifecycle());
        assertTrue(legacy.lifecycleMigrationRequired());assertTrue(legacy.episode().isPresent());
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base().with("succession_lifecycle",Nil.INSTANCE),PIPE));
        Loaded unknown=loaded(base().with("succession_lifecycle",unknownLifecycle()));
        assertFalse(unknown.lifecycleMigrationRequired());assertEquals(new Text("unknown"),assertInstanceOf(Obj.class,unknown.normalizedLifecycle()).get("lifecycle"));
        Loaded unbound=loaded(base().with("format_version",number(1)).with("episode_character_id",Nil.INSTANCE).with("episode_run_id",Nil.INSTANCE));
        assertEquals(1,unbound.formatVersion());assertTrue(unbound.episode().isEmpty());
        assertSame(Nil.INSTANCE,unbound.normalizedPayload().get("episode_character_id"));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base().with("episode_character_id",Nil.INSTANCE),PIPE));
    }

    @Test void receiptOmissionStillValidatesEveryHistoryRowAndCannotMasqueradeAsAnEmptyHistory() {
        Loaded receipt=assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(withHistory(),PIPE,HistoryMaterialization.OMIT));
        assertFalse(receipt.normalizedPayload().members().containsKey("command_history"));
        assertThrows(IllegalStateException.class,receipt::commandHistory);
        var rows=new ArrayList<>(array(withHistory().get("command_history"),"history"));
        rows.set(rows.size()-1,object(rows.getLast(),"last original row").with("ok",new Text("UNKNOWN")));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(withHistory().with("command_history",new Arr(rows)),PIPE,HistoryMaterialization.OMIT));
    }

    @Test void exactIntegerBoundariesAndLegacyWideAdvisoryDoNotRelaxTheExistingTypedPlanningDecoder() {
        assertInstanceOf(Ignored.class,LegacyResumeNormalizer.normalize(base().with("format_version",new Bool(true)),PIPE));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base().with("bridge_pid",new Bool(true)),PIPE));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base().with("campaign_goal",goal().with("format_version",new Bool(true))),PIPE));
        Obj wide=failure(52).with("war_id",new IntegerValue(BigInteger.ONE.shiftLeft(80))).with("original_extension",new Arr(List.of(Nil.INSTANCE,new DecimalValue("1.25"))));
        assertEquals(wide,RollbackWarFailures.normalizeLegacyDriverFailure(wide).orElseThrow());
        assertTrue(RollbackWarFailures.decode(wide).isEmpty(),"legacy DATA is not a narrowed typed retry permission");
        assertTrue(RollbackWarFailures.normalizeLegacyDriverFailure(wide.with("army_id",new Bool(true))).isEmpty());
        assertTrue(RollbackWarFailures.normalizeLegacyDriverFailure(wide.with("army_id",number(0))).isEmpty(),"the old persisted-advisory contract differs from the runtime public-CUnit-zero correction");
    }

    @Test void legacyNullAndMissingDatesSurviveActualHistoryNormalizationReceiptOmissionAndJsonReopen() {
        for(Obj original:List.of(epochDates(false,false,Nil.INSTANCE,Nil.INSTANCE),epochDates(true,true,Nil.INSTANCE,Nil.INSTANCE),
                epochDates(true,false,Nil.INSTANCE,Nil.INSTANCE),epochDates(false,true,Nil.INSTANCE,Nil.INSTANCE))) {
            Loaded normalized=loaded(original);
            Arr failures=assertInstanceOf(Arr.class,normalized.normalizedPayload().get("rollback_war_failures"));
            assertEquals(List.of(number(52),number(54)),failures.items().stream().map(value->object(value,"failure").get("target_province_id")).toList());
            assertSame(Nil.INSTANCE,object(failures.items().getLast(),"newest derived failure").get("previewed_date_raw"));
            assertEquals(original.get("command_history"),normalized.normalizedPayload().get("command_history"),
                    "reading legacy dates must not rewrite missing/present null fields in the original command history");
            List<Obj> rows=array(original.get("command_history"),"history").stream().map(value->object(value,"history row")).toList();
            List<Obj> completed=RollbackWarFailures.deriveCompletedLegacyDriverFailures(rows,checkpoint(),restoredScope(),"e",2);
            assertEquals(List.of(number(54),number(52)),completed.stream().map(value->value.get("target_province_id")).toList());
            assertEquals(completed.getFirst(),RollbackWarFailures.deriveCurrentLegacyDriverFailure(rows,checkpoint(),restoredScope(),"e",java.util.Optional.empty(),2).orElseThrow());
            assertTrue(RollbackWarFailures.deriveCompleted(rows,checkpoint(),restoredScope(),"e",2).isEmpty(),
                    "legacy DATA compatibility does not relax the live integer-date derivation");
            Loaded omitted=assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(original,PIPE,HistoryMaterialization.OMIT));
            assertFalse(omitted.normalizedPayload().members().containsKey("command_history"));
            assertEquals(failures,omitted.normalizedPayload().get("rollback_war_failures"));
            assertThrows(IllegalStateException.class,omitted::commandHistory);
            Loaded reopened=loaded(DriverJson.object(normalized.encode(),4<<20).with("pipe_name",new Text(PIPE)));
            assertEquals(failures,reopened.normalizedPayload().get("rollback_war_failures"));
            assertFalse(reopened.rollbackMigrationRequired());
        }
    }

    @Test void legacyDateComparisonStillRejectsDifferentJsonTypesAndRuntimeKeepsItsIntegerRequirement() {
        for(Obj original:List.of(epochDates(false,false,Nil.INSTANCE,number(24000)),
                epochDates(false,false,new Bool(true),number(1)),
                epochDates(false,false,new DecimalValue("1.0"),number(1)))) {
            List<Obj> rows=array(original.get("command_history"),"history").stream().map(value->object(value,"history row")).toList();
            assertTrue(RollbackWarFailures.deriveCompletedLegacyDriverFailures(rows,checkpoint(),restoredScope(),"e",2).isEmpty());
            assertTrue(RollbackWarFailures.deriveCompleted(rows,checkpoint(),restoredScope(),"e",2).isEmpty());
            Arr failures=assertInstanceOf(Arr.class,loaded(original).normalizedPayload().get("rollback_war_failures"));
            assertEquals(List.of(failure(52)),failures.items(),"an existing advisory survives; mismatching dates cannot invent a new one");
        }
        List<Obj> integerRows=array(epochState().get("command_history"),"history").stream().map(value->object(value,"history row")).toList();
        assertEquals(2,RollbackWarFailures.deriveCompleted(integerRows,checkpoint(),restoredScope(),"e",2).size());
    }

    @Test void originalEventOptionGrammarControlsActualCompletedEpochAdvisoriesAcrossPersistence() {
        for(String step:List.of("select-event-option-0","select-event-option-000","select-event-option-01",
                "select-event-option-1","select-event-option-1x","select-event-option-١")) {
            boolean submitted=step.equals("select-event-option-01")||step.equals("select-event-option-1");
            Obj original=eventOptionEpoch(step,true,false);
            List<Obj> rows=array(original.get("command_history"),"history").stream().map(value->object(value,"row")).toList();
            List<Obj> completed=RollbackWarFailures.deriveCompletedLegacyDriverFailures(rows,checkpoint(),restoredScope(),"e",2);
            assertEquals(submitted?List.of(number(54),number(52)):List.of(number(52)),
                    completed.stream().map(value->value.get("target_province_id")).toList(),step);
            assertEquals(submitted?2:1,RollbackWarFailures.deriveCompleted(rows,checkpoint(),restoredScope(),"e",2).size(),step);
            Loaded normalized=loaded(original);
            Arr failures=assertInstanceOf(Arr.class,normalized.normalizedPayload().get("rollback_war_failures"));
            assertEquals(submitted?List.of(number(52),number(54)):List.of(number(52)),
                    failures.items().stream().map(value->object(value,"failure").get("target_province_id")).toList(),step);
            assertEquals(original.get("command_history"),normalized.normalizedPayload().get("command_history"),step+" original history is immutable");
            Loaded omitted=assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(original,PIPE,HistoryMaterialization.OMIT));
            assertEquals(failures,omitted.normalizedPayload().get("rollback_war_failures"));
            Loaded reopened=loaded(DriverJson.object(normalized.encode(),4<<20).with("pipe_name",new Text(PIPE)));
            assertEquals(failures,reopened.normalizedPayload().get("rollback_war_failures"),step+" durable advisory roundtrip");
        }
        Obj nested=eventOptionEpoch("select-event-option-01",true,true);
        assertEquals(2,assertInstanceOf(Arr.class,loaded(nested).normalizedPayload().get("rollback_war_failures")).items().size());
        Obj failed=eventOptionEpoch("select-event-option-1",false,false);
        assertEquals(List.of(failure(52)),assertInstanceOf(Arr.class,loaded(failed).normalizedPayload().get("rollback_war_failures")).items(),
                "failed/unknown option history never proves that the unresolved event was selected");
    }

    private static List<Case> cases() {
        var cases=new ArrayList<Case>();cases.add(new Case("v1-unbound",base().with("format_version",number(1)).with("episode_character_id",Nil.INSTANCE).with("episode_run_id",Nil.INSTANCE),true));
        cases.add(new Case("complete-unknown-history-and-goal-extensions",withHistory().with("campaign_goal",goal()),true));
        cases.add(new Case("receipt-omits-only-history",withHistory().with("campaign_goal",goal()),false));
        cases.add(new Case("missing-plural-completed-epochs",epochState(),true));
        cases.add(new Case("legacy-null-dates-completed-epochs",epochDates(false,false,Nil.INSTANCE,Nil.INSTANCE),true));
        cases.add(new Case("legacy-missing-dates-completed-epochs",epochDates(true,true,Nil.INSTANCE,Nil.INSTANCE),true));
        cases.add(new Case("legacy-missing-preview-null-submit-completed-epochs",epochDates(true,false,Nil.INSTANCE,Nil.INSTANCE),true));
        cases.add(new Case("legacy-missing-dates-receipt-still-reduces",epochDates(true,true,Nil.INSTANCE,Nil.INSTANCE),false));
        cases.add(new Case("legacy-mismatching-dates-do-not-derive",epochDates(false,false,Nil.INSTANCE,number(24000)),true));
        for(String step:List.of("select-event-option-0","select-event-option-000","select-event-option-01","select-event-option-1"))
            cases.add(new Case("event-epoch-"+step,eventOptionEpoch(step,true,false),true));
        cases.add(new Case("event-epoch-omitted-history-still-reduces",eventOptionEpoch("select-event-option-0",true,false),false));
        cases.add(new Case("event-epoch-padded-option-auto-turn",eventOptionEpoch("select-event-option-01",true,true),true));
        cases.add(new Case("event-epoch-failed-option-is-not-submitted",eventOptionEpoch("select-event-option-1",false,false),true));
        cases.add(new Case("legacy-wide-scope-completed-epochs",epochState().with("rollback_war_failure",failure(52).with("war_id",new IntegerValue(BigInteger.ONE.shiftLeft(80)))),true));
        cases.add(new Case("plural-duplicates-and-scope",base().with("last_checkpoint",checkpoint()).with("rollback_war_failures",new Arr(List.of(failure(52),failure(52),failure(54),failure(55).with("war_id",number(9))))),true));
        cases.add(new Case("managed-transaction-retained",managedState(),true));
        cases.add(new Case("invalid-managed-normalizes-null",managedState().with("bridge_pid",number(99)),true));
        cases.add(new Case("expectation-original-title-metadata",base().with("succession_expectation",expectation()),true));
        cases.add(new Case("expectation-episode-mismatch",base().with("succession_expectation",expectation()).with("episode_run_id",new Text("other")),true));
        cases.add(new Case("explicit-unknown-lifecycle",base().with("succession_lifecycle",unknownLifecycle()),true));
        cases.add(new Case("explicit-null-lifecycle",base().with("succession_lifecycle",Nil.INSTANCE),true));
        cases.add(new Case("wrong-pipe",base().with("pipe_name",new Text("different")),true));
        cases.add(new Case("unsupported-v3",base().with("format_version",number(3)),true));
        cases.add(new Case("boolean-version",base().with("format_version",new Bool(true)),true));
        cases.add(new Case("bad-tail-in-receipt",base().with("command_history",new Arr(List.of(row(1,"unknown-original",Nil.INSTANCE).with("index",new Bool(true))))),false));
        return List.copyOf(cases);
    }
    private static Obj base(){return json("{\"format_version\":2,\"pipe_name\":\""+PIPE+"\",\"bridge_pid\":42,\"episode_character_id\":7,\"episode_run_id\":\"e\",\"command_history\":[],\"last_checkpoint\":null}");}
    private static Obj withHistory() {
        Obj active=new Obj(Map.of("active_siege",new Obj(Map.of()),"original",new IntegerValue(BigInteger.ONE.shiftLeft(80))));
        Obj inactive=new Obj(Map.of("active_siege",Nil.INSTANCE));
        Obj war=new Obj(Map.of("objective_province_states",new Arr(List.of(active,inactive,new Bool(false))),"unknown_original",new DecimalValue("1.2500")));
        Obj result=new Obj(Map.of("war_progress_after",new Obj(Map.of("wars",new Arr(List.of(war,new Text("retained non-object"))))),"raw_extension",Nil.INSTANCE));
        return base().with("command_history",new Arr(List.of(row(1,"unknown-failed",Nil.INSTANCE).with("ok",new Bool(false)).with("error",new Text("UNKNOWN")),row(2,"query-original",result))));
    }
    private static Obj checkpoint(){return json("{\"sha256\":\""+SHA+"\",\"size\":17,\"date_raw\":24000,\"history_index\":1}");}
    private static Obj failure(int target){return json("{\"status\":\"rolled_back_active_route\",\"episode_run_id\":\"e\",\"checkpoint_sha256\":\""+SHA+"\",\"war_id\":25,\"army_id\":304,\"restored_origin_province_id\":48,\"target_province_id\":"+target+",\"route_origin_province_id\":48,\"route_province_ids\":[50,"+target+"],\"restored_date_raw\":24000,\"extension\":{\"unknown\":[null,{},1.25]}}");}
    private static Obj epochState() {
        var history=new ArrayList<Value>();history.add(row(1,"save-checkpoint",new Obj(Map.of("checkpoint",checkpoint()))));
        for(int target:List.of(52,54)) {
            history.add(row(history.size()+1,"preview-move-army-304-to-"+target,json("{\"route_preview\":{\"status\":\"available\",\"army_id\":304,\"origin_province_id\":48,\"target_province_id\":"+target+",\"route_province_ids\":[50,"+target+"],\"previewed_date_raw\":24000}}")));
            history.add(row(history.size()+1,"move-army-304-to-"+target,json("{\"war_action\":{\"status\":\"moving\",\"army_id\":304,\"target_province_id\":"+target+",\"submitted_date_raw\":24000},\"player_armies\":[{\"army_id\":304,\"move_target_province_id\":"+target+",\"route_province_ids\":["+target+"]}]}")));
            history.add(row(history.size()+1,"restore-checkpoint",new Obj(Map.of("status",new Text("restored")))));
        }return base().with("last_checkpoint",checkpoint()).with("command_history",new Arr(history)).with("rollback_war_failure",failure(52));
    }
    private static Obj eventOptionEpoch(String option,boolean ok,boolean autoTurn) {
        Obj original=epochState();var history=new ArrayList<Value>(array(original.get("command_history"),"original history"));
        Obj restore=object(history.removeLast(),"last physical restore");
        Obj result=new Obj(Map.of());String command=option;
        if(autoTurn){command="auto-turn";result=new Obj(Map.of("auto_turn",new Obj(Map.of("selected_step",new Text(option),"result",result))));}
        history.add(row(history.size()+1,command,result).with("ok",new Bool(ok)));
        Obj context=new Obj(Map.of("status",new Text("available"),"window_match_count",number(1),
                "current_event_instance_id",number(17),"event_definition_key",new Text("history.unresolved")));
        history.add(row(history.size()+1,"query-current-event-window-context-v1",new Obj(Map.of("accepted",new Bool(true),
                "status",new Text("available"),"current_event_instance_id",number(17),"current_event_window_context",context))));
        history.add(restore.with("index",number(history.size()+1)));return original.with("command_history",new Arr(history));
    }
    /** Alter original row fields only; the checkpoint and physical restore boundaries stay fixed. */
    private static Obj epochDates(boolean omitPreview,boolean omitSubmitted,Value previewDate,Value submittedDate) {
        Obj original=epochState();List<Value> rows=new ArrayList<>();
        for(Value value:array(original.get("command_history"),"original history")) {
            Obj row=object(value,"original row");Obj result=object(row.get("result"),"original result");
            if(result.get("route_preview") instanceof Obj preview)
                row=row.with("result",result.with("route_preview",dateField(preview,"previewed_date_raw",omitPreview,previewDate)));
            else if(result.get("war_action") instanceof Obj action)
                row=row.with("result",result.with("war_action",dateField(action,"submitted_date_raw",omitSubmitted,submittedDate)));
            rows.add(row);
        }
        return original.with("command_history",new Arr(rows));
    }
    private static Obj dateField(Obj original,String key,boolean omit,Value value) {
        var fields=new java.util.LinkedHashMap<>(original.members());
        if(omit)fields.remove(key);else fields.put(key,value);return new Obj(fields);
    }
    private static Obj restoredScope() {
        Obj army=new Obj(Map.of("army_id",number(304),"current_province_id",number(48),"controllable",new Bool(true)));
        Obj war=new Obj(Map.of("war_id",number(25),"allied_armies",new Arr(List.of(army))));
        return new Obj(Map.of("date_raw",number(24000),"player_armies",new Arr(List.of(army)),"active_wars",new Arr(List.of(war))));
    }
    private static Obj managedState() {
        Obj transaction=json("{\"status\":\"awaiting_checkpoint_rebind\",\"request_id\":\"restore-original\",\"source_bridge_pid\":42,\"replacement_bridge_pid\":43,\"checkpoint_sha256\":\""+SHA+"\",\"checkpoint_size\":17,\"checkpoint_date_raw\":24000,\"history_index\":1,\"episode_character_id\":7,\"episode_run_id\":\"e\",\"original_extension\":[null,{}]}");
        return base().with("bridge_pid",number(43)).with("last_checkpoint",checkpoint()).with("command_history",new Arr(List.of(row(1,"save-checkpoint",new Obj(Map.of("checkpoint",checkpoint())))))).with("managed_restore_transaction",transaction);
    }
    private static Obj expectation(){return json("{\"schema\":\"xar.ck3.succession-expectation/v1\",\"status\":\"available\",\"binding\":{\"snapshot_id\":\"original\",\"revision\":18446744073709551615,\"native_revision\":1,\"date_raw\":24000,\"episode_run_id\":\"e\",\"episode_character_id\":7},\"expectation_state\":\"successor_expected\",\"predecessor_character_id\":7,\"expected_successor_character_id\":8,\"title_expectations\":[{\"title\":{\"title_id\":10,\"tier_raw\":\"unknown-original\",\"extension\":[null,{}]},\"first_heir_character_id\":8,\"primary\":true}],\"risk_state\":\"single_successor\",\"unavailable_reason\":null}");}
    private static Obj goal(){return json("{\"format_version\":1,\"goal_key\":\"dynasty_continuity\",\"campaign_id\":\"original-campaign\",\"origin_character_id\":7,\"current_character_id\":7,\"progress\":{\"reconciled_successions\":900719925474099312345,\"last_succession\":{\"untyped_legacy_extension\":[null,{}]},\"unknown_progress\":true},\"unknown_goal\":[null,1.25]}");}
    private static Obj unknownLifecycle(){return json("{\"schema\":\"xar.ck3.succession-lifecycle-binding/v1\",\"lifecycle\":\"unknown\",\"xar_enabled\":null,\"pact_contract\":\"unknown\",\"source\":\"unbound\",\"environment_sha256\":null}");}
    private static Obj row(int index,String command,Value result){return new Obj(Map.of("index",number(index),"command",new Text(command),"ok",new Bool(true),"result",result));}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Obj json(String raw){return DriverJson.object(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8),4<<20);}
    private static Loaded loaded(Obj original){return assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(original,PIPE));}
    private static String readLog(Path path){try {byte[] bytes=Files.readAllBytes(path);return new String(bytes,0,Math.min(bytes.length,65536),java.nio.charset.StandardCharsets.UTF_8);}catch(java.io.IOException failed){return failed.toString();}}
}
