package org.xar.ck3.control.warpolicy;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact current producer schema regression; no native producer or Game was executed for this fixture. */
final class NativeTerminationTermsUnsupportedTest {
    @Test void actual4UnsupportedRaiktorRemainsUnavailableAcrossTheSoleCodecAndWireRoundtrip() {
        ObjectNode packet = packet();
        ObjectNode normalized = NativeTerminationTerms.normalize(packet, 77);
        assertEquals("unsupported", normalized.get("status").textValue());
        assertFalse(normalized.at("/readiness/ready").booleanValue());
        assertFalse(normalized.has("claims")); assertFalse(normalized.has("gold_reparations"));
        assertEquals(normalized, NativeTerminationTerms.normalize(StrictJson.parse(StrictJson.canonical(normalized)), 77));
    }
    @Test void legacyRaiktorAndFalseAvailablePacketsRemainRejected() {
        ObjectNode legacy = packet(); ObjectNode provenance = (ObjectNode) legacy.get("provenance");
        provenance.put("game_version", "1.19.0.6").put("executable_sha256", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86")
                .put("native_reader", "CWar+0x270/+0x290;0x28B1AA0")
                .put("claim_script_sha256", "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1");
        assertThrows(IllegalArgumentException.class, () -> NativeTerminationTerms.normalize(legacy, 77));
        ObjectNode forged = packet(); forged.put("status", "available");
        assertThrows(IllegalArgumentException.class, () -> NativeTerminationTerms.normalize(forged, 77));
        ObjectNode claim = packet(); ((ObjectNode) claim.get("casus_belli")).put("canonical_key", "claim_cb");
        assertThrows(IllegalArgumentException.class, () -> NativeTerminationTerms.normalize(claim, 77));
    }
    @Test void wrongFieldTypeMissingProvenanceAndWarIdentityFailClosed() {
        ObjectNode wrong = packet(); wrong.put("war_id", true);
        assertThrows(IllegalArgumentException.class, () -> NativeTerminationTerms.normalize(wrong, 77));
        ObjectNode missing = packet(); ((ObjectNode) missing.get("provenance")).remove("claim_script_sha256");
        assertThrows(IllegalArgumentException.class, () -> NativeTerminationTerms.normalize(missing, 77));
        assertThrows(IllegalArgumentException.class, () -> NativeTerminationTerms.normalize(packet(), 78));
    }
    private static ObjectNode packet() {
        return (ObjectNode) StrictJson.parse("""
            {"schema_version":1,"status":"unsupported","war_id":77,
             "casus_belli":{"database_index":91,"canonical_key":"raiktor_claim_cb"},
             "supported_slice":"claim_cb_claim_disposition","reason":"casus_belli_not_claim_cb",
             "readiness":{"ready":false},"provenance":{
               "game_version":"1.20.0.4",
               "executable_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
               "native_reader":"CWar+0x270/+0x290;0x2B9ECB0",
               "present_claim_lifecycle":"present_only_vtable_slot_0_delete_flags_0",
               "claim_script_sha256":"887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4"}}
            """.getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
}
