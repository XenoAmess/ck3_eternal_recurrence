package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** The original producer and actual offline Native fixtures selected for the whole Java reactor. */
public final class FullParityOracleBindings {
    public static final String NATIVE_RELATIVE = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py";
    private static final String ROOT_PYTHON = "-Dxar.rootContext.pythonExecutable=";
    private static final String PYTHON = "-Dxar.python=";
    private static final String REPOSITORY = "-Dxar.repository.root=";
    private static final String NATIVE_PYTHON = "-Dxar.native.producer.python=";
    private static final String NATIVE_SOURCE = "-Dxar.native.producer.source=";
    private static final String NATIVE_SHA256 = "-Dxar.native.producer.sha256=";
    private FullParityOracleBindings() { }

    public sealed interface SelectedBindings permits Bindings, ResumedBindings, FullParityCurrentBindings.Bindings {
        String python();
        List<String> mavenArguments();
    }

    /** Closed fixture roles: neither arbitrary Maven properties nor cached inferred inputs are accepted. */
    public enum FixtureRole {
        M3_TIMELINE_WHOLE("XAR_M3_TIMELINE_NATIVE_WHOLE", "xar.m3.timeline.nativeWhole", "xar.m3.timeline.nativeWholeSha256"),
        ARMY_DEFAULT_RAISE("XAR_ARMY_DEFAULT_RAISE_FIXTURE", "xar.army.defaultRaise.fixture", "xar.army.defaultRaise.sha256");
        private final String environment, pathProperty, shaProperty;
        FixtureRole(String environment, String pathProperty, String shaProperty) {
            this.environment = environment; this.pathProperty = pathProperty; this.shaProperty = shaProperty;
        }
        String pathArgument() { return "-D" + pathProperty + "="; }
        String shaArgument() { return "-D" + shaProperty + "="; }
        String bytesArgument() { return "-Dxar.fullParity.fixture." + name() + ".bytes="; }
    }
    public record BoundFixture(FixtureRole role, ControlBuild.FileRef source) {
        public BoundFixture {
            Objects.requireNonNull(role); Objects.requireNonNull(source); absolute(source.path());
            if (source.bytes() < 1 || source.bytes() > 1L << 20)
                throw new IllegalArgumentException("Bounded actual original Native fixture required");
        }
        List<String> arguments() {
            return List.of(role.pathArgument() + source.path(), role.shaArgument() + source.sha256(),
                    role.bytesArgument() + source.bytes());
        }
    }

    /** Pure recorded contract. Construction does not consult today's filesystem or environment. */
    public record Bindings(String python, String repositoryRoot, String nativeProducerSource,
            String nativeProducerSha256, List<BoundFixture> nativeFixtures) implements SelectedBindings {
        public Bindings {
            python = absolute(python).toString(); repositoryRoot = absolute(repositoryRoot).toString();
            nativeProducerSource = absolute(nativeProducerSource).toString(); nativeFixtures = List.copyOf(nativeFixtures);
            if (!Path.of(nativeProducerSource).equals(Path.of(repositoryRoot).resolve(NATIVE_RELATIVE).normalize())
                    || nativeProducerSha256 == null || !nativeProducerSha256.matches("[a-f0-9]{64}")
                    || !nativeFixtures.stream().map(BoundFixture::role).toList().equals(List.of(FixtureRole.values())))
                throw new IllegalArgumentException("Exact selected producer and complete ordered Native fixture roles required");
        }
        public List<String> mavenArguments() {
            List<String> result = new ArrayList<>(List.of(PYTHON + python, REPOSITORY + repositoryRoot,
                    NATIVE_PYTHON + python, NATIVE_SOURCE + nativeProducerSource, NATIVE_SHA256 + nativeProducerSha256));
            for (BoundFixture fixture : nativeFixtures) result.addAll(fixture.arguments());
            return List.copyOf(result);
        }
    }

