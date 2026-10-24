package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Explicit R3 inputs. The original/R2 roles and their historical command reconstruction remain unchanged. */
public final class FullParityCurrentBindings {
    public static final String SCHEMA = "xar.full-parity-current-oracle-inputs/v1";
    public static final int MAX_INPUT_BYTES = 1 << 20;
    public static final String INVOCATION_SCHEMA = "xar.full-parity-current-maven-invocation/v1";
    public static final String INVOCATION_FILE = "xar-full-parity-current-invocation.json";
    public static final String MANAGERS_TARGET = "native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/ArmyStrengthsManagers.java";
    public static final String DETACHMENT_TARGET = "native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/ArmyStrengthsDetachment.java";
    private static final String INPUT = "-Dxar.fullParity.current.inputs=";
    private static final String INPUT_BYTES = "-Dxar.fullParity.current.inputs.bytes=";
    private static final String INPUT_SHA = "-Dxar.fullParity.current.inputs.sha256=";
    private static final String MACHINE = "-Dxar.machineId=";
    private static final String SELECTED_ROOT = "-Dxar.fullParity.current.selectedJavaRoot=";
    private static final String COMPILED_ROOT = "-Dxar.army.managers.java.root=";
    private static final String MANAGERS = "-Dxar.army.managers.source=";
    private static final String DETACHMENT = "-Dxar.detachment.java.source=";
    private static final String FIRST_ROOT = "-Dxar.army.reinforcementArrivalFirst.root=";
    private FullParityCurrentBindings() { }

