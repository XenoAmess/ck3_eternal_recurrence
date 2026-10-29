package org.xar.ck3.control.wave2.military.routewindowstep;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class RouteWindowStepTest {
    private static final ObjectMapper WIRE = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);

    @TestFactory Stream<DynamicTest> actualProducerConstructorAndParserCases() throws IOException {
        JsonNode fixture;
        try (InputStream input = RouteWindowStepTest.class.getResourceAsStream("/routewindowstep/producer-golden-v1.json")) {
            if (input == null) { throw new IOException("committed actual producer golden required"); }
            fixture = WIRE.readTree(input);
        }
        assertEquals("xar.route-window-step-producer-golden/v1", fixture.get("schema").textValue());
        assertTrue(fixture.get("cases").size() >= 60);
        return java.util.stream.StreamSupport.stream(fixture.get("cases").spliterator(), false).map(item ->
                DynamicTest.dynamicTest(item.get("name").textValue(), () -> {
                    byte[] input = WIRE.writeValueAsBytes(item.get("input"));
                    if (item.get("expected").has("error")) {
                        assertThrows(ContractViolationException.class, () -> RouteWindowStepCodec.execute(input));
                    } else { assertEquals(item.get("expected"), StrictJson.parse(RouteWindowStepCodec.execute(input))); }
                }));
    }

    @Test void canonicalBuilderSortsAndDeduplicatesOnlyHostileScope() {
        RouteWindowStep step = new RouteWindowStep(0, 31, List.of(22, 21, 22), 3);
        assertEquals(List.of(21, 22), step.hostileArmyIds());
        assertEquals("advance-route-contact-window-v1-0-to-31-days-3-h-2-21-22", step.canonical());
        assertEquals(step, RouteWindowStep.parse(step.canonical()).orElseThrow());
        assertThrows(UnsupportedOperationException.class, () -> step.hostileArmyIds().add(23));
    }

    @Test void limitsApplyAfterDeduplicationAndKeepPublicSlotZero() {
        List<Integer> repeated = java.util.Collections.nCopies(1000, 0);
        assertEquals(List.of(0), new RouteWindowStep(11, 31, repeated, 2).hostileArmyIds());
        assertThrows(ContractViolationException.class, () -> new RouteWindowStep(0, 31, List.of(0), 2));
        assertThrows(ContractViolationException.class, () -> new RouteWindowStep(11, 31,
                java.util.stream.IntStream.range(100, 165).boxed().toList(), 2));
    }

    @Test void parserRejectsExtremelyLargeTokensWithoutIntegerOverflow() {
        String input = "advance-route-contact-window-v1-" + "9".repeat(5000) + "-to-31-days-3-h-1-21";
        assertTrue(RouteWindowStep.parse(input).isEmpty());
        assertTrue(RouteWindowStep.parse(null).isEmpty());
    }

    @Test void directRawFloatingIdentityAndDayTokensReachActualDecoder() {
        String base = "{\"operation\":\"build\",\"subject_army_id\":11,\"target_province_id\":31,\"hostile_army_ids\":[21],\"horizon_days\":3}";
        for (String input : List.of(base.replace("\"subject_army_id\":11", "\"subject_army_id\":11.0"),
                base.replace("\"horizon_days\":3", "\"horizon_days\":3.0"),
                base.replace("\"hostile_army_ids\":[21]", "\"hostile_army_ids\":[21.0]"))) {
            assertThrows(ContractViolationException.class, () -> RouteWindowStepCodec.execute(input.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test void parserRoundTripWireRetainsTupleArrayRepresentation() {
        String request = "{\"operation\":\"parse\",\"step\":\"advance-route-contact-window-v1-11-to-31-days-2-h-2-0-21\"}";
        JsonNode result = StrictJson.parse(RouteWindowStepCodec.execute(request.getBytes(StandardCharsets.UTF_8)));
        assertEquals(11, result.get("parsed").get(0).intValue());
        assertEquals(0, result.get("parsed").get(2).get(0).intValue());
        assertEquals(2, result.get("parsed").get(3).intValue());
    }

    @Test void newWrapperRejectsUnknownAndDuplicateFields() {
        assertThrows(ContractViolationException.class, () -> RouteWindowStepCodec.execute(
                "{\"operation\":\"parse\",\"step\":null,\"alias\":true}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> RouteWindowStepCodec.execute(
                "{\"operation\":\"parse\",\"step\":null,\"step\":true}".getBytes(StandardCharsets.UTF_8)));
    }
}
