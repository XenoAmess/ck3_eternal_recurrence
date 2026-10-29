package org.xar.ck3.control.wave2.development.constructionmode3;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructionmode3.ConstructionMode3.*;

final class ConstructionMode3CodecTest {
    @TestFactory
    Stream<DynamicTest> comparesRealPacketProducerBothConsumersAndEveryRawTokenFailure() throws IOException {
        JsonNode root = golden(); assertEquals(41, root.get("cases").size());
        return StreamSupport.stream(root.get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            JsonNode actual = StrictJson.parse(ConstructionMode3Codec.evaluate(utf8(row.get("input_json").textValue())));
            assertEquals(row.get("expected"), actual);
            JsonNode packet = actual.get("world").get("native_mode3_inputs");
            if (packet != null && !packet.isNull() && !actual.get("observation").path("native_mode3_inputs_status").asText().equals("source_red")) {
                Packet decoded = ConstructionMode3Codec.decodePacket(StrictJson.canonical(packet));
                assertEquals(packet, StrictJson.parse(ConstructionMode3Codec.encode(decoded)));
                assertEquals(decoded, ConstructionMode3Codec.decodePacket(ConstructionMode3Codec.encode(decoded)));
            }
            JsonNode projection = actual.get("province_observation").get("native_mode3_inputs");
            if (projection != null) {
                assertFalse(projection.get("observed_native_producer_call").booleanValue());
                assertFalse(projection.get("per_building_attribution").booleanValue()); assertFalse(projection.get("realized_holder_net").booleanValue());
                assertEquals("source_software_projection", projection.get("conditional_aggregate_kind").textValue());
            }
        }));
    }

    @Test
    void keepsAbsentNullPartialObservedZeroAndRejectedSourceAsDifferentBranches() throws IOException {
        assertTrue(expected("packet_absent").get("observation").isEmpty());
        assertEquals("observation_unavailable", expected("packet_null").get("observation").get("native_mode3_inputs_status").textValue());
        assertEquals("partial", expected("aggregate_null").get("observation").get("native_mode3_inputs_status").textValue());
        JsonNode zero = expected("observed_zero_aggregate").get("province_observation").get("native_mode3_inputs");
        assertEquals("conditional_projection_available", zero.get("status").textValue()); assertEquals(BigInteger.ZERO, zero.get("inputs").get("conditional_aggregate_raw").bigIntegerValue());
        assertEquals("source_red", expected("reject_claim_per_building_attribution").get("observation").get("native_mode3_inputs_status").textValue());
    }

    @Test
    void doesNotTurnAnotherHoldingIntoAnAttributedBuildingResult() throws IOException {
        JsonNode observation = expected("different_holding_not_attributed").get("province_observation").get("native_mode3_inputs");
        assertEquals("observation_unavailable", observation.get("status").textValue());
        assertEquals("mode3_holding_missing_or_duplicate", observation.get("reason").textValue()); assertTrue(observation.get("inputs").isNull());
        assertFalse(observation.get("realized_holder_net").booleanValue());
    }

    @Test
    void preservesComponentOrderNativeWidthsNullableChildrenAndSdkFractionExtension() throws IOException {
        JsonNode second = expected("actual_second_holding_nullable_child").get("province_observation").get("native_mode3_inputs").get("inputs");
        assertTrue(second.get("child_28b9300_signed_eax").isNull());
        assertEquals(BigInteger.valueOf(Long.MIN_VALUE), expected("signed_q64_boundaries").get("world").get("native_mode3_inputs").get("holdings").get(0).get("inputs").get("factor_before_context").bigIntegerValue());
        assertEquals(StrictJson.UINT64_MAX, expected("unsigned_revision_max").get("world").get("native_mode3_inputs").get("snapshot_revision").bigIntegerValue());
        JsonNode actual = StrictJson.parse(ConstructionMode3Codec.evaluate(utf8(row("sdk_extension_fraction").get("input_json").textValue())));
        assertTrue(actual.get("world").get("unconsumed_extension").get("fraction").isFloatingPointNumber());
        assertEquals(expected("sdk_extension_fraction"), actual);
    }

    @Test
    void rejectsDuplicateWrapperKeysTrailingBytesMalformedUtf8AndOversize() throws IOException {
        String raw = row("actual_conditional_projection").get("input_json").textValue();
        assertThrows(IllegalArgumentException.class, () -> ConstructionMode3Codec.evaluate(utf8(raw + " {}")));
        assertThrows(IllegalArgumentException.class, () -> ConstructionMode3Codec.evaluate(utf8(raw.replace("\"schema\":\"xar.construction-mode3-input.v1\"", "\"schema\":\"xar.construction-mode3-input.v1\",\"schema\":\"duplicate\""))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionMode3Codec.evaluate(new byte[] {(byte) 0xC3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ConstructionMode3Codec.evaluate(new byte[ConstructionMode3Codec.MAX_BYTES + 1]));
        for (String token : List.of("2232.0", "2232e0", "true", "\"2232\"")) {
            assertThrows(IllegalArgumentException.class, () -> ConstructionMode3Codec.evaluate(utf8(raw.replace("\"barony_title_id\":2232,\"province_id\":2619}", "\"barony_title_id\":" + token + ",\"province_id\":2619}"))), token);
        }
    }

    @Test
    void validatesDirectNativeValueObjectsAndDefensiveComponentCopies() throws IOException {
        JsonNode packet = expected("actual_conditional_projection").get("world").get("native_mode3_inputs");
        Packet decoded = ConstructionMode3Codec.decodePacket(StrictJson.canonical(packet));
        assertThrows(UnsupportedOperationException.class, () -> decoded.holdings().clear());
        assertThrows(UnsupportedOperationException.class, () -> decoded.holdings().getFirst().inputs().components().clear());
        assertThrows(IllegalArgumentException.class, () -> new Keys(65536, null, null));
        assertThrows(IllegalArgumentException.class, () -> new Frame(BigInteger.ONE.shiftLeft(64), null, null));
        assertThrows(IllegalArgumentException.class, () -> new Component(0x1_0000_0000L, 0, false, null, ""));
    }

    @Test
    void requiresActualCapturedSourceAndRetainsHistoricalMachineUncertainty() throws IOException {
        JsonNode root = golden();
        assertEquals("xar.construction-mode3-original-producer-golden.v1", root.get("schema").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", root.get("machine_id").textValue()); StrictJson.utc(root.get("observed_at_utc").textValue());
        assertEquals("unknown", root.get("historical_material_machine_id").textValue()); assertEquals(5, root.get("source_refs").size());
        assertEquals("baf8c220d340075c21f1a4cad02fd13a2bb7e6482bf8014410dea4cb520e7c92", root.get("source_refs").get(0).get("sha256").textValue());
        assertEquals("8f218399d19db661e9fccd6ba43b7983ef707e576acd138c30f56998c916fe7b", root.get("source_refs").get(2).get("sha256").textValue());
        assertTrue(root.get("capture_scope").textValue().startsWith("Unchanged actual copied-input normalizer"));
    }

    private static JsonNode row(String name) throws IOException {
        for (JsonNode row : golden().get("cases")) { if (row.get("name").textValue().equals(name)) { return row; } }
        throw new IOException("required original producer case missing: " + name);
    }
    private static JsonNode expected(String name) throws IOException { return row(name).get("expected"); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden() throws IOException {
        try (InputStream resource = ConstructionMode3CodecTest.class.getResourceAsStream("/constructionmode3/original-producer-golden-v1.json.gz")) {
            if (resource == null) { throw new IOException("required actual original producer golden unavailable; no fallback or skip"); }
            try (GZIPInputStream input = new GZIPInputStream(resource)) {
                byte[] bytes = input.readNBytes(524_289); if (bytes.length > 524_288) { throw new IOException("decompressed golden exceeds fixed cap"); }
                return StrictJson.parse(bytes, 524_288);
            }
        }
    }
}
