package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleTerminalJson.*;

/** Full original terminal person/custody JSON boundary; no capture, death, callback or write is inferred. */
public final class BattleTerminalPersonCodec {
    private BattleTerminalPersonCodec() { }
    private static final String[] INJURIES = {"wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged", "one_eyed", "disfigured", "incapable"};
    private static final Set<String> PERSON_OPTIONAL = Set.of("death_record", "raw_numeric_inputs", "current_context_task_position_inputs",
            "context_branch_inputs", "current_prior_context_inputs", "current_stored_context_state", "current_context_source_inputs",
            "carrier_1c8_b70_direct", "following_2921a90", "following_2921a90_conditional", "following_2921a90_opinion",
            "following_2921a90_scope_weights", "following_2922680", "following_291ce01_government_gate", "following_291e3a0_local_titles",
            "following_291e3a0_first_title_vector", "following_291e3a0_captured_tail");
    private static final Set<String> CURRENT_EXTERNAL = Set.of("carrier_1c8_b70_direct", "following_2921a90", "following_2921a90_conditional",
            "following_2921a90_opinion", "following_2921a90_scope_weights", "following_2922680", "following_291ce01_government_gate",
            "following_291e3a0_local_titles", "following_291e3a0_first_title_vector", "following_291e3a0_captured_tail");

