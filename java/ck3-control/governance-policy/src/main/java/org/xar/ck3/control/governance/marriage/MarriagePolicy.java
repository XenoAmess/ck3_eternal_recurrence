package org.xar.ck3.control.governance.marriage;

import static org.xar.ck3.control.governance.marriage.MarriageModel.*;
import static org.xar.ck3.control.governance.marriage.MarriageModel.BooleanTerm.*;
import static org.xar.ck3.control.governance.marriage.MarriageModel.IntegerTerm.*;
import static org.xar.ck3.control.governance.marriage.MarriageModel.Reason.*;
import static org.xar.ck3.control.governance.marriage.MarriageModel.TextTerm.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Exact pure selection policy. It cannot authorize, submit, persist or reconcile an action. */
public final class MarriagePolicy {
    private static final BigInteger NATIVE_ID_CEILING = BigInteger.ONE.shiftLeft(31);
    private static final BigInteger MAX_WAIT = BigInteger.valueOf(3);
    private static final BigInteger FERTILE_CUTOFF = BigInteger.valueOf(43);
    private static final Set<Reason> INCOMPLETE = Set.of(MISSING_EXACT_LEGAL_VALUE,
            NATIVE_FINAL_OR_FRAME_UNAVAILABLE, ADULT_TIMING_UNAVAILABLE,
            DUPLICATE_FINAL_LEGAL_CANDIDATE, SEX_LINEALITY_MISMATCH);
    private MarriagePolicy() { }

    public static List<BigInteger> shortlist(Request request) {
        return shortlist(request.legality(), request.shortlistLimit(), request.excludedCandidateIds());
    }

    public static List<BigInteger> shortlist(Legality legality, int limit, Set<BigInteger> excludedCandidateIds) {
        if (limit < 1 || limit > 5) { throw new IllegalArgumentException("child default shortlist limit must be 1..5"); }
        Facts subject = legality.facts();
        BigInteger age = subject.number(ADULT_MEASURE);
        BigInteger threshold = subject.number(ADULT_THRESHOLD);
        BigInteger dynasty = subject.number(DYNASTY_ID);
        List<CompactCandidate> rows = legality.candidates().value();
        if (!"xar.ck3.player-child-marriage-subject.v1".equals(subject.text(SCHEMA))
                || !"available".equals(subject.text(STATUS)) || !yes(subject, CHILD_VERIFIED)
                || !empty(legality.relationship()) || age == null || threshold == null
                || !positive(dynasty) || rows == null) { return List.of(); }
        BigInteger wait = threshold.subtract(age);
        if (wait.signum() <= 0 || wait.compareTo(MAX_WAIT) > 0) { return List.of(); }
        List<Ranked> ranked = new ArrayList<>();
        Set<BigInteger> seen = new HashSet<>();
        Set<BigInteger> duplicates = new HashSet<>();
        for (CompactCandidate candidate : rows) {
            Facts row = candidate.facts();
            BigInteger candidateId = row.number(CANDIDATE_ID);
            if (positive(candidateId) && !seen.add(candidateId)) { duplicates.add(candidateId); }
            BigInteger candidateAge = row.number(CANDIDATE_ADULT_MEASURE);
            BigInteger candidateDynasty = row.number(CANDIDATE_DYNASTY_ID);
            BigInteger accept = row.number(ACCEPT);
            if (!positive(candidateId) || !positive(candidateDynasty) || candidateDynasty.equals(dynasty)
                    || candidateAge == null || candidateAge.compareTo(threshold) < 0
                    || candidateAge.add(wait).compareTo(FERTILE_CUTOFF) >= 0
                    || !eq(row.number(HEIR_ADULT_MEASURE), age)
                    || !eq(row.number(PLAYED_ID), subject.number(PLAYED_ID))
                    || !eq(row.number(SUBJECT_ID), subject.number(SUBJECT_ID))
                    || !yes(row, CAN_SEND) || !yes(row, ANSWER_ALLOWS) || !positive(accept)) { continue; }
            ranked.add(new Ranked(candidateAge.add(wait), accept, candidateId));
        }
        ranked.sort(Comparator.comparing(Ranked::futureAge)
                .thenComparing(Ranked::accept, Comparator.reverseOrder()).thenComparing(Ranked::candidateId));
        return ranked.stream().map(Ranked::candidateId).filter(id -> !duplicates.contains(id)
                && !excludedCandidateIds.contains(id)).limit(limit).toList();
    }

