package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.regex.Pattern;

/**
 * Finite diagnostic test-compile of the complete R2 reactor through existing shared producer APIs.
 * Never a ControlBuild accepted/capture receipt; test bodies and Full35/SDK/Game remain unexecuted.
 */
public final class Full35CompileOnly {
    private Full35CompileOnly() { }
    public static final String REQUEST_SCHEMA = "xar.full35-compile-only-request/v1";
    public static final String RECEIPT_SCHEMA = "xar.full35-compile-only-actual/v1";
    private static final int REQUEST_MAX = 1 << 20, RECEIPT_MAX = 4 << 20, COMPILATION_MAX = 8 << 20;
    private static final ControlBuild.SourceLimitProfile PROFILE =
            ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2;
    private static final ControlBuild.InventoryIo INVENTORY = new ControlBuild.InventoryIo() { };
    public enum State { COMPILED_NOT_TESTED, COMPILE_RED }
    public enum Tests { NOT_TESTED }
    public enum Scope { COMPILER_DIAGNOSTIC_ONLY_NOT_FULL35_SDK_HOST_OR_GAME_QUALIFICATION }

    public record Request(String schema, String machineId, String ownerTask,
            ControlBuild.FileRef planRef, ControlBuild.FileRef qualifiedToolsRef,
            List<ControlBuild.FileRef> expectedRuntime, String sourceRoot, String workRoot,
            ControlBuild.FileRef capacityReleaseRef, String attempt, String javaHome, int timeoutSeconds) {
        public Request {
            if (!REQUEST_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
                    || !"/root".equals(ownerTask) || planRef == null || qualifiedToolsRef == null
                    || capacityReleaseRef == null || attempt == null
                    || !attempt.matches("[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}")
                    || timeoutSeconds < 1 || timeoutSeconds > 900)
                throw new IllegalArgumentException("Exact Root-owned finite compiler request required");
            absolute(sourceRoot); absolute(workRoot); absolute(javaHome);
            expectedRuntime = List.copyOf(expectedRuntime);
            if (expectedRuntime.size() != 6) throw new IllegalArgumentException("Exact qualified six-file tool archive required");
        }
    }
    private record Lease(Instant review, Map<String, Long> caps, long memory, long heap,
            Map<Path, Long> minimumFree) { }
    public record ReactorSummary(String project, String outcome) { }
    public record Actual(String schema, String machineId, String observedAtUtc, Scope scope,
            State state, Tests tests, ControlBuild.FileRef requestRef, ControlBuild.FileRef planRef,
            ControlBuild.FileRef qualifiedToolsRef, ControlBuild.FileRef capacityReleaseRef,
            ControlBuild.SourceLimitProfile sourceLimitProfile, int expectedReactorProjects,
            List<ReactorSummary> actualReactorSummary, String sourceRoot, String compiledSourceRoot,
            String buildRoot, ControlBuild.SourcePostcheck sourcePostcheck,
            ControlBuild.SourcePostcheck compiledSourcePostcheck, List<ControlBuild.FileRef> sourcePins,
            List<ControlBuild.FileRef> compiledSourcePins, List<ControlBuild.FileRef> completeToolRuntime,
            ControlBuild.MavenToolchain mavenToolchain, ControlBuild.FileRef javaExecutableRef,
            WindowsJobProcess.CommandResult versionResult, WindowsJobProcess.CommandResult compileResult,
            List<String> mavenArguments, List<ControlBuild.FileRef> commandAndLogRefs,
            ControlBuild.FileRef testCompilationManifestRef, Map<String, Long> finalLogicalBytesByPart,
            String error) {
        public Actual {
            actualReactorSummary = List.copyOf(actualReactorSummary); sourcePins = List.copyOf(sourcePins);
            compiledSourcePins = List.copyOf(compiledSourcePins); completeToolRuntime = List.copyOf(completeToolRuntime);
            mavenArguments = List.copyOf(mavenArguments); commandAndLogRefs = List.copyOf(commandAndLogRefs);
            finalLogicalBytesByPart = Map.copyOf(finalLogicalBytesByPart);
            if (!RECEIPT_SCHEMA.equals(schema) || tests != Tests.NOT_TESTED
                    || scope != Scope.COMPILER_DIAGNOSTIC_ONLY_NOT_FULL35_SDK_HOST_OR_GAME_QUALIFICATION)
                throw new IllegalArgumentException("Compiler-only result must never grant test or application qualification");
            if (state == State.COMPILED_NOT_TESTED && (error != null || compileResult == null
                    || !compileResult.passed() || actualReactorSummary.size() != 35
                    || actualReactorSummary.stream().anyMatch(row -> !row.outcome().equals("SUCCESS"))
                    || sourcePostcheck.state() != ControlBuild.SourceState.MATCH
                    || compiledSourcePostcheck.state() != ControlBuild.SourceState.MATCH
                    || testCompilationManifestRef == null))
                throw new IllegalArgumentException("Complete compiler terminal and provenance are required");
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IOException("request-path exact-bytes exact-sha256 required");
        var requestRef = new ControlBuild.FileRef(args[0], Long.parseLong(args[1]), args[2]);
        requestRef.verify();
        Request request = ControlBuild.strictMapper().readValue(read(requestRef, REQUEST_MAX), Request.class);
        Actual result = execute(requestRef, request);
        System.out.println("full35_compile=" + result.state() + ";tests=NOT_TESTED;projects="
                + result.actualReactorSummary().size() + ";scope=" + result.scope());
        if (result.state() != State.COMPILED_NOT_TESTED) System.exit(1);
    }

    public static Actual execute(ControlBuild.FileRef requestRef, Request request) throws Exception {
        String machine = WindowsJobProcess.currentMachineId();
        if (!machine.equals(request.machineId())) throw new IOException("Current execution machine differs");
        requestRef.verify(); request.planRef().verify(); request.qualifiedToolsRef().verify();
        request.capacityReleaseRef().verify();
        var runtime = ControlBuild.producerClosure();
        var expected = new ArrayList<>(request.expectedRuntime());
        expected.sort(Comparator.comparing(ControlBuild.FileRef::path));
        if (!runtime.equals(expected)) throw new IOException("Mixed or unqualified compile helper dependency archive");
        JsonNode delivery = ControlBuild.strictMapper().readTree(read(request.qualifiedToolsRef(), 1 << 20));
        if (!machine.equals(delivery.path("machine_id").textValue())
                || !"WHOLE_MAVEN_AND_OWN_ARCHIVE_ACCEPTED_SOFTWARE_ONLY".equals(delivery.path("status").textValue()))
            throw new IOException("Actual software-only qualified tool delivery required");
        List<ControlBuild.FileRef> delivered = new ArrayList<>();
        for (JsonNode node : delivery.required("complete_deployment"))
            delivered.add(ControlBuild.strictMapper().treeToValue(node, ControlBuild.FileRef.class));
        delivered.sort(Comparator.comparing(ControlBuild.FileRef::path));
        if (!runtime.equals(delivered)) throw new IOException("Running tools differ from exact qualified delivery");
        for (var ref : runtime) ref.verify();
        var plan = CompleteSourceGraph.readPlan(request.planRef());
        if (!machine.equals(plan.machineId()) || plan.profile() != CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R2
                || plan.modules().size() != 34) throw new IOException("Actual R2 34-child/35-project plan required");
        Path source = absolute(request.sourceRoot()), work = absolute(request.workRoot());
        CompleteSourceGraph.verifyMaterialized(plan, source);
        var config = new ControlBuild.Config(source, work, Path.of(request.capacityReleaseRef().path()),
                request.attempt(), request.ownerTask(), null, absolute(request.javaHome()), "3.10.0",
                request.timeoutSeconds(), ControlBuild.TargetKind.SERVICE_FAST_JAR, PROFILE);
        ControlBuild.readLeaseAt(config, machine, Instant.now()); // Existing shared policy/volume/root/owner validation.
        Lease lease = lease(config, request.capacityReleaseRef());
        Path logs = work.resolve("logs"), snapshot = work.resolve("scratch/source-" + request.attempt());
        Path build = work.resolve("build/" + request.attempt());
        Path resultPath = logs.resolve("build-" + request.attempt() + "-compile-only.json");
        if (Files.exists(snapshot) || Files.exists(build) || Files.exists(resultPath))
            throw new IOException("Fresh compiler attempt required; original failed attempts remain immutable");
        Files.createDirectories(logs);
        try (FileChannel channel = FileChannel.open(work.resolve(".java-control-build.lock"),
                StandardOpenOption.CREATE, StandardOpenOption.WRITE); FileLock lock = channel.tryLock()) {
            if (lock == null || !lock.isValid()) throw new IOException("Another Maven writer owns the shared workpackage");
            long end = Math.addExact(System.nanoTime(), Duration.ofSeconds(request.timeoutSeconds()).toNanos());
            guard(config, lease, end);
            List<ControlBuild.FileRef> sources = ControlBuild.sourceManifest(source, PROFILE), compiled = new ArrayList<>();
            Files.createDirectories(snapshot); Files.createDirectories(build);
            for (var original : sources) {
                original.verify(); Path target = snapshot.resolve(source.relativize(Path.of(original.path()))).normalize();
                if (!target.startsWith(snapshot)) throw new IOException("Compiler snapshot escaped");
                Files.createDirectories(target.getParent()); Files.copy(Path.of(original.path()), target);
                var copy = ControlBuild.FileRef.measure(target);
                if (copy.bytes() != original.bytes() || !copy.sha256().equals(original.sha256()))
                    throw new IOException("Compiler snapshot bytes differ");
                original.verify(); compiled.add(copy);
            }
            if (ControlBuild.postcheckSource(snapshot, compiled, PROFILE).state() != ControlBuild.SourceState.MATCH)
                throw new IOException("Exact full compiler snapshot required");
            Path settings = logs.resolve("build-" + request.attempt() + "-settings.xml");
            Files.writeString(settings, "<?xml version=\"1.0\"?><settings xmlns=\"http://maven.apache.org/SETTINGS/1.2.0\"><interactiveMode>false</interactiveMode></settings>",
                    StandardOpenOption.CREATE_NEW);
            Map<String, String> environment = environment(config, snapshot, lease);
            List<String> arguments = List.of("--fail-at-end", "-B", "-ntp", "-e",
                    "-s", settings.toString(), "-gs", settings.toString(), "-f", snapshot.resolve("pom.xml").toString(),
                    "-Dmaven.repo.local=" + work.resolve("m2"), "-Dck3.build.root=" + build,
                    "-Djava.io.tmpdir=" + work.resolve("scratch"), "-Dmaven.test.skip=false", "-DskipTests=true", "test-compile");
            WindowsJobProcess.CommandResult version = null, command = null;
            ControlBuild.MavenToolchain toolchain = null; ControlBuild.FileRef compilation = null;
            List<ReactorSummary> summary = List.of(); String failure = null; boolean interrupted = false;
            try {
                version = invoke(config, lease, snapshot, environment, "version", List.of("-version"), end);
                if (!version.passed()) throw new IOException("Actual default Maven version command failed");
                toolchain = ControlBuild.measuredMavenToolchain(null,
                        Files.readString(logs.resolve("build-" + request.attempt() + "-version.stdout.log")), "3.10.0");
                command = invoke(config, lease, snapshot, environment, "test-compile", arguments, end);
                summary = reactorSummary(ControlBuild.FileRef.measure(logs.resolve("build-" + request.attempt() + "-test-compile.stdout.log")));
                if (!command.passed()) throw new IOException("Actual complete Maven test-compile failed or timed out");
                if (summary.size() != 35 || summary.stream().anyMatch(row -> !row.outcome().equals("SUCCESS"))
                        || summary.stream().map(ReactorSummary::project).distinct().count() != 35)
                    throw new IOException("Actual successful 35-project reactor summary required");
                var manifest = ControlBuild.collectTestCompilation(machine, snapshot, build, compiled);
                Path compilationPath = logs.resolve("build-" + request.attempt() + "-test-compilation.json");
                byte[] manifestBytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(manifest);
                if (!manifest.equals(ControlBuild.strictMapper().readValue(manifestBytes, ControlBuild.TestCompilationManifest.class)))
                    throw new IOException("Actual compiler manifest strict roundtrip differs");
                compilation = write(compilationPath, manifestBytes, COMPILATION_MAX);
                guard(config, lease, end);
            } catch (IOException | RuntimeException error) {
                failure = error.getClass().getSimpleName() + ": " + error.getMessage();
            } catch (InterruptedException error) {
                interrupted = true; failure = "InterruptedException: " + error.getMessage();
            }
            var sourcePost = ControlBuild.postcheckSource(source, sources, PROFILE);
            var compiledPost = ControlBuild.postcheckSource(snapshot, compiled, PROFILE);
            if (sourcePost.state() != ControlBuild.SourceState.MATCH || compiledPost.state() != ControlBuild.SourceState.MATCH)
                failure = append(failure, "Original or compiler source postcheck is not MATCH");
            Map<String, Long> sizes = Map.of();
            try { sizes = ControlBuild.sizes(work, lease.caps(), () -> {}, INVENTORY); }
            catch (IOException | RuntimeException error) { failure = append(failure, "Final shared accounting unavailable: " + error); }
            requestRef.verify(); request.planRef().verify(); request.capacityReleaseRef().verify();
            for (var pin : runtime) pin.verify();
            if (System.nanoTime() >= end || !Instant.now().isBefore(lease.review()))
                failure = append(failure, "Original compiler deadline expired during final provenance/accounting");
            var actual = new Actual(RECEIPT_SCHEMA, machine, Instant.now().toString(),
                    Scope.COMPILER_DIAGNOSTIC_ONLY_NOT_FULL35_SDK_HOST_OR_GAME_QUALIFICATION,
                    failure == null ? State.COMPILED_NOT_TESTED : State.COMPILE_RED, Tests.NOT_TESTED,
                    requestRef, request.planRef(), request.qualifiedToolsRef(), request.capacityReleaseRef(), PROFILE, 35,
                    summary, source.toString(), snapshot.toString(), build.toString(), sourcePost, compiledPost,
                    sources, compiled, runtime, toolchain, ControlBuild.FileRef.measure(config.javaHome().resolve("bin/java.exe")),
                    version, command, arguments, existingLogs(logs, request.attempt(), settings), compilation, sizes, failure);
            byte[] actualBytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(actual);
            if (!actual.equals(ControlBuild.strictMapper().readValue(actualBytes, Actual.class)))
                throw new IOException("Compiler-only result strict roundtrip differs");
            write(resultPath, actualBytes, RECEIPT_MAX);
            if (interrupted) Thread.currentThread().interrupt();
            return actual;
        }
    }

    private static WindowsJobProcess.CommandResult invoke(ControlBuild.Config config, Lease lease, Path snapshot,
            Map<String, String> environment, String phase, List<String> arguments, long end) throws IOException, InterruptedException {
        guard(config, lease, end);
        String prefix = "build-" + config.attempt() + "-" + phase;
        Path logs = config.workRoot().resolve("logs"), batch = logs.resolve(prefix + ".cmd");
        ControlBuild.writeMavenBatch(batch, null, arguments); // Exact existing default-mvn producer and CMD escaping.
        var spec = new WindowsJobProcess.CommandSpec(Path.of(System.getenv("SystemRoot"), "System32/cmd.exe"),
                List.of("/d", "/c", batch.toString()), snapshot, environment,
                logs.resolve(prefix + ".stdout.log"), logs.resolve(prefix + ".stderr.log"), lease.memory());
        AtomicLong last = new AtomicLong(System.nanoTime());
        Duration remaining = Duration.ofNanos(Math.max(1, end - System.nanoTime()));
        try (WindowsJobProcess child = WindowsJobProcess.start(spec)) {
            return child.await(remaining, lease.review(), () -> {
                long now = System.nanoTime();
                if (now - last.get() < Duration.ofSeconds(5).toNanos()) return;
                last.set(now);
                try { guard(config, lease, end); }
                catch (IOException error) { throw new IllegalStateException(error); }
            }, logs.resolve(prefix + "-before-cleanup.json"), WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
        }
    }

    private static Lease lease(ControlBuild.Config config, ControlBuild.FileRef ref) throws IOException {
        JsonNode root = ControlBuild.strictMapper().readTree(read(ref, 128 << 10));
        boolean typed = "xar.java-control.capacity-release/v1".equals(root.path("schema").textValue());
        boolean manual = "xar.java-phase1.manual-capacity-release/v1".equals(root.path("schema").textValue());
        if (!typed && !manual) throw new IOException("Existing shared typed/manual Maven capacity release required");
        JsonNode parts = root.required("parts");
        Map<String, Long> caps = new LinkedHashMap<>();
        for (String part : List.of("m2", "build", "tools", "scratch", "artifacts"))
            caps.put(part, positive(parts, part));
        caps.put("logs", positive(parts, "metadata_logs"));
        Map<Path, Long> minimum = new LinkedHashMap<>();
        for (var field : root.required("volumes").properties())
            minimum.put(absolute(field.getKey()), positive(field.getValue(), "required_free"));
        long memory = positive(root, typed ? "memory_limit_bytes" : "test_RAM_joint_hard_bytes");
        long heap = positive(root, typed ? "maven_heap_bytes" : "Maven_heap_bytes");
        if (memory > (2L << 30) || heap < (64L << 20) || heap > (768L << 20) || heap >= memory)
            throw new IOException("Released finite Maven memory range required");
        return new Lease(Instant.parse(root.required("review_at_utc").textValue()), Map.copyOf(caps), memory, heap, Map.copyOf(minimum));
    }

    private static void guard(ControlBuild.Config config, Lease lease, long end) throws IOException {
        if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Compiler operation interrupted");
        if (System.nanoTime() >= end || !Instant.now().isBefore(lease.review())) throw new IOException("Original compiler deadline expired");
        ControlBuild.readLeaseAt(config, WindowsJobProcess.currentMachineId(), Instant.now());
        for (var item : lease.minimumFree().entrySet())
            if (Files.getFileStore(item.getKey()).getUsableSpace() < item.getValue())
                throw new IOException("Shared admitted volume free space is insufficient");
        ControlBuild.sizes(config.workRoot(), lease.caps(), () -> {
            if (System.nanoTime() >= end) throw new IOException("Original compiler deadline expired during inventory");
        }, INVENTORY);
    }

    private static Map<String, String> environment(ControlBuild.Config config, Path snapshot, Lease lease) throws IOException {
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());
        for (String key : List.of("MAVEN_ARGS", "MAVEN_DEBUG_OPTS", "MAVEN_BATCH_ECHO", "JAVA_TOOL_OPTIONS",
                "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVAC_OPTIONS", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"))
            environment.remove(key);
        String scratch = config.workRoot().resolve("scratch").toString();
        String options = "-Xms32m -Xmx" + (lease.heap() >> 20)
                + "m -XX:MaxMetaspaceSize=256m -XX:ReservedCodeCacheSize=64m -XX:MaxDirectMemorySize=128m -Xss512k"
                + " -Djava.io.tmpdir=" + scratch + " -Djna.tmpdir=" + scratch;
        environment.put("JAVA_HOME", config.javaHome().toString()); environment.put("MAVEN_OPTS", options);
        environment.put("JAVA_TOOL_OPTIONS", options); environment.put("MAVEN_SKIP_RC", "1");
        environment.put("MAVEN_BASEDIR", snapshot.toString()); environment.put("MAVEN_USER_HOME", config.workRoot().resolve("m2").toString());
        environment.put("TEMP", scratch); environment.put("TMP", scratch);
        return Map.copyOf(environment);
    }

    /**
     * Parse only the ASCII Maven reactor protocol from the pinned raw stdout.
     * Other diagnostic bytes are never decoded or used as an encoding fallback.
     */
    public static List<ReactorSummary> reactorSummary(ControlBuild.FileRef stdoutRef) throws IOException {
        byte[] raw = read(stdoutRef, 8 << 20);
        Pattern row = Pattern.compile("^\\[(?:INFO|ERROR)] (.*?)\\s+\\.{2,}\\s+(SUCCESS|FAILURE|SKIPPED)(?:\\s.*)?$");
        List<ReactorSummary> result = new ArrayList<>();
        boolean summary = false; int headings = 0;
        for (int start = 0; start < raw.length;) {
            int end = start;
            while (end < raw.length && raw[end] != '\n') end++;
            StringBuilder ascii = new StringBuilder(end - start);
            boolean nonAscii = false;
            for (int cursor = start; cursor < end; cursor++) {
                int value = raw[cursor] & 0xff;
                if (value == 27 && cursor + 1 < end && raw[cursor + 1] == '[') {
                    int terminal = cursor + 2;
                    while (terminal < end && ((raw[terminal] >= '0' && raw[terminal] <= '9')
                            || raw[terminal] == ';')) terminal++;
                    if (terminal < end && (raw[terminal] == 'm' || raw[terminal] == 'K')) {
                        cursor = terminal; continue;
                    }
                }
                if (value > 127) { nonAscii = true; ascii.append((char) 127); }
                else ascii.append((char) value);
            }
            String line = ascii.toString().stripTrailing();
            boolean heading = line.startsWith("[INFO] Reactor Summary");
            if (heading || summary) {
                if (nonAscii) throw new IOException("Non-ASCII reactor protocol field at raw byte " + start
                        + "; stdout=" + stdoutRef.path() + "; sha256=" + stdoutRef.sha256());
                if (heading) { summary = true; headings++; }
                else if (line.startsWith("[INFO] BUILD ") || line.startsWith("[ERROR] BUILD ")) summary = false;
                else {
                    var match = row.matcher(line);
                    if (match.matches()) result.add(new ReactorSummary(match.group(1).strip(), match.group(2)));
                }
            }
            start = end + 1;
        }
        stdoutRef.verify();
        if (headings > 1 || result.size() > 35)
            throw new IOException("Ambiguous or oversized actual reactor summary; stdout="
                    + stdoutRef.path() + "; sha256=" + stdoutRef.sha256());
        return List.copyOf(result);
    }

    private static List<ControlBuild.FileRef> existingLogs(Path logs, String attempt, Path settings) throws IOException {
        List<ControlBuild.FileRef> result = new ArrayList<>(); result.add(ControlBuild.FileRef.measure(settings));
        for (String phase : List.of("version", "test-compile"))
            for (String suffix : List.of(".cmd", ".stdout.log", ".stderr.log")) {
                Path path = logs.resolve("build-" + attempt + "-" + phase + suffix);
                if (Files.exists(path)) result.add(ControlBuild.FileRef.measure(path));
            }
        return List.copyOf(result);
    }
    private static long positive(JsonNode node, String key) throws IOException {
        JsonNode value = node.get(key);
        if (value == null || !value.isIntegralNumber() || !value.canConvertToLong() || value.longValue() < 1)
            throw new IOException("Exact positive integer required: " + key);
        return value.longValue();
    }
    private static byte[] read(ControlBuild.FileRef ref, int maximum) throws IOException {
        Objects.requireNonNull(ref); ref.verify();
        if (ref.bytes() < 1 || ref.bytes() > maximum) throw new IOException("Bounded exact input required");
        byte[] bytes = Files.readAllBytes(Path.of(ref.path())); ref.verify(); return bytes;
    }
    private static ControlBuild.FileRef write(Path path, byte[] bytes, int maximum) throws IOException {
        if (bytes.length > maximum) throw new IOException("Finite compile metadata limit exceeded");
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW); return ControlBuild.FileRef.measure(path);
    }
    private static Path absolute(String value) {
        if (value == null || value.isBlank() || value.length() > 4096 || value.codePoints().anyMatch(Character::isISOControl))
            throw new IllegalArgumentException("Plain canonical absolute path required");
        Path path = Path.of(value);
        if (!path.isAbsolute() || !path.equals(path.normalize())) throw new IllegalArgumentException("Canonical absolute path required");
        return path;
    }
    private static String append(String first, String second) { return first == null ? second : first + "; " + second; }
}
