package org.xar.ck3.control.wave2.development.constructionvalue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.OptionalInt;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel.*;

/** Concentrated bounded JSON boundary. SDK world and rows are consumed field projections. */
public final class ConstructionValueCodec {
    public static final String LOOKUP_SCHEMA = "xar.construction-authored-income-input.v1";
    public static final String SELECT_SCHEMA = "xar.construction-value-selection-input.v1";
    public static final int MAX_BYTES = 65_536;
    private static final BigInteger INT64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    private static final BigInteger INT64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    private static final Set<String> CANDIDATE_FIELDS = Set.of("barony_title_id", "province_id", "building_type_id", "slot_index",
            "stock_gold_cost_raw", "gold_before_raw", "building_key", "authored_monthly_income_hundredths",
            "authored_monthly_income_delta_hundredths", "old_authored_monthly_income_hundredths", "old_building_key", "slot_was_empty");
    private ConstructionValueCodec() { }

    public static LookupInput decodeLookup(byte[] raw) {
        JsonNode node = object(StrictJson.parse(raw, MAX_BYTES));
        Set<String> fields = new HashSet<>(Set.of("schema", "kind"));
        if (node.has("building_key")) { fields.add("building_key"); }
        if (node.has("exact_ck3_build")) { fields.add("exact_ck3_build"); }
        StrictJson.object(node, fields); StrictJson.require(LOOKUP_SCHEMA.equals(text(node.get("schema"))), "authored lookup schema required");
        LookupKind kind = switch (text(node.get("kind"))) {
            case "target" -> LookupKind.TARGET;
            case "existing" -> LookupKind.EXISTING;
            default -> throw new IllegalArgumentException("target or existing authored lookup required");
        };
        Build build = node.has("exact_ck3_build") ? Build.fromWire(text(node.get("exact_ck3_build")))
                : kind == LookupKind.TARGET ? Build.V11906 : Build.V12003;
        return new LookupInput(kind, read(node, "building_key", ConstructionValueCodec::text), build);
    }
    public static byte[] lookup(byte[] raw) {
        LookupInput input = decodeLookup(raw);
        OptionalInt income = input.kind() == LookupKind.TARGET ? AuthoredConstructionIncome.target(input.key(), input.build())
                : AuthoredConstructionIncome.existing(input.key(), input.build());
        ObjectNode output = StrictJson.object();
        if (income.isPresent()) { output.put("authored_monthly_income_hundredths", income.getAsInt()); }
        else { output.putNull("authored_monthly_income_hundredths"); }
        return StrictJson.canonical(output, 4_096);
    }

    public static SelectionInput decodeSelection(byte[] raw) {
        JsonNode node = object(StrictJson.parse(raw, MAX_BYTES));
        StrictJson.object(node, node.has("exact_ck3_build") ? Set.of("schema", "world", "exact_ck3_build") : Set.of("schema", "world"));
        StrictJson.require(SELECT_SCHEMA.equals(text(node.get("schema"))), "construction value selection schema required");
        Build build = node.has("exact_ck3_build") ? Build.fromWire(text(node.get("exact_ck3_build"))) : Build.V11906;
        return new SelectionInput(worldProjection(node.get("world")), build);
    }
    /** Declared SDK projection for another strict codec; preserves raw parsed integer/float token categories. */
    public static World worldProjection(JsonNode parsedWorld) {
        JsonNode world = object(parsedWorld);
        return new World(read(world, "player_gold_raw", ConstructionValueCodec::signed64),
                read(world, "active_constructions", value -> rows(value, ConstructionValueCodec::active)),
                read(world, "legal_samples", value -> rows(value, ConstructionValueCodec::sample)),
                read(world, "completed_buildings_observed", ConstructionValueCodec::bool),
                read(world, "completed_buildings", value -> rows(value, ConstructionValueCodec::completed)),
                read(world, "positive_income_coverage_complete", ConstructionValueCodec::bool));
    }
    public static byte[] select(byte[] raw) { return encodeSelection(ConstructionValuePolicy.select(decodeSelection(raw))); }
    public static byte[] encodeSelection(Selection selection) {
        return selection instanceof Selected selected ? StrictJson.canonical(candidate(selected.candidate()), 4_096)
                : StrictJson.canonical(NullNode.instance, 4_096);
    }
    public static byte[] consumeSelection(byte[] raw) { return encodeConsumer(ConstructionValuePolicy.consumeSelection(decodeSelection(raw))); }
    public static byte[] encodeConsumer(ConsumerResult result) {
        ObjectNode node = StrictJson.object();
        switch (result) {
            case CandidateSelected selected -> { node.put("status", "selected"); node.set("candidate", candidate(selected.candidate())); }
            case NoLegalBudgetedBuilding ignored -> node.put("status", "no_legal_budgeted_building");
            case EvidenceInsufficient ignored -> {
                node.put("status", "evidence_insufficient"); node.put("reason", "positive_income_candidate_coverage_incomplete");
            }
        }
        return StrictJson.canonical(node, 4_096);
    }
    public static Selection decodeSelectionResult(byte[] raw) {
        JsonNode node = StrictJson.parse(raw, 4_096); if (node.isNull()) { return new NoCandidate(); }
        StrictJson.object(node, CANDIDATE_FIELDS);
        JsonNode oldKey = node.get("old_building_key");
        return new Selected(new Candidate(integer(node.get("barony_title_id")), integer(node.get("province_id")), integer(node.get("building_type_id")),
                integer(node.get("slot_index")), signed64(node.get("stock_gold_cost_raw")), signed64(node.get("gold_before_raw")),
                text(node.get("building_key")), nonnegativeInt(node.get("authored_monthly_income_hundredths")),
                nonnegativeInt(node.get("authored_monthly_income_delta_hundredths")), nonnegativeInt(node.get("old_authored_monthly_income_hundredths")),
                oldKey.isNull() ? null : text(oldKey), bool(node.get("slot_was_empty"))));
    }

