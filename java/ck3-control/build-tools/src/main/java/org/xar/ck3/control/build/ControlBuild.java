package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.cfg.CoercionAction;
import com.fasterxml.jackson.databind.cfg.CoercionInputShape;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.type.LogicalType;
import java.io.IOException;
import java.io.InputStream;
import java.io.InterruptedIOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.FileVisitor;
import java.nio.file.AccessDeniedException;
import java.nio.file.DirectoryIteratorException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.HashSet;
import java.util.concurrent.atomic.AtomicLong;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.SAXException;

/** The single Maven producer: pinned same-volume inputs, bounded Job and complete output closure. */
public final class ControlBuild {
    public static final String SCHEMA = "xar.java-control.actual-build/v5";
    /** One finite JSON byte contract for normal, completed and capture build receipts. */
    public static final int BUILD_RECEIPT_MAX_BYTES = 2 << 20;
    public static final int RESUMED_BUILD_RECEIPT_MAX_BYTES = 4 << 20;
    public static final int BUILD_RECEIPT_ENVELOPE_MAX_BYTES = RESUMED_BUILD_RECEIPT_MAX_BYTES;
    private static final String LOCAL_MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final Set<String> EXCLUDED = Set.of("target", ".git", "__pycache__", ".mypy_cache", ".pytest_cache");
    private static final ObjectMapper JSON = createMapper();
    private ControlBuild() {}

    public record FileRef(String path, long bytes, String sha256) {
        public FileRef {
            if (path == null || !Path.of(path).isAbsolute() || bytes < 0 || sha256 == null
                    || !sha256.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("Invalid exact file reference");
        }
        public static FileRef measure(Path path) throws IOException {
            requireRegular(path);
            try {
                MessageDigest digest = MessageDigest.getInstance("SHA-256"); long count = 0;
                try (InputStream input = Files.newInputStream(path)) {
                    byte[] buffer = new byte[65536]; int length;
                    while ((length = input.read(buffer)) != -1) { digest.update(buffer, 0, length); count = Math.addExact(count, length); }
                }
                return new FileRef(path.toAbsolutePath().normalize().toString(), count, HexFormat.of().formatHex(digest.digest()));
            } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        }
        public void verify() throws IOException {
            FileRef actual = measure(Path.of(path));
            if (!Path.of(path).toAbsolutePath().normalize().equals(Path.of(actual.path()))
                    || bytes != actual.bytes() || !sha256.equals(actual.sha256())) {
                throw new IOException("File reference changed: " + path);
            }
        }
    }

    /** Explicit source-only envelopes; deployment, logs, JSON and Job caps are unchanged. */
    public enum SourceLimitProfile {
        STANDARD_8_MIB(1000, 8L << 20),
        EXISTING_MIGRATION_20261022(1536, 24L << 20),
        G2_RESEARCH_20261023(2304, 32L << 20),
        G2_STABILIZATION_20261023(2304, 32L << 20),
        G2_FULL_PARITY_20261024(3072, 40L << 20),
        G2_FULL_PARITY_20261024_R2(4096, 64L << 20),
        G2_FULL_PARITY_20261024_R3(4096, 64L << 20),
        G2_FULL_PARITY_20261024_R4(5120, 64L << 20),
        G2_FULL_PARITY_20261024_R5(6144, 96L << 20),
        G2_FULL_PARITY_20261024_R6(6144, 96L << 20),
        G2_FULL_PARITY_20261025_R7(6144, 96L << 20);

        private final int maxFiles;
        private final long maxBytes;
        SourceLimitProfile(int maxFiles, long maxBytes) { this.maxFiles = maxFiles; this.maxBytes = maxBytes; }
        public int maxFiles() { return maxFiles; }
        public long maxBytes() { return maxBytes; }
        public boolean completeG2() {
            return this == G2_RESEARCH_20261023 || this == G2_STABILIZATION_20261023
                    || fullParity();
        }
        public boolean fullParity() { return this == G2_FULL_PARITY_20261024 || resumedParity(); }
        public boolean resumedParity() { return this == G2_FULL_PARITY_20261024_R2 || currentParity(); }
        public boolean currentParity() { return this == G2_FULL_PARITY_20261024_R3 || this == G2_FULL_PARITY_20261024_R4 || this == G2_FULL_PARITY_20261024_R5 || this == G2_FULL_PARITY_20261024_R6 || this == G2_FULL_PARITY_20261025_R7; }
        public long moduleSourceBytes(String module, String directory) {
            if ((this == G2_FULL_PARITY_20261024_R5 || this == G2_FULL_PARITY_20261024_R6 || this == G2_FULL_PARITY_20261025_R7) && directory.equals("src")) {
                return switch (module) {
                    case "local-service" -> this == G2_FULL_PARITY_20261025_R7 ? 19L << 20 : 16L << 20;
                    case "application" -> this == G2_FULL_PARITY_20261024_R5 ? 12L << 20
                            : this == G2_FULL_PARITY_20261025_R7 ? 14L << 20 : 13L << 20;
                    case "native-transport" -> 12L << 20;
                    default -> 8L << 20;
                };
            }
            return this == G2_FULL_PARITY_20261024_R4 && directory.equals("src")
                    && (module.equals("application") || module.equals("local-service")) ? 12L << 20 : 8L << 20;
        }
        public int maxReactorProjects() { return fullParity() ? 35 : 32; }
    }
    private static final Set<String> EXISTING_MIGRATION_MODULES = Set.of(
            "contracts",
            "local-service",
            "native-diagnostics",
            "war-policy",
            "campaign-score",
            "finance-policy",
            "event-policy",
            "military-policy",
            "late-outcome-reconciliation",
            "governance-policy",
            "planning-runtime",
            "closed-failure-recovery",
            "admission-contracts",
            "replenishment-policy",
            "wave2-military",
            "build-tools",
            "wave2-runtime",
            "war-budget",
            "wave2-finance",
            "wave2-governance",
            "wave3-governance",
            "wave2-planning",
            "wave3-planning",
            "wave2-events",
            "wave2-development",
            "wave2-prisoners",
            "wave3-development",
            "wave3-runtime",
            "wave3-military");

    public enum SourceState { MATCH, MISMATCH, UNKNOWN }
    public enum TargetKind { SERVICE_FAST_JAR, BUILD_TOOLS_RUNTIME }
    public enum MavenSelection { DEFAULT_COMMAND, EXPLICIT_OVERRIDE }
    public record MavenToolchain(MavenSelection selection, String requestedCommand, String reportedHome,
            String reportedVersion, String minimumVersion, FileRef distributionLauncherRef, FileRef explicitOverrideRef) {
        public MavenToolchain {
            if (selection == null || requestedCommand == null || reportedHome == null || !Path.of(reportedHome).isAbsolute()
                    || !mavenVersionAtLeast(minimumVersion, "3.10.0") || !mavenVersionAtLeast(reportedVersion, minimumVersion) || distributionLauncherRef == null
                    || (selection == MavenSelection.DEFAULT_COMMAND && (!requestedCommand.equals("mvn") || explicitOverrideRef != null))
                    || (selection == MavenSelection.EXPLICIT_OVERRIDE && (explicitOverrideRef == null || !requestedCommand.equals(explicitOverrideRef.path())))) {
                throw new IllegalArgumentException("Invalid actual Maven toolchain evidence");
            }
        }
    }
    public record SourcePostcheck(SourceState state, String error) {
        public SourcePostcheck {
            if (state == null || (state == SourceState.UNKNOWN) != (error != null)
                    || (error != null && error.isBlank())) throw new IllegalArgumentException("Invalid source postcheck");
        }
    }

    public static final String CAPTURE_SCHEMA = "xar.java-control-test-compiled-capture/v1";
    public static final String TEST_COMPILATION_SCHEMA = "xar.java-control-test-compilation/v1";
    public enum CaptureQualification { TEST_COMPILED_CAPTURE_ONLY }
    public enum CaptureTestState { NOT_RUN }

    public record NotRunTestCompilation(FileRef sourceRef, List<FileRef> compiledClassRefs, CaptureTestState state) {
        public NotRunTestCompilation {
            Objects.requireNonNull(sourceRef); compiledClassRefs = List.copyOf(compiledClassRefs);
            if (state != CaptureTestState.NOT_RUN || compiledClassRefs.isEmpty()
                    || compiledClassRefs.size() > 256 || compiledClassRefs.stream().map(FileRef::path).distinct().count() != compiledClassRefs.size()) {
                throw new IllegalArgumentException("Actual compiled test class origins and explicit NOT_RUN required");
            }
        }
    }

    /** Every test source has producer-verified SourceFile/binary/package class origins; no test execution is claimed. */
    public record ModuleTestCompilation(FileRef modulePomRef, String classOutputRoot,
            FileRef compilerInputsRef, FileRef compilerCreatedFilesRef) {
        public ModuleTestCompilation {
            Objects.requireNonNull(modulePomRef); Objects.requireNonNull(compilerInputsRef);
            Objects.requireNonNull(compilerCreatedFilesRef);
            if (!Path.of(classOutputRoot).isAbsolute()) throw new IllegalArgumentException("Actual module test-class root required");
        }
    }
    public record TestCompilationManifest(String schema, String machineId, String observedAtUtc,
            CaptureTestState tests, List<ModuleTestCompilation> modules, List<NotRunTestCompilation> notRunTests) {
        public TestCompilationManifest {
            modules = List.copyOf(modules); notRunTests = List.copyOf(notRunTests); Instant.parse(observedAtUtc);
            if (!TEST_COMPILATION_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
                    || tests != CaptureTestState.NOT_RUN || modules.isEmpty() || modules.size() > 35
                    || modules.stream().map(item -> item.modulePomRef().path()).distinct().count() != modules.size()
                    || notRunTests.isEmpty() || notRunTests.size() > 4096
                    || notRunTests.stream().map(item -> item.sourceRef().path()).distinct().count() != notRunTests.size()
                    || notRunTests.stream().mapToLong(item -> item.compiledClassRefs().size()).sum() > 4096
                    || notRunTests.stream().flatMap(item -> item.compiledClassRefs().stream()).map(FileRef::path).distinct().count()
                        != notRunTests.stream().mapToLong(item -> item.compiledClassRefs().size()).sum()) {
                throw new IllegalArgumentException("Finite complete actual test compilation inventory required");
            }
        }
    }

    /** Success only: default Maven package compiled tests but did not execute them; never normal software/production PASS. */
    public record CaptureBuildReceipt(String schema, String machineId, String observedAtUtc, String attempt, String ownerTask,
            CaptureQualification qualification, CaptureTestState tests,
            String sourceRoot, String compiledSourceRoot, String deploymentRoot,
            SourcePostcheck sourcePostcheck, SourcePostcheck compiledSourcePostcheck,
            TargetKind targetKind, SourceLimitProfile sourceLimitProfile,
            List<FileRef> sourcePins, List<FileRef> compiledSourcePins, List<FileRef> completeDeployment,
            List<FileRef> producerRuntimePins, FileRef capacityReleaseRef,
            MavenToolchain mavenToolchain, FileRef javaExecutableRef,
            WindowsJobProcess.CommandResult toolchainProbe, WindowsJobProcess.CommandResult mavenResult,
            List<String> mavenArguments, FileRef mavenCommandRef, FileRef mavenStdoutRef,
            FileRef mavenStderrRef, FileRef versionStdoutRef, FileRef testCompilationRef,
            Map<String, Long> finalLogicalBytesByPart, @com.fasterxml.jackson.annotation.JsonInclude(com.fasterxml.jackson.annotation.JsonInclude.Include.NON_NULL) FileRef workpackageAccountingRef) {
        public CaptureBuildReceipt(String schema, String machineId, String observedAtUtc, String attempt, String ownerTask,
            CaptureQualification qualification, CaptureTestState tests,
            String sourceRoot, String compiledSourceRoot, String deploymentRoot,
            SourcePostcheck sourcePostcheck, SourcePostcheck compiledSourcePostcheck,
            TargetKind targetKind, SourceLimitProfile sourceLimitProfile,
            List<FileRef> sourcePins, List<FileRef> compiledSourcePins, List<FileRef> completeDeployment,
            List<FileRef> producerRuntimePins, FileRef capacityReleaseRef,
            MavenToolchain mavenToolchain, FileRef javaExecutableRef,
            WindowsJobProcess.CommandResult toolchainProbe, WindowsJobProcess.CommandResult mavenResult,
            List<String> mavenArguments, FileRef mavenCommandRef, FileRef mavenStdoutRef,
            FileRef mavenStderrRef, FileRef versionStdoutRef, FileRef testCompilationRef,
            Map<String, Long> finalLogicalBytesByPart) {
            this(schema, machineId, observedAtUtc, attempt, ownerTask, qualification, tests, sourceRoot, compiledSourceRoot, deploymentRoot, sourcePostcheck, compiledSourcePostcheck, targetKind, sourceLimitProfile, sourcePins, compiledSourcePins, completeDeployment, producerRuntimePins, capacityReleaseRef, mavenToolchain, javaExecutableRef, toolchainProbe, mavenResult, mavenArguments, mavenCommandRef, mavenStdoutRef, mavenStderrRef, versionStdoutRef, testCompilationRef, finalLogicalBytesByPart, null);
        }
        public CaptureBuildReceipt {
            sourcePins = List.copyOf(sourcePins); compiledSourcePins = List.copyOf(compiledSourcePins);
            completeDeployment = List.copyOf(completeDeployment); producerRuntimePins = List.copyOf(producerRuntimePins);
            mavenArguments = List.copyOf(mavenArguments); finalLogicalBytesByPart = Map.copyOf(finalLogicalBytesByPart);
            Instant.parse(observedAtUtc);
            if ((!CAPTURE_SCHEMA.equals(schema) && !SCOPED_CAPTURE_SCHEMA.equals(schema)) || machineId == null || machineId.isBlank()
                    || attempt == null || !attempt.matches("[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}") || ownerTask == null || ownerTask.isBlank()
                    || qualification != CaptureQualification.TEST_COMPILED_CAPTURE_ONLY || tests != CaptureTestState.NOT_RUN
                    || targetKind != TargetKind.SERVICE_FAST_JAR || sourceLimitProfile == null
                    || sourcePostcheck == null || sourcePostcheck.state() != SourceState.MATCH
                    || compiledSourcePostcheck == null || compiledSourcePostcheck.state() != SourceState.MATCH
                    || sourcePins.isEmpty() || compiledSourcePins.isEmpty() || completeDeployment.isEmpty() || producerRuntimePins.isEmpty()
                    || toolchainProbe == null || !toolchainProbe.passed() || mavenResult == null || !mavenResult.passed()
                    || mavenToolchain == null || mavenToolchain.selection() != MavenSelection.DEFAULT_COMMAND
                    || !mavenArguments.contains("package") || !mavenArguments.contains("-DskipTests=true")
                    || mavenArguments.contains("verify") || !mavenArguments.contains("-Dmaven.test.skip=false")
                    || mavenArguments.stream().anyMatch(arg -> arg.startsWith("-Dmaven.test.skip") && !arg.equals("-Dmaven.test.skip=false"))) {
                throw new IllegalArgumentException("Actual test-compiled capture-only default-Maven terminal required");
            }
            for (String root : List.of(sourceRoot, compiledSourceRoot, deploymentRoot)) {
                if (!Path.of(root).isAbsolute()) throw new IllegalArgumentException("Absolute actual artifact roots required");
            }
            Objects.requireNonNull(capacityReleaseRef); Objects.requireNonNull(javaExecutableRef);
            Objects.requireNonNull(mavenCommandRef); Objects.requireNonNull(testCompilationRef);
            Objects.requireNonNull(mavenStdoutRef); Objects.requireNonNull(mavenStderrRef); Objects.requireNonNull(versionStdoutRef);
            if ((CAPTURE_SCHEMA.equals(schema) && workpackageAccountingRef != null) || (SCOPED_CAPTURE_SCHEMA.equals(schema) && (workpackageAccountingRef == null || !finalLogicalBytesByPart.isEmpty()))) throw new IllegalArgumentException("Versioned standalone capture accounting provenance required");
            if (testCompilationRef.bytes() < 1 || testCompilationRef.bytes() > (4L << 20)) {
                throw new IllegalArgumentException("Bounded external typed test compilation manifest required");
            }
        }
    }

    public record BuildReceipt(String schema, String machineId, String observedAtUtc, String status,
            String sourceRoot, String compiledSourceRoot, String deploymentRoot, SourcePostcheck sourcePostcheck,
            SourcePostcheck compiledSourcePostcheck, TargetKind targetKind, SourceLimitProfile sourceLimitProfile,
            List<FileRef> sourcePins, List<FileRef> compiledSourcePins, List<FileRef> completeDeployment,
            List<FileRef> producerRuntimePins,
            FileRef capacityReleaseRef, MavenToolchain mavenToolchain, FileRef javaExecutableRef,
            WindowsJobProcess.CommandResult toolchainProbe, WindowsJobProcess.CommandResult mavenResult,
            Map<String, Long> finalLogicalBytesByPart, String error, @com.fasterxml.jackson.annotation.JsonInclude(com.fasterxml.jackson.annotation.JsonInclude.Include.NON_NULL) FileRef workpackageAccountingRef) {
        public BuildReceipt(String schema, String machineId, String observedAtUtc, String status,
            String sourceRoot, String compiledSourceRoot, String deploymentRoot, SourcePostcheck sourcePostcheck,
            SourcePostcheck compiledSourcePostcheck, TargetKind targetKind, SourceLimitProfile sourceLimitProfile,
            List<FileRef> sourcePins, List<FileRef> compiledSourcePins, List<FileRef> completeDeployment,
            List<FileRef> producerRuntimePins,
            FileRef capacityReleaseRef, MavenToolchain mavenToolchain, FileRef javaExecutableRef,
            WindowsJobProcess.CommandResult toolchainProbe, WindowsJobProcess.CommandResult mavenResult,
            Map<String, Long> finalLogicalBytesByPart, String error) {
            this(schema, machineId, observedAtUtc, status, sourceRoot, compiledSourceRoot, deploymentRoot, sourcePostcheck, compiledSourcePostcheck, targetKind, sourceLimitProfile, sourcePins, compiledSourcePins, completeDeployment, producerRuntimePins, capacityReleaseRef, mavenToolchain, javaExecutableRef, toolchainProbe, mavenResult, finalLogicalBytesByPart, error, null);
        }
        public BuildReceipt {
            sourcePins = List.copyOf(sourcePins); compiledSourcePins = List.copyOf(compiledSourcePins);
            completeDeployment = List.copyOf(completeDeployment); finalLogicalBytesByPart = Map.copyOf(finalLogicalBytesByPart);
            producerRuntimePins = List.copyOf(producerRuntimePins);
            if ((!SCHEMA.equals(schema) && !SCOPED_BUILD_SCHEMA.equals(schema)) || !Set.of("PASS", "RED").contains(status) || sourcePostcheck == null || compiledSourcePostcheck == null || targetKind == null || sourceLimitProfile == null) throw new IllegalArgumentException("Unknown build receipt contract");
            if ((SCHEMA.equals(schema) && workpackageAccountingRef != null) || (SCOPED_BUILD_SCHEMA.equals(schema)
                    && (!finalLogicalBytesByPart.isEmpty() || (workpackageAccountingRef == null && (status.equals("PASS") || error == null || error.isBlank()))))) throw new IllegalArgumentException("Versioned standalone accounting provenance required");
            Instant.parse(observedAtUtc);
        }
    }

    public record Config(Path sourceRoot, Path workRoot, Path capacityRelease, String attempt,
            String ownerTask, Path mavenCommand, Path javaHome, String minimumMavenVersion, int timeoutSeconds, TargetKind targetKind, SourceLimitProfile sourceLimitProfile) {
        public Config {
            for (Path path : List.of(sourceRoot, workRoot, capacityRelease, javaHome)) {
                if (!path.isAbsolute()) throw new IllegalArgumentException("Absolute paths required");
            }
            if (mavenCommand != null && !mavenCommand.isAbsolute()) throw new IllegalArgumentException("Explicit Maven override must be absolute");
            if (!attempt.matches("[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}") || ownerTask.isBlank()
                    || !mavenVersionAtLeast(minimumMavenVersion, "3.10.0")
                    || timeoutSeconds <= 0 || timeoutSeconds > maximumBuildTimeoutSeconds(targetKind) || targetKind == null || sourceLimitProfile == null) throw new IllegalArgumentException("Invalid finite build parameters");
            if (sourceLimitProfile.currentParity() && targetKind != TargetKind.SERVICE_FAST_JAR) {
                throw new IllegalArgumentException("R3 full parity is the complete service reactor; standalone tools keep their independent standard profile");
            }
        }
    }

    /** Pinned lobby DATA for the existing native consumer; never Native ABI, runtime or execution authority. */
    public static final class LobbyVerifyTestInputs {
        public static final String SCHEMA = "xar.java-control-lobby-verify-inputs/v1";
        public static final String ENV = "XAR_LOBBY_VERIFY_INPUTS";
        public static final String PATH_PROPERTY = "xar.g2.frontend.lobby.inputs.path";
        private static final String BYTES_PROPERTY = "xar.g2.frontend.lobby.inputs.bytes";
        private static final String SHA_PROPERTY = "xar.g2.frontend.lobby.inputs.sha256";
        private static final String PREFIX = "-Dxar.g2.frontend.lobby.inputs.";
        private static final int MAXIMUM_BYTES = 65536;
        private static final String FIXTURE = "src/test/java/org/xar/ck3/control/build/FrontendLobbyCallbackObservationTest.java";
        private LobbyVerifyTestInputs() { }

        public record Inputs(String schema, String machineId, String reviewAtUtc,
                SdkFixtureProductionInputs.LobbyWireSet lobbyWires) {
            public Inputs {
                if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}")
                        || machineId.equals("unknown")) throw new IllegalArgumentException("Exact lobby DATA schema and machine required");
                Instant.parse(reviewAtUtc); Objects.requireNonNull(lobbyWires);
            }
        }

        /** Exact recorded projection; construction and decoding perform no I/O or clock lookup. */
        public record Recorded(FileRef inputsRef, String directory) {
            public Recorded {
                Objects.requireNonNull(inputsRef); absolute(inputsRef.path()); absolute(directory);
                if (inputsRef.bytes() < 2 || inputsRef.bytes() > MAXIMUM_BYTES)
                    throw new IllegalArgumentException("Bounded lobby metadata required");
            }
            public List<String> mavenArguments() {
                return List.of(property(SdkFixtureProductionInputs.LOBBY_DIRECTORY, directory),
                        property(PATH_PROPERTY, inputsRef.path()), property(BYTES_PROPERTY, Long.toString(inputsRef.bytes())),
                        property(SHA_PROPERTY, inputsRef.sha256()));
            }
        }

