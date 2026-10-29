package org.xar.ck3.control.governance.lifestyleperks;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Typed projection of the existing six-class native perk observation. No submission authority. */
public final class LifestylePerksModel {
    private LifestylePerksModel() { }

    public enum Lifestyle {
        DIPLOMACY("diplomacy_lifestyle"), INTRIGUE("intrigue_lifestyle"),
        LEARNING("learning_lifestyle"), MARTIAL("martial_lifestyle"),
        STEWARDSHIP("stewardship_lifestyle"), WANDERER("wanderer_lifestyle");
        private final String wire;
        Lifestyle(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Lifestyle fromWire(String value) {
            for (Lifestyle key : values()) { if (key.wire.equals(value)) { return key; } }
            throw new IllegalArgumentException("unknown authored lifestyle: " + value);
        }
    }

    public enum Completeness {
        COMPLETE("complete"), PARTIAL("partial");
        private final String wire;
        Completeness(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum Status {
        OBSERVATION_UNAVAILABLE("observation_unavailable"),
        LEGAL_CANDIDATES_UNAVAILABLE("legal_candidates_unavailable"),
        NO_LEGAL_MINIMUM("no_legal_minimum"), RECOMMEND_ACTION("recommend_action");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum Reason {
        PROGRESS_BINDING_INVALID("all_lifestyle_progress_binding_invalid"),
        TARGET_CARDINALITY_INVALID("policy_target_cardinality_invalid"),
        PARTIAL_NO_TARGET("progress_partial_no_target"),
        FINAL_LEGAL_NONE_WITH_POINTS("native_final_legal_none_with_unspent_points"),
        NO_UNSPENT_POINTS("no_unspent_points_across_all_lifestyles"),
        TARGET_OUTSIDE_AUTHORED("target_outside_authored_lifestyle"),
        TARGET_NOT_POSITIVE("target_progress_not_positive"),
        TARGET_ALREADY_OWNED("native_legal_target_already_owned"),
        FINAL_LEGAL_OBSERVED_POINT("all_lifestyle_native_final_legal_with_observed_point");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** Legacy Python integer domains are retained as exact arbitrary-precision JSON integers. */
    public record FrameIdentity(String snapshotId, BigInteger nativeRevision, BigInteger dateRaw,
            BigInteger playerCharacterId, String episodeRunId) {
        public FrameIdentity {
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            positive(nativeRevision); nonnegative(playerCharacterId); Objects.requireNonNull(dateRaw);
        }
    }

    public record ExpectedBinding(String expectedSnapshotId, String expectedEpisodeRunId,
            BigInteger expectedPublicRevision, BigInteger expectedNativeRevision,
            BigInteger expectedProofEpoch, BigInteger expectedDateRaw,
            BigInteger expectedPlayerCharacterId) {
        public ExpectedBinding {
            StrictJson.text(expectedSnapshotId); StrictJson.text(expectedEpisodeRunId);
            positive(expectedPublicRevision); positive(expectedNativeRevision); positive(expectedProofEpoch);
            Objects.requireNonNull(expectedDateRaw); nonnegative(expectedPlayerCharacterId);
        }
        public FrameIdentity frame() {
            return new FrameIdentity(expectedSnapshotId, expectedNativeRevision, expectedDateRaw,
                    expectedPlayerCharacterId, expectedEpisodeRunId);
        }
    }

    public sealed interface ProgressRow permits AvailableProgress, UnavailableProgress {
        Lifestyle lifestyle();
    }

    public record AvailableProgress(Lifestyle lifestyle, BigInteger xpTotalRaw,
            BigInteger xpWithinLevelRaw, BigInteger xpPerLevel, BigInteger unspentPerkPoints,
            BigInteger usedPerkPoints) implements ProgressRow {
        public AvailableProgress {
            Objects.requireNonNull(lifestyle); nonnegative(xpTotalRaw); nonnegative(xpWithinLevelRaw);
            positive(xpPerLevel); nonnegative(unspentPerkPoints); nonnegative(usedPerkPoints);
            StrictJson.require(xpWithinLevelRaw.compareTo(xpPerLevel.multiply(BigInteger.valueOf(100_000))) < 0,
                    "XP within-level range violated");
        }
    }

    public record UnavailableProgress(Lifestyle lifestyle, String reason) implements ProgressRow {
        public UnavailableProgress { Objects.requireNonNull(lifestyle); StrictJson.text(reason); }
    }

    public record ProgressObservation(FrameIdentity frame, Completeness completeness, List<ProgressRow> rows) {
        public ProgressObservation {
            Objects.requireNonNull(frame); Objects.requireNonNull(completeness); rows = List.copyOf(rows);
        }
    }

    /** Candidate spelling may be foreign: policy must reject it against the pinned catalog. */
    public record Candidate(String key, String lifestyleKey) {
        public Candidate { StrictJson.text(key); StrictJson.text(lifestyleKey); }
    }

    public sealed interface CandidateObservation permits LegalCandidates, UnavailableCandidates { }
    public record LegalCandidates(String scope, List<Candidate> items) implements CandidateObservation {
        public LegalCandidates { StrictJson.text(scope); items = List.copyOf(items); }
    }
    public record UnavailableCandidates(String sourceStatus) implements CandidateObservation {
        public UnavailableCandidates {
            StrictJson.text(sourceStatus);
            StrictJson.require(!sourceStatus.equals("available"), "available candidates require their payload");
        }
    }

    public record Input(FrameIdentity snapshotFrame, ProgressObservation progress,
            CandidateObservation candidates, ExpectedBinding binding, List<String> owned) {
        public Input {
            Objects.requireNonNull(snapshotFrame); Objects.requireNonNull(progress);
            Objects.requireNonNull(candidates); Objects.requireNonNull(binding);
            owned = List.copyOf(owned);
            for (String key : owned) { StrictJson.text(key); }
            StrictJson.require(snapshotFrame.equals(binding.frame()), "expected binding differs from snapshot");
        }
    }

    public record Action(String targetKey, Lifestyle targetLifestyle, ExpectedBinding expected) {
        public Action { StrictJson.text(targetKey); Objects.requireNonNull(targetLifestyle); Objects.requireNonNull(expected); }
        public String kind() { return "perk"; }
        public Reason reason() { return Reason.FINAL_LEGAL_OBSERVED_POINT; }
    }

    public sealed interface Decision permits ObservationUnavailable, CandidatesUnavailable, NoLegalMinimum, Recommendation {
        Status status();
    }
    public record ObservationUnavailable(Reason reason, Optional<List<Lifestyle>> unavailableLifestyles)
            implements Decision {
        public ObservationUnavailable {
            Objects.requireNonNull(reason); Objects.requireNonNull(unavailableLifestyles);
            unavailableLifestyles = unavailableLifestyles.map(List::copyOf);
        }
        @Override public Status status() { return Status.OBSERVATION_UNAVAILABLE; }
    }
    public record CandidatesUnavailable(Optional<Reason> reason) implements Decision {
        public CandidatesUnavailable { Objects.requireNonNull(reason); }
        @Override public Status status() { return Status.LEGAL_CANDIDATES_UNAVAILABLE; }
    }
    public record NoLegalMinimum(Reason reason, Map<Lifestyle, BigInteger> observedPositivePoints) implements Decision {
        public NoLegalMinimum {
            Objects.requireNonNull(reason); observedPositivePoints = Map.copyOf(observedPositivePoints);
            observedPositivePoints.forEach((key, value) -> { Objects.requireNonNull(key); positive(value); });
        }
        @Override public Status status() { return Status.NO_LEGAL_MINIMUM; }
    }
    public record Recommendation(Action action, Completeness progressStatus, BigInteger observedTargetPoints)
            implements Decision {
        public Recommendation { Objects.requireNonNull(action); Objects.requireNonNull(progressStatus); positive(observedTargetPoints); }
        @Override public Status status() { return Status.RECOMMEND_ACTION; }
    }

    private static void nonnegative(BigInteger value) {
        StrictJson.require(value != null && value.signum() >= 0, "nonnegative exact integer required");
    }
    private static void positive(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0, "positive exact integer required");
    }
}
