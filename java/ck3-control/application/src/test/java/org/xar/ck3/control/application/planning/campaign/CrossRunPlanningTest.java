package org.xar.ck3.control.application.planning.campaign;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Full unchanged producer -> Java reducer -> durable codec -> ordinary focus reader. */
final class CrossRunPlanningTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @Test void typedBoundaryRejectsWrongMissingAndNullWithoutGrantingActions() {
        assertThrows(IllegalArgumentException.class, () -> CrossRunPlanning.focus(Optional.of(json("{\"priorities\":[{\"priority\":true,\"action\":\"war\"}]}"))));
        assertThrows(IllegalArgumentException.class, () -> CrossRunPlanning.focus(Optional.of(json("{\"priorities\":[{\"priority\":1.0,\"action\":\"war\"}]}"))));
        assertThrows(IllegalArgumentException.class, () -> CrossRunPlanning.focus(Optional.of(json("{\"priorities\":null}"))));
        assertEquals(Optional.empty(), CrossRunPlanning.focus(Optional.of(json("{}"))));
        assertEquals(Optional.of("war"), CrossRunPlanning.focus(Optional.of(json("{\"priorities\":[{\"action\":\"war\"}]}"))));
        State initial = CrossRunPlanning.empty(); byte[] raw = CrossRunPlanning.encodeState(initial);
        assertEquals(initial, CrossRunPlanning.decodeState(raw));
        Obj row = object(OpportunityJson.parse(raw), "state");
        assertThrows(IllegalArgumentException.class, () -> CrossRunPlanning.decodeState(OpportunityJson.encode(row.with("format_version", new Bool(true)))));
        assertThrows(IllegalArgumentException.class, () -> CrossRunPlanning.decodeState(OpportunityJson.encode(row.with("episodes", Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class, () -> CrossRunPlanning.recordEpisode(initial, "fixture", List.of(), json("{\"terminal\":false}"), NOW));
        assertThrows(IllegalArgumentException.class, () -> CrossRunPlanning.recordEpisode(initial, "fixture", List.of(), json("{\"terminal\":true,\"terminal_reason\":1}"), NOW));
        assertThrows(IllegalArgumentException.class, () -> CrossRunPlanning.recordEpisode(initial, "fixture", List.of(json("{\"command\":\"enforce-demands-9\",\"ok\":1}")), json("{\"terminal\":true}"), NOW));
    }

    @Test void originalProductionReducerAndFocusDifferential() throws Exception {
        String rootValue = System.getProperty("xar.repository.root"), python = System.getProperty("xar.python");
        assertNotNull(rootValue, "whole parity must configure xar.repository.root; reference absence is RED, never skipped");
        assertNotNull(python, "whole parity must configure xar.python before the test JVM");
        assertFalse(rootValue.isBlank()); assertFalse(python.isBlank());
        Path root = Path.of(rootValue).toRealPath();
        Path source = root.resolve("ck3_autonomous_player/src/xar_autoplayer/strategy.py");
        byte[] before = Files.readAllBytes(source); String digest = sha(before);
        Process child = new ProcessBuilder(python, "-B", "-X", "utf8", "-c", SCRIPT, root.toString())
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var future = readers.submit(() -> child.getInputStream().readNBytes(131_073));
            if (!child.waitFor(90, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new AssertionError("original cross-run producer timed out");
            }
            raw = future.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) child.destroyForcibly(); }
        assertEquals(0, child.exitValue()); assertTrue(raw.length > 0 && raw.length <= 131_072);
        assertEquals(digest, sha(Files.readAllBytes(source)), "unchanged reference producer source required");
        Obj captured = object(OpportunityJson.parse(raw), "original producer capture");
        assertEquals(digest, text(captured.get("strategy_sha256"), "strategy_sha256"));
        List<Value> plans = array(captured.get("plans"), "plans"); assertEquals(16, plans.size());
        for (Value entry : plans) {
            Obj item = object(entry, "plan case"), a = object(item.get("achievements"), "achievements");
            Plan actual = CrossRunPlanning.nextRunPlan(new Achievements(bool(a.get("palermo_holy_war_won"), "war"), bool(a.get("armies_disbanded"), "disband"),
                    bool(a.get("danish_betrothal_accepted"), "marriage"), bool(a.get("partition_risk_visible"), "partition")));
            assertEquals(item.get("expected"), CrossRunPlanning.planJson(actual));
            assertEquals(actual, CrossRunPlanning.parsePlan(CrossRunPlanning.planJson(actual)));
        }
        List<Value> focuses = array(captured.get("focuses"), "focuses"); assertEquals(6, focuses.size());
        for (Value entry : focuses) {
            Obj item = object(entry, "focus case"); Value expected = item.get("expected");
            assertEquals(expected == Nil.INSTANCE ? Optional.empty() : Optional.of(text(expected, "expected")),
                    CrossRunPlanning.focus(Optional.of(object(item.get("input"), "input"))));
        }
        List<Value> episodes = array(captured.get("episodes"), "episodes"); assertEquals(5, episodes.size());
        for (Value entry : episodes) {
            Obj item = object(entry, "episode case");
            List<Obj> commands = array(item.get("commands"), "commands").stream().map(value -> object(value, "command")).toList();
            State actual = CrossRunPlanning.recordEpisode(CrossRunPlanning.empty(), "cross-run-fixture", commands,
                    object(item.get("terminal"), "terminal"), NOW);
            State restored = CrossRunPlanning.decodeState(CrossRunPlanning.encodeState(actual)); assertEquals(actual, restored);
            assertEquals(item.get("expected"), CrossRunPlanning.episodeJson(restored.episodes().getFirst()));
            assertEquals(item.get("next_run_plan"), CrossRunPlanning.planJson(restored.nextRunPlan()));
            State replaced = CrossRunPlanning.recordEpisode(restored, "cross-run-fixture", commands, object(item.get("terminal"), "terminal"), NOW);
            assertEquals(1, replaced.episodes().size(), "same episode identity is replaced, never duplicated");
            assertEquals(actual, replaced);
        }
    }
    private static Obj json(String raw) { return object(OpportunityJson.parse(raw.getBytes(StandardCharsets.UTF_8)), "fixture"); }
    private static String sha(byte[] bytes) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }

