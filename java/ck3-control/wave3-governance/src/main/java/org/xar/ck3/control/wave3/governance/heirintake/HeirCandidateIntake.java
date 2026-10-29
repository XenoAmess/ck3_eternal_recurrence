package org.xar.ck3.control.wave3.governance.heirintake;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.LegalRow;

/** Pure intake of an already returned native-final legal pool; no enumeration or reads. */
public final class HeirCandidateIntake {
    private static final int PROJECTED_CANDIDATE_COUNT = 5;
    private static final BigInteger ABSENT_DYNASTY = BigInteger.valueOf(-1);

    private HeirCandidateIntake() { }

    public enum Conclusion {
        NO_AGE_MATCHED_EXTERNAL_REALM_CANDIDATE("no_age_matched_external_realm_candidate"),
        UNOBSERVED_VALUE_INPUTS_REMAIN("unobserved_value_inputs_remain"),
        BOUNDED_FIVE_ROW_PROJECTION("bounded_five_row_projection");
        private final String wire;
        Conclusion(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Candidate(int sourceOrdinal, LegalRow row) {
        public Candidate {
            if (sourceOrdinal < 0) { throw new IllegalArgumentException("negative source ordinal"); }
            Objects.requireNonNull(row, "original compact legal row");
            if (!positive(row.roles().candidate()) || row.acceptance().isEmpty()) {
                throw new IllegalArgumentException("native legal pool needs candidate ID and exact acceptance");
            }
        }
    }

    public record Statistics(int eligibleCount, int unavailableCount, int absentDynastyCount,
                              int projectedCount, Conclusion conclusion) {
        public Statistics {
            if (eligibleCount < 0 || unavailableCount < 0 || absentDynastyCount < 0
                    || projectedCount < 0 || projectedCount > PROJECTED_CANDIDATE_COUNT) {
                throw new IllegalArgumentException("invalid compact candidate counts");
            }
            Objects.requireNonNull(conclusion, "conclusion");
        }
    }

    public record Intake(List<Candidate> picked, Statistics statistics) {
        public Intake {
            picked = List.copyOf(picked);
            Objects.requireNonNull(statistics, "statistics");
            if (picked.size() != statistics.projectedCount()) {
                throw new IllegalArgumentException("projection count differs from picked rows");
            }
        }
        /** Matches the real consumer's length gate; this is a proposed read, never read qualification. */
        public Optional<List<BigInteger>> nextRichCandidateIds() {
            return picked.size() < PROJECTED_CANDIDATE_COUNT ? Optional.empty()
                    : Optional.of(picked.stream().map(candidate -> candidate.row().roles().candidate().orElseThrow()).toList());
        }
    }

    public static Intake pick(List<LegalRow> legalRows, Set<BigInteger> refusedCandidates) {
        List<LegalRow> rows = List.copyOf(legalRows);
        Set<BigInteger> refused = Set.copyOf(refusedCandidates);
        List<Candidate> fresh = new ArrayList<>();
        List<Candidate> rejected = new ArrayList<>();
        for (int ordinal = 0; ordinal < rows.size(); ordinal++) {
            Candidate candidate = new Candidate(ordinal, rows.get(ordinal));
            (refused.contains(candidate.row().roles().candidate().orElseThrow()) ? rejected : fresh).add(candidate);
        }
        int unknown = 0;
        int absent = 0;
        List<Candidate> eligible = new ArrayList<>();
        for (Candidate candidate : fresh) {
            LegalRow row = candidate.row();
            Optional<BigInteger> dynasty = row.lineage().candidateDynasty();
            if (!positive(row.lineage().playedDynasty()) || !positive(row.lineage().heirDynasty())
                    || dynasty.isEmpty() || dynasty.orElseThrow().equals(BigInteger.ZERO)
                    || dynasty.orElseThrow().compareTo(ABSENT_DYNASTY) < 0
                    || row.adulthood().heirMeasure().isEmpty() || row.adulthood().candidateMeasure().isEmpty()
                    || row.realmBacked().isEmpty()) {
                unknown++;
                continue;
            }
            if (dynasty.orElseThrow().equals(ABSENT_DYNASTY)) {
                absent++;
                continue;
            }
            if (!row.lineage().heirDynasty().equals(row.lineage().playedDynasty())
                    || dynasty.equals(row.lineage().playedDynasty()) || !row.realmBacked().orElseThrow()
                    || gap(candidate).compareTo(HeirCandidateRanking.MAX_BETROTHAL_AGE_GAP_RAW) > 0
                    || row.acceptance().orElseThrow().signum() <= 0) {
                continue;
            }
            eligible.add(candidate);
        }
        Comparator<Candidate> fallbackOrder = Comparator.comparing(
                (Candidate candidate) -> candidate.row().acceptance().orElseThrow(), Comparator.reverseOrder())
                .thenComparing(candidate -> candidate.row().roles().candidate().orElseThrow());
        eligible.sort(Comparator.comparing(HeirCandidateIntake::gap).thenComparing(fallbackOrder));
        List<Candidate> picked = new ArrayList<>(eligible.subList(0, Math.min(PROJECTED_CANDIDATE_COUNT, eligible.size())));
        Set<BigInteger> pickedIds = new HashSet<>();
        picked.forEach(candidate -> pickedIds.add(candidate.row().roles().candidate().orElseThrow()));
        List<Candidate> fallback = fresh.stream().filter(candidate ->
                !pickedIds.contains(candidate.row().roles().candidate().orElseThrow())).sorted(fallbackOrder).toList();
        appendRemaining(picked, fallback);
        if (picked.size() < PROJECTED_CANDIDATE_COUNT) {
            rejected.sort(fallbackOrder);
            appendRemaining(picked, rejected);
        }
        Conclusion conclusion = eligible.isEmpty()
                ? unknown == 0 ? Conclusion.NO_AGE_MATCHED_EXTERNAL_REALM_CANDIDATE : Conclusion.UNOBSERVED_VALUE_INPUTS_REMAIN
                : Conclusion.BOUNDED_FIVE_ROW_PROJECTION;
        return new Intake(picked, new Statistics(eligible.size(), unknown, absent, picked.size(), conclusion));
    }

    private static void appendRemaining(List<Candidate> picked, List<Candidate> remainder) {
        int remaining = PROJECTED_CANDIDATE_COUNT - picked.size();
        picked.addAll(remainder.subList(0, Math.min(remaining, remainder.size())));
    }
    private static BigInteger gap(Candidate candidate) {
        return candidate.row().adulthood().heirMeasure().orElseThrow().subtract(
                candidate.row().adulthood().candidateMeasure().orElseThrow()).abs();
    }
    private static boolean positive(Optional<BigInteger> value) { return value.isPresent() && value.orElseThrow().signum() > 0; }
}
