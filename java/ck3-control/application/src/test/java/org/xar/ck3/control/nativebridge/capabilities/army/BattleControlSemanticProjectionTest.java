package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.BattleControlSemanticProjection;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.military.ActiveCombatObservedComparison;
import org.xar.ck3.control.application.planning.military.BattleControlTurnState;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original Python normalization -> strict Java projection -> actual ordinary consumers. No live qualification. */
final class BattleControlSemanticProjectionTest {
    private static final BigInteger MAX = new BigInteger("18446744073709551615");
    /** Source-shaped projection DTO, not a Native receipt or authority. */
    private record Data(Kind kind, Obj normalized, BigInteger sequence, Obj extensions) implements ArmyBattleReadValue { }
    @Test void originalReadFeedsOrdinaryGateAndComparisonWithoutHistory() throws Exception {
        ObjectNode fixture = BattleOriginalOracle.fixture(), raw = (ObjectNode) fixture.get("parent");
        ObjectNode original = BattleOriginalOracle.normalizeControl(raw, raw.get("subject_public_cunit_id").intValue(),
                raw.get("snapshot_revision").bigIntegerValue(), raw.get("observed_date_raw").longValue());
        ObjectNode resume = BattleControlExtensionCodec.normalizeResume((ObjectNode) fixture.get("resume"), original);
        Obj normalized = normalize(original), snapshot = snapshot(original);
        Obj projected = BattleControlSemanticProjection.project(new Data(ArmyBattleReadValue.Kind.CONTROL,
                normalized, MAX, new Obj(Map.of("active_combat_resume_inputs_v1", ast(resume)))), snapshot);
        Obj published = merge(snapshot, projected);
        assertEquals(normalized, projected.get("battle_control_snapshot_v1"));
        assertEquals(new IntegerValue(MAX), projected.get("battle_control_snapshot_v1_query_sequence"));
        assertEquals(ast(resume), projected.get("active_combat_resume_inputs_v1"));
        assertEquals(projected, ast((ObjectNode) OpportunityJson.toNode(projected)));
        assertPublicRoundtrip(published);
        Obj state = BattleControlTurnState.collect(request(published));
        assertEquals(new Text("ready"), state.get("status"));
        assertEquals(List.of(normalized), ((Arr) state.get("full_frames")).items());
        Obj comparison = new ActiveCombatObservedComparison().observe(request(published)).orElseThrow();
        assertEquals(new Text("provisional_observed_comparison"), comparison.get("status"));
        assertEquals(Nil.INSTANCE, comparison.get("whole_battle_win_probability"));
    }
    @Test void freshPhaseReplacesOldResumeAndFinalizedReadReachesTerminalGate() {
        ObjectNode before = control(), after = before.deepCopy();
        after.put("snapshot_revision", before.get("snapshot_revision").bigIntegerValue().add(BigInteger.ONE));
        after.put("observed_date_raw", before.get("observed_date_raw").longValue() + 24);
        after.put("phase_day", before.get("phase_day").intValue() + 1);
        ((ObjectNode) after.get("legality")).put("elapsed_whole_days", before.at("/legality/elapsed_whole_days").longValue() + 1);
        Obj snapshot = snapshot(after), fresh = BattleControlSemanticProjection.project(data(after), snapshot);
        Obj published = merge(snapshot.with("active_combat_resume_inputs_v1", new Obj(Map.of("old", new Bool(true)))), fresh);
        assertEquals(Nil.INSTANCE, published.get("active_combat_resume_inputs_v1"));
        assertPublicRoundtrip(published);
        Obj state = BattleControlTurnState.collect(request(published));
        assertEquals(new Text("ready"), state.get("status"));
        assertEquals(List.of(normalize(after)), ((Arr) state.get("full_frames")).items());
        assertThrows(IllegalArgumentException.class, () -> BattleControlSemanticProjection.project(data(before), snapshot));
        after.put("finalized", true);
        Obj terminalSnapshot = snapshot(after);
        Obj terminalFields = BattleControlSemanticProjection.project(data(after), terminalSnapshot);
        Obj terminal = BattleControlTurnState.collect(request(merge(terminalSnapshot, terminalFields)));
        assertEquals(new Text("terminal_observed"), terminal.get("status"));
        assertEquals(new Text("none"), ((Obj) terminal.get("frame")).get("winner_side"));
        assertTrue(new ActiveCombatObservedComparison().observe(request(merge(terminalSnapshot, terminalFields))).isEmpty());
        Obj cleared = merge(terminalSnapshot, BattleControlSemanticProjection.unavailable());
        assertEquals(new Text("query_required"), BattleControlTurnState.collect(request(cleared)).get("status"));
        for (String field : BattleControlSemanticProjection.fields()) assertEquals(Nil.INSTANCE, cleared.get(field));
    }
    @Test void staleSubjectWrongTypeUnknownSidecarAndOutOfRangeSequenceAreRejected() {
        ObjectNode raw = control(); Obj snapshot = snapshot(raw); Data value = data(raw);
        ObjectNode absent = (ObjectNode) OpportunityJson.toNode(snapshot); absent.putArray("player_armies");
        assertThrows(IllegalArgumentException.class, () -> BattleControlSemanticProjection.project(value, ast(absent)));
        ObjectNode regular = (ObjectNode) OpportunityJson.toNode(snapshot);
        ((ObjectNode) regular.at("/player_armies/0")).put("in_combat", false).put("army_state", "regular");
        assertThrows(IllegalArgumentException.class, () -> BattleControlSemanticProjection.project(value, ast(regular)));
        assertThrows(IllegalArgumentException.class, () -> BattleControlSemanticProjection.project(value, snapshot.with("native_revision", new Bool(true))));
        for (BigInteger sequence : List.of(BigInteger.ZERO, BigInteger.ONE.shiftLeft(64)))
            assertThrows(IllegalArgumentException.class, () -> BattleControlSemanticProjection.project(new Data(value.kind(), value.normalized(), sequence, value.extensions()), snapshot));
        for (Obj extensions : List.of(new Obj(Map.of("unhandled", Nil.INSTANCE)), new Obj(Map.of("active_combat_resume_inputs_v1", Nil.INSTANCE))))
            assertThrows(IllegalArgumentException.class, () -> BattleControlSemanticProjection.project(new Data(value.kind(), value.normalized(), value.sequence(), extensions), snapshot));
        assertFalse(BattleControlSemanticProjection.supports(new Data(ArmyBattleReadValue.Kind.TERMINAL, value.normalized(), MAX, value.extensions())));
        assertFalse(BattleControlSemanticProjection.same(value, new Data(value.kind(), value.normalized(), MAX,
                new Obj(Map.of("active_combat_resume_inputs_v1", Nil.INSTANCE)))));
    }
    @Test void originalStateAndCodeOnlySubjectsReachTheActualOrdinaryConsumers() throws Exception {
        ObjectNode raw = control();
        ObjectNode stateOnly = (ObjectNode) OpportunityJson.toNode(snapshot(raw));
        ObjectNode stateArmy = (ObjectNode) stateOnly.at("/player_armies/0");
        stateArmy.remove("in_combat"); stateArmy.put("army_state", "CoMbAt");
        ObjectNode codeOnly = stateOnly.deepCopy();
        ObjectNode codeArmy = (ObjectNode) codeOnly.at("/player_armies/0");
        codeArmy.put("in_combat", false); codeArmy.remove("army_state"); codeArmy.put("army_state_code", 2);
        ObjectNode nullFlag = codeOnly.deepCopy();
        ObjectNode nullArmy = (ObjectNode) nullFlag.at("/player_armies/0");
        nullArmy.putNull("in_combat"); nullArmy.putNull("army_state");
        List<ObjectNode> variants = List.of(stateOnly, codeOnly, nullFlag);
        ObjectNode input = ArmyJson.empty();
        var originalArmies = input.putArray("armies");
        variants.forEach(value -> originalArmies.add(value.at("/player_armies/0")));
        ObjectNode original = originalActiveSubjects(input);
        assertEquals(variants.size(), original.get("active").size());
        for (int i = 0; i < variants.size(); i++) {
            assertTrue(original.get("active").get(i).isBoolean());
            assertTrue(original.get("active").get(i).booleanValue());
            Obj current = ast(variants.get(i));
            Obj projected = BattleControlSemanticProjection.project(data(raw), current);
            Obj published = merge(current, projected);
            assertEquals(normalize(raw), projected.get("battle_control_snapshot_v1"));
            assertEquals(BattleControlSemanticProjection.fields(), projected.members().keySet());
            assertPublicRoundtrip(published);
            assertEquals(new Text("ready"), BattleControlTurnState.collect(request(published)).get("status"));
            assertEquals(new Text("provisional_observed_comparison"),
                    new ActiveCombatObservedComparison().observe(request(published)).orElseThrow().get("status"));
        }
    }
    @Test void stateCodeCannotCoerceBooleanFloatOrInactiveSubjectIntoTheCache() throws Exception {
        ObjectNode raw = control();
        ObjectNode inactive = (ObjectNode) OpportunityJson.toNode(snapshot(raw));
        ObjectNode inactiveArmy = (ObjectNode) inactive.at("/player_armies/0");
        inactiveArmy.put("in_combat", false); inactiveArmy.remove("army_state"); inactiveArmy.put("army_state_code", 1);
        ObjectNode boolCode = inactive.deepCopy(); ((ObjectNode) boolCode.at("/player_armies/0")).put("army_state_code", true);
        ObjectNode floatCode = inactive.deepCopy(); ((ObjectNode) floatCode.at("/player_armies/0")).put("army_state_code", 2.0);
        ObjectNode input = ArmyJson.empty(); var originalArmies = input.putArray("armies");
        List<ObjectNode> variants = List.of(inactive, boolCode, floatCode);
        variants.forEach(value -> originalArmies.add(value.at("/player_armies/0")));
        ObjectNode original = originalActiveSubjects(input);
        assertEquals(variants.size(), original.get("active").size());
        for (int i = 0; i < variants.size(); i++) {
            assertTrue(original.get("active").get(i).isBoolean());
            assertFalse(original.get("active").get(i).booleanValue());
            Obj current = ast(variants.get(i));
            assertThrows(IllegalArgumentException.class, () -> BattleControlSemanticProjection.project(data(raw), current));
        }
    }
    /** AST-load the exact retained producer helper; no duplicate Python business implementation. */
    private static ObjectNode originalActiveSubjects(ObjectNode input) throws Exception {
        return BattleOriginalOracle.call("""
                import ast,hashlib,json,sys
                path=root/'ck3_autonomous_player'/'src'/'xar_autoplayer'/'bridge'/'native_driver.py'
                source=path.read_bytes()
                if len(source)!=1658471 or hashlib.sha256(source).hexdigest()!='eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603':
                    raise RuntimeError('original active-combat producer source unavailable or drifted')
                tree=ast.parse(source,filename=str(path))
                nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_army_in_active_combat']
                if len(nodes)!=1:
                    raise RuntimeError('one original active-combat producer helper required')
                scope={}
                exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope)
                value=json.load(sys.stdin)
                result={'active':[scope['_army_in_active_combat'](army) for army in value['armies']]}
                if path.read_bytes()!=source:
                    raise RuntimeError('original active-combat producer changed during replay')
                print(json.dumps(result,allow_nan=False))
                """, input);
    }
    private static Data data(ObjectNode raw) { return new Data(ArmyBattleReadValue.Kind.CONTROL, normalize(raw), MAX, new Obj(Map.of())); }
    private static ObjectNode control() { return (ObjectNode) BattleAfterStateObservationTest.control().get("battle_control_snapshot"); }
    private static Obj normalize(ObjectNode raw) { return BattleResponseCodec.normalizeControl(ast(raw), raw.get("subject_public_cunit_id").intValue(), raw.get("snapshot_revision").bigIntegerValue(), raw.get("observed_date_raw").longValue()); }
    private static Obj ast(ObjectNode raw) { return DriverJson.object(ArmyJson.bytes(raw), DriverJson.MAX_NATIVE_BYTES); }
    private static Obj merge(Obj left, Obj right) { var fields = new LinkedHashMap<>(left.members()); fields.putAll(right.members()); return new Obj(fields); }
    private static void assertPublicRoundtrip(Obj published) {
        RawJson numeric = RawJson.fullMaterial(DriverJson.encode(published));
        RawJson encoded = PublicSnapshotCodec.encodePlanningSnapshotData(numeric);
        Obj publicValue = DriverJson.object(encoded.bytes(), RawJson.MAXIMUM_BYTES);
        assertEquals(new Text(MAX.toString()), publicValue.get("battle_control_snapshot_v1_query_sequence"));
        Obj frame = (Obj) publicValue.get("battle_control_snapshot_v1");
        assertTrue(frame.get("snapshot_revision") instanceof Text);
        assertTrue(((Obj) frame.get("attacker")).get("stored_current_fighting_raw") instanceof Text);
        if (publicValue.get("active_combat_resume_inputs_v1") instanceof Obj resume)
            assertTrue(((Obj) resume.get("source")).get("snapshot_revision") instanceof Text);
        RawJson decoded = PublicSnapshotCodec.decodePlanningSnapshotData(encoded);
        assertEquals(published, DriverJson.object(decoded.bytes(), RawJson.MAXIMUM_BYTES));
        assertEquals(encoded, PublicSnapshotCodec.encodePlanningSnapshotData(decoded));
        var wrong = new LinkedHashMap<>(publicValue.members());
        wrong.put("battle_control_snapshot_v1_query_sequence", new IntegerValue(MAX));
        assertThrows(IllegalArgumentException.class, () -> PublicSnapshotCodec.decodePlanningSnapshotData(
                RawJson.fullMaterial(DriverJson.encode(new Obj(wrong)))));
    }
    private static Obj snapshot(ObjectNode frame) {
        ObjectNode out = ArmyJson.empty(); out.put("format_version", 1); out.put("speed", 1);
        out.put("paused", true); out.put("map_ready", true); out.put("revision", 9);
        out.set("native_revision", frame.get("snapshot_revision")); out.set("date_raw", frame.get("observed_date_raw"));
        out.put("snapshot_id", "native:" + frame.get("snapshot_revision").asText()); out.put("episode_run_id", "episode");
        out.set("episode_character_id", frame.get("selected_owner_character_id")); out.putNull("one_life_terminal_reason");
        out.putNull("active_event"); out.putNull("pending_character_interaction"); out.put("one_life_terminal", false); out.putArray("active_wars");
        out.putObject("played_character").set("character_id", frame.get("selected_owner_character_id"));
        ((ObjectNode) out.get("played_character")).put("alive", true);
        ObjectNode army = out.putArray("player_armies").addObject(); army.set("army_id", frame.get("subject_public_cunit_id"));
        army.set("owner_character_id", frame.get("selected_owner_character_id")); army.set("current_province_id", frame.get("province_id"));
        army.put("controllable", true); army.put("in_combat", true); army.put("retreating", false); army.put("army_state", "combat");
        army.putNull("move_target_province_id"); army.putArray("route_province_ids");
        out.putObject("diagnostics").put("bridge_pid", 42).put("connection_generation", 1); return ast(out);
    }
    private static PlanningRequest request(Obj snapshot) {
        BigInteger actor = OpportunityJson.integer(OpportunityJson.object(snapshot.get("played_character"), "played_character").get("character_id"), "actor");
        var identity = new ObservationIdentity("fixture-machine", new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor, OpportunityJson.integer(snapshot.get("native_revision"), "native_revision"), OpportunityJson.integer(snapshot.get("date_raw"), "date_raw")),
                        OpportunityJson.text(snapshot.get("snapshot_id"), "snapshot_id"), OpportunityJson.integer(snapshot.get("revision"), "revision"), "episode"), 1);
        Instant time = Instant.parse("2026-10-25T14:00:00Z");
        var source = new G2Source("fixture-machine", time.toString(), "source-shaped-projection-test", new ExactRef("fixture", 1, "1".repeat(64)));
        return new PlanningRequest(identity, source, "session", time.plusSeconds(60), new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
}