    // Test-only invocation of unchanged production functions. No replacement Python implementation.
    private static final String SCRIPT = """
            import sys,json,hashlib,itertools,tempfile,copy
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            import xar_autoplayer.strategy as s
            source=root/'ck3_autonomous_player/src/xar_autoplayer/strategy.py';before=hashlib.sha256(source.read_bytes()).hexdigest()
            s.utc_now=lambda:'2026-10-24T00:00:00Z'
            keys=['palermo_holy_war_won','armies_disbanded','danish_betrothal_accepted','partition_risk_visible']
            plans=[]
            for flags in itertools.product([False,True],repeat=4):
                a=dict(zip(keys,flags));plans.append({'achievements':a,'expected':s._next_run_plan(a)})
            focuses=[]
            for p in [{},{'priorities':[]},{'priorities':[{'action':'war'}]}, {'priorities':[{'priority':5,'action':'succession'},{'priority':9,'action':'war'}]}, {'priorities':[{'priority':8,'action':'war'},{'priority':8,'action':'alliance'}]}, {'priorities':[{'priority':2,'action':'finish'},{'priority':1,'action':'partition'}]}]:
                focuses.append({'input':p,'expected':s._cross_run_focus(p)})
            terminal={'terminal':True,'technical_settlement_handoff':True,'score':{'final':123.5}}
            confirmed=[{'command':'enforce-demands-9','ok':True,'result':{'war_victory':{'status':'victory_enforced'}}}, {'command':'disband-army-9','ok':True,'result':{'war_action':{'status':'disbanded'}}}, {'command':'arrange-marriage-707-809','ok':True,'result':{'marriage_result':{'status':'accepted_betrothal','source':'native_relationship_snapshot','candidate_character_id':809}}}, {'command':'succession-review','ok':True,'result':{'succession_state':{'partition_risk_visible':True}}}, {'command':'save-checkpoint','ok':True,'result':{'checkpoint':{'name':'fixture','size':12,'sha256':'a'*64}}}]
            unknown=copy.deepcopy(confirmed)
            for r in unknown:r['ok']=False
            ack=copy.deepcopy(confirmed)
            for r in ack:r['result']={'accepted':True}
            nested=[{'command':'auto-run 5','ok':True,'result':{'turns':[dict(r,command='auto-turn',result=dict(r['result'],auto_turn={'selected_step':r['command']})) for r in confirmed]}}]
            newer=confirmed+[{'command':'enforce-demands-9','ok':True,'result':{'war_victory':{'status':'pending'}}}]
            episodes=[]
            for commands in [confirmed,unknown,ack,nested,newer]:
                original=copy.deepcopy(commands)
                with tempfile.TemporaryDirectory(prefix='xar-cross-run-reference-') as temp:
                    result=s.record_one_life_episode(Path(temp),run_id='cross-run-fixture',commands=commands,terminal=terminal)
                if original!=commands:raise RuntimeError('original producer mutated commands')
                episodes.append({'commands':commands,'terminal':terminal,'expected':result['recorded_episode'],'next_run_plan':result['next_run_plan']})
            if before!=hashlib.sha256(source.read_bytes()).hexdigest():raise RuntimeError('original producer drifted')
            print(json.dumps({'strategy_sha256':before,'plans':plans,'focuses':focuses,'episodes':episodes},ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
