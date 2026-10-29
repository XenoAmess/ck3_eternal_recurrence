package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.combatwire.*;
import org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import org.xar.ck3.control.wave2.events.registered.BookmarkRaiktorPolicy;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual original Python window producer -> real EventWindowRead full packet/outbound decoder ->
 * immutable archive -> opaque saved scope -> actual Army family prepare. Guards and packets are
 * software inputs. This neither supplies RootGuardFrameLoader authority nor claims a live Native read. */
final class EventSavedScopeReadIntegrationTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-24T04:00:00Z");
    private static final EventWindowModels.Build BUILD=EventWindowModels.Build.CROZIER4;
    private static final String ORACLE="""
        import ast,copy,hashlib,json,sys
        from pathlib import Path
        root=Path(sys.argv[1]); source=root/'ck3_autonomous_player/tests/unit/test_event_window_context_v1_bridge.py'
        contract=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/event_window_context_contract.py'
        war=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_entry_contract.py'
        if hashlib.sha256(source.read_bytes()).hexdigest()!='384208bffa65e183d82a1dd4510f7f7bb99ccb553b3928fac9c7b7f1f6f08463': raise RuntimeError('original fixture drift')
        if hashlib.sha256(contract.read_bytes()).hexdigest()!='c98985f1afe9196331e30c0f9b0cc2a7fadc9507ef6d3c2b77292bc82e619ef4': raise RuntimeError('original contract drift')
        if hashlib.sha256(war.read_bytes()).hexdigest()!='7678a5f561365ae50a915fe9efc2ea71443be70e26cfba3d2032c205ef412c26': raise RuntimeError('original war-entry producer drift')
        nodes=[]
        for n in ast.parse(source.read_text(encoding='utf-8-sig')).body:
            if isinstance(n,ast.Assign) and (isinstance(n.value,ast.Constant) or (isinstance(n.value,ast.UnaryOp) and isinstance(n.value.op,ast.USub) and isinstance(n.value.operand,ast.Constant) and type(n.value.operand.value) is int)): nodes.append(n)
            elif isinstance(n,ast.FunctionDef) and n.name in ('_scope','_indicator_rows','_frame','_snapshot','_raiktor_frame_and_snapshot'): nodes.append(n)
        scope={'copy':copy};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
        frame,snapshot=scope['_raiktor_frame_and_snapshot']()
        sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        from xar_autoplayer.bridge.war_entry_contract import war_entry_assessment_target_scopes
        snapshot['declarable_wars']=[{'target_character_id':84}]
        result=war_entry_assessment_target_scopes(snapshot,[84],event_context=frame)
        print(json.dumps({'window':frame,'snapshot':snapshot,'scopes':result}))
        """;
    private record Fixture(RootEventWindowPublicProductsTest.ArchiveFixture files,PlanningRequest request,
            ReadContract<EventPolicies.ReadPublication> window,PlanningReadReceipt original,ExactRef retained,
            NativeWire.Hello hello,RootReadContractCatalog catalog,ObjectNode oracle) { }

    @Test void originalWindowCustodyFlowsToActualArmyFamilyWithoutLeakingInternalKeyToNative()throws Exception {
        Fixture f=fixture("army",true,true);
        var recommendation=BookmarkRaiktorPolicy.recommend(new BookmarkRaiktorPolicy.Input(
                RetainedJson.object(RetainedJson.parse(StrictJson.canonical(f.oracle().get("window")))),
                RetainedJson.object(RetainedJson.parse(DriverJson.encode(f.request().observations().snapshot()))),
                Map.of(),Set.of("query-war-entry-assessments-v1-1-84"),Optional.empty(),false)).orElseThrow();
        assertEquals(BookmarkRaiktorPolicy.Status.QUERY_REQUIRED,recommendation.status());
        var actualChosen=new OperationKey(((RetainedJson.StringValue)recommendation.wire().get("selected_step")).value());
        var scope=EventWarEntryReadBindings.SavedScope.from(f.request(),84,f.catalog(),f.window(),f.files().archive,f.hello());
        assertEquals(84,scope.targetCharacterId());
        assertEquals(f.oracle().get("scopes"),scope.scopes(context(f.request()),f.request().observations().snapshot(),f.files().archive).toNativeJson());
        assertEquals(OpportunityJson.parse(scope.key().bytes()),OpportunityJson.parse(DriverJson.encode(OpportunityJson.parse(scope.key().bytes()))));
        var base=new CombatSimulationInputsCodec();
        var cache=new CombatObservationCache(base,new CombatPhaseInputsCodec(base,new StockPhaseEventRuntime()));
        PlanningReadPort unused=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("prepare-only fixture cannot issue native reads");}};
        var forecasts=new ArmyForecastReads(f.files().source,f.files().source,unused,cache,
                (original,archive)->{throw new AssertionError("no fabricated Root Driver frame authority");},f.files().archive,
                ()->{throw new AssertionError("prepare-only fixture has no borrowed Game session");});
        var catalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(f.window(),f.files().source)),forecasts.families());
        var call=call(f.request());
        var selected=new ArmyForecastReads.Selection(call,context(f.request()),Optional.of(scope));
        var contract=forecasts.contract(catalog,selected);
        assertEquals(actualChosen,contract.operation(),"the actual dedicated policy choice reaches the installed Army family");
        assertSame(contract,forecasts.contract(catalog,selected));assertTrue(catalog.containsIdentity(contract));
        ObjectNode fields=(ObjectNode)StrictJson.parse(ArmyCallCodec.encode(call).bytes());fields.set("event_saved_scope_read",StrictJson.parse(scope.key().bytes()));
        var read=new PlanningReadRequest(f.request().before(),f.request().source(),f.request().sessionId(),contract.operation(),obj(fields),f.request().deadline());
        NativeRequest nativeRequest=contract.prepare(read,"actual-army-read-prepare");
        assertEquals("query-war-entry-assessments-v1-1-84",nativeRequest.step());
        assertFalse(nativeRequest.additionalFields().objectFieldNames().contains("event_saved_scope_read"));
        assertTrue(read.arguments().members().containsKey("event_saved_scope_read"));
        var ordinary=forecasts.contract(catalog,new ArmyForecastReads.Selection(call,context(f.request())));
        assertNotEquals(ordinary.contractId(),contract.contractId(),"event receipt custody is part of the actual private family identity");
        ObjectNode without=fields.deepCopy();without.remove("event_saved_scope_read");
        assertThrows(IllegalArgumentException.class,()->contract.prepare(new PlanningReadRequest(read.before(),read.source(),read.sessionId(),read.operation(),obj(without),read.deadline()),"missing-scope"));
        assertThrows(IllegalArgumentException.class,()->new ArmyForecastReads.Selection(new ArmyCalls.WarEntry(call.revision(),List.of(new PositiveId(77))),context(f.request()),Optional.of(scope)));
    }

    @Test void dynamicReadPublicationUsesTheActualChosenOperationOriginalDecoderAndHistorySerialization()throws Exception {
        Fixture f=fixture("dynamic",true,true);
        var binding=EventReadBinding.actualReceiptFamily(new OperationKey("software-window-family"),
                operation->operation.equals(f.window().operation()),
                (actual,selected)->new EventReadBinding.ReceiptResolution<>(f.window(),f.original().request().arguments(),PlanningReadResult.Known::value));
        PlanningReadPort actualPort=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
            assertSame(f.window(),contract);assertEquals(f.original().request(),request);
            var restored=f.files().archive.loadRead(f.retained());return new PlanningReadResult.Known<>(contract.decode(restored),restored,f.retained());
        }};
        var captured=assertInstanceOf(EventReadBinding.Captured.class,binding.read(actualPort,f.request(),f.window().operation()));
        assertEquals(f.window().operation(),captured.operation());assertNotEquals(binding.operation(),captured.operation());
        assertEquals(f.retained(),captured.originalReceipt());
        var round=OpportunityJson.object(OpportunityJson.parse(DriverJson.encode(captured.history())),"captured actual history");
        assertEquals(captured.history(),round);assertEquals(new OpportunityJson.Text(EventWindowRead.STEP),round.get("command"));
        assertEquals(f.retained(),ExactRef.fromJson(OpportunityJson.toNode(round.get("native_read_original_receipt"))));
        assertEquals(new OpportunityJson.Text("bookmark.1071"),captured.publication().result().get("event_definition_key"));
        assertThrows(IllegalArgumentException.class,()->binding.read(actualPort,f.request()));
        assertThrows(IllegalArgumentException.class,()->binding.read(actualPort,f.request(),new OperationKey("query-war-entry-assessments-v1-1-84")));
        var crossed=EventReadBinding.actualReceiptFamily(new OperationKey("bad-family"),ignored->true,
                (actual,selected)->new EventReadBinding.ReceiptResolution<>(f.window(),f.original().request().arguments(),PlanningReadResult.Known::value));
        assertThrows(IllegalArgumentException.class,()->crossed.read(actualPort,f.request(),new OperationKey("query-war-entry-assessments-v1-1-84")));
    }

    @Test void savedOnlyReservedNameDoesNotGrantAQueryAndMissingHistoryNeverMintsScope()throws Exception {
        Fixture noTarget=fixture("saved-only",false,true);
        assertTrue(assertThrows(IllegalArgumentException.class,()->EventWarEntryReadBindings.SavedScope.from(noTarget.request(),84,noTarget.catalog(),noTarget.window(),noTarget.files().archive,noTarget.hello())).getMessage().contains("not advertised"));
        Fixture noGeneric=fixture("no-generic",true,false);
        assertThrows(IllegalArgumentException.class,()->EventWarEntryReadBindings.SavedScope.from(noGeneric.request(),84,noGeneric.catalog(),noGeneric.window(),noGeneric.files().archive,noGeneric.hello()));
        Fixture good=fixture("missing",true,true);
        assertThrows(IllegalArgumentException.class,()->EventWarEntryReadBindings.SavedScope.from(good.request().withHistory(List.of()),84,good.catalog(),good.window(),good.files().archive,good.hello()));
        assertThrows(IllegalArgumentException.class,()->EventWarEntryReadBindings.SavedScope.from(good.request(),77,good.catalog(),good.window(),good.files().archive,good.hello()));
        assertThrows(IllegalArgumentException.class,()->EventWarEntryReadBindings.SavedScope.from(good.request(),84,RootReadContractCatalog.staticOnly(List.of()),good.window(),good.files().archive,good.hello()));
        for(String invalid:List.of("query-war-entry-assessments-v1-1-0","query-war-entry-assessments-v1-1-084","query-war-entry-assessments-v1-1-true","query-war-entry-assessments-v1-1-2147483648","query-war-entry-assessments-v1-2-84-77"))
            assertTrue(WarEntryAssessmentCodec.parseStep(invalid).isEmpty());
    }

    @Test void actualAssessmentReceiptMustRetainSameHelloAndWindowCustodyEvenBeforeDomainDecode()throws Exception {
        Fixture f=fixture("receipt",true,true);
        var scope=EventWarEntryReadBindings.SavedScope.from(f.request(),84,f.catalog(),f.window(),f.files().archive,f.hello());
        var operation=new OperationKey("query-war-entry-assessments-v1-1-84");
        var fields=obj(StrictJson.object().set("event_saved_scope_read",StrictJson.parse(scope.key().bytes())));
        var request=new PlanningReadRequest(f.request().before(),f.request().source(),f.request().sessionId(),operation,fields,f.request().deadline());
        var originalGuard=f.original().before().binding();
        var evidence=new GuardEvidence(request.before(),request.source(),request.sessionId(),originalGuard.connectionGeneration(),operation,
                originalGuard.nativeEvidence(),originalGuard.capabilityEvidence(),"synthetic-event-read",NOW,NOW.plusSeconds(60));
        var guard=new PlanningReadGuard(evidence,true,true,true,"a".repeat(64));
        var receipt=new PlanningReadReceipt(request,"software-assessment-boundary",f.original().requestId(),guard,guard,f.original().original());
        scope.requireAssessmentReceipt(receipt);
        var wrong=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),operation,new OpportunityJson.Obj(Map.of()),request.deadline());
        assertThrows(IllegalArgumentException.class,()->scope.requireAssessmentReceipt(new PlanningReadReceipt(wrong,receipt.contractId(),receipt.requestId(),guard,guard,receipt.original())));
        // This boundary record is deliberately never passed off as an Army decoder success or a completed event choice.
        var changed=f.request().observations().snapshot().with("active_event",obj(StrictJson.object().put("instance_id",5).put("option_count",3)));
        assertThrows(IllegalArgumentException.class,()->scope.scopes(context(f.request()),changed,f.files().archive));
        var extended=new Context(f.request().before(),f.request().source(),f.request().sessionId(),f.request().deadline().plusSeconds(1));
        assertThrows(IllegalArgumentException.class,()->scope.scopes(extended,f.request().observations().snapshot(),f.files().archive));
    }

    private Fixture fixture(String name,boolean ordinary,boolean generic)throws Exception {
        var files=new RootEventWindowPublicProductsTest.ArchiveFixture(temporary.resolve(name));
        ObjectNode oracle=oracle();ObjectNode window=(ObjectNode)oracle.get("window"),snapshot=(ObjectNode)oracle.get("snapshot");
        ((ObjectNode)window.get("provenance")).put("root",BUILD.root()).put("idler_vtable_rva",BUILD.vtable()).put("backend_id",BUILD.backend());
        for(JsonNode option:window.get("options"))((ObjectNode)option.get("effect_indicators")).put("coverage",BUILD.coverage());
        if(!ordinary)snapshot.putArray("declarable_wars");
        snapshot.put("snapshot_id","saved-scope-"+name).put("revision",9).put("episode_run_id","software-saved-event-episode").put("map_ready",true);
        snapshot.putArray("player_armies");snapshot.putObject("diagnostics").put("bridge_pid",123).put("connection_generation",11);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(42),BigInteger.valueOf(17),BigInteger.valueOf(741221)),snapshot.get("snapshot_id").textValue(),BigInteger.valueOf(9),"software-saved-event-episode");
        var before=new ObservationIdentity("event-public-protocol-fixture",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),frame,1);
        var source=new G2Source(before.machineId(),NOW.toString(),"SYNTHETIC-SAVED-EVENT-SOFTWARE",files.source);
        var read=new PlanningReadRequest(before,source,"software-saved-scope-session",new OperationKey(EventWindowRead.STEP),obj(snapshot),NOW.plusSeconds(60));
        var contract=EventWindowRead.contract(files.source,actual->assertEquals(read,actual));
        ObjectNode hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",123).put("connection_generation",11)
                .put("bridge_version","synthetic-saved-read").put("expected_ck3_sha256",BUILD.sha256()).put("game_adapter_id","ck3-"+BUILD.version()+"-msvc-x64")
                .put("game_adapter_status","ready").put("ck3_build_match",true);
        var capabilities=hello.putArray("capabilities").add(EventWindowRead.CAPABILITY);if(generic)capabilities.add(EventWarEntryReadBindings.GENERIC_CAPABILITY);
        byte[] helloPacket=NativeWire.packet(StrictJson.canonical(hello));ExactRef helloRef=store(files.root.resolve("hello.packet"),helloPacket);
        ObjectNode result=StrictJson.object().put("step",EventWindowRead.STEP).put("accepted",true).put("status","available").put("query_sequence",1).put("snapshot_revision",17).put("backend_id","native-headless");result.set("current_event_window_context",window);
        String id="saved-window-original";
        ObjectNode envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);envelope.set("result",result);
        byte[] packet=NativeWire.packet(StrictJson.canonical(envelope));ExactRef nativeRef=store(files.root.resolve("native-read.packet"),packet);
        var returned=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        ObjectNode outbound=StrictJson.object().put("type","execute_step").put("protocol_version",1).put("request_id",id).put("step",EventWindowRead.STEP).put("expected_revision",17).put("event_instance_id",window.get("current_event_instance_id").intValue());
        var ack=new NativeActionPort.AckReceived(id,true,returned.result().token().map(token->new RawJson(token.value())),new RawJson(returned.payload().value()),packet,Optional.of(new NativeActionPort.OutboundPacket(id,NativeWire.packet(StrictJson.canonical(outbound)))));
        var guard=new PlanningReadGuard(new GuardEvidence(before,source,read.sessionId(),BigInteger.valueOf(11),read.operation(),nativeRef,helloRef,"synthetic-event-read",NOW,NOW.plusSeconds(60)),true,true,true,"a".repeat(64));
        var receipt=new PlanningReadReceipt(read,contract.contractId(),id,guard,guard,ack);
        ExactRef retained=files.archive.preserveRead(receipt);var decoded=contract.decode(files.archive.loadRead(retained));
        var history=new EventReadBinding.Captured(decoded,read.operation(),id,contract.contractId(),retained,Optional.empty()).history();
        Set<String> observedCapabilities=generic?Set.of(EventWindowRead.CAPABILITY,EventWarEntryReadBindings.GENERIC_CAPABILITY):Set.of(EventWindowRead.CAPABILITY);
        var observation=new PlanningObservation(obj(snapshot),List.of(history),Set.of(),observedCapabilities,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        var planning=new PlanningRequest(before,source,read.sessionId(),read.deadline(),observation);
        return new Fixture(files,planning,contract,receipt,retained,assertInstanceOf(NativeWire.Hello.class,NativeWire.decode(helloPacket)),RootReadContractCatalog.staticOnly(List.of(contract)),oracle);
    }
    private static ObjectNode oracle()throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"mandatory original fixture repository; absence is NOT RUN");assertNotNull(python,"mandatory original Python compatibility interpreter");
        Process process=new ProcessBuilder(python,"-c",ORACLE,repository).redirectErrorStream(true).start();
        try{assertTrue(process.waitFor(30,TimeUnit.SECONDS));byte[] raw=process.getInputStream().readAllBytes();assertEquals(0,process.exitValue(),new String(raw,StandardCharsets.UTF_8));return (ObjectNode)StrictJson.parse(raw);}
        finally{if(process.isAlive())process.destroyForcibly();}
    }
    private static Context context(PlanningRequest request){return new Context(request.before(),request.source(),request.sessionId(),request.deadline());}
    private static ArmyCalls.WarEntry call(PlanningRequest request){return new ArmyCalls.WarEntry(new ArmyCalls.Revision(new Present<>(request.before().frame().revision())),List.of(new PositiveId(84)));}
    private static OpportunityJson.Obj obj(JsonNode value){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"actual software source");}
    private static ExactRef store(Path path,byte[] raw)throws Exception{Files.write(path,raw);return new ExactRef(path.toString(),raw.length,ActionCodec.sha256(raw));}
}
