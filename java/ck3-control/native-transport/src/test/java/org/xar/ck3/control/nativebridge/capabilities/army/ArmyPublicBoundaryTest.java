package org.xar.ck3.control.nativebridge.capabilities.army;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Complete public partition checks; this is software protocol coverage, never a Native/Game pass. */
final class ArmyPublicBoundaryTest {
    @Test void everyArmyCallRoundTripsAndRejectsExtraFields() {
        var methods = Arrays.stream(PublicMethod.values()).filter(m -> m.group() == PublicMethod.Group.ARMY).toList();
        assertEquals(47, methods.size());
        for (PublicMethod method : methods) {
            RawJson raw = json(sample(method)); var call = ArmyCallCodec.decode(method, raw);
            assertEquals(method, call.method()); assertEquals(call, ArmyCallCodec.decode(method, ArmyCallCodec.encode(call)));
            ObjectNode wrong = ArmyJson.parse(raw.bytes()).put("invented_field", true);
            assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(method, new RawJson(ArmyJson.bytes(wrong))));
            ObjectNode node = ArmyJson.parse(raw.bytes());
            if (node.has("expected_revision")) for (String value : new String[]{"true", "7.0", "9007199254740992"}) {
                ObjectNode changed = node.deepCopy(); changed.set("expected_revision", ArmyJson.parse(json("{\"n\":" + value + "}").bytes()).get("n"));
                assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(method, new RawJson(ArmyJson.bytes(changed))));
            }
        }
    }
    @Test void absenceAndNullRemainDistinctAndCunitZeroRemainsValid() {
        var m = PublicMethod.QUERY_ARMY_STRENGTHS;
        var absent = ArmyCallCodec.decode(m, json("{\"army_ids\":[0]}"));
        var nullable = ArmyCallCodec.decode(m, json("{\"army_ids\":[0],\"expected_revision\":null}"));
        assertNotEquals(absent, nullable);
        assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(m, json("{\"army_ids\":[0,0]}")));
        assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(m, json("{\"army_ids\":[0],\"profile\":null}")));
    }
    private static RawJson json(String body) { return new RawJson(body.getBytes(StandardCharsets.UTF_8)); }
    private static String sample(PublicMethod m) {
        String fields = switch (m) {
            case WAR_STATE -> "";
            case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1 -> "\"war_id\":-2,\"recipient_character_id\":0";
            case SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1 -> "\"type_index\":0,\"action_id\":\"x\"";
            case COLLECT_DECLARABLE_WARS_RESULT_V1 -> "\"request_id\":\"q\"";
            case DECLARE_WAR, QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1, QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2 -> "\"declaration_id\":\"0-0--1\"";
            case MOVE_ARMY -> "\"army_id\":0,\"target_province_id\":2";
            case START_ASSAULT, STOP_ASSAULT -> "\"siege_id\":1";
            case DISBAND_ARMY, QUERY_ARMY_COMMANDER_CANDIDATES_V1 -> "\"army_id\":0";
            case ENFORCE_DEMANDS, QUERY_WAR_OCCUPATION_TARGETS_V1, QUERY_WAR_TERMINATION_OPTIONS, QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS, QUERY_WAR_TERMINATION_TERMS, QUERY_WAR_TERMINATION_EXIT_TERMS, SURRENDER_WAR, OFFER_WHITE_PEACE -> "\"war_id\":1";
            case QUERY_PLAYER_TRUCE_EXPIRY_V1 -> "\"toward_character_id\":1";
            case HIRE_MERCENARY_V1 -> "\"company_id\":0";
            case HIRE_HOLY_ORDER_V1 -> "\"holy_order_id\":0";
            case ASSIGN_ARMY_COMMANDER_V1 -> "\"army_id\":0,\"commander_character_id\":0";
            case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> "\"enabled\":false";
            case QUERY_ARMY_STRENGTHS -> "\"army_ids\":[0]";
            case QUERY_BATTLE_CONTROL_SNAPSHOT_V1 -> "\"subject_public_cunit_id\":0";
            case QUERY_BATTLE_TRANSITION_V1, QUERY_COMBAT_PHASE_EVENT_TRACE_V1 -> "\"combat_id\":2";
            case QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1 -> "\"selected_public_cunit_id\":0";
            case QUERY_BATTLE_TERMINAL_TRANSITION_V1 -> "\"prior_combat_id\":-2,\"subject_public_cunit_id\":0";
            case PREVIEW_ACTIVE_COMBAT_RETREAT_V1 -> "\"selected_public_cunit_id\":0,\"target_province_id\":2";
            case ORDER_ACTIVE_COMBAT_RETREAT_V1 -> "\"selected_public_cunit_id\":0,\"expected_combat_id\":2,\"expected_side_index\":0,\"expected_scope\":\"full_side\",\"target_province_id\":2,\"candidate_token\":\"" + "a".repeat(32) + "\"";
            case QUERY_COMBAT_SIMULATION_INPUTS, QUERY_COMBAT_SIMULATION_INPUTS_V3 -> "\"target_province_id\":2,\"attacker_entry_province_id\":1,\"attacker_army_ids\":[0],\"defender_army_ids\":[1]";
            case QUERY_WAR_ENTRY_ASSESSMENTS -> "\"target_province_ids\":[2]";
            case QUERY_CURRENT_BATTLE_KNIGHT_V1 -> "\"subject_public_cunit_id\":0,\"character_id\":1,\"regiment_id\":1,\"expected_played_character_id\":1,\"expected_war_id\":0,\"expected_native_carmy_id\":1,\"expected_combat_id\":1,\"expected_province_id\":1,\"expected_date_raw\":0,\"expected_native_revision\":7,\"expected_snapshot_id\":\"native:7\"";
            default -> "";
        };
        if (m != PublicMethod.WAR_STATE) fields += (fields.isEmpty() ? "" : ",") + "\"expected_revision\":7";
        return "{" + fields + "}";
    }
}
