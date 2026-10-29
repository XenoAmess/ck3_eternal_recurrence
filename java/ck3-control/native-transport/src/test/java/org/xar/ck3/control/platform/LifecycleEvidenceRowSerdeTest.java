package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.GameLifecycle;

/** The real lifecycle row encoder uses the shared strict mapper, without an uninstalled Java-time module. */
final class LifecycleEvidenceRowSerdeTest {
    @Test void actualLifecycleEventRowSerializesAndReopensItsExplicitUtcTimestamp() throws Exception {
        var row = new LifecycleEvidence.Row("xar.java-game-lifecycle-event/v1", "machine-test",
                "2026-10-24T19:00:00.000000001Z", "request-test", "session-test", LifecycleEvidence.Event.UNAVAILABLE,
                null, null, null, GameLifecycle.TerminalKind.UNKNOWN, "original failure retained");
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(row);
        assertEquals(row, ControlBuild.strictMapper().readValue(bytes, LifecycleEvidence.Row.class));
        var json = ControlBuild.strictMapper().readTree(bytes);
        assertEquals("2026-10-24T19:00:00.000000001Z", json.get("observed_at_utc").textValue());
        assertTrue(json.get("game").isNull()); assertTrue(json.get("terminal").isNull());
    }
    @Test void malformedUtcTimestampIsRejectedByTheActualTypedRowConstructor() {
        assertThrows(java.time.format.DateTimeParseException.class, () -> new LifecycleEvidence.Row(
                "xar.java-game-lifecycle-event/v1", "machine-test", "not-an-observation-time", "request-test",
                "session-test", LifecycleEvidence.Event.UNAVAILABLE, null, null, null,
                GameLifecycle.TerminalKind.UNKNOWN, "original failure retained"));
    }
}
