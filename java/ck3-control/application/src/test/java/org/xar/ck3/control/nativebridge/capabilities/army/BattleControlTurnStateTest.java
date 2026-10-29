package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.military.BattleControlTurnState;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;

/** Real retained Python normalization -> new strict codec -> actual ordinary collector; source-shaped, not live. */
final class BattleControlTurnStateTest {
    @Test void originalProducerFeedsStrictCodecAndDirectCollector() throws Exception {
        ObjectNode frame = (ObjectNode) BattleOriginalOracle.fixture().get("parent");
        int subject = frame.get("subject_public_cunit_id").intValue(); BigInteger revision = frame.get("snapshot_revision").bigIntegerValue(); long date = frame.get("observed_date_raw").longValue();
        ObjectNode original = BattleOriginalOracle.normalizeControl(frame, subject, revision, date);
        Obj normalized = BattleResponseCodec.normalizeControl(ast(original), subject, revision, date);
        assertEquals(original, OpportunityJson.toNode(normalized));
        Obj state = BattleControlTurnState.collect(request(snapshot(original, true), List.of()));
        assertEquals(new OpportunityJson.Text("ready"), state.get("status"));
        assertEquals(normalized, ((OpportunityJson.Arr) state.get("full_frames")).items().getFirst());
    }
    @Test void malformedNestedStateCannotBecomeReadyEvidence() {
        ObjectNode raw = control(); ((ObjectNode) raw.get("attacker")).put("invented", 1);
        assertThrows(IllegalArgumentException.class, () -> normalize(raw));
        Obj state = BattleControlTurnState.collect(request(snapshot(raw, true), List.of()));
        assertEquals(new OpportunityJson.Text("query_required"), state.get("status"));
    }
    @Test void subjectLeavingCombatTrimsOnlyItsOldQueryAndNeverInventsWinner() {
        ObjectNode before = control(), current = snapshot(before, false);
        long date = before.get("observed_date_raw").longValue(); current.put("date_raw", date + 24); current.put("native_revision", before.get("snapshot_revision").bigIntegerValue().add(BigInteger.ONE));
        current.put("snapshot_id", "native:" + current.get("native_revision").asText());
        ObjectNode query = ArmyJson.empty(); query.put("command", "query-battle-control-snapshot-v1-0"); query.put("ok", true);
        ObjectNode out = query.putObject("result"); out.put("step", "query-battle-control-snapshot-v1-0"); out.put("accepted", true); out.put("status", "available");
        out.put("queried_snapshot_id", "native:" + before.get("snapshot_revision").asText()); out.put("queried_revision", 9); out.set("queried_native_revision", before.get("snapshot_revision")); out.set("snapshot_revision", before.get("snapshot_revision")); out.put("query_sequence", 1); out.set("battle_control_snapshot", before);
        ObjectNode advance = ArmyJson.empty(); advance.put("command", "life-advance"); advance.put("ok", true); ObjectNode result = advance.putObject("result"); result.put("step", "life-advance"); result.put("starting_date_raw", date); result.put("ending_date_raw", date + 24); result.put("elapsed_days", 1);
        Obj state = BattleControlTurnState.collect(request(current, List.of(ast(query), ast(advance))));
        assertEquals(new OpportunityJson.Text("transition_recognized"), state.get("status"));
        Obj transition = (Obj) ((OpportunityJson.Arr) state.get("transitions")).items().getFirst();
        assertEquals(new OpportunityJson.Text("left_combat"), transition.get("status")); assertNull(transition.get("winner"));
        assertEquals(List.of(ast(advance)), ((OpportunityJson.Arr) state.get("remaining_rows")).items());
    }
    @Test void dateAndAckAloneDoNotProveBattleProgress() {
        ObjectNode before = control(), after = before.deepCopy(); long date = before.get("observed_date_raw").longValue();
        after.put("observed_date_raw", date + 24); after.put("snapshot_revision", before.get("snapshot_revision").bigIntegerValue().add(BigInteger.ONE));
        ObjectNode advance = ArmyJson.empty(); advance.put("step", "life-advance"); advance.put("starting_date_raw", date); advance.put("ending_date_raw", date + 24); advance.put("elapsed_days", 1);
        assertEquals(new OpportunityJson.Text("invalid"), BattleControlTurnState.transition(ast(before), ast(after), ast(advance)).get("status"));
        after.put("phase_day", before.get("phase_day").intValue() + 1);
        assertEquals(new OpportunityJson.Text("same_combat_advanced"), BattleControlTurnState.transition(ast(before), ast(after), ast(advance)).get("status"));
    }
    @Test void fullSignedCombatAndPublicZeroHaveCanonicalRequestSpellings() {
        assertEquals(Integer.MIN_VALUE, BattleControlTurnState.parseTerminal("query-battle-terminal-transition-v1--2147483648-0-18446744073709551615").orElseThrow().combat());
        assertTrue(BattleControlTurnState.parseTerminal("query-battle-terminal-transition-v1--1-0-0").isEmpty());
        assertTrue(BattleControlTurnState.parseTerminal("query-battle-terminal-transition-v1-01-0-0").isEmpty());
        assertTrue(BattleControlTurnState.controlSubject("query-battle-control-snapshot-v1-00").isEmpty());
    }
    @Test void completeTerminalTopActuallyConsumesPersonBoundaryAndKeepsUint64() throws Exception {
        JsonNode people;
        try (var stream = getClass().getResourceAsStream("/battle-terminal-person-current-source-shaped.json")) {
            assertNotNull(stream, "source-shaped person fixture required"); people = new com.fasterxml.jackson.databind.ObjectMapper().readTree(stream);
        }
        ObjectNode frame = (ObjectNode) BattleAfterStateObservationTest.terminalWire(false, 1).get("battle_terminal_transition");
        frame.put("prior_combat_id", -1); frame.put("subject_public_cunit_id", -1); frame.put("battle_terminal_transition_ready", false);
        for (String key : List.of("prior", "removal", "subject", "successor")) frame.putNull(key);
        ObjectNode journal = (ObjectNode) frame.get("terminal_journal"); journal.put("oldest_available_sequence", 0); journal.put("latest_sequence", 0); journal.putNull("event_sequence"); journal.put("event_status", "not_observed"); frame.set("character_observations", people);
        Obj normalized = BattleTerminalCodec.normalizeTerminal(ast(frame), -1, -1, Optional.empty(), List.of(29829), frame.get("snapshot_revision").bigIntegerValue(), frame.get("observed_date_raw").longValue());
        assertEquals(new BigInteger("18446744073709551615"), OpportunityJson.toNode(normalized).at("/character_observations/0/current_person_state/death_record/date_object_raw_u64").bigIntegerValue());
        ((ObjectNode) people.at("/0/current_person_state/death_record")).put("date_object_raw_u64", true);
        assertThrows(IllegalArgumentException.class, () -> BattleTerminalCodec.normalizeTerminal(ast(frame), -1, -1, Optional.empty(), List.of(29829), frame.get("snapshot_revision").bigIntegerValue(), frame.get("observed_date_raw").longValue()));
    }
    private static ObjectNode control() { return (ObjectNode) BattleAfterStateObservationTest.control().get("battle_control_snapshot"); }
    private static Obj normalize(ObjectNode frame) { return BattleResponseCodec.normalizeControl(ast(frame), frame.get("subject_public_cunit_id").intValue(), frame.get("snapshot_revision").bigIntegerValue(), frame.get("observed_date_raw").longValue()); }
    private static Obj ast(ObjectNode n) { return ArmyJsonFreeze.freeze(n); }
    private static final class ArmyJsonFreeze { private ArmyJsonFreeze() { } static Obj freeze(ObjectNode n) { return org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(n), org.xar.ck3.control.application.action.RawJson.MAXIMUM_BYTES); } }
    private static ObjectNode snapshot(ObjectNode frame, boolean combat) {
        ObjectNode out = ArmyJson.empty(); out.put("paused", true); out.put("map_ready", true); out.put("revision", 9); out.set("native_revision", frame.get("snapshot_revision")); out.set("date_raw", frame.get("observed_date_raw")); out.put("snapshot_id", "native:" + frame.get("snapshot_revision").asText()); out.put("episode_run_id", "episode");
        out.putNull("active_event"); out.putNull("pending_character_interaction"); out.put("one_life_terminal", false); out.putArray("active_wars");
        ObjectNode actor = out.putObject("played_character"); actor.set("character_id", frame.get("selected_owner_character_id")); actor.put("alive", true);
        ObjectNode army = out.putArray("player_armies").addObject(); army.set("army_id", frame.get("subject_public_cunit_id")); army.set("owner_character_id", frame.get("selected_owner_character_id")); army.set("current_province_id", frame.get("province_id")); army.put("controllable", true); army.put("in_combat", combat); army.put("retreating", false); army.put("army_state", combat ? "combat" : "regular"); army.putNull("move_target_province_id"); army.putArray("route_province_ids");
        ObjectNode diagnostic = out.putObject("diagnostics"); diagnostic.put("bridge_pid", 42); diagnostic.put("connection_generation", 1);
        if (combat) { out.set("battle_control_snapshot_v1", frame); out.put("battle_control_snapshot_v1_status", "available"); out.set("battle_control_snapshot_v1_subject_army_id", frame.get("subject_public_cunit_id")); out.set("battle_control_snapshot_v1_queried_snapshot_id", out.get("snapshot_id")); out.put("battle_control_snapshot_v1_queried_revision", 9); out.put("battle_control_snapshot_v1_query_sequence", 1); }
        return out;
    }
    private static PlanningRequest request(ObjectNode raw, List<Obj> history) {
        Obj snapshot = ast(raw); BigInteger actor = raw.at("/played_character/character_id").bigIntegerValue();
        var identity = new ObservationIdentity("fixture-machine", new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor, raw.get("native_revision").bigIntegerValue(), raw.get("date_raw").bigIntegerValue()), raw.get("snapshot_id").asText(), raw.get("revision").bigIntegerValue(), "episode"), 1);
        Instant time = Instant.parse("2026-10-24T00:00:00Z"); var source = new G2Source("fixture-machine", time.toString(), "synthetic-exact4-source-shape", new ExactRef("fixture", 1, "1".repeat(64)));
        return new PlanningRequest(identity, source, "session", time.plusSeconds(60), new PlanningObservation(snapshot, history, Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
}
