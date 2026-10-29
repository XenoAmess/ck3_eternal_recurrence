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
    public static final String REGISTER_REQUEST_SCHEMA = "xar.native-bridge-build-request/v3";
    public static final String BOUND_REQUEST_SCHEMA = "xar.native-bridge-build-request/v4";
    public static final String LEGACY_REQUEST_SCHEMA = "xar.native-bridge-build-request/v1";
    public static final String LEGACY_ACTUAL_SCHEMA = "xar.native-bridge-build-actual/v2";
    public static final String ACTUAL_SCHEMA = "xar.native-bridge-build-actual/v3";
    public static final List<String> TARGETS = List.of("xar_ck3_bridge", "xar_ck3_bridge_injector");
    static final long MAX_MEMORY_LIMIT_BYTES = 8L << 30;
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
            NativeBridgeDefender.Runtime defender, ControlBuild.FileRef compileSourceBindingRef) {
        public Request {
            if ((!REQUEST_SCHEMA.equals(schema) && !LEGACY_REQUEST_SCHEMA.equals(schema) && !REGISTER_REQUEST_SCHEMA.equals(schema) && !BOUND_REQUEST_SCHEMA.equals(schema)) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}")
                    || machineId.equals("unknown") || stage == null || parallelJobs < 1 || parallelJobs > 64)
                throw new IllegalArgumentException("Versioned finite bridge request required");
            canonicalRepository = absolute(canonicalRepository); sourceRoot = absolute(sourceRoot);
            buildRoot = absolute(buildRoot); scratchRoot = absolute(scratchRoot);
            completeSources = unique(completeSources); definitions = List.copyOf(definitions);
            Objects.requireNonNull(qualifiedToolsBuild); Objects.requireNonNull(tools);
            if (BOUND_REQUEST_SCHEMA.equals(schema)) {
                Objects.requireNonNull(compileSourceBindingRef, "Version4 requires the complete retained/compile binding");
                if ((stage == Stage.REGISTER) != (defender != null)
                        || (stage == Stage.REGISTER && !(defender instanceof NativeBridgeDefender.ManifestRuntime)))
                    throw new IllegalArgumentException("Version4 requires null runtime for ENV/BUILD and complete manifest runtime for REGISTER");
            } else if (LEGACY_REQUEST_SCHEMA.equals(schema)) {
                if(!(defender instanceof NativeBridgeDefender.HelperRuntime))throw new IllegalArgumentException("Legacy requests retain exact six-field helper contract");
            }else if(REGISTER_REQUEST_SCHEMA.equals(schema)){
                if(stage!=Stage.REGISTER||!(defender instanceof NativeBridgeDefender.ManifestRuntime))
                    throw new IllegalArgumentException("Version3 is solely REGISTER with complete versioned manifest runtime");
            }else{
                if((stage==Stage.REGISTER)!=(defender!=null))
                    throw new IllegalArgumentException("Version2 requires explicit null defender for ENV/BUILD and a complete helper runtime for REGISTER");
                if(stage==Stage.REGISTER&&!(defender instanceof NativeBridgeDefender.HelperRuntime))
                    throw new IllegalArgumentException("Historical version2 registration retains its exact six-field helper");
            }
            if (!BOUND_REQUEST_SCHEMA.equals(schema) && compileSourceBindingRef != null)
                throw new IllegalArgumentException("Historical request versions cannot acquire a compile-source binding");
            if (completeSources.isEmpty() || definitions.size() > 512
                    || definitions.stream().map(Definition::option).distinct().count() != definitions.size()
                    || overlap(sourceRoot, buildRoot) || overlap(sourceRoot, scratchRoot) || overlap(buildRoot, scratchRoot)
                    || (stage != Stage.ENV) != (environmentActual != null) || (stage == Stage.REGISTER) != (buildActual != null))
                throw new IllegalArgumentException("Disjoint exact roots, complete sources and causal prior stages required");
        }
        /** Retained source binding is an explicit version4 field; old Java callers keep their exact version. */
        public Request(String schema,String machineId,Stage stage,Path canonicalRepository,Path sourceRoot,List<ControlBuild.FileRef> completeSources,
                Path buildRoot,Path scratchRoot,ControlBuild.FileRef qualifiedToolsBuild,Toolchain tools,List<Definition> definitions,
                int parallelJobs,ControlBuild.FileRef environmentActual,ControlBuild.FileRef buildActual,NativeBridgeDefender.Runtime defender){
            this(schema,machineId,stage,canonicalRepository,sourceRoot,completeSources,buildRoot,scratchRoot,qualifiedToolsBuild,tools,definitions,
                    parallelJobs,environmentActual,buildActual,defender,null);
        }
        /** Historical construction compatibility; no constructor can bypass requireCurrentRequest. */
        public Request(String schema,String machineId,Stage stage,Path canonicalRepository,Path sourceRoot,List<ControlBuild.FileRef> completeSources,
                Path buildRoot,Path scratchRoot,ControlBuild.FileRef qualifiedToolsBuild,Toolchain tools,List<Definition> definitions,
                int parallelJobs,ControlBuild.FileRef environmentActual,ControlBuild.FileRef buildActual,NativeBridgeDefender.HelperRuntime defender){
            this(schema,machineId,stage,canonicalRepository,sourceRoot,completeSources,buildRoot,scratchRoot,qualifiedToolsBuild,tools,definitions,
                    parallelJobs,environmentActual,buildActual,(NativeBridgeDefender.Runtime)defender);
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
            if (memoryLimitBytes < (64L << 20) || memoryLimitBytes > NativeBridgeBuild.MAX_MEMORY_LIMIT_BYTES
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
    public record AuxiliaryCommand(CommandKind kind, MsvcAuxiliaryPolicy.Outcome outcome) {
        public AuxiliaryCommand {
            Objects.requireNonNull(kind); Objects.requireNonNull(outcome);
            if (!usesMsvc(kind)) throw new IllegalArgumentException("Only the actual compiler/configure/build command has an MSVC outcome");
        }
    }
    public record Actual(String schema, String machineId, Stage stage, Status status,
            String startedAtUtc, String observedAtUtc, ControlBuild.FileRef requestRef, Grant grant,
            List<Command> commands, List<SharedSourceFiles.Witness> sourceWitnesses,
            List<ControlBuild.FileRef> toolRefs, List<ControlBuild.FileRef> runtimeRefs,
            ControlBuild.FileRef snapshotRef, ControlBuild.FileRef manifestRef, ControlBuild.FileRef helperReceiptRef,
            List<ControlBuild.FileRef> graphRefs, List<ControlBuild.FileRef> dependencyRefs,
            List<ControlBuild.FileRef> outputRefs, boolean sourceUnchanged, String error,
            List<AuxiliaryCommand> auxiliaryCommands) {
        public Actual {
            if ((!ACTUAL_SCHEMA.equals(schema) && !LEGACY_ACTUAL_SCHEMA.equals(schema)) || machineId == null || stage == null || status == null)
                throw new IllegalArgumentException("Exact bridge Actual protocol required");
            Instant.parse(startedAtUtc); Instant.parse(observedAtUtc); Objects.requireNonNull(requestRef); Objects.requireNonNull(grant);
            commands = List.copyOf(commands); sourceWitnesses = List.copyOf(sourceWitnesses);
            toolRefs = unique(toolRefs); runtimeRefs = unique(runtimeRefs); graphRefs = unique(graphRefs);
            dependencyRefs = unique(dependencyRefs); outputRefs = unique(outputRefs);
            auxiliaryCommands = List.copyOf(auxiliaryCommands);
            if (LEGACY_ACTUAL_SCHEMA.equals(schema) && !auxiliaryCommands.isEmpty())
                throw new IllegalArgumentException("Historical native Actual cannot acquire new auxiliary completion evidence");
            if (status == Status.PASS && (error != null || !sourceUnchanged || commands.isEmpty()))
                throw new IllegalArgumentException("PASS needs original completed terminals and unchanged sources");
            if (status != Status.PASS && (error == null || error.isBlank())) throw new IllegalArgumentException("Failure must retain its actual cause");
        }
        public Actual(String schema, String machineId, Stage stage, Status status,
                String startedAtUtc, String observedAtUtc, ControlBuild.FileRef requestRef, Grant grant,
                List<Command> commands, List<SharedSourceFiles.Witness> sourceWitnesses,
                List<ControlBuild.FileRef> toolRefs, List<ControlBuild.FileRef> runtimeRefs,
                ControlBuild.FileRef snapshotRef, ControlBuild.FileRef manifestRef, ControlBuild.FileRef helperReceiptRef,
                List<ControlBuild.FileRef> graphRefs, List<ControlBuild.FileRef> dependencyRefs,
                List<ControlBuild.FileRef> outputRefs, boolean sourceUnchanged, String error) {
            this(schema, machineId, stage, status, startedAtUtc, observedAtUtc, requestRef, grant, commands,
                    sourceWitnesses, toolRefs, runtimeRefs, snapshotRef, manifestRef, helperReceiptRef,
                    graphRefs, dependencyRefs, outputRefs, sourceUnchanged, error, List.of());
        }
    }
    public record Evidence(Request request, Actual environment, Actual build, Actual registration,
            ControlBuild.FileRef bridgeDll, ControlBuild.FileRef injector, List<ControlBuild.FileRef> completeRefs) {
        public Evidence { completeRefs = unique(completeRefs); }
    }

    public static Request readRequest(ControlBuild.FileRef pin) throws IOException {
        JsonNode node = JSON.readTree(read(pin, MAX_JSON));
        // Only the three old tags predate this field. No other missing creator is synthesized.
        if (node.isObject() && Set.of(LEGACY_REQUEST_SCHEMA, REQUEST_SCHEMA, REGISTER_REQUEST_SCHEMA).contains(node.path("schema").asText())
                && !node.has("compile_source_binding_ref"))
            ((com.fasterxml.jackson.databind.node.ObjectNode) node).putNull("compile_source_binding_ref");
        return JSON.treeToValue(node, Request.class);
    }
    /** Shape decoding only; historical Root/command qualification remains in readAccepted. */
    static Grant readGrantEnvelope(ControlBuild.FileRef pin) throws IOException {
        return JSON.readValue(read(pin, 131072), Grant.class);
    }
    static Actual readActualEnvelope(ControlBuild.FileRef pin) throws IOException {
        JsonNode node = JSON.readTree(read(pin, MAX_JSON));
        if (node.isObject() && LEGACY_ACTUAL_SCHEMA.equals(node.path("schema").asText()) && !node.has("auxiliary_commands"))
            ((com.fasterxml.jackson.databind.node.ObjectNode) node).putArray("auxiliary_commands");
        return JSON.treeToValue(node, Actual.class);
    }
    public static ControlBuild.FileRef writeRequest(Request request, Path ownedRoot, Path output) throws IOException {
        requireCurrentRequest(request);
        inside(ownedRoot, output); validateSources(request); verifyRuntime(request);
        var before = observeRequestSources(request); var result = writeNew(output, request);
        assertLiveSourceBinding(request, before); return result;
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
        List<AuxiliaryCommand> auxiliaryCommands = new ArrayList<>();
        List<SharedSourceFiles.Witness> witnesses = observeRequestSources(request);
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
                List<SharedSourceFiles.Witness> bindingSources = witnesses;
                Runnable bindingGuard = () -> {
                    try { check(gate, grant, request); assertSources(bindingSources); }
                    catch (IOException failureBeforeCompiler) { throw new IllegalStateException(failureBeforeCompiler); }
                };
                var compilerBinding = MsvcAuxiliaryPolicy.bind(Path.of(request.tools().compiler().path()), grant.deadline(), bindingGuard);
                compilerBinding.requireCompiler(request.tools().compiler());
                runMsvc(request, grant, gate, commands, CommandKind.COMPILER_HELP, compilerHelpCommand(request), environment,
                        witnesses, compilerBinding, auxiliaryCommands);
                outputs = List.of(ControlBuild.FileRef.measure(batch));
            } else {
                Actual env = readAccepted(request.environmentActual(), Stage.ENV); Request envRequest = readRequest(env.requestRef());
                require(ACTUAL_SCHEMA.equals(env.schema()), "New native execution requires the original MSVC-qualified ENV Actual");
                require(sameBuild(request, envRequest), "ENV belongs to another source/tool/build contract");
                snapshot = env.snapshotRef(); var observed = NativeBuildEnvironment.read(envRequest.stageRoot(), request.machineId(), read(snapshot, 65536));
                validateTools(request, observed); environment = nativeEnvironment(observed, stageRoot);
                if (request.stage() == Stage.BUILD) {
                    var compilerBinding = environmentCompilerBinding(env);
                    check(gate, grant, request); prepareBuildRoot(request);
                    Path query = request.buildRoot().resolve(".cmake/api/v1/query/client-xar-defender-exe/codemodel-v2");
                    Files.createDirectories(query.getParent()); prepareQuery(query);
                    prepareQuery(query.resolveSibling("cmakeFiles-v1"));
                    runMsvc(request, grant, gate, commands, CommandKind.CONFIGURE, configureCommand(request), environment,
                            witnesses, compilerBinding, auxiliaryCommands);
                    runMsvc(request, grant, gate, commands, CommandKind.BRIDGE_BUILD, buildCommand(request), environment,
                            witnesses, compilerBinding, auxiliaryCommands);
                    run(request, grant, gate, commands, CommandKind.ACTIVE_DEPENDENCIES,
                            List.of(request.tools().ninja().path(), "-C", request.buildRoot().toString(), "-t", "deps"), environment, witnesses);
                    var model = NativeBridgeDefender.readGraph(request); graph = model.graphRefs();
                    outputs = List.of(model.bridgeDll(), model.injector());
                    dependencies = readDependencies(commands.getLast().stdout(), request);
                    require(!dependencies.isEmpty(), "Actual active compiler dependencies are required");
                } else {
                    Actual build = readAccepted(request.buildActual(), Stage.BUILD);
                    require(ACTUAL_SCHEMA.equals(build.schema()), "New registration requires the MSVC-qualified production BUILD Actual");
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
            assertSources(witnesses); assertLiveSourceBinding(request, witnesses); validateSources(request); check(gate, grant, request); unchanged = true;
        } catch (InterruptedException error) { failure = error.toString(); interrupted = true; }
        catch (IOException | RuntimeException error) { failure = error.toString(); }
        finally {
            try { assertSources(witnesses); assertLiveSourceBinding(request, witnesses); requestPin.verify(); verify(request.tools().references()); validateSources(request); }
            catch (IOException | RuntimeException error) { unchanged = false; failure = (failure == null ? "" : failure + "; ") + "postcheck: " + error; }
            if(request.stage()==Stage.REGISTER && request.defender() instanceof NativeBridgeDefender.ManifestRuntime){
                try{NativeBridgeDefender.verifyHelperRuntime(request.canonicalRepository(),request.defender());}
                catch(IOException|RuntimeException error){unchanged=false;failure=(failure==null?"":failure+"; ")+"complete runtime postcheck: "+error;}
            }
        }
        boolean unknown = commands.stream().anyMatch(row -> row.terminal() == null);
        Actual actual = new Actual(ACTUAL_SCHEMA, request.machineId(), request.stage(), failure == null ? Status.PASS : unknown ? Status.UNKNOWN : Status.RED,
                started, Instant.now().toString(), requestPin, grant, commands, witnesses, request.tools().references(), runtime.completeDeployment(),
                snapshot, manifest, helperReceipt, graph, dependencies, outputs, unchanged, failure, auxiliaryCommands);
        writeNew(stageRoot.resolve("ACTUAL.json"), actual);
        if (interrupted) Thread.currentThread().interrupt();
        return actual;
    }

    private static void run(Request request, Grant grant, Gate gate, List<Command> commands, CommandKind kind,
            List<String> argv, Map<String, String> environment, List<SharedSourceFiles.Witness> sources) throws IOException, InterruptedException {
        run(request, grant, gate, commands, kind, argv, environment, sources, null, null);
    }
    private static void runMsvc(Request request, Grant grant, Gate gate, List<Command> commands, CommandKind kind,
            List<String> argv, Map<String, String> environment, List<SharedSourceFiles.Witness> sources,
            MsvcAuxiliaryPolicy.Binding compilerBinding, List<AuxiliaryCommand> auxiliaryCommands) throws IOException, InterruptedException {
        require(usesMsvc(kind), "Explicit MSVC completion is limited to compiler/configure/build");
        compilerBinding.requireCompiler(request.tools().compiler());
        ControlBuild.FileRef root = kind == CommandKind.COMPILER_HELP ? request.tools().compiler() : request.tools().cmake();
        var execution = new MsvcAuxiliaryPolicy.ExecutionBinding("xar.exact-msvc-owned-execution/v1", compilerBinding, root);
        execution.requireRequest(root, request.tools().references());
        require(argv.getFirst().equals(root.path()), "MSVC completion root differs from the exact command");
        run(request, grant, gate, commands, kind, argv, environment, sources, execution, auxiliaryCommands);
    }
    private static void run(Request request, Grant grant, Gate gate, List<Command> commands, CommandKind kind,
            List<String> argv, Map<String, String> environment, List<SharedSourceFiles.Witness> sources,
            MsvcAuxiliaryPolicy.ExecutionBinding execution, List<AuxiliaryCommand> auxiliaryCommands) throws IOException, InterruptedException {
        check(gate, grant, request); assertSources(sources);
        Path output = request.stageRoot().resolve(kind.name().toLowerCase(Locale.ROOT) + ".stdout.log");
        Path error = request.stageRoot().resolve(kind.name().toLowerCase(Locale.ROOT) + ".stderr.log");
        commands.add(new Command(kind, argv, request.stageRoot().toString(), null, null, null, null));
        WindowsJobProcess.ProcessIdentity ownerIdentity = null; WindowsJobProcess.CommandResult terminal = null;
        Runnable periodic = () -> {
            try { check(gate, grant, request); boundedLog(output); boundedLog(error); }
            catch (IOException failure) { throw new IllegalStateException(failure); }
        };
        int auxiliaryIndex = execution == null ? -1 : auxiliaryCommands.size();
        if (execution != null) auxiliaryCommands.add(new AuxiliaryCommand(kind,
                MsvcAuxiliaryPolicy.notEntered(execution, "Original native command has not entered MSVC completion")));
        try (var heldImages = execution == null ? null : MsvcAuxiliaryPolicy.retain(execution, grant.deadline(), periodic);
                WindowsJobProcess owner = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(argv.getFirst()), argv.subList(1, argv.size()),
                request.stageRoot(), environment, output, error, grant.memoryLimitBytes()))) {
            ownerIdentity = owner.identity();
            commands.set(commands.size() - 1, new Command(kind, argv, request.stageRoot().toString(), ownerIdentity, null, null, null));
            if (heldImages == null) {
                terminal = owner.await(Duration.ofSeconds(grant.timeoutSeconds()), grant.deadline(), periodic,
                        null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
            } else {
                var awaited = owner.awaitWithMsvcAuxiliaries(Duration.ofSeconds(grant.timeoutSeconds()), grant.deadline(),
                        periodic, request.stageRoot().resolve(kind.name().toLowerCase(Locale.ROOT) + ".before-cleanup.json"), heldImages);
                terminal = awaited.original().commandResult();
                auxiliaryCommands.set(auxiliaryIndex, new AuxiliaryCommand(kind, awaited.auxiliaryCleanup()));
            }
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
        verify(actual.runtimeRefs()); verify(actual.toolRefs()); assertHistoricalSourceWitnesses(request, actual.sourceWitnesses());
        require(actual.sourceUnchanged() && actual.sourceWitnesses().stream().map(SharedSourceFiles.Witness::source).toList().containsAll(request.completeSources()),
                "Actual source witnesses are incomplete");
        validateCommands(request, actual);
        if (ACTUAL_SCHEMA.equals(actual.schema())) verifyAuxiliaryImages(actual);
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
            if (ACTUAL_SCHEMA.equals(actual.schema())) {
                var compilerBinding = environmentCompilerBinding(env);
                for (AuxiliaryCommand command : actual.auxiliaryCommands())
                    require(command.outcome().binding().toolchain().equals(compilerBinding),
                            "Production BUILD changed its exact original ENV compiler/VCTIP/mspdb binding");
            }
            var model = NativeBridgeDefender.readGraph(request);
            if (expectedStage == Stage.BUILD) {
                require(model.graphRefs().equals(actual.graphRefs()), "Configured bridge graph differs");
                require(actual.outputRefs().equals(List.of(model.bridgeDll(), model.injector())), "Both real production bridge artifacts are required");
                require(!actual.dependencyRefs().isEmpty() && actual.dependencyRefs().equals(readDependencies(actual.commands().getLast().stdout(), request)), "Active compiler dependency closure differs");
            } else {
                Actual build = readAccepted(request.buildActual(), Stage.BUILD);
                if (ACTUAL_SCHEMA.equals(actual.schema())) require(ACTUAL_SCHEMA.equals(build.schema()),
                        "Production registration cannot upgrade a historical BUILD completion");
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
        require(ACTUAL_SCHEMA.equals(env.schema()) && ACTUAL_SCHEMA.equals(build.schema()) && ACTUAL_SCHEMA.equals(registration.schema()),
                "Current physical launch requires all three original MSVC-qualified native stages; older Actuals are historical read-only");
        Request request = readRequest(registration.requestRef());
        require(request.environmentActual().equals(environmentPin) && request.buildActual().equals(buildPin)
                && readRequest(build.requestRef()).environmentActual().equals(environmentPin), "Three actual stages do not form one causal bridge build");
        var graph = NativeBridgeDefender.readGraph(request); var refs = new ArrayList<ControlBuild.FileRef>();
        refs.addAll(List.of(environmentPin, buildPin, registrationPin));
        for (Actual actual : List.of(env, build, registration)) {
            refs.add(actual.requestRef()); refs.addAll(NativeBridgeRootGate.evidenceReferences(actual.grant()));
            refs.add(ControlBuild.FileRef.measure(readRequest(actual.requestRef()).stageRoot().resolve("INTENT.json")));
            refs.addAll(actual.runtimeRefs()); refs.addAll(actual.toolRefs());
            Request actualRequest = readRequest(actual.requestRef());
            var binding = actualRequest.compileSourceBindingRef() == null ? null : sourceBinding(actualRequest);
            refs.addAll(sourceReferences(actualRequest, binding, actual.sourceWitnesses().stream().map(witness -> Path.of(witness.source().path())).toList()));
            if (binding != null) {
                refs.add(actualRequest.compileSourceBindingRef()); refs.add(binding.retainedSourceActualRef());
                var sourceActual = CompileSourceBinding.sourceActual(binding);
                refs.add(sourceActual.requestRef()); refs.add(sourceActual.producerToolsBuildRef()); refs.add(sourceActual.capacityRef());
                refs.addAll(sourceActual.completeToolsRuntime()); refs.addAll(sourceActual.completePackageSources());
            }
            refs.addAll(actual.graphRefs()); refs.addAll(actual.dependencyRefs()); refs.addAll(actual.outputRefs());
            for (ControlBuild.FileRef optional : new ControlBuild.FileRef[]{actual.snapshotRef(), actual.manifestRef(), actual.helperReceiptRef()}) if (optional != null) refs.add(optional);
            for (Command command : actual.commands()) { refs.add(command.stdout()); refs.add(command.stderr()); }
            for (AuxiliaryCommand command : actual.auxiliaryCommands()) {
                var compiler = command.outcome().binding().toolchain();
                for (var image : List.of(compiler.vctip(), compiler.mspdbsrv()))
                    refs.add(new ControlBuild.FileRef(image.canonicalPath(), image.bytes(), image.sha256()));
            }
        }
        refs.add(request.qualifiedToolsBuild());
        var registrationBinding = request.compileSourceBindingRef() == null ? null : sourceBinding(request);
        refs.addAll(sourceReferences(request, registrationBinding, request.completeSources().stream().map(source -> Path.of(source.path())).toList()));
        refs.add(graph.bridgeDll()); refs.add(graph.injector());
        var tools = ControlBuild.verifiedCompletedReceipt(request.qualifiedToolsBuild());
        refs.addAll(tools.sourcePins()); refs.addAll(tools.compiledSourcePins()); refs.addAll(tools.producerRuntimePins());
        refs.addAll(tools.completeDeployment()); refs.add(tools.capacityReleaseRef()); refs.add(tools.javaExecutableRef());
        refs.add(tools.mavenToolchain().distributionLauncherRef());
        if (tools.mavenToolchain().explicitOverrideRef() != null) refs.add(tools.mavenToolchain().explicitOverrideRef());
        List<ControlBuild.FileRef> closure = merge(refs); verify(closure);
        return new Evidence(request, env, build, registration, graph.bridgeDll(), graph.injector(), closure);
    }

    public static List<String> configureCommand(Request request) {
        return configureCommand(request, true);
    }
    private static List<String> configureCommand(Request request, boolean resetProjectOptions) {
        var argv = new ArrayList<>(List.of(request.tools().cmake().path(), "-S", request.sourceRoot().toString(), "-B", request.buildRoot().toString(),
                "-G", "Ninja"));
        // Reused development cache must not retain project booleans omitted by this exact Request.
        // CMake then restores source defaults before the explicit Request definitions below.
        if (resetProjectOptions) argv.addAll(List.of("-U", "XAR_*"));
        argv.addAll(List.of("-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=OFF", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                "-DCMAKE_MAKE_PROGRAM=" + request.tools().ninja().path(), "-DCMAKE_CXX_COMPILER=" + request.tools().compiler().path(),
                "-DCMAKE_C_COMPILER=" + request.tools().compiler().path()));
        request.definitions().forEach(item -> argv.add("-D" + item.option() + "=" + item.value().name())); return List.copyOf(argv);
    }
    public static List<String> buildCommand(Request request) {
        return List.of(request.tools().cmake().path(), "--build", request.buildRoot().toString(), "--parallel", Integer.toString(request.parallelJobs()),
                "--target", TARGETS.get(0), TARGETS.get(1));
    }
    /** Sole compiler-help argv used by live execution and exact historical command validation. */
    static List<String> compilerHelpCommand(Request request) {
        return List.of(request.tools().compiler().path(), "/HELP");
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
                case COMPILER_HELP -> compilerHelpCommand(request);
                case CONFIGURE -> configureCommand(request, ACTUAL_SCHEMA.equals(actual.schema()));
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
        validateAuxiliaryCommands(request, actual);
    }
    private static boolean usesMsvc(CommandKind kind) {
        return kind == CommandKind.COMPILER_HELP || kind == CommandKind.CONFIGURE || kind == CommandKind.BRIDGE_BUILD;
    }
    static void validateAuxiliaryCommands(Request request, Actual actual) throws IOException {
        if (LEGACY_ACTUAL_SCHEMA.equals(actual.schema())) {
            require(actual.auxiliaryCommands().isEmpty(), "Historical native Actual cannot supply MSVC completion");
            return;
        }
        List<CommandKind> expected = actual.commands().stream().map(Command::kind).filter(NativeBridgeBuild::usesMsvc).toList();
        require(actual.auxiliaryCommands().stream().map(AuxiliaryCommand::kind).toList().equals(expected),
                "Every original MSVC command requires its own exact auxiliary completion");
        MsvcAuxiliaryPolicy.Binding sameCompiler = null;
        for (AuxiliaryCommand auxiliary : actual.auxiliaryCommands()) {
            var command = actual.commands().stream().filter(row -> row.kind() == auxiliary.kind()).findFirst().orElseThrow();
            var outcome = auxiliary.outcome();
            ControlBuild.FileRef root = auxiliary.kind() == CommandKind.COMPILER_HELP ? request.tools().compiler() : request.tools().cmake();
            outcome.binding().requireRequest(root, request.tools().references());
            outcome.binding().toolchain().requireCompiler(request.tools().compiler());
            require(outcome.completed() && outcome.originalRoot().identity().equals(command.owner())
                    && command.terminal() != null && command.terminal().passed(),
                    "Original command and its independently observed MSVC root/auxiliary/Job0 completion differ");
            if (sameCompiler == null) sameCompiler = outcome.binding().toolchain();
            else require(sameCompiler.equals(outcome.binding().toolchain()), "One stage cannot change its original three-image compiler binding");
        }
    }
    static MsvcAuxiliaryPolicy.Binding environmentCompilerBinding(Actual environment) throws IOException {
        require(ACTUAL_SCHEMA.equals(environment.schema()) && environment.stage() == Stage.ENV,
                "A new native BUILD requires actual MSVC-qualified ENV evidence");
        List<AuxiliaryCommand> original = environment.auxiliaryCommands();
        require(original.size() == 1 && original.getFirst().kind() == CommandKind.COMPILER_HELP
                && original.getFirst().outcome().completed(), "Original compiler-help completion binding is missing");
        return original.getFirst().outcome().binding().toolchain();
    }
    private static void verifyAuxiliaryImages(Actual actual) throws IOException {
        var images = new java.util.LinkedHashSet<MsvcAuxiliaryPolicy.Image>();
        for (AuxiliaryCommand command : actual.auxiliaryCommands()) {
            var binding = command.outcome().binding().toolchain();
            images.addAll(List.of(binding.compiler(), binding.vctip(), binding.mspdbsrv()));
        }
        for (var image : images) {
            var physical = SharedSourceFiles.observe(Path.of(image.canonicalPath()));
            require(physical.source().bytes() == image.bytes() && physical.source().sha256().equals(image.sha256())
                    && physical.nativeFile().volumeSerialDecimal().equals(image.volumeSerialDecimal())
                    && physical.nativeFile().fileIdDecimal().equals(image.fileIdDecimal()),
                    "Original native compiler/auxiliary path, volume, FileID or SHA differs from the held ENV image");
        }
    }
    static void prepareBuildRoot(Request request) throws IOException {
        Path root = request.buildRoot();
        if (Files.notExists(root, LinkOption.NOFOLLOW_LINKS)) { Files.createDirectory(root); return; }
        requireReusableCMakeCache(request.sourceRoot(), root, request.tools().compiler(), request.tools().ninja());
    }
    /** Live admission only: a case-insensitive Windows path match does not prevent CMake's compiler reset. */
    static void requireReusableCMakeCache(Path sourceRoot, Path buildRoot, ControlBuild.FileRef compiler,
            ControlBuild.FileRef ninja) throws IOException {
        plainDirectory(buildRoot);
        var pin = ControlBuild.FileRef.measure(buildRoot.resolve("CMakeCache.txt"));
        String cache = new String(read(pin, 2 << 20), StandardCharsets.UTF_8);
        require(Path.of(cacheValue(cache, "CMAKE_HOME_DIRECTORY")).normalize().equals(sourceRoot)
                && Path.of(cacheValue(cache, "CMAKE_CACHEFILE_DIR")).normalize().equals(buildRoot)
                && cacheValue(cache, "CMAKE_GENERATOR").equals("Ninja")
                && cacheValue(cache, "CMAKE_BUILD_TYPE").equals("Release"),
                "Only the same source/build Release Ninja cache can be reused");
        requireCachedNativeTool(cacheValue(cache, "CMAKE_CXX_COMPILER"), compiler, true);
        requireCachedNativeTool(cacheValue(cache, "CMAKE_C_COMPILER"), compiler, true);
        requireCachedNativeTool(cacheValue(cache, "CMAKE_MAKE_PROGRAM"), ninja, false);
        pin.verify();
    }
    private static void requireCachedNativeTool(String cachedLiteral, ControlBuild.FileRef approved,
            boolean compiler) throws IOException {
        Path cachedPath = Path.of(cachedLiteral);
        require(cachedPath.isAbsolute(), "Absolute cached native tool required");
        approved.verify();
        var expected = SharedSourceFiles.observe(Path.of(approved.path()));
        var cached = SharedSourceFiles.observe(cachedPath);
        require(expected.source().bytes() == approved.bytes() && expected.source().sha256().equals(approved.sha256())
                && cached.source().bytes() == approved.bytes() && cached.source().sha256().equals(approved.sha256())
                && cached.nativeFile().identityKey().equals(expected.nativeFile().identityKey()),
                "Cached native tool must be the exact qualified physical image and SHA");
        if (compiler) require(cachedLiteral.replace('\\', '/').equals(approved.path().replace('\\', '/')),
                "Cached compiler spelling would reset CMake; bind the request to the exact cached spelling");
        SharedSourceFiles.assertUnchanged(expected); SharedSourceFiles.assertUnchanged(cached); approved.verify();
    }
    private static String cacheValue(String cache, String key) throws IOException {
        List<String> values = cache.lines().filter(line -> line.startsWith(key + ":") && line.indexOf('=') >= 0)
                .map(line -> line.substring(line.indexOf('=') + 1)).toList();
        require(values.size() == 1 && !values.getFirst().isBlank(), "Unique existing CMake cache field required: " + key);
        return values.getFirst();
    }
    static void prepareQuery(Path query) throws IOException {
        SharedSourceFiles.plainAncestors(query);
        if (Files.notExists(query, LinkOption.NOFOLLOW_LINKS)) Files.write(query, new byte[0], StandardOpenOption.CREATE_NEW);
        else require(Files.isRegularFile(query, LinkOption.NOFOLLOW_LINKS) && Files.size(query) == 0,
                "Only the original empty CMake file-api query can be reused");
    }
    private static ControlBuild.BuildReceipt verifyRuntime(Request request) throws IOException {
        var tools = ControlBuild.verifiedCompletedReceipt(request.qualifiedToolsBuild());
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME && tools.machineId().equals(request.machineId())
                && tools.mavenToolchain().selection() == ControlBuild.MavenSelection.DEFAULT_COMMAND
                && tools.javaExecutableRef().equals(request.tools().java()) && tools.completeDeployment().equals(ControlBuild.producerClosure()), "Exact actually loaded qualified tools runtime required");
        for (Class<?> type : List.of(NativeBridgeBuild.class, NativeBridgeRootGate.class, NativeBridgeDefender.class, NativeBuildEnvironment.class, RootNativePlanJson.class, WindowsJobProcess.class, MsvcAuxiliaryPolicy.class)) {
            try { require(tools.completeDeployment().contains(ControlBuild.FileRef.measure(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()))), "Native producer class is outside qualified runtime"); }
            catch (java.net.URISyntaxException error) { throw new IOException(error); }
        }
        return tools;
    }
    static void validateSources(Request request) throws IOException {
        List<ControlBuild.FileRef> readableSources;
        if (BOUND_REQUEST_SCHEMA.equals(request.schema())) {
            var binding = sourceBinding(request); readableSources = CompileSourceBinding.retainedSources(binding);
        } else {
            require(request.completeSources().equals(inventory(request.sourceRoot())), "Complete frozen source tree differs; build outputs cannot be mixed into it");
            readableSources = request.completeSources();
        }
        require(readableSources.stream().anyMatch(file -> Path.of(file.path()).getFileName().toString().equals("CMakeLists.txt")), "Project CMake source missing");
        Set<String> options = new HashSet<>();
        var pattern = Pattern.compile("(?m)\\boption\\s*\\(\\s*(XAR_[A-Z0-9_]+)\\b");
        for (ControlBuild.FileRef file : readableSources) if (file.path().endsWith("CMakeLists.txt") || file.path().endsWith(".cmake")) {
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
    private static List<ControlBuild.FileRef> readDependencies(ControlBuild.FileRef raw, Request request) throws IOException {
        var binding = request.compileSourceBindingRef() == null ? null : sourceBinding(request);
        return readDependencies(raw, request, binding);
    }
    /** Invocation-local lookup only; the production entry validates the complete historical binding first. */
    static List<ControlBuild.FileRef> readDependencies(ControlBuild.FileRef raw, Request request,
                                                       CompileSourceBinding.Binding binding) throws IOException {
        var paths = new ArrayList<Path>();
        for (String line : new String(read(raw, 16 << 20), StandardCharsets.UTF_8).split("\\R")) if (line.startsWith("    ")) {
            String value = line.strip(); if (value.isEmpty()) continue; Path path = Path.of(value);
            if (!path.isAbsolute()) path = request.buildRoot().resolve(path).normalize();
            paths.add(path);
        }
        return merge(sourceReferences(request, binding, paths));
    }
    /** Shared bulk mapping for dependency, witness and configure closures; external files are never memoized. */
    static List<ControlBuild.FileRef> sourceReferences(Request request, CompileSourceBinding.Binding binding,
                                                      List<Path> originals) throws IOException {
        Map<Path, List<ControlBuild.FileRef>> compileIndex = new LinkedHashMap<>();
        Map<Path, ControlBuild.FileRef> retainedIndex = new LinkedHashMap<>();
        if (BOUND_REQUEST_SCHEMA.equals(request.schema()))
            for (ControlBuild.FileRef source : request.completeSources())
                compileIndex.computeIfAbsent(Path.of(source.path()), ignored -> new ArrayList<>()).add(source);
        var refs = new ArrayList<ControlBuild.FileRef>();
        for (Path path : originals) {
            if (BOUND_REQUEST_SCHEMA.equals(request.schema()) && path.startsWith(request.sourceRoot())) {
                absolute(path);
                require(binding != null && binding.compileSourceRoot().equals(request.sourceRoot()), "Validated compile binding required");
                List<ControlBuild.FileRef> matches = compileIndex.getOrDefault(path, List.of());
                require(matches.size() == 1, "Configured/dependency source is outside the exact compile inventory");
                ControlBuild.FileRef retained = retainedIndex.get(path);
                if (retained == null) {
                    retained = CompileSourceBinding.retainedFor(binding, matches.getFirst());
                    retainedIndex.put(path, retained);
                }
                refs.add(retained);
            } else {
                // External paths retain their original ancestor and content checks on every occurrence.
                refs.add(sourceReference(request, binding, path));
            }
        }
        return List.copyOf(refs);
    }
    /** A new stage cannot use a historical request to obtain a live reservation or create an INTENT. */
    static void requireCurrentRequest(Request request) throws IOException {
        Objects.requireNonNull(request);
        require(REQUEST_SCHEMA.equals(request.schema())||REGISTER_REQUEST_SCHEMA.equals(request.schema())||BOUND_REQUEST_SCHEMA.equals(request.schema()),
                "Legacy native request is historical read-only; version2 required for new stage execution");
        if(request.stage()==Stage.REGISTER)require((REGISTER_REQUEST_SCHEMA.equals(request.schema())||BOUND_REQUEST_SCHEMA.equals(request.schema()))
                &&request.defender() instanceof NativeBridgeDefender.ManifestRuntime,
                "New registration requires explicit version3 and complete runtime inventory; legacy registration is historical read-only");
        if(request.stage()==Stage.REGISTER)NativeBridgeDefender.requireDirectHelperRuntime(request.defender());
    }
    /** Shared plan identity; version2 registration authority belongs only to its REGISTER stage. */
    static boolean sameBuild(Request left, Request right) {
        boolean transition=(REGISTER_REQUEST_SCHEMA.equals(left.schema())&&left.stage()==Stage.REGISTER
                &&REQUEST_SCHEMA.equals(right.schema())&&right.stage()!=Stage.REGISTER)
                ||(REGISTER_REQUEST_SCHEMA.equals(right.schema())&&right.stage()==Stage.REGISTER
                &&REQUEST_SCHEMA.equals(left.schema())&&left.stage()!=Stage.REGISTER);
        boolean sameDefender = Objects.equals(left.defender(), right.defender());
        if(transition||((REQUEST_SCHEMA.equals(left.schema())||BOUND_REQUEST_SCHEMA.equals(left.schema()))&&left.schema().equals(right.schema())&&left.stage()!=right.stage()))sameDefender=true;
        return (left.schema().equals(right.schema())||transition) && left.machineId().equals(right.machineId()) && left.canonicalRepository().equals(right.canonicalRepository())
                && left.sourceRoot().equals(right.sourceRoot()) && left.completeSources().equals(right.completeSources())
                && left.buildRoot().equals(right.buildRoot()) && left.scratchRoot().equals(right.scratchRoot())
                && left.qualifiedToolsBuild().equals(right.qualifiedToolsBuild()) && left.tools().equals(right.tools())
                && left.definitions().equals(right.definitions()) && left.parallelJobs() == right.parallelJobs() && sameDefender
                && Objects.equals(left.compileSourceBindingRef(), right.compileSourceBindingRef());
    }
    static CompileSourceBinding.Binding sourceBinding(Request request) throws IOException {
        require(BOUND_REQUEST_SCHEMA.equals(request.schema()) && request.compileSourceBindingRef() != null, "Version4 source binding required");
        var binding = CompileSourceBinding.readHistorical(request.compileSourceBindingRef());
        require(binding.compileSourceRoot().equals(request.sourceRoot())
                && CompileSourceBinding.compileSources(binding).equals(request.completeSources()),
                "Request compile root/full inventory differs from the complete retained binding");
        require(binding.machineId().equals(request.machineId()) && binding.producerToolsBuildRef().equals(request.qualifiedToolsBuild()),
                "Retained source binding belongs to another machine or producer");
        return binding;
    }
    /** Configured paths stay original compile paths; persisted byte references use the immutable retained view. */
    static ControlBuild.FileRef sourceReference(Request request, Path original) throws IOException {
        return sourceReference(request, request.compileSourceBindingRef() == null ? null : sourceBinding(request), original);
    }
    static ControlBuild.FileRef sourceReference(Request request, CompileSourceBinding.Binding binding, Path original) throws IOException {
        absolute(original);
        if (BOUND_REQUEST_SCHEMA.equals(request.schema()) && original.startsWith(request.sourceRoot())) {
            require(binding != null && binding.compileSourceRoot().equals(request.sourceRoot()), "Validated compile binding required");
            var matches = request.completeSources().stream().filter(file -> Path.of(file.path()).equals(original)).toList();
            require(matches.size() == 1, "Configured/dependency source is outside the exact compile inventory");
            return CompileSourceBinding.retainedFor(binding, matches.getFirst());
        }
        SharedSourceFiles.plainAncestors(original); return ControlBuild.FileRef.measure(original);
    }
    static List<SharedSourceFiles.Witness> observeRequestSources(Request request) throws IOException {
        if (!BOUND_REQUEST_SCHEMA.equals(request.schema())) return observe(request.completeSources());
        var binding = sourceBinding(request);
        var before = new ArrayList<>(CompileSourceBinding.observeLive(binding));
        var bindingWitness = SharedSourceFiles.observe(Path.of(request.compileSourceBindingRef().path()));
        require(bindingWitness.source().equals(request.compileSourceBindingRef()), "Original binding metadata changed");
        before.add(bindingWitness); before.add(binding.retainedSourceActualWitness());
        return List.copyOf(before);
    }
    static void assertLiveSourceBinding(Request request, List<SharedSourceFiles.Witness> witnesses) throws IOException {
        assertSources(witnesses);
        if (BOUND_REQUEST_SCHEMA.equals(request.schema())) {
            var nativeWitnesses = nativeWitnesses(request, witnesses);
            CompileSourceBinding.assertLiveUnchanged(sourceBinding(request), nativeWitnesses);
        }
    }
    private static List<SharedSourceFiles.Witness> nativeWitnesses(Request request, List<SharedSourceFiles.Witness> witnesses) throws IOException {
        Set<String> paths = request.completeSources().stream().map(ControlBuild.FileRef::path).collect(java.util.stream.Collectors.toSet());
        var nativeWitnesses = witnesses.stream().filter(row -> paths.contains(row.source().path())).toList();
        require(nativeWitnesses.stream().map(SharedSourceFiles.Witness::source).toList().equals(request.completeSources()),
                "Actual must retain each original compile witness exactly once and in complete inventory order");
        return nativeWitnesses;
    }
    /** A historical receipt retains original identities while mutable compile files may advance after the stage. */
    static void assertHistoricalSourceWitnesses(Request request, List<SharedSourceFiles.Witness> witnesses) throws IOException {
        if (!BOUND_REQUEST_SCHEMA.equals(request.schema())) { assertSources(witnesses); return; }
        var binding = sourceBinding(request);
        var nativeRows = nativeWitnesses(request, witnesses);
        var retainedIdentities = binding.rows().stream().map(row -> row.retainedWitness().nativeFile().identityKey()).collect(java.util.stream.Collectors.toSet());
        for (var witness : nativeRows) {
            CompileSourceBinding.retainedFor(binding, witness.source()).verify();
            require(!retainedIdentities.contains(witness.nativeFile().identityKey()), "Historical compile witness aliases immutable retained input");
        }
        Set<String> nativePaths = request.completeSources().stream().map(ControlBuild.FileRef::path).collect(java.util.stream.Collectors.toSet());
        for (var witness : witnesses) if (!nativePaths.contains(witness.source().path())) SharedSourceFiles.assertUnchanged(witness);
    }

    public record CausalInput(String schema, String machineId, Stage stage, ControlBuild.FileRef retainedSourceActualRef,
            ControlBuild.FileRef environmentActualRef, ControlBuild.FileRef buildActualRef,
            ControlBuild.FileRef runtimeInventoryRef, Path ownedRoot, Path requestOutput) {
        public CausalInput {
            if (!"xar.native-bridge-causal-request-input/v2".equals(schema) || stage == null || stage == Stage.ENV)
                throw new IllegalArgumentException("Explicit bound BUILD/REGISTER causal input version2 required");
            Objects.requireNonNull(machineId); Objects.requireNonNull(retainedSourceActualRef); Objects.requireNonNull(environmentActualRef);
            ownedRoot = absolute(ownedRoot); requestOutput = absolute(requestOutput);
            if ((stage == Stage.REGISTER) != (buildActualRef != null) || (stage == Stage.REGISTER) != (runtimeInventoryRef != null))
                throw new IllegalArgumentException("REGISTER requires actual BUILD and complete runtime inventory; BUILD retains explicit nulls");
        }
    }
    static NativeCombinedSourceCut.Actual stageSource(ControlBuild.FileRef sourceRef, Request request) throws IOException {
        var source = NativeCombinedSourceCut.readAcceptedSource(sourceRef);
        if (BOUND_REQUEST_SCHEMA.equals(request.schema())) {
            var binding = sourceBinding(request);
            require(binding.retainedSourceActualRef().equals(sourceRef), "Stage selected another retained source Actual");
        } else require(Path.of(source.nativeSourceRoot()).equals(request.sourceRoot())
                && source.completeNativeSources().equals(request.completeSources()), "Stage does not bind this complete accepted frozen source");
        return source;
    }
    /** The original causal adapter now uses the one qualified producer and explicit retained/compile contract. */
    public static ControlBuild.FileRef writeCausalRequest(CausalInput input) throws IOException {
        require(input.machineId().equals(WindowsJobProcess.currentMachineId()), "Causal input belongs to another machine");
        var environment = readAccepted(input.environmentActualRef(), Stage.ENV);
        var original = readRequest(environment.requestRef());
        require(BOUND_REQUEST_SCHEMA.equals(original.schema()) && input.machineId().equals(original.machineId()),
                "Current causal writer requires the actual bound ENV request");
        stageSource(input.retainedSourceActualRef(), original);
        NativeBridgeDefender.Runtime defender = null;
        if (input.stage() == Stage.REGISTER) {
            var build = readAccepted(input.buildActualRef(), Stage.BUILD);
            var buildRequest = readRequest(build.requestRef());
            require(sameBuild(original, buildRequest) && input.environmentActualRef().equals(buildRequest.environmentActual()),
                    "REGISTER cannot acquire an unrelated actual BUILD");
            var inventory = JSON.readValue(read(input.runtimeInventoryRef(), MAX_JSON), NativeRegistrationRuntimeInventory.Manifest.class);
            require(inventory.qualifiedToolsBuild().equals(original.qualifiedToolsBuild()), "Runtime inventory producer differs from this actual tools cut");
            defender = NativeBridgeDefender.directBaseRuntime(original.canonicalRepository(), input.runtimeInventoryRef());
        }
        var request = new Request(BOUND_REQUEST_SCHEMA, original.machineId(), input.stage(), original.canonicalRepository(),
                original.sourceRoot(), original.completeSources(), original.buildRoot(), original.scratchRoot(), original.qualifiedToolsBuild(),
                original.tools(), original.definitions(), original.parallelJobs(), input.environmentActualRef(), input.buildActualRef(),
                defender, original.compileSourceBindingRef());
        var result = writeRequest(request, input.ownedRoot(), input.requestOutput());
        stageSource(input.retainedSourceActualRef(), original); return result;
    }
    /** Mechanical CLI adapter of the existing Root producer; it issues no capacity or stage qualification. */
    public static ControlBuild.FileRef executeStage(NativeProjectExeUac.CurrentNativeStageSpec spec) throws IOException, InterruptedException {
        require(spec != null && "xar.native-bridge-stage-command/v1".equals(spec.schema()) && spec.expectedStage() != null
                && spec.requestRef() != null && spec.frozenSourceActualRef() != null && spec.limits() != null
                && Objects.equals(spec.machineId(), WindowsJobProcess.currentMachineId()), "Exact current-machine stage spec required");
        var request = readRequest(spec.requestRef()); requireCurrentRequest(request);
        require(request.stage() == spec.expectedStage() && request.machineId().equals(spec.machineId()), "Expected stage/machine differs");
        var source = stageSource(spec.frozenSourceActualRef(), request);
        var nativeFiles = Set.copyOf(source.completeNativeSources()); var siblings = new ArrayList<SharedSourceFiles.Witness>();
        for (var pin : source.completePackageSources()) if (!nativeFiles.contains(pin)) {
            var witness = SharedSourceFiles.observe(Path.of(pin.path()));
            require(witness.source().equals(pin), "Retained sibling differs before stage"); siblings.add(witness);
        }
        require(siblings.size() == 10, "Exact ten-sibling source closure required");
        Actual actual; ControlBuild.FileRef result;
        try {
            actual = executeRoot(spec.requestRef(), spec.limits());
            result = ControlBuild.FileRef.measure(request.stageRoot().resolve("ACTUAL.json"));
            if (actual.status() == Status.PASS) readAccepted(result, spec.expectedStage());
        } finally {
            stageSource(spec.frozenSourceActualRef(), request);
            for (var sibling : siblings) SharedSourceFiles.assertUnchanged(sibling);
        }
        require(actual.status() == Status.PASS, "Original stage retained non-PASS Actual; dependent stages are prohibited"); return result;
    }
    public static void main(String[] args) throws IOException, InterruptedException {
        require(args.length == 4 && (args[0].equals("execute") || args[0].equals("write-request")),
                "execute|write-request INPUT_PATH EXACT_BYTES SHA256 required");
        var pin = SharedOwnedCommand.cliRef(args[1], args[2], args[3]);
        require(pin.bytes() > 0 && pin.bytes() <= 131072, "Finite exact stage metadata required");
        var witness = SharedSourceFiles.observe(Path.of(pin.path())); require(witness.source().equals(pin), "Pinned stage metadata differs");
        byte[] raw = read(pin, 131072); SharedSourceFiles.assertUnchanged(witness);
        var result = args[0].equals("execute") ? executeStage(JSON.readValue(raw, NativeProjectExeUac.CurrentNativeStageSpec.class))
                : writeCausalRequest(JSON.readValue(raw, CausalInput.class));
        SharedSourceFiles.assertUnchanged(witness); System.out.println(JSON.writeValueAsString(result));
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
