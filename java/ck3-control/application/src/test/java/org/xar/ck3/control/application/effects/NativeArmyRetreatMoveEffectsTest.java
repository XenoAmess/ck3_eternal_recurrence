package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.effects.NativeArmyMoveEffects.*;

/** Executes the previous combat-rejection path and the distinct source-bound retreat projection. */
final class NativeArmyRetreatMoveEffectsTest {
    private static final int COMBAT = -2147483647;
    private static final String TOKEN = "a".repeat(32);
    private static ActiveRetreatProposal.Order order() {
        var source = new ActiveRetreatProposal.SourceFrame("native:10", BigInteger.TEN, BigInteger.TEN, BigInteger.valueOf(100), "episode-one", BigInteger.valueOf(5));
        var arguments = new BattleRetreatPolicy.RetreatOrder(0, BigInteger.TEN, COMBAT, 0, BattleRetreatPolicy.Scope.OWNER_SUBSET, 3, TOKEN);
        return new ActiveRetreatProposal.Order(source, 9, arguments, List.of(0), List.of(2), List.of(2, 3), new OpportunityJson.Obj(Map.of()));
    }
    private static ObjectNode before() {
        var body = StrictJson.object(); body.put("snapshot_id", "native:10").put("revision", 10).put("native_revision", 10).put("date_raw", 100)
                .put("episode_run_id", "episode-one").put("paused", true).put("map_ready", true);
        body.putObject("diagnostics").put("connection_generation", 5); body.putObject("played_character").put("character_id", 9).put("alive", true);
        var armies = body.putArray("player_armies");
        armies.addObject().put("army_id", 0).put("owner_character_id", 9).put("controllable", true).put("in_combat", true).put("retreating", false)
                .put("army_state", "combat").put("army_state_code", 2).put("current_province_id", 2).putNull("move_target_province_id").putArray("route_province_ids");
        armies.addObject().put("army_id", 2).put("owner_character_id", 8).put("controllable", false).put("in_combat", true).put("retreating", false)
                .put("army_state", "combat").put("army_state_code", 2).put("current_province_id", 2).putNull("move_target_province_id").putArray("route_province_ids");
        return body;
    }
    private static ObjectNode after() {
        var body = before(); body.put("snapshot_id", "native:11").put("revision", 11).put("native_revision", 11);
        var selected = (ObjectNode) body.withArray("player_armies").get(0); selected.put("in_combat", false).put("retreating", true)
                .put("army_state", "retreating").put("army_state_code", 6).put("move_target_province_id", 3);
        selected.putArray("route_province_ids").add(2).add(3); return body;
    }
    private static OpportunityJson.Obj preview() {
        var order = order(); var body = StrictJson.object(); body.put("status", "available").put("action_ready", true);
        body.set("source_binding", OpportunityJson.toNode(order.source().json()));
        body.put("selected_public_cunit_id", 0).put("selected_owner_character_id", 9).put("combat_id", COMBAT).put("combat_province_id", 2)
                .put("side_index", 0).put("side_scope", "owner_subset").put("target_province_id", 3);
        body.putArray("affected_public_cunit_ids_in_stored_order").add(0); body.putArray("unaffected_same_side_public_cunit_ids_in_stored_order").add(2);
        var control = body.putObject("battle_control_snapshot"); control.put("selected_public_cunit_id", 0).put("selected_owner_character_id", 9)
                .put("combat_id", COMBAT).put("combat_province_id", 2).put("side_index", 0).put("side_scope", "owner_subset").put("snapshot_revision", 10).put("observed_date_raw", 100);
        control.putObject("legality").put("legal_now", true);
        var target = body.putObject("target_preview"); target.put("status", "available").put("army_id", 0).put("origin_province_id", 2).put("target_province_id", 3).put("candidate_token", TOKEN);
        target.putArray("route_province_ids").add(2).add(3);
        return (OpportunityJson.Obj) OpportunityJson.parse(StrictJson.canonical(body));
    }
    @Test void publicZeroUsesDistinctRetreatBranchWhileOrdinaryCombatMoveStillFails() {
        var move = parse(new OperationKey("move-army-0-to-3")); assertEquals(0, move.armyId());
        assertThrows(IllegalArgumentException.class, () -> verify(move, before(), after()), "ordinary movement must keep rejecting combat/retreat");
        assertEquals(State.RETREATING, verifyRetreat(move, order(), preview(), before(), after()));
        assertThrows(IllegalArgumentException.class, () -> parse(new OperationKey("move-army--1-to-3")));
    }
    @Test void ackOrPartialAfterStateCannotProveExactRetreatScopeAndRoute() {
        var wrongTarget = after(); ((ObjectNode) wrongTarget.withArray("player_armies").get(0)).put("move_target_province_id", 4);
        assertEquals(State.NOT_OBSERVED, verifyRetreat(new Move(0, 3), order(), preview(), before(), wrongTarget));
        var wrongRoute = after(); ((ObjectNode) wrongRoute.withArray("player_armies").get(0)).putArray("route_province_ids").add(3);
        assertEquals(State.NOT_OBSERVED, verifyRetreat(new Move(0, 3), order(), preview(), before(), wrongRoute));
        var stillCombat = after(); ((ObjectNode) stillCombat.withArray("player_armies").get(0)).put("in_combat", true);
        assertEquals(State.NOT_OBSERVED, verifyRetreat(new Move(0, 3), order(), preview(), before(), stillCombat));
        var expandedScope = after(); ((ObjectNode) expandedScope.withArray("player_armies").get(1)).put("in_combat", false).put("retreating", true);
        assertEquals(State.NOT_OBSERVED, verifyRetreat(new Move(0, 3), order(), preview(), before(), expandedScope));
    }
    @Test void wrongOriginalOwnerSourceCombatAndBooleanIdentityAreRejected() {
        var wrongBefore = before(); ((ObjectNode) wrongBefore.withArray("player_armies").get(0)).put("owner_character_id", 8);
        assertThrows(IllegalArgumentException.class, () -> verifyRetreat(new Move(0, 3), order(), preview(), wrongBefore, after()));
        var wrongSource = before(); wrongSource.put("episode_run_id", "another-episode");
        assertThrows(IllegalArgumentException.class, () -> verifyRetreat(new Move(0, 3), order(), preview(), wrongSource, after()));
        var wrongPreview = EffectJson.object(preview()); wrongPreview.put("combat_id", COMBAT + 1);
        var invalidPreview = (OpportunityJson.Obj) OpportunityJson.parse(StrictJson.canonical(wrongPreview));
        assertThrows(IllegalArgumentException.class, () -> verifyRetreat(new Move(0, 3), order(), invalidPreview, before(), after()));
        var boolIdentity = after(); ((ObjectNode) boolIdentity.withArray("player_armies").get(0)).put("army_id", false);
        assertThrows(IllegalArgumentException.class, () -> verifyRetreat(new Move(0, 3), order(), preview(), before(), boolIdentity));
    }
}
