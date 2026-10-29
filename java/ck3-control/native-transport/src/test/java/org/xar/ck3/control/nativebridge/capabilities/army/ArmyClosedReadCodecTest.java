package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original fixture -> closed model -> public decimal64. Missing fixture configuration is a failure, never a skip. */
final class ArmyClosedReadCodecTest {
    static final BigInteger MAX = new BigInteger("18446744073709551615");
    static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    static final ExactRef REF = new ExactRef("fixture-original", 1, "a".repeat(64));
    static Context context(String version, int actor) {
        var source = new G2Source("fixture-machine", NOW.toString(), version, REF);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor), BigInteger.valueOf(11), BigInteger.valueOf(53238336)), "native:11", BigInteger.valueOf(7), "fixture-episode");
        return new Context(new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "fixture-session", NOW.plusSeconds(60));
    }
    static ArmyCalls.Call call(PublicMethod method, String arguments) { return ArmyCallCodec.decode(method, new RawJson(arguments.getBytes(StandardCharsets.UTF_8))); }
    static ObjectNode fixture() throws Exception {
        String file = required("xar.army.defaultRaise.fixture"), sha = required("xar.army.defaultRaise.sha256");
        byte[] original = Files.readAllBytes(Path.of(file));
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)), "retained producer fixture changed");
        return ArmyJson.parse(original);
    }
    static String required(String name) {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: required original Army fixture property missing: " + name);
        return value;
    }
    @Test void originalLegalAndIllegalFalseRemainDistinctFromUnavailable() throws Exception {
        var request = call(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, "{\"expected_revision\":7}");
        for (String name : List.of("legal", "illegal")) {
            byte[] raw = ArmyJson.bytes(fixture().get(name));
            var value = assertInstanceOf(ArmyClosedReads.DefaultRaise.class, ArmyClosedReadCodec.decodeToken(request, context("1.20.0.3", 29829), raw));
            assertTrue(value.legalityReady()); assertEquals(new Present<>(name.equals("legal")), value.legal());
            assertFalse(value.reserveReady()); assertInstanceOf(NullValue.class, value.soldiers());
            assertArrayEquals(raw, ArmyJson.bytes(fixture().get(name)));
        }
    }
    @Test void everyRequiredDefaultRaiseFieldAndExactTypeIsChecked() throws Exception {
        var request = call(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, "{\"expected_revision\":7}");
        ObjectNode original = ArmyJson.object(fixture().get("legal")); Context context = context("1.20.0.3", 29829);
        for (String name : ArmyJson.names(original)) {
            ObjectNode changed = original.deepCopy(); changed.remove(name);
            assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodeToken(request, context, ArmyJson.bytes(changed)), name);
        }
        ObjectNode originalBody = ArmyJson.object(original.get("player_default_raise"));
        for (String name : ArmyJson.names(originalBody)) {
            ObjectNode changed = original.deepCopy(); ArmyJson.object(changed.get("player_default_raise")).remove(name);
            assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodeToken(request, context, ArmyJson.bytes(changed)), name);
        }
        for (String token : List.of("true", "11.0", "\"11\"", "null")) {
            ObjectNode changed = original.deepCopy(); changed.set("snapshot_revision", ArmyJson.parse(("{\"value\":" + token + "}").getBytes(StandardCharsets.UTF_8)).get("value"));
            assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodeToken(request, context, ArmyJson.bytes(changed)));
        }
        ObjectNode extra = original.deepCopy().put("unknown", 1);
        assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodeToken(request, context, ArmyJson.bytes(extra)));
        assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodeToken(request, context("1.20.0.4", 29829), ArmyJson.bytes(original)));
    }
    @Test void publicNativeUint64IsDecimalWhileOriginalRemainsAnIntegerAndCharacterZeroIsValid() throws Exception {
        var request = call(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, "{\"expected_revision\":7}");
        ObjectNode raw = ArmyJson.object(fixture().get("legal")).deepCopy(); raw.put("query_sequence", MAX);
        ArmyJson.object(raw.get("player_default_raise")).put("actor_character_id", 0);
        byte[] original = ArmyJson.bytes(raw); Context context = context("1.20.0.3", 0);
        var value = assertInstanceOf(ArmyClosedReads.DefaultRaise.class, ArmyClosedReadCodec.decodeToken(request, context, original));
        var encoded = ArmyJson.parse(ArmyClosedReadCodec.encode(value, context).bytes());
        assertEquals(value, ArmyClosedReadCodec.decodePublic(request, context, new RawJson(ArmyJson.bytes(encoded))));
        assertEquals(MAX.toString(), encoded.get("query_sequence").textValue());
        assertEquals("11", encoded.get("snapshot_revision").textValue()); assertEquals(0, encoded.get("player_default_raise").get("actor_character_id").intValue());
        assertTrue(ArmyJson.parse(original).get("query_sequence").isIntegralNumber()); assertEquals(MAX, ArmyJson.parse(original).get("query_sequence").bigIntegerValue());
        for (String wrong : List.of("00", "+11", "18446744073709551616")) {
            ObjectNode changed = encoded.deepCopy().put("snapshot_revision", wrong);
            assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodePublic(request, context, new RawJson(ArmyJson.bytes(changed))));
        }
        ObjectNode rounded = encoded.deepCopy().put("query_sequence", MAX.doubleValue());
        assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodePublic(request, context, new RawJson(ArmyJson.bytes(rounded))));
    }
    @Test void productionDefaultPresenterCopiesTheActualNullableDiagnosticsAndRejectsAChangedFrame() throws Exception {
        var request = call(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, "{\"expected_revision\":7}");
        Context context = context("1.20.0.3", 29829);
        var observed = ArmyClosedReadCodec.decodeToken(request, context, ArmyJson.bytes(fixture().get("legal")));
        var snapshot = ArmyJson.empty().put("snapshot_id", context.before().frame().snapshotId()).put("revision", 7)
                .put("native_revision", 11).put("date_raw", 53238336).put("episode_run_id", "fixture-episode");
        snapshot.putObject("diagnostics").put("connection_generation", MAX).put("bridge_pid", 4242);
        var wire = ArmyClosedReadCodec.encode(observed, context, org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(snapshot), org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES));
        var encoded = ArmyJson.parse(wire.bytes());
        assertEquals(MAX.toString(), encoded.get("queried_connection_generation").textValue());
        assertEquals("fixture-episode", encoded.get("queried_episode_run_id").textValue());
        assertTrue(encoded.get("queried_bridge_pid").isIntegralNumber()); assertEquals(4242, encoded.get("queried_bridge_pid").intValue());
        assertEquals(observed, ArmyClosedReadCodec.decodePublic(request, context, wire));
        var missing = snapshot.deepCopy(); missing.remove("diagnostics"); missing.putNull("episode_run_id");
        var nullable = ArmyJson.parse(ArmyClosedReadCodec.encode(observed, context, org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(missing), org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES)).bytes());
        for (String field : List.of("queried_episode_run_id", "queried_connection_generation", "queried_bridge_pid")) assertTrue(nullable.get(field).isNull());
        var changed = snapshot.deepCopy().put("native_revision", 12);
        assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.encode(observed, context, org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(changed), org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES)));
    }
    @Test void gatheringIsAReadOnlyResearchStateWithAllFourExactUint64Counters() {
        String raw = "{\"step\":\"query-army-gathering-research-sampling-v1\",\"accepted\":true,\"status\":\"enabled\",\"backend_id\":\"native-headless\",\"army_gathering_research_sampling_v1\":{\"capture_enabled\":true,\"busy\":false,\"clear_completed\":false,\"epoch\":18446744073709551615,\"active_captures\":0,\"retained_records\":1,\"qualified_records\":1,\"readiness\":\"retained_observation\"}}";
        var request = call(PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1, "{\"expected_revision\":7}"); Context context = context("1.20.0.4", 29829);
        var value = assertInstanceOf(ArmyClosedReads.Gathering.class, ArmyClosedReadCodec.decodeToken(request, context, raw.getBytes(StandardCharsets.UTF_8)));
        var encoded = ArmyJson.parse(ArmyClosedReadCodec.encode(value, context).bytes()); assertEquals(MAX.toString(), encoded.get("army_gathering_research_sampling_v1").get("epoch").textValue());
        assertEquals(value, ArmyClosedReadCodec.decodePublic(request, context, new RawJson(ArmyJson.bytes(encoded))));
        for (String token : List.of("true", "0.0", "\"0\"", "null", "-1", "18446744073709551616")) {
            String wrong = raw.replace("\"active_captures\":0", "\"active_captures\":" + token);
            assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodeToken(request, context, wrong.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(IllegalArgumentException.class, () -> new ArmyClosedReadContracts.Selection(call(PublicMethod.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1, "{\"expected_revision\":7,\"enabled\":false}"), context));
    }
    @Test void absentTruceIsAnAcceptedStableObservationAndPublicRoundtripPreservesNull() {
        Context context = context("1.20.0.4", 0); var request = call(PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1, "{\"toward_character_id\":2,\"expected_revision\":7}");
        ObjectNode body = ArmyJson.empty().put("schema_version", 1).put("backend_id", "ck3-1.20.0.4-native-player-truce-expiry-v1").put("ck3_build", "1.20.0.4")
                .put("executable_sha256", ArmyResponseCodec.ACTUAL4_SHA).put("status", "no_truce").put("snapshot_revision", 11).put("current_date_raw", 53238336)
                .put("owner_character_id", 0).put("toward_character_id", 2).put("native_has_truce", false).put("actual_expiry_observable", false)
                .putNull("expiry_date_raw").put("same_frame_stable", true).put("readiness", false).put("temporal_semantics", "post_application_persisted_relation_state").put("unavailable_reason", "native_has_truce_false");
        ObjectNode token = ArmyJson.empty().put("step", "query-raiktor-actual-truce-expiry-v1-2").put("accepted", true).put("query_sequence", MAX).put("snapshot_revision", 11).put("date_raw", 53238336).put("read_only", true).put("backend_id", "native-headless");
        token.set("raiktor_actual_truce_expiry", body);
        var value = assertInstanceOf(ArmyClosedReads.Truce.class, ArmyClosedReadCodec.decodeToken(request, context, ArmyJson.bytes(token)));
        assertFalse(value.readiness()); assertInstanceOf(NullValue.class, value.expiryDateRaw());
        RawJson encoded = ArmyClosedReadCodec.encode(value, context); assertEquals(value, ArmyClosedReadCodec.decodePublic(request, context, encoded));
        ObjectNode missing = token.deepCopy(); ArmyJson.object(missing.get("raiktor_actual_truce_expiry")).remove("expiry_date_raw");
        assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodeToken(request, context, ArmyJson.bytes(missing)));
        ObjectNode conflicting = ArmyJson.parse(encoded.bytes()); ArmyJson.object(conflicting.get("player_truce_expiry_v1")).put("readiness", true);
        assertThrows(IllegalArgumentException.class, () -> ArmyClosedReadCodec.decodePublic(request, context, new RawJson(ArmyJson.bytes(conflicting))));
    }
    @Test void actualArmyScopeMaximumIs64AtBothPublicAndInternalInputBoundaries() {
        var ids = java.util.stream.IntStream.range(0, 64).mapToObj(PublicUnitId::new).toList();
        var revision = new ArmyCalls.Revision(new Missing<>());
        assertEquals(64, new ArmyCalls.Strengths(revision, ids, new Missing<>(), new Missing<>(), new Missing<>()).armies().size());
        assertEquals(64, new ArmyRequests.Strengths(ids, ArmyRequests.StrengthProfile.ORDINARY_CORE_V1, ArmyRequests.RefillEntryMode.OBSERVED_PREPARED, ArmyRequests.RefillEntryMode.OBSERVED_PREPARED).armies().size());
        var tooMany = java.util.stream.IntStream.range(0, 65).mapToObj(PublicUnitId::new).toList();
        assertThrows(IllegalArgumentException.class, () -> new ArmyCalls.Strengths(revision, tooMany, new Missing<>(), new Missing<>(), new Missing<>()));
        assertThrows(IllegalArgumentException.class, () -> new ArmyRequests.Strengths(tooMany, ArmyRequests.StrengthProfile.ORDINARY_CORE_V1, ArmyRequests.RefillEntryMode.OBSERVED_PREPARED, ArmyRequests.RefillEntryMode.OBSERVED_PREPARED));
    }
}
