package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Actual software Native receive -> codec versus original Python init/ingest/getters. Semantic classification is injected and explicitly separate. */
final class BridgeDiagnosticsOriginalProducerTest {
    @TempDir Path temporary;
    private static final String NATIVE_SHA="eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final String SERVICE_SHA="a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e";
    private static final String HELLO="""
        {"protocol_version":1,"type":"hello","pid":42,"connection_generation":18446744073709551615,"bridge_version":"fixture",
         "expected_ck3_sha256":"0000000000000000000000000000000000000000000000000000000000000000","game_adapter_id":"fixture-adapter",
         "game_adapter_status":"ready","ck3_build_match":true,"capabilities":["game.state.snapshot"]}
        """;
    private static final String HEARTBEAT="""
        {"protocol_version":1,"type":"heartbeat","sequence":7,"connection_generation":18446744073709551615,
         "g2_truce_preview_entry_observer_v1":{"count":2},"vfs_mount_lifecycle_observer_v1":{"mounts":[]},
         "physfs_mounted_data_observer_v1":{"paths":["original/path"]},"unregistered_private_observer":{"value":true}}
        """;
    private static final String PONG="{\"protocol_version\":1,\"type\":\"pong\",\"request_id\":\"actual-pong\"}";
    private static final String ERROR="{\"protocol_version\":1,\"type\":\"error\",\"message\":\"original diagnostic\"}";
    private static final String PUBLISH="{\"protocol_version\":1,\"type\":\"snapshot_publish_diagnostic\",\"request_id\":\"actual-publish\",\"phase\":\"end\",\"status\":\"retained\",\"revision\":9,\"payload_bytes\":128}";
    private static final String STATE="{\"paused\":true,\"map_ready\":true,\"date_raw\":1,\"played_character\":{\"character_id\":73,\"alive\":true},\"top_exclusive_modal_choice_hint\":{\"instance\":\"actual-modal\"}}";
    private static final String SNAPSHOT="{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"actual-snapshot\",\"revision\":9,\"state\":"+STATE+"}";
    private static final String REJECTED="{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"original-rejected\",\"revision\":18446744073709551615,\"state\":{\"date_raw\":1,\"speed\":true,\"paused\":true,\"map_ready\":true,\"active_wars\":true,\"top_exclusive_modal_choice_hint\":{\"original\":\"rejected-raw-hint\"}}}";
    private static final String PENDING="{\"request_id\":\"pending-original\",\"step\":\"query-declarable-wars\",\"status\":\"pending\",\"binding\":{\"snapshot_id\":\"actual-snapshot\",\"revision\":9,\"native_revision\":9,\"episode_run_id\":\"fixture-episode\",\"date_raw\":1,\"paused\":true,\"map_ready\":true,\"player_character_id\":73,\"bridge_pid\":42,\"connection_generation\":18446744073709551615},\"timeout_seconds\":1.5}";
    private static final String FRONTEND="{\"native_request_id\":\"frontend-original\",\"status\":\"prepared_not_submitted\",\"deadline_monotonic\":123456.125,\"initial_remaining_seconds\":0.5,\"snapshot_id\":\"actual-snapshot\",\"native_revision\":9,\"date_raw\":1,\"original_request_replayed\":false}";
    private static final String ORIGINAL="""
        import ast,base64,copy,hashlib,json,sys,threading,types
        from pathlib import Path
        native=Path(sys.argv[1]);service=Path(sys.argv[2])
        if hashlib.sha256(native.read_bytes()).hexdigest()!=sys.argv[3]:raise RuntimeError('original Native producer drift')
        if hashlib.sha256(service.read_bytes()).hexdigest()!=sys.argv[4]:raise RuntimeError('original Service producer drift')
        def method(path,owner,name):
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==owner)
            return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
        # This narrow injected classifier tests the ORIGINAL counting/raw-summary state machine, not semantic normalizer parity.
        def classify_fixture(frame):
            if frame.get('state',{}).get('active_wars') is True:raise ValueError('explicit fixture classification rejection')
            return {'fixture_classification':'accepted'}
        scope={'copy':copy,'threading':threading,'PROTOCOL_VERSION':1,'_semantic_snapshot_from_frame':classify_fixture}
        for path,owner,name in [(native,'NativeProtocolState','__init__'),(native,'NativeProtocolState','ingest'),(native,'NativeProtocolState','_diagnostics_locked'),(native,'NativeHeadlessGameplayDriver','diagnostics'),(service,'GameplayBridgeService','bridge_diagnostics')]:
            node=method(path,owner,name);node.decorator_list=[]
            future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[future,node],type_ignores=[])),str(path),'exec'),scope)
        data=json.loads(base64.b64decode(sys.argv[5]))
        state=types.SimpleNamespace();scope['__init__'](state,data['pipe'])
        statuses=[scope['ingest'](state,data[key]) for key in ['hello','heartbeat','pong','error','publish','rejected','snapshot']]
        if statuses!=['hello','heartbeat','pong','error','snapshot_publish_diagnostic','state_snapshot_rejected','state_snapshot']:
            raise RuntimeError('actual original ingest rejected the expected fixture state machine')
        state.diagnostics=lambda:scope['_diagnostics_locked'](state)
        driver=types.SimpleNamespace(state=state,_transport_error=lambda:None,endpoint=types.SimpleNamespace(transport_diagnostic=lambda:None),
            _driver_state_lock=threading.RLock(),_pending_declaration_query={**data['pending'],'result_frame':{'never':'export'}},_frontend_start_campaign_root_query=copy.deepcopy(data['frontend']))
        driver.diagnostics=lambda:scope['diagnostics'](driver)
        def forbidden():raise RuntimeError('Service must not use capability fallback for a real diagnostic producer')
        result=scope['bridge_diagnostics'](types.SimpleNamespace(driver=driver,capabilities=forbidden))
        print(json.dumps(result,separators=(',',':')))
        """;
    @Test void actualTransportAndSharedCodecMatchOriginalNativeDriverAndServiceWithoutSendingARequest() throws Exception {
        var packets=new Packets(HELLO,HEARTBEAT,PONG,ERROR,PUBLISH,REJECTED,SNAPSHOT);var config=config();
        try(var transport=new NativeGameTransport(packets,config,16,4)) {
            var observed=transport.observe(Instant.parse("2030-01-01T00:00:00Z"));transport.recordAdoptionObserved();int reads=packets.reads;
            var received=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.of(observed));
            var supplement=new BridgeDiagnostics.Supplement(Optional.of(jsonObject(PENDING)),Optional.of(jsonObject(FRONTEND)));
            var report=new BridgeDiagnostics.Report(received,true,supplement);Obj original=BridgeDiagnosticsCodec.internal(report);
            assertEquals(new IntegerValue(BigInteger.ONE),original.get("rejected_state_snapshot_count"));
            assertEquals(new IntegerValue(BigInteger.ONE),original.get("snapshot_publish_diagnostic_count"));
            Obj rejected=object(original.get("last_rejected_state_snapshot"),"last_rejected_state_snapshot");
            assertEquals(new Text("original-rejected"),rejected.get("snapshot_id"));assertEquals(new IntegerValue(NativeWire.UINT64_MAX),rejected.get("revision"));
            assertEquals(new Bool(true),rejected.get("speed"));assertEquals(new IntegerValue(BigInteger.ONE),rejected.get("date_raw"));
            assertEquals(new Bool(true),rejected.get("paused"));assertEquals(new Bool(true),rejected.get("map_ready"));
            Obj python=originalProducer(config.pipeName());Obj pythonRejected=object(python.get("last_rejected_state_snapshot"),"last_rejected_state_snapshot");
            assertEquals(new Text("ValueError"),pythonRejected.get("error_type"));assertEquals(new Text("explicit fixture classification rejection"),pythonRejected.get("error"));
            assertEquals(new Text(transport.diagnostics().production().orElseThrow().lastRejectedSnapshot().orElseThrow().errorType()),rejected.get("error_type"));
            assertEquals(new Text(transport.diagnostics().production().orElseThrow().lastRejectedSnapshot().orElseThrow().error()),rejected.get("error"));
            assertEquals(withoutLanguageError(original),withoutLanguageError(python),"actual ingest count/last raw summary/private fields must match; language/classifier errors are checked separately");
            assertEquals(original,BridgeDiagnosticsCodec.decodePublic(BridgeDiagnosticsCodec.encode(report)));
            assertEquals(new Text("18446744073709551615"),DriverJson.object(BridgeDiagnosticsCodec.encode(report).bytes(),RawJson.MAXIMUM_BYTES).get("connection_generation"));
            assertEquals(Set.of("g2_truce_preview_entry_observer_v1","vfs_mount_lifecycle_observer_v1","physfs_mounted_data_observer_v1"),object(original.get("private_observers"),"private_observers").members().keySet());
            var session=observed.session();var otherGame=new GameGeneration(session.game().pid(),new PythonOnlyUInt64(session.game().creationFiletime().value().add(BigInteger.ONE)));
            var crossed=new org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame(
                    new org.xar.ck3.control.application.action.NativeObservationPort.TransportSession(session.machineId(),otherGame,session.connectionGeneration(),session.sessionId()),
                    observed.snapshotId(),observed.nativeRevision(),observed.state(),observed.originalPacket(),observed.observedAt());
            assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.of(crossed)));
            assertEquals(reads,packets.reads);assertEquals(0,packets.writes);
            var missing=new BridgeDiagnostics.MissingInputs(Set.of(BridgeDiagnostics.RequiredInput.REJECTED_STATE_SNAPSHOT_COUNT),Optional.of(received));
            assertSame(received,missing.received().orElseThrow());assertFalse(missing.missing().isEmpty());
        }
    }
    @Test void strictEmptyRequestAndPublicDecimalReaderRejectWrongTypesAndMissingInputs() throws Exception {
        for(var args:List.of(new PublicBindings.Missing(),new PublicBindings.Null(),new PublicBindings.Value(new RawJson("{}".getBytes(StandardCharsets.UTF_8)))))
            assertNotNull(BridgeDiagnosticsCodec.decodeRequest(args));
        for(String value:List.of("[]","true","{\"fresh\":true}","{\"expected_revision\":1}","{\"x\":null}"))
            assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodeRequest(new PublicBindings.Value(new RawJson(value.getBytes(StandardCharsets.UTF_8)))));
        var packets=new Packets(HELLO,HEARTBEAT,SNAPSHOT);
        try(var transport=new NativeGameTransport(packets,config(),8,2)) {
            var observed=transport.observe(Instant.parse("2030-01-01T00:00:00Z"));
            var unobserved=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.of(observed));
            assertEquals(Set.of(BridgeDiagnostics.RequiredInput.TRANSPORT_REFUSAL),assertThrows(BridgeDiagnostics.MissingInputs.class,()->BridgeDiagnostics.requireNativeProduction(unobserved)).missing());
            transport.recordAdoptionObserved();var received=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.of(observed));
            var report=new BridgeDiagnostics.Report(received,true,new BridgeDiagnostics.Supplement(Optional.empty(),Optional.empty()));
            Obj wire=DriverJson.object(BridgeDiagnosticsCodec.encode(report).bytes(),RawJson.MAXIMUM_BYTES);
            assertEquals(new Text("0"),wire.get("rejected_state_snapshot_count"));
            for(var invalid:List.of(new Bool(true),new IntegerValue(BigInteger.ONE),new Text("01"),new Text("18446744073709551616"))) {
                var changed=wire.with("connection_generation",invalid);assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(changed))));
            }
            var fields=new java.util.LinkedHashMap<>(wire.members());fields.remove("transport_refusal");
            assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(new Obj(fields)))));
            assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(wire.with("connected",new IntegerValue(BigInteger.ONE))))));
            var unproved=wire.with("transport_refusal",new Obj(Map.of("unproved_identity",new IntegerValue(NativeWire.UINT64_MAX))));
            assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(unproved))));
            var forged=wire.with("private_observers",new Obj(Map.of()));
            assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(forged))));
            assertEquals(0,packets.writes);
        }
    }
    @Test void actualRejectedRawReceiveAndAdoptionRefusalRemainDistinctFromTheLastAcceptedSemanticPacket() throws Exception {
        var packets=new Packets(HELLO,HEARTBEAT,SNAPSHOT);
        try(var transport=new NativeGameTransport(packets,config(),8,2)) {
            var accepted=transport.observe(Instant.parse("2030-01-01T00:00:00Z"));transport.recordAdoptionObserved();
            packets.add(REJECTED);
            assertThrows(java.io.UncheckedIOException.class,()->transport.observe(Instant.parse("2030-01-01T00:00:00Z")));
            assertArrayEquals(accepted.originalPacket(),transport.latestObservedSnapshot().orElseThrow().originalPacket());
            var raw=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.of(accepted));
            var production=BridgeDiagnostics.requireNativeProduction(raw);
            assertEquals(BigInteger.TWO,production.receivedSnapshotCount());assertEquals(BigInteger.ONE,production.rejectedSnapshotCount());
            assertEquals(Optional.of(jsonObject("{\"original\":\"rejected-raw-hint\"}")),raw.modalChoiceHint());
            int reads=packets.reads;var report=new BridgeDiagnostics.Report(raw,true,new BridgeDiagnostics.Supplement(Optional.empty(),Optional.empty()));
            BridgeDiagnosticsCodec.internal(report);BridgeDiagnosticsCodec.internal(report);
            assertEquals(production,transport.diagnostics().production().orElseThrow());assertEquals(reads,packets.reads);
            var original=transport.diagnostics();var legacy=new NativeGameTransport.TransportDiagnostics(original.receivedState(),original.session(),original.originalHello(),
                    original.latestHeartbeat(),original.latestPong(),original.latestError(),original.latestSnapshotDiagnostic(),original.terminalFailure(),original.lastOriginalPacket());
            var missing=BridgeDiagnosticsCapture.capture(transport.pipeName(),legacy,Optional.of(accepted));
            assertEquals(4,assertThrows(BridgeDiagnostics.MissingInputs.class,()->BridgeDiagnostics.requireNativeProduction(missing)).missing().size());
            assertEquals(reads,packets.reads);assertEquals(0,packets.writes);
        }
        var refusalPackets=new Packets(HELLO);
        try(var refusedTransport=new NativeGameTransport(refusalPackets,config(),8,2)) {
            refusedTransport.awaitHello(Instant.parse("2030-01-01T00:00:00Z"));
            refusedTransport.recordAdoptionRefused(NativeTransportDiagnostics.AdoptionRefusalReason.INVALID_DRIVER_JOURNAL,"OriginalJournalInvalid","original refusal");
            int reads=refusalPackets.reads;
            var refused=BridgeDiagnosticsCapture.capture(refusedTransport.pipeName(),refusedTransport.diagnostics(),Optional.empty());
            Obj value=BridgeDiagnosticsCodec.internal(new BridgeDiagnostics.Report(refused,false,new BridgeDiagnostics.Supplement(Optional.empty(),Optional.empty())));
            assertEquals(new Bool(false),value.get("connected"));Obj refusal=object(value.get("transport_refusal"),"transport_refusal");
            assertEquals(Set.of("schema","exception_type","stage","reason","message","attempted_bridge_pid"),refusal.members().keySet());
            assertEquals(new Text("invalid_driver_journal"),refusal.get("reason"));assertEquals(new IntegerValue(BigInteger.valueOf(42)),refusal.get("attempted_bridge_pid"));
            assertEquals(reads,refusalPackets.reads);assertEquals(0,refusalPackets.writes);
        }
    }
    @Test void oneNativeFormatterKeepsPreAdoptionAbsenceAndOnlyProvedPendingBindingRolesBecomeDecimalStrings() throws Exception {
        var packets=new Packets(HELLO,HEARTBEAT,SNAPSHOT);
        try(var transport=new NativeGameTransport(packets,config(),8,2)) {
            var observed=transport.observe(Instant.parse("2030-01-01T00:00:00Z"));int reads=packets.reads;
            var unobserved=transport.diagnostics().production().orElseThrow();
            Obj before=BridgeDiagnosticsCodec.nativeProductionFields(unobserved);
            assertEquals(Set.of("rejected_state_snapshot_count","last_rejected_state_snapshot","snapshot_publish_diagnostic_count"),before.members().keySet());
            assertFalse(before.members().containsKey("transport_refusal"));assertEquals(4,BridgeDiagnosticsCodec.nativeOwnedFields().size());
            transport.recordAdoptionObserved();var original=transport.diagnostics();
            Obj nativeFields=BridgeDiagnosticsCodec.nativeProductionFields(original.production().orElseThrow());assertSame(Nil.INSTANCE,nativeFields.get("transport_refusal"));
            var captured=BridgeDiagnosticsCapture.capture(transport.pipeName(),original,Optional.of(observed));
            Obj pending=jsonObject(PENDING);Obj binding=object(pending.get("binding"),"binding")
                    .with("revision",new IntegerValue(new BigInteger("90071992547409931234567890")))
                    .with("native_revision",new IntegerValue(NativeWire.UINT64_MAX));pending=pending.with("binding",binding);
            var report=new BridgeDiagnostics.Report(captured,true,new BridgeDiagnostics.Supplement(Optional.of(pending),Optional.empty()));
            Obj internal=BridgeDiagnosticsCodec.internal(report);for(String key:BridgeDiagnosticsCodec.nativeOwnedFields())assertEquals(nativeFields.get(key),internal.get(key));
            RawJson encoded=BridgeDiagnosticsCodec.encode(report);Obj wire=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);
            Obj publicPending=object(wire.get("pending_declaration_query"),"pending_declaration_query"),publicBinding=object(publicPending.get("binding"),"binding");
            assertEquals(new Text("90071992547409931234567890"),publicBinding.get("revision"));
            assertEquals(new Text(NativeWire.UINT64_MAX.toString()),publicBinding.get("native_revision"));
            assertEquals(new Text(NativeWire.UINT64_MAX.toString()),publicBinding.get("connection_generation"));
            assertEquals(internal,BridgeDiagnosticsCodec.decodePublic(encoded));
            for(Value wrong:List.of(new Bool(true),new IntegerValue(BigInteger.ONE),new Text("01"),new Text(NativeWire.UINT64_MAX.add(BigInteger.ONE).toString()))) {
                Obj changed=wire.with("pending_declaration_query",publicPending.with("binding",publicBinding.with("native_revision",wrong)));
                assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(changed))));
            }
            Obj wrongSource=wire.with("pending_declaration_query",publicPending.with("binding",publicBinding.with("connection_generation",new Text("1"))));
            assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(wrongSource))));
            Obj internalOnly=wire.with("pending_declaration_query",publicPending.with("result_frame",new Obj(Map.of())));
            assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(internalOnly))));
            assertEquals(reads,packets.reads);assertEquals(0,packets.writes);
        }
    }

    /** Frontend rows here are strict serialized DATA fixtures, not a constructed live Start journal/source authority. */
    @Test void frontendStatesKeepOpaqueSnapshotIdsAndExactDecimalSecondsWhileOnlyTypedUint64RolesBecomeStrings() throws Exception {
        var packets=new Packets(HELLO,HEARTBEAT,SNAPSHOT);
        try(var transport=new NativeGameTransport(packets,config(),8,2)) {
            var observed=transport.observe(Instant.parse("2030-01-01T00:00:00Z"));transport.recordAdoptionObserved();
            var received=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.of(observed));int reads=packets.reads;
            Obj base=new Obj(Map.of("native_request_id",new Text("actual-coordinator-opaque-request"),"status",new Text("prepared_not_submitted"),
                    "deadline_monotonic",new DecimalValue("12345678.123456789"),"initial_remaining_seconds",new DecimalValue("0.000000001"),
                    "snapshot_id",new Text("opaque-snapshot-90071992547409931234567890"),"native_revision",new IntegerValue(NativeWire.UINT64_MAX),
                    "date_raw",new IntegerValue(BigInteger.ONE),"original_request_replayed",new Bool(false)));
            Obj receivedRow=base.with("status",new Text("native_result_received")).with("native_result_status",new Text("available"))
                    .with("native_query_sequence",new IntegerValue(NativeWire.UINT64_MAX));
            for(Obj row:List.of(base,receivedRow,receivedRow.with("status",new Text("campaign_root_frame_verified")),
                    base.with("status",new Text("query_failed")).with("error",new Text("original failure")),
                    base.with("status",new Text("native_result_pending_at_deadline")).with("error",new Text("original pending")))) {
                var report=new BridgeDiagnostics.Report(received,true,new BridgeDiagnostics.Supplement(Optional.empty(),Optional.of(row)));
                Obj internal=BridgeDiagnosticsCodec.internal(report);
                RawJson encoded=BridgeDiagnosticsCodec.encode(report);Obj publicValue=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);
                Obj publicRow=object(publicValue.get("frontend_start_campaign_root_query"),"frontend");
                assertEquals(row.get("snapshot_id"),publicRow.get("snapshot_id"));
                assertEquals(row.get("deadline_monotonic"),publicRow.get("deadline_monotonic"));
                assertEquals(row.get("initial_remaining_seconds"),publicRow.get("initial_remaining_seconds"));
                assertEquals(new Text(NativeWire.UINT64_MAX.toString()),publicRow.get("native_revision"));
                if(row.members().containsKey("native_query_sequence"))assertEquals(new Text(NativeWire.UINT64_MAX.toString()),publicRow.get("native_query_sequence"));
                assertEquals(internal,BridgeDiagnosticsCodec.decodePublic(encoded));
            }
            for(Value wrong:List.of(new Bool(true),new DecimalValue("5.0"),new Text("5"))) {
                Obj malformed=receivedRow.with("native_query_sequence",wrong);
                var report=new BridgeDiagnostics.Report(received,true,new BridgeDiagnostics.Supplement(Optional.empty(),Optional.of(malformed)));
                assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.encode(report));
                assertEquals(wrong,malformed.get("native_query_sequence"),"malformed original header is retained, never coerced or cleared");
            }
            Obj nullResult=receivedRow.with("native_query_sequence",Nil.INSTANCE).with("native_result_status",Nil.INSTANCE);
            var nullableReport=new BridgeDiagnostics.Report(received,true,new BridgeDiagnostics.Supplement(Optional.empty(),Optional.of(nullResult)));
            assertEquals(BridgeDiagnosticsCodec.internal(nullableReport),BridgeDiagnosticsCodec.decodePublic(BridgeDiagnosticsCodec.encode(nullableReport)));
            for(Obj malformed:List.of(base.with("initial_remaining_seconds",new DecimalValue("0.0")),
                    base.with("snapshot_id",new IntegerValue(BigInteger.ONE)),base.with("original_request_replayed",new Bool(true)),
                    base.with("error",new Text("not a failed state")),receivedRow.with("native_result_status",new Bool(true)))) {
                var report=new BridgeDiagnostics.Report(received,true,new BridgeDiagnostics.Supplement(Optional.empty(),Optional.of(malformed)));
                assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.encode(report));
            }
            var report=new BridgeDiagnostics.Report(received,true,new BridgeDiagnostics.Supplement(Optional.empty(),Optional.of(receivedRow)));
            Obj wire=DriverJson.object(BridgeDiagnosticsCodec.encode(report).bytes(),RawJson.MAXIMUM_BYTES);
            Obj frontend=object(wire.get("frontend_start_campaign_root_query"),"frontend");
            for(Value wrong:List.of(new Text("01"),new Text(NativeWire.UINT64_MAX.add(BigInteger.ONE).toString()),new IntegerValue(BigInteger.ONE),new Bool(true))) {
                Obj changed=wire.with("frontend_start_campaign_root_query",frontend.with("native_query_sequence",wrong));
                assertThrows(IllegalArgumentException.class,()->BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(changed))));
            }
            assertEquals(reads,packets.reads);assertEquals(0,packets.writes);
        }
    }

    @Test void rejectedSnapshotPublicEncodingRoundTripForRawRevisionTokens() throws Exception {
        String[] tokens = {"18446744073709551615", "\"18446744073709551615\"", "true", "1.25", "-3", "null", "MISSING", "9"};
        for (String token : tokens) {
            String rejectedJson;
            if (token.equals("MISSING")) {
                rejectedJson = "{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"original-rejected\",\"state\":{\"date_raw\":1,\"speed\":true,\"paused\":true,\"map_ready\":true,\"active_wars\":true,\"top_exclusive_modal_choice_hint\":{\"original\":\"rejected-raw-hint\"}}}";
            } else {
                rejectedJson = "{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"original-rejected\",\"revision\":" + token + ",\"state\":{\"date_raw\":1,\"speed\":true,\"paused\":true,\"map_ready\":true,\"active_wars\":true,\"top_exclusive_modal_choice_hint\":{\"original\":\"rejected-raw-hint\"}}}";
            }
            var packets = new Packets(HELLO, HEARTBEAT, rejectedJson, SNAPSHOT);
            try (var transport = new NativeGameTransport(packets, config(), 16, 4)) {
                var observed = transport.observe(Instant.parse("2030-01-01T00:00:00Z"));
                transport.recordAdoptionObserved();
                int reads = packets.reads;
                var received = BridgeDiagnosticsCapture.capture(transport.pipeName(), transport.diagnostics(), Optional.of(observed));
                var supplement = new BridgeDiagnostics.Supplement(Optional.empty(), Optional.empty());
                var report = new BridgeDiagnostics.Report(received, true, supplement);
                Obj internal = BridgeDiagnosticsCodec.internal(report);
                Obj internalRejected = object(internal.get("last_rejected_state_snapshot"), "last_rejected_state_snapshot");
                Value expectedRaw = jsonObject(rejectedJson).members().getOrDefault("revision", Nil.INSTANCE);
                assertEquals(expectedRaw, internalRejected.get("revision"));
                RawJson encoded = BridgeDiagnosticsCodec.encode(report);
                Obj publicValue = DriverJson.object(encoded.bytes(), RawJson.MAXIMUM_BYTES);
                Obj publicRejected = object(publicValue.get("last_rejected_state_snapshot"), "last_rejected_state_snapshot");
                String markerField = org.xar.ck3.control.application.driver.RejectedSnapshotPublicEncoding.ENCODING_FIELD;
                if (token.equals("18446744073709551615")) {
                    assertEquals(new Text("18446744073709551615"), publicRejected.get("revision"));
                    assertEquals(new Text("decimal-u64/v1"), publicRejected.get(markerField));
                    assertEquals(1, publicRejected.members().keySet().stream().filter(k -> k.equals(markerField)).count());
                } else {
                    assertEquals(expectedRaw, publicRejected.get("revision"));
                    assertFalse(publicRejected.members().containsKey(markerField));
                }
                assertEquals(internal, BridgeDiagnosticsCodec.decodePublic(encoded));
                if (token.equals("\"18446744073709551615\"")) {
                    Obj unmarked = publicValue.with("last_rejected_state_snapshot", publicRejected.with("revision", new IntegerValue(NativeWire.UINT64_MAX)));
                    assertThrows(IllegalArgumentException.class, () -> BridgeDiagnosticsCodec.decodePublic(new RawJson(DriverJson.encode(unmarked))));
                }
                assertEquals(reads, packets.reads);
                assertEquals(0, packets.writes);
            }
        }
    }

    private static Obj withoutLanguageError(Obj diagnostics) {
        var original=object(diagnostics.get("last_rejected_state_snapshot"),"last_rejected_state_snapshot");
        var fields=new java.util.LinkedHashMap<>(original.members());fields.remove("error_type");fields.remove("error");
        return diagnostics.with("last_rejected_state_snapshot",new Obj(fields));
    }
    private Obj originalProducer(String pipe)throws Exception {
        Path nativeSource=Path.of(required("xar.native.producer.source"));Path service=nativeSource.resolveSibling("service.py");
        StrictPaths.requireAbsolute(nativeSource);Path python=Path.of(required("xar.native.producer.python"));StrictPaths.requireAbsolute(python);
        var input=new Obj(Map.of("pipe",new Text(pipe),"hello",jsonObject(HELLO),"heartbeat",jsonObject(HEARTBEAT),"pong",jsonObject(PONG),"error",jsonObject(ERROR),"publish",jsonObject(PUBLISH),"rejected",jsonObject(REJECTED),"snapshot",jsonObject(SNAPSHOT),"pending",jsonObject(PENDING),"frontend",jsonObject(FRONTEND)));
        Path output=temporary.resolve("original-diagnostics.json"),error=temporary.resolve("original-diagnostics.stderr");
        Process child=new ProcessBuilder(python.toString(),"-X","utf8","-c",ORIGINAL,nativeSource.toString(),service.toString(),NATIVE_SHA,SERVICE_SHA,Base64.getEncoder().encodeToString(DriverJson.encode(input)))
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!child.waitFor(20,TimeUnit.SECONDS)){child.destroyForcibly();throw new IOException("original diagnostics producer timed out");}
        if(child.exitValue()!=0)throw new IOException("original diagnostics producer failed: "+Files.readString(error,StandardCharsets.UTF_8));
        return DriverJson.object(Files.readAllBytes(output),RawJson.MAXIMUM_BYTES);
    }
    private static Obj jsonObject(String json){return DriverJson.object(json.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);}
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT EXECUTED: required original diagnostics fixture property missing: "+key);return value;}
    private static final class StrictPaths {private static void requireAbsolute(Path path){if(!path.isAbsolute())throw new IllegalArgumentException("actual original fixture requires an absolute path");}}
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\offline-diagnostic-fixture","fixture-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"fixture-session","fixture","0".repeat(64),"fixture-adapter");}
    private static final class Packets implements NativePacketPort {
        private final ArrayDeque<byte[]> packets=new ArrayDeque<>();int reads,writes;
        Packets(String... originals){for(String original:originals)add(original);}
        void add(String original){byte[] body=original.getBytes(StandardCharsets.UTF_8);packets.add(ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array());}
        @Override public void verify(){ }
        @Override public void awaitConnection(Instant deadline){ }
        @Override public byte[] readPacket(Instant deadline)throws IOException {reads++;if(packets.isEmpty())throw new IOException("original diagnostic packets exhausted");return packets.removeFirst();}
        @Override public void writePacket(byte[] original,Instant deadline){writes++;throw new AssertionError("diagnostics cannot send a Native request");}
        @Override public void close(){ }
    }
}
