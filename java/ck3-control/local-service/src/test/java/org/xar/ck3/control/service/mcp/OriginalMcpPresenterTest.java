package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Producer fixtures came from the existing Python presenters and actual SDK registration, never Native/Game. */
final class OriginalMcpPresenterTest {
    record Request(PublicBindings.Arguments original) { }
    private static JsonNode oracle() throws Exception {
        try (InputStream input = OriginalMcpPresenterTest.class.getResourceAsStream("/mcp/original-presenter-oracle.json")) {
            assertNotNull(input); return McpJson.parse(input.readAllBytes());
        }
    }
    private static ToolDescriptor descriptor(String name) throws Exception {
        for (JsonNode row : oracle().get("descriptors")) if (name.equals(row.get("name").textValue()))
            return new ToolDescriptor(name, new RawJson(McpJson.encode(row)));
        throw new IllegalArgumentException("original descriptor fixture missing");
    }
    private static PublicMcpDirectory installed(String name, PublicMethod method, RawJson business, AtomicInteger calls) throws Exception {
        PublicMcpBindings directory = PublicMcpBindingTest.oneAdmitted(name);
        PublicBindings nativeBindings = new PublicBindings();
        var actual = nativeBindings.register(method, Request.class, RawJson.class,
                request -> { calls.incrementAndGet(); return business; }, Request::new, value -> value,
                PublicMcpProtocolTest.target(), PublicRoutes.Status.IMPLEMENTED, "software oracle producer only");
        nativeBindings.freeze(Set.of(method));
        PublicMcpNativeAdapter.register(directory, descriptor(name), actual);
        return directory.freezeSoftwareScope();
    }
    private static Arguments arguments(String json) {
        return new Arguments(Presence.VALUE, Optional.of(new RawJson(McpJson.utf8(json))));
    }
    private static ToolCall call(String name, String json) {
        return new ToolCall(name, arguments(json), Optional.empty(), new McpCancellation());
    }
    private static JsonNode example(String name) throws Exception {
        for (JsonNode row : oracle().get("cases")) if (name.equals(row.get("name").textValue())) return row;
        throw new IllegalArgumentException("oracle case missing");
    }

