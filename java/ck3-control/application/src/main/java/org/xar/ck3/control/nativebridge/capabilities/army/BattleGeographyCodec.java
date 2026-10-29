package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleControlExtensionCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Set;

/** Checked retained/current geography operands; no future constructor reconstruction. */
final class BattleGeographyCodec {
    private BattleGeographyCodec() { }
    static JsonNode normalize(JsonNode raw, String field) {
        require(field != null && !field.isEmpty(), "geography field name required");
        if (nil(raw)) return raw.deepCopy();
        ObjectNode n = object(raw);
        optionalKeys(n, Set.of("terrain", "constructor_adjacency_kind_raw", "holding_defender"),
                Set.of("constructor_rule_effects_v1", "current_rule_context_v1", "stored_advantage_sources_v1", "current_dynamic_advantage_v1", "current_dynamic_components_v1", "current_own_nested_modifier_v1"));
        ObjectNode terrain = closed(n.get("terrain"), "status", "key", "combat_width_multiplier_raw", "scale", "unavailable_reason");
        eqInt(terrain.get("scale"), 100_000); nullableI64(terrain.get("combat_width_multiplier_raw"));
        String terrainStatus = text(terrain.get("status"));
        if (terrainStatus.equals("available")) { nonempty(terrain.get("key")); require(!nil(terrain.get("combat_width_multiplier_raw")) && nil(terrain.get("unavailable_reason")), "available terrain incomplete"); }
        else { require(terrainStatus.equals("unavailable") && nil(terrain.get("key")) && nil(terrain.get("combat_width_multiplier_raw")), "unavailable terrain has operands"); nonempty(terrain.get("unavailable_reason")); }
        nullableI32(n.get("constructor_adjacency_kind_raw")); nullableBool(n.get("holding_defender"));
        if (n.has("constructor_rule_effects_v1")) effects(n.get("constructor_rule_effects_v1"), n.get("constructor_adjacency_kind_raw"));
        if (n.has("current_rule_context_v1")) ruleContext(n.get("current_rule_context_v1"), n.get("holding_defender"), n.get("constructor_rule_effects_v1"));
        if (n.has("stored_advantage_sources_v1")) stored(n.get("stored_advantage_sources_v1"));
        if (n.has("current_dynamic_advantage_v1")) dynamic(n.get("current_dynamic_advantage_v1"));
        if (n.has("current_dynamic_components_v1")) components(n.get("current_dynamic_components_v1"), false);
        if (n.has("current_own_nested_modifier_v1")) components(n.get("current_own_nested_modifier_v1"), true);
        return n.deepCopy();
    }
    private static void effects(JsonNode raw, JsonNode kindNode) {
        ObjectNode n = closed(raw, "status", "points_scale", "unavailable_reason", "rows");
        eqInt(n.get("points_scale"), 1); String status = text(n.get("status"));
        require(status.equals("available") || status.equals("unavailable"), "retained rule status differs");
        if (status.equals("available")) require(nil(n.get("unavailable_reason")), "available rules have reason"); else nonempty(n.get("unavailable_reason"));
        List<JsonNode> rows = rows(n.get("rows")); require(rows.isEmpty() || rows.size() == 3, "retained source slots must be empty or three");
        require(!rows.isEmpty() || !status.equals("available"), "available retained rule slots missing");
        if (rows.isEmpty()) return;
        require(!nil(kindNode), "retained source kind missing"); int kind = i32(kindNode); require(kind >= 0 && kind <= 3, "unsupported retained source kind");
        boolean allKnown = true;
        for (int index = 0; index < 3; index++) {
            ObjectNode row = closed(rows.get(index), "stage", "side_index", "rules_pointer_offset", "status", "key", "advantage_points", "unavailable_reason");
            equal(row.get("stage"), List.of("attacker_adjacency", "defender_adjacency", "holding_defender").get(index));
            require(i32(row.get("side_index")) == (index == 0 ? 0 : 1), "retained effect side differs");
            require(i32(row.get("rules_pointer_offset")) == (index == 0 ? 0xF70 + 8 * kind : index == 1 ? 0xFA0 + 8 * kind : 0xF10), "retained effect source slot differs");
            nullableI32(row.get("advantage_points")); String rowStatus = text(row.get("status"));
            if (rowStatus.equals("available")) {
                nonempty(row.get("key")); require(!nil(row.get("advantage_points")) && nil(row.get("unavailable_reason")), "available effect incomplete");
                if (index == 2) equal(row.get("key"), "holding_defender_advantage");
            } else {
                require(nil(row.get("key")) && nil(row.get("advantage_points")), "unobserved effect contains values");
                if (rowStatus.equals("not_selected")) require(index != 2 && nil(row.get("unavailable_reason")), "invalid adjacency skip");
                else { require(rowStatus.equals("unavailable"), "unknown retained effect status"); nonempty(row.get("unavailable_reason")); allKnown = false; }
            }
        }
        require(status.equals("available") == allKnown, "retained effect completeness differs");
    }
    private static void ruleContext(JsonNode raw, JsonNode holdingDefender, JsonNode effects) {
        ObjectNode n = closed(raw, "holding_multiplier", "commander_exclusion");
        ObjectNode holding = closed(n.get("holding_multiplier"), "status", "scale", "province_multiplier_raw", "province_has_holding", "holding_modifier_raw", "unavailable_reason");
        eqInt(holding.get("scale"), 100_000); nullableI64(holding.get("province_multiplier_raw")); nullableI64(holding.get("holding_modifier_raw")); nullableBool(holding.get("province_has_holding"));
        ObjectNode commander = closed(n.get("commander_exclusion"), "status", "selected_character_id_raw", "used_native_fallback", "defender_adjacency_excluded", "unavailable_reason");
        i32(commander.get("selected_character_id_raw")); nullableBool(commander.get("used_native_fallback")); nullableBool(commander.get("defender_adjacency_excluded"));
        for (ObjectNode row : List.of(holding, commander)) {
            String status = text(row.get("status")); require(Set.of("available", "not_applicable", "unavailable").contains(status), "rule context status differs");
            if (status.equals("unavailable")) nonempty(row.get("unavailable_reason")); else require(nil(row.get("unavailable_reason")), "known rule context has a reason");
        }
        String holdingStatus = text(holding.get("status"));
        if (holdingStatus.equals("available")) {
            yes(holdingDefender); require(!nil(holding.get("province_multiplier_raw")) && !nil(holding.get("province_has_holding")), "holding current operands missing");
            require(bool(holding.get("province_has_holding")) != nil(holding.get("holding_modifier_raw")), "holding modifier branch differs");
        } else if (holdingStatus.equals("not_applicable")) {
            no(holdingDefender); require(nil(holding.get("province_multiplier_raw")) && nil(holding.get("province_has_holding")) && nil(holding.get("holding_modifier_raw")), "inactive holding operands differ");
        }
        String defenderStatus = null;
        if (effects != null && effects.isObject() && effects.get("rows").isArray() && effects.get("rows").size() == 3) defenderStatus = text(effects.get("rows").get(1).get("status"));
        String commanderStatus = text(commander.get("status"));
        if (commanderStatus.equals("available")) require("available".equals(defenderStatus) && !nil(commander.get("used_native_fallback")) && !nil(commander.get("defender_adjacency_excluded")), "commander current selected effect incomplete");
        else if (commanderStatus.equals("not_applicable")) require("not_selected".equals(defenderStatus) && nil(commander.get("used_native_fallback")) && nil(commander.get("defender_adjacency_excluded")), "commander inactive source differs");
    }
    private static void flags(JsonNode raw) {
        ObjectNode n = closed(raw, "status", "flag88_raw", "flag89_raw", "unavailable_reason"); String status = text(n.get("status"));
        if (status.equals("available")) { require(nonnegative(n.get("flag88_raw")) <= 255 && nonnegative(n.get("flag89_raw")) <= 255 && nil(n.get("unavailable_reason")), "available effect flags differ"); }
        else { require(status.equals("unavailable") && nil(n.get("flag88_raw")) && nil(n.get("flag89_raw")), "unavailable effect flags have operands"); nonempty(n.get("unavailable_reason")); }
    }
    private static void stored(JsonNode raw) {
        ObjectNode n = closed(raw, "scale", "base_advantage_raw", "resolved_advantage_raw", "sides"); eqInt(n.get("scale"), 100_000); fields64(n, "base_advantage_raw", "resolved_advantage_raw");
        List<JsonNode> sides = pair(n.get("sides"));
        for (int index = 0; index < 2; index++) {
            ObjectNode side = closed(sides.get(index), "side_index", "status", "unavailable_reason", "rows"); require(i32(side.get("side_index")) == index, "stored ledger side order differs");
            String status = text(side.get("status"));
            if (status.equals("unavailable")) { require(nil(side.get("rows")), "unavailable stored ledger has rows"); nonempty(side.get("unavailable_reason")); continue; }
            require(status.equals("available") && nil(side.get("unavailable_reason")), "stored ledger status differs"); List<JsonNode> rows = rows(side.get("rows")); require(rows.size() <= 65536, "stored ledger row bound exceeded");
            for (JsonNode rawRow : rows) {
                ObjectNode row = object(rawRow); optionalKeys(row, Set.of("effect_key", "key_unavailable_reason", "contribution_raw"), Set.of("effect_flags_v1"));
                if (nil(row.get("effect_key"))) nonempty(row.get("key_unavailable_reason"));
                else { String key = nonempty(row.get("effect_key")); require(key.codePointCount(0, key.length()) <= 512 && nil(row.get("key_unavailable_reason")), "decoded effect key differs"); }
                i64(row.get("contribution_raw")); if (row.has("effect_flags_v1")) flags(row.get("effect_flags_v1"));
            }
        }
    }
    private static void dynamic(JsonNode raw) {
        ObjectNode n = closed(raw, "scale", "base_advantage_raw", "stored_resolved_advantage_raw", "sides"); eqInt(n.get("scale"), 100_000); fields64(n, "base_advantage_raw", "stored_resolved_advantage_raw"); List<JsonNode> sides = pair(n.get("sides"));
        for (int index = 0; index < 2; index++) {
            ObjectNode side = closed(sides.get(index), "side_index", "status", "current_roll_points", "selected_character_id_raw", "side_dynamic_total_raw", "unavailable_reason");
            require(i32(side.get("side_index")) == index, "dynamic side order differs"); fields32(side, "current_roll_points", "selected_character_id_raw"); availabilityRow(side, "side_dynamic_total_raw", 64);
        }
    }
    private static void selection(JsonNode raw) {
        ObjectNode n = closed(raw, "status", "resolved_character_id_raw", "used_native_fallback", "unavailable_reason"); String status = text(n.get("status"));
        if (status.equals("available")) { i32(n.get("resolved_character_id_raw")); bool(n.get("used_native_fallback")); require(nil(n.get("unavailable_reason")), "available selection has reason"); }
        else { require(status.equals("unavailable") && nil(n.get("resolved_character_id_raw")) && nil(n.get("used_native_fallback")), "unavailable selection has lineage"); nonempty(n.get("unavailable_reason")); }
    }
    private static void component(JsonNode raw, String name, int bits) { ObjectNode n = closed(raw, "status", "unavailable_reason", name); availabilityRow(n, name, bits); }
    private static void components(JsonNode raw, boolean ownNested) {
        ObjectNode n = ownNested ? closed(raw, "scale", "modifier_id", "sides") : closed(raw, "scale", "sides"); eqInt(n.get("scale"), 100_000); if (ownNested) eqInt(n.get("modifier_id"), 415);
        List<JsonNode> sides = pair(n.get("sides"));
        for (int index = 0; index < 2; index++) {
            ObjectNode side = ownNested ? closed(sides.get(index), "side_index", "selected_character_id_raw", "selection", "combat_side_aggregate", "selected_character_aggregate")
                    : closed(sides.get(index), "side_index", "current_roll_points", "selected_character_id_raw", "selection", "relation", "commander", "side_aggregate");
            require(i32(side.get("side_index")) == index, "component side order differs"); i32(side.get("selected_character_id_raw")); selection(side.get("selection"));
            if (ownNested) { component(side.get("combat_side_aggregate"), "amount_raw", 64); component(side.get("selected_character_aggregate"), "amount_raw", 64); }
            else { i32(side.get("current_roll_points")); component(side.get("relation"), "kind_raw", 32); component(side.get("commander"), "total_raw", 64); component(side.get("side_aggregate"), "total_raw", 64); }
        }
    }
}
