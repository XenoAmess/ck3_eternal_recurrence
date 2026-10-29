package org.xar.ck3.control.wave2.runtime.savedproof;

import java.util.Objects;

/** Same-JVM result of the real post-HELLO SDK worker; it cannot be reconstructed from JSON. */
public final class ColdRestoreMeasurement {
    private final SavedCheckpointMeasurement checkpoint;
    private final ColdRestoreDriverLineage lineage;
    ColdRestoreMeasurement(SavedCheckpointMeasurement checkpoint,ColdRestoreDriverLineage lineage) {
        this.checkpoint=Objects.requireNonNull(checkpoint); this.lineage=Objects.requireNonNull(lineage);
    }
    public SavedCheckpointMeasurement checkpoint() { return checkpoint; }
    public ColdRestoreDriverLineage lineage() { return lineage; }
}
