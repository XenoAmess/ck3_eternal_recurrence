package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Read-only projection of the sole durable preview; it owns neither a second token cache nor a writer. */
public final class ArmyRetreatTokens {
    public static final String STAGE = "java_production_composition";
    private ArmyRetreatTokens() { }
    public static Optional<Obj> capabilityToken(ActiveRetreatState.State state) {
        if (state.preview().isEmpty() || state.pending().isPresent()) return Optional.empty(); Obj preview = state.preview().orElseThrow();
        if (!new OpportunityJson.Bool(true).equals(preview.get("action_ready"))) return Optional.empty();
        var p = parse(DriverJson.encode(preview)); var target = object(get(p, "target_preview")); var control = object(get(p, "battle_control_snapshot"));
        equal(get(p, "contract_stage"), STAGE); equal(get(p, "status"), "available"); equal(get(target, "status"), "available");
        String token = nonempty(get(target, "candidate_token")); require(token.matches("[A-Za-z0-9_-]{32,128}"), "exact original token syntax required");
        var result = empty().put("candidate_token", token).put("order_step", nonempty(get(target, "order_step"))).set("source_binding", get(p, "source_binding"));
        // Explicit ObjectNode type avoids bean or untyped-map projection at the dynamic capability boundary.
        var n = object(result); n.set("battle_control_snapshot", control); n.set("battle_binding", battleBinding(control)); n.set("target_province_id", get(p, "target_province_id"));
        var route = target.deepCopy(); route.remove(List.of("status", "unavailable_reason", "provenance", "candidate_token", "order_step")); n.set("route_preview", route);
        return Optional.of(DriverJson.object(bytes(n), DriverJson.MAX_NATIVE_BYTES));
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode battleBinding(com.fasterxml.jackson.databind.node.ObjectNode control) {
        var binding = empty(); for (String key : List.of("combat_id", "combat_province_id", "selected_public_cunit_id", "selected_native_carmy_id", "selected_owner_character_id", "side_index", "side_scope", "affected_public_cunit_ids_in_stored_order", "unaffected_same_side_public_cunit_ids_in_stored_order")) binding.set(key, get(control, key)); return binding;
    }
}
