package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Chain;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.ChainPlan;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Pin;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Proof;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.ProofKind;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Request;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Status;
import org.xar.ck3.rrf.qualification.SourceQualificationEmitter;

/** Real producer and actual unchanged shared consumer, with synthetic provenance kept explicit. */
final class SourceQualificationTest {
    @TempDir Path directory;
    @BeforeEach void canonicalizeTemporaryDirectory() throws IOException {
        directory = directory.toRealPath();
    }
    private static final String HOST = "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py";
    private static final List<String> CRITICAL = List.of("player_pilgrimage_planner_private_transport.py", "player_pilgrimage_activities_private_transport.py", "native_driver.py", "mcp_server.py", "nonwar_private_build.py", "version_identity.py", "activity_feast_stage5_start_private_transport.py", "driver.py", "exact_clock_failure_diagnostic_v1.py");
    private record Fixture(Path root, Request request) { }

    @Test void actualProducerPreservesOriginalIdentityAndPassesAllSixRealConsumers() throws Exception {
        Fixture fixture = fixture(true); Path output = directory.resolve("qualified");
        var result = SourceQualificationEmitter.generate(fixture.request(), output);
        assertEquals(Status.SOURCE_BOUND_NOT_LIVE, result.status()); assertEquals(7, result.outputs().size());
        JsonNode q = Json.read(Files.readAllBytes(output.resolve("QUALIFICATION.other_source_delta.actual.json")), JsonNode.class);
        assertEquals(fixture.request().sourceCommit(), q.get("source_commit").textValue());
        assertFalse(q.get("new_test_execution_performed").booleanValue());
        assertEquals(0, q.get("current_test_executions_run").intValue());
        assertEquals(1, q.get("actual_source_proofs").size());
        Path repo = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        String script = """
                import pathlib, sys
                sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / 'tools'))
                import ck3_mod_acceptance_build_runtime as builder
                for chain in ('public_control','case_hooks','shared_host','shared_sdk_delta','pilgrimage_wire_seam','other_source_delta'):
                    builder.qualify(chain, pathlib.Path(sys.argv[3]) / ('QUALIFICATION.'+chain+'.actual.json'), sys.argv[4], pathlib.Path(sys.argv[2]), ['other.txt'], 'synthetic-source-fixture')
                print('ACTUAL_SIX_CONSUMERS_PASS')
                """;
        String python = python(repo);
        assertTrue(command(List.of(python, "-B", "-X", "utf8", "-c", script, repo.toString(), fixture.root().toString(), output.toString(), fixture.request().sourceCommit())).contains("ACTUAL_SIX_CONSUMERS_PASS"));
        JsonNode delta = Json.read(Files.readAllBytes(output.resolve("NATIVE-SHARED-HOST-DELTA.actual.json")), JsonNode.class);
        assertEquals(fixture.request().sourceCommit(), delta.get("runtime_source_commit").textValue());
    }

    @Test void uncoveredChangedSourceProducesGapWithoutAnyQualificationAndTamperedProofRejects() throws Exception {
        Fixture fixture = fixture(false);
        var result = SourceQualificationEmitter.generate(fixture.request(), directory.resolve("gap"));
        assertEquals(Status.GAP, result.status()); assertTrue(result.outputs().isEmpty());
        assertTrue(result.gaps().stream().anyMatch(g -> g.path().equals("other.txt")));
        assertFalse(Files.exists(directory.resolve("gap/QUALIFICATION.other_source_delta.actual.json")));
        Files.writeString(Path.of(fixture.request().sourceDelta().path()), "{}");
        assertThrows(IOException.class, () -> SourceQualificationEmitter.generate(fixture.request(), directory.resolve("tampered")));
    }

    @Test void strictRequestRejectsMissingWrongTypeAndPreservesRoundTrip() throws Exception {
        Fixture fixture = fixture(true); byte[] bytes = Json.write(fixture.request());
        assertEquals(fixture.request(), Json.read(bytes, Request.class));
        String text = new String(bytes, StandardCharsets.UTF_8);
        for (String wrong : List.of("true", "1.0", "\"1\"", "null")) assertThrows(IOException.class, () -> Json.read(text.replace("\"schemaVersion\" : 1", "\"schemaVersion\" : " + wrong).getBytes(StandardCharsets.UTF_8), Request.class));
        ObjectNode bad = new ObjectMapper().readValue(bytes, ObjectNode.class);
        bad.withObject("sourceDelta").put("bytes", true); assertThrows(IOException.class, () -> Json.read(Json.write(bad), Request.class));
        bad.withObject("sourceDelta").put("bytes", 1.0); assertThrows(IOException.class, () -> Json.read(Json.write(bad), Request.class));
        assertThrows(IllegalArgumentException.class, () -> new Request(1, "fixture", fixture.root().toString(), "a".repeat(40), fixture.request().sourceDelta(), fixture.request().classifierProgram(), List.of(), fixture.request().previousHostDelta()));
    }

