package org.xar.ck3.control.wave2.military.sharedwire;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class ArmyManagerSharedWireTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String OWN = ArmyManagerSharedWire.Family.COMBAT_ROLES_PHASE.wireName();
    private static JsonNode golden() throws IOException {
        try (InputStream resource = ArmyManagerSharedWireTest.class.getResourceAsStream("/sharedwire/original-producer-golden.json.gz")) {
            assertNotNull(resource, "original pure producer golden required; absence cannot become a skipped pass");
            try (GZIPInputStream input = new GZIPInputStream(resource)) {
                byte[] raw = input.readNBytes(262145); assertTrue(raw.length <= 262144); return StrictJson.parse(raw, 262144);
            }
        }
    }
    private static JsonNode scene(JsonNode golden, String name) {
        for (JsonNode sample : golden.get("cases")) if (sample.get("name").textValue().equals(name)) return sample;
        fail("required original producer case missing: " + name); return StrictJson.object();
    }
    private static void sameTokens(JsonNode expected, JsonNode actual) throws IOException {
        // Transport accepts opaque floating nodes. Shared map's integer-only canonical emitter is intentionally not used.
        assertEquals(StrictJson.parse(JSON.writeValueAsBytes(expected)), StrictJson.parse(JSON.writeValueAsBytes(actual)));
    }
    @Test void unchangedOriginalProducerAndAllTransportConsumersAgreeForValidTokenDomain() throws IOException {
        JsonNode golden = golden(); assertFalse(golden.get("actual_live_qualification").booleanValue());
        assertFalse(golden.get("machine_id").textValue().isEmpty()); assertFalse(golden.get("source_bindings").isEmpty());
        for (JsonNode sample : golden.get("cases")) {
            if (!sample.path("valid_token_domain").booleanValue()) continue;
            ObjectNode input = sample.get("input").deepCopy(); JsonNode before = input.deepCopy();
            ObjectNode packed = ArmyManagerSharedWire.pack(input);
            sameTokens(sample.get("expected_packed"), packed); sameTokens(before, input);
            assertEquals(sample.get("pack_returned_original_object").booleanValue(), packed == input, sample.get("name").textValue());
            if (sample.has("expected_expanded")) {
                sameTokens(sample.get("expected_expanded"), ArmyManagerSharedWire.expand(packed, true));
                sameTokens(sample.get("expected_expanded"), ArmyManagerSharedWire.expand(packed, false));
            }
        }
        for (JsonNode rejection : golden.get("rejections")) {
            assertThrows(ContractViolationException.class, () -> ArmyManagerSharedWire.expand((ObjectNode) rejection.get("input"), true),
                    rejection.get("name").textValue());
        }
    }
    @Test void originalPythonEqualityCannotHideMalformedBooleanOrFloatTokens() throws IOException {
        JsonNode golden = golden();
        for (String name : List.of("historical_python_equal_bool", "historical_python_equal_float")) {
            JsonNode sample = scene(golden, name); ObjectNode input = sample.get("input").deepCopy();
            assertTrue(sample.path("expected_packed").has(ArmyManagerSharedWire.SHARED_KEY), "historical Python masking remains recorded");
            assertFalse(sample.path("valid_token_domain").booleanValue());
            assertSame(input, ArmyManagerSharedWire.pack(input), "malformed distinct token must remain in its own row for strict family validation");
            JsonNode originalSecondToken = sample.path("input").path("army_strengths").get(1).path(OWN).path("same_python_value");
            JsonNode actualSecondToken = input.path("army_strengths").get(1).path(OWN).path("same_python_value");
            assertEquals(originalSecondToken.getNodeType(), actualSecondToken.getNodeType());
            if (name.endsWith("float")) assertTrue(actualSecondToken.isFloatingPointNumber()); else assertTrue(actualSecondToken.isBoolean());
        }
    }
    @Test void realDriverSharesSourceObjectsWhileDetachedExternalRowsAreIndependent() throws IOException {
        ObjectNode original = (ObjectNode) scene(golden(), "all_ten_families").get("input").deepCopy();
        ObjectNode packed = ArmyManagerSharedWire.pack(original); ObjectNode before = packed.deepCopy();
        ArmyManagerSharedWire.BundleView view = ArmyManagerSharedWire.inspectBundle(packed);
        assertEquals(List.of(new ArmyManagerSharedWire.PublicCUnitId(0), new ArmyManagerSharedWire.PublicCUnitId(17)), view.armyIds());
        assertEquals(10, view.families().size());
        assertThrows(UnsupportedOperationException.class, () -> view.families().clear());
        ObjectNode driver = ArmyManagerSharedWire.expand(packed, false);
        assertSame(driver.path("army_strengths").get(0).get(OWN), driver.path("army_strengths").get(1).get(OWN));
        assertSame(packed.path(ArmyManagerSharedWire.SHARED_KEY).path("fields").get(OWN), driver.path("army_strengths").get(0).get(OWN));
        ObjectNode detached = ArmyManagerSharedWire.expand(packed, true);
        ObjectNode first = (ObjectNode) detached.path("army_strengths").get(0).get(OWN);
        ObjectNode second = (ObjectNode) detached.path("army_strengths").get(1).get(OWN);
        assertNotSame(first, second); first.put("external_mutation", true);
        assertFalse(second.has("external_mutation")); sameTokens(before, packed);
    }
    @Test void baseAdmissionAndAdditionalIndependentHoistingUseOriginalFamilyOrder() throws IOException {
        JsonNode golden = golden();
        ObjectNode noBase = (ObjectNode) scene(golden, "only_additional_no_base").get("input").deepCopy();
        assertSame(noBase, ArmyManagerSharedWire.pack(noBase));
        ObjectNode divergent = (ObjectNode) scene(golden, "divergent_additional_retains_inline").get("input").deepCopy();
        ObjectNode packed = ArmyManagerSharedWire.pack(divergent);
        assertTrue(packed.path("army_strengths").get(0).has(ArmyManagerSharedWire.Family.FLAG20.wireName()));
        assertFalse(packed.path(ArmyManagerSharedWire.SHARED_KEY).path("fields").has(ArmyManagerSharedWire.Family.FLAG20.wireName()));
        assertTrue(packed.path(ArmyManagerSharedWire.SHARED_KEY).path("fields").has(ArmyManagerSharedWire.Family.FLAG21.wireName()));
        ObjectNode zero = (ObjectNode) scene(golden, "known_null_family").get("expected_packed").deepCopy();
        assertTrue(zero.path(ArmyManagerSharedWire.SHARED_KEY).path("fields").get(OWN).isNull());
        assertEquals(0, ArmyManagerSharedWire.inspectBundle(zero).armyIds().get(0).value());
    }
    @Test void duplicateRawKeysFloatVersionAndInvalidPublicIdsFailBeforeExpansion() throws IOException {
        ObjectNode packed = (ObjectNode) scene(golden(), "all_six_base_families").get("expected_packed").deepCopy();
        String raw = JSON.writeValueAsString(packed);
        String duplicated = raw.replace("\"schema_version\":1", "\"schema_version\":1,\"schema_version\":1");
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(duplicated.getBytes(StandardCharsets.UTF_8)));
        for (String token : List.of("true", "1.0", "1e0", "\"1\"")) {
            byte[] mutated = raw.replace("\"schema_version\":1", "\"schema_version\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class, () -> ArmyManagerSharedWire.expand((ObjectNode) StrictJson.parse(mutated), false));
        }
        assertThrows(ContractViolationException.class, () -> new ArmyManagerSharedWire.PublicCUnitId(-1));
        ObjectNode emptyFields = packed.deepCopy(); ((ObjectNode) emptyFields.path(ArmyManagerSharedWire.SHARED_KEY)).set("fields", StrictJson.object());
        assertThrows(ContractViolationException.class, () -> ArmyManagerSharedWire.inspectBundle(emptyFields));
        ObjectNode opaqueFloat = StrictJson.object(); opaqueFloat.put("army_id", 0); opaqueFloat.put("another_extension", 1.0);
        ObjectNode inline = StrictJson.object(); ArrayNode rows = inline.putArray("army_strengths"); rows.add(opaqueFloat);
        assertSame(inline, ArmyManagerSharedWire.expand(inline, false));
        assertTrue(ArmyManagerSharedWire.expand(inline, true).path("army_strengths").get(0).path("another_extension").isFloatingPointNumber());
    }
}
