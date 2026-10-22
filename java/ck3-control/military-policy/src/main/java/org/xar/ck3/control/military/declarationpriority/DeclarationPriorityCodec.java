package org.xar.ck3.control.military.declarationpriority;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.declarationpriority.DeclarationObjectivePriority.Declaration;
import org.xar.ck3.control.military.declarationpriority.DeclarationObjectivePriority.LeafInput;
import org.xar.ck3.control.military.declarationpriority.DeclarationObjectivePriority.PowerAssessment;
import org.xar.ck3.control.military.declarationpriority.DeclarationObjectivePriority.SelectionInput;

/** Strict projected contract; rich legacy rows must be projected explicitly before encoding. */
public final class DeclarationPriorityCodec {
    public static final String LEAF_SCHEMA = "xar.ck3.declaration-objective-priority.input/v1";
    public static final String SELECTION_SCHEMA = "xar.ck3.declaration-objective-order.input/v1";
    private static final Set<String> DECLARATION_FIELDS = Set.of("declaration_id", "target_character_id",
            "casus_belli_index", "casus_belli_key", "configuration_index", "claimant_character_id",
            "target_title_ids", "source");
    private static final Set<String> ASSESSMENT_FIELDS = Set.of("target_character_id", "actor_power_base_raw",
            "actor_network_contribution_raw", "target_network_contribution_raw", "target_power_total_raw",
            "actual_power_ratio_raw", "distance_raw");

    private DeclarationPriorityCodec() { }

