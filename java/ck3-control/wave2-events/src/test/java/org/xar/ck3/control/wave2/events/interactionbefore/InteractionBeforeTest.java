package org.xar.ck3.control.wave2.events.interactionbefore;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence.*;

class InteractionBeforeTest {
    private static final String RESOURCE = "/interactionbefore/legacy-producer-golden-v1.json";
    private static final Identity TEST_ID = new Identity("0123456789abcdef0123456789abcdef", "2026-10-22T00:00:00Z", "synthetic-not-a-runtime-machine");

    @Test void actualOriginalBeforeProducerCasesKeepEveryOriginalCaptureField() throws IOException {
        JsonNode golden = golden(); assertEquals(9, golden.get("cases").size());
        for (JsonNode row : golden.get("cases")) {
            byte[] source = utf8(row.get("planned_utf8").textValue()); JsonNode result = row.get("result");
            if (result.get("status").textValue().equals("rejected")) {
                assertThrows(ContractViolationException.class, () -> InteractionBeforeComposer.compose(source, row.get("planned_sha256").textValue(), TEST_ID, gui(golden)), row.get("name").textValue());
                continue;
            }
            Identity identity = new Identity(result.get("incident_id").textValue(), result.get("captured_at_utc").textValue(), golden.get("machine_id").textValue());
            Prepared actual = assertInstanceOf(Prepared.class, InteractionBeforeComposer.compose(source, row.get("planned_sha256").textValue(), identity, gui(golden)));
            ObjectNode expected = ((ObjectNode) StrictJson.parse(source).path("plan").path("unhandled_interaction_fallback")).deepCopy();
            expected.put("incident_id", identity.incidentId()); expected.put("stage", "before_submission"); expected.put("captured_at_utc", identity.capturedAtUtc()); expected.put("machine_id", identity.machineId()); expected.put("dispatch_attempted", false);
            assertEquals(expected, StrictJson.parse(actual.json()), row.get("name").textValue());
            assertEquals(identity, actual.identity()); assertEquals(row.get("planned_sha256").textValue(), actual.plannedSourceSha256());
            JsonNode selected = StrictJson.parse(source).path("plan").get("selected_step");
            assertEquals(selected != null && !selected.isNull(), actual.selectedStep().isPresent());
            actual.selectedStep().ifPresent(value -> assertEquals(actual.action().step(), value));
            assertFalse(actual.dispatchAttempted()); assertFalse(actual.durableBeforeWritten()); assertFalse(actual.replayAllowed());
            assertTrue(new String(actual.json(), StandardCharsets.UTF_8).contains("\"opaque_float_hint\":1.0"), "opaque floating token must not become integer 1");
        }
    }

    @Test void rawFloatBoolStringAndMissingFrameValuesAreActuallyRejected() throws IOException {
        JsonNode golden = golden(); String source = sample("known").get("planned_utf8").textValue();
        for (String token : List.of("true", "3.0", "3e0", "\"3\"", "null", "18446744073709551616")) {
            String raw = source.replace("\"revision\":3", "\"revision\":" + token); assertTrue(raw.contains("\"revision\":" + token));
            assertThrows(ContractViolationException.class, () -> compose(raw, golden), token);
        }
        ObjectNode changed = (ObjectNode) StrictJson.parse(utf8(source)); ((ObjectNode) changed.get("plan").get("unhandled_interaction_fallback").get("binding")).remove("revision");
        assertThrows(ContractViolationException.class, () -> compose(changed.toString(), golden));
    }

    @Test void unreachableOrContradictoryNativeReplyDoesNotProduceDispatchableBeforeEvidence() throws IOException {
        JsonNode golden = golden(); ObjectNode raw = planned(); ObjectNode capture = capture(raw); ((ObjectNode) capture.get("selection")).put("action_reachable", false);
        ObjectNode unreachable = raw; assertThrows(ContractViolationException.class, () -> compose(unreachable.toString(), golden));
        raw = planned(); capture = capture(raw); ((ObjectNode) capture.get("context").get("legality").get("reject")).put("allowed", false);
        ObjectNode nativeConflict = raw;
        assertThrows(ContractViolationException.class, () -> compose(nativeConflict.toString(), golden));
        raw = planned(); capture = capture(raw); ((ObjectNode) capture.get("selection")).put("action", "accept");
        ObjectNode right = raw; assertThrows(ContractViolationException.class, () -> compose(right.toString(), golden));
    }