    /** Like the original chooser, always compares its bounded top two, independently of shortlistLimit. */
    public static Decision choose(Request request) {
        Legality legality = request.legality();
        Facts subject = legality.facts();
        if (!request.splitSuccessorVerified()
                || !"xar.ck3.player-child-marriage-subject.v1".equals(subject.text(SCHEMA))
                || !"available".equals(subject.text(STATUS)) || !yes(subject, CHILD_VERIFIED)
                || !positive(subject.number(SUBJECT_ID)) || !positive(subject.number(PLAYED_ID))
                || !positive(subject.number(NATIVE_REVISION)) || !positive(subject.number(QUERY_SEQUENCE))
                || !empty(legality.relationship())) { return rejected(List.of(), SPLIT_CHILD_SUBJECT_NOT_VERIFIED); }
        List<CompactCandidate> rows = legality.candidates().value();
        if (rows == null) { return rejected(List.of(), FINAL_LEGAL_CANDIDATES_UNAVAILABLE); }
        Map<BigInteger, CompactCandidate> legalRows = new HashMap<>();
        Set<BigInteger> duplicates = new HashSet<>();
        for (CompactCandidate row : rows) {
            BigInteger id = row.facts().number(CANDIDATE_ID);
            if (positive(id) && legalRows.put(id, row) != null) { duplicates.add(id); }
        }
        List<BigInteger> shortlist = shortlist(legality, 2, request.excludedCandidateIds());
        List<Evaluation> evaluated = new ArrayList<>();
        Map<BigInteger, CandidateValue> valueById = new HashMap<>();
        Map<BigInteger, Reason> reasons = new HashMap<>();
        for (CandidateValue value : request.values()) {
            BigInteger id = value.facts().number(CANDIDATE_ID);
            if (!positive(id)) { continue; }
            if (valueById.put(id, value) != null) { return rejected(evaluated, DUPLICATE_FULL_VALUE); }
            Reason reason = duplicates.contains(id) ? DUPLICATE_FINAL_LEGAL_CANDIDATE
                    : reason(legality, value, legalRows.get(id));
            PositiveTiming timing = null;
            if (reason == POSITIVE_EARLY_SPLIT_SUCCESSOR_BETROTHAL) {
                Facts row = value.row().value().facts();
                BigInteger wait = row.number(HEIR_ADULT_THRESHOLD).subtract(row.number(HEIR_ADULT_MEASURE));
                timing = new PositiveTiming(wait, row.number(CANDIDATE_ADULT_MEASURE).add(wait), row.number(ACCEPT));
            }
            evaluated.add(new Evaluation(id, reason, timing));
            reasons.put(id, reason);
        }
        if (shortlist.stream().anyMatch(id -> !valueById.containsKey(id))) {
            return rejected(evaluated, INCOMPLETE_TOP_TWO_FULL_VALUE_COMPARISON);
        }
        if (shortlist.stream().anyMatch(id -> INCOMPLETE.contains(reasons.get(id)))) {
            return rejected(evaluated, INCOMPLETE_SAME_FRAME_FULL_VALUE);
        }
        for (BigInteger id : shortlist) {
            if (!request.excludedCandidateIds().contains(id) && reasons.get(id) == POSITIVE_EARLY_SPLIT_SUCCESSOR_BETROTHAL) {
                return new Decision(Status.SELECTED, id, evaluated, EARLY_ZERO_UPFRONT_COST_SPLIT_SUCCESSOR_BETROTHAL);
            }
        }
        return rejected(evaluated, NO_BOUNDED_POSITIVE_PAIR);
    }