    /** Live producer: measure the actual selected source and both original Native fixtures on this machine. */
    public static Bindings fromEnvironment(Map<String, String> environment) {
        Objects.requireNonNull(environment, "selected oracle environment");
        Path python = absolute(required(environment, "XAR_ORACLE_PYTHON"));
        Path repository = absolute(required(environment, "XAR_ORACLE_REPO"));
        try {
            if (!Files.isRegularFile(python, LinkOption.NOFOLLOW_LINKS) || Files.size(python) <= 0
                    || !Files.isDirectory(repository, LinkOption.NOFOLLOW_LINKS))
                throw new IOException("Selected absolute interpreter/repository is unavailable");
            python = python.toRealPath(); repository = repository.toRealPath();
            Path source = repository.resolve(NATIVE_RELATIVE);
            if (!Files.isRegularFile(source, LinkOption.NOFOLLOW_LINKS) || Files.size(source) <= 0
                    || Files.size(source) > (16L << 20) || !source.toRealPath().equals(source))
                throw new IOException("Selected ordinary Native producer source is unavailable or escapes the repository");
            ControlBuild.FileRef measured = ControlBuild.FileRef.measure(source); measured.verify();
            List<BoundFixture> fixtures = new ArrayList<>();
            for (FixtureRole role : FixtureRole.values()) {
                Path fixture = absolute(required(environment, role.environment));
                if (!Files.isRegularFile(fixture, LinkOption.NOFOLLOW_LINKS) || !fixture.toRealPath().equals(fixture)
                        || Files.size(fixture) < 1 || Files.size(fixture) > 1L << 20)
                    throw new IOException("Actual original Native fixture unavailable: " + role);
                ControlBuild.FileRef ref = ControlBuild.FileRef.measure(fixture); ref.verify();
                fixtures.add(new BoundFixture(role, ref));
            }
            return new Bindings(python.toString(), repository.toString(), measured.path(), measured.sha256(), fixtures);
        } catch (IOException error) {
            throw new IllegalArgumentException("NOT EXECUTED: full-parity original producer inputs unavailable", error);
        }
    }

