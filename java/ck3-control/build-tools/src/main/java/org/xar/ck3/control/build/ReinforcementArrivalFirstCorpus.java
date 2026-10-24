package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Sole manifest producer/reader for the original seven C++ serializer outputs; no Game qualification. */
public final class ReinforcementArrivalFirstCorpus {
    public static final String SCHEMA = "xar.reinforcement-arrival-first-native-corpus/v1";
    public static final int MAX_MANIFEST_BYTES = 65536;
    public static final int MAX_FILE_BYTES = 1 << 20;
    public static final long PRODUCER_SOURCE_BYTES = 12234;
    public static final String PRODUCER_SOURCE_SHA256 = "eb740cebb51a5db20a17b826ff4bfeb806f90955de2ad4b55f8c7f6f567827ab";
    private static final List<String> CASES = java.util.stream.Stream.of("help_attacker_en_route", "help_defender_en_route",
            "ordinary_last_compatible", "help_retreating_arrived", "help_empty_en_route", "already_participating", "ordinary_no_compatible").sorted().toList();
    private ReinforcementArrivalFirstCorpus() { }
    public record CaseFile(String caseName, FileRef sourceRef) {
        public CaseFile { require(CASES.contains(caseName), "Original FIRST case name required"); Objects.requireNonNull(sourceRef); bounded(sourceRef, MAX_FILE_BYTES); }
    }
    public record Manifest(String schema, String machineId, String observedAtUtc, String corpusRoot,
            FileRef producerSourceRef, FileRef executableRef, FileRef executionRef, List<CaseFile> files) {
        public Manifest {
            require(SCHEMA.equals(schema) && machineId != null && !machineId.isBlank(), "Exact FIRST corpus schema/machine required"); Instant.parse(observedAtUtc); absolute(corpusRoot);
            bounded(producerSourceRef, 2L << 20); bounded(executableRef, 64L << 20); bounded(executionRef, 2L << 20);
            require(producerSourceRef.bytes() == PRODUCER_SOURCE_BYTES && producerSourceRef.sha256().equals(PRODUCER_SOURCE_SHA256), "FIRST v1 requires its exact original C++ producer body");
            files = List.copyOf(files); require(files.stream().map(CaseFile::caseName).toList().equals(CASES), "Complete ordered original seven FIRST cases required");
            for (CaseFile file : files) require(absolute(file.sourceRef().path()).equals(absolute(corpusRoot).resolve(file.caseName() + ".json")), "FIRST file path crossed its exact original case");
        }
    }
    /** Arguments are exact source, executable and actual terminal path/bytes/SHA, followed by fresh output. */
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 11) throw new IllegalArgumentException("corpus-root cpp-source bytes sha executable bytes sha actual-terminal bytes sha fresh-manifest");
        FileRef source = argument(arguments, 1), executable = argument(arguments, 4), terminal = argument(arguments, 7);
        FileRef result = produce(Path.of(arguments[0]), source, executable, terminal, Path.of(arguments[10]));
        System.out.println("WROTE_FIRST7_CORPUS_MANIFEST " + ControlBuild.strictMapper().writeValueAsString(result));
    }
    public static FileRef produce(Path corpusRoot, FileRef source, FileRef executable, FileRef execution, Path output) throws IOException {
        Path root = directory(corpusRoot); var files = new ArrayList<CaseFile>();
        for (String name : CASES) files.add(new CaseFile(name, actual(root.resolve(name + ".json"), MAX_FILE_BYTES)));
        Manifest manifest = new Manifest(SCHEMA, WindowsJobProcess.currentMachineId(), Instant.now().toString(), root.toString(), source, executable, execution, files);
        validate(manifest, true); Path target = absolute(output.toString());
        require(!target.startsWith(root), "The manifest must be outside the complete untouched original corpus"); SharedSourceFiles.plainAncestors(target);
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(manifest); require(raw.length <= MAX_MANIFEST_BYTES, "Finite FIRST manifest required");
        Files.write(target, raw, StandardOpenOption.CREATE_NEW); FileRef result = FileRef.measure(target);
        require(manifest.equals(require(result, root.toString())), "Actual FIRST manifest producer/read roundtrip differs"); return result;
    }
    public static Manifest readManifest(FileRef source) throws IOException {
        bounded(source, MAX_MANIFEST_BYTES); source.verify();
        Manifest result = ControlBuild.strictMapper().readValue(Files.readAllBytes(absolute(source.path())), Manifest.class); source.verify(); return result;
    }
    public static Manifest require(FileRef manifestRef, String expectedRoot) throws IOException {
        Manifest manifest = readManifest(manifestRef);
        require(absolute(manifest.corpusRoot()).equals(absolute(expectedRoot)) && !absolute(manifestRef.path()).startsWith(absolute(expectedRoot)), "Exact selected FIRST root and external manifest required");
        validate(manifest, false); manifestRef.verify(); return manifest;
    }
    private static void validate(Manifest manifest, boolean liveProducer) throws IOException {
        require(manifest.machineId().equals(WindowsJobProcess.currentMachineId()), "FIRST input belongs to another execution machine");
        Path root = directory(Path.of(manifest.corpusRoot())); Set<Path> expected = new HashSet<>(); long total = 0;
        for (CaseFile file : manifest.files()) {
            FileRef ref = file.sourceRef(); expected.add(absolute(ref.path())); total = Math.addExact(total, ref.bytes());
            require(total <= 7L << 20, "Finite complete FIRST corpus bytes required"); byte[] raw = read(ref, MAX_FILE_BYTES);
            JsonNode wire = ControlBuild.strictMapper().readTree(raw);
            exact(wire, Set.of("case_name", "fixture", "hello", "semantic_snapshot", "result"));
            require(wire.path("case_name").isTextual() && file.caseName().equals(wire.path("case_name").textValue()), "Original FIRST case body differs from its exact filename");
            JsonNode metadata = wire.get("fixture"); exact(metadata, Set.of("synthetic", "source_baseline", "integration_baseline", "game_version", "exe_sha256"));
            require(metadata.get("synthetic").isBoolean() && metadata.get("synthetic").booleanValue()
                    && "df87fd85".equals(metadata.path("source_baseline").textValue())
                    && "be06a134b9a5472275e08ea452a8e3542b192fb8".equals(metadata.path("integration_baseline").textValue()),
                    "Original serializer fixture metadata required");
            require("1.20.0.3".equals(metadata.path("game_version").textValue())
                    && "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6".equals(metadata.path("exe_sha256").textValue()) && wire.path("result").isObject()
                    && wire.path("result").path("battle_reinforcement_assignment").isObject(), "Original FIRST whole assignment frame required");
        }
        Set<Path> actual = new HashSet<>();
        try (var entries = Files.list(root)) { for (Path path : entries.toList()) {
            SharedSourceFiles.plainAncestors(path); require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && path.toRealPath().equals(path), "No FIRST links, directories or extra entries allowed"); actual.add(path);
        } }
        require(actual.equals(expected), "Complete FIRST directory differs from its exact seven original files");
        manifest.producerSourceRef().verify(); manifest.executableRef().verify();
        require(absolute(manifest.producerSourceRef().path()).getFileName().toString().equals("battle_reinforcement_arrival_first_12003.cpp"), "Exact original FIRST C++ producer source required");
        var terminal = ControlBuild.strictMapper().readValue(read(manifest.executionRef(), 2 << 20), SharedOwnedCommand.Terminal.class);
        require("xar.shared-owned-command-terminal/v2".equals(terminal.schema()) && terminal.machineId().equals(manifest.machineId())
                && terminal.status() == SharedOwnedCommand.Status.PASS && terminal.childStarted() && terminal.child() != null && terminal.child().passed()
                && terminal.failure() == null && terminal.inputPrecheck() == SharedOwnedCommand.Check.MATCH && terminal.inputPostcheck() == SharedOwnedCommand.Check.MATCH
                && terminal.runtimePostcheck() == SharedOwnedCommand.Check.MATCH && terminal.gameRpcCalls() == 0 && terminal.actualDriverOrSaveBodyReads() == 0, "Actual unchanged successful FIRST child and settled Job required");
        require(terminal.completeRuntime().size() == 6 && new HashSet<>(terminal.completeRuntime()).size() == 6, "Complete recorded six-piece executing runtime required");
        for (FileRef ref : terminal.completeRuntime()) ref.verify();
        if (liveProducer) {
            var runtime = ControlBuild.producerClosure(); require(runtime.size() == 6, "Complete actual manifest-publisher runtime required");
            for (FileRef ref : runtime) ref.verify();
        }
        terminal.requestRef().verify(); var request = SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(read(terminal.requestRef(), 1 << 20)));
        NativeFixtureCorpora.requireSettledOwnedProcess(manifest.machineId(), terminal, request);
        require(request.executable().equals(manifest.executableRef()) && request.arguments().size() == 1 && absolute(request.arguments().getFirst()).equals(root)
                && terminal.effectiveArguments().equals(request.arguments()) && request.inputs().contains(manifest.producerSourceRef()), "FIRST execution changed its actual executable, original source or sole output-directory argument");
        for (FileRef ref : request.inputs()) ref.verify();
        for (FileRef ref : List.of(manifest.producerSourceRef(), manifest.executableRef())) require(terminal.inputBefore().stream().anyMatch(before -> before.source().equals(ref)), "FIRST execution lacks the actual prechecked source/executable witness");
        require(terminal.stdoutRef() != null && terminal.stderrRef() != null && terminal.stdoutRef().bytes() <= MAX_FILE_BYTES && terminal.stderrRef().bytes() <= MAX_FILE_BYTES, "Finite original FIRST stdout/stderr required");
        terminal.stdoutRef().verify(); terminal.stderrRef().verify(); manifest.executionRef().verify();
        for (CaseFile file : manifest.files()) file.sourceRef().verify();
    }
    private static FileRef argument(String[] values, int index) { require(values[index + 1].matches("[1-9][0-9]{0,8}"), "Exact positive source bytes required"); return new FileRef(values[index], Long.parseLong(values[index + 1]), values[index + 2]); }
    private static byte[] read(FileRef ref, int maximum) throws IOException { bounded(ref, maximum); SharedSourceFiles.plainAncestors(absolute(ref.path())); ref.verify(); byte[] raw = Files.readAllBytes(absolute(ref.path())); ref.verify(); require(raw.length == ref.bytes(), "Original FIRST bytes changed during read"); return raw; }
    private static FileRef actual(Path path, long maximum) throws IOException { SharedSourceFiles.plainAncestors(path); require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && path.toRealPath().equals(path), "Plain actual FIRST file required"); FileRef ref = FileRef.measure(path); bounded(ref, maximum); return ref; }
    private static Path directory(Path value) throws IOException { Path root = absolute(value.toString()); SharedSourceFiles.plainAncestors(root); require(Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS) && root.toRealPath().equals(root), "Plain canonical actual FIRST root required"); return root; }
    private static Path absolute(String value) { require(value != null && value.length() <= 4096 && value.chars().noneMatch(c -> c < 32 || c == 127), "Bounded FIRST path required"); Path result = Path.of(value); require(result.isAbsolute() && result.equals(result.normalize()), "Canonical absolute FIRST path required"); return result; }
    private static void bounded(FileRef ref, long maximum) { Objects.requireNonNull(ref); absolute(ref.path()); require(ref.bytes() > 0 && ref.bytes() <= maximum, "Finite exact FIRST role required"); }
    private static void exact(JsonNode node, Set<String> fields) { require(node != null && node.isObject() && node.size() == fields.size(), "Exact original FIRST envelope fields required"); for (String field : fields) require(node.has(field), "Missing original FIRST field: " + field); }
    private static void require(boolean value, String reason) { if (!value) throw new IllegalArgumentException(reason); }
}
