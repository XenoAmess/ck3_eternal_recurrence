package org.xar.ck3.control.nativebridge.capabilities.china_career;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;

/** An ABI profile represents the complete checked provenance, including every original RVA. */
public record CareerProvenance(Profile profile, String game_version, String executable_sha256) {
    public enum Profile { CAREER_HC, COLLECTIVE, NORMAL_EXIT, GOVERNANCE, SELECTOR }
    static CareerProvenance parse(JsonNode raw, Profile profile) {
        ObjectNode expected = JsonNodeFactory.instance.objectNode().put("game_version", VERSION).put("executable_sha256", EXE_SHA256);
        if (profile == Profile.SELECTOR) {
            expected.put("subject_contract_storage_slot_rva", "0x570CCA0").put("subject_contract_fallback_slot_rva", "0x570CC50")
                    .put("immediate_liege_rva", "0x2613480").put("primary_title_rva", "0x25F3350")
                    .put("effective_government_rva", "0x26165B0").put("is_human_player_rva", "0x28BCEB0");
        } else {
            String suffix = switch (profile) {
                case CAREER_HC -> "career-hc-workforce-postcondition";
                case COLLECTIVE -> "workforce-collective-snapshot";
                case NORMAL_EXIT -> "workforce-normal-exit-snapshot";
                case GOVERNANCE -> "manager-governance-snapshot";
                default -> throw new IllegalArgumentException("unknown ABI profile");
            };
            String allowlist = switch (profile) {
                case CAREER_HC -> "zg361-m360-route-b-career-hc-ledger-v1";
                case COLLECTIVE -> "zg361-workforce-collective-received-self-v1";
                case NORMAL_EXIT -> "zg361-workforce-normal-exit-received-self-v1";
                case GOVERNANCE -> "zg361-manager-governance-v1";
                default -> throw new IllegalArgumentException("unknown ABI profile");
            };
            expected.put("backend_id", "ck3-1.19.0.6-native-zhongguo-" + suffix + "-v1")
                    .put("consumer_id", "xar-autoplayer-zhongguo-" + suffix + "-v1").put("allowlist_id", allowlist)
                    .put("variable_context_for_scope_rva", "0x3329A40").put("variable_identifier_table_rva", "0x3B971A0")
                    .put("variable_identifier_lookup_rva", "0x3B97020").put("variable_identifier_name_rva", "0x3B97090")
                    .put("character_storage_slot_rva", "0x570C130");
            if (profile == Profile.CAREER_HC) expected.put("character_fallback_slot_rva", "0x570C138");
            if (profile == Profile.COLLECTIVE || profile == Profile.NORMAL_EXIT)
                expected.put("subject_allowlist_count", BigInteger.valueOf(profile == Profile.COLLECTIVE ? 144 : 94))
                        .put("owner_allowlist_count", BigInteger.valueOf(profile == Profile.COLLECTIVE ? 31 : 0))
                        .put("query_scope", profile == Profile.COLLECTIVE ? "paused_received_self_al_case_plus_owner_rolling_three_cycle" : "paused_received_self_workforce_normal_exit_lifecycle");
        }
        require(expected.equals(raw), "complete exact-build provenance changed");
        return new CareerProvenance(profile, text(raw.get("game_version")), text(raw.get("executable_sha256")));
    }
}