    private static ObjectNode candidate(Candidate value) {
        ObjectNode node = StrictJson.object(); node.put("barony_title_id", value.baronyId()); node.put("province_id", value.provinceId());
        node.put("building_type_id", value.buildingTypeId()); node.put("slot_index", value.slotIndex());
        node.put("stock_gold_cost_raw", value.stockGoldCost()); node.put("gold_before_raw", value.goldBefore()); node.put("building_key", value.buildingKey());
        node.put("authored_monthly_income_hundredths", value.authoredIncomeHundredths());
        node.put("authored_monthly_income_delta_hundredths", value.authoredIncomeDeltaHundredths());
        node.put("old_authored_monthly_income_hundredths", value.oldAuthoredIncomeHundredths());
        if (value.oldBuildingKey() == null) { node.putNull("old_building_key"); } else { node.put("old_building_key", value.oldBuildingKey()); }
        node.put("slot_was_empty", value.slotWasEmpty()); return node;
    }
    private static Active active(JsonNode node) {
        object(node); return new Active(read(node, "barony_title_id", ConstructionValueCodec::integer),
                read(node, "province_id", ConstructionValueCodec::integer), read(node, "active", ConstructionValueCodec::bool));
    }
    private static Sample sample(JsonNode node) {
        object(node); return new Sample(read(node, "barony_title_id", ConstructionValueCodec::integer),
                read(node, "province_id", ConstructionValueCodec::integer), read(node, "building_type_id", ConstructionValueCodec::integer),
                read(node, "slot_index", ConstructionValueCodec::integer), read(node, "building_key", ConstructionValueCodec::text),
                read(node, "native_cost_observed", ConstructionValueCodec::bool), read(node, "cost_raw_native", value -> rows(value, ConstructionValueCodec::signed64)));
    }
    private static Completed completed(JsonNode node) {
        object(node); return new Completed(read(node, "barony_title_id", ConstructionValueCodec::integer),
                read(node, "province_id", ConstructionValueCodec::integer), read(node, "slot_index", ConstructionValueCodec::integer),
                read(node, "building_key", ConstructionValueCodec::text));
    }
    private static <T> List<T> rows(JsonNode node, Function<JsonNode, T> parse) {
        StrictJson.require(node.isArray(), "declared SDK array required"); List<T> result = new ArrayList<>();
        for (JsonNode value : node) { result.add(parse.apply(value)); } return List.copyOf(result);
    }
    private static JsonNode object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "SDK object projection required"); return node; }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "exact integer token required; bool/float/string rejected"); return node.bigIntegerValue();
    }
    private static BigInteger signed64(JsonNode node) { return StrictJson.integer(node, INT64_MIN, INT64_MAX); }
    private static int nonnegativeInt(JsonNode node) { return Math.toIntExact(StrictJson.integer(node, 0, Integer.MAX_VALUE)); }
    private static Boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "actual boolean token required"); return node.booleanValue(); }
    private static String text(JsonNode node) {
        StrictJson.require(node != null && node.isTextual(), "string token required");
        if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); } return node.textValue();
    }
    private static <T> Field<T> read(JsonNode node, String name, Function<JsonNode, T> parser) {
        JsonNode value = node.get(name); return value == null ? Field.missing() : value.isNull() ? Field.nil() : Field.of(parser.apply(value));
    }
}
