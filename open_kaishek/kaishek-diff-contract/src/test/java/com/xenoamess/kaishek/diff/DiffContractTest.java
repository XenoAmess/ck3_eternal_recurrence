package com.xenoamess.kaishek.diff;

import com.xenoamess.kaishek.ir.IrProgram;
import com.xenoamess.kaishek.profile.BuildFingerprint;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/** Snapshot/delta contracts reject identity and resource inconsistencies. */
class DiffContractTest {
    private static final String HASH = "c".repeat(64);
    private static final BuildFingerprint FINGERPRINT =
            new BuildFingerprint("ck3", "1.19.0.6", HASH, List.of(), null, null);

    @Test
    void scenarioBindsProgramToSnapshotFingerprint() {
        var snapshot = new WorldSnapshot(FINGERPRINT, Instant.EPOCH, 0,
                Map.of(), Map.of(), Map.of(), List.of());
        var program = new IrProgram("ck3-1.19.0.6", "1.19.0.6", FINGERPRINT,
                List.of(), List.of());
        var scenario = new DifferentialScenario("case-1", snapshot, program,
                List.of(1L, 2L), Map.of("kind", "fixture"));
        assertEquals("case-1", scenario.id());
        assertThrows(IllegalArgumentException.class,
                () -> new ResourceState("owner", "gold", 1, 2));
        assertThrows(IllegalArgumentException.class,
                () -> new ResourceState("owner", "gold", -1, 0));
    }

    @Test
    void stateDeltaNormalizesHashesAndRevisions() {
        var delta = new StateDelta("case-1", HASH.toUpperCase(), HASH,
                1, 2, List.of(new DeltaChange("gold", "1", "2")),
                List.of(), List.of());
        assertEquals(HASH, delta.beforeHash());
        assertEquals(HASH, delta.afterHash());
        assertThrows(IllegalArgumentException.class,
                () -> new StateDelta("case-1", HASH, HASH, 2, 1, List.of(), List.of(), List.of()));
    }
}
