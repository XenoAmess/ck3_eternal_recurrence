package org.xar.ck3.control.wave2.military.routewindow;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
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
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Available;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Horizon;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.OpposingEdge;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.Route;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy.SameProvince;

final class RouteWindowPolicyTest {
    private static final ObjectMapper WIRE = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);

    private static JsonNode golden() throws IOException {
        try (InputStream input = RouteWindowPolicyTest.class.getResourceAsStream("/routewindow/producer-golden-v1.json")) {
            if (input == null) { throw new IOException("committed actual producer golden required"); }
            return WIRE.readTree(input);
        }
    }
    private static ObjectNode base() throws IOException { return (ObjectNode) golden().get("bases").get("free").deepCopy(); }
    private static byte[] bytes(JsonNode value) throws IOException { return WIRE.writeValueAsBytes(value); }

    @TestFactory Stream<DynamicTest> actualProducerCases() throws IOException {
        JsonNode fixture = golden();
        assertEquals("xar.route-window-producer-golden/v1", fixture.get("schema").textValue());
        assertTrue(fixture.get("cases").size() >= 60);
        return java.util.stream.StreamSupport.stream(fixture.get("cases").spliterator(), false).map(item ->
                DynamicTest.dynamicTest(item.get("name").textValue(), () -> {
                    ObjectNode input = (ObjectNode) fixture.get("bases").get(item.get("base").textValue()).deepCopy();
                    for (JsonNode patch : item.get("patches")) { apply(input, patch); }
                    assertEquals(item.get("expected"), StrictJson.parse(RouteWindowCodec.project(bytes(input))));
                }));
    }
    private static void apply(ObjectNode input, JsonNode patch) {
        JsonNode path = patch.get("path"); JsonNode target = input;
        for (int index = 0; index < path.size() - 1; index++) {
            JsonNode segment = path.get(index); target = segment.isIntegralNumber() ? target.get(segment.intValue()) : target.get(segment.textValue());
        }
        JsonNode key = path.get(path.size() - 1);
        if (target instanceof ObjectNode object) {
            if (patch.get("op").textValue().equals("remove")) { object.remove(key.textValue()); }
            else { object.set(key.textValue(), patch.get("value").deepCopy()); }
        } else if (target instanceof ArrayNode array && key.isIntegralNumber()) {
            if (patch.get("op").textValue().equals("remove")) { array.remove(key.intValue()); }
            else { array.set(key.intValue(), patch.get("value").deepCopy()); }
        } else { throw new IllegalArgumentException("invalid frozen input patch"); }
    }

    @Test void directDomainClosedBoundariesRoundOutwardAtOneRawUnit() {
        for (int offset : List.of(0, 1, 23, 24, 25, 47, 48, 49, 71, 72, 73)) {
            Available output = RouteWindowPolicy.project(new Horizon(1000, 3,
                    new Route(11, 20, List.of(), List.of()), new java.util.ArrayList<>(List.of(
                            new Route(21, 99, List.of(20), List.of(1000 + offset))))));
            assertEquals(offset > 72, output.contactFree());
            assertEquals(offset > 72 ? 3 : Math.max(0, Math.floorDiv(offset - 1, 24)), output.contactFreeWholeDays());
        }
    }

    @Test void reverseEdgeConflictDoesNotRequireObservedArrival() {
        Available projection = RouteWindowPolicy.project(new Horizon(1000, 3,
                new Route(11, 20, List.of(31), List.of(1120)),
                List.of(new Route(21, 31, List.of(20), List.of(1121)))));
        assertEquals(List.of(new OpposingEdge(21, 20, 31, 31, 20, 1000, 1072)), projection.conflicts());
        assertEquals(0, projection.contactFreeWholeDays()); assertFalse(projection.contactFree());
    }

    @Test void publicUnitZeroAndSignedNativeClockArePreserved() {
        Available projection = RouteWindowPolicy.project(new Horizon(Integer.MIN_VALUE, 1,
                new Route(0, 20, List.of(), List.of()), List.of(new Route(1, 20, List.of(), List.of()))));
        assertEquals(Integer.valueOf(Integer.MIN_VALUE), projection.firstContactDateRaw());
        assertEquals(new SameProvince(1, 20, Integer.MIN_VALUE, Integer.MIN_VALUE + 24), projection.conflicts().getFirst());
    }

    @Test void typedRoutesRetainInputOrderAndCannotBeMutated() {
        Route subject = new Route(11, 20, List.of(31, 20), List.of(1001, 1002));
        assertEquals(List.of(31, 20), subject.provinceIds());
        assertThrows(UnsupportedOperationException.class, () -> subject.arrivalDateRaws().add(1003));
        assertThrows(ContractViolationException.class, () -> new Route(11, 20, List.of(31, 20), List.of(1002, 1001)));
    }

    @Test void horizonIntegerTokenGuardReceivesOriginalFloat() throws IOException {
        for (String token : List.of("true", "3.0", "\"3\"", "0", "4", "null")) {
            ObjectNode input = base(); input.set("horizon_days", WIRE.readTree(token)); byte[] raw = bytes(input);
            assertTrue(new String(raw, StandardCharsets.UTF_8).contains("\"horizon_days\":" + token));
            assertThrows(ContractViolationException.class, () -> RouteWindowCodec.project(raw));
        }
    }

    @Test void timelineFloatBooleanAndOverflowRemainUnavailable() throws IOException {
        for (String token : List.of("true", "24000.0", "2147483648", "null")) {
            ObjectNode input = base(); ((ObjectNode) input.get("horizon")).set("date_raw", WIRE.readTree(token));
            JsonNode result = StrictJson.parse(RouteWindowCodec.project(bytes(input)));
            assertEquals("unavailable", result.get("status").textValue()); assertTrue(result.get("window_start_date_raw").isNull());
            assertEquals("date_raw", result.get("missing").get(0).textValue());
        }
    }

    @Test void jsonBoundaryRejectsUnknownWrapperDuplicateAndInvalidUtf8() throws IOException {
        ObjectNode input = base(); input.put("alias", true); byte[] unknown = bytes(input);
        assertThrows(ContractViolationException.class, () -> RouteWindowCodec.project(unknown));
        assertThrows(ContractViolationException.class, () -> RouteWindowCodec.project(
                "{\"horizon_days\":3,\"horizon_days\":2,\"horizon\":{}}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> RouteWindowCodec.project(new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test void clockOverflowAndBadTypedResultsCannotInventAWindow() {
        assertThrows(ContractViolationException.class, () -> new Horizon(Integer.MAX_VALUE - 23, 1,
                new Route(11, 20, List.of(), List.of()), List.of(new Route(21, 99, List.of(), List.of()))));
        assertThrows(ContractViolationException.class, () -> new Available(3, 1000, 1072,
                List.of(new SameProvince(21, 20, 1024, 1072)), 1024, 1));
    }
}
