package org.xar.ck3.control.wave2.military.landstock;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.landstock.LandStockModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

class LandStockPolicyTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void completeOriginalRateKernelGolden() throws IOException {
        JsonNode golden = golden();
        assertTrue(golden.path("rates").size() >= 40);
        for (JsonNode vector : golden.path("rates")) {
            JsonNode actual = JSON.readTree(LandStockCodec.project(JSON.writeValueAsBytes(vector.get("input"))));
            assertEquals(vector.get("expected_rate"), actual.get("rate"), vector.path("id").asText());
            if (vector.has("expected_poststock")) {
                assertEquals(vector.get("expected_poststock"), actual.get("poststock"), vector.path("id").asText());
            }
        }
    }

    @Test void originalSupplyMultiplyAndAllDivisionPathsGolden() throws IOException {
        JsonNode golden = golden();
        assertTrue(golden.path("multiplications").size() >= 50);
        assertTrue(golden.path("divisions").size() >= 50);
        for (JsonNode vector : golden.path("multiplications")) {
            assertEquals(vector.get("expected").longValue(), LandStockPolicy.nativeFixedMultiply(
                    vector.get("base").longValue(), vector.get("multiplier").longValue()), vector.path("id").asText());
        }
        for (JsonNode vector : golden.path("divisions")) {
            DivisionResult actual = LandStockPolicy.nativeFixedDivide(vector.get("value").longValue(),
                    vector.get("divisor").longValue());
            assertEquals(vector.get("expected_value").bigIntegerValue(), actual.value(), vector.path("id").asText());
            assertEquals(vector.get("expected_path").textValue(), actual.path().name().toLowerCase(java.util.Locale.ROOT));
        }
    }

    @Test void omittedUnreachedOperandsStayUnused() {
        RateInput nonnegative = new RateInput(0L, 1L, 0L, false, null, null, null, null, null, null);
        AvailableRate zero = assertInstanceOf(AvailableRate.class, LandStockPolicy.projectRate(nonnegative));
        assertEquals(0, zero.conditionalRate());
        RateInput overLimit = new RateInput(2L, 1L, 700_000L, null, null, 10_000L, 200_000L,
                5_000_000L, null, null);
        assertInstanceOf(AvailableRate.class, LandStockPolicy.projectRate(overLimit));
        RateInput reached = new RateInput(0L, 1L, -1L, false, null, null, null, null, null, null);
        ComponentsUnavailableRate absent = assertInstanceOf(ComponentsUnavailableRate.class, LandStockPolicy.projectRate(reached));
        assertEquals(List.of("loaded_divisor_floor_raw", "commander_modifier_1a9_raw", "loaded_max_loss_raw"), absent.missingInputs());
    }

    @Test void nativeZeroDivisorAndNegativeWrappedStockArePreserved() {
        RateInput input = new RateInput(0L, 0L, -200_000L, false, null, null, null, 1_000_000L, 0L, -100_000L);
        AvailableRate rate = assertInstanceOf(AvailableRate.class, LandStockPolicy.projectRate(input));
        assertEquals(4_294_967_295L, rate.conditionalRate());
        assertEquals(DivisionPath.ZERO_DIVISOR_POSITIVE_U32_MAX, rate.divisionPath());
        AvailableStock stock = assertInstanceOf(AvailableStock.class,
                LandStockPolicy.projectStockAfterRate(rate, Long.MAX_VALUE, null));
        assertEquals(0, stock.raw());
        assertEquals(ClampBranch.NEGATIVE_WRAPPED_ADD_TO_ZERO, stock.clampBranch());
        StockResult wide = LandStockPolicy.projectStockAfterRate(BigInteger.ONE.shiftLeft(64).add(BigInteger.TEN), 20L, 100L);
        assertEquals(new AvailableStock(30, 30, ClampBranch.MIN_CHANGED_CAPTURED_CAPACITY), wide);
    }

    @Test void minMaxOrderAndMissingCapacityAreNotRewritten() {
        RateInput input = new RateInput(110L, 100L, 0L, false, null, 10_000L, 600_000L,
                400_000L, 300_000L, 100_000L);
        AvailableRate rate = assertInstanceOf(AvailableRate.class, LandStockPolicy.projectRate(input));
        assertEquals(600_000, rate.components().excessLoss());
        MissingStock stock = assertInstanceOf(MissingStock.class,
                LandStockPolicy.projectStockAfterRate(rate, 1_000_000L, null));
        assertEquals(List.of("current_supply_capacity_raw"), stock.missingInputs());
        assertNotNull(stock.signed64Add());
    }

    @Test void actualIntegerTokensAndDomainsAreChecked() throws IOException {
        JsonNode input = golden().path("rates").get(0).get("input");
        for (String field : List.of("usage", "limit", "province_component_raw", "loaded_gain_raw",
                "loaded_excess_slope_raw", "loaded_min_loss_raw", "loaded_max_loss_raw",
                "loaded_divisor_floor_raw", "commander_modifier_1a9_raw", "captured_stock_raw", "captured_capacity_raw")) {
            for (String wrong : List.of("true", "1.0", "1e0", "\"1\"", "9223372036854775808", "-9223372036854775809")) {
                byte[] mutated = withRawToken(input, field, wrong);
                assertThrows(IllegalArgumentException.class,
                        () -> LandStockCodec.decode(mutated), field + ":" + wrong);
            }
        }
        for (String wrong : List.of("0", "1", "\"true\"")) {
            byte[] mutated = withRawToken(input, "native_resupply_eligible", wrong);
            assertThrows(IllegalArgumentException.class, () -> LandStockCodec.decode(mutated));
        }
    }

    @Test void missingNullAndMalformedWireHaveExplicitBehavior() throws IOException {
        ObjectNode input = golden().path("rates").get(0).get("input").deepCopy();
        input.putNull("usage");
        assertInstanceOf(UnavailableRate.class, LandStockPolicy.projectRate(LandStockCodec.decode(JSON.writeValueAsBytes(input)).rate()));
        input.remove("usage");
        assertThrows(IllegalArgumentException.class, () -> LandStockCodec.decode(JSON.writeValueAsBytes(input)));
        assertThrows(IllegalArgumentException.class, () -> LandStockCodec.decode("{\"schema\":1,\"schema\":1}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LandStockCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> LandStockCodec.decode(new byte[LandStockCodec.MAX_BYTES + 1]));
        ObjectNode extra = golden().path("rates").get(0).get("input").deepCopy();
        extra.put("extra", 0);
        assertThrows(IllegalArgumentException.class, () -> LandStockCodec.decode(JSON.writeValueAsBytes(extra)));
        byte[] trailing = (JSON.writeValueAsString(golden().path("rates").get(0).get("input")) + "{}").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> LandStockCodec.decode(trailing));
        assertEquals(BigInteger.valueOf(4_294_967_295L), LandStockPolicy.nativeFixedDivide(-1, 0).value());
    }

    private static byte[] withRawToken(JsonNode input, String target, String token) throws IOException {
        StringBuilder json = new StringBuilder("{");
        for (var entry : input.properties()) {
            if (json.length() > 1) json.append(',');
            json.append(JSON.writeValueAsString(entry.getKey())).append(':');
            json.append(entry.getKey().equals(target) ? token : JSON.writeValueAsString(entry.getValue()));
        }
        return json.append('}').toString().getBytes(StandardCharsets.UTF_8);
    }

    private static JsonNode golden() throws IOException {
        try (var input = LandStockPolicyTest.class.getResourceAsStream("/landstock/native-land-stock-golden-v1.json")) {
            if (input == null) throw new IOException("tracked original producer golden required; no runtime Python fallback or skip");
            return JSON.readTree(input);
        }
    }
}
