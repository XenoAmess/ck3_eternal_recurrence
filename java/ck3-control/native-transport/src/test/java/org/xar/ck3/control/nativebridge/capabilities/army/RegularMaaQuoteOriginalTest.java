package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.*;

/** Retained C++ production collector/serializer outputs. Their callback costs are fixture observations, not live prices. */
class RegularMaaQuoteOriginalTest {
    private static JsonNode fixture() throws IOException {
        try(var input=RegularMaaQuoteOriginalTest.class.getResourceAsStream("/maa/retained-native-recruitment-wire.json")) {
            assertNotNull(input,"mandatory retained C++ production quote output");return StrictJson.parse(input.readAllBytes());
        }
    }
    private static ObjectNode block(JsonNode data,int scenario) {
        return (ObjectNode)data.path("cases").get(scenario).path("rows").get(0).get("native_maa_recruitment_inputs_v1");
    }
    @Test void actualTwoNativeQuoteCasesKeepOrderFalseUnknownTenSignedSlotsAndRoundtrip() throws IOException {
        var data=fixture();assertEquals(2,data.path("bounded_cases").intValue());
        var allowed=ArmyStrengthsMonthlyCodec.decodeMaa(block(data,0));var denied=ArmyStrengthsMonthlyCodec.decodeMaa(block(data,1));
        assertEquals(List.of("mangonel","onager"),allowed.types().stream().map(MaaType::typeKey).toList());
        assertEquals(List.of(7,4),allowed.types().stream().map(MaaType::typeIndex).toList());
        assertEquals(List.of(125000L,0L,750000L,0L,0L,0L,0L,910000L,-25000L,0L),allowed.types().getFirst().quote().resourcesRaw().orElseThrow());
        assertEquals(Optional.of(false),denied.types().getFirst().canCreate());assertTrue(denied.types().getFirst().inputsReady());
        assertTrue(denied.types().getLast().quote().resourcesRaw().isEmpty());assertFalse(denied.types().getLast().inputsReady());
        for(int scenario=0;scenario<2;scenario++) {
            var original=block(data,scenario);var typed=ArmyStrengthsMonthlyCodec.decodeMaa(original);
            assertEquals(original,ArmyStrengthsMonthlyCodec.encodeMaa(typed));
            assertEquals(typed,ArmyStrengthsMonthlyCodec.decodeMaa(StrictJson.parse(StrictJson.canonical(ArmyStrengthsMonthlyCodec.encodeMaa(typed)))));
            assertEquals(typed,ArmyStrengthsMonthlyCodec.decodeMaa(data.path("cases").get(scenario).path("rows").get(1).get("native_maa_recruitment_inputs_v1")));
        }
    }
    @Test void actualQuoteDecoderRejectsWrongBooleanMissingCostsAndWrongIntegerType() throws IOException {
        var original=block(fixture(),0);
        var numeric=original.deepCopy();((ObjectNode)numeric.path("types_in_native_order").get(0)).put("can_create",1);
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsMonthlyCodec.decodeMaa(numeric));
        var missing=original.deepCopy();((ObjectNode)missing.path("types_in_native_order").get(0).get("regular_personal_quote")).remove("resources_raw");
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsMonthlyCodec.decodeMaa(missing));
        var floating=original.deepCopy();((ObjectNode)floating.path("types_in_native_order").get(0)).put("type_index",7.0);
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsMonthlyCodec.decodeMaa(floating));
        var shortSlots=original.deepCopy();((ObjectNode)shortSlots.path("types_in_native_order").get(0).get("regular_personal_quote")).putArray("resources_raw").add(1);
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsMonthlyCodec.decodeMaa(shortSlots));
    }
}
