package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.contracts.StrictJson;

/** Recorded proof is DATA; only the lifecycle domain verifier can grant actual canonical acceptance. */
final class LifecycleActionContractTest {
    private static LifecycleTransitionProof recorded(ActionCommand parent) {
        var row = StrictJson.object(); row.put("schema", "xar.java-lifecycle-transition-proof/v1"); row.put("kind", "DEATH");
        row.put("parent_action_id", parent.actionId()); row.put("body_sha256", ActionCodec.bodySha256(parent));
        row.put("operation", parent.operation().value()); row.put("committed_event_identity", "f".repeat(64));
        var document = row.putArray("committed_documents").addObject(); document.set("reference", ActionCoordinatorTest.REF.toJson());
        var nativeIdentity = document.putObject("native_identity"); nativeIdentity.put("volume_serial", "9007199254740993");
        nativeIdentity.put("file_id", "18446744073709551615"); nativeIdentity.put("creation_filetime", "133700000000000001");
        nativeIdentity.put("modified_instant", ActionCoordinatorTest.NOW.toString()); nativeIdentity.put("bytes", ActionCoordinatorTest.REF.bytes());
        row.putArray("original_evidence").add(ActionCoordinatorTest.REF.toJson()); row.putObject("result").put("status", "recorded-data-only");
        return LifecycleProofCodec.decodeRecorded(StrictJson.canonical(row, 262_144));
    }
    @Test void lifecycleProofCannotSettleAPrimitiveOrAcquireOrdinaryDayCredit() {
        var command = ActionCoordinatorTest.command("death", "death-terminal");
        var proof = recorded(command); var settlement = new ActionState.LifecycleApplied(proof);
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(command, ActionCoordinatorTest.attempt(command, "native"), settlement));
        var execution = new CompositeExecution("lifecycle", ActionCoordinatorTest.NOW, ActionCoordinatorTest.guard(command, ActionCoordinatorTest.NOW), java.util.List.of());
        var receipt = new ActionReceipt(1, 3, command, ActionCodec.bodySha256(command), new ActionState.CompositeSettled(execution, settlement));
        assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance()); assertTrue(receipt.applied().isEmpty());
        assertEquals(proof.originalEvidence(), ActionEffects.supportingEvidence(settlement));
    }
    @Test void recordedProofRoundTripKeepsExactDecimalIdentityAndCanonicalEquality() {
        var command = ActionCoordinatorTest.command("death", "death-terminal"); var original = recorded(command);
        var loaded = LifecycleProofCodec.decodeRecorded(original.encode());
        assertEquals(new ActionState.LifecycleApplied(original), new ActionState.LifecycleApplied(loaded));
        assertEquals(new ActionState.LifecycleApplied(original).hashCode(), new ActionState.LifecycleApplied(loaded).hashCode());
        assertArrayEquals(original.encode(), loaded.encode());
        assertThrows(IllegalArgumentException.class, () -> loaded.validateParent(ActionCoordinatorTest.command("another", "death-terminal")));
    }
}