    private static Reason reason(Legality legality, CandidateValue value, CompactCandidate candidate) {
        FullValue full = value.row().value();
        if (full == null || candidate == null) { return MISSING_EXACT_LEGAL_VALUE; }
        Facts subject = legality.facts();
        Facts envelope = value.facts();
        Facts row = full.facts();
        Facts legal = candidate.facts();
        BigInteger candidateId = envelope.number(CANDIDATE_ID);
        BigInteger answer = row.number(ANSWER_STATUS);
        if (!"xar.ck3.player-child-marriage-value.v1".equals(envelope.text(SCHEMA))
                || !"available".equals(envelope.text(STATUS)) || !yes(envelope, READ_ONLY)
                || !no(envelope, REQUEST_MATRILINEAL)
                || !eq(envelope.number(SUBJECT_ID), subject.number(SUBJECT_ID))
                || !eq(envelope.number(PLAYED_ID), subject.number(PLAYED_ID))
                || !eq(envelope.number(NATIVE_REVISION), subject.number(NATIVE_REVISION))
                || !eq(envelope.number(LEGALITY_QUERY_SEQUENCE), subject.number(QUERY_SEQUENCE))
                || !eq(row.number(ACTOR_ID), subject.number(PLAYED_ID))
                || !eq(row.number(HEIR_ID), subject.number(SUBJECT_ID))
                || !eq(row.number(CANDIDATE_ID), candidateId)
                || !eq(row.number(RECIPIENT_ID), legal.number(RECIPIENT_MATCHMAKER_ID))
                || !yes(row, FINAL_SAMPLED) || !yes(row, CAN_SEND)
                || !yes(legal, CAN_SEND) || !yes(legal, ANSWER_ALLOWS)
                || !(BigInteger.ZERO.equals(answer) || BigInteger.ONE.equals(answer))
                || !positive(row.number(ACCEPT)) || !eq(row.number(ACCEPT), legal.number(ACCEPT))
                || !eq(row.number(HEIR_ADULT_MEASURE), legal.number(HEIR_ADULT_MEASURE))
                || !eq(row.number(CANDIDATE_ADULT_MEASURE), legal.number(CANDIDATE_ADULT_MEASURE))) {
            return NATIVE_FINAL_OR_FRAME_UNAVAILABLE;
        }
        if (!BigInteger.ZERO.equals(row.number(HEIR_SEX)) || !BigInteger.ONE.equals(row.number(CANDIDATE_SEX))
                || !no(row, EFFECTIVE_MATRILINEAL)) { return SEX_LINEALITY_MISMATCH; }
        if (!no(row, REQUESTED_MATRILINEAL) || !no(row, SELECTED_MATRILINEAL)
                || !no(row, EFFECTIVE_MATRILINEAL) || !"betrothal".equals(row.text(OUTCOME))
                || !no(row, GRAND_WEDDING) || !no(row, HEIR_ADULT)
                || !eq(row.number(HEIR_HOUSE_ID), subject.number(HOUSE_ID))
                || !eq(row.number(HEIR_DYNASTY_ID), subject.number(DYNASTY_ID))
                || !eq(row.number(PLAYED_HOUSE_ID), subject.number(HOUSE_ID))
                || !eq(row.number(PLAYED_DYNASTY_ID), subject.number(DYNASTY_ID))
                || !positive(row.number(CANDIDATE_DYNASTY_ID))
                || eq(row.number(CANDIDATE_DYNASTY_ID), subject.number(DYNASTY_ID))
                || !empty(full.heirRelationship()) || !empty(full.candidateRelationship())) {
            return FAMILY_RELATION_OR_LINEALITY_NOT_VALUED;
        }
        BigInteger heirAge = row.number(HEIR_ADULT_MEASURE);
        BigInteger heirThreshold = row.number(HEIR_ADULT_THRESHOLD);
        BigInteger candidateAge = row.number(CANDIDATE_ADULT_MEASURE);
        BigInteger candidateThreshold = row.number(CANDIDATE_ADULT_THRESHOLD);
        if (heirAge == null || heirThreshold == null || candidateAge == null || candidateThreshold == null
                || !eq(heirAge, subject.number(ADULT_MEASURE)) || !eq(heirThreshold, subject.number(ADULT_THRESHOLD))) {
            return ADULT_TIMING_UNAVAILABLE;
        }
        if (candidateAge.compareTo(candidateThreshold) < 0) { return CANDIDATE_NOT_ADULT; }
        if (!yes(row, CANDIDATE_ADULT)) { return ADULT_TIMING_UNAVAILABLE; }
        BigInteger wait = heirThreshold.subtract(heirAge);
        if (wait.signum() <= 0 || wait.compareTo(MAX_WAIT) > 0 || candidateAge.add(wait).compareTo(FERTILE_CUTOFF) >= 0) {
            return BETROTHAL_WAIT_OR_FUTURE_AGE_TOO_HIGH;
        }
        if (!fertile(full.heirFertility()) || !fertile(full.candidateFertility())) { return NATIVE_FERTILITY_GATE_UNAVAILABLE; }
        Costs costs = full.costs().value();
        if (costs == null || !"actor".equals(costs.facts().text(PAYER)) || !"on_send".equals(costs.facts().text(COST_TIMING))) {
            return UPFRONT_COST_UNPRICED;
        }
        for (CostTerm term : CostTerm.values()) {
            if (!BigInteger.ZERO.equals(costs.amounts().getOrDefault(term, Field.missing()).value())) { return UPFRONT_COST_UNPRICED; }
        }
        List<Facts> alliances = full.alliances().value();
        if (alliances == null || alliances.isEmpty() || alliances.stream().anyMatch(pair -> !no(pair, WOULD_ATTEMPT_ALLIANCE))) {
            return ALLIANCE_OBLIGATION_UNPRICED;
        }
        return POSITIVE_EARLY_SPLIT_SUCCESSOR_BETROTHAL;
    }

    private static boolean fertile(Field<Facts> field) {
        Facts value = field.value();
        return value != null && "native_marriage_fertility_input".equals(value.text(SOURCE))
                && yes(value, EXTENSION_PRESENT) && yes(value, GATE_EVALUATED) && yes(value, GATE_ALLOWS)
                && positive(value.number(EFFECTIVE_FERTILITY));
    }
    private static boolean empty(Relationship relationship) {
        return relationship.betrothed().value() == null && relationship.primarySpouse().value() == null
                && relationship.spouses().value() != null && relationship.spouses().value().isEmpty();
    }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0 && value.compareTo(NATIVE_ID_CEILING) < 0; }
    private static boolean yes(Facts facts, BooleanTerm key) { return Boolean.TRUE.equals(facts.flag(key)); }
    private static boolean no(Facts facts, BooleanTerm key) { return Boolean.FALSE.equals(facts.flag(key)); }
    private static boolean eq(Object first, Object second) { return Objects.equals(first, second); }
    private static Decision rejected(List<Evaluation> evaluated, Reason reason) { return new Decision(Status.NO_POSITIVE_VALUE, null, evaluated, reason); }
    private record Ranked(BigInteger futureAge, BigInteger accept, BigInteger candidateId) { }
}
