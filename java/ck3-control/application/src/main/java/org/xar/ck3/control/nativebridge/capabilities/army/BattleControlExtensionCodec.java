package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;

/**
 * The checked JSON boundary for BattleControl's twelve optional observations.
 * Parent identity/side/ledger validation belongs to BattleResponseCodec. Values
 * remain in the historical native numeric JSON domain; this is not a JS encoder
 * or a claim that observed operands make a resumed simulation complete.
 */
public final class BattleControlExtensionCodec {
    private BattleControlExtensionCodec() { }
    public static final Set<String> OPTIONAL_FIELDS = Set.of("entry_preceding_capture_12004", "actual_geography_v1",
            "roll_cadence_interval", "current_phase_transition_inputs_v1", "current_finalizer_manager_inputs_v1",
            "current_warscore_caps_v1", "current_pursuit_inputs_v1", "actual_hard_casualty_sides",
            "pursuit_modifier_sides", "active_counter_inputs_v1", "current_loss_inputs_v1", "full_backing_inputs_v1");
    public static ObjectNode normalize(ObjectNode parent) {
        require(parent != null, "normalized BattleControl parent required");
        int combat = full(get(parent, "combat_id")).value(), province = id(get(parent, "province_id")).value();
        ObjectNode attacker = object(get(parent, "attacker")), defender = object(get(parent, "defender"));
        ObjectNode result = parent.deepCopy();
        if (parent.has("roll_cadence_interval")) nullableI32(parent.get("roll_cadence_interval"));
        if (parent.has("actual_hard_casualty_sides")) hard(parent.get("actual_hard_casualty_sides"), combat, province, attacker, defender, false);
        if (parent.has("pursuit_modifier_sides")) hard(parent.get("pursuit_modifier_sides"), combat, province, attacker, defender, true);
        if (parent.has("active_counter_inputs_v1")) counter(parent.get("active_counter_inputs_v1"), combat, province, attacker, defender);
        if (parent.has("current_loss_inputs_v1")) loss(parent.get("current_loss_inputs_v1"), combat, province, attacker, defender);
        if (parent.has("full_backing_inputs_v1")) backing(parent.get("full_backing_inputs_v1"), combat, province, attacker, defender);
        if (parent.has("current_phase_transition_inputs_v1")) phase(parent.get("current_phase_transition_inputs_v1"));
        if (parent.has("current_finalizer_manager_inputs_v1")) manager(parent.get("current_finalizer_manager_inputs_v1"), combat);
        if (parent.has("current_warscore_caps_v1")) warscore(parent.get("current_warscore_caps_v1"), combat);
        if (parent.has("current_pursuit_inputs_v1")) pursuit(parent.get("current_pursuit_inputs_v1"), combat);
        if (parent.has("actual_geography_v1")) result.set("actual_geography_v1", normalizeGeography(parent.get("actual_geography_v1"), "battle_control_snapshot.actual_geography_v1"));
        if (parent.has("entry_preceding_capture_12004")) {
            try { preceding(parent.get("entry_preceding_capture_12004"), combat); }
            catch (IllegalArgumentException invalidOptionalRawFacts) { result.putNull("entry_preceding_capture_12004"); }
        }
        return result;
    }
    public static JsonNode normalizeGeography(JsonNode raw, String field) { return BattleGeographyCodec.normalize(raw, field); }
    public static ObjectNode normalizeResume(ObjectNode value, ObjectNode normalizedParent) { return BattleResumeInputCodec.normalize(value, normalizedParent); }
    static boolean nil(JsonNode node) { require(node != null, "required field is missing"); return node.isNull(); }
    static void nullableI32(JsonNode node) { if (!nil(node)) i32(node); }
    static void nullableI64(JsonNode node) { if (!nil(node)) i64(node); }
    static void nullableBool(JsonNode node) { if (!nil(node)) bool(node); }
    static List<JsonNode> rows(JsonNode node) { return array(node, item -> item); }
    static List<JsonNode> pair(JsonNode node) { List<JsonNode> result = rows(node); require(result.size() == 2, "two native-order side slots required"); return result; }
    static void eqInt(JsonNode node, long expected) { require(integer(node).equals(BigInteger.valueOf(expected)), "same-frame integer differs"); }
    static void same(JsonNode left, JsonNode right) {
        require(left != null && right != null, "same-frame value is missing");
        if (left.isIntegralNumber() && right.isIntegralNumber()) require(integer(left).equals(integer(right)), "same-frame integer differs");
        else if (left.isArray() && right.isArray()) { require(left.size() == right.size(), "same-frame array size differs"); for (int i = 0; i < left.size(); i++) same(left.get(i), right.get(i)); }
        else if (left.isObject() && right.isObject()) { require(names(object(left)).equals(names(object(right))), "same-frame fields differ"); for (String key : names(object(left))) same(left.get(key), right.get(key)); }
        else require(left.equals(right), "same-frame JSON value differs");
    }
    static void fields64(ObjectNode row, String... names) { for (String name : names) i64(get(row, name)); }
    static void fields32(ObjectNode row, String... names) { for (String name : names) i32(get(row, name)); }
    static void optionalKeys(ObjectNode row, Set<String> required, Set<String> optional) { require(names(row).containsAll(required) && names(row).stream().allMatch(key -> required.contains(key) || optional.contains(key)), "missing or unknown optional observation fields"); }
    static void availabilityRow(ObjectNode row, String rawName, int bits) {
        String status = text(get(row, "status")); JsonNode raw = get(row, rawName), reason = get(row, "unavailable_reason");
        if (status.equals("available")) { if (bits == 32) i32(raw); else i64(raw); require(nil(reason), "available component has a reason"); }
        else { require(status.equals("unavailable") && nil(raw), "unavailable component must retain null"); nonempty(reason); }
    }
    static void phase(JsonNode raw) {
        if (nil(raw)) return;
        ObjectNode n = closed(raw, "forced_winner_raw", "result_start_date_raw", "minimum_elapsed_days", "sides");
        fields32(n, "forced_winner_raw", "result_start_date_raw", "minimum_elapsed_days");
        List<JsonNode> sides = pair(n.get("sides"));
        for (int index = 0; index < 2; index++) {
            ObjectNode side = closed(sides.get(index), "side_index", "stored_current_fighting_raw", "disallowed", "allow_early", "skip_pursuit", "first_native_carmy_id", "native_can_retreat", "owner_land_rule_allows");
            require(i32(side.get("side_index")) == index, "phase side order differs"); i64(side.get("stored_current_fighting_raw")); nullableI32(side.get("first_native_carmy_id"));
            for (String key : List.of("disallowed", "allow_early", "skip_pursuit")) bool(side.get(key));
            nullableBool(side.get("native_can_retreat")); nullableBool(side.get("owner_land_rule_allows"));
        }
    }
    static void manager(JsonNode raw, int combat) {
        if (nil(raw)) return;
        ObjectNode n = closed(raw, "source_combat_id", "combat_manager_row_admitted", "pending_suppression_sweep_raw", "pending_suppression_sweep");
        require(i32(n.get("source_combat_id")) == combat, "manager Combat identity differs"); bool(n.get("combat_manager_row_admitted"));
        int flag = nonnegative(n.get("pending_suppression_sweep_raw")); require(flag <= 255 && bool(n.get("pending_suppression_sweep")) == (flag != 0), "manager pending-sweep mirror differs");
    }
    static void warscore(JsonNode raw, int combat) {
        if (nil(raw)) return;
        ObjectNode n = closed(raw, "source_combat_id", "war_attacker_winner_cap_raw_q100000", "war_defender_winner_cap_raw_q100000");
        require(i32(n.get("source_combat_id")) == combat, "warscore Combat identity differs");
        fields64(n, "war_attacker_winner_cap_raw_q100000", "war_defender_winner_cap_raw_q100000");
    }
    static void pursuit(JsonNode raw, int combat) {
        if (nil(raw)) return;
        ObjectNode n = object(raw);
        optionalKeys(n, Set.of("scale", "source_combat_id", "pursuit_phase_days", "base_toughness_multiplier_raw", "minimum_pursuit_multiplier_raw", "pursuit_stat_multiplier_raw", "losing_side_index", "initial_loser_levy_soft_raw", "initial_loser_maa_soft_raw"), Set.of("losing_side_skip_pursuit"));
        require(i32(n.get("scale")) == 100_000 && i32(n.get("source_combat_id")) == combat, "pursuit identity or scale differs");
        i32(n.get("pursuit_phase_days")); fields64(n, "base_toughness_multiplier_raw", "minimum_pursuit_multiplier_raw", "pursuit_stat_multiplier_raw");
        nullableI32(n.get("losing_side_index")); nullableI64(n.get("initial_loser_levy_soft_raw")); nullableI64(n.get("initial_loser_maa_soft_raw"));
        if (n.has("losing_side_skip_pursuit")) nullableBool(n.get("losing_side_skip_pursuit"));
    }
    private static void backing(JsonNode raw, int combat, int province, ObjectNode attacker, ObjectNode defender) {
        if (nil(raw)) return;
        ObjectNode n = closed(raw, "scale", "source_combat_id", "source_target_province_id", "enumeration_complete", "sides");
        require(i32(n.get("scale")) == 1 && full(n.get("source_combat_id")).value() == combat && id(n.get("source_target_province_id")).value() == province, "backing identity or whole-soldier scale differs"); yes(n.get("enumeration_complete"));
        List<JsonNode> sides = pair(n.get("sides")); List<ObjectNode> parents = List.of(attacker, defender);
        for (int index = 0; index < 2; index++) {
            ObjectNode side = closed(sides.get(index), "side_index", "ordered_armies"); require(i32(side.get("side_index")) == index, "backing side order differs");
            List<JsonNode> armies = rows(side.get("ordered_armies")), expected = rows(get(parents.get(index), "ordered_armies"));
            require(armies.size() == expected.size(), "backing native Army census differs");
            for (int j = 0; j < armies.size(); j++) {
                ObjectNode army = closed(armies.get(j), "native_carmy_id", "public_cunit_id", "owner_character_id", "ordered_regiments");
                id(army.get("native_carmy_id")); unit(army.get("public_cunit_id")); id(army.get("owner_character_id"));
                for (String key : List.of("native_carmy_id", "public_cunit_id", "owner_character_id")) same(army.get(key), expected.get(j).get(key));
                for (JsonNode regiment : rows(army.get("ordered_regiments"))) { ObjectNode r = closed(regiment, "regiment_id", "current_soldiers"); full(r.get("regiment_id")); i32(r.get("current_soldiers")); }
            }
        }
    }
    private static void loss(JsonNode raw, int combat, int province, ObjectNode attacker, ObjectNode defender) {
        if (nil(raw)) return;
        ObjectNode n = object(raw);
        optionalKeys(n, Set.of("scale", "source_combat_id", "source_target_province_id", "stored_advantage_damage_factor_raw", "runtime_damage_scaling_raw", "runtime_main_hard_conversion_raw", "runtime_pursuit_hard_conversion_raw", "province_has_holding", "province_winter_hard_conversion_modifier_raw", "sides"), Set.of("runtime_advantage_scaling_raw"));
        require(i32(n.get("scale")) == 100_000 && id(n.get("source_combat_id")).value() == combat && id(n.get("source_target_province_id")).value() == province, "loss identity or scale differs");
        bool(n.get("province_has_holding")); fields64(n, "stored_advantage_damage_factor_raw", "runtime_damage_scaling_raw", "runtime_main_hard_conversion_raw", "runtime_pursuit_hard_conversion_raw", "province_winter_hard_conversion_modifier_raw");
        if (n.has("runtime_advantage_scaling_raw")) nullableI64(n.get("runtime_advantage_scaling_raw"));
        List<JsonNode> sides = pair(n.get("sides")); List<ObjectNode> parents = List.of(attacker, defender);
        for (int index = 0; index < 2; index++) {
            ObjectNode side = object(sides.get(index)); Set<String> base = Set.of("side_index", "outgoing_advantage_factor_raw", "own_hard_conversion_modifier_raw", "opposing_hard_conversion_modifier_raw");
            boolean levy = side.has("levy_damage_raw"); optionalKeys(side, base, levy ? Set.of("primary_participant_character_id", "levy_damage_raw") : Set.of());
            require(levy == side.has("primary_participant_character_id"), "loss levy fields must appear together");
            require(i32(side.get("side_index")) == index, "loss side order differs"); fields64(side, "outgoing_advantage_factor_raw", "own_hard_conversion_modifier_raw", "opposing_hard_conversion_modifier_raw");
            if (levy) { id(side.get("primary_participant_character_id")); same(side.get("primary_participant_character_id"), get(parents.get(index), "primary_participant_character_id")); nullableI64(side.get("levy_damage_raw")); }
        }
    }
    private static void hard(JsonNode raw, int combat, int province, ObjectNode attacker, ObjectNode defender, boolean pursuit) {
        ObjectNode n = closed(raw, "status", "source_combat_id", "source_target_province_id", "scale", "sides", "unavailable_reason");
        require(full(n.get("source_combat_id")).value() == combat && id(n.get("source_target_province_id")).value() == province, "modifier Combat/province identity differs"); eqInt(n.get("scale"), 100_000);
        String status = text(n.get("status"));
        if (status.equals("unavailable")) { require(nil(n.get("sides")), "unavailable modifier has sides"); nonempty(n.get("unavailable_reason")); return; }
        require(status.equals("available") && nil(n.get("unavailable_reason")), "modifier availability differs");
        List<JsonNode> sides = pair(n.get("sides")); List<ObjectNode> parents = List.of(attacker, defender);
        for (int index = 0; index < 2; index++) {
            ObjectNode side = pursuit ? closed(sides.get(index), "side_index", "encounter_role", "pursuit_efficiency_raw", "retreat_losses_raw")
                    : closed(sides.get(index), "side_index", "encounter_role", "ordered_army_ids", "commander_character_id", "own_modifier_raw", "enemy_modifier_raw");
            require(i32(side.get("side_index")) == index, "modifier side order differs"); equal(side.get("encounter_role"), index == 0 ? "attacker" : "defender");
            if (pursuit) fields64(side, "pursuit_efficiency_raw", "retreat_losses_raw");
            else {
                JsonNode selected = get(parents.get(index), "selected_commander_character_id"); int expectedCommander = selected.isNull() || integer(selected).signum() == 0 ? -1 : i32(selected);
                require(i32(side.get("commander_character_id")) == expectedCommander, "hard modifier commander differs");
                List<ArmyTypes.PublicUnitId> observed = units(side.get("ordered_army_ids"));
                List<ArmyTypes.PublicUnitId> expected = array(get(parents.get(index), "ordered_armies"), army -> unit(army.get("public_cunit_id")));
                require(observed.equals(expected), "hard modifier public Army order differs"); fields64(side, "own_modifier_raw", "enemy_modifier_raw");
            }
        }
    }
    private static void counter(JsonNode raw, int combat, int province, ObjectNode attacker, ObjectNode defender) {
        ObjectNode n = closed(raw, "schema_version", "status", "operand_census_complete", "source_combat_id", "source_target_province_id", "scale", "class_count", "sides", "contexts", "unavailable_reason");
        eqInt(n.get("schema_version"), 1); eqInt(n.get("scale"), 100_000);
        require(full(n.get("source_combat_id")).value() == combat && id(n.get("source_target_province_id")).value() == province, "counter identity differs");
        String status = text(n.get("status"));
        if (status.equals("unavailable")) { no(n.get("operand_census_complete")); require(nil(n.get("class_count")) && nil(n.get("sides")) && nil(n.get("contexts")), "unavailable counter contains partial operands"); nonempty(n.get("unavailable_reason")); return; }
        require(status.equals("available") && nil(n.get("unavailable_reason")), "counter availability differs"); yes(n.get("operand_census_complete"));
        int classes = id(n.get("class_count")).value(); require(classes <= 4096, "counter class bound exceeded");
        List<JsonNode> sides = pair(n.get("sides")), contexts = pair(n.get("contexts")); List<ObjectNode> parents = List.of(attacker, defender);
        for (int index = 0; index < 2; index++) {
            ObjectNode side = closed(sides.get(index), "side_index", "primary_owner_character_id", "counter_efficiency_raw", "counter_resistance_raw", "men_at_arms_entries");
            require(i32(side.get("side_index")) == index, "counter side order differs"); id(side.get("primary_owner_character_id")); same(side.get("primary_owner_character_id"), get(parents.get(index), "primary_participant_character_id"));
            fields64(side, "counter_efficiency_raw", "counter_resistance_raw");
            List<JsonNode> entries = rows(side.get("men_at_arms_entries")), expected = rows(get(parents.get(index), "men_at_arms_entries")); require(entries.size() == expected.size(), "counter MAA census differs");
            for (int j = 0; j < entries.size(); j++) {
                ObjectNode entry = closed(entries.get(j), "bucket_index", "regiment_id", "native_carmy_id", "current_fighting_raw", "status", "class_index", "stack_size_soldiers", "current_chunk_raw", "targets");
                i32(entry.get("bucket_index")); full(entry.get("regiment_id")); full(entry.get("native_carmy_id")); i64(entry.get("current_fighting_raw"));
                for (String key : List.of("bucket_index", "regiment_id", "native_carmy_id", "current_fighting_raw")) same(entry.get(key), expected.get(j).get(key));
                String entryStatus = text(entry.get("status")); List<JsonNode> targets = rows(entry.get("targets"));
                if (entryStatus.equals("absent")) { require(nil(entry.get("class_index")) && nil(entry.get("stack_size_soldiers")) && nil(entry.get("current_chunk_raw")) && targets.isEmpty(), "absent counter operands differ"); }
                else {
                    require(entryStatus.equals("available"), "counter entry unavailable"); int clazz = i32(entry.get("class_index")), stack = id(entry.get("stack_size_soldiers")).value(); long chunk = i64(entry.get("current_chunk_raw"));
                    require(clazz >= 0 && clazz < classes && chunk >= 0 && chunk == Math.floorDiv(i64(expected.get(j).get("current_fighting_raw")), stack), "counter native chunk/class differs");
                    require(targets.size() <= 4096, "counter target bound exceeded");
                    for (JsonNode target : targets) { ObjectNode t = closed(target, "class_index", "effectiveness_raw"); int c = i32(t.get("class_index")); require(c >= 0 && c < classes, "counter target class differs"); i64(t.get("effectiveness_raw")); }
                }
            }
        }
        for (int index = 0; index < 2; index++) {
            ObjectNode context = closed(contexts.get(index), "countered_side_index", "countering_side_index", "countered_primary_owner_character_id", "countering_primary_owner_character_id", "context_scale_raw");
            require(i32(context.get("countered_side_index")) == index && i32(context.get("countering_side_index")) == 1 - index, "counter directional order differs");
            id(context.get("countered_primary_owner_character_id")); id(context.get("countering_primary_owner_character_id"));
            same(context.get("countered_primary_owner_character_id"), sides.get(index).get("primary_owner_character_id"));
            same(context.get("countering_primary_owner_character_id"), sides.get(1 - index).get("primary_owner_character_id")); require(i64(context.get("context_scale_raw")) >= 0, "negative counter context scale");
        }
    }
    private static BigInteger uint(JsonNode node, int bits) { return range(node, BigInteger.ZERO, BigInteger.ONE.shiftLeft(bits).subtract(BigInteger.ONE)); }
    private static void event(JsonNode raw) {
        ObjectNode event = closed(raw, "clock_identity", "sequence", "thread_id"); uint(event.get("clock_identity"), 64); uint(event.get("sequence"), 64); if (!nil(event.get("thread_id"))) uint(event.get("thread_id"), 32);
    }
    private static void preceding(JsonNode raw, int combat) {
        if (nil(raw)) return;
        ObjectNode n = closed(raw, "schema", "configured", "installed", "request_filtered", "install_failure_flags", "latest_record_sequence", "overwritten_records", "full_entry", "records");
        equal(n.get("schema"), "xar.ck3.entry-preceding-capture-12004-v1"); bool(n.get("configured")); bool(n.get("installed")); yes(n.get("request_filtered")); no(n.get("full_entry")); uint(n.get("install_failure_flags"), 32);
        BigInteger latest = uint(n.get("latest_record_sequence"), 64); uint(n.get("overwritten_records"), 64); List<JsonNode> records = rows(n.get("records")); require(records.size() <= 128, "preceding journal bound exceeded");
        BigInteger previous = BigInteger.ZERO, expected = BigInteger.valueOf(Integer.toUnsignedLong(combat));
        for (JsonNode rawRecord : records) {
            ObjectNode r = closed(rawRecord, "record_sequence", "install_epoch", "offline_fixture", "original_returned", "identity_stable", "combat_identity", "combat_full_id_before", "combat_full_id_after", "caller_return_rva", "caller_return_slot", "original_begin", "original_completion", "raw_return_bits", "outer_invocation");
            BigInteger sequence = uint(r.get("record_sequence"), 64); require(sequence.compareTo(previous) > 0 && sequence.compareTo(latest) <= 0, "preceding journal ordinal differs"); previous = sequence; uint(r.get("install_epoch"), 64); bool(r.get("offline_fixture")); yes(r.get("original_returned"));
            BigInteger identity = uint(r.get("combat_identity"), 64); require(identity.signum() > 0, "preceding Combat pointer missing");
            for (String key : List.of("caller_return_rva", "caller_return_slot", "raw_return_bits")) uint(r.get(key), 64);
            BigInteger before = uint(r.get("combat_full_id_before"), 32); require(before.equals(expected), "preceding full Combat identity differs");
            BigInteger after = nil(r.get("combat_full_id_after")) ? null : uint(r.get("combat_full_id_after"), 32);
            require(after == null || !after.equals(new BigInteger("4294967295")), "invalid after identity must be null");
            require(bool(r.get("identity_stable")) == (after != null && before.equals(after)), "preceding identity stability differs");
            event(r.get("original_begin")); event(r.get("original_completion")); require(nil(r.get("outer_invocation")), "unobserved outer invocation must be null");
        }
    }
}
