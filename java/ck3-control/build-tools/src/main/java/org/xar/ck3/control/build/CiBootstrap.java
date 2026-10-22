package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
import java.io.InterruptedIOException;
import java.io.OutputStream;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationTargetException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileStore;
import java.nio.file.AccessDeniedException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * JDK21-only hosted bootstrap. Run this source file before Jackson/JNA exist.
 * The first Maven child has heap/time/log bounds, NOT a pre-existing native Job.
 * It cannot qualify the pipeline. ControlCi must subsequently validate all stages.
 */
public final class CiBootstrap {
    public static final String PLAN_SCHEMA = "xar.java-control-CI-bootstrap-plan/v1";
    public static final String MAVEN_VERSION = "3.10.0";
    public static final String MINIMUM_MAVEN_VERSION = "3.10.0";
    public static final String MAVEN_ZIP_SHA512 =
            "22d31676d5b92ed53308c19ecded3245d0efd0cddfec51ec7bab62f4f13ad70ddddceff"
            + "8e62940e0e8e2421f3cde8106737f4becec0aa034ffeff2a754e88337";
    private static final URI MAVEN_ZIP = URI.create("https://downloads.apache.org/maven/maven-3/"
            + MAVEN_VERSION + "/binaries/apache-maven-" + MAVEN_VERSION + "-bin.zip");
    private static final URI MAVEN_CHECKSUM = URI.create(MAVEN_ZIP + ".sha512");
    private static final long MIB = 1L << 20;
    private static final long GIB = 1L << 30;
    private static final Map<String, Long> PARTS = Map.of(
            "m2", 2 * GIB, "build", 768 * MIB, "tools", 128 * MIB,
            "scratch", 512 * MIB, "metadata_logs", 32 * MIB, "artifacts", 128 * MIB,
            "guard", 480 * MIB);
    private static final Pattern SIMPLE_PATH = Pattern.compile("[^\\s\"%&|<>^!]+", Pattern.UNICODE_CHARACTER_CLASS);

    private CiBootstrap() {}

    public record FilePin(String path, long bytes, String sha256) {
        public FilePin {
            if (path == null || !Path.of(path).isAbsolute() || bytes < 0 || sha256 == null
                    || !sha256.matches("[0-9a-f]{64}")) {
                throw new IllegalArgumentException("exact bootstrap file pin required");
            }
        }
    }

    public record VolumeBudget(long totalVolumeBytes, long availableBytes, long thisWritePeak,
                               long otherUnspentReservations, long systemGrowthReserve,
                               long safetyReserve, long currentProjectUsageConservativeUpper,
                               long effectiveProjectQuota, long requiredFree) {}

    public record QuotaOverride(String owner, String task, String reason, long maxProjectBytes,
                                String reviewAtUtc, FilePin sourceRef) {
        public QuotaOverride {
            if (owner == null || owner.isBlank() || task == null || task.isBlank()
                    || reason == null || reason.isBlank() || maxProjectBytes <= 0 || sourceRef == null) {
                throw new IllegalArgumentException("explicit finite quota override provenance required");
            }
            Instant.parse(reviewAtUtc);
        }
    }

    public record Plan(String schema, String machineId, String observedAtUtc, String reviewAtUtc,
                       String repoRoot, String workRoot, String javaHome, String mavenCommand,
                       String pythonExecutable, String ownerTask, FilePin policyRef,
                        Map<String, VolumeBudget> volumes, Map<String, QuotaOverride> quotaOverrides, Map<String, Long> parts,
                       List<FilePin> sourcePins, List<FilePin> bootstrapRuntimeClosure,
                       boolean bootstrapNativeJobHardBound, boolean bootstrapAloneGrantsPipelineQualification) {
        public Plan {
            if (!PLAN_SCHEMA.equals(schema)) throw new IllegalArgumentException("unknown bootstrap plan");
            Objects.requireNonNull(machineId);
            Instant.parse(observedAtUtc);
            Instant.parse(reviewAtUtc);
            volumes = Map.copyOf(volumes);
            quotaOverrides = Map.copyOf(quotaOverrides);
            parts = Map.copyOf(parts);
            sourcePins = List.copyOf(sourcePins);
            bootstrapRuntimeClosure = List.copyOf(bootstrapRuntimeClosure);
            if (bootstrapNativeJobHardBound || bootstrapAloneGrantsPipelineQualification) {
                throw new IllegalArgumentException("standard-JDK bootstrap cannot grant native Job or pipeline qualification");
            }
        }
    }

    public record BootstrapActual(String schema, String machineId, String startedAtUtc,
                                  String observedAtUtc, String status, String error,
                                   FilePin planRef, DefaultMaven defaultMaven,
                                   List<FilePin> mavenProbeRefs,
                                   boolean bootstrapNativeJobHardBound,
                                  boolean bootstrapAloneGrantsPipelineQualification) {
        public BootstrapActual { mavenProbeRefs = List.copyOf(mavenProbeRefs); }
    }

    public record DefaultMaven(String command, String reportedVersion, String minimumVersion,
                               String reportedHome, FilePin distributionLauncherRef) {
        public DefaultMaven {
            if (!"mvn".equals(command) || !MINIMUM_MAVEN_VERSION.equals(minimumVersion)
                    || reportedHome == null || !Path.of(reportedHome).isAbsolute() || distributionLauncherRef == null) {
                throw new IllegalArgumentException("observed default Maven contract required");
            }
            requireStableMinimum(reportedVersion);
        }
    }

    /** Observation precedes admission: an old stable installation can be upgraded, not admitted. */
    public record MavenObservation(String reportedVersion, String reportedHome, FilePin launcherRef) {
        public MavenObservation {
            requireStableVersion(reportedVersion);
            if (reportedHome == null || !Path.of(reportedHome).isAbsolute() || launcherRef == null) {
                throw new IllegalArgumentException("actual Maven installation observation required");
            }
        }
    }

    public enum MavenProbePhase { BEFORE_ENSURE, AFTER_IN_PLACE_UPGRADE }
    public enum MavenProbeStatus { OBSERVED, REJECTED }

    /** A durable observation is separate from minimum-version and pipeline admission. */
    public record MavenProbeActual(String schema, String machineId, String observedAtUtc,
                                   String command, String minimumVersion, MavenProbePhase phase,
                                   MavenProbeStatus status, String error, FilePin bootstrapSourceRef,
                                   FilePin outputRef, FilePin selectedLauncherRef, MavenObservation observation) {
        public MavenProbeActual {
            if (!"xar.java-control-default-maven-probe/v1".equals(schema)
                    || machineId == null || machineId.isBlank() || !"mvn".equals(command)
                    || !MINIMUM_MAVEN_VERSION.equals(minimumVersion) || phase == null || status == null
                    || bootstrapSourceRef == null) {
                throw new IllegalArgumentException("source-bound default Maven observation required");
            }
            Instant.parse(observedAtUtc);
            if ((observation != null && outputRef == null) || (selectedLauncherRef != null && observation == null)) {
                throw new IllegalArgumentException("observed Maven identity requires its actual output evidence");
            }
            if (status == MavenProbeStatus.OBSERVED) {
                if (error != null || outputRef == null || observation == null
                        || !observation.launcherRef().equals(selectedLauncherRef)) {
                    throw new IllegalArgumentException("complete matching launcher observation required");
                }
            } else if (error == null || error.isBlank()) {
                throw new IllegalArgumentException("rejected Maven probe requires its actual error");
            }
        }
    }

    @FunctionalInterface interface MavenProbe { String run() throws IOException, InterruptedException; }
    @FunctionalInterface interface MavenLauncherProbe { Path resolve() throws IOException; }
    @FunctionalInterface interface MavenInstaller { void replace(MavenObservation before) throws IOException, InterruptedException; }
    @FunctionalInterface interface IoGuard { void check() throws IOException; }
    @FunctionalInterface interface AttributeReader { BasicFileAttributes read(Path path) throws IOException; }
    private record MavenUpgradePlan(String machineId, String observedAtUtc, String status,
                                    MavenObservation before, String officialArchiveUrl, String officialChecksumUrl,
                                    FilePin archiveRef, List<FilePin> originalFiles, List<FilePin> replacementFiles,
                                    String backupRoot, List<String> preservedConfiguration, VolumeBudget installationVolumeBudget) {}

