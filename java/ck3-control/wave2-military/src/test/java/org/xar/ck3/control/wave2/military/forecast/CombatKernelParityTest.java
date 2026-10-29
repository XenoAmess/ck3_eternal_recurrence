package org.xar.ck3.control.wave2.military.forecast;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatCore.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatInputs.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.n;
import static org.xar.ck3.control.wave2.military.forecast.ResearchEnvelope.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import org.junit.jupiter.api.Test;

/** Differential tests invoke the retained original production modules, never a Java-derived golden. */
final class CombatKernelParityTest {
    private static void assertJsonEquals(JsonNode expected, JsonNode actual) {
        assertArrayEquals(CombatJson.canonical(expected), CombatJson.canonical(actual));
    }
    private static final List<String> LIVE_FIXTURES = List.of(
            "live_rev4_vs_357.json", "live_rev4_vs_33554657.json", "live_rev4_vs_combined.json",
            "live_rev4_player_attacks_357.json", "live_rev4_player_attacks_combined.json");

    private static Path fixturePath(String name) {
        String root = System.getProperty("xar.repository.root");
        assertNotNull(root, "xar.repository.root is required for original production differential");
        return Path.of(root).resolve("ck3_autonomous_player/tests/fixtures/combat").resolve(name);
    }
    private static JsonNode fixture(String name) throws Exception { return CombatJson.parse(Files.readAllBytes(fixturePath(name))); }
    private static Frozen frozen(String name) throws Exception {
        var fixture = fixture(name);
        return CombatInputs.freeze(fixture.get("combat_simulation_inputs"), new Capture((ObjectNode) fixture.get("capture")));
    }
    private static String wire(RegimentKind kind) { return kind == RegimentKind.LEVY ? "levy" : "men_at_arms"; }
    private static String wire(TrialResult result) { return result.name().toLowerCase(java.util.Locale.ROOT); }
    private static ObjectNode entry(Entry e) {
        var o = CombatJson.object(); o.put("regiment_id", e.regimentId()); o.put("kind", wire(e.kind()));
        o.put("current_raw", e.currentRaw()); o.put("soft_casualties_raw", e.softCasualtiesRaw());
        o.put("toughness_raw", e.toughnessRaw()); o.put("pursuit_raw", e.pursuitRaw()); o.put("screen_raw", e.screenRaw());
        var components = o.putArray("components");
        for (var c : e.components()) { var row = components.addObject(); row.put("maximum_soldiers", c.maximumSoldiers());
            row.put("current_soldiers", c.currentSoldiers()); row.put("kind", c.kind()); }
        return o;
    }
    private static ArrayNode entries(List<Entry> values) { var a = CombatJson.array(); for (var e : values) a.add(entry(e)); return a; }
    private static ArrayNode integers(List<BigInteger> values) { var a = CombatJson.array(); values.forEach(a::add); return a; }
    private static ObjectNode main(MainCasualtyResult r) {
        var o = CombatJson.object(); o.set("entries", entries(r.entries())); o.put("conversion_raw", r.conversionRaw());
        o.put("total_hard_raw", r.totalHardRaw()); o.put("total_soft_raw", r.totalSoftRaw());
        var rows = o.putArray("rows"); for (var r0 : r.rows()) { var row = rows.addObject();
            row.put("regiment_id", r0.regimentId()); row.put("total_raw", r0.totalRaw()); row.put("hard_raw", r0.hardRaw());
            row.put("soft_raw", r0.softRaw()); row.put("component_whole_soldier_loss", r0.componentWholeSoldierLoss()); }
        return o;
    }
    private static ObjectNode pursuit(PursuitDayResult r) {
        var o = CombatJson.object(); o.set("entries", entries(r.entries())); var credit = o.putArray("hard_by_regiment_raw");
        for (var row : r.hardByRegimentRaw()) credit.addArray().add(row.regimentId()).add(row.hardRaw());
        o.put("total_hard_raw", r.totalHardRaw()); o.put("toughness_soft_raw", r.toughnessSoftRaw());
        o.put("pursuit_damage_raw", r.pursuitDamageRaw()); o.put("screen_raw", r.screenRaw()); o.put("base_raw", r.baseRaw());
        o.put("minimum_raw", r.minimumRaw()); o.put("extra_raw", r.extraRaw()); o.put("floor_component_raw", r.floorComponentRaw());
        var domains = o.putArray("domains");
        for (var d : r.domains()) { var row = domains.addObject(); row.put("kind", wire(d.kind()));
            row.put("current_soft_raw", d.currentSoftRaw()); row.put("extra_daily_raw", d.extraDailyRaw());
            row.put("floor_daily_raw", d.floorDailyRaw()); row.put("hard_raw", d.hardRaw());
            row.put("allocation_remainder_raw", d.allocationRemainderRaw()); }
        return o;
    }
    private static ObjectNode trial(TrialOutcome r) {
        var o = CombatJson.object(); o.put("result", wire(r.result())); o.put("battle_days", r.battleDays());
        o.put("player_hard_loss_raw", r.playerHardLossRaw()); o.put("enemy_hard_loss_raw", r.enemyHardLossRaw());
        o.put("player_stack_wipe", r.playerStackWipe()); o.put("commander_or_knight_death", r.commanderOrKnightDeath()); return o;
    }
    private static Entry regiment(long id, RegimentKind kind, long current, long soft, long toughness, long pursuit, long screen,
            List<BackingComponent> components) {
        return new Entry(n(id), kind, n(current), n(soft), n(toughness), n(pursuit), n(screen), components);
    }

