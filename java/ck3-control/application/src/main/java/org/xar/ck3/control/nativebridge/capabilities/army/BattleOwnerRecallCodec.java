package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleResponseCodec.exactOptional;

/** Current owner operands do not attest the scheduler's E(context) or a future recall selection. */
public final class BattleOwnerRecallCodec {
    private BattleOwnerRecallCodec() { }
    public static JsonNode normalize(JsonNode raw, boolean lifecycleAvailable) {
        if (raw.isNull()) return raw;
        ObjectNode n = closed(raw, "schema_version", "status", "unavailable_reason", "raw_inputs_ready", "native_context_prefix_status", "native_context_prefix_admitted", "native_selection_ready", "owners_in_stored_order");
        require(i32(n.get("schema_version")) == 1 && lifecycleAvailable, "native recall requires available current lifecycle");
        status(n); bool(n.get("raw_inputs_ready")); equal(n.get("native_context_prefix_status"), "unobserved_scheduler_context");
        require(n.get("native_context_prefix_admitted").isNull() && !bool(n.get("native_selection_ready")), "current recall invented scheduler admission/selection");
        var owners = array(n.get("owners_in_stored_order"), BattleOwnerRecallCodec::owner);
        require(!text(n.get("status")).equals("unavailable") || owners.isEmpty() && !bool(n.get("raw_inputs_ready")), "unavailable recall invented owner operands");
        return n.deepCopy();
    }
    private static ObjectNode owner(JsonNode raw) {
        ObjectNode n = exactOptional(raw, Set.of("owner_character_id", "land_318_count_raw", "owner_target_source_title_id", "owner_native_recall_target_province_id", "target_status", "owned_cunit_roster_status", "raw_inputs_ready", "owned_cunits_in_stored_order"), Set.of("native_activity_context_v1"));
        int owner = full(n.get("owner_character_id")).value(); Integer count = optionalI32(n.get("land_318_count_raw"));
        optionalFull(n.get("owner_target_source_title_id")); optionalFull(n.get("owner_native_recall_target_province_id"));
        nonempty(n.get("target_status")); nonempty(n.get("owned_cunit_roster_status")); bool(n.get("raw_inputs_ready"));
        array(n.get("owned_cunits_in_stored_order"), unit -> unit(unit, count));
        if (n.has("native_activity_context_v1") && !n.get("native_activity_context_v1").isNull()) activity(n.get("native_activity_context_v1"), owner);
        return n;
    }
    private static ObjectNode unit(JsonNode raw, Integer count) {
        ObjectNode n = closed(raw, "public_cunit_id", "status", "receiver_owner_character_id", "native_carmy_id", "attached_combat_id", "current_province_id", "army_1d4_raw", "army_1ec_raw", "first_fallback_raw_condition", "second_fallback_raw_condition");
        ArmyJson.unit(n.get("public_cunit_id")); require(Set.of("available", "unit_unresolved", "army_unresolved").contains(text(n.get("status"))), "native recall unit status");
        for (String key : List.of("receiver_owner_character_id", "native_carmy_id", "attached_combat_id", "current_province_id")) optionalFull(n.get(key));
        Integer first = optionalRange(n.get("army_1d4_raw"), 0, 255), second = optionalRange(n.get("army_1ec_raw"), 0, 255);
        condition(n.get("first_fallback_raw_condition"), count, first); condition(n.get("second_fallback_raw_condition"), count, second); return n;
    }
    private static void condition(JsonNode raw, Integer count, Integer flag) {
        Boolean expected = Integer.valueOf(0).equals(count) || Integer.valueOf(0).equals(flag) ? Boolean.FALSE : count == null || flag == null ? null : Boolean.TRUE;
        require(expected == null ? raw.isNull() : !raw.isNull() && bool(raw) == expected, "fallback raw condition differs from native count/flag");
    }
    private static ObjectNode activity(JsonNode raw, int owner) {
        ObjectNode n = exactOptional(raw, Set.of("schema_version", "status", "unavailable_reason", "membership_observed", "matched_contexts_in_native_order"), Set.of("owner_prefix_inputs"));
        require(i32(n.get("schema_version")) == 1, "activity context version"); status(n); bool(n.get("membership_observed"));
        array(n.get("matched_contexts_in_native_order"), value -> activityMatch(value, owner));
        if (n.has("owner_prefix_inputs") && !n.get("owner_prefix_inputs").isNull()) ownerPrefix(n.get("owner_prefix_inputs")); return n;
    }
    private static ObjectNode activityMatch(JsonNode raw, int owner) {
        ObjectNode n = closed(raw, "collection", "prefix_kind", "stored_index", "actor_character_id", "status", "unavailable_reason", "e_prefix_admitted", "context_state_raw", "context_16_raw", "context_2e_raw", "government_flags_40_raw", "plin_flags_2f0_raw");
        require(Set.of("fallback_d8", "mission_90").contains(text(n.get("collection"))), "activity collection invalid"); equal(n.get("prefix_kind"), "e_1a781a0");
        nonnegative(n.get("stored_index")); require(i32(n.get("actor_character_id")) == owner, "activity owner differs"); status(n);
        if (text(n.get("status")).equals("available")) bool(n.get("e_prefix_admitted")); else require(n.get("e_prefix_admitted").isNull(), "unavailable E prefix invented admission");
        optionalI32(n.get("context_state_raw")); optionalRange(n.get("context_16_raw"), 0, 255); optionalRange(n.get("context_2e_raw"), 0, 255);
        if (!n.get("government_flags_40_raw").isNull()) u64(n.get("government_flags_40_raw")); optionalRange(n.get("plin_flags_2f0_raw"), 0, 65535); return n;
    }
    private static ObjectNode ownerPrefix(JsonNode raw) {
        ObjectNode n = closed(raw, "status", "unavailable_reason", "owner_land_present", "government_status", "government_flags_40_raw", "government_bit41", "owner_necessary_condition", "plin_selection", "plin_status", "plin_flags_2f0_raw", "plin_bit8");
        status(n); require(Set.of("available", "unavailable", "invalid_magic", "owner_land_absent").contains(text(n.get("government_status"))), "government source status");
        require(Set.of("owner_first_match", "native_fallback", "unresolved").contains(text(n.get("plin_selection"))), "PlIn selection source status");
        require(Set.of("available", "unavailable", "invalid_identity_native_literal5").contains(text(n.get("plin_status"))), "PlIn source status");
        for (String key : List.of("owner_land_present", "government_bit41", "owner_necessary_condition", "plin_bit8")) if (!n.get(key).isNull()) bool(n.get(key));
        if (!n.get("government_flags_40_raw").isNull()) u64(n.get("government_flags_40_raw")); optionalRange(n.get("plin_flags_2f0_raw"), 0, 65535); return n;
    }
    private static void status(ObjectNode n) {
        String status = text(n.get("status")); require(Set.of("available", "unavailable").contains(status), "native source availability invalid");
        if (status.equals("available")) require(n.get("unavailable_reason").isNull(), "available native source invented reason"); else nonempty(n.get("unavailable_reason"));
    }
    private static Integer optionalI32(JsonNode raw) { return raw.isNull() ? null : i32(raw); }
    private static void optionalFull(JsonNode raw) { if (!raw.isNull()) full(raw); }
    private static Integer optionalRange(JsonNode raw, int minimum, int maximum) {
        Integer value = optionalI32(raw); require(value == null || value >= minimum && value <= maximum, "native unsigned narrow operand out of bounds"); return value;
    }
}
