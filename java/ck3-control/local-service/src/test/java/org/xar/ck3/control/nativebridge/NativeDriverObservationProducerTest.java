package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual original packet/Driver producers -> held bootstrap/full history -> semantic archive replay. */
final class NativeDriverObservationProducerTest {
    @TempDir Path temporary;
    private int sequence;
    private static final String DRIVER="""
        {"format_version":2,"pipe_name":"original-driver-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"original-episode",
        "last_checkpoint":null,"command_history":[{"index":1,"command":"query-armies","ok":true,"result":{"armies":[]}},
        {"index":2,"command":"move-army","ok":false,"error":"original rejection"}],"rollback_war_failure":null,
        "managed_restore_transaction":null,"succession_expectation":null,"succession_lifecycle":null,"campaign_goal":null,"rollback_war_failures":[]}
        """;
    private static final String STATE="{\"date_raw\":53144328,\"paused\":true,\"map_ready\":true,\"speed\":3,\"played_character\":{\"character_id\":73,\"alive\":true},"
            +"\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{},\"original_metric\":1.0}";
    private static final String SEND="""
        import ast,base64,copy,hashlib,json,struct,sys,threading,types
        from pathlib import Path
        source=Path(sys.argv[1]).read_bytes()
        if hashlib.sha256(source).hexdigest()!=sys.argv[2]: raise RuntimeError('original packet producer source drift')
        tree=ast.parse(source.decode('utf-8-sig'))
        if sys.argv[4]=='driver':
          driver=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeHeadlessGameplayDriver')
          payload=next(n for n in driver.body if isinstance(n,ast.FunctionDef) and n.name=='_driver_state_payload_locked')
          future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
          scope={'copy':copy,'_NATIVE_DRIVER_STATE_VERSION':2}
          exec(compile(ast.fix_missing_locations(ast.Module(body=[future,payload],type_ignores=[])),str(Path(sys.argv[1])),'exec'),scope)
          row=json.loads(base64.b64decode(sys.argv[3]))
          owner=types.SimpleNamespace(pipe_name=row['pipe_name'],_session_bridge_pid=row['bridge_pid'],_episode_character_id=row['episode_character_id'],
            _episode_run_id=row['episode_run_id'],_last_checkpoint=row['last_checkpoint'],_command_history=row['command_history'],
            _rollback_war_failures=row['rollback_war_failures'],_managed_restore_transaction=row['managed_restore_transaction'],
            _succession_expectation=row['succession_expectation'],_succession_lifecycle=row['succession_lifecycle'],_campaign_goal=row['campaign_goal'],
            _rollback_war_failures_migration_required=False)
          sys.stdout.buffer.write(json.dumps(scope['_driver_state_payload_locked'](owner),ensure_ascii=False,separators=(',',':')).encode('utf-8'))
          sys.exit(0)
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeNamedPipeServer')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='send')
        packets=[]
        def write(handle,packet): packets.append(packet); return True
        scope={'json':json,'struct':struct,'MAXIMUM_FRAME_BYTES':64*1024*1024,'_write_all':write,'BridgeUnavailableError':RuntimeError}
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future,method],type_ignores=[])),str(Path(sys.argv[1])),'exec'),scope)
        owner=types.SimpleNamespace(_write_lock=threading.Lock(),_current_handle=lambda:1)
        scope['send'](owner,json.loads(base64.b64decode(sys.argv[3])))
        if len(packets)!=1: raise RuntimeError('original packet producer did not make exactly one attempt')
        sys.stdout.buffer.write(packets[0])
        """;
    private static final String SEMANTIC_ORACLE="""
        import ast,base64,copy,hashlib,importlib,json,sys,threading
        from pathlib import Path
        source=Path(sys.argv[1]).resolve(); original=source.read_bytes()
        if hashlib.sha256(original).hexdigest()!=sys.argv[2]: raise ValueError('actual native semantic producer source drift')
        expected={
          'event_contract':'876d69c1efa7948ebaa157782a688caeeab7954dc550e06dfc8afff1cc5e8970',
          'settlement_contract':'647d7f558a18326682817f53d55cbf600ced2754b72b6fdc84d6244c807c6bbd',
          'player_event_trait_membership_contract':'d45db52c93332ee47208db976aea18bb64133b4c7b86476ad7a173400f194afb',
          'pending_character_interaction_context_contract':'a0cec914987b8e430fc5660d0ec248fed9179b8c23676b4a185c177a94a58177',
          'war_contract':'ae960cc6a928eb9d26f2f9c93f30463a978951c374021558d08860c8f9125b2a',
          'version_identity':'9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086'}
        before={}; modules={}; sys.path.insert(0,str(source.parents[2]))
        for name,sha in expected.items():
          path=source.with_name(name+'.py'); raw=path.read_bytes()
          if hashlib.sha256(raw).hexdigest()!=sha: raise ValueError('semantic sibling source drift: '+name)
          before[path]=raw; module=importlib.import_module('xar_autoplayer.bridge.'+name)
          if Path(module.__file__).resolve()!=path: raise ValueError('another semantic module imported: '+name)
          modules[name]=module
        scope={'copy':copy,
          'normalize_active_event':modules['event_contract'].normalize_active_event,
          'normalize_one_life_settlement':modules['settlement_contract'].normalize_one_life_settlement,
          'normalize_player_event_trait_membership_v1':modules['player_event_trait_membership_contract'].normalize_player_event_trait_membership_v1,
          'normalize_pending_interaction_id':modules['pending_character_interaction_context_contract'].normalize_pending_interaction_id,
          'normalize_active_wars':modules['war_contract'].normalize_active_wars,
          'player_armies_from_state':modules['war_contract'].player_armies_from_state}
        names={'_semantic_snapshot_from_frame','_validate_revision','_played_character','_played_character_gold',
          '_played_character_prestige','_played_character_piety','_pending_character_interaction'}
        definitions=[node for node in ast.parse(original.decode('utf-8-sig')).body if isinstance(node,ast.FunctionDef) and node.name in names]
        if len(definitions)!=len(names): raise ValueError('actual complete semantic producer definitions missing')
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future,*definitions],type_ignores=[])),str(source),'exec'),scope)
        if sys.argv[4] in {'protocol','protocol-lifecycle'}:
          tree=ast.parse(original.decode('utf-8-sig'))
          version=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROTOCOL_VERSION' for t in n.targets))
          cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeProtocolState')
          scope['threading']=threading
          exec(compile(ast.fix_missing_locations(ast.Module(body=[future,version,cls],type_ignores=[])),str(source),'exec'),scope)
          owner=scope['NativeProtocolState']('original-receive-revision-oracle');result=[]
          for frame in json.loads(base64.b64decode(sys.argv[3])):
            if frame is None and sys.argv[4]=='protocol-lifecycle': owner.mark_disconnected()
            else: owner.ingest(frame)
            result.append(owner.public_revision())
        else:
          result=scope['_semantic_snapshot_from_frame'](json.loads(base64.b64decode(sys.argv[3])))
        if source.read_bytes()!=original: raise ValueError('actual semantic producer changed during oracle')
        for path,raw in before.items():
          if path.read_bytes()!=raw: raise ValueError('actual semantic sibling changed during oracle')
        sys.stdout.buffer.write(json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8'))
        """;

