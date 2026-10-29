package org.xar.ck3.control.application.planning;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

/** Calls the unchanged original Python producer as a compatibility oracle; no Python policy is generated. */
final class OrdinaryCoreOriginalProducerTest {
    private static final int MAX_OUTPUT_BYTES = 2 * 1024 * 1024;
    private static final String ORACLE = """
            import hashlib, json, pathlib, sys
            repo = pathlib.Path(sys.argv[1])
            sys.path.insert(0, str(repo / "ck3_autonomous_player" / "src"))
            from xar_autoplayer.strategy import _choose_one_life_turn_core
            source = repo / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "strategy.py"
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            cases = json.load(sys.stdin)["cases"]
            outputs = [_choose_one_life_turn_core(c["history"], snapshot=c["snapshot"],
                action_steps=c["action_steps"], bridge_capabilities=[]) for c in cases]
            after = hashlib.sha256(source.read_bytes()).hexdigest()
            if before != after:
                raise RuntimeError("original source changed during producer evaluation")
            json.dump({"source_sha256": before, "outputs": outputs}, sys.stdout, ensure_ascii=False)
            """;

    @Test void baselinePostwarTieAndVisibleFailuresMatchTheActualOriginalCoreProducer() throws Exception {
        var baseline = request(snapshot(), List.of(), Set.of(new OperationKey("save-checkpoint")));
        var interrupted = request(snapshot(), List.of(history("life-advance", "ordinary event interrupted")),
                Set.of(new OperationKey("resolve-current-event")));
        var terminal = request(snapshot(), List.of(history("life-advance", "one-life death terminal visible: fixture")),
                Set.of(new OperationKey("death-terminal")));
        var armies = new OpportunityJson.Arr(List.of(army(12, 1000), army(0, 1000), army(99, 100)));
        var postwar = request(snapshot().with("player_armies", armies), List.of(),
                Set.of(new OperationKey("disband-army-0"), new OperationKey("disband-army-12"), new OperationKey("disband-army-99")));
        List<PlanningRequest> requests = List.of(baseline, interrupted, terminal, postwar);
        var originals = original(requests);
        assertEquals(requests.size(), originals.size());
        var core = core();
        for (int i = 0; i < requests.size(); i++) {
            var selected = assertInstanceOf(OrdinaryPolicy.Replace.class,
                    core.evaluate(requests.get(i), OrdinaryPolicy.Draft.empty()));
            assertEquals(originals.get(i), selected.draft().detail(), "complete original policy/phase/reason/step/payload case " + i);
            var command = selected.draft().command().orElseThrow();
            assertEquals(originals.get(i).get("selected_step"), new OpportunityJson.Text(command.operation().value()));
            assertEquals(requests.get(i).before(), command.before());
            assertEquals(requests.get(i).source(), command.source());
        }
    }

