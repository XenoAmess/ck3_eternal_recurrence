package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Public Service shape after actual receipt/domain validation; mirrors come from the same normalized frame. */
public final class ArmyBattlePublicPresenter {
    private static final List<String> CONTROL = List.of("selected_public_cunit_id", "selected_native_carmy_id", "selected_owner_character_id", "combat_province_id", "side_index", "side_scope", "affected_public_cunit_ids_in_stored_order", "unaffected_same_side_public_cunit_ids_in_stored_order", "side_flags", "legality");
    private static final List<String> TRANSITION = List.of("combat_id", "province_id", "phase", "phase_raw", "phase_day", "winner_side", "winner_raw", "forced_winner_side", "forced_winner_raw", "finalized", "battle_result_id", "attacker_public_cunit_ids_in_stored_order", "defender_public_cunit_ids_in_stored_order", "battle_transition_ready");
    private static final List<String> TERMINAL = List.of("prior_combat_id", "subject_public_cunit_id", "terminal_journal", "prior", "removal", "subject", "successor", "battle_terminal_transition_ready", "unavailable_reason");
    private ArmyBattlePublicPresenter() { }
    public static RawJson encode(ArmyBattleReadValue observation, Obj originalNativeEnvelope, ArmyPublicSnapshot captured) {
        ObjectNode original = object(OpportunityJson.toNode(originalNativeEnvelope)).deepCopy(), frame = object(OpportunityJson.toNode(observation.normalized()));
        yes(get(original, "accepted")); require(positive(get(original, "query_sequence")).value().equals(observation.sequence()), "battle presenter changed its original sequence"); equal(get(original, "snapshot_revision"), captured.context().nativeRevision());
        if (original.has("backend_id")) text(get(original, "backend_id")); else original.put("backend_id", "native-headless");
        original.put("schema_version", 1); original.set("source", captured.source()); String nested; List<String> mirrors;
        switch (observation.kind()) {
            case CONTROL -> { nested = "battle_control_snapshot"; mirrors = CONTROL; original.put("scope", "exact-ongoing-battle").put("status", "available").put("battle_control_ready", true); original.set("subject_army_id", get(frame, "subject_public_cunit_id").deepCopy()); }
            case TRANSITION -> { nested = "battle_transition_snapshot"; mirrors = TRANSITION; original.put("scope", "exact-combat-lifecycle"); original.set("status", get(frame, "status").deepCopy()); }
            case TERMINAL -> { nested = "battle_terminal_transition"; mirrors = TERMINAL; original.put("scope", "journal-backed-battle-terminal-transition"); original.set("status", get(frame, "status").deepCopy()); }
            default -> throw new IllegalArgumentException("unknown actual battle public observation");
        }
        for (String field : mirrors) original.set(field, get(frame, field).deepCopy());
        if (observation.kind() == ArmyBattleReadValue.Kind.TRANSITION) for (String field : List.of("current_observation", "actual_geography_v1")) if (frame.has(field)) original.set(field, frame.get(field).deepCopy());
        if (observation.kind() == ArmyBattleReadValue.Kind.TERMINAL && frame.has("character_observations")) original.set("character_observations", frame.get("character_observations").deepCopy());
        original.set(nested, frame.deepCopy()); ObjectNode extensions = object(OpportunityJson.toNode(observation.extensions()));
        for (String field : names(extensions)) original.set(field, extensions.get(field).deepCopy());
        ObjectNode diagnostics = object(OpportunityJson.toNode(BattlePublicDiagnostics.project(observation.kind(), observation.normalized(), captured)));
        for (String field : names(diagnostics)) original.set(field, diagnostics.get(field).deepCopy());
        return ArmyPublicWire.encode(DriverJson.object(bytes(original), DriverJson.MAX_NATIVE_BYTES), captured.context());
    }
}
