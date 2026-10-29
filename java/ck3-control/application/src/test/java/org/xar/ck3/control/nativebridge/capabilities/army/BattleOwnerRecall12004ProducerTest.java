package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

/** Requires the real compiled C++ fixture; fixture-owned storage is actual=0. */
final class BattleOwnerRecall12004ProducerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    @Test void exactCurrentFactoryReaderSerializerAndStrictJavaConsumer() throws Exception {
        String configured = System.getProperty("xar.ownerRecall12004.nativeWire");
        assertNotNull(configured, "required actual4 owner-recall C++ fixture wire; no skip/fallback");
        Path wire = Path.of(configured);
        assertTrue(wire.isAbsolute() && Files.isRegularFile(wire), "absolute existing C++ wire required");
        String expectedSha = System.getProperty("xar.ownerRecall12004.nativeWireSha256");
        assertNotNull(expectedSha, "required fresh native producer output SHA-256; no skip/fallback");
        assertTrue(expectedSha.matches("[0-9a-f]{64}"), "canonical lowercase SHA-256 required");
        byte[] wireBytes = Files.readAllBytes(wire);
        assertTrue(wireBytes.length > 0 && wireBytes.length <= RawJson.MAXIMUM_BYTES,
                "native producer wire must fit the existing Army8MiB boundary");
        assertEquals(expectedSha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(wireBytes)),
                "native wire differs from the recorded fresh producer output");
        ObjectNode top = closed(JSON.readTree(wireBytes),
                "schema_version", "actual", "executable_sha256", "cases");
        assertEquals(1, i32(top.get("schema_version"))); assertEquals(0, i32(top.get("actual")));
        assertEquals("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
                text(top.get("executable_sha256")));
        Set<String> required = Set.of("title_zero_public_zero_highbit_combat", "title_highbit",
                "title_wrong_generation", "type2_highbit_child", "fallback_source_unavailable",
                "zero_count_false", "zero_army_flag_false", "public_unit_wrong_generation",
                "private_army_zero_rejected", "unpaused_scope", "changed_date",
                "transition_current_combat", "transition_stale_combat",
                "fallback_holy_order_zero", "fallback_negative_nonzero_first_count",
                "fallback_holy_generation_uses_native_fallback", "fallback_holy_null_registry_uses_native_fallback",
                "fallback_mercenary_zero_type2", "fallback_title_flag_nonzero", "fallback_domi_zero",
                "fallback_domi_backup_province", "fallback_derived_coda_fallback", "fallback_first_source_unavailable");
        Set<String> seen = new HashSet<>();
        for (JsonNode value : top.withArray("cases")) {
            ObjectNode row = closed(value, "name", "leaf"); String name = text(row.get("name"));
            assertTrue(required.contains(name) && seen.add(name), "unknown/duplicate C++ fixture case");
            JsonNode normalized = BattleOwnerRecallCodec.normalize(row.get("leaf"), true);
            assertEquals(row.get("leaf"), normalized);
            assertEquals(normalized, BattleOwnerRecallCodec.normalize(
                    JSON.readTree(JSON.writeValueAsBytes(normalized)), true));
            ObjectNode invented = (ObjectNode) normalized.deepCopy(); invented.put("native_selection_ready", true);
            assertThrows(IllegalArgumentException.class, () -> BattleOwnerRecallCodec.normalize(invented, true));
            if (Set.of("fallback_holy_order_zero", "fallback_negative_nonzero_first_count",
                    "fallback_holy_generation_uses_native_fallback", "fallback_holy_null_registry_uses_native_fallback",
                    "fallback_mercenary_zero_type2", "fallback_title_flag_nonzero", "fallback_domi_zero",
                    "fallback_domi_backup_province", "fallback_derived_coda_fallback").contains(name)) {
                JsonNode owner = normalized.get("owners_in_stored_order").get(0);
                assertEquals(0x1000004, i32(owner.get("owner_native_recall_target_province_id")));
                assertEquals("available_native_fallback_28B2200", text(owner.get("target_status")));
            }
            if (name.equals("title_zero_public_zero_highbit_combat")) {
                JsonNode owner = normalized.get("owners_in_stored_order").get(0);
                assertEquals(0, i32(owner.get("owner_target_source_title_id")));
                assertEquals(0, i32(owner.get("owned_cunits_in_stored_order").get(1).get("public_cunit_id")));
                assertEquals(Integer.MIN_VALUE + 3, i32(owner.get("owned_cunits_in_stored_order").get(1).get("attached_combat_id")));
                ObjectNode malformed = (ObjectNode) normalized.deepCopy();
                ((ObjectNode) malformed.get("owners_in_stored_order").get(0)).put("land_318_count_raw", true);
                assertThrows(IllegalArgumentException.class, () -> BattleOwnerRecallCodec.normalize(malformed, true));
            }
        }
        assertEquals(required, seen, "incomplete native producer-to-consumer matrix");
    }
}
