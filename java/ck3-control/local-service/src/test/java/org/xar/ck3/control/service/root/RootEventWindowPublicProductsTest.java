package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original Python fixture producer -> strict real read decoder -> real immutable archive -> existing
 * EventWindowService -> supplied public registry. Packets/guards are explicit synthetic software inputs;
 * no ManagedGame, current Root, capability permit or ledger transition is fabricated. */
final class RootEventWindowPublicProductsTest {
    @TempDir Path temporary;
    private static final String MACHINE="event-public-protocol-fixture";
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final EventWindowModels.Build BUILD=EventWindowModels.Build.CROZIER4;
    private static final String ORIGINAL_FIXTURE="""
        import ast,hashlib,json,sys
        from pathlib import Path
        root=Path(sys.argv[1]); source=root/'ck3_autonomous_player/tests/unit/test_event_window_context_v1_bridge.py'
        contract=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/event_window_context_contract.py'
        if hashlib.sha256(source.read_bytes()).hexdigest()!='384208bffa65e183d82a1dd4510f7f7bb99ccb553b3928fac9c7b7f1f6f08463': raise RuntimeError('original event fixture drift')
        if hashlib.sha256(contract.read_bytes()).hexdigest()!='c98985f1afe9196331e30c0f9b0cc2a7fadc9507ef6d3c2b77292bc82e619ef4': raise RuntimeError('original event contract drift')
        nodes=[]
        for n in ast.parse(source.read_text(encoding='utf-8-sig')).body:
            if isinstance(n,ast.Assign) and (isinstance(n.value,ast.Constant) or (isinstance(n.value,ast.UnaryOp) and isinstance(n.value.op,ast.USub) and isinstance(n.value.operand,ast.Constant) and type(n.value.operand.value) is int)): nodes.append(n)
            elif isinstance(n,ast.FunctionDef) and n.name in ('_scope','_indicator_rows','_frame'): nodes.append(n)
        scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
        print(json.dumps(scope['_frame'](sys.argv[2]),ensure_ascii=True))
        """;