    @Test void exactOriginalMainCasualtiesAndStoredOrderPursuitMatch() throws Exception {
        var request = CombatJson.object(); var cases = request.putArray("main"); var expected = CombatJson.object();
        var mainExpected = expected.putArray("main"); var random = new Random(0x4ad685b3L);
        for (int i = 0; i < 32; i++) {
            var values = List.of(
                    regiment(1, RegimentKind.LEVY, 40_000_000 + random.nextInt(10_000), 0,
                            i == 0 ? -1_000_000 : 1_100_000, 0, 0, List.of(new BackingComponent(n(3), n(3), 0), new BackingComponent(n(5), n(5), 0))),
                    regiment(2, RegimentKind.MEN_AT_ARMS, 60_000_000 + random.nextInt(10_000), 0, 1_300_000, 0, 0,
                            List.of(new BackingComponent(n(2), n(2), 0), new BackingComponent(n(5), n(5), 0))));
            BigInteger incoming = n(31_000_000L + random.nextInt(100_000)), total = fighting(values);
            var row = cases.addObject(); row.set("entries", entries(values)); row.put("incoming", incoming); row.put("total", total);
            mainExpected.add(main(applyMainPhaseCasualties(values, incoming, total, n(30_000), n(10_000), n(20_000), n(5_000))));
        }
        var retreaters = List.of(
                regiment(1, RegimentKind.LEVY, 0, 35_000_000, 1_000_000, 0, 0, List.of()),
                regiment(1, RegimentKind.LEVY, 0, 25_000_000, 1_000_000, 0, 0, List.of()),
                regiment(3, RegimentKind.MEN_AT_ARMS, 0, 40_000_000, 2_000_000, 0, 500_000, List.of()));
        var pursuers = List.of(regiment(4, RegimentKind.MEN_AT_ARMS, 30_000_000, 0, 1, 1_500_000, 0, List.of()));
        request.set("retreaters", entries(retreaters)); request.set("pursuers", entries(pursuers));
        var pools = PursuitInitialPools.fromEntries(retreaters);
        expected.set("pursuit", pursuit(applyPursuitDay(retreaters, pursuers, pools, n(0), n(0))));
        var three = applyThreeDayPursuit(retreaters, pursuers, pools, n(0), n(0));
        expected.put("three_total", three.totalHardRaw()); expected.set("three_entries", entries(three.entries()));
        var componentCases = request.putArray("components"); var componentExpected = expected.putArray("components");
        for (var amount : List.of(n(456_516), n(-200_000), n(0), BigInteger.ONE.shiftLeft(68).add(n(123)))) {
            var values = List.of(new BackingComponent(n(2), n(0), 3), new BackingComponent(n(5), n(5), 0));
            componentCases.add(amount); var result = allocateHardCasualtiesToComponents(values, amount);
            var row = componentExpected.addArray(); row.add(integers(result.components().stream().map(BackingComponent::currentSoldiers).toList()));
            row.add(integers(result.wholeSoldierLosses())); row.add(result.unallocatedRaw());
        }
        JsonNode actual = ForecastOriginalOracle.call("""
                import json,sys
                from dataclasses import asdict
                from xar_autoplayer.simulation.combat_core import *
                p=json.load(sys.stdin)
                def entries(rows):
                    return tuple(CombatRegimentState(**{**r,'kind':RegimentKind(r['kind']),
                        'components':tuple(BackingComponent(**c) for c in r['components'])}) for r in rows)
                mains=[asdict(apply_main_phase_casualties(entries(r['entries']),incoming_damage_raw=r['incoming'],
                    defending_total_fighting_men_raw=r['total'],defending_hard_modifier_raw=10000,
                    attacking_enemy_hard_modifier_raw=20000,combat_hard_winter_raw=5000)) for r in p['main']]
                ret,pur=entries(p['retreaters']),entries(p['pursuers'])
                pools=PursuitInitialPools.from_entries(ret)
                day=apply_pursuit_day(ret,pur,initial_pools=pools)
                three=apply_three_day_pursuit(ret,pur,initial_pools=pools)
                components=[]
                for amount in p['components']:
                    r=allocate_hard_casualties_to_components((BackingComponent(2,0,3),BackingComponent(5,5)),amount)
                    components.append([[c.current_soldiers for c in r.components],r.whole_soldier_losses,r.unallocated_raw])
                print(json.dumps({'main':mains,'pursuit':asdict(day),'three_total':three.total_hard_raw,
                    'three_entries':[asdict(e) for e in three.entries],'components':components}))
                """, request);
        assertJsonEquals(expected, actual);
        assertEquals(List.of(n(1_357_000), n(1_357_000), n(904_666)),
                applyPursuitDay(retreaters, pursuers, pools, n(0), n(0)).hardByRegimentRaw().stream().map(HardCredit::hardRaw).toList());
    }

