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
        EXISTING_MIGRATION_20261022(1536, 24L << 20);

        private final int maxFiles;
        private final long maxBytes;
        SourceLimitProfile(int maxFiles, long maxBytes) { this.maxFiles = maxFiles; this.maxBytes = maxBytes; }
        public int maxFiles() { return maxFiles; }
        public long maxBytes() { return maxBytes; }
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
                    || tests != CaptureTestState.NOT_RUN || modules.isEmpty() || modules.size() > 32
                    || modules.stream().map(item -> item.modulePomRef().path()).distinct().count() != modules.size()
                    || notRunTests.isEmpty() || notRunTests.size() > 1536
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
            Map<String, Long> finalLogicalBytesByPart) {
        public CaptureBuildReceipt {
            sourcePins = List.copyOf(sourcePins); compiledSourcePins = List.copyOf(compiledSourcePins);
            completeDeployment = List.copyOf(completeDeployment); producerRuntimePins = List.copyOf(producerRuntimePins);
            mavenArguments = List.copyOf(mavenArguments); finalLogicalBytesByPart = Map.copyOf(finalLogicalBytesByPart);
            Instant.parse(observedAtUtc);
            if (!CAPTURE_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
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
            Map<String, Long> finalLogicalBytesByPart, String error) {
        public BuildReceipt {
            sourcePins = List.copyOf(sourcePins); compiledSourcePins = List.copyOf(compiledSourcePins);
            completeDeployment = List.copyOf(completeDeployment); finalLogicalBytesByPart = Map.copyOf(finalLogicalBytesByPart);
            producerRuntimePins = List.copyOf(producerRuntimePins);
            if (!SCHEMA.equals(schema) || !Set.of("PASS", "RED").contains(status) || sourcePostcheck == null || compiledSourcePostcheck == null || targetKind == null || sourceLimitProfile == null) throw new IllegalArgumentException("Unknown build receipt contract");
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
                    || timeoutSeconds <= 0 || timeoutSeconds > 900 || targetKind == null || sourceLimitProfile == null) throw new IllegalArgumentException("Invalid finite build parameters");
        }
    }

    private record Lease(String machineId, Instant deadline, Map<String, Long> caps, long memoryLimitBytes,
            long mavenHeapBytes, Map<Path, Long> minimumFreeByVolume) {}
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

    public static ObjectMapper strictMapper() { return JSON.copy(); }

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

    public static BuildReceipt acceptedReceipt(Path path) throws IOException {
        BuildReceipt receipt = JSON.readValue(readLimited(path, 1024 * 1024), BuildReceipt.class);
        JsonNode release = readObject(Path.of(receipt.capacityReleaseRef().path()));
        requireNativeScratch(Path.of(text(release, "temporary_root")));
        if (!receipt.machineId().equals(WindowsJobProcess.currentMachineId()) || !receipt.status().equals("PASS")
                || receipt.sourcePostcheck().state() != SourceState.MATCH || receipt.compiledSourcePostcheck().state() != SourceState.MATCH || receipt.error() != null
                || receipt.toolchainProbe() == null || !receipt.toolchainProbe().passed()
                || receipt.mavenToolchain() == null
                || receipt.mavenResult() == null || !receipt.mavenResult().passed()
                || receipt.sourcePins().isEmpty() || receipt.completeDeployment().isEmpty()) {
            throw new IOException("Build receipt did not establish current-machine complete qualification");
        }
        receipt.capacityReleaseRef().verify(); receipt.mavenToolchain().distributionLauncherRef().verify(); receipt.javaExecutableRef().verify();
        if (receipt.mavenToolchain().explicitOverrideRef() != null) receipt.mavenToolchain().explicitOverrideRef().verify();
        if (!Instant.now().isBefore(Instant.parse(text(release, "review_at_utc")))) throw new IOException("Build capacity release expired");
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
        List<FileRef> actual = deploymentManifest(Path.of(receipt.deploymentRoot()), receipt.targetKind());
        if (!actual.equals(receipt.completeDeployment())) throw new IOException("Deployment closure grew or changed");
        return receipt;
    }

    private enum BuildPurpose { VERIFY, TEST_COMPILED_CAPTURE_ONLY }
    private record BuildEvidence(Config config, Path snapshot, Path deployment, List<FileRef> source,
            List<FileRef> compiled, List<FileRef> closure, SourcePostcheck sourcePostcheck,
            SourcePostcheck compiledPostcheck, MavenToolchain toolchain,
            WindowsJobProcess.CommandResult probe, WindowsJobProcess.CommandResult result,
            List<String> mavenArguments, FileRef testCompilationRef, Map<String, Long> finalSizes,
            String failure, boolean interrupted) { }
    private record BuildOutcome(BuildReceipt verified, CaptureBuildReceipt capture) { }
    private record CaptureBuildFailure(String schema, String machineId, String observedAtUtc,
            CaptureTestState tests, BuildReceipt terminal, List<String> mavenArguments,
            FileRef mavenCommandRef) { }

    /** Strictly separate admission; a normal acceptedReceipt rejects this schema. */
    public static CaptureBuildReceipt acceptedCaptureReceipt(Path path) throws IOException {
        CaptureBuildReceipt receipt = JSON.readValue(readLimited(path, 1 << 20), CaptureBuildReceipt.class);
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
        receipt.capacityReleaseRef().verify(); Lease lease = readLease(config, machine);
        if (receipt.mavenResult().accounting().memoryLimitBytes() != lease.memoryLimitBytes()
                || receipt.toolchainProbe().accounting().memoryLimitBytes() != lease.memoryLimitBytes()) throw new IOException("Capture Job differs from the consumed single-Maven memory release");
        Path settings = logs.resolve("build-" + receipt.attempt() + "-settings.xml");
        List<String> expectedArgs = reactorCaptureArguments(config, settings, snapshot, build);
        if (!expectedArgs.equals(receipt.mavenArguments())) throw new IOException("Capture command arguments differ from explicit package/test-compile/no-run producer");
        String prefix = "build-" + receipt.attempt();
        requireExactPath(receipt.mavenCommandRef(), logs.resolve(prefix + "-package.cmd"));
        requireExactPath(receipt.mavenStdoutRef(), logs.resolve(prefix + "-package.stdout.log"));
        requireExactPath(receipt.mavenStderrRef(), logs.resolve(prefix + "-package.stderr.log"));
        requireExactPath(receipt.versionStdoutRef(), logs.resolve(prefix + "-version.stdout.log"));
        requireExactPath(receipt.testCompilationRef(), logs.resolve(prefix + "-test-compilation.json"));
        for (FileRef ref : List.of(receipt.mavenCommandRef(), receipt.mavenStdoutRef(), receipt.mavenStderrRef(),
                receipt.versionStdoutRef(), receipt.testCompilationRef(), receipt.javaExecutableRef(), receipt.mavenToolchain().distributionLauncherRef())) ref.verify();
        if (!java.util.Arrays.equals(readLimited(Path.of(receipt.mavenCommandRef().path()), 65536), mavenBatchText(null, expectedArgs).getBytes(StandardCharsets.UTF_8))) {
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
        if (!receipt.finalLogicalBytesByPart().keySet().equals(lease.caps().keySet())) throw new IOException("Complete capture final part accounting required");
        for (var item : receipt.finalLogicalBytesByPart().entrySet()) if (item.getValue() < 0 || item.getValue() > lease.caps().get(item.getKey())) throw new IOException("Capture final part exceeded its actual release");
        receipt.testCompilationRef().verify(); return receipt;
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

    private static BuildOutcome buildExclusive(Config config, BuildPurpose purpose) throws IOException, InterruptedException {
        requireNativeScratch(config.workRoot().resolve("scratch"));
        String machine = WindowsJobProcess.currentMachineId();
        Lease lease = readLease(config, machine);
        requireToolPaths(config, machine);
        guard(config, lease);
        Path logs = config.workRoot().resolve("logs"); Files.createDirectories(logs);
        try (FileChannel channel = FileChannel.open(config.workRoot().resolve(".java-control-build.lock"),
                StandardOpenOption.CREATE, StandardOpenOption.WRITE); FileLock lock = channel.tryLock()) {
            if (lock == null || !lock.isValid()) throw new IOException("Another Maven writer owns this workpackage");
            BuildEvidence evidence = buildLocked(config, lease, machine, logs, purpose);
            Path receiptPath = logs.resolve("build-" + config.attempt() + ".json");
            try {
                if (purpose == BuildPurpose.VERIFY) {
                    BuildReceipt receipt = normalReceipt(evidence, machine, evidence.failure());
                    Files.write(receiptPath, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(receipt), StandardOpenOption.CREATE_NEW);
                    return new BuildOutcome(receipt, null);
                }
                if (evidence.failure() != null) throw new IOException(evidence.failure());
                CaptureBuildReceipt receipt = new CaptureBuildReceipt(CAPTURE_SCHEMA, machine, Instant.now().toString(),
                        config.attempt(), config.ownerTask(), CaptureQualification.TEST_COMPILED_CAPTURE_ONLY, CaptureTestState.NOT_RUN,
                        config.sourceRoot().toString(), evidence.snapshot().toString(), evidence.deployment().toString(),
                        evidence.sourcePostcheck(), evidence.compiledPostcheck(), config.targetKind(), config.sourceLimitProfile(),
                        evidence.source(), evidence.compiled(), evidence.closure(), producerClosure(), FileRef.measure(config.capacityRelease()),
                        evidence.toolchain(), FileRef.measure(config.javaHome().resolve("bin/java.exe")), evidence.probe(), evidence.result(),
                        evidence.mavenArguments(), FileRef.measure(logs.resolve("build-" + config.attempt() + "-package.cmd")),
                        FileRef.measure(logs.resolve("build-" + config.attempt() + "-package.stdout.log")),
                        FileRef.measure(logs.resolve("build-" + config.attempt() + "-package.stderr.log")),
                        FileRef.measure(logs.resolve("build-" + config.attempt() + "-version.stdout.log")), evidence.testCompilationRef(), evidence.finalSizes());
                byte[] receiptBytes = JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(receipt);
                if (receiptBytes.length > (1 << 20)) throw new IOException("Capture receipt exceeds the unchanged 1 MiB reader bound");
                Files.write(receiptPath, receiptBytes, StandardOpenOption.CREATE_NEW);
                return new BuildOutcome(null, receipt);
            } catch (IOException | RuntimeException error) {
                if (purpose == BuildPurpose.TEST_COMPILED_CAPTURE_ONLY && !Files.exists(receiptPath)) {
                    String failure = appendFailure(evidence.failure(), "Capture qualification unavailable: " + error.getMessage());
                    Path command = logs.resolve("build-" + config.attempt() + "-package.cmd");
                    CaptureBuildFailure actual = new CaptureBuildFailure("xar.java-control-test-compiled-capture-failure/v1", machine,
                            Instant.now().toString(), CaptureTestState.NOT_RUN, normalReceipt(evidence, machine, failure),
                            evidence.mavenArguments(), Files.exists(command) ? FileRef.measure(command) : null);
                    Files.write(receiptPath, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(actual), StandardOpenOption.CREATE_NEW);
                }
                throw error;
            } finally { if (evidence.interrupted()) Thread.currentThread().interrupt(); }
        }
    }

    private static BuildReceipt normalReceipt(BuildEvidence evidence, String machine, String failure) throws IOException {
        Config config = evidence.config();
        return new BuildReceipt(SCHEMA, machine, Instant.now().toString(), failure == null ? "PASS" : "RED",
                config.sourceRoot().toString(), evidence.snapshot().toString(), evidence.deployment().toString(),
                evidence.sourcePostcheck(), evidence.compiledPostcheck(), config.targetKind(), config.sourceLimitProfile(),
                evidence.source(), evidence.compiled(), evidence.closure(), producerClosure(), FileRef.measure(config.capacityRelease()),
                evidence.toolchain(), FileRef.measure(config.javaHome().resolve("bin/java.exe")), evidence.probe(), evidence.result(), evidence.finalSizes(), failure);
    }

    private static BuildEvidence buildLocked(Config config, Lease lease, String machine, Path logs, BuildPurpose purpose)
            throws IOException, InterruptedException {
        Path snapshot = config.workRoot().resolve("scratch/source-" + config.attempt());
        Path build = config.workRoot().resolve("build/" + config.attempt());
        Path receiptPath = logs.resolve("build-" + config.attempt() + ".json");
        if (Files.exists(snapshot) || Files.exists(build) || Files.exists(receiptPath)) throw new IOException("Build attempt already exists");
        List<FileRef> source = sourceManifest(config.sourceRoot(), config.sourceLimitProfile());
        if (source.isEmpty() || !Files.isRegularFile(config.sourceRoot().resolve("pom.xml"))) throw new IOException("Maven source closure is missing");
        Files.createDirectories(snapshot); Files.createDirectories(build);
        if (!Files.getFileStore(snapshot).equals(Files.getFileStore(build))) throw new IOException("Source snapshot and build output must share a filesystem");
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
        List<String> mavenArguments = purpose == BuildPurpose.VERIFY ? reactorVerifyArguments(config, settings, snapshot, build)
                : reactorCaptureArguments(config, settings, snapshot, build);
        FileRef testCompilationRef = null;
        Path deployment = config.targetKind() == TargetKind.SERVICE_FAST_JAR
                ? build.resolve("ck3-control-local-service/quarkus-app") : build.resolve("ck3-control-build-tools");
        try {
            probe = invoke(config, lease, snapshot, environment, logs, "version", List.of("-version"));
            interrupted |= Thread.interrupted();
            String versionOutput = Files.readString(logs.resolve("build-" + config.attempt() + "-version.stdout.log"));
            if (!probe.passed()) {
                throw new IOException("Actual default Maven version probe failed or mismatched");
            }
            toolchain = measuredMavenToolchain(config.mavenCommand(), versionOutput, config.minimumMavenVersion());
            result = invoke(config, lease, snapshot, environment, logs, purpose == BuildPurpose.VERIFY ? "verify" : "package", mavenArguments);
            interrupted |= Thread.interrupted();
            if (!result.passed()) throw new IOException("Maven failed, timed out, retained children, or exceeded Job memory");
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
            guard(config, lease);
        } catch (IOException | RuntimeException error) { failure = error.getClass().getSimpleName() + ": " + error.getMessage(); }
        catch (InterruptedException error) { interrupted = true; failure = "InterruptedException: " + error.getMessage(); }
        SourcePostcheck postcheck = postcheckSource(config.sourceRoot(), source, config.sourceLimitProfile());
        if (postcheck.state() != SourceState.MATCH) failure = appendFailure(failure, "Source postcheck " + postcheck.state() + ": " + postcheck.error());
        SourcePostcheck compiledPostcheck = postcheckSource(snapshot, compiled, config.sourceLimitProfile());
        if (compiledPostcheck.state() != SourceState.MATCH) failure = appendFailure(failure, "Compiled source postcheck " + compiledPostcheck.state() + ": " + compiledPostcheck.error());
        Map<String, Long> finalSizes;
        try { finalSizes = measureSizes(config.workRoot(), lease.caps()); }
        catch (IOException | RuntimeException error) { finalSizes = Map.of(); failure = appendFailure(failure, "Final part accounting unavailable: " + error); }
        for (var part : finalSizes.entrySet()) if (part.getValue() > lease.caps().get(part.getKey())) failure = appendFailure(failure, "Final part cap exceeded: " + part.getKey());
        return new BuildEvidence(config, snapshot, deployment, List.copyOf(source), List.copyOf(compiled), closure,
                postcheck, compiledPostcheck, toolchain, probe, result, mavenArguments, testCompilationRef, finalSizes, failure, interrupted);
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
            Map<String, String> environment, Path logs, String phase, List<String> args) throws IOException, InterruptedException {
        String label = "build-" + config.attempt() + "-" + phase;
        Path batch = logs.resolve(label + ".cmd");
        writeMavenBatch(batch, config.mavenCommand(), args);
        Path cmd = Path.of(System.getenv("SystemRoot"), "System32/cmd.exe");
        WindowsJobProcess.CommandSpec spec = new WindowsJobProcess.CommandSpec(cmd, List.of("/d", "/c", batch.toString()),
                snapshot, environment, logs.resolve(label + ".stdout.log"), logs.resolve(label + ".stderr.log"), lease.memoryLimitBytes());
        try (WindowsJobProcess child = WindowsJobProcess.start(spec)) {
            AtomicLong lastGuard = new AtomicLong();
            long commandDeadline = Math.addExact(System.nanoTime(), Duration.ofSeconds(config.timeoutSeconds()).toNanos());
            return child.await(Duration.ofSeconds(config.timeoutSeconds()), lease.deadline(), () -> {
                long now = System.nanoTime();
                if (now - lastGuard.get() < Duration.ofSeconds(5).toNanos()) return;
                lastGuard.set(now);
                try {
                    guard(config, lease, () -> {
                        if (System.nanoTime() >= commandDeadline) throw new IOException("Original Maven command deadline expired");
                    });
                } catch (IOException error) { throw new IllegalStateException(error); }
            });
        }
    }

    /** Collect independent reactor failures while Maven still returns a failing terminal exit. */
    static List<String> reactorVerifyArguments(Config config, Path settings, Path snapshot, Path build) {
        return List.of("--fail-at-end", "-B", "-ntp", "-e", "-U",
                "-s", settings.toString(), "-gs", settings.toString(), "-f", snapshot.resolve("pom.xml").toString(),
                "-Dmaven.repo.local=" + config.workRoot().resolve("m2"), "-Dck3.build.root=" + build,
                "-Djava.io.tmpdir=" + config.workRoot().resolve("scratch"), "-DargLine=-Xms32m -Xmx256m", "verify");
    }

    static List<String> reactorCaptureArguments(Config config, Path settings, Path snapshot, Path build) {
        List<String> args = new ArrayList<>(reactorVerifyArguments(config, settings, snapshot, build));
        if (!args.removeLast().equals("verify")) throw new IllegalStateException("Exact existing verify argument contract required");
        args.add("-Dmaven.test.skip=false"); args.add("-DskipTests=true"); args.add("package");
        return List.copyOf(args);
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
        Files.writeString(batch, mavenBatchText(explicitOverride, args), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }

    private static String mavenBatchText(Path explicitOverride, List<String> args) {
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

    private static Map<String, String> buildEnvironment(Config config, Path snapshot, Lease lease) {
        Map<String, String> env = new TreeInsensitiveMap(System.getenv()).values();
        for (String key : List.of("MAVEN_ARGS", "MAVEN_DEBUG_OPTS", "MAVEN_BATCH_ECHO", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "JDK_JAVA_OPTIONS")) env.remove(key);
        String scratch = config.workRoot().resolve("scratch").toString();
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
        JsonNode data = readObject(config.capacityRelease());
        if (text(data, "schema").equals("xar.java-control.capacity-release/v1")) {
            return readTypedLease(config, machine, JSON.treeToValue(data, CapacityRelease.class));
        }
        if (!text(data, "schema").equals("xar.java-phase1.manual-capacity-release/v1")
                || !text(data, "status").equals("RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE")
                || !text(data, "machine_id").equals(machine) || !text(data, "single_Maven_writer").equals(config.ownerTask())) {
            throw new IOException("Capacity release schema, machine, state or writer mismatch");
        }
        Instant deadline = Instant.parse(text(data, "review_at_utc"));
        if (!Instant.now().isBefore(deadline)) throw new IOException("Capacity release expired");
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
        return new Lease(machine, deadline, Map.copyOf(caps), positive(data, "test_RAM_joint_hard_bytes"), positive(data, "Maven_heap_bytes"), Map.copyOf(minimum));
    }

    private static Lease readTypedLease(Config config, String machine, CapacityRelease release) throws IOException {
        Instant deadline = Instant.parse(release.reviewAtUtc());
        if (!machine.equals(release.machineId()) || !config.ownerTask().equals(release.ownerTask())
                || !Instant.now().isBefore(deadline)) throw new IOException("Capacity machine, writer or deadline rejected");
        boolean work = false, source = false;
        for (String root : release.approvedOutputRoots()) {
            Path approved = Path.of(root).toRealPath();
            work |= config.workRoot().toRealPath().startsWith(approved);
            source |= config.sourceRoot().toRealPath().startsWith(approved);
        }
        if (!work || !source || config.sourceRoot().startsWith(config.workRoot()) || config.workRoot().startsWith(config.sourceRoot())
                || !Path.of(release.temporaryRoot()).equals(config.workRoot().resolve("scratch"))) throw new IOException("Independent approved roots required");
        release.policyRef().verify();
        CiBootstrap.Policy policy = CiBootstrap.readPolicy(readLimited(Path.of(release.policyRef().path()), 128 * 1024));
        Map<Path, Long> minimum = new HashMap<>();
        for (var field : release.volumes().entrySet()) {
            CiBootstrap.VolumeBudget volume = field.getValue();
            long defaultQuota = Math.min(policy.quotaCeiling(), java.math.BigDecimal.valueOf(volume.totalVolumeBytes()).multiply(policy.quotaVolumeFraction())
                    .setScale(0, java.math.RoundingMode.FLOOR).longValueExact());
            CiBootstrap.QuotaOverride override = release.quotaOverrides().get(field.getKey());
            if (volume.effectiveProjectQuota() != defaultQuota) {
                if (override == null || override.owner() == null || override.owner().isBlank() || !override.task().equals(release.ownerTask())
                        || override.reason() == null || override.reason().isBlank() || override.maxProjectBytes() != (8L << 30)
                        || override.maxProjectBytes() != volume.effectiveProjectQuota() || !Instant.now().isBefore(Instant.parse(override.reviewAtUtc()))
                        || Instant.parse(override.reviewAtUtc()).isAfter(deadline)
                        || Math.addExact(volume.currentProjectUsageConservativeUpper(), volume.thisWritePeak()) <= defaultQuota) {
                    throw new IOException("Explicit finite CI quota override required only for an insufficient default quota");
                }
                new FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()).verify();
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
        return new Lease(machine, deadline, Map.copyOf(caps), release.memoryLimitBytes(), release.mavenHeapBytes(), Map.copyOf(minimum));
    }

    public static CapacityRelease ciCapacityRelease(CiBootstrap.Plan plan) throws IOException {
        if (!"true".equals(System.getenv("GITHUB_ACTIONS")) || !"github-actions-java-ci".equals(plan.ownerTask())
                || !plan.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("Isolated hosted runner authority required");
        return new CapacityRelease("xar.java-control.capacity-release/v1", plan.machineId(), plan.observedAtUtc(), plan.reviewAtUtc(),
                "RELEASED", plan.ownerTask(), new FileRef(plan.policyRef().path(), plan.policyRef().bytes(), plan.policyRef().sha256()),
                List.of(plan.workRoot(), Path.of(plan.repoRoot()).resolve("java/ck3-control").toString()),
                Path.of(plan.workRoot()).resolve("scratch").toString(), plan.parts(), plan.volumes(), plan.quotaOverrides(), 2L << 30, 768L << 20);
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
        CiBootstrap.IoGuard active = () -> {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Build inventory interrupted");
            if (!Instant.now().isBefore(lease.deadline())) throw new IOException("Capacity release expired");
            childDeadline.check();
        };
        active.check();
        for (var volume : lease.minimumFreeByVolume().entrySet()) {
            if (Files.getFileStore(volume.getKey()).getUsableSpace() < volume.getValue()) throw new IOException("Current volume free space is insufficient: " + volume.getKey());
        }
        sizes(config.workRoot(), lease.caps(), active, NIO_INVENTORY);
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
    @FunctionalInterface interface InventoryObserver { void beforeCheck(Path path) throws IOException; }

    /** Mutable output accounting tolerates only entries removed during this observation. */
    static long mutableInventoryBytes(Path root, InventoryObserver observer) throws IOException {
        return mutableInventoryBytes(root, observer, new InventoryAccess(false, () -> {}, NIO_INVENTORY));
    }

    private static long mutableInventoryBytes(Path root, InventoryObserver observer, InventoryAccess access) throws IOException {
        AtomicLong total = new AtomicLong();
        walk(root, false, 100000, true, observer, (path, active) -> {
            try { total.set(Math.addExact(total.get(), CiBootstrap.rereadScratchMetadata(
                    access.scratch() && !path.equals(root), active, () -> access.io().size(path)))); }
            catch (NoSuchFileException removedEntry) { /* A concurrent producer removed this output/cache entry. */ }
        }, access);
        return total.get();
    }

    private interface FileAction { void accept(Path path, CiBootstrap.IoGuard active) throws IOException; }

    private static List<FileRef> manifest(Path root, boolean excludeBuildCaches, int maxFiles, long maxBytes) throws IOException {
        List<FileRef> references = new ArrayList<>(); AtomicLong total = new AtomicLong();
        walk(root, excludeBuildCaches, maxFiles, (path, active) -> {
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
        collectModule(root.toRealPath(), root.toRealPath(), new HashSet<>(), result, profile);
        requireSourceExtent(result, profile);
        result.sort(Comparator.comparing(FileRef::path)); return List.copyOf(result);
    }

    private static void requireSourceExtent(List<FileRef> files, SourceLimitProfile profile) throws IOException {
        long bytes = 0;
        for (FileRef file : files) bytes = Math.addExact(bytes, file.bytes());
        if (files.size() > profile.maxFiles() || bytes > profile.maxBytes()) {
            throw new IOException("Maven source closure exceeds finite " + profile.name() + " limit");
        }
    }

    public static List<FileRef> producerClosure() throws IOException {
        try {
            Path archive = Path.of(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            requireRegular(archive);
            List<FileRef> result = new ArrayList<>(); result.add(FileRef.measure(archive));
            result.addAll(manifest(archive.getParent().resolve("lib"), false, 100, 64L * 1024 * 1024));
            result.sort(Comparator.comparing(FileRef::path)); return List.copyOf(result);
        } catch (java.net.URISyntaxException error) { throw new IOException("Build producer runtime URI invalid", error); }
    }

    private static void collectModule(Path module, Path boundary, Set<Path> visited, List<FileRef> result, SourceLimitProfile profile) throws IOException {
        if (!module.startsWith(boundary) || !visited.add(module) || visited.size() > 32) throw new IOException("Module graph escapes, repeats or exceeds limit");
        if (profile == SourceLimitProfile.EXISTING_MIGRATION_20261022 && !module.equals(boundary)
                && !EXISTING_MIGRATION_MODULES.contains(boundary.relativize(module).toString().replace('\\', '/'))) {
            throw new IOException("Module is outside the existing finite migration cohort");
        }
        Path pom = module.resolve("pom.xml"); result.add(FileRef.measure(pom));
        for (String directory : List.of("src", ".mvn")) {
            Path path = module.resolve(directory);
            if (Files.exists(path)) result.addAll(manifest(path, false, profile.maxFiles(), 8L * 1024 * 1024));
        }
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance(); factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            Element project = factory.newDocumentBuilder().parse(pom.toFile()).getDocumentElement();
            if (profile == SourceLimitProfile.EXISTING_MIGRATION_20261022) {
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
        if (!Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(root)) throw new IOException("Actual plain inventory root required: " + root);
        long deadline = System.nanoTime() + Duration.ofSeconds(120).toNanos(); AtomicLong count = new AtomicLong();
        Path realRoot = access.io().realPath(root);
        CiBootstrap.IoGuard active = () -> {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Build inventory interrupted");
            if (System.nanoTime() >= deadline) throw new IOException("Inventory time limit");
            access.active().check();
        };
        access.io().walk(root, new SimpleFileVisitor<>() {
            @Override public FileVisitResult preVisitDirectory(Path directory, BasicFileAttributes attributes) throws IOException {
                if (excludeBuildCaches && !directory.equals(root) && EXCLUDED.contains(directory.getFileName().toString())) return FileVisitResult.SKIP_SUBTREE;
                return check(directory, attributes) ? FileVisitResult.CONTINUE : FileVisitResult.SKIP_SUBTREE;
            }
            @Override public FileVisitResult visitFile(Path file, BasicFileAttributes attributes) throws IOException {
                if (!check(file, attributes)) return FileVisitResult.CONTINUE;
                if (!attributes.isRegularFile()) throw new IOException("Nonregular inventory file");
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
                active.check();
                observer.beforeCheck(path);
                if (attributes.isSymbolicLink() || attributes.isOther() || count.incrementAndGet() > maxFiles
                        || System.nanoTime() >= deadline) throw new IOException("Inventory link, extent or time limit");
                try {
                    if (!CiBootstrap.rereadScratchMetadata(scratchDescendant(path), active,
                            () -> access.io().realPath(path)).startsWith(realRoot)) throw new IOException("Inventory path escaped root");
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
