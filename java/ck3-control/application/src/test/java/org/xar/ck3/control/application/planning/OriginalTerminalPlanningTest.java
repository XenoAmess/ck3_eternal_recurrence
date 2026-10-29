package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure DATA differential tests; none of these inputs is a current Native or terminal lease. */
public final class OriginalTerminalPlanningTest {
    private static final String SHA = "52b4381758ee712dc8555ac3a31186e13adbe10c3c18dc93b23bca5147934111";
    private static final String PROGRAM = """
            import hashlib,json,pathlib,sys
            root=pathlib.Path(sys.argv[1])
            source=root/'ck3_autonomous_player/src/xar_autoplayer/strategy.py'
            assert hashlib.sha256(source.read_bytes()).hexdigest()==sys.argv[2]
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer import strategy
            value=json.load(sys.stdin)
            rows=strategy._expanded_command_rows(value['history'])
            result=strategy._plan_one_life_terminal_v1(rows,value['snapshot'],set(value['steps']))
            print(json.dumps({'result':result},ensure_ascii=False,separators=(',',':')))
            """;
    private static Obj parse(String json) { return DriverJson.object(json.getBytes(StandardCharsets.UTF_8), DriverJson.MAX_NATIVE_BYTES); }
    private static Obj snapshot() {
        return parse("{\"snapshot_id\":\"terminal-data\",\"revision\":7,\"native_revision\":11,\"date_raw\":1070,\"episode_run_id\":\"old-episode\",\"episode_character_id\":41,\"played_character\":{\"character_id\":41,\"alive\":false},\"one_life_terminal_reason\":null}");
    }
    private static Obj lifecycle(String mode) {
        Lifecycle value = mode.equals("ordinary_campaign_succession")
                ? new Lifecycle(mode, Optional.of("xar_off"), "absent_by_fresh_campaign_xar_off_contract",
                        "actual-frozen-profile", Optional.of("a".repeat(64)))
                : new Lifecycle("rogue_one_life", Optional.of("xar_on"), "terminal_settlement_required",
                        "actual-frozen-profile", Optional.of("b".repeat(64)));
        return OpportunityJson.object(DriverJson.fromNode(value.toJson()), "lifecycle");
    }
    private static Obj changed(Obj base, String verdict, boolean matched) {
        return base.with("one_life_terminal_reason", new Text("played_character_changed"))
                .with("played_character", parse("{\"character_id\":52,\"alive\":true}"))
                .with("succession_reconciliation", new Obj(Map.of("status", new Text("available"),
                        "verdict", new Text(verdict), "successor_match", new Bool(matched),
                        "title_distribution_match", new Bool(matched))));
    }
    private static Obj completed(Value score, Value status, boolean ok) {
        var result = new java.util.LinkedHashMap<String,Value>();
        result.put("terminal", new Bool(true)); result.put("score", score);
        if (status != null) result.put("settlement_status", status);
        return new Obj(Map.of("command", new Text("death-terminal"), "ok", new Bool(ok), "result", new Obj(result)));
    }
    private static OriginalTerminalPlanning.Input input(Obj snapshot, List<Obj> rows, String... steps) {
        return new OriginalTerminalPlanning.Input(snapshot, rows,
                java.util.Arrays.stream(steps).map(OperationKey::new).collect(java.util.stream.Collectors.toSet()),
                Set.of(), Optional.empty(), Optional.empty());
    }
    private static void original(OriginalTerminalPlanning.Input input) throws Exception {
        String python = System.getProperty("xar.python");
        String repository = System.getProperty("xar.repository.root");
        if (python == null || python.isBlank() || repository == null || repository.isBlank())
            throw new IllegalStateException("MISSING_ORIGINAL_TERMINAL_PYTHON_INPUTS_NOT_RUN");
        Path strategy = Path.of(repository).resolve("ck3_autonomous_player/src/xar_autoplayer/strategy.py");
        assertEquals(SHA, DriverJson.sha256(Files.readAllBytes(strategy)));
        var steps = new Arr(input.actionSteps().stream().map(value -> (Value)new Text(value.value())).toList());
        var request = new Obj(Map.of("snapshot",input.snapshot(),"history",new Arr(new ArrayList<Value>(input.history())),"steps",steps));
        Process process = new ProcessBuilder(python,"-X","utf8","-c",PROGRAM,repository,SHA).redirectErrorStream(true).start();
        try (var out = process.getOutputStream()) { out.write(DriverJson.encode(request)); }
        if (!process.waitFor(30,TimeUnit.SECONDS)) {
            process.destroyForcibly(); throw new IllegalStateException("original terminal oracle timed out");
        }
        byte[] bytes = process.getInputStream().readAllBytes();
        assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));
        Value expected = DriverJson.object(bytes,DriverJson.MAX_NATIVE_BYTES).get("result");
        Value actual = OriginalTerminalPlanning.terminal(input).<Value>map(value -> value).orElse(Nil.INSTANCE);
        assertEquals(expected,actual);
        var wrapped = new Obj(Map.of("result",actual));
        assertEquals(wrapped,DriverJson.object(DriverJson.encode(wrapped),DriverJson.MAX_NATIVE_BYTES));
    }
    @Test void actualOriginalOrdinaryTerminalAndAllSuccessorReconciliationBranches() throws Exception {
        Obj base = snapshot().with("succession_lifecycle",lifecycle("ordinary_campaign_succession"));
        original(input(base,List.of(),"death-terminal","start-next-episode","continue-as-reconciled-successor"));
        original(input(changed(base,"matched",true),List.of(),"continue-as-reconciled-successor"));
        original(input(changed(base,"matched",true),List.of()));
        original(input(changed(base,"different",false),List.of(),"continue-as-reconciled-successor"));
        original(input(base.with("one_life_terminal_reason",new Text("played_character_changed")),List.of(),"continue-as-reconciled-successor"));
    }
    @Test void actualOriginalRogueCompletedScoreZeroUnknownScoreAndExactHistorySelection() throws Exception {
        Obj base = snapshot().with("succession_lifecycle",lifecycle("rogue_one_life"));
        Obj complete = completed(new IntegerValue(java.math.BigInteger.ZERO),new Text("complete"),true);
        original(input(base,List.of(complete),"start-next-episode"));
        original(input(base,List.of(completed(parse("{\"exact\":9007199254740993}"),null,true)),"start-next-episode"));
        original(input(changed(base,"matched",true),List.of(complete),"continue-as-reconciled-successor","start-next-episode"));
        original(input(changed(base,"different",false),List.of(complete),"continue-as-reconciled-successor"));
        original(input(changed(base,"matched",true),List.of(complete),"start-next-episode"));
        original(input(base,List.of(complete,completed(new IntegerValue(java.math.BigInteger.TEN),new Text("complete"),false)),"start-next-episode"));
    }
    @Test void actualOriginalLegacyMissingNullMalformedAndExplicitUnknownLifecycleRemainDistinct() throws Exception {
        original(input(snapshot(),List.of(),"death-terminal"));
        original(input(snapshot().with("succession_lifecycle",Nil.INSTANCE),List.of(),"death-terminal"));
        Obj malformed = lifecycle("ordinary_campaign_succession").with("environment_sha256",Nil.INSTANCE);
        original(input(snapshot().with("succession_lifecycle",malformed),List.of(),"death-terminal"));
        original(input(snapshot().with("succession_lifecycle",new Bool(true)),List.of(),"death-terminal"));
        original(input(snapshot().with("succession_lifecycle",lifecycle("ordinary_campaign_succession").with("extra",new Text("x"))),List.of()));
    }
    @Test void actualOriginalSettlementUnavailableNeedsBothOriginalFieldsAndNoRepeatedDeath() throws Exception {
        Obj row = completed(Nil.INSTANCE,new Text("settlement_unavailable"),true);
        Obj base = snapshot().with("one_life_settlement_status",new Text("settlement_unavailable"));
        original(input(base,List.of(row),"death-terminal","start-next-episode"));
        original(input(snapshot(),List.of(row),"death-terminal"));
        original(input(base,List.of(),"death-terminal"));
    }
    @Test void actualOriginalMissingPlayerUnknownTerminalAndUnsupportedSelectorAreRetainedData() throws Exception {
        Obj base = snapshot().with("played_character",Nil.INSTANCE).with("one_life_terminal_reason",new Text("played_character_missing"));
        original(input(base,List.of(),"death-terminal"));
        original(input(base,List.of()));
        original(input(snapshot().with("played_character",parse("{\"character_id\":41,\"alive\":true}")),List.of(),"death-terminal"));
    }
    @Test void wrongEpisodeIntegerTypeCannotBeReinterpretedByThePureBoundary() {
        assertThrows(IllegalArgumentException.class,() -> OriginalTerminalPlanning.terminal(input(
                snapshot().with("episode_character_id",new Bool(true)),List.of(),"death-terminal")));
        assertThrows(IllegalArgumentException.class,() -> OriginalTerminalPlanning.terminal(input(
                snapshot().with("episode_character_id",parse("{\"v\":41.0}").get("v")),List.of(),"death-terminal")));
    }

    @Test void configuredVanillaTerminalUsesOrdinarySuccessionWithoutSettlement() {
        Obj binding=OpportunityJson.object(DriverJson.fromNode(Lifecycle.ordinaryVanilla().toJson()),"vanilla lifecycle");
        Obj base=snapshot().with("succession_lifecycle",binding);
        Obj terminal=OriginalTerminalPlanning.terminal(input(base,List.of(),"death-terminal","start-next-episode")).orElseThrow();
        assertEquals(new Text("ordinary_campaign_terminal_no_successor"),terminal.get("phase"));
        assertEquals(new Bool(false),terminal.get("settlement_required"));
        assertEquals(Nil.INSTANCE,terminal.get("selected_step"));
        assertEquals(binding,terminal.get("succession_lifecycle"));
        Obj successor=OriginalTerminalPlanning.terminal(input(changed(base,"matched",true),List.of(),"continue-as-reconciled-successor")).orElseThrow();
        assertEquals(new Text("ordinary_successor_continuation_ready"),successor.get("phase"));
        assertEquals(new Text("continue-as-reconciled-successor"),successor.get("selected_step"));
        assertEquals(new Bool(false),successor.get("settlement_required"));
        assertEquals(terminal,OriginalTerminalPlanning.terminal(input(parse(new String(DriverJson.encode(base),StandardCharsets.UTF_8)),
                List.of(),"death-terminal","start-next-episode")).orElseThrow());
    }
    @Test void malformedConfiguredVanillaFieldsRemainExplicitlyUnknownAtTerminalBoundary() {
        Obj binding=OpportunityJson.object(DriverJson.fromNode(Lifecycle.ordinaryVanilla().toJson()),"vanilla lifecycle");
        for(String field:List.of("xar_enabled","environment_sha256")) {
            var fields=new java.util.LinkedHashMap<>(binding.members());fields.remove(field);
            List<Obj> mutations=new ArrayList<>();mutations.add(new Obj(fields));
            for(Value bad:List.<Value>of(new Bool(true),new IntegerValue(java.math.BigInteger.ONE),
                    parse("{\"v\":1.0}").get("v"),new Arr(List.of()),new Obj(Map.of()),new Text("")))
                mutations.add(binding.with(field,bad));
            for(Obj malformed:mutations) {
                Obj terminal=OriginalTerminalPlanning.terminal(input(snapshot().with("succession_lifecycle",malformed),List.of(),"death-terminal")).orElseThrow();
                assertEquals(new Text("terminal_succession_lifecycle_unbound"),terminal.get("phase"));
                assertEquals(new Text("unknown"),OpportunityJson.object(terminal.get("succession_lifecycle"),"normalized lifecycle").get("lifecycle"));
            }
        }
    }
}