    @Test void originalRandomConsumptionRetreatAndNullableForcedWinnerMatch() throws Exception {
        var input = CombatJson.array(); var expected = CombatJson.array();
        for (long seed : new long[] {0, 1, 42, -1, 0x8000_0000L, 0xffff_ffffL, Long.MAX_VALUE}) {
            input.add(seed); var row = expected.addArray(); row.add(avalanche32(seed));
            var state = phaseScheduleState(seed); row.add(state.counter()); row.add(state.draw31().value());
            var child = effectChildState(state, 1_775_997_395L);
            row.add(child.parentDraw()); row.add(child.nextParent().counter()); row.add(child.child().counter()); row.add(child.child().draw31().value());
            var seeds = firePhaseEventSeeds(seed, 2, true); row.add(seeds.base());
            var knights = row.addArray(); seeds.knightEffectSeeds().forEach(knights::add); row.add(seeds.commanderEffectSeed());
            var day = scheduleMainDayRandomness(state, 0, new CommanderRollRequest(true, n(0), n(10), n(0)),
                    new CommanderRollRequest(true, n(11), n(-1), n(0)));
            row.add(day.side0FireDraw()); row.add(day.side1FireDraw()); row.add(day.side0RollDraw()); row.add(day.side1RollDraw());
            row.add(day.side0Roll()); row.add(day.side1Roll()); row.add(day.state().counter());
            var force = row.addArray();
            for (var phase : Phase.values()) { var f = applyForcedWinnerEffect(phase, null, 0, false);
                var f0 = force.addArray().add(f.forcedSideField()); if (f.winnerSide() == null) f0.addNull(); else f0.add(f.winnerSide()); f0.add(f.synchronouslyAdvanced()); }
        }
        assertJsonEquals(expected, ForecastOriginalOracle.call("""
                import json,sys
                from xar_autoplayer.simulation.combat_core import *
                out=[]
                for seed in json.load(sys.stdin):
                    s=phase_schedule_state(seed); child=effect_child_state(s,1775997395)
                    f=fire_phase_event_seeds(seed,executed_knight_count=2,commander_executes=True)
                    d=schedule_main_day_randomness(s,roll_cadence=0,side_0_roll=CommanderRollRequest(True,0,10),
                        side_1_roll=CommanderRollRequest(True,11,-1))
                    force=[]
                    for phase in CombatPhase:
                        r=apply_forced_winner_effect(phase=phase,current_winner_side=None,scoped_side=0,scoped_yes=False)
                        force.append([r.forced_side_field,r.winner_side,r.synchronously_advanced])
                    out.append([avalanche32(seed),s.counter,s.draw31()[0],child[0],child[1].counter,child[2].counter,
                        child[2].draw31()[0],f.base,list(f.knight_effect_seeds),f.commander_effect_seed,
                        d.side_0_fire_draw,d.side_1_fire_draw,d.side_0_roll_draw,d.side_1_roll_draw,d.side_0_roll,d.side_1_roll,d.state.counter,force])
                print(json.dumps(out))
                """, input));
        assertEquals(RetreatBlockReason.MINIMUM_DAYS, evaluateCanRetreat(new RetreatGateInput(false, false, 14, Phase.MAIN, false, 14)).blockedBy());
        assertTrue(evaluateCanRetreat(new RetreatGateInput(false, false, 15, Phase.MAIN, false, 14)).canRetreat());
        assertEquals(RetreatBlockReason.PHASE, evaluateCanRetreat(new RetreatGateInput(false, true, 0, Phase.PURSUIT, false, 14)).blockedBy());
        assertEquals(RetreatBlockReason.DISALLOWED, evaluateCanRetreat(new RetreatGateInput(true, true, 0, Phase.PURSUIT, true, 14)).blockedBy());
        assertEquals(1, winnerAtMainTickStart(null, n(0), n(0)).intValue());
    }

