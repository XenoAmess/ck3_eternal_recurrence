package org.xar.ck3.control.wave2.military.warresultssource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.warresults.WarResultsCodec;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Binding;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Field;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Request;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Snapshot;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class WarResultsSourceTest {
    @TestFactory Stream<DynamicTest> actualOldNativeNormalizerAndPolicyConsumerGolden() throws IOException {
        JsonNode golden = golden(); assertEquals(10, golden.get("original_tests").intValue()); assertEquals(0, golden.get("original_skipped").intValue());
        assertEquals("xar.ck3.war-results-native-source-golden/v1", golden.get("schema").textValue());
        assertEquals("unknown", golden.get("source_machine_id").textValue());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : golden.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                byte[] bytes = raw(vector);
                if (!vector.get("accepted").booleanValue()) {
                    assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate(bytes));
                    return;
                }
                var validated = WarResultsSourceCodec.validate(bytes);
                assertEquals(vector.get("normalized"), StrictJson.parse(WarResultsSourceCodec.encodeNormalized(validated)));
                assertEquals(validated.input(), WarResultsSourceCodec.decode(WarResultsSourceCodec.encodeInput(validated.input())));
                Request request = currentRequest(vector.get("consumer_snapshot")); Snapshot before = request.snapshot().orElseThrow();
                var observation = WarResultsObservationComposer.compose(validated, before.binding());
                assertEquals(vector.get("consumer_presence").textValue(), WarResultsPolicy.presence(observation).name().toLowerCase(Locale.ROOT));
                Snapshot projected = new Snapshot(before.binding(), before.mapReady(), before.paused(), Field.of(observation),
                        before.queryAttempt(), before.closePending(), before.checkDue(), before.nextCheckDateRaw());
                Request complete = new Request(Optional.of(projected), request.actionSteps(), request.bridgeCapabilities());
                JsonNode actualPlan = StrictJson.parse(WarResultsCodec.encodePlan(WarResultsPolicy.plan(complete)));
                assertEquals(vector.get("consumer_plan"), actualPlan);
                if (!actualPlan.isNull()) { assertFalse(actualPlan.get("war_results_window").get("close_action_credit").booleanValue()); }
            }));
        }
        return tests.stream();
    }

    @Test void allUint64IdentityBitsAndUint32ThreadAreRetained() throws IOException {
        ObjectNode input = input("retained-812"); ObjectNode leaf = object(input.get("leaf")); ObjectNode owner = object(input.get("owner_receipt"));
        BigInteger high = new BigInteger("18446744073709551615");
        for (String key : List.of("ticket_sequence", "pump_epoch", "connection_generation")) { leaf.put(key, high); owner.put(key, high); }
        owner.put("executor_started_sequence", high); owner.put("completed_sequence", high); input.put("native_generation", high);
        leaf.put("thread_id", 0xffff_ffffL); owner.put("thread_id", 0xffff_ffffL);
        leaf.put("native_revision", high); object(input.get("binding")).put("native_revision", high);
        var validated = WarResultsSourceCodec.validate(StrictJson.canonical(input));
        assertEquals(high, validated.leaf().owner().ticketSequence()); assertEquals(high, validated.leaf().frame().revision());
        assertEquals(0xffff_ffffL, validated.leaf().owner().threadId());
        assertEquals(validated.input(), WarResultsSourceCodec.decode(WarResultsSourceCodec.encodeInput(validated.input())));
    }

    @Test void correctWireCannotBeComposedIntoAChangedOriginalLease() throws IOException {
        JsonNode vector = vector("retained-812"); var validated = WarResultsSourceCodec.validate(raw(vector));
        Binding original = currentRequest(vector.get("consumer_snapshot")).snapshot().orElseThrow().binding();
        Binding wrong = new Binding(original.snapshotId(), original.revision(), original.nativeRevision(), original.dateRaw(),
                Field.of(BigInteger.valueOf(999)), original.connectionGeneration(), original.episodeRunId());
        assertThrows(IllegalArgumentException.class, () -> WarResultsObservationComposer.compose(validated, wrong));
        Binding missing = new Binding(Field.missing(), original.revision(), original.nativeRevision(), original.dateRaw(),
                original.actorId(), original.connectionGeneration(), original.episodeRunId());
        assertThrows(IllegalArgumentException.class, () -> WarResultsObservationComposer.compose(validated, missing));
    }

    @Test void nativeBoolFloatAndStringTokensActuallyReachStrictDecoder() throws IOException {
        String json = new String(StrictJson.canonical(input("retained-812")), StandardCharsets.UTF_8);
        assertTrue(json.contains("\"native_revision\":586"));
        for (String token : List.of("true", "586.0", "586e0", "\"586\"")) {
            byte[] raw = json.replace("\"native_revision\":586", "\"native_revision\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate(raw), token);
        }
    }

    @Test void nullFlagExtraSourceBooleanAndPartialNativeTraceNeverQualify() throws IOException {
        ObjectNode nullFlag = input("retained-812"); object(nullFlag.get("leaf")).putNull("post_observed");
        assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate(StrictJson.canonical(nullFlag)));
        ObjectNode extra = input("retained-812"); extra.put("source_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate(StrictJson.canonical(extra)));
        ObjectNode trace = input("retained-812"); object(trace.get("leaf")).remove("dismiss_stage");
        assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate(StrictJson.canonical(trace)));
    }

    @Test void absentSourceReceiptAndUnknownEnvelopeAreNotWireProof() throws IOException {
        ObjectNode missing = input("retained-812"); missing.remove("owner_receipt");
        assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate(StrictJson.canonical(missing)));
        ObjectNode version = input("retained-812"); version.put("schema", "other");
        assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate(StrictJson.canonical(version)));
        assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void unicodeWhitespaceCannotStandInForAnUnavailableReason() throws IOException {
        for (String blank : List.of("", " \t\r\n", "\u0085", "\u00a0", "\u2007\u202f", "\u3000")) {
            ObjectNode input = input("retained-814"); object(input.get("leaf")).put("unavailable_reason", blank);
            assertThrows(IllegalArgumentException.class, () -> WarResultsSourceCodec.validate(StrictJson.canonical(input)));
        }
    }

    private static Request currentRequest(JsonNode snapshot) {
        ObjectNode node = StrictJson.object(); node.put("schema", WarResultsCodec.SCHEMA); node.set("snapshot", snapshot.deepCopy());
        node.putArray("action_steps").add(WarResultsPolicy.QUERY_STEP).add(WarResultsPolicy.CLOSE_STEP).add("pause-map");
        node.putArray("bridge_capabilities").add(WarResultsPolicy.QUERY_CAPABILITY).add(WarResultsPolicy.CLOSE_CAPABILITY);
        return WarResultsCodec.decode(StrictJson.canonical(node));
    }
    private static byte[] raw(JsonNode vector) {
        return vector.has("input_raw") ? vector.get("input_raw").textValue().getBytes(StandardCharsets.UTF_8) : StrictJson.canonical(vector.get("input"));
    }
    private static ObjectNode input(String name) throws IOException { return object(vector(name).get("input")).deepCopy(); }
    private static JsonNode vector(String name) throws IOException {
        for (JsonNode vector : golden().get("cases")) { if (name.equals(vector.get("name").textValue())) { return vector; } }
        throw new IOException("required retained producer vector missing: " + name);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = WarResultsSourceTest.class.getResourceAsStream("/warresultssource/producer-golden.json")) {
            if (stream == null) { throw new IOException("required committed native-source golden missing"); } return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode object(JsonNode value) { return (ObjectNode) value; }
}
