package org.xar.ck3.control.wave3.governance.heirintake;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.LegalRow;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRankingConsumerPort;

/** Shared compact-to-rich request projection; it owns neither native queries nor a planner. */
public final class HeirCandidateIntakeConsumerPort {
    private HeirCandidateIntakeConsumerPort() { }

    /** The original opaque compact rows are retained in immutable source bytes. */
    public record Request(List<LegalRow> legalRows, Set<BigInteger> rejected, byte[] sourceJson) {
        public Request { legalRows = List.copyOf(legalRows); rejected = Set.copyOf(rejected);
            sourceJson = sourceJson.clone(); }
        @Override public byte[] sourceJson() { return sourceJson.clone(); }
    }

    public record Evaluation(byte[] result, Optional<List<BigInteger>> nextRichCandidateIds) {
        public Evaluation {
            result = result.clone();
            nextRichCandidateIds = nextRichCandidateIds.map(List::copyOf);
        }
        @Override public byte[] result() { return result.clone(); }
    }

    public static byte[] consume(byte[] input) { return evaluate(input).result(); }

    public static Evaluation evaluate(byte[] input) { return evaluate(decode(input)); }

    public static Request decode(byte[] input) {
        ObjectNode request = StrictJson.object(StrictJson.parse(input), Set.of("legal_rows", "rejected_candidate_ids"));
        HeirCandidateRankingConsumerPort.encodeOpaqueJson(request);
        JsonNode legalRows = request.get("legal_rows");
        JsonNode rejectedIds = request.get("rejected_candidate_ids");
        StrictJson.require(legalRows instanceof ArrayNode && rejectedIds instanceof ArrayNode, "explicit candidate arrays required");
        Set<BigInteger> refused = new HashSet<>();
        for (JsonNode raw : rejectedIds) {
            StrictJson.require(raw.isIntegralNumber() && raw.bigIntegerValue().signum() > 0
                    && refused.add(raw.bigIntegerValue()), "distinct positive integer refusal IDs required");
        }
        List<LegalRow> rows = new ArrayList<>();
        for (JsonNode raw : legalRows) { rows.add(HeirCandidateRankingConsumerPort.projectLegalRow(raw)); }
        return new Request(rows, refused, input);
    }

    public static Evaluation evaluate(Request decoded) {
        JsonNode legalRows = StrictJson.parse(decoded.sourceJson()).get("legal_rows");
        var intake = HeirCandidateIntake.pick(decoded.legalRows(), decoded.rejected());
        ObjectNode result = StrictJson.object();
        ArrayNode picked = result.putArray("picked");
        for (var candidate : intake.picked()) { picked.add(legalRows.get(candidate.sourceOrdinal()).deepCopy()); }
        var statistics = intake.statistics();
        ObjectNode ranking = result.putObject("ranking");
        ranking.put("rule", "external_dynasty_realm_backed_age_gap_v1");
        ranking.put("age_gap_max_raw", HeirCandidateRanking.MAX_BETROTHAL_AGE_GAP_RAW);
        ranking.put("prefilter_eligible_count", statistics.eligibleCount());
        ranking.put("value_input_unavailable_count", statistics.unavailableCount());
        ranking.put("candidate_dynasty_absent_count", statistics.absentDynastyCount());
        ranking.put("conclusion", statistics.conclusion().wire());
        ranking.put("projected_count", statistics.projectedCount());
        return new Evaluation(HeirCandidateRankingConsumerPort.encodeOpaqueJson(result), intake.nextRichCandidateIds());
    }
}