    @Test void originalWidthAttributionSelectionAndSummaryContractsMatch() throws Exception {
        var expected = CombatJson.object(); var widths = expected.putArray("widths");
        BigInteger previous = n(0);
        for (long[] pair : new long[][] {{200300000,128800000},{410690163,82785368},{470651390,12161798}}) {
            var width = updateCombatWidth(n(pair[0]), n(pair[1]), previous, n(90000), n(100000), n(100));
            widths.addArray().add(width.base()).add(width.finalWidth()); previous = width.base();
        }
        expected.set("credit", integers(allocateAttackerHardCredit(List.of(n(18000000), n(13000000)), n(456516), n(31000000))));
        var weights = List.of(n(0), n(-5), BigInteger.ONE.shiftLeft(100), n(3));
        expected.put("choice", weightedChoiceIndex(weights, n(2147483647), -1));
        var selection = selectPhaseEvent(List.of(new PhaseEventCandidate("none", true, n(0), true),
                new PhaseEventCandidate("invalid", false, n(100), false)), phaseScheduleState(42));
        expected.put("selection_key", selection.selectedCandidateKey()); expected.put("selection_draw", selection.random31());
        expected.put("selection_counter", selection.state().counter()); expected.put("trigger_count", selection.triggerValidCount());
        var streams = deriveTrialRandomStreams(BigInteger.ONE.shiftLeft(64).subtract(n(1)), 3);
        expected.putArray("streams").add(streams.globalState().counter()).add(streams.globalState().salt())
                .add(streams.phaseScheduleState().counter()).add(streams.phaseScheduleState().salt());
        var outcomes = List.of(
                new TrialOutcome(TrialResult.PLAYER_WIN,1,n(10),n(50),false,false),
                new TrialOutcome(TrialResult.PLAYER_WIN,2,n(20),n(40),false,false),
                new TrialOutcome(TrialResult.PLAYER_WIN,3,n(30),n(30),false,false),
                new TrialOutcome(TrialResult.PLAYER_LOSS,4,n(40),n(20),true,true),
                new TrialOutcome(TrialResult.NO_RESOLUTION,5,n(50),n(10),false,false));
        var summary = summarizeTrialOutcomes(outcomes, new Experiment("B".repeat(64), n(7), 5, 30), BOUNDED_CORE_MANIFEST);
        var summaryNode = expected.putArray("summary").add(summary.inputSha256()).add(summary.playerWins()).add(summary.playerLosses())
                .add(summary.noResolution()).add(summary.playerWinProbabilityResolved())
                .add(summary.playerWinWilson95().lower()).add(summary.playerWinWilson95().upper());
        for (var distribution : List.of(summary.battleDays(), summary.playerHardLossesRaw(), summary.enemyHardLossesRaw()))
            summaryNode.addArray().add(distribution.mean()).add(distribution.p10()).add(distribution.p50()).add(distribution.p90());
        summaryNode.add(summary.playerStackWipeProbability()).add(summary.commanderOrKnightDeathProbability())
                .add(summary.fidelityGate()).add(summary.plannerUsable()).add(summary.modelFidelity());
        var domains = summaryNode.addArray(); summary.missingRequiredDomains().forEach(domains::add);
        assertJsonEquals(expected, ForecastOriginalOracle.call("""
                import json,sys
                from xar_autoplayer.simulation.combat_core import *
                json.load(sys.stdin)
                widths=[]; previous=0
                for a,b in ((200300000,128800000),(410690163,82785368),(470651390,12161798)):
                    width=update_combat_width(a,b,previous_base_width=previous,terrain_width_multiplier_raw=90000)
                    widths.append(width); previous=width[0]
                choice=weighted_choice_index((0,-5,1<<100,3),2147483647)
                sel=select_phase_event((PhaseEventCandidate('none',True,0,True),PhaseEventCandidate('invalid',False,100)),phase_schedule_state(42))
                r=derive_trial_random_streams((1<<64)-1,3)
                outcomes=tuple(TrialOutcome(result,day,player,enemy,wipe,death) for result,day,player,enemy,wipe,death in (
                    (TrialResult.PLAYER_WIN,1,10,50,False,False),(TrialResult.PLAYER_WIN,2,20,40,False,False),
                    (TrialResult.PLAYER_WIN,3,30,30,False,False),(TrialResult.PLAYER_LOSS,4,40,20,True,True),
                    (TrialResult.NO_RESOLUTION,5,50,10,False,False)))
                s=summarize_trial_outcomes(outcomes,experiment=CombatExperiment('B'*64,7,5,30),manifest=CURRENT_BOUNDED_CORE_MANIFEST)
                summary=[s.input_sha256,s.player_wins,s.player_losses,s.no_resolution,s.player_win_probability_resolved,
                    s.player_win_wilson95.lower,s.player_win_wilson95.upper]
                summary.extend([[d.mean,d.p10,d.p50,d.p90] for d in (s.battle_days,s.player_hard_losses_raw,s.enemy_hard_losses_raw)])
                summary.extend([s.player_stack_wipe_probability,s.commander_or_knight_death_probability,s.fidelity_gate,s.planner_usable,s.model_fidelity,list(s.missing_required_domains)])
                print(json.dumps({'widths':widths,'credit':allocate_attacker_hard_credit((18000000,13000000),hard_raw=456516,incoming_damage_raw=31000000),
                    'choice':choice,'selection_key':sel.selected_candidate_key,'selection_draw':sel.random31,'selection_counter':sel.state.counter,
                    'trigger_count':sel.trigger_valid_count,'streams':[r.global_state.counter,r.global_state.salt,r.phase_schedule_state.counter,r.phase_schedule_state.salt],
                    'summary':summary}))
                """, CombatJson.object()));
    }

