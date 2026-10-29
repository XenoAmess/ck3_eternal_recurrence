package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Retained historical Python DTO + exact mailbox protocol vectors. No current native/build/Root qualification credit. */
final class RegularMaaSubmissionMigrationTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z"),DEADLINE=NOW.plusSeconds(30);
    private static final ExactRef SOURCE=new ExactRef("memory/maa-original-source",1,"a".repeat(64));
    private static ObjectNode retained() throws IOException {
        try(var in=RegularMaaSubmissionMigrationTest.class.getResourceAsStream("/maa/retained-python-create-queued.json")) {
            assertNotNull(in,"mandatory original Python producer fixture; historical machine_id unknown");
            return (ObjectNode)StrictJson.parse(in.readAllBytes()).get("packet").get("structuredContent");
        }
    }
    private static byte[] packet(ObjectNode value) {
        byte[] json=StrictJson.canonical(value);return ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
    }
    private record Vector(ArmyCalls.CreateMaa call,ArmyTypes.Context context,ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.AckReceived ack,Archive archive,ObjectNode originalPublic) { }
    private static Vector vector(ObjectNode original) {
        var source=new G2Source("software-only-machine",NOW.toString(),"1.20.0.3",SOURCE);
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var identity=new ProposalLifecycle.ObservationIdentity(source.machineId(),game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(9),BigInteger.valueOf(10660101)),"actual-before-9",BigInteger.TEN,"episode-original"),1);
        var context=new ArmyTypes.Context(identity,source,"held-original",DEADLINE);
        var call=new ArmyCalls.CreateMaa(new ArmyCalls.Revision(new ArmyTypes.Present<>(BigInteger.TEN)),50,original.get("action_id").textValue(),new ArmyTypes.Missing<>());
        var args=new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1,ArmyCallCodec.encode(call),List.of());
        var operation=new OperationKey(NativeRegularMaaSubmission.STEP);
        var command=new ActionCommand("canonical-root-action",identity,source,context.sessionId(),operation,args.encode(),
                NativeArmyOrdinaryEffects.expected(identity,source,operation,args.raw()),ArmyOrdinaryActionPreparation.claims(call,context),DEADLINE);
        command=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
        var request=ArmyOrdinaryActionPreparation.primitive(call,context,List.of());RegularMaaPrivatePermission.validate(request);
        var guard=new GuardEvidence(identity,source,context.sessionId(),BigInteger.valueOf(5),operation,SOURCE,SOURCE,"software-only-domain-vector",NOW,DEADLINE);
        var attempt=new ActionState.Attempt(original.get("request_id").textValue(),NOW,guard,request);
        var outbound=(ObjectNode)StrictJson.parse(request.additionalFields().bytes());
        outbound.put("type","execute_step").put("protocol_version",1).put("request_id",attempt.requestId()).put("step",operation.value()).put("expected_revision",9);
        var result=StrictJson.object().put("step",operation.value()).put("accepted",true).put("private_build",true).put("advertised",false)
                .put("backend_id","native-headless").put("game_version",original.get("exact_ck3_build").textValue()).put("executable_sha256",original.get("exe_sha256").textValue())
                .put("read_only",false).put("status",original.get("status").textValue()).put("snapshot_revision",9).put("public_revision",10).put("date_raw",10660101)
                .put("capture_epoch",original.get("capture_epoch").bigIntegerValue()).put("action_id",call.actionId());
        result.set("submission",original.get("native_submission").deepCopy());
        var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",attempt.requestId()).put("ok",true);frame.set("result",result);
        byte[] sent=packet(outbound),received=packet(frame);
        var custody=new NativeRequestChronology(new NativeObservationPort.TransportSession(source.machineId(),game,BigInteger.valueOf(5),context.sessionId()),UUID.fromString("00000000-0000-0000-0000-000000000001"),attempt.requestId(),
                NativeRequestChronology.PacketIdentity.of(sent),NativeRequestChronology.PacketIdentity.of(received),
                new NativeRequestChronology.Event(BigInteger.ONE,NOW.plusMillis(1)),new NativeRequestChronology.Event(BigInteger.TWO,NOW.plusMillis(2)),new NativeRequestChronology.Event(BigInteger.valueOf(3),NOW.plusMillis(3)));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(StrictJson.canonical(frame)),received,Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(),sent)),Optional.of(custody));
        var archive=new Archive();archive.preserve(ack);archive.preserveRequest(request);
        return new Vector(call,context,command,attempt,ack,archive,original);
    }
    private static ActionReceipt receipt(Vector v,ActionState state) {return new ActionReceipt(1,1,v.command(),ActionCodec.bodySha256(v.command()),state);}
    @Test void retainedProducerThroughRealPrimitiveOriginalDecoderPublicConsumerAndWireRoundTrip() throws IOException {
        var v=vector(retained());var decoded=NativeRegularMaaSubmission.original(v.command(),v.attempt(),v.ack(),v.archive());
        assertArrayEquals(StrictJson.canonical(v.originalPublic(),StrictJson.EXPLICIT_MAX_BYTES),StrictJson.canonical(decoded.pythonProjection(),StrictJson.EXPLICIT_MAX_BYTES));assertNotEquals(v.command().actionId(),decoded.actionId());
        var receipt=receipt(v,new ActionState.AckReceived(v.attempt(),v.ack()));
        var material=ArmyOrdinaryActionService.resultMaterial(v.call(),receipt,Optional.empty(),v.archive());
        var node=OpportunityJson.toNode(material);assertArrayEquals(StrictJson.canonical(v.originalPublic(),StrictJson.EXPLICIT_MAX_BYTES),StrictJson.canonical(node.get("regular_maa_create"),StrictJson.EXPLICIT_MAX_BYTES));
        assertEquals(v.command().actionId(),node.get("action_id").textValue());assertTrue(node.get("regular_maa_create").get("submitted").booleanValue());
        assertFalse(node.get("world_effect_verified").booleanValue());assertTrue(node.get("independent_material").isNull());
        assertThrows(IllegalArgumentException.class,()->ArmyOrdinaryActionService.resultMaterial(v.call(),receipt,Optional.of(new RawJson(new byte[]{123,125})),v.archive()));
        var encoded=ArmyOrdinaryActionService.encode(new ArmyOrdinaryActionService.Reply(v.call(),v.context(),receipt,material));
        assertEquals(material,ArmyPublicWire.decode(encoded,v.context()));
        assertEquals(receipt,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,v.archive()),v.archive()));
    }
    @Test void fullWidthEpochUnicodeActionAndExplicitNullSurvivePublicAndDurableSerialization() throws IOException {
        var original=retained();original.put("action_id","原件-maa-01").put("capture_epoch",StrictJson.UINT64_MAX);
        var v=vector(original);var receipt=receipt(v,new ActionState.AckReceived(v.attempt(),v.ack()));
        var material=ArmyOrdinaryActionService.resultMaterial(v.call(),receipt,Optional.empty(),v.archive());
        var wire=ArmyOrdinaryActionService.encode(new ArmyOrdinaryActionService.Reply(v.call(),v.context(),receipt,material));
        assertEquals(StrictJson.UINT64_MAX.toString(),StrictJson.parse(wire.bytes()).get("regular_maa_create").get("capture_epoch").textValue());
        assertEquals(material,ArmyPublicWire.decode(wire,v.context()));
        assertEquals(receipt,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,v.archive()),v.archive()));
        var unknown=receipt(v,new ActionState.Unknown(Optional.of(v.attempt()),Optional.empty(),"original result not received; no replay",List.of(SOURCE)));
        var pending=ArmyOrdinaryActionService.resultMaterial(v.call(),unknown,Optional.empty(),v.archive());var n=OpportunityJson.toNode(pending);
        assertTrue(n.get("regular_maa_create").isNull());assertTrue(n.get("regular_maa_original_dispatch").isNull());assertFalse(n.get("automatic_retry").booleanValue());
        assertEquals(unknown,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(unknown,v.archive()),v.archive()));
        assertThrows(IllegalArgumentException.class,()->ArmyOrdinaryActionService.rejectReplay(List.of(unknown),v.call(),v.context()));
    }
    @Test void onlyActualCleanNativeRefusalsCanColdReplayWithZeroNativeReads() throws IOException {
        for(String reason:List.of("native_denied","native_queue_rejected")) {
            var original=retained();original.put("status","rejected").put("reason",reason).put("submitted",false).put("verification_pending",false);
            var inner=(ObjectNode)original.get("native_submission");inner.put("status","rejected").put("reason",reason);
            if(reason.equals("native_denied"))inner.put("native_can_create",false).putNull("native_submit_accepted").putNull("command_pointer_consumed");else inner.put("native_submit_accepted",false);
            var v=vector(original);var decoded=NativeRegularMaaSubmission.original(v.command(),v.attempt(),v.ack(),v.archive());assertArrayEquals(StrictJson.canonical(original,StrictJson.EXPLICIT_MAX_BYTES),StrictJson.canonical(decoded.pythonProjection(),StrictJson.EXPLICIT_MAX_BYTES));
            var rejection=new ActionState.Rejected(v.attempt().requestId(),"native_regular_maa_rejected:"+reason,v.archive().referenceOf(v.ack()));
            var receipt=receipt(v,new ActionState.Settled(v.attempt(),v.ack(),rejection));
            var restored=ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,v.archive()),v.archive());
            NativeEffectEvidence.FrameLoader noFrames=(basis,archive)->{throw new AssertionError("rejection replay must not borrow a new frame");};
            var snapshots=new NativeEffectSnapshots(()->{throw new AssertionError("cold replay must not query native");},v.archive(),noFrames);
            var observer=new NativeArmyOrdinaryEffects(snapshots,(query,command,attempt,after)->{throw new AssertionError("cold replay must not query");},noFrames,Optional.empty());
            assertDoesNotThrow(()->observer.archivedVerifier(v.command().operation(),SOURCE,noFrames).verifier().verify(null,restored,v.archive()));
            assertThrows(IllegalArgumentException.class,()->ArmyOrdinaryActionService.rejectReplay(List.of(restored),v.call(),v.context()));
        }
    }
    @Test void invalidNativeTuplesWrongFieldsAndUnqualifiedPrimitiveFailBeforeMaterial() throws IOException {
        var original=retained();var malformed=original.deepCopy();((ObjectNode)malformed.get("native_submission")).put("native_can_create",1);
        var bad=vector(malformed);assertThrows(IllegalArgumentException.class,()->NativeRegularMaaSubmission.original(bad.command(),bad.attempt(),bad.ack(),bad.archive()));
        var mismatch=original.deepCopy();mismatch.put("status","rejected");var crossed=vector(mismatch);
        assertThrows(IllegalArgumentException.class,()->NativeRegularMaaSubmission.original(crossed.command(),crossed.attempt(),crossed.ack(),crossed.archive()));
        var missing=original.deepCopy();((ObjectNode)missing.get("native_submission")).remove("command_pointer_consumed");var absent=vector(missing);
        assertThrows(IllegalArgumentException.class,()->NativeRegularMaaSubmission.original(absent.command(),absent.attempt(),absent.ack(),absent.archive()));
        var v=vector(original);var fields=(ObjectNode)StrictJson.parse(v.attempt().preparedRequest().additionalFields().bytes());
        for(String field:List.of("expected_public_revision","expected_snapshot_revision","expected_date_raw","expected_player_character_id","type_index")) {
            var wrong=fields.deepCopy();wrong.put(field,true);
            assertThrows(IllegalArgumentException.class,()->RegularMaaPrivatePermission.validate(new NativeRequest(NativeRegularMaaSubmission.STEP,Optional.empty(),new RawJson(StrictJson.canonical(wrong)))));
        }
        fields.put("expected_player_character_id",29830);
        assertThrows(IllegalArgumentException.class,()->RegularMaaPrivatePermission.validate(new NativeRequest(NativeRegularMaaSubmission.STEP,Optional.empty(),new RawJson(StrictJson.canonical(fields)))));
        var noCustody=new NativeActionPort.AckReceived(v.ack().requestId(),true,v.ack().originalResultToken(),v.ack().originalFrame(),v.ack().originalPacket(),v.ack().outbound());v.archive().preserve(noCustody);
        assertThrows(IllegalArgumentException.class,()->NativeRegularMaaSubmission.original(v.command(),v.attempt(),noCustody,v.archive()));
        var undecided=receipt(v,new ActionState.Unknown(Optional.of(v.attempt()),Optional.of(v.ack()),"queued_pending is not material",List.of(SOURCE)));
        assertThrows(IllegalArgumentException.class,()->ArmyOrdinaryActionService.rejectReplay(List.of(undecided),v.call(),v.context()));
    }
    @Test void independentOriginalPythonProcessAgreesWithSameJavaProducerDecoder() throws Exception {
        var repository=java.nio.file.Path.of(required("xar.repository.root")).toRealPath();
        byte[] actual=java.nio.file.Files.readAllBytes(repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/regular_maa_create_private_action_v1.py"));
        assertEquals("6fc9ab51477cee3377f09a0390c35dc141e74572a90463d7c7043daa6d31d134",DriverJson.sha256(actual));
        for(String status:List.of("queued_pending","rejected","unavailable")) {
            var original=retained();var inner=(ObjectNode)original.get("native_submission");original.put("status",status);inner.put("status",status);
            if(status.equals("rejected")){original.put("reason","native_denied");inner.put("reason","native_denied").put("native_can_create",false).putNull("native_submit_accepted").putNull("command_pointer_consumed");}
            if(status.equals("unavailable")){original.put("reason","native_submit_ownership_not_consumed");inner.put("reason","native_submit_ownership_not_consumed").put("command_pointer_consumed",false);}
            original.put("submitted",status.equals("queued_pending")).put("verification_pending",status.equals("queued_pending"));
            var v=vector(original);var input=StrictJson.object();input.set("result",StrictJson.parse(v.ack().originalResultToken().orElseThrow().bytes()));
            String script="""
                import json,sys
                sys.path.insert(0,sys.argv[1]+'/ck3_autonomous_player/src')
                from xar_autoplayer.bridge.regular_maa_create_private_action_v1 import submit_regular_maa_create_private_v1
                value=json.load(sys.stdin)['result']
                class Driver:
                    def __init__(self): self.endpoint=self;self.state=self;self.sent=None
                    def take_snapshot(self):
                        return dict(revision=10,native_revision=9,paused=True,map_ready=True,date_raw=10660101,played_character=dict(character_id=29829,alive=True),diagnostics=dict(hello=dict(expected_ck3_version=value['game_version'],expected_ck3_sha256=value['executable_sha256'])))
                    def send(self,request): self.sent=request
                    def wait_for_command_result(self,request_id,timeout):
                        assert request_id==self.sent['request_id']
                        return dict(type='command_result',protocol_version=1,request_id=request_id,ok=True,result=value)
                driver=Driver()
                result=submit_regular_maa_create_private_v1(driver,expected_revision=10,type_index=value['submission']['type_index'],action_id=value['action_id'])
                assert result['request_id']==driver.sent['request_id']
                print(json.dumps(result,allow_nan=False))
                """;
            var builder=new ProcessBuilder(required("xar.python"),"-B","-I","-c",script,repository.toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.redirectError(ProcessBuilder.Redirect.INHERIT);
            var process=builder.start();try(var stdin=process.getOutputStream()){stdin.write(StrictJson.canonical(input));}
            boolean finished=process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS);if(!finished)process.destroyForcibly();assertTrue(finished,"original producer timeout");assertEquals(0,process.exitValue());
            var python=assertInstanceOf(ObjectNode.class,StrictJson.parse(process.getInputStream().readAllBytes()));var same=vector(python);
            assertArrayEquals(StrictJson.canonical(python,StrictJson.EXPLICIT_MAX_BYTES),StrictJson.canonical(NativeRegularMaaSubmission.original(same.command(),same.attempt(),same.ack(),same.archive()).pythonProjection(),StrictJson.EXPLICIT_MAX_BYTES));
        }
    }
    @Test void canonicalWireComparisonStillRejectsBooleanDecimalAndDifferentIntegerVersion() throws IOException {
        var v=vector(retained());var original=v.ack();var custody=original.custody().orElseThrow();
        byte[] sent=original.outbound().orElseThrow().originalPacket();
        String json=new String(sent,4,sent.length-4,java.nio.charset.StandardCharsets.UTF_8);
        for(String wrong:List.of("true","1.0","2")) {
            String changed=json.replace("\"protocol_version\":1","\"protocol_version\":"+wrong);assertNotEquals(json,changed);
            byte[] body=changed.getBytes(java.nio.charset.StandardCharsets.UTF_8);
            byte[] wire=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
            var bound=new NativeRequestChronology(custody.session(),custody.custodyEpoch(),custody.requestId(),
                    NativeRequestChronology.PacketIdentity.of(wire),custody.originalResponse(),custody.writeEntered(),custody.writeCompleted(),custody.responseReceived());
            var invalid=new NativeActionPort.AckReceived(original.requestId(),true,original.originalResultToken(),original.originalFrame(),original.originalPacket(),
                    Optional.of(new NativeActionPort.OutboundPacket(original.requestId(),wire)),Optional.of(bound));
            v.archive().preserve(invalid);
            assertThrows(IllegalArgumentException.class,()->NativeRegularMaaSubmission.original(v.command(),v.attempt(),invalid,v.archive()));
        }
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("mandatory original Python setting missing: "+key);return value;}
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> dispatches=new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests=new HashMap<>();
        private final Map<ExactRef,RawJson> materials=new HashMap<>();
        private static ExactRef ref(String kind,byte[] bytes){return new ExactRef("memory/"+kind+"/"+ActionCodec.sha256(bytes),bytes.length,ActionCodec.sha256(bytes));}
        private static byte[] bytes(NativeActionPort.DispatchOutcome value) {
            var ack=(NativeActionPort.AckReceived)value;var n=StrictJson.object().put("request_id",ack.requestId()).put("received",Base64.getEncoder().encodeToString(ack.originalPacket()))
                    .put("sent",Base64.getEncoder().encodeToString(ack.outbound().orElseThrow().originalPacket()));
            n.set("custody",ack.custody().<com.fasterxml.jackson.databind.JsonNode>map(NativeRequestChronologyCodec::encode).orElseGet(n::nullNode));return StrictJson.canonical(n);
        }
        private static byte[] bytes(NativeRequest request) {var n=StrictJson.object().put("step",request.step());n.set("fields",StrictJson.parse(request.additionalFields().bytes()));return StrictJson.canonical(n);}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){var r=ref("dispatch",bytes(value));dispatches.putIfAbsent(r,value);return r;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef r){return Objects.requireNonNull(dispatches.get(r));}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){var r=ref("dispatch",bytes(value));assertEquals(value,dispatches.get(r));return r;}
        @Override public ExactRef preserveRequest(NativeRequest value){var r=ref("request",bytes(value));requests.putIfAbsent(r,value);return r;}
        @Override public NativeRequest loadRequest(ExactRef r){return Objects.requireNonNull(requests.get(r));}
        @Override public ExactRef requestReferenceOf(NativeRequest value){var r=ref("request",bytes(value));assertEquals(value,requests.get(r));return r;}
        @Override public ExactRef preserveMaterial(RawJson value){var r=ref("material",value.bytes());materials.putIfAbsent(r,value);return r;}
        @Override public RawJson loadMaterial(ExactRef r){return Objects.requireNonNull(materials.get(r));}
        @Override public ExactRef materialReferenceOf(RawJson value){var r=ref("material",value.bytes());assertEquals(value,materials.get(r));return r;}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw new AssertionError("no independent material is inferred from a MAA submit");}
        @Override public PlanningReadReceipt loadRead(ExactRef r){throw new AssertionError("no read");}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){throw new AssertionError("no read");}
        @Override public ExactRef preserveRecord(ActionRecord value){throw new AssertionError("pure vector does not grant writer authority");}
        @Override public ActionRecord loadRecord(ExactRef r){throw new AssertionError("no record");}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw new AssertionError("no record");}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw new AssertionError("pure codec vector does not append");}
        @Override public ActionReceipt loadReceipt(ExactRef r){throw new AssertionError("no receipt");}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw new AssertionError("no receipt");}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw new AssertionError("cold refusal needs no new frame");}
        @Override public byte[] loadNativeFrame(ExactRef r){throw new AssertionError("cold refusal needs no new frame");}
    }
}
