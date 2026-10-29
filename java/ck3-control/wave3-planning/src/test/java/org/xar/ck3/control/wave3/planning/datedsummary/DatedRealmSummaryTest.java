package org.xar.ck3.control.wave3.planning.datedsummary;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.io.ByteArrayInputStream;
import java.util.Base64;
import java.util.HashSet;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifferenceCodec;
import org.xar.ck3.control.wave3.planning.realmmembership.RealmMembershipFeedback;
import org.xar.ck3.control.wave3.planning.realmmembership.RealmMembershipFeedback.VerifiedFeedback;

final class DatedRealmSummaryTest {
    @Test void realPrivateSummaryProducerMatchesCurrentHistoricalMissingAndRepeatedCases() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java-datedsummary-producer-golden/v1", golden.path("schema").asText());
        assertEquals(12, golden.path("cases").size());
        for (JsonNode row : golden.path("cases")) {
            byte[] input = new ObjectMapper().writeValueAsBytes(row.get("request"));
            assertEquals(row.path("expected").get("value"), StrictJson.parse(DatedSummaryCodec.evaluate(input)), row.path("id").asText());
        }
    }

    @Test void datedProjectionDoesNotRelabelAFormerObservationAsCurrent() throws IOException {
        JsonNode current = summary("current-loss");
        JsonNode historical = summary("historical-revision");
        assertEquals("current", current.path("status").asText());
        assertEquals("historical", historical.path("status").asText());
        assertTrue(historical.get("current_realm_county_count").isNull());
        assertEquals(current.get("last_observed_realm_county_count"), historical.get("last_observed_realm_county_count"));
        assertEquals(current.get("source_frame"), historical.get("source_frame"));
        assertEquals(current.get("query_sequence"), historical.get("query_sequence"));
        assertEquals(0, historical.path("new_RPC_calls").intValue());
        assertTrue(historical.get("cause").isNull());
    }

    @Test void unknownLossAndObservedEmptyDifferenceAreDifferentAndLongListsStayBounded() throws IOException {
        JsonNode first = summary("first-observation"), same = summary("same-set"), longLoss = summary("long-loss");
        assertTrue(first.get("loss_observed").isNull());
        assertTrue(first.get("lost_county_count").isNull());
        assertEquals(false, same.path("loss_observed").booleanValue());
        assertEquals(0, same.path("lost_county_count").intValue());
        assertEquals(12, longLoss.path("lost_county_count").intValue());
        assertEquals(8, longLoss.path("lost_county_title_ids_first8").size());
        assertTrue(longLoss.path("loss_list_truncated").booleanValue());
        assertTrue(summary("repeated-observation").get("loss_observed").isNull());
    }

    @Test void availableFlagCannotReplaceActualObservationComponentAndDifferenceBindings() throws IOException {
        ObjectNode request = request("current-loss");
        ObjectNode feedback = (ObjectNode) request.get("feedback");
        ((ObjectNode) ((ObjectNode) feedback.get("observation")).get("component")).put("complete", false);
        assertThrows(IllegalArgumentException.class, () -> decode(request));
        ObjectNode changedFrame = request("current-loss");
        ((ObjectNode) ((ObjectNode) ((ObjectNode) changedFrame.get("feedback")).get("difference")).get("after_source_frame"))
                .put("bridge_pid", 99);
        assertThrows(IllegalArgumentException.class, () -> decode(changedFrame));
        ObjectNode impossibleLoss = request("current-loss");
        ((ObjectNode) ((ObjectNode) impossibleLoss.get("feedback")).get("difference")).putArray("lost_county_title_ids").add(2231);
        assertThrows(IllegalArgumentException.class, () -> decode(impossibleLoss));
    }

    @Test void integerAliasesAreRejectedAndSourceOutputIsDefensivelyRecreated() throws IOException {
        for (String token : List.of("true", "2488.0", "\"2488\"")) {
            ObjectNode request = request("current-loss");
            ObjectNode difference = (ObjectNode) ((ObjectNode) request.get("feedback")).get("difference");
            difference.putArray("lost_county_title_ids").add(StrictJson.parse(bytes(token)));
            JsonNode transported = StrictJson.parse(SdkProjectionJson.encode(request, RealmDifferenceCodec.MAX_BYTES),
                    RealmDifferenceCodec.MAX_BYTES).path("feedback").path("difference").path("lost_county_title_ids").get(0);
            assertEquals(StrictJson.parse(bytes(token)).getNodeType(), transported.getNodeType());
            assertEquals(StrictJson.parse(bytes(token)).isFloatingPointNumber(), transported.isFloatingPointNumber());
            assertThrows(IllegalArgumentException.class, () -> decode(request));
        }
        DatedRealmSummary.Retained retained = assertInstanceOf(DatedRealmSummary.Retained.class, decode(request("current-loss")));
        ObjectNode original = retained.toJson();
        ((ObjectNode) original.get("source_frame")).put("snapshot_id", "changed");
        assertTrue(!retained.toJson().path("source_frame").path("snapshot_id").asText().equals("changed"));
        JsonNode serialized = DatedSummaryCodec.parsedResult(retained);
        assertEquals(serialized, StrictJson.parse(DatedSummaryCodec.encode(retained)));
    }

    @Test void narrowRequestRejectsUnknownMissingDuplicateAndInvalidUtf8() {
        for (String input : List.of("{\"feedback\":null}", "{\"feedback\":null,\"current_source_frame\":null,\"extra\":0}",
                "{\"feedback\":null,\"feedback\":null,\"current_source_frame\":null}")) {
            assertThrows(IllegalArgumentException.class, () -> DatedSummaryCodec.evaluate(bytes(input)));
        }
        assertThrows(IllegalArgumentException.class, () -> DatedSummaryCodec.evaluate(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test void actualOriginalQueryInputsPassWholeSharedFactoryBeforeTypedSummaryConsumption() throws IOException {
        assertEquals(0, VerifiedFeedback.class.getConstructors().length);
        int verified = 0;
        for (JsonNode row : golden().path("cases")) {
            if (!row.has("verified_feedback_input")) { continue; }
            RealmMembershipFeedback.Result result = RealmMembershipFeedback.project(
                    new ObjectMapper().writeValueAsBytes(row.get("verified_feedback_input")));
            VerifiedFeedback fact = assertInstanceOf(VerifiedFeedback.class, result, row.path("id").asText());
            DatedRealmSummary.Result summary = DatedRealmSummary.fromVerified(fact,
                    new ObjectMapper().writeValueAsBytes(row.path("request").get("current_source_frame")));
            assertEquals(row.path("expected").get("value"), DatedSummaryCodec.parsedResult(summary), row.path("id").asText());
            assertEquals(DatedRealmSummary.Status.HISTORICAL,
                    assertInstanceOf(DatedRealmSummary.Retained.class, DatedRealmSummary.fromVerified(fact, bytes("null"))).status());
            verified++;
        }
        assertEquals(3, verified, "three original upstream query inputs must execute the real Java factory");
        assertThrows(IllegalArgumentException.class, () -> DatedRealmSummary.fromVerified(null, bytes("null")));
    }

    @Test void realFeedbackFactoryAndSummaryRetainSdkExtensionFloatingDomain() throws IOException {
        JsonNode original = null;
        for (JsonNode row : golden().path("cases")) {
            if (row.path("id").asText().equals("current-loss")) { original = row; break; }
        }
        assertTrue(original != null && original.has("verified_feedback_input"));
        ObjectNode producerInput = ((ObjectNode) original.get("verified_feedback_input")).deepCopy();
        ObjectNode source = (ObjectNode) producerInput.get("source_frame");
        source.put("sdk_extension", 1.0);
        VerifiedFeedback verified = assertInstanceOf(VerifiedFeedback.class,
                RealmMembershipFeedback.project(new ObjectMapper().writeValueAsBytes(producerInput)));
        DatedRealmSummary.Retained result = assertInstanceOf(DatedRealmSummary.Retained.class,
                DatedRealmSummary.fromVerified(verified, new ObjectMapper().writeValueAsBytes(source)));
        assertEquals(DatedRealmSummary.Status.CURRENT, result.status());
        JsonNode reparsed = DatedSummaryCodec.parsedResult(result);
        assertTrue(reparsed.path("source_frame").path("sdk_extension").isFloatingPointNumber());
        assertEquals(reparsed, StrictJson.parse(DatedSummaryCodec.encode(result)));
        ObjectNode changedDomain = source.deepCopy(); changedDomain.put("sdk_extension", 1);
        assertEquals(DatedRealmSummary.Status.HISTORICAL,
                assertInstanceOf(DatedRealmSummary.Retained.class, DatedRealmSummary.fromVerified(verified,
                        new ObjectMapper().writeValueAsBytes(changedDomain))).status());
    }


    @Test void originalGoldenIsBoundToTheImmutablePrivateProducerAndActualUnchangedFixtureSources() throws IOException {
        JsonNode captured = golden();
        assertTrue(captured.path("machine_id").isTextual() && !captured.path("machine_id").textValue().isBlank());
        assertTrue(captured.path("observed_at_utc").isTextual() && !captured.path("observed_at_utc").textValue().isBlank());
        assertEquals(7, captured.path("original_test_count").intValue());
        assertEquals(0, captured.path("original_test_skipped").intValue());
        assertEquals(3, captured.path("verified_feedback_input_count").intValue());
        assertSourceBindings(captured, List.of(
                "ck3_autonomous_player/src/xar_autoplayer/bridge/realm_membership_after_query_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/player_faction_alerts_contract.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py",
                "ck3_autonomous_player/tests/unit/test_realm_membership_after_query_v1.py",
                "ck3_autonomous_player/tests/unit/test_realm_membership_feedback_v1.py",
                "tools/ck3_live_run_id.py",
                "java/ck3-control/wave3-planning/src/test/resources/datedsummary/producer-spec.json"));
    }

    @Test void rawSummaryEntryPreservesOpaqueFloatBooleanAndLargeIntegerTokens() throws IOException {
        for (String token : List.of("1.0", "true", "9007199254740993")) {
            ObjectNode input = request("current-loss");
            ObjectNode feedback = (ObjectNode) input.get("feedback");
            ((ObjectNode) input.get("current_source_frame")).put("sdk_extension", "__RAW_TOKEN__");
            ((ObjectNode) feedback.path("observation").get("source_frame")).put("sdk_extension", "__RAW_TOKEN__");
            ((ObjectNode) feedback.path("difference").get("before_source_frame")).put("sdk_extension", "__RAW_TOKEN__");
            ((ObjectNode) feedback.path("difference").get("after_source_frame")).put("sdk_extension", "__RAW_TOKEN__");
            JsonNode output = StrictJson.parse(DatedSummaryCodec.evaluate(withRawToken(input, token)), RealmDifferenceCodec.MAX_BYTES);
            assertEquals("current", output.path("status").textValue());
            assertTokenDomain(output.path("source_frame").get("sdk_extension"), token);
            assertTokenDomain(output.path("before_source_frame").get("sdk_extension"), token);
        }
    }

    @Test void rawLossIdAliasesReachTheActualSummaryEntryWithoutTreeReserialization() throws IOException {
        for (String token : List.of("true", "2488.0", "\"2488\"")) {
            ObjectNode input = request("current-loss");
            ((ObjectNode) input.path("feedback").get("difference")).putArray("lost_county_title_ids").add("__RAW_TOKEN__");
            byte[] raw = withRawToken(input, token);
            assertThrows(IllegalArgumentException.class, () -> DatedSummaryCodec.evaluate(raw), token);
        }
    }

    @Test void rawUtf8SummaryInputUses512KiBWithoutWideningTheSharedDefaultParser() {
        String json = "{\"feedback\":null,\"current_source_frame\":{\"sdk_note\":\"界\"}}";
        assertTrue(bytes(json).length > json.length());
        for (int length : List.of(RealmDifferenceCodec.MAX_BYTES - 1, RealmDifferenceCodec.MAX_BYTES)) {
            byte[] raw = paddedRawInput(json, length);
            assertEquals("unavailable", StrictJson.parse(DatedSummaryCodec.evaluate(raw)).path("status").textValue());
            assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(raw));
        }
        byte[] over = paddedRawInput(json, RealmDifferenceCodec.MAX_BYTES + 1);
        assertThrows(IllegalArgumentException.class, () -> DatedSummaryCodec.evaluate(over));
    }

    @Test void verifiedFactorySummaryUtf8OutputFits512KiBAndRejectsTheNextByte() throws IOException {
        for (int length : List.of(RealmDifferenceCodec.MAX_BYTES - 1, RealmDifferenceCodec.MAX_BYTES)) {
            DatedRealmSummary.Result result = paddedSummary(length);
            byte[] raw = DatedSummaryCodec.encode(result);
            assertEquals(length, raw.length);
            assertTrue(raw.length > new String(raw, StandardCharsets.UTF_8).length());
            assertEquals(result.toJson().path("source_frame").get("sdk_padding"),
                    StrictJson.parse(raw, RealmDifferenceCodec.MAX_BYTES).path("source_frame").get("sdk_padding"));
            assertThrows(IllegalArgumentException.class, () -> SdkProjectionJson.encode(result.toJson()));
        }
        DatedRealmSummary.Result over = paddedSummary(RealmDifferenceCodec.MAX_BYTES + 1);
        assertThrows(IllegalArgumentException.class, () -> DatedSummaryCodec.encode(over));
    }

    private static DatedRealmSummary.Result paddedSummary(int targetBytes) throws IOException {
        JsonNode original = null;
        for (JsonNode row : golden().path("cases")) {
            if (row.path("id").textValue().equals("first-observation")) { original = row.get("verified_feedback_input"); break; }
        }
        assertTrue(original instanceof ObjectNode, "actual first-observation producer input required");
        ObjectNode producerInput = ((ObjectNode) original).deepCopy();
        ObjectNode source = (ObjectNode) producerInput.get("source_frame");
        ArrayNode padding = source.putArray("sdk_padding");
        DatedRealmSummary.Result base = verifiedSummary(producerInput, source);
        addUtf8Padding(padding, targetBytes - DatedSummaryCodec.encode(base).length);
        return verifiedSummary(producerInput, source);
    }

    private static DatedRealmSummary.Result verifiedSummary(ObjectNode producerInput, ObjectNode source) {
        VerifiedFeedback verified = assertInstanceOf(VerifiedFeedback.class,
                RealmMembershipFeedback.project(SdkProjectionJson.encode(producerInput, RealmMembershipFeedback.MAX_BYTES)));
        return DatedRealmSummary.fromVerified(verified, SdkProjectionJson.encode(source, RealmDifferenceCodec.MAX_BYTES));
    }

    /** Add exactly this many UTF-8 wire bytes to an initially empty JSON array. */
    private static void addUtf8Padding(ArrayNode padding, int additionalBytes) {
        if (additionalBytes < 2) { throw new IllegalArgumentException("padding needs a JSON string"); }
        int remaining = additionalBytes;
        while (remaining > 0) {
            int punctuation = padding.isEmpty() ? 2 : 3;
            int content = Math.min(32_766, remaining - punctuation);
            int tail = remaining - punctuation - content;
            if (tail > 0 && tail < 3) { content -= 3; }
            if (content < 0) { throw new IllegalArgumentException("invalid padding remainder"); }
            padding.add("界".repeat(content / 3) + "x".repeat(content % 3));
            remaining -= content + punctuation;
        }
    }

    private static byte[] paddedRawInput(String json, int targetBytes) {
        byte[] prefix = bytes(json);
        assertTrue(prefix.length < targetBytes);
        byte[] raw = Arrays.copyOf(prefix, targetBytes);
        Arrays.fill(raw, prefix.length, raw.length, (byte) ' ');
        return raw;
    }

    private static byte[] withRawToken(ObjectNode input, String token) throws IOException {
        String json = new ObjectMapper().writeValueAsString(input);
        assertTrue(json.contains("\"__RAW_TOKEN__\""), "raw token marker must be present");
        return bytes(json.replace("\"__RAW_TOKEN__\"", token));
    }

    private static void assertTokenDomain(JsonNode value, String token) {
        assertEquals(StrictJson.parse(bytes(token)), value);
        if (token.equals("1.0")) { assertTrue(value.isFloatingPointNumber()); }
        else if (token.equals("true")) { assertTrue(value.isBoolean()); }
        else { assertTrue(value.isIntegralNumber()); assertEquals(new BigInteger(token), value.bigIntegerValue()); }
    }

    private static void assertSourceBindings(JsonNode golden, List<String> expectedPaths) throws IOException {
        JsonNode refs = golden.get("source_refs");
        assertTrue(refs != null && refs.isArray(), "actual golden must retain source refs");
        assertEquals(expectedPaths.size(), refs.size(), "complete original source closure");
        assertEquals(refs.get(0), golden.get("producer"), "producer must be the pinned original entry");
        Path root = repositoryRoot();
        for (String relative : expectedPaths) {
            JsonNode selected = null; int matches = 0;
            for (JsonNode ref : refs) {
                assertTrue(ref.path("path").isTextual());
                String recorded = ref.path("path").textValue().replace('\\', '/');
                if (recorded.equals(relative) || recorded.endsWith("/" + relative)) { selected = ref; matches++; }
            }
            assertEquals(1, matches, "one current source ref required: " + relative);
            assertTrue(selected != null && selected.path("bytes").isIntegralNumber());
            assertTrue(selected.path("sha256").isTextual() && selected.path("sha256").textValue().matches("[0-9a-f]{64}"));
            byte[] actual = originalSource(root, relative);
            assertEquals(BigInteger.valueOf(actual.length), selected.path("bytes").bigIntegerValue(), relative + " source bytes");
            assertEquals(selected.path("sha256").textValue(), sha256(actual), relative + " source SHA");
        }
    }


    @Test void adoptedJavaConsumerSourcesArePinnedSeparatelyFromTheImmutableOriginalOracle() throws IOException {
        JsonNode bindings;
        try (InputStream stream = DatedRealmSummaryTest.class.getResourceAsStream("/datedsummary/java-consumer-bindings-v1.json")) {
            if (stream == null) { throw new IOException("actual candidate consumer source bindings required; never skip"); }
            bindings = StrictJson.parse(stream.readAllBytes());
        }
        assertEquals("xar.ck3.realm-java-consumer-source-bindings/v1", bindings.path("schema").textValue());
        Set<String> expected = Set.of(
                "ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/realm_membership_after_query_v1.py",
                "java/ck3-control/wave2-planning/src/main/java/org/xar/ck3/control/wave2/planning/realmcompare/RealmDifferenceCodec.java",
                "java/ck3-control/wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/datedsummary/DatedSummaryCodec.java",
                "java/ck3-control/wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/realmmembership/RealmMembershipFeedback.java",
                "java/ck3-control/wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/realmmembership/RealmFeedbackApplication.java",
                "java/ck3-control/wave3-planning/src/main/java/org/xar/ck3/control/wave3/planning/realmmembership/RealmProjectionCatalog.java",
                "tools/g2_saved_campaign/java_map_admission_client_v1.py");
        Set<String> seen = new HashSet<>();
        Path root = repositoryRoot();
        String cash = "ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py";
        Set<String> completeOrigins = new HashSet<>(expected); completeOrigins.add(cash);
        java.util.Map<String, Path> origins = candidateSources(root, completeOrigins);
        for (JsonNode ref : bindings.path("candidate_source_refs")) {
            String relative = StrictJson.text(ref.get("path"));
            assertTrue(expected.contains(relative) && seen.add(relative), "one exact current candidate path");
            Path path = origins.get(relative);
            byte[] actual = Files.readAllBytes(path);
            assertTrue(ref.path("bytes").isIntegralNumber());
            assertEquals(ref.path("bytes").bigIntegerValue(), BigInteger.valueOf(actual.length), relative + " candidate bytes");
            assertEquals(ref.path("sha256").textValue(), sha256(actual), relative + " candidate SHA");
        }
        assertEquals(expected, seen, "all actual adapter, application, codec, catalog and sole-client sources");
        JsonNode related = bindings.get("related_consumer_source_refs");
        assertTrue(related != null && related.isArray());
        assertEquals(1, related.size(), "actual cash adapter is part of the consumer source closure");
        JsonNode cashRef = related.get(0);
        assertEquals(cash, StrictJson.text(cashRef.get("path")));
        byte[] actualCash = Files.readAllBytes(origins.get(cash));
        assertEquals(StrictJson.integer(cashRef.get("bytes"), BigInteger.ONE, BigInteger.valueOf(1_048_576)),
                BigInteger.valueOf(actualCash.length));
        assertEquals(StrictJson.text(cashRef.get("sha256")), sha256(actualCash));
    }

    /** Original producer and selected candidate may have different explicitly declared origins. */
    private static java.util.Map<String, Path> candidateSources(Path root, Set<String> expected) throws IOException {
        String configured = System.getenv("XAR_CANDIDATE_SOURCE_ORIGINS");
        java.util.Map<String, Path> origins = new java.util.HashMap<>();
        if (configured == null) {
            for (String relative : expected) {
                Path path = root.resolve(relative).normalize();
                StrictJson.require(path.startsWith(root), "candidate source stays inside actual repository");
                origins.put(relative, path);
            }
        } else {
            JsonNode declaration = StrictJson.parse(Files.readAllBytes(Path.of(StrictJson.text(configured))));
            StrictJson.object(declaration, Set.of("schema", "machine_id", "observed_at_utc", "source_origins"));
            StrictJson.require("xar.ck3.candidate-source-origins/v1".equals(StrictJson.text(declaration.get("schema"))),
                    "explicit candidate origin schema required");
            StrictJson.require(StrictJson.text(declaration.get("machine_id")).equals(System.getenv("XAR_MACHINE_ID")),
                    "candidate source origins must bind the current execution machine");
            StrictJson.utc(StrictJson.text(declaration.get("observed_at_utc")));
            JsonNode rows = declaration.get("source_origins");
            StrictJson.require(rows != null && rows.isArray(), "candidate source origin array required");
            for (JsonNode row : rows) {
                StrictJson.object(row, Set.of("logical_path", "source_path"));
                String logical = StrictJson.text(row.get("logical_path"));
                Path path = Path.of(StrictJson.text(row.get("source_path"))).normalize();
                StrictJson.require(expected.contains(logical) && path.isAbsolute()
                        && origins.putIfAbsent(logical, path) == null, "one absolute origin per exact candidate source");
            }
        }
        StrictJson.require(origins.keySet().equals(expected), "complete candidate source origin closure required");
        return java.util.Map.copyOf(origins);
    }

    private static byte[] originalSource(Path root, String relative) throws IOException {
if (!relative.equals("ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py")
                && !relative.equals("ck3_autonomous_player/src/xar_autoplayer/bridge/realm_membership_after_query_v1.py")
                && !relative.equals("ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py")) {
            return Files.readAllBytes(root.resolve(relative));
        }
        JsonNode bundle;
        try (InputStream stream = DatedRealmSummaryTest.class.getResourceAsStream("/datedsummary/original-oracle-sources-v1.json")) {
            if (stream == null) { throw new IOException("immutable original oracle source resource required; never skip"); }
            bundle = StrictJson.parse(stream.readAllBytes());
        }
        assertEquals("xar.ck3.realm-original-oracle-source/v1", bundle.path("schema").textValue());
        byte[] compressed = Base64.getDecoder().decode(StrictJson.text(bundle.get("gzip_base64")));
        assertEquals(bundle.path("gzip_bytes").intValue(), compressed.length);
        assertEquals(bundle.path("gzip_sha256").textValue(), sha256(compressed));
        byte[] decoded;
        try (InputStream stream = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            decoded = stream.readNBytes(65_537);
        }
        assertTrue(decoded.length <= 65_536, "bounded test-only source archive");
        assertEquals(bundle.path("decoded_bytes").intValue(), decoded.length);
        assertEquals(bundle.path("decoded_sha256").textValue(), sha256(decoded));
        JsonNode archive = StrictJson.parse(decoded);
        assertEquals("xar.ck3.realm-original-oracle-source-members/v1", archive.path("schema").textValue());
        for (JsonNode entry : archive.path("entries")) {
            if (!relative.equals(entry.path("path").textValue())) { continue; }
            byte[] source = StrictJson.text(entry.get("source_utf8")).getBytes(StandardCharsets.UTF_8);
            assertEquals(entry.path("bytes").intValue(), source.length);
            assertEquals(entry.path("sha256").textValue(), sha256(source));
            return source;
        }
        throw new IOException("actual immutable oracle source missing: " + relative);
    }

    private static Path repositoryRoot() throws IOException {
        String configured = System.getenv("XAR_REPO_ROOT");
        if (configured != null && !configured.isBlank()) {
            Path root = Path.of(configured).toAbsolutePath().normalize();
            if (!Files.isDirectory(root.resolve("ck3_autonomous_player/src"))) { throw new IOException("XAR_REPO_ROOT lacks original sources"); }
            return root;
        }
        for (Path root = Path.of("").toAbsolutePath().normalize(); root != null; root = root.getParent()) {
            if (Files.isDirectory(root.resolve("ck3_autonomous_player/src"))) { return root; }
        }
        throw new IOException("original source root required for golden bindings; set XAR_REPO_ROOT");
    }

    private static String sha256(byte[] value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (NoSuchAlgorithmException error) { throw new AssertionError(error); }
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = DatedRealmSummaryTest.class.getResourceAsStream("/datedsummary/producer-golden.json")) {
            if (stream == null) { throw new IOException("real private-summary producer capture required; never skip"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode request(String id) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (id.equals(row.path("id").asText())) { return ((ObjectNode) row.get("request")).deepCopy(); }
        }
        throw new IOException("real producer summary case missing: " + id);
    }
    private static DatedRealmSummary.Result decode(ObjectNode request) throws IOException {
        return DatedSummaryCodec.decode(SdkProjectionJson.encode(request, RealmDifferenceCodec.MAX_BYTES));
    }
    private static JsonNode summary(String id) throws IOException { return DatedSummaryCodec.parsedResult(decode(request(id))); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}