    @Test void integerDivisionRoundsOnceAndCanonicalFloatsMatchOriginalPython() throws Exception {
        var request = CombatJson.object(); var ratios = request.putArray("ratios"); var expectedBits = CombatJson.array();
        var values = List.of(
                List.of(BigInteger.ONE.shiftLeft(53).add(n(1)), BigInteger.ONE.shiftLeft(53)),
                List.of(BigInteger.ONE.shiftLeft(53).add(n(3)), BigInteger.ONE.shiftLeft(53)),
                List.of(n(1), BigInteger.ONE.shiftLeft(1075)),
                List.of(n(-1), BigInteger.ONE.shiftLeft(1076)),
                List.of(n(3), BigInteger.ONE.shiftLeft(1075)),
                List.of(BigInteger.ONE.shiftLeft(1024).subtract(BigInteger.ONE.shiftLeft(971)), n(1)));
        var expanded = new ArrayList<>(values);
        var random = new Random(0xc0319a06L);
        for (int i = 0; i < 128; i++) expanded.add(List.of(new BigInteger(300, random).subtract(BigInteger.ONE.shiftLeft(299)),
                new BigInteger(300, random).add(BigInteger.ONE)));
        for (var row : expanded) {
            ratios.addArray().add(row.get(0)).add(row.get(1));
            expectedBits.add(java.util.HexFormat.of().formatHex(ByteBuffer.allocate(8).putDouble(CombatCore.ratio(row.get(0), row.get(1))).array()));
        }
        var floats = request.putArray("floats");
        for (double value : new double[] {0.0, -0.0, 1e23, 1e-4, 1e-5, 1e16, Double.MIN_VALUE, Double.MIN_NORMAL, Double.MAX_VALUE}) floats.add(value);
        for (int exponent = -1074; exponent <= 1023; exponent++) floats.add(Math.scalb(1.0, exponent));
        for (int i = 0; i < 256; i++) { double value = Double.longBitsToDouble(random.nextLong()); if (Double.isFinite(value)) floats.add(value); }
        request.put("unicode", "汉字\u2028\u0000\uD83D\uDE00");
        JsonNode original = ForecastOriginalOracle.call("""
                import json,sys,struct
                p=json.load(sys.stdin)
                bits=[struct.pack('>d',a/b).hex() for a,b in p['ratios']]
                print(json.dumps({'bits':bits,'canonical':json.dumps(p['floats'],ensure_ascii=False,sort_keys=True,separators=(',',':')),
                    'whole':json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':'))},ensure_ascii=False))
                """, request);
        assertJsonEquals(expectedBits, original.get("bits"));
        assertEquals(original.get("canonical").textValue(), new String(CombatJson.canonical(floats), StandardCharsets.UTF_8));
        assertEquals(original.get("whole").textValue(), new String(CombatJson.canonical(request), StandardCharsets.UTF_8));
        assertThrows(ArithmeticException.class, () -> CombatCore.ratio(n(1), n(0)));
        assertThrows(ArithmeticException.class, () -> CombatCore.ratio(BigInteger.ONE.shiftLeft(1024), n(1)));
        assertThrows(CombatInputException.class, () -> CombatJson.canonical(CombatJson.object().put("float", Double.NaN)));
    }

    @Test void allFiveActualBaseInputProducersAndMalformedFieldBoundariesMatch() throws Exception {
        var packet = CombatJson.object(); var cases = packet.putArray("valid"); var expected = CombatJson.object();
        var valid = expected.putArray("valid");
        for (String name : LIVE_FIXTURES) {
            var source = fixture(name); cases.add(source); valid.add(inputProjection(frozen(name)));
        }
        var negative = packet.putArray("invalid"); var base = (ObjectNode) fixture(LIVE_FIXTURES.getFirst()).get("combat_simulation_inputs");
        var variants = new ArrayList<ObjectNode>();
        var wrong = base.deepCopy(); wrong.put("target_province_id", true); variants.add(wrong);
        wrong = base.deepCopy(); wrong.put("target_province_id", 2596.0); variants.add(wrong);
        wrong = base.deepCopy(); wrong.remove("target_province_id"); variants.add(wrong);
        wrong = base.deepCopy(); wrong.putNull("target_province_id"); variants.add(wrong);
        wrong = base.deepCopy(); ((ObjectNode) wrong.get("scenario")).put("actual_route_dependency", true); variants.add(wrong);
        wrong = base.deepCopy(); ((ObjectNode) wrong.get("armies").get(0)).put("identity_valid", false);
        ((ObjectNode) wrong.get("armies").get(0).get("regiments").get(0)).put("identity_valid", false); variants.add(wrong);
        wrong = base.deepCopy(); ((ObjectNode) wrong.get("armies").get(0).get("regiments").get(0).get("effective_stats")).put("scale", true); variants.add(wrong);
        wrong = base.deepCopy(); ((ObjectNode) wrong.get("target_province").get("defender_context")).put("holding_defender", 1); variants.add(wrong);
        wrong = base.deepCopy(); ((ObjectNode) wrong.get("completeness")).put("input_observation_ready", false); variants.add(wrong);
        wrong = base.deepCopy(); ((ObjectNode) wrong.get("armies").get(0).get("regiments").get(1).get("counter")).put("current_chunk_raw", 99991); variants.add(wrong);
        for (var variant : variants) { negative.add(variant); assertThrows(CombatInputException.class, () -> CombatInputs.freeze(variant, null)); }
        expected.put("invalid_count", variants.size());
        assertJsonEquals(expected, ForecastOriginalOracle.call("""
                import json,sys
                from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input,CombatInputError
                p=json.load(sys.stdin)
                def project(x):
                    out={'input_sha256':x.input_sha256,'armies':[],'sides':[]}
                    for a in x.armies:
                        out['armies'].append([a.public_army_id,a.native_army_id,a.current_soldiers,a.main_phase_soldiers,len(a.regiments),
                            a.commander.character_id,a.commander.generic_advantage_points,len(a.knights),sum(k.prowess for k in a.knights)])
                    for side in ('player_or_allied','enemy'):
                        other='enemy' if side=='player_or_allied' else 'player_or_allied'
                        own=x.initial_entries_for_side(side); enemy=x.initial_entries_for_side(other)
                        out['sides'].append([x.dynamic_counter_retention_by_class_raw(side,own,enemy),x.counter_adjusted_damage_raw(side),
                            [[e.regiment_id,e.current_raw,e.soft_casualties_raw,e.toughness_raw,e.pursuit_raw,e.screen_raw] for e in own]])
                    return out
                good=[project(freeze_combat_simulation_input(r['combat_simulation_inputs'],capture=r['capture'])) for r in p['valid']]
                invalid=0
                for r in p['invalid']:
                    try: freeze_combat_simulation_input(r)
                    except CombatInputError: invalid+=1
                print(json.dumps({'valid':good,'invalid_count':invalid}))
                """, packet));
    }