    /** Supported policy is read from the shared versioned file, never a copied retention policy. */
    public record Policy(long safetyFloor, long safetyCeiling, BigDecimal safetyVolumeFraction,
                          long quotaCeiling, BigDecimal quotaVolumeFraction, long quotaOverrideMaxHours) {
        public Policy {
            if (safetyFloor <= 0 || safetyCeiling < safetyFloor || quotaCeiling <= 0
                    || safetyVolumeFraction == null || quotaVolumeFraction == null
                    || safetyVolumeFraction.signum() <= 0 || quotaVolumeFraction.signum() <= 0
                    || quotaOverrideMaxHours <= 0 || safetyVolumeFraction.compareTo(BigDecimal.ONE) > 0
                    || quotaVolumeFraction.compareTo(BigDecimal.ONE) > 0) {
                throw new IllegalArgumentException("known positive shared storage policy parameters required");
            }
        }
    }

    public static void main(String[] arguments) throws Exception {
        if (!System.getProperty("os.name").startsWith("Windows") || Runtime.version().feature() != 21) {
            throw new IllegalStateException("explicit installed Windows JDK21 required; no skip");
        }
        if (arguments.length == 2 && arguments[0].equals("--verify-maven-evidence-root")) {
            String machine = machineId(Path.of(Objects.requireNonNull(System.getenv("SystemRoot"))).toRealPath());
            int count = verifyMavenEvidence(Path.of(arguments[1]), machine);
            System.out.println("Verified " + count + " persisted Maven probe records; evidence integrity grants no pipeline qualification");
            return;
        }
        Map<String, String> values = arguments(arguments);
        Path repo = Path.of(values.get("--repo-root")).toRealPath();
        Path root = Path.of(values.get("--work-root")).toAbsolutePath().normalize();
        Path python = Path.of(values.get("--python-executable")).toRealPath();
        long reserve = Long.parseLong(values.get("--system-growth-reserve-bytes"));
        long requestedQuota = Long.parseLong(values.get("--max-project-bytes"));
        if (reserve <= 0 || reserve > 100 * GIB) throw new IllegalArgumentException("explicit system growth reserve required");
        if (!"true".equals(System.getenv("GITHUB_ACTIONS"))) {
            throw new IllegalStateException("this bootstrap profile is only for an isolated hosted runner");
        }
        Path runnerTemp = Path.of(Objects.requireNonNull(System.getenv("RUNNER_TEMP"))).toRealPath();
        Path systemRoot = Path.of(Objects.requireNonNull(System.getenv("SystemRoot"))).toRealPath();
        Path javaHome = Path.of(System.getProperty("java.home")).toRealPath();
        if (!root.getParent().toRealPath().equals(runnerTemp) || root.startsWith(repo)
                || root.getRoot().equals(systemRoot.getRoot()) || Files.exists(root, LinkOption.NOFOLLOW_LINKS)) {
            throw new IllegalArgumentException("new task root in the explicit non-system RUNNER_TEMP required");
        }
        for (Path path : List.of(root, repo, javaHome, python)) {
            if (!SIMPLE_PATH.matcher(path.toString()).matches()) {
                throw new IllegalArgumentException("the shared exact Windows CMD route requires plain absolute tool/task paths");
            }
        }
        Path policyPath = repo.resolve("docs/storage-retention-policy.json");
        Policy policy = readPolicy(Files.readAllBytes(policyPath));
        Path profilePath = repo.resolve("java/ck3-control/ci-profile.json");
        J profile = parse(Files.readAllBytes(profilePath));
        if (!string(field(profile, "schema")).equals("xar.java-control-CI-profile/v1")
                || integer(field(profile, "max_project_bytes")) != requestedQuota || requestedQuota != 8 * GIB
                || integer(field(profile, "review_minutes")) != 90
                || !string(field(profile, "task")).equals("github-actions-java-ci")) {
            throw new IOException("explicit approved versioned hosted CI quota profile required");
        }
        String machine = machineId(systemRoot);
        Instant observed = Instant.now();
        Instant expiry = observed.plus(Duration.ofMinutes(90));
        QuotaOverride override = new QuotaOverride(string(field(profile, "owner")), string(field(profile, "task")),
                string(field(profile, "reason")), requestedQuota, expiry.toString(), measure(profilePath));
        Map<String, QuotaOverride> overrides = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        Map<String, VolumeBudget> volumes = budgets(policy, List.of(repo, runnerTemp), root, systemRoot, reserve,
                override, observed, expiry, overrides);
        requireFree(volumes);
        Files.createDirectory(root);
        for (String part : List.of("m2", "build", "tools", "scratch", "logs", "artifacts")) Files.createDirectory(root.resolve(part));
        Path planPath = root.resolve("logs/bootstrap-plan.json");
        String started = Instant.now().toString();
        FilePin planRef = null;
        DefaultMaven defaultMaven = null;
        List<FilePin> mavenProbeRefs = new ArrayList<>();
        String failure = null;
        boolean completed = false;
        try {
            Path source = repo.resolve("java/ck3-control/build-tools");
            List<FilePin> before = sourcePins(source);
            FilePin bootstrapSourceRef = measure(source.resolve("src/main/java/org/xar/ck3/control/build/CiBootstrap.java"));
            Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
            environment.putAll(System.getenv());
            environment.put("JAVA_HOME", javaHome.toString());
            environment.put("XAR_ORACLE_PYTHON", python.toString());
            environment.put("XAR_REPO_ROOT", repo.toString());
            String scratch = root.resolve("scratch").toString();
            String jvm = "-Xms32m -Xmx512m -XX:MaxMetaspaceSize=192m -XX:ReservedCodeCacheSize=64m"
                    + " -XX:MaxDirectMemorySize=64m -Xss512k -Djava.io.tmpdir=" + scratch + " -Djna.tmpdir=" + scratch;
            environment.put("JAVA_TOOL_OPTIONS", jvm);
            environment.put("MAVEN_OPTS", jvm);
            environment.put("MAVEN_SKIP_RC", "1");
            environment.put("MAVEN_USER_HOME", root.resolve("m2").toString());
            environment.put("TEMP", scratch);
            environment.put("TMP", scratch);
            for (String name : List.of("MAVEN_ARGS", "MAVEN_DEBUG_OPTS", "JDK_JAVA_OPTIONS")) environment.remove(name);
            Path settings = root.resolve("scratch/maven-settings.xml");
            Files.writeString(settings, "<settings xmlns=\"http://maven.apache.org/SETTINGS/1.2.0\"></settings>\n",
                    StandardOpenOption.CREATE_NEW);
            Path versionBatch = root.resolve("scratch/maven-version.cmd");
            Files.writeString(versionBatch, "@echo off\r\ncall mvn --version\r\nexit /b %errorlevel%\r\n",
                    StandardOpenOption.CREATE_NEW);
            int[] probeOrdinal = {0};
            defaultMaven = ensureDefaultMaven(() -> {
                int ordinal = ++probeOrdinal[0];
                Path log = root.resolve("logs/maven-version-" + ordinal + ".log");
                return recordedMavenProbe(() -> {
                    runPlain(List.of(systemRoot.resolve("System32/cmd.exe").toString(), "/d", "/c", versionBatch.toString()),
                            root.resolve("scratch"), environment, log, Duration.ofSeconds(30), expiry, root, volumes);
                    return Files.readString(log);
                }, () -> defaultMavenLauncher(environment, root.resolve("scratch"), true), log,
                        root.resolve("logs/maven-observation-" + ordinal + ".json"), machine, bootstrapSourceRef,
                        ordinal == 1 ? MavenProbePhase.BEFORE_ENSURE : MavenProbePhase.AFTER_IN_PLACE_UPGRADE,
                        true, mavenProbeRefs);
            }, observedInstallation -> installOfficialMaven(observedInstallation, root, machine, volumes, () -> guard(root, volumes, expiry)));
            Path maven = Path.of(defaultMaven.distributionLauncherRef().path());
            Path batch = root.resolve("scratch/bootstrap-verify.cmd");
            Files.writeString(batch, "@echo off\r\ncall mvn -B -ntp -e -s \"" + settings
                    + "\" -gs \"" + settings + "\" -f \"" + source.resolve("pom.xml")
                    + "\" \"-Dmaven.repo.local=" + root.resolve("m2") + "\" \"-Dck3.build.root="
                    + root.resolve("build/bootstrap-tools") + "\" verify\r\nexit /b %errorlevel%\r\n",
                    StandardOpenOption.CREATE_NEW);
            runPlain(List.of(systemRoot.resolve("System32/cmd.exe").toString(), "/d", "/c", batch.toString()),
                    root.resolve("scratch"), environment, root.resolve("logs/bootstrap-verify.log"), Duration.ofMinutes(15), expiry, root, volumes);
            if (!before.equals(sourcePins(source))) throw new IOException("bootstrap source changed during full verify");
            Path output = root.resolve("build/bootstrap-tools/ck3-control-build-tools");
            List<FilePin> runtime = new ArrayList<>();
            runtime.add(measure(output.resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar")));
            try (var paths = Files.list(output.resolve("lib"))) {
                for (Path path : paths.sorted().toList()) {
                    if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || !path.toString().endsWith(".jar")) {
                        throw new IOException("complete regular runtime jar closure required");
                    }
                    runtime.add(measure(path));
                }
            }
            Plan plan = new Plan(PLAN_SCHEMA, machine, Instant.now().toString(), expiry.toString(),
                    repo.toString(), root.toString(), javaHome.toString(), maven.toString(), python.toString(),
                    "github-actions-java-ci", measure(policyPath), volumes, overrides, PARTS, before, List.copyOf(runtime), false, false);
            planRef = publish(planPath, plan);
            String classpath = String.join(";", runtime.stream().map(FilePin::path).toList());
            List<String> command = List.of(javaHome.resolve("bin/java.exe").toString(), "-Xms32m", "-Xmx128m",
                    "-XX:MaxMetaspaceSize=96m", "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m",
                    "-Djava.io.tmpdir=" + scratch, "-Djna.tmpdir=" + scratch, "-cp", classpath,
                    "org.xar.ck3.control.build.ControlCi", "--bootstrap-plan", planPath.toString());
            environment.remove("JAVA_TOOL_OPTIONS");
            runPlain(command, repo, environment, root.resolve("logs/qualified-pipeline.log"),
                    Duration.ofMinutes(20), expiry, root, volumes);
            requireFree(volumes);
            completed = true;
        } catch (Exception error) {
            failure = error.getClass().getName() + ": " + error.getMessage();
        } finally {
            if (!completed && failure == null) failure = "bootstrap did not reach complete downstream terminal validation";
            publish(root.resolve("logs/bootstrap-actual.json"), new BootstrapActual(
                    "xar.java-control-CI-bootstrap-actual/v3", machine, started, Instant.now().toString(),
                    completed && failure == null ? "PIPELINE_EXIT_0" : "RED", failure, planRef, defaultMaven,
                    mavenProbeRefs, false, false));
        }
        if (!completed || failure != null) throw new IllegalStateException(failure);
    }

    /** Existing default command is authoritative; admission never substitutes a task-local command. */
    public static DefaultMaven requireDefaultMaven(String output) throws IOException {
        MavenObservation observed = observeDefaultMaven(output, System.getProperty("os.name").startsWith("Windows"));
        try { requireStableMinimum(observed.reportedVersion()); }
        catch (IllegalArgumentException error) { throw new IOException("default Maven is below the stable minimum", error); }
        return new DefaultMaven("mvn", observed.reportedVersion(), MINIMUM_MAVEN_VERSION,
                observed.reportedHome(), observed.launcherRef());
    }

    static MavenObservation observeDefaultMaven(String output, boolean windows) throws IOException {
        MavenReportedIdentity identity = reportedMavenIdentity(output);
        return new MavenObservation(identity.reportedVersion(), identity.reportedHome(),
                measure(Path.of(identity.reportedHome()).resolve(windows ? "bin/mvn.cmd" : "bin/mvn")));
    }

    private record MavenReportedIdentity(String reportedVersion, String reportedHome) {}

    private static MavenReportedIdentity reportedMavenIdentity(String output) throws IOException {
        if (output == null || output.length() > 65536) throw new IOException("bounded actual Maven version output required");
        var versions = Pattern.compile("(?m)^Apache Maven ([^\\r\\n ]+)(?: [^\\r\\n]*)?$").matcher(output);
        if (!versions.find()) throw new IOException("default mvn did not report its version; environment not qualified");
        String version = versions.group(1);
        if (versions.find()) throw new IOException("ambiguous default Maven version");
        try { requireStableVersion(version); }
        catch (IllegalArgumentException error) { throw new IOException("stable default Maven version required", error); }
        var homes = Pattern.compile("(?m)^Maven home: ([^\\r\\n]+)$").matcher(output);
        if (!homes.find()) throw new IOException("default mvn did not report its actual installation home");
        Path home = Path.of(homes.group(1).strip()).toRealPath();
        if (homes.find()) throw new IOException("ambiguous default Maven installation home");
        return new MavenReportedIdentity(version, home.toString());
    }

    /** Always publish before returning or propagating failure, including an old stable version. */
    static String recordedMavenProbe(MavenProbe probe, MavenLauncherProbe launcher, Path outputPath,
                                     Path receiptPath, String machineId, FilePin bootstrapSourceRef,
                                     MavenProbePhase phase, boolean windows, List<FilePin> publishedRefs)
            throws IOException, InterruptedException {
        MavenObservation observation = null;
        FilePin outputRef = null, selected = null;
        Exception failure = null;
        MavenProbeStatus status = MavenProbeStatus.REJECTED;
        try {
            // Validate the actual first default candidate before CALL can execute a script association.
            FilePin before = measure(launcher.resolve());
            String output = probe.run();
            outputRef = measure(outputPath);
            if (outputRef.bytes() > 65_536 || !output.equals(Files.readString(outputPath))
                    || !outputRef.equals(measure(outputPath))) {
                throw new IOException("bounded unchanged actual Maven stdout required");
            }
            observation = observeDefaultMaven(output, windows);
            selected = measure(launcher.resolve());
            if (!before.equals(selected)) throw new IOException("selected default Maven launcher changed during its version probe");
            if (!selected.equals(observation.launcherRef())) {
                throw new IOException("selected default Maven launcher differs from its reported installation");
            }
            status = MavenProbeStatus.OBSERVED;
            return output;
        } catch (IOException | InterruptedException | RuntimeException error) {
            failure = error;
            throw error;
        } finally {
            try {
                if (outputRef == null && Files.isRegularFile(outputPath, LinkOption.NOFOLLOW_LINKS)) {
                    outputRef = measure(outputPath);
                }
                String error = failure != null ? failure.getClass().getName() + ": " + failure.getMessage()
                        : status == MavenProbeStatus.REJECTED ? "Maven probe did not complete normally" : null;
                FilePin receipt = publish(receiptPath, new MavenProbeActual(
                        "xar.java-control-default-maven-probe/v1", machineId, Instant.now().toString(),
                        "mvn", MINIMUM_MAVEN_VERSION, phase, status, error, bootstrapSourceRef,
                        outputRef, selected, observation));
                publishedRefs.add(receipt);
            } catch (IOException | RuntimeException publicationFailure) {
                if (failure == null) throw publicationFailure;
                failure.addSuppressed(publicationFailure);
            }
        }
    }

    /** JDK-only artifact consumer. RED bootstrap evidence can be intact without granting admission. */
    static int verifyMavenEvidence(Path workRoot, String expectedMachineId) throws IOException {
        Path logs = workRoot.toRealPath().resolve("logs");
        J terminal = readMetadata(logs.resolve("bootstrap-actual.json"));
        exactFields(terminal, Set.of("schema", "machine_id", "started_at_utc", "observed_at_utc", "status", "error",
                "plan_ref", "default_maven", "maven_probe_refs", "bootstrap_native_job_hard_bound",
                "bootstrap_alone_grants_pipeline_qualification"));
        requireText(terminal, "schema", "xar.java-control-CI-bootstrap-actual/v3");
        requireText(terminal, "machine_id", expectedMachineId);
        requireFalse(terminal, "bootstrap_native_job_hard_bound");
        requireFalse(terminal, "bootstrap_alone_grants_pipeline_qualification");
        try {
            nullableFilePin(field(terminal, "plan_ref"));
            Instant.parse(string(field(terminal, "started_at_utc")));
            Instant.parse(string(field(terminal, "observed_at_utc")));
            J refsNode = field(terminal, "maven_probe_refs");
            if (!(refsNode instanceof JA refs) || refs.values().size() > 2) throw new IOException("at most two actual Maven probes required");
            List<MavenProbeActual> observations = new ArrayList<>();
            for (int index = 0; index < refs.values().size(); index++) {
                FilePin ref = parseFilePin(refs.values().get(index));
                Path expected = logs.resolve("maven-observation-" + (index + 1) + ".json").toAbsolutePath().normalize();
                if (!expected.toString().equals(ref.path())) throw new IOException("Maven probe receipt route differs");
                verifyPin(ref);
                MavenProbeActual probe = parseMavenProbe(readMetadata(expected));
                verifyPin(ref);
                MavenProbePhase phase = index == 0 ? MavenProbePhase.BEFORE_ENSURE : MavenProbePhase.AFTER_IN_PLACE_UPGRADE;
                if (!expectedMachineId.equals(probe.machineId()) || phase != probe.phase()) {
                    throw new IOException("Maven probe machine/phase differs from terminal sequence");
                }
                verifyPin(probe.bootstrapSourceRef());
                if (!observations.isEmpty() && !observations.getFirst().bootstrapSourceRef().equals(probe.bootstrapSourceRef())) {
                    throw new IOException("Maven bootstrap source changed between probes");
                }
                if (probe.outputRef() != null) {
                    Path output = logs.resolve("maven-version-" + (index + 1) + ".log").toAbsolutePath().normalize();
                    if (!output.toString().equals(probe.outputRef().path())) throw new IOException("Maven stdout route differs");
                    verifyPin(probe.outputRef());
                    if (probe.observation() != null) {
                        if (probe.outputRef().bytes() > 65_536) throw new IOException("observed Maven stdout exceeds parser budget");
                        MavenReportedIdentity reported = reportedMavenIdentity(Files.readString(output));
                        if (!reported.reportedVersion().equals(probe.observation().reportedVersion())
                                || !reported.reportedHome().equals(probe.observation().reportedHome())) {
                            throw new IOException("persisted Maven version/home differs from its actual stdout");
                        }
                        verifyPin(probe.outputRef());
                    }
                }
                // Historical launcher pins are retained evidence: an in-place upgrade changes that same path.
                observations.add(probe);
            }
            DefaultMaven admitted = parseDefaultMaven(field(terminal, "default_maven"));
            String status = string(field(terminal, "status"));
            String error = nullableText(field(terminal, "error"));
            if ((!status.equals("RED") && !status.equals("PIPELINE_EXIT_0"))
                    || (status.equals("RED") != (error != null))) throw new IOException("terminal bootstrap status/error differs");
            if (observations.size() == 2) {
                MavenProbeActual before = observations.getFirst();
                if (before.status() != MavenProbeStatus.OBSERVED || atMinimum(before.observation().reportedVersion())) {
                    throw new IOException("post-upgrade observation has no actual old stable before-state");
                }
            }
            if (admitted != null) {
                if (observations.isEmpty()) throw new IOException("admitted default Maven has no actual probe");
                MavenProbeActual last = observations.getLast();
                if (last.status() != MavenProbeStatus.OBSERVED
                        || !last.observation().reportedVersion().equals(admitted.reportedVersion())
                        || !last.observation().reportedHome().equals(admitted.reportedHome())
                        || !last.observation().launcherRef().equals(admitted.distributionLauncherRef())) {
                    throw new IOException("admitted default Maven differs from its actual final probe");
                }
                if (!atMinimum(observations.getFirst().observation().reportedVersion()) && observations.size() != 2) {
                    throw new IOException("successful in-place upgrade lacks its actual after-state");
                }
                if (observations.size() == 2 && (!observations.getFirst().observation().reportedHome().equals(admitted.reportedHome())
                        || !observations.getFirst().observation().launcherRef().path().equals(admitted.distributionLauncherRef().path())
                        || !MAVEN_VERSION.equals(admitted.reportedVersion()))) {
                    throw new IOException("admitted upgrade changed the original default installation");
                }
                verifyPin(admitted.distributionLauncherRef());
            } else if (status.equals("PIPELINE_EXIT_0")) {
                throw new IOException("successful pipeline has no admitted default Maven");
            }
            return observations.size();
        } catch (IllegalArgumentException error) {
            throw new IOException("invalid persisted Maven observation contract", error);
        }
    }

    private static boolean atMinimum(String version) {
        try { requireStableMinimum(version); return true; }
        catch (IllegalArgumentException belowMinimum) { return false; }
    }

    private static MavenProbeActual parseMavenProbe(J value) throws IOException {
        exactFields(value, Set.of("schema", "machine_id", "observed_at_utc", "command", "minimum_version", "phase",
                "status", "error", "bootstrap_source_ref", "output_ref", "selected_launcher_ref", "observation"));
        J observationNode = field(value, "observation");
        MavenObservation observation = null;
        if (!(observationNode instanceof JNull)) {
            exactFields(observationNode, Set.of("reported_version", "reported_home", "launcher_ref"));
            observation = new MavenObservation(string(field(observationNode, "reported_version")),
                    string(field(observationNode, "reported_home")), parseFilePin(field(observationNode, "launcher_ref")));
        }
        return new MavenProbeActual(string(field(value, "schema")), string(field(value, "machine_id")),
                string(field(value, "observed_at_utc")), string(field(value, "command")), string(field(value, "minimum_version")),
                MavenProbePhase.valueOf(string(field(value, "phase"))), MavenProbeStatus.valueOf(string(field(value, "status"))),
                nullableText(field(value, "error")), parseFilePin(field(value, "bootstrap_source_ref")),
                nullableFilePin(field(value, "output_ref")), nullableFilePin(field(value, "selected_launcher_ref")), observation);
    }

    private static DefaultMaven parseDefaultMaven(J value) throws IOException {
        if (value instanceof JNull) return null;
        exactFields(value, Set.of("command", "reported_version", "minimum_version", "reported_home", "distribution_launcher_ref"));
        return new DefaultMaven(string(field(value, "command")), string(field(value, "reported_version")),
                string(field(value, "minimum_version")), string(field(value, "reported_home")),
                parseFilePin(field(value, "distribution_launcher_ref")));
    }

    private static FilePin nullableFilePin(J value) throws IOException { return value instanceof JNull ? null : parseFilePin(value); }
    private static String nullableText(J value) throws IOException { return value instanceof JNull ? null : string(value); }
    private static FilePin parseFilePin(J value) throws IOException {
        exactFields(value, Set.of("path", "bytes", "sha256"));
        return new FilePin(string(field(value, "path")), integer(field(value, "bytes")), string(field(value, "sha256")));
    }
    private static void verifyPin(FilePin ref) throws IOException {
        Path path = Path.of(ref.path());
        if (ref.bytes() > 8 * MIB || Files.size(path) != ref.bytes() || !ref.equals(measure(path))) {
            throw new IOException("persisted Maven evidence file pin differs: " + ref.path());
        }
    }
    private static J readMetadata(Path path) throws IOException {
        long bytes = Files.size(path);
        if (bytes <= 0 || bytes > MIB) throw new IOException("bounded complete Maven metadata required");
        FilePin before = measure(path);
        if (before.bytes() <= 0 || before.bytes() > MIB) throw new IOException("bounded complete Maven metadata required");
        J value = parse(Files.readAllBytes(path));
        if (!before.equals(measure(path))) throw new IOException("Maven metadata changed during consumption");
        return value;
    }
    private static void exactFields(J value, Set<String> expected) throws IOException {
        if (!(value instanceof JO object) || !object.values().keySet().equals(expected)) throw new IOException("exact Maven metadata fields required");
    }
    private static void requireText(J value, String key, String expected) throws IOException {
        if (!expected.equals(string(field(value, key)))) throw new IOException("Maven metadata " + key + " differs");
    }
    private static void requireFalse(J value, String key) throws IOException {
        if (!(field(value, key) instanceof JB flag) || flag.value()) throw new IOException("Maven observation cannot grant pipeline/Job qualification");
    }

    static DefaultMaven ensureDefaultMaven(MavenProbe probe, MavenInstaller installer) throws IOException, InterruptedException {
        boolean windows = System.getProperty("os.name").startsWith("Windows");
        String initial = probe.run();
        MavenObservation before = observeDefaultMaven(initial, windows);
        try { requireStableMinimum(before.reportedVersion()); return requireDefaultMaven(initial); }
        catch (IllegalArgumentException belowMinimum) { /* Only a valid old stable installation reaches replacement. */ }
        installer.replace(before);
        DefaultMaven after = requireDefaultMaven(probe.run());
        if (!after.reportedHome().equals(before.reportedHome())
                || !after.distributionLauncherRef().path().equals(before.launcherRef().path())
                || !after.reportedVersion().equals(MAVEN_VERSION)) {
            throw new IOException("default Maven installation identity/version changed during in-place upgrade");
        }
        return after;
    }

    static Path defaultMavenLauncher(Map<String, String> environment, Path cwd, boolean windows) throws IOException {
        String search = environment.get("PATH");
        if (search == null) throw new IOException("default Maven PATH unavailable");
        List<Path> directories = new ArrayList<>();
        if (windows) directories.add(cwd);
        for (String directory : search.split(windows ? ";" : ":", -1)) {
            if (directory.isEmpty()) directories.add(cwd);
            else directories.add(Path.of(directory.replaceAll("^\"|\"$", "")));
        }
        List<String> suffixes = windows
                ? List.of(environment.getOrDefault("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")) : List.of("");
        for (Path directory : directories) {
            for (String suffix : suffixes) {
                Path name;
                try { name = Path.of("mvn" + suffix); }
                catch (java.nio.file.InvalidPathException malformed) { throw new IOException("invalid default command extension", malformed); }
                if (windows && (!suffix.startsWith(".") || name.isAbsolute() || name.getNameCount() != 1 || name.getParent() != null)) {
                    throw new IOException("invalid default command extension");
                }
                Path candidate = directory.resolve(name);
                if (Files.isRegularFile(candidate) && (windows || Files.isExecutable(candidate))) {
                    if (windows && !suffix.matches("(?i)\\.(COM|EXE|BAT|CMD)")) {
                        throw new IOException("unsupported actual default Maven launcher extension: " + suffix);
                    }
                    return candidate.toRealPath();
                }
            }
        }
        throw new IOException("default Maven launcher is unresolved");
    }

    private static void installOfficialMaven(MavenObservation before, Path root, String machine,
                                            Map<String, VolumeBudget> volumes, IoGuard guard)
            throws IOException, InterruptedException {
        guard.check();
        Path home = Path.of(before.reportedHome());
        VolumeBudget base = volumes.get(home.getRoot().toString());
        if (base == null) throw new IOException("observed Maven installation volume has no approved capacity basis");
        long peak = Math.addExact(base.thisWritePeak(), 64 * MIB);
        long required = Math.addExact(base.requiredFree(), 64 * MIB);
        long available = Files.getFileStore(home).getUsableSpace();
        if (available < required || Math.addExact(base.currentProjectUsageConservativeUpper(), peak) > base.effectiveProjectQuota()) {
            throw new IOException("in-place Maven installation growth exceeds actual approved volume budget");
        }
        VolumeBudget installationBudget = new VolumeBudget(base.totalVolumeBytes(), available, peak,
                base.otherUnspentReservations(), base.systemGrowthReserve(), base.safetyReserve(),
                base.currentProjectUsageConservativeUpper(), base.effectiveProjectQuota(), required);
        IoGuard upgradeGuard = () -> {
            guard.check();
            if (Files.getFileStore(home).getUsableSpace() < required) throw new IOException("in-place Maven installation reserve became unavailable");
        };
        Path tools = Files.createDirectory(root.resolve("tools/default-maven-upgrade"));
        Path archive = tools.resolve("apache-maven-" + MAVEN_VERSION + "-bin.zip");
        Path checksum = tools.resolve("official.sha512");
        download(MAVEN_CHECKSUM, checksum, 1024);
        if (!Files.readString(checksum, StandardCharsets.US_ASCII).strip().equals(MAVEN_ZIP_SHA512)) {
            throw new IOException("official Maven checksum differs from the reviewed stable release pin");
        }
        download(MAVEN_ZIP, archive, 16 * MIB);
        requireMavenArchiveChecksum(archive, MAVEN_ZIP_SHA512);
        upgradeGuard.check();
        Path extracted = Files.createDirectory(tools.resolve("extracted"));
        extractMaven(archive, extracted);
        Path replacement = extracted.resolve("apache-maven-" + MAVEN_VERSION);
        Path backup = tools.resolve("original-installation");
        List<FilePin> original = installationFiles(home), vendor = installationFiles(replacement);
        List<String> preserved = List.of("conf/settings.xml", "conf/toolchains.xml").stream()
                .filter(name -> Files.isRegularFile(home.resolve(name), LinkOption.NOFOLLOW_LINKS)).toList();
        publish(root.resolve("logs/maven-upgrade-plan.json"), new MavenUpgradePlan(machine, Instant.now().toString(),
                "PLANNED_NOT_ADMITTED", before, MAVEN_ZIP.toString(), MAVEN_CHECKSUM.toString(), measure(archive),
                original, vendor, backup.toString(), preserved, installationBudget));
        replaceMavenInstallation(before, replacement, backup, upgradeGuard);
    }

    static void requireMavenArchiveChecksum(Path archive, String expectedSha512) throws IOException {
        if (!MAVEN_ZIP_SHA512.equals(expectedSha512) || !digest(archive, "SHA-512").equals(expectedSha512)) {
            throw new IOException("reviewed official Maven archive SHA-512 mismatch");
        }
    }

    /** The final installation stays at its observed home; old vendor files are backed up exactly. */
    static void replaceMavenInstallation(MavenObservation before, Path replacement, Path backup, IoGuard guard)
            throws IOException {
        Path home = Path.of(before.reportedHome()).toRealPath(), staged = replacement.toRealPath();
        if (home.getParent() == null || staged.startsWith(home) || home.startsWith(staged)
                || backup.toAbsolutePath().normalize().startsWith(home) || Files.exists(backup, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("independent exact Maven home/stage/fresh backup required");
        }
        List<FilePin> originals = installationFiles(home), replacements = installationFiles(staged);
        if (!before.launcherRef().equals(measure(Path.of(before.launcherRef().path()))) || replacements.isEmpty()) {
            throw new IOException("observed Maven launcher drift or missing replacement");
        }
        guard.check(); Files.createDirectory(backup);
        copyInstallation(originals, home, backup);
        for (String name : List.of("conf/settings.xml", "conf/toolchains.xml")) {
            Path active = home.resolve(name);
            if (Files.isRegularFile(active, LinkOption.NOFOLLOW_LINKS)) {
                Files.createDirectories(staged.resolve(name).getParent());
                Files.copy(active, staged.resolve(name), StandardCopyOption.REPLACE_EXISTING);
            }
        }
        if (!originals.equals(installationFiles(home))) throw new IOException("Maven installation drift before replacement");
        guard.check();
        // Delete only the previously measured regular files; retain the home directory and its ACL/owner.
        for (FilePin file : originals) Files.delete(Path.of(file.path()));
        copyInstallation(installationFiles(staged), staged, home);
        for (String name : List.of("mvn", "mvnDebug")) {
            Path script = home.resolve("bin/" + name);
            if (!System.getProperty("os.name").startsWith("Windows") && Files.isRegularFile(script)
                    && !script.toFile().setExecutable(true, false)) throw new IOException("Unix Maven launcher permission update failed");
        }
        for (FilePin file : installationFiles(staged)) {
            FilePin actual = measure(home.resolve(staged.relativize(Path.of(file.path()))));
            if (actual.bytes() != file.bytes() || !actual.sha256().equals(file.sha256())) throw new IOException("Maven vendor/configuration postcheck mismatch");
        }
        guard.check();
    }

    private static void copyInstallation(List<FilePin> files, Path source, Path target) throws IOException {
        for (FilePin file : files) {
            Path from = Path.of(file.path()), destination = target.resolve(source.relativize(from));
            if (!file.equals(measure(from))) throw new IOException("Maven source changed during exact copy");
            Files.createDirectories(destination.getParent());
            Files.copy(from, destination, StandardCopyOption.COPY_ATTRIBUTES);
            FilePin copied = measure(destination);
            if (copied.bytes() != file.bytes() || !copied.sha256().equals(file.sha256())) throw new IOException("Maven backup/install copy mismatch");
        }
    }

    private static List<FilePin> installationFiles(Path root) throws IOException {
        if (Files.isSymbolicLink(root) || !Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("regular Maven installation directory required");
        List<FilePin> files = new ArrayList<>(); long bytes = 0;
        try (var paths = Files.walk(root)) {
            for (Path path : paths.sorted().toList()) {
                if (Files.isSymbolicLink(path) || (!Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)
                        && !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS))) throw new IOException("linked/nonregular Maven installation entry refused");
                if (Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) {
                    FilePin file = measure(path); files.add(file); bytes = Math.addExact(bytes, file.bytes());
                    if (files.size() > 5000 || bytes > 48 * MIB) throw new IOException("bounded Maven installation backup required");
                }
            }
        }
        return List.copyOf(files);
    }

    private static void requireStableMinimum(String version) {
        requireStableVersion(version);
        String[] actual = version.split("\\."), minimum = MINIMUM_MAVEN_VERSION.split("\\.");
        for (int index = 0; index < 3; index++) {
            int comparison = new BigInteger(actual[index]).compareTo(new BigInteger(minimum[index]));
            if (comparison > 0) return;
            if (comparison < 0) throw new IllegalArgumentException("default Maven version is below the stable minimum");
        }
    }

    private static void requireStableVersion(String version) {
        if (version == null || version.length() > 64 || !version.matches("[0-9]+\\.[0-9]+\\.[0-9]+")) {
            throw new IllegalArgumentException("bounded stable Maven version required");
        }
    }

    public static Policy readPolicy(byte[] raw) throws IOException {
        J root = parse(raw);
        if (!string(field(root, "schema")).equals("xar-storage-retention-policy-v1")
                || !string(field(root, "policy_version")).equals("1.0.0")) {
            throw new IOException("unsupported shared storage policy version");
        }
        J capacity = field(root, "capacity");
        return new Policy(integer(field(capacity, "safety_floor_bytes")), integer(field(capacity, "safety_ceiling_bytes")),
                decimal(field(capacity, "safety_volume_fraction")), integer(field(capacity, "default_project_quota_ceiling_bytes")),
                 decimal(field(capacity, "default_project_quota_volume_fraction")), integer(field(capacity, "quota_override_max_hours")));
    }

    public static VolumeBudget calculate(Policy policy, long total, long available, long peak,
                                        long other, long reserve, long current) {
        return calculate(policy, total, available, peak, other, reserve, current, null, Instant.EPOCH, Instant.EPOCH);
    }

    public static VolumeBudget calculate(Policy policy, long total, long available, long peak,
                                         long other, long reserve, long current, QuotaOverride override,
                                         Instant observed, Instant deadline) {
        if (total <= 0 || available < 0 || peak < 0 || other < 0 || reserve <= 0 || current < 0) {
            throw new IllegalArgumentException("complete nonnegative actual budget inputs required");
        }
        long safety = Math.max(policy.safetyFloor(), Math.min(policy.safetyCeiling(),
                BigDecimal.valueOf(total).multiply(policy.safetyVolumeFraction()).setScale(0, RoundingMode.CEILING).longValueExact()));
        long quota = Math.min(policy.quotaCeiling(), BigDecimal.valueOf(total).multiply(policy.quotaVolumeFraction())
                .setScale(0, RoundingMode.FLOOR).longValueExact());
        if (override != null) {
            Instant review = Instant.parse(override.reviewAtUtc());
            if (Math.addExact(current, peak) <= quota || !review.isAfter(observed) || review.isAfter(deadline)
                    || review.isAfter(observed.plus(Duration.ofHours(policy.quotaOverrideMaxHours())))
                    || override.maxProjectBytes() <= quota) {
                throw new IllegalArgumentException("unneeded, expired or unbounded project quota override rejected");
            }
            quota = override.maxProjectBytes();
        }
        long required = Math.addExact(Math.addExact(peak, other), Math.addExact(reserve, safety));
        if (available < required || Math.addExact(current, peak) > quota) {
            throw new IllegalArgumentException("shared storage free-space or project quota does not admit this task");
        }
        return new VolumeBudget(total, available, peak, other, reserve, safety, current, quota, required);
    }

    public static FilePin measure(Path path) throws IOException {
        BasicFileAttributes before = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (!before.isRegularFile() || before.isSymbolicLink()) throw new IOException("regular exact bootstrap file required");
        String hash = digest(path, "SHA-256");
        BasicFileAttributes after = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (before.size() != after.size() || !Objects.equals(before.fileKey(), after.fileKey())
                || !before.lastModifiedTime().equals(after.lastModifiedTime())) throw new IOException("bootstrap file changed during measurement");
        return new FilePin(path.toAbsolutePath().normalize().toString(), before.size(), hash);
    }

    private static Map<String, VolumeBudget> budgets(Policy policy, List<Path> projectRoots, Path taskRoot,
                                                     Path systemRoot, long reserve, QuotaOverride override,
                                                     Instant observed, Instant deadline, Map<String, QuotaOverride> overrides) throws IOException {
        List<Path> roots = projectRoots.stream().map(path -> path.toAbsolutePath().normalize()).distinct().toList();
        Map<String, Long> usage = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for (Path root : roots) {
            if (roots.stream().anyMatch(other -> !root.equals(other) && root.startsWith(other))) continue;
            long bytes = 0;
            int count = 0;
            try (var paths = Files.walk(root)) {
                for (Path path : paths.toList()) {
                    if (++count > 100000 || Files.isSymbolicLink(path)) throw new IOException("bounded original project inventory required");
                    if (Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) {
                        bytes = Math.addExact(bytes, Math.addExact(Files.size(path), 65536));
                    }
                }
            }
            usage.merge(root.getRoot().toString(), bytes, Math::addExact);
        }
        Map<String, VolumeBudget> result = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for (Path volume : List.of(taskRoot.getRoot(), systemRoot.getRoot())) {
            FileStore store = Files.getFileStore(volume);
            boolean taskVolume = volume.equals(taskRoot.getRoot());
            long total = store.getTotalSpace(), current = usage.getOrDefault(volume.toString(), 0L);
            long peak = taskVolume ? 4 * GIB : 0;
            long defaultQuota = Math.min(policy.quotaCeiling(), BigDecimal.valueOf(total).multiply(policy.quotaVolumeFraction())
                    .setScale(0, RoundingMode.FLOOR).longValueExact());
            QuotaOverride effective = Math.addExact(current, peak) > defaultQuota ? override : null;
            if (effective != null) overrides.put(volume.toString(), effective);
            result.put(volume.toString(), calculate(policy, total, store.getUsableSpace(), peak, 0, reserve, current,
                    effective, observed, deadline));
        }
        return Map.copyOf(result);
    }

    private static void requireFree(Map<String, VolumeBudget> volumes) throws IOException {
        for (var volume : volumes.entrySet()) {
            if (Files.getFileStore(Path.of(volume.getKey())).getUsableSpace() < volume.getValue().requiredFree()) {
                throw new IOException("fresh shared storage free-space threshold rejected");
            }
        }
    }

    private static void guard(Path root, Map<String, VolumeBudget> volumes, Instant expiry) throws IOException {
        guard(root, volumes, expiry, () -> {}, path -> Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS));
    }

