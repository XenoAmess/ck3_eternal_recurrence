package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Original cycle and capture metadata; distinct from the prior readonly-prefix recovery route. */
public record ClosedAdoptionSources(RecoveryEvidence savedSeed, RecoveryEvidence savedGovernance,
        RecoveryEvidence coldBound, RecoveryEvidence openingSemantic, RecoveryEvidence openingCapabilities,
        RecoveryEvidence classifierPin, ExactRef classifierSource, ExactRef queueSource,
        RecoveryEvidence captureProbe, RecoveryEvidence captureCleanup, List<CycleSources> cycles) {
    public ClosedAdoptionSources {
        Objects.requireNonNull(savedSeed); Objects.requireNonNull(savedGovernance);
        Objects.requireNonNull(coldBound); Objects.requireNonNull(openingSemantic); Objects.requireNonNull(openingCapabilities);
        Objects.requireNonNull(classifierPin); Objects.requireNonNull(classifierSource); Objects.requireNonNull(queueSource);
        Objects.requireNonNull(captureProbe); Objects.requireNonNull(captureCleanup);
        cycles = List.copyOf(cycles); StrictJson.require(!cycles.isEmpty() && cycles.size() <= 30, "bounded complete partial prefix");
    }
    public record CycleSources(RecoveryEvidence event, RecoveryEvidence ordinaryCredit,
            RecoveryEvidence autoAfter, RecoveryEvidence metricsAfter, RecoveryEvidence beforePlan,
            java.util.Optional<RecoveryEvidence> readonlySaveSkip) {
        public CycleSources {
            Objects.requireNonNull(event); Objects.requireNonNull(ordinaryCredit); Objects.requireNonNull(autoAfter);
            Objects.requireNonNull(metricsAfter); Objects.requireNonNull(beforePlan); Objects.requireNonNull(readonlySaveSkip);
        }
    }
    public interface SourceVerifier {
        /** Reread small immutable sources or fresh-stat an explicitly source-bound immutable cache. */
        void verify(ExactRef source);
    }
}