    /** Historical reader: reconstruct only immutable recorded values, without rehashing today's originals. */
    public static Bindings fromRecordedArguments(List<String> recordedArguments) {
        List<String> arguments = List.copyOf(recordedArguments);
        List<BoundFixture> fixtures = new ArrayList<>();
        for (FixtureRole role : FixtureRole.values()) {
            String size = one(arguments, role.bytesArgument());
            if (!size.matches("[1-9][0-9]{0,6}")) throw new IllegalArgumentException("Canonical recorded fixture byte count required");
            fixtures.add(new BoundFixture(role, new ControlBuild.FileRef(one(arguments, role.pathArgument()),
                    Long.parseLong(size), one(arguments, role.shaArgument()))));
        }
        Bindings bindings = new Bindings(one(arguments, PYTHON), one(arguments, REPOSITORY),
                one(arguments, NATIVE_SOURCE), one(arguments, NATIVE_SHA256), fixtures);
        if (!absolute(one(arguments, ROOT_PYTHON)).equals(Path.of(bindings.python()))
                || !absolute(one(arguments, NATIVE_PYTHON)).equals(Path.of(bindings.python())))
            throw new IllegalArgumentException("One original interpreter must bind all recorded producers and consumers");
        return bindings;
    }
    /** R2 is independent: historical bindings keep exactly their original two roles. */
    public enum ResumedFixtureRole {
        M3_TIMELINE_WHOLE("XAR_M3_TIMELINE_NATIVE_WHOLE", "xar.m3.timeline.nativeWhole", "xar.m3.timeline.nativeWholeSha256", 1L << 20),
        ARMY_DEFAULT_RAISE("XAR_ARMY_DEFAULT_RAISE_FIXTURE", "xar.army.defaultRaise.fixture", "xar.army.defaultRaise.sha256", 1L << 20),
        BATTLE_CONTEXT_SOURCE("XAR_BATTLE_CONTEXT_SOURCE_FIXTURE", "xar.battle.context.source.fixture", "xar.battle.context.source.fixture.sha256", 64L << 20),
        BATTLE_CONTEXT_ADMISSIONS("XAR_BATTLE_CONTEXT_ADMISSIONS_FIXTURE", "xar.battle.context.admissions.fixture", "xar.battle.context.admissions.fixture.sha256", 64L << 20),
        RELIGION_CONTEXT_SOURCE_MAP("XAR_RELIGION_CONTEXT_SOURCE_MAP", "xar.religionContext.sourceMap", "xar.religionContext.sourceMapSha256", 1L << 20),
        ARMY_STRENGTHS_ORACLE_MANIFEST("XAR_ARMY_STRENGTHS_ORACLE_MANIFEST", "xar.army.strengths.oracle.manifest", "xar.army.strengths.oracle.manifest.sha256", 1L << 20),
        CONSTRUCTION_REFUND_PRODUCER_GOLDEN("XAR_CONSTRUCTION_REFUND_PRODUCER_GOLDEN", "xar.construction.refund.producer.golden", "xar.construction.refund.producer.golden.sha256", 1L << 20);
        private final String environment, pathProperty, shaProperty;
        private final long maxBytes;
        ResumedFixtureRole(String environment, String pathProperty, String shaProperty, long maxBytes) {
            this.environment = environment; this.pathProperty = pathProperty; this.shaProperty = shaProperty; this.maxBytes = maxBytes;
        }
        String pathArgument() { return "-D" + pathProperty + "="; }
        String shaArgument() { return "-D" + shaProperty + "="; }
        String bytesArgument() { return "-Dxar.fullParity.fixture." + name() + ".bytes="; }
    }
    public record ResumedFixture(ResumedFixtureRole role, ControlBuild.FileRef source) {
        public ResumedFixture {
            Objects.requireNonNull(role); Objects.requireNonNull(source); absolute(source.path());
            if (source.bytes() < 1 || source.bytes() > role.maxBytes) throw new IllegalArgumentException("Finite original fixture role bound exceeded");
        }
        List<String> arguments() {
            return List.of(role.pathArgument() + source.path(), role.shaArgument() + source.sha256(), role.bytesArgument() + source.bytes());
        }
    }
    public record CorpusBinding(String root, ControlBuild.FileRef manifest) {
        public CorpusBinding {
            absolute(root); Objects.requireNonNull(manifest); absolute(manifest.path());
            if (manifest.bytes() < 1 || manifest.bytes() > Person10NativeCorpus.MANIFEST_MAX_BYTES
                    || Path.of(manifest.path()).startsWith(Path.of(root)))
                throw new IllegalArgumentException("Exact bounded corpus manifest outside original input root required");
        }
        List<String> arguments() {
            return List.of("-Dxar.person10.nativeCorpus=" + root,
                    "-Dxar.person10.nativeCorpus.manifest=" + manifest.path(),
                    "-Dxar.person10.nativeCorpus.manifest.sha256=" + manifest.sha256(),
                    "-Dxar.fullParity.fixture.PERSON10_NATIVE_CORPUS_MANIFEST.bytes=" + manifest.bytes());
        }
    }
    public record ResumedBindings(ControlBuild.SourceLimitProfile profile, String python, String repositoryRoot,
            String nativeProducerSource, String nativeProducerSha256, List<ResumedFixture> nativeFixtures,
            CorpusBinding person10Corpus) implements SelectedBindings {
        public ResumedBindings {
            if (profile != ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2)
                throw new IllegalArgumentException("Explicit R2 selected profile required");
            python = absolute(python).toString(); repositoryRoot = absolute(repositoryRoot).toString();
            nativeProducerSource = absolute(nativeProducerSource).toString(); nativeFixtures = List.copyOf(nativeFixtures);
            Objects.requireNonNull(person10Corpus);
            if (!Path.of(nativeProducerSource).equals(Path.of(repositoryRoot).resolve(NATIVE_RELATIVE).normalize())
                    || nativeProducerSha256 == null || !nativeProducerSha256.matches("[a-f0-9]{64}")
                    || !nativeFixtures.stream().map(ResumedFixture::role).toList().equals(List.of(ResumedFixtureRole.values())))
                throw new IllegalArgumentException("Exact original producer and all ordered R2 fixture roles required");
        }
        public List<String> mavenArguments() {
            List<String> result = new ArrayList<>(List.of(PYTHON + python, REPOSITORY + repositoryRoot,
                    NATIVE_PYTHON + python, NATIVE_SOURCE + nativeProducerSource, NATIVE_SHA256 + nativeProducerSha256));
            for (ResumedFixture fixture : nativeFixtures) result.addAll(fixture.arguments());
            result.addAll(person10Corpus.arguments()); return List.copyOf(result);
        }
    }