    private static ObjectNode inputProjection(Frozen x) {
        var o = CombatJson.object(); o.put("input_sha256", x.inputSha256()); var armies = o.putArray("armies");
        for (var a : x.armies()) { var row = armies.addArray().add(a.publicArmyId()).add(a.nativeArmyId()).add(a.currentSoldiers())
                .add(a.mainPhaseSoldiers()).add(a.regiments().size());
            if (a.commander().characterId() == null) row.addNull(); else row.add(a.commander().characterId());
            if (a.commander().genericAdvantagePoints() == null) row.addNull(); else row.add(a.commander().genericAdvantagePoints());
            row.add(a.knights().size()); BigInteger prowess = n(0); for (var k : a.knights()) prowess = prowess.add(k.prowess()); row.add(prowess); }
        var sides = o.putArray("sides");
        for (var side : Coalition.values()) { var other = side == Coalition.PLAYER_OR_ALLIED ? Coalition.ENEMY : Coalition.PLAYER_OR_ALLIED;
            var own = x.initialEntriesForSide(side); var row = sides.addArray();
            row.add(integers(x.dynamicCounterRetentionByClassRaw(side, own, x.initialEntriesForSide(other))));
            row.add(x.counterAdjustedDamageRaw(side)); var stored = row.addArray();
            for (var e : own) stored.addArray().add(e.regimentId()).add(e.currentRaw()).add(e.softCasualtiesRaw())
                    .add(e.toughnessRaw()).add(e.pursuitRaw()).add(e.screenRaw()); }
        return o;
    }

    @Test void realV2ProducerZeroIdentitiesReachJavaConsumerWithoutBecomingAbsent() throws Exception {
        // Intentional correction: original producer accepts slot/character zero,
        // while the retained legacy simulation consumer erroneously rejects it.
        JsonNode cases = ForecastOriginalOracle.call("""
                import json,sys,ast,types,importlib,copy
                from pathlib import Path
                from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input,CombatInputError
                json.load(sys.stdin); root=Path(sys.argv[1]); src=root/'ck3_autonomous_player/src'
                bridge=types.ModuleType('xar_autoplayer.bridge'); bridge.__path__=[str(src/'xar_autoplayer/bridge')]
                sys.modules[bridge.__name__]=bridge
                producer=importlib.import_module('xar_autoplayer.bridge.combat_contract')
                file=root/'ck3_autonomous_player/tests/unit/test_combat_simulation_inputs_contract.py'
                names={'_army','_snapshot','_combat_regiment','_combat_army','_combat_inputs'}
                selected=[node for node in ast.parse(file.read_text(encoding='utf-8')).body if isinstance(node,ast.FunctionDef) and node.name in names]
                ns={}; exec(compile(ast.Module(body=selected,type_ignores=[]),str(file),'exec'),ns)
                out=[]
                for kind in ('public_cunit','owner','commander','knight'):
                    value=ns['_combat_inputs'](); snapshot=ns['_snapshot'](); attackers=[12]
                    if kind=='public_cunit':
                        attackers=[0]; value['scenario']['attacker_army_ids']=[0]; value['armies'][0]['army_id']=0
                        for war in snapshot['active_wars']:
                            for army in war['allied_armies']:
                                if army['army_id']==12: army['army_id']=0
                    elif kind=='owner':
                        value['armies'][0]['owner']['character_id']=0
                        value['counter_resolutions'][0]['countered_modifier_owner_character_id']=0
                        value['counter_resolutions'][1]['countering_modifier_owner_character_id']=0
                    elif kind=='commander':
                        value['armies'][0]['commander'].update(status='available',character_id=0,generic_advantage_points=0)
                    else:
                        value['armies'][0]['knights']['members']=[dict(eligible=True,character_id=0,source_regiment_id=31,army_id=1012,
                            participant_army_membership_verified=True,prowess=-3,knight_effectiveness_raw=185000,
                            effective_damage_raw=9250000,effective_toughness_raw=1850000,scale=100000)]
                    scope=producer.combat_simulation_encounter_scope(snapshot,attackers,[22])
                    normalized=producer.normalize_combat_simulation_inputs(value,expected_target_province_id=900,
                        expected_attacker_entry_province_id=800,expected_encounter_scope=scope)
                    rejected=False
                    try: freeze_combat_simulation_input(normalized)
                    except CombatInputError: rejected=True
                    out.append(dict(kind=kind,normalized=normalized,original_consumer_rejected=rejected))
                print(json.dumps(out))
                """, CombatJson.object());
        assertEquals(4, cases.size());
        for (JsonNode row : cases) {
            assertTrue(row.get("original_consumer_rejected").booleanValue(), "preserve original consumer bug evidence");
            var input = CombatInputs.freeze(row.get("normalized"), null); var army = input.armies().getFirst();
            switch (row.get("kind").textValue()) {
                case "public_cunit" -> {
                    assertEquals(n(0), army.publicArmyId()); assertEquals(n(0), input.encounter().attackerArmyIds().getFirst());
                    assertEquals(n(0), new ActiveRouteSideState(n(0), false, false, false, false, 0, n(0), n(0)).firstStoredPublicCunitId());
                }
                case "owner" -> { assertEquals(n(0), army.ownerCharacterId()); assertEquals(n(0), input.counterResolutions().getFirst().counteredOwnerCharacterId()); }
                case "commander" -> {
                    assertEquals(n(0), army.commander().characterId());
                    assertEquals(n(0), new SelectedCommanders(n(0), null).attackerCharacterId());
                    assertNull(new SelectedCommanders(null, null).attackerCharacterId());
                }
                case "knight" -> assertEquals(n(0), army.knights().getFirst().characterId());
                default -> fail("unexpected original case");
            }
        }
        assertEquals(n(Integer.MAX_VALUE), CombatJson.publicCunitId(n(Integer.MAX_VALUE), "slot"));
        for (var bad : List.of(n(-1), n(2_147_483_648L))) {
            assertThrows(CombatInputException.class, () -> CombatJson.publicCunitId(bad, "slot"));
            assertThrows(CombatInputException.class, () -> CombatJson.characterId(bad, "character"));
        }
        assertThrows(CombatInputException.class, () -> CombatJson.publicCunitId(CombatJson.parse("true".getBytes(StandardCharsets.UTF_8)), "slot"));
        assertThrows(CombatInputException.class, () -> CombatJson.characterId(CombatJson.parse("0.0".getBytes(StandardCharsets.UTF_8)), "character"));
    }

