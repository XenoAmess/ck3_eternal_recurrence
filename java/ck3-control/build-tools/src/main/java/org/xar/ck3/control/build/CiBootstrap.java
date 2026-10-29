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
import java.nio.file.FileVisitResult;
import java.nio.file.FileVisitor;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
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
    /** Sole oracle engine, kept here so the JDK21 source-file entry has no sibling dependency. */
    static final class OracleEnvironment {
        private OracleEnvironment() { }

        public record Inputs(String python, String repositoryRoot) {
            public Inputs {
                absolute(python); absolute(repositoryRoot);
            }
        }

        /** Live validation. Both repository roles must independently name the same real source root. */
        public static Inputs require(Map<String, String> environment) throws IOException {
            Path python = plainFile(required(environment, "XAR_ORACLE_PYTHON"));
            Path oracle = plainDirectory(required(environment, "XAR_ORACLE_REPO"));
            Path canonical = plainDirectory(required(environment, "XAR_REPO_ROOT"));
            if (!oracle.equals(canonical))
                throw new IOException("XAR_ORACLE_REPO and XAR_REPO_ROOT must bind the same actual repository");
            Path workflow = oracle.resolve(".github/workflows/static-ci.yml");
            if (!Files.isRegularFile(workflow, LinkOption.NOFOLLOW_LINKS) || Files.size(workflow) < 1
                    || !workflow.toRealPath().equals(workflow))
                throw new IOException("Actual canonical workflow source is unavailable");
            return new Inputs(python.toString(), oracle.toString());
        }

        /** A producer deliberately sets all three roles; no missing role is inferred by a reader. */
        public static Map<String, String> bind(Path repository, Path python, Map<String, String> inherited) throws IOException {
            Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
            environment.putAll(inherited);
            environment.put("XAR_ORACLE_PYTHON", python.toString());
            environment.put("XAR_ORACLE_REPO", repository.toString());
            environment.put("XAR_REPO_ROOT", repository.toString());
            require(environment);
            return Map.copyOf(environment);
        }

        /** Keep the explicit oracle repository when the selected Java source graph has a different root. */
        public static Map<String, String> bindSelectedInterpreter(Path python, Map<String, String> inherited) throws IOException {
            Inputs original = require(inherited);
            Path selected = plainFile(python.toString());
            if (!selected.equals(Path.of(original.python())))
                throw new IOException("Selected CI interpreter differs from explicit XAR_ORACLE_PYTHON");
            return bind(Path.of(original.repositoryRoot()), selected, inherited);
        }

        private static String required(Map<String, String> environment, String name) throws IOException {
            String value = environment.get(name);
            if (value == null || value.isBlank()) throw new IOException("NOT EXECUTED: explicit " + name + " required");
            return value;
        }
        private static Path plainFile(String value) throws IOException {
            Path path = absolute(value);
            if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.size(path) < 1
                    || !path.toRealPath().equals(path)) throw new IOException("Plain actual interpreter required: " + path);
            return path;
        }
        private static Path plainDirectory(String value) throws IOException {
            Path path = absolute(value);
            if (!Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS) || !path.toRealPath().equals(path))
                throw new IOException("Plain actual repository required: " + path);
            return path;
        }
        private static Path absolute(String value) {
            if (value == null || value.isBlank() || value.length() > 4096
                    || value.codePoints().anyMatch(point -> point < 32 || point == 127))
                throw new IllegalArgumentException("Bounded plain absolute source path required");
            Path path = Path.of(value);
            if (!path.isAbsolute() || !path.equals(path.normalize()))
                throw new IllegalArgumentException("Canonical absolute source path required");
            return path;
        }
    }

    public static final String PLAN_SCHEMA = "xar.java-control-CI-bootstrap-plan/v1";
    public static final String COMPLETE_PLAN_SCHEMA = "xar.java-control-CI-bootstrap-plan/v2";
    public static final String HISTORICAL_MANAGED_PLAN_SCHEMA = "xar.java-control-CI-bootstrap-plan/v3";
    public static final String MANAGED_PLAN_SCHEMA = "xar.java-control-CI-bootstrap-plan/v4";
    public static final String SOFTWARE_PLAN_SCHEMA = "xar.java-control-CI-software-plan/v1";
    public static final String TOOLS_POSTQUALIFICATION_POLICY = "REAL_QUALIFIED_JAR_OWN_LARGE_INPUTS_JUNIT2_REQUIRED";
    public enum ToolsPostqualificationState { MISSING_FULL_OWN_INPUTS }
    public record ToolsPostqualificationAvailability(String schema,ToolsPostqualificationState state,
            List<String> missingDependencies,boolean toolsAdopted,boolean actualJunitExecuted) {
        public ToolsPostqualificationAvailability {
            missingDependencies=List.copyOf(missingDependencies);
            if(!"xar.control-ci-tools-postqualification-availability/v1".equals(schema)
                    ||state!=ToolsPostqualificationState.MISSING_FULL_OWN_INPUTS||missingDependencies.isEmpty()||toolsAdopted||actualJunitExecuted)
                throw new IllegalArgumentException("Missing actual full Own inputs grant no Tools adoption or JUnit execution");
        }
    }
    public static ToolsPostqualificationAvailability missingToolsPostqualification() {
        return new ToolsPostqualificationAvailability("xar.control-ci-tools-postqualification-availability/v1",
                ToolsPostqualificationState.MISSING_FULL_OWN_INPUTS,List.of("original_full_own_producer_source","materialized_source_map",
                "historical_completed_build","genuine_historical_capture","original_quota_lease","original_quota_rejection",
                "original_quota_source_map","bounded_full_own_input_manifest","original_junit_jars","individual_original_inputs"),false,false);
    }

    /** Closed bounds from the existing complete production stages; these are limits, not measured runtimes. */
    public record PipelineBudget(long bootstrapSeconds, long nativeBuildSeconds, long mapConsumerSeconds,
            long pythonStaticSeconds, long supplementalSeconds, long preparationSeconds,
            int freshCommands, long freshCommandSeconds, long canonicalSeconds,
            long originalReviewSeconds, long settlementSeconds) {
        public PipelineBudget {
            if (bootstrapSeconds <= 0 || nativeBuildSeconds <= 0 || mapConsumerSeconds <= 0
                    || pythonStaticSeconds <= 0 || supplementalSeconds <= 0 || preparationSeconds <= 0
                    || freshCommands <= 0 || freshCommandSeconds <= 0 || canonicalSeconds <= 0
                    || originalReviewSeconds <= 0 || settlementSeconds <= 0) {
                throw new IllegalArgumentException("Positive complete pipeline stage bounds required");
            }
        }
        public Duration minimumTotal() {
            long seconds = Math.addExact(bootstrapSeconds, nativeBuildSeconds);
            for (long value : new long[] {mapConsumerSeconds, pythonStaticSeconds, supplementalSeconds,
                    preparationSeconds, Math.multiplyExact(freshCommands, freshCommandSeconds),
                    canonicalSeconds, originalReviewSeconds, settlementSeconds}) {
                seconds = Math.addExact(seconds, value);
            }
            return Duration.ofSeconds(seconds);
        }
    }

    private static final PipelineBudget COMPLETE_BUDGET = new PipelineBudget(
            3660, 8100, 670, 1200, 1620, 900, 4, 900, 2100, 900, 30);
    public static Duration managedPipelineMinimum() {
        return COMPLETE_BUDGET.minimumTotal().plusSeconds(4500+600+60+1800+1200+60);
    }
    public static boolean completeProfile(PipelineProfile profile) { return profile!=PipelineProfile.LEGACY; }

    public enum PipelineProfile {
        LEGACY(PLAN_SCHEMA, Duration.ofMinutes(45), Duration.ofHours(2)),
        COMPLETE_CURRENT(COMPLETE_PLAN_SCHEMA, Duration.ofHours(8), Duration.ofHours(8)),
        HOSTED_SOFTWARE(SOFTWARE_PLAN_SCHEMA, Duration.ofMinutes(300), Duration.ofMinutes(300)),
        ROOT_MANAGED_COMPLETE(MANAGED_PLAN_SCHEMA, Duration.ofHours(12), Duration.ofHours(12));

        private final String schema;
        private final Duration maximumTotal;
        private final Duration maximumServiceLease;
        PipelineProfile(String schema, Duration maximumTotal, Duration maximumServiceLease) {
            this.schema = schema; this.maximumTotal = maximumTotal; this.maximumServiceLease = maximumServiceLease;
        }
        public String schema() { return schema; }
        public Duration maximumTotal() { return maximumTotal; }
        public Duration maximumServiceLease() { return maximumServiceLease; }
    }

    public static PipelineBudget completePipelineBudget() { return COMPLETE_BUDGET; }

    public static boolean supportedPlanSchema(String schema) {
        return PLAN_SCHEMA.equals(schema) || COMPLETE_PLAN_SCHEMA.equals(schema)
                || SOFTWARE_PLAN_SCHEMA.equals(schema) || MANAGED_PLAN_SCHEMA.equals(schema)
                || HISTORICAL_MANAGED_PLAN_SCHEMA.equals(schema);
    }

    public static PipelineProfile pipelineProfile(Plan plan) {
        Objects.requireNonNull(plan);
        if (PLAN_SCHEMA.equals(plan.schema())) return PipelineProfile.LEGACY;
        if (COMPLETE_PLAN_SCHEMA.equals(plan.schema())) return PipelineProfile.COMPLETE_CURRENT;
        if (SOFTWARE_PLAN_SCHEMA.equals(plan.schema())) return PipelineProfile.HOSTED_SOFTWARE;
        if (MANAGED_PLAN_SCHEMA.equals(plan.schema())) return PipelineProfile.ROOT_MANAGED_COMPLETE;
        if (HISTORICAL_MANAGED_PLAN_SCHEMA.equals(plan.schema()))
            throw new IllegalArgumentException("Historical eight-hour managed plan is DATA only; current execution requires " + MANAGED_PLAN_SCHEMA);
        throw new IllegalArgumentException("Unknown pipeline profile");
    }

    static void requireCompletePipeline(Plan plan) {
        if (!completeProfile(pipelineProfile(plan))) {
            throw new IllegalArgumentException("Complete fixtures require an explicitly admitted complete software or managed pipeline window");
        }
        pipelineTiming(plan);
    }
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
    private static final Duration PIPELINE_SETTLEMENT = Duration.ofSeconds(30);
    private static final Map<String, Long> PARTS = Map.of(
            "m2", 2 * GIB, "build", 768 * MIB, "tools", 128 * MIB,
            "scratch", 512 * MIB, "metadata_logs", 32 * MIB, "artifacts", 128 * MIB,
            "guard", 480 * MIB);
    private static final Pattern SIMPLE_PATH = Pattern.compile("[^\\s\"%&|<>^!]+", Pattern.UNICODE_CHARACTER_CLASS);

    private static final Pattern MAVEN_CHECKSUM_TEMPORARY = Pattern.compile(
            ".+\\.(?:md5|sha1|sha256|sha512)\\.(0|[1-9][0-9]{0,19})\\.tmp");
    private static final Pattern MAVEN_ARTIFACT_TEMPORARY = Pattern.compile(
            ".+\\.(?:jar|pom)\\.(0|[1-9][0-9]{0,19})\\.tmp(?:\\.(0|[1-9][0-9]{0,19})\\.tmp)?");

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
            if (!supportedPlanSchema(schema)) throw new IllegalArgumentException("unknown bootstrap plan");
            Objects.requireNonNull(machineId);
            Instant observed = Instant.parse(observedAtUtc);
            Instant review = Instant.parse(reviewAtUtc);
            if (HISTORICAL_MANAGED_PLAN_SCHEMA.equals(schema)
                    && (!observed.isBefore(review) || Duration.between(observed, review).compareTo(Duration.ofHours(8)) > 0))
                throw new IllegalArgumentException("Historical managed v3 retains its original finite eight-hour clock");
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

    /** One original deadline; a profile selects finite bounds, never a new clock or resource authority. */
    public record PipelineTiming(Instant observedAt, Instant workDeadline, Instant outerDeadline, PipelineProfile profile) {
        public PipelineTiming(Instant observedAt, Instant workDeadline, Instant outerDeadline) {
            this(observedAt, workDeadline, outerDeadline, PipelineProfile.LEGACY);
        }
        public PipelineTiming {
            Objects.requireNonNull(observedAt); Objects.requireNonNull(workDeadline); Objects.requireNonNull(outerDeadline);
            Objects.requireNonNull(profile);
            Duration total = Duration.between(observedAt, outerDeadline);
            if (!observedAt.isBefore(workDeadline) || !workDeadline.plus(PIPELINE_SETTLEMENT).equals(outerDeadline)
                    || total.compareTo(profile.maximumTotal()) > 0
                    || completeProfile(profile) && total.compareTo(profile==PipelineProfile.ROOT_MANAGED_COMPLETE
                            ? managedPipelineMinimum() : COMPLETE_BUDGET.minimumTotal()) < 0) {
                throw new IllegalArgumentException("Finite original pipeline authority must admit every selected stage and settlement");
            }
        }
        public Duration remainingWork(Instant now) throws IOException { return remaining(now, workDeadline); }
        public Duration remainingOuter(Instant now) throws IOException { return remaining(now, outerDeadline); }
        private Duration remaining(Instant now, Instant deadline) throws IOException {
            if (now.isBefore(observedAt) || !now.isBefore(deadline)) throw new IOException("Shared pipeline deadline unavailable or expired");
            return Duration.between(now, deadline);
        }
    }

    public static PipelineTiming pipelineTiming(Plan plan) {
        return pipelineTiming(Instant.parse(plan.observedAtUtc()), Instant.parse(plan.reviewAtUtc()), pipelineProfile(plan));
    }
    private static PipelineTiming pipelineTiming(Instant observed, Instant review) {
        return pipelineTiming(observed, review, PipelineProfile.LEGACY);
    }
    private static PipelineTiming pipelineTiming(Instant observed, Instant review, PipelineProfile profile) {
        Instant total = observed.plus(profile.maximumTotal());
        if (completeProfile(profile) && review.isAfter(total)) {
            throw new IllegalArgumentException("Complete pipeline review exceeds its finite profile");
        }
        Instant outer = review.isBefore(total) ? review : total;
        return new PipelineTiming(observed, outer.minus(PIPELINE_SETTLEMENT), outer, profile);
    }

    /** Narrow the existing execution lease and any quota override; original plan/pins remain immutable. */
    public static Plan pipelineExecutionPlan(Plan plan) {
        String review = pipelineTiming(plan).workDeadline().toString();
        Map<String, QuotaOverride> overrides = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for (var entry : plan.quotaOverrides().entrySet()) {
            QuotaOverride original = entry.getValue();
            String bounded = Instant.parse(original.reviewAtUtc()).isBefore(Instant.parse(review)) ? original.reviewAtUtc() : review;
            overrides.put(entry.getKey(), new QuotaOverride(original.owner(), original.task(), original.reason(),
                    original.maxProjectBytes(), bounded, original.sourceRef()));
        }
        return new Plan(plan.schema(), plan.machineId(), plan.observedAtUtc(), review, plan.repoRoot(), plan.workRoot(),
                plan.javaHome(), plan.mavenCommand(), plan.pythonExecutable(), plan.ownerTask(), plan.policyRef(),
                plan.volumes(), overrides, plan.parts(), plan.sourcePins(), plan.bootstrapRuntimeClosure(),
                plan.bootstrapNativeJobHardBound(), plan.bootstrapAloneGrantsPipelineQualification());
    }

    static Duration hostedReviewDuration(byte[] raw, long requestedQuota, PipelineProfile pipelineProfile) throws IOException {
        Objects.requireNonNull(pipelineProfile);
        J profile = parse(raw);
        String schema = string(field(profile, "schema"));
        long minutes = integer(field(profile, "review_minutes"));
        boolean legacy = schema.equals("xar.java-control-CI-profile/v1") && minutes == 90;
        boolean complete = schema.equals("xar.java-control-CI-profile/v2") && minutes == 245;
        boolean software = (schema.equals("xar.java-control-CI-profile/v3") || schema.equals("xar.java-control-CI-profile/v4")) && minutes == 300
                && string(field(profile,"qualification_scope")).equals("SOFTWARE_ONLY_NOT_POSTQUALIFIED");
        if(schema.equals("xar.java-control-CI-profile/v4")&&!TOOLS_POSTQUALIFICATION_POLICY.equals(string(field(profile,"tools_postqualification_policy"))))
            throw new IOException("Explicit mandatory original full Own and large-input two-JUnit policy required");
        if ((!legacy && !complete && !software) || integer(field(profile, "max_project_bytes")) != requestedQuota
                || requestedQuota != 8 * GIB || !string(field(profile, "task")).equals("github-actions-java-ci")
                || pipelineProfile == PipelineProfile.COMPLETE_CURRENT && !complete
                || pipelineProfile == PipelineProfile.HOSTED_SOFTWARE && !software
                || pipelineProfile == PipelineProfile.ROOT_MANAGED_COMPLETE) {
            throw new IOException("Explicit approved versioned hosted CI quota and complete-stage review required");
        }
        return Duration.ofMinutes(pipelineProfile == PipelineProfile.LEGACY ? 90 : minutes);
    }
    static void requireToolsPostqualificationPolicy(byte[] raw,String requested)throws IOException {
        J profile=parse(raw);
        if(!"xar.java-control-CI-profile/v4".equals(string(field(profile,"schema")))
                ||!TOOLS_POSTQUALIFICATION_POLICY.equals(requested)
                ||!TOOLS_POSTQUALIFICATION_POLICY.equals(string(field(profile,"tools_postqualification_policy"))))
            throw new IOException("Current hosted Tools adoption requires explicit v4 mandatory real full Own plus two-JUnit policy");
    }

    public record BootstrapActual(String schema, String machineId, String startedAtUtc,
                                  String observedAtUtc, BootstrapTerminalStatus status, String error,
                                   FilePin planRef, DefaultMaven defaultMaven,
                                   List<FilePin> mavenProbeRefs,
                                   boolean bootstrapNativeJobHardBound,
                                  boolean bootstrapAloneGrantsPipelineQualification) {
        public BootstrapActual {
            Objects.requireNonNull(status, "status");
            mavenProbeRefs = List.copyOf(mavenProbeRefs);
        }
    }

    public enum BootstrapMode { PIPELINE, MAVEN_ONLY }
    public enum BootstrapTerminalStatus { RED, PIPELINE_EXIT_0, MAVEN_READY_NO_PIPELINE_QUALIFICATION }
    public record Invocation(BootstrapMode mode, Map<String, String> values) {
        public Invocation {
            Objects.requireNonNull(mode, "mode");
            values = Map.copyOf(values);
        }
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
    @FunctionalInterface interface IoValue<T> { T read() throws IOException; }
    @FunctionalInterface interface AttributeReader { BasicFileAttributes read(Path path) throws IOException; }
    @FunctionalInterface interface TreeWalker { void walk(Path root, FileVisitor<Path> visitor) throws IOException; }
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
        if (arguments.length > 0 && arguments[0].equals("--utf8-java-invocation")) {
            JavaUtf8Invocation.run(JavaUtf8Invocation.entryPublication(arguments));
            return;
        }
        if (!System.getProperty("os.name").startsWith("Windows") || Runtime.version().feature() != 21) {
            throw new IllegalStateException("explicit installed Windows JDK21 required; no skip");
        }
        if (arguments.length == 1 && arguments[0].equals("--verify-canonical-oracle-environment")) {
            OracleEnvironment.require(System.getenv());
            System.out.println("Verified explicit canonical oracle environment; no pipeline qualification");
            return;
        }
        if (arguments.length == 2 && arguments[0].equals("--verify-maven-evidence-root")) {
            String machine = machineId(Path.of(Objects.requireNonNull(System.getenv("SystemRoot"))).toRealPath());
            int count = verifyMavenEvidence(Path.of(arguments[1]), machine);
            System.out.println("Verified " + count + " persisted Maven probe records; evidence integrity grants no pipeline qualification");
            return;
        }
        Invocation bootstrapInvocation = invocation(arguments);
        Map<String, String> values = bootstrapInvocation.values();
        FilePin fixtureProduction = fixtureProductionPin(values);
        FilePin plannedFixtureProduction = plannedFixtureProductionPin(values);
        String qualification=values.get("--qualification-scope");
        if(qualification!=null && !qualification.equals("SOFTWARE_ONLY_NOT_POSTQUALIFIED"))
            throw new IllegalArgumentException("Hosted runner cannot request managed complete qualification");
        PipelineProfile pipelineProfile = qualification!=null ? PipelineProfile.HOSTED_SOFTWARE
                : fixtureProduction != null || plannedFixtureProduction != null ? PipelineProfile.COMPLETE_CURRENT : PipelineProfile.LEGACY;
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
        byte[] profileBytes = Files.readAllBytes(profilePath);
        if(qualification!=null)requireToolsPostqualificationPolicy(profileBytes,values.get("--tools-postqualification-policy"));
        J profile = parse(profileBytes);
        Duration reviewDuration = hostedReviewDuration(profileBytes, requestedQuota, pipelineProfile);
        String machine = machineId(systemRoot);
        Instant observed = Instant.now();
        Instant expiry = observed.plus(reviewDuration);
        if(pipelineProfile==PipelineProfile.HOSTED_SOFTWARE) {
            System.out.println(emit(toJson(missingToolsPostqualification())));
            System.out.println("SOFTWARE_ONLY_NOT_POSTQUALIFIED: PERSON10_ACTUAL NOT_EXECUTED; ROOT_INVOCATION_ACTUAL NOT_EXECUTED; FULL_CI_NOT_QUALIFIED");
            if(fixtureProduction==null&&plannedFixtureProduction==null)
                System.out.println("HOSTED_SOFTWARE_UNAVAILABLE: actual same-run current fixture production inputs were not supplied; nine-stage software qualification NOT_EXECUTED");
            if(reviewDuration.compareTo(COMPLETE_BUDGET.minimumTotal())<0)
                System.out.println("HOSTED_SOFTWARE_UNAVAILABLE: configured "+reviewDuration.toSeconds()+"s cannot admit complete software bounds "+COMPLETE_BUDGET.minimumTotal().toSeconds()+"s; no stage or timeout was shortened");
        }
        PipelineTiming timing = pipelineTiming(observed, expiry, pipelineProfile);
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
            environment.putAll(OracleEnvironment.bindSelectedInterpreter(python, environment));
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
                            root.resolve("scratch"), environment, log, Duration.ofSeconds(30), timing.workDeadline(), root, volumes);
                    return Files.readString(log);
                }, () -> defaultMavenLauncher(environment, root.resolve("scratch"), true), log,
                        root.resolve("logs/maven-observation-" + ordinal + ".json"), machine, bootstrapSourceRef,
                        ordinal == 1 ? MavenProbePhase.BEFORE_ENSURE : MavenProbePhase.AFTER_IN_PLACE_UPGRADE,
                        true, mavenProbeRefs);
            }, observedInstallation -> installOfficialMaven(observedInstallation, root, machine, volumes, () -> guard(root, volumes, timing.workDeadline())));
            if (bootstrapInvocation.mode() == BootstrapMode.MAVEN_ONLY) {
                if (!before.equals(sourcePins(source))) throw new IOException("bootstrap source changed during default Maven admission");
                completed = true;
                return;
            }
            Path maven = Path.of(defaultMaven.distributionLauncherRef().path());
            Path batch = root.resolve("scratch/bootstrap-verify.cmd");
            Files.writeString(batch, "@echo off\r\ncall mvn -B -ntp -e -s \"" + settings
                    + "\" -gs \"" + settings + "\" -f \"" + source.resolve("pom.xml")
                    + "\" \"-Dmaven.repo.local=" + root.resolve("m2") + "\" \"-Dck3.build.root="
                    + root.resolve("build/bootstrap-tools") + "\" verify\r\nexit /b %errorlevel%\r\n",
                    StandardOpenOption.CREATE_NEW);
            runPlain(List.of(systemRoot.resolve("System32/cmd.exe").toString(), "/d", "/c", batch.toString()),
                    root.resolve("scratch"), environment, root.resolve("logs/bootstrap-verify.log"), Duration.ofSeconds(3600), timing.workDeadline(), root, volumes);
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
            Plan plan = new Plan(pipelineProfile.schema(), machine, observed.toString(), expiry.toString(),
                    repo.toString(), root.toString(), javaHome.toString(), maven.toString(), python.toString(),
                    "github-actions-java-ci", measure(policyPath), volumes, overrides, PARTS, before, List.copyOf(runtime), false, false);
            planRef = publish(planPath, plan);
            var invocation=qualifiedInvocation(runtime,planPath,fixtureProduction,plannedFixtureProduction,root.resolve("logs"),Path.of(scratch),pending->{
                guard(root,volumes,timing.workDeadline());
                long existing;try(var entries=Files.walk(root.resolve("logs"))){existing=entries.filter(path->Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS)).mapToLong(path->{try{return Files.size(path);}catch(IOException error){throw new UncheckedIOException(error);}}).reduce(0L,Math::addExact);}
                catch(UncheckedIOException error){throw error.getCause();}
                if(Math.addExact(existing,pending)>PARTS.get("metadata_logs"))throw new IOException("UTF8 invocation exceeds the original finite metadata budget");
                for(var volume:volumes.entrySet())if(Files.getFileStore(Path.of(volume.getKey())).getUsableSpace()<Math.addExact(volume.getValue().requiredFree(),pending))throw new IOException("Fresh free-space margin cannot admit the invocation outputs");
            });
            List<String> command=new ArrayList<>();command.add(javaHome.resolve("bin/java.exe").toString());command.addAll(invocation.physicalArguments());
            environment.remove("JAVA_TOOL_OPTIONS");
            runPlain(command, repo, environment, root.resolve("logs/qualified-pipeline.log"),
                    timing.remainingOuter(Instant.now()), timing.outerDeadline(), root, volumes);
            requireFree(volumes);
            completed = true;
        } catch (Exception error) {
            failure = error.getClass().getName() + ": " + error.getMessage();
        } finally {
            if (!completed && failure == null) failure = "bootstrap did not reach its requested terminal validation";
            publish(root.resolve("logs/bootstrap-actual.json"), new BootstrapActual(
                    "xar.java-control-CI-bootstrap-actual/v3", machine, started, Instant.now().toString(),
                    completionStatus(bootstrapInvocation.mode(), completed, failure), failure, planRef, defaultMaven,
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
            BootstrapTerminalStatus status = BootstrapTerminalStatus.valueOf(string(field(terminal, "status")));
            String error = nullableText(field(terminal, "error"));
            if ((status == BootstrapTerminalStatus.RED) != (error != null)) throw new IOException("terminal bootstrap status/error differs");
            if (status == BootstrapTerminalStatus.MAVEN_READY_NO_PIPELINE_QUALIFICATION && field(terminal, "plan_ref") != JNull.VALUE) {
                throw new IOException("Maven-only admission cannot include a pipeline plan");
            }
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
            } else if (status != BootstrapTerminalStatus.RED) {
                throw new IOException("successful bootstrap has no admitted default Maven");
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
        guard(root, volumes, expiry, childDeadline, reader, (part, visitor) -> Files.walkFileTree(part, visitor));
    }

    static void guard(Path root, Map<String, VolumeBudget> volumes, Instant expiry,
                      IoGuard childDeadline, AttributeReader reader, TreeWalker walker) throws IOException {
        IoGuard active = () -> {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("bootstrap guard interrupted");
            if (!Instant.now().isBefore(expiry)) throw new IOException("finite hosted capacity authority expired");
            childDeadline.check();
        };
        active.check();
        requireFree(volumes);
        for (String name : List.of("m2", "build", "tools", "scratch", "logs", "artifacts")) {
            Path part = root.resolve(name);
            boolean scratch = name.equals("scratch");
            long limit = PARTS.get(name.equals("logs") ? "metadata_logs" : name);
            // JUnit removes scratch entries and Maven retires update/checksum/download temporaries.
            // Handle only their actual disappearance, preserving every surviving sibling.
            class BudgetVisitor extends SimpleFileVisitor<Path> {
                private long size;
                private boolean traversalDenied;
                @Override public FileVisitResult preVisitDirectory(Path directory, BasicFileAttributes attributes) throws IOException {
                    return inspect(directory) ? FileVisitResult.CONTINUE : FileVisitResult.SKIP_SUBTREE;
                }
                @Override public FileVisitResult visitFile(Path file, BasicFileAttributes attributes) throws IOException {
                    inspect(file); return FileVisitResult.CONTINUE;
                }
                @Override public FileVisitResult visitFileFailed(Path file, IOException error) throws IOException {
                    return failed(file, error);
                }
                @Override public FileVisitResult postVisitDirectory(Path directory, IOException error) throws IOException {
                    active.check();
                    return error == null ? FileVisitResult.CONTINUE : failed(directory, error);
                }
                private FileVisitResult failed(Path path, IOException error) throws IOException {
                    active.check();
                    boolean mavenTemporary = name.equals("m2") && mavenTransientRepositoryFile(path);
                    if (!path.equals(part) && path.startsWith(part) && (scratch || mavenTemporary)
                            && error instanceof NoSuchFileException) return FileVisitResult.CONTINUE;
                    if (scratch && error instanceof AccessDeniedException) traversalDenied = true;
                    throw error;
                }
                private boolean inspect(Path path) throws IOException {
                    active.check();
                    try {
                        BasicFileAttributes attributes = guardedAttributes(path, scratch, reader, active);
                        if (attributes.isSymbolicLink()) throw new IOException("linked task output refused");
                        if (path.equals(part) && !attributes.isDirectory()) throw new IOException("plain task part directory required");
                        if (attributes.isRegularFile()) size = Math.addExact(size, attributes.size());
                        if (size > limit) throw new IOException("task part budget exceeded: " + name);
                        return true;
                    } catch (NoSuchFileException removedTemporary) {
                        failed(path, removedTemporary); return false;
                    }
                }
            }
            for (int attempt = 0; ; attempt++) {
                BudgetVisitor visitor = new BudgetVisitor();
                try {
                    walker.walk(part, visitor);
                    break;
                } catch (AccessDeniedException denied) {
                    // A Windows delete-pending directory can fail enumeration before
                    // inspect() runs. Retry that traversal with fresh byte accounting.
                    if (!scratch || !visitor.traversalDenied || attempt == 3) throw denied;
                    pauseScratchMetadataRetry(active);
                }
            }
        }
    }

    private static boolean mavenTransientRepositoryFile(Path path) {
        String name = path.getFileName().toString();
        if (name.endsWith(".lastUpdated")) return true;
        // Resolver PathProcessorSupport appends an unsigned random long and .tmp.
        // Download/staging can nest that suffix once; final artifact bodies remain fatal.
        // Present temporary files still pass through normal accounting.
        var checksum = MAVEN_CHECKSUM_TEMPORARY.matcher(name);
        if (checksum.matches()) return unsignedTemporaryNumber(checksum.group(1));
        var artifact = MAVEN_ARTIFACT_TEMPORARY.matcher(name);
        return artifact.matches() && unsignedTemporaryNumber(artifact.group(1))
                && (artifact.group(2) == null || unsignedTemporaryNumber(artifact.group(2)));
    }

    private static boolean unsignedTemporaryNumber(String number) {
        try { Long.parseUnsignedLong(number); return true; }
        catch (NumberFormatException outOfRange) { return false; }
    }

    private static BasicFileAttributes guardedAttributes(Path path, boolean scratch,
                                                        AttributeReader reader, IoGuard active) throws IOException {
        return rereadScratchMetadata(scratch, active, () -> reader.read(path));
    }

    static <T> T rereadScratchMetadata(boolean scratch, IoGuard active, IoValue<T> operation) throws IOException {
        // Windows can briefly deny metadata while a JUnit scratch file is being deleted.
        // A successful no-follow read or an actual NoSuchFileException resolves that race;
        // persistent denial, links, and every other I/O failure remain fatal.
        for (int attempt = 0; ; attempt++) {
            active.check();
            try { return operation.read(); }
            catch (AccessDeniedException denied) {
                if (!scratch || attempt == 3) throw denied;
                pauseScratchMetadataRetry(active);
            }
        }
    }

    private static void pauseScratchMetadataRetry(IoGuard active) throws IOException {
        active.check();
        try { Thread.sleep(25); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new InterruptedIOException("scratch metadata retry interrupted");
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

    static BootstrapTerminalStatus completionStatus(BootstrapMode mode, boolean completed, String failure) {
        Objects.requireNonNull(mode, "mode");
        if (!completed || failure != null) return BootstrapTerminalStatus.RED;
        return mode == BootstrapMode.MAVEN_ONLY ? BootstrapTerminalStatus.MAVEN_READY_NO_PIPELINE_QUALIFICATION
                : BootstrapTerminalStatus.PIPELINE_EXIT_0;
    }

    static Invocation invocation(String[] arguments) {
        boolean mavenOnly = arguments.length > 0 && arguments[0].equals("--ensure-default-maven-only");
        String[] parameters = mavenOnly ? java.util.Arrays.copyOfRange(arguments, 1, arguments.length) : arguments;
        Map<String, String> values = arguments(parameters);
        if (mavenOnly && (values.containsKey("--fixture-production-request") || values.containsKey("--planned-fixture-production-request"))) {
            throw new IllegalArgumentException("Maven-only admission cannot request fixture production");
        }
        return new Invocation(mavenOnly ? BootstrapMode.MAVEN_ONLY : BootstrapMode.PIPELINE, values);
    }

    static Map<String, String> arguments(String[] arguments) {
        List<String> required = List.of("--repo-root", "--work-root", "--python-executable", "--system-growth-reserve-bytes", "--max-project-bytes");
        List<String> fixture = List.of("--fixture-production-request", "--fixture-production-request-bytes", "--fixture-production-request-sha256");
        List<String> planned = List.of("--planned-fixture-production-request", "--planned-fixture-production-request-bytes", "--planned-fixture-production-request-sha256");
        if (arguments.length%2!=0 || (arguments.length != required.size()*2 && arguments.length != (required.size()+fixture.size())*2
                && arguments.length != (required.size()+1)*2 && arguments.length != (required.size()+fixture.size()+1)*2
                && arguments.length != (required.size()+2)*2 && arguments.length != (required.size()+fixture.size()+2)*2)) {
            throw new IllegalArgumentException("All five bootstrap parameters and, when requested, all three exact fixture production fields required");
        }
        Map<String, String> result = new LinkedHashMap<>();
        for (int index = 0; index < arguments.length; index += 2) {
            if ((!required.contains(arguments[index]) && !fixture.contains(arguments[index]) && !planned.contains(arguments[index])
                    && !arguments[index].equals("--qualification-scope") && !arguments[index].equals("--tools-postqualification-policy")) || result.putIfAbsent(arguments[index], arguments[index + 1]) != null) {
                throw new IllegalArgumentException("unknown or duplicate bootstrap parameter");
            }
        }
        boolean hasFixture = !java.util.Collections.disjoint(result.keySet(), fixture);
        boolean hasPlanned = !java.util.Collections.disjoint(result.keySet(), planned);
        if (!result.keySet().containsAll(required) || hasFixture && !result.keySet().containsAll(fixture)
                || hasPlanned && !result.keySet().containsAll(planned) || hasFixture && hasPlanned) {
            throw new IllegalArgumentException("Complete bootstrap and fixture production parameters required");
        }
        if(result.containsKey("--qualification-scope")&&!result.get("--qualification-scope").equals("SOFTWARE_ONLY_NOT_POSTQUALIFIED"))
            throw new IllegalArgumentException("Hosted arguments cannot select managed full qualification");
        if(result.containsKey("--tools-postqualification-policy")
                &&(!result.containsKey("--qualification-scope")||!TOOLS_POSTQUALIFICATION_POLICY.equals(result.get("--tools-postqualification-policy"))))
            throw new IllegalArgumentException("Exact hosted scope and mandatory full-Own/two-JUnit policy required");
        return Map.copyOf(result);
    }

    static FilePin fixtureProductionPin(Map<String, String> values) throws IOException {
        return fixtureProductionPin(values, "--fixture-production-request");
    }

    static FilePin plannedFixtureProductionPin(Map<String, String> values) throws IOException {
        return fixtureProductionPin(values, "--planned-fixture-production-request");
    }

    private static FilePin fixtureProductionPin(Map<String, String> values, String flag) throws IOException {
        String path = values.get(flag);
        if (path == null) return null;
        String bytes = values.get(flag + "-bytes");
        if (bytes == null || !bytes.matches("[1-9][0-9]{0,7}")) throw new IllegalArgumentException("Positive bounded fixture production bytes required");
        FilePin pin = new FilePin(Path.of(path).toRealPath().toString(), Long.parseLong(bytes), values.get(flag + "-sha256"));
        if (pin.bytes() > 4 * MIB || !pin.equals(measure(Path.of(pin.path())))) throw new IOException("Fixture production input changed or exceeds its bound");
        return pin;
    }

    static void appendFixtureProduction(List<String> command, FilePin pin) throws IOException {
        appendFixtureProduction(command, pin, "--fixture-production-request");
    }

    static void appendPlannedFixtureProduction(List<String> command, FilePin pin) throws IOException {
        appendFixtureProduction(command, pin, "--planned-fixture-production-request");
    }

    private static void appendFixtureProduction(List<String> command, FilePin pin, String flag) throws IOException {
        if (pin == null) return;
        if (!pin.equals(measure(Path.of(pin.path())))) throw new IOException("Fixture production input changed before forwarding");
        command.addAll(List.of(flag, pin.path(), Long.toString(pin.bytes()), pin.sha256()));
    }

    /** Actual bootstrap producer, shared with its regression; the original runtime closure remains authoritative. */
    static JavaUtf8Invocation.Launch qualifiedInvocation(List<FilePin> runtime,Path planPath,FilePin fixtureProduction,
            Path evidenceRoot,Path scratch,JavaUtf8Invocation.OutputGuard guard)throws IOException {
        return qualifiedInvocation(runtime,planPath,fixtureProduction,null,evidenceRoot,scratch,guard);
    }
    static JavaUtf8Invocation.Launch qualifiedInvocation(List<FilePin> runtime,Path planPath,FilePin fixtureProduction,FilePin plannedFixtureProduction,
            Path evidenceRoot,Path scratch,JavaUtf8Invocation.OutputGuard guard)throws IOException {
        if(fixtureProduction!=null&&plannedFixtureProduction!=null)throw new IllegalArgumentException("One production or planned fixture route required");
        var pinnedClasspath=new ArrayList<JavaUtf8Invocation.ClasspathPin>();
        for(FilePin pin:runtime){if(!pin.equals(measure(Path.of(pin.path()))))throw new IOException("Original bootstrap runtime pin drifted");pinnedClasspath.add(JavaUtf8Invocation.captureClasspath(Path.of(pin.path())));}
        if(pinnedClasspath.isEmpty())throw new IOException("Actual complete bootstrap runtime closure required");
        var arguments=new ArrayList<>(List.of("--bootstrap-plan",planPath.toString()));appendFixtureProduction(arguments,fixtureProduction);appendPlannedFixtureProduction(arguments,plannedFixtureProduction);
        var evidence=JavaUtf8Invocation.captureOutputRoot(evidenceRoot);
        var request=new JavaUtf8Invocation.Request(new JavaUtf8Invocation.ClassTarget("org.xar.ck3.control.build.ControlCi",pinnedClasspath.getFirst(),pinnedClasspath),List.of(),arguments,evidence);
        var publication=JavaUtf8Invocation.publish(request,evidence,"qualified-pipeline-utf8.bin",guard);
        return JavaUtf8Invocation.launch(publication,new JavaUtf8Invocation.ClassCarrier(pinnedClasspath),List.of(
                "-Xms32m","-Xmx128m","-XX:MaxMetaspaceSize=96m","-XX:ReservedCodeCacheSize=48m","-XX:MaxDirectMemorySize=32m",
                "-Djava.io.tmpdir="+scratch,"-Djna.tmpdir="+scratch));
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

    /** One JDK-only codec and same-JVM entry. Pins are data; the original caller still owns admission and output guards. */
    public static final class JavaUtf8Invocation {
        private JavaUtf8Invocation() { }
        public static final int MAXIMUM_ENVELOPE_BYTES = 4 << 20;
        private static final int MAGIC = 0x584a5531, PREPARED_MAGIC = 0x584a5031;
        private static final int MAXIMUM_FILES = 8192, MAXIMUM_CLASSPATH = 1024;
        private static final String ENTRY = "--utf8-java-invocation";
        /** These JDK observations never assert a Win32 FileID or continuously held native custody. */
        public enum WitnessScope { JDK_METADATA_AND_CONTENT }
        public record JdkFileMetadata(String createdAt,String modifiedAt,java.util.Optional<String> providerFileKey) {
            public JdkFileMetadata { timestamp(createdAt);timestamp(modifiedAt);providerFileKey=optionalKey(providerFileKey); }
        }
        public record JdkDirectoryMetadata(String createdAt,java.util.Optional<String> providerFileKey) {
            public JdkDirectoryMetadata { timestamp(createdAt);providerFileKey=optionalKey(providerFileKey); }
        }
        public record PinnedFile(String path,long bytes,String sha256,JdkFileMetadata metadata) {
            public PinnedFile { absolute(path);Objects.requireNonNull(metadata);if(bytes<0||bytes>(2L<<30)||sha256==null||!sha256.matches("[0-9a-f]{64}"))throw new IllegalArgumentException("Exact bounded JDK content/metadata pin required"); }
            public WitnessScope witnessScope(){return WitnessScope.JDK_METADATA_AND_CONTENT;}
        }
        public record DirectoryIdentity(String path,JdkDirectoryMetadata metadata) {
            public DirectoryIdentity { absolute(path);Objects.requireNonNull(metadata); }
            public WitnessScope witnessScope(){return WitnessScope.JDK_METADATA_AND_CONTENT;}
        }
        private static java.util.Optional<String> optionalKey(java.util.Optional<String> value){Objects.requireNonNull(value);value.ifPresent(JavaUtf8Invocation::text);return value;}
        private static void timestamp(String value){text(value);try{java.time.Instant.parse(value);}catch(java.time.format.DateTimeParseException error){throw new IllegalArgumentException("JDK timestamp required",error);}}
        private static JdkFileMetadata fileMetadata(java.nio.file.attribute.BasicFileAttributes value){return new JdkFileMetadata(value.creationTime().toString(),value.lastModifiedTime().toString(),java.util.Optional.ofNullable(value.fileKey()).map(Object::toString));}
        private static JdkDirectoryMetadata directoryMetadata(java.nio.file.attribute.BasicFileAttributes value){return new JdkDirectoryMetadata(value.creationTime().toString(),java.util.Optional.ofNullable(value.fileKey()).map(Object::toString));}
        public sealed interface ClasspathPin permits FileClasspath,DirectoryClasspath,JarClasspath { String path(); }
        public record FileClasspath(PinnedFile file) implements ClasspathPin {
            public FileClasspath { Objects.requireNonNull(file); }
            public String path(){return file.path();}
        }
        public record DirectoryClasspath(DirectoryIdentity directory,List<PinnedFile> files) implements ClasspathPin {
            public DirectoryClasspath { Objects.requireNonNull(directory);files=List.copyOf(files);if(files.size()>MAXIMUM_FILES)throw new IllegalArgumentException("Finite complete class directory required"); }
            public String path(){return directory.path();}
        }
        /** A single original classpath root, retaining its complete manifest-ordered closure. */
        public record JarClasspath(PinnedFile jar,List<ClasspathPin> manifestClasspath) implements ClasspathPin {
            public JarClasspath { Objects.requireNonNull(jar);manifestClasspath=classpath(manifestClasspath);if(!manifestClasspath.getFirst().equals(new FileClasspath(jar))||manifestClasspath.stream().anyMatch(JarClasspath.class::isInstance))throw new IllegalArgumentException("Flat original JAR manifest closure required"); }
            public String path(){return jar.path();}
        }
        public sealed interface Target permits ClassTarget,JarTarget,SourceTarget { }
        public record ClassTarget(String mainClass,ClasspathPin mainOrigin,List<ClasspathPin> classpath) implements Target {
            public ClassTarget { className(mainClass);Objects.requireNonNull(mainOrigin);classpath=JavaUtf8Invocation.classpath(classpath);if(!classpath.contains(mainOrigin))throw new IllegalArgumentException("Exact main origin must occur in runtime classpath"); }
        }
        public record JarTarget(PinnedFile jar,String mainClass,List<ClasspathPin> manifestClasspath) implements Target {
            public JarTarget { Objects.requireNonNull(jar);className(mainClass);manifestClasspath=classpath(manifestClasspath);if(!manifestClasspath.getFirst().equals(new FileClasspath(jar)))throw new IllegalArgumentException("Executable JAR must be first effective classpath entry"); }
        }
        public record SourceTarget(PinnedFile source,String mainClass,List<ClasspathPin> classpath,
                DirectoryIdentity compiledRoot,long maximumCompiledBytes) implements Target {
            public SourceTarget { Objects.requireNonNull(source);className(mainClass);classpath=List.copyOf(classpath);Objects.requireNonNull(compiledRoot);if(classpath.size()>MAXIMUM_CLASSPATH||source.bytes()>(4<<20)||maximumCompiledBytes<1||maximumCompiledBytes>(64L<<20))throw new IllegalArgumentException("Bounded single-source Java21 compilation required"); }
        }
        public record Property(String name,String value) {
            public Property { text(name);text(value);if(!name.matches("(?:xar|quarkus)\\.[A-Za-z0-9_.-]+"))throw new IllegalArgumentException("Only application properties may be applied after VM startup"); }
        }
        public record Request(Target target,List<Property> properties,List<String> arguments,DirectoryIdentity evidenceRoot) {
            public Request { Objects.requireNonNull(target);properties=List.copyOf(properties);arguments=List.copyOf(arguments);Objects.requireNonNull(evidenceRoot);if(properties.size()>256||arguments.size()>4096)throw new IllegalArgumentException("Finite typed Java invocation required");var names=new java.util.HashSet<String>();for(Property property:properties)if(!names.add(property.name()))throw new IllegalArgumentException("Duplicate application property");arguments.forEach(JavaUtf8Invocation::text); }
        }
        public record Publication(PinnedFile envelope) { public Publication { Objects.requireNonNull(envelope);if(envelope.bytes()<1||envelope.bytes()>MAXIMUM_ENVELOPE_BYTES)throw new IllegalArgumentException("Finite invocation envelope required"); } }
        public sealed interface Carrier permits ClassCarrier,SourceCarrier { }
        public record ClassCarrier(List<ClasspathPin> classpath) implements Carrier { public ClassCarrier { classpath=JavaUtf8Invocation.classpath(classpath); } }
        public record SourceCarrier(PinnedFile source) implements Carrier { public SourceCarrier { Objects.requireNonNull(source); } }
        public record Launch(List<String> physicalArguments,Publication publication,Request logicalRequest) {
            public Launch { physicalArguments=List.copyOf(physicalArguments);Objects.requireNonNull(publication);Objects.requireNonNull(logicalRequest); }
        }
        public record Preparation(PinnedFile envelope,String mode,String mainClass,String actualCodeSource,
                List<ClasspathPin> effectiveClasspath,List<PinnedFile> compiledClasses) {
            public Preparation { Objects.requireNonNull(envelope);if(!Set.of("CLASS","JAR","SOURCE").contains(mode))throw new IllegalArgumentException("Exact preparation mode required");className(mainClass);absolute(actualCodeSource);effectiveClasspath=List.copyOf(effectiveClasspath);compiledClasses=List.copyOf(compiledClasses);if(effectiveClasspath.isEmpty()||effectiveClasspath.size()>MAXIMUM_CLASSPATH||compiledClasses.size()>1024||(!mode.equals("SOURCE")&&!compiledClasses.isEmpty()))throw new IllegalArgumentException("Finite mode-bound preparation closure required"); }
        }
        @FunctionalInterface public interface OutputGuard { void require(long pendingBytes) throws IOException; }
        private static void text(String value){if(value==null||value.indexOf('\0')>=0)throw new IllegalArgumentException("UTF8 text without NUL required");}
        private static void absolute(String value){text(value);if(!Path.of(value).isAbsolute())throw new IllegalArgumentException("Absolute original path required");}
        private static void className(String value){text(value);if(!javax.lang.model.SourceVersion.isName(value))throw new IllegalArgumentException("Exact Java binary main name required");}
        private static List<ClasspathPin> classpath(List<ClasspathPin> input){var result=List.copyOf(input);if(result.isEmpty()||result.size()>MAXIMUM_CLASSPATH)throw new IllegalArgumentException("Finite original ordered runtime classpath required");return result;}
        private static java.nio.file.attribute.BasicFileAttributes attributes(Path path)throws IOException {
            var value=Files.readAttributes(path,java.nio.file.attribute.BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
            if(value.isSymbolicLink()||value.isOther())throw new IOException("Plain JDK metadata required; links/other entries are unavailable");return value;
        }
        public static PinnedFile captureFile(Path input)throws IOException {
            Path path=input.toRealPath(LinkOption.NOFOLLOW_LINKS);if(!path.equals(path.toRealPath()))throw new IOException("Linked source ancestry is unavailable");var before=attributes(path);
            if(!before.isRegularFile()||before.size()>(2L<<30))throw new IOException("Bounded regular original file required");
            var digest=digest();try(var stream=Files.newInputStream(path)){byte[] buffer=new byte[65536];for(int count;(count=stream.read(buffer))!=-1;)digest.update(buffer,0,count);}
            var after=attributes(path);if(!fileMetadata(before).equals(fileMetadata(after))||before.size()!=after.size())throw new IOException("Original file changed during pin capture");
            return new PinnedFile(path.toString(),before.size(),java.util.HexFormat.of().formatHex(digest.digest()),fileMetadata(before));
        }
        private static DirectoryIdentity directory(Path input)throws IOException {
            Path path=input.toRealPath(LinkOption.NOFOLLOW_LINKS);if(!path.equals(path.toRealPath()))throw new IOException("Linked output ancestry is unavailable");var value=attributes(path);if(!value.isDirectory())throw new IOException("Existing plain directory required");return new DirectoryIdentity(path.toString(),directoryMetadata(value));
        }
        public static DirectoryIdentity captureOutputRoot(Path existingRoot)throws IOException {var result=directory(existingRoot);ascii(result.path());return result;}
        public static ClasspathPin captureClasspath(Path input)throws IOException {
            Path path=input.toRealPath(LinkOption.NOFOLLOW_LINKS);var value=attributes(path);if(value.isRegularFile()){
                if(isArchive(path)){var closure=new LinkedHashMap<String,ClasspathPin>();jarClosure(path,closure,0);return new JarClasspath(captureFile(path),List.copyOf(closure.values()));}
                return new FileClasspath(captureFile(path));
            }
            DirectoryIdentity identity=directory(path);var files=new ArrayList<PinnedFile>();
            try(var walk=Files.walk(path)){var iterator=walk.iterator();while(iterator.hasNext()){Path next=iterator.next();var item=attributes(next);if(item.isRegularFile()){if(files.size()>=MAXIMUM_FILES)throw new IOException("Complete classpath inventory exceeded its finite limit");files.add(captureFile(next));}else if(!item.isDirectory())throw new IOException("Unsupported runtime classpath member");}}
            files.sort(java.util.Comparator.comparing(PinnedFile::path));if(!identity.equals(directory(path)))throw new IOException("Original class directory changed identity");return new DirectoryClasspath(identity,files);
        }
        private static void verify(PinnedFile pin)throws IOException {if(!pin.equals(captureFile(Path.of(pin.path()))))throw new IOException("Exact source bytes/JDK metadata drifted: "+pin.path());}
        private static void verify(DirectoryIdentity pin)throws IOException {if(!pin.equals(directory(Path.of(pin.path()))))throw new IOException("Original output directory JDK metadata drifted");}
        private static void verify(ClasspathPin pin)throws IOException {if(pin instanceof FileClasspath file){verify(file.file());return;}if(!pin.equals(captureClasspath(Path.of(pin.path()))))throw new IOException("Complete original runtime classpath drifted: "+pin.path());}
        private static void controlled(DirectoryIdentity pin)throws IOException {ascii(pin.path());verify(pin);}
        private static void ascii(String value)throws IOException {if(value.codePoints().anyMatch(code->code<32||code>126))throw new IOException("Only the caller-admitted physical carrier/output roots may use this ASCII route");}
        private static java.security.MessageDigest digest(){try{return java.security.MessageDigest.getInstance("SHA-256");}catch(java.security.NoSuchAlgorithmException error){throw new IllegalStateException(error);}}

        private static java.util.jar.Manifest manifest(PinnedFile original)throws IOException {
            verify(original);java.util.jar.Manifest result;
            try(var jar=new java.util.jar.JarFile(Path.of(original.path()).toFile(),true)){result=jar.getManifest();}
            verify(original);return result==null?new java.util.jar.Manifest():result;
        }
        private static boolean isArchive(Path path)throws IOException {try(var archive=new java.util.jar.JarFile(path.toFile(),true)){return archive.size()>=0;}catch(java.util.zip.ZipException notArchive){if(path.getFileName().toString().toLowerCase(java.util.Locale.ROOT).endsWith(".jar"))throw new IOException("Declared runtime JAR is not an intact archive",notArchive);return false;}}
        private static void jarClosure(Path path,LinkedHashMap<String,ClasspathPin> result,int depth)throws IOException {
            var file=captureFile(path);if(result.containsKey(file.path()))return;
            if(depth>32||result.size()>=MAXIMUM_CLASSPATH)throw new IOException("Finite JAR manifest dependency closure exceeded");
            result.put(file.path(),new FileClasspath(file));
            var attributes=manifest(file).getMainAttributes();
            // Module/native launcher attributes have no effect on classpath dependencies.
            // Agent and boot-path declarations retain the existing conservative prohibition.
            for(String unsupported:List.of("Launcher-Agent-Class","Boot-Class-Path"))
                if(attributes.getValue(unsupported)!=null)throw new IOException("Unsupported launcher-only JAR manifest attribute: "+unsupported);
            String declared=attributes.getValue(java.util.jar.Attributes.Name.CLASS_PATH);if(declared==null||declared.isBlank())return;
            for(String token:declared.trim().split(" +")){
                java.net.URI uri;try{uri=Path.of(file.path()).toUri().resolve(token);}catch(IllegalArgumentException error){throw new IOException("Malformed original manifest Class-Path",error);}
                if(!"file".equalsIgnoreCase(uri.getScheme())||uri.getRawQuery()!=null||uri.getRawFragment()!=null)throw new IOException("Only exact local manifest dependencies are supported");
                Path dependency;try{dependency=Path.of(uri).toRealPath(LinkOption.NOFOLLOW_LINKS);}catch(IllegalArgumentException error){throw new IOException("Invalid original manifest dependency",error);}
                var item=attributes(dependency);if(result.containsKey(dependency.toString()))continue;
                if(item.isDirectory()){if(result.size()>=MAXIMUM_CLASSPATH)throw new IOException("Finite manifest directory dependency count exceeded");result.put(dependency.toString(),captureClasspath(dependency));}
                else if(item.isRegularFile())jarClosure(dependency,result,depth+1);
                else throw new IOException("Unavailable original manifest classpath dependency");
            }
        }
        public static JarTarget captureJar(Path path)throws IOException {
            var jar=captureFile(path);var attributes=manifest(jar).getMainAttributes();
            // The same-JVM engine cannot emulate java -jar launcher effects for the actual entry JAR.
            for(String unsupported:List.of("Launcher-Agent-Class","Add-Exports","Add-Opens","Enable-Native-Access","Boot-Class-Path"))
                if(attributes.getValue(unsupported)!=null)throw new IOException("Unsupported launcher-only JAR manifest attribute: "+unsupported);
            var closure=new LinkedHashMap<String,ClasspathPin>();jarClosure(Path.of(jar.path()),closure,0);
            String main=attributes.getValue(java.util.jar.Attributes.Name.MAIN_CLASS);
            if(main==null||main.isBlank())throw new IOException("Original executable JAR Main-Class is missing");
            try{return new JarTarget(jar,main.trim(),List.copyOf(closure.values()));}catch(IllegalArgumentException error){throw new IOException("Invalid executable JAR main",error);}
        }
        private static List<ClasspathPin> effective(List<ClasspathPin> roots)throws IOException {
            var all=new LinkedHashMap<String,ClasspathPin>();for(var root:roots){verify(root);if(root instanceof FileClasspath&&isArchive(Path.of(root.path())))throw new IOException("A JAR root requires its exact manifest closure pin");if(root instanceof JarClasspath jar){for(var entry:jar.manifestClasspath())all.putIfAbsent(entry.path(),entry);}else all.putIfAbsent(root.path(),root);}
            if(all.size()>MAXIMUM_CLASSPATH)throw new IOException("Effective runtime closure is too large");return List.copyOf(all.values());
        }
        /** Peak additional output reservation; callers retain their existing whole-scope storage guard. */
        public static long maximumOutputBytes(Request request)throws IOException {
            return Math.addExact(Math.addExact(encode(request).length,preparationUpperBound(request)+8192L),request.target() instanceof SourceTarget source?Math.addExact(source.maximumCompiledBytes(),1280L*4096):0L);
        }
        private static long preparationUpperBound(Request request)throws IOException {
            if(request.target() instanceof SourceTarget)return MAXIMUM_ENVELOPE_BYTES;
            String mode,main,origin;List<ClasspathPin> complete;
            if(request.target() instanceof JarTarget target){mode="JAR";main=target.mainClass();origin=target.jar().path();complete=target.manifestClasspath();}
            else {var target=(ClassTarget)request.target();mode="CLASS";main=target.mainClass();origin=target.mainOrigin().path();var entries=new LinkedHashMap<String,ClasspathPin>();for(var root:target.classpath())if(root instanceof JarClasspath jar){for(var item:jar.manifestClasspath())entries.putIfAbsent(item.path(),item);}else entries.putIfAbsent(root.path(),root);complete=List.copyOf(entries.values());}
            // Only the not-yet-created path/provider key are unknown. JDK timestamps have bounded wire fields.
            var placeholder=new PinnedFile(request.evidenceRoot().path(),0,"0".repeat(64),new JdkFileMetadata("2000-01-01T00:00:00Z","2000-01-01T00:00:00Z",java.util.Optional.empty()));
            long known=encodePreparation(new Preparation(placeholder,mode,main,origin,complete,List.of())).length;
            return Math.min(MAXIMUM_ENVELOPE_BYTES,Math.addExact(known,131328L-utf8(placeholder.path()).length));
        }

        public static Publication publish(Request request,DirectoryIdentity envelopeRoot,String fileName,OutputGuard guard)throws IOException {
            Objects.requireNonNull(guard);controlled(envelopeRoot);controlled(request.evidenceRoot());if(!fileName.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"))throw new IOException("Exact controlled envelope filename required");
            Path path=Path.of(envelopeRoot.path()).resolve(fileName);if(path.equals(preparationPath(request))||Files.exists(preparationPath(request),LinkOption.NOFOLLOW_LINKS))throw new IOException("Original invocation preparation output is already occupied");
            if(request.target() instanceof SourceTarget source&&(path.startsWith(Path.of(source.compiledRoot().path()))||preparationPath(request).startsWith(Path.of(source.compiledRoot().path()))))throw new IOException("Compilation output must be disjoint from retained invocation evidence");
            verifyRequest(request);byte[] raw=encode(request);guard.require(maximumOutputBytes(request));
            Files.write(path,raw,StandardOpenOption.CREATE_NEW);verify(envelopeRoot);return new Publication(captureFile(path));
        }
        public static Path preparationPath(Request request){return preparationPath(request.evidenceRoot());}
        public static Path preparationPath(DirectoryIdentity evidenceRoot){return Path.of(evidenceRoot.path()).resolve("java-utf8-prepared.bin");}
        public static Request read(Publication publication)throws IOException {return decode(pinnedBytes(publication.envelope(),MAXIMUM_ENVELOPE_BYTES));}
        private static byte[] pinnedBytes(PinnedFile pin,int maximum)throws IOException {
            if(pin.bytes()>maximum)throw new IOException("Pinned input exceeds this bounded role");verify(pin);byte[] raw=Files.readAllBytes(Path.of(pin.path()));
            if(raw.length!=pin.bytes()||!java.util.HexFormat.of().formatHex(digest().digest(raw)).equals(pin.sha256()))throw new IOException("Pinned input bytes changed while opening");verify(pin);return raw;
        }
        private static void verifyRequest(Request request)throws IOException {
            controlled(request.evidenceRoot());
            if(request.target() instanceof ClassTarget target)effective(target.classpath());
            else if(request.target() instanceof JarTarget target){if(!target.equals(captureJar(Path.of(target.jar().path()))))throw new IOException("Executable JAR source closure changed");}
            else {var target=(SourceTarget)request.target();verify(target.source());controlled(target.compiledRoot());effective(target.classpath());}
        }
        public static Launch launch(Publication publication,Carrier carrier,List<String> asciiVmOptions)throws IOException {
            Request request=read(publication);verifyRequest(request);var args=new ArrayList<String>();
            for(String option:asciiVmOptions){text(option);ascii(option);if(!option.startsWith("-")||option.equals("-cp")||option.equals("-classpath")||option.startsWith("--class-path")||option.equals("-jar")||option.equals("-m")||option.startsWith("--module")||option.startsWith("--source")||Set.of("--","-version","--version","-help","--help","-?","-X","--dry-run").contains(option))throw new IOException("Actual startup-only JVM options cannot override or skip the carrier entry");args.add(option);}
            if(carrier instanceof ClassCarrier classes){for(var pin:classes.classpath()){ascii(pin.path());verify(pin);}args.add("-cp");args.add(String.join(java.io.File.pathSeparator,classes.classpath().stream().map(ClasspathPin::path).toList()));args.add(CiBootstrap.class.getName());}
            else {var source=((SourceCarrier)carrier).source();ascii(source.path());verify(source);if(!Path.of(source.path()).getFileName().toString().equals("CiBootstrap.java"))throw new IOException("Single actual CiBootstrap source carrier required");args.add("--source");args.add("21");args.add(source.path());}
            PinnedFile pin=publication.envelope();ascii(pin.path());args.add(ENTRY);args.add(pin.path());args.add(Long.toString(pin.bytes()));args.add(pin.sha256());args.add(java.util.Base64.getEncoder().encodeToString(metadataBytes(pin.metadata())));return new Launch(args,publication,request);
        }
        /** Finite original JDK input observations. Native callers separately acquire actual held OS witnesses. */
        public record JdkInputs(List<PinnedFile> files,List<DirectoryIdentity> directories) {
            public JdkInputs { files=List.copyOf(files);directories=List.copyOf(directories);if(files.size()>32768||directories.size()>4096)throw new IllegalArgumentException("Finite complete input set required"); }
        }
        public static JdkInputs inputSnapshot(Launch launch,Carrier carrier)throws IOException {
            Request request=read(launch.publication());if(!request.equals(launch.logicalRequest()))throw new IOException("Launch is not its original published request");verifyRequest(request);
            var files=new LinkedHashMap<String,PinnedFile>();var directories=new LinkedHashMap<String,DirectoryIdentity>();
            addFile(files,launch.publication().envelope());directories.put(request.evidenceRoot().path(),request.evidenceRoot());
            if(request.target() instanceof ClassTarget target){for(var pin:target.classpath())addInput(pin,files,directories);}
            else if(request.target() instanceof JarTarget target){for(var pin:target.manifestClasspath())addInput(pin,files,directories);}
            else {var target=(SourceTarget)request.target();addFile(files,target.source());directories.put(target.compiledRoot().path(),target.compiledRoot());for(var pin:target.classpath())addInput(pin,files,directories);}
            if(carrier instanceof ClassCarrier classes){for(var pin:classes.classpath())addInput(pin,files,directories);}else addFile(files,((SourceCarrier)carrier).source());
            for(var file:files.values())verify(file);for(var folder:directories.values())verify(folder);return new JdkInputs(List.copyOf(files.values()),List.copyOf(directories.values()));
        }
        private static void addFile(Map<String,PinnedFile> files,PinnedFile pin)throws IOException {var previous=files.putIfAbsent(pin.path(),pin);if(previous!=null&&!previous.equals(pin))throw new IOException("Conflicting same-path original file observations");}
        private static void addInput(ClasspathPin pin,Map<String,PinnedFile> files,Map<String,DirectoryIdentity> directories)throws IOException {
            verify(pin);if(pin instanceof FileClasspath file)addFile(files,file.file());else if(pin instanceof JarClasspath jar){for(var item:jar.manifestClasspath())addInput(item,files,directories);}else {var folder=(DirectoryClasspath)pin;var previous=directories.putIfAbsent(folder.path(),folder.directory());if(previous!=null&&!previous.equals(folder.directory()))throw new IOException("Conflicting same-path directory observations");for(var file:folder.files())addFile(files,file);}
        }
        /** New readers compare the complete physical command against their original expected carrier and VM options. */
        public static Request inspect(List<String> physicalArguments,Carrier expectedCarrier,List<String> asciiVmOptions)throws IOException {
            int start=physicalArguments.size()-5;if(start<1||!physicalArguments.get(start).equals(ENTRY)||physicalArguments.stream().filter(ENTRY::equals).count()!=1)throw new IOException("Exact explicit UTF8 carrier invocation required");
            Publication publication=entryPublication(physicalArguments.subList(start,physicalArguments.size()).toArray(String[]::new));Launch expected=launch(publication,expectedCarrier,asciiVmOptions);if(!expected.physicalArguments().equals(physicalArguments))throw new IOException("Physical carrier/VM arguments differ from the original declaration");return expected.logicalRequest();
        }
        private static Publication entryPublication(String[] arguments)throws IOException {
            if(arguments.length!=5||!ENTRY.equals(arguments[0])||!arguments[2].matches("[1-9][0-9]*"))throw new IOException("Exact pinned invocation entry arguments required");
            for(String argument:arguments)ascii(argument);
            try{return new Publication(new PinnedFile(arguments[1],Long.parseLong(arguments[2]),arguments[3],readMetadataBytes(java.util.Base64.getDecoder().decode(arguments[4]))));}
            catch(IllegalArgumentException error){throw new IOException("Malformed pinned invocation entry",error);}
        }
        private static byte[] utf8(String value)throws IOException {
            try {var encoded=StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).encode(java.nio.CharBuffer.wrap(value));byte[] bytes=new byte[encoded.remaining()];encoded.get(bytes);return bytes;}
            catch(java.nio.charset.CharacterCodingException error){throw new IOException("Malformed Unicode text in invocation",error);}
        }
        private static String decodeUtf8(byte[] bytes)throws IOException {
            try{return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();}
            catch(java.nio.charset.CharacterCodingException error){throw new IOException("Malformed UTF8 invocation bytes",error);}
        }
        private static final class LimitedBytes extends java.io.ByteArrayOutputStream {
            @Override public synchronized void write(int value){if(count>=MAXIMUM_ENVELOPE_BYTES)throw new IllegalArgumentException("Invocation exceeds its finite wire limit");super.write(value);}
            @Override public synchronized void write(byte[] bytes,int offset,int length){if(length>MAXIMUM_ENVELOPE_BYTES-count)throw new IllegalArgumentException("Invocation exceeds its finite wire limit");super.write(bytes,offset,length);}
        }
        private static void string(java.io.DataOutputStream out,String value)throws IOException {byte[] bytes=utf8(value);if(bytes.length>65536)throw new IOException("Bounded invocation field required");out.writeInt(bytes.length);out.write(bytes);}
        private static String string(java.io.DataInputStream in)throws IOException {int count=count(in,65536);return decodeUtf8(exact(in,count));}
        private static int count(java.io.DataInputStream in,int maximum)throws IOException {int count=in.readInt();if(count<0||count>maximum)throw new IOException("Invocation field count outside declared bounds");return count;}
        private static byte[] exact(java.io.DataInputStream in,int count)throws IOException {byte[] bytes=in.readNBytes(count);if(bytes.length!=count)throw new java.io.EOFException("Truncated invocation envelope");return bytes;}
        private static void optional(java.io.DataOutputStream out,java.util.Optional<String> value)throws IOException {out.writeByte(value.isPresent()?1:0);if(value.isPresent())string(out,value.orElseThrow());}
        private static java.util.Optional<String> optional(java.io.DataInputStream in)throws IOException {return switch(in.readUnsignedByte()){case 0->java.util.Optional.empty();case 1->java.util.Optional.of(string(in));default->throw new IOException("Unknown JDK provider-key presence tag");};}
        private static void metadata(java.io.DataOutputStream out,JdkFileMetadata value)throws IOException {string(out,value.createdAt());string(out,value.modifiedAt());optional(out,value.providerFileKey());}
        private static JdkFileMetadata metadata(java.io.DataInputStream in)throws IOException {return new JdkFileMetadata(string(in),string(in),optional(in));}
        private static byte[] metadataBytes(JdkFileMetadata value)throws IOException {var bytes=new java.io.ByteArrayOutputStream();var out=new java.io.DataOutputStream(bytes);out.writeInt(2);metadata(out,value);out.flush();return bytes.toByteArray();}
        private static JdkFileMetadata readMetadataBytes(byte[] raw)throws IOException {if(raw.length>131328)throw new IOException("Bounded JDK metadata entry required");var in=new java.io.DataInputStream(new java.io.ByteArrayInputStream(raw));if(in.readInt()!=2)throw new IOException("Unknown JDK metadata entry version; legacy nativeKey is not a Win32 witness");var value=metadata(in);if(in.read()!=-1||!java.util.Arrays.equals(raw,metadataBytes(value)))throw new IOException("Noncanonical or trailing JDK metadata entry");return value;}
        private static void pin(java.io.DataOutputStream out,PinnedFile value)throws IOException {string(out,value.path());out.writeLong(value.bytes());string(out,value.sha256());metadata(out,value.metadata());}
        private static PinnedFile pin(java.io.DataInputStream in)throws IOException {return new PinnedFile(string(in),in.readLong(),string(in),metadata(in));}
        private static void dir(java.io.DataOutputStream out,DirectoryIdentity value)throws IOException {string(out,value.path());string(out,value.metadata().createdAt());optional(out,value.metadata().providerFileKey());}
        private static DirectoryIdentity dir(java.io.DataInputStream in)throws IOException {return new DirectoryIdentity(string(in),new JdkDirectoryMetadata(string(in),optional(in)));}
        private static void pins(java.io.DataOutputStream out,List<PinnedFile> files)throws IOException {out.writeInt(files.size());for(var file:files)pin(out,file);}
        private static List<PinnedFile> pins(java.io.DataInputStream in)throws IOException {int size=count(in,MAXIMUM_FILES);var files=new ArrayList<PinnedFile>();for(int index=0;index<size;index++)files.add(pin(in));return List.copyOf(files);}
        private static void cp(java.io.DataOutputStream out,ClasspathPin value)throws IOException {
            if(value instanceof FileClasspath file){out.writeByte(1);pin(out,file.file());}
            else if(value instanceof DirectoryClasspath folder){out.writeByte(2);dir(out,folder.directory());pins(out,folder.files());}
            else {var jar=(JarClasspath)value;out.writeByte(3);pin(out,jar.jar());cps(out,jar.manifestClasspath());}
        }
        private static ClasspathPin cp(java.io.DataInputStream in,int depth)throws IOException {
            if(depth>1)throw new IOException("Nested manifest closure is not a canonical invocation");
            return switch(in.readUnsignedByte()){
                case 1->new FileClasspath(pin(in));case 2->new DirectoryClasspath(dir(in),pins(in));
                case 3->new JarClasspath(pin(in),cps(in,depth+1));default->throw new IOException("Unknown invocation classpath tag");};
        }
        private static void cps(java.io.DataOutputStream out,List<ClasspathPin> values)throws IOException {out.writeInt(values.size());for(var value:values)cp(out,value);}
        private static List<ClasspathPin> cps(java.io.DataInputStream in,int depth)throws IOException {int size=count(in,MAXIMUM_CLASSPATH);var values=new ArrayList<ClasspathPin>();for(int index=0;index<size;index++)values.add(cp(in,depth));return List.copyOf(values);}
        public static byte[] encode(Request request)throws IOException {
            try {var bytes=new LimitedBytes();var out=new java.io.DataOutputStream(bytes);out.writeInt(MAGIC);out.writeInt(2);
                if(request.target() instanceof ClassTarget target){out.writeByte(1);string(out,target.mainClass());cp(out,target.mainOrigin());cps(out,target.classpath());}
                else if(request.target() instanceof JarTarget target){out.writeByte(2);pin(out,target.jar());string(out,target.mainClass());cps(out,target.manifestClasspath());}
                else {var target=(SourceTarget)request.target();out.writeByte(3);pin(out,target.source());string(out,target.mainClass());cps(out,target.classpath());dir(out,target.compiledRoot());out.writeLong(target.maximumCompiledBytes());}
                out.writeInt(request.properties().size());for(var property:request.properties()){string(out,property.name());string(out,property.value());}
                out.writeInt(request.arguments().size());for(String argument:request.arguments())string(out,argument);dir(out,request.evidenceRoot());out.flush();return bytes.toByteArray();
            }catch(IllegalArgumentException error){throw new IOException("Invocation is not a bounded canonical value",error);}
        }
        public static Request decode(byte[] original)throws IOException {
            if(original.length<9||original.length>MAXIMUM_ENVELOPE_BYTES)throw new IOException("Bounded versioned invocation envelope required");
            try {var in=new java.io.DataInputStream(new java.io.ByteArrayInputStream(original));if(in.readInt()!=MAGIC||in.readInt()!=2)throw new IOException("Unknown Java invocation schema/version; legacy v1 is not native-qualified");
                Target target=switch(in.readUnsignedByte()){
                    case 1->new ClassTarget(string(in),cp(in,0),cps(in,0));
                    case 2->new JarTarget(pin(in),string(in),cps(in,0));
                    case 3->new SourceTarget(pin(in),string(in),cps(in,0),dir(in),in.readLong());
                    default->throw new IOException("Unknown Java invocation target");};
                int propertyCount=count(in,256);var properties=new ArrayList<Property>();for(int index=0;index<propertyCount;index++)properties.add(new Property(string(in),string(in)));
                int argumentCount=count(in,4096);var arguments=new ArrayList<String>();for(int index=0;index<argumentCount;index++)arguments.add(string(in));
                var result=new Request(target,properties,arguments,dir(in));if(in.read()!=-1)throw new IOException("Trailing bytes in Java invocation envelope");
                if(!java.util.Arrays.equals(original,encode(result)))throw new IOException("Noncanonical Java invocation envelope");return result;
            }catch(IllegalArgumentException error){throw new IOException("Malformed typed Java invocation",error);}
        }

        private static byte[] encodePreparation(Preparation value)throws IOException {
            try {var bytes=new LimitedBytes();var out=new java.io.DataOutputStream(bytes);out.writeInt(PREPARED_MAGIC);out.writeInt(2);pin(out,value.envelope());string(out,value.mode());string(out,value.mainClass());string(out,value.actualCodeSource());cps(out,value.effectiveClasspath());pins(out,value.compiledClasses());out.flush();return bytes.toByteArray();}
            catch(IllegalArgumentException error){throw new IOException("Preparation proof exceeds its finite output reservation",error);}
        }
        /** This proves preparation/source binding only. It never substitutes for the original Job terminal result. */
        public static Preparation readPreparation(PinnedFile original)throws IOException {
            byte[] raw=pinnedBytes(original,MAXIMUM_ENVELOPE_BYTES);
            try {var in=new java.io.DataInputStream(new java.io.ByteArrayInputStream(raw));if(in.readInt()!=PREPARED_MAGIC||in.readInt()!=2)throw new IOException("Unknown Java preparation proof version; legacy v1 is not native-qualified");
                var value=new Preparation(pin(in),string(in),string(in),string(in),cps(in,0),pins(in));if(in.read()!=-1||!java.util.Arrays.equals(raw,encodePreparation(value)))throw new IOException("Noncanonical or trailing preparation bytes");verify(value.envelope());for(var entry:value.effectiveClasspath())verify(entry);for(var file:value.compiledClasses())verify(file);return value;
            }catch(IllegalArgumentException error){throw new IOException("Malformed preparation proof",error);}
        }
        /** Rebinds the actual preparation proof to its original request. Still never grants a successful main/Job terminal. */
        public static Preparation inspectPreparation(PinnedFile original,Publication publication)throws IOException {
            Request request=read(publication);verifyRequest(request);Preparation proof=readPreparation(original);
            if(!original.path().equals(preparationPath(request).toString())||!proof.envelope().equals(publication.envelope()))throw new IOException("Preparation is not the original invocation output");
            String mode,main,origin;List<ClasspathPin> closure;List<PinnedFile> generated=List.of();
            if(request.target() instanceof ClassTarget target){mode="CLASS";main=target.mainClass();origin=target.mainOrigin().path();closure=effective(target.classpath());}
            else if(request.target() instanceof JarTarget target){mode="JAR";main=target.mainClass();origin=target.jar().path();closure=target.manifestClasspath();}
            else {var target=(SourceTarget)request.target();mode="SOURCE";main=target.mainClass();origin=target.compiledRoot().path();var compiled=(DirectoryClasspath)captureClasspath(Path.of(origin));generated=compiled.files();var roots=new ArrayList<ClasspathPin>();roots.add(compiled);roots.addAll(target.classpath());closure=effective(roots);}
            var expected=new Preparation(publication.envelope(),mode,main,origin,closure,generated);if(!expected.equals(proof))throw new IOException("Preparation mode/main/original code source or complete effective deployment differs");return proof;
        }
        private static final List<java.net.URLClassLoader> LIVE_LOADERS=new ArrayList<>();
        private record Compiled(DirectoryClasspath classes,List<PinnedFile> generated) { }
        private static Compiled compile(SourceTarget target)throws IOException {
            String originalSource=decodeUtf8(pinnedBytes(target.source(),4<<20));controlled(target.compiledRoot());for(var pin:target.classpath())verify(pin);
            Path output=Path.of(target.compiledRoot().path());try(var entries=Files.list(output)){if(entries.findAny().isPresent())throw new IOException("Single-source compilation requires its original empty controlled output directory");}
            var compiler=javax.tools.ToolProvider.getSystemJavaCompiler();if(compiler==null||Runtime.version().feature()!=21)throw new IOException("Actual JDK21 compiler required for source mode");
            var generated=new ArrayList<Path>();long[] written={0L};int[] newDirectories={0};var diagnostic=new LimitedBytes();
            try(var standard=compiler.getStandardFileManager(null,java.util.Locale.ROOT,StandardCharsets.UTF_8)){
                var manager=new javax.tools.ForwardingJavaFileManager<javax.tools.StandardJavaFileManager>(standard){
                    @Override public javax.tools.JavaFileObject getJavaFileForOutput(javax.tools.JavaFileManager.Location location,String className,javax.tools.JavaFileObject.Kind kind,javax.tools.FileObject sibling)throws IOException {
                        if(location!=javax.tools.StandardLocation.CLASS_OUTPUT||kind!=javax.tools.JavaFileObject.Kind.CLASS||generated.size()>=1024)throw new IOException("Unexpected or unbounded single-source compiler output");
                        Path next=output.resolve(className.replace('.','/')+kind.extension).normalize();if(!next.startsWith(output)||next.equals(output))throw new IOException("Compiler output escaped the original root");
                        controlled(target.compiledRoot());Path parent=next.getParent();Path relative=output.relativize(parent);Path current=output;
                        for(Path segment:relative){current=current.resolve(segment);try{if(++newDirectories[0]>256)throw new IOException("Compiler output directory maximum exceeded");Files.createDirectory(current);}catch(java.nio.file.FileAlreadyExistsException existing){newDirectories[0]--;if(!attributes(current).isDirectory())throw new IOException("Compiler output parent is not an original directory",existing);}}
                        generated.add(next);
                        return new javax.tools.SimpleJavaFileObject(next.toUri(),kind){
                            @Override public OutputStream openOutputStream()throws IOException {
                                OutputStream raw=Files.newOutputStream(next,StandardOpenOption.CREATE_NEW);
                                return new java.io.FilterOutputStream(raw){
                                    private void reserve(int count)throws IOException {written[0]=Math.addExact(written[0],count);if(written[0]>target.maximumCompiledBytes())throw new IOException("Source compilation exceeded its admitted output maximum");}
                                    @Override public void write(int value)throws IOException {reserve(1);out.write(value);}
                                    @Override public void write(byte[] bytes,int offset,int count)throws IOException {reserve(count);out.write(bytes,offset,count);}
                                };
                            }
                        };
                    }
                    @Override public javax.tools.FileObject getFileForOutput(javax.tools.JavaFileManager.Location location,String packageName,String relativeName,javax.tools.FileObject sibling)throws IOException {throw new IOException("No resource or annotation-processor output is admitted in single-source mode");}
                };
                var options=new ArrayList<String>(List.of("--release","21","-proc:none","-encoding","UTF-8","-implicit:none"));
                if(!target.classpath().isEmpty()){options.add("-classpath");options.add(String.join(java.io.File.pathSeparator,target.classpath().stream().map(ClasspathPin::path).toList()));}
                else {options.add("-classpath");options.add(output.toString());}
                boolean success;try(var writer=new java.io.OutputStreamWriter(diagnostic,StandardCharsets.UTF_8)){
                    var sourceUnit=new javax.tools.SimpleJavaFileObject(Path.of(target.source().path()).toUri(),javax.tools.JavaFileObject.Kind.SOURCE){@Override public CharSequence getCharContent(boolean ignoreEncodingErrors){return originalSource;}};
                    success=Boolean.TRUE.equals(compiler.getTask(writer,manager,null,options,null,List.of(sourceUnit)).call());
                }catch(RuntimeException error){throw new IOException("Single-source compilation failed within its original admitted output",error);}
                if(!success)throw new IOException("Single-source compilation rejected original source: "+decodeUtf8(diagnostic.toByteArray()));
            }
            verify(target.source());controlled(target.compiledRoot());for(var pin:target.classpath())verify(pin);
            var classes=(DirectoryClasspath)captureClasspath(output);if(classes.files().size()!=generated.size())throw new IOException("Unexpected source compilation output appeared");
            for(Path generatedFile:generated)if(classes.files().stream().noneMatch(pin->pin.path().equals(generatedFile.toString())))throw new IOException("Compiled class is absent from its complete pinned inventory");
            return new Compiled(classes,classes.files());
        }
        /** Same JVM entry. Target classes never delegate to the carrier's build-tools classloader. */
        public static void run(Publication publication)throws Exception {
            Request request=read(publication);controlled(request.evidenceRoot());String main;String mode;String expectedOrigin;
            List<ClasspathPin> roots;List<ClasspathPin> complete;List<PinnedFile> generated=List.of();
            if(request.target() instanceof ClassTarget target){main=target.mainClass();mode="CLASS";expectedOrigin=target.mainOrigin().path();roots=target.classpath();complete=effective(roots);}
            else if(request.target() instanceof JarTarget target){
                var current=captureJar(Path.of(target.jar().path()));if(!target.equals(current))throw new IOException("Original executable JAR main/manifest/deployment changed");
                main=target.mainClass();mode="JAR";expectedOrigin=target.jar().path();roots=List.of(new FileClasspath(target.jar()));complete=target.manifestClasspath();
                for(var pin:complete)verify(pin);
            }else {var target=(SourceTarget)request.target();var compiled=compile(target);main=target.mainClass();mode="SOURCE";expectedOrigin=compiled.classes().path();generated=compiled.generated();var values=new ArrayList<ClasspathPin>();values.add(compiled.classes());values.addAll(target.classpath());roots=List.copyOf(values);complete=effective(roots);}
            for(var property:request.properties())System.setProperty(property.name(),property.value());
            // java.class.path is a target-observation property, not a substitute for actual startup VM options.
            System.setProperty("java.class.path",String.join(java.io.File.pathSeparator,roots.stream().map(ClasspathPin::path).toList()));
            java.net.URL[] urls=new java.net.URL[roots.size()];for(int index=0;index<roots.size();index++)urls[index]=Path.of(roots.get(index).path()).toUri().toURL();
            var loader=new java.net.URLClassLoader(urls,ClassLoader.getPlatformClassLoader());
            // Deliberately retained until JVM teardown: server main may return while its non-daemon threads still load classes.
            synchronized(LIVE_LOADERS){LIVE_LOADERS.add(loader);}
            Thread.currentThread().setContextClassLoader(loader);
            Class<?> actual=Class.forName(main,false,loader);if(actual.getClassLoader()!=loader||actual.getProtectionDomain().getCodeSource()==null)throw new IOException("Main class did not originate in its exact target loader");
            Path actualOrigin=Path.of(actual.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath(LinkOption.NOFOLLOW_LINKS);
            if(!actualOrigin.equals(Path.of(expectedOrigin)))throw new IOException("Target main was shadowed by another deployment member");
            var entry=actual.getMethod("main",String[].class);if(!java.lang.reflect.Modifier.isStatic(entry.getModifiers())||entry.getReturnType()!=void.class)throw new IOException("Exact public static void main(String[]) entry required");
            for(var pin:complete)verify(pin);verify(publication.envelope());controlled(request.evidenceRoot());
            var prepared=new Preparation(publication.envelope(),mode,main,actualOrigin.toString(),complete,generated);
            byte[] proof=encodePreparation(prepared);Files.write(preparationPath(request),proof,StandardOpenOption.CREATE_NEW);controlled(request.evidenceRoot());
            try {entry.invoke(null,(Object)request.arguments().toArray(String[]::new));}
            catch(InvocationTargetException error){Throwable cause=error.getCause();if(cause instanceof Exception exception)throw exception;if(cause instanceof Error fatal)throw fatal;throw new IOException("Target main failed",cause);}
        }
    }
}
