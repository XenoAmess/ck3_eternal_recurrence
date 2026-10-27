package org.xar.ck3.rrf.qualification;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.rrf.Contracts;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Chain;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Disposition;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Gap;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Pin;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Proof;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Request;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Result;
import org.xar.ck3.rrf.qualification.SourceQualificationContracts.Status;

/** Fresh source-equivalence producer. Historical executions keep their original immutable receipts. */
public final class SourceQualificationEmitter {
    private static final String SDK = "ck3_autonomous_player/src/";
    private static final Set<String> GENERIC_DECISION_CONTRACTS = Set.of(
            SDK + "xar_autoplayer/bridge/ingame_decision_item_action_contract.py",
            SDK + "xar_autoplayer/bridge/ingame_decisions_open_contract.py");
    private static final String GENERIC_RELIGION_TRANSPORT = SDK + "xar_autoplayer/bridge/player_religion_context_private_transport.py";
    private static final String NATIVE = "ck3_autonomous_player/native_bridge/";
    private static final String HOST = NATIVE + "research/run_ck3_12002_mcp_live.py";
    private static final Set<String> CRITICAL = Set.of("player_pilgrimage_planner_private_transport.py", "player_pilgrimage_activities_private_transport.py", "native_driver.py", "mcp_server.py", "nonwar_private_build.py", "version_identity.py", "activity_feast_stage5_start_private_transport.py", "driver.py", "exact_clock_failure_diagnostic_v1.py");
    private SourceQualificationEmitter() { }

    public static int run(String[] args) {
        try {
            if (args.length != 4 || !args[0].equals("--inputs") || !args[2].equals("--output")) throw new IllegalArgumentException("source-qualifications --inputs REQUEST --output NEW_DIRECTORY required");
            Result result = generate(Json.read(Files.readAllBytes(Path.of(args[1])), Request.class), Path.of(args[3]));
            System.out.println(new String(Json.write(result), StandardCharsets.UTF_8)); return result.gaps().isEmpty() ? 0 : 1;
        } catch (IOException | IllegalArgumentException error) { System.err.println("RRF SOURCE QUALIFICATION GAP: " + error.getMessage()); return 1; }
    }

