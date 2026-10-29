package org.xar.ck3.control.wave3.governance.heirdiagnostic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
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
import org.xar.ck3.control.wave3.governance.heirdiagnostic.HeirCandidateDiagnostic.Header;
import org.xar.ck3.control.wave3.governance.heirdiagnostic.HeirCandidateDiagnostic.Observation;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.LegalRow;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRanking.ProjectedRow;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRankingConsumerPort;

/** Strict JSON adapter for the existing private diagnostic, without submit or native I/O. */
public final class HeirCandidateDiagnosticConsumerPort {
    private HeirCandidateDiagnosticConsumerPort() { }

    private enum Kind { TEXT, INTEGER, BOOLEAN, OBJECT, INTEGER_LIST }
    private enum Field {
        STATUS("status", Kind.TEXT), ACTOR("actor_character_id", Kind.INTEGER), HEIR("heir_character_id", Kind.INTEGER),
        RECIPIENT("recipient_character_id", Kind.INTEGER), CANDIDATE("candidate_character_id", Kind.INTEGER),
        OUTCOME("predicted_outcome_if_accepted", Kind.TEXT), HEIR_ADULT("heir_is_adult", Kind.BOOLEAN),
        CANDIDATE_ADULT("candidate_is_adult", Kind.BOOLEAN), HEIR_AGE("heir_adult_measure_raw", Kind.INTEGER),
        CANDIDATE_AGE("candidate_adult_measure_raw", Kind.INTEGER), HEIR_THRESHOLD("heir_adult_threshold_raw", Kind.INTEGER),
        CANDIDATE_THRESHOLD("candidate_adult_threshold_raw", Kind.INTEGER), GRAND_WEDDING("grand_wedding_option_selected", Kind.BOOLEAN),
        HEIR_FERTILITY("heir_native_fertility", Kind.OBJECT), CANDIDATE_FERTILITY("candidate_native_fertility", Kind.OBJECT),
        FERTILITY_FLOOR("native_candidate_fertility_floor_raw", Kind.INTEGER),
        FERTILITY_COMPARISON("candidate_native_fertility_floor_comparison_v1", Kind.OBJECT),
        HEIR_AGE_OVERRIDE("heir_native_scorer_age_override_raw", Kind.INTEGER),
        CANDIDATE_AGE_OVERRIDE("candidate_native_scorer_age_override_raw", Kind.INTEGER),
        AGE_UPPER("native_candidate_scorer_age_upper_raw", Kind.INTEGER),
        HEIR_EFFECTIVE_AGE("heir_native_scorer_effective_age_v1", Kind.OBJECT),
        CANDIDATE_EFFECTIVE_AGE("candidate_native_scorer_effective_age_v1", Kind.OBJECT),
        AGE_BRANCH("candidate_native_scorer_age_branch_v1", Kind.OBJECT), COSTS("generic_costs", Kind.OBJECT),
        HEIR_BETROTHED("heir_betrothed_character_id", Kind.INTEGER), HEIR_SPOUSE("heir_primary_spouse_character_id", Kind.INTEGER),
        PLAYED_HOUSE("played_house_id", Kind.INTEGER), PLAYED_DYNASTY("played_dynasty_id", Kind.INTEGER),
        HEIR_HOUSE("heir_house_id", Kind.INTEGER), HEIR_DYNASTY("heir_dynasty_id", Kind.INTEGER),
        CANDIDATE_HOUSE("candidate_house_id", Kind.INTEGER), CANDIDATE_DYNASTY("candidate_dynasty_id", Kind.INTEGER),
        HEIR_SELECTOR("heir_sex_selector_raw", Kind.INTEGER), CANDIDATE_SELECTOR("candidate_sex_selector_raw", Kind.INTEGER),
        MATRILINEAL("matrilineal_option_selected", Kind.BOOLEAN), EFFECTIVE_MATRILINEAL("effective_matrilineal_if_accepted", Kind.BOOLEAN),
        CANDIDATE_BETROTHED("candidate_betrothed_character_id", Kind.INTEGER),
        CANDIDATE_SPOUSE("candidate_primary_spouse_character_id", Kind.INTEGER),
        CANDIDATE_SPOUSES("candidate_spouse_character_ids", Kind.INTEGER_LIST);

        private final String wire;
        private final Kind kind;
        Field(String wire, Kind kind) { this.wire = wire; this.kind = kind; }
    }
    private static final Set<String> PAIR_FIELDS = Set.of("first_character_id", "second_character_id",
            "already_allied", "both_have_realm_data", "would_attempt_if_accepted");
    private static final Set<String> NATIVE_BOOLEAN_FIELDS = Set.of("extension_present", "native_gate_allows",
            "native_gate_evaluated", "ready", "passes", "selector_zero_bypass");
    private static final Set<String> NATIVE_INTEGER_FIELDS = Set.of("effective_raw", "raw_scale", "gold_raw",
            "prestige_raw", "piety_raw", "renown_raw", "influence_raw", "herd_raw", "treasury_raw",
            "treasury_or_gold_raw", "merit_raw", "barter_goods_raw", "adjusted_candidate_age_raw", "subject_adult_deficit_raw");