    public static LeafInput decodeLeaf(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "actor_character_id", "declaration"));
        require(text(root.get("schema")).equals(LEAF_SCHEMA), "wrong leaf schema");
        return new LeafInput(field(root, "actor_character_id", DeclarationPriorityCodec::integer),
                field(root, "declaration", DeclarationPriorityCodec::declaration));
    }

    public static SelectionInput decodeSelection(byte[] raw) {
        ObjectNode root = object(StrictJson.parse(raw));
        allowed(root, Set.of("schema", "actor_character_id", "declarations", "war_entry_assessments"));
        require(root.has("schema") && root.has("actor_character_id") && root.has("declarations"), "missing selection fields");
        require(text(root.get("schema")).equals(SELECTION_SCHEMA), "wrong selection schema");
        return new SelectionInput(field(root, "actor_character_id", DeclarationPriorityCodec::integer),
                list(root.get("declarations"), DeclarationPriorityCodec::declaration),
                field(root, "war_entry_assessments", node -> list(node, DeclarationPriorityCodec::assessment)));
    }

    public static byte[] encodeLeaf(LeafInput input) {
        ObjectNode root = StrictJson.object().put("schema", LEAF_SCHEMA);
        put(root, "actor_character_id", input.actorCharacterId(), DeclarationPriorityCodec::integerNode);
        put(root, "declaration", input.declaration(), DeclarationPriorityCodec::declarationNode);
        return StrictJson.canonical(root);
    }

    public static byte[] encodeSelection(SelectionInput input) {
        ObjectNode root = StrictJson.object().put("schema", SELECTION_SCHEMA);
        put(root, "actor_character_id", input.actorCharacterId(), DeclarationPriorityCodec::integerNode);
        root.set("declarations", arrayNode(input.declarations(), DeclarationPriorityCodec::declarationNode));
        put(root, "war_entry_assessments", input.warEntryAssessments(),
                rows -> arrayNode(rows, DeclarationPriorityCodec::assessmentNode));
        return StrictJson.canonical(root);
    }

    private static Declaration declaration(JsonNode node) {
        ObjectNode row = object(node);
        allowed(row, DECLARATION_FIELDS);
        return new Declaration(field(row, "declaration_id", DeclarationPriorityCodec::text),
                field(row, "target_character_id", DeclarationPriorityCodec::integer),
                field(row, "casus_belli_index", DeclarationPriorityCodec::integer),
                field(row, "casus_belli_key", DeclarationPriorityCodec::text),
                field(row, "configuration_index", DeclarationPriorityCodec::integer),
                field(row, "claimant_character_id", DeclarationPriorityCodec::integer),
                field(row, "target_title_ids", value -> list(value, DeclarationPriorityCodec::integer)),
                field(row, "source", DeclarationPriorityCodec::text));
    }

    private static PowerAssessment assessment(JsonNode node) {
        ObjectNode row = StrictJson.object(node, ASSESSMENT_FIELDS);
        return new PowerAssessment(integer(row.get("target_character_id")), integer(row.get("actor_power_base_raw")),
                integer(row.get("actor_network_contribution_raw")), integer(row.get("target_network_contribution_raw")),
                integer(row.get("target_power_total_raw")), integer(row.get("actual_power_ratio_raw")), integer(row.get("distance_raw")));
    }

    private static ObjectNode declarationNode(Declaration row) {
        ObjectNode node = StrictJson.object();
        put(node, "declaration_id", row.declarationId(), DeclarationPriorityCodec::textNode);
        put(node, "target_character_id", row.targetCharacterId(), DeclarationPriorityCodec::integerNode);
        put(node, "casus_belli_index", row.casusBelliIndex(), DeclarationPriorityCodec::integerNode);
        put(node, "casus_belli_key", row.casusBelliKey(), DeclarationPriorityCodec::textNode);
        put(node, "configuration_index", row.configurationIndex(), DeclarationPriorityCodec::integerNode);
        put(node, "claimant_character_id", row.claimantCharacterId(), DeclarationPriorityCodec::integerNode);
        put(node, "target_title_ids", row.targetTitleIds(), values -> arrayNode(values, DeclarationPriorityCodec::integerNode));
        put(node, "source", row.source(), DeclarationPriorityCodec::textNode);
        return node;
    }

    private static ObjectNode assessmentNode(PowerAssessment row) {
        ObjectNode node = StrictJson.object();
        node.set("target_character_id", integerNode(row.targetCharacterId()));
        node.set("actor_power_base_raw", integerNode(row.actorPowerBaseRaw()));
        node.set("actor_network_contribution_raw", integerNode(row.actorNetworkContributionRaw()));
        node.set("target_network_contribution_raw", integerNode(row.targetNetworkContributionRaw()));
        node.set("target_power_total_raw", integerNode(row.targetPowerTotalRaw()));
        node.set("actual_power_ratio_raw", integerNode(row.actualPowerRatioRaw()));
        node.set("distance_raw", integerNode(row.distanceRaw()));
        return node;
    }

    private static ObjectNode object(JsonNode node) {
        require(node instanceof ObjectNode, "JSON object required");
        return (ObjectNode) node;
    }

    private static void allowed(ObjectNode node, Set<String> fields) {
        node.fieldNames().forEachRemaining(name -> require(fields.contains(name), "unknown field: " + name));
    }

    private static String text(JsonNode value) {
        require(value != null && value.isTextual(), "exact JSON string required");
        String result = value.textValue();
        if (!result.isEmpty()) { StrictJson.text(result); }
        return result;
    }

    private static BigInteger integer(JsonNode value) {
        require(value != null && value.isIntegralNumber(), "exact JSON integer required; no boolean, float or string");
        return value.bigIntegerValue();
    }

    private static JsonNode integerNode(BigInteger value) { return StrictJson.object().numberNode(value); }
    private static JsonNode textNode(String value) { return StrictJson.object().textNode(value); }

    private static <T> JsonField<T> field(ObjectNode row, String key, Function<JsonNode, T> parser) {
        if (!row.has(key)) { return JsonField.missing(); }
        JsonNode value = row.get(key);
        return value.isNull() ? JsonField.nullValue() : JsonField.of(parser.apply(value));
    }

    private static <T> List<T> list(JsonNode value, Function<JsonNode, T> parser) {
        require(value instanceof ArrayNode, "JSON array required");
        List<T> values = new ArrayList<>();
        for (JsonNode row : value) { values.add(parser.apply(row)); }
        return List.copyOf(values);
    }

    private static <T> ArrayNode arrayNode(List<T> values, Function<T, JsonNode> writer) {
        ArrayNode result = StrictJson.object().arrayNode();
        values.forEach(value -> result.add(writer.apply(value)));
        return result;
    }

    private static <T> void put(ObjectNode row, String key, JsonField<T> value, Function<T, JsonNode> writer) {
        switch (value.presence()) {
            case MISSING -> { }
            case NULL -> row.putNull(key);
            case VALUE -> row.set(key, writer.apply(value.value()));
        }
    }
}
