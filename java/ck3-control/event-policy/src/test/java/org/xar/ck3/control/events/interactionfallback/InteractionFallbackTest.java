package org.xar.ck3.control.events.interactionfallback;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.events.interactionfallback.InteractionFallback.*;

class InteractionFallbackTest {
    private static final String RESOURCE = "/interactionfallback/legacy-producer-golden-v1.json";
    private static final String PRODUCER_SHA = "1b60333c70edec9e1deb233cf5d49ce77dfd51301ef22bbf216d25e12d3ec1f5";

    @Test void actualLegacyProducerProjectionsMatchAllTenCapturedCases() throws IOException {
        JsonNode golden = golden();
        assertEquals(PRODUCER_SHA, golden.get("producer_sha256").textValue());
        assertEquals(10, golden.get("cases").size());
        for (JsonNode row : golden.get("cases")) {
            Request request = parse((ObjectNode) row.get("request"));
            byte[] output = InteractionFallbackCodec.encodeResult(InteractionFallbackPlanner.plan(request));
            assertEquals(row.get("expected"), StrictJson.parse(output), row.get("name").textValue());
            assertArrayEquals(StrictJson.canonical(row.get("expected")), output, row.get("name").textValue());
        }
    }

    @Test void requestRoundTripPreservesMissingNullAndEmptyCollectionSemantics() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            Request request = parse((ObjectNode) row.get("request"));
            Request reloaded = InteractionFallbackCodec.parseRequest(InteractionFallbackCodec.encodeRequest(request));
            assertEquals(request, reloaded, row.get("name").textValue());
        }
        Request missing = parse(request("missing_legality"));
        Request explicitNull = parse(request("null_legality"));
        assertEquals(Presence.MISSING, missing.context().legality().reject().presence());
        assertEquals(Presence.NULL, explicitNull.context().legality().reject().presence());
        assertNotEquals(missing, explicitNull);
        ObjectNode empty = request("unknown"); empty.putArray("action_steps");
        Result result = InteractionFallbackPlanner.plan(parse(empty));
        assertEquals(Phase.UNSUPPORTED, result.candidate().phase());
        assertNull(result.candidate().selectedStep());
    }

    @Test void dedicatedDecisionsAndExistingFallbackHavePriority() throws IOException {
        for (String field : List.of("selected_step", "blocked_marriage_reply", "existing_interaction_fallback")) {
            ObjectNode raw = request("known"); ObjectNode original = (ObjectNode) raw.get("original_plan");
            if (field.equals("selected_step")) { original.put(field, "accept-pending-character-interaction"); }
            else { original.put(field, true); }
            Result result = InteractionFallbackPlanner.plan(parse(raw));
            assertEquals(Disposition.DEDICATED_PLAN_RETAINED, result.disposition());
            assertNull(result.candidate());
        }
        ObjectNode ordinary = request("known"); ((ObjectNode) ordinary.get("original_plan")).put("phase", "ordinary_turn");
        assertEquals(Disposition.NOT_APPLICABLE, InteractionFallbackPlanner.plan(parse(ordinary)).disposition());
    }

    @Test void staleContextAndUnknownNotificationNeverProduceCandidate() throws IOException {
        for (String field : List.of("snapshot_revision", "date_raw", "pending_interaction_id")) {
            ObjectNode raw = request("known"); ObjectNode context = (ObjectNode) raw.get("context");
            context.put(field, context.get(field).bigIntegerValue().add(BigInteger.ONE));
            Result result = InteractionFallbackPlanner.plan(parse(raw));
            assertEquals(Disposition.STALE_CONTEXT, result.disposition()); assertNull(result.candidate());
        }
        ObjectNode unavailable = request("known"); ((ObjectNode) unavailable.get("context")).put("status", "unavailable");
        assertEquals(Disposition.STALE_CONTEXT, InteractionFallbackPlanner.plan(parse(unavailable)).disposition());
        ObjectNode absentNotification = request("known"); ((ObjectNode) absentNotification.get("pending")).putNull("auto_accept_notification");
        assertEquals(Disposition.NOT_APPLICABLE, InteractionFallbackPlanner.plan(parse(absentNotification)).disposition());
    }

    @Test void disabledLeftNeverChangesToRightAndAllGuiSourcesRemainBound() throws IOException {
        for (String name : List.of("disabled", "unavailable", "missing_legality", "null_legality", "no_command")) {
            Candidate candidate = InteractionFallbackPlanner.plan(parse(request(name))).candidate();
            assertNull(candidate.selectedStep()); assertEquals(Action.REJECT, candidate.selection().action());
            assertEquals("left", candidate.selection().position());
            assertTrue(candidate.replyOptions().get(1).nativeLegality().enabled());
        }
        ObjectNode gui = InteractionFallbackCodec.guiBinding();
        assertEquals(GUI_SHA256, gui.get("sha256").textValue());
        assertEquals(GUI_SOURCE, gui.get("source").textValue());
        assertEquals("reject", gui.get("normal_channel").get(0).get("action").textValue());
        assertEquals("accept", gui.get("normal_channel").get(1).get("action").textValue());
        assertEquals(3, gui.get("same_order_stock_variants").size());
        Candidate acknowledge = InteractionFallbackPlanner.plan(parse(request("acknowledge"))).candidate();
        assertEquals(Action.ACKNOWLEDGE, acknowledge.selection().action()); assertEquals("only", acknowledge.selection().position());
    }

    @Test void wrongMissingAndNullTypesAreRejectedBeforeDomainConstruction() throws IOException {
        for (String field : List.of("revision", "native_revision", "date_raw", "connection_generation", "bridge_pid", "actor_character_id")) {
            for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "[]", "{}")) {
                byte[] wire = rawToken(request("known"), "binding", field, token);
                assertTrue(new String(wire, StandardCharsets.UTF_8).contains("\"" + field + "\":" + token));
                if (token.equals("1.0") || token.equals("1e0")) {
                    assertTrue(StrictJson.parse(wire).get("binding").get(field).isFloatingPointNumber());
                }
                assertThrows(ContractViolationException.class, () -> InteractionFallbackCodec.parseRequest(wire), field + ": " + token);
            }
            ObjectNode missing = request("known"); ((ObjectNode) missing.get("binding")).remove(field);
            assertThrows(ContractViolationException.class, () -> parse(missing), "missing " + field);
        }
        ObjectNode extra = request("known"); extra.put("reviewed_rule", "unvalidated-review-is-not-authority");
        assertThrows(ContractViolationException.class, () -> parse(extra));
        ObjectNode wrongBoolean = request("known"); ((ObjectNode) wrongBoolean.get("pending")).put("auto_accept_notification", 1);
        assertThrows(ContractViolationException.class, () -> parse(wrongBoolean));
        ObjectNode unknown = request("known"); ((ObjectNode) unknown.get("context")).put("status", "success");
        assertThrows(ContractViolationException.class, () -> parse(unknown));
    }

    @Test void signedGenerationIdsAndFullNumericUint64SurviveWithoutDoubleConversion() throws IOException {
        assertEquals(Integer.MIN_VALUE, parse(request("signed_pending")).pending().instanceId());
        for (String invalid : List.of("-2147483649", "2147483648", "-1", "1.0", "1e0", "true")) {
            byte[] wire = rawToken(request("known"), "pending", "instance_id", invalid);
            assertTrue(new String(wire, StandardCharsets.UTF_8).contains("\"instance_id\":" + invalid));
            assertThrows(ContractViolationException.class, () -> InteractionFallbackCodec.parseRequest(wire), invalid);
        }
        ObjectNode max = request("known"); ObjectNode b = (ObjectNode) max.get("binding"); ObjectNode c = (ObjectNode) max.get("context");
        for (String field : List.of("revision", "native_revision", "date_raw", "connection_generation")) { b.put(field, StrictJson.UINT64_MAX); }
        c.put("snapshot_revision", StrictJson.UINT64_MAX); c.put("date_raw", StrictJson.UINT64_MAX);
        Request parsed = parse(max); assertEquals(StrictJson.UINT64_MAX, parsed.binding().revision());
        assertEquals(parsed, InteractionFallbackCodec.parseRequest(InteractionFallbackCodec.encodeRequest(parsed)));
        assertEquals(Disposition.CANDIDATE, InteractionFallbackPlanner.plan(parsed).disposition());
        b.put("revision", StrictJson.UINT64_MAX.add(BigInteger.ONE));
        assertThrows(ContractViolationException.class, () -> parse(max));
    }

    @Test void codecRejectsDuplicatesMalformedUtf8TrailingTokensAndOversize() throws IOException {
        String valid = new String(StrictJson.canonical(request("known")), StandardCharsets.UTF_8);
        String duplicated = valid.replaceFirst("\\{", "{\"schema\":\"duplicated\",");
        assertThrows(ContractViolationException.class, () -> InteractionFallbackCodec.parseRequest(duplicated.getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> InteractionFallbackCodec.parseRequest((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> InteractionFallbackCodec.parseRequest(new byte[] {(byte) 0xc0, (byte) 0xaf}));
        assertThrows(ContractViolationException.class, () -> InteractionFallbackCodec.parseRequest(new byte[InteractionFallbackCodec.MAX_BYTES + 1]));
    }

    @Test void inputIsNotMutatedAndHashMismatchRemainsUnreviewed() throws IOException {
        ObjectNode raw = request("hash_mismatch"); ObjectNode before = raw.deepCopy();
        Candidate value = InteractionFallbackPlanner.plan(parse(raw)).candidate();
        assertEquals(before, raw); assertFalse(value.registryKnown()); assertTrue(value.offlineFollowupRequired());
        assertThrows(UnsupportedOperationException.class, () -> value.replyOptions().clear());
        JsonNode output = StrictJson.parse(InteractionFallbackCodec.encodeResult(new Result(Disposition.CANDIDATE, value)));
        assertFalse(output.get("candidate").get("semantic_optimal").booleanValue());
        assertFalse(output.get("candidate").get("native_ai_equivalent").booleanValue());
    }

    // Valid object helper only. Negative raw number tests must never round-trip a parsed DecimalNode.
    private static Request parse(ObjectNode raw) { return InteractionFallbackCodec.parseRequest(raw.toString().getBytes(StandardCharsets.UTF_8)); }
    private static JsonNode golden() throws IOException {
        try (var stream = InteractionFallbackTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(stream, "committed golden resource is required"); return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode request(String name) throws IOException {
        for (JsonNode row : golden().get("cases")) { if (row.get("name").textValue().equals(name)) { return ((ObjectNode) row.get("request")).deepCopy(); } }
        throw new AssertionError("missing golden " + name);
    }
    private static byte[] rawToken(ObjectNode original, String parent, String field, String token) {
        ObjectNode changed = original.deepCopy();
        String marker = "__interaction_fallback_test_raw_token__";
        ((ObjectNode) changed.get(parent)).put(field, marker);
        String encoded = changed.toString();
        assertEquals(encoded.indexOf(marker), encoded.lastIndexOf(marker), "unique raw-token marker required");
        // Raw literals reach parseRequest unchanged: Jackson's DecimalNode rendering would turn 1.0 into 1.
        return encoded.replace("\"" + marker + "\"", token).getBytes(StandardCharsets.UTF_8);
    }
}
