package org.xar.ck3.control.wave2.military.declarationcontract;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.Choice;

final class DeclarationContractTest {
    @Test
    void originalCatalogueProducerAndLiteralConsumersGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.declarationcontract.original-producer-golden/v1", golden.path("schema").textValue());
        assertTrue(golden.path("source_refs").size() >= 14);
        for (JsonNode sample : golden.path("catalogues")) {
            JsonNode input = parse(sample.get("raw_input_json").textValue());
            JsonNode untouched = input.deepCopy();
            String id = sample.path("id").textValue();
            if (sample.path("expected").path("accepted").booleanValue()) {
                List<Choice> choices = DeclarationContract.normalize(input);
                assertEquals(canonical(sample.path("expected").get("rows")), canonical(DeclarationContract.encode(choices)), id);
                assertEquals(choices, DeclarationContract.normalize(parse(canonical(DeclarationContract.encode(choices)))), id);
                assertThrows(UnsupportedOperationException.class, choices::clear, id);
                for (Choice choice : choices) {
                    assertThrows(UnsupportedOperationException.class, () -> choice.targetTitleIds().clear(), id);
                    assertEquals(choice.declarationId(), DeclarationContract.parseStep(choice.step().wire()).orElseThrow().declarationId(), id);
                    assertTrue(DeclarationContract.isNativeDeclarationStep(choice.step().wire()), id);
                }
            } else assertThrows(IllegalArgumentException.class, () -> DeclarationContract.normalize(input), id);
            assertEquals(untouched, input, "producer mutated source catalogue: " + id);
        }
        for (JsonNode sample : golden.path("literals")) {
            String id = sample.path("id").textValue();
            JsonNode step = parse(sample.get("raw_step_json").textValue());
            var parsed = DeclarationContract.parseStep(step);
            String expectedId = sample.get("expected_parse").isNull() ? null : sample.get("expected_parse").textValue();
            assertEquals(expectedId, parsed.map(DeclarationContract.LiteralStep::declarationId).orElse(null), id);
            assertEquals(sample.get("expected_native").booleanValue(), DeclarationContract.isNativeDeclarationStep(step), id);
            if (sample.has("expected_build")) {
                JsonNode rawId = parse(sample.get("raw_id_json").textValue());
                if (sample.path("expected_build").path("accepted").booleanValue()) {
                    assertEquals(sample.path("expected_build").path("step").textValue(), DeclarationContract.buildStep(rawId.textValue()).wire(), id);
                } else assertThrows(IllegalArgumentException.class, () -> DeclarationContract.buildStep(rawId.isTextual() ? rawId.textValue() : null), id);
            }
        }
    }

    @Test
    void rawTokenBooleanAndFloatRemainDistinctFromActualIntegralIds() {
        for (String value : List.of("true", "808.0", "8.08e2", "\"808\"")) {
            JsonNode input = parse("[{\"declaration_id\":\"808-17-0\",\"target_character_id\":" + value
                    + ",\"casus_belli_index\":17,\"configuration_index\":0,\"claimant_character_id\":-1,\"casus_belli_key\":\"cb\",\"target_title_ids\":[]}]" );
            assertThrows(IllegalArgumentException.class, () -> DeclarationContract.normalize(input), value);
        }
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = DeclarationContractTest.class.getResourceAsStream("/declarationcontract/original-producer-golden01.json")) {
            assertNotNull(input, "committed actual producer golden required"); return StrictJson.parse(input.readAllBytes(), 51_200);
        }
    }
    private static JsonNode parse(String json) { return StrictJson.parse(json.getBytes(StandardCharsets.UTF_8)); }
    private static String canonical(JsonNode value) { return new String(StrictJson.canonical(value), StandardCharsets.UTF_8); }
}
