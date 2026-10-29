package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Frozen outputs from actual original Python producer functions; no receipt grants live authority. */
final class SteamOfflineObservationCodecTest {
    private static JsonNode oracle() throws IOException {
        try (InputStream stream = SteamOfflineObservationCodecTest.class.getResourceAsStream("/steam-offline/python-producer-oracle03.json")) {
            if (stream == null) throw new IOException("Original producer oracle resource missing");
            return StrictJson.parse(stream.readAllBytes(), SteamOfflineObservationCodec.MAXIMUM_BYTES);
        }
    }
    @Test void allThreeActualOriginalNativeProducersRoundTripWithoutChangingWideIdentities() throws Exception {
        JsonNode receipts = oracle().get("native_profile_producer_receipts"); assertEquals(3, receipts.size());
        for (JsonNode wire : receipts) {
            var result = SteamOfflineObservationCodec.fromJson(wire);
            assertInstanceOf(SteamOfflineObservation.Offline.class, result);
            assertArrayEquals(StrictJson.canonical(wire), SteamOfflineObservationCodec.encode(result));
            assertEquals(result, SteamOfflineObservationCodec.decode(SteamOfflineObservationCodec.encode(result)));
            var source = result.common().source().orElseThrow(); var steam = result.common().steam().orElseThrow();
            assertNotNull(SteamOfflineProfiles.select(steam.fileVersion(), source.bytes(), source.sha256()));
            assertEquals(wire.path("steam").path("birth_filetime").textValue(), steam.birthFiletime());
            assertEquals(wire.path("source").path("file_id").textValue(), source.fileId());
        }
    }
    @Test void originalCefOfflineAndOnlineRemainDistinctAndV1MigratesAsDataOnly() throws Exception {
        JsonNode receipts = oracle().get("cef_receipts");
        assertInstanceOf(SteamOfflineObservation.Offline.class, SteamOfflineObservationCodec.fromJson(receipts.get(0)));
        assertInstanceOf(SteamOfflineObservation.Online.class, SteamOfflineObservationCodec.fromJson(receipts.get(1)));
        for (JsonNode wire : receipts) {
            var value = SteamOfflineObservationCodec.fromJson(wire);
            assertArrayEquals(StrictJson.canonical(wire), SteamOfflineObservationCodec.encode(value));
            ObjectNode v1 = ((ObjectNode) wire).deepCopy(); v1.put("schema", "xar.steam-offline-state-probe/v1");
            v1.remove("observation_method"); v1.remove("native_evidence");
            assertEquals(value, SteamOfflineObservationCodec.fromJson(v1));
        }
    }
    @Test void nativeWrongFieldsTypesIdentitiesSourcesAndStateCannotBecomeAnObservation() throws Exception {
        ObjectNode base = (ObjectNode) oracle().path("native_profile_producer_receipts").get(0);
        for (String mutation : List.of("numeric_address", "wrong_address", "range", "bool_sample", "float_sample",
                "changed_sample", "changed_process", "changed_source", "wrong_nonce", "wrong_anchor", "wrong_method",
                "missing_method", "false_mode", "tray_mismatch", "tray_wrong_type", "manager_null", "unexpected_field")) {
            ObjectNode wire = base.deepCopy(); ObjectNode evidence = (ObjectNode) wire.get("native_evidence");
            switch (mutation) {
                case "numeric_address" -> evidence.put("module_base", 9007199254740993L);
                case "wrong_address" -> evidence.put("value_address", "1");
                case "range" -> evidence.put("module_size", 100);
                case "bool_sample" -> evidence.putArray("raw_samples").add(true).add(true);
                case "float_sample" -> evidence.putArray("raw_samples").add(1.0).add(1.0);
                case "changed_sample" -> evidence.putArray("raw_samples").add(1).add(0);
                case "changed_process" -> ((ObjectNode) evidence.get("steam_after")).put("birth_filetime", "1");
                case "changed_source" -> ((ObjectNode) evidence.get("source_after")).put("file_id", "1");
                case "wrong_nonce" -> evidence.put("nonce", "stale");
                case "wrong_anchor" -> evidence.put("producer_anchor_hex", "00");
                case "wrong_method" -> wire.put("observation_method", "cef_app_getters");
                case "missing_method" -> wire.putNull("observation_method");
                case "false_mode" -> wire.put("offline_mode", false);
                case "tray_mismatch" -> evidence.putArray("tray_state_samples").add(5).add(5);
                case "tray_wrong_type" -> evidence.putArray("tray_state_samples").add(4.0).add(4.0);
                case "manager_null" -> evidence.put("tray_manager_address", "0");
                case "unexpected_field" -> evidence.put("alias", "wrong");
                default -> throw new IllegalStateException(mutation);
            }
            assertThrows(IllegalArgumentException.class, () -> SteamOfflineObservationCodec.fromJson(wire), mutation);
        }
    }
    @Test void missingNullUnavailableAndDuplicateJsonFieldsKeepTheirOriginalMeaning() throws Exception {
        ObjectNode base = (ObjectNode) oracle().path("cef_receipts").get(0);
        for (String mutation : List.of("missing_source", "null_source", "null_diagnostics", "numeric_boolean", "alias")) {
            ObjectNode wire = base.deepCopy();
            switch (mutation) {
                case "missing_source" -> wire.remove("source"); case "null_source" -> wire.putNull("source");
                case "null_diagnostics" -> wire.putNull("diagnostics"); case "numeric_boolean" -> wire.put("offline_mode", 1);
                case "alias" -> wire.put("offline", true); default -> throw new IllegalStateException(mutation);
            }
            assertThrows(IllegalArgumentException.class, () -> SteamOfflineObservationCodec.fromJson(wire));
        }
        ObjectNode unavailable = base.deepCopy(); unavailable.put("status", "unavailable"); unavailable.put("reason", "cdp_not_enabled");
        unavailable.remove("offline_mode"); unavailable.putNull("steam"); unavailable.putNull("source"); unavailable.putNull("endpoint");
        unavailable.putNull("observation_method"); unavailable.putNull("native_evidence");
        var data = SteamOfflineObservationCodec.fromJson(unavailable);
        assertInstanceOf(SteamOfflineObservation.Unavailable.class, data);
        assertFalse(SteamOfflineObservationCodec.toJson(data).has("offline_mode"));
        ObjectNode nullBoolean = unavailable.deepCopy(); nullBoolean.putNull("offline_mode");
        assertThrows(IllegalArgumentException.class, () -> SteamOfflineObservationCodec.fromJson(nullBoolean));
        String duplicate = new String(SteamOfflineObservationCodec.encode(data), StandardCharsets.UTF_8)
                .replace("\"status\":\"unavailable\"", "\"status\":\"unavailable\",\"status\":\"offline\"");
        assertThrows(IllegalArgumentException.class, () -> SteamOfflineObservationCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
    }
    @Test void retainedOriginalLiveReceiptIsOnlyComparisonDataAndCannotMintEitherPrivateToken() throws Exception {
        try (InputStream stream = getClass().getResourceAsStream("/steam-offline/original-background-r4-01.json")) {
            if (stream == null) throw new IOException("Retained original comparison receipt missing");
            var parsed = assertInstanceOf(SteamOfflineObservation.Offline.class, SteamOfflineObservationCodec.decode(stream.readAllBytes()));
            assertEquals(SteamOfflineObservation.Method.NATIVE_CURRENT_USER_BYTE, parsed.method());
            assertEquals("134372982139497536", parsed.common().steam().orElseThrow().birthFiletime());
            assertEquals("38562071810319963", parsed.common().source().orElseThrow().fileId());
            var source = parsed.common().source().orElseThrow();
            assertEquals("11.15.70.27", SteamOfflineProfiles.select(parsed.common().steam().orElseThrow().fileVersion(), source.bytes(), source.sha256()).version());
        }
        for (var constructor : SteamOfflineProbe.QualifiedOffline.class.getDeclaredConstructors()) assertTrue(Modifier.isPrivate(constructor.getModifiers()));
        assertTrue(List.of(SteamOfflineProbe.QualifiedOffline.class.getMethods()).stream()
                .noneMatch(method -> method.getName().equals("fromJson") || method.getName().equals("decode")));
    }
}
