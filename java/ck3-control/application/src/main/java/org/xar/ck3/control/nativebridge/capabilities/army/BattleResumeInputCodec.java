package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleControlExtensionCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** V1 only preserves unavailable same-frame resume operands; there is no ready branch. */
final class BattleResumeInputCodec {
    private BattleResumeInputCodec() { }
    private static final Set<String> OBSERVED = Set.of("phase", "phase_day", "elapsed_whole_days", "roll_cadence_counter",
            "final_combat_width", "side_0_current_roll_points", "side_1_current_roll_points",
            "side_0_selected_commander_character_id", "side_1_selected_commander_character_id",
            "side_0_selected_commander_next_roll_bounds", "side_1_selected_commander_next_roll_bounds",
            "side_0_ordered_public_cunit_ids", "side_1_ordered_public_cunit_ids", "side_0_entry_count", "side_1_entry_count");
    static ObjectNode normalize(ObjectNode value, ObjectNode parent) {
        require(parent != null, "normalized BattleControl parent required");
        ObjectNode n = closed(value, "schema_version", "status", "input_observation_ready", "unavailable_reason", "missing_required_domains", "source", "observed");
        eqInt(n.get("schema_version"), 1); equal(n.get("status"), "unavailable"); no(n.get("input_observation_ready"));
        equal(n.get("unavailable_reason"), "same_frame_resume_operands_incomplete");
        List<String> missing = array(n.get("missing_required_domains"), ArmyJson::nonempty);
        require(!missing.isEmpty() && new HashSet<>(missing).size() == missing.size(), "resume missing domains differ");
        ObjectNode source = closed(n.get("source"), "snapshot_revision", "observed_date_raw", "subject_public_cunit_id", "subject_native_carmy_id", "combat_id", "province_id");
        positive(source.get("snapshot_revision")); i64(source.get("observed_date_raw")); unit(source.get("subject_public_cunit_id"));
        id(source.get("subject_native_carmy_id")); full(source.get("combat_id")); id(source.get("province_id"));
        for (String key : names(source)) same(source.get(key), get(parent, key));
        ObjectNode observed = object(n.get("observed"));
        optionalKeys(observed, OBSERVED, Set.of("roll_cadence_interval", "current_pursuit_inputs_v1", "current_finalizer_manager_inputs_v1",
                "current_warscore_caps_v1", "current_phase_transition_inputs_v1", "battle_side_mapping", "active_counter_inputs_v1"));
        same(observed.get("phase"), get(parent, "phase"));
        ObjectNode attacker = object(get(parent, "attacker")), defender = object(get(parent, "defender"));
        for (String key : List.of("phase_day", "roll_cadence_counter", "final_combat_width")) { i32(observed.get(key)); same(observed.get(key), get(parent, key)); }
        i32(observed.get("elapsed_whole_days")); same(observed.get("elapsed_whole_days"), get(object(get(parent, "legality")), "elapsed_whole_days"));
        boolean bothBounds = true;
        for (int index = 0; index < 2; index++) {
            ObjectNode side = index == 0 ? attacker : defender; String prefix = "side_" + index + "_";
            i32(observed.get(prefix + "current_roll_points")); same(observed.get(prefix + "current_roll_points"), get(side, "current_roll_points"));
            i32(observed.get(prefix + "entry_count")); eqInt(observed.get(prefix + "entry_count"), (long) rows(get(side, "levy_entries")).size() + rows(get(side, "men_at_arms_entries")).size());
            JsonNode selected = observed.get(prefix + "selected_commander_character_id"); if (!nil(selected)) id(selected);
            same(selected, get(side, "selected_commander_character_id"));
            List<ArmyTypes.PublicUnitId> units = units(observed.get(prefix + "ordered_public_cunit_ids"));
            require(units.equals(array(get(side, "ordered_armies"), army -> unit(army.get("public_cunit_id")))), "resume Army native order differs");
            ObjectNode bounds = closed(observed.get(prefix + "selected_commander_next_roll_bounds"), "status", "effective_min_roll", "effective_max_roll", "unavailable_reason");
            String status = text(bounds.get("status"));
            if (status.equals("available")) { fields32(bounds, "effective_min_roll", "effective_max_roll"); require(nil(bounds.get("unavailable_reason")), "available roll bounds have reason"); }
            else { bothBounds = false; require(status.equals("unavailable") && nil(bounds.get("effective_min_roll")) && nil(bounds.get("effective_max_roll")), "unavailable roll bounds have endpoints"); nonempty(bounds.get("unavailable_reason")); }
        }
        require(missing.contains("selected_commander_next_roll_bounds") != bothBounds, "resume roll-bound completeness differs");
        int combat = full(get(parent, "combat_id")).value();
        if (observed.has("roll_cadence_interval")) { nullableI32(observed.get("roll_cadence_interval")); sameOptional(observed.get("roll_cadence_interval"), parent.get("roll_cadence_interval")); }
        if (observed.has("current_phase_transition_inputs_v1")) { phase(observed.get("current_phase_transition_inputs_v1")); sameOptional(observed.get("current_phase_transition_inputs_v1"), parent.get("current_phase_transition_inputs_v1")); }
        if (observed.has("current_finalizer_manager_inputs_v1")) { manager(observed.get("current_finalizer_manager_inputs_v1"), combat); sameOptional(observed.get("current_finalizer_manager_inputs_v1"), parent.get("current_finalizer_manager_inputs_v1")); }
        if (observed.has("current_warscore_caps_v1")) { warscore(observed.get("current_warscore_caps_v1"), combat); sameOptional(observed.get("current_warscore_caps_v1"), parent.get("current_warscore_caps_v1")); }
        if (observed.has("current_pursuit_inputs_v1")) { pursuit(observed.get("current_pursuit_inputs_v1"), combat); sameOptional(observed.get("current_pursuit_inputs_v1"), parent.get("current_pursuit_inputs_v1")); }
        boolean hasMapping = observed.has("battle_side_mapping");
        require(hasMapping != missing.contains("active_coalition_side_mapping"), "resume coalition completeness differs");
        if (hasMapping) mapping(observed.get("battle_side_mapping"), parent, attacker, defender);
        if (observed.has("active_counter_inputs_v1")) {
            JsonNode counter = parent.get("active_counter_inputs_v1"); require(counter != null && counter.isObject(), "resume lacks parent counter census"); same(observed.get("active_counter_inputs_v1"), counter);
        }
        require(missing.contains("active_regiment_counter_class_stack_context"), "next-day counter domain is not complete");
        return n.deepCopy();
    }
    private static void sameOptional(JsonNode observed, JsonNode parent) { if (parent == null) require(nil(observed), "missing parent optional differs"); else same(observed, parent); }
    private static void mapping(JsonNode raw, ObjectNode parent, ObjectNode attacker, ObjectNode defender) {
        ObjectNode n = closed(raw, "status", "subject_side_index", "opposing_side_index", "subject_owner_character_id", "side_scope",
                "same_side_public_cunit_ids_in_stored_order", "opposing_side_public_cunit_ids_in_stored_order",
                "affected_public_cunit_ids_in_stored_order", "unaffected_same_side_public_cunit_ids_in_stored_order");
        equal(n.get("status"), "available"); int side = i32(n.get("subject_side_index"));
        require(side == i32(get(parent, "side_index")) && i32(n.get("opposing_side_index")) == 1 - side, "resume subject side differs");
        id(n.get("subject_owner_character_id")); same(n.get("subject_owner_character_id"), get(parent, "selected_owner_character_id")); same(n.get("side_scope"), get(parent, "side_scope"));
        ObjectNode own = side == 0 ? attacker : defender, opposing = side == 0 ? defender : attacker;
        require(units(n.get("same_side_public_cunit_ids_in_stored_order")).equals(array(get(own, "ordered_armies"), army -> unit(army.get("public_cunit_id")))), "resume same-side Army order differs");
        require(units(n.get("opposing_side_public_cunit_ids_in_stored_order")).equals(array(get(opposing, "ordered_armies"), army -> unit(army.get("public_cunit_id")))), "resume opposing Army order differs");
        for (String key : List.of("affected_public_cunit_ids_in_stored_order", "unaffected_same_side_public_cunit_ids_in_stored_order")) { units(n.get(key)); same(n.get(key), get(parent, key)); }
    }
}
