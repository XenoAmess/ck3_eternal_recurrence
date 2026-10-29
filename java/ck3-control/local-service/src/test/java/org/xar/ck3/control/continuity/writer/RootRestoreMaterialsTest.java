package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.NativeCandidate;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSemanticReadState;
import org.xar.ck3.control.application.history.DriverHistoryImport;
import org.xar.ck3.control.application.history.DriverRestoreHistoryProducer;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.service.root.RootRestoreMaterialProjection;
import org.xar.ck3.control.service.root.RootRestoreMaterials;

/** Actual cold reducer, complete history producer and physical archive/pin failures. No fake managed Game is constructed. */
class RootRestoreMaterialsTest {
    @TempDir Path temporary;
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186",REQUEST="material-real-cold-restore";

    @Test void actualColdCompleteFeedsSoleManagedHistoryProducerAndOriginalFullImport() throws Exception {
        var archive=archive(temporary.resolve("writer"));var input=input(nativeState(),control(),saved(),abandoned());
        var cold=RootRestoreMaterialProjection.reduce(input);
        assertEquals(3,cold.provisional().commandHistory().size());
        assertEquals(unknown(),DriverSurvivingHistory.rows(cold.provisional()).getFirst());
        assertTrue(DriverJson.same(saved().campaignGoal(),cold.provisional().campaignGoal()));
        assertInstanceOf(DriverStateSnapshot.Missing.class,cold.provisional().successionLifecycle());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,cold.provisional().successionExpectation());
        assertFalse(cold.completedRow().members().containsKey("revision"));
        Obj completedResult=OpportunityJson.object(cold.completedRow().get("result"),"completed result");
        assertFalse(completedResult.members().containsKey("revision"));
        assertEquals(new Text("actual-native-frame"),completedResult.get("snapshot_id"));
        ExactRef provisional=archive.preserveMaterial(new RawJson(cold.provisional().encode()));
        ExactRef completed=archive.preserveMaterial(new RawJson(OpportunityJson.encode(cold.completedRow())));
        var candidate=DriverRestoreHistoryProducer.prepare(archive,saved(),provisional,completed,
                new DriverRestoreHistoryProducer.Binding(REQUEST,oldGame(),newGame(),cold.provisional().session(),BigInteger.valueOf(100)));
        assertEquals(3,candidate.driver().commandHistory().size());
        var imported=DriverHistoryImport.archivedOriginalV2(archive,candidate.driverEvidence(),4,2,newGame(),json("{}"));
        assertArrayEquals(candidate.driver().encode(),imported.facts().driver().encode());
        assertFalse(DriverSurvivingHistory.rows(candidate.driver()).stream().anyMatch(row->new Text("move-army-1-to-99").equals(row.get("command"))));
        var rows=DriverSurvivingHistory.rows(imported.facts().driver());
        assertEquals(3,rows.size());assertEquals(unknown(),rows.getFirst());
        assertEquals(new Text("save-checkpoint"),rows.get(1).get("command"));
        assertEquals(new Text("restore-checkpoint"),rows.get(2).get("command"));
    }
    @Test void repeatedPureColdReplayPreservesCanonicalCompleteWireAndSourceReferences() {
        var original=input(nativeState(),control(),saved(),abandoned());
        var first=RootRestoreMaterialProjection.reduce(original);var second=RootRestoreMaterialProjection.reduce(original);
        assertArrayEquals(first.provisional().encode(),second.provisional().encode());assertEquals(first.completedRow(),second.completedRow());
        assertEquals(first.restoredSemantic(),second.restoredSemantic());
        Obj result=OpportunityJson.object(first.completedRow().get("result"),"result");
        assertEquals(DriverObservationRef(nativeRef()),result.get("original_native_packet"));
    }
    @Test void lifecycleControlCannotSubstituteBooleanPidWrongParentOrRoundedBirth() {
        for(String raw:List.of(encoded(control()).replace("\"oldPid\":7","\"oldPid\":true"),
                encoded(control()).replace(REQUEST,"foreign-parent"),encoded(control()).replace("134373229053165471","134373229053165470"),
                encoded(control()).replace("NATIVE_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED","STOP_ENTERED"))) {
            assertThrows(IllegalArgumentException.class,()->RootRestoreMaterialProjection.reduce(input(nativeState(),json(raw),saved(),abandoned())));
        }
    }
    @Test void mapPausedLivingDateActorAndConnectionAreValidatedBeforeColdProjection() {
        for(String raw:List.of(encoded(nativeState()).replace("\"map_ready\":true","\"map_ready\":false"),
                encoded(nativeState()).replace("\"paused\":true","\"paused\":false"),encoded(nativeState()).replace("\"alive\":true","\"alive\":false"),
                encoded(nativeState()).replace("\"date_raw\":100","\"date_raw\":100.0"),encoded(nativeState()).replace("\"character_id\":1","\"character_id\":2"),
                encoded(nativeState()).replace("\"bridge_pid\":9","\"bridge_pid\":8"),
                encoded(nativeState()).replace("\"connection_generation\":4","\"connection_generation\":5"))) {
            assertThrows(IllegalArgumentException.class,()->RootRestoreMaterialProjection.reduce(input(json(raw),control(),saved(),abandoned())));
        }
    }
    @Test void changedSavedUnknownPrefixOrCheckpointCannotEnterColdHistory() {
        var rows=new ArrayList<>(DriverSurvivingHistory.rows(abandoned()));
        rows.set(0,json(encoded(unknown()).replace("real failure","altered failure")));
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterialProjection.reduce(input(nativeState(),control(),saved(),driver(7,rows))));
        var alteredSaved=DriverStateSnapshot.decodeComplete(new String(saved().encode(),StandardCharsets.UTF_8).replace("\"history_index\":2","\"history_index\":1").getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterialProjection.reduce(input(nativeState(),control(),alteredSaved,abandoned())));
    }
    @Test void coldAuxiliaryClearsConsumablesAndKeepsRealPrivateRootSeedConfigAndSourceLineage() {
        // Stale persisted DATA is deliberately not a private preclock source or a qualification fixture.
        Obj stalePreclock=json("{\"stale_serialized_input_only\":true}");
        Obj original=auxiliary().with("driver_preclock_expectation_source",stalePreclock);
        Obj reduced=RootRestoreMaterialProjection.reduceAuxiliary(original,nativeState());
        assertFalse(reduced.members().containsKey("driver_preclock_expectation_source"));
        assertEquals(stalePreclock,original.get("driver_preclock_expectation_source"));
        assertEquals(new Arr(List.of()),reduced.get("arrange_marriage_choices"));assertSame(Nil.INSTANCE,reduced.get("arrange_marriage_query_sequence"));
        assertSame(Nil.INSTANCE,reduced.get("active_combat_retreat_token"));assertSame(Nil.INSTANCE,reduced.get("succession_reconciliation"));
        assertSame(Nil.INSTANCE,OpportunityJson.object(reduced.get("capability_read_sources"),"read sources").get("marriage"));
        assertFalse(reduced.members().containsKey("capability_retreat_source"));assertFalse(reduced.members().containsKey("diagnostics"));
        for(String key:List.of("campaign_root_context_query","episode_seed","independent_battle_speed_readiness","capability_state_source",
                "capability_observed_native_source","capability_configuration","capability_session_paths","capability_initialization_source",
                "capability_state_version","untouched_strategy_evidence"))assertEquals(original.get(key),reduced.get(key),key);
        assertTrue(DriverCapabilityStateProducer.sessionPresentation(reduced).driverStateRestored());
    }
    @Test void missingActualPrivateCacheAndUnresolvedEpisodeTransitionDoNotBecomeEmptyDefaults() {
        var missing=new java.util.LinkedHashMap<>(auxiliary().members());missing.remove("episode_seed");
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterialProjection.reduceAuxiliary(new Obj(missing),nativeState()));
        var pending=auxiliary().with("episode_transition",json("{\"status\":\"unknown\",\"request_id\":\"real-unresolved\"}"));
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterialProjection.reduceAuxiliary(pending,nativeState()));
    }
    @Test void actualLifecycleJobZeroTerminalAllowsConsumedExit125ButRejectsMissingOrFractionalAccounting() {
        var join=new RootRestoreMaterials.LifecycleJoin(MACHINE,"old-session","new-session",oldGame(),newGame(),JavaGameLifecycle.replacementRequestId(REQUEST));
        Obj stopped=event("STOPPED",7,"134373229053165471","old-session","old-launch",true),launch=event("HELLO",9,"134373229053165472","new-session",join.launchRequestId(),false);
        RootRestoreMaterials.requireLifecycleRows(stopped,launch,join);
        for(String altered:List.of(encoded(stopped).replace("\"activeProcesses\":0","\"activeProcesses\":1"),
                encoded(stopped).replace("\"activeProcesses\":0","\"activeProcesses\":0.0"),encoded(stopped).replace("\"stopReason\":null","\"stopReason\":\"timeout\""),
                encoded(stopped).replace("134373229053165471","134373229053165470"))) {
            assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.requireLifecycleRows(json(altered),launch,join));
        }
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.requireLifecycleRows(stopped,launch.with("requestId",new Text("wrong-child")),join));
    }
    @Test void originalNativePacketRetainsLexicalStateAndRejectsChangedEnvelopeOrInventedClaim() throws Exception {
        byte[] state=OpportunityJson.encode(nativeState());byte[] packet=packet(new String(state,StandardCharsets.UTF_8),"actual-native-frame",2);
        var candidate=new NativeCandidate(new NativeObservationPort.ObservedFrame(transport(),"actual-native-frame",BigInteger.TWO,new RawJson(state),packet,Instant.parse("2026-10-23T19:00:00Z")),
                new G2Source(MACHINE,"2026-10-23T19:00:00Z","fixture-build",lifecycleRef()),"lineage",nativeRef());
        RootRestoreMaterials.requireNativePacket(candidate,packet);
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.requireNativePacket(candidate,packet(new String(state,StandardCharsets.UTF_8),"other-frame",2)));
        assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.requireNativePacket(candidate,packet(" "+new String(state,StandardCharsets.UTF_8),"actual-native-frame",2)));
        byte[] truncated=java.util.Arrays.copyOf(packet,packet.length-1);assertThrows(IOException.class,()->RootRestoreMaterials.requireNativePacket(candidate,truncated));
    }
    @Test void actualPhysicalSourceReadAndArchiveRoundTripShareOneLiveWriterSession() throws Exception {
        var archive=archive(temporary.resolve("writer"));var files=new NativeCheckpointFiles();
        Path physical=temporary.resolve("original-lifecycle.json");byte[] original=OpportunityJson.encode(control());Files.write(physical,original);
        ExactRef reference=files.observe(physical).orElseThrow().reference();
        archive.writer().locked(borrowed->{
            var read=RootRestoreMaterials.readPinned(borrowed,files,reference,65536);assertArrayEquals(original,read.contents());
            byte[] copy=read.contents();copy[0]=0;assertArrayEquals(original,read.contents());
            ExactRef archived=archive.preserveArtifact(borrowed,read.contents(),65536);
            assertArrayEquals(original,archive.readArtifact(borrowed,archived,65536));borrowed.verifyPin(read.pin());return null;
        });
    }
    @Test void sameBytesReplacedFileIdAndEscapedOriginalSessionNeverPassPhysicalReplay() throws Exception {
        var archive=archive(temporary.resolve("writer"));var files=new NativeCheckpointFiles();
        Path physical=temporary.resolve("original.json");byte[] body=OpportunityJson.encode(control());Files.write(physical,body);
        ExactRef reference=files.observe(physical).orElseThrow().reference();var escaped=new ContinuityStorePort.Session[1];
        archive.writer().locked(borrowed->{
            escaped[0]=borrowed;var original=RootRestoreMaterials.readPinned(borrowed,files,reference,65536);
            Path substitution=temporary.resolve("same-bytes-different-file.json");Files.write(substitution,body);
            Files.move(substitution,physical,StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class,()->borrowed.verifyPin(original.pin()));return null;
        });
        assertThrows(ContractViolationException.class,()->RootRestoreMaterials.readPinned(escaped[0],files,reference,65536));
    }
    @Test void missingChangedOrOversizedOriginalPhysicalSourceIsUnavailable() throws Exception {
        var archive=archive(temporary.resolve("writer"));var files=new NativeCheckpointFiles();
        Path physical=temporary.resolve("original.json");Files.writeString(physical,"{}");ExactRef reference=files.observe(physical).orElseThrow().reference();
        archive.writer().locked(borrowed->{
            assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.readPinned(borrowed,files,reference,1));
            Files.writeString(physical,"[]");assertThrows(IOException.class,()->RootRestoreMaterials.readPinned(borrowed,files,reference,65536));
            Files.delete(physical);assertThrows(IOException.class,()->RootRestoreMaterials.readPinned(borrowed,files,reference,65536));return null;
        });
    }
    private static RootRestoreMaterialProjection.Input input(Obj raw,Obj control,DriverStateSnapshot.Complete saved,DriverStateSnapshot.Complete abandoned) {
        return new RootRestoreMaterialProjection.Input(REQUEST,oldGame(),transport(),"actual-replacement-pipe","actual-native-frame",BigInteger.TWO,
                saved,abandoned,raw,control,lifecycleRef(),nativeRef(),Optional.empty());
    }
    private static NativeObservationPort.TransportSession transport(){return new NativeObservationPort.TransportSession(MACHINE,newGame(),BigInteger.valueOf(4),"new-session");}
    private static GameGeneration oldGame(){return new GameGeneration(7,new PythonOnlyUInt64(new BigInteger("134373229053165471")));}
    private static GameGeneration newGame(){return new GameGeneration(9,new PythonOnlyUInt64(new BigInteger("134373229053165472")));}
    private static ExactRef lifecycleRef(){return new ExactRef("Z:/fixture/actual-lifecycle.json",100,"b".repeat(64));}
    private static ExactRef nativeRef(){return new ExactRef("Z:/fixture/actual-native.packet",100,"c".repeat(64));}
    private static Obj DriverObservationRef(ExactRef ref){return org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.reference(ref);}
    private static Obj nativeState(){return json("{\"map_ready\":true,\"paused\":true,\"date_raw\":100,\"played_character\":{\"character_id\":1,\"alive\":true},\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":9,\"connection_generation\":4}}");}
    private static Obj control(){return json("{\"schema\":\"xar.java-game-replacement/v1\",\"parentLifecycleIntentId\":\""+REQUEST+"\",\"phase\":\"NATIVE_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED\",\"oldPid\":7,\"oldBirthDecimal\":\"134373229053165471\"}");}
    private static Obj unknown(){return json("{\"index\":1,\"command\":\"unknown-original\",\"ok\":false,\"result\":null,\"error\":\"real failure\",\"extension\":[null,[],{}]}");}
    private static Obj checkpoint(){return json("{\"history_index\":2,\"sha256\":\""+"a".repeat(64)+"\",\"size\":4096,\"date_raw\":100,\"episode_character_id\":1,\"episode_run_id\":\"ep\"}");}
    private static Obj anchor(){return json("{\"index\":2,\"command\":\"save-checkpoint\",\"ok\":true,\"result\":{\"checkpoint\":"+encoded(checkpoint())+"}}");}
    private static DriverStateSnapshot.Complete saved(){return driver(7,List.of(unknown(),anchor()));}
    private static DriverStateSnapshot.Complete abandoned(){return driver(7,List.of(unknown(),anchor(),json("{\"index\":3,\"command\":\"move-army-1-to-99\",\"ok\":true,\"result\":{}}")));}
    private static DriverStateSnapshot.Complete driver(long pid,List<Obj> rows) {
        var history=rows.stream().map(row->new DriverStateSnapshot.HistoryEntry(OpportunityJson.integer(row.get("index"),"history index").longValueExact(),new DriverStateSnapshot.Value(OpportunityJson.encode(row)))).toList();
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("original-pipe",pid,BigInteger.ONE,"ep"),history,
                new DriverStateSnapshot.Value(OpportunityJson.encode(checkpoint())),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.Value("{\"requested\":true}".getBytes(StandardCharsets.UTF_8)),new DriverStateSnapshot.Missing(),
                new DriverStateSnapshot.Value("{\"goal\":null,\"calendar\":[],\"actual_strategy\":{\"x\":1}}".getBytes(StandardCharsets.UTF_8)),
                new DriverStateSnapshot.Value("[]".getBytes(StandardCharsets.UTF_8)));
    }
    @Test void coldProjectionClearsActualSemanticCachesAndOldSuccessionProofWhileRetainingTheirOriginalSourceTable() {
        Obj original=auxiliary().with(DriverSemanticReadState.SOURCES,json("{\"WAR_ENTRY\":{\"receipt\":{\"retained_original\":true}}}"))
                .with("combat_simulation_inputs",json("{\"old_actual_operands\":true}"))
                .with("combat_simulation_inputs_v3",json("{\"old_actual_operands\":true}"))
                .with("war_entry_assessments_two_read_trace_v1",new Arr(List.of(json("{\"old_query\":1}"))))
                .with("war_declared_overview_v1_observation",json("{\"old_game\":true}"))
                .with("war_results_window_v1_observation",json("{\"old_game\":true}"))
                .with("capability_succession_source",json("{\"old_natural_succession_proof\":true}"));
        Obj reduced=RootRestoreMaterialProjection.reduceAuxiliary(original,nativeState());
        assertSame(Nil.INSTANCE,reduced.get("combat_simulation_inputs"));assertSame(Nil.INSTANCE,reduced.get("combat_simulation_inputs_v3"));
        assertEquals(new Arr(List.of()),reduced.get("war_entry_assessments_two_read_trace_v1"));
        assertSame(Nil.INSTANCE,reduced.get("war_declared_overview_v1_observation"));
        assertSame(Nil.INSTANCE,reduced.get("war_results_window_v1_observation"));
        assertFalse(reduced.members().containsKey("capability_succession_source"));
        assertSame(Nil.INSTANCE,reduced.get("succession_reconciliation"));
        assertEquals(original.get(DriverSemanticReadState.SOURCES),reduced.get(DriverSemanticReadState.SOURCES));
        assertEquals(original.get("untouched_strategy_evidence"),reduced.get("untouched_strategy_evidence"));
        assertEquals(original.get("episode_seed"),reduced.get("episode_seed"));
    }
    private static Obj auxiliary() {
        return json("{\"arrange_marriage_choices\":[{\"choice_id\":\"1-2\"}],\"arrange_marriage_query_sequence\":3,\"campaign_root_context_query\":{\"real\":1},\"active_combat_retreat_token\":{\"real\":2},\"episode_seed\":{\"original\":true},\"episode_transition\":null,\"succession_reconciliation\":{\"old\":true},\"independent_battle_speed_readiness\":{\"actual_old_frame\":1},\"capability_read_sources\":{\"marriage\":{},\"campaign_root\":{}},\"capability_retreat_source\":{},\"capability_state_source\":{},\"capability_observed_native_source\":{},\"capability_configuration\":{\"actual\":true},\"capability_session_paths\":{\"queue_dir\":\"Z:/queue\",\"driver_state_path\":\"Z:/state.json\"},\"capability_initialization_source\":{},\"capability_state_version\":\"8\",\"episode_transition_error\":null,\"untouched_strategy_evidence\":{\"source\":\"retained\"},\"diagnostics\":{\"bridge_pid\":7}}");
    }
    private static Obj event(String event,long pid,String birth,String session,String request,boolean stopped) {
        return json("{\"schema\":\"xar.java-game-lifecycle-event/v1\",\"machineId\":\""+MACHINE+"\",\"observedAtUtc\":\"2026-10-23T19:00:00Z\",\"sessionId\":\""+session+"\",\"requestId\":\""+request+"\",\"event\":\""+event+"\",\"game\":{\"pid\":"+pid+",\"creationFiletimeDecimal\":\""+birth+"\"},\"accounting\":{\"activeProcesses\":0},\"terminal\":"+(stopped?"{\"exitCode\":125,\"stopReason\":null,\"accounting\":{\"activeProcesses\":0}}":"null")+"}");
    }
    private static byte[] packet(String state,String snapshot,long revision) {
        byte[] json=("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\""+snapshot+"\",\"revision\":"+revision+",\"state\":"+state+"}").getBytes(StandardCharsets.UTF_8);
        return ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
    }
    private static Obj json(String raw){return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
    private static String encoded(Obj value){return new String(OpportunityJson.encode(value),StandardCharsets.UTF_8);}
    private static NativeOutcomeArchive archive(Path root) throws IOException {
        Files.createDirectory(root);Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");
        byte[] state=ContinuityJson.canonical(state());Files.write(snapshot,state);Files.write(anchor,state);
        Path lock=root.resolve("ROOT-CONTINUITY-WINDOW.lock");Files.createFile(lock);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path source=root.resolve("reviewed-source.txt");Files.writeString(source,"synthetic source-bound physical restore regression fixture");
        Layout layout=new Layout(snapshot,LedgerFiles.read(anchor,65536).pin().reference(),MACHINE);Path artifactRoot=root.resolve("artifacts");Files.createDirectory(artifactRoot);
        var storage=StorageWriteGuardTestSupport.create(layout);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifactRoot,lock,1_048_576),storage);
        var writer=new ContinuityWriter(layout,List.of(LedgerFiles.read(source,65536).pin().reference()),new TransitionAuthority(){
            @Override public String revalidate(ContinuityState predecessor,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState predecessor,Request request){return OriginalWindowReducer.reduce(predecessor,request);}
        },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),storage);return new NativeOutcomeArchive(artifacts,writer);
    }
    private static ObjectNode state() {
        ObjectNode row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id",MACHINE);row.put("sequence",0);row.put("window_id",1);
        row.put("status","running");row.put("target_days",10_958);row.put("target_years",30);row.put("calendar_year_days",365.25);
        row.put("start_date_raw",1000);row.put("target_date_raw",1000+10_958*24);row.put("last_settled_date_raw",1000);row.put("last_settled_cycles",1);
        row.put("manual_repair_count",1);row.put("automatic_recovery_count",0);row.put("binding_lineage_count",0);
        var game=row.putObject("game_binding");game.put("pid",123);game.put("creation_date","2026-10-23T01:00:00Z");row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);row.put("NEXT",11559);return row;
    }
}
