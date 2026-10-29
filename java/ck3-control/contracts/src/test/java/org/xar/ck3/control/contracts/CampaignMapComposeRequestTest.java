package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;

class CampaignMapComposeRequestTest {
    @Test void theOriginalQualifiedN46ResponseIsByteExactAfterTheSharedRequestAdoption() throws Exception {
        // Exact encoding of logs/client-n46-map-e90880ecb92241949213bef1c893d1d8.response.bin.
        // Source was read and SHA-verified; this is the original 536-byte response, not a rebuilt golden.
        byte[] original = Base64.getDecoder().decode(
                "eyJHYW1lX21hcF92aXNpYmxlIjp0cnVlLCJhY3R1YWxfaW5pdGlhbF9mcmFtZSI6eyJhY3Rvcl9jaGFyYWN0ZXJfaWQiOjQw"
                 + "NTI2LCJkYXRlX3JhdyI6NTMyNzk0MDAsImVwaXNvZGVfcnVuX2lkIjoibmF0aXZlLTQwNTI2LTFiZWM5NTE4Mjg4NiIsIm5h"
                 + "dGl2ZV9yZXZpc2lvbiI6MSwicmV2aXNpb24iOjIsInNuYXBzaG90X2lkIjoibmF0aXZlOjEifSwiZGVjaXNpb25fdGV4dF92"
                 + "aXNpYmxlIjp0cnVlLCJnYW1lX2NyZWF0aW9uX2ZpbGV0aW1lIjoxMzQzNzE0MzAzNDg4Mjg3NDEsImdhbWVfcGlkIjo1MDY4"
                 + "OCwibWFjaGluZV9pZCI6Inhlbm9hbWVzcy1mdWxsLXRvd2VyLWViOWQyYzExODYiLCJvYnNlcnZlZF9hdF91dGMiOiIyMDI2"
                 + "LTEwLTIyVDEyOjM3OjAyLjQwNDk0NSswMDowMCIsInJlY29yZGluZ19zZXNzaW9uX2lkIjoiMDZjMjRkMDItM2MwOS00ZGJi"
                 + "LThmMjEtYzIzNzEyZWIyZDViIiwicmV2aWV3ZXIiOiIvcm9vdCIsInNjaGVtYSI6Inhhci5jdXJyZW50LXNhdmVkLXJvb3Qt"
                 + "bWFwLXJldmlldy92MSIsInN0YXR1cyI6IkdSRUVOIn0=");
        assertEquals(536, original.length);
        assertEquals("0658d5925d52abe25e9ba70d3eb8750344e9dbdf4ffe3120242a419c4bd843ba",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        CampaignMapAdmission admitted = CampaignMapAdmission.fromJson(StrictJson.parse(original));
        CampaignMapComposeRequest derivedRequest = new CampaignMapComposeRequest(admitted.machineId(),
                admitted.game(), admitted.recordingSessionId(), admitted.actualInitialFrame(), admitted.observedAtUtc());
        byte[] serializedRequest = derivedRequest.toCanonicalBytes();
        // The request is newly serialized from the original response; only its old metadata digest is available.
        assertEquals(512, serializedRequest.length);
        assertEquals("b83463477a6539821cf776e6786d1f1ecfa1db0bdfe39750af808dee450f520a",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(serializedRequest)));
        assertArrayEquals(original, CampaignMapAdmissionComposer.compose(serializedRequest));
    }

    private static CampaignMapComposeRequest request() {
        return new CampaignMapComposeRequest("map-contract-fixture",
                new GameGeneration(200332, new PythonOnlyUInt64(new BigInteger("134371375868945259"))),
                "recording-actual-session", new SavedFrame("native:1", 2, 1,
                53279400, 40526, "native-40526-1bec95182886"), "2026-10-22T12:00:00.123456+00:00");
    }

