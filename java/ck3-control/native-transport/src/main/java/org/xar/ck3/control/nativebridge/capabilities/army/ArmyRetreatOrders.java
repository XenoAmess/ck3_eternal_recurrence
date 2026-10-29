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

/** Validates actual public/ordinary orders against the single durable token view. */
public final class ArmyRetreatOrders {
    private ArmyRetreatOrders() { }
    public static ActiveRetreatProposal.Order order(ActiveRetreatState.State state, ArmyCalls.RetreatOrder input) {
        Obj preview = state.preview().orElseThrow(() -> new IllegalArgumentException("original durable retreat preview is absent"));
        Obj token = ArmyRetreatTokens.capabilityToken(state).orElseThrow(() -> new IllegalArgumentException("original available retreat token is absent"));
        var p = parse(DriverJson.encode(preview)); var target = object(get(p, "target_preview"));
        ActiveRetreatProposal.SourceFrame source = ActiveRetreatState.source(OpportunityJson.object(preview.get("source_binding"), "retreat preview source"));
        input.revision().requireCurrent(source.revision()); require(input.revision().value() instanceof Present<?>, "retreat order needs its original expected revision");
        require(i32(get(p, "selected_public_cunit_id")) == input.selected().value() && i32(get(p, "combat_id")) == input.combat().value()
                && i32(get(p, "side_index")) == input.sideIndex() && text(get(p, "side_scope")).equals(input.scope().name().toLowerCase(java.util.Locale.ROOT))
                && i32(get(p, "target_province_id")) == input.target().value() && OpportunityJson.text(token.get("candidate_token"), "token").equals(input.token()), "retreat order differs from the sole original preview binding");
        String expected = ArmyRetreatPreview.orderStep(input.selected(), source.revision(), input.combat(), input.sideIndex(), input.scope(), input.target(), input.token());
        equal(get(target, "order_step"), expected);
        var args = new BattleRetreatPolicy.RetreatOrder(input.selected().value(), source.revision(), input.combat().value(), input.sideIndex(),
                input.scope() == Scope.FULL_SIDE ? BattleRetreatPolicy.Scope.FULL_SIDE : BattleRetreatPolicy.Scope.OWNER_SUBSET, input.target().value(), input.token());
        Obj assessment = new Obj(java.util.Map.of("source", new OpportunityJson.Text("public_native_retreat"), "command_causation_verified", new OpportunityJson.Bool(false)));
        return new ActiveRetreatProposal.Order(source, i32(get(p, "selected_owner_character_id")), args,
                ids(get(p, "affected_public_cunit_ids_in_stored_order")), ids(get(p, "unaffected_same_side_public_cunit_ids_in_stored_order")), ids(get(target, "route_province_ids")), assessment);
    }
    public static void matches(ActiveRetreatState.State before, ActiveRetreatProposal.Order order) {
        var a = order.arguments(); var call = new ArmyCalls.RetreatOrder(new ArmyCalls.Revision(new Present<>(a.expectedRevision())), new PublicUnitId(a.selectedPublicCunitId()),
                new FullId(a.expectedCombatId()), a.expectedSideIndex(), a.expectedScope() == BattleRetreatPolicy.Scope.FULL_SIDE ? Scope.FULL_SIDE : Scope.OWNER_SUBSET,
                new PositiveId(a.targetProvinceId()), a.candidateToken());
        var actual = order(before, call); require(actual.source().equals(order.source()) && actual.selectedOwnerCharacterId() == order.selectedOwnerCharacterId()
                && actual.arguments().equals(order.arguments()) && actual.affectedInStoredOrder().equals(order.affectedInStoredOrder())
                && actual.unaffectedInStoredOrder().equals(order.unaffectedInStoredOrder()) && actual.routeProvinceIds().equals(order.routeProvinceIds()), "durable ordinary/public order changed original preview identity or exact route");
    }
    private static List<Integer> ids(com.fasterxml.jackson.databind.JsonNode value) { return array(value, node -> { int id = i32(node); require(id >= 0, "nonnegative public ID/positive route province required"); return id; }); }
}
