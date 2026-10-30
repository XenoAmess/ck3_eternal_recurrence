package org.xar.ck3.control.wave3.governance.heirranking;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.Adulthood;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.AlliancePair;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.LegalRow;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.Lineage;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.Outcome;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.ProjectedRow;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.Relationship;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.Roles;

/** Shared producer for ranking and the same rejection reasons used by diagnostics. */
public final class HeirCandidateRankingConsumerPort {
    private HeirCandidateRankingConsumerPort() { }

    /** Immutable validated input shared by the byte codec and the resident typed port. */
    public record Request(boolean available, List<LegalRow> legalRows, List<ProjectedRow> rows,
            Set<BigInteger> rejected, byte[] sourceJson) {
        public Request { legalRows = List.copyOf(legalRows); rows = List.copyOf(rows);
            rejected = Set.copyOf(rejected); sourceJson = sourceJson.clone(); }
        @Override public byte[] sourceJson() { return sourceJson.clone(); }
    }

    public record Evaluation(byte[] choices, byte[] rejectionReasons) {
        public Evaluation {
            choices = choices.clone();
            rejectionReasons = rejectionReasons.clone();
        }
        @Override public byte[] choices() { return choices.clone(); }
        @Override public byte[] rejectionReasons() { return rejectionReasons.clone(); }
    }

    public static byte[] rank(byte[] input) { return evaluate(input).choices(); }
    public static byte[] diagnose(byte[] input) { return evaluate(input).rejectionReasons(); }

    public static Evaluation evaluate(byte[] input) { return evaluate(decode(input)); }

    public static Request decode(byte[] input) {
        ObjectNode request = StrictJson.object(parseInput(input),
                Set.of("legality", "projection", "rejected_candidate_ids"));
        ObjectNode legality = object(request.get("legality"));
        ObjectNode projection = object(request.get("projection"));
        Set<BigInteger> rejected = new HashSet<>();
        for (JsonNode node : array(request.get("rejected_candidate_ids"))) {
            BigInteger id = integer(node);
            StrictJson.require(id.signum() > 0 && rejected.add(id), "distinct positive rejected IDs required");
        }
        if (!text(legality.get("status")).equals("available") || !text(projection.get("status")).equals("available")) {
            return new Request(false, List.of(), List.of(), rejected, input);
        }
        BigInteger nativeRevision = nonnegative(legality.get("native_revision"));
        BigInteger projectionRevision = nonnegative(projection.get("native_revision"));
        BigInteger querySequence = nonnegative(legality.get("query_sequence"));
        BigInteger projectionSequence = nonnegative(projection.get("legality_query_sequence"));
        if (!nativeRevision.equals(projectionRevision) || !querySequence.equals(projectionSequence)) { return new Request(false, List.of(), List.of(), rejected, input); }
        ArrayNode projectedJson = array(projection.get("rows"));
        if (projectedJson.size() != 5) { return new Request(false, List.of(), List.of(), rejected, input); }
        List<LegalRow> legalRows = new ArrayList<>();
        for (JsonNode node : array(legality.get("native_legal_candidates"))) {
            LegalRow parsed = projectLegalRow(node);
            legalRows.add(parsed);
        }
        List<ProjectedRow> rows = new ArrayList<>();
        for (int ordinal = 0; ordinal < projectedJson.size(); ordinal++) {
            rows.add(projectProjectedRow(projectedJson.get(ordinal), ordinal));
        }
        return new Request(true, legalRows, rows, rejected, input);
    }

