package org.xar.ck3.control.wave2.military.updaterwrites;

import java.util.List;
import java.util.Objects;

public record UpdaterProjection(Status status, boolean ready, List<String> missingInputs,
                                Integer armyId, Integer nativeCarmyId, SourceNextFrame sourceNextDate,
                                Long observedArmyByte22, boolean observedArmyByte22Ready,
                                Long observedLastSupplyUpdateStorage, Integer observedLastSupplyUpdateLow,
                                Long observedCallerStorage, boolean updateComparisonReady,
                                Boolean updateMatchesCurrentClock, Boolean currentClockMatchesSourceSeed,
                                Integer observedGraceElapsedDays, UpdaterAdmission nextAdmission,
                                List<ConditionalWrite> conditionalWrites, GraceAnchor graceAnchor,
                                boolean sourceNextFullDateReady) {
    public UpdaterProjection {
        Objects.requireNonNull(status); Objects.requireNonNull(nextAdmission); Objects.requireNonNull(graceAnchor);
        missingInputs = List.copyOf(missingInputs); conditionalWrites = List.copyOf(conditionalWrites);
        if (ready != (status == Status.AVAILABLE)) throw new IllegalArgumentException("updater result status and readiness differ");
    }
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public record GraceAnchor(boolean ready, Long observedValue, Integer observedLow32) {}
}
