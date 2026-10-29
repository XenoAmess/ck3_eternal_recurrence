package org.xar.ck3.control.wave3.governance.heirranking;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Existing final-legal five-row value filter and stable marriage opportunity order. */
public final class HeirCandidateRanking {
    public static final BigInteger MAX_BETROTHAL_AGE_GAP_RAW = BigInteger.TWO;
    private static final BigInteger ABSENT_COMPACT_DYNASTY = BigInteger.valueOf(-1);

    private HeirCandidateRanking() { }

    public enum Outcome { MARRIAGE, BETROTHAL, UNAVAILABLE }

    public enum RejectionReason {
        INVALID_CANDIDATE_IDENTITY("invalid_candidate_identity"),
        NOT_IN_FINAL_LEGAL_ROWS("not_in_final_legal_rows"),
        PREVIOUSLY_REFUSED_OR_INVALIDATED("previously_refused_or_invalidated"),
        PROJECTION_UNAVAILABLE("projection_unavailable"),
        ACTOR_IDENTITY_MISMATCH("actor_identity_mismatch"),
        HEIR_IDENTITY_MISMATCH("heir_identity_mismatch"),
        RECIPIENT_IDENTITY_MISMATCH("recipient_identity_mismatch"),
        CANDIDATE_DYNASTY_CHANGED("candidate_dynasty_changed_since_ranking"),
        CANDIDATE_AGE_CHANGED("candidate_age_changed_since_ranking"),
        HEIR_AGE_CHANGED("heir_age_changed_since_ranking"),
        OUTCOME_UNAVAILABLE("outcome_unavailable"),
        HEIR_ALREADY_BETROTHED("heir_already_betrothed"),
        HEIR_SPOUSE_LIST_NOT_EMPTY("heir_spouse_list_not_empty"),
        HEIR_PRIMARY_SPOUSE_PRESENT("heir_primary_spouse_present"),
        PLAYED_DYNASTY_UNAVAILABLE("played_dynasty_unavailable"),
        HEIR_DYNASTY_NOT_PLAYED("heir_dynasty_not_played_dynasty"),
        HEIR_HOUSE_NOT_PLAYED("heir_house_not_played_house"),
        HEIR_SELECTOR_UNAVAILABLE("heir_selector_unavailable"),
        CANDIDATE_SELECTOR_UNAVAILABLE("candidate_selector_unavailable"),
        SAME_SELECTOR_PAIR("same_selector_pair"),
        LINEALITY_NOT_HEIR_ALIGNED("lineality_not_heir_aligned"),
        BETROTHAL_RANKING_INPUTS_UNAVAILABLE("betrothal_ranking_inputs_unavailable"),
        NOT_ORDINARY_MINOR_BETROTHAL("not_ordinary_minor_betrothal"),
        ADULT_WAIT_MEASURE_UNAVAILABLE("adult_wait_measure_unavailable"),
        BETROTHAL_AGE_GAP_OUT_OF_BOUNDS("betrothal_age_gap_out_of_bounds"),
        BETROTHAL_EXTERNAL_DYNASTY_UNAVAILABLE("betrothal_external_dynasty_unavailable"),
        BETROTHAL_ALLIANCE_PROJECTION_UNAVAILABLE("betrothal_alliance_projection_unavailable"),
        NATIVE_CAN_SEND_NOT_TRUE("native_can_send_not_true"),
        RECIPIENT_ANSWER_BLOCKS_SEND("recipient_answer_blocks_send"),
        RECIPIENT_ANSWER_STATUS_NOT_ALLOWED("recipient_answer_status_not_allowed"),
        RECIPIENT_ACCEPT_NOT_POSITIVE("recipient_accept_not_positive");

        private final String wire;
        RejectionReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Roles(Optional<BigInteger> candidate, Optional<BigInteger> actor,
                        Optional<BigInteger> heir, Optional<BigInteger> recipient) {
        public Roles {
            Objects.requireNonNull(candidate, "candidate observation");
            Objects.requireNonNull(actor, "actor observation");
            Objects.requireNonNull(heir, "heir observation");
            Objects.requireNonNull(recipient, "recipient observation");
        }
    }

