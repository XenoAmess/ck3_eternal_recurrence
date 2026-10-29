package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Explicit input fragment for the selected formal Git fixtures; it never runs Git or grants a lease. */
public final class FormalReleaseTestInputs {
    public static final String SCHEMA = "xar.formal-release-test-inputs/v1";
    public static final String PATH_ENV = "XAR_FORMAL_RELEASE_TEST_INPUTS";
    public static final String BYTES_ENV = PATH_ENV + "_BYTES";
    public static final String SHA_ENV = PATH_ENV + "_SHA256";
    private static final String ROOT = "-Dxar.formalReleaseTestRoot=";
    private static final String GIT = "-Dxar.formalReleaseGitExecutable=";
    private static final String PATH = "-Dxar.formalRelease.inputs.path=";
    private static final String BYTES = "-Dxar.formalRelease.inputs.bytes=";
    private static final String SHA = "-Dxar.formalRelease.inputs.sha256=";
    private static final List<String> ARGUMENTS = List.of(ROOT, GIT, PATH, BYTES, SHA);
    private static final String FIXTURE = "src/test/java/org/xar/ck3/control/service/root/FormalReleaseTestFixture.java";

    private FormalReleaseTestInputs() { }

    public record Inputs(String schema, String machineId, String repositoryRoot, String testRoot,
            FileRef gitExecutableRef, String observedAtUtc, String reviewAtUtc) {
        public Inputs {
            if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{0,127}"))
                throw new IllegalArgumentException("Versioned same-machine formal fixture inputs required");
            repositoryRoot = absolute(repositoryRoot).toString();
            testRoot = absolute(testRoot).toString();
            Objects.requireNonNull(gitExecutableRef);
            if (!absolute(gitExecutableRef.path()).getFileName().toString().equalsIgnoreCase("git.exe")
                    || gitExecutableRef.bytes() < 1
                    || !Instant.parse(observedAtUtc).isBefore(Instant.parse(reviewAtUtc)))
                throw new IllegalArgumentException("Pinned Git executable and finite fixture input window required");
        }
    }

    /** Pure recorded argument fragment. Constructing or decoding it does not qualify its original inputs. */
    public record Recorded(FileRef inputsRef, String testRoot, String gitExecutable) {
        public Recorded {
            Objects.requireNonNull(inputsRef);
            absolute(inputsRef.path());
            if (inputsRef.bytes() < 2 || inputsRef.bytes() > 65536)
                throw new IllegalArgumentException("Bounded formal fixture input ref required");
            testRoot = absolute(testRoot).toString();
            gitExecutable = absolute(gitExecutable).toString();
            if (!Path.of(gitExecutable).getFileName().toString().equalsIgnoreCase("git.exe"))
                throw new IllegalArgumentException("Exact recorded git.exe required");
        }

        public List<String> mavenArguments() {
            return List.of(ROOT + testRoot, GIT + gitExecutable, PATH + inputsRef.path(),
                    BYTES + inputsRef.bytes(), SHA + inputsRef.sha256());
        }
    }

    /** Only the actual selected fixture source makes this configuration mandatory. */
    public static boolean selected(Path sourceRoot) {
        Objects.requireNonNull(sourceRoot);
        return Files.isRegularFile(sourceRoot.resolve(FIXTURE), LinkOption.NOFOLLOW_LINKS)
                || Files.isRegularFile(sourceRoot.resolve("local-service").resolve(FIXTURE), LinkOption.NOFOLLOW_LINKS);
    }

    public static Recorded fromEnvironment(Map<String, String> environment, String machine, String repository)
            throws IOException {
        Objects.requireNonNull(environment);
        final FileRef reference;
        try {
            reference = new FileRef(absolute(required(environment, PATH_ENV)).toString(),
                    count(required(environment, BYTES_ENV)), required(environment, SHA_ENV));
        } catch (IllegalArgumentException invalid) {
            throw new IOException("Exact formal fixture configuration reference required", invalid);
        }
        Inputs inputs = read(reference);
        requireContext(inputs, machine, repository, true);
        return new Recorded(reference, inputs.testRoot(), inputs.gitExecutableRef().path());
    }

