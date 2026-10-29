package org.xar.ck3.control.governance.marriage;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Typed projection of the fields actually read by the existing child policy. */
public final class MarriageModel {
    private MarriageModel() { }

    public enum Presence { MISSING, NULL, VALUE }

    /** Missing, explicit null and a value survive projection and JSON round trips. */
    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) {
                throw new IllegalArgumentException("field presence/value mismatch");
            }
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nil() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
    }

    public enum IntegerTerm {
        NATIVE_REVISION("native_revision"), QUERY_SEQUENCE("query_sequence"),
        LEGALITY_QUERY_SEQUENCE("legality_query_sequence"), PLAYED_ID("played_character_id"),
        SUBJECT_ID("subject_character_id"), CANDIDATE_ID("candidate_character_id"),
        RECIPIENT_MATCHMAKER_ID("recipient_matchmaker_character_id"),
        ACTOR_ID("actor_character_id"), HEIR_ID("heir_character_id"), RECIPIENT_ID("recipient_character_id"),
        ADULT_MEASURE("adult_measure_raw"), ADULT_THRESHOLD("adult_threshold_raw"),
        HOUSE_ID("house_id"), DYNASTY_ID("dynasty_id"),
        HEIR_ADULT_MEASURE("heir_adult_measure_raw"), HEIR_ADULT_THRESHOLD("heir_adult_threshold_raw"),
        CANDIDATE_ADULT_MEASURE("candidate_adult_measure_raw"), CANDIDATE_ADULT_THRESHOLD("candidate_adult_threshold_raw"),
        CANDIDATE_DYNASTY_ID("candidate_dynasty_id"), ACCEPT("recipient_ai_accept_raw"),
        ANSWER_STATUS("recipient_answer_status_raw"), HEIR_SEX("heir_sex_selector_raw"),
        CANDIDATE_SEX("candidate_sex_selector_raw"), HEIR_HOUSE_ID("heir_house_id"),
        HEIR_DYNASTY_ID("heir_dynasty_id"), PLAYED_HOUSE_ID("played_house_id"),
        PLAYED_DYNASTY_ID("played_dynasty_id"), EFFECTIVE_FERTILITY("effective_raw");
        private final String wire;
        IntegerTerm(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum BooleanTerm {
        CHILD_VERIFIED("player_child_verified"), CAN_SEND("complete_can_send"),
        ANSWER_ALLOWS("recipient_answer_allows_send"), READ_ONLY("read_only"),
        REQUEST_MATRILINEAL("request_matrilineal_option"), FINAL_SAMPLED("final_legality_sampled"),
        REQUESTED_MATRILINEAL("requested_matrilineal_option"), SELECTED_MATRILINEAL("matrilineal_option_selected"),
        EFFECTIVE_MATRILINEAL("effective_matrilineal_if_accepted"), GRAND_WEDDING("grand_wedding_option_selected"),
        HEIR_ADULT("heir_is_adult"), CANDIDATE_ADULT("candidate_is_adult"),
        EXTENSION_PRESENT("extension_present"), GATE_EVALUATED("native_gate_evaluated"),
        GATE_ALLOWS("native_gate_allows"), WOULD_ATTEMPT_ALLIANCE("would_attempt_if_accepted");
        private final String wire;
        BooleanTerm(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum TextTerm {
        SCHEMA("schema"), STATUS("status"), OUTCOME("predicted_outcome_if_accepted"),
        SOURCE("source"), PAYER("payer_role"), COST_TIMING("application_timing");
        private final String wire;
        TextTerm(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** Enum keys are the single field contract; no untyped business map crosses this boundary. */
    public record Facts(Map<IntegerTerm, Field<BigInteger>> integers,
                        Map<BooleanTerm, Field<Boolean>> booleans,
                        Map<TextTerm, Field<String>> texts) {
        public Facts {
            integers = Map.copyOf(integers);
            booleans = Map.copyOf(booleans);
            texts = Map.copyOf(texts);
        }
        public BigInteger number(IntegerTerm key) { return integers.getOrDefault(key, Field.missing()).value(); }
        public Boolean flag(BooleanTerm key) { return booleans.getOrDefault(key, Field.missing()).value(); }
        public String text(TextTerm key) { return texts.getOrDefault(key, Field.missing()).value(); }
    }

    public record Relationship(Field<BigInteger> betrothed, Field<BigInteger> primarySpouse,
                               Field<List<BigInteger>> spouses) {
        public Relationship {
            Objects.requireNonNull(betrothed); Objects.requireNonNull(primarySpouse); Objects.requireNonNull(spouses);
            if (spouses.presence() == Presence.VALUE) { spouses = Field.of(List.copyOf(spouses.value())); }
        }
    }

    public record CompactCandidate(Facts facts) { public CompactCandidate { Objects.requireNonNull(facts); } }

    public record Legality(Facts facts, Relationship relationship, Field<List<CompactCandidate>> candidates) {
        public Legality {
            Objects.requireNonNull(facts); Objects.requireNonNull(relationship); Objects.requireNonNull(candidates);
            if (candidates.presence() == Presence.VALUE) { candidates = Field.of(List.copyOf(candidates.value())); }
        }
    }

    public enum CostTerm {
        GOLD("gold_raw"), PRESTIGE("prestige_raw"), PIETY("piety_raw"), RENOWN("renown_raw"),
        INFLUENCE("influence_raw"), HERD("herd_raw"), TREASURY("treasury_raw"),
        TREASURY_OR_GOLD("treasury_or_gold_raw"), MERIT("merit_raw"), BARTER_GOODS("barter_goods_raw");
        private final String wire;
        CostTerm(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Costs(Facts facts, Map<CostTerm, Field<BigInteger>> amounts) {
        public Costs { Objects.requireNonNull(facts); amounts = Map.copyOf(amounts); }
    }

    public record FullValue(Facts facts, Relationship heirRelationship, Relationship candidateRelationship,
                            Field<Facts> heirFertility, Field<Facts> candidateFertility,
                            Field<Costs> costs, Field<List<Facts>> alliances) {
        public FullValue {
            Objects.requireNonNull(facts); Objects.requireNonNull(heirRelationship); Objects.requireNonNull(candidateRelationship);
            Objects.requireNonNull(heirFertility); Objects.requireNonNull(candidateFertility); Objects.requireNonNull(costs);
            Objects.requireNonNull(alliances);
            if (alliances.presence() == Presence.VALUE) { alliances = Field.of(List.copyOf(alliances.value())); }
        }
    }

    public record CandidateValue(Facts facts, Field<FullValue> row) {
        public CandidateValue { Objects.requireNonNull(facts); Objects.requireNonNull(row); }
    }

    public record Request(Legality legality, List<CandidateValue> values, boolean splitSuccessorVerified,
                          Set<BigInteger> excludedCandidateIds, int shortlistLimit) {
        public Request {
            Objects.requireNonNull(legality); values = List.copyOf(values); excludedCandidateIds = Set.copyOf(excludedCandidateIds);
            if (shortlistLimit < 1 || shortlistLimit > 5) { throw new IllegalArgumentException("child default shortlist limit must be 1..5"); }
            if (excludedCandidateIds.stream().anyMatch(id -> id.signum() <= 0 || id.bitLength() > 31)) {
                throw new IllegalArgumentException("excluded native CharacterID must be positive and below 2**31");
            }
        }
    }

    public enum Status { SELECTED, NO_POSITIVE_VALUE }
    public enum Reason {
        SPLIT_CHILD_SUBJECT_NOT_VERIFIED, FINAL_LEGAL_CANDIDATES_UNAVAILABLE,
        DUPLICATE_FULL_VALUE, DUPLICATE_FINAL_LEGAL_CANDIDATE,
        MISSING_EXACT_LEGAL_VALUE, NATIVE_FINAL_OR_FRAME_UNAVAILABLE, SEX_LINEALITY_MISMATCH,
        FAMILY_RELATION_OR_LINEALITY_NOT_VALUED, ADULT_TIMING_UNAVAILABLE, CANDIDATE_NOT_ADULT,
        BETROTHAL_WAIT_OR_FUTURE_AGE_TOO_HIGH, NATIVE_FERTILITY_GATE_UNAVAILABLE,
        UPFRONT_COST_UNPRICED, ALLIANCE_OBLIGATION_UNPRICED,
        POSITIVE_EARLY_SPLIT_SUCCESSOR_BETROTHAL, INCOMPLETE_TOP_TWO_FULL_VALUE_COMPARISON,
        INCOMPLETE_SAME_FRAME_FULL_VALUE, EARLY_ZERO_UPFRONT_COST_SPLIT_SUCCESSOR_BETROTHAL,
        NO_BOUNDED_POSITIVE_PAIR;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }

    public record PositiveTiming(BigInteger childWaitRaw, BigInteger candidateAgeAtChildAdulthoodRaw,
                                 BigInteger recipientAiAcceptRaw) {
        public PositiveTiming { Objects.requireNonNull(childWaitRaw); Objects.requireNonNull(candidateAgeAtChildAdulthoodRaw); Objects.requireNonNull(recipientAiAcceptRaw); }
    }
    public record Evaluation(BigInteger candidateCharacterId, Reason reason, PositiveTiming positiveTiming) {
        public Evaluation {
            Objects.requireNonNull(candidateCharacterId); Objects.requireNonNull(reason);
            if ((reason == Reason.POSITIVE_EARLY_SPLIT_SUCCESSOR_BETROTHAL) != (positiveTiming != null)) {
                throw new IllegalArgumentException("only positive evaluation has timing fields");
            }
        }
    }
    public record Decision(Status status, BigInteger selectedCandidateCharacterId, List<Evaluation> evaluated, Reason reason) {
        public Decision {
            Objects.requireNonNull(status); Objects.requireNonNull(reason); evaluated = List.copyOf(evaluated);
            if ((status == Status.SELECTED) != (selectedCandidateCharacterId != null)) {
                throw new IllegalArgumentException("selected candidate/status mismatch");
            }
        }
    }
}