    public record Lineage(Optional<BigInteger> candidateDynasty, Optional<BigInteger> playedDynasty,
                          Optional<BigInteger> heirDynasty, Optional<BigInteger> playedHouse,
                          Optional<BigInteger> heirHouse) {
        public Lineage {
            Objects.requireNonNull(candidateDynasty, "candidate dynasty");
            Objects.requireNonNull(playedDynasty, "played dynasty");
            Objects.requireNonNull(heirDynasty, "heir dynasty");
            Objects.requireNonNull(playedHouse, "played house");
            Objects.requireNonNull(heirHouse, "heir house");
        }
    }

    public record Adulthood(Optional<BigInteger> heirMeasure, Optional<BigInteger> candidateMeasure,
                            Optional<BigInteger> heirThreshold, Optional<BigInteger> candidateThreshold,
                            Optional<Boolean> heirIsAdult, Optional<Boolean> candidateIsAdult,
                            Optional<Boolean> grandWedding) {
        public Adulthood {
            Objects.requireNonNull(heirMeasure, "heir measure");
            Objects.requireNonNull(candidateMeasure, "candidate measure");
            Objects.requireNonNull(heirThreshold, "heir threshold");
            Objects.requireNonNull(candidateThreshold, "candidate threshold");
            Objects.requireNonNull(heirIsAdult, "heir adulthood");
            Objects.requireNonNull(candidateIsAdult, "candidate adulthood");
            Objects.requireNonNull(grandWedding, "grand wedding");
        }
    }

    public record Relationship(Optional<BigInteger> betrothed, Optional<BigInteger> primarySpouse,
                               Optional<List<BigInteger>> spouses) {
        public Relationship {
            Objects.requireNonNull(betrothed, "betrothed observation");
            Objects.requireNonNull(primarySpouse, "primary spouse observation");
            spouses = Objects.requireNonNull(spouses, "spouse collection observation").map(List::copyOf);
        }
    }

    public record AlliancePair(Optional<BigInteger> first, Optional<BigInteger> second,
                               Optional<Boolean> alreadyAllied, Optional<Boolean> bothHaveRealmData,
                               Optional<Boolean> wouldAttempt) {
        public AlliancePair {
            Objects.requireNonNull(first, "first character");
            Objects.requireNonNull(second, "second character");
            Objects.requireNonNull(alreadyAllied, "allied observation");
            Objects.requireNonNull(bothHaveRealmData, "realm data observation");
            Objects.requireNonNull(wouldAttempt, "attempt observation");
        }
    }

    public record LegalRow(Roles roles, Lineage lineage, Adulthood adulthood,
                           Optional<Boolean> realmBacked, Optional<Boolean> completeCanSend,
                           Optional<Boolean> answerAllowsSend, Optional<BigInteger> answerStatus,
                           Optional<BigInteger> acceptance) {
        public LegalRow {
            Objects.requireNonNull(roles, "legal roles");
            Objects.requireNonNull(lineage, "legal lineage");
            Objects.requireNonNull(adulthood, "legal adulthood");
            Objects.requireNonNull(realmBacked, "realm backing");
            Objects.requireNonNull(completeCanSend, "native send observation");
            Objects.requireNonNull(answerAllowsSend, "answer send observation");
            Objects.requireNonNull(answerStatus, "answer status");
            Objects.requireNonNull(acceptance, "acceptance observation");
        }
    }

    public record ProjectedRow(int ordinal, Roles roles, boolean available, Outcome outcome,
                               Lineage lineage, Adulthood adulthood, Relationship relationship,
                               Optional<BigInteger> heirSelector, Optional<BigInteger> candidateSelector,
                               Optional<Boolean> effectiveMatrilineal,
                               Optional<List<AlliancePair>> alliancePairs) {
        public ProjectedRow {
            if (ordinal < 0) { throw new IllegalArgumentException("negative projection ordinal"); }
            Objects.requireNonNull(roles, "projected roles");
            Objects.requireNonNull(outcome, "projected outcome");
            Objects.requireNonNull(lineage, "projected lineage");
            Objects.requireNonNull(adulthood, "projected adulthood");
            Objects.requireNonNull(relationship, "current relationship");
            Objects.requireNonNull(heirSelector, "heir selector");
            Objects.requireNonNull(candidateSelector, "candidate selector");
            Objects.requireNonNull(effectiveMatrilineal, "effective option");
            alliancePairs = Objects.requireNonNull(alliancePairs, "alliance projection").map(List::copyOf);
        }
    }

