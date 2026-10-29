package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;

/** Runs existing actual-.4 C++ software fixtures. This produces no live-Game qualification. */
public final class Person10NativeCorpusBuild {
    public static final String REQUEST_SCHEMA = "xar.person10-native-fixture-build-request/v1";
    public static final String ACTUAL_SCHEMA = "xar.person10-native-fixture-build-actual/v1";
    public static final String MANIFEST_NAME = "PERSON10-NATIVE-MANIFEST.json";
    public static final String ACTUAL_NAME = "PERSON10-NATIVE-ACTUAL.json";
    public static final String SCOPE = "ACTUAL_CPP_SOFTWARE_FIXTURE_NOT_LIVE_GAME";
    private static final String EXE_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final int MAX_JSON = 16 << 20;
    private Person10NativeCorpusBuild() { }

    public record Producer(String target, String fixtureSource, String field, int packetCount) {
        public Producer {
            if (target == null || !target.matches("xar_ck3_12004_person_[a-z0-9_]+_mcp_test")
                    || fixtureSource == null || !fixtureSource.startsWith("tests/") || !fixtureSource.endsWith(".cpp")
                    || field == null || field.isBlank() || packetCount < 1 || packetCount > 32)
                throw new IllegalArgumentException("Exact current-.4 original producer required");
        }
    }
    public static final List<Producer> PRODUCERS = List.of(
        producer("carrier_direct", "person_carrier_direct12004_mcp_fixture.cpp", "carrier_1c8_b70_direct", 8),
        producer("following_2921a90", "person_following_2921a90_12004_mcp_fixture.cpp", "following_2921a90", 10),
        producer("conditional_2921a90", "person_conditional_2921a90_12004_mcp_fixture.cpp", "following_2921a90_conditional", 12),
        producer("conditional_opinion", "person_conditional_opinion_12004_mcp_fixture.cpp", "following_2921a90_opinion", 5),
        producer("conditional_scope_weights", "person_conditional_scope_weights_12004_mcp_fixture.cpp", "following_2921a90_scope_weights", 5),
        producer("following_2922680", "person_following_2922680_12004_mcp_fixture.cpp", "following_2922680", 14),
        producer("following_291ce01_government_gate", "person_following_291ce01_government_gate_12004_mcp_fixture.cpp", "following_291ce01_government_gate", 7),
        producer("following_291e3a0_local_titles", "person_following_291e3a0_local_titles_12004_mcp_fixture.cpp", "following_291e3a0_local_titles", 10),
        producer("first_title_vector", "person_first_title_vector_12004_mcp_fixture.cpp", "following_291e3a0_first_title_vector", 6),
        producer("native_title_tail_capture", "person_native_title_tail_capture_12004_mcp_fixture.cpp", "following_291e3a0_captured_tail", 6));
    private static Producer producer(String target, String source, String field, int count) {
        return new Producer("xar_ck3_12004_person_" + target + "_mcp_test", "tests/" + source, field, count);
    }

    /** Existing cache reuse is permitted only for an independently admitted research tree, never the production Bridge tree. */
    public record Request(String schema, String machineId, ControlBuild.FileRef environmentActual,
            ControlBuild.FileRef producerRuntimeBuild, @com.fasterxml.jackson.databind.annotation.JsonSerialize(using = CompiledAddonOptionalSerializer.class)
            @com.fasterxml.jackson.databind.annotation.JsonDeserialize(using = CompiledAddonOptionalDeserializer.class)
            Optional<CompiledAddon> compiledAddon, Path buildRoot, Path outputRoot, Path temporaryRoot, int parallelJobs,
            List<ControlBuild.FileRef> existingResearchCache, NativeBridgeRootGate.Limits limits) {
        public Request {
            if (!REQUEST_SCHEMA.equals(schema) || machineId == null || machineId.equals("unknown")
                    || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}") || parallelJobs < 1 || parallelJobs > 64)
                throw new IllegalArgumentException("Exact finite fixture request required");
            Objects.requireNonNull(environmentActual); Objects.requireNonNull(producerRuntimeBuild); Objects.requireNonNull(compiledAddon); Objects.requireNonNull(limits);
            buildRoot = absolute(buildRoot); outputRoot = absolute(outputRoot); temporaryRoot = absolute(temporaryRoot); existingResearchCache = List.copyOf(existingResearchCache);
            if (overlap(buildRoot, outputRoot) || overlap(buildRoot, temporaryRoot) || overlap(outputRoot, temporaryRoot)
                    || (!existingResearchCache.isEmpty() && existingResearchCache.size() != 3))
                throw new IllegalArgumentException("Disjoint corpus/build roots and three exact cache inputs required");
        }
        public Path corpusRoot() { return outputRoot.resolve("corpus"); }
    }
    /** Root may compile just these two producers with the already qualified C16 mechanical javac caller. */
    public record CompiledAddon(Path classesRoot, List<ControlBuild.FileRef> sources,
            List<ControlBuild.FileRef> classes, ControlBuild.FileRef compilationTerminal) {
        public CompiledAddon {
            classesRoot = absolute(classesRoot); sources = List.copyOf(sources); classes = List.copyOf(classes);
            Objects.requireNonNull(compilationTerminal);
            if (sources.size() != 2 || classes.isEmpty() || classes.size() > 64)
                throw new IllegalArgumentException("Exact two-source bounded javac addon required");
        }
    }

