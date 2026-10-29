package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleAfterStateObservation.*;

/** Synthetic original-wire-shape tests of the real decoders and new consumer, never live evidence. */
public final class BattleAfterStateObservationTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final BigInteger NATIVE = new BigInteger("9007199254740993");
    private static final int COMBAT = Integer.MIN_VALUE;
    private static final PublicUnitId SUBJECT = new PublicUnitId(0);
    private static final ExactRef REF = new ExactRef("synthetic-original-read", 2, "1".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-23T17:00:00Z");
    @Test void nativeAndPublicRevisionsStaySeparateWithHighFullCombatId() throws Exception {
        Result result = observe(transition(true), "post", 8, BigInteger.ONE);
        CurrentBattle current = assertInstanceOf(CurrentBattle.class, result);
        assertEquals(COMBAT, current.original().combat().value());
        var roundtrip = JSON.readTree(toJson(result).toString());
        assertEquals("8", roundtrip.get("post_public_revision").textValue());
        assertEquals(NATIVE.toString(), roundtrip.get("post_native_revision").textValue());
        assertFalse(result.dispatchAllowed()); assertFalse(result.commandCausationVerified());
        assertFalse(result.actualArrivalObserved()); assertFalse(result.warOutcomeVerified());
    }
    @Test void missingCombatNeedsJournalAndDoesNotInventWin() {
        Pending result = assertInstanceOf(Pending.class, observe(transition(false), "post", 8, BigInteger.ONE));
        assertEquals(Reason.REMOVAL_REQUIRES_JOURNAL, result.reason());
        assertFalse(toJson(result).has("winner")); assertFalse(result.replayAllowed());
    }
    @Test void reusedRequestStalePublicFrameAndReconnectStayPending() {
        assertEquals(Reason.NO_INDEPENDENT_POST, assertInstanceOf(Pending.class, observe(transition(true), "before", 8, BigInteger.ONE)).reason());
        assertEquals(Reason.NO_INDEPENDENT_POST, assertInstanceOf(Pending.class, observe(transition(true), "post", 7, BigInteger.ONE)).reason());
        assertEquals(Reason.FRAME_OR_AUTHORITY_DRIFT, assertInstanceOf(Pending.class, observe(transition(true), "post", 8, BigInteger.TWO)).reason());
    }
    @Test void noNormalResultRetainsNoWinnerAndActualRemovalIsSeparate() {
        TerminalBattle result = assertInstanceOf(TerminalBattle.class, terminalResult(terminalWire(true, 1), Optional.empty()));
        assertEquals(TerminalKind.NO_NORMAL_RESULT, result.kind());
        assertEquals(Winner.NONE, result.winner()); assertTrue(result.originalCombatRemoved());
        assertFalse(result.completeBattleConsequencesVerified()); assertFalse(result.replayAllowed());
    }
    @Test void unboundedCursorCannotHideAnAlreadyTruncatedRing() {
        assertEquals(Reason.JOURNAL_GAP, assertInstanceOf(Pending.class, terminalResult(terminalWire(false, 2), Optional.empty())).reason());
        assertInstanceOf(TerminalBattle.class, terminalResult(terminalWire(false, 2), Optional.of(new UInt64(BigInteger.ONE))));
    }
    @Test void originalGenerationAndJournalSuppressionAreRequired() {
        ObjectNode changed = terminalWire(false, 1);
        ((ObjectNode) changed.get("battle_terminal_transition").get("prior")).put("combat_id", COMBAT + 1);
        assertThrows(IllegalArgumentException.class, () -> terminalResult(changed, Optional.empty()));
        ObjectNode mismatch = terminalWire(false, 1);
        ((ObjectNode) mismatch.get("battle_terminal_transition").get("prior")).put("suppress_normal_result_envelopes", true);
        assertThrows(IllegalArgumentException.class, () -> terminalResult(mismatch, Optional.empty()));
    }
    @Test void rawIngressRejectsWrongTypesAndMissingActualFields() {
        for (String value : List.of("true", "8.0", "null")) {
            ObjectNode changed = transition(true);
            try { changed.set("snapshot_revision", JSON.readTree(value)); }
            catch (java.io.IOException impossible) { throw new AssertionError(impossible); }
            assertThrows(IllegalArgumentException.class, () -> observe(changed, "post", 8, BigInteger.ONE));
        }
        ObjectNode missing = transition(true);
        ((ObjectNode) missing.get("battle_transition_snapshot")).remove("winner_raw");
        assertThrows(IllegalArgumentException.class, () -> observe(missing, "post", 8, BigInteger.ONE));
    }
    private static Result observe(ObjectNode wire, String postId, long publicRevision, BigInteger generation) {
        return BattleAfterStateObservation.transition(receipt(control(), "before", 7, BigInteger.ONE), REF,
                receipt(wire, postId, publicRevision, generation), REF, SUBJECT);
    }
    private static Result terminalResult(ObjectNode wire, Optional<UInt64> after) {
        ((ObjectNode) wire.get("battle_terminal_transition").get("terminal_journal"))
                .set("requested_after_sequence", after.<com.fasterxml.jackson.databind.JsonNode>map(x -> JSON.getNodeFactory().numberNode(x.value())).orElse(JSON.getNodeFactory().nullNode()));
        ArmyRequests.Terminal request = new ArmyRequests.Terminal(Optional.of(new FullId(COMBAT)), Optional.of(SUBJECT), after, List.of());
        wire.put("step", ArmySteps.terminal(request));
        return BattleAfterStateObservation.terminal(receipt(control(), "before", 7, BigInteger.ONE), REF,
                receipt(wire, "post", 8, BigInteger.ONE), REF, SUBJECT, request);
    }
    private static PlanningReadReceipt receipt(ObjectNode raw, String id, long publicRevision, BigInteger generation) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), NATIVE, BigInteger.valueOf(53147376)), "snapshot-" + publicRevision, BigInteger.valueOf(publicRevision), "episode");
        var observed = new ObservationIdentity("fixture-machine", new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        var source = new G2Source("fixture-machine", NOW.toString(), "synthetic-exact4-wire-shape", REF);
        var operation = new OperationKey("query-battle");
        var request = new PlanningReadRequest(observed, source, "session", operation, new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(60));
        var evidence = new GuardEvidence(observed, source, "session", generation, operation, REF, REF, "authority", NOW, NOW.plusSeconds(60));
        var guard = new PlanningReadGuard(evidence, true, true, true, "2".repeat(64));
        RawJson result = new RawJson(raw.toString().getBytes(StandardCharsets.UTF_8));
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(result), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), "{}".getBytes(StandardCharsets.UTF_8));
        return new PlanningReadReceipt(request, "synthetic-query", id, guard, guard, ack);
    }
    private static ObjectNode envelope(String step) {
        ObjectNode out = JSON.createObjectNode(); out.put("step", step); out.put("accepted", true);
        out.put("snapshot_revision", NATIVE); out.put("query_sequence", NATIVE); return out;
    }
    public static ObjectNode control() {
        ObjectNode root = envelope("query-battle-control-snapshot-v1-0"); ObjectNode c = root.putObject("battle_control_snapshot");
        c.put("schema_version",1); c.put("contract_stage","production_exact_ongoing_combat"); c.put("status","available"); c.put("battle_control_ready",true);
        c.put("snapshot_revision",NATIVE); c.put("observed_date_raw",53147376); c.put("subject_public_cunit_id",0); c.put("subject_native_carmy_id",10);
        c.put("combat_id",COMBAT); c.put("province_id",2619); c.put("selected_public_cunit_id",0); c.put("selected_native_carmy_id",10);
        c.put("selected_owner_character_id",29829); c.put("combat_province_id",2619); c.put("side_index",0); c.put("side_scope","full_side");
        c.putArray("affected_public_cunit_ids_in_stored_order").add(0); c.putArray("unaffected_same_side_public_cunit_ids_in_stored_order");
        ObjectNode flags = c.putObject("side_flags"); flags.put("disallow_retreat",false); flags.put("allow_early_retreat",false); flags.put("skip_pursuit",false);
        ObjectNode legal = c.putObject("legality"); legal.put("status","available"); legal.put("native_boolean",true); legal.put("phase_raw",1); legal.put("phase","main");
        legal.put("retreat_elapsed_baseline_date_raw",53146896); legal.put("elapsed_whole_days",20); legal.put("minimum_elapsed_whole_days_exclusive",14);
        legal.put("landless_gate_allows_retreat",true); legal.put("legal_now",true); legal.putArray("reason_codes_in_native_order"); legal.putArray("native_reason_keys_in_native_order"); legal.put("earliest_day_gate_date_raw",0x029C55C0L+((53146896L-0x029C55C0L)/24+15)*24);
        lifecycle(c, true); c.remove("battle_transition_ready"); c.put("base_combat_width",100); c.put("final_combat_width",100); c.put("roll_cadence_counter",0); c.put("base_advantage_raw",0); c.put("resolved_advantage_raw",0);
        c.set("attacker",side(0,0,10,29829)); c.set("defender",side(1,20,11,2)); return root;
    }
    private static ObjectNode side(int side,int unit,int army,int owner) {
        ObjectNode s=JSON.createObjectNode(); s.put("side_index",side); s.put("role",side==0?"attacker":"defender"); s.put("primary_participant_character_id",owner);
        s.putNull("selected_commander_character_id"); s.put("current_roll_points",0);
        ObjectNode a=s.putArray("ordered_armies").addObject(); a.put("native_carmy_id",army); a.put("public_cunit_id",unit); a.put("owner_character_id",owner); a.put("combat_backlink_id",COMBAT);
        s.putArray("levy_entries"); s.putArray("men_at_arms_entries"); s.putArray("participant_hard_ledger");
        for(String key:List.of("stored_current_fighting_raw","stored_levy_current_fighting_raw","derived_current_fighting_raw","derived_soft_casualties_raw","derived_main_fighting_entry_hard_casualties_raw","non_main_start_minus_current_minus_soft_raw","participant_hard_total_raw"))s.put(key,0);
        s.put("stored_current_matches_derived",true); s.put("stored_levy_current_matches_derived",true); s.put("side_strength_raw",1); s.put("side_strength_scale",100000); return s;
    }
    public static ObjectNode transition(boolean available) {
        ObjectNode root=envelope("query-battle-transition-v1-"+COMBAT); ObjectNode t=root.putObject("battle_transition_snapshot");
        t.put("schema_version",1); t.put("contract_stage","production_exact_combat_lifecycle"); t.put("status",available?"available":"combat_not_found");
        t.put("snapshot_revision",NATIVE); t.put("observed_date_raw",53147376); t.put("combat_id",COMBAT); lifecycle(t,available);
        var a=t.putArray("attacker_public_cunit_ids_in_stored_order"); var d=t.putArray("defender_public_cunit_ids_in_stored_order"); if(available){a.add(0);d.add(20);} return root;
    }
    private static void lifecycle(ObjectNode t,boolean available) {
        t.put("battle_transition_ready",true);
        if(available){ t.put("province_id",2619); t.put("phase","main"); t.put("phase_raw",1); t.put("phase_day",2); t.put("winner_side","none"); t.put("winner_raw",-1); t.put("forced_winner_side","none"); t.put("forced_winner_raw",-1); t.put("finalized",false); t.putNull("battle_result_id"); }
        else for(String key:List.of("province_id","phase","phase_raw","phase_day","winner_side","winner_raw","forced_winner_side","forced_winner_raw","finalized","battle_result_id"))t.putNull(key);
    }
    public static ObjectNode terminalWire(boolean suppressed,int oldest) {
        ObjectNode root=envelope("terminal"); ObjectNode t=root.putObject("battle_terminal_transition"); t.put("schema_version",1); t.put("contract_stage","production_exact_battle_terminal_transition"); t.put("status","available"); t.put("battle_terminal_transition_ready",true); t.putNull("unavailable_reason");
        t.put("snapshot_revision",NATIVE); t.put("observed_date_raw",53147376); t.put("prior_combat_id",COMBAT); t.put("subject_public_cunit_id",0);
        ObjectNode j=t.putObject("terminal_journal"); j.putNull("requested_after_sequence"); j.put("oldest_available_sequence",oldest); j.put("latest_sequence",3); j.put("event_sequence",3); j.put("event_status","observed");
        ObjectNode p=t.putObject("prior"); p.put("combat_id",COMBAT); p.put("terminal_kind",suppressed?"no_normal_result":"normal_result"); p.put("terminal_date_raw",53147376); p.put("suppress_normal_result_envelopes",suppressed); p.put("phase_raw",3); p.put("phase_day",0); p.put("winner_raw",suppressed?-1:1); p.put("finalized_before",false); p.put("daily_guard_raw",0); p.put("province_id",2619); p.putNull("battle_result_id"); p.putNull("wipe_raw"); p.put("attacker_primary_participant_character_id",29829); p.put("defender_primary_participant_character_id",2); p.putArray("attacker_public_cunit_ids_in_stored_order").add(0); p.putArray("defender_public_cunit_ids_in_stored_order").add(20);
        ObjectNode w=p.putObject("battle_warscore"); w.put("status","not_recorded_by_native"); for(String key:List.of("war_id","war_battle_row_index","value_raw_q100000","winner_is_war_attacker","combat_side0_is_war_attacker","attacker_relative_delta_raw_q100000"))w.putNull(key);
        ObjectNode r=t.putObject("removal"); r.put("prior_combat_strictly_resolves",false); r.put("prior_province_strictly_resolves",true); r.put("prior_province_contains_prior_combat_id",false); r.put("result_strictly_resolves",false); r.putNull("result_relevant_player_count");
        ObjectNode s=t.putObject("subject"); s.put("exists",true); s.put("current_province_id",2619); s.put("native_carmy_id",10); s.putNull("combat_backlink_id"); s.putNull("active_combat_id"); s.put("movement_or_retreat_state_raw",0); s.putNull("move_target_province_id"); s.putArray("route_province_ids_in_stored_order"); s.put("ai_membership_status","none"); s.putNull("coordinator_id"); s.putNull("unit_stack_stored_index"); s.putNull("subunit_stored_index"); s.put("blocked_by_active_combat",false);
        ObjectNode x=t.putObject("successor"); x.put("state","no_successor"); x.putArray("matching_combat_ids_in_native_order"); x.putNull("selected_successor_combat_id"); x.putArray("participant_overlap_public_cunit_ids_in_prior_order"); return root;
    }
}
