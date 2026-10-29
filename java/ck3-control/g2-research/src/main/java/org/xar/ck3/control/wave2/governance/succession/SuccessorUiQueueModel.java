package org.xar.ck3.control.wave2.governance.succession;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Read-only post-Continue values. Original App/Queue keep action and durable writer ownership. */
public final class SuccessorUiQueueModel {
    private SuccessorUiQueueModel() { }

    public enum Status {
        CLEAR("clear"), DEFERRED_PLAYER_DECISION("deferred_player_decision"),
        UI_UNRESOLVED("ui_unresolved"), CLOSE_REQUIRED("close_required");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Status fromWire(String value) {
            for (Status status : values()) if (status.wire.equals(value)) return status;
            throw new IllegalArgumentException("unknown original App UI status");
        }
    }

    public record SourceFrame(String snapshotId, BigInteger revision, BigInteger nativeRevision,
            BigInteger dateRaw, BigInteger bridgePid, BigInteger connectionGeneration) {
        public SourceFrame {
            nonempty(snapshotId); positive(revision); positive(nativeRevision); nonnegative(dateRaw);
            positive(bridgePid); positive(connectionGeneration);
        }
    }

    public record LivingFrame(SourceFrame source, String episodeRunId, BigInteger successorCharacterId) {
        public LivingFrame { Objects.requireNonNull(source); nonempty(episodeRunId); NativeCharacterId.of(successorCharacterId); }
    }

    public record Input(Status status, boolean pending, LivingFrame claimed, LivingFrame independent,
            String expectedEpisodeRunId, BigInteger expectedSuccessorId, SourceFrame originalSource,
            boolean playerDecisionPending, boolean coldOwnerRevalidationRequired) {
        public Input {
            Objects.requireNonNull(status); Objects.requireNonNull(claimed); Objects.requireNonNull(independent);
            nonempty(expectedEpisodeRunId); NativeCharacterId.of(expectedSuccessorId); Objects.requireNonNull(originalSource);
        }
    }

    public sealed interface Result permits Observed, Unavailable { LivingFrame frame(); }
    public record Observed(Status status, boolean pending, LivingFrame frame,
            boolean playerDecisionPending) implements Result {
        public Observed { Objects.requireNonNull(status); Objects.requireNonNull(frame); }
    }
    public enum UnavailableReason { ORIGINAL_APP_COLD_RECONNECT_VALIDATION_REQUIRED }
    public record Unavailable(UnavailableReason reason, LivingFrame frame) implements Result {
        public Unavailable { Objects.requireNonNull(reason); Objects.requireNonNull(frame); }
    }

    public static Result evaluate(Input input) {
        Objects.requireNonNull(input);
        require(input.claimed().equals(input.independent()), "independent Queue post differs from original App response");
        require(input.expectedEpisodeRunId().equals(input.independent().episodeRunId())
                && input.expectedSuccessorId().equals(input.independent().successorCharacterId()),
                "Queue post crossed its retained successor episode");
        if (input.coldOwnerRevalidationRequired()) {
            return new Unavailable(UnavailableReason.ORIGINAL_APP_COLD_RECONNECT_VALIDATION_REQUIRED, input.independent());
        }
        require(input.originalSource().bridgePid().equals(input.independent().source().bridgePid())
                && input.originalSource().connectionGeneration().equals(input.independent().source().connectionGeneration()),
                "Queue post changed the original process/connection");
        require(input.status() == Status.CLEAR ? !input.pending() : input.pending(), "App UI status contradicts pending obligation");
        require(input.status() != Status.CLEAR || !input.playerDecisionPending(), "App clear still has a player decision");
        return new Observed(input.status(), input.pending(), input.independent(), input.playerDecisionPending());
    }

    static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
    private static void nonempty(String value) { require(value != null && !value.isEmpty(), "nonempty identity required"); }
    private static void positive(BigInteger value) { require(value != null && value.signum() > 0, "positive original integer required"); }
    private static void nonnegative(BigInteger value) { require(value != null && value.signum() >= 0, "nonnegative original integer required"); }
}
