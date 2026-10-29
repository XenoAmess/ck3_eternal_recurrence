package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle;

/** Pure configuration DATA and original-owner codec regression; no Native authority is created. */
public final class NativeColdAdoptionProjectionLifecycleTest {
    private static ObjectNode projection(ObjectNode lifecycle) {
        ObjectNode checkpoint = StrictJson.object().put("sha256", "a".repeat(64)).put("size", 1).put("date_raw", 1066);
        ObjectNode pending = StrictJson.object().put("format_version", 2).put("bridge_pid", 17)
                .put("episode_character_id", 41).put("episode_run_id", "fixture-episode")
                .put("command_history_length", 0).put("original_cold_ready", false);
        pending.set("succession_lifecycle", lifecycle);
        pending.set("last_checkpoint", checkpoint);
        pending.putNull("checkpoint_anchor");
        ObjectNode result = StrictJson.object().put("schema", NativeColdAdoptionProjection.SCHEMA)
                .put("binding_state", "pending_cold_candidate").put("session_bridge_pid", 17);
        result.putNull("restore_kind"); result.putNull("rejection"); result.set("pending", pending);
        return result;
    }
    private static Lifecycle roundtrip(Lifecycle lifecycle) {
        ObjectNode source = projection(lifecycle.toJson());
        var parsed = NativeColdAdoptionProjection.fromJson(source);
        assertEquals(source.toString(), parsed.toJson().toString());
        var restored = NativeColdAdoptionProjection.parse(parsed.toJson().toString().getBytes(StandardCharsets.UTF_8));
        assertEquals(parsed.toJson(), restored.toJson());
        assertEquals(lifecycle, restored.pending().orElseThrow().lifecycle());
        return restored.pending().orElseThrow().lifecycle();
    }
    @Test void configuredVanillaRetainsExplicitNullsThroughActualProjectionCodec() {
        Lifecycle value = roundtrip(Lifecycle.ordinaryVanilla());
        assertEquals("ordinary_campaign_succession", value.lifecycle());
        assertTrue(value.xarEnabled().isEmpty());
        assertTrue(value.environmentSha256().isEmpty());
        assertTrue(value.toJson().get("xar_enabled").isNull());
        assertTrue(value.toJson().get("environment_sha256").isNull());
        assertFalse(value.pactContract().contains("verified"));
        assertFalse(value.source().contains("verified"));
    }
    @Test void legacyProfilesKeepTheirOriginalRoles() {
        roundtrip(new Lifecycle("rogue_one_life", Optional.of("xar_on"), "terminal_settlement_required", "legacy-driver-default", Optional.empty()));
        roundtrip(new Lifecycle("ordinary_campaign_succession", Optional.of("xar_off"), "absent_by_fresh_campaign_xar_off_contract", "fixture-environment", Optional.of("b".repeat(64))));
        roundtrip(new Lifecycle("ordinary_campaign_succession", Optional.empty(), "absent_by_verified_xar_mod_not_loaded", "absent_by_verified_xar_mod_not_loaded", Optional.of("c".repeat(64))));
        roundtrip(new Lifecycle("unknown", Optional.empty(), "unknown", "unbound", Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> new Lifecycle("ordinary_campaign_succession", Optional.of("xar_off"),
                "absent_by_fresh_campaign_xar_off_contract", "fixture-environment", Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> new Lifecycle("ordinary_campaign_succession", Optional.empty(),
                "absent_by_verified_xar_mod_not_loaded", "absent_by_verified_xar_mod_not_loaded", Optional.empty()));
    }
    @Test void nullableFieldsAreRequiredAndRejectOtherJsonTypes() {
        for (String field : List.of("xar_enabled", "environment_sha256")) {
            ObjectNode missing = Lifecycle.ordinaryVanilla().toJson(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> NativeColdAdoptionProjection.fromJson(projection(missing)), field);
            for (String json : List.of("true", "1", "1.0", "[]", "{}", "\"\"")) {
                JsonNode invalid = StrictJson.parse(json.getBytes(StandardCharsets.UTF_8), 1024);
                ObjectNode changed = Lifecycle.ordinaryVanilla().toJson(); changed.set(field, invalid);
                assertThrows(IllegalArgumentException.class, () -> NativeColdAdoptionProjection.fromJson(projection(changed)), field + "=" + json);
            }
        }
    }
    @Test void vanillaConfigurationCannotReclassifyLoadedXarOrAnEnvironmentBinding() {
        for (String xar : List.of("xar_off", "xar_on")) {
            ObjectNode changed = Lifecycle.ordinaryVanilla().toJson().put("xar_enabled", xar);
            assertThrows(IllegalArgumentException.class, () -> NativeColdAdoptionProjection.fromJson(projection(changed)));
        }
        ObjectNode environment = Lifecycle.ordinaryVanilla().toJson().put("environment_sha256", "d".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> NativeColdAdoptionProjection.fromJson(projection(environment)));
        ObjectNode inconsistent = Lifecycle.ordinaryVanilla().toJson().put("source", "different-configuration");
        assertThrows(IllegalArgumentException.class, () -> NativeColdAdoptionProjection.fromJson(projection(inconsistent)));
    }
}