    /** Explicit wire: null means no compiled addon; an object must satisfy the sole typed addon contract. */
    public static final class CompiledAddonOptionalSerializer
            extends com.fasterxml.jackson.databind.JsonSerializer<Optional<CompiledAddon>> {
        @Override public void serialize(Optional<CompiledAddon> value,
                com.fasterxml.jackson.core.JsonGenerator output,
                com.fasterxml.jackson.databind.SerializerProvider provider) throws IOException {
            if (value.isEmpty()) output.writeNull();
            else provider.defaultSerializeValue(value.orElseThrow(), output);
        }
    }
    public static final class CompiledAddonOptionalDeserializer
            extends com.fasterxml.jackson.databind.JsonDeserializer<Optional<CompiledAddon>> {
        @Override public Optional<CompiledAddon> deserialize(com.fasterxml.jackson.core.JsonParser input,
                com.fasterxml.jackson.databind.DeserializationContext context) throws IOException {
            if (input.currentToken() != com.fasterxml.jackson.core.JsonToken.START_OBJECT)
                throw context.wrongTokenException(input, CompiledAddon.class,
                        com.fasterxml.jackson.core.JsonToken.START_OBJECT,
                        "Explicit null or one complete compiled addon object required");
            return Optional.of(context.readValue(input, CompiledAddon.class));
        }
        @Override public Optional<CompiledAddon> getNullValue(
                com.fasterxml.jackson.databind.DeserializationContext context) {
            return Optional.empty();
        }
    }

    public enum Status { PASS, RED, UNKNOWN }
    public record Command(String role, List<String> argv, String cwd, WindowsJobProcess.ProcessIdentity identity,
            WindowsJobProcess.CommandResult terminal, ControlBuild.FileRef stdout, ControlBuild.FileRef stderr) {
        public Command { Objects.requireNonNull(role); argv = List.copyOf(argv); Objects.requireNonNull(cwd); }
    }
    public record Produced(Producer producer, ControlBuild.FileRef executable, List<ControlBuild.FileRef> packets) {
        public Produced { Objects.requireNonNull(producer); Objects.requireNonNull(executable); packets = List.copyOf(packets); }
    }
    public record Actual(String schema, String scope, String machineId, String startedAtUtc, String observedAtUtc,
            Status status, ControlBuild.FileRef requestRef, List<ControlBuild.FileRef> sourceRefs,
            List<ControlBuild.FileRef> toolsAndRuntime, List<ControlBuild.FileRef> configuredGraph,
            List<Command> commands, List<Produced> produced, ControlBuild.FileRef corpusManifest,
            boolean sourcesUnchanged, String error) {
        public Actual {
            if (!ACTUAL_SCHEMA.equals(schema) || !SCOPE.equals(scope)) throw new IllegalArgumentException("Exact software fixture scope required");
            Instant.parse(startedAtUtc); Instant.parse(observedAtUtc); Objects.requireNonNull(status); Objects.requireNonNull(requestRef);
            sourceRefs = List.copyOf(sourceRefs); toolsAndRuntime = List.copyOf(toolsAndRuntime); configuredGraph = List.copyOf(configuredGraph);
            commands = List.copyOf(commands); produced = List.copyOf(produced);
            if (status == Status.PASS && (error != null || !sourcesUnchanged || corpusManifest == null || produced.size() != 10
                    || commands.size() != 12 || commands.stream().anyMatch(c -> c.terminal() == null || !c.terminal().passed())))
                throw new IllegalArgumentException("PASS requires actual completed ten producers and source-bound corpus");
            if (status != Status.PASS && (error == null || error.isBlank())) throw new IllegalArgumentException("Explicit failure required");
        }
    }

