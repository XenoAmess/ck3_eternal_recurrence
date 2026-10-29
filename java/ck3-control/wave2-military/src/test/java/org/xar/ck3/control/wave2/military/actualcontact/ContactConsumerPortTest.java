package org.xar.ck3.control.wave2.military.actualcontact;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.actualcontact.ContactConsumerPort.Operation;
import org.xar.ck3.control.wave2.military.actualcontact.ContactConsumerPort.Request;
import org.xar.ck3.control.wave2.military.actualcontact.ContactConsumerPort.Result;

/** Default Java seam regressions; the compiled original-consumer probe is a separate required CI step. */
final class ContactConsumerPortTest {
    private static JsonNode fixture(String name) throws IOException {
        try (InputStream stream = ContactConsumerPortTest.class.getResourceAsStream("/" + name + "/producer-golden-v1.json")) {
            assertNotNull(stream, "mandatory original producer golden: " + name);
            return StrictJson.parse(stream.readNBytes(65_537));
        }
    }
    private static String json(JsonNode value) { return new String(StrictJson.canonical(value), StandardCharsets.UTF_8); }
    private static JsonNode apply(Operation operation, String input) {
        return StrictJson.parse(ContactConsumerPort.apply(new Request(operation, input.getBytes(StandardCharsets.UTF_8))).utf8());
    }

    @Test void actualNativeMailboxOutputRetainsFalseAuthorizationAndArrayRepresentation() throws IOException {
        JsonNode input = fixture("armyinventory").path("bases").path("mailbox");
        JsonNode output = apply(Operation.INVENTORY, json(input));
        assertTrue(output.path("valid").booleanValue());
        assertEquals("shape_valid_only", output.path("reason").textValue());
        assertFalse(output.path("date_or_action_authorized").booleanValue());
        assertTrue(output.path("hostile_army_ids").isArray());
        assertEquals(output.get("hostile_army_ids"), output.get("contact_hostile_army_ids"));
        ObjectNode changed = input.deepCopy(); ((ObjectNode) changed.get("current")).put("future_supported", true);
        assertEquals("capability_frame_changed", apply(Operation.INVENTORY, json(changed)).path("reason").textValue());
        assertEquals(output, apply(Operation.INVENTORY, json(input)), "caller-owned starting/current inputs must stay unchanged");
    }

    @Test void actualScopeNativeRevisionCannotBeReplacedWithPublicWrapperRevision() throws IOException {
        ObjectNode input = fixture("actualcontact").path("bases").path("new_attacker").deepCopy();
        JsonNode output = apply(Operation.ACTUAL_SCOPE, json(input));
        assertEquals(input.get("scope"), output);
        ((ObjectNode) input.get("expected")).put("snapshot_revision", 997);
        assertThrows(ContractViolationException.class, () -> apply(Operation.ACTUAL_SCOPE, json(input)));
    }

    @Test void actualQueryAndRouteStepKeepPublicZeroDistinctFromNativeCarmyAndProvince() {
        JsonNode query = apply(Operation.ACTUAL_QUERY, "{\"operation\":\"build_query\",\"subject_army_id\":0,\"target_province_id\":2585}");
        assertEquals("query-actual-contact-scope-v1-0-at-2585", query.path("step").textValue());
        JsonNode parsed = apply(Operation.ACTUAL_QUERY, "{\"operation\":\"parse_query\",\"step\":\"query-actual-contact-scope-v1-0-at-2585\"}");
        assertEquals(0, parsed.path("parsed").get(0).intValue());
        JsonNode route = apply(Operation.ROUTE_STEP, "{\"operation\":\"build\",\"subject_army_id\":0,\"target_province_id\":2585,\"hostile_army_ids\":[31,21,31],\"horizon_days\":2}");
        assertEquals("advance-route-contact-window-v1-0-to-2585-days-2-h-2-21-31", route.path("step").textValue());
        JsonNode tuple = apply(Operation.ROUTE_STEP, "{\"operation\":\"parse\",\"step\":\"advance-route-contact-window-v1-0-to-2585-days-2-h-2-21-31\"}");
        assertTrue(tuple.path("parsed").get(2).isArray());
        assertEquals(21, tuple.path("parsed").get(2).get(0).intValue());
        assertThrows(ContractViolationException.class, () -> apply(Operation.ACTUAL_QUERY,
                "{\"operation\":\"build_query\",\"subject_army_id\":0,\"target_province_id\":0}"));
    }

    @Test void originalFloatTokensReachSelectedProducerWithoutIntermediateTreeReserialization() throws IOException {
        String input = json(fixture("actualcontact").path("bases").path("new_attacker"));
        for (String token : new String[]{"true", "1.0", "1e0"}) {
            String changed = input.replace("\"schema_version\":1", "\"schema_version\":" + token);
            assertTrue(changed.contains("\"schema_version\":" + token));
            assertThrows(ContractViolationException.class, () -> apply(Operation.ACTUAL_SCOPE, changed));
        }
        assertThrows(ContractViolationException.class, () -> apply(Operation.ROUTE_STEP,
                "{\"operation\":\"build\",\"subject_army_id\":0.0,\"target_province_id\":2585,\"hostile_army_ids\":[21],\"horizon_days\":2}"));
    }

    @Test void routeProjectionAndSerializedPacketResultRetainCurrentRouteClockAndImmutability() throws IOException {
        String input = json(fixture("routewindow").path("bases").path("free"));
        byte[] raw = input.getBytes(StandardCharsets.UTF_8);
        Request request = new Request(Operation.ROUTE_WINDOW, raw);
        Result result = ContactConsumerPort.apply(request);
        JsonNode output = StrictJson.parse(result.utf8());
        assertEquals("available", output.path("status").textValue());
        assertEquals("frozen_current_routes", output.path("context_basis").textValue());
        assertEquals(3, output.path("contact_free_whole_days").intValue());
        byte[] changed = result.utf8(); changed[0] = 'x';
        assertEquals(output, StrictJson.parse(result.utf8()));
        assertArrayEquals(raw, request.inputJson());
        raw[0] = 'x';
        assertEquals(input, new String(request.inputJson(), StandardCharsets.UTF_8));
        assertThrows(ContractViolationException.class, () -> new Request(Operation.ACTUAL_QUERY,
                new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test void unknownRouteDuplicateFieldAndMissingNullableFieldRemainRejectedAtConsumerPort() throws IOException {
        assertThrows(IllegalArgumentException.class, () -> Operation.valueOf("CONTACT_ALIAS"));
        assertThrows(ContractViolationException.class, () -> apply(Operation.ACTUAL_QUERY,
                "{\"operation\":\"parse_query\",\"step\":null,\"step\":true}"));
        ObjectNode input = fixture("actualcontact").path("bases").path("new_attacker").deepCopy();
        ((ObjectNode) input.get("scope")).remove("selected_combat_id");
        assertThrows(ContractViolationException.class, () -> apply(Operation.ACTUAL_SCOPE, json(input)));
    }
}
