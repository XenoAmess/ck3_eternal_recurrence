package org.xar.ck3.control.warpolicy;

import java.util.Objects;
import org.xar.ck3.control.contracts.observation.ObservationReuse;

/**
 * Typed convenience consumer of the actual production projector's scoped path. It never reads
 * native state, binds a lease, settles an action or owns writer versions.
 */
public final class ScopedWarOutcomeStakesProjector {
    private final WarOutcomeStakesProjector projector;
    private final ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult> reuse;

    public ScopedWarOutcomeStakesProjector(WarOutcomeStakesProjector projector,
            ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult> reuse) {
        this.projector = Objects.requireNonNull(projector); this.reuse = Objects.requireNonNull(reuse);
    }

    public ObservationReuse.Read<WarOutcomeStakesResult> project(
            ObservationReuse.Token<ObservationContext, WarObservationFrame> token, byte[] input) {
        return projector.projectScoped(reuse, token, input);
    }
}