    @Test void originalProducersThroughActualTypedBindingsPreserveAllSevenCompleteResults() throws Exception {
        int checked = 0;
        for (JsonNode row : oracle().get("cases")) {
            boolean army = row.get("entry").textValue().equals("ARMY_QUERY");
            String name = army ? "ck3_query_army_strengths" : "ck3_auto_turn";
            PublicMethod method = army ? PublicMethod.QUERY_ARMY_STRENGTHS : PublicMethod.AUTO_TURN;
            AtomicInteger invocations = new AtomicInteger(); RawJson business = new RawJson(McpJson.encode(row.get("business")));
            var directory = installed(name, method, business, invocations);
            CallResult actual = directory.invoke(call(name, army ? "{\"army_ids\":[0]}" : "{}"));
            assertEquals(row.get("expected"), McpJson.parse(actual.bytes()), row.get("name").textValue());
            assertEquals(1, invocations.get()); assertEquals(row.get("business"), McpJson.parse(business.bytes())); checked++;
        }
        assertEquals(7, checked);
    }
    @Test void executeStepPresentationConsumesItsActualRequestEvenWhenResultHasNoStep() throws Exception {
        JsonNode row = example("army_direct"); AtomicInteger calls = new AtomicInteger();
        var directory = installed("ck3_execute_step", PublicMethod.EXECUTE_STEP, new RawJson(McpJson.encode(row.get("business"))), calls);
        assertEquals(row.get("expected"), McpJson.parse(directory.invoke(call("ck3_execute_step", "{\"step\":\"query-army-strengths-v1\"}")).bytes()));
        assertEquals(1, calls.get());
        var other = McpJson.parse(directory.invoke(call("ck3_execute_step", "{\"step\":\"query-war-state-v1\"}")).bytes());
        assertEquals(row.get("business"), other.get("structuredContent")); assertEquals(2, calls.get());
        assertThrows(ToolFailure.class, () -> directory.invoke(call("ck3_execute_step", "{}"))); assertEquals(2, calls.get());
    }
    @Test void sourceBoundPublicNameCannotRegisterAnotherRealAction() throws Exception {
        PublicMcpBindings directory = PublicMcpBindingTest.oneAdmitted("ck3_auto_turn"); PublicBindings nativeBindings = new PublicBindings();
        AtomicInteger calls = new AtomicInteger();
        var wrong = nativeBindings.register(PublicMethod.SURRENDER_WAR, Request.class, RawJson.class,
                request -> { calls.incrementAndGet(); return new RawJson(McpJson.utf8("{}")); }, Request::new, value -> value,
                PublicMcpProtocolTest.target(), PublicRoutes.Status.IMPLEMENTED, "deliberate wrong action test");
        nativeBindings.freeze(Set.of(PublicMethod.SURRENDER_WAR));
        assertThrows(IllegalArgumentException.class, () -> PublicMcpNativeAdapter.register(directory, descriptor("ck3_auto_turn"), wrong));
        assertEquals(0, calls.get()); assertEquals(0, directory.actualBindings().size());
        assertEquals(PublicMethod.CAPABILITIES, PublicMcpNativeAdapter.expectedServiceMethod("ck3_get_capabilities"));
        assertEquals(PublicMethod.SNAPSHOT, PublicMcpNativeAdapter.expectedServiceMethod("ck3_take_snapshot"));
        assertThrows(IllegalArgumentException.class, () -> PublicMcpNativeAdapter.expectedServiceMethod("ck3_auto_nonwar_turn"));
    }
    @Test void malformedCombatPrefixDoesNotBecomeAQueryAndBlockedMarketPreservesItsFullOriginal() throws Exception {
        for (String name : List.of("combat_v2", "mercenary_auto")) {
            ObjectNode payload = McpJson.object(example(name).get("business").deepCopy());
            if (name.equals("combat_v2")) {
                String malformed = "query-combat-simulation-inputs-v2-5-2-a-1-00-d-1-1";
                payload.put("selected_step", malformed); McpJson.object(payload.get("plan")).put("selected_step", malformed);
                McpJson.object(payload.get("result")).put("step", malformed);
            } else McpJson.object(payload.get("result")).put("read_only", false);
            RawJson original = new RawJson(McpJson.encode(payload));
            assertArrayEquals(CallResult.fromBusinessJson(original).bytes(), OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.AUTO_TURN, arguments("{}"), original).bytes());
        }
    }
    @Test void publicFullWidthStringsRoundTripAndUnsafeNumericIdentityIsRejectedWithoutConversion() throws Exception {
        ObjectNode payload = McpJson.object(example("combat_v2").get("business").deepCopy());
        ObjectNode result = McpJson.object(payload.get("result")); result.put("query_sequence", "18446744073709551615");
        result.put("queried_native_revision", "9007199254740993");
        var full = OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.AUTO_TURN, arguments("{}"), new RawJson(McpJson.encode(payload)));
        JsonNode actual = McpJson.parse(full.bytes()); assertEquals(payload, actual.get("structuredContent"));
        assertEquals("18446744073709551615", McpJson.parse(actual.get("content").get(0).get("text").textValue().getBytes(StandardCharsets.UTF_8)).get("query_sequence").textValue());
        result.put("query_sequence", new java.math.BigInteger("18446744073709551615"));
        assertThrows(IllegalArgumentException.class, () -> OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.AUTO_TURN, arguments("{}"), new RawJson(McpJson.encode(payload))));
    }
    @Test void invalidTimingIsOmittedAndNaturalAppliedErrorsRetainOriginalEvidence() throws Exception {
        ObjectNode payload = McpJson.object(example("army_direct").get("business").deepCopy());
        McpJson.object(payload.get("army_native_timing_v1")).put("baseline_read_ns", true);
        var actual = McpJson.parse(OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.ARMY_QUERY, arguments("{}"), new RawJson(McpJson.encode(payload))).bytes());
        assertFalse(actual.get("structuredContent").has("army_native_timing_v1")); assertEquals(17, actual.get("structuredContent").get("query_sequence").intValue());
        for (String name : List.of("persistence_failure", "handoff_unverified")) {
            JsonNode example = example(name); var error = McpJson.parse(OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.AUTO_TURN, arguments("{}"), new RawJson(McpJson.encode(example.get("business")))).bytes());
            assertTrue(error.get("isError").booleanValue()); assertTrue(error.get("content").get(0).get("text").textValue().contains("do not resend Continue"));
            assertEquals(example.get("expected"), error);
        }
    }
}