    public enum Value {
        ADULT_MARRIAGE("unpartnered_first_heir_adult_marriage_opportunity"),
        BETROTHAL_ALLIANCE("bounded_first_heir_betrothal_and_realm_alliance_attempt"),
        BETROTHAL_EXTERNAL_DYNASTY("bounded_first_heir_external_dynasty_betrothal_opportunity");

        private final String wire;
        Value(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record RankedChoice(BigInteger candidate, int selectedRowOrdinal, Outcome outcome,
                                BigInteger acceptance, BigInteger ageGap, boolean allianceAttempt,
                                Value value) {
        public RankedChoice {
            Objects.requireNonNull(candidate, "candidate");
            Objects.requireNonNull(outcome, "outcome");
            Objects.requireNonNull(acceptance, "acceptance");
            Objects.requireNonNull(ageGap, "age gap");
            Objects.requireNonNull(value, "value");
            if (candidate.signum() <= 0 || selectedRowOrdinal < 0 || acceptance.signum() <= 0
                    || ageGap.signum() < 0 || outcome == Outcome.UNAVAILABLE) {
                throw new IllegalArgumentException("ranked choice requires positive observed opportunity values");
            }
            Value expected = outcome == Outcome.MARRIAGE ? Value.ADULT_MARRIAGE
                    : allianceAttempt ? Value.BETROTHAL_ALLIANCE : Value.BETROTHAL_EXTERNAL_DYNASTY;
            if (value != expected) { throw new IllegalArgumentException("value differs from its observed outcome branch"); }
        }
    }

    public static List<RejectionReason> rejectionReasons(Optional<LegalRow> source, ProjectedRow row,
                                                 Set<BigInteger> rejectedCandidates) {
        Set<BigInteger> rejected = Set.copyOf(rejectedCandidates);
        if (!positive(row.roles().candidate())) { return List.of(RejectionReason.INVALID_CANDIDATE_IDENTITY); }
        if (source.isEmpty()) { return List.of(RejectionReason.NOT_IN_FINAL_LEGAL_ROWS); }
        LegalRow legal = source.orElseThrow();
        List<RejectionReason> reasons = new ArrayList<>();
        if (rejected.contains(row.roles().candidate().orElseThrow())) { reasons.add(RejectionReason.PREVIOUSLY_REFUSED_OR_INVALIDATED); }
        if (!row.available()) { reasons.add(RejectionReason.PROJECTION_UNAVAILABLE); }
        if (!row.roles().actor().equals(legal.roles().actor())) { reasons.add(RejectionReason.ACTOR_IDENTITY_MISMATCH); }
        if (!row.roles().heir().equals(legal.roles().heir())) { reasons.add(RejectionReason.HEIR_IDENTITY_MISMATCH); }
        if (!row.roles().recipient().equals(legal.roles().recipient())) { reasons.add(RejectionReason.RECIPIENT_IDENTITY_MISMATCH); }
        if (legal.lineage().candidateDynasty().isPresent()) {
            Optional<BigInteger> ranked = legal.lineage().candidateDynasty().filter(value -> !value.equals(ABSENT_COMPACT_DYNASTY));
            if (!row.lineage().candidateDynasty().equals(ranked)) { reasons.add(RejectionReason.CANDIDATE_DYNASTY_CHANGED); }
        }
        changed(legal.adulthood().candidateMeasure(), row.adulthood().candidateMeasure(),
                RejectionReason.CANDIDATE_AGE_CHANGED, reasons);
        changed(legal.adulthood().heirMeasure(), row.adulthood().heirMeasure(),
                RejectionReason.HEIR_AGE_CHANGED, reasons);
        if (row.outcome() == Outcome.UNAVAILABLE) { reasons.add(RejectionReason.OUTCOME_UNAVAILABLE); }
        if (row.relationship().betrothed().isPresent()) { reasons.add(RejectionReason.HEIR_ALREADY_BETROTHED); }
        if (row.relationship().spouses().isEmpty() || !row.relationship().spouses().orElseThrow().isEmpty()) {
            reasons.add(RejectionReason.HEIR_SPOUSE_LIST_NOT_EMPTY);
        }
        if (row.relationship().primarySpouse().isPresent()) { reasons.add(RejectionReason.HEIR_PRIMARY_SPOUSE_PRESENT); }
        if (!positive(row.lineage().playedDynasty())) { reasons.add(RejectionReason.PLAYED_DYNASTY_UNAVAILABLE); }
        if (!row.lineage().playedDynasty().equals(row.lineage().heirDynasty())) { reasons.add(RejectionReason.HEIR_DYNASTY_NOT_PLAYED); }
        if (!row.lineage().playedHouse().equals(row.lineage().heirHouse())) { reasons.add(RejectionReason.HEIR_HOUSE_NOT_PLAYED); }
        boolean heirSelectorKnown = selector(row.heirSelector());
        boolean candidateSelectorKnown = selector(row.candidateSelector());
        if (!heirSelectorKnown) { reasons.add(RejectionReason.HEIR_SELECTOR_UNAVAILABLE); }
        if (!candidateSelectorKnown) { reasons.add(RejectionReason.CANDIDATE_SELECTOR_UNAVAILABLE); }
        if (heirSelectorKnown && candidateSelectorKnown) {
            if (row.heirSelector().equals(row.candidateSelector())) { reasons.add(RejectionReason.SAME_SELECTOR_PAIR); }
            boolean expectedMatrilineal = row.heirSelector().orElseThrow().equals(BigInteger.ONE);
            if (!row.effectiveMatrilineal().equals(Optional.of(expectedMatrilineal))) { reasons.add(RejectionReason.LINEALITY_NOT_HEIR_ALIGNED); }
        }
        if (row.outcome() == Outcome.BETROTHAL) {
            if (legal.adulthood().heirMeasure().isEmpty() || legal.adulthood().candidateMeasure().isEmpty()
                    || legal.lineage().playedDynasty().isEmpty() || legal.lineage().heirDynasty().isEmpty()
                    || legal.lineage().candidateDynasty().isEmpty() || !is(legal.realmBacked(), true)) {
                reasons.add(RejectionReason.BETROTHAL_RANKING_INPUTS_UNAVAILABLE);
            }
            Adulthood adult = row.adulthood();
            if (!is(adult.grandWedding(), false) || adult.heirIsAdult().isEmpty()
                    || adult.candidateIsAdult().isEmpty() || (is(adult.heirIsAdult(), true) && is(adult.candidateIsAdult(), true))) {
                reasons.add(RejectionReason.NOT_ORDINARY_MINOR_BETROTHAL);
            }
            if (adult.heirMeasure().isEmpty() || adult.candidateMeasure().isEmpty()
                    || adult.heirThreshold().isEmpty() || adult.candidateThreshold().isEmpty()) {
                reasons.add(RejectionReason.ADULT_WAIT_MEASURE_UNAVAILABLE);
            } else if (!adult.heirIsAdult().equals(Optional.of(adult.heirMeasure().orElseThrow()
                    .compareTo(adult.heirThreshold().orElseThrow()) >= 0))
                    || !adult.candidateIsAdult().equals(Optional.of(adult.candidateMeasure().orElseThrow()
                    .compareTo(adult.candidateThreshold().orElseThrow()) >= 0))
                    || adult.heirMeasure().orElseThrow().subtract(adult.candidateMeasure().orElseThrow()).abs()
                    .compareTo(MAX_BETROTHAL_AGE_GAP_RAW) > 0) {
                reasons.add(RejectionReason.BETROTHAL_AGE_GAP_OUT_OF_BOUNDS);
            }
            if (!positive(row.lineage().candidateDynasty())
                    || row.lineage().candidateDynasty().equals(row.lineage().playedDynasty())) {
                reasons.add(RejectionReason.BETROTHAL_EXTERNAL_DYNASTY_UNAVAILABLE);
            }
            if (row.alliancePairs().isEmpty()) { reasons.add(RejectionReason.BETROTHAL_ALLIANCE_PROJECTION_UNAVAILABLE); }
        }
        if (!is(legal.completeCanSend(), true)) { reasons.add(RejectionReason.NATIVE_CAN_SEND_NOT_TRUE); }
        if (!is(legal.answerAllowsSend(), true)) { reasons.add(RejectionReason.RECIPIENT_ANSWER_BLOCKS_SEND); }
        if (!selector(legal.answerStatus())) { reasons.add(RejectionReason.RECIPIENT_ANSWER_STATUS_NOT_ALLOWED); }
        if (!positive(legal.acceptance())) { reasons.add(RejectionReason.RECIPIENT_ACCEPT_NOT_POSITIVE); }
        return List.copyOf(reasons);
    }

    public static List<RankedChoice> rank(List<LegalRow> legalRows, List<ProjectedRow> projected,
                                          Set<BigInteger> rejectedCandidates) {
        Map<BigInteger, LegalRow> byId = new HashMap<>();
        for (LegalRow row : List.copyOf(legalRows)) { row.roles().candidate().ifPresent(id -> byId.put(id, row)); }
        List<RankedChoice> choices = new ArrayList<>();
        List<ProjectedRow> rows = List.copyOf(projected);
        if (rows.size() != 5) { return List.of(); }
        for (ProjectedRow row : rows) {
            Optional<LegalRow> source = row.roles().candidate().map(byId::get);
            if (!rejectionReasons(source, row, rejectedCandidates).isEmpty()) { continue; }
            LegalRow legal = source.orElseThrow();
            BigInteger candidate = row.roles().candidate().orElseThrow();
            ProjectedRow selected = rows.stream().filter(value -> value.roles().candidate().equals(row.roles().candidate()))
                    .findFirst().orElseThrow();
            List<AlliancePair> pairs = selected.alliancePairs().orElseThrow(() ->
                    new IllegalArgumentException("eligible marriage requires its native alliance projection"));
            boolean attempt = pairs.stream().anyMatch(pair -> pair.first().equals(legal.roles().actor())
                    && pair.second().equals(selected.roles().recipient()) && is(pair.alreadyAllied(), false)
                    && is(pair.bothHaveRealmData(), true) && is(pair.wouldAttempt(), true));
            BigInteger gap = row.adulthood().heirMeasure().orElseThrow(() ->
                    new IllegalArgumentException("eligible projection requires heir adult measure")).subtract(
                    row.adulthood().candidateMeasure().orElseThrow(() ->
                    new IllegalArgumentException("eligible projection requires candidate adult measure"))).abs();
            Value value = row.outcome() == Outcome.MARRIAGE ? Value.ADULT_MARRIAGE
                    : attempt ? Value.BETROTHAL_ALLIANCE : Value.BETROTHAL_EXTERNAL_DYNASTY;
            choices.add(new RankedChoice(candidate, selected.ordinal(), row.outcome(),
                    legal.acceptance().orElseThrow(), gap, attempt, value));
        }
        choices.sort(Comparator.comparing((RankedChoice choice) -> choice.outcome() == Outcome.MARRIAGE).reversed()
                .thenComparing(RankedChoice::ageGap).thenComparing(RankedChoice::acceptance, Comparator.reverseOrder())
                .thenComparing(RankedChoice::candidate));
        return List.copyOf(choices);
    }

    private static boolean positive(Optional<BigInteger> value) { return value.isPresent() && value.orElseThrow().signum() > 0; }
    private static boolean selector(Optional<BigInteger> value) {
        return value.isPresent() && (value.orElseThrow().equals(BigInteger.ZERO) || value.orElseThrow().equals(BigInteger.ONE));
    }
    private static boolean is(Optional<Boolean> value, boolean expected) { return value.equals(Optional.of(expected)); }
    private static void changed(Optional<BigInteger> source, Optional<BigInteger> observed,
                                RejectionReason reason, List<RejectionReason> reasons) {
        if (source.isPresent() && !source.equals(observed)) { reasons.add(reason); }
    }
}
