package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m3.M3Research;

/** Derived role vectors from the submitted original producer capture. No Game or action authority. */
final class SuccessionFreshnessNativeCharacterIdTest {
    private static final String RESOURCE = "/g2/m3/original-producer-golden.json";
    private static final JsonMapper JSON = JsonMapper.builder()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                    DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private static final int[][] ROLES = {{2, 0}, {2, -2}, {2, Integer.MIN_VALUE},
            {2, Integer.MAX_VALUE}, {0, 3}, {-2, 3}, {Integer.MIN_VALUE, 3}};
    private record Golden(ObjectNode value, byte[] bytes) {
        private Golden { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    private enum RoleSlot { PREDECESSOR, EPISODE, LAST_LIVING }

    @Test void actualFreshnessProjectionPreservesModernRoleMatrixThroughSerdeAndM3() throws Exception {
        Golden golden = golden(); G2Source source = source(golden); var domain = new M3Research();
        for (int[] roles : ROLES) {
            ObjectNode request = request(golden, roles[0], roles[1]);
            byte[] original = JSON.writeValueAsBytes(request), retained = original.clone();
            var decoded = SuccessionFreshnessCodec.decode(original);
            BigInteger actor = BigInteger.valueOf(roles[0]);
            assertEquals(actor, decoded.predecessorCharacterId());
            assertEquals(actor, decoded.predecessorBinding().episodeCharacterId());
            assertEquals(actor, decoded.lastLivingFrame().orElseThrow().episodeCharacterId());
            JsonNode observed = JSON.readTree(SuccessionFreshnessCodec.observe(original));
            byte[] persisted = SuccessionFreshnessCodec.encodeRequest(decoded);
            assertEquals(observed, JSON.readTree(SuccessionFreshnessCodec.observe(persisted)));
            assertEquals(actor, JSON.readTree(persisted).path("reconciliation")
                    .path("predecessor_character_id").bigIntegerValue());
            var routed = domain.evaluate(new G2Request("freshness-native-" + roles[0] + "-" + roles[1],
                    Milestone.M3, source, ProjectionJson.object(original, M3Research.MAXIMUM_BYTES)));
            assertEquals(observed, JSON.readTree(routed.result().bytes()));
            assertEquals(source, routed.source()); assertEquals(Milestone.M3, routed.milestone());
            assertArrayEquals(retained, original);
            assertEquals("full_expectation_not_observed", observed.path("all_title_freshness").textValue());
            assertTrue(observed.path("complete_title_ids").isNull());
            for (String flag : List.of("fresh_immediately_before_death_claimed",
                    "reconciliation_verified_by_this_observer", "process_birth_verified_by_this_observer",
                    "replay_allowed", "business_credit", "M7_coverage_credit")) {
                assertTrue(observed.get(flag).isBoolean(), flag); assertFalse(observed.get(flag).booleanValue(), flag);
            }
        }
    }

    @Test void absentUnsignedAndWrongTypedRolesStayRejectedAtEveryRawRoleBoundary() throws Exception {
        Golden golden = golden();
        for (RoleSlot slot : RoleSlot.values()) {
            for (String token : List.of("-1", "-2147483649", "2147483648", "4294967294",
                    "true", "2.0", "\"0\"", "null")) {
                ObjectNode request = request(golden, 2, 3);
                roleParent(request, slot).set(roleKey(slot), JSON.readTree(token));
                byte[] raw = JSON.writeValueAsBytes(request);
                assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.decode(raw), slot + ":" + token);
            }
            ObjectNode missing = request(golden, 2, 3); roleParent(missing, slot).remove(roleKey(slot));
            byte[] raw = JSON.writeValueAsBytes(missing);
            assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.decode(raw), slot + ":missing");
        }
        var frame = new SuccessionFreshnessModel.Frame("frame", BigInteger.ZERO, BigInteger.ZERO, BigInteger.ZERO);
        var binding = new SuccessionFreshnessModel.EpisodeBinding(frame, "episode", BigInteger.ZERO);
        for (BigInteger invalid : List.of(BigInteger.valueOf(-1), BigInteger.ONE.shiftLeft(31),
                BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE), new BigInteger("4294967294"))) {
            assertThrows(IllegalArgumentException.class,
                    () -> new SuccessionFreshnessModel.EpisodeBinding(frame, "episode", invalid));
            assertThrows(IllegalArgumentException.class,
                    () -> new SuccessionFreshnessModel.Input(binding, frame, invalid, Optional.empty(), Optional.empty(),
                            new SuccessionFreshnessModel.VerdictEvidence("null".getBytes(StandardCharsets.UTF_8))));
        }
    }

    @Test void originalFrameDomainsIdentityDatesAndGoldenObservationsRemainUnchanged() throws Exception {
        Golden golden = golden();
        for (JsonNode vector : golden.value().path("freshness_cases")) {
            assertEquals(vector.get("expected"), JSON.readTree(SuccessionFreshnessCodec.observe(
                    JSON.writeValueAsBytes(vector.get("request")))));
        }
        BigInteger large = BigInteger.ONE.shiftLeft(130);
        assertDoesNotThrow(() -> new SuccessionFreshnessModel.Frame("opaque", BigInteger.ZERO, large, BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,
                () -> new SuccessionFreshnessModel.Frame("opaque", BigInteger.valueOf(-1), BigInteger.ZERO, BigInteger.ZERO));
        ObjectNode mismatch = request(golden, 0, 3);
        roleParent(mismatch, RoleSlot.PREDECESSOR).put(roleKey(RoleSlot.PREDECESSOR), -2);
        byte[] mismatchBytes = JSON.writeValueAsBytes(mismatch);
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(mismatchBytes));
        ObjectNode reverse = request(golden, 0, 3);
        object(reverse.path("reconciliation").path("successor_binding")).put("date_raw", 0);
        byte[] reverseBytes = JSON.writeValueAsBytes(reverse);
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(reverseBytes));
        for (String token : List.of("-1", "true", "2.0", "\"0\"", "null")) {
            ObjectNode changed = request(golden, 0, 3);
            object(changed.path("reconciliation").path("predecessor_binding")).set("revision", JSON.readTree(token));
            byte[] raw = JSON.writeValueAsBytes(changed);
            assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.decode(raw), token);
        }
    }

    @Test void actualFullExpectationRoleMatrixMatchesOriginalGoldenThroughSerdeAndM3() throws Exception {
        Golden golden = golden(); G2Source source = source(golden); var domain = new M3Research();
        byte[] goldenBefore = JSON.writeValueAsBytes(golden.value()); int fullCases = 0, evaluated = 0;
        for (JsonNode vector : golden.value().path("freshness_cases")) {
            if (vector.path("request").path("expectation").isNull()) continue;
            fullCases++;
            for (int[] roles : ROLES) {
                ObjectNode request = object(vector.get("request")).deepCopy();
                ObjectNode reconciliation = object(request.get("reconciliation"));
                ObjectNode expectation = object(request.get("expectation"));
                BigInteger oldSuccessor = expectation.path("expected_successor_character_id").bigIntegerValue();
                reconciliation.put("predecessor_character_id", BigInteger.valueOf(roles[0]));
                object(reconciliation.get("predecessor_binding")).put("episode_character_id", BigInteger.valueOf(roles[0]));
                object(expectation.get("binding")).put("episode_character_id", BigInteger.valueOf(roles[0]));
                expectation.put("predecessor_character_id", BigInteger.valueOf(roles[0]));
                expectation.put("expected_successor_character_id", BigInteger.valueOf(roles[1]));
                for (JsonNode row : expectation.path("title_expectations")) {
                    JsonNode heir = row.get("first_heir_character_id");
                    if (!heir.isNull() && heir.bigIntegerValue().equals(oldSuccessor)) {
                        object(row).put("first_heir_character_id", BigInteger.valueOf(roles[1]));
                    }
                }
                if (!request.get("last_living_frame").isNull()) {
                    object(request.get("last_living_frame")).put("episode_character_id", BigInteger.valueOf(roles[0]));
                }
                ObjectNode expected = object(vector.get("expected")).deepCopy();
                object(expected.get("predecessor_binding")).put("episode_character_id", BigInteger.valueOf(roles[0]));
                if (!expected.get("last_observed_living_binding").isNull()) {
                    object(expected.get("last_observed_living_binding")).put("episode_character_id", BigInteger.valueOf(roles[0]));
                }
                byte[] raw = JSON.writeValueAsBytes(request), retained = raw.clone();
                var decoded = SuccessionFreshnessCodec.decode(raw);
                var full = decoded.expectation().orElseThrow();
                assertEquals(roles[0], full.binding().episodeCharacterId());
                assertEquals(roles[0], full.predecessorCharacterId());
                assertEquals(Integer.valueOf(roles[1]), full.expectedSuccessorCharacterId());
                assertEquals(expectation.path("title_expectations").size(), full.titleExpectations().size());
                for (int index = 0; index < full.titleExpectations().size(); index++) {
                    JsonNode originalRow = expectation.path("title_expectations").get(index);
                    var actualRow = full.titleExpectations().get(index);
                    JsonNode heir = originalRow.get("first_heir_character_id");
                    assertEquals(heir.isNull() ? null : Integer.valueOf(heir.intValue()), actualRow.firstHeirCharacterId());
                    assertEquals(originalRow.get("title"), JSON.readTree(actualRow.title().original().bytes()));
                    assertEquals(originalRow.path("primary").booleanValue(), actualRow.primary());
                }
                byte[] persisted = SuccessionFreshnessCodec.encodeRequest(decoded);
                assertTrue(SuccessionFreshnessCodec.decode(persisted).expectation().isPresent());
                assertEquals(expectation, JSON.readTree(persisted).get("expectation"));
                assertEquals(expected, JSON.readTree(SuccessionFreshnessCodec.observe(raw)));
                assertEquals(expected, JSON.readTree(SuccessionFreshnessCodec.observe(persisted)));
                var routed = domain.evaluate(new G2Request("freshness-full-" + vector.path("name").textValue()
                        + "-" + roles[0] + "-" + roles[1], Milestone.M3, source,
                        ProjectionJson.object(raw, M3Research.MAXIMUM_BYTES)));
                JsonNode observed = JSON.readTree(routed.result().bytes());
                assertEquals(expected, observed); assertEquals(source, routed.source());
                assertEquals(Milestone.M3, routed.milestone());
                assertTrue(observed.path("complete_title_expectation_observed").booleanValue());
                for (String flag : List.of("fresh_immediately_before_death_claimed",
                        "reconciliation_verified_by_this_observer", "process_birth_verified_by_this_observer",
                        "replay_allowed", "business_credit", "M7_coverage_credit")) {
                    assertTrue(observed.get(flag).isBoolean(), flag); assertFalse(observed.get(flag).booleanValue(), flag);
                }
                assertArrayEquals(retained, raw); evaluated++;
            }
        }
        assertEquals(3, fullCases); assertEquals(fullCases * ROLES.length, evaluated);
        assertArrayEquals(goldenBefore, JSON.writeValueAsBytes(golden.value()));
    }

    private static ObjectNode request(Golden golden, int actor, int successor) {
        for (JsonNode vector : golden.value().path("freshness_cases")) {
            if (!vector.path("request").path("expectation").isNull()
                    || !vector.path("request").path("last_living_frame").isObject()) continue;
            ObjectNode request = object(vector.get("request")).deepCopy();
            ObjectNode reconciliation = object(request.get("reconciliation"));
            reconciliation.put("predecessor_character_id", actor);
            reconciliation.put("expected_successor_character_id", successor);
            reconciliation.put("actual_successor_character_id", successor);
            object(reconciliation.get("predecessor_binding")).put("episode_character_id", actor);
            object(request.get("last_living_frame")).put("episode_character_id", actor);
            return request;
        }
        throw new AssertionError("actual no-expectation/living-frame producer capture required");
    }
    private static ObjectNode roleParent(ObjectNode request, RoleSlot slot) {
        if (slot == RoleSlot.LAST_LIVING) return object(request.get("last_living_frame"));
        ObjectNode reconciliation = object(request.get("reconciliation"));
        return slot == RoleSlot.PREDECESSOR ? reconciliation : object(reconciliation.get("predecessor_binding"));
    }
    private static String roleKey(RoleSlot slot) {
        return slot == RoleSlot.PREDECESSOR ? "predecessor_character_id" : "episode_character_id";
    }
    private static ObjectNode object(JsonNode node) { return assertInstanceOf(ObjectNode.class, node); }
    private static Golden golden() throws IOException {
        try (InputStream input = SuccessionFreshnessNativeCharacterIdTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(input, "submitted original producer capture must be available");
            byte[] bytes = input.readAllBytes(); ObjectNode golden = object(JSON.readTree(bytes));
            assertEquals("xar.g2.m3.original-producer-golden/v1", golden.path("schema").textValue());
            return new Golden(golden, bytes);
        }
    }
    private static G2Source source(Golden golden) throws Exception {
        String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(golden.bytes()));
        return new G2Source(golden.value().path("machine_id").textValue(), golden.value().path("observed_at_utc").textValue(),
                "offline-original-producer-fixture", new ExactRef(RESOURCE, golden.bytes().length, sha));
    }
}