    static void guard(Path root, Map<String, VolumeBudget> volumes, Instant expiry,
                      IoGuard childDeadline, AttributeReader reader) throws IOException {
        IoGuard active = () -> {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("bootstrap guard interrupted");
            if (!Instant.now().isBefore(expiry)) throw new IOException("finite hosted capacity authority expired");
            childDeadline.check();
        };
        active.check();
        requireFree(volumes);
        for (String name : List.of("m2", "build", "tools", "scratch", "logs", "artifacts")) {
            long size = 0;
            try (var paths = Files.walk(root.resolve(name))) {
                for (Path path : paths.toList()) {
                    active.check();
                    try {
                        BasicFileAttributes attributes = guardedAttributes(path, name.equals("scratch"), reader, active);
                        if (attributes.isSymbolicLink()) throw new IOException("linked task output refused");
                        if (attributes.isRegularFile()) size = Math.addExact(size, attributes.size());
                    }
                    catch (java.nio.file.NoSuchFileException removedTemporary) { }
                }
            }
            if (size > PARTS.get(name.equals("logs") ? "metadata_logs" : name)) throw new IOException("task part budget exceeded: " + name);
        }
    }

    private static BasicFileAttributes guardedAttributes(Path path, boolean scratch,
                                                        AttributeReader reader, IoGuard active) throws IOException {
        // Windows can briefly deny metadata while a JUnit scratch file is being deleted.
        // A successful no-follow read or an actual NoSuchFileException resolves that race;
        // persistent denial, links, and every other I/O failure remain fatal.
        for (int attempt = 0; ; attempt++) {
            active.check();
            try { return reader.read(path); }
            catch (AccessDeniedException denied) {
                if (!scratch || attempt == 3) throw denied;
                active.check();
                try { Thread.sleep(25); }
                catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    throw new InterruptedIOException("bootstrap scratch metadata retry interrupted");
                }
            }
        }
    }

    private static List<FilePin> sourcePins(Path source) throws IOException {
        List<FilePin> result = new ArrayList<>();
        try (var paths = Files.walk(source.resolve("src"))) {
            for (Path path : paths.filter(Files::isRegularFile).sorted().toList()) result.add(measure(path));
        }
        result.add(measure(source.resolve("pom.xml")));
        return List.copyOf(result);
    }

    private static void runPlain(List<String> command, Path cwd, Map<String, String> environment,
                                 Path log, Duration timeout, Instant expiry, Path root,
                                 Map<String, VolumeBudget> volumes) throws IOException, InterruptedException {
        guard(root, volumes, expiry);
        ProcessBuilder builder = new ProcessBuilder(command).directory(cwd.toFile()).redirectErrorStream(true)
                .redirectOutput(ProcessBuilder.Redirect.to(log.toFile()));
        builder.environment().clear();
        builder.environment().putAll(environment);
        if (Files.exists(log)) throw new IOException("fresh bootstrap command log required");
        Process child = builder.start();
        long until = System.nanoTime() + timeout.toNanos();
        try {
            while (!child.waitFor(250, TimeUnit.MILLISECONDS)) {
                guard(root, volumes, expiry, () -> {
                    if (System.nanoTime() >= until) throw new IOException("bootstrap child timeout/log budget");
                }, path -> Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS));
                if (System.nanoTime() >= until || Files.size(log) > 4 * MIB) throw new IOException("bootstrap child timeout/log budget");
            }
            if (child.exitValue() != 0 || Files.size(log) > 4 * MIB) throw new IOException("bootstrap child failed; see " + log.getFileName());
        } finally {
            List<ProcessHandle> descendants = child.descendants().toList();
            for (ProcessHandle handle : descendants.reversed()) if (handle.isAlive()) handle.destroyForcibly();
            if (child.isAlive()) child.destroyForcibly();
            if (!child.waitFor(10, TimeUnit.SECONDS)) throw new IOException("bootstrap root exit was not observed");
            for (ProcessHandle handle : descendants) if (handle.isAlive()) throw new IOException("bootstrap descendant exit unavailable");
        }
    }

    private static String machineId(Path systemRoot) throws IOException, InterruptedException {
        String hostname = nativeText(List.of(systemRoot.resolve("System32/hostname.exe").toString())).strip();
        String output = nativeText(List.of(systemRoot.resolve("System32/reg.exe").toString(), "query",
                "HKLM\\SOFTWARE\\Microsoft\\Cryptography", "/v", "MachineGuid", "/reg:64"));
        var match = Pattern.compile("(?im)^\\s*MachineGuid\\s+REG_SZ\\s+([^\\r\\n]+)\\s*$").matcher(output);
        if (!match.find()) throw new IOException("actual 64bit Windows machine identity unavailable");
        String token = match.group(1).strip();
        if (match.find() || !token.matches("[0-9a-fA-F-]{36}")) throw new IOException("unambiguous actual Windows machine token required");
        String slug = hostname.strip().toLowerCase(java.util.Locale.ROOT).replaceAll("[^a-z0-9]+", "-").replaceAll("^-|-$", "");
        if (slug.isEmpty()) throw new IOException("actual hostname unavailable");
        slug = slug.substring(0, Math.min(32, slug.length())).replaceAll("-+$", "");
        try {
            String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(("windows-machine-guid:" + token).getBytes(StandardCharsets.UTF_8)));
            return slug + "-" + hash.substring(0, 10);
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    private static String nativeText(List<String> command) throws IOException, InterruptedException {
        Process child = new ProcessBuilder(command).redirectErrorStream(true).start();
        try {
            if (!child.waitFor(10, TimeUnit.SECONDS)) throw new IOException("native identity query timeout");
            byte[] raw = child.getInputStream().readNBytes(8193);
            if (child.exitValue() != 0 || raw.length > 8192) throw new IOException("bounded actual identity query failed");
            return new String(raw, StandardCharsets.UTF_8);
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }

    private static void download(URI uri, Path target, long maximum) throws IOException, InterruptedException {
        HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(15))
                .followRedirects(HttpClient.Redirect.NEVER).build();
        HttpResponse<InputStream> response = client.send(HttpRequest.newBuilder(uri).timeout(Duration.ofMinutes(2)).GET().build(),
                HttpResponse.BodyHandlers.ofInputStream());
        try (InputStream input = response.body(); var output = Files.newOutputStream(target, StandardOpenOption.CREATE_NEW)) {
            if (response.statusCode() != 200) throw new IOException("official fixed tool download unavailable");
            transferBounded(input, output, maximum, Duration.ofMinutes(2));
        }
    }

    /** A body stream can stall after headers; the request's header timeout is insufficient. */
    static void transferBounded(InputStream input, OutputStream output, long maximum, Duration timeout)
            throws IOException, InterruptedException {
        if (maximum <= 0 || timeout.isNegative() || timeout.isZero()) {
            throw new IllegalArgumentException("positive complete HTTP body bounds required");
        }
        CompletableFuture<Void> transfer = CompletableFuture.runAsync(() -> {
            try {
                byte[] buffer = new byte[65536];
                long count = 0;
                int length;
                while ((length = input.read(buffer)) != -1) {
                    count = Math.addExact(count, length);
                    if (count > maximum) throw new IOException("bounded official tool archive required");
                    output.write(buffer, 0, length);
                }
            } catch (IOException error) { throw new UncheckedIOException(error); }
        });
        try {
            transfer.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
        } catch (TimeoutException error) {
            transfer.cancel(true);
            input.close();
            throw new IOException("complete official HTTP body deadline expired", error);
        } catch (ExecutionException error) {
            if (error.getCause() instanceof UncheckedIOException io) throw io.getCause();
            throw new IOException("official HTTP body transfer failed", error.getCause());
        } catch (InterruptedException error) {
            transfer.cancel(true);
            input.close();
            Thread.currentThread().interrupt();
            throw error;
        }
    }

    static void extractMaven(Path archive, Path destination) throws IOException {
        long size = 0;
        int entries = 0;
        Path root = destination.toAbsolutePath().normalize();
        try (ZipInputStream input = new ZipInputStream(Files.newInputStream(archive))) {
            ZipEntry entry;
            while ((entry = input.getNextEntry()) != null) {
                String name = entry.getName();
                if (++entries > 5000 || name.indexOf('\\') >= 0 || name.indexOf(':') >= 0 || name.indexOf('\0') >= 0) {
                    throw new IOException("bounded canonical archive entries required");
                }
                Path path = root.resolve(name).normalize();
                if (!path.startsWith(root) || path.equals(root)) throw new IOException("archive path escaped task tools root");
                if (entry.isDirectory()) { Files.createDirectories(path); continue; }
                Files.createDirectories(path.getParent());
                try (var output = Files.newOutputStream(path, StandardOpenOption.CREATE_NEW)) {
                    byte[] buffer = new byte[65536];
                    int count;
                    while ((count = input.read(buffer)) != -1) {
                        size = Math.addExact(size, count);
                        if (size > 64 * MIB) throw new IOException("unpacked tool archive budget exceeded");
                        output.write(buffer, 0, count);
                    }
                }
            }
        }
    }

    private static String digest(Path path, String algorithm) throws IOException {
        try {
            MessageDigest hash = MessageDigest.getInstance(algorithm);
            try (InputStream input = Files.newInputStream(path)) {
                byte[] buffer = new byte[65536];
                int count;
                while ((count = input.read(buffer)) != -1) hash.update(buffer, 0, count);
            }
            return HexFormat.of().formatHex(hash.digest());
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    private static Map<String, String> arguments(String[] arguments) {
        List<String> allowed = List.of("--repo-root", "--work-root", "--python-executable", "--system-growth-reserve-bytes", "--max-project-bytes");
        if (arguments.length != allowed.size() * 2) throw new IllegalArgumentException("all five explicit bootstrap parameters required");
        Map<String, String> result = new LinkedHashMap<>();
        for (int index = 0; index < arguments.length; index += 2) {
            if (!allowed.contains(arguments[index]) || result.putIfAbsent(arguments[index], arguments[index + 1]) != null) {
                throw new IllegalArgumentException("unknown or duplicate bootstrap parameter");
            }
        }
        return Map.copyOf(result);
    }

    static FilePin publish(Path path, Record value) throws IOException {
        byte[] raw = emit(toJson(value)).getBytes(StandardCharsets.UTF_8);
        if (raw.length > MIB) throw new IOException("bounded complete bootstrap metadata required");
        Files.write(path, raw, StandardOpenOption.CREATE_NEW);
        return measure(path);
    }

    // A small strict JDK-only boundary is necessary before the first JSON dependency exists.
    // It is confined to policy/bootstrap metadata; production HTTP continues to use StrictJson/Jackson.
    private sealed interface J permits JO, JA, JS, JN, JB, JNull {}
    private record JO(Map<String, J> values) implements J { JO { values = Map.copyOf(values); } }
    private record JA(List<J> values) implements J { JA { values = List.copyOf(values); } }
    private record JS(String value) implements J {}
    private record JN(BigDecimal value, boolean integerToken) implements J {}
    private record JB(boolean value) implements J {}
    private enum JNull implements J { VALUE }

    private static J parse(byte[] raw) throws IOException {
        if (raw.length > MIB) throw new IOException("bounded bootstrap JSON required");
        String source = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        Parser parser = new Parser(source);
        J value = parser.value(0);
        parser.space();
        if (parser.position != source.length()) throw new IOException("trailing bootstrap JSON token");
        return value;
    }

    private static J field(J value, String name) throws IOException {
        if (!(value instanceof JO object) || !object.values().containsKey(name)) throw new IOException("missing bootstrap JSON field: " + name);
        return object.values().get(name);
    }
    private static String string(J value) throws IOException {
        if (!(value instanceof JS text)) throw new IOException("exact bootstrap JSON string required");
        return text.value();
    }
    private static BigDecimal decimal(J value) throws IOException {
        if (!(value instanceof JN number)) throw new IOException("exact bootstrap JSON number required");
        return number.value();
    }
    private static long integer(J value) throws IOException {
        BigDecimal number = decimal(value);
        if (!(value instanceof JN token) || !token.integerToken()) throw new IOException("integer JSON token required");
        try { return number.longValueExact(); }
        catch (ArithmeticException error) { throw new IOException("bounded exact bootstrap integer required", error); }
    }

    private static final class Parser {
        private final String source;
        private int position;
        private int tokens;
        Parser(String source) { this.source = source; }
        void space() { while (position < source.length() && " \r\n\t".indexOf(source.charAt(position)) >= 0) position++; }
        J value(int depth) throws IOException {
            space();
            if (depth > 32 || ++tokens > 100000 || position == source.length()) throw new IOException("bounded complete bootstrap JSON required");
            char first = source.charAt(position);
            if (first == '"') return new JS(text());
            if (first == '{') {
                position++; space(); Map<String, J> values = new LinkedHashMap<>();
                if (take('}')) return new JO(values);
                do {
                    space(); String key = text(); space(); expect(':');
                    if (values.putIfAbsent(key, value(depth + 1)) != null) throw new IOException("duplicate bootstrap JSON key");
                    space(); if (take('}')) return new JO(values); expect(',');
                } while (true);
            }
            if (first == '[') {
                position++; space(); List<J> values = new ArrayList<>();
                if (take(']')) return new JA(values);
                do { values.add(value(depth + 1)); space(); if (take(']')) return new JA(values); expect(','); } while (true);
            }
            for (String literal : List.of("true", "false", "null")) {
                if (source.startsWith(literal, position)) {
                    position += literal.length();
                    return literal.equals("null") ? JNull.VALUE : new JB(literal.equals("true"));
                }
            }
            int start = position;
            while (position < source.length() && "-+0123456789.eE".indexOf(source.charAt(position)) >= 0) position++;
            String token = source.substring(start, position);
            if (token.length() > 64 || !token.matches("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?")) throw new IOException("invalid bootstrap JSON token");
            try {
                BigDecimal number = new BigDecimal(token);
                if (number.precision() > 30 || Math.abs((long) number.scale()) > 30) throw new IOException("bounded bootstrap JSON numeric domain required");
                return new JN(number, token.matches("-?(0|[1-9][0-9]*)"));
            } catch (NumberFormatException error) { throw new IOException("invalid bootstrap JSON number", error); }
        }
        String text() throws IOException {
            expect('"'); StringBuilder result = new StringBuilder();
            while (position < source.length()) {
                char character = source.charAt(position++);
                if (character == '"') { validateUnicode(result.toString()); return result.toString(); }
                if (character < 32) throw new IOException("unescaped bootstrap JSON control");
                if (character != '\\') { result.append(character); continue; }
                if (position == source.length()) throw new IOException("truncated bootstrap JSON escape");
                char escaped = source.charAt(position++);
                switch (escaped) {
                    case '"', '\\', '/' -> result.append(escaped);
                    case 'b' -> result.append('\b'); case 'f' -> result.append('\f');
                    case 'n' -> result.append('\n'); case 'r' -> result.append('\r'); case 't' -> result.append('\t');
                    case 'u' -> {
                        if (position + 4 > source.length()) throw new IOException("truncated bootstrap Unicode escape");
                        String digits = source.substring(position, position + 4);
                        if (!digits.matches("[0-9a-fA-F]{4}")) throw new IOException("invalid bootstrap Unicode escape");
                        result.append((char) Integer.parseInt(digits, 16)); position += 4;
                    }
                    default -> throw new IOException("invalid bootstrap JSON escape");
                }
            }
            throw new IOException("unterminated bootstrap JSON string");
        }
        boolean take(char value) { if (position < source.length() && source.charAt(position) == value) { position++; return true; } return false; }
        void expect(char value) throws IOException { if (!take(value)) throw new IOException("bootstrap JSON punctuation at offset " + position); }
    }

    private static J toJson(Object value) throws IOException {
        if (value == null) return JNull.VALUE;
        if (value instanceof String text) { validateUnicode(text); return new JS(text); }
        if (value instanceof Enum<?> branch) return new JS(branch.name());
        if (value instanceof Boolean flag) return new JB(flag);
        if (value instanceof Long number) return new JN(BigDecimal.valueOf(number), true);
        if (value instanceof Integer number) return new JN(BigDecimal.valueOf(number), true);
        if (value instanceof BigDecimal number) return new JN(number, number.scale() <= 0);
        if (value instanceof List<?> list) { List<J> result = new ArrayList<>(); for (Object item : list) result.add(toJson(item)); return new JA(result); }
        if (value instanceof Map<?, ?> map) {
            Map<String, J> result = new TreeMap<>();
            for (var entry : map.entrySet()) {
                if (!(entry.getKey() instanceof String key)) throw new IOException("string bootstrap metadata keys required");
                result.put(key, toJson(entry.getValue()));
            }
            return new JO(result);
        }
        if (value instanceof Record record) {
            Map<String, J> fields = new TreeMap<>();
            for (var component : record.getClass().getRecordComponents()) {
                String name = component.getName().replaceAll("([a-z0-9])([A-Z])", "$1_$2").toLowerCase(java.util.Locale.ROOT);
                try { fields.put(name, toJson(component.getAccessor().invoke(record))); }
                catch (IllegalAccessException | InvocationTargetException error) { throw new IOException("typed bootstrap record serialization failed", error); }
            }
            return new JO(fields);
        }
        throw new IOException("unsupported bootstrap metadata type");
    }
    private static String emit(J value) throws IOException {
        if (value instanceof JNull) return "null";
        if (value instanceof JB flag) return Boolean.toString(flag.value());
        if (value instanceof JN number) return number.value().toPlainString();
        if (value instanceof JS text) {
            validateUnicode(text.value()); StringBuilder result = new StringBuilder("\"");
            for (int index = 0; index < text.value().length(); index++) {
                char character = text.value().charAt(index);
                if (character == '"' || character == '\\') result.append('\\').append(character);
                else if (character < 32) result.append(String.format(java.util.Locale.ROOT, "\\u%04x", (int) character));
                else result.append(character);
            }
            return result.append('"').toString();
        }
        if (value instanceof JA array) { List<String> parts = new ArrayList<>(); for (J item : array.values()) parts.add(emit(item)); return "[" + String.join(",", parts) + "]"; }
        if (value instanceof JO object) {
            List<String> fields = new ArrayList<>();
            for (var entry : new TreeMap<>(object.values()).entrySet()) fields.add(emit(new JS(entry.getKey())) + ":" + emit(entry.getValue()));
            return "{" + String.join(",", fields) + "}";
        }
        throw new IOException("unknown typed bootstrap JSON branch");
    }
    private static void validateUnicode(String text) throws IOException {
        for (int index = 0; index < text.length(); index++) {
            char character = text.charAt(index);
            if (Character.isHighSurrogate(character)) {
                if (++index >= text.length() || !Character.isLowSurrogate(text.charAt(index))) throw new IOException("unpaired bootstrap Unicode surrogate");
            } else if (Character.isLowSurrogate(character)) throw new IOException("unpaired bootstrap Unicode surrogate");
        }
    }
}