    @Test void completeOriginalResearchEnvelopeTrialsUseFrozenNativeAdvantageAndOrderedWorkers() throws Exception {
        var source = fixture("live_rev4_player_attacks_357.json"); var input = frozen("live_rev4_player_attacks_357.json");
        var packet = CombatJson.object(); packet.set("source", source); var rows = packet.putArray("cases");
        var expected = CombatJson.array();
        BigInteger a = input.encounter().attackerArmyIds().getFirst(), d = input.encounter().defenderArmyIds().getFirst();
        var ordinary = new Assumptions(a, d);
        var selected = new SelectedCommanders(input.armiesForSide(input.encounter().attackerSide()).getFirst().commander().characterId(),
                input.armiesForSide(input.encounter().defenderSide()).getFirst().commander().characterId());
        for (int horizon : new int[] {1, 3, 4, 12, 120}) for (BigInteger nativeRaw : new BigInteger[] {null, n(-20_000_000)}) {
            var assumptions = nativeRaw == null ? ordinary : new Assumptions(a, d, nativeRaw, selected);
            var kernel = new PhaseEventsDisabledResearchKernel(assumptions);
            var row = rows.addObject(); row.put("horizon", horizon); if (nativeRaw == null) row.putNull("native"); else row.put("native", nativeRaw);
            var outcomes = expected.addArray();
            for (int index = 0; index < 4; index++) outcomes.add(trial(kernel.simulateTrial(input, deriveTrialRandomStreams(n(42), index), horizon)));
        }
        assertJsonEquals(expected, ForecastOriginalOracle.call("""
                import json,sys
                from dataclasses import asdict
                from xar_autoplayer.simulation.combat_core import derive_trial_random_streams
                from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input
                from xar_autoplayer.simulation.research_envelope import ResearchEnvelopeAssumptions,PhaseEventsDisabledResearchKernel
                p=json.load(sys.stdin); s=p['source']; x=freeze_combat_simulation_input(s['combat_simulation_inputs'],capture=s['capture'])
                a=x.armies_for_side(x.encounter.attacker_side)[0]; d=x.armies_for_side(x.encounter.defender_side)[0]
                out=[]
                for r in p['cases']:
                    kw={} if r['native'] is None else {'precontact_zero_roll_advantage_raw':r['native'],
                        'precontact_selected_commander_character_ids':(a.commander.character_id,d.commander.character_id)}
                    k=PhaseEventsDisabledResearchKernel(ResearchEnvelopeAssumptions(a.public_army_id,d.public_army_id,**kw))
                    out.append([asdict(k.simulate_trial(x,streams=derive_trial_random_streams(42,i),horizon_days=r['horizon'])) for i in range(4)])
                print(json.dumps(out))
                """, packet));
        var experiment = new Experiment(input.inputSha256(), n(42), 8, 120);
        var serial = ResearchEnvelope.run(input, experiment, ordinary, 1, 2);
        var parallel = ResearchEnvelope.run(input, experiment, ordinary, 2, 4);
        assertEquals(serial, parallel); assertFalse(serial.fidelityGate()); assertFalse(serial.plannerUsable());
        assertEquals("ck3-1.19.0.6-phase-events-disabled-envelope-v4", serial.simulatorBuild());
    }

