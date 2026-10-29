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
 * Finite diagnostic test-compile of the complete reactor through shared producer and accounting APIs.
 * Never a ControlBuild accepted/capture receipt; test bodies and Full35/SDK/Game remain unexecuted.
 */
public final class Full35CompileOnly {
    private Full35CompileOnly() { }
    public static final String REQUEST_SCHEMA = "xar.full35-compile-only-request/v1";
    public static final String QUALIFIED_REQUEST_SCHEMA = "xar.full35-qualified-compile-only-request/v2";
    public static final String RECEIPT_SCHEMA = "xar.full35-compile-only-actual/v2";
    private static final int REQUEST_MAX = 1 << 20, RECEIPT_MAX = 4 << 20, COMPILATION_MAX = 8 << 20;
    public enum State { COMPILED_NOT_TESTED, COMPILE_RED }
    public enum Tests { NOT_TESTED }
    public enum Scope { COMPILER_DIAGNOSTIC_ONLY_NOT_FULL35_SDK_HOST_OR_GAME_QUALIFICATION }

    public record OwnReadbackExpectation(String schema, String scope) {
        public OwnReadbackExpectation {
            if(schema==null || schema.isBlank() || scope==null || !scope.matches("[A-Z][A-Z0-9_]{0,127}"))
                throw new IllegalArgumentException("Exact own-readback schema and scope required");
        }
    }
    public record AdapterQualification(SharedOwnedCommandBinding.AuthorityExpectation deliveryExpectation,
            ControlBuild.FileRef wholeBuildReceiptRef, ControlBuild.FileRef ownArchiveActualRef,
            OwnReadbackExpectation ownReadbackExpectation) {
        public AdapterQualification {
            Objects.requireNonNull(deliveryExpectation); Objects.requireNonNull(wholeBuildReceiptRef);
            Objects.requireNonNull(ownArchiveActualRef); Objects.requireNonNull(ownReadbackExpectation);
        }
    }
    /** Explicit current qualified adapter, retaining the complete historical v1 request unchanged. */
    public record QualifiedRequest(String schema, Request request, AdapterQualification qualification) {
        public QualifiedRequest {
            if(!QUALIFIED_REQUEST_SCHEMA.equals(schema)) throw new IllegalArgumentException("Qualified compiler request v2 required");
            Objects.requireNonNull(request); Objects.requireNonNull(qualification);
        }
    }

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
            ControlBuild.FileRef testCompilationManifestRef, ControlBuild.WorkpackageAccounting finalWorkpackageAccounting,
            String error) {
        public Actual {
            actualReactorSummary = List.copyOf(actualReactorSummary); sourcePins = List.copyOf(sourcePins);
            compiledSourcePins = List.copyOf(compiledSourcePins); completeToolRuntime = List.copyOf(completeToolRuntime);
            mavenArguments = List.copyOf(mavenArguments); commandAndLogRefs = List.copyOf(commandAndLogRefs);
            if (!RECEIPT_SCHEMA.equals(schema) || tests != Tests.NOT_TESTED
                    || scope != Scope.COMPILER_DIAGNOSTIC_ONLY_NOT_FULL35_SDK_HOST_OR_GAME_QUALIFICATION)
                throw new IllegalArgumentException("Compiler-only result must never grant test or application qualification");
            if (state == State.COMPILED_NOT_TESTED && (error != null || compileResult == null
                    || !compileResult.passed() || actualReactorSummary.size() != 35
                    || actualReactorSummary.stream().anyMatch(row -> !row.outcome().equals("SUCCESS"))
                    || sourcePostcheck.state() != ControlBuild.SourceState.MATCH
                    || compiledSourcePostcheck.state() != ControlBuild.SourceState.MATCH
                    || testCompilationManifestRef == null || finalWorkpackageAccounting == null
                    || !sameFileReference(capacityReleaseRef, finalWorkpackageAccounting.capacityReleaseRef())))
                throw new IllegalArgumentException("Complete compiler terminal and provenance are required");
        }
    }

    /** A completed adapter join is evidence only; it grants no current operation card. */
    public enum AdapterValidationScope {
        COMPLETED_TOOLS_ADAPTER_BINDING_ONLY_NO_EXECUTION_S40_FULL_CI_HOST_SDK_OR_GAME
    }
    public record AdapterValidation(String schema, String machineId, String observedAtUtc,
            AdapterValidationScope scope, ControlBuild.FileRef deliveryRef,
            ControlBuild.FileRef qualificationRef, AdapterQualification qualification,
            List<ControlBuild.FileRef> completeToolRuntime) {
        public AdapterValidation {
            if (!"xar.full35-adapter-validation/v1".equals(schema) || machineId == null || machineId.isBlank()
                    || scope != AdapterValidationScope.COMPLETED_TOOLS_ADAPTER_BINDING_ONLY_NO_EXECUTION_S40_FULL_CI_HOST_SDK_OR_GAME)
                throw new IllegalArgumentException("Completed adapter binding evidence only");
            Instant.parse(observedAtUtc);
            Objects.requireNonNull(deliveryRef); Objects.requireNonNull(qualificationRef);
            Objects.requireNonNull(qualification); completeToolRuntime = List.copyOf(completeToolRuntime);
            if (completeToolRuntime.size() != 6) throw new IllegalArgumentException("Complete six-file tools runtime required");
        }
    }

    /**
     * Read-only route to execute's qualification gate. It constructs no compiler Request,
     * takes no writer lock, creates no output, invokes no Maven, and renews no lease.
     */
    public static AdapterValidation validateAdapter(ControlBuild.FileRef deliveryRef,
            ControlBuild.FileRef qualificationRef) throws IOException {
        AdapterQualification qualification = readAdapterQualification(qualificationRef);
        JsonNode delivery = ControlBuild.strictMapper().readTree(read(deliveryRef, REQUEST_MAX));
        String machine = WindowsJobProcess.currentMachineId();
        List<ControlBuild.FileRef> runtime = ControlBuild.producerClosure();
        qualifyAdapter(delivery, qualification, machine, runtime);
        deliveryRef.verify(); qualificationRef.verify();
        for (ControlBuild.FileRef ref : runtime) ref.verify();
        return new AdapterValidation("xar.full35-adapter-validation/v1", machine, Instant.now().toString(),
                AdapterValidationScope.COMPLETED_TOOLS_ADAPTER_BINDING_ONLY_NO_EXECUTION_S40_FULL_CI_HOST_SDK_OR_GAME,
                deliveryRef, qualificationRef, qualification, runtime);
    }

    static AdapterQualification readAdapterQualification(ControlBuild.FileRef qualificationRef) throws IOException {
        AdapterQualification value = ControlBuild.strictMapper().readValue(
                read(qualificationRef, REQUEST_MAX), AdapterQualification.class);
        if (value == null) throw new IOException("Non-null complete adapter qualification required");
        return value;
    }

    public record IncrementalRequest(String schema, QualifiedRequest base, List<String> modules,
            int threads, String runId) {
        public IncrementalRequest {
            if (!"xar.mutable-module-compile/v1".equals(schema) || base == null || threads != 2
                    || runId == null || !runId.matches("[a-zA-Z0-9][a-zA-Z0-9_-]{0,31}"))
                throw new IllegalArgumentException("Explicit finite mutable module request required");
            modules = List.copyOf(modules);
            if (modules.isEmpty() || modules.size() > 35
                    || modules.stream().anyMatch(v -> !v.matches("[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}")))
                throw new IllegalArgumentException("Explicit reactor module selectors required");
        }
    }
    public record IncrementalActual(String schema, String machineId, String observedAtUtc,
            String scope, State state, Tests tests, ControlBuild.FileRef requestRef,
            String sourceRoot, String buildRoot, List<String> modules, int threads,
            ControlBuild.MavenToolchain mavenToolchain, WindowsJobProcess.CommandResult versionResult,
            WindowsJobProcess.CommandResult compileResult, List<ReactorSummary> reactorSummary,
            ControlBuild.SourcePostcheck sourcePostcheck, ControlBuild.WorkpackageAccounting accounting,
            List<String> mavenArguments, String error) { }

    private enum IncrementalGoal { COMPILE, TEST_COMPILE, TOOLS_PRODUCER_JAR, MAIN_JARS_ONLY;
        String mavenGoal() { return switch (this) {
            case COMPILE -> "compile";
            case TEST_COMPILE -> "test-compile";
            case TOOLS_PRODUCER_JAR -> "tools-producer-jar";
            case MAIN_JARS_ONLY -> "main-jars-only";
        }; }
        List<String> mavenGoals() { return switch (this) {
            case COMPILE -> List.of("compile");
            case TEST_COMPILE -> List.of("test-compile");
            case TOOLS_PRODUCER_JAR -> List.of("jar:jar", "dependency:copy-dependencies@portable-runtime-closure");
            case MAIN_JARS_ONLY -> List.of("jar:jar");
        }; }
        boolean jarsOnly() { return this == TOOLS_PRODUCER_JAR || this == MAIN_JARS_ONLY; }
    }
    public static IncrementalActual executeIncremental(ControlBuild.FileRef original,
            IncrementalRequest input) throws Exception {
        return executeIncremental(original, input, IncrementalGoal.TEST_COMPILE);
    }
    private static IncrementalActual executeIncremental(ControlBuild.FileRef original,
            IncrementalRequest input, IncrementalGoal goal) throws Exception {
        Request request = input.base().request();
        String machine = WindowsJobProcess.currentMachineId();
        if (!machine.equals(request.machineId())) throw new IOException("Actual machine differs");
        original.verify(); request.planRef().verify(); request.capacityReleaseRef().verify();
        List<ControlBuild.FileRef> runtime = ControlBuild.producerClosure(WindowsJobProcess.class);
        var expected = new ArrayList<>(request.expectedRuntime());
        expected.sort(Comparator.comparing(ControlBuild.FileRef::path));
        if (!runtime.equals(expected)) throw new IOException("Exact original qualified tools required");
        qualifyAdapter(ControlBuild.strictMapper().readTree(read(request.qualifiedToolsRef(), REQUEST_MAX)),
                input.base().qualification(), machine, runtime);
        Path source = absolute(request.sourceRoot()), work = absolute(request.workRoot());
        var profile = sourceProfile(CompleteSourceGraph.readPlan(request.planRef()));
        var config = new ControlBuild.Config(source, work, Path.of(request.capacityReleaseRef().path()),
                request.attempt(), request.ownerTask(), null, absolute(request.javaHome()), "3.10.0",
                request.timeoutSeconds(), ControlBuild.TargetKind.SERVICE_FAST_JAR, profile);
        Lease lease = lease(config, request.capacityReleaseRef());
        Path build = work.resolve("build/" + request.attempt());
        Path temporary = work.resolve("scratch/" + request.attempt() + "-tmp");
        if (!Files.isDirectory(source, LinkOption.NOFOLLOW_LINKS)
                || !Files.isDirectory(build, LinkOption.NOFOLLOW_LINKS)
                || !Files.isDirectory(temporary, LinkOption.NOFOLLOW_LINKS)
                || !temporary.equals(temporary.toRealPath()))
            throw new IOException("Existing bounded independent mutable source/build/TMP required");
        Path resultPath = work.resolve("logs/build-" + request.attempt() + "-" + input.runId() + ".json");
        if (Files.exists(resultPath)) throw new IOException("Unique incremental result required");
        long end = System.nanoTime() + Duration.ofSeconds(request.timeoutSeconds()).toNanos();
        WindowsJobProcess.CommandResult version = null, command = null;
        ControlBuild.MavenToolchain toolchain = null;
        List<ReactorSummary> summary = List.of(); String error = null;
        if (goal == IncrementalGoal.TOOLS_PRODUCER_JAR && !input.modules().equals(List.of("build-tools"))
                || goal == IncrementalGoal.MAIN_JARS_ONLY && !input.modules().equals(List.of("local-service")))
            throw new IOException("Fixed existing Maven Jar goal requires its exact module selector");
        Path mavenPom = source.resolve(goal == IncrementalGoal.TOOLS_PRODUCER_JAR ? "build-tools/pom.xml" : "pom.xml");
        List<String> arguments = new ArrayList<>(List.of("--fail-at-end", "-B", "-ntp", "-e", "-T", "2",
                "-f", mavenPom.toString(), "-Dmaven.repo.local=" + work.resolve("m2"),
                "-Dck3.build.root=" + build, "-Djava.io.tmpdir=" + temporary,
                "-Dmaven.compiler.useIncrementalCompilation=false"));
        if (goal != IncrementalGoal.TOOLS_PRODUCER_JAR)
            arguments.addAll(List.of("-pl", String.join(",", input.modules()), "-am"));
        if (goal == IncrementalGoal.TEST_COMPILE) arguments.addAll(List.of("-Dmaven.test.skip=false", "-DskipTests=true"));
        arguments.addAll(goal.mavenGoals());
        List<ControlBuild.FileRef> pins;
        ControlBuild.SourcePostcheck post; ControlBuild.WorkpackageAccounting accounting;
        try (FileChannel channel = FileChannel.open(work.resolve(".java-control-build.lock"),
                StandardOpenOption.CREATE, StandardOpenOption.WRITE); FileLock lock = channel.tryLock()) {
            if (lock == null || !lock.isValid()) throw new IOException("Another Maven writer owns work");
            incrementalGuard(config, lease, end);
            var coreOrigin = ControlBuild.class.getProtectionDomain().getCodeSource();
            var adapterOrigin = Full35CompileOnly.class.getProtectionDomain().getCodeSource();
            if (coreOrigin == null || adapterOrigin == null || !coreOrigin.getLocation().equals(adapterOrigin.getLocation()))
                throw new IOException("Explicit pinned mutable core and adapter CodeSource must match");
            System.out.println("MUTABLE_CORE_CODE_ORIGIN=" + coreOrigin.getLocation()
                    + " LS_SOURCE_LIMIT=" + profile.moduleSourceBytes("local-service", "src"));
            pins = ControlBuild.sourceManifest(source, profile);
            Map<String,String> environment = environment(config, source, lease, temporary);
            try {
                version = invokeIncremental(config, lease, source, environment,
                        input.runId() + "-version", List.of("-version"), end);
                if (!version.passed()) throw new IOException("Actual default mvn version failed");
                String text = Files.readString(work.resolve("logs/build-" + request.attempt()
                        + "-" + input.runId() + "-version.stdout.log"));
                toolchain = ControlBuild.measuredMavenToolchain(null, text, "3.10.0");
                System.out.println("actual_default_maven=" + toolchain);
                command = invokeIncremental(config, lease, source, environment,
                        input.runId() + "-" + goal.mavenGoal(), arguments, end);
                summary = reactorSummary(ControlBuild.FileRef.measure(work.resolve("logs/build-"
                        + request.attempt() + "-" + input.runId() + "-" + goal.mavenGoal() + ".stdout.log")));
                if (!command.passed()) throw new IOException("Actual mutable module compilation failed");
            } catch (IOException | RuntimeException failure) {
                error = failure.getClass().getSimpleName() + ": " + failure.getMessage();
            }
            post = ControlBuild.postcheckSource(source, pins, profile);
            if (post.state() != ControlBuild.SourceState.MATCH) error = append(error, "Source postcheck " + post.state());
            accounting = incrementalGuard(config, lease, end);
        }
        for (var pin : runtime) pin.verify(); original.verify(); request.capacityReleaseRef().verify();
        var actual = new IncrementalActual("xar.mutable-module-compile-actual/v1", machine, Instant.now().toString(),
                goal.jarsOnly() ? "MUTABLE_MAIN_JAR_PACKAGING_ONLY_NOT_TEST_COMPILED_CAPTURE_SERVICE_OR_GAME_QUALIFICATION"
                        : "MUTABLE_MODULE_COMPILER_ONLY_NO_FULL_REACTOR_TEST_SERVICE_OR_GAME_QUALIFICATION",
                error == null ? State.COMPILED_NOT_TESTED : State.COMPILE_RED, Tests.NOT_TESTED,
                original, source.toString(), build.toString(), input.modules(), input.threads(), toolchain,
                version, command, summary, post, accounting, arguments, error);
        write(resultPath, ControlBuild.strictMapper().writeValueAsBytes(actual), RECEIPT_MAX);
        return actual;
    }
    private static ControlBuild.WorkpackageAccounting incrementalGuard(ControlBuild.Config config,
            Lease lease, long end) throws IOException {
        accountingDeadline(lease, end);
        ControlBuild.readLeaseAt(config, WindowsJobProcess.currentMachineId(), Instant.now());
        for (var item : lease.minimumFree().entrySet())
            if (Files.getFileStore(item.getKey()).getUsableSpace() < item.getValue())
                throw new IOException("Admitted volume free space insufficient");
        return ControlBuild.accountWorkpackage(config, () -> accountingDeadline(lease, end));
    }
    private static WindowsJobProcess.CommandResult invokeIncremental(ControlBuild.Config config,
            Lease lease, Path source, Map<String,String> environment, String phase,
            List<String> arguments, long end) throws IOException, InterruptedException {
        incrementalGuard(config, lease, end);
        String prefix = "build-" + config.attempt() + "-" + phase;
        Path logs = config.workRoot().resolve("logs"), batch = logs.resolve(prefix + ".cmd");
        ControlBuild.writeMavenBatch(batch, null, arguments);
        var spec = new WindowsJobProcess.CommandSpec(Path.of(System.getenv("SystemRoot"), "System32/cmd.exe"),
                List.of("/d", "/c", batch.toString()), source, environment,
                logs.resolve(prefix + ".stdout.log"), logs.resolve(prefix + ".stderr.log"), lease.memory());
        AtomicLong last = new AtomicLong(System.nanoTime());
        try (WindowsJobProcess child = WindowsJobProcess.start(spec)) {
            return child.await(Duration.ofNanos(Math.max(1, end - System.nanoTime())), lease.review(), () -> {
                long now = System.nanoTime();
                if (now - last.get() < Duration.ofSeconds(5).toNanos()) return;
                last.set(now);
                try { incrementalGuard(config, lease, end); }
                catch (IOException failure) { throw new IllegalStateException(failure); }
            }, logs.resolve(prefix + "-before-cleanup.json"),
                    WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 4 && java.util.Set.of("--incremental", "--incremental-main",
                "--incremental-tools-jar", "--incremental-main-jars").contains(args[0])) {
            var original = new ControlBuild.FileRef(args[1], Long.parseLong(args[2]), args[3]);
            var request = ControlBuild.strictMapper().readValue(read(original, REQUEST_MAX), IncrementalRequest.class);
            IncrementalGoal goal = switch (args[0]) {
                case "--incremental" -> IncrementalGoal.TEST_COMPILE;
                case "--incremental-main" -> IncrementalGoal.COMPILE;
                case "--incremental-tools-jar" -> IncrementalGoal.TOOLS_PRODUCER_JAR;
                case "--incremental-main-jars" -> IncrementalGoal.MAIN_JARS_ONLY;
                default -> throw new IOException("Unknown incremental goal");
            };
            var actual = executeIncremental(original, request, goal);
            System.out.println("mutable_compile=" + actual.state() + ";tests=NOT_TESTED;projects="
                    + actual.reactorSummary().size());
            if (actual.state() != State.COMPILED_NOT_TESTED) System.exit(1);
            return;
        }
        if (args.length > 0 && "--qualify-adapter".equals(args[0])) {
            if (args.length != 7)
                throw new IOException("--qualify-adapter delivery-path exact-bytes exact-sha256 qualification-path exact-bytes exact-sha256 required");
            var deliveryRef = new ControlBuild.FileRef(args[1], Long.parseLong(args[2]), args[3]);
            var qualificationRef = new ControlBuild.FileRef(args[4], Long.parseLong(args[5]), args[6]);
            System.out.println(ControlBuild.strictMapper().writeValueAsString(validateAdapter(deliveryRef, qualificationRef)));
            return;
        }
        if (args.length != 3) throw new IOException("request-path exact-bytes exact-sha256 required");
        var requestRef = new ControlBuild.FileRef(args[0], Long.parseLong(args[1]), args[2]);
        requestRef.verify();
        JsonNode wire=ControlBuild.strictMapper().readTree(read(requestRef,REQUEST_MAX));
        Actual result;
        if(QUALIFIED_REQUEST_SCHEMA.equals(wire.path("schema").textValue())) {
            QualifiedRequest request=ControlBuild.strictMapper().treeToValue(wire,QualifiedRequest.class);
            result=execute(requestRef,request.request(),request.qualification());
        } else {
            Request request=ControlBuild.strictMapper().treeToValue(wire,Request.class);
            result=execute(requestRef,request);
        }
        System.out.println("full35_compile=" + result.state() + ";tests=NOT_TESTED;projects="
                + result.actualReactorSummary().size() + ";scope=" + result.scope());
        if (result.state() != State.COMPILED_NOT_TESTED) System.exit(1);
    }

    public static Actual execute(ControlBuild.FileRef requestRef, Request request) throws Exception {
        return execute(requestRef,request,null);
    }

    private static Actual execute(ControlBuild.FileRef requestRef, Request request, AdapterQualification qualification) throws Exception {
        String machine = WindowsJobProcess.currentMachineId();
        if (!machine.equals(request.machineId())) throw new IOException("Current execution machine differs");
        requestRef.verify(); request.planRef().verify(); request.qualifiedToolsRef().verify();
        request.capacityReleaseRef().verify();
        var runtime = ControlBuild.producerClosure();
        var expected = new ArrayList<>(request.expectedRuntime());
        expected.sort(Comparator.comparing(ControlBuild.FileRef::path));
        if (!runtime.equals(expected)) throw new IOException("Mixed or unqualified compile helper dependency archive");
        JsonNode delivery = ControlBuild.strictMapper().readTree(read(request.qualifiedToolsRef(), 1 << 20));
        if(qualification!=null) {
            qualifyAdapter(delivery,qualification,machine,runtime);
        } else {
        if (!machine.equals(delivery.path("machine_id").textValue())
                || !"WHOLE_MAVEN_AND_OWN_ARCHIVE_ACCEPTED_SOFTWARE_ONLY".equals(delivery.path("status").textValue()))
            throw new IOException("Actual software-only qualified tool delivery required");
        List<ControlBuild.FileRef> delivered = new ArrayList<>();
        for (JsonNode node : delivery.required("complete_deployment"))
            delivered.add(ControlBuild.strictMapper().treeToValue(node, ControlBuild.FileRef.class));
        delivered.sort(Comparator.comparing(ControlBuild.FileRef::path));
        if (!runtime.equals(delivered)) throw new IOException("Running tools differ from exact qualified delivery");
        }
        for (var ref : runtime) ref.verify();
        var plan = CompleteSourceGraph.readPlan(request.planRef());
        ControlBuild.SourceLimitProfile profile = sourceProfile(plan);
        if (!machine.equals(plan.machineId())) throw new IOException("Actual plan machine differs");
        Path source = absolute(request.sourceRoot()), work = absolute(request.workRoot());
        CompleteSourceGraph.verifyMaterialized(plan, source);
        var config = new ControlBuild.Config(source, work, Path.of(request.capacityReleaseRef().path()),
                request.attempt(), request.ownerTask(), null, absolute(request.javaHome()), "3.10.0",
                request.timeoutSeconds(), ControlBuild.TargetKind.SERVICE_FAST_JAR, profile);
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
            try (var temporary = ControlBuild.prepareWorkpackageTemporaryRoot(config, () -> accountingDeadline(lease, end))) {
            guard(config, lease, end, temporary);
            List<ControlBuild.FileRef> sources = ControlBuild.sourceManifest(source, profile), compiled = new ArrayList<>();
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
            if (ControlBuild.postcheckSource(snapshot, compiled, profile).state() != ControlBuild.SourceState.MATCH)
                throw new IOException("Exact full compiler snapshot required");
            Path settings = logs.resolve("build-" + request.attempt() + "-settings.xml");
            Files.writeString(settings, "<?xml version=\"1.0\"?><settings xmlns=\"http://maven.apache.org/SETTINGS/1.2.0\"><interactiveMode>false</interactiveMode></settings>",
                    StandardOpenOption.CREATE_NEW);
            var beforeMavenAccounting = guard(config, lease, end, temporary);
            Path privateTemporary = accountingTemporary(beforeMavenAccounting);
            if (!temporary.root().equals(privateTemporary) || !Files.isDirectory(privateTemporary))
                throw new IOException("Actual shared creator's private temporary root required");
            temporary.requireCurrent();
            SharedSourceFiles.plainAncestors(privateTemporary);
            Map<String, String> environment = environment(config, snapshot, lease, privateTemporary);
            List<String> arguments = List.of("--fail-at-end", "-B", "-ntp", "-e",
                    "-s", settings.toString(), "-gs", settings.toString(), "-f", snapshot.resolve("pom.xml").toString(),
                    "-Dmaven.repo.local=" + work.resolve("m2"), "-Dck3.build.root=" + build,
                    "-Djava.io.tmpdir=" + privateTemporary, "-Dmaven.test.skip=false", "-DskipTests=true", "test-compile");
            WindowsJobProcess.CommandResult version = null, command = null;
            ControlBuild.MavenToolchain toolchain = null; ControlBuild.FileRef compilation = null;
            List<ReactorSummary> summary = List.of(); String failure = null; boolean interrupted = false;
            try {
                version = invoke(config, lease, snapshot, environment, "version", List.of("-version"), end, temporary);
                if (!version.passed()) throw new IOException("Actual default Maven version command failed");
                toolchain = ControlBuild.measuredMavenToolchain(null,
                        Files.readString(logs.resolve("build-" + request.attempt() + "-version.stdout.log")), "3.10.0");
                command = invoke(config, lease, snapshot, environment, "test-compile", arguments, end, temporary);
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
                guard(config, lease, end, temporary);
            } catch (IOException | RuntimeException error) {
                failure = error.getClass().getSimpleName() + ": " + error.getMessage();
            } catch (InterruptedException error) {
                interrupted = true; failure = "InterruptedException: " + error.getMessage();
            }
            var sourcePost = ControlBuild.postcheckSource(source, sources, profile);
            var compiledPost = ControlBuild.postcheckSource(snapshot, compiled, profile);
            if (sourcePost.state() != ControlBuild.SourceState.MATCH || compiledPost.state() != ControlBuild.SourceState.MATCH)
                failure = append(failure, "Original or compiler source postcheck is not MATCH");
            ControlBuild.WorkpackageAccounting accounting = null;
            try { accounting = guard(config, lease, end, temporary); }
            catch (IOException | RuntimeException error) { failure = append(failure, "Final shared accounting unavailable: " + error); }
            requestRef.verify(); request.planRef().verify(); request.capacityReleaseRef().verify();
            request.qualifiedToolsRef().verify();
            if(qualification!=null) {
                qualification.wholeBuildReceiptRef().verify(); qualification.ownArchiveActualRef().verify();
            }
            for (var pin : runtime) pin.verify();
            if (System.nanoTime() >= end || !Instant.now().isBefore(lease.review()))
                failure = append(failure, "Original compiler deadline expired during final provenance/accounting");
            temporary.requireCurrent();
            var actual = new Actual(RECEIPT_SCHEMA, machine, Instant.now().toString(),
                    Scope.COMPILER_DIAGNOSTIC_ONLY_NOT_FULL35_SDK_HOST_OR_GAME_QUALIFICATION,
                    failure == null ? State.COMPILED_NOT_TESTED : State.COMPILE_RED, Tests.NOT_TESTED,
                    requestRef, request.planRef(), request.qualifiedToolsRef(), request.capacityReleaseRef(), profile, 35,
                    summary, source.toString(), snapshot.toString(), build.toString(), sourcePost, compiledPost,
                    sources, compiled, runtime, toolchain, ControlBuild.FileRef.measure(config.javaHome().resolve("bin/java.exe")),
                    version, command, arguments, existingLogs(logs, request.attempt(), settings), compilation, accounting, failure);
            byte[] actualBytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(actual);
            if (!actual.equals(ControlBuild.strictMapper().readValue(actualBytes, Actual.class)))
                throw new IOException("Compiler-only result strict roundtrip differs");
            write(resultPath, actualBytes, RECEIPT_MAX);
            if (interrupted) Thread.currentThread().interrupt();
            return actual;
            }
        }
    }

    /** Compiler diagnostics follow the exact selected plan; historical R2 keeps its own bounds. */
    static ControlBuild.SourceLimitProfile sourceProfile(CompleteSourceGraph.Plan plan) throws IOException {
        if (plan == null || (plan.profile() != CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R2
                && plan.profile() != CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R4
                && plan.profile() != CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R5
                && plan.profile() != CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R6
                && plan.profile() != CompleteSourceGraph.Profile.G2_FULL_PARITY_20261025_R7)
                || plan.modules().size() != 34)
            throw new IOException("Actual R2, R4, R5, R6 or R7 34-child/35-project compiler plan required");
        return plan.profile().sourceLimitProfile();
    }

    private static WindowsJobProcess.CommandResult invoke(ControlBuild.Config config, Lease lease, Path snapshot,
            Map<String, String> environment, String phase, List<String> arguments, long end,
            ControlBuild.PreparedTemporaryRoot temporary) throws IOException, InterruptedException {
        guard(config, lease, end, temporary);
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
                try { guard(config, lease, end, temporary); }
                catch (IOException error) { throw new IllegalStateException(error); }
            }, logs.resolve(prefix + "-before-cleanup.json"), WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
        }
    }

    private static Lease lease(ControlBuild.Config config, ControlBuild.FileRef ref) throws IOException {
        JsonNode root = ControlBuild.strictMapper().readTree(read(ref, 128 << 10));
        boolean typed = "xar.java-control.capacity-release/v1".equals(root.path("schema").textValue());
        boolean manual = "xar.java-phase1.manual-capacity-release/v1".equals(root.path("schema").textValue())
                || "xar.java-phase1.manual-capacity-release/v2".equals(root.path("schema").textValue());
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

    private static ControlBuild.WorkpackageAccounting guard(ControlBuild.Config config, Lease lease, long end,
            ControlBuild.PreparedTemporaryRoot temporary) throws IOException {
        temporary.requireCurrent();
        accountingDeadline(lease, end);
        ControlBuild.readLeaseAt(config, WindowsJobProcess.currentMachineId(), Instant.now());
        for (var item : lease.minimumFree().entrySet())
            if (Files.getFileStore(item.getKey()).getUsableSpace() < item.getValue())
                throw new IOException("Shared admitted volume free space is insufficient");
        return compilerAccounting(config, temporary, () -> accountingDeadline(lease, end));
    }

    /** Real compiler guard boundary: source/build usage is measured while its original TMP creator remains held. */
    static ControlBuild.WorkpackageAccounting compilerAccounting(ControlBuild.Config config,
            ControlBuild.PreparedTemporaryRoot temporary, CiBootstrap.IoGuard active) throws IOException {
        temporary.requireCurrent(); active.check();
        var result = ControlBuild.accountWorkpackage(config, () -> { temporary.requireCurrent(); active.check(); });
        if (!temporary.root().equals(accountingTemporary(result)))
            throw new IOException("Compiler accounting crossed its original temporary creator");
        temporary.requireCurrent(); active.check(); return result;
    }

    private static void accountingDeadline(Lease lease, long end) throws IOException {
        if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Compiler operation interrupted");
        if (System.nanoTime() >= end || !Instant.now().isBefore(lease.review()))
            throw new IOException("Original compiler deadline expired during accounting");
    }

    static Path accountingTemporary(ControlBuild.WorkpackageAccounting accounting) throws IOException {
        if (accounting == null) throw new IOException("Typed shared accounting must declare its temporary scope");
        String scope = switch (accounting.mode()) {
            case FULL_PART_INVENTORY -> "scratch";
            case CONSERVATIVE_VOLUME_ATTEMPT -> "private_tmp";
        };
        String root = accounting.measuredRoots().get(scope);
        if (root == null) throw new IOException("Shared accounting must declare its actual temporary scope: " + scope);
        return absolute(root);
    }

    private static boolean sameFileReference(ControlBuild.FileRef expected, ControlBuild.FileRef actual) {
        return expected != null && actual != null && expected.bytes() == actual.bytes()
                && expected.sha256().equals(actual.sha256())
                && Path.of(expected.path()).toAbsolutePath().normalize()
                        .equals(Path.of(actual.path()).toAbsolutePath().normalize());
    }

    private static Map<String, String> environment(ControlBuild.Config config, Path snapshot, Lease lease,
            Path privateTemporary) throws IOException {
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());
        for (String key : List.of("MAVEN_ARGS", "MAVEN_DEBUG_OPTS", "MAVEN_BATCH_ECHO", "JAVA_TOOL_OPTIONS",
                "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVAC_OPTIONS", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"))
            environment.remove(key);
        String scratch = privateTemporary.toString();
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
    private static void qualifyAdapter(JsonNode delivery,AdapterQualification expected,String machine,
            List<ControlBuild.FileRef> runtime) throws IOException {
        expected.wholeBuildReceiptRef().verify(); expected.ownArchiveActualRef().verify();
        var whole=ControlBuild.verifiedCompletedReceipt(expected.wholeBuildReceiptRef());
        var deployed=new ArrayList<>(whole.completeDeployment());deployed.sort(Comparator.comparing(ControlBuild.FileRef::path));
        if(!machine.equals(whole.machineId()) || whole.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                || !runtime.equals(deployed)) throw new IOException("Actual complete qualified build-tools archive differs");
        JsonNode own=ControlBuild.strictMapper().readTree(read(expected.ownArchiveActualRef(),1<<20));
        requireAdapterMetadata(delivery,own,expected,machine,runtime);
    }

    /** Shared metadata join only; production separately verifies the actual completed whole build receipt. */
    static void requireAdapterMetadata(JsonNode delivery,JsonNode own,AdapterQualification expected,String machine,
            List<ControlBuild.FileRef> runtime) throws IOException {
        SharedOwnedCommandBinding.verifyAuthority(delivery,expected.deliveryExpectation(),machine);
        var mapper=ControlBuild.strictMapper();
        ControlBuild.FileRef whole=mapper.treeToValue(delivery.required("qualified_whole_build_receipt_ref"),ControlBuild.FileRef.class);
        ControlBuild.FileRef ownRef=mapper.treeToValue(delivery.required("qualified_own_archive_actual_ref"),ControlBuild.FileRef.class);
        List<ControlBuild.FileRef> delivered=mapper.readerForListOf(ControlBuild.FileRef.class).readValue(delivery.required("complete_runtime"));
        List<ControlBuild.FileRef> readback=mapper.readerForListOf(ControlBuild.FileRef.class).readValue(own.required("complete_running_runtime"));
        ControlBuild.FileRef readbackWhole=mapper.treeToValue(own.required("build_receipt_ref"),ControlBuild.FileRef.class);
        var sortedDelivered=new ArrayList<>(delivered); sortedDelivered.sort(Comparator.comparing(ControlBuild.FileRef::path));
        var sortedReadback=new ArrayList<>(readback); sortedReadback.sort(Comparator.comparing(ControlBuild.FileRef::path));
        if(!whole.equals(expected.wholeBuildReceiptRef()) || !ownRef.equals(expected.ownArchiveActualRef())
                || !readbackWhole.equals(whole) || !machine.equals(own.path("machine_id").textValue())
                || !expected.ownReadbackExpectation().schema().equals(own.path("schema").textValue())
                || !expected.ownReadbackExpectation().scope().equals(own.path("scope").textValue())
                || runtime.size()!=6 || !runtime.equals(sortedDelivered) || !runtime.equals(sortedReadback))
            throw new IOException("Explicit adapter/whole/own complete-runtime binding differs");
    }

    private static byte[] read(ControlBuild.FileRef ref, int maximum) throws IOException {
        Objects.requireNonNull(ref); ref.verify();
        if (ref.bytes() < 1 || ref.bytes() > maximum) throw new IOException("Bounded exact input required");
        byte[] bytes;
        try(var input=Files.newInputStream(Path.of(ref.path()))) { bytes=input.readNBytes(Math.toIntExact(ref.bytes()+1)); }
        ref.verify(); BoundedSourceInputGuard.verifyReadBytes(ref,bytes,maximum); return bytes;
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