    @Test void classificationMatchesActualSharedConsumerForEveryRuleBranch() throws Exception {
        List<String> paths = List.of(HOST, "tools/g2_saved_campaign/a.py", "_runtime/a.py", "tools/ck3_obs_a.py", "ck3_autonomous_player/native_bridge/a.md", "ck3_autonomous_player/native_bridge/a.py", "ck3_autonomous_player/native_bridge/a.cpp", "ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py", "ck3_autonomous_player/src/exact_day.py", "ck3_autonomous_player/src/speed_configuration.py", "ck3_autonomous_player/src/application_main_clock.py", "ck3_autonomous_player/src/rite_governance.py", "ck3_autonomous_player/src/a.py", "tools/ck3_mod_acceptance_cases/event.json", "tools/ck3_mod_acceptance_cases/a.json", "tools/test_a.py", "ck3_autonomous_player/tests/a.py", "tools/ck3_mod_acceptance.py", "tools/build_normal_exit_a.py", "tools/fixture_engine_a.py", "x/recorder_job.py", "docs/a.json", "promo/a.py", "x/a.md", "x/a.bbcode", "mod_other/a.txt");
        Path repo = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Path input = directory.resolve("paths.json"); Files.write(input, Json.write(Map.of("paths", paths)));
        String script = "import json,pathlib,sys;sys.path.insert(0,str(pathlib.Path(sys.argv[1])/'tools'));import ck3_mod_acceptance_build_runtime as b;print(json.dumps({p:sorted(b.classify(p)) for p in json.loads(pathlib.Path(sys.argv[2]).read_text())['paths']}))";
        String python = python(repo);
        JsonNode actual = Json.read(command(List.of(python, "-B", "-X", "utf8", "-c", script, repo.toString(), input.toString())).getBytes(StandardCharsets.UTF_8), JsonNode.class);
        for (String path : paths) assertEquals(SourceQualificationEmitter.classify(path).stream().sorted().toList(), new ObjectMapper().convertValue(actual.get(path), new com.fasterxml.jackson.core.type.TypeReference<List<String>>() { }), path);
    }

    @Test void commandProofRequiresOriginalExactZeroWaitAndCurrentSourceSnapshot() throws Exception {
        Fixture fixture = fixture(false); Pin log = file("original-command.log", "synthetic original command PASS\n");
        ObjectNode command = new ObjectMapper().createObjectNode(); command.put("machine_id", "synthetic-source-fixture"); command.put("result", "PASS"); command.put("original_wait_returncode", 0); command.put("skipped", 0); command.putArray("argv").add("synthetic-only"); command.set("log", new ObjectMapper().valueToTree(log));
        Pin original = json("original-command.json", command);
        ObjectNode validation = new ObjectMapper().createObjectNode(); validation.put("machine_id", "synthetic-source-fixture"); validation.put("result", "PASS"); validation.put("exit_code", 0); validation.put("skipped", 0); validation.put("source_unchanged_during_execution", true); validation.put("commands_run", 1); validation.set("command_results", new ObjectMapper().valueToTree(List.of(original))); validation.set("source_pins", new ObjectMapper().valueToTree(List.of(pin(fixture.root().resolve("other.txt")))));
        Request valid = proofRequest(fixture, ProofKind.COMMAND_VALIDATION, json("validation.json", validation));
        assertTrue(SourceQualificationEmitter.generate(valid, directory.resolve("command-pass")).gaps().isEmpty());
        command.put("original_wait_returncode", true); Pin wrong = json("wrong-command.json", command); validation.set("command_results", new ObjectMapper().valueToTree(List.of(wrong)));
        Request invalid = proofRequest(fixture, ProofKind.COMMAND_VALIDATION, json("wrong-validation.json", validation));
        assertThrows(IOException.class, () -> SourceQualificationEmitter.generate(invalid, directory.resolve("command-fail")));
        command.put("original_wait_returncode", 0); command.put("pid", 123); command.put("cwd", fixture.root().toString()); command.put("process_create_time_seconds", "1792887209.0284"); command.put("started_at_utc", "2026-10-25T00:00:00Z"); command.put("finished_at_utc", "2026-10-25T00:00:01Z");
        validation.put("schema", "ck3-command-source-execution-v1"); validation.put("source_commit", fixture.request().sourceCommit()); validation.put("source_identity", "CLEAN_COMMIT"); validation.put("started_at_utc", "2026-10-25T00:00:00Z"); validation.put("observed_at_utc", "2026-10-25T00:00:02Z"); validation.set("source_pins_after", validation.get("source_pins").deepCopy()); validation.set("command_results", new ObjectMapper().valueToTree(List.of(json("fresh-command.json", command))));
        assertTrue(SourceQualificationEmitter.generate(proofRequest(fixture, ProofKind.COMMAND_SOURCE_EXECUTION, json("fresh-validation.json", validation)), directory.resolve("fresh-command-pass")).gaps().isEmpty());
        validation.remove("source_pins_after");
        assertThrows(IOException.class, () -> SourceQualificationEmitter.generate(proofRequest(fixture, ProofKind.COMMAND_SOURCE_EXECUTION, json("missing-after-validation.json", validation)), directory.resolve("fresh-command-fail")));
    }

