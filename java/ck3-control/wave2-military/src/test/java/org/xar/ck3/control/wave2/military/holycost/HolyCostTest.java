package org.xar.ck3.control.wave2.military.holycost;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.KnownQuote;

final class HolyCostTest {
    @Test
    void realOriginalNormalizerIncludingDeclaredStrictExpectationTypeHardening() throws IOException {
        JsonNode golden = golden();
        int originalParity = 0;
        int hardenings = 0;
        for (JsonNode sample : golden.path("cases")) {
            ObjectNode request = golden.path("base").deepCopy();
            for (JsonNode edit : sample.path("edits")) apply(request, edit);
            ObjectNode original = request.deepCopy();
            String id = sample.path("id").textValue();
            if (!sample.path("expected").path("java_accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> evaluate(request, sample.path("mode").textValue()), id);
            } else {
                assertEquals(canonical(sample.path("expected").get("output")), canonical(evaluate(request, sample.path("mode").textValue())), id);
                if (sample.path("mode").textValue().equals("normalize")) {
                    HolyCostObservation observation = normalize(request);
                    request.set("context", StrictJson.parse(StrictJson.canonical(HolyCostJsonAdapter.encode(observation))));
                    assertEquals(observation, normalize(request), "typed round trip " + id);
                    assertEquals(HolyCostObservation.TotalCost.UNKNOWN, observation.totalCost());
                    if (observation.cbCost() instanceof KnownQuote known) {
                        assertThrows(UnsupportedOperationException.class, () -> known.resourceCostsRaw().clear());
                    }
                    request.set("context", original.get("context"));
                }
            }
            assertEquals(original, request, "original boundary mutated input " + id);
            if (sample.path("strict_expectation_type_hardening").booleanValue()) {
                assertTrue(sample.path("expected").path("original_accepted").booleanValue()); hardenings++;
            } else originalParity++;
        }
        assertTrue(originalParity >= 70); assertEquals(4, hardenings);
    }

    @Test
    void enrichedQueryIsDeclaredProjectionThenFullValidation() throws IOException {
        ObjectNode request = golden().path("base").deepCopy();
        HolyCostObservation before = normalize(request);
        ObjectNode enriched = request.get("context").deepCopy();
        enriched.put("query_status", "observed").put("backend_id", "explicit-existing-container-extension");
        enriched.putObject("player_holy_war_defender_join_inputs").put("native_joiner_set_observed", true);
        assertThrows(IllegalArgumentException.class, () -> HolyCostJsonAdapter.normalize(enriched, request.get("snapshot"),
                request.get("declaration_id").textValue(), request.get("selected")));
        assertEquals(before, HolyCostJsonAdapter.normalize(HolyCostJsonAdapter.projectCore(enriched), request.get("snapshot"),
                request.get("declaration_id").textValue(), request.get("selected")));
        enriched.set("capture_epoch", StrictJson.parse("1007.0".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> HolyCostJsonAdapter.normalize(HolyCostJsonAdapter.projectCore(enriched), request.get("snapshot"),
                request.get("declaration_id").textValue(), request.get("selected")));
    }

    private static HolyCostObservation normalize(ObjectNode request) {
        return HolyCostJsonAdapter.normalize(request.get("context"), request.get("snapshot"), request.get("declaration_id").textValue(), request.get("selected"));
    }
    private static ObjectNode evaluate(ObjectNode request, String mode) {
        if (mode.equals("select")) return HolyCostJsonAdapter.selectedJson(HolyCostJsonAdapter.selectedDeclaration(request.get("snapshot"), request.get("declaration_id").textValue()));
        return HolyCostJsonAdapter.encode(normalize(request));
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = HolyCostTest.class.getResourceAsStream("/holycost/original-producer-golden01.json")) {
            assertNotNull(input, "committed real original producer golden required"); return StrictJson.parse(input.readAllBytes(), 65_536);
        }
    }
    private static String canonical(JsonNode value) { return new String(StrictJson.canonical(value), StandardCharsets.UTF_8); }
    private static void apply(ObjectNode request, JsonNode edit) {
        JsonNode path = edit.get("path"); JsonNode parent = request;
        for (int index = 0; index < path.size() - 1; index++) {
            JsonNode key = path.get(index); parent = key.isTextual() ? parent.get(key.textValue()) : parent.get(key.intValue());
        }
        JsonNode key = path.get(path.size() - 1);
        if (edit.path("remove").asBoolean()) {
            if (parent instanceof ObjectNode object) object.remove(key.textValue()); else ((ArrayNode) parent).remove(key.intValue());
        } else {
            JsonNode value = StrictJson.parse(edit.get("value_json").textValue().getBytes(StandardCharsets.UTF_8));
            if (parent instanceof ObjectNode object) object.set(key.textValue(), value); else ((ArrayNode) parent).set(key.intValue(), value);
        }
    }
}