    @Test void activeResumeUsesObservedPoolsAndHorizonIncludesFourthPursuitFinalizer() throws Exception {
        var input = frozen("live_rev4_player_attacks_357.json"); var e = input.encounter();
        var activeEncounter = new Encounter(e.targetProvinceId(), e.attackerEntryProvinceId(), e.attackerSide(), e.defenderSide(),
                e.attackerArmyIds(), e.defenderArmyIds(), "observed_active_combat_resume_fixed_future_participants",
                e.terrainKey(), e.terrainWidthMultiplierRaw(), e.crossingKind(), e.holdingDefender(), e.baseWidth(), e.finalWidth());
        var active = new Frozen(input.inputSha256(), activeEncounter, input.armies(), input.counterResolutions(),
                input.inputObservationReady(), input.nativeMonteCarloReady(), input.nativeMissingRequiredDomains(), input.capture());
        var a = active.armiesForSide(e.attackerSide()).getFirst(); var d = active.armiesForSide(e.defenderSide()).getFirst();
        var assumptions = new Assumptions(a.publicArmyId(), d.publicArmyId()); var kernel = new ActiveMainResumeResearchKernel(assumptions);
        var packet = CombatJson.object(); packet.set("source", fixture("live_rev4_player_attacks_357.json")); var cases = packet.putArray("cases");
        var expected = CombatJson.array();
        for (int loser : new int[] {-1, 0, 1}) for (int horizon : new int[] {1, 2, 3, 4, 5}) {
            var side0 = active.initialEntriesForSide(e.attackerSide()); var side1 = active.initialEntriesForSide(e.defenderSide());
            if (loser == 0) side0 = emptied(side0); if (loser == 1) side1 = emptied(side1);
            var route0 = new ActiveRouteSideState(a.publicArmyId(), false, false, false, false, 14, n(loser == 0 ? 11_000 : 15_000), n(loser == 0 ? -25_000 : 7_000));
            var route1 = new ActiveRouteSideState(d.publicArmyId(), false, false, false, false, 14, n(loser == 1 ? 11_000 : 15_000), n(loser == 1 ? -25_000 : 9_000));
            var state = new ActiveMainResumeState(active, n(16_777_218), active.capture().snapshotId(), Phase.MAIN, 2, 5, 1,
                    n(4), n(7), a.commander().genericAdvantagePoints(), d.commander().genericAdvantagePoints(),
                    a.commander().characterId(), d.commander().characterId(), e.finalWidth(), side0, side1,
                    damage(active, e.attackerSide()), damage(active, e.defenderSide()), route0, route1);
            cases.addObject().put("loser", loser).put("horizon", horizon);
            expected.add(trial(kernel.simulateTrial(state, deriveTrialRandomStreams(n(871), 0), horizon)));
        }
        assertJsonEquals(expected, ForecastOriginalOracle.call("""
                import json,sys
                from dataclasses import replace,asdict
                from xar_autoplayer.simulation.combat_core import CombatPhase,derive_trial_random_streams
                from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input
                from xar_autoplayer.simulation.research_envelope import *
                p=json.load(sys.stdin); s=p['source']; x=freeze_combat_simulation_input(s['combat_simulation_inputs'],capture=s['capture'])
                x=replace(x,encounter=replace(x.encounter,participant_policy='observed_active_combat_resume_fixed_future_participants'))
                a=x.armies_for_side(x.encounter.attacker_side)[0]; d=x.armies_for_side(x.encounter.defender_side)[0]
                def damage(side): return tuple((r.regiment_id,r.stats.damage_raw) for a in x.armies_for_side(side) for r in a.regiments if r.fights_in_main_phase)
                def empty(entries): return tuple(replace(e,current_raw=0,soft_casualties_raw=8000000 if i==0 else e.soft_casualties_raw) for i,e in enumerate(entries))
                out=[]
                for r in p['cases']:
                    loser=r['loser']; s0=x.initial_entries_for_side(x.encounter.attacker_side); s1=x.initial_entries_for_side(x.encounter.defender_side)
                    if loser==0: s0=empty(s0)
                    if loser==1: s1=empty(s1)
                    route0=ActiveRouteSideState(a.public_army_id,False,False,False,False,14,11000 if loser==0 else 15000,-25000 if loser==0 else 7000)
                    route1=ActiveRouteSideState(d.public_army_id,False,False,False,False,14,11000 if loser==1 else 15000,-25000 if loser==1 else 9000)
                    state=ActiveMainResumeState(x,16777218,x.capture_snapshot_id,CombatPhase.MAIN,2,5,1,4,7,
                        a.commander.generic_advantage_points,d.commander.generic_advantage_points,a.commander.character_id,d.commander.character_id,
                        x.encounter.final_width,s0,s1,damage(x.encounter.attacker_side),damage(x.encounter.defender_side),route0,route1)
                    k=ActiveMainResumeResearchKernel(ResearchEnvelopeAssumptions(a.public_army_id,d.public_army_id))
                    out.append(asdict(k.simulate_trial(state,streams=derive_trial_random_streams(871,0),horizon_days=r['horizon'])))
                print(json.dumps(out))
                """, packet));
        assertFalse(kernel.manifest().fidelityGate());
        assertEquals("ck3-1.19.0.6-active-main-resume-research-v3", kernel.manifest().simulatorBuild());
        assertThrows(CombatInputException.class, () -> new ActiveRouteSideState(n(1), false, false, false, false, 0, BigInteger.ONE.shiftLeft(63), n(0)));
        assertThrows(CombatInputException.class, () -> new Assumptions(a.publicArmyId(), d.publicArmyId(), n(0), null));
    }

    private static List<Entry> emptied(List<Entry> values) {
        var result = new ArrayList<Entry>();
        for (int i = 0; i < values.size(); i++) { var e = values.get(i);
            result.add(e.withPools(n(0), i == 0 ? n(8_000_000) : e.softCasualtiesRaw(), e.components())); }
        return List.copyOf(result);
    }
    private static List<EffectiveDamage> damage(Frozen input, Coalition side) {
        return input.regimentsForSide(side).stream().filter(Regiment::fightsInMainPhase)
                .map(r -> new EffectiveDamage(r.regimentId(), r.stats().damageRaw())).toList();
    }
}