    private static OrdinaryCorePolicy core() {
        var leaves = new ArrayList<WarCorePlanner.Leaf>();
        for (var boundary : List.of(WarCorePlanner.Boundary.TERMINATION_SCORE_PRELUDE,
                WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_PRELUDE,
                WarCorePlanner.Boundary.BATTLE_CONTROL_PRELUDE))
            leaves.add(new WarCorePlanner.Leaf(boundary, SOURCE,
                    (request, draft) -> new MilitaryPlanningDecision.Keep(new OpportunityJson.Obj(Map.of()))));
        PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                throw new AssertionError("these peaceful compatibility cases do not authorize native reads");
            }
        };
        var war = new WarCorePlanner(leaves, request -> { throw new AssertionError("no active war"); },
                (request, selected) -> { throw new AssertionError("no military action"); }, reads,
                (input, selection) -> { throw new AssertionError("no readonly query in this production regression path"); }, (request, previous) -> { throw new AssertionError("no battle transition"); });
        OrdinaryCorePolicy.CoreProducer noForeground = (request, previous) ->
                new OrdinaryPolicy.NotApplicable("actual compatibility inputs contain no event, interaction or optional domain");
        return new OrdinaryCorePolicy(SOURCE, war, noForeground, noForeground, noForeground, noForeground,
                (request, operation, arguments, plan, purpose, domain) ->
                        new OrdinaryCorePolicy.Prepared(command(request, operation, arguments)),
                step -> step.equals("life-advance"));
    }

    private static OpportunityJson.Obj army(long id, long soldiers) {
        return new OpportunityJson.Obj(Map.ofEntries(
                Map.entry("army_id", integer(id)), Map.entry("soldiers", integer(soldiers)),
                Map.entry("controllable", new OpportunityJson.Bool(true)),
                Map.entry("owner_character_id", integer(29829)),
                Map.entry("current_province_id", integer(10884)),
                Map.entry("army_state", new OpportunityJson.Text("regular")),
                Map.entry("in_combat", new OpportunityJson.Bool(false)), Map.entry("retreating", new OpportunityJson.Bool(false)),
                Map.entry("route_province_ids", new OpportunityJson.Arr(List.of())),
                Map.entry("move_target_province_id", OpportunityJson.Nil.INSTANCE)));
    }
    private static OpportunityJson.Obj history(String operation, String error) {
        return new OpportunityJson.Obj(Map.of("index", integer(1), "command", new OpportunityJson.Text(operation),
                "ok", new OpportunityJson.Bool(false), "error", new OpportunityJson.Text(error)));
    }
    private static List<OpportunityJson.Obj> original(List<PlanningRequest> requests) throws Exception {
        Path repo = Path.of(required("xar.repository.root")).toAbsolutePath().normalize();
        Path source = repo.resolve("ck3_autonomous_player/src/xar_autoplayer/strategy.py");
        assertTrue(Files.isRegularFile(source), "complete original producer source is required");
        String sourceSha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
        var cases = new ArrayList<OpportunityJson.Value>();
        for (var request : requests) {
            var steps = request.observations().actionSteps().stream().sorted(java.util.Comparator.comparing(OperationKey::value))
                    .<OpportunityJson.Value>map(step -> new OpportunityJson.Text(step.value())).toList();
            cases.add(new OpportunityJson.Obj(Map.of("snapshot", request.observations().snapshot(),
                    "history", new OpportunityJson.Arr(request.observations().history().stream().<OpportunityJson.Value>map(row -> row).toList()),
                    "action_steps", new OpportunityJson.Arr(steps))));
        }
        ProcessBuilder builder = new ProcessBuilder(required("xar.python"), "-B", "-X", "utf8", "-c", ORACLE, repo.toString());
        builder.directory(repo.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = readers.submit(() -> read(process.getInputStream()));
            var stderr = readers.submit(() -> read(process.getErrorStream()));
            try {
                try (var stdin = process.getOutputStream()) {
                    stdin.write(DriverJson.encode(new OpportunityJson.Obj(Map.of("cases", new OpportunityJson.Arr(cases)))));
                }
                assertTrue(process.waitFor(30, TimeUnit.SECONDS), "original producer timed out; no skipped or partial pass");
                byte[] output = stdout.get(5, TimeUnit.SECONDS), errors = stderr.get(5, TimeUnit.SECONDS);
                assertEquals(0, process.exitValue(), "original producer failed: " + new String(errors, StandardCharsets.UTF_8));
                var body = DriverJson.object(output, MAX_OUTPUT_BYTES);
                assertEquals(sourceSha, OpportunityJson.text(body.get("source_sha256"), "original source SHA"));
                var rows = new ArrayList<OpportunityJson.Obj>();
                for (var row : OpportunityJson.array(body.get("outputs"), "original outputs"))
                    rows.add(OpportunityJson.object(row, "original plan"));
                return List.copyOf(rows);
            } finally {
                if (process.isAlive()) process.destroyForcibly();
            }
        }
    }
    private static byte[] read(InputStream input) throws IOException {
        byte[] raw = input.readNBytes(MAX_OUTPUT_BYTES + 1);
        if (raw.length > MAX_OUTPUT_BYTES) throw new IOException("original producer output exceeds explicit oracle budget");
        return raw;
    }
    private static String required(String property) {
        String value = System.getProperty(property);
        assertNotNull(value, "required original compatibility property " + property);
        assertFalse(value.isBlank(), "empty original compatibility property " + property);
        return value;
    }
}