    public static Request readRequest(ControlBuild.FileRef source) throws IOException {
        source.verify(); require(source.bytes() > 0 && source.bytes() <= MAX_JSON, "Bounded exact native request required");
        Request request = RootNativePlanJson.mapper().readValue(Files.readAllBytes(Path.of(source.path())), Request.class);
        source.verify(); return request;
    }
    /** Verifies the actual producer chain without renewing authority or executing a native child. */
    public static Actual readProduced(ControlBuild.FileRef pin) throws IOException {
        pin.verify(); require(pin.bytes() > 0 && pin.bytes() <= MAX_JSON, "Bounded actual producer receipt required");
        Actual actual = RootNativePlanJson.mapper().readValue(Files.readAllBytes(Path.of(pin.path())), Actual.class);
        Request request = readRequest(actual.requestRef());
        require(actual.status() == Status.PASS && request.machineId().equals(actual.machineId())
                && actual.machineId().equals(WindowsJobProcess.currentMachineId())
                && Path.of(pin.path()).equals(request.outputRoot().resolve(ACTUAL_NAME)), "Actual current-machine software fixture receipt required");
        Instant started = Instant.parse(actual.startedAtUtc()), completed = Instant.parse(actual.observedAtUtc());
        require(!completed.isBefore(started) && completed.isBefore(request.limits().deadline()), "Producer exceeded its original admitted window");
        var env = NativeBridgeBuild.readAccepted(request.environmentActual(), NativeBridgeBuild.Stage.ENV);
        var source = NativeBridgeBuild.readRequest(env.requestRef());
        var release = ControlBuild.strictMapper().readValue(NativeBridgeBuild.read(request.limits().capacityEvidence(), 131072), ControlBuild.CapacityRelease.class);
        Person10CorpusBuildGate.validate(request, actual.requestRef(), release, source.sourceRoot(), started);
        require(actual.sourceRefs().equals(source.completeSources()) && actual.sourceRefs().equals(NativeBridgeBuild.inventory(source.sourceRoot())), "Complete original source lineage differs");
        for (var file : actual.toolsAndRuntime()) file.verify();
        var runtime = ControlBuild.verifiedCompletedReceipt(request.producerRuntimeBuild());
        if (request.compiledAddon().isPresent()) require(actual.toolsAndRuntime().containsAll(verifyAddon(request, runtime)), "Original javac addon lineage missing");
        require(actual.toolsAndRuntime().containsAll(source.tools().references()) && actual.toolsAndRuntime().containsAll(runtime.completeDeployment()), "Original complete tool/runtime closure missing");
        require(actual.configuredGraph().equals(cachePins(request.buildRoot())), "Configured research graph drifted");
        require(actual.produced().stream().map(Produced::producer).toList().equals(PRODUCERS), "All ten actual original producers required in order");
        for (int i = 0; i < actual.commands().size(); i++) {
            Command command = actual.commands().get(i);
            List<String> expected = i == 0 ? configureArguments(request, source) : i == 1 ? buildArguments(request, source.tools().cmake().path())
                    : List.of(actual.produced().get(i - 2).executable().path(), request.corpusRoot().resolve(PRODUCERS.get(i - 2).field()).toString());
            String role = i == 0 ? "configure" : i == 1 ? "build" : PRODUCERS.get(i - 2).field();
            require(command.role().equals(role) && command.argv().equals(expected) && command.cwd().equals(request.outputRoot().toString())
                    && command.identity() != null && command.terminal() != null && command.identity().equals(command.terminal().identity())
                    && command.terminal().passed() && Path.of(command.identity().executable()).equals(Path.of(expected.getFirst()))
                    && command.terminal().accounting().memoryLimitBytes() == request.limits().memoryLimitBytes(), "Actual original command/exit/Job binding differs");
            require(command.stdout() != null && command.stderr() != null
                    && Path.of(command.stdout().path()).equals(request.outputRoot().resolve(role + ".stdout.log"))
                    && Path.of(command.stderr().path()).equals(request.outputRoot().resolve(role + ".stderr.log")), "Original command log binding differs");
            command.stdout().verify(); command.stderr().verify();
        }
        List<ControlBuild.FileRef> all = new ArrayList<>();
        for (Produced produced : actual.produced()) {
            produced.executable().verify();
            require(Path.of(produced.executable().path()).equals(request.buildRoot().resolve(produced.producer().target() + ".exe")), "Original built executable role differs");
            require(produced.packets().equals(inspectProducer(produced.producer(), request.corpusRoot().resolve(produced.producer().field()))), "Actual producer original packets drifted");
            all.addAll(produced.packets());
        }
        var manifest = Person10NativeCorpus.require(actual.corpusManifest(), request.corpusRoot().toString());
        require(Path.of(actual.corpusManifest().path()).equals(request.outputRoot().resolve(MANIFEST_NAME))
                && all.stream().sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList().equals(manifest.files()), "Actual original complete manifest differs");
        actual.requestRef().verify(); pin.verify(); return actual;
    }
    public static ControlBuild.FileRef writeRequest(Request request, Path target) throws IOException {
        validateInputs(request); return writeNew(absolute(target), request);
    }

