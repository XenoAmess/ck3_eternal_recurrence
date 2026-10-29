package org.xar.ck3.control.governance.marriage;

import static org.xar.ck3.control.governance.marriage.MarriageModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.math.BigInteger;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict request envelope; existing native producer objects remain extensible projections. */
public final class MarriageCodec {
    public static final String SCHEMA = "xar.ck3.marriage-policy-request.v1";
    /** The 189-candidate producer is larger than the independent map receipt contract. */
    public static final int MAX_BYTES = 262_144;
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final Set<String> REQUEST_FIELDS = Set.of("schema", "legality", "values",
            "split_successor_verified", "excluded_candidate_ids", "shortlist_limit");
    private MarriageCodec() { }

    public static Request decode(byte[] raw) {
        ObjectNode root = StrictJson.object(parse(raw), REQUEST_FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "marriage policy request schema");
        JsonNode verified = root.get("split_successor_verified");
        StrictJson.require(verified.isBoolean(), "split proof must be boolean");
        List<CandidateValue> values = list(root.get("values"), MarriageCodec::candidateValue);
        List<BigInteger> exclusions = list(root.get("excluded_candidate_ids"), MarriageCodec::integer);
        Set<BigInteger> unique = new HashSet<>(exclusions);
        StrictJson.require(unique.size() == exclusions.size(), "duplicate excluded candidate IDs");
        int limit = (int) StrictJson.integer(root.get("shortlist_limit"), 1, 5);
        return new Request(legality(root.get("legality")), values, verified.booleanValue(), unique, limit);
    }

    public static byte[] encode(Request request) {
        ObjectNode root = StrictJson.object();
        root.put("schema", SCHEMA);
        root.set("legality", legalityNode(request.legality()));
        root.set("values", array(request.values(), MarriageCodec::candidateValueNode));
        root.put("split_successor_verified", request.splitSuccessorVerified());
        root.set("excluded_candidate_ids", array(request.excludedCandidateIds().stream().sorted().toList(), BigIntegerNode::valueOf));
        root.put("shortlist_limit", request.shortlistLimit());
        return canonical(root);
    }

    public static byte[] encodeDecision(Decision decision) { return canonical(decisionNode(decision)); }

