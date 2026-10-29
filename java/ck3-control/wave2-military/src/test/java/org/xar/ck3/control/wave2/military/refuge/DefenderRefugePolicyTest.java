package org.xar.ck3.control.wave2.military.refuge;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Assessment;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Request;

final class DefenderRefugePolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream input = DefenderRefugePolicyTest.class.getResourceAsStream("/refuge/original-producer-golden-v1.json")) {
            assertNotNull(input, "committed original producer golden required; absence is RED");
            return StrictJson.parse(input.readNBytes(71_681), 71_680);
        }
    }

    private static ObjectNode base(String name) throws IOException {
        return base(golden(), name);
    }
    private static ObjectNode base(JsonNode fixture, String name) {
        for (JsonNode row : fixture.get("bases")) {
            if (row.get("name").textValue().equals(name)) { return row.get("request").deepCopy(); }
        }
        throw new IllegalStateException("required historical projection absent: " + name);
    }

    /** This local test-data operation never touches files, live state, or an application command. */
    private static ObjectNode applyVector(JsonNode fixture, JsonNode vector) {
        ObjectNode request = base(fixture, vector.get("base").textValue());
        for (JsonNode operation : vector.get("patches")) {
            JsonNode path = operation.get("path"); JsonNode parent = request;
            assertTrue(path.isArray() && !path.isEmpty());
            for (int index = 0; index < path.size() - 1; index++) {
                String key = path.get(index).textValue();
                parent = parent.isArray() ? parent.get(Integer.parseInt(key)) : parent.get(key);
                assertNotNull(parent, "frozen local test path must exist");
            }
            String key = path.get(path.size() - 1).textValue(); String kind = operation.get("operation").textValue();
            if (parent instanceof ObjectNode object) {
                if (kind.equals("remove")) { object.remove(key); }
                else { assertEquals("set", kind); object.set(key, operation.get("value").deepCopy()); }
            } else if (parent instanceof ArrayNode array) {
                if (kind.equals("remove")) { array.remove(Integer.parseInt(key)); }
                else { assertEquals("set", kind); array.set(Integer.parseInt(key), operation.get("value").deepCopy()); }
            } else { throw new IllegalArgumentException("frozen test patch parent must be a container"); }
        }
        return request;
    }

    @TestFactory
    Stream<DynamicTest> unchangedThreeProducersOnActualHistoryAndExplicitVariants() throws IOException {
        JsonNode fixture = golden(); assertFalse(fixture.get("actual_live_qualification").booleanValue());
        assertEquals(2, fixture.get("bases").size()); assertEquals(36, fixture.get("cases").size());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : fixture.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                byte[] raw = StrictJson.canonical(applyVector(fixture, vector)); Request request = DefenderRefugeCodec.decode(raw);
                assertEquals(vector.get("expected"), StrictJson.parse(DefenderRefugeCodec.evaluate(raw)));
                Request roundTrip = DefenderRefugeCodec.decode(DefenderRefugeCodec.encodeRequest(request));
                assertEquals(request, roundTrip); assertEquals(DefenderRefugePolicy.assess(request), DefenderRefugePolicy.assess(roundTrip));
            }));
        }
        return tests.stream();
    }

    @Test
    void originalCapitalOrderAndArrivalContinuationRemainExact() throws IOException {
        Assessment initial = DefenderRefugePolicy.assess(DefenderRefugeCodec.decode(StrictJson.canonical(base("initial"))));
        assertEquals(List.of(2604, 2610, 2614, 2623, 2628, 2631, 8755), initial.directVassalCapitalProvinceIds());
        assertNotNull(initial.lifecycleScope()); assertEquals(2619, initial.lifecycleScope().ownCapitalProvinceId());
        assertEquals(DefenderRefugePolicy.CurrentKind.DIRECTLY_HELD_CAPITAL, initial.lifecycleScope().currentKind());
        Assessment arrived = DefenderRefugePolicy.assess(DefenderRefugeCodec.decode(StrictJson.canonical(base("arrived"))));
        assertNotNull(arrived.lifecycleScope()); assertEquals(2604, arrived.lifecycleScope().currentProvinceId());
        assertEquals(DefenderRefugePolicy.CurrentKind.DIRECT_VASSAL_CAPITAL, arrived.lifecycleScope().currentKind());
        assertEquals(List.of(2610, 2614, 2623, 2628, 2631, 8755, 2619), arrived.lifecycleScope().candidateProvinceIds());
        assertEquals(arrived.lifecycleScope(), arrived.sameFrameCachedScope());
    }

    @Test
    void observedEmptyCapitalSetIsDistinctFromUnavailableNull() throws IOException {
        ObjectNode request = base("initial"); ObjectNode root = (ObjectNode) request.get("root");
        root.putArray("direct_landed_vassal_character_ids"); ArrayNode rows = root.putArray("related_character_contexts");
        assertEquals(0, rows.size());
        Assessment observedEmpty = DefenderRefugePolicy.assess(DefenderRefugeCodec.decode(StrictJson.canonical(request)));
        assertEquals(List.of(), observedEmpty.directVassalCapitalProvinceIds()); assertNull(observedEmpty.lifecycleScope());
        root.putNull("direct_landed_vassal_character_ids");
        assertNull(DefenderRefugePolicy.assess(DefenderRefugeCodec.decode(StrictJson.canonical(request))).directVassalCapitalProvinceIds());
    }

    @Test
    void everyCacheBindingFieldMustBePresentTypedAndCurrent() throws IOException {
        for (String field : List.of("snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation")) {
            ObjectNode request = base("initial"); ObjectNode binding = (ObjectNode) request.get("cached_query").get("cache_binding");
            binding.remove(field);
            assertThrows(IllegalArgumentException.class, () -> DefenderRefugeCodec.decode(StrictJson.canonical(request)), field);
        }
        ObjectNode stale = base("initial"); ((ObjectNode) stale.get("cached_query").get("cache_binding")).put("bridge_pid", 1);
        Assessment result = DefenderRefugePolicy.assess(DefenderRefugeCodec.decode(StrictJson.canonical(stale)));
        assertNotNull(result.lifecycleScope()); assertNull(result.sameFrameCachedScope());
    }

    @Test
    void wrongRawNumericTokensReachDecoderWithoutTreeCoercion() throws IOException {
        String canonical = new String(StrictJson.canonical(base("initial")), StandardCharsets.UTF_8);
        for (String field : List.of("revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation",
                "snapshot_revision", "player_character_id", "top_liege_character_id", "character_id", "capital_province_id", "tier_raw", "army_id")) {
            Matcher token = Pattern.compile("\"" + field + "\":(-?[0-9]+)").matcher(canonical);
            assertTrue(token.find(), field); int start = token.start(1), end = token.end(1);
            String value = canonical.substring(start, end); assertFalse(value.isEmpty(), field);
            for (String replacement : List.of("true", value + ".0", "\"" + value + "\"")) {
                byte[] raw = (canonical.substring(0, start) + replacement + canonical.substring(end)).getBytes(StandardCharsets.UTF_8);
                assertThrows(IllegalArgumentException.class, () -> DefenderRefugeCodec.decode(raw), field + "=" + replacement);
            }
        }
    }

    @Test
    void currentUnknownMoveIntentNeverCreatesRefugeScope() throws IOException {
        ObjectNode request = base("initial"); ObjectNode army = (ObjectNode) request.get("snapshot").get("player_armies").get(0);
        army.put("move_target_province_id", 2604); army.putArray("route_province_ids").add(2604);
        Assessment result = DefenderRefugePolicy.assess(DefenderRefugeCodec.decode(StrictJson.canonical(request)));
        assertNull(result.lifecycleScope()); assertNull(result.sameFrameCachedScope());
        assertNotNull(result.directVassalCapitalProvinceIds());
    }

    @Test
    void schemaRejectsMissingAndUnknownWrapperButPreservesSdkExtensions() throws IOException {
        ObjectNode extra = base("initial"); extra.put("verified_native", true);
        assertThrows(IllegalArgumentException.class, () -> DefenderRefugeCodec.decode(StrictJson.canonical(extra)));
        ObjectNode missing = base("initial"); missing.remove("root");
        assertThrows(IllegalArgumentException.class, () -> DefenderRefugeCodec.decode(StrictJson.canonical(missing)));
        ObjectNode extension = base("initial"); ((ObjectNode) extension.get("root")).putObject("future_sdk_domain").put("key", "value");
        assertNotNull(DefenderRefugePolicy.assess(DefenderRefugeCodec.decode(StrictJson.canonical(extension))).lifecycleScope());
        assertThrows(IllegalArgumentException.class, () -> DefenderRefugeCodec.decode("{\"schema\":1,\"schema\":1}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> DefenderRefugeCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> DefenderRefugeCodec.decode(new byte[65_537]));
    }
}