    public static Result generate(Request request, Path destination) throws IOException {
        Path root = Path.of(request.repository()).toAbsolutePath().normalize();
        Path output = destination.toAbsolutePath().normalize();
        require(!output.startsWith(root) && !Files.exists(output), "new output outside source checkout required");
        checkRoot(root, request.sourceCommit());
        require(Path.of(request.classifierProgram().path()).toAbsolutePath().normalize().equals(root.resolve("tools/ck3_mod_acceptance_build_runtime.py")), "actual shared classifier program required");
        checked(request.classifierProgram()); JsonNode delta = read(request.sourceDelta());
        require(text(delta, "machine_id").equals(request.machineId()) && text(delta, "source_commit").equals(request.sourceCommit())
                && bool(delta, "complete_changed_paths_declared_by_Root"), "current complete source delta required");
        JsonNode diff = read(parsePin(field(delta, "Root_diff_receipt")));
        require(Set.of("ck3-shared-source-delta-v1", "faith-next-shared-source-delta-v1").contains(text(delta, "schema"))
                && text(delta, "base_source_commit").equals(text(diff, "base_commit")), "source delta/base identity differs");
        JsonNode runtime = read(parsePin(field(delta, "base_runtime")));
        require(text(runtime, "schema").equals("ck3-mod-acceptance-runtime-v1") && text(runtime, "machine_id").equals(request.machineId()) && Path.of(text(runtime, "repo_root")).toAbsolutePath().normalize().equals(root), "base runtime identity differs");
        JsonNode manifest = read(parsePin(field(runtime, "manifest")));
        require(text(manifest, "schema").equals("ck3-mod-acceptance-shared-runtime-v1") && text(manifest, "source_commit").equals(text(delta, "base_source_commit")) && text(manifest, "machine_id").equals(request.machineId()), "frozen base manifest differs");
        JsonNode indexHeader = field(manifest, "source_index");
        JsonNode index = read(new Pin(text(field(runtime, "paths"), text(indexHeader, "path_key")), integer(indexHeader, "bytes"), text(indexHeader, "sha256")));
        JsonNode beforeFiles = field(index, "files"); require(text(index, "schema").equals("ck3-common-source-index-v1") && beforeFiles.isObject(), "frozen source index required");
        require(text(diff, "machine_id").equals(request.machineId()) && text(diff, "source_commit").equals(request.sourceCommit())
                && bool(diff, "complete_changed_paths") && bool(diff, "working_tree_clean") && bool(diff, "untracked_runtime_source_inputs_checked"), "actual complete clean Root diff required");
        zero(diff, "exit_code"); zero(diff, "original_wait_returncode");
        Pin namesPin = parsePin(field(delta, "Root_diff_paths")); checked(namesPin);
        require(text(diff, "paths_sha256").equals(namesPin.sha256()), "Root path inventory hash differs");
        List<String> names = Files.readAllLines(Path.of(namesPin.path()), StandardCharsets.UTF_8);
        Set<String> changes = new HashSet<>(); List<Gap> gaps = new ArrayList<>();
        for (JsonNode change : array(delta, "changes")) {
            String relative = text(change, "path"); Contracts.safePath(relative); require(changes.add(relative), "duplicate delta path");
            JsonNode expectedBefore = beforeFiles.get(relative); JsonNode declaredBefore = field(change, "before");
            require(expectedBefore == null ? declaredBefore.isNull() : expectedBefore.equals(declaredBefore), "source delta before differs from actual base index: " + relative);
            Path path = below(root, relative); JsonNode after = field(change, "after");
            if (after.isNull()) { require(!Files.exists(path), "deleted source still exists"); gaps.add(new Gap("delta", relative, "deletion requires explicit separately qualified archive contract")); }
            else { Pin actual = measure(path); require(integer(after, "bytes") == actual.bytes() && text(after, "sha256").equals(actual.sha256()), "current delta source drift: " + relative); }
        }
        require(names.size() == changes.size() && Set.copyOf(names).equals(changes), "full changed-path list differs");
        String actualDiff = git(root, "diff", "--name-only", "--no-renames", "-z", text(delta, "base_source_commit"), request.sourceCommit(), "--");
        Set<String> actualNames = actualDiff.isEmpty() ? Set.of() : Set.of(actualDiff.split("\u0000"));
        require(actualNames.equals(changes), "complete actual Git delta differs");
        Map<Chain, ObjectNode> prepared = new EnumMap<>(Chain.class);
        for (var plan : request.chains()) {
            JsonNode prior = read(plan.previousQualification()); validatePrevious(prior, request.machineId(), plan.chain());
            Map<String, Pin> previous = sourceRows(prior, plan.chain() == Chain.PILGRIMAGE_WIRE_SEAM ? "critical_source_pins" : "source_pins", root, false);
            Map<String, Pin> verified = new HashMap<>(); Map<String, Pin> evidence = new HashMap<>(); List<Pin> proofRefs = new ArrayList<>();
            Map<String, Pin> proofDependencies = new HashMap<>();
            for (Proof proof : plan.proofs()) {
                JsonNode document = read(proof.receipt()); validateProof(document, proof, request.machineId(), root);
                Map<String, Pin> rows = sourceRows(document, proof.kind() == SourceQualificationContracts.ProofKind.MAVEN_REVIEW ? "source_files" : "source_pins", root, proof.kind() == SourceQualificationContracts.ProofKind.MAVEN_REVIEW);
                proofRefs.add(proof.receipt());
                for (var entry : rows.entrySet()) {
                    if (proof.kind() == SourceQualificationContracts.ProofKind.SOURCE_REVIEW) require(classify(entry.getKey()).stream().allMatch(c -> Set.of("other_source_delta", "case_hooks").contains(c)), "source-only review cannot cover selected control/SDK/host code");
                    Pin current = measure(below(root, entry.getKey()));
                    proofDependencies.put(entry.getKey(), current);
                    if (signatureEqual(current, entry.getValue())) { verified.put(entry.getKey(), current); evidence.put(entry.getKey(), proof.receipt()); }
                }
            }
            for (String dependency : proofDependencies.keySet()) if (!verified.containsKey(dependency)) gaps.add(new Gap(plan.chain().wire(), dependency, "execution proof dependency changed without a current covering proof"));
            Set<String> required = new HashSet<>(previous.keySet());
            for (String path : changes) {
                Set<String> categories = classify(path);
                for (String category : categories) if (!Set.of("changed_tests", "new_native_base_required").contains(category) && !isChain(category)) gaps.add(new Gap(category, path, "required chain is outside this six-chain producer"));
                if (categories.contains(plan.chain().wire()) && (plan.chain() != Chain.PILGRIMAGE_WIRE_SEAM || isCritical(path))) required.add(path);
            }
            if (plan.chain() == Chain.PILGRIMAGE_WIRE_SEAM) for (String critical : CRITICAL) required.add(SDK + "xar_autoplayer/bridge/" + critical);
            List<SourceQualificationContracts.Relation> relations = new ArrayList<>(); List<Pin> currentRows = new ArrayList<>();
            for (String path : required.stream().sorted().toList()) {
                if (!Files.isRegularFile(below(root, path))) { gaps.add(new Gap(plan.chain().wire(), path, "required source missing")); continue; }
                Pin current = measure(below(root, path)); currentRows.add(current);
                if (previous.containsKey(path) && signatureEqual(previous.get(path), current)) relations.add(new SourceQualificationContracts.Relation(path, current, Disposition.RAW_EQUAL_PRIOR, plan.previousQualification()));
                else if (verified.containsKey(path)) relations.add(new SourceQualificationContracts.Relation(path, current, Disposition.SOURCE_PROOF_COVERS, evidence.get(path)));
                else gaps.add(new Gap(plan.chain().wire(), path, "no byte-equal predecessor or actual per-file proof covers this source"));
            }
            ObjectNode next = new ObjectMapper().createObjectNode();
            next.put("machine_id", request.machineId()); next.put("source_commit", request.sourceCommit()); next.put("observed_at_utc", Instant.now().toString());
            next.put("result", "PASS"); next.put("exit_code", 0); next.put("skipped", 0); next.put("tests_run", integer(prior, "tests_run"));
            next.set("covered_chains", tree(List.of(plan.chain().wire())));
            next.put("exit_code_scope", "Actual source binding only; immutable previous qualification retains its original execution waits.");
            next.put("schema", "ck3-source-bound-qualification-successor-v2"); next.put("current_test_executions_run", 0); next.put("new_test_execution_performed", false);
            next.put("tests_run_scope", "Counter retained from immutable previous qualification; new operation binds source only. Each covering execution retains its own identity in actual_source_proofs; no combined or current test count is claimed.");
            next.set("previous_qualification", tree(plan.previousQualification())); next.set("current_source_delta", tree(request.sourceDelta()));
            next.set("source_relations", tree(relations)); next.set("actual_source_proofs", tree(proofRefs));
            next.set(plan.chain() == Chain.PILGRIMAGE_WIRE_SEAM ? "critical_source_pins" : "source_pins", tree(currentRows));
            next.put("all_declared_source_pins_raw_equal", relations.stream().allMatch(r -> r.disposition() == Disposition.RAW_EQUAL_PRIOR));
            next.put("scope", "Complete current source coverage checked per file against immutable prior signatures or explicit covering proofs; no execution, native build, runtime, or live qualification performed by this producer.");
            if (plan.chain() == Chain.SHARED_HOST) for (String key : List.of("source_consumer", "source_delta", "reviewed_host_change")) next.set(key, field(prior, key).deepCopy());
            if (plan.chain() == Chain.PILGRIMAGE_WIRE_SEAM) for (String key : List.of("test_groups", "wrong_SDK_imports", "source_or_wire_changed_during_test", "actual_execution_wire_packets", "actual_readonly4", "actual_wire_consumer14", "actual_current_wire_consumer14")) next.set(key, field(prior, key).deepCopy());
            next.put("game_started", false); next.put("actual_live_business_qualified", false); prepared.put(plan.chain(), next);
        }
        checkRoot(root, request.sourceCommit()); checked(request.sourceDelta()); checked(request.classifierProgram());
        for (var plan : request.chains()) { checked(plan.previousQualification()); for (Proof proof : plan.proofs()) checked(proof.receipt()); }
        ObjectNode hostDelta = null;
        if (gaps.isEmpty()) {
            hostDelta = object(read(request.previousHostDelta())).deepCopy();
            require(hostDelta.size() == 14 && hostDelta.has("observed_at_utc") && hostDelta.has("runtime_source_commit") && hostDelta.has("compiled_inputs") && hostDelta.has("shared_host_qualification")
                    && text(hostDelta, "source_classification").equals("shared_host") && field(hostDelta, "compiled_inputs").isObject(), "complete canonical old host delta required");
            require(text(hostDelta, "schema").equals("ck3-exact-same-root-python-host-delta-v1") && text(hostDelta, "machine_id").equals(request.machineId()), "original exact same-root host delta required");
            require(text(hostDelta, "canonical_repo_relative").equals(HOST), "canonical host delta required");
            JsonNode after = field(hostDelta, "after"); Pin host = measure(below(root, HOST));
            require(integer(after, "bytes") == host.bytes() && text(after, "sha256").equals(host.sha256()), "reviewed host changed; new independent host review required");
            JsonNode before = field(hostDelta, "before");
            byte[] original = git(root, "show", text(hostDelta, "native_source_commit") + ":" + HOST).getBytes(StandardCharsets.UTF_8);
            require(integer(before, "bytes") == original.length && text(before, "sha256").equals(hash(original)), "original committed host differs");
            require(prepared.get(Chain.SHARED_HOST).get("reviewed_host_change").equals(hostDelta.get("reviewed_host_change")), "independent original host review differs");
            for (String key : List.of("qualified_native", "snapshot", "reviewed_host_change")) checked(parsePin(field(hostDelta, key)));
            hostDelta.put("runtime_source_commit", request.sourceCommit()); hostDelta.put("observed_at_utc", Instant.now().toString());
        }
        long prospectiveBytes = 32_768;
        if (gaps.isEmpty()) for (ObjectNode value : prepared.values()) prospectiveBytes = Math.addExact(prospectiveBytes, Json.write(value).length);
        if (hostDelta != null) prospectiveBytes = Math.addExact(prospectiveBytes, Json.write(hostDelta).length + 1024L);
        else prospectiveBytes = Math.addExact(prospectiveBytes, Json.write(gaps).length);
        require(prospectiveBytes <= 2 * 1024 * 1024, "source qualification metadata exceeds total 2 MiB bound");
        Files.createDirectories(output); List<Pin> outputs = new ArrayList<>();
        if (gaps.isEmpty() && hostDelta != null) {
            for (var entry : prepared.entrySet()) outputs.add(write(output.resolve("QUALIFICATION." + entry.getKey().wire() + ".actual.json"), entry.getValue()));
            Pin hostQ = outputs.stream().filter(p -> p.path().endsWith("QUALIFICATION.shared_host.actual.json")).findFirst().orElseThrow();
            hostDelta.set("shared_host_qualification", tree(hostQ)); outputs.add(write(output.resolve("NATIVE-SHARED-HOST-DELTA.actual.json"), hostDelta));
        }
        Result result = new Result("rrf-source-qualification-production-v1", request.machineId(), request.sourceCommit(), Instant.now().toString(), gaps.isEmpty() ? Status.SOURCE_BOUND_NOT_LIVE : Status.GAP, outputs, gaps, false, false, false);
        write(output.resolve("RESULT.actual.json"), result); return result;
    }