    @Test void requestPersistenceAndComposerRetainTheExistingReceiptWireBytes() {
        CampaignMapComposeRequest original = request();
        byte[] serialized = original.toCanonicalBytes();
        CampaignMapComposeRequest decoded = CampaignMapComposeRequest.fromBytes(serialized);
        assertEquals(original, decoded);
        assertArrayEquals(serialized, decoded.toCanonicalBytes());
        String expected = "{\"Game_map_visible\":true,\"actual_initial_frame\":{\"actor_character_id\":40526,"
                + "\"date_raw\":53279400,\"episode_run_id\":\"native-40526-1bec95182886\",\"native_revision\":1,"
                + "\"revision\":2,\"snapshot_id\":\"native:1\"},\"decision_text_visible\":true,"
                + "\"game_creation_filetime\":134371375868945259,\"game_pid\":200332,"
                + "\"machine_id\":\"map-contract-fixture\",\"observed_at_utc\":\"2026-10-22T12:00:00.123456+00:00\","
                + "\"recording_session_id\":\"recording-actual-session\",\"reviewer\":\"/root\","
                + "\"schema\":\"xar.current-saved-root-map-review/v1\",\"status\":\"GREEN\"}";
        byte[] produced = CampaignMapAdmissionComposer.compose(serialized);
        assertArrayEquals(expected.getBytes(StandardCharsets.UTF_8), produced);
        CampaignMapAdmission receipt = CampaignMapAdmission.fromJson(StrictJson.parse(produced));
        assertEquals(original.nativeLaunch(), receipt.game());
        assertEquals(original.actualInitialFrame(), receipt.actualInitialFrame());
        assertArrayEquals(produced, receipt.toCanonicalBytes());
    }

    @Test void parsedRequestsRetainNoMutableJsonNodeAndNeverInventMissingVisibility() {
        ObjectNode json = request().toJson();
        CampaignMapComposeRequest decoded = CampaignMapComposeRequest.fromJson(json);
        json.put("machine_id", "later-mutation");
        assertEquals("map-contract-fixture", decoded.machineId());
        for (String visibility : new String[] {"game_map_visible", "decision_text_visible"}) {
            ObjectNode missing = request().toJson(); missing.remove(visibility);
            ObjectNode nullValue = request().toJson(); nullValue.putNull(visibility);
            ObjectNode falseValue = request().toJson(); falseValue.put(visibility, false);
            ObjectNode number = request().toJson(); number.put(visibility, 1);
            for (ObjectNode bad : new ObjectNode[] {missing, nullValue, falseValue, number}) {
                byte[] bytes = StrictJson.canonical(bad, StrictJson.INPUT_MAX_BYTES);
                assertThrows(ContractViolationException.class, () -> CampaignMapComposeRequest.fromBytes(bytes));
                assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(bytes));
            }
        }
    }

    @Test void requestWireUsesTheNumericPythonLaneAndRejectsAnAlternateSchema() {
        ObjectNode request = request().toJson();
        ((ObjectNode) request.get("native_launch")).put("creation_filetime", StrictJson.UINT64_MAX);
        CampaignMapComposeRequest decoded = CampaignMapComposeRequest.fromJson(request);
        assertEquals(StrictJson.UINT64_MAX, decoded.nativeLaunch().creationFiletime().value());
        assertEquals(decoded, CampaignMapComposeRequest.fromBytes(decoded.toCanonicalBytes()));
        ((ObjectNode) request.get("native_launch")).put("creation_filetime", StrictJson.UINT64_MAX.toString());
        assertThrows(ContractViolationException.class, () -> CampaignMapComposeRequest.fromJson(request));
        ObjectNode alternate = request().toJson();
        alternate.put("schema", CampaignMapAdmission.SCHEMA);
        assertThrows(ContractViolationException.class, () -> CampaignMapComposeRequest.fromJson(alternate));
    }

    @Test void sharedIdentityAdvertisesTheSameRequestSchemaConsumedByTheComposer() {
        CampaignMapProtocol.ProducerIdentity identity = CampaignMapProtocol.identity("fixture.Adapter");
        assertEquals(CampaignMapComposeRequest.SCHEMA, identity.request_schema());
        assertEquals(CampaignMapAdmissionComposer.REQUEST_SCHEMA, identity.request_schema());
        assertEquals("fixture.Adapter", identity.implementation());
        assertEquals("xar.java-map-admission-producer-identity/v1", identity.schema());
        assertEquals("java-quarkus-map-admission/v1", identity.producer());
        assertEquals("0.1.0", identity.producer_version());
    }
}
