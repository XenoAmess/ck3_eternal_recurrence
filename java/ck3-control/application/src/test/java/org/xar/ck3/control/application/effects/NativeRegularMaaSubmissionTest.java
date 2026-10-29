package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

class NativeRegularMaaSubmissionTest {
    private static ObjectNode retained() throws IOException {
        try(var stream=NativeRegularMaaSubmissionTest.class.getResourceAsStream("/maa/retained-python-create-queued.json")) {
            assertNotNull(stream,"mandatory retained original Python public producer result");
            return (ObjectNode)StrictJson.parse(stream.readAllBytes()).path("packet").path("structuredContent");
        }
    }
    private static NativeRegularMaaSubmission.Submission decode(JsonNode row) {
        return NativeRegularMaaSubmission.decode(new RawJson(StrictJson.canonical(row)),29829,50);
    }
    private static ObjectNode submission() throws IOException { return (ObjectNode)retained().get("native_submission"); }
    @Test void actualRetainedPublicProducerToSameTypedEffectConsumerRemainsPending() throws IOException {
        ObjectNode publicResult=retained();var original=submission();var value=decode(original);
        assertEquals(NativeRegularMaaSubmission.Status.QUEUED_PENDING,value.status());
        assertEquals(original,value.toJson());assertEquals(value,decode(StrictJson.parse(StrictJson.canonical(value.toJson()))));
        assertTrue(publicResult.get("submitted").booleanValue());assertTrue(publicResult.get("verification_pending").booleanValue());
        for(String material:List.of("material_result","created_observed","payment_observed","automatic_retry"))
            assertFalse(publicResult.get(material).booleanValue());
        var projected=NativeArmyOrdinaryEffects.maaSubmissionPending(value,List.of());
        assertInstanceOf(ActionPorts.Pending.class,projected.result());assertTrue(projected.compatibleResult().isEmpty());
        assertTrue(value.pendingReason().contains("created-owned-persistent-Regi"));assertTrue(value.pendingReason().contains("ten-resource-charge"));
    }
    @Test void nativeValidatorFalseAndQueueRejectionPreserveSeparateNullableObservations() throws IOException {
        var denied=submission();denied.put("status","rejected").put("reason","native_denied").put("native_can_create",false)
                .putNull("native_submit_accepted").putNull("command_pointer_consumed");
        var first=decode(denied);assertEquals(Optional.of(false),first.nativeCanCreate());assertTrue(first.nativeSubmitAccepted().isEmpty());
        assertEquals(denied,first.toJson());
        var rejected=submission();rejected.put("status","rejected").put("reason","native_queue_rejected").put("native_submit_accepted",false);
        var second=decode(rejected);assertEquals(Optional.of(false),second.nativeSubmitAccepted());assertEquals(Optional.of(true),second.commandPointerConsumed());
        for(var value:List.of(first,second)) {
            var result=NativeArmyOrdinaryEffects.maaSubmissionPending(value,List.of());
            assertInstanceOf(ActionPorts.Pending.class,result.result());assertTrue(result.compatibleResult().isEmpty());
        }
        rejected.put("reason","native_denied");assertThrows(IllegalArgumentException.class,()->decode(rejected));
    }
    @Test void nativeCleanupWarningDoesNotUndoOwnershipAndAmbiguityDoesNotGrantRetry() throws IOException {
        var cleanup=submission();cleanup.put("reason","native_stack_cleanup_unavailable");
        assertEquals(NativeRegularMaaSubmission.Status.QUEUED_PENDING,decode(cleanup).status());
        var unresolved=submission();unresolved.put("status","unavailable").put("reason","native_submit_ownership_not_consumed").put("command_pointer_consumed",false);
        var value=decode(unresolved);assertEquals(Optional.of(true),value.nativeSubmitAccepted());assertEquals(Optional.of(false),value.commandPointerConsumed());
        assertEquals(unresolved,value.toJson());assertTrue(value.pendingReason().contains("without replay"));
        assertInstanceOf(ActionPorts.Pending.class,NativeArmyOrdinaryEffects.maaSubmissionPending(value,List.of()).result());
    }
    @Test void nativeBoundaryRejectsWrongFieldMissingNullBoolAliasesAndCrossedSubject() throws IOException {
        var original=submission();var missing=original.deepCopy();missing.remove("native_can_create");assertThrows(IllegalArgumentException.class,()->decode(missing));
        var numeric=original.deepCopy();numeric.put("native_can_create",1);assertThrows(IllegalArgumentException.class,()->decode(numeric));
        var floating=original.deepCopy();floating.put("type_index",50.0);assertThrows(IllegalArgumentException.class,()->decode(floating));
        var wrong=original.deepCopy();wrong.put("created_observed",true);assertThrows(IllegalArgumentException.class,()->decode(wrong));
        assertThrows(IllegalArgumentException.class,()->NativeRegularMaaSubmission.decode(new RawJson(StrictJson.canonical(original)),29830,50));
        assertThrows(IllegalArgumentException.class,()->NativeRegularMaaSubmission.decode(new RawJson(StrictJson.canonical(original)),29829,49));
        var nullQueued=original.deepCopy();nullQueued.putNull("native_can_create");assertThrows(IllegalArgumentException.class,()->decode(nullQueued));
    }
}