    public static Set<String> classify(String path) {
        Contracts.safePath(path); String name = path.substring(path.lastIndexOf('/') + 1);
        if (path.startsWith("tools/g2_saved_campaign/") || path.startsWith("_runtime/") || path.startsWith("tools/ck3_obs_")) return Set.of();
        if (path.equals(HOST)) return Set.of("shared_host");
        if (path.startsWith(NATIVE)) return path.endsWith(".md") ? Set.of() : Set.of(path.endsWith(".py") ? "shared_host" : "new_native_base_required");
        if (path.startsWith(SDK)) {
            if (GENERIC_DECISION_CONTRACTS.contains(path) || path.equals(GENERIC_RELIGION_TRANSPORT)) return Set.of("shared_sdk_delta");
            if (CRITICAL.contains(name)) return Set.of("pilgrimage_wire_seam");
            if (name.contains("exact_day") || name.contains("speed_configuration") || name.contains("application_main_clock")) return Set.of("exact_day_clock", "pilgrimage_wire_seam");
            if (name.contains("ingame_decision") || name.contains("rite_governance") || name.contains("religion_context") || name.contains("holy_site")) return Set.of("hof_terms_confirm_seam");
            return Set.of("shared_sdk_delta");
        }
        if (path.startsWith("tools/ck3_mod_acceptance_cases/")) return name.contains("journey") || name.contains("event") || name.contains("health") || name.contains("interrupt") ? Set.of("case_hooks", "event_policy") : Set.of("case_hooks");
        if (name.startsWith("test_") || path.startsWith("ck3_autonomous_player/tests/")) return Set.of("changed_tests");
        if (path.startsWith("tools/") && (name.startsWith("ck3_mod_acceptance") || name.startsWith("build_normal_exit") || name.startsWith("fixture_engine"))) return Set.of("public_control");
        if (name.equals("recorder_job.py")) return Set.of("recording_control");
        if (path.startsWith("docs/") || path.startsWith("promo/") || name.endsWith(".md") || name.endsWith(".bbcode")) return Set.of();
        return Set.of("other_source_delta");
    }