    /** Root starts this separate admitted fixture process before Full35. No JUnit/corpus bootstrap cycle. */
    public static Actual execute(ControlBuild.FileRef requestPin) throws IOException, InterruptedException {
        Request request = readRequest(requestPin); Inputs inputs = validateInputs(request);
        try (Person10CorpusBuildGate gate = Person10CorpusBuildGate.open(request, requestPin, inputs.source().sourceRoot())) {
            gate.check(); require(Files.notExists(request.outputRoot(), LinkOption.NOFOLLOW_LINKS), "Existing intent/output is never replayed");
            Files.createDirectory(request.outputRoot()); writeNew(request.outputRoot().resolve("INTENT.json"), request);
            Files.createDirectory(request.temporaryRoot()); Files.createDirectory(request.corpusRoot());
            List<Command> commands = new ArrayList<>(); List<Produced> produced = new ArrayList<>();
            List<ControlBuild.FileRef> graph = List.of(); ControlBuild.FileRef manifest = null;
            String started = Instant.now().toString(), error = null; boolean unchanged = false, interrupted = false;
            try {
                if (request.existingResearchCache().isEmpty()) { gate.check(); Files.createDirectory(request.buildRoot()); }
                Map<String,String> environment = new TreeMap<>(inputs.environment().values());
                for (String key : List.of("TEMP", "TMP", "TMPDIR")) environment.put(key, request.temporaryRoot().toString());
                run(request, gate, commands, "configure", configureArguments(request, inputs.source()), environment);
                run(request, gate, commands, "build", buildArguments(request, inputs.source().tools().cmake().path()), environment);
                graph = cachePins(request.buildRoot());
                for (Producer producer : PRODUCERS) {
                    gate.check(); Path directory = request.corpusRoot().resolve(producer.field());
                    require(Files.notExists(directory, LinkOption.NOFOLLOW_LINKS), "Producer output must be absent");
                    Path executable = request.buildRoot().resolve(producer.target() + ".exe");
                    ControlBuild.FileRef binary = ControlBuild.FileRef.measure(executable); binary.verify();
                    run(request, gate, commands, producer.field(), List.of(binary.path(), directory.toString()), environment);
                    binary.verify(); List<ControlBuild.FileRef> packets = inspectProducer(producer, directory);
                    produced.add(new Produced(producer, binary, packets));
                }
                verifyInputs(request, inputs); gate.check();
                manifest = Person10NativeCorpus.produce(request.corpusRoot(), request.outputRoot().resolve(MANIFEST_NAME));
                var measured = Person10NativeCorpus.require(manifest, request.corpusRoot().toString());
                List<ControlBuild.FileRef> all = produced.stream().flatMap(p -> p.packets().stream())
                        .sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList();
                require(all.equals(measured.files()), "Manifest must enumerate exactly all original producer bytes");
                verifyInputs(request, inputs); gate.check(); unchanged = true;
            } catch (InterruptedException failure) { error = failure.toString(); interrupted = true; }
            catch (IOException | RuntimeException failure) { error = failure.toString(); }
            finally {
                try { verifyInputs(request, inputs); requestPin.verify(); }
                catch (IOException | RuntimeException failure) { unchanged = false; error = (error == null ? "" : error + "; ") + "postcheck: " + failure; }
            }
            boolean unknown = commands.stream().anyMatch(c -> c.terminal() == null);
            Actual actual = new Actual(ACTUAL_SCHEMA, SCOPE, request.machineId(), started, Instant.now().toString(),
                    error == null ? Status.PASS : unknown ? Status.UNKNOWN : Status.RED, requestPin, inputs.source().completeSources(),
                    inputs.toolsAndRuntime(), graph, commands, produced, manifest, unchanged, error);
            writeNew(request.outputRoot().resolve(ACTUAL_NAME), actual);
            if (interrupted) Thread.currentThread().interrupt();
            return actual;
        }
    }