    @Test void originalPacketsBootstrapFrozenFullHistoryAndArchiveReplayWithoutWrites() throws Exception {
        var archive=new MemoryArchive();byte[] driver=original("driver",new String(driverWire(),StandardCharsets.UTF_8));ExactRef full=archive.preserveMaterial(new RawJson(driver));
        byte[] originalHello=send(hello()),originalFrame=send(snapshot());
        var replay=new Replay(originalHello,originalFrame);var borrowed=new Borrowed();
        var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
        try(var transport=new NativeGameTransport(replay,config(),16,16)) {
            var stale=DriverJson.object(bytes("{\"rejected_state_snapshot_count\":99,\"last_rejected_state_snapshot\":{\"stale\":true},\"snapshot_publish_diagnostic_count\":98,\"transport_refusal\":{\"stale\":true}}"),65536);
            var seed=new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of("diagnostics",stale)),Optional.empty());
            var source=new G2Source("fixture-machine",Instant.now().toString(),"original-source-fixture",full);
            var adopted=DriverBootstrap.adopt(seed,borrowed,new ActionSnapshotReader(journal),transport,source,archive,
                    (ref,maximum) -> archive.loadMaterial(ref).bytes(),receipt -> { throw new AssertionError("no canonical actions in this actual fixture"); },4,Instant.now().plusSeconds(10));
            assertEquals(DriverBootstrap.AdoptionStatus.READ_ONLY_UNCLASSIFIED,adopted.status());
            assertEquals(List.of("entry_source_unclassified_no_private_original_or_java_cold_admission"),adopted.incompleteReasons());
            adopted.producer().requireSameTransport(transport,source);
            assertThrows(IllegalArgumentException.class,() -> adopted.producer().requireSameTransport(transport,
                    new G2Source(source.machineId(),source.observedAtUtc(),"different-source-data",source.sourceRef())));
            assertEquals(2,OpportunityJson.array(adopted.first().semantic().get("native_command_history"),"history").size());
            assertEquals(0,replay.writes);assertEquals(1,journal.borrowedEntries);assertTrue(journal.nestedEntries>0);
            var factsRef=DriverObservationEvidenceReader.reference(adopted.first().semantic().get("java_driver_facts_evidence"));
            RawJson manifest=archive.loadMaterial(factsRef);
            var nativeActual=DriverObservationEvidenceReader.nativeFrame(factsRef,manifest,archive.loadNativeFrame(adopted.first().originalEvidence()));
            var currentRef=DriverObservationEvidenceReader.currentDriverReference(factsRef,manifest);
            var facts=DriverObservationEvidenceReader.decode(factsRef,manifest,archive.loadMaterial(currentRef),nativeActual);
            var firstDiagnostics=OpportunityJson.object(facts.originalSemanticFields().get("diagnostics"),"actual first diagnostics");
            assertEquals(BigInteger.ZERO,OpportunityJson.integer(firstDiagnostics.get("rejected_state_snapshot_count"),"actual rejection count"));
            assertEquals(OpportunityJson.Nil.INSTANCE,firstDiagnostics.get("last_rejected_state_snapshot"));
            assertFalse(firstDiagnostics.members().containsKey("transport_refusal"),"first frame predates successful adoption; no known null may be fabricated");
            var publicFirst=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(adopted.first(),true));
            var publicDiagnostics=OpportunityJson.object(DriverJson.object(publicFirst.bytes(),RawJson.MAXIMUM_BYTES).get("diagnostics"),"public first diagnostics");
            assertEquals(new OpportunityJson.Text("0"),publicDiagnostics.get("rejected_state_snapshot_count"));
            assertEquals(new OpportunityJson.Text("0"),publicDiagnostics.get("snapshot_publish_diagnostic_count"));
            int contextReads=replay.reads,contextWrites=replay.writes;
            var publicContext=DriverPublicContext.from(adopted.first());
            assertArrayEquals(publicFirst.bytes(),publicContext.snapshot().bytes());
            assertEquals(publicDiagnostics,DriverJson.object(publicContext.diagnostics().bytes(),RawJson.MAXIMUM_BYTES));
            assertEquals(contextReads,replay.reads,"public context must preserve this frame without reading another");
            assertEquals(contextWrites,replay.writes,"public context must not submit an independent READ or action");
            assertEquals(OpportunityJson.toNode(adopted.first().semantic()),OpportunityJson.toNode(PublicSnapshotCodec.decode(publicFirst)));
            assertInstanceOf(NativeTransportDiagnostics.Unobserved.class,transport.diagnostics().production().orElseThrow().adoption(),"bare Seed software DATA cannot classify a physical adoption");
            int reads=replay.reads;var after=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(transport.latestObservedSnapshot().orElseThrow())).facts();
            var afterDiagnostics=OpportunityJson.object(after.originalSemanticFields().get("diagnostics"),"actual post-adoption diagnostics");
            assertFalse(afterDiagnostics.members().containsKey("transport_refusal"),"unclassified bare Seed cannot fabricate observed known-null refusal");
            assertEquals(BigInteger.ZERO,OpportunityJson.integer(afterDiagnostics.get("snapshot_publish_diagnostic_count"),"actual publication count"));
            assertEquals(reads,replay.reads,"diagnostic capture never observes again");
            var afterManifest=archive.loadMaterial(after.semanticFactsEvidence());
            var afterNative=DriverObservationEvidenceReader.nativeFrame(after.semanticFactsEvidence(),afterManifest,nativeActual.originalPacket());
            assertEquals(nativeActual.observedAt(),afterNative.observedAt());assertArrayEquals(nativeActual.originalPacket(),afterNative.originalPacket());
            assertArrayEquals(facts.driver().encode(),after.driver().encode());
            var rebuilt=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(nativeActual,facts,adopted.first().originalEvidence()));
            assertEquals(adopted.first(),rebuilt);assertEquals(adopted.currentDriverEvidence(),currentRef);
            assertEquals(new BigInteger("134055108000000017"),rebuilt.identity().game().creationFiletime().value());
        }
    }
    /** Native05 public actor is signed-i32 except -1. Negative support fixes the old Python semantic rejection.
     * This is an actual Java software receive/Driver/archive/cold-DATA path, not a physical negative-ID Game claim. */
    @Test void signedNativeActorsReachRealReceiveDriverPublicArchiveAndStrictColdDecodeWithoutUnsignedAliases()throws Exception {
        boolean rejectionCases=true;
        for(int actor:List.of(Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE)) {
            var archive=new MemoryArchive(temporary.resolve("signed-actor-"+actor));
            String originalDriver=new String(driverWire(),StandardCharsets.UTF_8).replace("\"episode_character_id\":73","\"episode_character_id\":"+actor);
            byte[] payload=original("driver",originalDriver);ExactRef full=archive.preserveMaterial(new RawJson(payload));
            assertEquals(BigInteger.valueOf(actor),DriverStateSnapshot.decodeComplete(payload).session().actorId());
            var readyFrame=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(bytes(snapshot()),65536);
            var readyState=(com.fasterxml.jackson.databind.node.ObjectNode)readyFrame.path("state");
            ((com.fasterxml.jackson.databind.node.ObjectNode)readyState.path("played_character")).put("character_id",actor);
            readyState.put("one_life_terminal",false).put("episode_identity_pending",false);
            ((com.fasterxml.jackson.databind.node.ObjectNode)readyState.path("diagnostics")).put("bridge_pid",42)
                    .put("connection_generation",session().connectionGeneration());
            String valid=new String(FullJsonTree.encode(readyFrame,65536),StandardCharsets.UTF_8);
            if(actor<0){IOException rejected=assertThrows(IOException.class,()->original("semantic",valid));assertTrue(rejected.getMessage().contains("played_character"),"old Python negative oracle remains a rejection, never fake parity");}
            var packets=new java.util.ArrayList<byte[]>();packets.add(send(hello()));int bad=0;
            if(rejectionCases){
                for(String token:List.of("-1","2147483648","-2147483649","true","1.0","null","\"7\"")){
                    packets.add(send(snapshot().replace("\"character_id\":73","\"character_id\":"+token)));bad++;
                }rejectionCases=false;
            }
            packets.add(send(valid));
            var unavailableFrame=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(bytes(valid),65536);
            var unavailablePlayed=(com.fasterxml.jackson.databind.node.ObjectNode)unavailableFrame.path("state").path("played_character");
            unavailablePlayed.putObject("event_trait_membership").put("schema","xar.ck3.player-event-trait-membership/v1")
                    .put("game_version","1.20.0.4").put("executable_sha256","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                    .put("status","unavailable").put("snapshot_revision",9).put("date_raw",53144328).put("played_character_id",actor)
                    .putNull("traits").put("unavailable_reason","current_player_frame_unavailable");
            String unavailableWire=new String(FullJsonTree.encode(unavailableFrame,65536),StandardCharsets.UTF_8);
            if(actor<=0)assertThrows(IOException.class,()->original("semantic",unavailableWire),"old Python trait metadata rejects nonpositive actors; this is an explicit native-domain repair");
            packets.add(send(unavailableWire));var replay=new Replay(packets.toArray(byte[][]::new));var borrowed=new Borrowed();
            var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
            var source=new G2Source("fixture-machine",Instant.now().toString(),"native-signed-actor-contract-repair",full);
            try(var transport=new NativeGameTransport(replay,config(),32,32)){
                var seed=new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty());
                var adopted=DriverBootstrap.adopt(seed,borrowed,new ActionSnapshotReader(journal),transport,source,archive,
                        (ref,max)->archive.loadMaterial(ref).bytes(),receipt->Optional.empty(),4,Instant.now().plusSeconds(10));
                assertEquals(BigInteger.valueOf(actor),adopted.first().identity().frame().identity().player());
                assertEquals(BigInteger.valueOf(bad),transport.diagnostics().production().orElseThrow().rejectedSnapshotCount());
                var manifestRef=DriverObservationEvidenceReader.reference(adopted.first().semantic().get("java_driver_facts_evidence"));
                var manifest=archive.loadMaterial(manifestRef);var raw=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,archive.loadNativeFrame(adopted.first().originalEvidence()));
                var normalized=DriverObservationAssembler.canonicalNativeState(raw).semantic();
                assertEquals(BigInteger.valueOf(actor),OpportunityJson.integer(OpportunityJson.object(normalized.get("played_character"),"played").get("character_id"),"signed actor"));
                var driverRef=DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest);
                var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,archive.loadMaterial(driverRef),raw);
                var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(raw,facts,adopted.first().originalEvidence()));
                assertEquals(adopted.first(),complete);
                // This is the public pure predicate's software DATA result, never a Root/Managed readiness ticket.
                var caps=DriverJson.object(bytes("""
                    {"mode":"native-headless","backend_id":"native-headless","visual_fallback":false,"transport_ready":true,"snapshot":true,
                    "diagnostics":{"connected":true,"semantic_state_available":true,"bridge_pid":42,"connection_generation":18446744073709551615,
                    "transport_fatal_error":null,"hello":{"ck3_build_match":true,"game_adapter_status":"ready"},
                    "last_heartbeat":{"sequence":1,"startup_failure_containment_enabled":false,"startup_particle2_stage_recorder_enabled":false,
                    "main_thread_query_mailbox_v1":{"installed":true,"stop":false,"failure":0,"ready":true,"executor_submission_enabled":true,
                    "date_raw":53144328,"paused":true,"pump_epochs":1}}},"native_session_control":{"episode_binding_state":"active_new"}}
                    """),65536);
                var policy=new NativeReadiness.Policy(false,false,Optional.of(BigInteger.valueOf(actor)),java.time.Duration.ZERO,false);
                var assessed=NativeReadiness.assess(complete,caps,policy);assertTrue(assessed.ready(),assessed::reason);
                assertEquals(BigInteger.valueOf(actor),assessed.key().orElseThrow().playedActor());
                assertEquals(BigInteger.valueOf(actor),assessed.key().orElseThrow().episodeActor());
                assertEquals(assessed,NativeReadiness.assess(complete,DriverJson.object(DriverJson.encode(caps),65536),policy));
                var disconnected=OpportunityJson.object(caps.get("diagnostics"),"diagnostics").with("connected",new OpportunityJson.Bool(false));
                assertFalse(NativeReadiness.assess(complete,caps.with("diagnostics",disconnected),policy).ready());
                var persisted=archive.loadMaterial(driverRef).bytes();var cold=DriverStateSnapshot.decodeComplete(persisted);
                assertEquals(BigInteger.valueOf(actor),cold.session().actorId());assertArrayEquals(persisted,cold.encode());
                assertEquals(complete.semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(complete,true))));
                assertEquals(BigInteger.valueOf(actor),OpportunityJson.integer(DriverJson.object(cold.encode(),DriverCheckpointStore.MAX_DRIVER_BYTES).get("episode_character_id"),"cold signed actor"));
                assertEquals(2,cold.commandHistory().size(),"full history is retained through signed cold DATA decode");
                var unavailableRaw=transport.observe(Instant.now().plusSeconds(10));
                var unavailableFacts=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(unavailableRaw)).facts();
                var unavailableComplete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler()
                        .assemble(unavailableRaw,unavailableFacts,archive.preserveNativeFrame(unavailableRaw)));
                var unavailableTrait=OpportunityJson.object(OpportunityJson.object(unavailableComplete.semantic().get("played_character"),"played")
                        .get("event_trait_membership"),"actual Native05 unavailable metadata");
                assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(actor)),unavailableTrait.get("played_character_id"));
                assertEquals(new OpportunityJson.Text("unavailable"),unavailableTrait.get("status"));
                assertEquals(unavailableComplete.semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(unavailableComplete,true))));
                assertEquals(BigInteger.valueOf(actor),DriverStateSnapshot.decodeComplete(unavailableFacts.driver().encode()).session().actorId());
                assertInstanceOf(NativeTransportDiagnostics.Unobserved.class,transport.diagnostics().production().orElseThrow().adoption(),"software bare Seed remains unclassified");
                assertEquals(0,replay.writes,"negative actor never grants an action/native write or private cold restore");
            }
            var model=DriverJson.object(payload,DriverCheckpointStore.MAX_DRIVER_BYTES);
            // Original JSON material, not Python numeric-output parity: opaque finite decimal tokens retain their lexical domain.
            String opaqueDriver=new String(payload,StandardCharsets.UTF_8).replace("\"error\":\"original rejection\"",
                    "\"error\":\"original rejection\",\"opaque_decimal\":1e999,\"signed_zero\":-0.0,\"integral_float\":1.0");
            var opaqueCold=DriverStateSnapshot.decodeComplete(bytes(opaqueDriver));
            var opaqueRound=DriverJson.object(opaqueCold.encode(),DriverCheckpointStore.MAX_DRIVER_BYTES);
            var opaqueRow=OpportunityJson.object(OpportunityJson.array(opaqueRound.get("command_history"),"history").get(1),"row");
            assertEquals(new OpportunityJson.DecimalValue("1e999"),opaqueRow.get("opaque_decimal"));
            assertEquals(new OpportunityJson.DecimalValue("-0.0"),opaqueRow.get("signed_zero"));
            assertEquals(new OpportunityJson.DecimalValue("1.0"),opaqueRow.get("integral_float"));
            for(String invalidToken:List.of("NaN","Infinity","01","1e"))assertThrows(IllegalArgumentException.class,
                    ()->DriverStateSnapshot.decodeComplete(bytes(opaqueDriver.replace("1e999",invalidToken))));
            assertThrows(IllegalArgumentException.class,()->DriverStateSnapshot.decodeComplete(DriverJson.encode(model.with("bridge_pid",new OpportunityJson.DecimalValue("1e999")))));
            for(OpportunityJson.Value malformed:List.<OpportunityJson.Value>of(new OpportunityJson.IntegerValue(BigInteger.valueOf(-1)),
                    new OpportunityJson.IntegerValue(BigInteger.ONE.shiftLeft(31)),new OpportunityJson.Bool(true),new OpportunityJson.DecimalValue("1.0"),new OpportunityJson.Text("1"),OpportunityJson.Nil.INSTANCE))
                assertThrows(IllegalArgumentException.class,()->DriverStateSnapshot.decodeComplete(DriverJson.encode(model.with("episode_character_id",malformed))));
        }
    }
    @Test void actualProducerPublishesVersionThreeFullWarsAndRejectsPartialCurrentFrameBeforeRevisionMint() throws Exception {
        var archive=new MemoryArchive();ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
        String current=STATE.replace("\"active_wars\":[]","\"active_wars\":[{\"war_id\":88,\"player_side\":\"defender\",\"player_relative_war_score\":-5,"
                +"\"allied_armies\":[{\"army_id\":0,\"owner_character_id\":73,\"controllable\":true,\"soldiers\":22}]}]");
        String envelope=snapshot().replace(STATE,current);
        String bad=envelope.replace("\"revision\":9","\"revision\":10").replace("\"player_relative_war_score\":-5","\"player_relative_war_score\":true");
        String next=envelope.replace("\"revision\":9","\"revision\":11");
        var replay=new Replay(send(hello()),send(envelope),send(bad),send(next));var borrowed=new Borrowed();
        var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
        var source=new G2Source("fixture-machine",Instant.now().toString(),"source-data-only-fixture",full);
        try(var transport=new NativeGameTransport(replay,config(),16,16)) {
            var seed=new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty());
            var adopted=DriverBootstrap.adopt(seed,borrowed,new ActionSnapshotReader(journal),transport,source,archive,
                    (ref,max)->archive.loadMaterial(ref).bytes(),receipt->Optional.empty(),4,Instant.now().plusSeconds(10));
            assertEquals(3,adopted.first().identity().observationVersion());
            var armies=OpportunityJson.array(adopted.first().semantic().get("player_armies"),"player_armies");
            assertEquals(1,armies.size());assertEquals(BigInteger.ZERO,OpportunityJson.integer(
                    OpportunityJson.object(armies.get(0),"army").get("army_id"),"army_id"));
            var manifestRef=DriverObservationEvidenceReader.reference(adopted.first().semantic().get("java_driver_facts_evidence"));
            var manifest=archive.loadMaterial(manifestRef);
            var nativeFrame=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,archive.loadNativeFrame(adopted.first().originalEvidence()));
            var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,
                    archive.loadMaterial(DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest)),nativeFrame);
            assertEquals(3,facts.observationVersion());
            assertEquals(adopted.first(),assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler()
                    .assemble(nativeFrame,facts,adopted.first().originalEvidence())));
            assertTrue(OpportunityJson.array(DriverObservationAssembler.originalNativeState(nativeFrame).get("player_armies"),"raw armies").isEmpty());
            var acceptedRaw=transport.observe(Instant.now().plusSeconds(10));
            var accepted=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(acceptedRaw)).facts();
            assertEquals(BigInteger.valueOf(11),accepted.nativeRevision(),"the actual receive loop rejects the intermediate semantic packet once before returning the next valid original");
            var counters=transport.diagnostics().production().orElseThrow();
            assertEquals(BigInteger.ONE,counters.rejectedSnapshotCount());assertEquals(BigInteger.valueOf(3),counters.receivedSnapshotCount());
            assertEquals(BigInteger.TEN,NativeWire.integer(NativeWire.parse(Arrays.copyOfRange(counters.lastRejectedSnapshot().orElseThrow().original().originalPacket().value(),4,
                    counters.lastRejectedSnapshot().orElseThrow().original().originalPacket().value().length)).get("revision"),BigInteger.ZERO,null));
            var diagnostic=OpportunityJson.object(accepted.originalSemanticFields().get("diagnostics"),"actual receive diagnostics");
            assertEquals(BigInteger.ONE,OpportunityJson.integer(diagnostic.get("rejected_state_snapshot_count"),"actual rejection count"));
            assertEquals(BigInteger.TEN,OpportunityJson.integer(OpportunityJson.object(diagnostic.get("last_rejected_state_snapshot"),"actual original rejection").get("revision"),"rejected revision"));
            var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(acceptedRaw,accepted,archive.preserveNativeFrame(acceptedRaw)));
            var exported=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(complete,true));
            var publicDiagnostic=OpportunityJson.object(DriverJson.object(exported.bytes(),RawJson.MAXIMUM_BYTES).get("diagnostics"),"public current diagnostic");
            assertEquals(new OpportunityJson.Text("1"),publicDiagnostic.get("rejected_state_snapshot_count"));
            assertEquals(new OpportunityJson.Text("0"),publicDiagnostic.get("snapshot_publish_diagnostic_count"));
            assertEquals(new OpportunityJson.IntegerValue(BigInteger.TEN),OpportunityJson.object(publicDiagnostic.get("last_rejected_state_snapshot"),"public raw rejection").get("revision"));
            assertEquals(OpportunityJson.toNode(complete.semantic()),OpportunityJson.toNode(PublicSnapshotCodec.decode(exported)));
            assertEquals(BigInteger.valueOf(3),accepted.publicRevision(),"malformed full War cannot mint a public fact revision");
            assertEquals(3,accepted.observationVersion());assertEquals(0,replay.writes);
        }
    }
    @Test void actualSevenFieldReceiveFingerprintPublicAndDiskReplayShareTheOriginalRawProjection() throws Exception {
        var archive=new MemoryArchive(temporary.resolve("real-semantic-archive"));
        ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
        var state=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(bytes(STATE),65536);
        state.putObject("active_event");
        var settlement=state.putObject("one_life_settlement").put("ready",1).put("commit_serial",1)
                .put("source_character_id",73).put("record_candidate",1).put("old_record",0).put("record_delta",1)
                .put("blessing_count",0).put("refusal_count",0).put("contract_progress",0).put("record_written",1);
        settlement.putObject("final_score").put("raw",new BigInteger("9007199254740993")).put("scale",new BigInteger("9007199254740992"));
        settlement.putObject("score_before_reject").put("raw",-1).put("scale",BigInteger.TEN.pow(400));
        for(String field:List.of("played_character_gold","played_character_prestige","played_character_piety"))
            state.putObject(field).put("raw",-123456).put("scale",100000);
        state.putObject("pending_character_interaction").put("instance_id",0).put("sender_character_id",74).put("auto_accept_notification",false);
        state.putArray("history").addObject().put("opaque_float",-0.0).put("integral_float",1.0);
        state.withArray("history").add(-0.0);
        state.withArray("history").addArray().add(1.0).addNull().add("opaque nested history");
        state.putObject("top_exclusive_modal_choice_hint").put("root",9).put("pump_epoch",1).put("thread_id",2);
        String validState=new String(FullJsonTree.encode(state,65536),StandardCharsets.UTF_8);
        String valid=snapshot().replace(STATE,validState);
        var packetList=new java.util.ArrayList<byte[]>();packetList.add(send(hello()));packetList.add(send(valid));
        String[] fields={"active_event","one_life_settlement","played_character","played_character_gold",
                "played_character_prestige","played_character_piety","pending_character_interaction"};
        for(int index=0;index<fields.length;index++) {
            var invalid=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(bytes(STATE),65536);
            invalid.put(fields[index],true);
            String wire=snapshot().replace("\"revision\":9","\"revision\":"+(10+index))
                    .replace(STATE,new String(FullJsonTree.encode(invalid,65536),StandardCharsets.UTF_8));
            packetList.add(send(wire));
        }
        String[] pendingFields={"sender_character_id","instance_id","auto_accept_notification"};
        for(int index=0;index<pendingFields.length;index++) {
            var invalid=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(bytes(STATE),65536);
            var pending=invalid.putObject("pending_character_interaction").put("instance_id",0).put("sender_character_id",74).put("auto_accept_notification",false);
            if(index==2)pending.put(pendingFields[index],0);else pending.put(pendingFields[index],true);
            packetList.add(send(snapshot().replace("\"revision\":9","\"revision\":"+(17+index))
                    .replace(STATE,new String(FullJsonTree.encode(invalid,65536),StandardCharsets.UTF_8))));
        }
        // Same semantic/native identity; GUI pump counters and numeric spelling cannot mint a new public revision.
        String equivalent=valid.replace("\"pump_epoch\":1","\"pump_epoch\":999").replace("\"original_metric\":1.0","\"original_metric\":1");
        packetList.add(send(equivalent));
        var scoredState=state.deepCopy();
        scoredState.putObject("active_event").putArray("options").addObject().put("index",0).put("option_number",1)
                .put("label","actual scored option").put("enabled",true).put("strategy_score",1.2345678901234567);
        String scored=snapshot().replace(STATE,new String(FullJsonTree.encode(scoredState,65536),StandardCharsets.UTF_8));
        packetList.add(send(scored));
        var replay=new Replay(packetList.toArray(byte[][]::new));
        var borrowed=new Borrowed(new WriterContracts.Head(continuity(8),List.of(),List.of(),List.of(),false));
        var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
        var source=new G2Source("fixture-machine",Instant.now().toString(),"actual-seven-semantic-source",full);
        try(var transport=new NativeGameTransport(replay,config(),16,16)) {
            var seed=new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty());
            var adopted=DriverBootstrap.adopt(seed,borrowed,new ActionSnapshotReader(journal),transport,source,archive,
                    (ref,max)->archive.loadMaterial(ref).bytes(),receipt->Optional.empty(),4,Instant.now().plusSeconds(10));
            var exact=DriverObservationEvidenceReader.reference(adopted.first().semantic().get("java_driver_facts_evidence"));
            var manifest=archive.loadMaterial(exact);
            var actual=DriverObservationEvidenceReader.nativeFrame(exact,manifest,archive.loadNativeFrame(adopted.first().originalEvidence()));
            var liveOriginal=transport.latestObservedSnapshot().orElseThrow();
            var canonical=DriverObservationAssembler.canonicalNativeState(actual).semantic();
            var expected=FullJsonTree.parse(original("semantic",valid),65536);
            assertEquals(expected,FullJsonTree.parse(DriverJson.encode(canonical),65536),"actual complete original Python semantic producer and Java shared route");
            assertTrue(OpportunityJson.object(canonical.get("active_event"),"event").get("option_count")==OpportunityJson.Nil.INSTANCE);
            var scores=OpportunityJson.object(canonical.get("one_life_settlement"),"settlement");
            assertEquals(new OpportunityJson.DecimalValue("1.0"),scores.get("final_score"));
            assertEquals(new OpportunityJson.DecimalValue("-0.0"),scores.get("score_before_reject"));
            assertTrue(new String(DriverJson.encode(canonical.get("history")),StandardCharsets.UTF_8).contains("-0.0"));
            var decoded=DriverObservationEvidenceReader.decode(exact,manifest,archive.loadMaterial(
                    DriverObservationEvidenceReader.currentDriverReference(exact,manifest)),actual);
            var rebuilt=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,decoded,adopted.first().originalEvidence()));
            assertEquals(adopted.first(),rebuilt); assertEquals(3,decoded.observationVersion());
            assertEquals(OpportunityJson.object(DriverObservationAssembler.originalNativeState(actual).get("active_event"),"raw event"),new OpportunityJson.Obj(Map.of()));
            assertArrayEquals(send(valid),actual.originalPacket());
            var publicWire=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(rebuilt,true));
            var publicRoundTrip=PublicSnapshotCodec.decode(publicWire);
            assertEquals(rebuilt.semantic(),publicRoundTrip,"all normalized and opaque decimal tokens survive the real public consumer");
            var currentKnown=adopted.authority().withFrozenFacts(borrowed,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
            verifyCanonicalOriginals(archive,borrowed,rebuilt,currentKnown);
            var next=transport.observe(Instant.now().plusSeconds(10));
            var nextFacts=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(next)).facts();
            assertEquals(BigInteger.TEN,transport.diagnostics().production().orElseThrow().rejectedSnapshotCount());
            assertEquals(BigInteger.valueOf(9),next.nativeRevision());
            assertEquals(BigInteger.valueOf(2),nextFacts.publicRevision(),"ten rejected packets, GUI counters and numeric-equivalent spelling do not publish another revision");
            var scoredRaw=transport.observe(Instant.now().plusSeconds(10));
            var scoredFacts=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(scoredRaw)).facts();
            assertEquals(BigInteger.valueOf(3),scoredFacts.publicRevision(),"a real option/score change advances the public revision on the same native identity");
            var scoredComplete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler()
                    .assemble(scoredRaw,scoredFacts,archive.preserveNativeFrame(scoredRaw)));
            var option=OpportunityJson.object(OpportunityJson.array(OpportunityJson.object(scoredComplete.semantic().get("active_event"),"event").get("options"),"options").get(0),"option");
            assertInstanceOf(OpportunityJson.DecimalValue.class,option.get("strategy_score"));
            assertEquals(scoredComplete.semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(scoredComplete,true))));
            int actualReads=replay.reads;
            var stale=assertInstanceOf(DriverObservationFacts.Unavailable.class,adopted.producer().read(liveOriginal));
            assertTrue(stale.reasons().stream().anyMatch(reason->reason.contains("older actual Native frame")),
                    "an original retained before image must use its archived manifest, never republish as current");
            var cached=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(scoredRaw)).facts();
            assertEquals(scoredFacts.publicRevision(),cached.publicRevision(),"a cached read after stale rejection cannot mint a revision");
            assertEquals(scoredFacts.nativeStateSha256(),cached.nativeStateSha256());
            assertEquals(actualReads,replay.reads,"stale rejection and cached projection perform no transport read");
            var oldReplay=DriverObservationEvidenceReader.decode(exact,manifest,archive.loadMaterial(
                    DriverObservationEvidenceReader.currentDriverReference(exact,manifest)),actual);
            assertEquals(decoded,oldReplay,"historical original remains fully replayable without touching the live revision owner");
            assertEquals(0,replay.writes);
            try(var files=Files.list(archive.disk)) { assertTrue(files.findAny().isPresent()); }
        }
    }
    @Test void actualIngestCountsSkippedProjectionsAndEqualTimeOccurrencesThroughPublicAndPersistedConsumers() throws Exception {
        var archive=new MemoryArchive(temporary.resolve("actual-receive-revisions"));
        ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
        BigInteger max=new BigInteger("18446744073709551615");
        String a=snapshot().replace("\"revision\":9","\"revision\":"+max);
        String b=a.replace("\"original_metric\":1.0","\"original_metric\":2.0");
        String equivalent=a.replace("\"original_metric\":1.0","\"original_metric\":1");
        String rejected=a.replace("\"played_character\":{\"character_id\":73,\"alive\":true}","\"played_character\":true");
        String c=a.replace("\"original_metric\":1.0","\"original_metric\":3.0");
        List<String> frames=List.of(hello(),a,b,a,equivalent,rejected,c);
        var expected=FullJsonTree.parse(original("protocol","["+String.join(",",frames)+"]"),65536);
        var packets=new java.util.ArrayList<byte[]>();for(String frame:frames)packets.add(send(frame));
        var replay=new Replay(packets.toArray(byte[][]::new));
        var borrowed=new Borrowed(new WriterContracts.Head(continuity(8),List.of(),List.of(),List.of(),false));
        var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
        var source=new G2Source("fixture-machine",Instant.now().toString(),"actual-receive-revision-source",full);
        var fixed=java.time.Clock.fixed(Instant.parse("2026-10-25T00:00:00Z"),java.time.ZoneOffset.UTC);
        try(var transport=new NativeGameTransport(replay,config(),16,16,List.of(),fixed)) {
            var adopted=DriverBootstrap.adopt(new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty()),
                    borrowed,new ActionSnapshotReader(journal),transport,source,archive,(ref,limit)->archive.loadMaterial(ref).bytes(),
                    receipt->Optional.empty(),4,Instant.now().plusSeconds(10));
            var first=transport.latestObservedSnapshot().orElseThrow();
            var firstReceipt=transport.acceptedSnapshotRevision(first);firstReceipt.requireOriginal(first);
            assertEquals(expected.get(1).bigIntegerValue(),firstReceipt.publicRevision());
            var accepted=new java.util.ArrayList<NativeObservationPort.ObservedFrame>();accepted.add(first);
            for(int index:List.of(2,3,4,6))accepted.add(transport.observe(Instant.now().plusSeconds(10)));
            assertEquals(first.observedAt(),accepted.getLast().observedAt());
            var last=accepted.getLast();int reads=replay.reads;
            var complete=journal.locked(borrowed,locked->{
                try{return adopted.observations().project(last,Instant.now().plusSeconds(10));}
                catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
            assertEquals(expected.get(6).bigIntegerValue(),complete.identity().frame().revision());
            assertEquals(BigInteger.valueOf(5),complete.identity().frame().revision());
            assertEquals(BigInteger.ONE,transport.diagnostics().production().orElseThrow().rejectedSnapshotCount());
            var known=adopted.authority().withFrozenFacts(borrowed,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
            var facts=known.observation().orElseThrow();var manifest=archive.loadMaterial(facts.semanticFactsEvidence());
            var restoredFacts=DriverObservationEvidenceReader.decode(facts.semanticFactsEvidence(),manifest,archive.loadMaterial(
                    DriverObservationEvidenceReader.currentDriverReference(facts.semanticFactsEvidence(),manifest)),last);
            assertEquals(known,DriverSnapshotFacts.decodeKnownOriginal(DriverSnapshotFacts.encodeKnownOriginal(known),Optional.of(restoredFacts)));
            verifyCanonicalOriginals(archive,borrowed,complete,known);
            var wire=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(complete,true));
            var publicTree=FullJsonTree.parse(wire.bytes(),RawJson.MAXIMUM_BYTES);
            assertTrue(publicTree.get("revision").isTextual());assertEquals("5",publicTree.get("revision").textValue());
            assertEquals(max.toString(),publicTree.get("native_revision").textValue());
            assertEquals(max.toString(),publicTree.get("diagnostics").get("connection_generation").textValue());
            assertEquals(complete.semantic(),PublicSnapshotCodec.decode(wire));
            assertInstanceOf(DriverObservationFacts.Unavailable.class,adopted.producer().read(first));
            var cached=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(last)).facts();
            assertEquals(BigInteger.valueOf(5),cached.publicRevision());assertSame(transport.acceptedSnapshotRevision(last),transport.latestAcceptedSnapshotRevision().orElseThrow());
            assertEquals(reads,replay.reads);assertEquals(0,replay.writes);
        }
    }
    @Test void actualPipeLossAndReplacementReceiveRevisionsMatchOriginalDisconnectAndReconnect() throws Exception {
        String replacementHello=hello().replace("18446744073709551615","18446744073709551614");
        var expected=FullJsonTree.parse(original("protocol-lifecycle","["+hello()+","+snapshot()+",null,null,"
                +replacementHello+","+snapshot()+"]"),65536);
        for(int code:List.of(109,232,233)) {
            var archive=new MemoryArchive();ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
            var borrowed=new Borrowed();var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
            var source=new G2Source("fixture-machine",Instant.now().toString(),"actual-pipe-loss-"+code,full);
            var api=new DisconnectionPipe(send(hello()),send(snapshot()));
            var endpoint=new NativePipeEndpoint(config(),ignored->{},api,new HANDLE(Pointer.createConstant(7)));
            try(var transport=new NativeGameTransport(endpoint,config(),16,16)) {
                var adopted=DriverBootstrap.adopt(new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty()),
                        borrowed,new ActionSnapshotReader(journal),transport,source,archive,(ref,limit)->archive.loadMaterial(ref).bytes(),
                        receipt->Optional.empty(),4,Instant.now().plusSeconds(10));
                var first=transport.latestObservedSnapshot().orElseThrow();var firstRevision=transport.acceptedSnapshotRevision(first);
                assertEquals(expected.get(1).bigIntegerValue(),firstRevision.publicRevision());
                api.failPeekCode=code;
                var loss=assertThrows(java.io.UncheckedIOException.class,()->transport.observe(Instant.now().plusSeconds(10)));
                var transfer=assertInstanceOf(NativePipeEndpoint.TransferFailure.class,loss.getCause());
                assertInstanceOf(NativePacketPort.ConnectionLost.class,transfer.getCause());
                var disconnected=transport.latestStateRevision().orElseThrow();
                assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,disconnected.kind());
                assertEquals(first.session(),disconnected.session());
                assertEquals(expected.get(2).bigIntegerValue(),disconnected.publicRevision());
                assertEquals(code,disconnected.disconnection().orElseThrow().win32Code());
                assertFalse(disconnected.disconnection().orElseThrow().nativeDisconnectSucceeded());
                assertTrue(disconnected.received().order().compareTo(firstRevision.received().order())>0);
                assertSame(firstRevision,transport.latestAcceptedSnapshotRevision().orElseThrow());
                assertInstanceOf(DriverObservationFacts.Unavailable.class,adopted.producer().read(first),
                        "disconnect cannot grant another live projection of the retained archive original");
                int reads=api.reads;assertThrows(java.io.UncheckedIOException.class,()->transport.observe(Instant.now().plusSeconds(10)));
                transport.close();transport.close();
                assertSame(disconnected,transport.latestStateRevision().orElseThrow());
                assertEquals(expected.get(3).bigIntegerValue(),disconnected.publicRevision());
                assertEquals(reads,api.reads);assertEquals(0,api.writes);assertEquals(1,api.closes);assertEquals(0,api.disconnects);
                var reconnect=new DisconnectionPipe(send(replacementHello),send(snapshot()));
                var reconnectEndpoint=new NativePipeEndpoint(config(),ignored->{},reconnect,new HANDLE(Pointer.createConstant(8)));
                try(var replacement=new NativeGameTransport(reconnectEndpoint,config(),16,16)) {
                    var nextSession=replacement.awaitHello(Instant.now().plusSeconds(10));
                    var nextHello=replacement.latestStateRevision().orElseThrow();
                    assertEquals(NativeGameTransport.StateRevisionKind.HELLO,nextHello.kind());
                    assertEquals(expected.get(4).bigIntegerValue(),disconnected.publicRevision().add(nextHello.publicRevision()));
                    var actual=replacement.observe(Instant.now().plusSeconds(10));var received=replacement.acceptedSnapshotRevision(actual);
                    assertEquals(new BigInteger("18446744073709551614"),nextSession.connectionGeneration());
                    assertSame(actual,replacement.latestObservedSnapshot().orElseThrow(),"loaded frame retains the identical occurrence");
                    assertEquals(expected.get(5).bigIntegerValue(),disconnected.publicRevision().add(received.publicRevision()),
                            "actual receiver offset inputs; this software fixture supplies no private NEXT adoption authority");
                    assertEquals(0,reconnect.writes);
                }
            }
        }
    }
    @Test void actualSuccessfulNativeDisconnectAndUnqualifiedCloseAckRemainDifferent() throws Exception {
        var expected=FullJsonTree.parse(original("protocol-lifecycle","["+hello()+","+snapshot()+",null,null]"),65536);
        var api=new DisconnectionPipe(send(hello()),send(snapshot()));
        var endpoint=new NativePipeEndpoint(config(),ignored->{},api,new HANDLE(Pointer.createConstant(7)));
        try(var transport=new NativeGameTransport(endpoint,config(),16,16)) {
            var first=transport.observe(Instant.now().plusSeconds(10));transport.close();
            var retired=transport.latestStateRevision().orElseThrow();
            assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,retired.kind());
            assertTrue(retired.disconnection().orElseThrow().nativeDisconnectSucceeded());
            assertEquals("DisconnectNamedPipe",retired.disconnection().orElseThrow().operation());
            assertEquals(expected.get(2).bigIntegerValue(),retired.publicRevision());
            assertEquals(BigInteger.TWO,transport.acceptedSnapshotRevision(first).publicRevision());
            transport.close();assertSame(retired,transport.latestStateRevision().orElseThrow());
            assertEquals(expected.get(3).bigIntegerValue(),retired.publicRevision());
            assertEquals(1,api.disconnects);assertEquals(1,api.closes);
        }
        var ackOnly=new Replay(send(hello()),send(snapshot()));
        try(var transport=new NativeGameTransport(ackOnly,config(),16,16)) {
            var first=transport.observe(Instant.now().plusSeconds(10));transport.close();
            assertTrue(transport.latestStateRevision().isEmpty(),"close without source custody cannot supply the retired NEXT revision");
            assertEquals(BigInteger.TWO,transport.acceptedSnapshotRevision(first).publicRevision());
        }
    }
    /** Software Win32 bytes; the real Endpoint produces disconnection custody from its native return values. */
    private static final class DisconnectionPipe implements NativePipeEndpoint.Api {
        final ArrayDeque<Byte> bytes=new ArrayDeque<>();int failPeekCode,reads,writes,closes,disconnects;
        DisconnectionPipe(byte[]... packets) { for(byte[] packet:packets)for(byte value:packet)bytes.addLast(value); }
        @Override public HANDLE CreateNamedPipeW(String name,int openMode,int pipeMode,int instances,int output,int input,int timeout,Pointer security) { throw new AssertionError("no physical pipe created"); }
        @Override public boolean ConnectNamedPipe(HANDLE pipe,Pointer overlapped) { return true; }
        @Override public boolean GetNamedPipeClientProcessId(HANDLE pipe,IntByReference client) { client.setValue(42);return true; }
        @Override public boolean PeekNamedPipe(HANDLE pipe,Pointer buffer,int size,Pointer read,IntByReference available,Pointer left) {
            if(failPeekCode!=0) { Native.setLastError(failPeekCode);return false; }
            available.setValue(bytes.size());return true;
        }
        @Override public boolean ReadFile(HANDLE pipe,Pointer buffer,int length,IntByReference read,Pointer overlapped) {
            reads++;int size=Math.min(length,bytes.size());byte[] actual=new byte[size];
            for(int i=0;i<size;i++)actual[i]=bytes.removeFirst();buffer.write(0,actual,0,size);read.setValue(size);return true;
        }
        @Override public boolean WriteFile(HANDLE pipe,Pointer buffer,int length,IntByReference written,Pointer overlapped) { writes++;throw new AssertionError("read-only fixture cannot submit an action"); }
        @Override public boolean DisconnectNamedPipe(HANDLE pipe) { disconnects++;return true; }
        @Override public boolean CloseHandle(HANDLE pipe) { closes++;return true; }
    }
    @Test void actualVersionThreeNoticeConsumerKeepsNativeOwnershipAndOnlyRemovesTransportWrappers() throws Exception {
        var archive=new MemoryArchive();ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
        String firstNotice=heartbeat(1,2,false),secondNotice=heartbeat(3,4,false),businessNotice=heartbeat(5,6,true);
        String ownedState=STATE.replace("\"diagnostics\":{}","\"diagnostics\":{\"last_heartbeat\":"+businessNotice+"}");
        String owned=snapshot().replace(STATE,ownedState);
        String differentOwned=owned.replace("\"sequence\":5","\"sequence\":7");
        var replay=new Replay(send(hello()),send(firstNotice),send(snapshot()),send(secondNotice),send(snapshot()),
                send(businessNotice),send(snapshot()),send(owned),send(differentOwned));
        var borrowed=new Borrowed();var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
        var source=new G2Source("fixture-machine",Instant.now().toString(),"actual-v3-notice-source",full);
        try(var transport=new NativeGameTransport(replay,config(),16,16)) {
            var adopted=DriverBootstrap.adopt(new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty()),
                    borrowed,new ActionSnapshotReader(journal),transport,source,archive,(ref,max)->archive.loadMaterial(ref).bytes(),
                    receipt->Optional.empty(),4,Instant.now().plusSeconds(10));
            var manifestRef=DriverObservationEvidenceReader.reference(adopted.first().semantic().get("java_driver_facts_evidence"));
            var original=DriverObservationEvidenceReader.nativeFrame(manifestRef,archive.loadMaterial(manifestRef),archive.loadNativeFrame(adopted.first().originalEvidence()));
            var before=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(transport.latestObservedSnapshot().orElseThrow())).facts();
            assertEquals(3,before.observationVersion());
            var firstStable=DriverTransportNoticeStability.originalFields(before,original);
            var afterRaw=transport.observe(Instant.now().plusSeconds(10));
            var after=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(afterRaw)).facts();
            assertEquals(firstStable,DriverTransportNoticeStability.originalFields(after,afterRaw));
            assertNotEquals(before.originalSemanticFields(),after.originalSemanticFields(),"actual transport sequence and time did change");
            var businessRaw=transport.observe(Instant.now().plusSeconds(10));
            var business=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(businessRaw)).facts();
            assertNotEquals(firstStable,DriverTransportNoticeStability.originalFields(business,businessRaw),"business packet extensions stay strict");
            var nativeOwnedRaw=transport.observe(Instant.now().plusSeconds(10));
            var nativeOwned=assertInstanceOf(DriverObservationFacts.Known.class,adopted.producer().read(nativeOwnedRaw)).facts();
            var nativeStable=DriverTransportNoticeStability.originalFields(nativeOwned,nativeOwnedRaw);
            var retained=OpportunityJson.object(OpportunityJson.object(nativeStable.get("diagnostics"),"diagnostics").get("last_heartbeat"),"native-owned heartbeat");
            assertEquals(BigInteger.valueOf(5),OpportunityJson.integer(retained.get("sequence"),"sequence"));
            assertEquals(BigInteger.valueOf(6),OpportunityJson.integer(retained.get("monotonic_ms"),"time"));
            var conflicting=transport.observe(Instant.now().plusSeconds(10));
            assertInstanceOf(DriverObservationFacts.Unavailable.class,adopted.producer().read(conflicting),"current producer cannot overwrite a different native-owned notice");
            var unsupported=new DriverObservationFacts(before.driver(),before.driverVersion(),before.episodeEpoch(),before.transport(),
                    before.snapshotId(),before.nativeRevision(),before.nativeStateSha256(),before.publicRevision(),4,before.source(),
                    before.originalSemanticFields(),before.semanticFactsEvidence());
            assertThrows(IllegalArgumentException.class,()->DriverTransportNoticeStability.originalFields(unsupported,original));
            assertEquals(0,replay.writes);
        }
    }
    @Test void originalUnknownReceiptStaysReadOnlyAndDoesNotRequestReplayCoverage() throws Exception {
        var archive=new MemoryArchive();ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
        var source=new G2Source("fixture-machine",Instant.now().toString(),"original-source-fixture",full);
        var before=new ProposalLifecycle.ObservationIdentity("fixture-machine",game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.valueOf(9),BigInteger.valueOf(53144328)),"original-native-snapshot",BigInteger.valueOf(2),"original-episode"),1);
        var expected=new ProposalLifecycle.ExpectedPostcondition(1,before,source,"fixture/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
        var command=new ActionCommand("original-unknown",before,source,"held-original-session",new OperationKey("pause-map"),new OpportunityJson.Obj(Map.of()),expected,
                new JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),Instant.now().plusSeconds(30));
        var unknown=new ActionReceipt(1,8,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"original UNKNOWN",List.of(full)));
        var borrowed=new Borrowed();var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(unknown),new ActionJournal.BoundHistoryBasis(full)));
        var replay=new Replay(send(hello()),send(snapshot()));
        try(var transport=new NativeGameTransport(replay,config(),16,16)) {
            var seed=new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty());
            var adopted=DriverBootstrap.adopt(seed,borrowed,new ActionSnapshotReader(journal),transport,source,archive,(ref,max) -> archive.loadMaterial(ref).bytes(),
                    receipt -> { throw new AssertionError("UNKNOWN never creates coverage or replay permission"); },2,Instant.now().plusSeconds(10));
            assertEquals(DriverBootstrap.AdoptionStatus.READ_ONLY_UNCLASSIFIED,adopted.status());
            assertTrue(adopted.incompleteReasons().contains("entry_source_unclassified_no_private_original_or_java_cold_admission"));
            assertTrue(adopted.incompleteReasons().contains("unreconciled_action:original-unknown"));assertEquals(0,replay.writes);
            adopted.authority().withFrozenFacts(borrowed,frozen -> {
                assertInstanceOf(org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Incomplete.class,
                        DriverStateAssembler.project(frozen.state(),frozen.actions(),frozen.activeActionId()));return null;
            });
        }
    }
    @Test void wrongCanonicalBaselineFailsBeforeReadingNativeHello() throws Exception {
        var archive=new MemoryArchive();ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
        var borrowed=new Borrowed();var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.NullHistoryBasis()));
        var replay=new Replay();
        try(var transport=new NativeGameTransport(replay,config(),16,16)) {
            var seed=new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty());
            assertThrows(IllegalArgumentException.class,() -> DriverBootstrap.adopt(seed,borrowed,new ActionSnapshotReader(journal),transport,
                    new G2Source("fixture-machine",Instant.now().toString(),"fixture",full),archive,(ref,max)->archive.loadMaterial(ref).bytes(),receipt->Optional.empty(),2,Instant.now().plusSeconds(10)));
            assertEquals(0,replay.reads);assertEquals(0,replay.writes);
            assertInstanceOf(NativeTransportDiagnostics.Unobserved.class,transport.diagnostics().production().orElseThrow().adoption());
        }
    }
    @Test void actualGenericReadFailureAfterHelloCannotBeReclassifiedAsOneOfTheFourLegacyAdoptionRefusals() throws Exception {
        var archive=new MemoryArchive();ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
        var borrowed=new Borrowed();var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
        var replay=new Replay(send(hello()));
        try(var transport=new NativeGameTransport(replay,config(),16,16)) {
            var seed=new DriverBootstrap.Seed(full,full,3,7,session(),new OpportunityJson.Obj(Map.of()),Optional.empty());
            assertThrows(IOException.class,()->DriverBootstrap.adopt(seed,borrowed,new ActionSnapshotReader(journal),transport,
                    new G2Source("fixture-machine",Instant.now().toString(),"fixture",full),archive,(ref,max)->archive.loadMaterial(ref).bytes(),receipt->Optional.empty(),2,Instant.now().plusSeconds(10)));
            var production=transport.diagnostics().production().orElseThrow();
            assertTrue(production.session().isPresent());assertInstanceOf(NativeTransportDiagnostics.Unobserved.class,production.adoption());
            assertEquals(BigInteger.ZERO,production.rejectedSnapshotCount(),"a generic endpoint I/O failure is not a shared semantic rejection");
            assertEquals(0,replay.writes);
        }
    }
    @Test void bareSeedCannotStageColdWithoutTheActualPrivateMaterialTicket() throws Exception {
        var archive=new MemoryArchive();ExactRef full=archive.preserveMaterial(new RawJson(driverWire()));
        var borrowed=new Borrowed();var journal=new Journal(borrowed,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),new ActionJournal.BoundHistoryBasis(full)));
        var source=new G2Source("fixture-machine",Instant.now().toString(),"unclassified-cold-data-fixture",full);
        var oldGame=new GameGeneration(41,new PythonOnlyUInt64(new BigInteger("134055107000000017")));
        var predecessor=new DriverSnapshotFacts.Stamp(3,7,oldGame,"original-episode","b".repeat(64));
        var replay=new Replay(send(hello()),send(snapshot()));
        try(var transport=new NativeGameTransport(replay,config(),16,16)) {
            var provisional=new DriverBootstrap.Seed(full,full,3,8,session(),new OpportunityJson.Obj(Map.of()),Optional.empty());
            assertThrows(NullPointerException.class,()->DriverBootstrap.stageRestored(provisional,predecessor,borrowed,new ActionSnapshotReader(journal),transport,source,archive,
                    (ref,max)->archive.loadMaterial(ref).bytes(),receipt->Optional.empty(),4,Instant.now().plusSeconds(10),null));
            assertEquals(0,replay.reads);assertEquals(0,replay.writes,"no ticket means no native attempt or fake physical cold positive");
        }
    }
    /** Actual producer archive -> canonical SEM consumer, under this fixture's identical borrowed read-only head. */
    private void verifyCanonicalOriginals(MemoryArchive archive,Borrowed borrowed,DriverObservationAssembler.Complete complete,
            DriverSnapshotFacts.Known known)throws IOException {
        ExactRef semantic=absoluteOriginal("canonical-semantic.json",DriverJson.encode(complete.semantic()));
        ExactRef nativePacket=absoluteOriginal("canonical-native.packet",archive.loadNativeFrame(complete.originalEvidence()));
        ExactRef driver=absoluteOriginal("canonical-driver.json",known.driver().encode());
        ExactRef stamp=absoluteOriginal("canonical-stamp.json",NativeDriverStamp.encode(complete,known));
        var verifier=new NativeSemanticEvidenceVerifier((same,ref,maximum)->{
            assertSame(borrowed,same);
            return Path.of(ref.path()).isAbsolute()?Files.readAllBytes(Path.of(ref.path())):archive.loadMaterial(ref).bytes();
        });
        var identity=new SessionPorts.SessionIdentity(complete.identity().machineId(),complete.identity().game(),complete.sessionId());
        var evidence=new SessionPorts.SemanticEvidence(complete.identity(),semantic,nativePacket,stamp,driver,complete.observedAt());
        assertNotNull(verifier.verify(borrowed,identity,evidence),
                "normalized raw event, fixed-point scores and retained decimal lexemes must verify from the actual original manifest");
        var altered=new java.util.LinkedHashMap<>(complete.semantic().members());
        var metric=assertInstanceOf(OpportunityJson.DecimalValue.class,complete.semantic().get("original_metric"));
        altered.put("original_metric",new OpportunityJson.DecimalValue(new java.math.BigDecimal(metric.token())
                .add(java.math.BigDecimal.ONE).toPlainString()));
        var alteredSemantic=new OpportunityJson.Obj(altered);
        assertNotEquals(complete.semantic(),alteredSemantic,"tamper fixture must change actual original metric DATA");
        assertEquals(DriverObservationAssembler.bindingSha256(complete.semantic()),
                DriverObservationAssembler.bindingSha256(alteredSemantic),"non-binding metric must leave the compact binding unchanged");
        ExactRef wrongSemantic=absoluteOriginal("changed-canonical-semantic.json",DriverJson.encode(alteredSemantic));
        var wrong=new SessionPorts.SemanticEvidence(complete.identity(),wrongSemantic,nativePacket,stamp,driver,complete.observedAt());
        var rejected=assertThrows(IOException.class,()->verifier.verify(borrowed,identity,wrong),
                "normalized content outside the compact binding remains exact");
        assertTrue(rejected.getMessage().contains("canonical archived SEM crossed its actual actor/frame/public revision/Driver originals"),
                rejected.getMessage());
    }
    private ExactRef absoluteOriginal(String name,byte[] bytes)throws IOException {
        Path path=temporary.resolve(name).toAbsolutePath();
        Files.write(path,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);
        return new ExactRef(path.toString(),bytes.length,DriverJson.sha256(bytes));
    }
    private static ContinuityState continuity(long sequence) {
        var row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id","fixture-machine");
        row.put("sequence",sequence);row.put("window_id",1);row.put("status","running");row.put("target_days",10);
        row.put("start_date_raw",53144328);row.put("target_date_raw",53144328+240);row.put("last_settled_date_raw",53144328);
        row.put("last_settled_cycles",1);row.putObject("UNKNOWN").put("historical-request","do-not-replay");
        return ContinuityState.fromJson(row,"fixture-machine");
    }
    private static WriterContracts.Prepared restorePrepared(ContinuityState before,DriverSnapshotFacts.Stamp old,ExactRef after) {
        var details=StrictJson.object();details.put("evidence_id","original-restore-fixture");details.put("source","source-data-only-fixture");
        var delta=details.putObject("driver_snapshot");delta.put("expected_version",old.driverVersion());delta.put("expected_epoch",old.episodeEpoch());
        delta.put("before_sha256",old.driverSha256());delta.put("after_sha256",after.sha256());delta.put("next_epoch",8);
        var game=details.putObject("driver_after_game");game.put("pid",session().game().pid());game.put("creation_filetime",session().game().creationFiletime().value().toString());
        var request=new WriterContracts.Request(org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority.KIND,ContinuityJson.canonical(details),List.of(after));
        var head=new WriterContracts.Head(before,List.of(),List.of(),List.of(),false);
        return new WriterContracts.Prepared(head,request,List.of(),List.of(),before,"c".repeat(64));
    }
    private byte[] send(String frame) throws Exception {
        return original("send",frame);
    }
    private byte[] original(String mode,String frame) throws Exception {
        String python=required("xar.native.producer.python"),source=required("xar.native.producer.source"),sha=required("xar.native.producer.sha256");
        if(!Path.of(python).isAbsolute() || !Path.of(source).isAbsolute() || !sha.matches("[a-f0-9]{64}"))throw new IllegalStateException("NOT EXECUTED: pinned original producer fixture required");
        Path output=temporary.resolve("original-packet-"+(++sequence)+".bin"),error=temporary.resolve("original-packet-"+sequence+".stderr");
        var builder=new ProcessBuilder(python,"-X","utf8","-c",(mode.equals("semantic")||mode.equals("protocol")||mode.equals("protocol-lifecycle"))?SEMANTIC_ORACLE:SEND,source,sha,Base64.getEncoder().encodeToString(bytes(frame)),mode)
                .redirectOutput(output.toFile()).redirectError(error.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        var process=builder.start();
        if(!process.waitFor(30,TimeUnit.SECONDS)) { process.destroyForcibly();throw new IOException("original packet producer timeout"); }
        if(process.exitValue()!=0)throw new IOException("original packet producer failed: "+Files.readString(error,StandardCharsets.UTF_8));
        return Files.readAllBytes(output);
    }
    private static String required(String key) { String value=System.getProperty(key);if(value==null || value.isBlank())throw new IllegalStateException("NOT EXECUTED: required original fixture property missing: "+key);return value; }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] driverWire() {
        var fields=new java.util.LinkedHashMap<>(DriverJson.object(bytes(DRIVER),65536).members());
        fields.put("pipe_name",new OpportunityJson.Text(config().pipeName()));return DriverJson.encode(new OpportunityJson.Obj(fields));
    }
    private static ExactRef ref(byte[] raw) { return new ExactRef("fixture/"+DriverJson.sha256(raw),raw.length,DriverJson.sha256(raw)); }
    private static GameGeneration game() { return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134055108000000017"))); }
    private static NativeObservationPort.TransportSession session() { return new NativeObservationPort.TransportSession("fixture-machine",game(),new BigInteger("18446744073709551615"),"held-original-session"); }
    private static NativePipeEndpoint.Config config() { return new NativePipeEndpoint.Config("\\\\.\\pipe\\original-driver-pipe","fixture-machine",game(),"held-original-session","fixture","0".repeat(64),"fixture-adapter"); }
    private static String hello() { return "{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":18446744073709551615,\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\""+"0".repeat(64)+"\",\"game_adapter_id\":\"fixture-adapter\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}"; }
    private static String snapshot() { return "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"original-native-snapshot\",\"revision\":9,\"state\":"+STATE+"}"; }
    private static String heartbeat(int sequence,int time,boolean business) { return "{\"type\":\"heartbeat\",\"protocol_version\":1,\"pid\":42,\"sequence\":"+sequence+",\"monotonic_ms\":"+time+(business?",\"actual_business_status\":\"changed\"":"")+"}"; }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets;int reads;int writes;
        Replay(byte[]... packets) { this.packets=new ArrayDeque<>(Arrays.asList(packets)); }
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) throws IOException { reads++;if(packets.isEmpty())throw new IOException("original fixture exhausted");return packets.removeFirst(); }
        @Override public void writePacket(byte[] value,Instant deadline) { writes++;throw new AssertionError("read-only bootstrap must send no action"); }
        @Override public void close() { }
    }
    /** Borrowed fixture identity; every path that tries to start another writer transaction fails. */
    private static final class Borrowed implements ContinuityStorePort.Session {
        private final WriterContracts.Head readOnlyHead;
        Borrowed(){this(null);}
        Borrowed(WriterContracts.Head readOnlyHead){this.readOnlyHead=readOnlyHead;}
        @Override public void requireWriter(Path path) { throw new AssertionError("fixture has no physical writer"); }
        @Override public WriterContracts.Pin capturePin(ExactRef ref,int max) { throw new AssertionError("fixture has no physical pins"); }
        @Override public void verifyPin(WriterContracts.Pin pin) { throw new AssertionError("fixture has no physical pins"); }
        @Override public WriterContracts.Head head() { if(readOnlyHead!=null)return readOnlyHead;throw new AssertionError("fixture journal supplies original snapshot"); }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request) { throw new AssertionError("bootstrap cannot preview a writer mutation"); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) { throw new AssertionError("bootstrap cannot commit a writer mutation"); }
        @Override public ExactRef persistedHead() { throw new AssertionError("bootstrap cannot produce another head"); }
    }
    private static final class Journal implements ActionJournal,ActionJournal.LockedJournal {
        final Borrowed expected;Snapshot snapshot;int depth;int borrowedEntries;int nestedEntries;
        Journal(Borrowed expected,Snapshot snapshot) { this.expected=expected;this.snapshot=snapshot; }
        @Override public <T>T locked(ContinuityStorePort.Session borrowed,Function<LockedJournal,T> work) { assertSame(expected,borrowed);borrowedEntries++;depth++;try{return work.apply(this);}finally{depth--;} }
        @Override public <T>T locked(Function<LockedJournal,T> work) { if(depth==0)throw new AssertionError("second writer transaction refused");nestedEntries++;return work.apply(this); }
        @Override public Optional<ActionReceipt> find(String id) { return snapshot.actions().stream().filter(row->row.command().actionId().equals(id)).findFirst(); }
        @Override public ContinuityStorePort.Session writerSession() { return expected; }
        @Override public List<ActionReceipt> unresolved() { return snapshot.actions().stream().filter(row->!row.settled()).toList(); }
        @Override public ActionReceipt append(ActionCommand command,String sha,ActionState state) { throw new AssertionError("bootstrap cannot append an action"); }
        @Override public Snapshot snapshot() { return snapshot; }
    }
    private static final class MemoryArchive implements ActionPorts.OutcomeArchive {
        final Path disk;
        MemoryArchive() { disk=null; }
        MemoryArchive(Path disk) {
            this.disk=disk;
            try { Files.createDirectory(disk); } catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
        }
        final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,byte[]> frames=new HashMap<>();
        private byte[] persist(String kind,ExactRef exact,byte[] original) {
            if(disk==null)return original;
            try {
                Path path=disk.resolve(kind+"-"+exact.sha256()+".bin");
                if(!Files.exists(path))Files.write(path,original,java.nio.file.StandardOpenOption.CREATE_NEW);
                byte[] actual=Files.readAllBytes(path);
                if(!ref(actual).equals(exact))throw new IllegalArgumentException("persisted original archive identity differs");
                return actual;
            } catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
        }
        private byte[] read(String kind,ExactRef exact,byte[] fallback) {
            if(disk==null)return fallback;
            try { return Files.readAllBytes(disk.resolve(kind+"-"+exact.sha256()+".bin")); }
            catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
        }
        @Override public ExactRef preserveMaterial(RawJson original) { ExactRef exact=ref(original.bytes());materials.putIfAbsent(exact,new RawJson(persist("material",exact,original.bytes())));return exact; }
        @Override public RawJson loadMaterial(ExactRef exact) { var retained=materials.get(exact);var value=retained==null?null:new RawJson(read("material",exact,retained.bytes()));if(value==null || !ref(value.bytes()).equals(exact))throw new IllegalArgumentException("actual material absent/drift");return value; }
        @Override public ExactRef materialReferenceOf(RawJson original) { ExactRef exact=ref(original.bytes());if(!materials.containsKey(exact))throw new IllegalArgumentException("original material not archived");return exact; }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { ExactRef exact=ref(original.originalPacket());frames.putIfAbsent(exact,persist("native",exact,original.originalPacket()));return exact; }
        @Override public byte[] loadNativeFrame(ExactRef exact) { var retained=frames.get(exact);var value=retained==null?null:read("native",exact,retained);if(value==null || !ref(value).equals(exact))throw new IllegalArgumentException("actual original frame absent/drift");return value.clone(); }
        private UnsupportedOperationException unused() { return new UnsupportedOperationException("unrelated action mutation is outside read-only original fixture"); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) { throw unused(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { throw unused(); }
        @Override public ExactRef preserveRequest(NativeRequest value) { throw unused(); }
        @Override public NativeRequest loadRequest(ExactRef ref) { throw unused(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { throw unused(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { throw unused(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) { throw unused(); }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { throw unused(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { throw unused(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { throw unused(); }
        @Override public ActionRecord loadRecord(ExactRef ref) { throw unused(); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { throw unused(); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { throw unused(); }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { throw unused(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { throw unused(); }
    }
}