    /** Validated typed facts plus immutable original JSON for opaque diagnostic copies. */
    public record Request(Header header, List<LegalRow> legalRows, List<ProjectedRow> rows,
            Set<BigInteger> rejected, byte[] sourceJson) {
        public Request { java.util.Objects.requireNonNull(header); legalRows = List.copyOf(legalRows);
            rows = List.copyOf(rows); rejected = Set.copyOf(rejected); sourceJson = sourceJson.clone(); }
        @Override public byte[] sourceJson() { return sourceJson.clone(); }
    }

    public record Evaluation(byte[] diagnostic, Observation observation) {
        public Evaluation { diagnostic = diagnostic.clone(); }
        @Override public byte[] diagnostic() { return diagnostic.clone(); }
    }

    public static byte[] project(byte[] input) { return evaluate(input).diagnostic(); }

    public static Evaluation evaluate(byte[] input) { return evaluate(decode(input)); }

    public static Request decode(byte[] input) {
        ObjectNode request = StrictJson.object(StrictJson.parse(input), Set.of("legality", "projection", "snapshot",
                "choice", "ranking", "rejected_candidate_ids"));
        HeirCandidateRankingConsumerPort.encodeOpaqueJson(request);
        ObjectNode legality = object(request.get("legality"));
        ObjectNode projection = object(request.get("projection"));
        ObjectNode snapshot = object(request.get("snapshot"));
        ObjectNode ranking = object(request.get("ranking"));
        JsonNode choice = request.get("choice");
        StrictJson.require(choice != null && (choice.isNull() || choice.isObject()), "choice object or explicit null required");
        Optional<BigInteger> selected = choice.isNull() || choice.isEmpty()
                ? Optional.empty() : Optional.of(positive(choice.get("candidate_character_id")));
        ArrayNode rawLegal = array(legality.get("native_legal_candidates"));
        ArrayNode rawRows = array(projection.get("rows"));
        StrictJson.require(rawRows.size() == 5, "exactly five assessed diagnostic rows required");
        List<LegalRow> legalRows = new ArrayList<>();
        for (JsonNode raw : rawLegal) {
            LegalRow row = HeirCandidateRankingConsumerPort.projectLegalRow(raw);
            legalRows.add(row);
        }
        List<ProjectedRow> rows = new ArrayList<>();
        for (int ordinal = 0; ordinal < rawRows.size(); ordinal++) {
            rows.add(HeirCandidateRankingConsumerPort.projectProjectedRow(rawRows.get(ordinal), ordinal));
        }
        Set<BigInteger> rejected = new HashSet<>();
        for (JsonNode node : array(request.get("rejected_candidate_ids"))) {
            StrictJson.require(rejected.add(positive(node)), "distinct refused candidate identities required");
        }
        Header header = new Header(text(projection.get("schema")), text(legality.get("exact_ck3_build")),
                text(snapshot.get("episode_run_id")), number(snapshot.get("date_raw")),
                nonnegative(legality.get("native_revision")), nonnegative(legality.get("query_sequence")),
                positive(legality.get("observed_first_heir_character_id")), rawLegal.size(), selected);
        // These are consumed input fields, validated before the policy/encoder boundary.
        for (JsonNode raw : rawRows) {
            ObjectNode row = object(raw);
            for (Field field : Field.values()) { validate(row.get(field.wire), field.kind); }
            JsonNode pairs = row.get("possible_alliance_pairs");
            if (pairs != null && !pairs.isNull()) {
                for (JsonNode rawPair : array(pairs)) {
                    ObjectNode pair = object(rawPair);
                    for (String field : PAIR_FIELDS) {
                        StrictJson.require(pair.has(field), "complete alliance pair fields required");
                    }
                }
            }
        }
        return new Request(header, legalRows, rows, rejected, input);
    }

