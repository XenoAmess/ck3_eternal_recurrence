package org.xar.ck3.control.wave2.military.landstock;

import static org.xar.ck3.control.wave2.military.landstock.LandStockModel.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Strict projected operand boundary, not a raw native snapshot parser. */
public final class LandStockCodec {
    public static final String SCHEMA = "xar.land-stock.numeric-input/v1";
    public static final int MAX_BYTES = 16_384;
    private static final Set<String> FIELDS = Set.of("schema", "usage", "limit", "province_component_raw",
            "native_resupply_eligible", "loaded_gain_raw", "loaded_excess_slope_raw", "loaded_min_loss_raw",
            "loaded_max_loss_raw", "loaded_divisor_floor_raw", "commander_modifier_1a9_raw",
            "captured_stock_raw", "captured_capacity_raw");
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(8).maxNumberLength(24).build()).build());

    public record Input(RateInput rate, Long capturedStock, Long capturedCapacity) {}
    private LandStockCodec() {}

    public static Input decode(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) throw invalid("input byte budget exceeded or empty");
        JsonNode node;
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
            try (JsonParser parser = JSON.createParser(bytes)) {
                node = JSON.readTree(parser);
                if (node == null || parser.nextToken() != null) throw invalid("exactly one JSON object required");
            }
        } catch (IOException failure) { throw new IllegalArgumentException("invalid strict UTF-8/JSON input", failure); }
        Set<String> fields = new HashSet<>();
        if (node.isObject()) for (var property : node.properties()) fields.add(property.getKey());
        if (!node.isObject() || !FIELDS.equals(fields)) throw invalid("land stock operand field contract differs");
        if (!node.get("schema").isTextual() || !SCHEMA.equals(node.get("schema").textValue())) throw invalid("unsupported land stock schema");
        return new Input(new RateInput(integer(node, "usage"), integer(node, "limit"), integer(node, "province_component_raw"),
                predicate(node, "native_resupply_eligible"), integer(node, "loaded_gain_raw"), integer(node, "loaded_excess_slope_raw"),
                integer(node, "loaded_min_loss_raw"), integer(node, "loaded_max_loss_raw"), integer(node, "loaded_divisor_floor_raw"),
                integer(node, "commander_modifier_1a9_raw")), integer(node, "captured_stock_raw"), integer(node, "captured_capacity_raw"));
    }

    public static byte[] project(byte[] bytes) {
        Input value = decode(bytes);
        return encode(LandStockPolicy.projectRateAndStock(value.rate(), value.capturedStock(), value.capturedCapacity()));
    }

    public static byte[] encode(RateAndStock value) {
        ObjectNode result = JSON.createObjectNode();
        result.set("rate", rateNode(value.rate()));
        result.set("poststock", stockNode(value.stock()));
        try { return JSON.writeValueAsBytes(result); }
        catch (IOException failure) { throw new IllegalArgumentException("cannot encode numeric projection", failure); }
    }

    private static ObjectNode rateNode(RateResult value) {
        ObjectNode node = JSON.createObjectNode();
        node.put("full_land_rate_ready", value instanceof AvailableRate);
        node.put("status", value instanceof AvailableRate ? "available" : "unavailable");
        nullable(node, "native_limit_soldiers", value.limit());
        node.putNull("conditional_full_land_rate_raw");
        ArrayNode missing = node.putArray("missing_inputs");
        value.missingInputs().forEach(missing::add);
        node.put("scale", LandStockPolicy.SCALE);
        Components components = switch (value) {
            case UnavailableRate ignored -> null;
            case ComponentsUnavailableRate partial -> partial.components();
            case AvailableRate available -> available.components();
        };
        if (components != null) {
            node.put("province_component_raw", components.provinceComponent());
            node.put("excess_loss_raw", components.excessLoss());
            node.put("gain_component_raw", components.gainComponent());
            node.put("local_component_before_adjustment_raw", components.localBeforeAdjustment());
        }
        if (value instanceof AvailableRate available) {
            node.put("conditional_full_land_rate_raw", available.conditionalRate());
            node.put("local_component_after_adjustment_raw", available.localAfterAdjustment());
            nullable(node, "commander_divisor_raw", available.commanderDivisor());
            node.put("division_path", wire(available.divisionPath()));
        }
        return node;
    }

    private static ObjectNode stockNode(StockResult value) {
        ObjectNode node = JSON.createObjectNode();
        node.put("ready", value instanceof AvailableStock);
        node.putNull("raw"); node.putNull("signed64_add_raw"); node.putNull("clamp_branch");
        node.put("capacity_basis", "captured_current_capacity_unchanged");
        node.put("actual_future_capacity_observed", false);
        ArrayNode missing = node.putArray("missing_inputs");
        if (value instanceof MissingStock absent) {
            nullable(node, "signed64_add_raw", absent.signed64Add());
            absent.missingInputs().forEach(missing::add);
        } else if (value instanceof AvailableStock known) {
            node.put("raw", known.raw()); node.put("signed64_add_raw", known.signed64Add());
            node.put("clamp_branch", wire(known.clampBranch()));
        }
        return node;
    }

    private static Long integer(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value.isNull()) return null;
        if (!value.isIntegralNumber() || value.bigIntegerValue().bitLength() > 63) throw invalid(field + " must be signed int64 or null");
        return value.longValue();
    }
    private static Boolean predicate(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value.isNull()) return null;
        if (!value.isBoolean()) throw invalid(field + " must be bool or null");
        return value.booleanValue();
    }
    private static void nullable(ObjectNode node, String field, Long value) {
        if (value == null) node.putNull(field); else node.put(field, value.longValue());
    }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