    private static JsonNode parse(byte[] raw) {
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded marriage UTF-8 input required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode result = MAPPER.readTree(text);
            StrictJson.require(result != null, "JSON value required");
            return result;
        } catch (IOException error) { throw new IllegalArgumentException("invalid marriage JSON/UTF-8/duplicate fields", error); }
    }

    private static byte[] canonical(JsonNode node) {
        try {
            byte[] result = MAPPER.writeValueAsBytes(ordered(node));
            StrictJson.require(result.length <= MAX_BYTES, "marriage projection exceeds byte budget");
            return result;
        } catch (IOException error) { throw new IllegalArgumentException("cannot serialize marriage projection", error); }
    }

    private static JsonNode ordered(JsonNode node) {
        if (node.isObject()) {
            ObjectNode result = StrictJson.object();
            TreeSet<String> keys = new TreeSet<>();
            node.fieldNames().forEachRemaining(keys::add);
            keys.forEach(key -> result.set(key, ordered(node.get(key))));
            return result;
        }
        if (node.isArray()) {
            ArrayNode result = StrictJson.object().arrayNode();
            node.forEach(value -> result.add(ordered(value)));
            return result;
        }
        StrictJson.require(!node.isFloatingPointNumber(), "marriage domain excludes floating point");
        return node.deepCopy();
    }

    public static ObjectNode decisionNode(Decision decision) {
        ObjectNode node = StrictJson.object();
        node.put("status", decision.status() == Status.SELECTED ? "selected" : "no_positive_value");
        if (decision.selectedCandidateCharacterId() == null) { node.putNull("selected_candidate_character_id"); }
        else { node.put("selected_candidate_character_id", decision.selectedCandidateCharacterId()); }
        node.put("reason", decision.reason().wire());
        node.set("evaluated", array(decision.evaluated(), evaluation -> {
            ObjectNode item = StrictJson.object();
            item.put("candidate_character_id", evaluation.candidateCharacterId());
            item.put("reason", evaluation.reason().wire());
            PositiveTiming timing = evaluation.positiveTiming();
            if (timing != null) {
                item.put("child_wait_raw", timing.childWaitRaw());
                item.put("candidate_age_at_child_adulthood_raw", timing.candidateAgeAtChildAdulthoodRaw());
                item.put("recipient_ai_accept_raw", timing.recipientAiAcceptRaw());
            }
            return item;
        }));
        return node;
    }

    private static ObjectNode object(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "native policy projection requires an object");
        return (ObjectNode) node;
    }

    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "exact integer token required; no boolean/float/string");
        return node.bigIntegerValue();
    }

    private static Boolean bool(JsonNode node) {
        StrictJson.require(node.isBoolean(), "boolean token required");
        return node.booleanValue();
    }

    private static String text(JsonNode node) {
        StrictJson.require(node.isTextual(), "string token required");
        String value = node.textValue();
        if (!value.isEmpty()) { StrictJson.text(value); }
        return value;
    }

    private static <T> Field<T> field(ObjectNode node, String key, Function<JsonNode, T> reader) {
        JsonNode value = node.get(key);
        if (value == null) { return Field.missing(); }
        if (value.isNull()) { return Field.nil(); }
        return Field.of(reader.apply(value));
    }

    private static <T> List<T> list(JsonNode node, Function<JsonNode, T> reader) {
        StrictJson.require(node != null && node.isArray(), "array token required");
        List<T> result = new ArrayList<>();
        for (JsonNode entry : node) { result.add(reader.apply(entry)); }
        return List.copyOf(result);
    }

    private static Facts facts(ObjectNode node) {
        EnumMap<IntegerTerm, Field<BigInteger>> integers = new EnumMap<>(IntegerTerm.class);
        EnumMap<BooleanTerm, Field<Boolean>> booleans = new EnumMap<>(BooleanTerm.class);
        EnumMap<TextTerm, Field<String>> texts = new EnumMap<>(TextTerm.class);
        for (IntegerTerm key : IntegerTerm.values()) { if (node.has(key.wire())) { integers.put(key, field(node, key.wire(), MarriageCodec::integer)); } }
        for (BooleanTerm key : BooleanTerm.values()) { if (node.has(key.wire())) { booleans.put(key, field(node, key.wire(), MarriageCodec::bool)); } }
        for (TextTerm key : TextTerm.values()) { if (node.has(key.wire())) { texts.put(key, field(node, key.wire(), MarriageCodec::text)); } }
        return new Facts(integers, booleans, texts);
    }

    private static Relationship relationship(ObjectNode node, String prefix) {
        return new Relationship(field(node, prefix + "betrothed_character_id", MarriageCodec::integer),
                field(node, prefix + "primary_spouse_character_id", MarriageCodec::integer),
                field(node, prefix + "spouse_character_ids", value -> list(value, MarriageCodec::integer)));
    }

    private static Legality legality(JsonNode node) {
        ObjectNode value = object(node);
        return new Legality(facts(value), relationship(value, ""),
                field(value, "native_legal_candidates", rows -> list(rows, row -> new CompactCandidate(facts(object(row))))));
    }

    private static CandidateValue candidateValue(JsonNode node) {
        ObjectNode value = object(node);
        return new CandidateValue(facts(value), field(value, "row", MarriageCodec::fullValue));
    }

    private static FullValue fullValue(JsonNode node) {
        ObjectNode value = object(node);
        return new FullValue(facts(value), relationship(value, "heir_"), relationship(value, "candidate_"),
                field(value, "heir_native_fertility", fertility -> facts(object(fertility))),
                field(value, "candidate_native_fertility", fertility -> facts(object(fertility))),
                field(value, "generic_costs", MarriageCodec::costs),
                field(value, "possible_alliance_pairs", rows -> list(rows, row -> facts(object(row)))));
    }

    private static Costs costs(JsonNode node) {
        ObjectNode value = object(node);
        EnumMap<CostTerm, Field<BigInteger>> terms = new EnumMap<>(CostTerm.class);
        for (CostTerm term : CostTerm.values()) { terms.put(term, field(value, term.wire(), MarriageCodec::integer)); }
        return new Costs(facts(value), terms);
    }

    private static ObjectNode factsNode(Facts facts) {
        ObjectNode node = StrictJson.object();
        facts.integers().forEach((key, value) -> write(node, key.wire(), value, BigIntegerNode::valueOf));
        facts.booleans().forEach((key, value) -> write(node, key.wire(), value, BooleanNode::valueOf));
        facts.texts().forEach((key, value) -> write(node, key.wire(), value, TextNode::valueOf));
        return node;
    }

    private static void relationshipNode(ObjectNode node, Relationship relationship, String prefix) {
        write(node, prefix + "betrothed_character_id", relationship.betrothed(), BigIntegerNode::valueOf);
        write(node, prefix + "primary_spouse_character_id", relationship.primarySpouse(), BigIntegerNode::valueOf);
        write(node, prefix + "spouse_character_ids", relationship.spouses(), values -> array(values, BigIntegerNode::valueOf));
    }

    private static ObjectNode legalityNode(Legality legality) {
        ObjectNode node = factsNode(legality.facts());
        relationshipNode(node, legality.relationship(), "");
        write(node, "native_legal_candidates", legality.candidates(), rows -> array(rows, row -> factsNode(row.facts())));
        return node;
    }

    private static ObjectNode candidateValueNode(CandidateValue value) {
        ObjectNode node = factsNode(value.facts());
        write(node, "row", value.row(), MarriageCodec::fullValueNode);
        return node;
    }

    private static ObjectNode fullValueNode(FullValue value) {
        ObjectNode node = factsNode(value.facts());
        relationshipNode(node, value.heirRelationship(), "heir_");
        relationshipNode(node, value.candidateRelationship(), "candidate_");
        write(node, "heir_native_fertility", value.heirFertility(), MarriageCodec::factsNode);
        write(node, "candidate_native_fertility", value.candidateFertility(), MarriageCodec::factsNode);
        write(node, "generic_costs", value.costs(), costs -> {
            ObjectNode result = factsNode(costs.facts());
            costs.amounts().forEach((key, amount) -> write(result, key.wire(), amount, BigIntegerNode::valueOf));
            return result;
        });
        write(node, "possible_alliance_pairs", value.alliances(), pairs -> array(pairs, MarriageCodec::factsNode));
        return node;
    }

    private static <T> void write(ObjectNode node, String key, Field<T> field, Function<T, JsonNode> encoder) {
        if (field.presence() == Presence.NULL) { node.set(key, NullNode.instance); }
        else if (field.presence() == Presence.VALUE) { node.set(key, encoder.apply(field.value())); }
    }

    private static <T> ArrayNode array(List<T> values, Function<T, JsonNode> encoder) {
        ArrayNode array = StrictJson.object().arrayNode();
        values.forEach(value -> array.add(encoder.apply(value)));
        return array;
    }
}
