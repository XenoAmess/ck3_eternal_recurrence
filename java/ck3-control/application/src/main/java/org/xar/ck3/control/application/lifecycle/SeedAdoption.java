package org.xar.ck3.control.application.lifecycle;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** SAVE may be physically confirmed even when no historical first-life seed is available. */
public sealed interface SeedAdoption permits SeedAdoption.Available, SeedAdoption.Unavailable, SeedAdoption.Unknown {
    enum Origin { EXISTING, FIRST_FREEZE }
    enum Reason { PRIOR_EPISODES, ORPHAN_SEED, HISTORY_UNREADABLE, INVALID_IDENTITY }
    record Available(SeedArtifact artifact, Origin origin) implements SeedAdoption {
        public Available { Objects.requireNonNull(artifact); Objects.requireNonNull(origin); }
    }
    record Unavailable(Reason reason, List<ExactRef> evidence) implements SeedAdoption {
        public Unavailable { Objects.requireNonNull(reason); evidence = List.copyOf(evidence); }
    }
    record Unknown(String reason, List<ExactRef> evidence) implements SeedAdoption {
        public Unknown { StrictJson.text(reason); evidence = List.copyOf(evidence); }
    }
}