    private static void validatePrevious(JsonNode value, String machine, Chain chain) throws IOException {
        require(text(value, "machine_id").equals(machine) && text(value, "result").equals("PASS") && integer(value, "tests_run") > 0, "finite same-machine original qualification required");
        zero(value, "exit_code"); zero(value, "skipped"); if (value.has("original_wait_returncode")) zero(value, "original_wait_returncode");
        boolean covered = false; for (JsonNode item : array(value, "covered_chains")) { require(item.isTextual(), "text chain required"); covered |= item.textValue().equals(chain.wire()); } require(covered, "predecessor chain differs");
        if (chain == Chain.PILGRIMAGE_WIRE_SEAM) {
            ArrayNode groups = array(value, "test_groups"); require(groups.size() == 3 && exactInteger(groups.get(0)) >= 20 && exactInteger(groups.get(1)) == 11 && exactInteger(groups.get(2)) == 6 && integer(value, "tests_run") == exactInteger(groups.get(0)) + 17, "original seam groups differ");
            require(array(value, "wrong_SDK_imports").isEmpty() && array(value, "source_or_wire_changed_during_test").isEmpty(), "original seam has source/import drift");
            for (String key : List.of("actual_execution_wire_packets", "actual_readonly4", "actual_wire_consumer14", "actual_current_wire_consumer14")) checked(parsePin(field(value, key)));
        }
        if (chain == Chain.SHARED_HOST) for (String key : List.of("source_consumer", "source_delta", "reviewed_host_change")) checked(parsePin(field(value, key)));
    }
    private static void validateProof(JsonNode value, Proof proof, String machine, Path root) throws IOException {
        require(text(value, "machine_id").equals(machine), "proof belongs to another machine"); zero(value, "exit_code");
        switch (proof.kind()) {
            case COMMAND_VALIDATION, COMMAND_SOURCE_EXECUTION -> {
                require(text(value, "result").equals("PASS") && bool(value, "source_unchanged_during_execution"), "actual unchanged-source command validation required"); zero(value, "skipped");
                ArrayNode commands = array(value, "command_results"); require(!commands.isEmpty() && integer(value, "commands_run") == commands.size(), "complete original command results required");
                for (JsonNode row : commands) { JsonNode command = read(parsePin(row)); require(text(command, "machine_id").equals(machine) && text(command, "result").equals("PASS"), "original command failed"); zero(command, "original_wait_returncode"); zero(command, "skipped"); require(!array(command, "argv").isEmpty(), "actual argv missing"); checked(parsePin(field(command, "log"))); }
                if (proof.kind() == SourceQualificationContracts.ProofKind.COMMAND_SOURCE_EXECUTION) {
                    require(text(value, "schema").equals("ck3-command-source-execution-v1") && text(value, "source_commit").matches("[a-f0-9]{40}")
                            && Set.of("CLEAN_COMMIT", "SCOPED_WORKING_TREE").contains(text(value, "source_identity")), "explicit actual execution source identity required");
                    orderedTimes(value, "started_at_utc", "observed_at_utc");
                    require(sourceRows(value, "source_pins", root, false).equals(sourceRows(value, "source_pins_after", root, false)), "actual source pre/post signatures differ");
                    if (value.has("input_pins") || value.has("input_pins_after")) {
                        ArrayNode before = array(value, "input_pins"), after = array(value, "input_pins_after"); require(before.equals(after), "external input pre/post signatures differ"); for (JsonNode row : before) checked(parsePin(row));
                    }
                    for (JsonNode row : commands) {
                        JsonNode command = read(parsePin(row)); require(integer(command, "pid") > 0 && Path.of(text(command, "cwd")).toAbsolutePath().normalize().equals(root), "original process/CWD identity required");
                        String birth = text(command, "process_create_time_seconds"); require(birth.matches("[0-9]+(?:\\.[0-9]+)?") && new java.math.BigDecimal(birth).signum() > 0, "canonical observed process birth seconds required");
                        orderedTimes(command, "started_at_utc", "finished_at_utc"); if (command.has("exit_code")) zero(command, "exit_code");
                        for (JsonNode arg : array(command, "argv")) require(arg.isTextual(), "text original argv required");
                    }
                }
            }
            case MAVEN_REVIEW -> {
                require(text(value, "status").equals("PASS") && text(value, "command").startsWith("mvn "), "actual default Maven review required");
                validateMaven(value);
                if (value.has("des_builder")) validateMaven(field(value, "des_builder"));
            }
            case SOURCE_REVIEW -> {
                require(text(value, "schema").equals("ck3-source-only-reviewed-scope-v1") && text(value, "result").equals("PASS")
                        && text(value, "scope").equals("UNSELECTED_SOURCE_ONLY") && !bool(value, "execution_qualified"), "explicit source-only review required");
                checked(parsePin(field(value, "previous_knowledge_proof")));
            }
        }
    }
    private static void orderedTimes(JsonNode value, String first, String last) throws IOException {
        try { Instant start = java.time.OffsetDateTime.parse(text(value, first)).toInstant(), end = java.time.OffsetDateTime.parse(text(value, last)).toInstant(); require(!end.isBefore(start) && !end.isAfter(Instant.now()), "actual execution UTC interval differs"); }
        catch (java.time.DateTimeException error) { throw new IOException("timezone-aware actual execution timestamps required", error); }
    }
    private static void validateMaven(JsonNode value) throws IOException {
        require(text(value, "status").equals("PASS"), "Maven review failed"); JsonNode tests = field(value, "tests"); long count = integer(tests, "run"); require(count > 0, "finite Maven count required");
        for (String field : List.of("failures", "errors", "skipped")) zero(tests, field);
        boolean matched = false;
        for (JsonNode row : array(value, "logs")) { Pin pin = parsePin(row); require(pin.bytes() <= 4 * 1024 * 1024, "Maven log exceeds bound"); checked(pin); if (text(row, "status").equals("PASS")) { String log = Files.readString(Path.of(pin.path())); matched |= log.contains("BUILD SUCCESS") && log.contains("Tests run: " + count + ", Failures: 0, Errors: 0, Skipped: 0"); } }
        require(matched, "actual successful Maven log/count missing");
    }
    private static Map<String, Pin> sourceRows(JsonNode value, String key, Path root, boolean relative) throws IOException {
        Map<String, Pin> result = new LinkedHashMap<>();
        for (JsonNode row : array(value, key)) {
            String path = text(row, "path"); Path absolute = relative ? below(root, path) : Path.of(path).toAbsolutePath().normalize();
            require(absolute.startsWith(root), "source proof escaped repository"); String name = root.relativize(absolute).toString().replace('\\', '/'); Contracts.safePath(name);
            Pin pin = new Pin(absolute.toString(), integer(row, "bytes"), text(row, "sha256")); require(result.put(name, pin) == null, "duplicate proof source");
        }
        require(!result.isEmpty() && result.size() <= 10000, "finite source proof required"); return Map.copyOf(result);
    }
    private static Path below(Path root, String relative) throws IOException { Contracts.safePath(relative); Path path = root.resolve(relative).normalize(); require(path.startsWith(root) && !Files.isSymbolicLink(path), "plain source below repository required"); return path; }
    private static boolean isChain(String value) { return java.util.Arrays.stream(Chain.values()).anyMatch(c -> c.wire().equals(value)); }
    private static boolean isCritical(String path) { return path.startsWith(SDK + "xar_autoplayer/bridge/") && CRITICAL.contains(path.substring(path.lastIndexOf('/') + 1)); }
    private static boolean signatureEqual(Pin left, Pin right) { return left.bytes() == right.bytes() && left.sha256().equals(right.sha256()); }
    private static Pin parsePin(JsonNode node) throws IOException { return new Pin(text(node, "path"), integer(node, "bytes"), text(node, "sha256")); }
    private static JsonNode tree(Object value) { return new ObjectMapper().valueToTree(value); }
    private static String hash(byte[] bytes) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); } }
    private static JsonNode read(Pin pin) throws IOException { require(pin.bytes() <= 4 * 1024 * 1024, "JSON proof exceeds bound"); byte[] bytes = Files.readAllBytes(Path.of(pin.path())); require(bytes.length == pin.bytes() && hash(bytes).equals(pin.sha256()), "JSON proof pin changed: " + pin.path()); return Json.read(bytes, JsonNode.class); }
    private static void checked(Pin pin) throws IOException { require(signatureEqual(pin, measure(Path.of(pin.path()))), "proof pin changed: " + pin.path()); }
    private static Pin measure(Path path) throws IOException {
        require(Files.isRegularFile(path) && !Files.isSymbolicLink(path), "ordinary pinned file required: " + path);
        try { MessageDigest digest = MessageDigest.getInstance("SHA-256"); try (var stream = Files.newInputStream(path)) { byte[] buffer = new byte[65536]; int count; while ((count = stream.read(buffer)) >= 0) digest.update(buffer, 0, count); } return new Pin(path.toAbsolutePath().normalize().toString(), Files.size(path), HexFormat.of().formatHex(digest.digest())); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    private static Pin write(Path path, Object value) throws IOException { Files.write(path, Json.write(value), StandardOpenOption.CREATE_NEW); return measure(path); }
    private static ObjectNode object(JsonNode value) throws IOException { require(value.isObject(), "object required"); return (ObjectNode) value; }
    private static JsonNode field(JsonNode value, String name) throws IOException { JsonNode field = value.get(name); require(field != null, "required field: " + name); return field; }
    private static String text(JsonNode value, String name) throws IOException { JsonNode field = field(value, name); require(field.isTextual() && !field.textValue().isEmpty(), "string required: " + name); return field.textValue(); }
    private static ArrayNode array(JsonNode value, String name) throws IOException { JsonNode field = field(value, name); require(field.isArray(), "array required: " + name); return (ArrayNode) field; }
    private static long exactInteger(JsonNode value) throws IOException { require(value.isIntegralNumber() && value.canConvertToLong(), "exact integer required"); return value.longValue(); }
    private static long integer(JsonNode value, String name) throws IOException { return exactInteger(field(value, name)); }
    private static boolean bool(JsonNode value, String name) throws IOException { JsonNode field = field(value, name); require(field.isBoolean(), "boolean required: " + name); return field.booleanValue(); }
    private static void zero(JsonNode value, String name) throws IOException { require(integer(value, name) == 0, "original zero required: " + name); }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
    private static void checkRoot(Path root, String commit) throws IOException { require(git(root, "rev-parse", "HEAD").strip().equals(commit) && git(root, "status", "--porcelain", "--untracked-files=all").isBlank(), "exact clean source HEAD required"); }
    private static String git(Path root, String... arguments) throws IOException {
        List<String> command = new ArrayList<>(List.of("git", "-C", root.toString())); command.addAll(List.of(arguments));
        Path log = Files.createTempFile("rrf-source-git-", ".log");
        try { Process child = new ProcessBuilder(command).redirectErrorStream(true).redirectOutput(log.toFile()).start();
            try { if (!child.waitFor(30, TimeUnit.SECONDS)) { child.destroyForcibly(); child.waitFor(5, TimeUnit.SECONDS); throw new IOException("Git source observation timed out"); } require(child.exitValue() == 0 && Files.size(log) <= 2 * 1024 * 1024, "Git source observation failed/bound exceeded"); return Files.readString(log); }
            catch (InterruptedException error) { child.destroyForcibly(); Thread.currentThread().interrupt(); throw new IOException("Git source observation interrupted", error); }
        } finally { Files.deleteIfExists(log); }
    }
}