        public static boolean selected(Path source) {
            return Files.isRegularFile(source.resolve(FIXTURE), LinkOption.NOFOLLOW_LINKS);
        }
        public static Recorded fromEnvironment(Map<String,String> environment, String machine) throws IOException {
            try {
                FileRef ref = new FileRef(required(environment, ENV), count(required(environment, ENV + "_BYTES")),
                        required(environment, ENV + "_SHA256"));
                Inputs inputs = read(ref);
                Recorded result = new Recorded(ref, inputs.lobbyWires().directory());
                requireInputs(result, machine, Instant.now()); return result;
            } catch (IllegalArgumentException invalid) { throw new IOException("Exact pinned lobby metadata triple required", invalid); }
        }
        public static java.util.Optional<Recorded> fromRecordedArguments(List<String> arguments) throws IOException {
            if (arguments.stream().noneMatch(value -> value.startsWith(PREFIX))) return java.util.Optional.empty();
            try {
                for (String value : arguments) if (value.startsWith(PREFIX)
                        && !value.startsWith(property(PATH_PROPERTY, "")) && !value.startsWith(property(BYTES_PROPERTY, ""))
                        && !value.startsWith(property(SHA_PROPERTY, ""))) throw new IllegalArgumentException("Unknown recorded lobby field");
                return java.util.Optional.of(new Recorded(new FileRef(one(arguments, PATH_PROPERTY), count(one(arguments, BYTES_PROPERTY)),
                        one(arguments, SHA_PROPERTY)), one(arguments, SdkFixtureProductionInputs.LOBBY_DIRECTORY)));
            } catch (IllegalArgumentException invalid) { throw new IOException("Complete unique recorded lobby fragment required", invalid); }
        }
        public static Inputs read(FileRef ref) throws IOException {
            if (ref.bytes() < 2 || ref.bytes() > MAXIMUM_BYTES) throw new IOException("Bounded lobby metadata required");
            Path path = absolute(ref.path()); SharedSourceFiles.plainAncestors(path);
            ref.verify(); byte[] raw;
            try (var input = Files.newInputStream(path)) { raw = input.readNBytes(MAXIMUM_BYTES + 1); }
            BoundedSourceInputGuard.verifyReadBytes(ref, raw, MAXIMUM_BYTES);
            Inputs result = ControlBuild.strictMapper().readValue(raw, Inputs.class);
            if (result == null) throw new IOException("Lobby metadata cannot be null");
            ref.verify(); return result;
        }
        public static List<FileRef> inputRefs(Recorded recorded) throws IOException {
            Inputs inputs = exact(recorded); var refs = new ArrayList<FileRef>();
            refs.add(recorded.inputsRef()); refs.addAll(inputs.lobbyWires().originals()); return List.copyOf(refs);
        }
        /** A completed reader supplies its original completion instant, never revives the old review. */
        public static void requireInputs(Recorded recorded, String machine, Instant at) throws IOException {
            Inputs inputs = exact(recorded);
            if (!inputs.machineId().equals(machine) || !at.isBefore(Instant.parse(inputs.reviewAtUtc())))
                throw new IOException("Same machine and original finite lobby DATA review required");
            Path directory = absolute(recorded.directory()); SharedSourceFiles.plainAncestors(directory);
            if (!Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS) || !directory.toRealPath().equals(directory))
                throw new IOException("Plain canonical lobby input directory required");
            for (FileRef ref : inputRefs(recorded)) { SharedSourceFiles.plainAncestors(absolute(ref.path())); ref.verify(); }
        }
        static CiBootstrap.IoGuard guarded(Recorded recorded, String machine, CiBootstrap.IoGuard active) throws IOException {
            active.check(); requireInputs(recorded, machine, Instant.now());
            var before = new ArrayList<SharedSourceFiles.Witness>();
            for (FileRef ref : inputRefs(recorded)) {
                var witness = SharedSourceFiles.observe(absolute(ref.path()));
                if (witness.source().bytes() != ref.bytes() || !witness.source().sha256().equals(ref.sha256()))
                    throw new IOException("Lobby source differs during observation");
                before.add(witness);
            }
            return () -> {
                active.check(); requireInputs(recorded, machine, Instant.now());
                for (var witness : before) SharedSourceFiles.assertUnchanged(witness);
            };
        }
        /** The real original consumer uses this reader; the existing complete v2 bundle remains an explicit lane. */
        public static byte[] original(String name) throws IOException {
            if (!SdkFixtureProductionInputs.LOBBY_NAMES.contains(name)) throw new IOException("One exact lobby basename required");
            List<String> properties = System.getProperties().stringPropertyNames().stream()
                    .map(key -> property(key, System.getProperty(key))).toList();
            java.util.Optional<Recorded> selected = fromRecordedArguments(properties);
            if (selected.isPresent()) {
                return original(selected.orElseThrow(), name);
            }
            // A directory alone is never accepted. This is the pre-existing complete four-package projection.
            final SdkFixtureProductionInputs.CommandArguments bundle;
            try { bundle = SdkFixtureProductionInputs.fromRecordedArguments(properties); }
            catch (IllegalArgumentException invalid) { throw new IOException("Pinned lobby metadata or complete original v2 bundle required", invalid); }
            if (bundle.generation() != SdkFixtureProductionInputs.Generation.V2_FOUR
                    || !bundle.machineId().equals(WindowsJobProcess.currentMachineId()))
                throw new IOException("Current-machine original v2 software fixture bundle required");
            Path path = absolute(bundle.lobbyWireDirectory()).resolve(name); SharedSourceFiles.plainAncestors(path);
            if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.size(path) < 1 || Files.size(path) > 1L << 20)
                throw new IOException("Actual bounded original lobby wire required");
            byte[] raw;
            try (var input = Files.newInputStream(path)) { raw = input.readNBytes((1 << 20) + 1); }
            if (raw.length < 1 || raw.length > 1 << 20) throw new IOException("Original lobby wire exceeds its explicit bound");
            return raw;
        }

        /** Reads a specific frame from an explicitly provided Recorded projection, preserving all strict verification. */
        public static byte[] original(Recorded recorded, String name) throws IOException {
            if (!SdkFixtureProductionInputs.LOBBY_NAMES.contains(name)) throw new IOException("One exact lobby basename required");
            requireInputs(recorded, WindowsJobProcess.currentMachineId(), Instant.now());
            FileRef ref = exact(recorded).lobbyWires().originals().stream()
                    .filter(value -> Path.of(value.path()).getFileName().toString().equals(name)).findFirst().orElseThrow();
            byte[] raw;
            try (var input = Files.newInputStream(absolute(ref.path()))) { raw = input.readNBytes((1 << 20) + 1); }
            BoundedSourceInputGuard.verifyReadBytes(ref, raw, 1 << 20);
            requireInputs(recorded, WindowsJobProcess.currentMachineId(), Instant.now());
            return raw;
        }
        private static Inputs exact(Recorded recorded) throws IOException {
            Inputs inputs = read(recorded.inputsRef());
            if (!absolute(inputs.lobbyWires().directory()).equals(absolute(recorded.directory())))
                throw new IOException("Recorded lobby directory differs from its pinned metadata");
            return inputs;
        }
        private static Path absolute(String value) {
            if (value == null || value.isBlank() || value.length() > 4096 || value.chars().anyMatch(c -> c < 32 || c == 127))
                throw new IllegalArgumentException("Bounded plain lobby path required");
            Path path = Path.of(value);
            if (!path.isAbsolute() || !path.equals(path.normalize())) throw new IllegalArgumentException("Normalized absolute lobby path required");
            return path;
        }
        private static long count(String value) {
            if (!value.matches("[1-9][0-9]{0,5}")) throw new IllegalArgumentException("Canonical lobby metadata byte count required");
            return Long.parseLong(value);
        }
        private static String required(Map<String,String> values, String key) throws IOException {
            String value = values.get(key);
            if (value == null || value.isBlank()) throw new IOException("Explicit " + key + " required");
            return value;
        }
        private static String one(List<String> arguments, String name) {
            String prefix = property(name, "");
            var values = arguments.stream().filter(value -> value.startsWith(prefix)).map(value -> value.substring(prefix.length())).toList();
            if (values.size() != 1 || values.getFirst().isBlank()) throw new IllegalArgumentException("One exact lobby field required");
            return values.getFirst();
        }
        private static String property(String name, String value) { return "-D" + name + "=" + value; }
    }

    /** Shared finite ceiling for complete verification; callers must still fit the original live lease. */
    public static int maximumBuildTimeoutSeconds(TargetKind targetKind) {
        if (targetKind == null) throw new IllegalArgumentException("Explicit build target kind required");
        return switch (targetKind) {
            case BUILD_TOOLS_RUNTIME, SERVICE_FAST_JAR -> 3600;
        };
    }

    public static final String ATTEMPT_RELEASE_SCHEMA = "xar.java-phase1.manual-capacity-release/v2";
    public static final String ACCOUNTING_SCHEMA = "xar.java-control.workpackage-accounting/v1";
    public static final String COMPLETED_ACCOUNTING_SCHEMA = "xar.java-control.workpackage-accounting/v2";
    public static final String ATTEMPT_AUTHORITY_SCHEMA = "xar.java-control.attempt-accounting-authority/v1";
    public static final String SCOPED_BUILD_SCHEMA = "xar.java-control.actual-build/v6";
    public static final String SCOPED_CAPTURE_SCHEMA = "xar.java-control-test-compiled-capture/v2";
    public static final String ACCOUNTING_FILE = "xar-workpackage-accounting.json";
    public enum AccountingMode { FULL_PART_INVENTORY, CONSERVATIVE_VOLUME_ATTEMPT }
    public enum RepositoryAccountingState { FULL_PART_MEASURED, CONSERVATIVE_VOLUME_COVERAGE }
    public enum FinancialLayout { CAPACITY_SUPPLEMENT18 }
    private static final Set<String> ATTEMPT_SCOPES = Set.of("source_snapshot", "build", "private_tmp", "artifacts", "logs");
    private static final Set<String> ATTEMPT_ROOTS = Set.of("maven_repository", "source_snapshot", "build", "private_tmp", "artifacts", "logs");
    public record VolumeObservation(String volumeRoot, long totalBytes, long usableBytes, long usedUpperBytes,
            long quotaUsedUpperBytes, long requiredFreeBytes, long effectiveProjectQuota, long allHoldsBytes,
            long systemGrowthReserve, long safetyReserve) {
        public VolumeObservation {
            if (!Path.of(volumeRoot).isAbsolute() || totalBytes <= 0 || usableBytes < 0 || usableBytes > totalBytes
                    || usedUpperBytes != totalBytes - usableBytes || quotaUsedUpperBytes < usedUpperBytes || quotaUsedUpperBytes > totalBytes || requiredFreeBytes <= 0 || effectiveProjectQuota <= 0
                    || allHoldsBytes <= 0 || systemGrowthReserve <= 0 || safetyReserve <= 0
                    || requiredFreeBytes != Math.addExact(allHoldsBytes, Math.addExact(systemGrowthReserve, safetyReserve)))
                throw new IllegalArgumentException("Exact actual volume observation and complete holds/reserves required");
        }
    }
    public record WorkpackageAccounting(String schema, AccountingMode mode, FileRef capacityReleaseRef,
            String machineId, String observedAtUtc, Map<String, String> measuredRoots,
            Map<String, Long> logicalBytesByScope, RepositoryAccountingState repositoryAccountingState,
            Long mavenRepositoryBaselineBytes, Long mavenRepositoryCurrentBytes, long peakNewLogicalBytes,
            Map<String, Long> nativeAllocatedBytesByScope, long peakNewNativeAllocatedBytes,
            List<VolumeObservation> volumes) {
        public WorkpackageAccounting {
            if (!ACCOUNTING_SCHEMA.equals(schema) || mode == null || capacityReleaseRef == null || machineId == null || machineId.isBlank()
                    || repositoryAccountingState == null) throw new IllegalArgumentException("Explicit accounting mode and original capacity source required");
            Instant.parse(observedAtUtc); measuredRoots = Map.copyOf(measuredRoots);
            logicalBytesByScope = Map.copyOf(logicalBytesByScope); nativeAllocatedBytesByScope = Map.copyOf(nativeAllocatedBytesByScope);
            volumes = List.copyOf(volumes);
            if (logicalBytesByScope.isEmpty() || measuredRoots.values().stream().anyMatch(value -> !Path.of(value).isAbsolute())
                    || logicalBytesByScope.values().stream().anyMatch(value -> value < 0)
                    || nativeAllocatedBytesByScope.values().stream().anyMatch(value -> value < 0)
                    || peakNewLogicalBytes < 0 || peakNewNativeAllocatedBytes < 0)
                throw new IllegalArgumentException("Actual bounded scope measurements required");
            if (mode == AccountingMode.CONSERVATIVE_VOLUME_ATTEMPT && (!measuredRoots.keySet().equals(ATTEMPT_ROOTS)
                    || !logicalBytesByScope.keySet().equals(ATTEMPT_SCOPES) || !nativeAllocatedBytesByScope.keySet().equals(ATTEMPT_SCOPES)
                    || repositoryAccountingState != RepositoryAccountingState.CONSERVATIVE_VOLUME_COVERAGE
                    || mavenRepositoryBaselineBytes != null || mavenRepositoryCurrentBytes != null || volumes.isEmpty()))
                throw new IllegalArgumentException("Shared repository is UNKNOWN and covered by complete volume upper bounds, never zero");
            if (mode == AccountingMode.FULL_PART_INVENTORY && (!logicalBytesByScope.keySet().equals(Set.of("m2", "build", "tools", "scratch", "artifacts", "logs"))
                    || !measuredRoots.keySet().equals(logicalBytesByScope.keySet()) || peakNewLogicalBytes != 0
                    || repositoryAccountingState != RepositoryAccountingState.FULL_PART_MEASURED
                    || mavenRepositoryBaselineBytes == null || mavenRepositoryCurrentBytes == null
                    || !mavenRepositoryBaselineBytes.equals(logicalBytesByScope.get("m2")) || !mavenRepositoryCurrentBytes.equals(logicalBytesByScope.get("m2"))
                    || !nativeAllocatedBytesByScope.isEmpty() || peakNewNativeAllocatedBytes != 0))
                throw new IllegalArgumentException("Historical full-part actual logical inventory is distinct from native allocation");
        }
    }
    /** Exact original bytes retained by the live producer; this never grants a current lease. */
    public record RetainedAccountingSource(FileRef originalRef, String bodyBase64) {
        public RetainedAccountingSource {
            Objects.requireNonNull(originalRef); Objects.requireNonNull(bodyBase64);
            if (originalRef.bytes() < 1 || originalRef.bytes() > (128 << 10) || bodyBase64.length() > 174764)
                throw new IllegalArgumentException("Bounded original accounting source required");
            byte[] body;
            try { body = java.util.Base64.getDecoder().decode(bodyBase64); }
            catch (IllegalArgumentException invalid) { throw new IllegalArgumentException("Canonical accounting source base64 required", invalid); }
            if (!java.util.Base64.getEncoder().encodeToString(body).equals(bodyBase64)
                    || body.length != originalRef.bytes() || !accountingDigest(body).equals(originalRef.sha256()))
                throw new IllegalArgumentException("Retained accounting source differs from its original path/length/SHA pin");
        }
        byte[] exactBytes(int maximum) throws IOException {
            if (originalRef.bytes() > maximum) throw new IOException("Bounded retained accounting source required");
            return java.util.Base64.getDecoder().decode(bodyBase64);
        }
    }

    /** Version 2 adds exact source bodies to the unchanged version 1 measurement contract. */
    public record CompletedWorkpackageAccounting(String schema, WorkpackageAccounting accounting,
            List<RetainedAccountingSource> reservationSources) {
        public CompletedWorkpackageAccounting {
            if (!COMPLETED_ACCOUNTING_SCHEMA.equals(schema) || accounting == null
                    || accounting.mode() != AccountingMode.CONSERVATIVE_VOLUME_ATTEMPT)
                throw new IllegalArgumentException("Versioned completed attempt accounting required");
            reservationSources = List.copyOf(reservationSources);
            if (reservationSources.isEmpty() || reservationSources.size() > 16
                    || reservationSources.stream().map(source -> source.originalRef().path()).distinct().count() != reservationSources.size())
                throw new IllegalArgumentException("One bounded retained body per original reservation source required");
        }
    }

    private static String accountingDigest(byte[] body) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }

    private record AccountingSources(List<RetainedAccountingSource> retained) {
        private AccountingSources { retained = List.copyOf(retained); }
        static AccountingSources live() { return new AccountingSources(List.of()); }
        byte[] read(FileRef original, int maximum) throws IOException {
            for (RetainedAccountingSource source : retained) {
                if (Path.of(source.originalRef().path()).equals(Path.of(original.path()))) {
                    if (!source.originalRef().equals(original)) throw new IOException("Retained original accounting identity substitution rejected");
                    return source.exactBytes(maximum);
                }
            }
            return exactAccountingBytes(original, maximum);
        }
        void verify(FileRef original) throws IOException { read(original, 128 << 10); }
    }

    private record AccountingEvidence(WorkpackageAccounting accounting, AccountingSources sources) { }

    private static AccountingEvidence completedAccountingEvidence(FileRef accountingRef) throws IOException {
        JsonNode node = object(JSON.readTree(exactAccountingBytes(accountingRef, 128 << 10)));
        String schema = text(node, "schema");
        if (ACCOUNTING_SCHEMA.equals(schema))
            return new AccountingEvidence(JSON.treeToValue(node, WorkpackageAccounting.class), AccountingSources.live());
        if (!COMPLETED_ACCOUNTING_SCHEMA.equals(schema)) throw new IOException("Unknown completed accounting schema");
        CompletedWorkpackageAccounting completed = JSON.treeToValue(node, CompletedWorkpackageAccounting.class);
        return new AccountingEvidence(completed.accounting(), new AccountingSources(completed.reservationSources()));
    }

    static WorkpackageAccounting readCompletedAccounting(FileRef accountingRef) throws IOException {
        return completedAccountingEvidence(accountingRef).accounting();
    }

    private static AccountingSources completedAccountingSources(FileRef accountingRef, FileRef releaseRef,
            AttemptCapacityRelease release) throws IOException {
        if (accountingRef == null) return AccountingSources.live();
        AccountingEvidence evidence = completedAccountingEvidence(accountingRef);
        if (!evidence.accounting().capacityReleaseRef().equals(releaseRef))
            throw new IOException("Completed retained sources belong to another original release");
        if (!evidence.sources().retained().isEmpty()
                && !evidence.sources().retained().stream().map(RetainedAccountingSource::originalRef).toList()
                        .equals(release.workpackageAccounting().reservationSourceRefs()))
            throw new IOException("Complete original reservation source identities and order required");
        return evidence.sources();
    }

    public record AttemptAccountingAuthority(String schema, String attempt, FinancialLayout financialLayout,
            FileRef financialSourceRef, List<FileRef> reservationSourceRefs,
            Map<String, String> measuredRoots, Map<String, Long> logicalCapsByScope, long maximumNewLogicalBytes,
            Map<String, Long> nativeCapsByScope, long maximumNewNativeBytes, long canonicalM2GrowthReservationBytes) {
        public AttemptAccountingAuthority {
            if (!ATTEMPT_AUTHORITY_SCHEMA.equals(schema) || attempt == null || !attempt.matches("[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}")
                    || financialLayout != FinancialLayout.CAPACITY_SUPPLEMENT18 || financialSourceRef == null
                    || maximumNewLogicalBytes <= 0 || maximumNewNativeBytes <= 0 || canonicalM2GrowthReservationBytes <= 0)
                throw new IllegalArgumentException("Explicit bounded attempt accounting authority required");
            reservationSourceRefs = List.copyOf(reservationSourceRefs); measuredRoots = Map.copyOf(measuredRoots);
            logicalCapsByScope = Map.copyOf(logicalCapsByScope); nativeCapsByScope = Map.copyOf(nativeCapsByScope);
            if (reservationSourceRefs.isEmpty() || reservationSourceRefs.size() > 16 || reservationSourceRefs.stream().map(FileRef::path).distinct().count() != reservationSourceRefs.size()
                    || !measuredRoots.keySet().equals(ATTEMPT_ROOTS)
                    || !logicalCapsByScope.keySet().equals(ATTEMPT_SCOPES) || !nativeCapsByScope.keySet().equals(ATTEMPT_SCOPES)
                    || logicalCapsByScope.values().stream().anyMatch(value -> value <= 0) || nativeCapsByScope.values().stream().anyMatch(value -> value <= 0)
                    || measuredRoots.values().stream().anyMatch(value -> !Path.of(value).isAbsolute()))
                throw new IllegalArgumentException("All exact roots, separate logical/native caps and retained reservation sources required");
        }
    }
    /** Versioned issuer document. Legacy parts remain runtime budgets, never alleged whole-project measurements. */
    public record AttemptCapacityRelease(String schema, String machineId, String observedAtUtc, String reviewAtUtc,
            String status, @com.fasterxml.jackson.annotation.JsonProperty("single_Maven_writer") String ownerTask,
            FileRef policyRef, List<String> approvedOutputRoots,
            @com.fasterxml.jackson.annotation.JsonProperty("Maven_repository") String mavenRepository,
            String buildRoot, String temporaryRoot, Map<String, Long> parts,
            Map<String, CiBootstrap.VolumeBudget> volumes, Map<String, CiBootstrap.QuotaOverride> quotaOverrides,
            @com.fasterxml.jackson.annotation.JsonProperty("test_RAM_joint_hard_bytes") long memoryLimitBytes,
            @com.fasterxml.jackson.annotation.JsonProperty("Maven_heap_bytes") long mavenHeapBytes,
            AttemptAccountingAuthority workpackageAccounting) {
        public AttemptCapacityRelease {
            if (!ATTEMPT_RELEASE_SCHEMA.equals(schema) || !"RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE".equals(status)
                    || machineId == null || machineId.isBlank() || ownerTask == null || ownerTask.isBlank() || policyRef == null
                    || workpackageAccounting == null || memoryLimitBytes <= 0 || mavenHeapBytes <= 0 || mavenHeapBytes >= memoryLimitBytes
                    || !Instant.parse(observedAtUtc).isBefore(Instant.parse(reviewAtUtc)))
                throw new IllegalArgumentException("Finite versioned issuer document and actual accounting source required");
            approvedOutputRoots = List.copyOf(approvedOutputRoots); parts = Map.copyOf(parts);
            volumes = Map.copyOf(volumes); quotaOverrides = Map.copyOf(quotaOverrides);
            if (approvedOutputRoots.isEmpty() || approvedOutputRoots.size() > 16 || volumes.isEmpty()
                    || !parts.keySet().equals(Set.of("m2", "build", "tools", "scratch", "artifacts", "metadata_logs"))
                    || parts.values().stream().anyMatch(value -> value <= 0)
                    || approvedOutputRoots.stream().anyMatch(value -> !Path.of(value).isAbsolute()))
                throw new IllegalArgumentException("Explicit approved roots, six runtime budgets and volume reservations required");
            for (String root : List.of(mavenRepository, buildRoot, temporaryRoot))
                if (!Path.of(root).isAbsolute()) throw new IllegalArgumentException("Canonical runtime paths required");
        }
    }

    private record Lease(String machineId, Instant deadline, Map<String, Long> caps, long memoryLimitBytes,
            long mavenHeapBytes, Map<Path, Long> minimumFreeByVolume, AttemptAccountingAuthority attemptAuthority, FileRef releaseRef) {}
    public record CapacityRelease(String schema, String machineId, String observedAtUtc, String reviewAtUtc,
            String status, String ownerTask, FileRef policyRef, List<String> approvedOutputRoots,
            String temporaryRoot, Map<String, Long> parts, Map<String, CiBootstrap.VolumeBudget> volumes,
            Map<String, CiBootstrap.QuotaOverride> quotaOverrides,
            long memoryLimitBytes, long mavenHeapBytes) {
        public CapacityRelease {
            if (!"xar.java-control.capacity-release/v1".equals(schema) || !"RELEASED".equals(status)
                    || machineId == null || machineId.isBlank() || ownerTask == null || ownerTask.isBlank()
                    || policyRef == null || temporaryRoot == null || !Path.of(temporaryRoot).isAbsolute()
                    || memoryLimitBytes <= 0 || mavenHeapBytes <= 0 || mavenHeapBytes >= memoryLimitBytes) {
                throw new IllegalArgumentException("Invalid typed capacity release");
            }
            if (!Instant.parse(observedAtUtc).isBefore(Instant.parse(reviewAtUtc))) throw new IllegalArgumentException("Finite authority required");
            approvedOutputRoots = List.copyOf(approvedOutputRoots); parts = Map.copyOf(parts); volumes = Map.copyOf(volumes); quotaOverrides = Map.copyOf(quotaOverrides);
            if (approvedOutputRoots.isEmpty() || approvedOutputRoots.size() > 16 || volumes.isEmpty()
                    || approvedOutputRoots.stream().anyMatch(path -> !Path.of(path).isAbsolute())
                    || parts.values().stream().anyMatch(value -> value <= 0)) throw new IllegalArgumentException("Finite roots and part caps required");
        }
    }
    private record Failure(String schema, String status, String observedAtUtc, String error) {}

    public static ObjectMapper strictMapper() {
        com.fasterxml.jackson.databind.module.SimpleModule versions = new com.fasterxml.jackson.databind.module.SimpleModule("explicit-build-accounting-versions");
        versions.addDeserializer(BuildReceipt.class, new com.fasterxml.jackson.databind.deser.std.StdDeserializer<BuildReceipt>(BuildReceipt.class) {
            private static final long serialVersionUID = 1L;
            @Override public BuildReceipt deserialize(com.fasterxml.jackson.core.JsonParser parser, com.fasterxml.jackson.databind.DeserializationContext context) throws IOException {
                JsonNode node = context.readTree(parser);
                try { return JSON.treeToValue(receiptAccountingVersion(node, SCHEMA, SCOPED_BUILD_SCHEMA), BuildReceipt.class); }
                catch (IOException error) { throw com.fasterxml.jackson.databind.JsonMappingException.from(parser, error.getMessage(), error); }
            }
        });
        versions.addDeserializer(CaptureBuildReceipt.class, new com.fasterxml.jackson.databind.deser.std.StdDeserializer<CaptureBuildReceipt>(CaptureBuildReceipt.class) {
            private static final long serialVersionUID = 1L;
            @Override public CaptureBuildReceipt deserialize(com.fasterxml.jackson.core.JsonParser parser, com.fasterxml.jackson.databind.DeserializationContext context) throws IOException {
                JsonNode node = context.readTree(parser);
                try { return JSON.treeToValue(receiptAccountingVersion(node, CAPTURE_SCHEMA, SCOPED_CAPTURE_SCHEMA), CaptureBuildReceipt.class); }
                catch (IOException error) { throw com.fasterxml.jackson.databind.JsonMappingException.from(parser, error.getMessage(), error); }
            }
        });
        return JSON.copy().registerModule(versions);
    }

    private static ObjectMapper createMapper() {
        ObjectMapper mapper = JsonMapper.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
                .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, DeserializationFeature.FAIL_ON_TRAILING_TOKENS,
                        DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES, DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES,
                        DeserializationFeature.FAIL_ON_NUMBERS_FOR_ENUMS)
                .propertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE).build();
        for (LogicalType type : List.of(LogicalType.Integer, LogicalType.Boolean)) {
            for (CoercionInputShape shape : List.of(CoercionInputShape.String, CoercionInputShape.Float,
                    CoercionInputShape.Boolean, CoercionInputShape.Integer)) {
                if ((type == LogicalType.Integer && shape == CoercionInputShape.Integer)
                        || (type == LogicalType.Boolean && shape == CoercionInputShape.Boolean)) continue;
                mapper.coercionConfigFor(type).setCoercion(shape, CoercionAction.Fail);
            }
        }
        for (CoercionInputShape shape : List.of(CoercionInputShape.Integer, CoercionInputShape.Float, CoercionInputShape.Boolean)) {
            mapper.coercionConfigFor(LogicalType.Textual).setCoercion(shape, CoercionAction.Fail);
        }
        for (CoercionInputShape shape : List.of(CoercionInputShape.String, CoercionInputShape.Boolean)) {
            mapper.coercionConfigFor(LogicalType.Float).setCoercion(shape, CoercionAction.Fail);
        }
        return mapper;
    }

    private record VerifiedCompletedBuild(BuildReceipt receipt, Instant leaseReviewAt, Path historicalScratch) { }

    /** Complete software qualification plus the original still-live build capacity lease. */
    public static BuildReceipt acceptedReceipt(Path path) throws IOException {
        VerifiedCompletedBuild verified = verifyCompletedBuild(FileRef.measure(path));
        if (!Instant.now().isBefore(verified.leaseReviewAt())) throw new IOException("Build capacity release expired");
        requireNativeScratch(verified.historicalScratch());
        BuildReceipt receipt = verified.receipt();
        if (SCOPED_BUILD_SCHEMA.equals(receipt.schema())) {
            Path snapshot = Path.of(receipt.compiledSourceRoot()); Path work = snapshot.getParent().getParent();
            JsonNode original = object(JSON.readTree(exactAccountingBytes(receipt.capacityReleaseRef(), 128 << 10)));
            AttemptCapacityRelease release = JSON.treeToValue(original, AttemptCapacityRelease.class);
            Config config = new Config(Path.of(receipt.sourceRoot()), work, Path.of(receipt.capacityReleaseRef().path()),
                    release.workpackageAccounting().attempt(), release.ownerTask(), null, work, "3.10.0", 900,
                    receipt.targetKind(), receipt.sourceLimitProfile());
            readAttemptLease(config, receipt.machineId(), release, Instant.now());
        }
        return receipt;
    }

    /**
     * Verifies completed software evidence without granting present execution or storage authority.
     * Callers must independently validate their current operation card, standing and allocation.
     */
    public static BuildReceipt verifiedCompletedReceipt(FileRef receiptRef) throws IOException {
        return verifyCompletedBuild(receiptRef).receipt();
    }

    private static VerifiedCompletedBuild verifyCompletedBuild(FileRef receiptRef) throws IOException {
        Objects.requireNonNull(receiptRef); receiptRef.verify();
        BuildReceipt receipt = decodeBuildReceipt(readReceiptEnvelope(receiptRef));
        if (!receipt.machineId().equals(WindowsJobProcess.currentMachineId()) || !receipt.status().equals("PASS")
                || receipt.sourcePostcheck().state() != SourceState.MATCH || receipt.compiledSourcePostcheck().state() != SourceState.MATCH
                || receipt.error() != null || receipt.toolchainProbe() == null || !receipt.toolchainProbe().passed()
                || receipt.mavenToolchain() == null || receipt.mavenResult() == null || !receipt.mavenResult().passed()
                || receipt.sourcePins().isEmpty() || receipt.compiledSourcePins().isEmpty() || receipt.completeDeployment().isEmpty()) {
            throw new IOException("Build receipt did not establish current-machine complete qualification");
        }
        Instant completed = Instant.parse(receipt.observedAtUtc());
        CompletedLeaseWindow window = completedLeaseWindow(receipt.capacityReleaseRef(), receipt.machineId(), completed);
        Instant opened = window.opened(); Instant review = window.review();
        requireCompletedNativeWindow(receipt.toolchainProbe(), opened, completed);
        requireCompletedNativeWindow(receipt.mavenResult(), opened, completed);
        receipt.mavenToolchain().distributionLauncherRef().verify(); receipt.javaExecutableRef().verify();
        if (receipt.mavenToolchain().explicitOverrideRef() != null) receipt.mavenToolchain().explicitOverrideRef().verify();
        for (FileRef reference : receipt.sourcePins()) reference.verify();
        for (FileRef reference : receipt.compiledSourcePins()) reference.verify();
        for (FileRef reference : receipt.completeDeployment()) reference.verify();
        if (receipt.producerRuntimePins().isEmpty()) throw new IOException("Build producer runtime closure missing");
        for (FileRef reference : receipt.producerRuntimePins()) reference.verify();
        requireSameContents(Path.of(receipt.sourceRoot()), Path.of(receipt.compiledSourceRoot()), receipt.sourcePins(), receipt.compiledSourcePins());
        if (!sourceManifest(Path.of(receipt.sourceRoot()), receipt.sourceLimitProfile()).equals(receipt.sourcePins())
                || !sourceManifest(Path.of(receipt.compiledSourceRoot()), receipt.sourceLimitProfile()).equals(receipt.compiledSourcePins())) {
            throw new IOException("Source closure grew or changed after build");
        }
        verifyCompletedAccounting(receipt.schema().equals(SCOPED_BUILD_SCHEMA), receipt.capacityReleaseRef(), receipt.machineId(), completed,
                Path.of(receipt.compiledSourceRoot()), Path.of(receipt.sourceRoot()), receipt.workpackageAccountingRef(), receipt.finalLogicalBytesByPart());
        Path argumentManifest = Path.of(receipt.compiledSourceRoot()).resolve(MavenArgumentFile.MANIFEST);
        if (Files.isRegularFile(argumentManifest, LinkOption.NOFOLLOW_LINKS)) {
            var manifest = JSON.readValue(readLimited(argumentManifest, MavenArgumentFile.MAXIMUM_BYTES), MavenArgumentFile.Manifest.class);
            MavenArgumentFile.readManifest(Path.of(receipt.compiledSourceRoot()), manifest.arguments());
            var lobby = LobbyVerifyTestInputs.fromRecordedArguments(manifest.arguments());
            if (lobby.isPresent()) LobbyVerifyTestInputs.requireInputs(lobby.orElseThrow(), receipt.machineId(), completed);
        }
        List<FileRef> actual = deploymentManifest(Path.of(receipt.deploymentRoot()), receipt.targetKind());
        if (!actual.equals(receipt.completeDeployment())) throw new IOException("Deployment closure grew or changed");
        if (receipt.sourceLimitProfile().currentParity()) FullParityCurrentBindings.completedBuildBindings(receipt);
        receiptRef.verify(); receipt.capacityReleaseRef().verify();
        return new VerifiedCompletedBuild(receipt, review, window.historicalScratch());
    }

    /** One original-lease chronology contract for normal and capture completion evidence. */
    record CompletedLeaseWindow(Instant opened, Instant review, Path historicalScratch) { }

    static CompletedLeaseWindow completedLeaseWindow(FileRef releaseRef, String machine, Instant completed) throws IOException {
        Objects.requireNonNull(releaseRef); Objects.requireNonNull(completed); releaseRef.verify();
        JsonNode release = readObject(Path.of(releaseRef.path()));
        String schema = text(release, "schema");
        boolean manual = schema.equals("xar.java-phase1.manual-capacity-release/v1") || schema.equals(ATTEMPT_RELEASE_SCHEMA);
        boolean typed = schema.equals("xar.java-control.capacity-release/v1");
        if ((!manual && !typed) || !text(release, "machine_id").equals(machine)
                || !text(release, "status").equals(manual ? "RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE" : "RELEASED")) {
            throw new IOException("Original build release schema, machine or state rejected");
        }
        Instant opened = Instant.parse(text(release, "observed_at_utc"));
        Instant review = Instant.parse(text(release, "review_at_utc"));
        if (!opened.isBefore(review) || completed.isBefore(opened) || !completed.isBefore(review) || completed.isAfter(Instant.now())) {
            throw new IOException("Completed build observation is outside its original finite lease window");
        }
        releaseRef.verify();
        return new CompletedLeaseWindow(opened, review, Path.of(text(release, "temporary_root")));
    }

    static void requireCompletedNativeWindow(WindowsJobProcess.CommandResult result, Instant opened, Instant completed) throws IOException {
        java.math.BigInteger ticks = new java.math.BigInteger(result.identity().creationFiletimeDecimal());
        java.math.BigInteger[] parts = ticks.divideAndRemainder(java.math.BigInteger.valueOf(10_000_000L));
        Instant born;
        try {
            born = Instant.ofEpochSecond(parts[0].longValueExact() - 11_644_473_600L, parts[1].longValueExact() * 100L);
        } catch (ArithmeticException | java.time.DateTimeException invalid) {
            throw new IOException("Native process birth is outside the timestamp domain", invalid);
        }
        Duration lifetime = Duration.between(opened, completed);
        double leaseElapsed = lifetime.getSeconds() + lifetime.getNano() / 1_000_000_000.0;
        // elapsedSeconds begins before CreateProcess, so it cannot be added to FILETIME birth exactly.
        if (born.isBefore(opened) || born.isAfter(completed) || result.elapsedSeconds() > leaseElapsed) {
            throw new IOException("Native terminal chronology differs from the completed build lease window");
        }
    }

    private enum BuildPurpose { VERIFY, TEST_COMPILED_CAPTURE_ONLY }
    private record BuildEvidence(Config config, Path snapshot, Path deployment, List<FileRef> source,
            List<FileRef> compiled, List<FileRef> closure, SourcePostcheck sourcePostcheck,
            SourcePostcheck compiledPostcheck, MavenToolchain toolchain,
            WindowsJobProcess.CommandResult probe, WindowsJobProcess.CommandResult result,
            List<String> mavenArguments, FileRef testCompilationRef, Map<String, Long> finalSizes,
            WorkpackageAccounting accounting, FileRef accountingRef, boolean scoped, String failure, boolean interrupted) { }
    private record BuildOutcome(BuildReceipt verified, CaptureBuildReceipt capture) { }
    private record CaptureBuildFailure(String schema, String machineId, String observedAtUtc,
            CaptureTestState tests, BuildReceipt terminal, List<String> mavenArguments,
            FileRef mavenCommandRef) { }

    private record VerifiedCompletedCapture(CaptureBuildReceipt receipt, Config config) { }

    /** Capture compilation evidence plus the original still-live capacity lease. */
    public static CaptureBuildReceipt acceptedCaptureReceipt(Path path) throws IOException {
        VerifiedCompletedCapture verified = verifyCompletedCapture(FileRef.measure(path));
        readLease(verified.config(), verified.receipt().machineId());
        return verified.receipt();
    }

    /**
     * Verifies completed test compilation only; tests remain NOT_RUN.
     * This supplies no present execution/storage authority: callers must validate their current card and standing.
     */
    public static CaptureBuildReceipt verifiedCompletedCaptureReceipt(FileRef receiptRef) throws IOException {
        return verifyCompletedCapture(receiptRef).receipt();
    }

    private static VerifiedCompletedCapture verifyCompletedCapture(FileRef receiptRef) throws IOException {
        Objects.requireNonNull(receiptRef); receiptRef.verify();
        CaptureBuildReceipt receipt = decodeCaptureReceipt(readReceiptEnvelope(receiptRef));
        String machine = WindowsJobProcess.currentMachineId();
        if (!receipt.machineId().equals(machine)) throw new IOException("Capture receipt belongs to another machine");
        Path snapshot = Path.of(receipt.compiledSourceRoot()).toAbsolutePath().normalize();
        if (snapshot.getParent() == null || snapshot.getParent().getParent() == null) throw new IOException("Exact capture snapshot ancestry required");
        Path work = snapshot.getParent().getParent(); Path build = work.resolve("build").resolve(receipt.attempt());
        Path logs = work.resolve("logs");
        if (!snapshot.equals(work.resolve("scratch/source-" + receipt.attempt()))
                || !Path.of(receipt.deploymentRoot()).toAbsolutePath().normalize().equals(build.resolve("ck3-control-local-service/quarkus-app"))) {
            throw new IOException("Capture source and deployment roots differ from actual producer attempt");
        }
        Config config = new Config(Path.of(receipt.sourceRoot()), work, Path.of(receipt.capacityReleaseRef().path()),
                receipt.attempt(), receipt.ownerTask(), null, Path.of(receipt.javaExecutableRef().path()).getParent().getParent(),
                receipt.mavenToolchain().minimumVersion(), 900, receipt.targetKind(), receipt.sourceLimitProfile());
        Instant completed = Instant.parse(receipt.observedAtUtc());
        CompletedLeaseWindow window = completedLeaseWindow(receipt.capacityReleaseRef(), machine, completed);
        requireCompletedNativeWindow(receipt.toolchainProbe(), window.opened(), completed);
        requireCompletedNativeWindow(receipt.mavenResult(), window.opened(), completed);
        Lease lease = readCompletedLeaseAt(config, machine, completed, receipt.capacityReleaseRef(), receipt.workpackageAccountingRef());
        if (receipt.mavenResult().accounting().memoryLimitBytes() != lease.memoryLimitBytes()
                || receipt.toolchainProbe().accounting().memoryLimitBytes() != lease.memoryLimitBytes()) throw new IOException("Capture Job differs from the consumed single-Maven memory release");
        Path settings = logs.resolve("build-" + receipt.attempt() + "-settings.xml");
        List<String> expectedArgs = completedCaptureArguments(config, settings, snapshot, build, receipt.mavenArguments(), receipt.capacityReleaseRef(), completed, receipt.workpackageAccountingRef());
        String prefix = "build-" + receipt.attempt();
        requireExactPath(receipt.mavenCommandRef(), logs.resolve(prefix + "-package.cmd"));
        requireExactPath(receipt.mavenStdoutRef(), logs.resolve(prefix + "-package.stdout.log"));
        requireExactPath(receipt.mavenStderrRef(), logs.resolve(prefix + "-package.stderr.log"));
        requireExactPath(receipt.versionStdoutRef(), logs.resolve(prefix + "-version.stdout.log"));
        requireExactPath(receipt.testCompilationRef(), logs.resolve(prefix + "-test-compilation.json"));
        for (FileRef ref : List.of(receipt.mavenCommandRef(), receipt.mavenStdoutRef(), receipt.mavenStderrRef(),
                receipt.versionStdoutRef(), receipt.testCompilationRef(), receipt.javaExecutableRef(), receipt.mavenToolchain().distributionLauncherRef())) ref.verify();
        if (!java.util.Arrays.equals(readLimited(Path.of(receipt.mavenCommandRef().path()), 65536), mavenExecutionBatchText(null, expectedArgs, snapshot).getBytes(StandardCharsets.UTF_8))) {
            throw new IOException("Actual pinned Maven command batch does not contain the exact default capture command");
        }
        MavenToolchain actualMaven = measuredMavenToolchain(null, Files.readString(Path.of(receipt.versionStdoutRef().path())), config.minimumMavenVersion());
        if (!actualMaven.equals(receipt.mavenToolchain())) throw new IOException("Capture default Maven reported home/version/source differs");
        for (FileRef ref : receipt.sourcePins()) ref.verify(); for (FileRef ref : receipt.compiledSourcePins()) ref.verify();
        for (FileRef ref : receipt.completeDeployment()) ref.verify(); for (FileRef ref : receipt.producerRuntimePins()) ref.verify();
        requireSameContents(config.sourceRoot(), snapshot, receipt.sourcePins(), receipt.compiledSourcePins());
        if (!sourceManifest(config.sourceRoot(), config.sourceLimitProfile()).equals(receipt.sourcePins())
                || !sourceManifest(snapshot, config.sourceLimitProfile()).equals(receipt.compiledSourcePins())
                || !deploymentManifest(Path.of(receipt.deploymentRoot()), receipt.targetKind()).equals(receipt.completeDeployment())) {
            throw new IOException("Capture source or complete packaged deployment closure changed");
        }
        TestCompilationManifest recorded = JSON.readValue(readLimited(Path.of(receipt.testCompilationRef().path()), 4 << 20), TestCompilationManifest.class);
        TestCompilationManifest actual = collectTestCompilation(machine, snapshot, build, receipt.compiledSourcePins());
        if (!recorded.machineId().equals(machine) || !recorded.modules().equals(actual.modules()) || !recorded.notRunTests().equals(actual.notRunTests())) {
            throw new IOException("Capture compiler input/created-file/test-binary SourceFile origin closure changed");
        }
        if (receipt.schema().equals(SCOPED_CAPTURE_SCHEMA)) verifyCompletedAccounting(true, receipt.capacityReleaseRef(), machine, completed,
                snapshot, Path.of(receipt.sourceRoot()), receipt.workpackageAccountingRef(), receipt.finalLogicalBytesByPart());
        else {
            if (lease.attemptAuthority() != null || !receipt.finalLogicalBytesByPart().keySet().equals(lease.caps().keySet())) throw new IOException("Complete historical capture final part accounting required");
            for (var item : receipt.finalLogicalBytesByPart().entrySet()) if (item.getValue() < 0 || item.getValue() > lease.caps().get(item.getKey())) throw new IOException("Capture final part exceeded its actual release");
        }
        receipt.testCompilationRef().verify(); receipt.capacityReleaseRef().verify(); receiptRef.verify();
        return new VerifiedCompletedCapture(receipt, config);
    }

    private static void verifyCompletedAccounting(boolean scoped, FileRef releaseRef, String machine, Instant completed,
            Path snapshot, Path sourceRoot, FileRef accountingRef, Map<String, Long> historicalParts) throws IOException {
        JsonNode original = object(JSON.readTree(exactAccountingBytes(releaseRef, 128 << 10)));
        boolean versioned = text(original, "schema").equals(ATTEMPT_RELEASE_SCHEMA);
        if (scoped != versioned) throw new IOException("Receipt accounting mode differs from original issuer schema");
        if (!scoped) return;
        if (!historicalParts.isEmpty()) throw new IOException("Scoped measurements must not impersonate complete historical parts");
        AttemptCapacityRelease release = JSON.treeToValue(original, AttemptCapacityRelease.class); AttemptAccountingAuthority authority = release.workpackageAccounting();
        Path work = snapshot.getParent().getParent();
        if (!snapshot.equals(work.resolve("scratch/source-" + authority.attempt()))) throw new IOException("Completed scoped snapshot ancestry differs");
        if (accountingRef == null) throw new IOException("Explicit accounting provenance pin required");
        requireExactPath(accountingRef, work.resolve("logs/build-" + authority.attempt() + "-accounting.json"));
        AccountingEvidence retained = completedAccountingEvidence(accountingRef);
        WorkpackageAccounting accounting = retained.accounting();
        AccountingSources sources = completedAccountingSources(accountingRef, releaseRef, release);
        Config config = new Config(sourceRoot, work, Path.of(releaseRef.path()), authority.attempt(), release.ownerTask(), null, work,
                "3.10.0", 900, TargetKind.SERVICE_FAST_JAR, SourceLimitProfile.STANDARD_8_MIB);
        readAttemptLease(config, machine, release, completed, sources);
        Instant observed = Instant.parse(accounting.observedAtUtc());
        if (accounting.mode() != AccountingMode.CONSERVATIVE_VOLUME_ATTEMPT || !accounting.capacityReleaseRef().equals(releaseRef)
                || !accounting.machineId().equals(machine) || !accounting.measuredRoots().equals(authority.measuredRoots())
                || observed.isBefore(Instant.parse(release.observedAtUtc())) || observed.isAfter(completed)) throw new IOException("Completed accounting provenance/chronology mismatch");
        for (String key : ATTEMPT_SCOPES) if (accounting.logicalBytesByScope().get(key) > authority.logicalCapsByScope().get(key)
                || accounting.nativeAllocatedBytesByScope().get(key) > authority.nativeCapsByScope().get(key)) throw new IOException("Completed actual scope exceeded its reservation");
        if (accounting.peakNewLogicalBytes() < exactSum(accounting.logicalBytesByScope()) || accounting.peakNewNativeAllocatedBytes() < exactSum(accounting.nativeAllocatedBytesByScope())
                || accounting.peakNewLogicalBytes() > authority.maximumNewLogicalBytes() || accounting.peakNewNativeAllocatedBytes() > authority.maximumNewNativeBytes()) throw new IOException("Completed actual logical/Native peak rejected");
        if (accounting.volumes().size() != release.volumes().size()) throw new IOException("Complete original volume coverage required");
        JsonNode financial = object(JSON.readTree(exactAccountingBytes(authority.financialSourceRef(), 128 << 10)));
        Set<Path> observedRoots = new HashSet<>();
        for (VolumeObservation volume : accounting.volumes()) {
            Path root = Path.of(volume.volumeRoot()); String letter = root.toString().substring(0, 1).toUpperCase(Locale.ROOT);
            CiBootstrap.VolumeBudget budget = release.volumes().entrySet().stream().filter(entry -> Path.of(entry.getKey()).equals(root)).map(Map.Entry::getValue).findFirst().orElseThrow(() -> new IOException("Foreign completed volume"));
            JsonNode old = object(object(financial.get("fresh_observations")).get(letter)); JsonNode reserves = object(financial.get("reserves"));
            long held = positive(financial, letter.equals("D") ? "all_holds_including_current_R3_bytes" : letter + "_other_unspent_holds_bytes");
            if (!observedRoots.add(root) || volume.totalBytes() != budget.totalVolumeBytes() || volume.requiredFreeBytes() != budget.requiredFree()
                    || volume.effectiveProjectQuota() != budget.effectiveProjectQuota() || volume.allHoldsBytes() != held
                    || volume.systemGrowthReserve() != positive(reserves, letter + "_system_growth") || volume.safetyReserve() != positive(reserves, letter + "_safety")
                    || volume.quotaUsedUpperBytes() < positive(old, "used_upper")) throw new IOException("Completed quote differs from retained source or grants deletion credit");
            requireVolumeQuote(volume);
        }
        sources.verify(release.policyRef()); authority.financialSourceRef().verify();
        for (FileRef ref : authority.reservationSourceRefs()) sources.verify(ref);
        accountingRef.verify();
    }

    private static void requireExactPath(FileRef reference, Path expected) throws IOException {
        if (!Path.of(reference.path()).toAbsolutePath().normalize().equals(expected.toAbsolutePath().normalize())) throw new IOException("Capture evidence path differs from exact producer attempt");
    }

    public static BuildReceipt build(Config config) throws IOException, InterruptedException {
        return buildExclusive(config, BuildPurpose.VERIFY).verified();
    }

    /** The same Maven producer and Job; package compiles tests and explicitly does not run them. */
    public static CaptureBuildReceipt buildCapture(Config config) throws IOException, InterruptedException {
        if (config.mavenCommand() != null || config.targetKind() != TargetKind.SERVICE_FAST_JAR) {
            throw new IOException("Capture qualification requires the default Maven and existing service fast-jar target");
        }
        return buildExclusive(config, BuildPurpose.TEST_COMPILED_CAPTURE_ONLY).capture();
    }

    /** Strict bounded envelope parsing only; this does not establish build qualification. */
    static BuildReceipt readBuildReceiptEnvelope(Path path) throws IOException {
        return decodeBuildReceipt(readLimited(path, BUILD_RECEIPT_MAX_BYTES));
    }

    /** Explicit historical wire branch; missing new provenance is accepted only for original v5/v1. */
    public static BuildReceipt decodeBuildReceipt(byte[] bytes) throws IOException {
        JsonNode node = receiptAccountingVersion(bytes, SCHEMA, SCOPED_BUILD_SCHEMA);
        return JSON.treeToValue(node, BuildReceipt.class);
    }
    public static CaptureBuildReceipt decodeCaptureReceipt(byte[] bytes) throws IOException {
        JsonNode node = receiptAccountingVersion(bytes, CAPTURE_SCHEMA, SCOPED_CAPTURE_SCHEMA);
        return JSON.treeToValue(node, CaptureBuildReceipt.class);
    }
    private static JsonNode receiptAccountingVersion(byte[] bytes, String historical, String current) throws IOException {
        if (bytes.length < 1 || bytes.length > BUILD_RECEIPT_ENVELOPE_MAX_BYTES) throw new IOException("Bounded build receipt required");
        return receiptAccountingVersion(JSON.readTree(bytes), historical, current);
    }
    private static JsonNode receiptAccountingVersion(JsonNode input, String historical, String current) throws IOException {
        JsonNode node = object(input); String schema = text(node, "schema");
        if (!schema.equals(historical) && !schema.equals(current)) throw new IOException("Unknown versioned accounting receipt schema");
        if ((schema.equals(historical) || (schema.equals(SCOPED_BUILD_SCHEMA) && "RED".equals(node.path("status").textValue())
                && node.path("error").isTextual() && !node.path("error").textValue().isBlank())) && !node.has("workpackage_accounting_ref")) ((com.fasterxml.jackson.databind.node.ObjectNode) node).putNull("workpackage_accounting_ref");
        return node;
    }

    public static int receiptMaxBytes(SourceLimitProfile profile) {
        return Objects.requireNonNull(profile).resumedParity()
                ? RESUMED_BUILD_RECEIPT_MAX_BYTES : BUILD_RECEIPT_MAX_BYTES;
    }

    /** Actual bytes only. This checks the selected versioned envelope, not completed-build qualification. */
    public static byte[] readReceiptEnvelope(FileRef ref) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > BUILD_RECEIPT_ENVELOPE_MAX_BYTES)
            throw new IOException("Bounded selected build receipt envelope required");
        ref.verify(); byte[] bytes = readLimited(Path.of(ref.path()), BUILD_RECEIPT_ENVELOPE_MAX_BYTES);
        final JsonNode envelope;
        try { envelope = JSON.readTree(bytes); }
        catch (com.fasterxml.jackson.core.JsonProcessingException error) {
            if (bytes.length > BUILD_RECEIPT_MAX_BYTES) throw new IOException("JSON input exceeds limit", error);
            throw error;
        }
        JsonNode selected = envelope == null ? null : envelope.get("source_limit_profile");
        if (selected == null || !selected.isTextual()) throw new IOException("Explicit selected receipt source profile required");
        final SourceLimitProfile profile;
        try { profile = SourceLimitProfile.valueOf(selected.textValue()); }
        catch (IllegalArgumentException error) { throw new IOException("Unknown selected receipt source profile", error); }
        if (bytes.length > receiptMaxBytes(profile)) throw new IOException("Build receipt exceeds its finite selected profile byte limit");
        ref.verify(); return bytes;
    }

    static byte[] buildReceiptBytes(BuildReceipt receipt) throws IOException {
        return checkedBuildReceiptBytes(JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(Objects.requireNonNull(receipt)), receipt.sourceLimitProfile());
    }

    static byte[] captureReceiptBytes(CaptureBuildReceipt receipt) throws IOException {
        return checkedBuildReceiptBytes(JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(Objects.requireNonNull(receipt)), receipt.sourceLimitProfile());
    }

    private static byte[] checkedBuildReceiptBytes(byte[] bytes) throws IOException {
        if (bytes.length > BUILD_RECEIPT_MAX_BYTES) throw new IOException("Build receipt exceeds finite 2 MiB byte limit");
        return bytes;
    }
    private static byte[] checkedBuildReceiptBytes(byte[] bytes, SourceLimitProfile profile) throws IOException {
        if (!profile.resumedParity()) return checkedBuildReceiptBytes(bytes);
        if (bytes.length > RESUMED_BUILD_RECEIPT_MAX_BYTES) throw new IOException("R2 build receipt exceeds finite 4 MiB byte limit");
        return bytes;
    }

    private static BuildOutcome buildExclusive(Config config, BuildPurpose purpose) throws IOException, InterruptedException {
        ProjectStoragePolicy.requireBulkOutput(config.workRoot());
        CanonicalOracleEnvironment.require(System.getenv());
        requireNativeScratch(config.workRoot().resolve("scratch"));
        String machine = WindowsJobProcess.currentMachineId();
        Lease lease = readLease(config, machine);
        requireToolPaths(config, machine);
        try (PreparedTemporaryRoot temporary = prepareWorkpackageTemporaryRoot(config, lease, () -> {})) {
        temporary.requireCurrent();
        guard(config, lease, temporary::requireCurrent);
        Path logs = config.workRoot().resolve("logs"); Files.createDirectories(logs);
        try (FileChannel channel = FileChannel.open(config.workRoot().resolve(".java-control-build.lock"),
                StandardOpenOption.CREATE, StandardOpenOption.WRITE); FileLock lock = channel.tryLock()) {
            if (lock == null || !lock.isValid()) throw new IOException("Another Maven writer owns this workpackage");
            BuildEvidence evidence = buildLocked(config, lease, machine, logs, purpose, temporary::requireCurrent);
            Path receiptPath = logs.resolve("build-" + config.attempt() + ".json");
            try {
                temporary.requireCurrent();
                if (purpose == BuildPurpose.VERIFY) {
                    BuildReceipt receipt = normalReceipt(evidence, machine, evidence.failure());
                    Files.write(receiptPath, buildReceiptBytes(receipt), StandardOpenOption.CREATE_NEW);
                    return new BuildOutcome(receipt, null);
                }
                if (evidence.failure() != null) throw new IOException(evidence.failure());
                CaptureBuildReceipt receipt = new CaptureBuildReceipt(evidence.scoped() ? SCOPED_CAPTURE_SCHEMA : CAPTURE_SCHEMA, machine, Instant.now().toString(),
                        config.attempt(), config.ownerTask(), CaptureQualification.TEST_COMPILED_CAPTURE_ONLY, CaptureTestState.NOT_RUN,
                        config.sourceRoot().toString(), evidence.snapshot().toString(), evidence.deployment().toString(),
                        evidence.sourcePostcheck(), evidence.compiledPostcheck(), config.targetKind(), config.sourceLimitProfile(),
                        evidence.source(), evidence.compiled(), evidence.closure(), producerClosure(), FileRef.measure(config.capacityRelease()),
                        evidence.toolchain(), FileRef.measure(config.javaHome().resolve("bin/java.exe")), evidence.probe(), evidence.result(),
                        evidence.mavenArguments(), FileRef.measure(logs.resolve("build-" + config.attempt() + "-package.cmd")),
                        FileRef.measure(logs.resolve("build-" + config.attempt() + "-package.stdout.log")),
                        FileRef.measure(logs.resolve("build-" + config.attempt() + "-package.stderr.log")),
                        FileRef.measure(logs.resolve("build-" + config.attempt() + "-version.stdout.log")), evidence.testCompilationRef(), evidence.finalSizes(), evidence.accountingRef());
                byte[] receiptBytes = captureReceiptBytes(receipt);
                Files.write(receiptPath, receiptBytes, StandardOpenOption.CREATE_NEW);
                return new BuildOutcome(null, receipt);
            } catch (IOException | RuntimeException error) {
                if (purpose == BuildPurpose.TEST_COMPILED_CAPTURE_ONLY && !Files.exists(receiptPath)) {
                    String failure = appendFailure(evidence.failure(), "Capture qualification unavailable: " + error.getMessage());
                    Path command = logs.resolve("build-" + config.attempt() + "-package.cmd");
                    CaptureBuildFailure actual = new CaptureBuildFailure("xar.java-control-test-compiled-capture-failure/v1", machine,
                            Instant.now().toString(), CaptureTestState.NOT_RUN, normalReceipt(evidence, machine, failure),
                            evidence.mavenArguments(), Files.exists(command) ? FileRef.measure(command) : null);
                    Files.write(receiptPath, checkedBuildReceiptBytes(JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(actual), config.sourceLimitProfile()), StandardOpenOption.CREATE_NEW);
                }
                throw error;
            } finally { if (evidence.interrupted()) Thread.currentThread().interrupt(); }
        }
        }
    }

    private static BuildReceipt normalReceipt(BuildEvidence evidence, String machine, String failure) throws IOException {
        Config config = evidence.config();
        return new BuildReceipt(evidence.scoped() ? SCOPED_BUILD_SCHEMA : SCHEMA, machine, Instant.now().toString(), failure == null ? "PASS" : "RED",
                config.sourceRoot().toString(), evidence.snapshot().toString(), evidence.deployment().toString(),
                evidence.sourcePostcheck(), evidence.compiledPostcheck(), config.targetKind(), config.sourceLimitProfile(),
                evidence.source(), evidence.compiled(), evidence.closure(), producerClosure(), FileRef.measure(config.capacityRelease()),
                evidence.toolchain(), FileRef.measure(config.javaHome().resolve("bin/java.exe")), evidence.probe(), evidence.result(), evidence.finalSizes(), failure, evidence.accountingRef());
    }

    private static BuildEvidence buildLocked(Config config, Lease lease, String machine, Path logs, BuildPurpose purpose,
            CiBootstrap.IoGuard temporaryGuard) throws IOException, InterruptedException {
        temporaryGuard.check();
        Path snapshot = config.workRoot().resolve("scratch/source-" + config.attempt());
        Path build = config.workRoot().resolve("build/" + config.attempt());
        Path receiptPath = logs.resolve("build-" + config.attempt() + ".json");
        if (Files.exists(snapshot) || Files.exists(build) || Files.exists(receiptPath)) throw new IOException("Build attempt already exists");
        List<FileRef> source = sourceManifest(config.sourceRoot(), config.sourceLimitProfile());
        if (source.isEmpty() || !Files.isRegularFile(config.sourceRoot().resolve("pom.xml"))) throw new IOException("Maven source closure is missing");
        Files.createDirectories(snapshot); Files.createDirectories(build);
        if (!Files.getFileStore(snapshot).equals(Files.getFileStore(build))) throw new IOException("Source snapshot and build output must share a filesystem");
        Files.createDirectory(build.resolve("integration-test-scratch"));
        List<FileRef> compiled = new ArrayList<>();
        for (FileRef original : source) {
            Path relative = config.sourceRoot().relativize(Path.of(original.path()));
            Path destination = snapshot.resolve(relative).normalize();
            if (!destination.startsWith(snapshot)) throw new IOException("Source path escaped snapshot");
            Files.createDirectories(destination.getParent()); Files.copy(Path.of(original.path()), destination);
            compiled.add(FileRef.measure(destination));
        }
        requireSameContents(config.sourceRoot(), snapshot, source, compiled);
        Path settings = logs.resolve("build-" + config.attempt() + "-settings.xml");
        Files.writeString(settings, "<?xml version=\"1.0\"?><settings xmlns=\"http://maven.apache.org/SETTINGS/1.2.0\"><interactiveMode>false</interactiveMode></settings>", StandardOpenOption.CREATE_NEW);
        Map<String, String> environment = buildEnvironment(config, snapshot, lease);
        WindowsJobProcess.CommandResult probe = null, result = null; MavenToolchain toolchain = null;
        List<FileRef> closure = List.of(); String failure = null; boolean interrupted = false;
        List<String> mavenArguments = List.of();
        FileRef testCompilationRef = null;
        Path deployment = config.targetKind() == TargetKind.SERVICE_FAST_JAR
                ? build.resolve("ck3-control-local-service/quarkus-app") : build.resolve("ck3-control-build-tools");
        try {
            // Missing selected oracle inputs are a real RED build, with the same receipt and terminal accounting.
            final CiBootstrap.IoGuard executionGuard;
            if (purpose == BuildPurpose.VERIFY && FormalReleaseTestInputs.selected(snapshot)) {
                var formal = FormalReleaseTestInputs.fromEnvironment(environment, machine, config.sourceRoot().toString());
                FormalReleaseTestInputs.requireRecordedInputs(formal, machine, config.sourceRoot().toString());
                WorkpackageAccounting before = accountWorkpackage(config, temporaryGuard);
                requirePendingAttempt(before, lease.attemptAuthority(), "private_tmp", 4096);
                FormalReleaseTestInputs.prepareRoot(formal, temporaryRoot(config, lease), temporaryGuard);
                executionGuard = FormalReleaseTestInputs.guarded(formal, machine, config.sourceRoot().toString(), temporaryGuard);
            } else executionGuard = temporaryGuard;
            List<String> releasedVerify = reactorVerifyArguments(config, settings, snapshot, build, environment,
                    temporaryRoot(config, lease), purpose == BuildPurpose.VERIFY);
            java.util.Optional<LobbyVerifyTestInputs.Recorded> lobby = LobbyVerifyTestInputs.fromRecordedArguments(releasedVerify);
            final CiBootstrap.IoGuard completeGuard = lobby.isPresent()
                    ? LobbyVerifyTestInputs.guarded(lobby.orElseThrow(), machine, executionGuard) : executionGuard;
            completeGuard.check();
            mavenArguments = purpose == BuildPurpose.VERIFY ? releasedVerify : captureArguments(releasedVerify);
            MavenArgumentFile.inheritedArguments(snapshot); // Reject ambiguous pre-existing config before any Maven child.
            probe = invoke(config, lease, snapshot, environment, logs, "version", List.of("-version"), completeGuard);
            interrupted |= Thread.interrupted();
            String versionOutput = Files.readString(logs.resolve("build-" + config.attempt() + "-version.stdout.log"));
            if (!probe.passed()) {
                throw new IOException("Actual default Maven version probe failed or mismatched");
            }
            toolchain = measuredMavenToolchain(config.mavenCommand(), versionOutput, config.minimumMavenVersion());
            MavenArgumentFile.prepare(config.sourceRoot(), snapshot, config.mavenCommand(), mavenArguments);
            compiled = new ArrayList<>(sourceManifest(snapshot, config.sourceLimitProfile()));
            requireSameContents(config.sourceRoot(), snapshot, source, compiled);
            result = invoke(config, lease, snapshot, environment, logs, purpose == BuildPurpose.VERIFY ? "verify" : "package", mavenArguments, completeGuard);
            interrupted |= Thread.interrupted();
            if (!result.passed()) throw new IOException("Maven failed, timed out, retained children, or exceeded Job memory");
            completeGuard.check();
            if (purpose == BuildPurpose.VERIFY && config.sourceLimitProfile().currentParity()) {
                FullParityCurrentBindings.retainCompletedInvocation(config, settings, snapshot, build, deployment, mavenArguments);
            }
            for (FileRef reference : compiled) reference.verify();
            closure = deploymentManifest(deployment, config.targetKind());
            if (purpose == BuildPurpose.TEST_COMPILED_CAPTURE_ONLY) {
                TestCompilationManifest compilation = collectTestCompilation(machine, snapshot, build, compiled);
                byte[] bytes = JSON.writeValueAsBytes(compilation);
                if (bytes.length > (4 << 20)) throw new IOException("Actual test compilation manifest exceeds 4 MiB");
                Path manifestPath = logs.resolve("build-" + config.attempt() + "-test-compilation.json");
                Files.write(manifestPath, bytes, StandardOpenOption.CREATE_NEW);
                testCompilationRef = FileRef.measure(manifestPath);
            }
            guard(config, lease, temporaryGuard);
        } catch (IOException | RuntimeException error) { failure = error.getClass().getSimpleName() + ": " + error.getMessage(); }
        catch (InterruptedException error) { interrupted = true; failure = "InterruptedException: " + error.getMessage(); }
        SourcePostcheck postcheck = postcheckSource(config.sourceRoot(), source, config.sourceLimitProfile());
        if (postcheck.state() != SourceState.MATCH) failure = appendFailure(failure, "Source postcheck " + postcheck.state() + ": " + postcheck.error());
        SourcePostcheck compiledPostcheck = postcheckSource(snapshot, compiled, config.sourceLimitProfile());
        if (compiledPostcheck.state() != SourceState.MATCH) failure = appendFailure(failure, "Compiled source postcheck " + compiledPostcheck.state() + ": " + compiledPostcheck.error());
        Map<String, Long> finalSizes = Map.of(); WorkpackageAccounting accounting = null; FileRef accountingRef = null;
        try {
            if (lease.releaseRef() != null) lease.releaseRef().verify();
            accounting = accountWorkpackage(config, temporaryGuard);
            if (accounting.mode() == AccountingMode.FULL_PART_INVENTORY) finalSizes = accounting.logicalBytesByScope();
            else {
                accountingRef = publishAttemptAccounting(config,accounting,lease.attemptAuthority(),temporaryGuard);
            }
        } catch (IOException | RuntimeException error) { failure = appendFailure(failure, "Final actual accounting unavailable: " + error); }
        temporaryGuard.check();
        return new BuildEvidence(config, snapshot, deployment, List.copyOf(source), List.copyOf(compiled), closure,
                postcheck, compiledPostcheck, toolchain, probe, result, mavenArguments, testCompilationRef, finalSizes, accounting, accountingRef, lease.attemptAuthority() != null, failure, interrupted);
    }

    /** Always runs after the child terminal result, including a failed Maven command. */
    public static SourcePostcheck postcheckSource(Path sourceRoot, List<FileRef> original) {
        return postcheckSource(sourceRoot, original, SourceLimitProfile.STANDARD_8_MIB);
    }

    public static SourcePostcheck postcheckSource(Path sourceRoot, List<FileRef> original, SourceLimitProfile profile) {
        try { return new SourcePostcheck(original.equals(sourceManifest(sourceRoot, profile)) ? SourceState.MATCH : SourceState.MISMATCH, null); }
        catch (IOException | RuntimeException error) { return new SourcePostcheck(SourceState.UNKNOWN, error.getClass().getSimpleName() + ": " + error.getMessage()); }
    }

    private static String appendFailure(String previous, String next) { return previous == null ? next : previous + "; " + next; }

    private static List<FileRef> deploymentManifest(Path deployment, TargetKind targetKind) throws IOException {
        if (targetKind == TargetKind.SERVICE_FAST_JAR) {
            List<FileRef> closure = manifest(deployment, false, 10000, 512L * 1024 * 1024);
            if (closure.isEmpty() || !Files.isRegularFile(deployment.resolve("quarkus-run.jar"))) throw new IOException("Complete fast-jar output is missing");
            return closure;
        }
        List<FileRef> closure = new ArrayList<>();
        closure.add(FileRef.measure(deployment.resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar")));
        closure.addAll(manifest(deployment.resolve("lib"), false, 100, 64L * 1024 * 1024));
        closure.sort(Comparator.comparing(FileRef::path));
        return List.copyOf(closure);
    }

    private static WindowsJobProcess.CommandResult invoke(Config config, Lease lease, Path snapshot,
            Map<String, String> environment, Path logs, String phase, List<String> args,
            CiBootstrap.IoGuard temporaryGuard) throws IOException, InterruptedException {
        temporaryGuard.check();
        String label = "build-" + config.attempt() + "-" + phase;
        Path batch = logs.resolve(label + ".cmd");
        Files.writeString(batch, mavenExecutionBatchText(config.mavenCommand(), args, snapshot),
                StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        Path cmd = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe");
        WindowsJobProcess.CommandSpec spec = new WindowsJobProcess.CommandSpec(cmd, List.of("/d", "/c", batch.toString()),
                snapshot, environment, logs.resolve(label + ".stdout.log"), logs.resolve(label + ".stderr.log"), lease.memoryLimitBytes());
        temporaryGuard.check();
        try (WindowsJobProcess child = WindowsJobProcess.start(spec)) {
            AtomicLong lastGuard = new AtomicLong();
            long commandDeadline = Math.addExact(System.nanoTime(), Duration.ofSeconds(config.timeoutSeconds()).toNanos());
            WindowsJobProcess.CommandResult terminal = child.await(Duration.ofSeconds(config.timeoutSeconds()), lease.deadline(), () -> {
                try {
                    temporaryGuard.check();
                    long now = System.nanoTime();
                    if (now - lastGuard.get() < Duration.ofSeconds(5).toNanos()) return;
                    lastGuard.set(now);
                    guard(config, lease, () -> {
                        temporaryGuard.check();
                        if (System.nanoTime() >= commandDeadline) throw new IOException("Original Maven command deadline expired");
                    });
                } catch (IOException error) { throw new IllegalStateException(error); }
            });
            temporaryGuard.check();
            return terminal;
        }
    }

    private static final String SERVICE_MAIN_ARGUMENT = "-Dquarkus.package.main-class=io.quarkus.runner.GeneratedMain";

    /** Collect independent reactor failures while Maven still returns a failing terminal exit. */
    static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build) {
        return reactorVerifyArguments(config, settings, snapshot, build, System.getenv());
    }

    static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            Map<String, String> environment) {
        return reactorVerifyArguments(config, settings, snapshot, build, environment, config.workRoot().resolve("scratch"));
    }

    private static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            Map<String, String> environment, Path temporary) {
        return reactorVerifyArguments(config, settings, snapshot, build, environment, temporary, true);
    }

    private static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            Map<String, String> environment, Path temporary, boolean consumeTestInputs) {
        java.util.Optional<FormalReleaseTestInputs.Recorded> formal = java.util.Optional.empty();
        if (consumeTestInputs && FormalReleaseTestInputs.selected(snapshot)) try {
            formal = java.util.Optional.of(FormalReleaseTestInputs.fromEnvironment(environment,
                    WindowsJobProcess.currentMachineId(), config.sourceRoot().toString()));
        } catch (IOException invalid) {
            throw new IllegalArgumentException("Selected formal fixture inputs required", invalid);
        }
        java.util.Optional<LobbyVerifyTestInputs.Recorded> lobby = java.util.Optional.empty();
        if (consumeTestInputs && config.targetKind() == TargetKind.BUILD_TOOLS_RUNTIME
                && config.sourceLimitProfile() == SourceLimitProfile.STANDARD_8_MIB
                && LobbyVerifyTestInputs.selected(snapshot)) try {
            lobby = java.util.Optional.of(LobbyVerifyTestInputs.fromEnvironment(environment, WindowsJobProcess.currentMachineId()));
        } catch (IOException invalid) {
            throw new IllegalArgumentException("Selected pinned lobby fixture inputs required", invalid);
        }
        String python = environment.get("XAR_ORACLE_PYTHON");
        if (python == null || python.isBlank() || !Path.of(python).isAbsolute()
                || python.chars().anyMatch(Character::isISOControl)) {
            throw new IllegalArgumentException("Explicit absolute XAR_ORACLE_PYTHON from the selected bootstrap plan required");
        }
        FullParityOracleBindings.SelectedBindings bindings = consumeTestInputs && config.sourceLimitProfile().fullParity()
                ? FullParityOracleBindings.fromEnvironment(config.sourceLimitProfile(), environment, snapshot) : null;
        return reactorVerifyArguments(config, settings, snapshot, build,
                bindings == null ? python : bindings.python(), bindings, temporary, formal, lobby);
    }

    static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            String python, FullParityOracleBindings.SelectedBindings bindings) {
        return reactorVerifyArguments(config, settings, snapshot, build, python, bindings, config.workRoot().resolve("scratch"));
    }

    private static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            String python, FullParityOracleBindings.SelectedBindings bindings, Path temporary) {
        return reactorVerifyArguments(config, settings, snapshot, build, python, bindings, temporary, java.util.Optional.empty());
    }

    private static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            String python, FullParityOracleBindings.SelectedBindings bindings, Path temporary,
            java.util.Optional<FormalReleaseTestInputs.Recorded> formal) {
        return reactorVerifyArguments(config, settings, snapshot, build, python, bindings, temporary, formal, java.util.Optional.empty());
    }

    private static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            String python, FullParityOracleBindings.SelectedBindings bindings, Path temporary,
            java.util.Optional<FormalReleaseTestInputs.Recorded> formal, java.util.Optional<LobbyVerifyTestInputs.Recorded> lobby) {
        // This sole complete producer owns ROOT_PYTHON; bindings contribute only the role fragment.
        if (bindings != null && !Path.of(python).equals(Path.of(bindings.python())))
            throw new IllegalArgumentException("Complete Maven invocation must bind one interpreter across Root context and original consumers");
        List<String> arguments = new ArrayList<>(List.of("--fail-at-end", "-B", "-ntp", "-e", "-U",
                "-s", settings.toString(), "-gs", settings.toString(), "-f", snapshot.resolve("pom.xml").toString(),
                "-Dmaven.repo.local=" + config.workRoot().resolve("m2"), "-Dck3.build.root=" + build,
                "-Dxar.rootContext.testRoot=" + build.resolve("root-context-provider-test"),
                "-Dxar.rootContext.pythonExecutable=" + python,
                "-Dxar.g2.http.evidence-dir=" + build.resolve("g2-http-evidence"),
                "-Dxar.scratch=" + build.resolve("integration-test-scratch"),
                "-Djava.io.tmpdir=" + temporary, "-DargLine=-Xms32m -Xmx256m", "verify"));
        if (bindings instanceof FullParityCurrentBindings.Bindings current) current.requireCompiledRoot(snapshot);
        if (config.targetKind() == TargetKind.SERVICE_FAST_JAR)
            arguments.add(arguments.size() - 1, SERVICE_MAIN_ARGUMENT);
        if (bindings != null) arguments.addAll(arguments.size() - 1, bindings.mavenArguments());
        formal.ifPresent(value -> arguments.addAll(arguments.size() - 1, value.mavenArguments()));
        lobby.ifPresent(value -> arguments.addAll(arguments.size() - 1, value.mavenArguments()));
        return List.copyOf(arguments);
    }

    static List<String> reactorCaptureArguments(Config config, Path settings, Path snapshot, Path build) {
        return reactorCaptureArguments(config, settings, snapshot, build, System.getenv());
    }

    static List<String> reactorCaptureArguments(Config config, Path settings, Path snapshot, Path build,
            Map<String, String> environment) {
        return captureArguments(reactorVerifyArguments(config, settings, snapshot, build, environment,
                config.workRoot().resolve("scratch"), false));
    }

    private enum CaptureCommandPolicy {
        LEGACY_PACKAGE_TEST_COMPILE, COMPILE_ONLY_WITHOUT_TEST_INPUTS;
        String argument() { return "-Dxar.control.capture.commandPolicy=" + name(); }
    }

    private static List<String> captureArguments(List<String> verifyArguments) {
        return captureArguments(verifyArguments, CaptureCommandPolicy.COMPILE_ONLY_WITHOUT_TEST_INPUTS);
    }

    private static List<String> captureArguments(List<String> verifyArguments, CaptureCommandPolicy policy) {
        List<String> args = new ArrayList<>(verifyArguments);
        if (!args.removeLast().equals("verify")) throw new IllegalStateException("Exact existing verify argument contract required");
        if (policy == CaptureCommandPolicy.COMPILE_ONLY_WITHOUT_TEST_INPUTS) args.add(policy.argument());
        args.add("-Dmaven.test.skip=false"); args.add("-DskipTests=true"); args.add("package");
        return List.copyOf(args);
    }

    /**
     * Reconstructs the exact completed command from its recorded invocation, independent of current
     * environment or execution authority. The caller also verifies the immutable command-file bytes.
     */
    static List<String> completedCaptureArguments(Config config, Path settings, Path snapshot, Path build,
            List<String> recordedArguments) throws IOException {
        return completedCaptureArguments(config, settings, snapshot, build, recordedArguments, config.workRoot().resolve("scratch"));
    }

    static List<String> completedCaptureArguments(Config config, Path settings, Path snapshot, Path build,
            List<String> recordedArguments, FileRef releaseRef, Instant completed) throws IOException {
        return completedCaptureArguments(config, settings, snapshot, build, recordedArguments, completedTemporaryRoot(config, releaseRef, completed));
    }

    static List<String> completedCaptureArguments(Config config, Path settings, Path snapshot, Path build,
            List<String> recordedArguments, FileRef releaseRef, Instant completed, FileRef accountingRef) throws IOException {
        return completedCaptureArguments(config, settings, snapshot, build, recordedArguments,
                completedTemporaryRoot(config, releaseRef, completed, accountingRef));
    }

    private static List<String> completedCaptureArguments(Config config, Path settings, Path snapshot, Path build,
            List<String> recordedArguments, Path temporary) throws IOException {
        final String property = "-Dxar.rootContext.pythonExecutable=";
        List<String> selected = recordedArguments.stream().filter(arg -> arg.startsWith(property)).toList();
        if (selected.size() != 1) throw new IOException("Exactly one recorded capture Python argument required");
        final List<String> expected;
        try {
            if (recordedArguments.contains(CaptureCommandPolicy.COMPILE_ONLY_WITHOUT_TEST_INPUTS.argument())) {
                expected = captureArguments(reactorVerifyArguments(config, settings, snapshot, build,
                        Map.of("XAR_ORACLE_PYTHON", selected.getFirst().substring(property.length())), temporary, false));
            } else if (config.sourceLimitProfile().fullParity()) {
                FullParityOracleBindings.SelectedBindings bindings = FullParityOracleBindings.fromRecordedArguments(config.sourceLimitProfile(), recordedArguments);
                expected = captureArguments(reactorVerifyArguments(config, settings, snapshot, build, bindings.python(), bindings, temporary),
                        CaptureCommandPolicy.LEGACY_PACKAGE_TEST_COMPILE);
            } else {
                expected = captureArguments(reactorVerifyArguments(config, settings, snapshot, build,
                        Map.of("XAR_ORACLE_PYTHON", selected.getFirst().substring(property.length())), temporary, false),
                        CaptureCommandPolicy.LEGACY_PACKAGE_TEST_COMPILE);
            }
        } catch (IllegalArgumentException error) {
            throw new IOException("Recorded absolute capture Python argument invalid", error);
        }
        return completedServiceMainArguments(config.targetKind(), expected, recordedArguments);
    }

    /**
     * Completed DATA only: retain exact commands recorded before explicit SERVICE main selection.
     * This method never chooses a command for execution or grants an old jar service qualification.
     */
    static List<String> completedServiceMainArguments(TargetKind target, List<String> producedArguments,
            List<String> recordedArguments) throws IOException {
        List<String> selectors = recordedArguments.stream()
                .filter(argument -> argument.startsWith("-Dquarkus.package.main-class")).toList();
        List<String> expected = new ArrayList<>(producedArguments);
        if (target == TargetKind.SERVICE_FAST_JAR && selectors.isEmpty()) {
            if (!expected.remove(SERVICE_MAIN_ARGUMENT))
                throw new IOException("Current SERVICE producer must select its explicit main");
        } else if (!selectors.isEmpty() && (target != TargetKind.SERVICE_FAST_JAR
                || selectors.size() != 1 || !selectors.getFirst().equals(SERVICE_MAIN_ARGUMENT))) {
            throw new IOException("Exactly one framework HTTP main selector is allowed only for SERVICE commands");
        }
        if (!expected.equals(recordedArguments))
            throw new IOException("Completed Maven arguments differ from the exact recorded command");
        return List.copyOf(expected);
    }

    /** An actual creator's continuously held private directory. It grants no runtime or source qualification. */
    public static final class PreparedTemporaryRoot implements AutoCloseable {
        private final Path root, parent;
        private final FileRef capacity;
        private final CiBootstrap.IoGuard active;
        private final InventoryObserver observer;
        private final com.sun.jna.platform.win32.WinNT.HANDLE parentHandle, childHandle;
        private final String parentIdentity, childIdentity;
        private boolean closed;
        private PreparedTemporaryRoot(Path root, FileRef capacity, CiBootstrap.IoGuard active, InventoryObserver observer,
                com.sun.jna.platform.win32.WinNT.HANDLE parentHandle, String parentIdentity,
                com.sun.jna.platform.win32.WinNT.HANDLE childHandle, String childIdentity) {
            this.root = root; this.parent = root.getParent(); this.capacity = capacity; this.active = active; this.observer = observer;
            this.parentHandle = parentHandle; this.parentIdentity = parentIdentity;
            this.childHandle = childHandle; this.childIdentity = childIdentity;
        }
        public Path root() { return root; }
        public synchronized void requireCurrent() throws IOException {
            if (closed) throw new IOException("Private temporary creator scope is closed");
            active.check(); capacity.verify();
            if (childHandle != null) {
                SharedSourceFiles.plainAncestors(root);
                if (!sampleHeldAccountingEntry(parentHandle, parent, true, true, active, observer).identityKey().equals(parentIdentity)
                        || !accountingEntry(parent, true, true, active, observer).identityKey().equals(parentIdentity)
                        || !sampleHeldAccountingEntry(childHandle, root, true, true, active, observer).identityKey().equals(childIdentity)
                        || !accountingEntry(root, true, true, active, observer).identityKey().equals(childIdentity))
                    throw new IOException("Actual private temporary parent/child identity changed");
            }
            active.check();
        }
        @Override public synchronized void close() throws IOException {
            if (closed) return; closed = true; IOException failure = null;
            if (childHandle != null && !com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(childHandle))
                failure = new IOException("Private temporary child close failed");
            if (parentHandle != null && !com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(parentHandle)) {
                IOException parentFailure = new IOException("Private temporary parent close failed");
                if (failure == null) failure = parentFailure; else failure.addSuppressed(parentFailure);
            }
            if (failure != null) throw failure;
        }
    }

    /** Same actual pre-guard entry used by builds and compiler consumers. No arbitrary parent is created. */
    public static PreparedTemporaryRoot prepareWorkpackageTemporaryRoot(Config config, CiBootstrap.IoGuard active) throws IOException {
        return prepareWorkpackageTemporaryRoot(config, active, path -> {});
    }

    static PreparedTemporaryRoot prepareWorkpackageTemporaryRoot(Config config, CiBootstrap.IoGuard active,
            InventoryObserver observer) throws IOException {
        Objects.requireNonNull(config); Objects.requireNonNull(active); Objects.requireNonNull(observer); active.check();
        return prepareWorkpackageTemporaryRoot(config, readLease(config, WindowsJobProcess.currentMachineId()), active, observer);
    }

    private static com.sun.jna.platform.win32.WinNT.HANDLE holdTemporaryDirectory(Path path,
            CiBootstrap.IoGuard active, InventoryObserver observer) throws IOException {
        SharedSourceFiles.plainAncestors(path);
        var handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path),
                0x81, 3, null, 3, 0x00200000 | 0x02000000, null);
        if (com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle))
            throw new IOException("Private temporary custody open Win32=" + com.sun.jna.Native.getLastError());
        try { sampleHeldAccountingEntry(handle, path, true, true, active, observer); return handle; }
        catch (IOException failure) { if (!com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle))
            failure.addSuppressed(new IOException("Rejected temporary handle close failed")); throw failure; }
    }

    private static PreparedTemporaryRoot prepareWorkpackageTemporaryRoot(Config config, Lease lease, CiBootstrap.IoGuard active) throws IOException {
        return prepareWorkpackageTemporaryRoot(config, lease, active, path -> {});
    }

    private static PreparedTemporaryRoot prepareWorkpackageTemporaryRoot(Config config, Lease lease,
            CiBootstrap.IoGuard active, InventoryObserver observer) throws IOException {
        CiBootstrap.IoGuard checked = () -> {
            active.check();
            if (Thread.currentThread().isInterrupted() || !Instant.now().isBefore(lease.deadline()))
                throw new IOException("Temporary preparation deadline/interruption");
        };
        FileRef release = lease.releaseRef() == null ? FileRef.measure(config.capacityRelease()) : lease.releaseRef();
        release.verify(); checked.check(); Path root = temporaryRoot(config, lease);
        if (lease.attemptAuthority() == null)
            return new PreparedTemporaryRoot(root, release, checked, observer, null, null, null, null);
        Path expected = config.workRoot().resolve("scratch/" + config.attempt() + "-tmp");
        if (!root.equals(expected) || !root.isAbsolute() || !root.normalize().equals(root))
            throw new IOException("Only the exact admitted private temporary child may be created");
        Path parent = root.getParent(); SharedSourceFiles.plainAncestors(parent);
        if (!Files.isDirectory(parent, LinkOption.NOFOLLOW_LINKS) || !parent.toRealPath().equals(parent))
            throw new IOException("Original plain private temporary parent must already exist");
        if (Files.exists(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Fresh private temporary attempt already exists");
        var parentHandle = holdTemporaryDirectory(parent, checked, observer);
        com.sun.jna.platform.win32.WinNT.HANDLE childHandle = null; PreparedTemporaryRoot prepared = null;
        boolean retained = false; Throwable primary = null;
        try {
            String parentIdentity = sampleHeldAccountingEntry(parentHandle, parent, true, true, checked, observer).identityKey();
            WorkpackageAccounting before = accountWorkpackage(config, checked, false);
            if (!before.capacityReleaseRef().equals(release)
                    || before.logicalBytesByScope().get("private_tmp") != 0
                    || before.nativeAllocatedBytesByScope().get("private_tmp") != 0)
                throw new IOException("Fresh temporary preflight crossed its original release or absent child");
            // financial18 currently admits this actual allocation unit only. Pending charges are upper bounds, not measurements.
            requireAccountingAllocationUnit(root.getRoot(), 4096);
            requirePendingAttempt(before, lease.attemptAuthority(), "private_tmp", 4096);
            checked.check(); release.verify(); SharedSourceFiles.plainAncestors(root);
            Files.createDirectory(root); // CREATE_NEW semantics; never mkdirs, overwrite, adopt, or implicit replay.
            childHandle = holdTemporaryDirectory(root, checked, observer);
            String childIdentity = sampleHeldAccountingEntry(childHandle, root, true, true, checked, observer).identityKey();
            prepared = new PreparedTemporaryRoot(root, release, checked, observer, parentHandle, parentIdentity, childHandle, childIdentity);
            prepared.requireCurrent();
            WorkpackageAccounting after = accountWorkpackage(config, checked);
            if (!after.capacityReleaseRef().equals(release)) throw new IOException("Temporary postguard crossed its original release");
            prepared.requireCurrent(); retained = true; return prepared;
        } catch (IOException | RuntimeException | Error failure) { primary = failure; throw failure;
        } finally {
            if (!retained) try {
                if (prepared != null) prepared.close();
                else {
                    IOException failure = null;
                    if (childHandle != null && !com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(childHandle)) failure = new IOException("Failed temporary child close");
                    if (!com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(parentHandle)) {
                        IOException parentFailure = new IOException("Failed temporary parent close");
                        if (failure == null) failure = parentFailure; else failure.addSuppressed(parentFailure);
                    }
                    if (failure != null) throw failure;
                }
            } catch (IOException closeFailure) {
                if (primary != null) primary.addSuppressed(closeFailure); else throw closeFailure;
            }
        }
    }

    private static Path temporaryRoot(Config config, Lease lease) {
        return lease.attemptAuthority() == null ? config.workRoot().resolve("scratch") : Path.of(lease.attemptAuthority().measuredRoots().get("private_tmp"));
    }

    /** Live actual issuer route. Historical metadata overloads above retain the original shared scratch contract. */
    static List<String> releasedReactorVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            Map<String, String> environment, Instant authorityAt) throws IOException {
        Lease lease = readLeaseAt(config, WindowsJobProcess.currentMachineId(), authorityAt);
        return reactorVerifyArguments(config, settings, snapshot, build, environment, temporaryRoot(config, lease));
    }

    private static Lease readCompletedLeaseAt(Config config, String machine, Instant completed,
            FileRef releaseRef, FileRef accountingRef) throws IOException {
        requireExactPath(releaseRef, config.capacityRelease());
        JsonNode original = object(JSON.readTree(exactAccountingBytes(releaseRef, 128 << 10)));
        if (text(original, "schema").equals(ATTEMPT_RELEASE_SCHEMA)) {
            AttemptCapacityRelease release = JSON.treeToValue(original, AttemptCapacityRelease.class);
            if (accountingRef != null) requireExactPath(accountingRef, config.workRoot().resolve("logs/build-" + config.attempt() + "-accounting.json"));
            return readAttemptLease(config, machine, release, completed, completedAccountingSources(accountingRef, releaseRef, release));
        }
        if (accountingRef != null) throw new IOException("Historical full-part lease cannot consume attempt source snapshots");
        return readLeaseAt(config, machine, completed);
    }

    private static Path completedTemporaryRoot(Config config, FileRef releaseRef, Instant completed) throws IOException {
        return completedTemporaryRoot(config, releaseRef, completed, null);
    }

    private static Path completedTemporaryRoot(Config config, FileRef releaseRef, Instant completed, FileRef accountingRef) throws IOException {
        requireExactPath(releaseRef, config.capacityRelease());
        JsonNode original = object(JSON.readTree(exactAccountingBytes(releaseRef, 128 << 10))); String schema = text(original, "schema");
        if (schema.equals(ATTEMPT_RELEASE_SCHEMA)) {
            Lease lease = readCompletedLeaseAt(config, WindowsJobProcess.currentMachineId(), completed, releaseRef, accountingRef);
            releaseRef.verify(); return temporaryRoot(config, lease);
        }
        if (accountingRef != null || (!schema.equals("xar.java-phase1.manual-capacity-release/v1") && !schema.equals("xar.java-control.capacity-release/v1")))
            throw new IOException("Unknown original completed TMP contract");
        releaseRef.verify(); return config.workRoot().resolve("scratch");
    }

    static List<String> completedVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            String python, FullParityOracleBindings.SelectedBindings bindings, FileRef releaseRef, Instant completed) throws IOException {
        return completedVerifyArguments(config, settings, snapshot, build, python, bindings, releaseRef, completed,
                java.util.Optional.empty());
    }

    static List<String> completedVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            String python, FullParityOracleBindings.SelectedBindings bindings, FileRef releaseRef, Instant completed,
            java.util.Optional<FormalReleaseTestInputs.Recorded> formal) throws IOException {
        java.util.Objects.requireNonNull(formal);
        if (formal.isPresent()) FormalReleaseTestInputs.requireRecordedInputs(formal.orElseThrow(),
                WindowsJobProcess.currentMachineId(), config.sourceRoot().toString());
        return completedVerifyArguments(config, settings, snapshot, build, python, bindings, releaseRef, completed, formal,
                java.util.Optional.empty());
    }

    static List<String> completedVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            String python, FullParityOracleBindings.SelectedBindings bindings, FileRef releaseRef, Instant completed,
            java.util.Optional<FormalReleaseTestInputs.Recorded> formal,
            java.util.Optional<LobbyVerifyTestInputs.Recorded> lobby) throws IOException {
        return completedVerifyArguments(config, settings, snapshot, build, python, bindings, releaseRef, completed, formal, lobby, null);
    }

    static List<String> completedVerifyArguments(Config config, Path settings, Path snapshot, Path build,
            String python, FullParityOracleBindings.SelectedBindings bindings, FileRef releaseRef, Instant completed,
            java.util.Optional<FormalReleaseTestInputs.Recorded> formal,
            java.util.Optional<LobbyVerifyTestInputs.Recorded> lobby, FileRef accountingRef) throws IOException {
        Objects.requireNonNull(formal); Objects.requireNonNull(lobby);
        if (formal.isPresent()) FormalReleaseTestInputs.requireRecordedInputs(formal.orElseThrow(),
                WindowsJobProcess.currentMachineId(), config.sourceRoot().toString());
        if (lobby.isPresent()) LobbyVerifyTestInputs.requireInputs(lobby.orElseThrow(), WindowsJobProcess.currentMachineId(), completed);
        return reactorVerifyArguments(config, settings, snapshot, build, python, bindings,
                completedTemporaryRoot(config, releaseRef, completed, accountingRef), formal, lobby);
    }

    static String capacityOwnerTask(FileRef releaseRef) throws IOException {
        JsonNode release = object(JSON.readTree(exactAccountingBytes(releaseRef, 128 << 10))); String schema = text(release, "schema");
        if (schema.equals(ATTEMPT_RELEASE_SCHEMA) || schema.equals("xar.java-phase1.manual-capacity-release/v1")) return text(release, "single_Maven_writer");
        if (schema.equals("xar.java-control.capacity-release/v1")) return text(release, "owner_task");
        throw new IOException("Unknown original capacity owner schema");
    }

    /** All compiler-created test binaries must attest to one actual compiler input in this immutable module. */
    static TestCompilationManifest collectTestCompilation(String machine, Path snapshot, Path build,
            List<FileRef> compiledSource) throws IOException {
        List<ModuleTestCompilation> modules = new ArrayList<>();
        List<NotRunTestCompilation> tests = new ArrayList<>();
        List<FileRef> poms = compiledSource.stream().filter(ref -> Path.of(ref.path()).getFileName().toString().equals("pom.xml")).toList();
        int totalClasses = 0;
        for (FileRef pom : poms) {
            Path module = Path.of(pom.path()).getParent();
            Path sourceBase = module.resolve("src/test/java");
            List<FileRef> sources = compiledSource.stream().filter(ref -> Path.of(ref.path()).startsWith(sourceBase)
                    && ref.path().endsWith(".java")).sorted(Comparator.comparing(FileRef::path)).toList();
            if (sources.isEmpty()) continue;
            String artifact = sourceArtifactId(Path.of(pom.path()));
            Path output = build.resolve(artifact).resolve("test-classes");
            Path status = build.resolve(artifact).resolve("maven-status/maven-compiler-plugin/testCompile/default-testCompile");
            FileRef inputs = FileRef.measure(status.resolve("inputFiles.lst"));
            FileRef created = FileRef.measure(status.resolve("createdFiles.lst"));
            Set<Path> inputPaths = new HashSet<>();
            for (String line : compilerLines(inputs)) {
                Path input = Path.of(line).toAbsolutePath().normalize();
                if (!Path.of(line).isAbsolute() || !input.startsWith(sourceBase) || !inputPaths.add(input)) throw new IOException("Compiler input is outside its exact module test sources or repeated");
            }
            Set<Path> expectedSources = new HashSet<>(); for (FileRef source : sources) expectedSources.add(Path.of(source.path()).toAbsolutePath().normalize());
            if (!inputPaths.equals(expectedSources)) throw new IOException("Maven testCompile did not report every pinned module test source");
            Set<Path> createdPaths = new HashSet<>();
            for (String line : compilerLines(created)) {
                Path relative = Path.of(line);
                Path file = output.resolve(relative).normalize();
                if (relative.isAbsolute() || !file.startsWith(output) || !line.endsWith(".class") || !createdPaths.add(file)) throw new IOException("Compiler-created class escaped or repeated");
            }
            if (createdPaths.isEmpty()) throw new IOException("Actual compiler-created test classes missing");
            List<FileRef> classes = new ArrayList<>(); AtomicLong classBytes = new AtomicLong();
            walk(output, false, 10000, (file, active) -> {
                if (!file.getFileName().toString().endsWith(".class")) return;
                FileRef ref = FileRef.measure(file); classes.add(ref); classBytes.set(Math.addExact(classBytes.get(), ref.bytes()));
                if (classes.size() > 4096 || classBytes.get() > (64L << 20)) throw new IOException("Finite compiled test-class extent exceeded");
            });
            Set<Path> actualClasses = new HashSet<>();for (FileRef file : classes) actualClasses.add(Path.of(file.path()).toAbsolutePath().normalize());
            if (!createdPaths.equals(actualClasses)) throw new IOException("Actual test-class directory differs from Maven createdFiles inventory");
            totalClasses = Math.addExact(totalClasses, classes.size());if (totalClasses > 4096) throw new IOException("Compiled test-class cohort exceeded");
            Map<Path,List<FileRef>> bySource = new HashMap<>();
            for (FileRef file : classes) {
                var origin = CompiledClassProvenance.attest(output, file, module, CompiledClassProvenance.SourceSet.TEST, compiledSource);
                Path sourcePath = Path.of(origin.sourceRef().path()).toAbsolutePath().normalize();
                if (!inputPaths.contains(sourcePath)) throw new IOException("Class SourceFile was not an actual Maven compiler input");
                bySource.computeIfAbsent(sourcePath, ignored -> new ArrayList<>()).add(file);
            }
            for (FileRef source : sources) {
                List<FileRef> binaries = bySource.get(Path.of(source.path()).toAbsolutePath().normalize());
                if (binaries == null || binaries.isEmpty()) throw new IOException("Pinned test source has no compiler-created SourceFile binary");
                binaries.sort(Comparator.comparing(FileRef::path)); source.verify();
                tests.add(new NotRunTestCompilation(source, binaries, CaptureTestState.NOT_RUN));
            }
            inputs.verify(); created.verify(); pom.verify();
            modules.add(new ModuleTestCompilation(pom, output.toRealPath().toString(), inputs, created));
        }
        modules.sort(Comparator.comparing(item -> item.modulePomRef().path()));
        tests.sort(Comparator.comparing(item -> item.sourceRef().path()));
        return new TestCompilationManifest(TEST_COMPILATION_SCHEMA, machine, Instant.now().toString(), CaptureTestState.NOT_RUN, modules, tests);
    }

    private static List<String> compilerLines(FileRef reference) throws IOException {
        reference.verify(); byte[] raw = readLimited(Path.of(reference.path()), 1 << 20);
        String text;
        try { text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(raw)).toString(); }
        catch (java.nio.charset.CharacterCodingException error) { throw new IOException("Compiler inventory must be UTF-8", error); }
        List<String> lines = text.lines().toList();
        if (lines.isEmpty() || lines.size() > 4096 || lines.stream().anyMatch(line -> line.isBlank() || line.length() > 4096
                || line.codePoints().anyMatch(point -> point < 32 || point == 127))) throw new IOException("Bounded complete compiler inventory lines required");
        reference.verify(); return lines;
    }

    private static String sourceArtifactId(Path pom) throws IOException {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance(); factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            String artifact = directText(factory.newDocumentBuilder().parse(pom.toFile()).getDocumentElement(), "artifactId");
            if (!artifact.matches("[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")) throw new IOException("Exact source module artifact ID required");
            return artifact;
        } catch (ParserConfigurationException | SAXException error) { throw new IOException("Actual module POM cannot be read", error); }
    }

    static void writeMavenBatch(Path batch, Path explicitOverride, List<String> args) throws IOException {
        if (MavenArgumentFile.required(explicitOverride, args)) throw new IOException("Long Maven argv requires its compiler snapshot argument artifact");
        Files.writeString(batch, mavenBatchText(explicitOverride, args), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }

    static String mavenExecutionBatchText(Path explicitOverride, List<String> args, Path snapshot) throws IOException {
        return MavenArgumentFile.batchText(explicitOverride, args, snapshot);
    }

    static String mavenBatchText(Path explicitOverride, List<String> args) {
        List<String> words = new ArrayList<>(); words.add(explicitOverride == null ? "mvn" : explicitOverride.toString()); words.addAll(args);
        for (String word : words) {
            if (word.isEmpty() || word.matches(".*[\\r\\n\"&|<>^%!].*")) throw new IllegalArgumentException("Unsafe CMD token");
        }
        String command = words.stream().map(word -> word.contains(" ") ? "\"" + word + "\"" : word)
                .reduce((a, b) -> a + " " + b).orElseThrow();
        return "@echo off\r\ncall " + command + "\r\nexit /b %errorlevel%\r\n";
    }

    static MavenToolchain measuredMavenToolchain(Path explicitOverride, String actualVersionOutput, String minimumVersion) throws IOException {
        var home = java.util.regex.Pattern.compile("(?m)^Maven home: ([^\\r\\n]+)$").matcher(actualVersionOutput);
        if (!home.find()) throw new IOException("Actual Maven home was not reported");
        Path actualHome = Path.of(home.group(1).strip()).toRealPath();
        if (home.find()) throw new IOException("Ambiguous actual Maven home");
        var version = java.util.regex.Pattern.compile("(?m)^Apache Maven ([0-9]+\\.[0-9]+\\.[0-9]+)(?: [^\\r\\n]*)?$").matcher(actualVersionOutput);
        if (!version.find() || !mavenVersionAtLeast(version.group(1), minimumVersion)) throw new IOException("Actual Maven is below the required stable minimum");
        String reportedVersion = version.group(1);
        if (version.find()) throw new IOException("Ambiguous actual Maven version");
        FileRef entry = FileRef.measure(actualHome.resolve("bin/mvn.cmd"));
        FileRef override = explicitOverride == null ? null : FileRef.measure(explicitOverride);
        return new MavenToolchain(explicitOverride == null ? MavenSelection.DEFAULT_COMMAND : MavenSelection.EXPLICIT_OVERRIDE,
                override == null ? "mvn" : override.path(), actualHome.toString(), reportedVersion, minimumVersion, entry, override);
    }

    public static boolean mavenVersionAtLeast(String actual, String minimum) {
        if (actual == null || minimum == null || !actual.matches("[0-9]+\\.[0-9]+\\.[0-9]+")
                || !minimum.matches("[0-9]+\\.[0-9]+\\.[0-9]+") || actual.length() > 64 || minimum.length() > 64) return false;
        String[] left = actual.split("\\."); String[] right = minimum.split("\\.");
        for (int i = 0; i < 3; i++) {
            int comparison = new java.math.BigInteger(left[i]).compareTo(new java.math.BigInteger(right[i]));
            if (comparison != 0) return comparison > 0;
        }
        return true;
    }

    private static Map<String, String> buildEnvironment(Config config, Path snapshot, Lease lease) throws IOException {
        Map<String, String> env = new TreeInsensitiveMap(System.getenv()).values();
        CanonicalOracleEnvironment.require(env);
        for (String key : List.of("MAVEN_ARGS", "MAVEN_DEBUG_OPTS", "MAVEN_BATCH_ECHO", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "JDK_JAVA_OPTIONS")) env.remove(key);
        String scratch = lease.attemptAuthority() == null ? config.workRoot().resolve("scratch").toString() : lease.attemptAuthority().measuredRoots().get("private_tmp");
        long heapMiB = Math.min(768, lease.mavenHeapBytes() / (1024 * 1024));
        if (heapMiB < 64) throw new IllegalArgumentException("Released Maven heap is insufficient");
        String jvm = "-Xms32m -Xmx" + heapMiB + "m -XX:MaxMetaspaceSize=256m -XX:ReservedCodeCacheSize=64m -XX:MaxDirectMemorySize=128m -Xss512k -Djava.io.tmpdir=" + scratch + " -Djna.tmpdir=" + scratch;
        env.put("JAVA_HOME", config.javaHome().toString()); env.put("JAVA_TOOL_OPTIONS", jvm); env.put("MAVEN_OPTS", jvm);
        env.put("MAVEN_SKIP_RC", "1"); env.put("MAVEN_BASEDIR", snapshot.toString());
        env.put("MAVEN_USER_HOME", config.workRoot().resolve("m2").toString()); env.put("TEMP", scratch); env.put("TMP", scratch);
        return Map.copyOf(env);
    }
    private record TreeInsensitiveMap(Map<String, String> values) {
        TreeInsensitiveMap { Map<String, String> copy = new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER); copy.putAll(values); values = copy; }
    }

    private static Lease readLease(Config config, String machine) throws IOException {
        return readLeaseAt(config, machine, Instant.now());
    }

    /** The authority instant is captured by the live caller or the already-validated original completion. */
    static Lease readLeaseAt(Config config, String machine, Instant authorityAt) throws IOException {
        Objects.requireNonNull(authorityAt);
        JsonNode data = readObject(config.capacityRelease());
        if (text(data, "schema").equals(ATTEMPT_RELEASE_SCHEMA)) return readAttemptLease(config, machine, JSON.treeToValue(data, AttemptCapacityRelease.class), authorityAt);
        if (text(data, "schema").equals("xar.java-control.capacity-release/v1")) {
            return readTypedLease(config, machine, JSON.treeToValue(data, CapacityRelease.class), authorityAt);
        }
        if (!text(data, "schema").equals("xar.java-phase1.manual-capacity-release/v1")
                || !text(data, "status").equals("RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE")
                || !text(data, "machine_id").equals(machine) || !text(data, "single_Maven_writer").equals(config.ownerTask())) {
            throw new IOException("Capacity release schema, machine, state or writer mismatch");
        }
        Instant deadline = Instant.parse(text(data, "review_at_utc"));
        if (!authorityAt.isBefore(deadline)) throw new IOException("Capacity release expired");
        JsonNode approved = data.get("approved_output_roots");
        if (approved == null || !approved.isArray() || approved.isEmpty() || approved.size() > 16) throw new IOException("Approved roots are unavailable");
        boolean allowed = false, sourceAllowed = false;
        for (JsonNode root : approved) {
            if (!root.isTextual()) throw new IOException("Root must be text");
            if (config.workRoot().toRealPath().startsWith(Path.of(root.textValue()).toRealPath())) allowed = true;
            if (config.sourceRoot().toRealPath().startsWith(Path.of(root.textValue()).toRealPath())) sourceAllowed = true;
        }
        if (!allowed || !sourceAllowed || config.sourceRoot().startsWith(config.workRoot()) || config.workRoot().startsWith(config.sourceRoot())) throw new IOException("Source and approved work roots must be independent");
        if (!Path.of(text(data, "Maven_repository")).equals(config.workRoot().resolve("m2"))
                || !Path.of(text(data, "build_root")).equals(config.workRoot().resolve("build"))
                || !Path.of(text(data, "temporary_root")).equals(config.workRoot().resolve("scratch"))) throw new IOException("Released path mapping differs");
        JsonNode parts = object(data.get("parts")); Map<String, Long> caps = new LinkedHashMap<>();
        for (String name : List.of("m2", "build", "tools", "scratch", "artifacts")) caps.put(name, positive(parts, name));
        caps.put("logs", positive(parts, "metadata_logs"));
        JsonNode policyRef = object(data.get("policy_ref"));
        new FileRef(text(policyRef, "path"), nonnegative(policyRef, "bytes"), text(policyRef, "sha256")).verify();
        JsonNode policy = readObject(Path.of(text(policyRef, "path")));
        if (!text(policy, "schema").equals("xar-storage-retention-policy-v1")) throw new IOException("Unknown storage policy");
        JsonNode volumes = object(data.get("volumes")); Map<Path, Long> minimum = new HashMap<>();
        for (var field : volumes.properties()) {
            JsonNode volume = object(field.getValue());
            long required = positive(volume, "required_free");
            long calculated = Math.addExact(Math.addExact(positive(volume, "this_write_peak"), nonnegative(volume, "other_unspent_reservations")),
                    Math.addExact(positive(volume, "system_growth_reserve"), positive(volume, "safety_reserve")));
            if (required != calculated) throw new IOException("Capacity formula mismatch");
            if (positive(volume, "current_project_usage_conservative_upper") + positive(volume, "this_write_peak")
                    > positive(volume, "effective_project_quota")) throw new IOException("Project quota exceeded");
            minimum.put(Path.of(field.getKey()), required);
        }
        if (minimum.isEmpty()) throw new IOException("Volume reservations unavailable");
        return new Lease(machine, deadline, Map.copyOf(caps), positive(data, "test_RAM_joint_hard_bytes"), positive(data, "Maven_heap_bytes"), Map.copyOf(minimum), null, null);
    }

    private static Lease readTypedLease(Config config, String machine, CapacityRelease release, Instant authorityAt) throws IOException {
        return readTypedLease(config, machine, release, authorityAt, AccountingSources.live());
    }

    private static Lease readTypedLease(Config config, String machine, CapacityRelease release, Instant authorityAt,
            AccountingSources sources) throws IOException {
        Instant deadline = Instant.parse(release.reviewAtUtc());
        if (!machine.equals(release.machineId()) || !config.ownerTask().equals(release.ownerTask())
                || !authorityAt.isBefore(deadline)) throw new IOException("Capacity machine, writer or deadline rejected");
        boolean work = false, source = false;
        for (String root : release.approvedOutputRoots()) {
            Path approved = Path.of(root).toRealPath();
            work |= config.workRoot().toRealPath().startsWith(approved);
            source |= config.sourceRoot().toRealPath().startsWith(approved);
        }
        if (!work || !source || config.sourceRoot().startsWith(config.workRoot()) || config.workRoot().startsWith(config.sourceRoot())
                || !Path.of(release.temporaryRoot()).equals(config.workRoot().resolve("scratch"))) throw new IOException("Independent approved roots required");
        CiBootstrap.Policy policy = CiBootstrap.readPolicy(sources.read(release.policyRef(), 128 << 10));
        Map<Path, Long> minimum = new HashMap<>();
        for (var field : release.volumes().entrySet()) {
            CiBootstrap.VolumeBudget volume = field.getValue();
            long defaultQuota = Math.min(policy.quotaCeiling(), java.math.BigDecimal.valueOf(volume.totalVolumeBytes()).multiply(policy.quotaVolumeFraction())
                    .setScale(0, java.math.RoundingMode.FLOOR).longValueExact());
            CiBootstrap.QuotaOverride override = release.quotaOverrides().get(field.getKey());
            if (volume.effectiveProjectQuota() != defaultQuota) {
                if (override == null || override.owner() == null || override.owner().isBlank() || !override.task().equals(release.ownerTask())
                        || override.reason() == null || override.reason().isBlank()
                        || override.maxProjectBytes() != volume.effectiveProjectQuota() || !authorityAt.isBefore(Instant.parse(override.reviewAtUtc()))
                        || Instant.parse(override.reviewAtUtc()).isAfter(deadline)
                        || Math.addExact(volume.currentProjectUsageConservativeUpper(), volume.thisWritePeak()) <= defaultQuota) {
                    throw new IOException("Explicit finite owner quota override required only for an insufficient default quota");
                }
                sources.verify(new FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()));
            } else if (override != null) throw new IOException("Unnecessary quota override rejected");
            CiBootstrap.VolumeBudget calculated = CiBootstrap.calculate(policy, volume.totalVolumeBytes(), volume.availableBytes(),
                    volume.thisWritePeak(), volume.otherUnspentReservations(), volume.systemGrowthReserve(), volume.currentProjectUsageConservativeUpper(),
                    override, Instant.parse(release.observedAtUtc()), deadline);
            if (!volume.equals(calculated)) throw new IOException("Shared policy volume calculation mismatch");
            minimum.put(Path.of(field.getKey()), volume.requiredFree());
        }
        Map<String, Long> caps = new LinkedHashMap<>();
        for (String key : List.of("m2", "build", "tools", "scratch", "artifacts")) {
            Long value = release.parts().get(key); if (value == null || value <= 0) throw new IOException("Missing part cap: " + key); caps.put(key, value);
        }
        Long logs = release.parts().get("metadata_logs"); if (logs == null || logs <= 0) throw new IOException("Missing metadata cap"); caps.put("logs", logs);
        return new Lease(machine, deadline, Map.copyOf(caps), release.memoryLimitBytes(), release.mavenHeapBytes(), Map.copyOf(minimum), null, null);
    }

    private static Lease readAttemptLease(Config config, String machine, AttemptCapacityRelease release, Instant authorityAt) throws IOException {
        return readAttemptLease(config, machine, release, authorityAt, AccountingSources.live());
    }

    private static Lease readAttemptLease(Config config, String machine, AttemptCapacityRelease release, Instant authorityAt,
            AccountingSources sources) throws IOException {
        FileRef boundRelease = FileRef.measure(config.capacityRelease());
        if (!release.equals(JSON.readValue(exactAccountingBytes(boundRelease, 128 << 10), AttemptCapacityRelease.class))) throw new IOException("Original release changed before typed admission");
        Lease base = readTypedLease(config, machine, new CapacityRelease("xar.java-control.capacity-release/v1", release.machineId(),
                release.observedAtUtc(), release.reviewAtUtc(), "RELEASED", release.ownerTask(), release.policyRef(),
                release.approvedOutputRoots(), release.temporaryRoot(), release.parts(), release.volumes(), release.quotaOverrides(),
                release.memoryLimitBytes(), release.mavenHeapBytes()), authorityAt, sources);
        AttemptAccountingAuthority authority = release.workpackageAccounting();
        if (!authority.attempt().equals(config.attempt()) || !Path.of(release.mavenRepository()).equals(config.workRoot().resolve("m2"))
                || !Path.of(release.buildRoot()).equals(config.workRoot().resolve("build"))) throw new IOException("Exact attempt/runtime roots required");
        Map<String, String> expected = attemptRoots(config);
        for (var entry : expected.entrySet()) if (!Path.of(entry.getValue()).equals(Path.of(authority.measuredRoots().get(entry.getKey()))))
            throw new IOException("Accounting root differs from the original actual attempt: " + entry.getKey());
        Map<String, String> corresponding = Map.of("source_snapshot", "scratch", "build", "build", "private_tmp", "scratch", "artifacts", "artifacts", "logs", "logs");
        for (String key : ATTEMPT_SCOPES) if (authority.logicalCapsByScope().get(key) > base.caps().get(corresponding.get(key))
                || authority.nativeCapsByScope().get(key) > base.caps().get(corresponding.get(key)))
            throw new IOException("Attempt cap exceeds its retained runtime part reservation: " + key);
        if (authorityAt.isBefore(Instant.parse(release.observedAtUtc()))) throw new IOException("Attempt release has not opened");
        if (Math.addExact(authority.nativeCapsByScope().get("source_snapshot"), authority.nativeCapsByScope().get("private_tmp")) > base.caps().get("scratch")
                || Math.addExact(authority.logicalCapsByScope().get("source_snapshot"), authority.logicalCapsByScope().get("private_tmp")) > base.caps().get("scratch")) throw new IOException("Combined private scratch reservations exceed original runtime budget");
        validateAttemptFinancial(config, release, authorityAt, false, sources);
        return new Lease(base.machineId(), base.deadline(), base.caps(), base.memoryLimitBytes(), base.mavenHeapBytes(), base.minimumFreeByVolume(), authority, boundRelease);
    }

    private static Map<String, String> attemptRoots(Config config) {
        Path root = config.workRoot();
        return Map.of("maven_repository", root.resolve("m2").toString(), "source_snapshot", root.resolve("scratch/source-" + config.attempt()).toString(),
                "build", root.resolve("build/" + config.attempt()).toString(), "private_tmp", root.resolve("scratch/" + config.attempt() + "-tmp").toString(),
                "artifacts", root.resolve("artifacts/" + config.attempt()).toString(), "logs", root.resolve("logs").toString());
    }

    /** Binds decoded bytes to this exact reference, including A-to-B-to-A replacement races. */
    static byte[] exactAccountingBytes(FileRef reference, int maximum) throws IOException {
        if (reference.bytes() < 1 || reference.bytes() > maximum) throw new IOException("Bounded accounting source required");
        byte[] bytes;
        try (InputStream input = Files.newInputStream(Path.of(reference.path()))) { bytes = input.readNBytes(Math.toIntExact(reference.bytes() + 1)); }
        try {
            if (bytes.length != reference.bytes() || !HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)).equals(reference.sha256()))
                throw new IOException("Accounting source bytes changed during exact read");
        } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        reference.verify(); return bytes;
    }

    private static List<VolumeObservation> validateAttemptFinancial(Config config, AttemptCapacityRelease release, Instant authorityAt, boolean observeCurrent) throws IOException {
        return validateAttemptFinancial(config, release, authorityAt, observeCurrent, AccountingSources.live());
    }

    private static List<VolumeObservation> validateAttemptFinancial(Config config, AttemptCapacityRelease release, Instant authorityAt,
            boolean observeCurrent, AccountingSources sources) throws IOException {
        AttemptAccountingAuthority authority = release.workpackageAccounting();
        JsonNode financial = object(JSON.readTree(exactAccountingBytes(authority.financialSourceRef(), 128 << 10)));
        if (!text(financial, "schema").equals("xar.java-phase1.resume56-r3-financial-supplement/v1")
                || !text(financial, "machine_id").equals(release.machineId())
                || !text(financial, "status").equals("RELEASED_EXPLICIT_ROOT_AUTHORIZED_0830_REVIEW_SUCCESSOR_WITHOUT_CAP_INCREASE")
                || !text(financial, "issuer_task").equals("/root/budget_fast_lane")) throw new IOException("Explicit financial18 issuer/machine/status rejected");
        Instant observed = Instant.parse(text(financial, "observed_at_utc")), review = Instant.parse(text(financial, "review_at_utc"));
        if (observed.isAfter(Instant.parse(release.observedAtUtc())) || authorityAt.isBefore(observed) || !authorityAt.isBefore(review)
                || Instant.parse(release.reviewAtUtc()).isAfter(review) || !review.equals(Instant.parse(text(financial, "quota_review_at_utc"))))
            throw new IOException("Accounting financial source is not current for the finite release");
        JsonNode refs = financial.get("old_heads_and_policy_refs");
        if (refs == null || !refs.isArray() || refs.size() != authority.reservationSourceRefs().size()) throw new IOException("All retained reservation sources required");
        List<FileRef> actualRefs = new ArrayList<>();
        for (JsonNode node : refs) actualRefs.add(JSON.treeToValue(node, FileRef.class));
        if (!actualRefs.equals(authority.reservationSourceRefs()) || !actualRefs.contains(release.policyRef())) throw new IOException("Reservation/policy source substitution rejected");
        for (FileRef ref : actualRefs) sources.verify(ref);
        if (!financial.has("current_whole_project_actual_usage_bytes") || !financial.get("current_whole_project_actual_usage_bytes").isNull()) throw new IOException("Financial volume upper is not a whole-project actual inventory");
        if (authority.canonicalM2GrowthReservationBytes() != positive(financial, "shared_canonical_m2_growth_hold_once_bytes")
                || authority.maximumNewNativeBytes() > positive(financial, "whole_R3_cap_after_bytes"))
            throw new IOException("Shared m2 hold must be covered once, and actual attempt must fit whole Native hold");
        JsonNode fresh = object(financial.get("fresh_observations"));
        if (!text(fresh, "machine_id").equals(release.machineId()) || !Instant.parse(text(fresh, "observed_at_utc")).equals(observed)) throw new IOException("Original machine observation mismatch");
        List<VolumeObservation> result = new ArrayList<>();
        for (var entry : release.volumes().entrySet()) {
            Path root = Path.of(entry.getKey()).toRealPath(); String letter = root.toString().substring(0, 1).toUpperCase(Locale.ROOT);
            JsonNode original = object(fresh.get(letter)); JsonNode reserves = object(financial.get("reserves"));
            long holds = positive(financial, letter.equals("D") ? "all_holds_including_current_R3_bytes" : letter + "_other_unspent_holds_bytes");
            long system = positive(reserves, letter + "_system_growth"), safety = positive(reserves, letter + "_safety");
            long required = Math.addExact(holds, Math.addExact(system, safety)); long quota = positive(financial, letter + "_quota_bytes");
            CiBootstrap.VolumeBudget budget = entry.getValue();
            if (budget.requiredFree() != required || budget.totalVolumeBytes() != positive(original, "total") || budget.effectiveProjectQuota() != quota
                    || budget.currentProjectUsageConservativeUpper() != positive(original, "used_upper")) throw new IOException("Release volume does not consume all financial holds/reserves/quota");
            if (observeCurrent) result.add(observeAccountingVolume(root, original, required, quota, holds, system, safety));
        }
        if (release.volumes().keySet().stream().map(Path::of).noneMatch(config.workRoot().getRoot()::equals)) throw new IOException("Actual work volume is not covered");
        return List.copyOf(result);
    }

    private static VolumeObservation observeAccountingVolume(Path root, JsonNode original, long required, long quota, long holds, long system, long safety) throws IOException {
        SharedSourceFiles.NativeFile identity = accountingDirectory(root);
        requireAccountingAllocationUnit(root, positive(original, "actual_cluster_bytes"));
        JsonNode expected = object(original.get("native_root_identity"));
        if (!text(expected, "api").equals("BY_HANDLE_FILE_INFORMATION")
                || !identity.legacyVolumeSerialDecimal().equals(text(expected, "volume_serial_decimal"))
                || !new java.math.BigInteger(identity.legacyFileIdHex(), 16).toString().equals(text(expected, "file_index_decimal")))
            throw new IOException("Original financial volume Native identity changed");
        java.nio.file.FileStore store = Files.getFileStore(root); long total = store.getTotalSpace(), usable = store.getUsableSpace();
        if (total != positive(original, "total")) throw new IOException("Actual volume geometry changed");
        long used = Math.subtractExact(total, usable), upper = Math.max(used, positive(original, "used_upper"));
        VolumeObservation observation = new VolumeObservation(root.toString(), total, usable, used, upper, required, quota, holds, system, safety);
        requireVolumeQuote(observation); return observation;
    }

    private static SharedSourceFiles.NativeFile accountingDirectory(Path path) throws IOException {
        SharedSourceFiles.plainAncestors(path);
        com.sun.jna.platform.win32.WinNT.HANDLE handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(
                path.toString(), 0x80, 7, null, 3, 0x00200000 | 0x02000000, null);
        if (com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("Actual accounting directory open Win32=" + com.sun.jna.Native.getLastError());
        try { return SharedSourceFiles.nativeHeldDirectory(handle); }
        catch (IOException failure) {
            throw new IOException("Strict financial directory decoder rejected: operation=nativeHeldDirectory; path="
                    + path + "; cause=" + failure.getClass().getName() + ": " + failure.getMessage(), failure);
        } finally { if (!com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("Accounting directory close failed: " + path); }
    }

    /** This versioned financial layout declares 4096; other actual units require a new explicit source/layout. */
    private static void requireAccountingAllocationUnit(Path root, long originalUnit) throws IOException {
        var sectors = new com.sun.jna.platform.win32.WinDef.DWORDByReference(); var bytes = new com.sun.jna.platform.win32.WinDef.DWORDByReference();
        var free = new com.sun.jna.platform.win32.WinDef.DWORDByReference(); var total = new com.sun.jna.platform.win32.WinDef.DWORDByReference();
        if (!com.sun.jna.platform.win32.Kernel32.INSTANCE.GetDiskFreeSpace(root.toString(), sectors, bytes, free, total)) throw new IOException("Actual accounting allocation unit unavailable");
        long actual = Math.multiplyExact(sectors.getValue().longValue(), bytes.getValue().longValue());
        if (originalUnit != 4096 || actual != originalUnit) throw new IOException("Actual allocation unit differs from explicit financial18 4096-byte guard");
    }

    static void requireVolumeQuote(VolumeObservation observation) throws IOException {
        if (observation.usableBytes() < observation.requiredFreeBytes()
                || Math.addExact(observation.quotaUsedUpperBytes(), observation.requiredFreeBytes()) > observation.effectiveProjectQuota())
            throw new IOException("Conservative actual volume upper plus all holds/reserves exceeds available/quota");
    }

    private record ScopeUsage(long logicalBytes, long nativeBytes) { }
    private record AccountingPeak(long logicalBytes, long nativeBytes) { }
    private static final Map<FileRef, AccountingPeak> ACCOUNTING_PEAKS = new HashMap<>();

    /** One shared live guard. FULL preserves the historical complete-part inventory. */
    public static WorkpackageAccounting accountWorkpackage(Config config, CiBootstrap.IoGuard active) throws IOException {
        return accountWorkpackage(config, active, true);
    }

    // Only the actual fresh-directory producer may precharge an absent private_tmp; ordinary readers stay strict.
    static WorkpackageAccounting accountWorkpackage(Config config, CiBootstrap.IoGuard active, InventoryObserver observer) throws IOException {
        return accountWorkpackage(config, active, true, Objects.requireNonNull(observer));
    }
    private static WorkpackageAccounting accountWorkpackage(Config config, CiBootstrap.IoGuard active, boolean requirePrivateTemporary) throws IOException {
        return accountWorkpackage(config, active, requirePrivateTemporary, path -> {});
    }
    private static WorkpackageAccounting accountWorkpackage(Config config, CiBootstrap.IoGuard active, boolean requirePrivateTemporary,
            InventoryObserver observer) throws IOException {
        Objects.requireNonNull(config); Objects.requireNonNull(active); active.check();
        FileRef releaseRef = FileRef.measure(config.capacityRelease());
        JsonNode data = object(JSON.readTree(exactAccountingBytes(releaseRef, 128 << 10)));
        String machine = WindowsJobProcess.currentMachineId(); Instant now = Instant.now();
        if (!text(data, "schema").equals(ATTEMPT_RELEASE_SCHEMA)) {
            Lease lease = readLeaseAt(config, machine, now);
            CiBootstrap.IoGuard fullActive = () -> { active.check(); if (!Instant.now().isBefore(lease.deadline())) throw new IOException("Full inventory lease expired"); };
            for (var volume : lease.minimumFreeByVolume().entrySet()) if (Files.getFileStore(volume.getKey()).getUsableSpace() < volume.getValue()) throw new IOException("Current full-inventory volume free space insufficient");
            Map<String, Long> measured = sizes(config.workRoot(), lease.caps(), fullActive, NIO_INVENTORY);
            fullActive.check();
            Map<String, String> roots = new LinkedHashMap<>(); measured.keySet().forEach(key -> roots.put(key, config.workRoot().resolve(key).toString()));
            releaseRef.verify();
            return new WorkpackageAccounting(ACCOUNTING_SCHEMA, AccountingMode.FULL_PART_INVENTORY, releaseRef, machine, now.toString(), roots,
                    measured, RepositoryAccountingState.FULL_PART_MEASURED, measured.get("m2"), measured.get("m2"), 0, Map.of(), 0, List.of());
        }
        AttemptCapacityRelease release = JSON.treeToValue(data, AttemptCapacityRelease.class);
        Lease lease = readAttemptLease(config, machine, release, now); AttemptAccountingAuthority authority = lease.attemptAuthority();
        List<VolumeObservation> volumes = validateAttemptFinancial(config, release, now, true);
        CiBootstrap.IoGuard checked = () -> { active.check(); if (Thread.currentThread().isInterrupted() || !Instant.now().isBefore(lease.deadline())) throw new IOException("Attempt accounting deadline/interruption"); };
        Map<String, Long> logical = new LinkedHashMap<>(), nativeBytes = new LinkedHashMap<>();
        for (String key : ATTEMPT_SCOPES) {
            checked.check(); Path root = Path.of(authority.measuredRoots().get(key));
            ScopeUsage usage = measureAttemptScope(root, key.equals("logs") ? "build-" + config.attempt() : null,
                    key.equals("private_tmp") && requirePrivateTemporary, !key.equals("source_snapshot"), key.equals("private_tmp"), checked, observer);
            if (usage.logicalBytes() > authority.logicalCapsByScope().get(key) || usage.nativeBytes() > authority.nativeCapsByScope().get(key))
                throw new IOException("Actual attempt logical/Native cap exceeded: " + key);
            logical.put(key, usage.logicalBytes()); nativeBytes.put(key, usage.nativeBytes());
        }
        long logicalTotal = exactSum(logical), nativeTotal = exactSum(nativeBytes); AccountingPeak peak;
        synchronized (ACCOUNTING_PEAKS) {
            if (!ACCOUNTING_PEAKS.containsKey(releaseRef) && ACCOUNTING_PEAKS.size() >= 64) throw new IOException("Finite accounting attempt history exhausted");
            AccountingPeak previous = ACCOUNTING_PEAKS.getOrDefault(releaseRef, new AccountingPeak(0, 0));
            peak = new AccountingPeak(Math.max(previous.logicalBytes(), logicalTotal), Math.max(previous.nativeBytes(), nativeTotal));
            ACCOUNTING_PEAKS.put(releaseRef, peak);
        }
        if (peak.logicalBytes() > authority.maximumNewLogicalBytes() || peak.nativeBytes() > authority.maximumNewNativeBytes()) throw new IOException("Actual attempt peak exceeds retained logical/Native reservation");
        releaseRef.verify(); checked.check();
        return new WorkpackageAccounting(ACCOUNTING_SCHEMA, AccountingMode.CONSERVATIVE_VOLUME_ATTEMPT, releaseRef, machine, now.toString(), authority.measuredRoots(),
                logical, RepositoryAccountingState.CONSERVATIVE_VOLUME_COVERAGE, null, null, peak.logicalBytes(), nativeBytes, peak.nativeBytes(), volumes);
    }

    /** Sole live sidecar publication: reserve the selected receipt envelope in both scope and whole domains. */
    static FileRef publishAttemptAccounting(Config config,WorkpackageAccounting accounting,
            AttemptAccountingAuthority authority,CiBootstrap.IoGuard active)throws IOException {
        active.check();
        Lease live = readLeaseAt(config, WindowsJobProcess.currentMachineId(), Instant.now());
        if (!authority.equals(live.attemptAuthority()) || !accounting.capacityReleaseRef().equals(live.releaseRef()))
            throw new IOException("Completed accounting publication requires its original current attempt lease");
        List<RetainedAccountingSource> retained = new ArrayList<>();
        for (FileRef source : authority.reservationSourceRefs()) {
            active.check();
            retained.add(new RetainedAccountingSource(source,
                    java.util.Base64.getEncoder().encodeToString(exactAccountingBytes(source, 128 << 10))));
        }
        CompletedWorkpackageAccounting completed = new CompletedWorkpackageAccounting(COMPLETED_ACCOUNTING_SCHEMA, accounting, retained);
        byte[] bytes=JSON.writeValueAsBytes(completed);
        if(bytes.length>(128<<10))throw new IOException("Bounded accounting receipt including exact retained source bodies required");
        int receiptBound=receiptMaxBytes(config.sourceLimitProfile());
        requirePendingAttempt(accounting,authority,"logs",Math.addExact(bytes.length,receiptBound));
        requirePendingAttempt(accounting,authority,"logs",receiptBound);
        Path path=config.workRoot().resolve("logs/build-"+config.attempt()+"-accounting.json");
        active.check();
        Lease rechecked = readLeaseAt(config, WindowsJobProcess.currentMachineId(), Instant.now());
        if (!authority.equals(rechecked.attemptAuthority()) || !accounting.capacityReleaseRef().equals(rechecked.releaseRef()))
            throw new IOException("Original accounting lease changed before publication");
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);
        FileRef published = FileRef.measure(path);
        active.check(); for (FileRef source : authority.reservationSourceRefs()) source.verify();
        accounting.capacityReleaseRef().verify(); published.verify();
        return published;
    }

    private static void requirePendingAttempt(WorkpackageAccounting accounting, AttemptAccountingAuthority authority, String scope, long bytes) throws IOException {
        long allocatedUpper = Math.multiplyExact(Math.floorDiv(Math.addExact(bytes, 4095), 4096), 4096);
        if (Math.addExact(accounting.logicalBytesByScope().get(scope), bytes) > authority.logicalCapsByScope().get(scope)
                || Math.addExact(accounting.nativeAllocatedBytesByScope().get(scope), allocatedUpper) > authority.nativeCapsByScope().get(scope)
                || Math.addExact(accounting.peakNewLogicalBytes(), bytes) > authority.maximumNewLogicalBytes()
                || Math.addExact(accounting.peakNewNativeAllocatedBytes(), allocatedUpper) > authority.maximumNewNativeBytes())
            throw new IOException("Pending publication cannot fit original logical/Native attempt reservation");
    }

    private static long exactSum(Map<String, Long> values) { long result = 0; for (long value : values.values()) result = Math.addExact(result, value); return result; }

    private static final int MUTABLE_SCOPE_CENSUS_ATTEMPTS = 8;
    private static final class AccountingIntegrityFailure extends IOException {
        private static final long serialVersionUID = 1L;
        AccountingIntegrityFailure(String message) { super(message); }
    }
    /** Only the original native 2/3 error, or NIO's typed missing-entry error, can restart a scope. */
    private static final class AccountingPathMissing extends NoSuchFileException {
        private static final long serialVersionUID = 1L;
        private final int nativeError;
        AccountingPathMissing(Path path, int error, String operation) {
            super(path.toString(), null, "Actual native accounting path unavailable; operation=" + operation + "; Win32=" + error);
            if (error != 2 && error != 3) throw new IllegalArgumentException("Native missing-path error required");
            nativeError = error;
        }
        int nativeError() { return nativeError; }
    }
    private static void accountingAttributes(Path path) throws IOException {
        Path current = path;
        while (current != null) {
            int attributes = com.sun.jna.platform.win32.Kernel32.INSTANCE.GetFileAttributes(SharedSourceFiles.nativePath(current));
            if (attributes == -1) throw accountingNativeFailure(current, com.sun.jna.Native.getLastError(), "GetFileAttributes");
            if ((attributes & 0x400) != 0) throw new AccountingIntegrityFailure("Reparse accounting path rejected: " + current);
            current = current.getParent();
        }
    }
    /** Only an original native5 may restart a complete mutable private-TMP census. */
    private static final class AccountingNativeAccessDenied extends java.nio.file.AccessDeniedException {
        private static final long serialVersionUID = 1L;
        private final int nativeError;
        private final String operation;
        AccountingNativeAccessDenied(Path path,int error,String operation) {
            super(path.toString(),null,"Native accounting access denied; operation="+operation+"; Win32="+error);
            if(error!=5)throw new IllegalArgumentException("Original native access-denied code required");
            nativeError=error;this.operation=operation;
        }
        int nativeError() { return nativeError; }
        String operation() { return operation; }
    }
    private static IOException accountingNativeFailure(Path path, int error, String operation) {
        if (error == 2 || error == 3) return new AccountingPathMissing(path, error, operation);
        if (error == 5) return new AccountingNativeAccessDenied(path,error,operation);
        return new IOException("Native accounting metadata failed, operation=" + operation + "; Win32=" + error + " path=" + path);
    }
    private static final int MUTABLE_METADATA_ATTEMPTS = 8;
    private static final class AccountingMetadataUnstable extends IOException {
        private static final long serialVersionUID = 1L;
        private final String pathText;
        AccountingMetadataUnstable(Path path, int attempts, String operation, SharedSourceFiles.NativeFactsChangedException cause) {
            super("Mutable accounting metadata remained unstable after " + attempts + " exact held samples: " + path
                    + "; operation=" + operation, cause);
            this.pathText = path.toString();
        }
        Path path() { return Path.of(pathText); }
    }

    private static final class AccountingEntryDeletePending extends IOException {
        private static final long serialVersionUID = 1L;
        private final String pathText;
        AccountingEntryDeletePending(Path path, String operation, SharedSourceFiles.NativeEntryStateException cause) {
            super("Actual mutable accounting entry delete-pending: " + path + "; operation=" + operation + "; " + cause.state(), cause);
            this.pathText = path.toString();
        }
        Path path() { return Path.of(pathText); }
    }

    /** Exact decoder and handle identity stay unchanged; mutable scopes alone may obtain a new complete sample. */
    private static SharedSourceFiles.NativeFile accountingEntry(Path path, boolean directory, boolean mutable,
            CiBootstrap.IoGuard active, InventoryObserver observer) throws IOException {
        accountingAttributes(path);
        var handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path),
                0x80, 7, null, 3, 0x00200000 | (directory ? 0x02000000 : 0), null);
        if (com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle))
            throw accountingNativeFailure(path, com.sun.jna.Native.getLastError(), "CreateFile");
        try {
            return sampleHeldAccountingEntry(handle, path, directory, mutable, active, observer);
        } finally {
            if (!com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle))
                throw new IOException("Accounting metadata close failed: " + path);
        }
    }

    /** One bounded sampler for live accounting and continuously held temporary custody; immutable decoders remain strict. */
    private static SharedSourceFiles.NativeFile sampleHeldAccountingEntry(
            com.sun.jna.platform.win32.WinNT.HANDLE handle, Path path, boolean directory, boolean mutable,
            CiBootstrap.IoGuard active, InventoryObserver observer) throws IOException {
        String operation = directory ? "nativeHeldDirectory" : "nativeHeldFile";
        for (int attempt = 1; attempt <= MUTABLE_METADATA_ATTEMPTS; attempt++) {
            active.check();
            try {
                SharedSourceFiles.MetadataReadObserver sampled = () -> observer.afterStandardMetadata(path);
                return directory ? SharedSourceFiles.nativeHeldDirectory(handle, sampled)
                        : SharedSourceFiles.nativeHeldFile(handle, sampled);
            } catch (SharedSourceFiles.NativeEntryStateException state) {
                if (mutable && state.state().onlyDeletePending())
                    throw new AccountingEntryDeletePending(path, operation, state);
                throw new IOException("Exact accounting entry state rejected: " + path + "; operation=" + operation + "; " + state.state(), state);
            } catch (SharedSourceFiles.NativeFactsChangedException changed) {
                if (!mutable || !changed.onlyMutableFactsChanged())
                    throw new IOException("Exact accounting metadata changed on " + (mutable ? "immutable creation identity: " : "immutable source: ") + path + "; operation=" + operation, changed);
                if (attempt == MUTABLE_METADATA_ATTEMPTS)
                    throw new AccountingMetadataUnstable(path, attempt, operation, changed);
            } catch (IOException failure) {
                throw new IOException("Held accounting decoder rejected: operation=" + operation + "; path=" + path
                        + "; cause=" + failure.getClass().getName() + ": " + failure.getMessage(), failure);
            }
        }
        throw new AssertionError("finite metadata attempts exhausted without a terminal branch");
    }

    private static boolean accountingDescendantMissing(Path root, IOException error) {
        if (!(error instanceof NoSuchFileException missing) || missing.getFile() == null) return false;
        Path absent = Path.of(missing.getFile()).toAbsolutePath().normalize();
        return !absent.equals(root) && absent.startsWith(root);
    }
    private static boolean accountingDescendantDeletePending(Path root, IOException failure) {
        if (!(failure instanceof AccountingEntryDeletePending pending)) return false;
        Path deleted = pending.path().toAbsolutePath().normalize();
        return !deleted.equals(root) && deleted.startsWith(root);
    }
    private static boolean accountingDescendantNativeAccessDenied(Path root,IOException failure) {
        if(!(failure instanceof AccountingNativeAccessDenied denied)||denied.nativeError()!=5)return false;
        Path path=Path.of(denied.getFile()).toAbsolutePath().normalize();
        return !path.equals(root)&&path.startsWith(root);
    }
    private static boolean accountingMetadataUnstable(Path root, IOException failure) {
        return failure instanceof AccountingMetadataUnstable unstable
                && unstable.path().toAbsolutePath().normalize().startsWith(root);
    }
    private static boolean selectedAccountingEntry(Path root, Path path, String logPrefix) {
        if (path.equals(root) || logPrefix == null) return true;
        String first = root.relativize(path).getName(0).toString();
        return first.equals(logPrefix + ".json") || first.startsWith(logPrefix + "-") || first.startsWith(logPrefix + ".");
    }

    /** Complete reachable-entry census: only independently confirmed native absence may resolve an enumerated entry. */
    private static ScopeUsage measureAttemptScope(Path root, String logPrefix, boolean mandatory, boolean mutable, boolean retryNativeDenied,
            CiBootstrap.IoGuard active, InventoryObserver observer) throws IOException {
        SharedSourceFiles.plainAncestors(root);
        try {
            BasicFileAttributes attributes = Files.readAttributes(root, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (attributes.isSymbolicLink() || attributes.isOther() || !attributes.isDirectory())
                throw new AccountingIntegrityFailure("Actual plain accounting root required: " + root);
        } catch (NoSuchFileException absent) { if (mandatory) throw absent; return new ScopeUsage(0, 0); }
        String identity = accountingEntry(root, true, mutable, active, observer).identityKey();
        long deadline = Math.addExact(System.nanoTime(), Duration.ofSeconds(120).toNanos());
        int[] visits = {0};
        for (int attempt = 1; attempt <= MUTABLE_SCOPE_CENSUS_ATTEMPTS; attempt++) {
            active.check();
            if (!accountingEntry(root, true, mutable, active, observer).identityKey().equals(identity))
                throw new AccountingIntegrityFailure("Actual accounting root identity changed: " + root);
            try {
                ScopeUsage measured = censusAttemptScope(root, logPrefix, mutable, active, observer, deadline, visits);
                active.check();
                if (!accountingEntry(root, true, mutable, active, observer).identityKey().equals(identity))
                    throw new AccountingIntegrityFailure("Actual accounting root identity changed: " + root);
                return measured;
            } catch (IOException failure) {
                active.check();
                if (!mutable || !(accountingDescendantMissing(root, failure)
                        || accountingDescendantDeletePending(root, failure) || accountingMetadataUnstable(root, failure)
                        || retryNativeDenied && accountingDescendantNativeAccessDenied(root,failure))) throw failure;
                if (!accountingEntry(root, true, mutable, active, observer).identityKey().equals(identity))
                    throw new AccountingIntegrityFailure("Accounting root changed during descendant disappearance: " + root);
                if (attempt == MUTABLE_SCOPE_CENSUS_ATTEMPTS)
                    throw new IOException("Mutable attempt scope remained unstable after " + attempt + " complete census attempts: " + root
                            + "; last_failure=" + failure.getClass().getName() + ": " + failure.getMessage(), failure);
                awaitMutableScopeRetry(root, attempt, deadline, active, failure);
                // Present/recreated entries and unstable samples restart the scope; unknown failures never become absence.
            }
        }
        throw new AssertionError("finite census attempts exhausted without a terminal branch");
    }

    /** Let a real bounded writer/cleanup wave settle without spending all eight complete censuses in one burst. */
    private static void awaitMutableScopeRetry(Path root, int completedAttempts, long deadline,
            CiBootstrap.IoGuard active, IOException lastFailure) throws IOException {
        long pause = java.util.concurrent.TimeUnit.MILLISECONDS.toNanos(25L << (completedAttempts - 1));
        long until = Math.min(deadline, Math.addExact(System.nanoTime(), pause));
        while (System.nanoTime() < until) {
            active.check();
            long remaining = until - System.nanoTime();
            if (remaining <= 0) break;
            try {
                java.util.concurrent.TimeUnit.NANOSECONDS.sleep(Math.min(remaining,
                        java.util.concurrent.TimeUnit.MILLISECONDS.toNanos(25)));
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                throw new IOException("Mutable scope retry interrupted: " + root, interrupted);
            }
        }
        active.check();
        if (System.nanoTime() >= deadline)
            throw new IOException("Finite private-scope inventory deadline exhausted during mutable retry: " + root
                    + "; last_failure=" + lastFailure.getClass().getName() + ": " + lastFailure.getMessage(), lastFailure);
    }

    private enum AccountingEntryKind { FILE, DIRECTORY, UNRESOLVED }

    /** Missing entries are known absent only while the same already observed plain ancestor remains bound. */
    private static boolean confirmedAccountingAbsence(Path root, Path path, AccountingEntryKind kind,
            IOException failure, Map<Path, String> directories, CiBootstrap.IoGuard active,
            InventoryObserver observer) throws IOException {
        if (!accountingDescendantMissing(root, failure) || path.equals(root)) return false;
        Path reported = Path.of(((NoSuchFileException) failure).getFile()).toAbsolutePath().normalize();
        if (!path.startsWith(reported)) return false;
        active.check();
        observer.afterMissingAccountingEntry(path);
        for (Path ancestor = path.getParent(); ancestor != null && ancestor.startsWith(root); ancestor = ancestor.getParent()) {
            String expected = directories.get(ancestor);
            if (expected == null) continue;
            SharedSourceFiles.NativeFile existing;
            try { existing = accountingEntry(ancestor, true, true, active, observer); }
            catch (AccountingPathMissing gone) { if (ancestor.equals(root)) throw gone; else continue; }
            if (!existing.identityKey().equals(expected))
                throw new AccountingIntegrityFailure("Observed accounting ancestor identity changed: " + ancestor);
            var handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(ancestor),
                    0x80, 7, null, 3, 0x00200000 | 0x02000000, null);
            if (com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle))
                throw accountingNativeFailure(ancestor, com.sun.jna.Native.getLastError(), "CreateFile(absence ancestor)");
            try {
                if (!sampleHeldAccountingEntry(handle, ancestor, true, true, active, observer).identityKey().equals(expected))
                    throw new AccountingIntegrityFailure("Held accounting ancestor identity changed: " + ancestor);
                verifyRecordedAccountingAncestors(root, path, directories, active, observer);
                boolean absent = nativeAccountingAbsence(path, kind);
                verifyRecordedAccountingAncestors(root, path, directories, active, observer);
                if (!sampleHeldAccountingEntry(handle, ancestor, true, true, active, observer).identityKey().equals(expected)
                        || !accountingEntry(ancestor, true, true, active, observer).identityKey().equals(expected))
                    throw new AccountingIntegrityFailure("Accounting absence ancestor replaced: " + ancestor);
                active.check();
                return absent && nativeAccountingAbsence(path, kind);
            } finally {
                if (!com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle))
                    throw new IOException("Accounting absence ancestor close failed: " + ancestor);
            }
        }
        throw new AccountingIntegrityFailure("No original surviving accounting ancestor for missing descendant: " + path);
    }

    private static void verifyRecordedAccountingAncestors(Path root, Path path, Map<Path, String> directories,
            CiBootstrap.IoGuard active, InventoryObserver observer) throws IOException {
        for (Path ancestor = path.getParent(); ancestor != null && ancestor.startsWith(root); ancestor = ancestor.getParent()) {
            String expected = directories.get(ancestor);
            if (expected == null) continue;
            try {
                if (!accountingEntry(ancestor, true, true, active, observer).identityKey().equals(expected))
                    throw new AccountingIntegrityFailure("Observed accounting ancestor identity changed: " + ancestor);
            } catch (AccountingPathMissing gone) { if (ancestor.equals(root)) throw gone; }
        }
    }

    private static boolean nativeAccountingAbsence(Path path, AccountingEntryKind kind) throws IOException {
        int attributes = com.sun.jna.platform.win32.Kernel32.INSTANCE.GetFileAttributes(SharedSourceFiles.nativePath(path));
        if (attributes == -1) {
            int error = com.sun.jna.Native.getLastError();
            if (error == 2 || error == 3) return true;
            throw accountingNativeFailure(path, error, "GetFileAttributes(confirm absence)");
        }
        if ((attributes & 0x400) != 0)
            throw new AccountingIntegrityFailure("Reparse accounting entry during absence confirmation: " + path);
        boolean directory = (attributes & 0x10) != 0;
        if ((kind == AccountingEntryKind.DIRECTORY && !directory) || (kind == AccountingEntryKind.FILE && directory))
            throw new AccountingIntegrityFailure("Accounting entry kind changed during absence confirmation: " + path);
        return false; // Present or recreated entries require the existing finite complete-scope resample.
    }

    private static ScopeUsage censusAttemptScope(Path root, String logPrefix, boolean mutable, CiBootstrap.IoGuard active,
            InventoryObserver observer, long deadline, int[] visits) throws IOException {
        long[] totals = {0, 0};
        Map<Path, String> directories = new HashMap<>();
        Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
            private void check(Path path, BasicFileAttributes attrs) throws IOException {
                active.check();
                if (System.nanoTime() > deadline || ++visits[0] > WORKPACKAGE_INVENTORY_LIMITS.totalEntries())
                    throw new IOException("Finite private-scope inventory exceeded");
                if (attrs.isSymbolicLink() || attrs.isOther())
                    throw new AccountingIntegrityFailure("Plain attempt entry required: " + path);
                observer.beforeCheck(path);
            }
            @Override public FileVisitResult preVisitDirectory(Path path, BasicFileAttributes attrs) throws IOException {
                check(path, attrs);
                if (!selectedAccountingEntry(root, path, logPrefix)) return FileVisitResult.SKIP_SUBTREE;
                SharedSourceFiles.NativeFile directory;
                try { directory = accountingEntry(path, true, mutable, active, observer); }
                catch (IOException failure) {
                    if (mutable && confirmedAccountingAbsence(root, path, AccountingEntryKind.DIRECTORY,
                            failure, directories, active, observer)) return FileVisitResult.SKIP_SUBTREE;
                    throw failure;
                }
                directories.put(path, directory.identityKey());
                totals[1] = Math.addExact(totals[1], Math.max(4096, directory.allocatedBytes()));
                return FileVisitResult.CONTINUE;
            }
            @Override public FileVisitResult visitFile(Path path, BasicFileAttributes attrs) throws IOException {
                check(path, attrs);
                if (!selectedAccountingEntry(root, path, logPrefix)) return FileVisitResult.CONTINUE;
                if (!attrs.isRegularFile()) throw new AccountingIntegrityFailure("Regular attempt file required: " + path);
                SharedSourceFiles.NativeFile file;
                try { file = accountingEntry(path, false, mutable, active, observer); }
                catch (IOException failure) {
                    if (mutable && confirmedAccountingAbsence(root, path, AccountingEntryKind.FILE,
                            failure, directories, active, observer)) return FileVisitResult.CONTINUE;
                    throw failure;
                }
                totals[0] = Math.addExact(totals[0], file.logicalBytes());
                totals[1] = Math.addExact(totals[1], file.allocatedBytes());
                return FileVisitResult.CONTINUE;
            }
            @Override public FileVisitResult visitFileFailed(Path path, IOException failure) throws IOException {
                active.check();
                if (!selectedAccountingEntry(root, path, logPrefix)) return FileVisitResult.CONTINUE;
                if (System.nanoTime() > deadline || ++visits[0] > WORKPACKAGE_INVENTORY_LIMITS.totalEntries())
                    throw new IOException("Finite private-scope inventory exceeded");
                if (mutable && confirmedAccountingAbsence(root, path, AccountingEntryKind.UNRESOLVED,
                        failure, directories, active, observer)) return FileVisitResult.CONTINUE;
                throw failure;
            }
            @Override public FileVisitResult postVisitDirectory(Path path, IOException failure) throws IOException {
                active.check();
                if (failure != null && !(mutable && confirmedAccountingAbsence(root, path, AccountingEntryKind.DIRECTORY,
                        failure, directories, active, observer))) throw failure;
                return FileVisitResult.CONTINUE;
            }
        });
        return new ScopeUsage(totals[0], totals[1]);
    }

    public static CapacityRelease ciCapacityRelease(CiBootstrap.Plan plan) throws IOException {
        if (!"true".equals(System.getenv("GITHUB_ACTIONS")) || !"github-actions-java-ci".equals(plan.ownerTask())
                || !plan.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("Isolated hosted runner authority required");
        return new CapacityRelease("xar.java-control.capacity-release/v1", plan.machineId(), plan.observedAtUtc(), plan.reviewAtUtc(),
                "RELEASED", plan.ownerTask(), new FileRef(plan.policyRef().path(), plan.policyRef().bytes(), plan.policyRef().sha256()),
                List.of(plan.workRoot(), Path.of(plan.repoRoot()).resolve("java/ck3-control").toString()),
                Path.of(plan.workRoot()).resolve("scratch").toString(), plan.parts(), plan.volumes(), plan.quotaOverrides(), 2L << 30, 768L << 20);
    }

    /** The remaining allocation comes from the retained package permit. */
    record PackagePendingAllocation(org.xar.ck3.control.build.runtime.JavaRuntimePackage.WritePermit issuedPermit,
            long accountedAllocationUpperBytes) {
        PackagePendingAllocation {
            Objects.requireNonNull(issuedPermit);
            if (accountedAllocationUpperBytes < 0 || accountedAllocationUpperBytes > issuedPermit.allocationUpperBytes())
                throw new IllegalArgumentException("Accounted package allocation must remain within its issued permit");
        }
        long remainingAllocationBytes() {
            return Math.subtractExact(issuedPermit.allocationUpperBytes(), accountedAllocationUpperBytes);
        }
    }

    /** The package consumer retains its distinct permit bound while reusing the original resource guard. */
    static void revalidateCiPackageResources(CiBootstrap.Plan plan, Path release, PackagePendingAllocation pending) throws IOException {
        if (plan == null || pending == null) throw new IOException("Current CI plan and typed package allocation required");
        var permit = pending.issuedPermit();
        if (!permit.machineId().equals(plan.machineId()) || !Instant.now().isBefore(Instant.parse(permit.expiresAtUtc())))
            throw new IOException("Issued package allocation machine or deadline rejected");
        permit.actualStorageEvidence().verify();
        revalidateCiArtifactAllocation(plan, release, pending.remainingAllocationBytes());
        permit.actualStorageEvidence().verify();
    }

    /** Reuse the admitted CI lease and inventory for a stage's pending artifact metadata. */
    public static void revalidateCiResources(CiBootstrap.Plan plan, Path release, long pendingMetadataBytes) throws IOException {
        if (pendingMetadataBytes < 0 || pendingMetadataBytes > (16L << 20))
            throw new IOException("Current CI plan and bounded pending metadata required");
        revalidateCiArtifactAllocation(plan, release, pendingMetadataBytes);
    }

    private static void revalidateCiArtifactAllocation(CiBootstrap.Plan plan, Path release, long pendingArtifactAllocationBytes) throws IOException {
        if (plan == null || release == null || !CiBootstrap.supportedPlanSchema(plan.schema())
                || !WindowsJobProcess.currentMachineId().equals(plan.machineId())
                || !Instant.now().isBefore(Instant.parse(plan.reviewAtUtc()))) {
            throw new IOException("Current CI plan and bounded pending metadata required");
        }
        Config config = new Config(Path.of(plan.repoRoot()).resolve("java/ck3-control/build-tools"),
                Path.of(plan.workRoot()), release, "ci-fixture-resource-check", plan.ownerTask(), null,
                Path.of(plan.javaHome()), CiBootstrap.MINIMUM_MAVEN_VERSION, 900,
                TargetKind.BUILD_TOOLS_RUNTIME, SourceLimitProfile.STANDARD_8_MIB);
        Lease lease = readLease(config, plan.machineId());
        guard(config, lease, () -> {}, pendingArtifactAllocationBytes);
    }

    private static void requireToolPaths(Config config, String machine) throws IOException {
        requireRegular(config.javaHome().resolve("bin/java.exe"));
        if (config.mavenCommand() != null) requireRegular(config.mavenCommand());
        Path scratch = config.workRoot().resolve("scratch").toRealPath();
        if (!Path.of(System.getProperty("jna.tmpdir", "")).toAbsolutePath().normalize().equals(scratch)) throw new IOException("Launch build-tools with approved -Djna.tmpdir");
        List<Path> paths = new ArrayList<>(List.of(config.workRoot(), config.javaHome()));
        if (config.mavenCommand() != null) paths.add(config.mavenCommand());
        for (Path path : paths) {
            if (path.toString().matches(".*[\\s\"&|<>^%!].*")) throw new IOException("Current exact CMD build route requires plain task/tool paths");
        }
    }

    private static void guard(Config config, Lease lease) throws IOException {
        guard(config, lease, () -> {});
    }

    private static void guard(Config config, Lease lease, CiBootstrap.IoGuard childDeadline) throws IOException {
        guard(config, lease, childDeadline, 0);
    }

    private static void guard(Config config, Lease lease, CiBootstrap.IoGuard childDeadline, long pendingMetadataBytes) throws IOException {
        CiBootstrap.IoGuard active = () -> {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Build inventory interrupted");
            if (!Instant.now().isBefore(lease.deadline())) throw new IOException("Capacity release expired");
            childDeadline.check();
        };
        active.check();
        if (lease.releaseRef() != null) lease.releaseRef().verify();
        for (var volume : lease.minimumFreeByVolume().entrySet()) {
            if (Files.getFileStore(volume.getKey()).getUsableSpace() < volume.getValue()) throw new IOException("Current volume free space is insufficient: " + volume.getKey());
        }
        if (lease.attemptAuthority() != null) {
            WorkpackageAccounting accounting = accountWorkpackage(config, active);
            requirePendingAttempt(accounting, lease.attemptAuthority(), "artifacts", pendingMetadataBytes);
            return;
        }
        Map<String, Long> measured = sizes(config.workRoot(), lease.caps(), active, NIO_INVENTORY);
        if (Math.addExact(measured.get("artifacts"), pendingMetadataBytes) > lease.caps().get("artifacts")) {
            throw new IOException("Workpackage artifact cap cannot admit pending CI metadata");
        }
    }

    static Map<String, Long> sizes(Path root, Map<String, Long> caps, CiBootstrap.IoGuard active, InventoryIo io) throws IOException {
        Map<String, Long> result = measureSizes(root, caps, active, io);
        for (var cap : caps.entrySet()) if (result.get(cap.getKey()) > cap.getValue()) throw new IOException("Workpackage cap exceeded: " + cap.getKey());
        return result;
    }

    private static Map<String, Long> measureSizes(Path root, Map<String, Long> caps) throws IOException {
        return measureSizes(root, caps, () -> {}, NIO_INVENTORY);
    }

    private static Map<String, Long> measureSizes(Path root, Map<String, Long> caps,
                                                   CiBootstrap.IoGuard active, InventoryIo io) throws IOException {
        Map<String, Long> result = new LinkedHashMap<>();
        for (var cap : caps.entrySet()) {
            active.check();
            Path part = root.resolve(cap.getKey());
            boolean scratch = cap.getKey().equals("scratch");
            boolean present;
            try { io.attributes(part); present = true; }
            catch (NoSuchFileException missingPart) {
                if (scratch) throw missingPart;
                present = false;
            }
            long size = present
                    ? mutableInventoryBytes(part, path -> {}, new InventoryAccess(scratch, active, io)) : 0;
            result.put(cap.getKey(), size);
        }
        return Map.copyOf(result);
    }

    interface InventoryIo {
        default BasicFileAttributes attributes(Path path) throws IOException {
            return Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        }
        default Path realPath(Path path) throws IOException { return path.toRealPath(); }
        default long size(Path path) throws IOException { return Files.size(path); }
        default DirectoryStream<Path> children(Path path) throws IOException { return Files.newDirectoryStream(path); }
        default void walk(Path root, FileVisitor<Path> visitor) throws IOException { Files.walkFileTree(root, visitor); }
    }

    private static final InventoryIo NIO_INVENTORY = new InventoryIo() {};
    private record InventoryAccess(boolean scratch, CiBootstrap.IoGuard active, InventoryIo io) {}
    @FunctionalInterface interface InventoryObserver {
        void beforeCheck(Path path) throws IOException;
        /** Observation point between the same held handle's Standard and legacy metadata reads. */
        default void afterStandardMetadata(Path path) throws IOException { }
        /** Exact boundary after a typed missing result, before independent native absence/ancestor confirmation. */
        default void afterMissingAccountingEntry(Path path) throws IOException { }
    }

    /** Mutable output accounting tolerates only entries removed during this observation. */
    static long mutableInventoryBytes(Path root, InventoryObserver observer) throws IOException {
        return mutableInventoryBytes(root, observer, new InventoryAccess(false, () -> {}, NIO_INVENTORY));
    }

    /** Output/cache inventory limits count the root directory and each observed entry exactly once. */
    record WorkpackageInventoryLimits(int regularFiles, int directories, int totalEntries) {
        WorkpackageInventoryLimits {
            if (regularFiles < 0 || directories < 1 || totalEntries < 1) {
                throw new IllegalArgumentException("Finite nonnegative files and positive directory/total limits required");
            }
        }
    }
    static final WorkpackageInventoryLimits WORKPACKAGE_INVENTORY_LIMITS =
            new WorkpackageInventoryLimits(250000, 131072, 381072);

    static long mutableInventoryBytes(Path root, InventoryObserver observer, WorkpackageInventoryLimits limits) throws IOException {
        return mutableInventoryBytes(root, observer, new InventoryAccess(false, () -> {}, NIO_INVENTORY), limits);
    }

    private static long mutableInventoryBytes(Path root, InventoryObserver observer, InventoryAccess access) throws IOException {
        return mutableInventoryBytes(root, observer, access, WORKPACKAGE_INVENTORY_LIMITS);
    }

    private static long mutableInventoryBytes(Path root, InventoryObserver observer, InventoryAccess access,
                                               WorkpackageInventoryLimits limits) throws IOException {
        AtomicLong total = new AtomicLong();
        walk(root, false, limits, true, true, observer, (path, active) -> {
            try { total.set(Math.addExact(total.get(), CiBootstrap.rereadScratchMetadata(
                    access.scratch() && !path.equals(root), active, () -> access.io().size(path)))); }
            catch (NoSuchFileException removedEntry) { /* A concurrent producer removed this output/cache entry. */ }
        }, access);
        return total.get();
    }

    private interface FileAction { void accept(Path path, CiBootstrap.IoGuard active) throws IOException; }

    private static List<FileRef> manifest(Path root, boolean excludeBuildCaches, int maxFiles, long maxBytes) throws IOException {
        return manifest(root, excludeBuildCaches, maxFiles, maxFiles, maxBytes);
    }

    private static List<FileRef> manifest(Path root, boolean excludeBuildCaches, int maxFiles, int maxEntries, long maxBytes) throws IOException {
        List<FileRef> references = new ArrayList<>(); AtomicLong total = new AtomicLong();
        walk(root, excludeBuildCaches, maxEntries, (path, active) -> {
            if (references.size() >= maxFiles) throw new IOException("Manifest regular file limit exceeded");
            FileRef reference = FileRef.measure(path); total.set(Math.addExact(total.get(), reference.bytes()));
            if (total.get() > maxBytes) throw new IOException("Manifest content limit exceeded");
            references.add(reference);
        });
        references.sort(Comparator.comparing(FileRef::path)); return List.copyOf(references);
    }

    public static List<FileRef> sourceManifest(Path root) throws IOException {
        return sourceManifest(root, SourceLimitProfile.STANDARD_8_MIB);
    }

    public static List<FileRef> sourceManifest(Path root, SourceLimitProfile profile) throws IOException {
        if (profile == null) throw new IllegalArgumentException("Explicit source limit profile required");
        List<FileRef> result = new ArrayList<>();
        Path boundary = root.toRealPath(); Set<Path> visited = new HashSet<>();
        collectModule(boundary, boundary, visited, result, profile);
        if (profile.completeG2()) {
            Set<Path> expected = new HashSet<>(); expected.add(boundary);
            for (String module : completeG2Modules(profile)) expected.add(boundary.resolve(module));
            if (!visited.equals(expected)) throw new IOException(profile.name()
                    + " requires the complete " + (expected.size() - 1) + "-child/" + expected.size() + "-project source graph");
            List<FileRef> ordinary = sourceManifestPart(boundary, profile, profile.maxBytes());
            if (!new HashSet<>(ordinary).equals(new HashSet<>(result))) throw new IOException("G2 ordinary source inventory differs from canonical module roots");
        }
        requireSourceExtent(result, profile);
        result.sort(Comparator.comparing(FileRef::path)); return List.copyOf(result);
    }

    // G2 admits directory-rich canonical source trees while bounding every visited entry.
    // The regular-file and byte limits remain the profile's independent source extent.
    private static final int G2_MAX_SOURCE_INVENTORY_ENTRIES = 8192;

    private static List<FileRef> sourceManifestPart(Path root, SourceLimitProfile profile, long maxBytes) throws IOException {
        if (profile.completeG2()) {
            return manifest(root, false, profile.maxFiles(), G2_MAX_SOURCE_INVENTORY_ENTRIES, maxBytes);
        }
        return manifest(root, false, profile.maxFiles(), maxBytes);
    }

    private static void requireSourceExtent(List<FileRef> files, SourceLimitProfile profile) throws IOException {
        long bytes = 0;
        for (FileRef file : files) bytes = Math.addExact(bytes, file.bytes());
        if (files.size() > profile.maxFiles() || bytes > profile.maxBytes()) {
            throw new IOException("Maven source closure exceeds finite " + profile.name() + " limit");
        }
    }

    public static List<FileRef> producerClosure() throws IOException {
        return producerClosure(ControlBuild.class);
    }

    /** Measures the actual archive of an explicit producer anchor; no qualification is granted here. */
    public static List<FileRef> producerClosure(Class<?> originAnchor) throws IOException {
        if (originAnchor == null || originAnchor.getProtectionDomain().getCodeSource() == null)
            throw new IOException("Actual producer anchor CodeSource required");
        try {
            Path archive = Path.of(originAnchor.getProtectionDomain().getCodeSource().getLocation().toURI());
            requireRegular(archive);
            List<FileRef> result = new ArrayList<>(); result.add(FileRef.measure(archive));
            result.addAll(manifest(archive.getParent().resolve("lib"), false, 100, 64L * 1024 * 1024));
            result.sort(Comparator.comparing(FileRef::path)); return List.copyOf(result);
        } catch (java.net.URISyntaxException error) { throw new IOException("Build producer runtime URI invalid", error); }
    }

    private static Set<String> completeG2Modules(SourceLimitProfile profile) {
        if (!profile.completeG2()) throw new IllegalArgumentException("Explicit complete G2 profile required");
        Set<String> modules = new HashSet<>(EXISTING_MIGRATION_MODULES);
        modules.add("g2-research");
        if (profile == SourceLimitProfile.G2_STABILIZATION_20261023 || profile.fullParity())
            modules.add("continuity-core");
        if (profile.fullParity())
            modules.addAll(Set.of("adapters-storage", "application", "native-transport"));
        return Set.copyOf(modules);
    }

    private static void collectModule(Path module, Path boundary, Set<Path> visited, List<FileRef> result, SourceLimitProfile profile) throws IOException {
        if (!module.startsWith(boundary) || !visited.add(module) || visited.size() > profile.maxReactorProjects())
            throw new IOException("Module graph escapes, repeats or exceeds limit");
        if (profile == SourceLimitProfile.EXISTING_MIGRATION_20261022 && !module.equals(boundary)
                && !EXISTING_MIGRATION_MODULES.contains(boundary.relativize(module).toString().replace('\\', '/'))) {
            throw new IOException("Module is outside the existing finite migration cohort");
        }
        if (profile.completeG2() && !module.equals(boundary)
                && !completeG2Modules(profile).contains(boundary.relativize(module).toString().replace('\\', '/'))) {
            throw new IOException("Module is outside the complete " + profile.name() + " cohort");
        }
        Path pom = module.resolve("pom.xml"); result.add(FileRef.measure(pom));
        for (String directory : List.of("src", ".mvn")) {
            Path path = module.resolve(directory);
            if (Files.exists(path)) result.addAll(sourceManifestPart(path, profile, profile.moduleSourceBytes(module.equals(boundary) ? "" : boundary.relativize(module).toString().replace((char)92, (char)47), directory)));
        }
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance(); factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            Element project = factory.newDocumentBuilder().parse(pom.toFile()).getDocumentElement();
            if (profile == SourceLimitProfile.EXISTING_MIGRATION_20261022 || profile.completeG2()) {
                if (module.equals(boundary) && !"ck3-control-parent".equals(directText(project, "artifactId"))) {
                    throw new IOException("Finite migration profile requires the existing control parent");
                }
                if (project.getElementsByTagNameNS("*", "sourceDirectory").getLength() != 0
                        || project.getElementsByTagNameNS("*", "testSourceDirectory").getLength() != 0) {
                    throw new IOException("Finite migration sources must use canonical module src roots");
                }
                var artifacts = project.getElementsByTagNameNS("*", "artifactId");
                for (int i = 0; i < artifacts.getLength(); i++) {
                    if ("build-helper-maven-plugin".equals(artifacts.item(i).getTextContent().strip())) {
                        throw new IOException("External source registration is outside the pinned migration closure");
                    }
                }
            }
            var parents = project.getElementsByTagNameNS("*", "relativePath");
            for (int i = 0; i < parents.getLength(); i++) {
                String relative = parents.item(i).getTextContent().strip();
                if (!relative.isEmpty() && !module.resolve(relative).normalize().startsWith(boundary)) throw new IOException("External source parent is outside the pinned closure");
            }
            var modules = project.getElementsByTagNameNS("*", "modules");
            for (int i = 0; i < modules.getLength(); i++) {
                Node container = modules.item(i);
                if (container.getParentNode() != project) throw new IOException("Profile-dependent module graphs require separate qualification");
                for (Node child = container.getFirstChild(); child != null; child = child.getNextSibling()) {
                    if (!(child instanceof Element element)) continue;
                    if (!"module".equals(element.getLocalName())) throw new IOException("Unknown module graph element");
                    String relative = element.getTextContent().strip();
                    if (relative.isEmpty() || Path.of(relative).isAbsolute()) throw new IOException("Relative Maven module required");
                    Path next = module.resolve(relative).normalize();
                    if (!next.toRealPath().startsWith(boundary)) throw new IOException("Maven module escapes source root");
                    collectModule(next, boundary, visited, result, profile);
                }
            }
        } catch (ParserConfigurationException | SAXException error) { throw new IOException("Maven source graph is not safely parseable", error); }
        requireSourceExtent(result, profile);
    }

    private static String directText(Element project, String name) {
        for (Node child = project.getFirstChild(); child != null; child = child.getNextSibling()) {
            if (child instanceof Element element && name.equals(element.getLocalName())) return element.getTextContent().strip();
        }
        return "";
    }

    private static void walk(Path root, boolean excludeBuildCaches, int maxFiles, FileAction action) throws IOException {
        walk(root, excludeBuildCaches, maxFiles, false, path -> {}, action);
    }

    private static void walk(Path root, boolean excludeBuildCaches, int maxFiles, boolean allowVanished,
                             InventoryObserver observer, FileAction action) throws IOException {
        walk(root, excludeBuildCaches, maxFiles, allowVanished, observer, action,
                new InventoryAccess(false, () -> {}, NIO_INVENTORY));
    }

    private static void walk(Path root, boolean excludeBuildCaches, int maxFiles, boolean allowVanished,
                             InventoryObserver observer, FileAction action, InventoryAccess access) throws IOException {
        // Source and other immutable inventories retain their existing total-entry ceiling.
        walk(root, excludeBuildCaches, new WorkpackageInventoryLimits(maxFiles, maxFiles, maxFiles),
                false, allowVanished, observer, action, access);
    }

    private static IOException inventoryFailure(boolean detailed, String category, Path path,
                                                long counter, long limit, String legacyMessage) {
        return new IOException(detailed ? "Workpackage inventory category=" + category + " path=" + path
                + " counter=" + counter + " limit=" + limit : legacyMessage);
    }

    private static void walk(Path root, boolean excludeBuildCaches, WorkpackageInventoryLimits limits,
                             boolean detailed, boolean allowVanished, InventoryObserver observer,
                             FileAction action, InventoryAccess access) throws IOException {
        if (!Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(root)) {
            throw inventoryFailure(detailed, "ROOT_TYPE", root, 1, 0, "Actual plain inventory root required: " + root);
        }
        long started = System.nanoTime(), deadline = started + Duration.ofSeconds(120).toNanos();
        AtomicLong count = new AtomicLong(), regularFiles = new AtomicLong(), directories = new AtomicLong();
        var currentPath = new java.util.concurrent.atomic.AtomicReference<Path>(root);
        Path realRoot = access.io().realPath(root);
        CiBootstrap.IoGuard active = () -> {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Build inventory interrupted");
            if (System.nanoTime() >= deadline) throw inventoryFailure(detailed, "TIME_MILLIS", currentPath.get(),
                    (System.nanoTime() - started) / 1000000L, 120000L, "Inventory time limit");
            access.active().check();
        };
        access.io().walk(root, new SimpleFileVisitor<>() {
            @Override public FileVisitResult preVisitDirectory(Path directory, BasicFileAttributes attributes) throws IOException {
                if (excludeBuildCaches && !directory.equals(root) && EXCLUDED.contains(directory.getFileName().toString())) return FileVisitResult.SKIP_SUBTREE;
                return check(directory, attributes) ? FileVisitResult.CONTINUE : FileVisitResult.SKIP_SUBTREE;
            }
            @Override public FileVisitResult visitFile(Path file, BasicFileAttributes attributes) throws IOException {
                if (!check(file, attributes)) return FileVisitResult.CONTINUE;
                if (!attributes.isRegularFile()) throw inventoryFailure(detailed, "NONREGULAR", file, 1, 0, "Nonregular inventory file");
                action.accept(file, active); return FileVisitResult.CONTINUE;
            }
            @Override public FileVisitResult visitFileFailed(Path file, IOException error) throws IOException {
                active.check();
                if (allowVanished && !file.equals(root) && error instanceof NoSuchFileException) return FileVisitResult.CONTINUE;
                if (scratchDescendant(file) && error instanceof AccessDeniedException) {
                    try {
                        AtomicLong attempt = new AtomicLong();
                        BasicFileAttributes attributes = CiBootstrap.rereadScratchMetadata(true, active, () -> {
                            if (attempt.getAndIncrement() == 0) throw error;
                            return access.io().attributes(file);
                        });
                        if (!attributes.isDirectory()) return visitFile(file, attributes);
                        if (preVisitDirectory(file, attributes) == FileVisitResult.SKIP_SUBTREE) return FileVisitResult.CONTINUE;
                        // This directory has not yielded any children yet. Open only it;
                        // retrying a whole consumed subtree could charge siblings twice.
                        try (var children = CiBootstrap.rereadScratchMetadata(true, active, () -> access.io().children(file))) {
                            for (Path entry : children) { active.check(); access.io().walk(entry, this); }
                        } catch (DirectoryIteratorException failedEnumeration) {
                            return postVisitDirectory(file, failedEnumeration.getCause());
                        }
                        return postVisitDirectory(file, null);
                    } catch (NoSuchFileException removedEntry) { return FileVisitResult.CONTINUE; }
                }
                throw error;
            }
            @Override public FileVisitResult postVisitDirectory(Path directory, IOException error) throws IOException {
                active.check();
                if (allowVanished && !directory.equals(root) && error instanceof NoSuchFileException) return FileVisitResult.CONTINUE;
                return super.postVisitDirectory(directory, error);
            }
            private boolean check(Path path, BasicFileAttributes attributes) throws IOException {
                currentPath.set(path); active.check();
                observer.beforeCheck(path);
                if (attributes.isSymbolicLink()) throw inventoryFailure(detailed, "SYMBOLIC_LINK", path, 1, 0, "Inventory link, extent or time limit");
                if (attributes.isOther()) throw inventoryFailure(detailed, "OTHER", path, 1, 0, "Inventory link, extent or time limit");
                long entries = count.incrementAndGet();
                if (attributes.isDirectory() && directories.incrementAndGet() > limits.directories()) {
                    throw inventoryFailure(detailed, "DIRECTORIES", path, directories.get(), limits.directories(), "Inventory link, extent or time limit");
                }
                if (attributes.isRegularFile() && regularFiles.incrementAndGet() > limits.regularFiles()) {
                    throw inventoryFailure(detailed, "REGULAR_FILES", path, regularFiles.get(), limits.regularFiles(), "Inventory link, extent or time limit");
                }
                if (entries > limits.totalEntries()) throw inventoryFailure(detailed, "TOTAL_ENTRIES", path, entries, limits.totalEntries(), "Inventory link, extent or time limit");
                if (System.nanoTime() >= deadline) throw inventoryFailure(detailed, "TIME_MILLIS", path,
                        (System.nanoTime() - started) / 1000000L, 120000L, "Inventory link, extent or time limit");
                try {
                    if (!CiBootstrap.rereadScratchMetadata(scratchDescendant(path), active,
                            () -> access.io().realPath(path)).startsWith(realRoot)) {
                        throw inventoryFailure(detailed, "PATH_ESCAPE", path, 1, 0, "Inventory path escaped root");
                    }
                    return true;
                } catch (NoSuchFileException error) {
                    if (allowVanished && !path.equals(root)) return false;
                    throw error;
                }
            }
            private boolean scratchDescendant(Path path) {
                return access.scratch() && !path.equals(root) && path.startsWith(root);
            }
        });
    }

    private static void requireSameContents(Path sourceRoot, Path compiledRoot, List<FileRef> source, List<FileRef> compiled) throws IOException {
        MavenArgumentFile.Inventories ordinary = MavenArgumentFile.ordinaryInventories(sourceRoot, compiledRoot, source, compiled);
        source = ordinary.source(); compiled = ordinary.compiled();
        if (source.size() != compiled.size()) throw new IOException("Source snapshot inventory differs");
        for (int i = 0; i < source.size(); i++) {
            if (!sourceRoot.relativize(Path.of(source.get(i).path())).equals(compiledRoot.relativize(Path.of(compiled.get(i).path())))
                    || source.get(i).bytes() != compiled.get(i).bytes() || !source.get(i).sha256().equals(compiled.get(i).sha256())) throw new IOException("Source snapshot content differs");
        }
    }
    private static void requireRegular(Path path) throws IOException {
        BasicFileAttributes attributes = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (!attributes.isRegularFile() || attributes.isSymbolicLink() || attributes.isOther()) throw new IOException("Plain regular file required: " + path);
    }
    private static byte[] readLimited(Path path, int maximum) throws IOException {
        requireRegular(path); if (Files.size(path) > maximum) throw new IOException("JSON input exceeds limit");
        byte[] data = Files.readAllBytes(path); if (data.length > maximum) throw new IOException("JSON input grew beyond limit"); return data;
    }
    private static JsonNode readObject(Path path) throws IOException { return object(JSON.readTree(readLimited(path, 128 * 1024))); }
    private static JsonNode object(JsonNode node) throws IOException { if (node == null || !node.isObject()) throw new IOException("JSON object required"); return node; }
    private static String text(JsonNode node, String name) throws IOException {
        JsonNode value = node.get(name); if (value == null || !value.isTextual() || value.textValue().isBlank()) throw new IOException("Nonempty text required: " + name); return value.textValue();
    }
    private static long nonnegative(JsonNode node, String name) throws IOException {
        JsonNode value = node.get(name); if (value == null || !value.isIntegralNumber() || !value.canConvertToLong() || value.longValue() < 0) throw new IOException("Exact nonnegative integer required: " + name); return value.longValue();
    }
    private static long positive(JsonNode node, String name) throws IOException { long value = nonnegative(node, name); if (value == 0) throw new IOException("Positive integer required: " + name); return value; }

    public static Config parseArguments(String[] args) throws IOException {
        Set<String> allowed = Set.of("--source-root", "--work-root", "--capacity-release", "--attempt", "--owner-task", "--maven-cmd", "--java-home", "--minimum-maven-version", "--timeout-seconds", "--target-kind", "--source-limit-profile", "--build-purpose");
        Map<String, String> values = new HashMap<>();
        if (args.length % 2 != 0) throw new IOException("Arguments must be exact key/value pairs");
        for (int i = 0; i < args.length; i += 2) {
            if (!allowed.contains(args[i]) || args[i + 1].isBlank() || values.putIfAbsent(args[i], args[i + 1]) != null) throw new IOException("Unknown, empty or duplicate argument");
        }
        for (String key : List.of("--source-root", "--work-root", "--capacity-release", "--attempt", "--owner-task")) if (!values.containsKey(key)) throw new IOException("Missing " + key);
        BuildPurpose.valueOf(values.getOrDefault("--build-purpose", "VERIFY"));
        requireNativeScratch(Path.of(values.get("--work-root")).resolve("scratch"));
        String machine = WindowsJobProcess.currentMachineId();
        if (!machine.equals(LOCAL_MACHINE) && !values.containsKey("--java-home")) throw new IOException("Other machines require an explicit Java home");
        return new Config(Path.of(values.get("--source-root")).toRealPath(), Path.of(values.get("--work-root")).toRealPath(),
                Path.of(values.get("--capacity-release")).toRealPath(), values.get("--attempt"), values.get("--owner-task"),
                values.containsKey("--maven-cmd") ? Path.of(values.get("--maven-cmd")).toAbsolutePath().normalize() : null,
                Path.of(values.getOrDefault("--java-home", "C:/jdk-21")).toAbsolutePath().normalize(),
                values.getOrDefault("--minimum-maven-version", "3.10.0"), Integer.parseInt(values.getOrDefault("--timeout-seconds", "900")),
                TargetKind.valueOf(values.getOrDefault("--target-kind", "SERVICE_FAST_JAR")),
                SourceLimitProfile.valueOf(values.getOrDefault("--source-limit-profile", "STANDARD_8_MIB")));
    }

    private static void requireNativeScratch(Path expected) throws IOException {
        String configured = System.getProperty("jna.tmpdir", "");
        if (configured.isEmpty() || !Path.of(configured).isAbsolute()
                || !Path.of(configured).toRealPath().equals(expected.toRealPath())) throw new IOException("Explicit approved -Djna.tmpdir required before loading JNA");
    }

    public static void main(String[] args) {
        try {
            Config config = parseArguments(args); BuildPurpose purpose = BuildPurpose.VERIFY;
            for (int index = 0; index < args.length; index += 2) if (args[index].equals("--build-purpose")) purpose = BuildPurpose.valueOf(args[index + 1]);
            if (purpose == BuildPurpose.TEST_COMPILED_CAPTURE_ONLY) {
                System.out.println(JSON.writeValueAsString(buildCapture(config))); System.exit(0);
            } else {
                BuildReceipt receipt = build(config);
                System.out.println(JSON.writeValueAsString(receipt)); System.exit(receipt.status().equals("PASS") ? 0 : 1);
            }
        } catch (Exception error) {
            try { System.err.println(JSON.writeValueAsString(new Failure("xar.java-control.build-rejected/v1", "RED", Instant.now().toString(), error.getClass().getSimpleName() + ": " + error.getMessage()))); }
            catch (IOException outputError) { System.err.println(outputError.getClass().getSimpleName()); }
            System.exit(1);
        }
    }
}
