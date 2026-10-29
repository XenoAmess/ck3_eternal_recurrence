package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.InteractionDirectPublicCodec;
import org.xar.ck3.control.service.root.KnownInteractionsRuntimeInstaller;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.junit.jupiter.api.Assertions.*;

/** Original Python software producers -> actual installed Java contracts/Facade -> public codecs. Never a Root/Game qualification. */
final class InteractionDirectPublicProductionTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z"),DEADLINE=NOW.plusSeconds(60);
    private static final ExactRef REF=new ExactRef("software/direct-interaction-source",1,"a".repeat(64));
    private static final Claims CLAIMS=new Claims(Set.of(),Set.of(),Set.of(),Set.of("foreground-window"));
    private static final String KEY="ordinary_fixture_interaction";
    private static final long RECIPIENT=2147483650L;
    private static ObjectNode corpus;

    @Test void strictPublicArgumentsPreserveFullIdsAndRequiredDecimalRevision() {
        var ordinary=InteractionDirectPublicCodec.ordinaryRequest(args("{\"interaction_key\":\""+KEY+"\",\"recipient_id\":2147483650,\"expected_revision\":\"18446744073709551615\"}"));
        assertEquals(RECIPIENT,ordinary.recipient().value());assertTrue(ordinary.nativeRequest().education().isEmpty());
        assertEquals(ordinary,InteractionDirectPublicCodec.ordinaryRequest(new PublicBindings.Value(InteractionDirectPublicCodec.encodeRequest(ordinary))));
        var pending=InteractionDirectPublicCodec.pendingRequest(args("{\"pending_interaction_id\":-2130706399,\"expected_revision\":\"0\"}"));
        assertEquals(pending,InteractionDirectPublicCodec.pendingRequest(new PublicBindings.Value(InteractionDirectPublicCodec.encodeRequest(pending))));
        for(String value:List.of("null","true","1.0","1","\"01\"","\"18446744073709551616\"")) {
            assertThrows(IllegalArgumentException.class,()->InteractionDirectPublicCodec.ordinaryRequest(args("{\"interaction_key\":\"x\",\"recipient_id\":1,\"expected_revision\":"+value+"}")));
            assertThrows(IllegalArgumentException.class,()->InteractionDirectPublicCodec.pendingRequest(args("{\"pending_interaction_id\":1,\"expected_revision\":"+value+"}")));
        }
        for(String value:List.of("true","1.0","-1","2147483648","null"))
            assertThrows(IllegalArgumentException.class,()->InteractionDirectPublicCodec.pendingRequest(args("{\"pending_interaction_id\":"+value+",\"expected_revision\":\"1\"}")));
        for(String value:List.of("true","1.0","0","4294967295","null"))
            assertThrows(IllegalArgumentException.class,()->InteractionDirectPublicCodec.ordinaryRequest(args("{\"interaction_key\":\"x\",\"recipient_id\":"+value+",\"expected_revision\":\"1\"}")));
        for(String document:List.of("{}","{\"pending_interaction_id\":1}","{\"interaction_key\":\"x\",\"recipient_id\":1}",
                "{\"interaction_key\":\"x\",\"recipient_id\":1,\"expected_revision\":\"1\",\"requested_option_keys\":[]}"))
            assertThrows(IllegalArgumentException.class,()->InteractionDirectPublicCodec.ordinaryRequest(args(document)));
    }
    @Test void originalOrdinaryServiceAvailableUnavailableUnsupportedAndNotReadyUseOneInstalledDecoder()throws Exception {
        for(JsonNode row:original().get("ordinary")) {
            Complete frame=frame(object(row.get("frame")),Build.CROZIER3);Context context=project(frame,Build.CROZIER3);
            var request=new InteractionDirectPublicCodec.Ordinary(new InteractionKey(KEY),new CharacterId(RECIPIENT),context.before().frame().revision());
            var rig=new Rig(context,raw(row.get("native")));var read=rig.facade.queryCharacterInteractionOrdinaryV1(context,request.nativeRequest());
            assertInstanceOf(PlanningReadResult.Known.class,read);var known=(PlanningReadResult.Known<OrdinaryContext>)read;
            assertSame(rig.definitions.ordinaryQuery(),rig.actualContract);assertEquals(known.value(),rig.definitions.ordinaryQuery().replay(known.receipt()));
            var reply=InteractionDirectPublicCodec.ordinary(known,context,request);assertJson(row.get("public"),node(reply.internal()));
            ObjectNode wire=node(InteractionDirectPublicCodec.encode(reply));assertEquals(known.value().availability().available(),wire.get("ordinary_interaction_context_ready").booleanValue());
            assertEquals("7",wire.get("snapshot_revision").textValue());assertEquals(RECIPIENT,wire.path("character_interaction_ordinary_context").path("recipient_id").longValue());
            assertJson(wire,node(raw(wire)));assertEquals(0,rig.submissions);
            if(!row.get("case").textValue().equals("ready"))assertFalse(known.value().readyToInitiate());
        }
    }
    @Test void exactPendingPublicResultMatchesOriginalServiceMirrorsSourceAndSemanticRed()throws Exception {
        ObjectNode row=object(original().get("pending"));Complete frame=frame(object(row.get("frame")),Build.WANDERER6);Context context=project(frame,Build.WANDERER6);
        var rig=new Rig(context,raw(row.get("native")));PendingId instance=context.controls().pending().instance();
        var read=rig.facade.queryPendingCharacterInteractionContextV1(context,instance);assertInstanceOf(PlanningReadResult.Known.class,read);
        var known=(PlanningReadResult.Known<PendingContext>)read;assertSame(rig.definitions.pendingQuery(),rig.actualContract);
        var reply=InteractionDirectPublicCodec.pending(known,context,frame);assertJson(row.get("public"),node(reply.internal()));
        ObjectNode wire=node(InteractionDirectPublicCodec.encode(reply));assertFalse(wire.get("pending_character_interaction_context_ready").booleanValue());
        assertEquals(instance.value(),wire.get("pending_interaction_id").intValue());assertEquals("41",wire.path("binding").path("native_revision").textValue());
        assertEquals("7",wire.path("source").path("revision").textValue());assertEquals(0,rig.submissions);
        ObjectNode wrong=object(row.get("native")).deepCopy();object(wrong.get("pending_character_interaction_context")).put("pending_interaction_id",instance.value()+1);
        ObjectNode idWrong=wrong;assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decode(raw(idWrong),context,instance));
        wrong=object(row.get("native")).deepCopy();object(wrong.get("pending_character_interaction_context")).put("pending_interaction_id",true);
        ObjectNode typedWrong=wrong;assertThrows(IllegalArgumentException.class,()->PendingContextCodec.decode(raw(typedWrong),context,instance));
    }
    @Test void nativeQueueProducerProjectsOriginalFirstAfterAndUnknownNeverReplays()throws Exception {
        ObjectNode row=object(original().get("initiation"));Complete frame=frame(object(row.get("frame")),Build.CROZIER3);Context context=project(frame,Build.CROZIER3);
        var request=new OrdinaryRequest(new InteractionKey(KEY),new CharacterId(RECIPIENT),Optional.empty());var rig=new Rig(context,raw(row.get("native")));
        var command=rig.facade.prepareInitiateCharacterInteractionOrdinaryV1(new ActionContext(context,"software-public-ordinary",OrdinaryPendingPublication.requestExpectation(context),CLAIMS),request);
        assertEquals(0,rig.submissions);assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        assertEquals(OrdinaryPendingPublication.EXPECTATION_SCHEMA,command.expected().observerSchema());
        RawJson prepared=OrdinaryInteractionCodec.request(context,request,true);ObjectNode sent=node(prepared);
        assertEquals(RECIPIENT,sent.get("recipient_id").longValue());assertFalse(sent.has("option_number"));assertFalse(sent.has("accept"));
        OrdinaryInteractionCodec.initiation(raw(row.get("native")),context,request);
        String requestId=row.path("public").path("action_request_id").textValue();String claimPath=row.path("public").path("action_claim_path").textValue();
        RawJson publication=OrdinaryInitiationPreparation.projectPending(raw(row.get("native")),context,frame,requestId,new ExactRef(claimPath,1,"b".repeat(64)));
        assertJson(row.get("public"),node(publication));
        var unknown=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"software request remains unknown",List.of(REF)));
        var archive=new ReceiptArchive(unknown);var response=InteractionDirectPublicCodec.initiation(unknown,archive,publication);
        ObjectNode wire=node(InteractionDirectPublicCodec.encode(response));assertFalse(wire.get("business_effects_verified").booleanValue());
        assertFalse(wire.get("full_product_acceptance_credit").booleanValue());assertFalse(wire.path("action_receipt").path("postcondition_verified").booleanValue());assertFalse(wire.get("replay_allowed").booleanValue());
        assertTrue(OrdinaryPendingPublication.load(unknown,archive,(basis,held)->{throw new AssertionError("no ACK publication may borrow a later frame");},Build.CROZIER3).isEmpty());
        assertEquals(Optional.of(unknown),KnownInteractionsRuntimeInstaller.retainedOrdinary(List.of(unknown),context,request));
        assertThrows(IllegalArgumentException.class,()->KnownInteractionsRuntimeInstaller.retainedOrdinary(List.of(unknown,unknown),context,request));
        assertTrue(KnownInteractionsRuntimeInstaller.retainedOrdinary(List.of(unknown),context,new OrdinaryRequest(new InteractionKey("other"),request.recipient(),Optional.empty())).isEmpty());
        Context successor=project(frame(object(row.get("frame")),Build.CROZIER3,context.actor().longValueExact()+1),Build.CROZIER3);
        assertEquals(context.before().game(),successor.before().game());assertEquals(context.source(),successor.source());assertEquals(context.sessionId(),successor.sessionId());
        assertNotEquals(context.actor(),successor.actor());
        assertTrue(KnownInteractionsRuntimeInstaller.retainedOrdinary(List.of(unknown),successor,request).isEmpty(),"an unresolved predecessor actor cannot retain the successor's ordinary interaction");
        var successorRig=new Rig(successor,raw(row.get("native")));
        var successorCommand=successorRig.facade.prepareInitiateCharacterInteractionOrdinaryV1(new ActionContext(successor,"software-successor-ordinary",OrdinaryPendingPublication.requestExpectation(successor),CLAIMS),request);
        var successorUnknown=new ActionReceipt(1,2,successorCommand,ActionCodec.bodySha256(successorCommand),new ActionState.Unknown(Optional.empty(),Optional.empty(),"successor request remains unknown",List.of(REF)));
        var restoredSuccessor=ActionCodec.decodeCommand(ActionCodec.encodeCommand(successorCommand));assertEquals(successor.actor(),restoredSuccessor.before().frame().identity().player());
        assertEquals(Optional.of(successorUnknown),KnownInteractionsRuntimeInstaller.retainedOrdinary(List.of(unknown,successorUnknown),successor,request));
        ObjectNode noData=node(InteractionDirectPublicCodec.encode(InteractionDirectPublicCodec.unknown(unknown,archive)));assertFalse(noData.get("native_publication_available").booleanValue());
        assertFalse(noData.get("replay_allowed").booleanValue());assertEquals(0,rig.submissions);
    }
    @Test void originalWrongNativeFieldsRejectBeforeAnySubmission()throws Exception {
        ObjectNode row=object(original().get("ordinary").get(0));Complete frame=frame(object(row.get("frame")),Build.CROZIER3);Context current=project(frame,Build.CROZIER3);
        var request=new OrdinaryRequest(new InteractionKey(KEY),new CharacterId(RECIPIENT),Optional.empty());
        for(int mode=0;mode<6;mode++) {
            ObjectNode changed=object(row.get("native")).deepCopy();ObjectNode terms=object(changed.get("character_interaction_ordinary_context"));
            switch(mode){case 0->terms.remove("can_send");case 1->terms.putNull("can_send");case 2->terms.put("can_send",1);case 3->terms.put("recipient_id",true);case 4->terms.put("snapshot_revision",8);case 5->terms.put("business_postcondition_verified",true);default->throw new AssertionError();}
            assertThrows(IllegalArgumentException.class,()->OrdinaryInteractionCodec.query(raw(changed),current,request));
        }
    }
    private static final class Rig {
        final InteractionCapabilities.Installation definitions;final InteractionCapabilities facade;ReadContract<?> actualContract;int submissions;
        Rig(Context current,RawJson result) {
            var refs=new InteractionCapabilities.Sources(REF,REF,REF,REF,REF,REF,REF,REF,REF,REF);
            definitions=new InteractionCapabilities.Installation(refs,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),new InteractionCapabilities.RootHeirSource(){
                @Override public PlanningReadResult<HeirSubject> read(Context value){throw new AssertionError("no heir query");}
                @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context value){throw new AssertionError("no heir query");}
            });
            PlanningReadPort reads=new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
                actualContract=contract;var receipt=receipt(contract,request,result);return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);
            }};
            facade=new InteractionCapabilities(definitions,reads,new ActionCoordinatorPort(){
                @Override public ActionReceipt execute(ActionCommand command){submissions++;throw new AssertionError("public preparation cannot submit");}
                @Override public ActionReceipt reconcile(String id){throw new AssertionError("UNKNOWN cannot reconcile/replay");}
            });
        }
    }
    static PlanningReadReceipt receipt(ReadContract<?> contract,PlanningReadRequest request,RawJson result) {
        String id="software-original-public-read";ObjectNode root=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);root.set("result",node(result));
        byte[] bytes=DriverJson.encodeNode(root);NativeActionPort.AckReceived ack;
        try{ack=new NativeActionPort.AckReceived(id,true,Optional.of(result),new RawJson(bytes),NativeWire.packet(bytes));}catch(java.io.IOException error){throw new AssertionError(error);}
        var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.TWO,request.operation(),REF,REF,"software-direct-public-read",NOW,DEADLINE);
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
    }
    static Complete frame(ObjectNode original,Build build) {
        return frame(original,build,build==Build.WANDERER6?2001:7001);
    }
    static Complete frame(ObjectNode original,Build build,long actor) {
        ObjectNode n=original.deepCopy();
        n.put("map_ready",true).put("speed",3).put("episode_character_id",actor).put("local_player_id",0).put("backend_id","native-headless");n.putNull("active_event");
        n.putObject("played_character").put("character_id",actor).put("alive",true).putNull("betrothed_id").putArray("spouse_ids");
        if(!n.has("pending_character_interaction"))n.putNull("pending_character_interaction");
        ObjectNode diagnostics=n.withObject("diagnostics");diagnostics.put("connection_generation",2).put("bridge_pid",991);
        diagnostics.putObject("hello").put("expected_ck3_version",build.version()).put("expected_ck3_sha256",build.sha256());
        var identity=new ObservationIdentity("software-direct-public",new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(actor),n.get("native_revision").bigIntegerValue(),n.get("date_raw").bigIntegerValue()),n.get("snapshot_id").textValue(),n.get("revision").bigIntegerValue(),n.get("episode_run_id").textValue()),1);
        var source=new G2Source(identity.machineId(),NOW.toString(),build.version(),REF);
        return new Complete(identity,source,"software-direct-session",BigInteger.TWO,DriverJson.object(DriverJson.encodeNode(n),DriverJson.MAX_NATIVE_BYTES),REF,NOW,"c".repeat(64));
    }
    static Context project(Complete frame,Build build){return new RootInteractionContextProjection(build).project(frame,DEADLINE);}
    static synchronized ObjectNode original()throws Exception {
        if(corpus!=null)return corpus;
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(python,"required xar.python missing; no ambient interpreter fallback");assertFalse(python.isBlank());
        assertNotNull(repository,"required xar.repository.root missing; no skipped producer differential");assertFalse(repository.isBlank());repository=Path.of(repository).toRealPath().toString();
        String script="""
            import copy,importlib.util,json,os,pathlib,sys,tempfile
            root=pathlib.Path(os.environ['XAR_SOURCE_REPOSITORY']).resolve(strict=True)
            sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
            import test_ordinary_interaction as ordinary
            import test_pending_character_interaction_context_v1_bridge as pending
            from xar_autoplayer.bridge.service import GameplayBridgeService
            rows=[]
            for mode in ['ready','unavailable','unsupported','not_ready']:
                with tempfile.TemporaryDirectory() as folder:
                    driver=ordinary.MemoryDriver(pathlib.Path(folder))
                    payload=ordinary.context(available=mode!='unavailable')
                    if mode=='unsupported': payload.update(special_payload_present=True,ordinary_context_supported=False,ready_to_initiate=False,unsupported_reason='software_special_payload')
                    if mode=='not_ready': payload.update(can_send=False,ready_to_initiate=False)
                    driver.custom_context=payload
                    before=driver.take_snapshot();native=ordinary.envelope(payload)
                    public=GameplayBridgeService(driver).query_character_interaction_ordinary_v1(ordinary.KEY,ordinary.RECIPIENT,expected_revision=1)
                    rows.append({'case':mode,'frame':before,'native':native,'public':public})
            pd=pending._ServiceDriver();pf=pd.take_snapshot();pv=GameplayBridgeService(pd).query_pending_character_interaction_context_v1(pending.PENDING_ID,expected_revision=pending.PUBLIC_REVISION)
            with tempfile.TemporaryDirectory() as folder:
                driver=ordinary.MemoryDriver(pathlib.Path(folder));before=driver.take_snapshot()
                initiated=GameplayBridgeService(driver).initiate_character_interaction_ordinary_v1(ordinary.KEY,ordinary.RECIPIENT,expected_revision=1)
                initiation={'frame':before,'native':ordinary.native_ack(),'public':initiated}
            json.dump({'ordinary':rows,'pending':{'frame':pf,'native':pending._native_result(),'public':pv},'initiation':initiation},sys.stdout,separators=(',',':'),allow_nan=False)
            """;
        var builder=new ProcessBuilder(python,"-c",script).directory(Path.of(repository).toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY",repository);builder.environment().put("PYTHONPATH",Path.of(repository,"ck3_autonomous_player","src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();var output=new java.util.concurrent.CompletableFuture<byte[]>();
        Thread reader=Thread.ofVirtual().start(()->{try{output.complete(process.getInputStream().readNBytes(1024*1024+1));}catch(java.io.IOException failure){output.completeExceptionally(failure);}});
        process.getOutputStream().close();
        try{assertTrue(process.waitFor(40,java.util.concurrent.TimeUnit.SECONDS),"original software producer timeout");byte[] bytes=output.get(5,java.util.concurrent.TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=1024*1024);corpus=node(new RawJson(bytes));return corpus;}
        finally{if(process.isAlive())process.destroyForcibly();reader.join(5000);}
    }
    private static PublicBindings.Value args(String value){return new PublicBindings.Value(new RawJson(value.getBytes(StandardCharsets.UTF_8)));}
    private static ObjectNode object(JsonNode value){assertInstanceOf(ObjectNode.class,value);return (ObjectNode)value;}
    private static ObjectNode node(RawJson value){return object(DriverJson.toNode(DriverJson.object(value.bytes(),DriverJson.MAX_NATIVE_BYTES)));}
    private static RawJson raw(JsonNode value){return new RawJson(DriverJson.encodeNode(value));}
    private static void assertJson(JsonNode expected,JsonNode actual){assertEquals(DriverJson.fromNode(expected),DriverJson.fromNode(actual));}
    private static final class ReceiptArchive implements ActionPorts.OutcomeArchive {
        private final ActionReceipt value;ReceiptArchive(ActionReceipt value){this.value=value;}
        @Override public ExactRef receiptReferenceOf(ActionReceipt receipt){assertEquals(value,receipt);return REF;}
        @Override public ActionReceipt loadReceipt(ExactRef reference){assertEquals(REF,reference);return value;}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw new UnsupportedOperationException();}@Override public NativeActionPort.DispatchOutcome load(ExactRef value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw new UnsupportedOperationException();}@Override public NativeRequest loadRequest(ExactRef value){throw new UnsupportedOperationException();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw new UnsupportedOperationException();}@Override public ExactRef requestReferenceOf(NativeRequest value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw new UnsupportedOperationException();}@Override public byte[] loadNativeFrame(ExactRef value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveMaterial(RawJson value){throw new UnsupportedOperationException();}@Override public RawJson loadMaterial(ExactRef value){throw new UnsupportedOperationException();}@Override public ExactRef materialReferenceOf(RawJson value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw new UnsupportedOperationException();}@Override public PlanningReadReceipt loadRead(ExactRef value){throw new UnsupportedOperationException();}@Override public ExactRef readReferenceOf(PlanningReadReceipt value){throw new UnsupportedOperationException();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw new UnsupportedOperationException();}@Override public ActionRecord loadRecord(ExactRef value){throw new UnsupportedOperationException();}@Override public ExactRef recordReferenceOf(ActionRecord value){throw new UnsupportedOperationException();}
    }
}