    public static Evaluation evaluate(Request decoded) {
        ObjectNode request = object(StrictJson.parse(decoded.sourceJson()));
        ObjectNode legality = object(request.get("legality"));
        ObjectNode projection = object(request.get("projection"));
        ObjectNode snapshot = object(request.get("snapshot"));
        ObjectNode ranking = object(request.get("ranking"));
        ArrayNode rawLegal = array(legality.get("native_legal_candidates"));
        ArrayNode rawRows = array(projection.get("rows"));
        Header header = decoded.header();
        Optional<BigInteger> selected = header.selectedCandidate();
        List<LegalRow> legalRows = decoded.legalRows();
        List<ProjectedRow> rows = decoded.rows();
        Set<BigInteger> rejected = decoded.rejected();
        Map<BigInteger, ObjectNode> sourceById = new HashMap<>();
        for (JsonNode raw : rawLegal) {
            sourceById.put(positive(raw.get("candidate_character_id")), object(raw));
        }
        Observation observed = HeirCandidateDiagnostic.observe(header, legalRows, rows, rejected);
        ObjectNode result = StrictJson.object();
        result.put("schema", HeirCandidateDiagnostic.SCHEMA).put("advertised", false).put("read_only", true);
        put(result, "source_projection_schema", projection.get("schema"));
        put(result, "exact_ck3_build", legality.get("exact_ck3_build"));
        put(result, "episode_run_id", snapshot.get("episode_run_id"));
        put(result, "date_raw", snapshot.get("date_raw"));
        result.put("native_revision", header.nativeRevision()).put("legality_query_sequence", header.legalityQuerySequence())
                .put("observed_first_heir_character_id", header.observedHeir()).put("final_legal_candidate_count", rawLegal.size());
        result.set("ranking", ranking.deepCopy());
        if (selected.isPresent()) { result.put("selected_candidate_character_id", selected.orElseThrow()); }
        else { result.putNull("selected_candidate_character_id"); }
        ArrayNode outputRows = result.putArray("rows");
        for (var observedRow : observed.rows()) {
            ObjectNode row = object(rawRows.get(observedRow.ordinal()));
            ObjectNode output = outputRows.addObject();
            for (Field field : Field.values()) {
                JsonNode value = row.get(field.wire);
                put(output, field.wire, value);
            }
            if (observedRow.heirSpouseCount().isPresent()) { output.put("heir_spouse_count", observedRow.heirSpouseCount().orElseThrow()); }
            else { output.putNull("heir_spouse_count"); }
            ObjectNode source = sourceById.get(observedRow.projected().roles().candidate().orElseThrow());
            for (String field : List.of("recipient_ai_accept_raw", "recipient_matchmaker_character_id",
                    "recipient_answer_status_raw", "recipient_answer_allows_send", "complete_can_send")) {
                put(output, field, source == null ? null : source.get(field));
            }
            JsonNode pairs = row.get("possible_alliance_pairs");
            if (pairs == null || pairs.isNull()) { output.putNull("possible_alliance_pairs"); }
            else {
                ArrayNode copiedPairs = output.putArray("possible_alliance_pairs");
                for (JsonNode rawPair : array(pairs)) {
                    ObjectNode pair = object(rawPair);
                    ObjectNode copy = copiedPairs.addObject();
                    for (String field : PAIR_FIELDS) {
                        put(copy, field, pair.get(field));
                    }
                }
            }
            ArrayNode reasons = output.putArray("rejection_reasons");
            observedRow.rejectionReasons().forEach(reason -> reasons.add(reason.wire()));
        }
        return new Evaluation(HeirCandidateRankingConsumerPort.encodeOpaqueJson(result), observed);
    }

    private static void validate(JsonNode value, Kind kind) {
        if (value == null || value.isNull()) { return; }
        switch (kind) {
            case TEXT -> text(value);
            case INTEGER -> integer(value);
            case BOOLEAN -> StrictJson.require(value.isBoolean(), "actual diagnostic boolean token required");
            case INTEGER_LIST -> { for (JsonNode id : array(value)) { positive(id); } }
            case OBJECT -> validateNativeObject(object(value));
        }
    }
    private static void validateNativeObject(ObjectNode value) {
        value.properties().forEach(entry -> {
            if (NATIVE_BOOLEAN_FIELDS.contains(entry.getKey())) { validate(entry.getValue(), Kind.BOOLEAN); }
            if (NATIVE_INTEGER_FIELDS.contains(entry.getKey())) { validate(entry.getValue(), Kind.INTEGER); }
            if (Set.of("source", "payer_role", "application_timing").contains(entry.getKey())) { validate(entry.getValue(), Kind.TEXT); }
            if (Set.of("first_comparison", "second_comparison").contains(entry.getKey())) { validate(entry.getValue(), Kind.OBJECT); }
        });
    }
    private static void put(ObjectNode output, String field, JsonNode value) {
        output.set(field, value == null ? NullNode.instance : value.deepCopy());
    }
    private static Optional<String> text(JsonNode value) {
        if (value == null || value.isNull()) { return Optional.empty(); }
        StrictJson.require(value.isTextual(), "diagnostic text token required");
        if (!value.textValue().isEmpty()) { StrictJson.text(value.textValue()); }
        return Optional.of(value.textValue());
    }
    private static Optional<BigInteger> number(JsonNode value) {
        return value == null || value.isNull() ? Optional.empty() : Optional.of(integer(value));
    }
    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact diagnostic integer token required");
        return value.bigIntegerValue();
    }
    private static BigInteger positive(JsonNode value) {
        BigInteger result = integer(value); StrictJson.require(result.signum() > 0, "positive character identity required"); return result;
    }
    private static BigInteger nonnegative(JsonNode value) {
        BigInteger result = integer(value); StrictJson.require(result.signum() >= 0, "nonnegative diagnostic source counter required"); return result;
    }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "diagnostic object required"); return (ObjectNode) value;
    }
    private static ArrayNode array(JsonNode value) {
        StrictJson.require(value instanceof ArrayNode, "diagnostic array required"); return (ArrayNode) value;
    }
}
