package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
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
                                   boolean bootstrapNativeJobHardBound,
                                  boolean bootstrapAloneGrantsPipelineQualification) {}

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
        String failure = null;
        boolean completed = false;
        try {
            Path source = repo.resolve("java/ck3-control/build-tools");
            List<FilePin> before = sourcePins(source);
            Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
            environment.putAll(System.getenv());
            environment.put("JAVA_HOME", javaHome.toString());
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
            runPlain(List.of(systemRoot.resolve("System32/cmd.exe").toString(), "/d", "/c", versionBatch.toString()),
                    root.resolve("scratch"), environment, root.resolve("logs/maven-version.log"), Duration.ofSeconds(30), expiry, root, volumes);
            defaultMaven = requireDefaultMaven(Files.readString(root.resolve("logs/maven-version.log")));
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
                    "xar.java-control-CI-bootstrap-actual/v2", machine, started, Instant.now().toString(),
                    completed && failure == null ? "PIPELINE_EXIT_0" : "RED", failure, planRef, defaultMaven, false, false));
        }
        if (!completed || failure != null) throw new IllegalStateException(failure);
    }

    /** Existing default command is authoritative. No download, PATH change or installation relocation. */
    public static DefaultMaven requireDefaultMaven(String output) throws IOException {
        if (output == null || output.length() > 65536) throw new IOException("bounded actual Maven version output required");
        var versions = Pattern.compile("(?m)^Apache Maven ([^\\r\\n ]+)(?: [^\\r\\n]*)?$").matcher(output);
        if (!versions.find()) throw new IOException("default mvn did not report its version; environment not qualified");
        String version = versions.group(1);
        if (versions.find()) throw new IOException("ambiguous default Maven version");
        try { requireStableMinimum(version); }
        catch (IllegalArgumentException error) {
            throw new IOException("default mvn requires an in-place upgrade to stable >=" + MINIMUM_MAVEN_VERSION
                    + "; this bootstrap does not replace its installation or PATH", error);
        }
        var homes = Pattern.compile("(?m)^Maven home: ([^\\r\\n]+)$").matcher(output);
        if (!homes.find()) throw new IOException("default mvn did not report its actual installation home");
        Path home = Path.of(homes.group(1).strip()).toRealPath();
        if (homes.find()) throw new IOException("ambiguous default Maven installation home");
        return new DefaultMaven("mvn", version, MINIMUM_MAVEN_VERSION, home.toString(), measure(home.resolve("bin/mvn.cmd")));
    }

    private static void requireStableMinimum(String version) {
        if (version == null || version.length() > 64 || !version.matches("[0-9]+\\.[0-9]+\\.[0-9]+")) {
            throw new IllegalArgumentException("bounded stable Maven version required");
        }
        String[] actual = version.split("\\."), minimum = MINIMUM_MAVEN_VERSION.split("\\.");
        for (int index = 0; index < 3; index++) {
            int comparison = new BigInteger(actual[index]).compareTo(new BigInteger(minimum[index]));
            if (comparison > 0) return;
            if (comparison < 0) throw new IllegalArgumentException("default Maven version is below the stable minimum");
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
        if (!Instant.now().isBefore(expiry)) throw new IOException("finite hosted capacity authority expired");
        requireFree(volumes);
        for (String name : List.of("m2", "build", "tools", "scratch", "logs", "artifacts")) {
            long size = 0;
            try (var paths = Files.walk(root.resolve(name))) {
                for (Path path : paths.toList()) {
                    if (Files.isSymbolicLink(path)) throw new IOException("linked task output refused");
                    try { if (Files.isRegularFile(path)) size = Math.addExact(size, Files.size(path)); }
                    catch (java.nio.file.NoSuchFileException removedTemporary) { }
                }
            }
            if (size > PARTS.get(name.equals("logs") ? "metadata_logs" : name)) throw new IOException("task part budget exceeded: " + name);
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
                guard(root, volumes, expiry);
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

    private static FilePin publish(Path path, Record value) throws IOException {
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