    @Test void sourceGuiOrderMachineMetadataAndNoCaptureBranchRemainExplicit() throws IOException {
        JsonNode golden = golden(); String source = sample("known").get("planned_utf8").textValue();
        assertThrows(ContractViolationException.class, () -> InteractionBeforeComposer.compose(utf8(source), "0".repeat(64), TEST_ID, gui(golden)));
        assertThrows(ContractViolationException.class, () -> InteractionBeforeComposer.compose(utf8(source), InteractionBeforeComposer.digest(utf8(source)), TEST_ID, new GuiSourcePin(gui(golden).source(), "0".repeat(64))));
        ObjectNode changed = planned(); ((ObjectNode) capture(changed).get("reply_options").get(0)).put("rendered_index", 1);
        assertThrows(ContractViolationException.class, () -> compose(changed.toString(), golden));
        byte[] noCapture = utf8("{\"plan\":{\"selected_step\":null}}");
        assertInstanceOf(NotApplicable.class, InteractionBeforeComposer.compose(noCapture, InteractionBeforeComposer.digest(noCapture), TEST_ID, gui(golden)));
        assertThrows(ContractViolationException.class, () -> new Identity("bad", "2026-10-22T00:00:00Z", "synthetic"));
    }

    @Test void completedJsonRejectsDuplicateKeysReservedMetadataMalformedUtf8AndOversize() throws IOException {
        JsonNode golden = golden(); String source = sample("known").get("planned_utf8").textValue();
        String duplicate = source.replaceFirst("\\{", "{\"revision\":3,");
        assertThrows(ContractViolationException.class, () -> compose(duplicate, golden));
        ObjectNode changed = planned(); capture(changed).put("incident_id", TEST_ID.incidentId());
        assertThrows(ContractViolationException.class, () -> compose(changed.toString(), golden));
        byte[] malformed = {(byte) 0xff};
        assertThrows(ContractViolationException.class, () -> InteractionBeforeComposer.compose(malformed, InteractionBeforeComposer.digest(malformed), TEST_ID, gui(golden)));
        byte[] oversized = new byte[65_537];
        assertThrows(ContractViolationException.class, () -> InteractionBeforeComposer.compose(oversized, InteractionBeforeComposer.digest(oversized), TEST_ID, gui(golden)));
    }

    @Test void immutablePreparedBytesPreserveSignedIdAndUint64WithoutJavaScriptRounding() throws IOException {
        JsonNode golden = golden(); ObjectNode raw = planned(); ObjectNode capture = capture(raw);
        capture.put("pending_interaction_id", Integer.MIN_VALUE); ((ObjectNode) capture.get("context")).put("pending_interaction_id", Integer.MIN_VALUE);
        Prepared result = assertInstanceOf(Prepared.class, compose(raw.toString(), golden)); assertEquals(Integer.MIN_VALUE, result.pendingInteractionId());
        byte[] first = result.json(); byte original = first[0]; first[0] = '!'; assertEquals(original, result.json()[0]);
        ObjectNode frame = (ObjectNode) capture.get("binding"); frame.put("revision", StrictJson.UINT64_MAX); raw.put("revision", StrictJson.UINT64_MAX);
        result = assertInstanceOf(Prepared.class, compose(raw.toString(), golden)); assertEquals(StrictJson.UINT64_MAX, result.frame().revision());
    }

    @Test void rawCaptureByteOffsetsPreserveMultibyteUnicodeAndOpaqueFloatingToken() throws IOException {
        JsonNode golden = golden(); String source = sample("known").get("planned_utf8").textValue();
        String unicode = source.replace("\"opaque_float_hint\":1.0", "\"opaque_float_hint\":1.0,\"unicode_note\":\"漢字😀\"");
        Prepared result = assertInstanceOf(Prepared.class, compose(unicode, golden));
        String output = new String(result.json(), StandardCharsets.UTF_8);
        assertTrue(output.contains("\"opaque_float_hint\":1.0")); assertTrue(output.contains("\"unicode_note\":\"漢字😀\""));
        assertEquals("漢字😀", StrictJson.parse(result.json()).path("original_plan").path("unicode_note").textValue());
    }

    private static Result compose(String raw, JsonNode golden) { byte[] bytes = utf8(raw); return InteractionBeforeComposer.compose(bytes, InteractionBeforeComposer.digest(bytes), TEST_ID, gui(golden)); }
    private static GuiSourcePin gui(JsonNode golden) { return new GuiSourcePin(golden.get("gui_source").textValue(), golden.get("gui_sha256").textValue()); }
    private static ObjectNode planned() throws IOException { return (ObjectNode) StrictJson.parse(utf8(sample("known").get("planned_utf8").textValue())); }
    private static ObjectNode capture(ObjectNode value) { return (ObjectNode) value.get("plan").get("unhandled_interaction_fallback"); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode sample(String name) throws IOException { for (JsonNode row : golden().get("cases")) { if (row.get("name").textValue().equals(name)) { return row; } } throw new AssertionError(name); }
    private static JsonNode golden() throws IOException {
        try (var stream = InteractionBeforeTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(stream, "committed real original producer golden required"); byte[] raw = stream.readNBytes(98_305); assertTrue(raw.length <= 98_304);
            return new ObjectMapper().readTree(raw); // Bounded committed fixture only; production planned JSON always uses StrictJson.
        }
    }
}