    public static Evaluation evaluate(Request decoded) {
        if (!decoded.available()) { return empty(); }
        ObjectNode request = object(parseInput(decoded.sourceJson()));
        ArrayNode projectedJson = array(object(request.get("projection")).get("rows"));
        List<LegalRow> legalRows = decoded.legalRows();
        List<ProjectedRow> rows = decoded.rows();
        Set<BigInteger> rejected = decoded.rejected();
        Map<BigInteger, LegalRow> byId = new HashMap<>();
        for (LegalRow row : legalRows) { row.roles().candidate().ifPresent(id -> byId.put(id, row)); }
        ArrayNode reasons = StrictJson.object().putArray("reasons");
        for (ProjectedRow row : rows) {
            ObjectNode reason = reasons.addObject();
            if (row.roles().candidate().isPresent()) { reason.put("candidate_character_id", row.roles().candidate().orElseThrow()); }
            else { reason.putNull("candidate_character_id"); }
            ArrayNode values = reason.putArray("rejection_reasons");
            HeirCandidateRanking.rejectionReasons(row.roles().candidate().map(byId::get), row, rejected)
                    .forEach(reasonCode -> values.add(reasonCode.wire()));
        }
        ArrayNode choices = StrictJson.object().putArray("choices");
        for (var choice : HeirCandidateRanking.rank(legalRows, rows, rejected)) {
            ObjectNode value = choices.addObject();
            value.put("candidate_character_id", choice.candidate());
            value.put("value", choice.value().wire());
            value.put("predicted_outcome_if_accepted", choice.outcome() == Outcome.MARRIAGE ? "marriage" : "betrothal");
            value.put("realm_alliance_attempt_if_accepted", choice.allianceAttempt());
            value.put("recipient_ai_accept_raw", choice.acceptance());
            JsonNode costs = projectedJson.get(choice.selectedRowOrdinal()).get("generic_costs");
            if (costs == null) { value.putNull("immediate_generic_costs"); }
            else { value.set("immediate_generic_costs", costs.deepCopy()); }
            ArrayNode unpriced = value.putArray("unpriced");
            unpriced.add("child_dynasty_result").add("alliance_result").add("alliance_war_obligation").add("betrothal_break_cost");
        }
        return new Evaluation(encodeOpaqueJson(choices), encodeOpaqueJson(reasons));
    }

    private static JsonNode parseInput(byte[] input) {
        try { return FullJsonTree.parse(input, FullJsonTree.MAXIMUM_BYTES); }
        catch (ContractViolationException failure) { throw failure; }
        catch (IllegalArgumentException failure) {
            throw new ContractViolationException("invalid heir ranking JSON", failure);
        }
    }

    /** Shared strict compact-row projection; it conveys no native provenance or action authority. */
    public static LegalRow projectLegalRow(JsonNode input) {
        ObjectNode row = object(input);
        return new LegalRow(roles(row, true), lineage(row), adulthood(row),
                bool(row.get("realm_backed_actor_recipient")), bool(row.get("complete_can_send")),
                bool(row.get("recipient_answer_allows_send")), number(row.get("recipient_answer_status_raw")),
                number(row.get("recipient_ai_accept_raw")));
    }

    /** Shared rich-row decoder; decoded observations are not native provenance. */
    public static ProjectedRow projectProjectedRow(JsonNode input, int ordinal) {
        ObjectNode row = object(input);
        String outcome = optionalText(row.get("predicted_outcome_if_accepted")).orElse("");
        return new ProjectedRow(ordinal, roles(row, false),
                optionalText(row.get("status")).filter("available"::equals).isPresent(),
                outcome.equals("marriage") ? Outcome.MARRIAGE
                        : outcome.equals("betrothal") ? Outcome.BETROTHAL : Outcome.UNAVAILABLE,
                lineage(row), adulthood(row), new Relationship(number(row.get("heir_betrothed_character_id")),
                        number(row.get("heir_primary_spouse_character_id")), numbers(row.get("heir_spouse_character_ids"))),
                number(row.get("heir_sex_selector_raw")), number(row.get("candidate_sex_selector_raw")),
                bool(row.get("effective_matrilineal_if_accepted")), pairs(row.get("possible_alliance_pairs")));
    }