    private record Inputs(NativeBridgeBuild.Request source, NativeBuildEnvironment.Snapshot environment,
            List<ControlBuild.FileRef> toolsAndRuntime) { }
    private static Inputs validateInputs(Request request) throws IOException {
        require(request.machineId().equals(WindowsJobProcess.currentMachineId()), "Native fixture request belongs to another machine");
        var env = NativeBridgeBuild.readAccepted(request.environmentActual(), NativeBridgeBuild.Stage.ENV);
        var source = NativeBridgeBuild.readRequest(env.requestRef());
        require(source.machineId().equals(request.machineId()), "ENV machine differs");
        require(!overlap(request.buildRoot(), source.buildRoot()) && !overlap(request.outputRoot(), source.scratchRoot())
                && !overlap(request.buildRoot(), source.sourceRoot()) && !overlap(request.outputRoot(), source.sourceRoot())
                && !overlap(request.temporaryRoot(), source.sourceRoot()),
                "Fixture outputs cannot mutate the production Bridge tree or frozen sources");
        require(NativeBridgeBuild.inventory(source.sourceRoot()).equals(source.completeSources()), "Complete current frozen source tree differs");
        for (Producer producer : PRODUCERS)
            require(source.completeSources().stream().anyMatch(p -> Path.of(p.path()).equals(source.sourceRoot().resolve(producer.fixtureSource()))),
                    "Original current-.4 fixture is absent: " + producer.fixtureSource());
        var runtime = ControlBuild.verifiedCompletedReceipt(request.producerRuntimeBuild());
        require(runtime.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME && runtime.machineId().equals(request.machineId())
                && runtime.mavenToolchain().selection() == ControlBuild.MavenSelection.DEFAULT_COMMAND, "Separate actual addon build-tools runtime required");
        List<ControlBuild.FileRef> pins = new ArrayList<>(source.tools().references()); pins.addAll(runtime.completeDeployment());
        pins.add(request.environmentActual()); pins.add(env.requestRef()); pins.add(env.snapshotRef()); pins.add(request.producerRuntimeBuild());
        if (request.compiledAddon().isPresent()) pins.addAll(verifyAddon(request, runtime));
        for (Class<?> type : List.of(Person10NativeCorpusBuild.class, Person10CorpusBuildGate.class, Person10NativeCorpus.class, WindowsJobProcess.class)) {
            try { require(runtime.completeDeployment().contains(ControlBuild.FileRef.measure(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()))),
                    "Native producer class is outside its independent qualified addon runtime"); }
            catch (java.net.URISyntaxException failure) { throw new IOException(failure); }
            catch (IOException failure) {
                if (request.compiledAddon().isEmpty() || (type != Person10NativeCorpusBuild.class && type != Person10CorpusBuildGate.class)) throw failure;
                try { require(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).equals(request.compiledAddon().orElseThrow().classesRoot()),
                        "Addon class escaped its actual javac output directory"); }
                catch (java.net.URISyntaxException invalid) { throw new IOException(invalid); }
            }
        }
        for (ControlBuild.FileRef pin : pins) pin.verify();
        var snapshot = NativeBuildEnvironment.read(source.stageRoot(), request.machineId(), Files.readAllBytes(Path.of(env.snapshotRef().path())));
        if (request.existingResearchCache().isEmpty()) require(Files.notExists(request.buildRoot(), LinkOption.NOFOLLOW_LINKS), "Fresh build root required");
        else {
            require(request.existingResearchCache().equals(cachePins(request.buildRoot())), "Exact previously admitted research cache differs");
            String cache = Files.readString(request.buildRoot().resolve("CMakeCache.txt"));
            require(cache.contains("BUILD_TESTING:BOOL=ON") && cache.contains("CMAKE_GENERATOR:INTERNAL=Ninja")
                    && cache.lines().anyMatch(l -> l.startsWith("CMAKE_HOME_DIRECTORY:INTERNAL=")
                        && Path.of(l.substring(l.indexOf('=') + 1)).equals(source.sourceRoot())), "Only same-source testing-ON Ninja research cache can be reused");
        }
        return new Inputs(source, snapshot, List.copyOf(pins));
    }
    private static List<ControlBuild.FileRef> verifyAddon(Request request, ControlBuild.BuildReceipt runtime) throws IOException {
        CompiledAddon addon = request.compiledAddon().orElseThrow(); addon.compilationTerminal().verify();
        require(addon.compilationTerminal().bytes() > 0 && addon.compilationTerminal().bytes() <= (1 << 20), "Bounded actual javac terminal required");
        var owned = SharedOwnedCommand.readNativeTerminal(addon.compilationTerminal());
        var terminal = owned.terminal();
        require(terminal.schema().equals("xar.shared-owned-command-terminal/v2") && terminal.machineId().equals(request.machineId())
                && terminal.status() == SharedOwnedCommand.Status.PASS && terminal.childStarted() && terminal.child() != null && terminal.child().passed()
                && terminal.inputPrecheck() == SharedOwnedCommand.Check.MATCH && terminal.inputPostcheck() == SharedOwnedCommand.Check.MATCH
                && terminal.runtimePostcheck() == SharedOwnedCommand.Check.MATCH && terminal.failure() == null
                && terminal.completeRuntime().equals(runtime.completeDeployment()), "Actual accepted C16 javac caller completion required");
        terminal.requestRef().verify();
        var spec = owned.request();
        require(Path.of(spec.executable().path()).getFileName().toString().equalsIgnoreCase("javac.exe")
                && spec.executable().path().equals(terminal.child().identity().executable()) && spec.inputs().containsAll(addon.sources())
                && spec.inputs().containsAll(runtime.completeDeployment()), "Actual javac/tool/source inputs required");
        List<String> expected = new ArrayList<>(List.of("-J-Xms32m", "-J-Xmx512m", "--release", "21", "-encoding", "UTF-8",
                "-proc:none", "-Xlint:all", "-Werror", "-implicit:none", "-sourcepath", "",
                "-classpath", String.join(java.io.File.pathSeparator, runtime.completeDeployment().stream().map(ControlBuild.FileRef::path).toList()),
                "-d", addon.classesRoot().toString()));
        addon.sources().forEach(source -> expected.add(source.path()));
        spec.standingRef().verify();
        JsonNode standing = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(spec.standingRef().path())));
        require(standing.path("private_temporary_aggregate_root").isTextual() && standing.path("native_tmp_root").isTextual(), "Actual C16 compiler temporary roots missing");
        Path temporary = Path.of(standing.path("private_temporary_aggregate_root").textValue()).resolve(spec.slotId().replace('/', '_'))
                .resolve(spec.owner().substring(6).replace('/', '_')).resolve(spec.runId());
        List<String> effective = new ArrayList<>(List.of("-J-Djava.io.tmpdir=" + temporary,
                "-J-Djna.tmpdir=" + Path.of(standing.path("native_tmp_root").textValue()).toAbsolutePath().normalize(),
                "-J-XX:ErrorFile=" + spec.outputRoot().resolve("hs_err_pid%p.log"),
                "-J-XX:ReplayDataFile=" + spec.outputRoot().resolve("replay_pid%p.log"), "-J-XX:HeapDumpPath=" + spec.outputRoot()));
        effective.addAll(expected);
        require(spec.arguments().equals(expected) && terminal.effectiveArguments().equals(effective), "Actual narrow javac argv differs");
        require(addon.sources().stream().map(p -> Path.of(p.path()).getFileName().toString()).toList()
                .equals(List.of("Person10NativeCorpusBuild.java", "Person10CorpusBuildGate.java")), "Only actual corpus producer source pair allowed");
        List<ControlBuild.FileRef> refs = new ArrayList<>(List.of(addon.compilationTerminal(), terminal.requestRef(), spec.standingRef(), spec.executable(), terminal.stdoutRef(), terminal.stderrRef()));
        refs.addAll(addon.sources()); refs.addAll(addon.classes());
        require(addon.classes().equals(NativeBridgeBuild.inventory(addon.classesRoot())), "Exact complete compiled addon classes differ");
        for (var file : addon.classes()) {
            Path path = Path.of(file.path()); String name = path.getFileName().toString();
            require(path.startsWith(addon.classesRoot().resolve("org/xar/ck3/control/build"))
                    && (name.matches("Person10NativeCorpusBuild(?:\\$[A-Za-z0-9_]+)?[.]class")
                        || name.matches("Person10CorpusBuildGate(?:\\$[A-Za-z0-9_]+)?[.]class")), "Addon cannot override the trusted C16 base");
        }
        for (var ref : refs) ref.verify(); return List.copyOf(refs);
    }
    private static void verifyInputs(Request request, Inputs inputs) throws IOException {
        request.environmentActual().verify(); request.producerRuntimeBuild().verify();
        for (var pin : inputs.toolsAndRuntime()) pin.verify();
        require(NativeBridgeBuild.inventory(inputs.source().sourceRoot()).equals(inputs.source().completeSources()), "Complete original source changed during fixture execution");
    }
    public static List<String> configureArguments(Request request, NativeBridgeBuild.Request source) {
        List<String> argv = new ArrayList<>(List.of(source.tools().cmake().path(), "-S", source.sourceRoot().toString(), "-B", request.buildRoot().toString(),
                "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=ON", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                "-DCMAKE_MAKE_PROGRAM=" + source.tools().ninja().path(), "-DCMAKE_CXX_COMPILER=" + source.tools().compiler().path(),
                "-DCMAKE_C_COMPILER=" + source.tools().compiler().path()));
        source.definitions().forEach(d -> argv.add("-D" + d.option() + "=" + d.value().name())); return List.copyOf(argv);
    }
    public static List<String> buildArguments(Request request, String cmake) {
        List<String> argv = new ArrayList<>(List.of(cmake, "--build", request.buildRoot().toString(), "--parallel", Integer.toString(request.parallelJobs()), "--target"));
        PRODUCERS.forEach(p -> argv.add(p.target())); return List.copyOf(argv);
    }
    private static void run(Request request, Person10CorpusBuildGate gate, List<Command> commands, String role,
            List<String> argv, Map<String,String> environment) throws IOException, InterruptedException {
        gate.check(); Path out = request.outputRoot().resolve(role + ".stdout.log"), err = request.outputRoot().resolve(role + ".stderr.log");
        WindowsJobProcess.ProcessIdentity identity = null; WindowsJobProcess.CommandResult terminal = null;
        commands.add(new Command(role, argv, request.outputRoot().toString(), null, null, null, null));
        try (WindowsJobProcess process = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(argv.getFirst()), argv.subList(1, argv.size()),
                request.outputRoot(), environment, out, err, request.limits().memoryLimitBytes()))) {
            identity = process.identity();
            int roleLimit = role.equals("configure") ? 300 : role.equals("build") ? 3600 : 60;
            terminal = process.await(Duration.ofSeconds(Math.min(request.limits().timeoutSeconds(), roleLimit)), request.limits().deadline(), () -> {
                try { gate.check(); require(Files.size(out) <= (8 << 20) && Files.size(err) <= (8 << 20), "Bounded native logs exceeded"); }
                catch (IOException failure) { throw new IllegalStateException(failure); }
            }, null, WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE).commandResult();
        } finally {
            commands.set(commands.size() - 1, new Command(role, argv, request.outputRoot().toString(), identity, terminal, measured(out), measured(err)));
        }
        require(terminal != null && terminal.passed(), "Native producer/build failed or timed out: " + role);
    }
    static List<ControlBuild.FileRef> inspectProducer(Producer producer, Path directory) throws IOException {
        List<ControlBuild.FileRef> packets = new ArrayList<>(); Set<String> requestIds = new HashSet<>();
        try (var listing = Files.list(directory)) {
            for (Path file : listing.sorted().toList()) {
                SharedSourceFiles.plainAncestors(file); require(Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS)
                        && file.getFileName().toString().endsWith(".json"), "Only original whole JSON packets allowed");
                var pin = ControlBuild.FileRef.measure(file); require(pin.bytes() > 0 && pin.bytes() <= (1 << 20), "Bounded original packet required");
                JsonNode packet = ControlBuild.strictMapper().readTree(Files.readAllBytes(file));
                validatePacket(producer, packet); require(requestIds.add(packet.path("request_id").textValue()), "Original request IDs must be unique per producer");
                pin.verify(); packets.add(pin);
            }
        }
        require(packets.size() == producer.packetCount(), "Actual producer did not output its complete original case set: " + producer.target());
        return List.copyOf(packets);
    }
    static void validatePacket(Producer producer, JsonNode packet) throws IOException {
        require(packet != null && packet.isObject() && "command_result".equals(packet.path("type").asText())
                && packet.path("protocol_version").isIntegralNumber() && packet.path("protocol_version").canConvertToInt() && packet.path("protocol_version").intValue() == 1
                && packet.path("ok").isBoolean() && packet.path("ok").booleanValue()
                && packet.path("request_id").isTextual() && !packet.path("request_id").textValue().isBlank(), "Actual complete command_result required");
        JsonNode result = packet.path("result"), transition = result.path("battle_terminal_transition");
        require(result.isObject() && result.path("accepted").isBoolean() && result.path("accepted").booleanValue()
                && result.path("step").isTextual() && result.path("step").textValue().startsWith("query-battle-terminal-transition-v1-none:characters:")
                && transition.isObject() && "production_exact_battle_terminal_transition".equals(transition.path("contract_stage").asText())
                && transition.path("character_observations").isArray() && !transition.path("character_observations").isEmpty(), "Actual character-query whole terminal payload required");
        int[] count = {0}; inspectLeaf(transition.path("character_observations"), producer.field(), count, 0);
        require(count[0] > 0, "Original whole packet lacks nonnull current-.4 " + producer.field());
    }
    private static void inspectLeaf(JsonNode node, String field, int[] count, int depth) throws IOException {
        require(depth <= 64, "Bounded native packet nesting required");
        if (node.isObject()) {
            if (node.has(field) && !node.get(field).isNull()) {
                JsonNode leaf = node.get(field);
                require(leaf.isObject() && "1.20.0.4".equals(leaf.path("build_version").asText())
                        && EXE_SHA.equalsIgnoreCase(leaf.path("executable_sha256").asText()), "Mixed/old build cannot qualify current Person corpus");
                count[0]++;
            }
            var values = node.elements(); while (values.hasNext()) inspectLeaf(values.next(), field, count, depth + 1);
        } else if (node.isArray()) for (JsonNode child : node) inspectLeaf(child, field, count, depth + 1);
    }
    static List<ControlBuild.FileRef> cachePins(Path buildRoot) throws IOException {
        List<ControlBuild.FileRef> pins = new ArrayList<>();
        for (String name : List.of("CMakeCache.txt", "build.ninja", "compile_commands.json")) pins.add(ControlBuild.FileRef.measure(buildRoot.resolve(name)));
        return List.copyOf(pins);
    }
    static ControlBuild.FileRef writeNew(Path output, Object value) throws IOException {
        SharedSourceFiles.plainAncestors(output); byte[] raw = RootNativePlanJson.mapper().writeValueAsBytes(value);
        require(raw.length <= MAX_JSON, "Finite producer metadata required");
        Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE); return ControlBuild.FileRef.measure(output);
    }
    private static ControlBuild.FileRef measured(Path file) throws IOException { return Files.exists(file, LinkOption.NOFOLLOW_LINKS) ? ControlBuild.FileRef.measure(file) : null; }
    static Path absolute(Path path) { if (path == null || !path.isAbsolute() || !path.equals(path.normalize())) throw new IllegalArgumentException("Absolute normalized path required"); return path; }
    static boolean overlap(Path left, Path right) { return left.startsWith(right) || right.startsWith(left); }
    static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
    public static void main(String[] args) throws Exception {
        require(args.length == 3 && args[0].equals("execute") && args[2].matches("[0-9a-f]{64}"), "execute EXACT_REQUEST_JSON EXPECTED_SHA256 required");
        var request = ControlBuild.FileRef.measure(absolute(Path.of(args[1]))); require(request.sha256().equals(args[2]), "Request SHA differs");
        Actual actual = execute(request); if (actual.status() != Status.PASS) throw new IOException(actual.error());
    }
}
