package org.xar.ck3.control.wave3.governance.crownfinalterms;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;

final class CrownFinalTermsTest {
    @TestFactory
    Stream<DynamicTest> actualFullQueryAndCppWireConsumerGolden() throws IOException {
        JsonNode golden = golden(); assertEquals(32, golden.get("cases").size());
        assertEquals(4, golden.get("original_unittest").get("tests").intValue());
        assertEquals(0, golden.get("original_unittest").get("skipped").intValue());
        assertTrue(golden.get("source_refs_unchanged").booleanValue());
        return stream(golden.get("cases")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            ObjectNode prepare = patch(golden.get("base_prepare"), row.get("prepare_patch"));
            ObjectNode consume = patch(golden.get("base_consume"), row.get("consume_patch"));
            if (row.get("sent_count").intValue() == 0) {
                assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.prepare(raw(prepare)));
            } else {
                assertEquals(row.get("actual_request"), StrictJson.parse(CrownFinalTermsCodec.prepare(raw(prepare))));
                if (row.get("legacy_error").isNull()) {
                    assertEquals(patch(golden.get("base_readback"), row.get("expected_readback_patch")), StrictJson.parse(CrownFinalTermsCodec.consume(raw(consume))));
                } else {
                    assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(consume)));
                }
            }
        }));
    }

    @TestFactory
    Stream<DynamicTest> strictWireRejectsOriginalNumericEqualityAliases() throws IOException {
        JsonNode golden = golden(); assertEquals(4, golden.get("wire_rejections").size());
        return stream(golden.get("wire_rejections")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () ->
                assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.normalize(row.get("raw_request_json").textValue().getBytes(StandardCharsets.UTF_8)))));
    }

    @Test
    void everySigned64CostAndNativeReasonSurvivesTypedRoundtrip() throws IOException {
        ObjectNode request = consumeCase("signed64_cost_extremes_retained");
        CrownFinalTerms.Readback value = CrownFinalTermsCodec.decodeReadback(raw(request));
        assertEquals(Long.MIN_VALUE, value.payload().groups().get(0).candidates().get(1).costRaw().get(0).longValue());
        assertEquals(Long.MAX_VALUE, value.payload().groups().get(0).candidates().get(1).costRaw().get(1).longValue());
        assertEquals(StrictJson.parse(CrownFinalTermsCodec.consume(raw(request))), StrictJson.parse(CrownFinalTermsCodec.encode(value)));
        assertThrows(UnsupportedOperationException.class, () -> value.payload().groups().clear());
        assertThrows(UnsupportedOperationException.class, () -> value.payload().groups().get(0).candidates().get(0).costRaw().clear());
    }

    @Test
    void pythonReasonBoundCountsUnicodeCodePointsAndRetainsControlCharacters() throws IOException {
        ObjectNode request = payloadRequest(); ObjectNode candidate = firstCandidate(request);
        String reason = "\ud83d\udc51".repeat(4096); candidate.put("native_reason", reason);
        assertEquals(reason, CrownFinalTermsCodec.decode(raw(request)).groups().get(0).candidates().get(0).nativeReason());
        candidate.put("native_reason", reason + "x");
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.decode(raw(request)));
        candidate.put("native_reason", "\u0015 native \"reason\"\n");
        assertEquals(request.get("payload"), StrictJson.parse(CrownFinalTermsCodec.normalize(raw(request))));
    }

    @Test
    void optionalProfileSelectorsAndNonavailableSentinelRemainDistinct() throws IOException {
        ObjectNode nullable = consumeCase("nullable_native_succession_selectors");
        CrownFinalTerms.SuccessionProfile profile = CrownFinalTermsCodec.decodeReadback(raw(nullable)).payload().groups().get(1).candidates().get(1).profile();
        assertNotNull(profile); assertEquals(null, profile.order()); assertEquals(null, profile.traversal());
        ObjectNode absent = consumeCase("explicit_12004_absent_profile_and_raw_timed_counter");
        assertEquals(null, CrownFinalTermsCodec.decodeReadback(raw(absent)).payload().groups().get(1).candidates().get(0).profile());
        ObjectNode candidate = (ObjectNode) absent.get("command_result").get("result").get("realm_law_final_terms").get("groups").get(1).get("candidates").get(0);
        candidate.putObject("succession_profile");
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(absent)));
    }

    @Test
    void projectedClockRetainsItsSameQueryCountAndCannotGainPermissionFromUnitAlone() throws IOException {
        ObjectNode projected = consumeCase("explicit_12004_same_query_projected_clock");
        CrownFinalTerms.Readback readback = CrownFinalTermsCodec.decodeReadback(raw(projected));
        assertEquals(2, readback.payload().turnTick().managerMatchCount().intValueExact());
        assertEquals(readback.payload().dateRaw().add(java.math.BigInteger.valueOf(120)), readback.payload().cooldown().retryDateRaw());
        ObjectNode payload = (ObjectNode) projected.get("command_result").get("result").get("realm_law_final_terms");
        payload.remove("crown_authority_cooldown_turn_tick");
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(projected)));
    }

    @Test
    void afterWholeActorAndMapChecksCannotBeWeakenedToOneId() throws IOException {
        ObjectNode request = consumeCase("actual_cpp_serializer_fixture_query");
        ObjectNode actor = (ObjectNode) request.get("after_snapshot").get("played_character"); actor.put("new_field", "changed");
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(request)));
        actor.remove("new_field"); actor.put("character_id", true);
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(request)));
        ObjectNode sameDateNewRevision = consumeCase("later_native_revision_same_actor_date_allowed");
        assertEquals("native:later", CrownFinalTermsCodec.decodeReadback(raw(sameDateNewRevision)).postSnapshotId());
    }

    @Test
    void exactBuildPairAndArchivedLegacyRepresentationStaySeparate() throws IOException {
        ObjectNode legacy = consumeCase("archived_119_contract_without_hello");
        JsonNode result = StrictJson.parse(CrownFinalTermsCodec.consume(raw(legacy)));
        assertEquals("1.19.0.6", result.get("exact_ck3_build").textValue()); assertFalse(result.has("exe_sha256"));
        ObjectNode request = consumeCase("actual_cpp_serializer_fixture_query");
        ObjectNode hello = (ObjectNode) request.get("before_snapshot").get("diagnostics").get("hello");
        hello.put("expected_ck3_version", "1.20.0.4");
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(request)));
    }

    @Test
    void missingProtocolAndUnknownFieldsAreRejectedAndNativeRedReasonIsRetained() throws IOException {
        ObjectNode request = consumeCase("actual_cpp_serializer_fixture_query");
        ObjectNode command = (ObjectNode) request.get("command_result"); command.remove("protocol_version");
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(request)));
        ObjectNode nativeRed = consumeCase("native_red_retains_original_reason");
        assertEquals("private realm-law native RED: fixture-native-red", assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(nativeRed))).getMessage());
        ObjectNode payload = payloadRequest(); payload.put("admitted", true);
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.normalize(raw(payload)));
        ObjectNode missing = payloadRequest(); missing.remove("payload");
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.normalize(raw(missing)));
    }

    @Test
    void malformedJsonAndNumericIdentityTokensCannotEnterTheDomain() throws IOException {
        String valid = new String(raw(payloadRequest()), StandardCharsets.UTF_8);
        String field = "\"expected_revision\":" + payloadRequest().get("expected_revision");
        assertTrue(valid.contains(field));
        assertEquals(valid.indexOf(field), valid.lastIndexOf(field), "replace exactly the wrapper identity token");
        for (String token : List.of("true", "74.0", "\"74\"")) {
            byte[] outgoing = valid.replace(field, "\"expected_revision\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.normalize(outgoing), token);
        }
        String duplicate = valid.substring(0, valid.length() - 1) + ",\"exact_ck3_build\":\"1.20.0.2\"}";
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.normalize(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.normalize((valid + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.prepare(new byte[65_537]));
    }

    @Test
    void responsePrevalidationHasNoAfterFrameAndCannotGrantFullReadback() throws IOException {
        ObjectNode full = consumeCase("actual_cpp_serializer_fixture_query");
        ObjectNode response = full.deepCopy();
        response.remove("after_snapshot");
        response.put("schema", "xar.java-crown-final-terms-validate-response/v1");
        JsonNode marker = StrictJson.parse(CrownFinalTermsCodec.validateResponse(raw(response)));
        assertEquals("validated", marker.get("status").textValue());
        assertEquals(full.get("request_id"), marker.get("request_id"));
        assertEquals(full.get("expected_revision"), marker.get("expected_revision"));
        assertEquals(4, marker.size());
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(response)));
        ((ObjectNode) full.get("after_snapshot")).put("paused", false);
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.consume(raw(full)));
        ((ObjectNode) response.get("command_result")).put("request_id", "foreign");
        assertThrows(IllegalArgumentException.class, () -> CrownFinalTermsCodec.validateResponse(raw(response)));
    }

    private static ObjectNode firstCandidate(ObjectNode request) { return (ObjectNode) request.get("payload").get("groups").get(0).get("candidates").get(0); }
    private static ObjectNode payloadRequest() throws IOException {
        JsonNode golden = golden(); JsonNode readback = golden.get("base_readback"); ObjectNode request = StrictJson.object();
        request.put("schema", CrownFinalTermsCodec.PAYLOAD_SCHEMA); request.set("expected_revision", readback.get("snapshot_revision")); request.set("date_raw", readback.get("date_raw"));
        request.set("actor_character_id", readback.get("actor_character_id")); request.set("exact_ck3_build", readback.get("exact_ck3_build"));
        request.set("payload", golden.get("base_consume").get("command_result").get("result").get("realm_law_final_terms").deepCopy()); return request;
    }
    private static ObjectNode consumeCase(String name) throws IOException {
        JsonNode golden = golden(); JsonNode row = stream(golden.get("cases")).filter(item -> name.equals(item.get("name").textValue())).findFirst().orElseThrow();
        return patch(golden.get("base_consume"), row.get("consume_patch"));
    }
    private static ObjectNode patch(JsonNode base, JsonNode changes) {
        ObjectNode result = (ObjectNode) base.deepCopy();
        for (JsonNode change : changes) {
            String path = change.get("path").textValue(); int split = path.lastIndexOf('/'); ObjectNode parent = (ObjectNode) result.at(path.substring(0, split)); String key = path.substring(split + 1);
            if ("remove".equals(change.get("op").textValue())) { parent.remove(key); } else { parent.set(key, change.get("value").deepCopy()); }
        }
        return result;
    }
    private static Stream<JsonNode> stream(JsonNode array) { return StreamSupport.stream(array.spliterator(), false); }
    private static JsonNode golden() throws IOException {
        try (InputStream source = CrownFinalTermsTest.class.getResourceAsStream("/crownfinalterms/original-producer-golden.json.gz")) {
            assertNotNull(source, "committed complete original query gzip capture required; default JUnit never invokes Python");
            byte[] stored = source.readNBytes(32769);
            assertTrue(stored.length > 0 && stored.length <= 32768, "aggregate gzip budget");
            try (InputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(stored))) {
                byte[] raw = gzip.readNBytes(262145);
                assertTrue(raw.length > 0 && raw.length <= 262144, "aggregate decoded budget; production requests remain 64KiB");
                return StrictJson.parse(raw, 262144);
            }
        }
    }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
}