    /** Missing optional outer section and explicit null both yield NullNode; the outer caller retains key presence. */
    public static JsonNode normalizeCustody(JsonNode raw, String field, boolean allowCurrentPersonState) {
        if (nil(raw)) return NullNode.instance;
        ArrayNode rows = array(raw, field);
        ArrayNode result = StrictJson.object().arrayNode();
        for (int index = 0; index < rows.size(); index++) {
            String name = field + "[" + index + "]";
            ObjectNode row = extended(rows.get(index), name, Set.of("character_id", "status", "actual_jailer_character_id"),
                    allowCurrentPersonState ? Set.of("alive", "current_person_state") : Set.of("alive"));
            int actor = positive(row.get("character_id"), name + ".character_id");
            String status = text(row.get("status"), name + ".status");
            Long jailer = optionalInteger(row.get("actual_jailer_character_id"), name + ".actual_jailer_character_id", -1, Integer.MAX_VALUE);
            require(Set.of("observed", "none", "unavailable").contains(status), name + ": custody status");
            require(switch (status) {
                case "observed" -> jailer != null && jailer > 0;
                case "none" -> jailer != null && jailer == -1;
                case "unavailable" -> jailer == null;
                default -> false;
            }, name + ": custody evidence disagrees");
            if (row.has("alive")) optionalBool(row.get("alive"), name + ".alive");
            ObjectNode normalized = row.deepCopy();
            if (row.has("current_person_state")) {
                ObjectNode person = currentPerson(row.get("current_person_state"), name + ".current_person_state");
                for (String key : new String[] {"raw_numeric_inputs", "current_context_task_position_inputs", "context_branch_inputs",
                        "current_context_source_inputs"}) bindActor(person.get(key), "character_id", actor, name + "." + key, false);
                for (String key : new String[] {"current_prior_context_inputs", "current_stored_context_state"})
                    bindActor(person.get(key), "character_full_id", actor, name + "." + key, false);
                for (String key : CURRENT_EXTERNAL) bindActor(person.get(key), "character_id", actor, name + "." + key, true);
                normalized.set("current_person_state", person);
            }
            result.add(normalized);
        }
        return result;
    }
    private static void bindActor(JsonNode value, String key, int actor, String field, boolean nullableActor) {
        if (nil(value)) return;
        JsonNode id = value.get(key);
        if (nullableActor && nil(id)) return;
        require(integer(id, field, Integer.MIN_VALUE, Integer.MAX_VALUE) == actor, field + ": receiver CharacterID differs");
    }
    static ObjectNode currentPerson(JsonNode raw, String field) {
        ObjectNode row = extended(raw, field, Set.of("scope", "effective_prowess", "injury_traits"), PERSON_OPTIONAL);
        require(text(row.get("scope"), field + ".scope").equals("current_character"), field + ": current-character scope required");
        prowess(row.get("effective_prowess"), field + ".effective_prowess");
        injuries(row.get("injury_traits"), field + ".injury_traits");
        ObjectNode result = row.deepCopy();
        if (row.has("death_record")) death(row.get("death_record"), field + ".death_record");
        if (row.has("raw_numeric_inputs")) result.set("raw_numeric_inputs", BattleTerminalNumericCodec.normalize(row.get("raw_numeric_inputs"), field + ".raw_numeric_inputs"));
        if (row.has("context_branch_inputs")) result.set("context_branch_inputs", BattleTerminalContextCodec.branch(row.get("context_branch_inputs"), field + ".context_branch_inputs"));
        if (row.has("current_prior_context_inputs")) result.set("current_prior_context_inputs", BattleTerminalContextCodec.prior(row.get("current_prior_context_inputs"), field + ".current_prior_context_inputs"));
        if (row.has("current_stored_context_state")) result.set("current_stored_context_state", BattleTerminalContextCodec.stored(row.get("current_stored_context_state"), field + ".current_stored_context_state"));
        if (row.has("current_context_source_inputs")) result.set("current_context_source_inputs", BattleContextSourceCodec.normalize(row.get("current_context_source_inputs"), field + ".current_context_source_inputs"));
        if (row.has("current_context_task_position_inputs")) result.set("current_context_task_position_inputs", BattleTaskPositionContextCodec.normalize(row.get("current_context_task_position_inputs"), field + ".current_context_task_position_inputs"));
        for (String key : CURRENT_EXTERNAL) if (row.has(key)) result.set(key,
                BattlePersonExternalCodec.normalize(BattlePersonExternalCodec.Leaf.fromWire(key), row.get(key), field + "." + key));
        return result;
    }
    private static void prowess(JsonNode value, String field) {
        ObjectNode row = object(value, field, "status", "points", "unavailable_reason");
        Integer points = i32(row.get("points"), field + ".points");
        String status = text(row.get("status"), field + ".status");
        require(Set.of("available", "unavailable").contains(status), field + ": prowess status");
        boolean ready = status.equals("available");
        require(ready == (points != null), field + ": prowess points disagree");
        reason(row.get("unavailable_reason"), field + ".unavailable_reason", ready);
    }
    private static void injuries(JsonNode value, String field) {
        ObjectNode row = object(value, field, "status", "flags", "wounded_rank", "unavailable_reason", "wounded_rank_unavailable_reason");
        ObjectNode flags = object(row.get("flags"), field + ".flags", INJURIES);
        int observed = 0; int woundMatches = 0; int rank = 0; boolean woundObserved = true;
        for (int index = 0; index < INJURIES.length; index++) {
            Boolean flag = optionalBool(flags.get(INJURIES[index]), field + ".flags." + INJURIES[index]);
            if (flag != null) observed++;
            if (index < 3) {
                woundObserved &= flag != null;
                if (Boolean.TRUE.equals(flag)) { woundMatches++; rank = index + 1; }
            }
        }
        String expected = observed == 8 ? "available" : observed == 0 ? "unavailable" : "partial";
        require(text(row.get("status"), field + ".status").equals(expected), field + ": injury availability differs");
        reason(row.get("unavailable_reason"), field + ".unavailable_reason", observed == 8);
        Long actualRank = optionalInteger(row.get("wounded_rank"), field + ".wounded_rank", 0, 3);
        boolean rankObserved = woundObserved && woundMatches <= 1;
        require(rankObserved ? actualRank != null && actualRank == rank : actualRank == null, field + ": wounded rank differs");
        reason(row.get("wounded_rank_unavailable_reason"), field + ".wounded_rank_unavailable_reason", rankObserved);
    }
    private static void death(JsonNode value, String field) {
        ObjectNode row = extended(value, field, Set.of("status", "reason_key", "unavailable_reason"),
                Set.of("date_object_raw_u64", "killer_full_character_id_raw", "artifact_full_id_raw"));
        if (!nil(row.get("reason_key"))) text(row.get("reason_key"), field + ".reason_key");
        String status = text(row.get("status"), field + ".status");
        switch (status) {
            case "none" -> { require(nil(row.get("reason_key")), field + ": absent death key"); reason(row.get("unavailable_reason"), field, true); }
            case "available" -> reason(row.get("unavailable_reason"), field, true);
            case "unavailable" -> { require(nil(row.get("reason_key")), field + ": unavailable death key"); reason(row.get("unavailable_reason"), field, false); }
            default -> throw new IllegalArgumentException(field + ": death status");
        }
        if (row.has("date_object_raw_u64")) u64(row.get("date_object_raw_u64"), field + ".date_object_raw_u64");
        for (String key : new String[] {"killer_full_character_id_raw", "artifact_full_id_raw"}) if (row.has(key)) i32(row.get(key), field + "." + key);
    }
    public static JsonNode normalizePendingDeathQueue(JsonNode value) {
        if (nil(value)) return NullNode.instance;
        String field = "battle_terminal_transition.pending_death_queue";
        ObjectNode row = object(value, field, "status", "unavailable_reason", "source_state_pointer_present", "manager_owner_pointer_present",
                "execution_mode_raw", "data_pointer_present", "capacity_raw", "count_raw", "rows");
        observed(row, field);
        for (String key : new String[] {"source_state_pointer_present", "manager_owner_pointer_present", "data_pointer_present"}) optionalBool(row.get(key), field + "." + key);
        optionalInteger(row.get("execution_mode_raw"), field + ".execution_mode_raw", 0, 255);
        for (String key : new String[] {"capacity_raw", "count_raw"}) i32(row.get(key), field + "." + key);
        if (!nil(row.get("rows"))) {
            ArrayNode rows = array(row.get("rows"), field + ".rows");
            for (int index = 0; index < rows.size(); index++) {
                String name = field + ".rows[" + index + "]";
                ObjectNode current = object(rows.get(index), name, "status", "unavailable_reason", "row_index", "victim_pointer_present",
                        "victim_full_character_id_raw", "victim_death_data_pointer_present", "reason_pointer_present", "reason_key", "date_object_raw_u64",
                        "killer_pointer_present", "killer_full_character_id_raw", "artifact_pointer_present", "artifact_full_id_raw");
                observed(current, name);
                integer(current.get("row_index"), name + ".row_index", 0, Integer.MAX_VALUE);
                for (String key : new String[] {"victim_pointer_present", "victim_death_data_pointer_present", "reason_pointer_present", "killer_pointer_present", "artifact_pointer_present"}) optionalBool(current.get(key), name + "." + key);
                for (String key : new String[] {"victim_full_character_id_raw", "killer_full_character_id_raw", "artifact_full_id_raw"}) i32(current.get(key), name + "." + key);
                u64(current.get("date_object_raw_u64"), name + ".date_object_raw_u64");
                if (!nil(current.get("reason_key"))) text(current.get("reason_key"), name + ".reason_key");
            }
        }
        return row.deepCopy();
    }
    private static void observed(ObjectNode row, String field) {
        String status = text(row.get("status"), field + ".status");
        require(Set.of("available", "unavailable").contains(status), field + ": observed status");
        reason(row.get("unavailable_reason"), field + ".unavailable_reason", status.equals("available"));
    }
}