    private static Roles roles(ObjectNode row, boolean legal) {
        return new Roles(positiveIdentity(row.get("candidate_character_id")),
                positiveIdentity(row.get(legal ? "played_character_id" : "actor_character_id")),
                positiveIdentity(row.get(legal ? "subject_character_id" : "heir_character_id")),
                positiveIdentity(row.get(legal ? "recipient_matchmaker_character_id" : "recipient_character_id")));
    }
    private static Lineage lineage(ObjectNode row) {
        return new Lineage(number(row.get("candidate_dynasty_id")), number(row.get("played_dynasty_id")),
                number(row.get("heir_dynasty_id")), number(row.get("played_house_id")), number(row.get("heir_house_id")));
    }
    private static Adulthood adulthood(ObjectNode row) {
        return new Adulthood(number(row.get("heir_adult_measure_raw")), number(row.get("candidate_adult_measure_raw")),
                number(row.get("heir_adult_threshold_raw")), number(row.get("candidate_adult_threshold_raw")),
                bool(row.get("heir_is_adult")), bool(row.get("candidate_is_adult")), bool(row.get("grand_wedding_option_selected")));
    }
    private static Optional<List<AlliancePair>> pairs(JsonNode node) {
        if (node == null || node.isNull()) { return Optional.empty(); }
        List<AlliancePair> result = new ArrayList<>();
        for (JsonNode raw : array(node)) {
            ObjectNode pair = object(raw);
            result.add(new AlliancePair(number(pair.get("first_character_id")), number(pair.get("second_character_id")),
                    bool(pair.get("already_allied")), bool(pair.get("both_have_realm_data")), bool(pair.get("would_attempt_if_accepted"))));
        }
        return Optional.of(List.copyOf(result));
    }
    private static Optional<List<BigInteger>> numbers(JsonNode node) {
        if (node == null || node.isNull()) { return Optional.empty(); }
        List<BigInteger> result = new ArrayList<>();
        for (JsonNode value : array(node)) { result.add(integer(value)); }
        return Optional.of(List.copyOf(result));
    }
    private static Optional<BigInteger> number(JsonNode node) {
        return node == null || node.isNull() ? Optional.empty() : Optional.of(integer(node));
    }
    private static Optional<BigInteger> positiveIdentity(JsonNode node) {
        BigInteger id = integer(node);
        StrictJson.require(id.signum() > 0, "required positive character identity");
        return Optional.of(id);
    }
    private static Optional<Boolean> bool(JsonNode node) {
        if (node == null || node.isNull()) { return Optional.empty(); }
        StrictJson.require(node.isBoolean(), "actual boolean token required");
        return Optional.of(node.booleanValue());
    }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "exact integer token required");
        return node.bigIntegerValue();
    }
    private static BigInteger nonnegative(JsonNode node) {
        BigInteger value = integer(node);
        StrictJson.require(value.signum() >= 0, "nonnegative source revision/sequence required");
        return value;
    }
    private static Optional<String> optionalText(JsonNode node) {
        if (node == null || node.isNull()) { return Optional.empty(); }
        StrictJson.require(node.isTextual(), "actual text token required");
        if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); }
        return Optional.of(node.textValue());
    }
    private static String text(JsonNode node) { return StrictJson.text(node); }
    private static ObjectNode object(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "object required");
        return (ObjectNode) node;
    }
    private static ArrayNode array(JsonNode node) {
        StrictJson.require(node instanceof ArrayNode, "array required");
        return (ArrayNode) node;
    }
    private static Evaluation empty() {
        byte[] empty = new byte[] {'[', ']'};
        return new Evaluation(empty, empty);
    }
    /** Shared heir JSON encoding; consumed numeric fields are validated separately before this boundary. */
    public static byte[] encodeOpaqueJson(JsonNode value) {
        StringBuilder output = new StringBuilder();
        appendOpaqueJson(value, output);
        byte[] raw = output.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        StrictJson.require(raw.length <= StrictJson.INPUT_MAX_BYTES, "canonical JSON exceeds shared receipt byte budget");
        return raw;
    }

    private static void appendOpaqueJson(JsonNode value, StringBuilder output) {
        StrictJson.require(value != null, "missing JSON node cannot be serialized as null");
        if (value.isObject()) {
            output.append('{');
            java.util.TreeSet<String> names = new java.util.TreeSet<>();
            value.fieldNames().forEachRemaining(names::add);
            boolean first = true;
            for (String name : names) {
                if (!first) { output.append(','); } first = false;
                output.append(new String(StrictJson.canonical(
                        com.fasterxml.jackson.databind.node.TextNode.valueOf(name)), java.nio.charset.StandardCharsets.UTF_8));
                output.append(':'); appendOpaqueJson(value.get(name), output);
            }
            output.append('}');
        } else if (value.isArray()) {
            output.append('['); boolean first = true;
            for (JsonNode item : value) {
                if (!first) { output.append(','); } first = false;
                appendOpaqueJson(item, output);
            }
            output.append(']');
        } else if (value.isFloatingPointNumber()) {
            // JsonNode's numeric kind survives decimal scale normalization. Keep an actual float token.
            StrictJson.require(Double.isFinite(value.doubleValue()), "finite opaque JSON number required");
            String token = value.decimalValue().toString();
            if (token.indexOf('.') < 0 && token.indexOf('e') < 0 && token.indexOf('E') < 0) { token += ".0"; }
            output.append(token);
        } else {
            output.append(new String(StrictJson.canonical(value), java.nio.charset.StandardCharsets.UTF_8));
        }
    }


}
