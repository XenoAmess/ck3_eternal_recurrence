package org.xar.ck3.control.finance.feastvalue;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Amounts;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Assessment;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Availability;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Costs;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.ObservedBoolean;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Request;

/** Strict leaf wire boundary. Missing and explicit null are intentionally distinct. */
public final class FeastValueCodec {
    public static final int MAX_BYTES = 65_536;
    private static final Set<String> INPUT_KEYS = Set.of("activity_key", "selected_option_key", "planning_stage",
            "final_can_start", "configured_cost_raw", "balance_available", "balance_raw", "reserved_raw",
            "expected_nonhost_guest_count", "peaceful_spend_allowed", "gold_floor_raw", "active_war_count", "war_cash_reserve_raw");
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(16).maxNumberLength(4096).build())
            .build()).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    private FeastValueCodec() { }

    public static Request decodeRequest(byte[] bytes) {
        JsonNode root = parse(bytes);
        if (!root.isObject()) throw new IllegalArgumentException("request must be an object");
        Set<String> actual = new HashSet<>();
        root.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(INPUT_KEYS)) throw new IllegalArgumentException("request fields differ from the declared leaf contract");
        JsonNode costs = vector(root, "configured_cost_raw");
        JsonNode available = vector(root, "balance_available");
        return new Request(text(root, "activity_key"), text(root, "selected_option_key"), integer(root.get("planning_stage"), "planning_stage", false),
                observedBoolean(root.get("final_can_start"), "final_can_start"),
                new Costs(nullableInteger(costs.get(0), "configured_cost_raw[0]"), nullableInteger(costs.get(1), "configured_cost_raw[1]"),
                        nullableInteger(costs.get(2), "configured_cost_raw[2]"), nullableInteger(costs.get(3), "configured_cost_raw[3]")),
                new Availability(bool(available.get(0), "balance_available[0]"), bool(available.get(1), "balance_available[1]"),
                        bool(available.get(2), "balance_available[2]"), bool(available.get(3), "balance_available[3]")),
                amounts(root, "balance_raw"), amounts(root, "reserved_raw"), nullableInteger(root.get("expected_nonhost_guest_count"), "expected_nonhost_guest_count"),
                observedBoolean(root.get("peaceful_spend_allowed"), "peaceful_spend_allowed"),
                nullableInteger(root.get("gold_floor_raw"), "gold_floor_raw"), nullableInteger(root.get("active_war_count"), "active_war_count"),
                nullableInteger(root.get("war_cash_reserve_raw"), "war_cash_reserve_raw"));
    }

    public static byte[] encodeRequest(Request request) {
        ObjectNode root = MAPPER.createObjectNode();
        root.put("activity_key", request.activityKey()); root.put("selected_option_key", request.selectedOptionKey());
        root.put("planning_stage", request.planningStage()); put(root, "final_can_start", request.finalCanStart());
        root.set("configured_cost_raw", costs(request.configuredCostRaw()));
        ArrayNode available = root.putArray("balance_available");
        for (int index = 0; index < 4; index++) available.add(request.balanceAvailable().at(index));
        root.set("balance_raw", amounts(request.balanceRaw())); root.set("reserved_raw", amounts(request.reservedRaw()));
        put(root, "expected_nonhost_guest_count", request.expectedNonhostGuestCount());
        put(root, "peaceful_spend_allowed", request.peacefulSpendAllowed());
        put(root, "gold_floor_raw", request.goldFloorRaw()); put(root, "active_war_count", request.activeWarCount());
        put(root, "war_cash_reserve_raw", request.warCashReserveRaw());
        return bytes(root);
    }

    public static byte[] encodeAssessment(Assessment assessment) {
        ObjectNode root = MAPPER.createObjectNode();
        root.put("policy", FeastStage5ValuePolicy.POLICY);
        root.put("decision", lower(assessment.decision())); root.put("status", lower(assessment.status()));
        root.put("reason", lower(assessment.reason())); root.put("positive_value_supported", assessment.positiveValueSupported());
        if (assessment.positiveValueSupported()) root.put("benefit_if_successful", FeastStage5ValuePolicy.BENEFIT);
        else root.putNull("benefit_if_successful");
        ArrayNode resources = root.putArray("resource_keys");
        FeastStage5ValuePolicy.RESOURCE_KEYS.forEach(resources::add);
        root.put("scale", FeastStage5ValuePolicy.SCALE); root.set("configured_cost_raw", costs(assessment.configuredCostRaw()));
        if (assessment.resourceCommitmentRaw().isPresent()) root.set("resource_commitment_raw", amounts(assessment.resourceCommitmentRaw().orElseThrow()));
        else root.putNull("resource_commitment_raw");
        if (assessment.submitReserveRaw().isPresent()) root.set("submit_reserve_raw", amounts(assessment.submitReserveRaw().orElseThrow()));
        else root.putNull("submit_reserve_raw");
        return bytes(root);
    }

    private static JsonNode parse(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) throw new IllegalArgumentException("input byte budget exceeded or empty");
        try {
            String value = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode node = MAPPER.readTree(value);
            if (node == null) throw new IllegalArgumentException("input is empty");
            return node;
        } catch (CharacterCodingException exception) {
            throw new IllegalArgumentException("input is not UTF-8", exception);
        } catch (IOException exception) {
            throw new IllegalArgumentException("input is not strict JSON", exception);
        }
    }
    private static JsonNode vector(JsonNode root, String name) {
        JsonNode value = root.get(name);
        if (value == null || !value.isArray() || value.size() != 4) throw new IllegalArgumentException(name + " must have four named resources");
        return value;
    }
    private static Amounts amounts(JsonNode root, String name) {
        JsonNode value = vector(root, name);
        return new Amounts(integer(value.get(0), name + "[0]", true), integer(value.get(1), name + "[1]", true),
                integer(value.get(2), name + "[2]", true), integer(value.get(3), name + "[3]", true));
    }
    private static String text(JsonNode root, String name) {
        JsonNode value = root.get(name);
        if (value == null || !value.isTextual()) throw new IllegalArgumentException(name + " must be a string");
        return value.textValue();
    }
    private static BigInteger integer(JsonNode value, String name, boolean nonnegative) {
        if (value == null || !value.isIntegralNumber()) throw new IllegalArgumentException(name + " must be an integer");
        BigInteger result = value.bigIntegerValue();
        if (nonnegative && result.signum() < 0) throw new IllegalArgumentException(name + " must be nonnegative");
        return result;
    }
    private static Optional<BigInteger> nullableInteger(JsonNode value, String name) {
        if (value == null) throw new IllegalArgumentException(name + " is required, null is explicit unknown");
        return value.isNull() ? Optional.empty() : Optional.of(integer(value, name, true));
    }
    private static boolean bool(JsonNode value, String name) {
        if (value == null || !value.isBoolean()) throw new IllegalArgumentException(name + " must be boolean");
        return value.booleanValue();
    }
    private static ObservedBoolean observedBoolean(JsonNode value, String name) {
        if (value == null) throw new IllegalArgumentException(name + " is required, null is explicit unknown");
        return value.isNull() ? ObservedBoolean.UNKNOWN : bool(value, name) ? ObservedBoolean.TRUE : ObservedBoolean.FALSE;
    }
    private static ArrayNode costs(Costs value) {
        ArrayNode result = MAPPER.createArrayNode();
        for (int index = 0; index < 4; index++) {
            Optional<BigInteger> cost = value.at(index);
            if (cost.isPresent()) result.add(cost.orElseThrow()); else result.addNull();
        }
        return result;
    }
    private static ArrayNode amounts(Amounts value) {
        ArrayNode result = MAPPER.createArrayNode();
        for (int index = 0; index < 4; index++) result.add(value.at(index));
        return result;
    }
    private static void put(ObjectNode root, String name, Optional<BigInteger> value) {
        if (value.isPresent()) root.put(name, value.orElseThrow()); else root.putNull(name);
    }
    private static void put(ObjectNode root, String name, ObservedBoolean value) {
        switch (value) { case TRUE -> root.put(name, true); case FALSE -> root.put(name, false); case UNKNOWN -> root.putNull(name); }
    }
    private static String lower(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static byte[] bytes(JsonNode root) {
        try {
            byte[] result = MAPPER.writeValueAsBytes(root);
            if (result.length > MAX_BYTES) throw new IllegalArgumentException("output byte budget exceeded");
            return result;
        } catch (IOException exception) {
            throw new IllegalStateException("JSON encoding failed", exception);
        }
    }
}