    @Test void sameRegistryBoundaryUsesRealServiceDecoderArchiveAndCompleteOriginalPublicEncoding()throws Exception {
        Fixture f=fixture("known",123,9,"available");PublicBindings registry=new PublicBindings();
        var binding=RootEventWindowPublicProducts.register(registry,f.service()::query_current_event_window_context_v1,f.archive().source);
        assertEquals(EventWindowService.Query.class,binding.requestType());assertEquals(EventWindowService.Response.class,binding.resultType());
        assertEquals(PublicRoutes.Status.DELEGATED,binding.info().status());
        assertEquals(RootEventWindowPublicProducts.class.getName(),binding.info().target().orElseThrow().actualClass());
        assertThrows(IllegalArgumentException.class,()->binding.invoke(arguments(f.event(),9)));assertEquals(0,f.reads().get());
        registry.freeze(Set.of(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1));
        RawJson wire=binding.invoke(arguments(f.event(),9));ObjectNode publicResult=object(wire);
        assertEquals(1,f.reads().get());assertEquals("exact-current-event-window",publicResult.path("scope").textValue());
        assertEquals("9",publicResult.path("queried_revision").textValue());assertEquals("17",publicResult.path("queried_native_revision").textValue());
        assertEquals(f.event(),publicResult.path("binding").path("event_instance_id").intValue());
        ObjectNode publicWindow=f.window().deepCopy();publicWindow.put("snapshot_revision","17");
        assertEquals(publicWindow,publicResult.get("current_event_window_context"));
        assertEquals(f.window().get("options"),publicResult.get("options"));
        assertFalse(publicResult.path("readiness").path("effect_preview_ready").booleanValue());
        assertFalse(publicResult.path("readiness").path("semantic_decision_ready").booleanValue());
        assertFalse(publicResult.has("ordinary_events"));
        var decoded=f.contract().decode(f.receipt());var restored=f.archive().archive.loadRead(f.retained());
        assertEquals(f.receipt(),restored);assertEquals(decoded,f.contract().replay(restored));
        assertEquals(object(EventWindowService.encode(new EventWindowService.Response(new PlanningReadResult.Known<>(decoded,restored,f.retained())))),publicResult);
        assertEquals(List.of(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1),registry.coverage().installed());
        assertTrue(registry.lookup(PublicMethod.SELECT_EVENT_OPTION).isEmpty());assertTrue(registry.lookup(PublicMethod.RESOLVE_ACTIVE_EVENT).isEmpty());
    }
    @Test void everyInvocationResolvesTheSelectedCurrentServiceAndCannotReadThePreviousFrame()throws Exception {
        Fixture first=fixture("first",123,9,"available"),next=fixture("next",124,10,"available");
        AtomicReference<EventWindowService> current=new AtomicReference<>(first.service());PublicBindings registry=new PublicBindings();
        var binding=RootEventWindowPublicProducts.register(registry,query->current.get().query_current_event_window_context_v1(query),first.archive().source);
        registry.freeze(Set.of(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1));
        assertEquals("9",object(binding.invoke(arguments(first.event(),9))).path("queried_revision").textValue());
        current.set(next.service());
        assertThrows(IllegalArgumentException.class,()->binding.invoke(arguments(first.event(),9)));
        assertEquals(0,next.reads().get());
        assertEquals("10",object(binding.invoke(arguments(next.event(),10))).path("queried_revision").textValue());
        assertEquals(1,first.reads().get());assertEquals(1,next.reads().get());
    }
    @Test void missingNullWrongTypesAndWrongWindowFailBeforeTheInstalledReadProducer()throws Exception {
        Fixture f=fixture("bad",123,9,"available");PublicBindings registry=new PublicBindings();
        var binding=RootEventWindowPublicProducts.register(registry,f.service()::query_current_event_window_context_v1,f.archive().source);
        registry.freeze(Set.of(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1));
        for(var missing:List.<PublicBindings.Arguments>of(new PublicBindings.Missing(),new PublicBindings.Null()))assertThrows(IllegalArgumentException.class,()->binding.invoke(missing));
        for(String value:List.of("{}","{\"event_instance_id\":true,\"expected_revision\":9}","{\"event_instance_id\":1,\"expected_revision\":9.0}",
                "{\"event_instance_id\":1,\"expected_revision\":9,\"output_path\":\"elsewhere\"}","{\"event_id\":1,\"expected_revision\":9}",
                "{\"event_instance_id\":2147483648,\"expected_revision\":9}","{\"event_instance_id\":1,\"expected_revision\":18446744073709551616}",
                "{\"event_instance_id\":1,\"expected_revision\":9007199254740992}","{\"event_instance_id\":1,\"expected_revision\":\"09\"}"))
            assertThrows(IllegalArgumentException.class,()->binding.invoke(new PublicBindings.Value(raw(value))));
        assertThrows(IllegalArgumentException.class,()->binding.invoke(arguments(f.event()+1,9)));
        assertThrows(IllegalArgumentException.class,()->binding.invoke(arguments(f.event(),8)));
        assertEquals(0,f.reads().get());
        var maximum=EventWindowService.decode(new PublicBindings.Value(raw("{\"event_instance_id\":2147483647,\"expected_revision\":\"18446744073709551615\"}")));
        assertEquals(Integer.MAX_VALUE,maximum.eventInstanceId());assertEquals(new BigInteger("18446744073709551615"),maximum.expectedRevision());
    }
    @Test void nativeUnavailablePresentationIsRetainedWhileAnUnavailableReadAndInterruptStayUnavailable()throws Exception {
        Fixture f=fixture("native-unavailable",123,9,"unavailable");PublicBindings registry=new PublicBindings();
        var binding=RootEventWindowPublicProducts.register(registry,f.service()::query_current_event_window_context_v1,f.archive().source);
        registry.freeze(Set.of(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1));
        var result=object(binding.invoke(arguments(f.event(),9)));assertEquals("unavailable",result.path("status").textValue());
        assertFalse(result.path("current_event_window_context_ready").booleanValue());assertTrue(result.path("options").isNull());
        var missing=new PlanningReadResult.Unavailable<EventPolicies.ReadPublication>("actual read source unavailable",Optional.empty());
        PublicBindings rejected=new PublicBindings();var route=RootEventWindowPublicProducts.register(rejected,query->new EventWindowService.Response(missing),f.archive().source);
        rejected.freeze(Set.of(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1));
        assertSame(missing,assertThrows(EventWindowService.ReadUnavailable.class,()->route.invoke(arguments(f.event(),9))).original());
        PublicBindings interrupted=new PublicBindings();var interrupt=RootEventWindowPublicProducts.register(interrupted,query->{throw new InterruptedException("current Root retired");},f.archive().source);
        interrupted.freeze(Set.of(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1));assertThrows(InterruptedException.class,()->interrupt.invoke(arguments(f.event(),9)));
    }
    @Test void duplicateQueryRoutesAndAQueryAloneCannotSupplyTheSeparateResolver()throws Exception {
        Fixture f=fixture("inventory",123,9,"available");PublicBindings registry=new PublicBindings();
        RootEventWindowPublicProducts.register(registry,f.service()::query_current_event_window_context_v1,f.archive().source);
        assertThrows(IllegalArgumentException.class,()->RootEventWindowPublicProducts.register(registry,f.service()::query_current_event_window_context_v1,f.archive().source));
        assertThrows(IllegalArgumentException.class,()->registry.freeze(Set.of(PublicMethod.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1,PublicMethod.RESOLVE_ACTIVE_EVENT)));
        assertTrue(registry.lookup(PublicMethod.RESOLVE_ACTIVE_EVENT).isEmpty());assertTrue(registry.lookup(PublicMethod.SELECT_EVENT_OPTION).isEmpty());
    }