    @Test void mavenProofRequiresMatchingActualSuccessLogAndCannotCoverAnUnlistedFile() throws Exception {
        Fixture fixture = fixture(false); Pin source = pin(fixture.root().resolve("other.txt"));
        Pin log = file("maven.log", "[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0\n[INFO] BUILD SUCCESS\n");
        ObjectNode review = new ObjectMapper().createObjectNode(); review.put("machine_id", "synthetic-source-fixture"); review.put("command", "mvn verify"); review.put("status", "PASS"); review.put("exit_code", 0); review.set("tests", new ObjectMapper().valueToTree(Map.of("run", 1, "failures", 0, "errors", 0, "skipped", 0))); review.set("logs", new ObjectMapper().valueToTree(List.of(Map.of("path", log.path(), "bytes", log.bytes(), "sha256", log.sha256(), "status", "PASS")))); review.set("source_files", new ObjectMapper().valueToTree(List.of(Map.of("path", "other.txt", "bytes", source.bytes(), "sha256", source.sha256()))));
        assertTrue(SourceQualificationEmitter.generate(proofRequest(fixture, ProofKind.MAVEN_REVIEW, json("review.json", review)), directory.resolve("maven-pass")).gaps().isEmpty());
        ObjectNode wrongTests = review.withObject("tests"); wrongTests.put("run", 53);
        assertThrows(IOException.class, () -> SourceQualificationEmitter.generate(proofRequest(fixture, ProofKind.MAVEN_REVIEW, json("wrong-review.json", review)), directory.resolve("maven-fail")));
        wrongTests.put("run", 1); Pin unselected = pin(fixture.root().resolve("tools/ck3_mod_acceptance_cases/sample.json")); review.set("source_files", new ObjectMapper().valueToTree(List.of(Map.of("path", "tools/ck3_mod_acceptance_cases/sample.json", "bytes", unselected.bytes(), "sha256", unselected.sha256()))));
        assertFalse(SourceQualificationEmitter.generate(proofRequest(fixture, ProofKind.MAVEN_REVIEW, json("unlisted-review.json", review)), directory.resolve("maven-unlisted")).gaps().isEmpty());
    }

    private Request proofRequest(Fixture fixture, ProofKind kind, Pin receipt) {
        Request old = fixture.request(); List<ChainPlan> plans = old.chains().stream().map(p -> p.chain() == Chain.OTHER_SOURCE_DELTA ? new ChainPlan(p.chain(), p.previousQualification(), List.of(new Proof(kind, receipt))) : p).toList();
        return new Request(old.schemaVersion(), old.machineId(), old.repository(), old.sourceCommit(), old.sourceDelta(), old.classifierProgram(), plans, old.previousHostDelta());
    }

