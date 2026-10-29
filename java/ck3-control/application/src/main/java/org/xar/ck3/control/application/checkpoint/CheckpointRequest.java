package org.xar.ck3.control.application.checkpoint;

import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.contracts.ExactRef;

public record CheckpointRequest(ActionCommand saveCommand, Path expectedSavePath, String lineageId, Optional<CheckpointPair> baseline) {
    public CheckpointRequest {
        Objects.requireNonNull(saveCommand); Objects.requireNonNull(expectedSavePath); StrictJson.text(lineageId); baseline = Objects.requireNonNull(baseline);
        StrictJson.require(saveCommand.operation().value().equals("save-checkpoint") && expectedSavePath.isAbsolute()
                && expectedSavePath.getFileName().toString().equals("xar_checkpoint.ck3"), "shared SAVE operation and canonical configured save path");
        baseline.ifPresent(pair -> StrictJson.require(pair.frame().machineId().equals(saveCommand.before().machineId()) && pair.lineageId().equals(lineageId)
                && pair.frame().frame().episodeRunId().equals(saveCommand.before().frame().episodeRunId()), "baseline remains in original campaign/episode"));
    }
    public record Readiness(ObservationIdentity observed, G2Source source, String sessionId, String lineageId, boolean mapReady,
            boolean paused, boolean saveEligible, String reason, ExactRef nativeEvidence, Instant observedAt) {
        public Readiness {
            Objects.requireNonNull(observed); Objects.requireNonNull(source); StrictJson.text(sessionId); StrictJson.text(lineageId);
            StrictJson.text(reason); Objects.requireNonNull(nativeEvidence); Objects.requireNonNull(observedAt);
            StrictJson.require(nativeEvidence.bytes() > 0 && source.machineId().equals(observed.machineId()), "fresh actual readiness evidence");
        }
    }
    @FunctionalInterface public interface ObservationPort {
        Readiness observe(Instant deadline) throws InterruptedException;
        /** Preparation may borrow the actual received planning frame; post-SAVE collection still observes independently. */
        default Readiness observeForPreparation(ObservationIdentity expected, Instant deadline) throws InterruptedException {
            Objects.requireNonNull(expected); return observe(deadline);
        }
    }
}