    /** Historical absence stays explicit. This decoder performs no environment, filesystem, or clock lookup. */
    public static Optional<Recorded> fromRecordedArguments(List<String> arguments) throws IOException {
        Objects.requireNonNull(arguments);
        boolean present = arguments.stream().anyMatch(value -> ARGUMENTS.stream().anyMatch(value::startsWith)
                || value.startsWith("-Dxar.formalRelease.inputs."));
        if (!present) return Optional.empty();
        for (String argument : arguments)
            if (argument.startsWith("-Dxar.formalRelease.inputs.") && ARGUMENTS.stream().noneMatch(argument::startsWith))
                throw new IOException("Unknown formal fixture recorded field");
        try {
            return Optional.of(new Recorded(new FileRef(one(arguments, PATH), count(one(arguments, BYTES)),
                    one(arguments, SHA)), one(arguments, ROOT), one(arguments, GIT)));
        } catch (IllegalArgumentException invalid) {
            throw new IOException("Strict formal fixture recorded arguments required", invalid);
        }
    }

    public static void requireExecutedInputs(Recorded recorded, String machine, String repository) throws IOException {
        Inputs inputs = exact(recorded);
        requireContext(inputs, machine, repository, true);
        Path root = Path.of(inputs.testRoot());
        SharedSourceFiles.plainAncestors(root);
        if (!Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS) || !root.toRealPath().equals(root))
            throw new IOException("Formal fixture data root must already be an ordinary canonical directory");
        requireExplicitStorage(root);
        requireGit(inputs);
        recorded.inputsRef().verify();
    }

    /** Completed command replay verifies original pinned inputs without reviving its expired output lease. */
    public static void requireRecordedInputs(Recorded recorded, String machine, String repository) throws IOException {
        Inputs inputs = exact(recorded);
        requireContext(inputs, machine, repository, false);
        requireGit(inputs);
        recorded.inputsRef().verify();
    }

    private static void requireGit(Inputs inputs) throws IOException {
        Path executable = Path.of(inputs.gitExecutableRef().path());
        SharedSourceFiles.plainAncestors(executable);
        if (!Files.isRegularFile(executable, LinkOption.NOFOLLOW_LINKS) || !executable.toRealPath().equals(executable))
            throw new IOException("Original ordinary canonical Git executable required");
        inputs.gitExecutableRef().verify();
    }

    /** Reuses the shared immutable-source witness in the original build's periodic/pre/post callback. */
    static CiBootstrap.IoGuard guarded(Recorded recorded, String machine, String repository,
            CiBootstrap.IoGuard active) throws IOException {
        Objects.requireNonNull(active); active.check(); requireExecutedInputs(recorded, machine, repository);
        List<FileRef> refs = inputRefs(recorded);
        List<SharedSourceFiles.Witness> before = new ArrayList<>();
        for (FileRef reference : refs) {
            reference.verify();
            var witness = SharedSourceFiles.observe(Path.of(reference.path()));
            if (reference.bytes() != witness.source().bytes()
                    || !reference.sha256().equals(witness.source().sha256()))
                throw new IOException("Formal original input differs during source observation");
            before.add(witness);
        }
        return () -> {
            active.check(); requireExecutedInputs(recorded, machine, repository);
            for (var witness : before)
                SharedSourceFiles.assertUnchanged(witness);
        };
    }

    private static void requireExplicitStorage(Path root) throws IOException {
        String flag = System.getProperty(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
        if (flag == null) flag = System.getenv(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
        if (flag == null) throw new IOException("Explicit project bulk-storage flag required for formal fixtures");
        var policy = ProjectStoragePolicy.configuration(System::getProperty, System::getenv);
        String systemRoot = System.getenv("SystemRoot");
        if (systemRoot == null || systemRoot.isBlank()) throw new IOException("Actual SystemRoot required");
        ProjectStoragePolicy.requireBulkOutput(policy, root, Path.of(systemRoot));
    }

    /** The sole build producer creates one dedicated child after acquiring its original TMP lease. */
    static void prepareRoot(Recorded recorded, Path temporary, CiBootstrap.IoGuard guard) throws IOException {
        Objects.requireNonNull(guard); guard.check();
        Path parent = temporary.toAbsolutePath().normalize(), root = Path.of(recorded.testRoot());
        if (!parent.equals(root.getParent()) || !Files.isDirectory(parent, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Formal fixture root must be one explicit child of the admitted private TMP");
        SharedSourceFiles.plainAncestors(parent);
        requireExplicitStorage(parent);
        if (Files.exists(root, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Fresh formal fixture data directory required; existing attempts are not adopted");
        Files.createDirectory(root);
        guard.check();
    }

    public static List<FileRef> inputRefs(Recorded recorded) throws IOException {
        Inputs inputs = exact(recorded);
        return List.of(recorded.inputsRef(), inputs.gitExecutableRef());
    }

    private static Inputs exact(Recorded recorded) throws IOException {
        Objects.requireNonNull(recorded);
        Inputs inputs = read(recorded.inputsRef());
        if (!inputs.testRoot().equals(recorded.testRoot())
                || !absolute(inputs.gitExecutableRef().path()).toString().equals(recorded.gitExecutable()))
            throw new IOException("Recorded formal fixture arguments differ from their exact configuration");
        return inputs;
    }

    private static Inputs read(FileRef reference) throws IOException {
        if (reference.bytes() < 2 || reference.bytes() > 65536) throw new IOException("Bounded fixture configuration required");
        Path path = absolute(reference.path()); SharedSourceFiles.plainAncestors(path);
        if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || !path.toRealPath().equals(path))
            throw new IOException("Original ordinary fixture configuration required");
        reference.verify(); byte[] raw;
        try (var input = Files.newInputStream(path)) { raw = input.readNBytes(Math.toIntExact(reference.bytes()) + 1); }
        BoundedSourceInputGuard.verifyReadBytes(reference, raw, 65536);
        Inputs result = ControlBuild.strictMapper().readValue(raw, Inputs.class);
        if (result == null) throw new IOException("Formal fixture configuration cannot be null");
        reference.verify(); return result;
    }

    private static void requireContext(Inputs inputs, String machine, String repository, boolean live) throws IOException {
        if (!inputs.machineId().equals(machine) || !Path.of(inputs.repositoryRoot()).equals(absolute(repository)))
            throw new IOException("Formal fixture machine or canonical repository differs");
        if (live) {
            Instant now = Instant.now();
            if (now.isBefore(Instant.parse(inputs.observedAtUtc())) || !now.isBefore(Instant.parse(inputs.reviewAtUtc())))
                throw new IOException("Formal fixture input window expired or not started");
        }
    }

    private static Path absolute(String value) {
        if (value == null || value.isBlank() || value.chars().anyMatch(Character::isISOControl))
            throw new IllegalArgumentException("Explicit ordinary absolute path required");
        Path path = Path.of(value);
        if (!path.isAbsolute() || !path.normalize().equals(path))
            throw new IllegalArgumentException("Normalized absolute path required");
        return path;
    }

    private static String required(Map<String, String> environment, String name) throws IOException {
        String value = environment.get(name);
        if (value == null || value.isBlank()) throw new IOException("Missing explicit " + name);
        return value;
    }

    private static long count(String value) throws IOException {
        if (!value.matches("0|[1-9][0-9]{0,18}")) throw new IOException("Canonical exact byte count required");
        try { return Long.parseLong(value); }
        catch (NumberFormatException invalid) { throw new IOException("Exact byte count overflow", invalid); }
    }

    private static String one(List<String> arguments, String prefix) throws IOException {
        List<String> values = new ArrayList<>();
        for (String argument : arguments) if (argument.startsWith(prefix)) values.add(argument.substring(prefix.length()));
        if (values.size() != 1 || values.getFirst().isBlank())
            throw new IOException("One exact formal fixture argument required: " + prefix);
        return values.getFirst();
    }
}
