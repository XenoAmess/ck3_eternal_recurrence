package org.xar.ck3.control.wave2.military.forecast;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.forecast.CurrentBattleConditionCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/** Unchanged actual control producer/adapter/runner fixtures, never a Java-derived golden. */
final class CurrentBattleConditionParityTest {
    private static final String PROGRAM = """
            import copy,hashlib,json,runpy
            sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
            pins={
              'src/xar_autoplayer/bridge/battle_control_contract.py':'2a5509214b8c0187bb0799a4fc10728d7ea7b7954a525af977d768de0528c3de',
              'src/xar_autoplayer/simulation/battle_current_adapter.py':'7860986a1e435b6e992b840e50072ae8106ed7f05c1787de99a5c57c80751155',
              'src/xar_autoplayer/simulation/battle_current_runner.py':'07c23795802ebb891a18c679432caf05064929c3a25d99227fe5348dbbe53e55',
              'src/xar_autoplayer/simulation/active_counter_current_basis.py':'aefb80f5fe4771063d9b0da2d0caf75470903488212d30b45ff0f300a41eedd1',
              'tests/unit/test_battle_current_condition.py':'18ba3867161b66632c72c370347fced9030e0d87091f0c0f1ea0b626dceece03'}
            def verify():
                for name,pin in pins.items():assert hashlib.sha256((root/'ck3_autonomous_player'/name).read_bytes()).hexdigest()==pin,name
            verify()
            from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
            from xar_autoplayer.simulation.battle_current_runner import run_frozen_main_tick,run_seeded_frozen_main_tick,next_roll_distribution
            from xar_autoplayer.simulation.active_counter_current_basis import project_current_counter_attack_raw
            from xar_autoplayer.simulation.combat_core import BackingComponent,DrawState,CommanderRollRequest
            module=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_battle_current_condition.py'))
            rows=[]
            for case in (1,2):
                for variant in ('base','backing','no-counter','no-loss','stale-resume','not-due','no-commander','caller-levy','seeded','maneuver'):
                    frame=module['_normalized_frame'](case)
                    resume=module['_normalized_roll_receipt'](frame)
                    backing={99:(BackingComponent(1,1),BackingComponent(4,4)),3:(BackingComponent(4,4),BackingComponent(1,1))} if variant=='backing' else None
                    adapter_levy={0:123456,1:98765} if variant=='caller-levy' else None
                    runner_levy={0:222222,1:111111} if variant=='caller-levy' else None
                    if variant=='no-counter':frame.pop('active_counter_inputs_v1',None)
                    if variant=='no-loss':frame.pop('current_loss_inputs_v1',None)
                    if variant=='stale-resume':resume['source']['snapshot_revision']+=1
                    if variant=='not-due':frame['roll_cadence_counter']=1
                    if variant=='no-commander':frame['attacker']['selected_commander_character_id']=-1
                    if variant=='maneuver':frame.update(phase='maneuver',phase_raw=0)
                    condition=adapt_current_battle_condition(frame,backing_components_by_regiment_id=backing,active_resume_inputs=resume,levy_damage_raw_by_side=adapter_levy)
                    result=run_seeded_frozen_main_tick(condition,seed_u64=2**64-1,trial_index=2**65+1,levy_damage_raw_by_side=runner_levy) if variant=='seeded' else run_frozen_main_tick(condition,draw_state=DrawState(7,19),levy_damage_raw_by_side=runner_levy)
                    try:counter_projection=project_current_counter_attack_raw(frame)
                    except ValueError:counter_projection=None
                    rows.append({'case':case,'variant':variant,'frame':frame,'resume':resume,'backing':[] if backing is None else [{'regiment_id':r,'components':[{'maximum_soldiers':c.maximum_soldiers,'current_soldiers':c.current_soldiers,'kind':c.kind} for c in values]} for r,values in backing.items()], 'adapter_levy':[] if adapter_levy is None else [{'side_index':s,'damage_raw':d} for s,d in adapter_levy.items()], 'runner_levy':[] if runner_levy is None else [{'side_index':s,'damage_raw':d} for s,d in runner_levy.items()], 'counter_projection':counter_projection,'expected':result})
            distributions=[]
            for enabled,lo,hi,previous,due in ((True,4,4,9,True),(True,8,-3,1,True),(True,0,2**40,3,True),(False,0,0,17,True),(True,0,8,-2,False)):
                distributions.append({'enabled':enabled,'lo':lo,'hi':hi,'previous':previous,'due':due,'expected':next_roll_distribution(CommanderRollRequest(enabled,lo,hi,previous),roll_due=due)})
            verify()
            print(json.dumps({'producer':'unchanged-actual-current-battle-modules','rows':rows,'distributions':distributions},separators=(',',':')))
            """;
    private static JsonNode captured;
    private static synchronized JsonNode corpus() throws Exception { if (captured == null) captured = ForecastOriginalOracle.call(PROGRAM, CombatJson.object()); return captured; }
    private static List<LevyDamage> levies(JsonNode rows) { List<LevyDamage> values = new ArrayList<>(); for (JsonNode row : rows) values.add(new LevyDamage(row.get("side_index").intValue(), row.get("damage_raw").bigIntegerValue())); return List.copyOf(values); }
    private static ObservedInputs supplied(JsonNode row) {
        List<RegimentBacking> backing = new ArrayList<>();
        for (JsonNode regiment : row.get("backing")) { List<CombatCore.BackingComponent> values = new ArrayList<>(); for (JsonNode component : regiment.get("components")) values.add(new CombatCore.BackingComponent(component.get("maximum_soldiers").bigIntegerValue(), component.get("current_soldiers").bigIntegerValue(), component.get("kind").intValue())); backing.add(new RegimentBacking(regiment.get("regiment_id").bigIntegerValue(), values)); }
        return new ObservedInputs(backing, Optional.of(ResumeInputs.decode(row.get("resume"))), levies(row.get("adapter_levy")));
    }
    @Test void fullActualCurrentAdapterAndRunnerMatchOriginalTwentyVariants() throws Exception {
        assertEquals(20, corpus().path("rows").size());
        for (JsonNode row : corpus().get("rows")) {
            Condition condition = adapt(row.get("frame"), supplied(row));
            FrozenCurrentBattleRunner.Result result = row.path("variant").textValue().equals("seeded")
                    ? FrozenCurrentBattleRunner.runSeeded(condition, new BigInteger("18446744073709551615"), BigInteger.ONE.shiftLeft(65).add(BigInteger.ONE), levies(row.get("runner_levy")))
                    : FrozenCurrentBattleRunner.run(condition, new CombatCore.DrawState(7, 19), levies(row.get("runner_levy")));
            assertArrayEquals(CombatJson.canonical(row.get("expected")), CombatJson.canonical(result.toJson()), row.path("case") + ":" + row.path("variant"));
            assertFalse(result.toJson().get("complete_transition").booleanValue()); assertFalse(result.toJson().get("actual_next_draw_claimed").booleanValue());
            assertEquals(condition.source().revision(), result.toRetreatTick().observedFrame().snapshotRevision());
            ObjectNode detached = condition.sourceSnapshot(); detached.removeAll(); assertTrue(condition.sourceSnapshot().has("attacker"));
            Condition reloaded = adapt(CombatJson.parse(CombatJson.canonical(row.get("frame"))), supplied(row));
            assertEquals(condition.missingInputs(), reloaded.missingInputs()); assertEquals(condition.source(), reloaded.source());
        }
    }
    @Test void moduloDistributionIsExactEvenWhenDrawSpaceIsSmallerThanSpan() throws Exception {
        for (JsonNode row : corpus().get("distributions")) {
            CombatCore.CommanderRollRequest request = new CombatCore.CommanderRollRequest(row.get("enabled").booleanValue(), row.get("lo").bigIntegerValue(), row.get("hi").bigIntegerValue(), row.get("previous").bigIntegerValue());
            assertArrayEquals(CombatJson.canonical(row.get("expected")), CombatJson.canonical(FrozenCurrentBattleRunner.nextRollDistribution(request, row.get("due").booleanValue()).toJson()));
        }
    }
    @Test void completeSharedCurrentCounterProjectorMatchesOriginalFilteredAttacksAndRetentions() throws Exception {
        for (JsonNode row : corpus().get("rows")) {
            if (row.get("counter_projection").isNull()) { assertThrows(IllegalArgumentException.class, () -> ActiveCurrentCounterProjector.project(row.get("frame"))); continue; }
            var result = ActiveCurrentCounterProjector.project(row.get("frame")); var actual = CombatJson.array(); var attacks = actual.addArray(); result.attacks().forEach(attacks::add); var retentions = actual.addArray(); for (List<BigInteger> values : result.retentions()) { var side = retentions.addArray(); values.forEach(side::add); }
            assertArrayEquals(CombatJson.canonical(row.get("counter_projection")), CombatJson.canonical(actual));
        }
    }
    @Test void publicZeroAndActualPrivateComponentDomainRemainSeparateAndTokensStayStrict() throws Exception {
        ObjectNode frame = corpus().get("rows").get(0).get("frame").deepCopy();
        for (String key : List.of("snapshot_revision", "observed_date_raw", "phase_raw", "roll_cadence_counter")) for (String raw : List.of("true", "5.0", "null")) {
            ObjectNode bad = frame.deepCopy(); bad.set(key, CombatJson.parse(raw.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> adapt(bad));
        }
        ObjectNode bad = frame.deepCopy(); ((ObjectNode) bad.path("attacker").path("levy_entries").get(0)).remove("hard_casualties_raw"); assertThrows(IllegalArgumentException.class, () -> adapt(bad));
        ObjectNode changed = frame.deepCopy(); ((ObjectNode) changed.path("attacker").path("levy_entries").get(0)).put("public_cunit_id", 0);
        assertEquals(0, adapt(changed).sides().getFirst().entries().getFirst().publicUnitId());
        ((ObjectNode) changed.path("attacker").path("levy_entries").get(0)).put("public_cunit_id", -1); assertThrows(IllegalArgumentException.class, () -> adapt(changed));
        assertThrows(IllegalArgumentException.class, () -> new ObservedInputs(List.of(new RegimentBacking(BigInteger.ONE, List.of()), new RegimentBacking(BigInteger.ONE, List.of())), Optional.empty(), List.of()));
    }
}
