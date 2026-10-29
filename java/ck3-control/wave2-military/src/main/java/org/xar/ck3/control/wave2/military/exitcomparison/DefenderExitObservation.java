package org.xar.ck3.control.wave2.military.exitcomparison;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Active tactical-planner observation only. An observed option never supplies exit authority. */
public final class DefenderExitObservation {
    public static final String POLICY = "formal-primary-defender-de-jure-exit-observation-v1";
    private DefenderExitObservation() { }

    /** This observer preserves its legacy arbitrary-integer frame, distinct from the native query ABI. */
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision,
                        BigInteger dateRaw, String episodeRunId, BigInteger connectionGeneration,
                        BigInteger playedCharacterId, BigInteger warId, BigInteger relativeWarScore) {
        public Frame {
            textAllowEmpty(snapshotId);
            textAllowEmpty(episodeRunId);
            require(revision != null && nativeRevision != null && dateRaw != null && connectionGeneration != null,
                    "complete exact-integer frame required");
            require(playedCharacterId != null && playedCharacterId.signum() > 0
                    && warId != null && warId.signum() > 0 && relativeWarScore != null && relativeWarScore.signum() < 0,
                    "positive defender identity and negative score required");
        }
    }

    public enum Outcome {
        VICTORY("victory"), WHITE_PEACE("white_peace"), SURRENDER("surrender");
        private final String wire;
        Outcome(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum AbsoluteOutcome {
        ATTACKER_VICTORY("attacker_victory"), ATTACKER_DEFEAT("attacker_defeat"), WHITE_PEACE("white_peace");
        private final String wire;
        AbsoluteOutcome(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static AbsoluteOutcome fromWire(String value) {
            for (AbsoluteOutcome candidate : values()) {
                if (candidate.wire.equals(value)) { return candidate; }
            }
            throw new IllegalArgumentException("invalid absolute outcome");
        }
    }

    public record OptionObservation(Outcome outcome, boolean nativeLegalNow, Boolean recipientAcceptsNow,
                                    boolean materialTermsObservable, String materialTermsStatus,
                                    String materialTermsReason, AbsoluteOutcome absoluteOutcome) {
        public OptionObservation {
            require(outcome != null && absoluteOutcome != null, "typed option outcome required");
            require(!materialTermsObservable && "unavailable".equals(materialTermsStatus)
                    && "cb_specific_terms_not_observable".equals(materialTermsReason),
                    "current normalizer cannot invent material terms");
        }
    }

    public enum RedReason {
        FRAME_OR_CARDINALITY_MISMATCH("native_options_frame_or_cardinality_mismatch"),
        SCHEMA_INVALID("native_options_schema_invalid"),
        WAR_IDENTITY_MISMATCH("native_options_war_identity_mismatch");
        private final String wire;
        RedReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public sealed interface Result permits NotApplicable, OptionsRequired, ObservationRed, NativeLegality { }
    public record NotApplicable() implements Result { }
    public record OptionsRequired(Frame frame) implements Result {
        public OptionsRequired { require(frame != null, "frame required"); }
        public String requiredObservationStep() {
            require(frame.warId().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                    "query WarID outside positive int32 ABI");
            return "query-war-termination-options-" + frame.warId();
        }
    }
    public record ObservationRed(Frame frame, RedReason reason) implements Result {
        public ObservationRed { require(frame != null && reason != null, "bound red observation required"); }
    }
    public record NativeLegality(Frame frame, int casusBelliIndex, String casusBelliKey,
                                 Integer warDurationDays, List<OptionObservation> options) implements Result {
        public NativeLegality {
            require(frame != null && casusBelliIndex == 17 && "individual_county_de_jure_cb".equals(casusBelliKey),
                    "exact de-jure observation required");
            require(warDurationDays == null || warDurationDays >= 0, "nonnegative observed duration required");
            require(options != null && options.size() == 3, "complete three-way option projection required");
            options = List.copyOf(options);
            for (int index = 0; index < Outcome.values().length; index++) {
                require(options.get(index).outcome() == Outcome.values()[index], "stable unique outcome ordering required");
            }
        }
        public List<Outcome> legalAcceptedOutcomes() {
            return options.stream().filter(row -> row.nativeLegalNow() && Boolean.TRUE.equals(row.recipientAcceptsNow()))
                    .map(OptionObservation::outcome).toList();
        }
    }

    public enum HandoffStatus {
        CANDIDATE_REQUIRES_REVALIDATION("existing_tactical_candidate_requires_revalidation"),
        NO_TACTICAL_CANDIDATE("no_tactical_candidate");
        private final String wire;
        HandoffStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record ContinuationHandoff(HandoffStatus status, String candidateSelectedStep) {
        public ContinuationHandoff {
            require(status != null && (status == HandoffStatus.CANDIDATE_REQUIRES_REVALIDATION
                    ? candidateSelectedStep != null : candidateSelectedStep == null), "typed tactical handoff required");
        }
    }

    /** The actual strategy consumer's read-only handoff; it does not rewrite the existing plan or decision. */
    public static ContinuationHandoff continuationHandoff(String candidateSelectedStep) {
        String candidate = candidateSelectedStep;
        if (candidate != null && (candidate.startsWith("surrender-war-") || candidate.startsWith("offer-white-peace-"))) {
            candidate = null;
        }
        return new ContinuationHandoff(candidate == null ? HandoffStatus.NO_TACTICAL_CANDIDATE
                : HandoffStatus.CANDIDATE_REQUIRES_REVALIDATION, candidate);
    }

    static void textAllowEmpty(String value) {
        require(value != null, "string required");
        if (!value.isEmpty()) { StrictJson.text(value); }
    }
}
