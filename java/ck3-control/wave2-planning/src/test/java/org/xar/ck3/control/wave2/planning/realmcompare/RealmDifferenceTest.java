package org.xar.ck3.control.wave2.planning.realmcompare;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
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
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

final class RealmDifferenceTest {
    @Test void actualProducerObservationsAndEveryCapturedRejectionRemainEquivalent() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java-realmcompare-producer-golden/v1", golden.path("schema").asText());
        assertEquals(24, golden.path("cases").size());
        for (JsonNode row : golden.path("cases")) {
            ObjectNode request = (ObjectNode) row.get("request");
            RealmDifference result = RealmDifference.compare(request.get("previous"), request.get("observation"));
            assertEquals(row.path("expected").get("value"), RealmDifferenceCodec.parsedResult(result), row.path("id").asText());
            assertEquals(RealmDifferenceCodec.parsedResult(result), StrictJson.parse(RealmDifferenceCodec.evaluate(StrictJson.canonical(request))));
        }
    }

    @Test void fullGeneratedIdentityAndCompleteEmptySetAreNeverConfusedWithMissingEvidence() throws IOException {
        ObjectNode request = request("generation-id-not-storage-index");
        JsonNode result = RealmDifferenceCodec.parsedResult(RealmDifference.compare(request.get("previous"), request.get("observation")));
        assertEquals(new BigInteger("16777227"), result.path("lost_county_title_ids").get(0).bigIntegerValue());
        assertEquals(new BigInteger("11"), result.path("gained_county_title_ids").get(0).bigIntegerValue());
        ObjectNode empty = request("complete-empty-after");
        assertEquals("available", RealmDifference.compare(empty.get("previous"), empty.get("observation")).toJson().path("status").asText());
        JsonNode absent = RealmDifference.compare(null, empty.get("observation")).toJson();
        assertTrue(absent.get("lost_county_title_ids").isNull());
        assertTrue(absent.get("gained_county_title_ids").isNull());
        assertTrue(!absent.has("before_source_frame"));
    }

    @Test void wrongNumericTokensCannotAliasOwnerRevisionsOrCollectionIds() throws IOException {
        ObjectNode request = request("real-loss");
        ObjectNode previous = (ObjectNode) request.get("previous");
        for (String token : List.of("true", "1.0", "\"1\"")) {
            JsonNode value = StrictJson.parse(bytes(token));
            ((ObjectNode) previous.get("source_frame")).set("bridge_pid", value);
            ((ObjectNode) ((ObjectNode) request.get("observation")).get("source_frame")).set("bridge_pid", value);
            assertInstanceOf(RealmDifference.Unavailable.class, RealmDifference.compare(previous, request.get("observation")));
        }
        ObjectNode fresh = request("real-loss");
        ObjectNode component = (ObjectNode) ((ObjectNode) fresh.get("previous")).get("component");
        component.putArray("county_title_ids").add(StrictJson.parse(bytes("2231.0")));
        assertEquals("unavailable", RealmDifference.compare(fresh.get("previous"), fresh.get("observation")).toJson().path("status").asText());
    }

    @Test void exactComponentRoundTripAndSourceFrameCopiesAreImmutable() throws IOException {
        ObjectNode request = request("real-loss");
        RealmObservation current = RealmObservation.parse(request.get("observation"));
        SubrealmCounties component = current.component();
        SubrealmCounties restored = SubrealmCounties.parse(StrictJson.parse(StrictJson.canonical(component.toJson())),
                component.actorCharacterId(), component.nativeRevision(), component.dateRaw());
        assertEquals(component, restored);
        assertThrows(UnsupportedOperationException.class, () -> component.countyTitleIds().clear());
        String episode = current.frame().episodeRunId();
        current.sourceFrame().put("episode_run_id", "mutated");
        assertEquals(episode, current.sourceFrame().path("episode_run_id").asText());
        RealmDifference.Available difference = assertInstanceOf(RealmDifference.Available.class,
                RealmDifference.compare(request.get("previous"), request.get("observation")));
        difference.beforeSourceFrame().put("snapshot_id", "changed");
        assertTrue(!difference.toJson().path("before_source_frame").path("snapshot_id").asText().equals("changed"));
    }

    @Test void bothNativeSizedSetsFitTheCollectionProfileAndPreserveItsRealCountLimit() throws IOException {
        ObjectNode request = request("real-loss");
        ObjectNode before = (ObjectNode) ((ObjectNode) request.get("previous")).get("component");
        ObjectNode after = (ObjectNode) ((ObjectNode) request.get("observation")).get("component");
        ArrayNode oldIds = before.putArray("county_title_ids");
        ArrayNode newIds = after.putArray("county_title_ids");
        IntStream.rangeClosed(1, 16_384).forEach(oldIds::add);
        IntStream.rangeClosed(20_000, 36_383).forEach(newIds::add);
        byte[] input = new ObjectMapper().writeValueAsBytes(request);
        assertTrue(input.length > StrictJson.INPUT_MAX_BYTES);
        RealmDifference.Available result = assertInstanceOf(RealmDifference.Available.class, RealmDifferenceCodec.decodeAndCompare(input));
        assertEquals(16_384, result.lostCountyTitleIds().size());
        assertEquals(16_384, result.gainedCountyTitleIds().size());
        assertTrue(RealmDifferenceCodec.encode(result).length < RealmDifferenceCodec.MAX_BYTES);
        oldIds.add(16_385);
        assertInstanceOf(RealmDifference.Unavailable.class, RealmDifferenceCodec.decodeAndCompare(new ObjectMapper().writeValueAsBytes(request)));
    }

    @Test void strictJsonEntryRejectsDuplicateMissingUnknownInvalidUtf8AndOversizedPayload() {
        for (String raw : List.of("{\"previous\":null}",
                "{\"previous\":null,\"observation\":null,\"extra\":0}",
                "{\"previous\":null,\"previous\":null,\"observation\":null}")) {
            assertThrows(IllegalArgumentException.class, () -> RealmDifferenceCodec.evaluate(bytes(raw)));
        }
        assertThrows(IllegalArgumentException.class, () -> RealmDifferenceCodec.evaluate(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> RealmDifferenceCodec.evaluate(new byte[RealmDifferenceCodec.MAX_BYTES + 1]));
    }


    @Test void originalGoldenIsBoundToTheImmutableProducerAndActualUnchangedFixtureSources() throws IOException {
        JsonNode captured = golden();
        assertTrue(captured.path("machine_id").isTextual() && !captured.path("machine_id").textValue().isBlank());
        assertTrue(captured.path("observed_at_utc").isTextual() && !captured.path("observed_at_utc").textValue().isBlank());
        assertEquals(10, captured.path("original_test_count").intValue());
        assertEquals(0, captured.path("original_test_skipped").intValue());
        assertSourceBindings(captured, List.of(
                "ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/player_faction_alerts_contract.py",
                "ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py",
                "ck3_autonomous_player/tests/unit/test_realm_membership_feedback_v1.py",
                "tools/ck3_live_run_id.py",
                "java/ck3-control/wave2-planning/src/test/resources/realmcompare/producer-spec.json"));
    }

    @Test void rawEntryPreservesOpaqueFloatBooleanAndLargeIntegerTokensInBothFrames() throws IOException {
        for (String token : List.of("1.0", "true", "9007199254740993")) {
            ObjectNode input = request("real-loss");
            ((ObjectNode) input.path("previous").get("source_frame")).put("sdk_extension", "__RAW_TOKEN__");
            ((ObjectNode) input.path("observation").get("source_frame")).put("sdk_extension", "__RAW_TOKEN__");
            byte[] raw = withRawToken(input, token);
            JsonNode encoded = StrictJson.parse(RealmDifferenceCodec.evaluate(raw), RealmDifferenceCodec.MAX_BYTES);
            assertEquals("available", encoded.path("status").textValue());
            assertTokenDomain(encoded.path("before_source_frame").get("sdk_extension"), token);
            assertTokenDomain(encoded.path("after_source_frame").get("sdk_extension"), token);
        }
    }

    @Test void rawIntegerAliasesReachTheActualEntryWithoutTreeReserialization() throws IOException {
        for (String token : List.of("true", "44.0", "\"44\"")) {
            ObjectNode input = request("real-loss");
            ((ObjectNode) input.path("previous").get("source_frame")).put("bridge_pid", "__RAW_TOKEN__");
            ((ObjectNode) input.path("observation").get("source_frame")).put("bridge_pid", "__RAW_TOKEN__");
            JsonNode output = StrictJson.parse(RealmDifferenceCodec.evaluate(withRawToken(input, token)));
            assertEquals("unavailable", output.path("status").textValue(), token);
        }
        for (String token : List.of("true", "2231.0", "\"2231\"")) {
            ObjectNode input = request("real-loss");
            ((ObjectNode) input.path("previous").get("component")).putArray("county_title_ids").add("__RAW_TOKEN__");
            JsonNode output = StrictJson.parse(RealmDifferenceCodec.evaluate(withRawToken(input, token)));
            assertEquals("unavailable", output.path("status").textValue(), token);
        }
    }

    @Test void rawUtf8InputUsesTheExplicit512KiBBudgetWithoutWideningTheDefaultParser() {
        String json = "{\"previous\":null,\"observation\":{\"sdk_note\":\"界\"}}";
        assertTrue(bytes(json).length > json.length());
        for (int length : List.of(RealmDifferenceCodec.MAX_BYTES - 1, RealmDifferenceCodec.MAX_BYTES)) {
            byte[] raw = paddedRawInput(json, length);
            assertEquals("unavailable", StrictJson.parse(RealmDifferenceCodec.evaluate(raw)).path("status").textValue());
            assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(raw));
        }
        byte[] over = paddedRawInput(json, RealmDifferenceCodec.MAX_BYTES + 1);
        assertThrows(IllegalArgumentException.class, () -> RealmDifferenceCodec.evaluate(over));
    }

    @Test void utf8OutputFitsAt512KiBAndRejectsOneByteOverWithoutWideningSdkDefault() throws IOException {
        for (int length : List.of(RealmDifferenceCodec.MAX_BYTES - 1, RealmDifferenceCodec.MAX_BYTES)) {
            RealmDifference.Available result = paddedDifference(length);
            byte[] raw = RealmDifferenceCodec.encode(result);
            assertEquals(length, raw.length);
            assertTrue(raw.length > new String(raw, StandardCharsets.UTF_8).length());
            assertEquals(result.beforeSourceFrame().get("sdk_padding"),
                    StrictJson.parse(raw, RealmDifferenceCodec.MAX_BYTES).path("before_source_frame").get("sdk_padding"));
            assertThrows(IllegalArgumentException.class, () -> SdkProjectionJson.encode(result.toJson()));
        }
        RealmDifference.Available over = paddedDifference(RealmDifferenceCodec.MAX_BYTES + 1);
        assertThrows(IllegalArgumentException.class, () -> RealmDifferenceCodec.encode(over));
    }

    private static RealmDifference.Available paddedDifference(int targetBytes) throws IOException {
        ObjectNode request = request("real-loss");
        RealmDifference.Available original = assertInstanceOf(RealmDifference.Available.class,
                RealmDifference.compare(request.get("previous"), request.get("observation")));
        ObjectNode before = original.beforeSourceFrame(), after = original.afterSourceFrame();
        ArrayNode padding = before.putArray("sdk_padding");
        RealmDifference.Available base = new RealmDifference.Available(original.lostCountyTitleIds(),
                original.gainedCountyTitleIds(), before, after);
        addUtf8Padding(padding, targetBytes - RealmDifferenceCodec.encode(base).length);
        return new RealmDifference.Available(original.lostCountyTitleIds(), original.gainedCountyTitleIds(), before, after);
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
        try (InputStream stream = RealmDifferenceTest.class.getResourceAsStream("/realmcompare/java-consumer-bindings-v1.json")) {
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
        try (InputStream stream = RealmDifferenceTest.class.getResourceAsStream("/realmcompare/original-oracle-sources-v1.json")) {
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
        try (InputStream stream = RealmDifferenceTest.class.getResourceAsStream("/realmcompare/producer-golden.json")) {
            if (stream == null) { throw new IOException("actual producer observation/difference capture required; never skip"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode request(String id) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (id.equals(row.path("id").asText())) { return ((ObjectNode) row.get("request")).deepCopy(); }
        }
        throw new IOException("actual producer case missing: " + id);
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}

