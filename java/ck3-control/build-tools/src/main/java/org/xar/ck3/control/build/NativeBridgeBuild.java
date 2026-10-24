package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Pattern;

/** Fixed bridge/injector producer. Research fixture receipts never enter this protocol. */
public final class NativeBridgeBuild {
    public static final String REQUEST_SCHEMA = "xar.native-bridge-build-request/v2";
    public static final String LEGACY_REQUEST_SCHEMA = "xar.native-bridge-build-request/v1";
    public static final String ACTUAL_SCHEMA = "xar.native-bridge-build-actual/v2";
    public static final List<String> TARGETS = List.of("xar_ck3_bridge", "xar_ck3_bridge_injector");
    private static final int MAX_JSON = 16 << 20;
    private static final int MAX_FILES = 16000;
    // A private copy keeps the global SDK/build receipt mapper and the six-JAR deployment unchanged.
    private static final ObjectMapper JSON = RootNativePlanJson.mapper();
    private NativeBridgeBuild() { }
    public enum Stage { ENV, BUILD, REGISTER }
    public enum Status { PASS, RED, UNKNOWN }
    public enum SwitchValue { ON, OFF }
    public enum CommandKind { ENV_CAPTURE, CMAKE_VERSION, NINJA_VERSION, COMPILER_HELP, CONFIGURE, BRIDGE_BUILD, ACTIVE_DEPENDENCIES, DEFENDER_HELPER }
    public record Definition(String option, SwitchValue value) {
        public Definition {
            Objects.requireNonNull(value);
            if (option == null || !option.matches("XAR_(CK3_|ENABLE_)[A-Z0-9_]{1,160}"))
                throw new IllegalArgumentException("Source-declared project boolean option required");
        }
    }
    public record Toolchain(ControlBuild.FileRef cmd, ControlBuild.FileRef vcvars64,
            ControlBuild.FileRef java, ControlBuild.FileRef cmake, ControlBuild.FileRef ninja,
            ControlBuild.FileRef compiler, ControlBuild.FileRef linker) {
        public Toolchain {
            List<ControlBuild.FileRef> pins = List.of(cmd, vcvars64, java, cmake, ninja, compiler, linker);
            List<String> names = List.of("cmd.exe", "vcvars64.bat", "java.exe", "cmake.exe", "ninja.exe", "cl.exe", "link.exe");
            for (int index = 0; index < pins.size(); index++)
                if (!Path.of(pins.get(index).path()).getFileName().toString().equalsIgnoreCase(names.get(index)))
                    throw new IllegalArgumentException("Exact native tool role disagrees with filename");
        }
        public List<ControlBuild.FileRef> references() { return List.of(cmd, vcvars64, java, cmake, ninja, compiler, linker); }
    }
    public record Request(String schema, String machineId, Stage stage, Path canonicalRepository,
            Path sourceRoot, List<ControlBuild.FileRef> completeSources, Path buildRoot, Path scratchRoot,
            ControlBuild.FileRef qualifiedToolsBuild, Toolchain tools, List<Definition> definitions,
            int parallelJobs, ControlBuild.FileRef environmentActual, ControlBuild.FileRef buildActual,
            NativeBridgeDefender.HelperRuntime defender) {
        public Request {
            if ((!REQUEST_SCHEMA.equals(schema) && !LEGACY_REQUEST_SCHEMA.equals(schema)) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}")
                    || machineId.equals("unknown") || stage == null || parallelJobs < 1 || parallelJobs > 64)
                throw new IllegalArgumentException("Versioned finite bridge request required");
            canonicalRepository = absolute(canonicalRepository); sourceRoot = absolute(sourceRoot);
            buildRoot = absolute(buildRoot); scratchRoot = absolute(scratchRoot);
            completeSources = unique(completeSources); definitions = List.copyOf(definitions);
            Objects.requireNonNull(qualifiedToolsBuild); Objects.requireNonNull(tools);
            if (LEGACY_REQUEST_SCHEMA.equals(schema)) Objects.requireNonNull(defender, "Legacy requests retain their exact helper contract");
            else if ((stage == Stage.REGISTER) != (defender != null))
                throw new IllegalArgumentException("Version2 requires explicit null defender for ENV/BUILD and a complete helper runtime for REGISTER");
            if (completeSources.isEmpty() || definitions.size() > 512
                    || definitions.stream().map(Definition::option).distinct().count() != definitions.size()
                    || overlap(sourceRoot, buildRoot) || overlap(sourceRoot, scratchRoot) || overlap(buildRoot, scratchRoot)
                    || (stage != Stage.ENV) != (environmentActual != null) || (stage == Stage.REGISTER) != (buildActual != null))
                throw new IllegalArgumentException("Disjoint exact roots, complete sources and causal prior stages required");
        }
        public Path stageRoot() { return scratchRoot.resolve(stage.name().toLowerCase(Locale.ROOT)); }
    }
    public record Grant(String machineId, String ownerTask, Stage stage, ControlBuild.FileRef requestRef,
            ControlBuild.FileRef capacityEvidence, Instant deadline, long memoryLimitBytes, long outputAllocationLimitBytes,
            int timeoutSeconds) {
        public Grant {
            Objects.requireNonNull(machineId); Objects.requireNonNull(stage); Objects.requireNonNull(requestRef);
            Objects.requireNonNull(capacityEvidence); Objects.requireNonNull(deadline);
            if (ownerTask == null || !ownerTask.matches("/root(?:/[a-z0-9_-]+)*"))
                throw new IllegalArgumentException("Exact Root stage owner required");
            if (memoryLimitBytes < (64L << 20) || memoryLimitBytes > (4L << 30)
                    || outputAllocationLimitBytes < 4096 || timeoutSeconds < 1 || timeoutSeconds > 7200)
                throw new IllegalArgumentException("Finite native memory/storage/time authority required");
        }
    }
    /** Root supplies a live allocation/accounting guard. There is no JSON-only gate or default issuer. */
    public interface Gate {
        Grant acquire(Request request, ControlBuild.FileRef exactRequest) throws IOException;
        void revalidate(Grant grant, Path buildRoot, Path scratchRoot) throws IOException;
    }
    public record Command(CommandKind kind, List<String> argv, String cwd,
            WindowsJobProcess.ProcessIdentity owner, WindowsJobProcess.CommandResult terminal,
            ControlBuild.FileRef stdout, ControlBuild.FileRef stderr) {
        public Command { Objects.requireNonNull(kind); argv = List.copyOf(argv); Objects.requireNonNull(cwd); }
    }
    public record Actual(String schema, String machineId, Stage stage, Status status,
            String startedAtUtc, String observedAtUtc, ControlBuild.FileRef requestRef, Grant grant,
            List<Command> commands, List<SharedSourceFiles.Witness> sourceWitnesses,
            List<ControlBuild.FileRef> toolRefs, List<ControlBuild.FileRef> runtimeRefs,
            ControlBuild.FileRef snapshotRef, ControlBuild.FileRef manifestRef, ControlBuild.FileRef helperReceiptRef,
            List<ControlBuild.FileRef> graphRefs, List<ControlBuild.FileRef> dependencyRefs,
            List<ControlBuild.FileRef> outputRefs, boolean sourceUnchanged, String error) {
        public Actual {
            if (!ACTUAL_SCHEMA.equals(schema) || machineId == null || stage == null || status == null)
                throw new IllegalArgumentException("Exact bridge Actual protocol required");
            Instant.parse(startedAtUtc); Instant.parse(observedAtUtc); Objects.requireNonNull(requestRef); Objects.requireNonNull(grant);
            commands = List.copyOf(commands); sourceWitnesses = List.copyOf(sourceWitnesses);
            toolRefs = unique(toolRefs); runtimeRefs = unique(runtimeRefs); graphRefs = unique(graphRefs);
            dependencyRefs = unique(dependencyRefs); outputRefs = unique(outputRefs);
            if (status == Status.PASS && (error != null || !sourceUnchanged || commands.isEmpty()))
                throw new IllegalArgumentException("PASS needs original natural terminals and unchanged sources");
            if (status != Status.PASS && (error == null || error.isBlank())) throw new IllegalArgumentException("Failure must retain its actual cause");
        }
    }
    public record Evidence(Request request, Actual environment, Actual build, Actual registration,
            ControlBuild.FileRef bridgeDll, ControlBuild.FileRef injector, List<ControlBuild.FileRef> completeRefs) {
        public Evidence { completeRefs = unique(completeRefs); }
    }

    public static Request readRequest(ControlBuild.FileRef pin) throws IOException {
        return JSON.readValue(read(pin, MAX_JSON), Request.class);
    }
    /** Shape decoding only; historical Root/command qualification remains in readAccepted. */
    static Grant readGrantEnvelope(ControlBuild.FileRef pin) throws IOException {
        return JSON.readValue(read(pin, 131072), Grant.class);
    }
    static Actual readActualEnvelope(ControlBuild.FileRef pin) throws IOException {
        return JSON.readValue(read(pin, MAX_JSON), Actual.class);
    }
    public static ControlBuild.FileRef writeRequest(Request request, Path ownedRoot, Path output) throws IOException {
        requireCurrentRequest(request);
        inside(ownedRoot, output); validateSources(request); verifyRuntime(request);
        return writeNew(output, request);
    }

    /** Root opens the real OS/storage reservation; all stages use the one existing producer. */
    public static Actual executeRoot(ControlBuild.FileRef requestPin, NativeBridgeRootGate.Limits limits)
            throws IOException, InterruptedException {
        try (var gate = NativeBridgeRootGate.open(requestPin, limits)) { return execute(requestPin, gate); }
    }

    /** The only operation entry; a new one-shot stage directory is reserved before any child call. */
    public static Actual execute(ControlBuild.FileRef requestPin, Gate gate) throws IOException, InterruptedException {
        Request request = readRequest(requestPin); requireCurrentRequest(request); Objects.requireNonNull(gate);
        require(gate.getClass() == NativeBridgeRootGate.class, "The concrete live Root OS/storage gate is mandatory");
        require(request.machineId().equals(WindowsJobProcess.currentMachineId()), "Current machine differs");
        validateSources(request); var runtime = verifyRuntime(request); verify(request.tools().references());
        Grant grant = gate.acquire(request, requestPin);
        require(grant.machineId().equals(request.machineId()) && grant.stage() == request.stage()
                && grant.requestRef().equals(requestPin), "Live authority does not bind this exact native stage");
        Path stageRoot = request.stageRoot(); plainDirectory(request.scratchRoot());
        require(!Files.exists(stageRoot, LinkOption.NOFOLLOW_LINKS), "Stage already reserved; UNKNOWN is never repeated");
        check(gate, grant, request); Files.createDirectory(stageRoot); writeNew(stageRoot.resolve("INTENT.json"), grant);
        String started = Instant.now().toString(); List<Command> commands = new ArrayList<>();
        List<SharedSourceFiles.Witness> witnesses = observe(request.completeSources());
        List<ControlBuild.FileRef> graph = List.of(), dependencies = List.of(), outputs = List.of();
        ControlBuild.FileRef snapshot = null, manifest = null, helperReceipt = null;
        String failure = null; boolean unchanged = false; boolean interrupted = false;
        try {
            Map<String, String> environment;
            if (request.stage() == Stage.ENV) {
                environment = baseEnvironment(stageRoot); Path batch = stageRoot.resolve("capture.cmd");
                require(!batch.toString().matches(".*[\\s\"&|<>^%!].*"), "Exact static ENV batch path must be shell-safe");
                List<String> boot = NativeBuildEnvironment.bootstrapArguments(Path.of(request.tools().vcvars64().path()),
                        Path.of(request.tools().java().path()), runtime.completeDeployment().stream().map(row -> Path.of(row.path())).toList(),
                        stageRoot, request.machineId());
                Files.writeString(batch, "@echo off\r\n" + boot.getLast() + "\r\nexit /b %errorlevel%\r\n", StandardOpenOption.CREATE_NEW);
                run(request, grant, gate, commands, CommandKind.ENV_CAPTURE,
                        List.of(request.tools().cmd().path(), "/d", "/c", batch.toString()), environment, witnesses);
                snapshot = ControlBuild.FileRef.measure(stageRoot.resolve(NativeBuildEnvironment.SNAPSHOT_NAME));
                var observed = NativeBuildEnvironment.read(stageRoot, request.machineId(), read(snapshot, 65536));
                validateTools(request, observed); environment = nativeEnvironment(observed, stageRoot);
                run(request, grant, gate, commands, CommandKind.CMAKE_VERSION, List.of(request.tools().cmake().path(), "--version"), environment, witnesses);
                run(request, grant, gate, commands, CommandKind.NINJA_VERSION, List.of(request.tools().ninja().path(), "--version"), environment, witnesses);
                run(request, grant, gate, commands, CommandKind.COMPILER_HELP, List.of(request.tools().compiler().path(), "/?"), environment, witnesses);
                outputs = List.of(ControlBuild.FileRef.measure(batch));
            } else {
                Actual env = readAccepted(request.environmentActual(), Stage.ENV); Request envRequest = readRequest(env.requestRef());
                require(sameBuild(request, envRequest), "ENV belongs to another source/tool/build contract");
                snapshot = env.snapshotRef(); var observed = NativeBuildEnvironment.read(envRequest.stageRoot(), request.machineId(), read(snapshot, 65536));
                validateTools(request, observed); environment = nativeEnvironment(observed, stageRoot);
                if (request.stage() == Stage.BUILD) {
                    require(!Files.exists(request.buildRoot(), LinkOption.NOFOLLOW_LINKS), "A genuinely fresh bridge build root is required");
                    check(gate, grant, request); Files.createDirectory(request.buildRoot());
                    Path query = request.buildRoot().resolve(".cmake/api/v1/query/client-xar-defender-exe/codemodel-v2");
                    Files.createDirectories(query.getParent()); Files.write(query, new byte[0], StandardOpenOption.CREATE_NEW);
                    Files.write(query.resolveSibling("cmakeFiles-v1"), new byte[0], StandardOpenOption.CREATE_NEW);
                    run(request, grant, gate, commands, CommandKind.CONFIGURE, configureCommand(request), environment, witnesses);
                    run(request, grant, gate, commands, CommandKind.BRIDGE_BUILD, buildCommand(request), environment, witnesses);
                    run(request, grant, gate, commands, CommandKind.ACTIVE_DEPENDENCIES,
                            List.of(request.tools().ninja().path(), "-C", request.buildRoot().toString(), "-t", "deps"), environment, witnesses);
                    var model = NativeBridgeDefender.readGraph(request); graph = model.graphRefs();
                    outputs = List.of(model.bridgeDll(), model.injector());
                    dependencies = readDependencies(commands.getLast().stdout(), request.buildRoot());
                    require(!dependencies.isEmpty(), "Actual active compiler dependencies are required");
                } else {
                    Actual build = readAccepted(request.buildActual(), Stage.BUILD);
                    require(sameBuild(request, readRequest(build.requestRef())) && Objects.equals(build.snapshotRef(), snapshot),
                            "REGISTER must consume this exact completed bridge build and ENV");
                    var model = NativeBridgeDefender.readGraph(request); graph = model.graphRefs();
                    require(new HashSet<>(build.outputRefs()).equals(Set.of(model.bridgeDll(), model.injector())), "Build outputs drifted before registration");
                    NativeBridgeDefender.verifyHelperRuntime(request.canonicalRepository(), request.defender());
                    witnesses = mergeWitnesses(witnesses, observe(request.defender().references()));
                    manifest = NativeBridgeDefender.writeManifest(request, model, stageRoot.resolve("manifest.json"));
                    Path receipt = stageRoot.resolve("helper-receipt.json");
                    run(request, grant, gate, commands, CommandKind.DEFENDER_HELPER,
                            NativeBridgeDefender.command(request, manifest, receipt), environment, witnesses);
                    helperReceipt = ControlBuild.FileRef.measure(receipt);
                    var readback = NativeBridgeDefender.readVerified(helperReceipt, manifest, model.injector());
                    var withBroker = new ArrayList<>(graph); withBroker.addAll(readback.supplementalEvidence()); graph = merge(withBroker);
                    outputs = List.of(model.injector()); dependencies = build.dependencyRefs();
                }
            }
            assertSources(witnesses); validateSources(request); check(gate, grant, request); unchanged = true;
        } catch (InterruptedException error) { failure = error.toString(); interrupted = true; }
        catch (IOException | RuntimeException error) { failure = error.toString(); }
        finally {
            try { assertSources(witnesses); requestPin.verify(); verify(request.tools().references()); validateSources(request); }
            catch (IOException | RuntimeException error) { unchanged = false; failure = (failure == null ? "" : failure + "; ") + "postcheck: " + error; }
        }
        boolean unknown = commands.stream().anyMatch(row -> row.terminal() == null);
        Actual actual = new Actual(ACTUAL_SCHEMA, request.machineId(), request.stage(), failure == null ? Status.PASS : unknown ? Status.UNKNOWN : Status.RED,
                started, Instant.now().toString(), requestPin, grant, commands, witnesses, request.tools().references(), runtime.completeDeployment(),
                snapshot, manifest, helperReceipt, graph, dependencies, outputs, unchanged, failure);
        writeNew(stageRoot.resolve("ACTUAL.json"), actual);
        if (interrupted) Thread.currentThread().interrupt();
        return actual;
    }

    private static void run(Request request, Grant grant, Gate gate, List<Command> commands, CommandKind kind,
            List<String> argv, Map<String, String> environment, List<SharedSourceFiles.Witness> sources) throws IOException, InterruptedException {
        check(gate, grant, request); assertSources(sources);
        Path output = request.stageRoot().resolve(kind.name().toLowerCase(Locale.ROOT) + ".stdout.log");
        Path error = request.stageRoot().resolve(kind.name().toLowerCase(Locale.ROOT) + ".stderr.log");
        commands.add(new Command(kind, argv, request.stageRoot().toString(), null, null, null, null));
        WindowsJobProcess.ProcessIdentity ownerIdentity = null; WindowsJobProcess.CommandResult terminal = null;
        try (WindowsJobProcess owner = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(argv.getFirst()), argv.subList(1, argv.size()),
                request.stageRoot(), environment, output, error, grant.memoryLimitBytes()))) {
            ownerIdentity = owner.identity();
            commands.set(commands.size() - 1, new Command(kind, argv, request.stageRoot().toString(), ownerIdentity, null, null, null));
            terminal = owner.await(Duration.ofSeconds(grant.timeoutSeconds()), grant.deadline(), () -> {
                try { check(gate, grant, request); boundedLog(output); boundedLog(error); }
                catch (IOException failure) { throw new IllegalStateException(failure); }
            }, null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
        } finally {
            commands.set(commands.size() - 1, new Command(kind, argv, request.stageRoot().toString(), ownerIdentity, terminal,
                    measured(output), measured(error)));
        }
        require(terminal != null && terminal.passed(), "Native child failed, timed out, or retained Job members: " + kind);
    }

    public static Actual readAccepted(ControlBuild.FileRef pin, Stage expectedStage) throws IOException {
        Actual actual = readActualEnvelope(pin);
        Request request = readRequest(actual.requestRef());
        require(actual.stage() == expectedStage && request.stage() == expectedStage && actual.status() == Status.PASS
                && actual.machineId().equals(request.machineId()) && actual.machineId().equals(WindowsJobProcess.currentMachineId())
                && Path.of(pin.path()).equals(request.stageRoot().resolve("ACTUAL.json")), "Exact same-machine bridge stage Actual required");
        require(actual.grant().stage() == expectedStage && actual.grant().requestRef().equals(actual.requestRef())
                && actual.grant().machineId().equals(actual.machineId()), "Historical authority binding differs");
        Instant start = Instant.parse(actual.startedAtUtc()), observed = Instant.parse(actual.observedAtUtc());
        require(!observed.isBefore(start) && observed.isBefore(actual.grant().deadline()), "Actual terminal exceeds its original stage window");
        NativeBridgeRootGate.verifyHistorical(request, actual.grant(), start, observed);
        var intent = ControlBuild.FileRef.measure(request.stageRoot().resolve("INTENT.json"));
        require(readGrantEnvelope(intent).equals(actual.grant()),
                "Original one-shot stage INTENT differs from completed Root grant");
        actual.grant().capacityEvidence().verify(); validateSources(request);
        var tools = ControlBuild.verifiedCompletedReceipt(request.qualifiedToolsBuild());
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME && tools.machineId().equals(actual.machineId())
                && tools.mavenToolchain().selection() == ControlBuild.MavenSelection.DEFAULT_COMMAND && tools.javaExecutableRef().equals(request.tools().java())
                && tools.completeDeployment().equals(actual.runtimeRefs()) && request.tools().references().equals(actual.toolRefs()), "Native tool/runtime closure differs");
        verify(actual.runtimeRefs()); verify(actual.toolRefs()); assertSources(actual.sourceWitnesses());
        require(actual.sourceUnchanged() && actual.sourceWitnesses().stream().map(SharedSourceFiles.Witness::source).toList().containsAll(request.completeSources()),
                "Actual source witnesses are incomplete");
        validateCommands(request, actual);
        if (expectedStage == Stage.ENV) {
            require(actual.snapshotRef() != null && Path.of(actual.snapshotRef().path()).equals(request.stageRoot().resolve(NativeBuildEnvironment.SNAPSHOT_NAME)), "ENV snapshot missing");
            var snapshot = NativeBuildEnvironment.read(request.stageRoot(), request.machineId(), read(actual.snapshotRef(), 65536)); validateTools(request, snapshot);
            require(actual.outputRefs().size() == 1 && Path.of(actual.outputRefs().getFirst().path()).equals(request.stageRoot().resolve("capture.cmd")), "ENV batch original missing");
            String batch = Files.readString(Path.of(actual.outputRefs().getFirst().path()));
            List<String> boot = NativeBuildEnvironment.bootstrapArguments(Path.of(request.tools().vcvars64().path()), Path.of(request.tools().java().path()),
                    tools.completeDeployment().stream().map(row -> Path.of(row.path())).toList(), request.stageRoot(), request.machineId());
            require(batch.equals("@echo off\r\n" + boot.getLast() + "\r\nexit /b %errorlevel%\r\n"), "ENV command source differs");
        } else {
            Actual env = readAccepted(request.environmentActual(), Stage.ENV);
            require(sameBuild(request, readRequest(env.requestRef())) && Objects.equals(actual.snapshotRef(), env.snapshotRef()), "Actual ENV input is not the original completed stage");
            var model = NativeBridgeDefender.readGraph(request);
            if (expectedStage == Stage.BUILD) {
                require(model.graphRefs().equals(actual.graphRefs()), "Configured bridge graph differs");
                require(actual.outputRefs().equals(List.of(model.bridgeDll(), model.injector())), "Both real production bridge artifacts are required");
                require(!actual.dependencyRefs().isEmpty() && actual.dependencyRefs().equals(readDependencies(actual.commands().getLast().stdout(), request.buildRoot())), "Active compiler dependency closure differs");
            } else {
                Actual build = readAccepted(request.buildActual(), Stage.BUILD);
                require(sameBuild(request, readRequest(build.requestRef())) && build.dependencyRefs().equals(actual.dependencyRefs())
                        && actual.outputRefs().equals(List.of(model.injector())), "Registration build lineage differs");
                NativeBridgeDefender.verifyHelperRuntime(request.canonicalRepository(), request.defender());
                require(actual.sourceWitnesses().stream().map(SharedSourceFiles.Witness::source).toList().containsAll(request.defender().references()), "Helper runtime identity closure missing");
                NativeBridgeDefender.verifyManifest(request, model, actual.manifestRef());
                var readback = NativeBridgeDefender.readVerified(actual.helperReceiptRef(), actual.manifestRef(), model.injector());
                var withBroker = new ArrayList<>(model.graphRefs()); withBroker.addAll(readback.supplementalEvidence());
                require(merge(withBroker).equals(actual.graphRefs()), "Complete CMake/broker proof closure differs");
            }
        }
        verify(actual.graphRefs()); verify(actual.dependencyRefs()); verify(actual.outputRefs()); pin.verify(); return actual;
    }

    public static Evidence checkedEvidence(ControlBuild.FileRef environmentPin, ControlBuild.FileRef buildPin,
            ControlBuild.FileRef registrationPin) throws IOException {
        Actual env = readAccepted(environmentPin, Stage.ENV), build = readAccepted(buildPin, Stage.BUILD), registration = readAccepted(registrationPin, Stage.REGISTER);
        Request request = readRequest(registration.requestRef());
        require(request.environmentActual().equals(environmentPin) && request.buildActual().equals(buildPin)
                && readRequest(build.requestRef()).environmentActual().equals(environmentPin), "Three actual stages do not form one causal bridge build");
        var graph = NativeBridgeDefender.readGraph(request); var refs = new ArrayList<ControlBuild.FileRef>();
        refs.addAll(List.of(environmentPin, buildPin, registrationPin));
        for (Actual actual : List.of(env, build, registration)) {
            refs.add(actual.requestRef()); refs.addAll(NativeBridgeRootGate.evidenceReferences(actual.grant()));
            refs.add(ControlBuild.FileRef.measure(readRequest(actual.requestRef()).stageRoot().resolve("INTENT.json")));
            refs.addAll(actual.runtimeRefs()); refs.addAll(actual.toolRefs());
            refs.addAll(actual.sourceWitnesses().stream().map(SharedSourceFiles.Witness::source).toList()); refs.addAll(actual.graphRefs()); refs.addAll(actual.dependencyRefs()); refs.addAll(actual.outputRefs());
            for (ControlBuild.FileRef optional : new ControlBuild.FileRef[]{actual.snapshotRef(), actual.manifestRef(), actual.helperReceiptRef()}) if (optional != null) refs.add(optional);
            for (Command command : actual.commands()) { refs.add(command.stdout()); refs.add(command.stderr()); }
        }
        refs.add(request.qualifiedToolsBuild()); refs.addAll(request.completeSources()); refs.add(graph.bridgeDll()); refs.add(graph.injector());
        var tools = ControlBuild.verifiedCompletedReceipt(request.qualifiedToolsBuild());
        refs.addAll(tools.sourcePins()); refs.addAll(tools.compiledSourcePins()); refs.addAll(tools.producerRuntimePins());
        refs.addAll(tools.completeDeployment()); refs.add(tools.capacityReleaseRef()); refs.add(tools.javaExecutableRef());
        refs.add(tools.mavenToolchain().distributionLauncherRef());
        if (tools.mavenToolchain().explicitOverrideRef() != null) refs.add(tools.mavenToolchain().explicitOverrideRef());
        List<ControlBuild.FileRef> closure = merge(refs); verify(closure);
        return new Evidence(request, env, build, registration, graph.bridgeDll(), graph.injector(), closure);
    }

    public static List<String> configureCommand(Request request) {
        var argv = new ArrayList<>(List.of(request.tools().cmake().path(), "-S", request.sourceRoot().toString(), "-B", request.buildRoot().toString(),
                "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=OFF", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                "-DCMAKE_MAKE_PROGRAM=" + request.tools().ninja().path(), "-DCMAKE_CXX_COMPILER=" + request.tools().compiler().path(),
                "-DCMAKE_C_COMPILER=" + request.tools().compiler().path()));
        request.definitions().forEach(item -> argv.add("-D" + item.option() + "=" + item.value().name())); return List.copyOf(argv);
    }
    public static List<String> buildCommand(Request request) {
        return List.of(request.tools().cmake().path(), "--build", request.buildRoot().toString(), "--parallel", Integer.toString(request.parallelJobs()),
                "--target", TARGETS.get(0), TARGETS.get(1));
    }
    static void validateCommands(Request request, Actual actual) throws IOException {
        List<CommandKind> expected = switch (request.stage()) {
            case ENV -> List.of(CommandKind.ENV_CAPTURE, CommandKind.CMAKE_VERSION, CommandKind.NINJA_VERSION, CommandKind.COMPILER_HELP);
            case BUILD -> List.of(CommandKind.CONFIGURE, CommandKind.BRIDGE_BUILD, CommandKind.ACTIVE_DEPENDENCIES);
            case REGISTER -> List.of(CommandKind.DEFENDER_HELPER);
        };
        require(actual.commands().stream().map(Command::kind).toList().equals(expected), "Exact native command sequence required");
        for (Command command : actual.commands()) {
            List<String> argv = switch (command.kind()) {
                case ENV_CAPTURE -> List.of(request.tools().cmd().path(), "/d", "/c", request.stageRoot().resolve("capture.cmd").toString());
                case CMAKE_VERSION -> List.of(request.tools().cmake().path(), "--version");
                case NINJA_VERSION -> List.of(request.tools().ninja().path(), "--version");
                case COMPILER_HELP -> List.of(request.tools().compiler().path(), "/?");
                case CONFIGURE -> configureCommand(request);
                case BRIDGE_BUILD -> buildCommand(request);
                case ACTIVE_DEPENDENCIES -> List.of(request.tools().ninja().path(), "-C", request.buildRoot().toString(), "-t", "deps");
                case DEFENDER_HELPER -> NativeBridgeDefender.command(request, actual.manifestRef(), request.stageRoot().resolve("helper-receipt.json"));
            };
            require(command.argv().equals(argv) && command.cwd().equals(request.stageRoot().toString()) && command.owner() != null
                    && command.terminal() != null && command.owner().equals(command.terminal().identity()) && command.terminal().passed()
                    && Path.of(command.owner().executable()).equals(Path.of(argv.getFirst()))
                    && command.terminal().accounting().memoryLimitBytes() == actual.grant().memoryLimitBytes(), "Original exact command owner/exit/timeout/Job0 required");
            require(command.stdout() != null && command.stderr() != null
                    && Path.of(command.stdout().path()).equals(request.stageRoot().resolve(command.kind().name().toLowerCase(Locale.ROOT) + ".stdout.log"))
                    && Path.of(command.stderr().path()).equals(request.stageRoot().resolve(command.kind().name().toLowerCase(Locale.ROOT) + ".stderr.log")), "Original command output paths differ");
            command.stdout().verify(); command.stderr().verify();
        }
    }
    private static ControlBuild.BuildReceipt verifyRuntime(Request request) throws IOException {
        var tools = ControlBuild.verifiedCompletedReceipt(request.qualifiedToolsBuild());
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME && tools.machineId().equals(request.machineId())
                && tools.mavenToolchain().selection() == ControlBuild.MavenSelection.DEFAULT_COMMAND
                && tools.javaExecutableRef().equals(request.tools().java()) && tools.completeDeployment().equals(ControlBuild.producerClosure()), "Exact actually loaded qualified tools runtime required");
        for (Class<?> type : List.of(NativeBridgeBuild.class, NativeBridgeRootGate.class, NativeBridgeDefender.class, NativeBuildEnvironment.class, RootNativePlanJson.class, WindowsJobProcess.class)) {
            try { require(tools.completeDeployment().contains(ControlBuild.FileRef.measure(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()))), "Native producer class is outside qualified runtime"); }
            catch (java.net.URISyntaxException error) { throw new IOException(error); }
        }
        return tools;
    }
    static void validateSources(Request request) throws IOException {
        require(request.completeSources().equals(inventory(request.sourceRoot())), "Complete frozen source tree differs; build outputs cannot be mixed into it");
        Path cmake = request.sourceRoot().resolve("CMakeLists.txt"); require(Files.isRegularFile(cmake), "Project CMake source missing");
        Set<String> options = new HashSet<>();
        var pattern = Pattern.compile("(?m)\\boption\\s*\\(\\s*(XAR_[A-Z0-9_]+)\\b");
        for (ControlBuild.FileRef file : request.completeSources()) if (file.path().endsWith("CMakeLists.txt") || file.path().endsWith(".cmake")) {
            require(file.bytes() <= (2 << 20), "Bounded reviewed CMake source required"); var matches = pattern.matcher(Files.readString(Path.of(file.path())));
            while (matches.find()) options.add(matches.group(1));
        }
        for (Definition item : request.definitions()) require(options.contains(item.option()), "Unknown source option cannot enter configure argv");
    }
    public static List<ControlBuild.FileRef> inventory(Path root) throws IOException {
        plainDirectory(root); var refs = new ArrayList<ControlBuild.FileRef>();
        try (var stream = Files.walk(root)) {
            var iterator = stream.iterator(); int entries = 0;
            while (iterator.hasNext()) {
                Path file = iterator.next(); require(++entries <= MAX_FILES * 2, "Finite ordinary source/runtime tree required"); SharedSourceFiles.plainAncestors(file);
                if (Files.isDirectory(file, LinkOption.NOFOLLOW_LINKS)) continue;
                require(Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS), "Nonordinary source/runtime file rejected"); refs.add(ControlBuild.FileRef.measure(file));
                require(refs.size() <= MAX_FILES, "Source/runtime inventory exceeds finite bound");
            }
        }
        return unique(refs.stream().sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList());
    }
    private static void validateTools(Request request, NativeBuildEnvironment.Snapshot snapshot) throws IOException {
        var values = snapshot.values(); Path system = Path.of(values.get("SystemRoot"));
        require(Path.of(request.tools().cmd().path()).equals(system.resolve("System32/cmd.exe")), "CMD is not the captured system tool");
        Path compilerRoot = Path.of(values.get("VCToolsInstallDir")).resolve("bin/Hostx64/x64");
        require(Path.of(request.tools().compiler().path()).equals(compilerRoot.resolve("cl.exe"))
                && Path.of(request.tools().linker().path()).equals(compilerRoot.resolve("link.exe")), "Compiler/linker do not match the captured x64 vcvars installation");
        Path vs = Path.of(Objects.requireNonNull(values.get("VSINSTALLDIR")));
        require(Path.of(request.tools().vcvars64().path()).equals(vs.resolve("VC/Auxiliary/Build/vcvars64.bat"))
                && Path.of(request.tools().cmake().path()).equals(vs.resolve("Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"))
                && Path.of(request.tools().ninja().path()).equals(vs.resolve("Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe")), "CMake/Ninja/vcvars source installation differs");
    }
    private static Map<String, String> baseEnvironment(Path temporary) {
        var values = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER); values.putAll(System.getenv()); clean(values, temporary); return Map.copyOf(values);
    }
    private static Map<String, String> nativeEnvironment(NativeBuildEnvironment.Snapshot snapshot, Path temporary) {
        var values = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER); values.putAll(snapshot.values()); clean(values, temporary); return Map.copyOf(values);
    }
    private static void clean(Map<String, String> values, Path temporary) {
        for (String key : List.of("CL", "_CL_", "LINK", "_LINK_", "PYTHONPATH", "PYTHONHOME", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS")) values.remove(key);
        for (String key : List.of("TEMP", "TMP", "TMPDIR")) values.put(key, temporary.toString());
        values.put("VSLANG", "1033"); values.put("PYTHONDONTWRITEBYTECODE", "1"); values.put("PYTHONNOUSERSITE", "1");
    }
    private static List<ControlBuild.FileRef> readDependencies(ControlBuild.FileRef raw, Path buildRoot) throws IOException {
        var refs = new ArrayList<ControlBuild.FileRef>();
        for (String line : new String(read(raw, 16 << 20), StandardCharsets.UTF_8).split("\\R")) if (line.startsWith("    ")) {
            String value = line.strip(); if (value.isEmpty()) continue; Path path = Path.of(value);
            if (!path.isAbsolute()) path = buildRoot.resolve(path).normalize(); SharedSourceFiles.plainAncestors(path); refs.add(ControlBuild.FileRef.measure(path));
        }
        return merge(refs);
    }
    /** A new stage cannot use a historical request to obtain a live reservation or create an INTENT. */
    static void requireCurrentRequest(Request request) throws IOException {
        Objects.requireNonNull(request);
        require(REQUEST_SCHEMA.equals(request.schema()), "Legacy native request is historical read-only; version2 required for new stage execution");
    }
    /** Shared plan identity; version2 registration authority belongs only to its REGISTER stage. */
    static boolean sameBuild(Request left, Request right) {
        boolean sameDefender = Objects.equals(left.defender(), right.defender());
        if (REQUEST_SCHEMA.equals(left.schema()) && left.stage() != right.stage()) sameDefender = true;
        return left.schema().equals(right.schema()) && left.machineId().equals(right.machineId()) && left.canonicalRepository().equals(right.canonicalRepository())
                && left.sourceRoot().equals(right.sourceRoot()) && left.completeSources().equals(right.completeSources())
                && left.buildRoot().equals(right.buildRoot()) && left.scratchRoot().equals(right.scratchRoot())
                && left.qualifiedToolsBuild().equals(right.qualifiedToolsBuild()) && left.tools().equals(right.tools())
                && left.definitions().equals(right.definitions()) && left.parallelJobs() == right.parallelJobs() && sameDefender;
    }
    private static void check(Gate gate, Grant grant, Request request) throws IOException {
        require(Instant.now().isBefore(grant.deadline()), "Native stage authority expired"); grant.capacityEvidence().verify();
        gate.revalidate(grant, request.buildRoot(), request.scratchRoot());
    }
    private static List<SharedSourceFiles.Witness> observe(List<ControlBuild.FileRef> refs) throws IOException {
        var result = new ArrayList<SharedSourceFiles.Witness>(); for (var pin : refs) { var witness = SharedSourceFiles.observe(Path.of(pin.path())); require(witness.source().equals(pin), "Observed native input differs"); result.add(witness); } return List.copyOf(result);
    }
    private static List<SharedSourceFiles.Witness> mergeWitnesses(List<SharedSourceFiles.Witness> left, List<SharedSourceFiles.Witness> right) {
        var result = new LinkedHashMap<String, SharedSourceFiles.Witness>(); for (var list : List.of(left, right)) for (var item : list) result.putIfAbsent(item.source().path(), item); return List.copyOf(result.values());
    }
    private static void assertSources(List<SharedSourceFiles.Witness> witnesses) throws IOException { for (var witness : witnesses) SharedSourceFiles.assertUnchanged(witness); }
    static void verify(List<ControlBuild.FileRef> refs) throws IOException { for (var ref : refs) ref.verify(); }
    static List<ControlBuild.FileRef> unique(List<ControlBuild.FileRef> refs) {
        Objects.requireNonNull(refs); var result = List.copyOf(refs);
        if (result.size() > MAX_FILES || result.stream().map(row -> row.path().toLowerCase(Locale.ROOT)).distinct().count() != result.size()) throw new IllegalArgumentException("Finite unique exact pins required"); return result;
    }
    static List<ControlBuild.FileRef> merge(List<ControlBuild.FileRef> refs) throws IOException {
        var result = new TreeMap<String, ControlBuild.FileRef>();
        for (var pin : refs) { var old = result.putIfAbsent(pin.path().toLowerCase(Locale.ROOT), pin); require(old == null || old.equals(pin), "Conflicting evidence pins"); }
        return unique(result.values().stream().sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList());
    }
    static byte[] read(ControlBuild.FileRef ref, int maximum) throws IOException {
        require(ref != null && ref.bytes() >= 0 && ref.bytes() <= maximum, "Bounded pinned native evidence required"); ref.verify();
        byte[] bytes = Files.readAllBytes(Path.of(ref.path())); require(bytes.length == ref.bytes(), "Native evidence size changed"); ref.verify(); return bytes;
    }
    static ControlBuild.FileRef writeNew(Path path, Object value) throws IOException {
        SharedSourceFiles.plainAncestors(path.getParent()); byte[] bytes = JSON.writeValueAsBytes(value);
        require(bytes.length <= MAX_JSON, "Native metadata exceeds finite bound"); Files.write(path, bytes, StandardOpenOption.CREATE_NEW); return ControlBuild.FileRef.measure(path);
    }
    private static void boundedLog(Path path) throws IOException { if (Files.exists(path)) require(Files.size(path) <= (16L << 20), "Native output log exceeded bound"); }
    private static ControlBuild.FileRef measured(Path path) throws IOException { return Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) ? ControlBuild.FileRef.measure(path) : null; }
    static Path absolute(Path path) { Objects.requireNonNull(path); if (!path.isAbsolute() || !path.equals(path.toAbsolutePath().normalize())) throw new IllegalArgumentException("Canonical absolute path required"); return path; }
    private static boolean overlap(Path left, Path right) { return left.startsWith(right) || right.startsWith(left); }
    static void plainDirectory(Path path) throws IOException { SharedSourceFiles.plainAncestors(path); require(Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS) && path.toRealPath().equals(path), "Plain canonical directory required"); }
    static void inside(Path root, Path path) throws IOException { absolute(root); absolute(path); require(path.startsWith(root) && !path.equals(root), "Output escapes exact owned root"); SharedSourceFiles.plainAncestors(path.getParent()); }
    static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
}
