package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Production failure shape reached by the native selector's invalid Character singleton. No engine eligibility reimplementation. */
final class NativePlayerHeirNegativeResult12004Test {
    private static final int ACTOR = 31254, DATE = 53144328;
    private static final BigInteger NATIVE = BigInteger.valueOf(31);
    private static final Frame FRAME = new Frame("native-31", BigInteger.valueOf(900), NATIVE, DATE, ACTOR, 0);
    @Test void nonnullInvalidSingletonRemainsUnavailableAndKeepsObservedPresence() {
        Core core = new Core(DATE, true, 3, 0, true, true, ACTOR, true);
        // ReadUnchecked sets candidate_present before Identity fails; Fail clears identity/stability but preserves getter/presence.
        Component actualFailureShape = new Component(NATIVE, true, new Observation(false,
                "candidate_identity_unavailable", false, true, core, core, true, true, ACTOR, -1,
                false, false, false, new Lineage(-1, -1), null));
        Parsed decoded = parse(root(actualFailureShape), FRAME);
        assertEquals(State.UNAVAILABLE, decoded.state());
        assertTrue(decoded.component().observation().candidatePresent());
        assertTrue(decoded.component().observation().getterObserved());
        assertEquals(-1, decoded.component().observation().candidateCharacterId());
        assertArrayEquals(encodeComponent(actualFailureShape), encodeComponent(decoded.component()));
    }
    @Test void actualNullAndInvalidObjectCannotCollapseIntoTheSameObservation() {
        Core core = new Core(DATE, true, 3, 0, true, true, ACTOR, true);
        Component observedNull = new Component(NATIVE, true, new Observation(true, null, false, true,
                core, core, true, false, ACTOR, -1, false, true, false, new Lineage(-1, -1), null));
        assertEquals(State.OBSERVED_NULL, parse(root(observedNull), FRAME).state());
        Component invalidClaim = new Component(NATIVE, true, new Observation(true, null, false, true,
                core, core, true, true, ACTOR, -1, false, true, false, new Lineage(-1, -1), null));
        assertThrows(IllegalArgumentException.class, () -> parse(root(invalidClaim), FRAME));
    }
    @Test void failedSelectorCannotHideAChangedNativeActorFrame() {
        Core before = new Core(DATE, true, 3, 0, true, true, ACTOR, true);
        Core after = new Core(DATE, true, 3, 0, true, true, ACTOR + 1, true);
        Component changed = new Component(NATIVE, true, new Observation(false,
                "candidate_identity_unavailable", false, true, before, after, true, true, ACTOR, -1,
                false, false, false, new Lineage(-1, -1), null));
        assertEquals(State.UNBOUND, parse(root(changed), FRAME).state());
    }
    private static byte[] root(Component component) {
        ObjectNode result = StrictJson.object().put("status", "available");
        result.putObject("binding").put("snapshot_id", FRAME.snapshotId()).put("revision", FRAME.publicRevision())
                .put("native_revision", NATIVE).put("date_raw", DATE);
        ObjectNode nativeRoot = result.putObject("campaign_root_context");
        nativeRoot.put("status", "available").put("snapshot_revision", NATIVE).put("date_raw", DATE)
                .put("local_player_id", 0).put("player_character_id", ACTOR).put("player_character_alive", true);
        nativeRoot.putObject("readiness").put("same_frame_ready", true);
        nativeRoot.putObject("provenance").put("executable_sha256", EXE_SHA256);
        nativeRoot.set(COMPONENT, StrictJson.parse(encodeComponent(component), MAX_BYTES));
        return StrictJson.canonical(result, MAX_BYTES);
    }
}