    public static SelectedBindings fromEnvironment(ControlBuild.SourceLimitProfile profile, Map<String, String> environment) {
        if (profile == ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024) return fromEnvironment(environment);
        if (profile != ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2)
            throw new IllegalArgumentException("Explicit full-parity profile required");
        try {
            var inputs = CanonicalOracleEnvironment.require(environment);
            Path repository = Path.of(inputs.repositoryRoot()), producer = repository.resolve(NATIVE_RELATIVE);
            ControlBuild.FileRef source = actual(producer, 16L << 20);
            List<ResumedFixture> fixtures = new ArrayList<>();
            for (ResumedFixtureRole role : ResumedFixtureRole.values())
                fixtures.add(new ResumedFixture(role, actual(absolute(required(environment, role.environment)), role.maxBytes)));
            ControlBuild.FileRef corpusRef = actual(absolute(required(environment, "XAR_PERSON10_NATIVE_CORPUS_MANIFEST")), Person10NativeCorpus.MANIFEST_MAX_BYTES);
            var corpus = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(corpusRef.path())), Person10NativeCorpus.Manifest.class);
            Person10NativeCorpus.require(corpusRef, corpus.corpusRoot());
            if (!corpus.machineId().equals(WindowsJobProcess.currentMachineId()))
                throw new IOException("Actual corpus measurement belongs to a different execution machine");
            return new ResumedBindings(profile, inputs.python(), inputs.repositoryRoot(), source.path(), source.sha256(),
                    fixtures, new CorpusBinding(corpus.corpusRoot(), corpusRef));
        } catch (IOException error) {
            throw new IllegalArgumentException("NOT EXECUTED: R2 original producer or complete typed Native fixture inputs unavailable", error);
        }
    }
    public static SelectedBindings fromEnvironment(ControlBuild.SourceLimitProfile profile, Map<String, String> environment, Path compiledRoot) {
        return profile.currentParity()
                ? FullParityCurrentBindings.fromEnvironment(environment, compiledRoot) : fromEnvironment(profile, environment);
    }
    /** Historical R2 reader consults recorded argv only, including exact corpus manifest and root. */
    public static SelectedBindings fromRecordedArguments(ControlBuild.SourceLimitProfile profile, List<String> recordedArguments) {
        if (profile.currentParity()) return FullParityCurrentBindings.fromRecordedArguments(recordedArguments);
        if (profile == ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024) return fromRecordedArguments(recordedArguments);
        if (profile != ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2)
            throw new IllegalArgumentException("Explicit full-parity profile required");
        List<String> arguments = List.copyOf(recordedArguments); List<ResumedFixture> fixtures = new ArrayList<>();
        for (ResumedFixtureRole role : ResumedFixtureRole.values())
            fixtures.add(new ResumedFixture(role, new ControlBuild.FileRef(one(arguments, role.pathArgument()),
                    recordedBytes(arguments, role.bytesArgument()), one(arguments, role.shaArgument()))));
        var corpus = new CorpusBinding(one(arguments, "-Dxar.person10.nativeCorpus="),
                new ControlBuild.FileRef(one(arguments, "-Dxar.person10.nativeCorpus.manifest="),
                        recordedBytes(arguments, "-Dxar.fullParity.fixture.PERSON10_NATIVE_CORPUS_MANIFEST.bytes="),
                        one(arguments, "-Dxar.person10.nativeCorpus.manifest.sha256=")));
        var bindings = new ResumedBindings(profile, one(arguments, PYTHON), one(arguments, REPOSITORY),
                one(arguments, NATIVE_SOURCE), one(arguments, NATIVE_SHA256), fixtures, corpus);
        if (!absolute(one(arguments, ROOT_PYTHON)).equals(Path.of(bindings.python()))
                || !absolute(one(arguments, NATIVE_PYTHON)).equals(Path.of(bindings.python())))
            throw new IllegalArgumentException("One actual interpreter must bind all original R2 consumers");
        return bindings;
    }
    private static long recordedBytes(List<String> arguments, String property) {
        String value = one(arguments, property);
        if (!value.matches("[1-9][0-9]{0,8}")) throw new IllegalArgumentException("Canonical recorded fixture byte count required");
        return Long.parseLong(value);
    }
    private static ControlBuild.FileRef actual(Path path, long maxBytes) throws IOException {
        SharedSourceFiles.plainAncestors(path);
        if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || !path.toRealPath().equals(path)
                || Files.size(path) < 1 || Files.size(path) > maxBytes)
            throw new IOException("Actual plain bounded original input required: " + path);
        ControlBuild.FileRef ref = ControlBuild.FileRef.measure(path); ref.verify(); return ref;
    }
    private static String one(List<String> arguments, String property) {
        List<String> matches = new ArrayList<>();
        for (String argument : arguments) if (argument.startsWith(property)) matches.add(argument.substring(property.length()));
        if (matches.size() != 1 || matches.getFirst().isBlank())
            throw new IllegalArgumentException("Exactly one nonempty recorded argument required: " + property);
        return matches.getFirst();
    }
    private static String required(Map<String, String> environment, String name) {
        String value = environment.get(name);
        if (value == null || value.isBlank()) throw new IllegalArgumentException("NOT EXECUTED: explicit " + name + " required");
        return value;
    }
    private static Path absolute(String value) {
        if (value == null || value.isBlank() || value.length() > 4096
                || value.codePoints().anyMatch(point -> point < 32 || point == 127))
            throw new IllegalArgumentException("Bounded plain absolute original input path required");
        Path path = Path.of(value);
        if (!path.isAbsolute() || !path.equals(path.normalize())) throw new IllegalArgumentException("Canonical absolute original input path required");
        return path;
    }
}
