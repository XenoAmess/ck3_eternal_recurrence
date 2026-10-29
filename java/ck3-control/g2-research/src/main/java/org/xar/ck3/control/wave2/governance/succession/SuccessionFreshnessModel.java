package org.xar.ck3.control.wave2.governance.succession;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Consumed projections of the original offline freshness observer; no authority or IO. */
public final class SuccessionFreshnessModel {
    private SuccessionFreshnessModel() { }

    /** The original diagnostic permits nonnegative arbitrary precision frame integers. */
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw) {
        public Frame {
            SuccessionModel.nonempty(snapshotId);
            nonnegative(revision); nonnegative(nativeRevision); nonnegative(dateRaw);
        }
    }

    public record EpisodeBinding(Frame frame, String episodeRunId, BigInteger episodeCharacterId) {
        public EpisodeBinding {
            Objects.requireNonNull(frame); SuccessionModel.nonempty(episodeRunId);
            NativeCharacterId.of(episodeCharacterId);
        }
        public static EpisodeBinding fromExpectation(SuccessionModel.Binding binding) {
            Objects.requireNonNull(binding);
            SuccessionModel.Frame frame = binding.frame();
            return new EpisodeBinding(new Frame(frame.snapshotId(), frame.revision(), frame.nativeRevision(),
                    BigInteger.valueOf(frame.dateRaw())), binding.episodeRunId(),
                    BigInteger.valueOf(binding.episodeCharacterId()));
        }
    }

    /** Opaque verdict evidence is transcribed, never evaluated or treated as verification. */
    public record VerdictEvidence(byte[] json) {
        public VerdictEvidence { json = Objects.requireNonNull(json).clone(); }
        @Override public byte[] json() { return json.clone(); }
    }

    public record Input(EpisodeBinding predecessorBinding, Frame boundaryBinding,
            BigInteger predecessorCharacterId, Optional<SuccessionModel.Expectation> expectation,
            Optional<EpisodeBinding> lastLivingFrame, VerdictEvidence verdict) {
        public Input {
            Objects.requireNonNull(predecessorBinding); Objects.requireNonNull(boundaryBinding);
            NativeCharacterId.of(predecessorCharacterId); Objects.requireNonNull(expectation);
            Objects.requireNonNull(lastLivingFrame); Objects.requireNonNull(verdict);
        }
    }

    public enum AllTitleFreshness {
        FULL_EXPECTATION_NOT_OBSERVED("full_expectation_not_observed"),
        LAST_LIVING_FRAME_NOT_OBSERVED("last_living_frame_not_observed"),
        SAME_AS_LAST_OBSERVED_LIVING_FRAME("same_as_last_observed_living_frame"),
        DIFFERENT_FROM_LAST_OBSERVED_LIVING_FRAME("different_from_last_observed_living_frame");
        private final String wire;
        AllTitleFreshness(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Observation(Input input, BigInteger expectationAgeRaw,
            Optional<BigInteger> lastLivingAgeRaw, Optional<Boolean> sameFrame,
            AllTitleFreshness allTitleFreshness) {
        public Observation {
            Objects.requireNonNull(input); nonnegative(expectationAgeRaw);
            Objects.requireNonNull(lastLivingAgeRaw); lastLivingAgeRaw.ifPresent(SuccessionFreshnessModel::nonnegative);
            Objects.requireNonNull(sameFrame); Objects.requireNonNull(allTitleFreshness);
        }
    }

    private static void positive(BigInteger value) {
        SuccessionModel.check(value != null && value.signum() > 0, "positive exact diagnostic integer required");
    }
    private static void nonnegative(BigInteger value) {
        SuccessionModel.check(value != null && value.signum() >= 0, "nonnegative exact diagnostic integer required");
    }
}
