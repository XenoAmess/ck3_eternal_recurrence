package org.xar.ck3.control.wave2.finance.factionalerts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatCodec;
import org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeCodec;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel.*;

class FactionAlertsCodecTest {
    @Test void unchangedWholeProducerAndAllCommittedBranchesRoundTrip() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java.faction-alerts-producer-golden/v1", golden.path("schema").textValue());
        assertFalse(golden.path("capture").path("machine_id").textValue().isBlank());
        assertFalse(golden.path("capture").path("observed_at_utc").textValue().isBlank());
        assertEquals(0, golden.path("capture").path("native_rpc_count").intValue());
        assertEquals(0, golden.path("capture").path("ledger_writes").intValue());
        assertTrue(golden.path("cases").size() >= 40);
        JsonNode consumers = golden.path("consumer_tests"); assertTrue(consumers.path("tests_run").intValue() >= 40);
        assertEquals(0, consumers.path("failures").intValue()); assertEquals(0, consumers.path("errors").intValue());
        assertEquals(0, consumers.path("skipped").intValue());
        assertEquals("14aeddc4c4ac978f617e9498a295e9d13b00cf499665be57bbcce7bc6049877e", golden.path("sources").get(0).path("sha256").textValue());
        for (JsonNode vector : golden.path("cases")) {
            String name = vector.path("name").textValue(); ObjectNode input = materialize(golden, vector);
            ExpectedFrame expected = FactionAlertsCodec.expected(bytes(vector.get("expected_frame")));
            if (!vector.path("failure").isNull()) {
                assertThrows(IllegalArgumentException.class, () -> {
                    FactionAlertsCodec.Normalized normalized = FactionAlertsCodec.normalize(bytes(input), expected);
                    FactionAlertsCodec.validateWarHandoffs(normalized.frame(), bytes(vector.get("active_wars")));
                }, name);
            } else {
                byte[] before = bytes(input); FactionAlertsCodec.Normalized normalized = FactionAlertsCodec.normalize(before, expected);
                FactionAlertsCodec.validateWarHandoffs(normalized.frame(), bytes(vector.get("active_wars")));
                assertEquals(vector.path("expected_sha256").textValue(), sha256(normalized.json()), name);
                if (!vector.path("expected").isNull()) assertEquals(vector.get("expected"), StrictJson.parse(normalized.json(), FactionAlertsCodec.MAX_BYTES), name);
                assertEquals(normalized.frame(), FactionAlertsCodec.normalize(normalized.json(), expected).frame(), name);
                assertArrayEquals(before, bytes(input), name);
            }
        }
    }
    @Test void actualRawTokensCannotNormalizeOnePointZeroOrBooleanToInteger() throws IOException {
        ObjectNode full = (ObjectNode) golden().path("bases").path("full").deepCopy();
        ExpectedFrame expected = new ExpectedFrame(53789952, BigInteger.valueOf(41), Optional.empty());
        String wire = new String(bytes(full), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "1e0", "\"1\"")) {
            String changed = wire.replace("\"schema_version\":1", "\"schema_version\":" + token);
            assertNotEquals(wire, changed); assertThrows(IllegalArgumentException.class, () -> FactionAlertsCodec.normalize(utf8(changed), expected), token);
        }
        for (String token : List.of("true", "41.0", "41e0", "\"41\"")) {
            String changed = wire.replace("\"snapshot_revision\":41", "\"snapshot_revision\":" + token);
            assertNotEquals(wire, changed); assertThrows(IllegalArgumentException.class, () -> FactionAlertsCodec.normalize(utf8(changed), expected), token);
        }
        String floatRaw = wire.replace("\"raw\":9100000", "\"raw\":9100000.0");
        assertNotEquals(wire, floatRaw); assertThrows(IllegalArgumentException.class, () -> FactionAlertsCodec.normalize(utf8(floatRaw), expected));
        String wrongBoolean = wire.replace("\"leader_is_human\":false", "\"leader_is_human\":0");
        assertThrows(IllegalArgumentException.class, () -> FactionAlertsCodec.normalize(utf8(wrongBoolean), expected));
        assertThrows(IllegalArgumentException.class, () -> FactionAlertsCodec.normalize(utf8(wire + " {}"), expected));
        assertThrows(IllegalArgumentException.class, () -> FactionAlertsCodec.normalize(utf8(wire.replace("\"schema_version\":1", "\"schema_version\":1,\"schema_version\":1")), expected));
    }
    @Test void strictProducerFeedsBothExistingGiftConsumersThroughDeclaredProjection() throws IOException {
        ObjectNode frame = (ObjectNode) golden().path("bases").path("full").deepCopy();
        ObjectNode original = StrictJson.object(); original.set("player_faction_alerts", frame);
        original.set("sdk_extension", StrictJson.parse(utf8("{\"unrelated_float\":1.0,\"opaque_identity\":18446744073709551615}")));
        byte[] raw = wireWithExtension(original);
        ExpectedFrame expected = new ExpectedFrame(53789952, BigInteger.valueOf(41), Optional.of(Build.CK3_11906));
        FactionAlertsBoundary.Projection projection = FactionAlertsBoundary.normalizeExistingDriverResult(raw, expected, utf8("[{\"war_id\":9001}]"));
        assertEquals(sha256(raw), projection.originalSha256());
        JsonNode packet = StrictJson.parse(projection.consumerProjectionJson(), FactionAlertsCodec.MAX_BYTES);
        assertTrue(packet.path("projection_not_original").booleanValue());
        assertEquals(projection.originalSha256(), packet.path("original_source_sha256").textValue());
        assertFalse(packet.has("sdk_extension"));
        var threat = FactionThreatCodec.decodeExistingObserverResult(FactionAlertsBoundary.forThreatObserver(projection).json());
        assertTrue(threat.available()); assertEquals(BigInteger.valueOf(41), threat.frame().orElseThrow().nativeRevision());
        assertEquals(4, threat.targetingRows().size());
        var outcome = GiftOutcomeCodec.alertResult(FactionAlertsBoundary.forResolvedGiftOutcome(projection).json());
        assertEquals(Optional.of(BigInteger.valueOf(41)), outcome.snapshotRevision());
        assertEquals(4, outcome.targetingRows().orElseThrow().size());
        byte[] altered = projection.normalizedAlertJson(); altered[0] = 0;
        assertEquals(frame, StrictJson.parse(projection.normalizedAlertJson(), FactionAlertsCodec.MAX_BYTES));
    }
    @Test void uint64NativeRevisionAndOptionalComponentAreNotTruncatedOrGuessed() throws IOException {
        ObjectNode full = (ObjectNode) golden().path("bases").path("full").deepCopy();
        full.put("snapshot_revision", StrictJson.UINT64_MAX);
        ExpectedFrame maximum = new ExpectedFrame(53789952, StrictJson.UINT64_MAX, Optional.empty());
        var normalized = FactionAlertsCodec.normalize(bytes(full), maximum);
        assertEquals(StrictJson.UINT64_MAX, normalized.frame().snapshotRevision());
        assertTrue(((Available) normalized.frame()).subrealmCounties().isEmpty());
        assertThrows(IllegalArgumentException.class, () -> new ExpectedFrame(0, StrictJson.UINT64_MAX.add(BigInteger.ONE), Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> FactionAlertsCodec.expected(utf8("{\"expected_date_raw\":0,\"expected_snapshot_revision\":1,\"expected_game_version\":\"1.20.0.4\"}")));
    }
    @Test void subrealmReasonBoundUsesPythonUnicodeCodePoints() throws IOException {
        ObjectNode full = (ObjectNode) golden().path("bases").path("full").deepCopy();
        ObjectNode component = StrictJson.object(); component.put("status", "unavailable"); component.put("complete", false);
        component.put("scope", COUNTY_SCOPE); component.put("source", COUNTY_SOURCE); component.put("snapshot_revision", 41);
        component.put("date_raw", 53789952); component.put("actor_character_id", 32904); component.putNull("county_title_ids");
        component.put("unavailable_reason", "😀".repeat(256)); full.set(COUNTY_COMPONENT, component);
        ExpectedFrame expected = new ExpectedFrame(53789952, BigInteger.valueOf(41), Optional.empty());
        Available accepted = (Available) FactionAlertsCodec.normalize(bytes(full), expected).frame();
        assertEquals("😀".repeat(256), ((IncompleteCounties) accepted.subrealmCounties().orElseThrow()).unavailableReason());
        component.put("unavailable_reason", "😀".repeat(257));
        assertThrows(IllegalArgumentException.class, () -> FactionAlertsCodec.normalize(bytes(full), expected));
    }
    @Test void oneSubrealmCodecOwnsCompleteAndUnavailableWireForms() {
        var complete = new CompleteCounties(List.of());
        ObjectNode empty = FactionSubrealmCodec.toJson(complete, 32904, BigInteger.valueOf(41), 53789952);
        assertTrue(empty.path("county_title_ids").isArray()); assertEquals(0, empty.path("county_title_ids").size());
        assertEquals(complete, FactionSubrealmCodec.parse(empty, 32904, BigInteger.valueOf(41), 53789952));
        var missing = new IncompleteCounties("not_observed");
        ObjectNode unavailable = FactionSubrealmCodec.toJson(missing, 32904, BigInteger.valueOf(41), 53789952);
        assertTrue(unavailable.path("county_title_ids").isNull());
        assertEquals(missing, FactionSubrealmCodec.parse(unavailable, 32904, BigInteger.valueOf(41), 53789952));
        String raw = new String(bytes(empty), StandardCharsets.UTF_8).replace("\"snapshot_revision\":41", "\"snapshot_revision\":41.0");
        assertThrows(IllegalArgumentException.class, () -> FactionSubrealmCodec.parse(StrictJson.parse(utf8(raw)), 32904, BigInteger.valueOf(41), 53789952));
    }
    @Test void sharedPrivateBuildSelectorUsesPresentKeysWithoutHeartbeatFallback() {
        ObjectNode snapshot = StrictJson.object(); ObjectNode diagnostics = snapshot.putObject("diagnostics");
        ObjectNode hello = diagnostics.putObject("hello"); hello.put("game_version", Build.CK3_12004.version()); hello.put("executable_sha256", Build.CK3_12004.sha256().toLowerCase(java.util.Locale.ROOT));
        assertEquals(Build.CK3_12004, NativeBuildIdentityCodec.fromSemanticSnapshot(snapshot));
        hello.putNull("expected_ck3_sha256");
        assertThrows(IllegalArgumentException.class, () -> NativeBuildIdentityCodec.fromSemanticSnapshot(snapshot));
        hello.remove("expected_ck3_sha256"); hello.putNull("expected_ck3_version");
        assertThrows(IllegalArgumentException.class, () -> NativeBuildIdentityCodec.fromSemanticSnapshot(snapshot));
        diagnostics.remove("hello"); diagnostics.set("last_heartbeat", hello);
        assertEquals(Build.CK3_11906, NativeBuildIdentityCodec.fromSemanticSnapshot(snapshot));
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = FactionAlertsCodecTest.class.getResourceAsStream("/factionalerts/original-producer-golden.json")) {
            assertNotNull(stream, "required unchanged producer capture missing; do not count skip as pass");
            return StrictJson.parse(stream.readAllBytes(), FactionAlertsCodec.MAX_BYTES);
        }
    }
    private static ObjectNode materialize(JsonNode golden, JsonNode vector) {
        ObjectNode root = (ObjectNode) golden.path("bases").get(vector.path("base").textValue()).deepCopy();
        for (JsonNode operation : vector.path("operations")) {
            String path = operation.path("path").textValue(); int split = path.lastIndexOf('/');
            JsonNode parent = root.at(path.substring(0, split)); String key = path.substring(split + 1);
            if (parent instanceof ObjectNode object) {
                if (operation.path("remove").asBoolean()) object.remove(key); else object.set(key, operation.get("value").deepCopy());
            } else if (parent instanceof ArrayNode array) {
                int index = Integer.parseInt(key); if (operation.path("remove").asBoolean()) array.remove(index); else array.set(index, operation.get("value").deepCopy());
            } else fail("invalid golden operation " + path);
        }
        return root;
    }
    private static byte[] bytes(JsonNode node) { return StrictJson.canonical(node, FactionAlertsCodec.MAX_BYTES); }
    private static byte[] wireWithExtension(JsonNode node) {
        try { return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(node); }
        catch (IOException error) { throw new IllegalStateException(error); }
    }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
