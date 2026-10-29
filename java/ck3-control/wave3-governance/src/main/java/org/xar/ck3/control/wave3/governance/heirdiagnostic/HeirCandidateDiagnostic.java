package org.xar.ck3.control.wave3.governance.heirdiagnostic;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.LegalRow;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.ProjectedRow;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.RejectionReason;

/** Read-only five-row observation, with the ranking module's single rejection policy. */
public final class HeirCandidateDiagnostic {
    public static final String SCHEMA = "xar.ck3.first-heir-marriage-private-diagnostic.v1";
    private HeirCandidateDiagnostic() { }

    public record Header(Optional<String> projectionSchema, Optional<String> exactBuild,
            Optional<String> episode, Optional<BigInteger> date, BigInteger nativeRevision,
            BigInteger legalityQuerySequence, BigInteger observedHeir, int legalCandidateCount,
            Optional<BigInteger> selectedCandidate) {
        public Header {
            Objects.requireNonNull(projectionSchema); Objects.requireNonNull(exactBuild);
            Objects.requireNonNull(episode); Objects.requireNonNull(date);
            Objects.requireNonNull(nativeRevision); Objects.requireNonNull(legalityQuerySequence);
            Objects.requireNonNull(observedHeir); Objects.requireNonNull(selectedCandidate);
            if (nativeRevision.signum() < 0 || legalityQuerySequence.signum() < 0
                    || observedHeir.signum() <= 0 || legalCandidateCount < 0
                    || selectedCandidate.filter(id -> id.signum() <= 0).isPresent()) {
                throw new IllegalArgumentException("exact diagnostic identities and source counters required");
            }
        }
    }

    public record Row(int ordinal, ProjectedRow projected, Optional<LegalRow> legal,
            Optional<Integer> heirSpouseCount, List<RejectionReason> rejectionReasons) {
        public Row {
            if (ordinal < 0 || ordinal >= 5) { throw new IllegalArgumentException("five-row ordinal required"); }
            Objects.requireNonNull(projected); Objects.requireNonNull(legal); Objects.requireNonNull(heirSpouseCount);
            if (projected.ordinal() != ordinal || !heirSpouseCount.equals(projected.relationship().spouses().map(List::size))) {
                throw new IllegalArgumentException("diagnostic ordinal or spouse count differs from assessed row");
            }
            rejectionReasons = List.copyOf(rejectionReasons);
        }
    }

    public record Observation(Header header, List<Row> rows) {
        public Observation {
            Objects.requireNonNull(header); rows = List.copyOf(rows);
            if (rows.size() != 5) { throw new IllegalArgumentException("exactly five assessed rows required"); }
        }
        /** A selected projection only; callers retain original source and submission guards. */
        public Optional<Row> selectedProjection() {
            return header.selectedCandidate().flatMap(id -> rows.stream()
                    .filter(row -> row.projected().roles().candidate().filter(id::equals).isPresent()).findFirst());
        }
    }

    public static Observation observe(Header header, List<LegalRow> legalRows,
            List<ProjectedRow> projectedRows, Set<BigInteger> rejectedCandidateIds) {
        Objects.requireNonNull(header); legalRows = List.copyOf(legalRows); projectedRows = List.copyOf(projectedRows);
        rejectedCandidateIds = Set.copyOf(rejectedCandidateIds);
        if (header.legalCandidateCount() != legalRows.size() || projectedRows.size() != 5) {
            throw new IllegalArgumentException("bounded diagnostic source counts changed");
        }
        Map<BigInteger, LegalRow> byId = new HashMap<>();
        for (LegalRow row : legalRows) { row.roles().candidate().ifPresent(id -> byId.put(id, row)); }
        List<Row> result = new ArrayList<>();
        for (int ordinal = 0; ordinal < projectedRows.size(); ordinal++) {
            ProjectedRow row = projectedRows.get(ordinal);
            Optional<LegalRow> legal = row.roles().candidate().map(byId::get);
            result.add(new Row(ordinal, row, legal, row.relationship().spouses().map(List::size),
                    HeirCandidateRanking.rejectionReasons(legal, row, rejectedCandidateIds)));
        }
        return new Observation(header, result);
    }
}