    public enum Role {
        STRENGTHS_MOVEMENT_ORACLE("XAR_STRENGTHS_MOVEMENT_ORACLE_MANIFEST", "xar.army.strengths.movement.oracle.manifest", "xar.army.strengths.movement.oracle.manifest.sha256", 1L << 20),
        STRENGTHS_MONTHLY_ORACLE("XAR_STRENGTHS_MONTHLY_ORACLE_MANIFEST", "xar.monthly.original.manifest", "xar.monthly.original.manifest.sha256", 1L << 20),
        STRENGTHS_SUPPLY_ORACLE("XAR_STRENGTHS_SUPPLY_ORACLE_MANIFEST", "xar.strengths.supply.oracle.manifest", "xar.strengths.supply.oracle.manifest.sha256", 1L << 20),
        FORECAST_READ_ORACLE("XAR_FORECAST_READ_ORACLE_MANIFEST", "xar.forecast.read.oracle.manifest", "xar.forecast.read.oracle.manifest.sha256", 1L << 20),
        STRENGTHS_PHASES_ORACLE("XAR_PHASES_SOURCE_MANIFEST", "xar.phases.source.manifest", "xar.phases.source.manifest.sha256", 1L << 20),
        STRENGTHS_MANAGERS_ORACLE("XAR_ARMY_MANAGERS_SOURCE_MANIFEST", "xar.army.managers.manifest", "xar.army.managers.manifest.sha256", 1L << 20),
        STRENGTHS_MANAGERS_NATIVE_FIXTURES("XAR_ARMY_MANAGERS_NATIVE_FIXTURES", "xar.army.managers.fixtures", "xar.army.managers.fixtures.sha256", 1L << 20),
        COMMANDER_TARGET_ORACLE("XAR_COMMANDER_TARGET_ORACLE_MANIFEST", "xar.commander.target.oracle.manifest", "xar.commander.target.oracle.manifest.sha256", 1L << 20),
        GUARDIAN_OUTGOING_EXECUTABLE("XAR_GUARDIAN_OUTGOING_NATIVE_FIXTURE", "xar.guardian.outgoing.native.fixture", "xar.guardian.outgoing.native.fixture.sha256", 64L << 20),
        FAMILY_SCORER_AGE_EXECUTABLE("XAR_FAMILY_SCORER_AGE_NATIVE_FIXTURE", "xar.family.scorer.age.native.fixture", "xar.family.scorer.age.native.fixture.sha256", 64L << 20),
        FAMILY_RESULT_ORACLE("XAR_FAMILY_RESULT_SOURCE_MANIFEST", "xar.family.result.source.manifest", "xar.family.result.source.manifest.sha256", 1L << 20),
        PERSON_INSTALLED_TRANSFER_EXECUTABLE("XAR_PERSON_INSTALLED_TRANSFER_FIXTURE", "xar.person.installed.transfer.fixture", "xar.person.installed.transfer.fixture.sha256", 64L << 20),
        OWNER_RECALL_12004_WIRE("XAR_OWNER_RECALL_12004_NATIVE_WIRE", "xar.ownerRecall12004.nativeWire", "xar.ownerRecall12004.nativeWireSha256", 8L << 20),
        ARMY_WAR_WINDOW_SOURCE_MAP("XAR_ARMY_WAR_WINDOW_SOURCE_MAP", "xar.armyWarWindow.sourceMap", "xar.armyWarWindow.sourceMapSha256", 1L << 20),
        HOLY_ORDER_NATIVE_CORPUS("XAR_HOLY_ORDER_FIXTURE_CORPUS", "xar.holyOrder.fixtureCorpus", "xar.holyOrder.fixtureCorpusSha256", 1L << 20),
        HOLY_LOAN_SOURCE_PRODUCER_GOLDEN("XAR_HOLY_LOAN_SOURCE_PRODUCER_GOLDEN", "xar.holy.loan.source.producer.golden", "xar.holy.loan.source.producer.golden.sha256", 1L << 20),
        LOSS_ALLOCATION_GOLDEN("XAR_LOSS_ALLOCATION_GOLDEN", "xar.lossallocation.golden", "xar.lossallocation.golden.sha256", 1L << 20),
        RECOVERY_TRANSPORT_ORACLE("XAR_RECOVERY_TRANSPORT_ORACLE_SOURCE", "xar.recovery.transport", "xar.recovery.transport.sha256", 4L << 20),
        RECOVERY_PREPARATION_ORACLE("XAR_RECOVERY_PREPARATION_ORACLE_SOURCE", "xar.recovery.prepare", "xar.recovery.prepare.sha256", 4L << 20),
        SCORE_COMPATIBILITY_CANDIDATE("XAR_SCORE_COMPAT_CANDIDATE", "xar.score.compat.candidate", "xar.score.compat.candidate.sha256", 1L << 20),
        SCORE_REFERENCE_CLIENT("XAR_SCORE_REFERENCE_CLIENT", "xar.score.reference.client", "xar.score.reference.client.sha256", 1L << 20),
        REINFORCEMENT_ARRIVAL_FIRST_CORPUS("XAR_REINFORCEMENT_ARRIVAL_FIRST_MANIFEST", "xar.army.reinforcementArrivalFirst.manifest", "xar.army.reinforcementArrivalFirst.manifest.sha256", 65536);
        private final String environment, pathProperty, shaProperty;
        private final long maxBytes;
        Role(String environment, String pathProperty, String shaProperty, long maxBytes) {
            this.environment = environment; this.pathProperty = pathProperty; this.shaProperty = shaProperty; this.maxBytes = maxBytes;
        }
        public String environment() { return environment; }
        public String pathProperty() { return pathProperty; }
        public String shaProperty() { return shaProperty; }
        public long maxBytes() { return maxBytes; }
        public String bytesProperty() { return "xar.fullParity.fixture." + name() + ".bytes"; }
        String pathArgument() { return "-D" + pathProperty + "="; }
        String shaArgument() { return "-D" + shaProperty + "="; }
        String bytesArgument() { return "-D" + bytesProperty() + "="; }
    }
    public record Fixture(Role role, FileRef source) {
        public Fixture {
            Objects.requireNonNull(role); Objects.requireNonNull(source); absolute(source.path());
            require(source.bytes() > 0 && source.bytes() <= role.maxBytes(), "Finite actual R3 fixture role bound required");
        }
        List<String> arguments() { return List.of(role.pathArgument() + source.path(), role.shaArgument() + source.sha256(), role.bytesArgument() + source.bytes()); }
    }
    public record NativePublication(NativeFixtureCorpora.Kind kind, FileRef proofRef, FileRef sourceMapRef) {
        public NativePublication { Objects.requireNonNull(kind); Objects.requireNonNull(proofRef); Objects.requireNonNull(sourceMapRef); require(proofRef.bytes() > 0 && proofRef.bytes() <= MAX_INPUT_BYTES && sourceMapRef.bytes() > 0 && sourceMapRef.bytes() <= MAX_INPUT_BYTES, "Finite exact native publication proof/source map required"); }
    }
    /** Measured data, not execution authority. Root's actual fixture request binds this exact immutable file. */
    public record Inputs(String schema, String machineId, String observedAtUtc,
            FullParityOracleBindings.ResumedBindings originalR2, FileRef pythonRef, FileRef nativeProducerRef,
            String selectedJavaRoot, FileRef managersSource, FileRef detachmentSource,
            List<Fixture> additionalFixtures, String first7Root, List<NativePublication> nativePublications) {
        public Inputs {
            require(SCHEMA.equals(schema) && machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{0,63}") && !machineId.equals("unknown"), "Exact R3 measured input schema and machine required"); Instant.parse(observedAtUtc);
            Objects.requireNonNull(originalR2); Objects.requireNonNull(pythonRef); Objects.requireNonNull(nativeProducerRef);
            absolute(selectedJavaRoot); sources(selectedJavaRoot, managersSource, detachmentSource); fixtures(additionalFixtures); additionalFixtures = List.copyOf(additionalFixtures); absolute(first7Root);
            require(pythonRef.path().equals(originalR2.python()) && nativeProducerRef.path().equals(originalR2.nativeProducerSource())
                    && nativeProducerRef.sha256().equals(originalR2.nativeProducerSha256()), "R3 source/interpreter pins crossed the original bindings");
            nativePublications = List.copyOf(nativePublications);
            require(nativePublications.stream().map(NativePublication::kind).toList().equals(List.of(NativeFixtureCorpora.Kind.values())), "All three original native publication proofs required");
        }
    }
    public record Bindings(FileRef inputsRef, String machineId, FullParityOracleBindings.ResumedBindings originalR2,
            String selectedJavaRoot, String compiledJavaRoot, FileRef managersSource, FileRef detachmentSource,
            List<Fixture> additionalFixtures, String first7Root) implements FullParityOracleBindings.SelectedBindings {
        public Bindings {
            Objects.requireNonNull(inputsRef); require(inputsRef.bytes() > 0 && inputsRef.bytes() <= MAX_INPUT_BYTES, "Bounded exact R3 input permit required"); absolute(inputsRef.path());
            require(machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{0,63}") && !machineId.equals("unknown"), "One recorded actual machine role required");
            Objects.requireNonNull(originalR2); absolute(selectedJavaRoot); sources(compiledJavaRoot, managersSource, detachmentSource);
            fixtures(additionalFixtures); additionalFixtures = List.copyOf(additionalFixtures); absolute(first7Root);
        }
        @Override public String python() { return originalR2.python(); }
        @Override public List<String> mavenArguments() {
            var result = new ArrayList<>(originalR2.mavenArguments());
            result.addAll(List.of(INPUT + inputsRef.path(), INPUT_BYTES + inputsRef.bytes(), INPUT_SHA + inputsRef.sha256(), MACHINE + machineId, SELECTED_ROOT + selectedJavaRoot,
                    COMPILED_ROOT + compiledJavaRoot, MANAGERS + managersSource.path(), DETACHMENT + detachmentSource.path(), FIRST_ROOT + first7Root));
            result.addAll(sourceArguments("MANAGERS_JAVA_SOURCE", managersSource)); result.addAll(sourceArguments("DETACHMENT_JAVA_SOURCE", detachmentSource));
            for (Fixture fixture : additionalFixtures) result.addAll(fixture.arguments()); return List.copyOf(result);
        }
        public void requireCompiledRoot(Path actual) { require(absolute(compiledJavaRoot).equals(actual.toAbsolutePath().normalize()), "R3 source properties must bind the exact compiled Maven snapshot"); }
    }
    /** This actual producer output is pinned inside the complete deployment, including the original command bytes. */
    public record Invocation(String schema, String sourceRoot, String compiledRoot, String workRoot, String attempt,
            FileRef settingsRef, FileRef commandRef, List<String> mavenArguments) {
        public Invocation {
            require(INVOCATION_SCHEMA.equals(schema), "Exact completed R3 command schema required"); absolute(sourceRoot); absolute(compiledRoot); absolute(workRoot);
            require(attempt != null && attempt.matches("[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}"), "Exact completed Maven attempt required");
            Objects.requireNonNull(settingsRef); Objects.requireNonNull(commandRef); mavenArguments = List.copyOf(mavenArguments);
            require(settingsRef.bytes() > 0 && settingsRef.bytes() <= 65536 && commandRef.bytes() > 0 && commandRef.bytes() <= 262144, "Finite original settings and command files required");
            require(!mavenArguments.isEmpty() && mavenArguments.getLast().equals("verify"), "Completed full Maven verify invocation required");
        }
    }
    static void retainCompletedInvocation(ControlBuild.Config config, Path settings, Path snapshot, Path build,
            Path deployment, List<String> arguments) throws IOException {
        Bindings bindings = fromRecordedArguments(arguments); bindings.requireCompiledRoot(snapshot);
        require(bindings.selectedJavaRoot().equals(config.sourceRoot().toString()), "Actual R3 input source must equal the selected complete source root");
        Inputs inputs = readInputs(bindings.inputsRef()); verify(inputs); requireExecutedInputs(inputs, bindings);
        Invocation invocation = new Invocation(INVOCATION_SCHEMA, config.sourceRoot().toString(), snapshot.toString(), config.workRoot().toString(), config.attempt(),
                FileRef.measure(settings), FileRef.measure(config.workRoot().resolve("logs/build-" + config.attempt() + "-verify.cmd")), arguments);
        Files.write(deployment.resolve(INVOCATION_FILE), ControlBuild.strictMapper().writeValueAsBytes(invocation), StandardOpenOption.CREATE_NEW);
    }
    /** Completed evidence only: uses original pins and argv, never current environment or fixture authority. */
    public static Bindings completedBuildBindings(ControlBuild.BuildReceipt receipt) throws IOException {
        require(receipt.sourceLimitProfile() == ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3
                && receipt.targetKind() == ControlBuild.TargetKind.SERVICE_FAST_JAR, "Exact full R3 service receipt required");
        Path path = absolute(receipt.deploymentRoot()).resolve(INVOCATION_FILE);
        var pins = receipt.completeDeployment().stream().filter(ref -> absolute(ref.path()).equals(path)).toList();
        require(pins.size() == 1 && pins.getFirst().bytes() <= MAX_INPUT_BYTES, "Complete deployment must pin its actual R3 invocation");
        FileRef ref = pins.getFirst(); ref.verify(); Invocation invocation = ControlBuild.strictMapper().readValue(Files.readAllBytes(path), Invocation.class); ref.verify();
        require(invocation.sourceRoot().equals(receipt.sourceRoot()) && invocation.compiledRoot().equals(receipt.compiledSourceRoot()), "Actual invocation crossed receipt source roots");
        Path work = absolute(invocation.workRoot()), snapshot = absolute(invocation.compiledRoot()), build = work.resolve("build").resolve(invocation.attempt());
        require(snapshot.equals(work.resolve("scratch/source-" + invocation.attempt()))
                && absolute(invocation.settingsRef().path()).equals(work.resolve("logs/build-" + invocation.attempt() + "-settings.xml"))
                && absolute(invocation.commandRef().path()).equals(work.resolve("logs/build-" + invocation.attempt() + "-verify.cmd"))
                && absolute(receipt.deploymentRoot()).equals(build.resolve("ck3-control-local-service/quarkus-app")), "Actual R3 output layout changed");
        invocation.settingsRef().verify(); invocation.commandRef().verify(); Bindings bindings = fromRecordedArguments(invocation.mavenArguments()); bindings.requireCompiledRoot(snapshot);
        require(bindings.selectedJavaRoot().equals(receipt.sourceRoot()), "Recorded R3 source selection differs from its compiled receipt");
        var config = new ControlBuild.Config(Path.of(receipt.sourceRoot()), work, Path.of(receipt.capacityReleaseRef().path()), invocation.attempt(), "completed-r3-evidence-reader", null,
                Path.of(receipt.javaExecutableRef().path()).getParent().getParent(), CiBootstrap.MINIMUM_MAVEN_VERSION, 900, receipt.targetKind(), receipt.sourceLimitProfile());
        var expected = ControlBuild.reactorVerifyArguments(config, Path.of(invocation.settingsRef().path()), snapshot, build, bindings.python(), bindings);
        require(expected.equals(invocation.mavenArguments()) && java.util.Arrays.equals(Files.readAllBytes(Path.of(invocation.commandRef().path())),
                ControlBuild.mavenBatchText(null, expected).getBytes(java.nio.charset.StandardCharsets.UTF_8)), "Actual completed R3 command differs from its strict recorded arguments");
        for (FileRef javaSource : List.of(bindings.managersSource(), bindings.detachmentSource())) require(receipt.compiledSourcePins().contains(javaSource), "R3 source properties must be exact actual compiler input pins");
        requireExecutedInputs(readInputs(bindings.inputsRef()), bindings);
        return bindings;
    }

    public static FileRef produce(Path selectedJavaRoot, Map<String, String> environment, Path output) throws IOException {
        var r2 = (FullParityOracleBindings.ResumedBindings)FullParityOracleBindings.fromEnvironment(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2, environment);
        Path root = plainDirectory(selectedJavaRoot); var additional = new ArrayList<Fixture>();
        for (Role role : Role.values()) additional.add(new Fixture(role, actual(absolute(required(environment, role.environment())), role.maxBytes())));
        FileRef first = fixture(additional, Role.REINFORCEMENT_ARRIVAL_FIRST_CORPUS).source();
        var firstManifest = ReinforcementArrivalFirstCorpus.readManifest(first); ReinforcementArrivalFirstCorpus.require(first, firstManifest.corpusRoot());
        var publications = new ArrayList<NativePublication>();
        for (var kind : NativeFixtureCorpora.Kind.values()) {
            FileRef artifact = fixture(additional, publicationRole(kind)).source(); FileRef proof = actual(NativeFixtureCorpora.proofPath(Path.of(artifact.path())), MAX_INPUT_BYTES);
            var produced = NativeFixtureCorpora.readProduction(proof); var request = NativeFixtureCorpora.readRequest(produced.requestRef());
            publications.add(new NativePublication(kind, proof, request.sourceMapRef()));
        }
        Inputs inputs = new Inputs(SCHEMA, WindowsJobProcess.currentMachineId(), Instant.now().toString(), r2,
                actual(Path.of(r2.python()), 64L << 20), actual(Path.of(r2.nativeProducerSource()), 16L << 20), root.toString(),
                actual(root.resolve(MANAGERS_TARGET), 1L << 20), actual(root.resolve(DETACHMENT_TARGET), 1L << 20), additional, firstManifest.corpusRoot(), publications);
        verify(inputs); Path destination = absolute(output.toString()); SharedSourceFiles.plainAncestors(destination);
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(inputs); require(raw.length <= MAX_INPUT_BYTES, "Finite R3 input serialization required");
        Files.write(destination, raw, StandardOpenOption.CREATE_NEW); FileRef result = FileRef.measure(destination);
        require(inputs.equals(readInputs(result)), "Exact persisted R3 producer roundtrip required"); return result;
    }
    public static Inputs readInputs(FileRef ref) throws IOException {
        require(ref.bytes() > 0 && ref.bytes() <= MAX_INPUT_BYTES, "Finite exact R3 input role required"); ref.verify();
        var result = ControlBuild.strictMapper().readValue(Files.readAllBytes(absolute(ref.path())), Inputs.class); ref.verify(); return result;
    }
    public static void verify(Inputs inputs) throws IOException {
        require(inputs.machineId().equals(WindowsJobProcess.currentMachineId()), "Actual R3 inputs belong to a different execution machine");
        inputs.pythonRef().verify(); inputs.nativeProducerRef().verify(); inputs.managersSource().verify(); inputs.detachmentSource().verify();
        for (var item : inputs.originalR2().nativeFixtures()) item.source().verify();
        Person10NativeCorpus.require(inputs.originalR2().person10Corpus().manifest(), inputs.originalR2().person10Corpus().root());
        for (Fixture fixture : inputs.additionalFixtures()) fixture.source().verify();
        ReinforcementArrivalFirstCorpus.require(fixture(inputs.additionalFixtures(), Role.REINFORCEMENT_ARRIVAL_FIRST_CORPUS).source(), inputs.first7Root());
        for (NativePublication publication : inputs.nativePublications()) {
            FileRef expectedMap = switch (publication.kind()) {
                case MANAGERS -> fixture(inputs.additionalFixtures(), Role.STRENGTHS_MANAGERS_ORACLE).source();
                case HOLY_ORDER -> fixture(inputs.additionalFixtures(), Role.ARMY_WAR_WINDOW_SOURCE_MAP).source();
                case HOLY_LOAN -> publication.sourceMapRef();
            };
            require(expectedMap.equals(publication.sourceMapRef()), "Native publication source map differs from its selected domain oracle role");
            NativeFixtureCorpora.requireProduction(publication.proofRef(), fixture(inputs.additionalFixtures(), publicationRole(publication.kind())).source(), publication.kind(), expectedMap);
        }
    }
    public static Bindings fromEnvironment(Map<String, String> environment, Path compiledRoot) {
        try {
            var canonical = CanonicalOracleEnvironment.require(environment);
            Path path = absolute(required(environment, "XAR_FULL_PARITY_CURRENT_INPUTS")); String sha = required(environment, "XAR_FULL_PARITY_CURRENT_INPUTS_SHA256");
            require(sha.matches("[a-f0-9]{64}"), "Canonical R3 inputs SHA required"); FileRef inputRef = actual(path, MAX_INPUT_BYTES);
            require(inputRef.sha256().equals(sha), "Actual R3 input file changed from its Root selected pin"); Inputs inputs = readInputs(inputRef); verify(inputs);
            require(inputs.originalR2().python().equals(canonical.python()) && inputs.originalR2().repositoryRoot().equals(canonical.repositoryRoot()), "One canonical interpreter/repository must serve all R3 consumers");
            Path root = plainDirectory(compiledRoot); FileRef managers = actual(root.resolve(MANAGERS_TARGET), 1L << 20), detachment = actual(root.resolve(DETACHMENT_TARGET), 1L << 20);
            require(sameContent(inputs.managersSource(), managers) && sameContent(inputs.detachmentSource(), detachment), "Compiled source bodies differ from their exact selected producer inputs");
            return new Bindings(inputRef, inputs.machineId(), inputs.originalR2(), inputs.selectedJavaRoot(), root.toString(), managers, detachment, inputs.additionalFixtures(), inputs.first7Root());
        } catch (IOException error) { throw new IllegalArgumentException("NOT EXECUTED: complete source-bound R3 inputs unavailable", error); }
    }
    /** Completed receipt replay reconstructs original values only; it never reads current environment or files. */
    public static Bindings fromRecordedArguments(List<String> arguments) {
        var original = (FullParityOracleBindings.ResumedBindings)FullParityOracleBindings.fromRecordedArguments(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2, arguments);
        var additional = new ArrayList<Fixture>(); for (Role role : Role.values()) additional.add(new Fixture(role,
                new FileRef(one(arguments, role.pathArgument()), bytes(one(arguments, role.bytesArgument())), one(arguments, role.shaArgument()))));
        FileRef input = new FileRef(one(arguments, INPUT), bytes(one(arguments, INPUT_BYTES)), one(arguments, INPUT_SHA));
        return new Bindings(input, one(arguments, MACHINE), original, one(arguments, SELECTED_ROOT), one(arguments, COMPILED_ROOT),
                recordedSource(arguments, "MANAGERS_JAVA_SOURCE", MANAGERS), recordedSource(arguments, "DETACHMENT_JAVA_SOURCE", DETACHMENT), additional, one(arguments, FIRST_ROOT));
    }
    public static void requireExecutedInputs(Inputs selected, Bindings executed) throws IOException {
        require(selected.machineId().equals(executed.machineId()) && selected.originalR2().equals(executed.originalR2()) && selected.selectedJavaRoot().equals(executed.selectedJavaRoot())
                && sameContent(selected.managersSource(), executed.managersSource()) && sameContent(selected.detachmentSource(), executed.detachmentSource())
                && selected.additionalFixtures().equals(executed.additionalFixtures()) && selected.first7Root().equals(executed.first7Root()), "Executed R3 command crossed its actual fixture-production input contract");
    }
    private static FileRef recordedSource(List<String> arguments, String name, String path) { return new FileRef(one(arguments, path), bytes(one(arguments, "-Dxar.fullParity.fixture." + name + ".bytes=")), one(arguments, "-Dxar.fullParity.fixture." + name + ".sha256=")); }
    private static Role publicationRole(NativeFixtureCorpora.Kind kind) { return switch (kind) { case MANAGERS -> Role.STRENGTHS_MANAGERS_NATIVE_FIXTURES; case HOLY_ORDER -> Role.HOLY_ORDER_NATIVE_CORPUS; case HOLY_LOAN -> Role.HOLY_LOAN_SOURCE_PRODUCER_GOLDEN; }; }
    private static List<String> sourceArguments(String name, FileRef source) { return List.of("-Dxar.fullParity.fixture." + name + ".bytes=" + source.bytes(), "-Dxar.fullParity.fixture." + name + ".sha256=" + source.sha256()); }
    private static void sources(String rootText, FileRef managers, FileRef detachment) {
        Path root = absolute(rootText); Objects.requireNonNull(managers); Objects.requireNonNull(detachment);
        require(absolute(managers.path()).equals(root.resolve(MANAGERS_TARGET)) && absolute(detachment.path()).equals(root.resolve(DETACHMENT_TARGET))
                && managers.bytes() > 0 && managers.bytes() <= (1 << 20) && detachment.bytes() > 0 && detachment.bytes() <= (1 << 20), "Unique full installed Java producer paths and finite source pins required");
    }
    private static void fixtures(List<Fixture> values) { require(values != null && values.stream().map(Fixture::role).toList().equals(List.of(Role.values())), "Complete unique ordered R3 fixture roles required"); }
    private static Fixture fixture(List<Fixture> values, Role role) { return values.stream().filter(value -> value.role() == role).findFirst().orElseThrow(); }
    private static boolean sameContent(FileRef first, FileRef second) { return first.bytes() == second.bytes() && first.sha256().equals(second.sha256()); }
    private static FileRef actual(Path path, long max) throws IOException {
        SharedSourceFiles.plainAncestors(path); require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && path.toRealPath().equals(path)
                && Files.size(path) > 0 && Files.size(path) <= max, "Actual plain bounded selected source required: " + path);
        FileRef result = FileRef.measure(path); result.verify(); return result;
    }
    private static Path plainDirectory(Path path) throws IOException { Path result = absolute(path.toString()); SharedSourceFiles.plainAncestors(result); require(Files.isDirectory(result, LinkOption.NOFOLLOW_LINKS) && result.toRealPath().equals(result), "Actual canonical source root required"); return result; }
    private static long bytes(String value) { require(value.matches("[1-9][0-9]{0,8}"), "Canonical bounded recorded source bytes required"); return Long.parseLong(value); }
    private static String one(List<String> arguments, String prefix) { var values = arguments.stream().filter(arg -> arg.startsWith(prefix)).map(arg -> arg.substring(prefix.length())).toList(); require(values.size() == 1 && !values.getFirst().isBlank(), "One exact recorded R3 property required: " + prefix); return values.getFirst(); }
    private static String required(Map<String, String> environment, String name) { String result = environment.get(name); require(result != null && !result.isBlank(), "NOT EXECUTED: required " + name); return result; }
    private static Path absolute(String value) { require(value != null && value.length() <= 4096 && value.chars().noneMatch(c -> c < 32 || c == 127), "Plain bounded source path required"); Path path = Path.of(value); require(path.isAbsolute() && path.equals(path.normalize()), "Canonical absolute source role required"); return path; }
    private static void require(boolean value, String reason) { if (!value) throw new IllegalArgumentException(reason); }
}