    record Fixture(ArchiveFixture archive,ReadContract<EventPolicies.ReadPublication> contract,PlanningReadReceipt receipt,
            ExactRef retained,EventWindowService service,AtomicInteger reads,ObjectNode window,int event) { }
    Fixture fixture(String name,int pid,long publicRevision,String status)throws Exception {
        ArchiveFixture archive=new ArchiveFixture(temporary.resolve(name));ObjectNode window=originalWindow(status);int event=window.path("current_event_instance_id").intValue();
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(42),BigInteger.valueOf(17),BigInteger.valueOf(741221)),
                "event-public-"+publicRevision,BigInteger.valueOf(publicRevision),"software-public-event-episode");
        var identity=new ObservationIdentity(MACHINE,new GameGeneration(pid,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),frame,1);
        G2Source source=new G2Source(MACHINE,NOW.toString(),"SYNTHETIC-EVENT-PUBLIC-SOFTWARE",archive.source);
        ObjectNode semantic=StrictJson.object().put("snapshot_id",frame.snapshotId()).put("revision",publicRevision).put("native_revision",17).put("date_raw",741221)
                .put("paused",true).put("map_ready",true).put("backend_id","native-headless");
        semantic.put("episode_run_id",frame.episodeRunId()).putObject("played_character").put("character_id",frame.identity().player());
        semantic.putArray("active_wars");semantic.putArray("player_armies");semantic.putObject("active_event").put("instance_id",event);
        var request=new PlanningReadRequest(identity,source,"software-event-public-session",new OperationKey(EventWindowRead.STEP),opportunity(semantic),NOW.plusSeconds(60));
        var contract=EventWindowRead.contract(archive.source,actual->assertEquals(request,actual));
        ObjectNode hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",pid).put("connection_generation",11)
                .put("bridge_version","synthetic-public-read").put("expected_ck3_sha256",BUILD.sha256()).put("game_adapter_id","ck3-"+BUILD.version()+"-msvc-x64")
                .put("game_adapter_status","ready").put("ck3_build_match",true);hello.putArray("capabilities").add(EventWindowRead.CAPABILITY);
        ExactRef helloRef=store(archive.root.resolve("hello.packet"),NativeWire.packet(StrictJson.canonical(hello)));
        ObjectNode result=StrictJson.object().put("step",EventWindowRead.STEP).put("accepted",true).put("status",status).put("query_sequence",1).put("snapshot_revision",17).put("backend_id","native-headless");
        result.set("current_event_window_context",window);
        ObjectNode envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","software-public-event-read").put("ok",true);envelope.set("result",result);
        byte[] packet=NativeWire.packet(StrictJson.canonical(envelope));ExactRef nativeRef=store(archive.root.resolve("native-read.packet"),packet);
        var parsed=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        ObjectNode outgoing=StrictJson.object().put("type","execute_step").put("protocol_version",1).put("request_id",parsed.requestId())
                .put("step",EventWindowRead.STEP).put("expected_revision",17).put("event_instance_id",event);
        var outbound=new NativeActionPort.OutboundPacket(parsed.requestId(),NativeWire.packet(StrictJson.canonical(outgoing)));
        var ack=new NativeActionPort.AckReceived(parsed.requestId(),parsed.nativeOk(),parsed.result().token().map(value->new RawJson(value.value())),new RawJson(parsed.payload().value()),packet,Optional.of(outbound));
        var evidence=new GuardEvidence(identity,source,request.sessionId(),BigInteger.valueOf(11),request.operation(),nativeRef,helloRef,"synthetic-software-public-read-only",NOW,NOW.plusSeconds(60));
        var guard=new PlanningReadGuard(evidence,true,true,true,"a".repeat(64));
        var original=new PlanningReadReceipt(request,contract.contractId(),parsed.requestId(),guard,guard,ack);
        ExactRef retained=archive.archive.preserveRead(original);assertEquals(original,archive.archive.loadRead(retained));
        AtomicInteger reads=new AtomicInteger();PlanningReadPort port=new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> actual,PlanningReadRequest current) {
                assertSame(contract,actual);assertEquals(request,current);reads.incrementAndGet();
                var primitive=actual.prepare(current,original.requestId());assertEquals(EventWindowRead.STEP,primitive.step());
                PlanningReadReceipt restored=archive.archive.loadRead(retained);return new PlanningReadResult.Known<>(actual.decode(restored),restored,retained);
            }
        };
        return new Fixture(archive,contract,original,retained,new EventWindowService(port,contract,query->request),reads,window,event);
    }
    /** The existing archive regression layout, with all ledger transitions deliberately forbidden. */
    static final class ArchiveFixture {
        final Path root;final ExactRef source;final NativeOutcomeArchive archive;
        ArchiveFixture(Path root)throws IOException {
            this.root=Files.createDirectory(root);byte[] state=ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"),state);Files.write(root.resolve("anchor.json"),state);Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Files.createDirectory(root.resolve("artifacts"));Files.writeString(root.resolve("reviewed-source.txt"),"synthetic public event protocol fixture");
            source=LedgerFilesFixtureAccess.read(root.resolve("reviewed-source.txt"),100).pin().reference();
            var layout=new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),LedgerFilesFixtureAccess.read(root.resolve("anchor.json"),65536).pin().reference(),MACHINE);
            var guard=StorageWriteGuardTestSupport.create(root,layout.lock(),16*1024*1024);
            var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"),layout.lock(),8*1024*1024),guard);
            var writer=new ContinuityWriter(layout,List.of(source),new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before,Request request){return ContinuityJson.digest(request.detailsObject());}
                @Override public ContinuityState reduce(ContinuityState before,Request request){throw new AssertionError("software archive test cannot commit a ledger transition");}
            },Clock.fixed(NOW,ZoneOffset.UTC),new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),guard);
            archive=new NativeOutcomeArchive(artifacts,writer);
        }
        private static ObjectNode state() {
            ObjectNode row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE).put("sequence",0).put("window_id",1)
                    .put("status","running").put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25).put("start_date_raw",1000)
                    .put("target_date_raw",263992).put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1)
                    .put("automatic_recovery_count",0).put("binding_lineage_count",0);
            row.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");row.putNull("latest_binding");
            row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);row.put("NEXT",11559);return row;
        }
    }
    private static ObjectNode originalWindow(String status)throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"mandatory actual original fixture repository; NOT RUN when missing");assertNotNull(python,"mandatory explicit original Python compatibility fixture interpreter");assertTrue(Path.of(python).isAbsolute());
        Process process=new ProcessBuilder(python,"-c",ORIGINAL_FIXTURE,repository,status).redirectErrorStream(true).start();
        try {
            assertTrue(process.waitFor(30,TimeUnit.SECONDS),"original fixture producer timeout");byte[] raw=process.getInputStream().readAllBytes();assertEquals(0,process.exitValue(),new String(raw,StandardCharsets.UTF_8));
            ObjectNode value=object(new RawJson(raw));ObjectNode provenance=(ObjectNode)value.get("provenance");
            provenance.put("root",BUILD.root()).put("idler_vtable_rva",BUILD.vtable()).put("backend_id",BUILD.backend());
            if(value.get("options").isArray())for(JsonNode option:value.get("options"))((ObjectNode)option.get("effect_indicators")).put("coverage",BUILD.coverage());
            EventWindowCodec.decode(json(value),new EventWindowModels.Binding(BUILD,BigInteger.valueOf(17),741221,value.path("current_event_instance_id").intValue()));return value;
        } finally {if(process.isAlive())process.destroyForcibly();}
    }
    private static PublicBindings.Arguments arguments(int event,long revision){return new PublicBindings.Value(json(StrictJson.object().put("event_instance_id",event).put("expected_revision",revision)));}
    private static OpportunityJson.Obj opportunity(JsonNode value){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"actual synthetic current semantic source");}
    private static RawJson json(JsonNode value){return new RawJson(StrictJson.canonical(value));}
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static ObjectNode object(RawJson value){return (ObjectNode)StrictJson.parse(value.bytes());}
    private static ExactRef store(Path path,byte[] raw)throws IOException {Files.write(path,raw);return new ExactRef(path.toString(),raw.length,ActionCodec.sha256(raw));}
}
