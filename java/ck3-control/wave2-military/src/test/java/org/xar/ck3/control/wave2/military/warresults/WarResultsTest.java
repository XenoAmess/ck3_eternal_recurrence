package org.xar.ck3.control.wave2.military.warresults;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.FieldPresence;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowPresence;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class WarResultsTest {
    @TestFactory Stream<DynamicTest> unchangedProducerGoldenPlansPresenceAndFrameIdentity() throws IOException {
        JsonNode golden = golden(); assertEquals(4, golden.get("original_tests").intValue());
        assertEquals(0, golden.get("original_skipped").intValue());
        assertEquals("xar.ck3.war-results-priority-golden/v1", golden.get("schema").textValue());
        assertTrue(golden.get("source_pins").size() >= 5); assertTrue(golden.get("machine_id").isTextual());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : golden.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                var request = WarResultsCodec.decode(StrictJson.canonical(vector.get("input")));
                assertEquals(vector.get("plan"), StrictJson.parse(WarResultsCodec.encodePlan(WarResultsPolicy.plan(request))));
                WindowPresence presence = request.snapshot().flatMap(frame -> frame.observation().value())
                        .map(WarResultsPolicy::presence).orElse(WindowPresence.UNKNOWN);
                assertEquals(vector.get("presence").textValue(), presence.name().toLowerCase(Locale.ROOT));
                if (request.snapshot().isPresent()) {
                    assertEquals(vector.get("query_frame"), StrictJson.parse(WarResultsCodec.encodeQueryFrame(
                            WarResultsPolicy.queryFrame(request.snapshot().orElseThrow()))));
                } else { assertTrue(vector.get("query_frame").isNull()); }
            }));
        }
        return tests.stream();
    }

    @Test void roundTripSelectedProjectionRetainsTypedMissingNullAndUnknownState() throws IOException {
        for (JsonNode vector : golden().get("cases")) {
            var first = WarResultsCodec.decode(StrictJson.canonical(vector.get("input")));
            var second = WarResultsCodec.decode(WarResultsCodec.encodeRequest(first));
            assertEquals(first, second, vector.get("name").textValue());
            assertEquals(WarResultsPolicy.plan(first), WarResultsPolicy.plan(second));
            assertThrows(UnsupportedOperationException.class, () -> first.actionSteps().clear());
            assertThrows(UnsupportedOperationException.class, () -> first.bridgeCapabilities().clear());
        }
    }

    @Test void absentNullAndEmptyPendingRemainDistinct() throws IOException {
        ObjectNode input = input("unknown-query"); ObjectNode frame = object(input.get("snapshot"));
        var absent = WarResultsCodec.decode(StrictJson.canonical(input)).snapshot().orElseThrow();
        assertEquals(FieldPresence.MISSING, absent.closePending().presence());
        frame.putNull("war_results_window_v1_close_pending");
        var explicitNull = WarResultsCodec.decode(StrictJson.canonical(input)).snapshot().orElseThrow();
        assertEquals(FieldPresence.NULL, explicitNull.closePending().presence());
        frame.putObject("war_results_window_v1_close_pending");
        var emptyObject = WarResultsCodec.decode(StrictJson.canonical(input)).snapshot().orElseThrow();
        assertTrue(emptyObject.closePending().isValue());
        assertEquals(WarResultsPolicy.queryFrame(absent), WarResultsPolicy.queryFrame(explicitNull));
        assertEquals(WarResultsPolicy.queryFrame(absent), WarResultsPolicy.queryFrame(emptyObject));
        assertNotEquals(absent.closePending(), emptyObject.closePending());
    }

    @Test void rawFloatBoolStringTokensCannotBecomeExactNativeIdentities() {
        for (String token : List.of("true", "3.0", "3e0", "\"3\"", "-1", "18446744073709551616")) {
            String json = "{\"schema\":\"" + WarResultsCodec.SCHEMA + "\",\"snapshot\":{\"native_revision\":"
                    + token + "},\"action_steps\":[],\"bridge_capabilities\":[]}";
            assertThrows(IllegalArgumentException.class, () -> WarResultsCodec.decode(json.getBytes(StandardCharsets.UTF_8)), token);
        }
        String wrong = "{\"schema\":\"" + WarResultsCodec.SCHEMA + "\",\"snapshot\":{\"paused\":1},\"action_steps\":[],\"bridge_capabilities\":[]}";
        assertThrows(IllegalArgumentException.class, () -> WarResultsCodec.decode(wrong.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void uint64NativeRevisionAndSignedNativeDatesRoundTripWithoutDouble() throws IOException {
        ObjectNode input = input("unknown-query"); ObjectNode frame = object(input.get("snapshot"));
        BigInteger maximum = new BigInteger("18446744073709551615"); frame.put("native_revision", maximum);
        frame.put("revision", new BigInteger("9007199254740993")); frame.put("date_raw", Integer.MIN_VALUE);
        frame.put("war_results_window_v1_next_check_date_raw", BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.valueOf(144)));
        var request = WarResultsCodec.decode(StrictJson.canonical(input)); var identity = WarResultsPolicy.queryFrame(request.snapshot().orElseThrow());
        JsonNode values = StrictJson.parse(WarResultsCodec.encodeQueryFrame(identity));
        assertEquals(maximum, values.get(0).bigIntegerValue()); assertEquals(Integer.MIN_VALUE, values.get(1).intValue());
        assertEquals(request, WarResultsCodec.decode(WarResultsCodec.encodeRequest(request)));
    }

    @Test void acceptedDispatchAckCannotEstablishPostPresenceOrCloseCredit() throws IOException {
        var request = WarResultsCodec.decode(StrictJson.canonical(input("ack-only")));
        assertEquals(WindowPresence.UNKNOWN, WarResultsPolicy.presence(request.snapshot().orElseThrow().observation().value().orElseThrow()));
        JsonNode plan = StrictJson.parse(WarResultsCodec.encodePlan(WarResultsPolicy.plan(request)));
        assertEquals(WarResultsPolicy.QUERY_STEP, plan.get("selected_step").textValue());
        assertFalse(plan.get("war_results_window").get("close_action_credit").booleanValue());
    }

    @Test void publicProjectionChangesDoNotChangeCadenceButPendingOriginalIdentityDoes() throws IOException {
        ObjectNode input = input("unknown-query"); var first = WarResultsCodec.decode(StrictJson.canonical(input)).snapshot().orElseThrow();
        ObjectNode frame = object(input.get("snapshot")); frame.put("snapshot_id", "public:new"); frame.put("revision", 10000);
        var second = WarResultsCodec.decode(StrictJson.canonical(input)).snapshot().orElseThrow();
        assertEquals(WarResultsPolicy.queryFrame(first), WarResultsPolicy.queryFrame(second));
        frame.putObject("war_results_window_v1_close_pending").put("native_request_id", "original-unresolved");
        var third = WarResultsCodec.decode(StrictJson.canonical(input)).snapshot().orElseThrow();
        assertNotEquals(WarResultsPolicy.queryFrame(first), WarResultsPolicy.queryFrame(third));
    }

    @Test void exactEnvelopeRejectsMissingUnknownDuplicateAndInvalidContainers() throws IOException {
        ObjectNode missing = input("unknown-query"); missing.remove("snapshot");
        assertThrows(IllegalArgumentException.class, () -> WarResultsCodec.decode(StrictJson.canonical(missing)));
        ObjectNode unexpected = input("unknown-query"); unexpected.put("unexpected", true); byte[] raw = StrictJson.canonical(unexpected);
        assertThrows(IllegalArgumentException.class, () -> WarResultsCodec.decode(raw));
        assertThrows(IllegalArgumentException.class, () -> WarResultsCodec.decode("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
        ObjectNode nullSteps = input("unknown-query"); nullSteps.putNull("action_steps");
        assertThrows(IllegalArgumentException.class, () -> WarResultsCodec.decode(StrictJson.canonical(nullSteps)));
        ObjectNode wrongPending = input("unknown-query"); object(wrongPending.get("snapshot")).put("war_results_window_v1_close_pending", true);
        assertThrows(IllegalArgumentException.class, () -> WarResultsCodec.decode(StrictJson.canonical(wrongPending)));
        assertThrows(IllegalArgumentException.class, () -> WarResultsCodec.decode(new byte[65_537]));
    }

    private static ObjectNode input(String name) throws IOException {
        for (JsonNode vector : golden().get("cases")) {
            if (name.equals(vector.get("name").textValue())) { return object(vector.get("input")).deepCopy(); }
        }
        throw new IOException("required producer case missing: " + name);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = WarResultsTest.class.getResourceAsStream("/warresults/producer-golden.json")) {
            if (stream == null) { throw new IOException("required committed producer golden missing"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode object(JsonNode node) { return (ObjectNode) node; }
}