    private Fixture fixture(boolean covered) throws Exception {
        Path root = directory.resolve("repo"); Files.createDirectory(root);
        for (String relative : List.of(HOST, "tools/ck3_mod_acceptance_cases/sample.json", "ck3_autonomous_player/src/sample.py", "other.txt")) source(root, relative, "before\n");
        for (String name : CRITICAL) source(root, "ck3_autonomous_player/src/xar_autoplayer/bridge/" + name, "# synthetic\n");
        Path actual = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent().resolve("tools/ck3_mod_acceptance_build_runtime.py");
        Path classifier = root.resolve("tools/ck3_mod_acceptance_build_runtime.py"); Files.copy(actual, classifier);
        git(root, "init", "--quiet"); git(root, "add", "--all"); git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "native"); String nativeCommit = git(root, "rev-parse", "HEAD").strip();
        Pin originalHost = pin(root.resolve(HOST)); source(root, HOST, "after\n"); git(root, "add", "--all"); git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "base"); String base = git(root, "rev-parse", "HEAD").strip();
        Map<String, Map<String, Object>> indexRows = new TreeMap<>();
        for (String name : git(root, "ls-files", "-z").split("\u0000")) { Pin p = pin(root.resolve(name)); indexRows.put(name, signature(p)); }
        Pin beforeOther = pin(root.resolve("other.txt"));
        Pin index = json("source-index.json", Map.of("schema", "ck3-common-source-index-v1", "files", indexRows));
        Pin manifest = json("manifest.json", Map.of("schema", "ck3-mod-acceptance-shared-runtime-v1", "source_commit", base, "machine_id", "synthetic-source-fixture", "source_index", Map.of("path_key", "source_index", "bytes", index.bytes(), "sha256", index.sha256())));
        Pin runtime = json("runtime.json", Map.of("schema", "ck3-mod-acceptance-runtime-v1", "repo_root", root.toString(), "machine_id", "synthetic-source-fixture", "manifest", manifest, "paths", Map.of("source_index", index.path())));
        source(root, "other.txt", "current\n"); git(root, "add", "--all"); git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "current"); String current = git(root, "rev-parse", "HEAD").strip();
        Pin names = file("paths.txt", "other.txt\n");
        Pin diff = json("diff.json", Map.of("machine_id", "synthetic-source-fixture", "source_commit", current, "base_commit", base, "complete_changed_paths", true, "working_tree_clean", true, "untracked_runtime_source_inputs_checked", true, "exit_code", 0, "original_wait_returncode", 0, "paths_sha256", names.sha256()));
        Pin delta = json("source-delta.json", Map.of("schema", "ck3-shared-source-delta-v1", "machine_id", "synthetic-source-fixture", "source_commit", current, "base_source_commit", base, "base_runtime", runtime, "complete_changed_paths_declared_by_Root", true, "Root_diff_receipt", diff, "Root_diff_paths", names, "changes", List.of(Map.of("path", "other.txt", "before", signature(beforeOther), "after", signature(pin(root.resolve("other.txt")))))));
        Pin knowledge = json("knowledge.json", Map.of("result", "PASS", "scope", "synthetic source-only review"));
        Pin proof = json("source-review.json", Map.of("schema", "ck3-source-only-reviewed-scope-v1", "machine_id", "synthetic-source-fixture", "source_commit", current, "result", "PASS", "exit_code", 0, "scope", "UNSELECTED_SOURCE_ONLY", "execution_qualified", false, "previous_knowledge_proof", knowledge, "source_pins", List.of(pin(root.resolve("other.txt")))));
        List<ChainPlan> plans = new ArrayList<>();
        for (Chain chain : Chain.values()) {
            List<Pin> rows = switch (chain) { case PUBLIC_CONTROL -> List.of(pin(classifier)); case CASE_HOOKS -> List.of(pin(root.resolve("tools/ck3_mod_acceptance_cases/sample.json"))); case SHARED_HOST -> List.of(pin(root.resolve(HOST))); case SHARED_SDK_DELTA -> List.of(pin(root.resolve("ck3_autonomous_player/src/sample.py"))); case OTHER_SOURCE_DELTA -> List.of(beforeOther); case PILGRIMAGE_WIRE_SEAM -> { List<Pin> pins = new ArrayList<>(); for (String name : CRITICAL) pins.add(pin(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/" + name))); yield List.copyOf(pins); } };
            ObjectNode q = new ObjectMapper().createObjectNode(); q.put("machine_id", "synthetic-source-fixture"); q.put("source_commit", base); q.put("result", "PASS"); q.put("exit_code", 0); q.put("skipped", 0); q.put("tests_run", chain == Chain.PILGRIMAGE_WIRE_SEAM ? 37 : 1); q.set("covered_chains", new ObjectMapper().valueToTree(List.of(chain.wire()))); q.set(chain == Chain.PILGRIMAGE_WIRE_SEAM ? "critical_source_pins" : "source_pins", new ObjectMapper().valueToTree(rows));
            if (chain == Chain.SHARED_HOST) for (String key : List.of("source_consumer", "source_delta", "reviewed_host_change")) q.set(key, new ObjectMapper().valueToTree(knowledge));
            if (chain == Chain.PILGRIMAGE_WIRE_SEAM) { q.set("test_groups", new ObjectMapper().valueToTree(List.of(20, 11, 6))); q.putArray("wrong_SDK_imports"); q.putArray("source_or_wire_changed_during_test"); for (String key : List.of("actual_execution_wire_packets", "actual_readonly4", "actual_wire_consumer14", "actual_current_wire_consumer14")) q.set(key, new ObjectMapper().valueToTree(knowledge)); }
            Pin previous = json("prior-" + chain.wire() + ".json", q); plans.add(new ChainPlan(chain, previous, chain == Chain.OTHER_SOURCE_DELTA && covered ? List.of(new Proof(ProofKind.SOURCE_REVIEW, proof)) : List.of()));
        }
        ObjectNode hostDelta = new ObjectMapper().createObjectNode(); hostDelta.put("schema", "ck3-exact-same-root-python-host-delta-v1"); hostDelta.put("machine_id", "synthetic-source-fixture"); hostDelta.put("canonical_repo_relative", HOST); hostDelta.put("native_source_commit", nativeCommit); hostDelta.put("runtime_source_commit", base); hostDelta.put("observed_at_utc", "2026-10-25T00:00:00Z"); hostDelta.put("source_classification", "shared_host"); hostDelta.putObject("compiled_inputs"); hostDelta.set("shared_host_qualification", new ObjectMapper().valueToTree(plans.stream().filter(p -> p.chain() == Chain.SHARED_HOST).findFirst().orElseThrow().previousQualification())); hostDelta.set("before", new ObjectMapper().valueToTree(signature(originalHost))); hostDelta.set("after", new ObjectMapper().valueToTree(signature(pin(root.resolve(HOST))))); for (String key : List.of("qualified_native", "snapshot", "reviewed_host_change")) hostDelta.set(key, new ObjectMapper().valueToTree(knowledge));
        return new Fixture(root, new Request(1, "synthetic-source-fixture", root.toString(), current, delta, pin(classifier), plans, json("old-host-delta.json", hostDelta)));
    }
    private Pin json(String name, Object value) throws IOException { Path path = directory.resolve(name); Files.write(path, Json.write(value)); return pin(path); }
    private Pin file(String name, String value) throws IOException { Path path = directory.resolve(name); Files.writeString(path, value); return pin(path); }
    private static Map<String, Object> signature(Pin pin) { return Map.of("bytes", pin.bytes(), "sha256", pin.sha256()); }
    private static String python(Path repo) { Path local = repo.resolve("tools/.venv/Scripts/python.exe"); return System.getProperty("rrf.python", Files.isRegularFile(local) ? local.toString() : "python"); }
    private static Pin pin(Path path) throws IOException { byte[] bytes = Files.readAllBytes(path); return new Pin(path.toAbsolutePath().toString(), bytes.length, ReleaseBuilder.sha256(bytes)); }
    private static void source(Path root, String relative, String text) throws IOException { Path path = root.resolve(relative); Files.createDirectories(path.getParent()); Files.writeString(path, text); }
    private static String git(Path root, String... args) throws Exception { List<String> command = new ArrayList<>(List.of("git", "-C", root.toString())); command.addAll(List.of(args)); return command(command); }
    private static String command(List<String> args) throws Exception { Path log = Files.createTempFile("rrf-source-test-", ".log"); Process child = null; try { child = new ProcessBuilder(args).redirectErrorStream(true).redirectOutput(log.toFile()).start(); assertTrue(child.waitFor(30, TimeUnit.SECONDS)); String output = Files.readString(log); assertEquals(0, child.exitValue(), output); return output; } finally { if (child != null && child.isAlive()) { child.destroyForcibly(); child.waitFor(5, TimeUnit.SECONDS); } Files.deleteIfExists(log); } }
}
