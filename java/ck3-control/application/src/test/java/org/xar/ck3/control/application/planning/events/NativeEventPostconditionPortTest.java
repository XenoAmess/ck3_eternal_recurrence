package org.xar.ck3.control.application.planning.events;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Synthetic independent native-read fixture; no Game, transport, ACK or writer is used. */
final class NativeEventPostconditionPortTest {
    private static final ExactRef REF = new ExactRef("fixture-native-read", 1, "a".repeat(64));
    private static final G2Source SOURCE = new G2Source("fixture-machine", "2026-10-23T00:00:00Z", "1.20.0.4", REF);
    private static final OpportunityJson.Obj ARGS = new OpportunityJson.Obj(java.util.Map.of());
    private static ObservationIdentity identity(int revision, int nativeRevision) {
        return new ObservationIdentity("fixture-machine", new GameGeneration(101, new PythonOnlyUInt64(BigInteger.ONE)),
            new ProposalFrame(new Frame(BigInteger.valueOf(29829), BigInteger.valueOf(nativeRevision), BigInteger.valueOf(53144520)),
                "p" + revision, BigInteger.valueOf(revision), "fixture-episode"), 1);
    }
    private static ExpectedPostcondition expected() {
        return new ExpectedPostcondition(1, identity(900, 51), SOURCE, NativeEventPostconditionPort.EVENT_SCHEMA, List.of(
            new ExpectedInteger(new FieldKey("old_instance_id"), BigInteger.valueOf(17)), new ExpectedBoolean(new FieldKey("old_instance_advanced"), true),
            new ExpectedInteger(new FieldKey("actor_id"), BigInteger.valueOf(29829)), new ExpectedText(new FieldKey("connection_generation_decimal"), "7")));
    }
    private static NativeEventPostconditionPort.BoundSnapshot after(String active, int revision, int nativeRevision, int connection) {
        String wire = "{\"snapshot_id\":\"p" + revision + "\",\"revision\":" + revision + ",\"native_revision\":" + nativeRevision
            + ",\"date_raw\":53144520,\"episode_run_id\":\"fixture-episode\",\"paused\":true,\"map_ready\":true,"
            + "\"played_character\":{\"character_id\":29829},\"diagnostics\":{\"bridge_pid\":101,\"connection_generation\":" + connection + "}"
            + (active == null ? "" : ",\"active_event\":" + active) + "}";
        return new NativeEventPostconditionPort.BoundSnapshot(identity(revision, nativeRevision), SOURCE, "fixture-session",
            OpportunityJson.object(OpportunityJson.parse(wire.getBytes(StandardCharsets.UTF_8)), "fixture"), "independent-read", Instant.parse("2026-10-23T00:00:01Z"), REF);
    }
    private static boolean verified(String active, int revision, int nativeRevision, int connection) {
        return NativeEventPostconditionPort.project(identity(900, 51), SOURCE, "fixture-session", expected(), ARGS,
            after(active, revision, nativeRevision, connection)).isPresent();
    }
    @Test void disappearanceAndReplacementAreBothRealOldInstanceChanges() {
        assertTrue(verified("null", 902, 53, 7));
        assertTrue(verified("{\"instance_id\":18}", 902, 53, 7));
    }
    @Test void originalInstanceMissingObservationStaleFrameAndConnectionDriftRemainUnresolved() {
        assertFalse(verified("{\"instance_id\":17}", 902, 53, 7));
        assertFalse(verified(null, 902, 53, 7));
        assertFalse(verified("null", 900, 51, 7));
        assertFalse(verified("null", 902, 51, 7));
        assertFalse(verified("null", 902, 53, 8));
    }
}
