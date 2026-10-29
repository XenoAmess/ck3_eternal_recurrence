package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.CheckpointPublicCodec;
import org.xar.ck3.control.service.mcp.LifecyclePublicCodec;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Protocol DATA and real software canonical failure only. No Core, ManagedGame or private lifecycle proof is fabricated. */
final class RootLifecyclePublicStepProductsTest {
    @TempDir Path temporary;
    private static final ExactRef SOURCE=new ExactRef("lifecycle-step-protocol-data-only",1,"a".repeat(64));
    private static final ExactRef RECEIPT=new ExactRef("unconfirmed-protocol-receipt-data-only",1,"b".repeat(64));
    private static RawJson raw(String json){return new RawJson(json.getBytes(StandardCharsets.UTF_8));}
    private static PublicPlanningCodec.ExecuteRequest request(String json){
        return PublicPlanningCodec.decodeExecute(PublicBindings.present(raw(json)));
    }
    private static RootPublicStepExecution.Lifecycle select(List<RootPublicStepExecution.Product> products,
            PublicPlanningCodec.ExecuteRequest caller){
        var matches=products.stream().filter(product->product.matches(caller.step())).toList();
        assertEquals(1,matches.size());return assertInstanceOf(RootPublicStepExecution.Lifecycle.class,matches.getFirst());
    }
    @Test void actualExecuteDecoderSelectsExactlyFiveOriginalLifecycleDescriptorsAndPreservesRevisionPresence()throws Exception {
        var received=new ArrayList<PublicPlanningCodec.ExecuteRequest>();
        RawJson dataOnly=CheckpointPublicCodec.save(new RootCheckpointPublicCalls.SaveCall(
                new CheckpointResult.Unknown("protocol-only","actual material and Root are not supplied by this DATA test",Optional.empty()),
                Optional.empty(),Optional.empty()));
        var products=RootLifecyclePublicStepProducts.bind(ignored->{},List.of(SOURCE),
                (step,root,installed,caller,deadline)->{received.add(caller);return dataOnly;});
        assertEquals(5,products.size());
        for(String step:List.of("save-checkpoint","restore-checkpoint","death-terminal","start-next-episode","continue-as-reconciled-successor")){
            for(String suffix:List.of("",",\"expected_revision\":null",",\"expected_revision\":9007199254740991",",\"expected_revision\":\"18446744073709551615\"")){
                var caller=request("{\"step\":\""+step+"\""+suffix+"}");
                assertEquals(caller,request(new String(PublicPlanningCodec.encodeExecute(caller).bytes(),StandardCharsets.UTF_8)));
                var product=select(products,caller);
                // This is the protocol-only call seam, not RootPublicStepExecution.execute or a source/Root admission.
                assertEquals(dataOnly,product.work().execute(null,null,caller,Instant.parse("2026-10-24T10:00:00Z")));
                assertSame(caller,received.getLast());
                var checkpoint=RootLifecyclePublicStepProducts.checkpointRequest(caller);
                if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionMissing)assertInstanceOf(RootCheckpointPublicCalls.MissingRevision.class,checkpoint.expectedRevision());
                else if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionNull)assertInstanceOf(RootCheckpointPublicCalls.NullRevision.class,checkpoint.expectedRevision());
                else assertEquals(((PublicPlanningCodec.RevisionValue)caller.expectedRevision()).value(),checkpoint.effectiveExpectedRevision().orElseThrow());
                assertEquals(checkpoint.effectiveExpectedRevision(),RootLifecyclePublicStepProducts.expected(caller));
            }
        }
        for(String other:List.of("save-checkpoint:x","restore-checkpoint-2","death-terminal:x","start-next-episode:x",
                "continue-as-reconciled-successor:x","normal-exit-map-v1","prepare_confirmation","advance-days:1","assign-army-commander-v1:1:2"))
            assertTrue(products.stream().noneMatch(product->product.matches(new OperationKey(other))));
    }
    @Test void malformedOriginalFieldsFailBeforeTheLifecycleDelegateAndTypedSourceErrorsAreNotRewritten()throws Exception {
        var calls=new AtomicInteger();
        var original=new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,"original revision mismatch",Optional.of(RECEIPT));
        var products=RootLifecyclePublicStepProducts.bind(ignored->{},List.of(SOURCE),
                (step,root,installed,caller,deadline)->{calls.incrementAndGet();throw original;});
        for(String body:List.of("{\"step\":\"save-checkpoint\",\"expected_revision\":true}",
                "{\"step\":\"save-checkpoint\",\"expected_revision\":1.0}",
                "{\"step\":\"save-checkpoint\",\"expected_revision\":-1}",
                "{\"step\":\"save-checkpoint\",\"expected_revision\":9007199254740992}",
                "{\"step\":\"save-checkpoint\",\"expected_revision\":\"01\"}",
                "{\"step\":\"save-checkpoint\",\"expected_revision\":18446744073709551616}",
                "{\"step\":\"save-checkpoint\",\"revision\":1}",
                "{\"step\":\"save-checkpoint\",\"expected_revision\":1,\"expected_revision\":2}"))
            assertThrows(IllegalArgumentException.class,()->request(body));
        assertEquals(0,calls.get());
        var caller=request("{\"step\":\"restore-checkpoint\"}");var route=select(products,caller);
        assertSame(original,assertThrows(PublicServiceFailure.class,()->route.work().execute(null,null,caller,Instant.parse("2026-10-24T10:00:00Z"))));
        assertEquals(1,calls.get());
        assertThrows(java.io.IOException.class,()->route.work().execute(null,null,request("{\"step\":\"save-checkpoint\"}"),Instant.parse("2026-10-24T10:00:00Z")));
        assertEquals(1,calls.get());
    }
    @Test void soleCheckpointUnknownEncoderAndOldDeathNextPayloadsRemainUnconfirmedAndRoundTripTheirOriginalRequestStates(){
        var checkpoint=CheckpointPublicCodec.save(new RootCheckpointPublicCalls.SaveCall(
                new CheckpointResult.Unknown("original-data-only","no actual material",Optional.empty()),Optional.empty(),Optional.empty()));
        var saved=StrictJson.parse(checkpoint.bytes());assertEquals("save-checkpoint",saved.get("step").textValue());
        assertFalse(saved.get("accepted").booleanValue());assertFalse(saved.path("materialization").get("available").booleanValue());
        for(var operation:List.of(LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE)){
            var value=new LifecyclePublicCodec.Unconfirmed(operation,ActionReceipt.Outcome.UNRESOLVED,false,
                    "original-data-only","c".repeat(64),RECEIPT,"protocol-only-machine",Instant.parse("2026-10-24T09:00:00Z"));
            var output=StrictJson.parse(LifecyclePublicCodec.encode(value).bytes());assertEquals(operation.key().value(),output.get("step").textValue());
            assertEquals(RECEIPT.toJson(),output.get("original_receipt"));assertTrue(output.get("never_replay").booleanValue());
            assertFalse(output.get("material_result_available").booleanValue());
        }
        for(var arguments:List.<PublicBindings.Arguments>of(new PublicBindings.Missing(),new PublicBindings.Null(),
                PublicBindings.present(raw("{}")),PublicBindings.present(raw("{\"expected_revision\":null}")))){
            var old=LifecyclePublicCodec.decodeRequest(arguments);assertEquals(arguments,LifecyclePublicCodec.encodeRequest(old));
        }
    }
    @Test void realCanonicalUnknownCannotBePresentedAsATerminalParentOrResubmittedFromAProjectionFailure()throws Exception {
        var operation=LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR;
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(operation.key(),"software.lifecycle-origin-negative",
                (command,attempt,dispatch)->new ActionPorts.Pending("actual software ACK has no lifecycle business proof",List.of(attempt.guard().nativeEvidence())),()->{});
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("canonical-wrong-origin"),true,scenario)){
            // The fixture issues a real Gameplay command; it cannot impersonate a private terminal parent.
            var command=fixture.command("actual-canonical-unknown");var receipt=fixture.coordinator.execute(command);
            assertFalse(receipt.settled());assertTrue(receipt.applied().isEmpty());assertEquals(1,fixture.nativeActionWrites());
            fixture.writer.locked(same->{
                var archive=fixture.archive.withSession(same);var reference=archive.receiptReferenceOf(receipt);
                assertEquals(receipt,archive.loadReceipt(reference));
                assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.presentStep(operation,receipt,archive));
                assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.presentStep(LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,receipt,archive));
                return null;
            });
            assertEquals(receipt,fixture.coordinator.execute(command));assertEquals(1,fixture.nativeActionWrites());
            assertEquals(0,fixture.continuationWrites());
        }
    }
    /** Mandatory whole-Root hook: caller must already hold the actual admitted Root/catalog/request/deadline.
     * Existing Root CI supplies them; absence is NOT_RUN and cannot be replaced by the DATA seams above. */
    static RawJson executeActualQualified(RootApplicationSession root,RootInstalledCatalog installed,
            PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws Exception {
        assertSame(root,installed.context().actions());
        assertInstanceOf(RootPublicStepExecution.Lifecycle.class,installed.publicSteps().require(caller));
        return RootPublicStepExecution.execute(root,installed,caller,deadline);
    }
}
