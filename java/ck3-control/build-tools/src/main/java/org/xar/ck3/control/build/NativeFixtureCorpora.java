package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Publishes metadata from actual owned C++ outputs. It never constructs or re-encodes native packets. */
public final class NativeFixtureCorpora {
    public static final String REQUEST_SCHEMA = "xar.full-parity-native-fixture-publication-request/v1";
    public static final String PROOF_SCHEMA = "xar.full-parity-native-fixture-production/v1";
    public static final int MAX_BYTES = 1 << 20;
    public enum Kind { MANAGERS, HOLY_ORDER, HOLY_LOAN }
    public record Run(String target, FileRef sourceRef, FileRef executableRef, FileRef terminalRef, FileRef outputRef) {
        public Run {
            require(target != null && target.matches("[a-z0-9_]{1,128}"), "Exact native producer target required");
            bounded(sourceRef, 2L << 20); bounded(executableRef, 64L << 20); bounded(terminalRef, 2L << 20); bounded(outputRef, MAX_BYTES);
        }
    }
    public record Request(String schema, String machineId, Kind kind, FileRef sourceMapRef,
            FileRef nativeEnvironmentRef, FileRef nativeSourceSnapshotRef, List<Run> runs) {
        public Request {
            require(REQUEST_SCHEMA.equals(schema) && machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{0,63}") && !machineId.equals("unknown"), "Exact source publication machine/schema required");
            Objects.requireNonNull(kind); bounded(sourceMapRef, MAX_BYTES); bounded(nativeEnvironmentRef, 4L << 20); bounded(nativeSourceSnapshotRef, 8L << 20);
            runs = List.copyOf(runs); require(runs.stream().map(Run::target).toList().equals(targets(kind)), "Complete ordered native target set required");
        }
    }
    public record Production(String schema, Kind kind, FileRef artifactRef, FileRef requestRef, List<FileRef> normalizedReceipts) {
        public Production { require(PROOF_SCHEMA.equals(schema), "Exact native publication proof required"); Objects.requireNonNull(kind); bounded(artifactRef, MAX_BYTES); bounded(requestRef, MAX_BYTES); normalizedReceipts = List.copyOf(normalizedReceipts); }
    }
    public record Fixture(String kind, String container, FileRef sourceRef) { }
    public record Managers(int schemaVersion, String machineId, List<Fixture> fixtures) { }
    public record ProcessReceipt(String schema, String machineId, String target, FileRef executableRef,
            int exitCode, boolean timedOut, int actualGameActions, FileRef originalTerminalRef, FileRef sourceRef, FileRef outputRef) { }
    public record HolyRun(String target, FileRef sourceRef, FileRef executableRef, FileRef receiptRef, FileRef outputRef) { }
    public record Holy(String schema, String machineId, FileRef sourceMapRef, FileRef nativeEnvironmentRef, FileRef nativeSourceSnapshotRef, List<HolyRun> runs) { }
    private static final List<String> MANAGERS = List.of("xar_bridge_ck3_12003_army_condition30_inputs_test", "xar_bridge_ck3_12003_army_flag20_inputs_test", "xar_bridge_ck3_12003_army_flag21_inputs_test", "xar_bridge_ck3_12003_selected_title_holder_owner_relation_test", "xar_bridge_ck3_12003_army_flag31_inputs_test");
    private static final List<String> HOLY = List.of("xar_ck3_12003_holy_order_war_eligibility_test", "xar_ck3_12003_holy_order_service_lifecycle_test", "xar_ck3_12003_holy_order_troop_association_test", "xar_ck3_12003_holy_order_hire_cost_context_test", "xar_ck3_12003_holy_order_current_reinforcement_test");
    private static final List<String> KINDS = List.of("CONDITION30", "FLAG20", "FLAG21", "HOLDER_RELATION", "FLAG31");
    private static final List<Integer> SAMPLES = List.of(9, 6, 9, 10, 7);
    private NativeFixtureCorpora() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 4 || !arguments[1].matches("[1-9][0-9]{0,8}")) throw new IllegalArgumentException("publication-request-path bytes sha fresh-artifact-path");
        FileRef result = produce(new FileRef(arguments[0], Long.parseLong(arguments[1]), arguments[2]), Path.of(arguments[3]));
        System.out.println("WROTE_NATIVE_FIXTURE_CORPUS " + ControlBuild.strictMapper().writeValueAsString(result));
    }
    public static FileRef produce(FileRef requestRef, Path output) throws IOException {
        Request request = readRequest(requestRef); validate(request); Path artifact = absolute(output.toString());
        SharedSourceFiles.plainAncestors(artifact); require(!Files.exists(artifact) && !Files.exists(proofPath(artifact)), "Fresh corpus and production proof required");
        var receipts = new ArrayList<FileRef>(); var holy = new ArrayList<HolyRun>(); var managers = new ArrayList<Fixture>();
        for (int i = 0; i < request.runs().size(); i++) {
            Run run = request.runs().get(i); Path receipt = artifact.resolveSibling(artifact.getFileName() + ".run-" + i + ".json");
            receipts.add(write(receipt, new ProcessReceipt("xar.native-fixture-owned-process/v1", request.machineId(), run.target(), run.executableRef(), 0, false, 0, run.terminalRef(), run.sourceRef(), run.outputRef())));
            holy.add(new HolyRun(run.target(), run.sourceRef(), run.executableRef(), receipts.getLast(), run.outputRef()));
            if (request.kind() == Kind.MANAGERS) managers.add(new Fixture(KINDS.get(i), i == 0 ? "LEAF_SAMPLES_V1" : "WHOLE_QUERY_SAMPLES_V1", run.outputRef()));
        }
        FileRef result;
        if (request.kind() == Kind.MANAGERS) result = write(artifact, new Managers(1, request.machineId(), managers));
        else if (request.kind() == Kind.HOLY_ORDER) result = write(artifact, new Holy("xar.ck3.holy-order-native-fixture-corpus/v1", request.machineId(), request.sourceMapRef(), request.nativeEnvironmentRef(), request.nativeSourceSnapshotRef(), holy));
        else { byte[] original = read(request.runs().getFirst().outputRef(), MAX_BYTES); Files.write(artifact, original, StandardOpenOption.CREATE_NEW); result = FileRef.measure(artifact); }
        Production production = new Production(PROOF_SCHEMA, request.kind(), result, requestRef, receipts); FileRef proof = write(proofPath(artifact), production);
        requireProduction(proof, result, request.kind(), request.sourceMapRef()); return result;
    }
    public static Path proofPath(Path artifact) { return artifact.resolveSibling(artifact.getFileName() + ".production.json"); }
    public static Production requireProduction(FileRef proofRef, FileRef artifactRef, Kind kind, FileRef sourceMapRef) throws IOException {
        Production proof = readProduction(proofRef);
        require(proof.artifactRef().equals(artifactRef) && proof.kind() == kind && absolute(proofRef.path()).equals(proofPath(absolute(artifactRef.path()))), "Corpus production proof crossed its exact artifact/role");
        Request request = readRequest(proof.requestRef()); require(request.kind() == kind && request.sourceMapRef().equals(sourceMapRef), "Corpus proof crossed its exact source contract"); validate(request);
        require(proof.normalizedReceipts().size() == request.runs().size(), "Every native run needs its original terminal-derived receipt");
        for (int i = 0; i < request.runs().size(); i++) {
            Run run = request.runs().get(i); ProcessReceipt actual = ControlBuild.strictMapper().readValue(read(proof.normalizedReceipts().get(i), MAX_BYTES), ProcessReceipt.class);
            require(actual.equals(new ProcessReceipt("xar.native-fixture-owned-process/v1", request.machineId(), run.target(), run.executableRef(), 0, false, 0, run.terminalRef(), run.sourceRef(), run.outputRef())), "Normalized native receipt differs from its actual successful owned process");
        }
        byte[] raw = read(artifactRef, MAX_BYTES);
        if (kind == Kind.MANAGERS) {
            var rows = new ArrayList<Fixture>(); for (int i = 0; i < 5; i++) rows.add(new Fixture(KINDS.get(i), i == 0 ? "LEAF_SAMPLES_V1" : "WHOLE_QUERY_SAMPLES_V1", request.runs().get(i).outputRef()));
            require(new Managers(1, request.machineId(), rows).equals(ControlBuild.strictMapper().readValue(raw, Managers.class)), "Actual manager manifest differs from its original five outputs");
        } else if (kind == Kind.HOLY_ORDER) {
            var rows = new ArrayList<HolyRun>(); for (int i = 0; i < 5; i++) { Run run = request.runs().get(i); rows.add(new HolyRun(run.target(), run.sourceRef(), run.executableRef(), proof.normalizedReceipts().get(i), run.outputRef())); }
            require(new Holy("xar.ck3.holy-order-native-fixture-corpus/v1", request.machineId(), sourceMapRef, request.nativeEnvironmentRef(), request.nativeSourceSnapshotRef(), rows).equals(ControlBuild.strictMapper().readValue(raw, Holy.class)), "Actual Holy corpus differs from its original five runs");
        } else require(java.util.Arrays.equals(raw, read(request.runs().getFirst().outputRef(), MAX_BYTES)), "Loan golden changed the exact original native stdout bytes");
        proofRef.verify(); return proof;
    }
    public static Request readRequest(FileRef reference) throws IOException { return ControlBuild.strictMapper().readValue(read(reference, MAX_BYTES), Request.class); }
    public static Production readProduction(FileRef reference) throws IOException { return ControlBuild.strictMapper().readValue(read(reference, MAX_BYTES), Production.class); }
    private static void validate(Request request) throws IOException {
        require(request.machineId().equals(WindowsJobProcess.currentMachineId()), "Native publication belongs to another execution machine");
        JsonNode map = ControlBuild.strictMapper().readTree(read(request.sourceMapRef(), MAX_BYTES)); request.nativeEnvironmentRef().verify(); request.nativeSourceSnapshotRef().verify();
        for (int i = 0; i < request.runs().size(); i++) {
            Run run = request.runs().get(i); require(containsRef(map, run.sourceRef()), "Actual native source is absent from its exact selected source contract");
            successful(request.machineId(), run, arguments(request.kind(), run)); JsonNode original = ControlBuild.strictMapper().readTree(read(run.outputRef(), MAX_BYTES));
            if (request.kind() == Kind.MANAGERS) require(original.isObject() && original.size() == 1 && original.path("samples").isObject() && original.get("samples").size() == SAMPLES.get(i), "Complete original manager serializer sample set required");
            else if (request.kind() == Kind.HOLY_ORDER) require(original.isObject() && original.path("samples").isArray() && !original.get("samples").isEmpty() && original.get("samples").size() <= 256, "Complete original Holy native packet samples required");
            else require(original.isObject() && original.size() == 2 && "xar.holy-loan-source-native-producer-golden.v1".equals(original.path("schema").textValue()) && original.path("rows").isArray() && original.get("rows").size() == 18, "Exact original eighteen-row native loan producer golden required");
        }
    }
    private static void successful(String machine, Run run, List<String> expectedArguments) throws IOException {
        run.sourceRef().verify(); run.executableRef().verify();
        var terminal = ControlBuild.strictMapper().readValue(read(run.terminalRef(), 2 << 20), SharedOwnedCommand.Terminal.class);
        require("xar.shared-owned-command-terminal/v2".equals(terminal.schema()) && machine.equals(terminal.machineId()) && terminal.status() == SharedOwnedCommand.Status.PASS
                && terminal.childStarted() && terminal.child() != null && terminal.child().passed() && terminal.failure() == null
                && terminal.inputPrecheck() == SharedOwnedCommand.Check.MATCH && terminal.inputPostcheck() == SharedOwnedCommand.Check.MATCH && terminal.runtimePostcheck() == SharedOwnedCommand.Check.MATCH
                && terminal.gameRpcCalls() == 0 && terminal.actualDriverOrSaveBodyReads() == 0 && terminal.completeRuntime().size() == 6 && new HashSet<>(terminal.completeRuntime()).size() == 6, "Actual successful settled native Job and unchanged source/runtime required");
        for (FileRef ref : terminal.completeRuntime()) ref.verify();
        var command = SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(read(terminal.requestRef(), MAX_BYTES)));
        requireSettledOwnedProcess(machine, terminal, command);
        require(command.executable().equals(run.executableRef()) && command.arguments().equals(expectedArguments) && terminal.effectiveArguments().equals(expectedArguments)
                && command.inputs().contains(run.sourceRef()) && absolute(run.outputRef().path()).startsWith(command.outputRoot()), "Native run crossed its original executable/source/argv/output role");
        for (FileRef ref : command.inputs()) ref.verify();
        for (FileRef ref : List.of(run.sourceRef(), run.executableRef())) require(terminal.inputBefore().stream().anyMatch(value -> value.source().equals(ref)), "Native terminal lacks the actual source/executable prechecked witness");
        if (expectedArguments.equals(List.of("emit"))) require(run.outputRef().equals(terminal.stdoutRef()), "Loan emit golden must be the actual original child stdout");
        bounded(terminal.stdoutRef(), MAX_BYTES); bounded(terminal.stderrRef(), MAX_BYTES); terminal.stdoutRef().verify(); terminal.stderrRef().verify(); run.terminalRef().verify(); run.outputRef().verify();
    }
    /** The v2 shared caller records an outer reservation and a real child-and-descendants Job. */
    static void requireSettledOwnedProcess(String machine, SharedOwnedCommand.Terminal terminal,
            SharedOwnedCommand.Request command) {
        require("xar.shared-owned-command-terminal/v2".equals(terminal.schema())
                && machine.equals(terminal.machineId()) && machine.equals(command.machineId())
                && terminal.status() == SharedOwnedCommand.Status.PASS && terminal.childStarted()
                && terminal.child() != null && terminal.child().passed() && terminal.failure() == null,
                "Successful original child and descendants must have a settled hard Job");
        var outer = terminal.outer();
        require(outer != null && !outer.hardJobEnforced() && outer.reservedMemoryBytes() == (256L << 20)
                && outer.pidDecimal() != null && outer.pidDecimal().matches("[1-9][0-9]{0,9}"),
                "Shared v2 outer is the original 256MiB reservation; no outer hard Job is claimed");
        require(terminal.owner().equals(command.owner()) && terminal.slotId().equals(command.slotId())
                && Objects.equals(terminal.borrowedSlotId(), command.borrowedSlotId())
                && terminal.standingRef().equals(command.standingRef())
                && terminal.launcherSourceRef().equals(command.launcherSourceRef())
                && absolute(terminal.child().identity().executable()).equals(absolute(command.executable().path()))
                && terminal.child().accounting().memoryLimitBytes() == command.memoryLimitBytes(),
                "Actual child image, Job memory and owner/slot/authority must match its original request");
        // CommandResult.passed checks exit0, no stop reason, activeProcesses0, peak<=limit and REQUIRED_FLAGS.
    }
    private static List<String> arguments(Kind kind, Run run) { return switch (kind) {
        case MANAGERS -> List.of("--wire-dir", absolute(run.outputRef().path()).getParent().toString());
        case HOLY_ORDER -> List.of(run.outputRef().path());
        case HOLY_LOAN -> List.of("emit");
    }; }
    private static List<String> targets(Kind kind) { return switch (kind) { case MANAGERS -> MANAGERS; case HOLY_ORDER -> HOLY; case HOLY_LOAN -> List.of("xar_ck3_12004_holy_loan_source_fixture"); }; }
    private static boolean containsRef(JsonNode value, FileRef ref) {
        if (value.isObject() && value.size() == 3 && value.has("path") && value.has("bytes") && value.has("sha256")) {
            try { if (ControlBuild.strictMapper().treeToValue(value, FileRef.class).equals(ref)) return true; } catch (IOException invalid) { return false; }
        }
        if (value.isContainerNode()) for (JsonNode child : value) if (containsRef(child, ref)) return true; return false;
    }
    private static FileRef write(Path path, Object value) throws IOException { SharedSourceFiles.plainAncestors(path); byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(value); require(raw.length > 0 && raw.length <= MAX_BYTES, "Finite native publication metadata required"); Files.write(path, raw, StandardOpenOption.CREATE_NEW); return FileRef.measure(path); }
    private static byte[] read(FileRef ref, int maximum) throws IOException { bounded(ref, maximum); SharedSourceFiles.plainAncestors(absolute(ref.path())); ref.verify(); byte[] raw = Files.readAllBytes(absolute(ref.path())); require(raw.length == ref.bytes(), "Native publication original changed bytes"); ref.verify(); return raw; }
    private static void bounded(FileRef ref, long maximum) { Objects.requireNonNull(ref); absolute(ref.path()); require(ref.bytes() > 0 && ref.bytes() <= maximum, "Finite actual native publication role required"); }
    private static Path absolute(String text) { require(text != null && text.length() <= 4096 && text.chars().noneMatch(c -> c < 32 || c == 127), "Plain native publication path required"); Path path = Path.of(text); require(path.isAbsolute() && path.equals(path.normalize()), "Canonical absolute native publication path required"); return path; }
    private static void require(boolean value, String reason) { if (!value) throw new IllegalArgumentException(reason); }
}
