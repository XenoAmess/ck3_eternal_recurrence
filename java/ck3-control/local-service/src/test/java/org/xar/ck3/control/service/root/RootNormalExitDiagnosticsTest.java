package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.NormalExitPublicCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Actual software ACK-loss/central/archive/cold chain plus original-wire and public-registry DATA.
 * No fake Core, Managed, private inventory, qualified registration, negative canonical ACK or OS-exit success. */
final class RootNormalExitDiagnosticsTest {
    @TempDir Path temporary;
    private static final BigInteger BIRTH=new BigInteger("133700000000000001");
    @Test void noRetainedObserverUsesTheOriginalUnsupportedTypeAndMessageThroughTheActualPublicBinding()throws Exception{
        var registry=new PublicBindings();var unrelated=new AtomicInteger();
        RootNormalExitPublicProducts.register(registry,input->{
            RootNormalExitRuntime.requireRetainedObserver(null,null);
            throw new AssertionError("missing observer must not acquire a result or handle");
        },input->{unrelated.incrementAndGet();throw new AssertionError("no query");},
          input->{unrelated.incrementAndGet();throw new AssertionError("no replacement confirmation");},source());
        freeze(registry);
        var binding=registry.lookup(PublicMethod.OBSERVE_NORMAL_EXIT_V1).orElseThrow();
        for(var args:List.<PublicBindings.Arguments>of(new PublicBindings.Missing(),PublicBindings.present(raw(StrictJson.object())))){
            var failure=assertThrows(PublicServiceFailure.class,()->binding.invoke(args));
            assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,failure.kind());
            assertEquals("no backend-owned pending original-process observer is available",failure.getMessage());
        }
        assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw(StrictJson.object().put("retry",true)))));
        assertEquals(0,unrelated.get());
    }
    @Test void actualNegativeAckPacketUsesOnlyOriginalErrorAndPreservesItThroughPublicRequestAndV2Roundtrip()throws Exception{
        var frame=ackFrame(false).put("error","source guard rejected the exact original process");
        frame.put("message","must not replace error");frame.set("result",StrictJson.object().put("reason","must not replace error"));
        var ack=ack(frame);var reason=RootNormalExitRuntime.rejectedAckReason(ack);
        String exact="BridgeUnavailableError: normal-exit native response rejected: source guard rejected the exact original process";
        assertEquals(Optional.of(exact),reason);
        var registry=new PublicBindings();var calls=new AtomicInteger();
        RootNormalExitPublicProducts.register(registry,input->{throw new AssertionError("no observer");},input->{throw new AssertionError("no query");},
            input->{calls.incrementAndGet();var memory=requestMemory(input.action());RootNormalExitRuntime.putRequestReason(memory,reason);
                return NormalExitPublicCodec.fromMemory(raw(memory));},source());freeze(registry);
        var input=new NormalExitPublicCodec.Request(Action.PREPARE_CONFIRMATION,StrictJson.UINT64_MAX,"a".repeat(64));
        var wire=registry.lookup(PublicMethod.REQUEST_NORMAL_EXIT_V1).orElseThrow().invoke(PublicBindings.present(NormalExitPublicCodec.encodeRequest(input)));
        var decoded=NormalExitPublicCodec.decode(wire,Optional.of(BIRTH));
        assertEquals(exact,StrictJson.parse(decoded.memory().bytes()).get("reason").textValue());
        assertEquals("18446744073709551615",StrictJson.parse(wire.bytes()).get("public_revision").textValue());
        assertEquals(1,calls.get());assertNoCredit(StrictJson.parse(wire.bytes()));
        // These are original wire DATA, not an invented canonical negative ACK or Managed qualification.
        frame.remove("error");assertEquals(Optional.of("BridgeUnavailableError: normal-exit native response rejected: None"),RootNormalExitRuntime.rejectedAckReason(ack(frame)));
        frame.putNull("error");assertEquals(Optional.of("BridgeUnavailableError: normal-exit native response rejected: None"),RootNormalExitRuntime.rejectedAckReason(ack(frame)));
        frame.put("ok",true).put("error","ignored on success");assertTrue(RootNormalExitRuntime.rejectedAckReason(ack(frame)).isEmpty());
    }
    @Test void diagnosticReopensPacketAndRejectsMismatchedFrameTokenOrRequestRatherThanTrustingCallerFields()throws Exception{
        var original=ack(ackFrame(false).put("error","actual error"));
        var changedFrame=new NativeActionPort.AckReceived(original.requestId(),false,original.originalResultToken(),
                raw(ackFrame(false).put("error","replacement")),original.originalPacket());
        assertThrows(IllegalArgumentException.class,()->RootNormalExitRuntime.rejectedAckReason(changedFrame));
        var changedId=new NativeActionPort.AckReceived("another",false,original.originalResultToken(),original.originalFrame(),original.originalPacket());
        assertThrows(IllegalArgumentException.class,()->RootNormalExitRuntime.rejectedAckReason(changedId));
        var changedToken=new NativeActionPort.AckReceived(original.requestId(),false,Optional.of(raw(StrictJson.object())),original.originalFrame(),original.originalPacket());
        assertThrows(IllegalArgumentException.class,()->RootNormalExitRuntime.rejectedAckReason(changedToken));
        var nonText=ackFrame(false);nonText.set("error",StrictJson.object().put("original",7));
        assertEquals(Optional.of("Native command_result rejected; original error JSON: {\"original\":7}"),RootNormalExitRuntime.rejectedAckReason(ack(nonText)));
    }
    @Test void actualWriteCompletedReceiveFailureSurvivesCanonicalArchiveColdReopenAndPublicSerdeWithoutAnotherSubmission()throws Exception{
        var selector=NativeStepDiscriminator.NormalExit.PREPARE_CONFIRMATION;var writes=new AtomicInteger();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(selector.operationKey(),selector.capability(),
                (command,attempt,dispatch)->new ActionPorts.Pending("original normal-exit response remains unknown",List.of(attempt.guard().nativeEvidence())),
                writes::incrementAndGet,Optional.of(()->raw(StrictJson.object().put("software_ack_only",true))),Optional.empty(),false,
                Optional.of(command->request(command,selector)));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual-original-response-loss"),false,scenario)){
            fixture.loseActionAckOnce();var seed=fixture.command("normal-exit-original-response-loss");
            var command=new ActionCommand(seed.actionId(),seed.before(),seed.source(),seed.sessionId(),selector.operationKey(),seed.arguments(),seed.expected(),seed.claims(),seed.deadline());
            var actual=fixture.coordinator.execute(command);assertInstanceOf(ActionState.Unknown.class,actual.state());
            assertFalse(actual.settled());assertFalse(actual.visibleGameplay());assertFalse(actual.eligibleAdvance());assertTrue(actual.applied().isEmpty());
            var original=assertInstanceOf(NativeActionPort.Unknown.class,ActionTransitions.dispatch(actual.state()).orElseThrow());
            assertEquals(1,fixture.nativeActionWrites());assertEquals(1,writes.get());
            fixture.writer.locked(same->{var archive=fixture.archive.withSession(same);
                var reopened=archive.loadReceipt(archive.receiptReferenceOf(actual));assertEquals(actual,reopened);
                var reason=RootNormalExitRuntime.requestFailure(reopened,archive);assertEquals(Optional.of(original.reason()),reason);
                // NGT coalesces receive IO/frame-budget/interruption. Do not fabricate Python's missing-response exception.
                assertFalse(reason.orElseThrow().startsWith("BridgeUnavailableError: normal-exit native response missing"));
                var memory=requestMemory(Action.PREPARE_CONFIRMATION);RootNormalExitRuntime.putRequestReason(memory,reason);
                var registry=new PublicBindings();
                RootNormalExitPublicProducts.register(registry,input->{throw new AssertionError("no observer");},input->{throw new AssertionError("no extra query");},
                        input->NormalExitPublicCodec.fromMemory(raw(memory)),source());freeze(registry);
                final RawJson wire;
                try{wire=registry.lookup(PublicMethod.REQUEST_NORMAL_EXIT_V1).orElseThrow().invoke(PublicBindings.present(
                        NormalExitPublicCodec.encodeRequest(new NormalExitPublicCodec.Request(Action.PREPARE_CONFIRMATION,StrictJson.UINT64_MAX,"a".repeat(64)))));}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new java.io.IOException(interrupted);}
                assertEquals(original.reason(),StrictJson.parse(NormalExitPublicCodec.decode(wire,Optional.of(BIRTH)).memory().bytes()).get("reason").textValue());
                assertNoCredit(StrictJson.parse(wire.bytes()));return null;
            });
            assertEquals(actual,fixture.coordinator.execute(command));
            var cold=fixture.reopenAndReturnExisting(command);assertEquals(actual,cold);
            fixture.writer.locked(same->{var bound=fixture.archive.withSession(same);assertEquals(Optional.of(original.reason()),RootNormalExitRuntime.requestFailure(cold,bound));return null;});
            assertEquals(1,fixture.nativeActionWrites());assertEquals(1,writes.get());
        }
    }
    @Test void confirmRequestReasonDoesNotChangeIndependentSameHandleFactsOrAuthorizeRetryAndObservationMayKeepNull()throws Exception{
        var identity=new NormalExitRetainedObserver.Identity(42,BIRTH);
        var opens=new AtomicInteger();var closes=new AtomicInteger();
        var observer=NormalExitRetainedObserver.capture(pid->{opens.incrementAndGet();return new NormalExitRetainedObserver.Handle(){
            public NormalExitRetainedObserver.Identity identity(){return identity;}public long waitZero(){return 258;}
            public long exitCode(){return 259;}public void close(){closes.incrementAndGet();}
        };},identity,()->100);
        try{
            var pin=observer.verifyBeforeConfirm();var process=observer.observe(0);
            var memory=requestMemory(Action.CONFIRM_DESKTOP);
            var facts=NormalExitProtocol.classify(Optional.empty(),process,Optional.empty(),observer.identity()).json();
            facts.properties().forEach(entry->memory.set(entry.getKey(),entry.getValue()));
            memory.set("process_preconfirm_pin",pin);memory.set("process_observation",NormalExitRetainedObserver.json(process));
            memory.put("snapshot_after_required",false).putNull("driver_dispatch_receipt_observed_monotonic_ns");
            String exact="BridgeUnavailableError: normal-exit native response rejected: original confirm error";
            RootNormalExitRuntime.putRequestReason(memory,Optional.of(exact));
            var wire=NormalExitPublicCodec.encode(NormalExitPublicCodec.fromMemory(raw(memory)));
            assertEquals(exact,StrictJson.parse(NormalExitPublicCodec.decode(wire,Optional.of(BIRTH)).memory().bytes()).get("reason").textValue());
            assertNoCredit(StrictJson.parse(wire.bytes()));assertEquals(1,opens.get());assertEquals(0,closes.get());
            memory.put("schema","ck3-normal-exit-process-observation-result-v1").put("native_submission_count",0).put("observer_retained",true);
            RootNormalExitRuntime.putRequestReason(memory,Optional.empty());
            var observation=NormalExitPublicCodec.fromMemory(raw(memory));assertEquals(NormalExitPublicCodec.Kind.OBSERVATION,observation.kind());
            assertTrue(StrictJson.parse(observation.memory().bytes()).get("reason").isNull());
        }finally{observer.close();}
        assertEquals(1,opens.get());assertEquals(1,closes.get());
    }
    private static ObjectNode requestMemory(Action action){
        var row=StrictJson.object().put("schema","ck3-normal-exit-request-result-v1").put("action",action.wire()).put("status","dispatch_unknown_claimed")
                .put("public_revision",StrictJson.UINT64_MAX).put("process_creation_filetime_100ns",BIRTH).put("source_inventory_sha256","b".repeat(64))
                .put("claim_consumed",true).put("retry_authorized",false).put("autosave_verified",false).put("orderly_exit_verified",false)
                .put("process_exit_observed",false).put("typed_normal_exit_observed",false).put("request_id","original-request").put("claim_path","original-claim")
                .put("uses_desktop_input",false).put("uses_ocr",false).put("native_submission_count",1);
        row.putNull("native_observation");return row;
    }
    private static NativeActionPort.AckReceived ack(ObjectNode original)throws Exception{
        byte[] payload=StrictJson.canonical(original);byte[] packet=ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        var parsed=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        return new NativeActionPort.AckReceived(parsed.requestId(),parsed.nativeOk(),parsed.result().token().map(value->new RawJson(value.value())),new RawJson(parsed.payload().value()),packet);
    }
    private static ObjectNode ackFrame(boolean ok){return StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","original-request").put("ok",ok);}
    private static NativeRequest request(ActionCommand command,NativeStepDiscriminator.NormalExit selector){
        var binding=new Binding(command.before().frame().identity().nativeRevision(),command.before().frame().identity().player(),BigInteger.valueOf(42),BigInteger.valueOf(5),BIRTH,command.source().sourceRef().sha256());
        var value=new Request(RequestIds.forCommand(command),Action.parse(selector.wire()),binding,RequestIds.forCommand(command),Optional.of("a".repeat(64)));
        var fields=(ObjectNode)StrictJson.parse(NormalExitProtocol.payload(value));for(String key:List.of("type","protocol_version","request_id","step","expected_revision"))fields.remove(key);
        return new NativeRequest(selector.nativeStep(),Optional.of(selector.capability()),raw(fields));
    }
    private static void freeze(PublicBindings registry){registry.freeze(Set.of(PublicMethod.OBSERVE_NORMAL_EXIT_V1,PublicMethod.QUERY_NORMAL_EXIT_CONTEXT_V1,PublicMethod.REQUEST_NORMAL_EXIT_V1));}
    private static ExactRef source(){return new ExactRef("protocol-DATA-only",1,"a".repeat(64));}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
    private static void assertNoCredit(JsonNode row){assertFalse(row.get("retry_authorized").booleanValue());assertFalse(row.get("autosave_verified").booleanValue());assertFalse(row.get("orderly_exit_verified").booleanValue());assertFalse(row.get("typed_normal_exit_observed").booleanValue());assertFalse(row.get("process_exit_observed").booleanValue());}
}
