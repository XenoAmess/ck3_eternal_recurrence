package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Finite two-target operation. All process ownership is the shared WindowsJobProcess. */
public final class NativeFixtureBuild {
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final Path REPO = Path.of("Z:/ck3_mod_rewrite");
    private static final Path SOURCE = REPO.resolve("ck3_autonomous_player/native_bridge");
    private static final Path WORK = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1");
    private static final List<Path> PREVIOUS_BUILDS = List.of(WORK.resolve("build/native-prisoners-combat01"), WORK.resolve("build/native-prisoners-combat02"), WORK.resolve("build/native-prisoners-combat03"), WORK.resolve("build/native-prisoners-combat04"));
    private static final Path BUILD = WORK.resolve("build/native-prisoners-combat05");
    private static final Path SCRATCH = WORK.resolve("scratch/native-prisoners-combat05");
    private static final String KINSHIP = "ck3_12003_prisoner_native_kinship_test";
    private static final String COMBAT = "xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test";
    private static final String RUNTIME = "xar_ck3_12002_runtime";
    private static final String CONFIGURE_ID = "configure-next01";
    private static final List<String> TARGETS = List.of(KINSHIP, COMBAT);
    private static final List<String> CASES = List.of("nonchild_close_family", "unrelated", "sample_drift",
            "wrong_generation", "wrong_jailer", "not_paused");
    private static final Pattern INCLUDE = Pattern.compile("(?m)^\\s*#\\s*include\\s*([\"<])([^\">]+)[\">]");
    private static final long MEMORY = 2L << 30;
    private static final long ENV_MEMORY = 256L << 20;
    private static final long ENV_SCRATCH_CAP = 16L << 20;
    private static final long BUILD_CAP = 512L << 20;
    private static final long SCRATCH_CAP = 128L << 20;
    private static final long LOG_CAP = 2L << 20;
    private static final long DEPENDENCY_EVIDENCE_CAP = 16L << 20;

    private NativeFixtureBuild() { }
    public enum Stage { ENV, VERSIONS, VENDOR_TIMEOUTS, CONFIGURE, GRAPH, BUILD, REGISTER, KINSHIP, COMBAT }
    public enum ActualStatus { PASS, RED }
    public enum ResourceStatus { ADMITTED_SINGLE_STAGE }
    public enum GraphStatus { CONFIGURED_SOURCE_FROZEN_NOT_BUILT }
    public enum RegistrationPreparationStatus { PREPARED_NOT_SUBMITTED }
    public enum EnvironmentPreparationStatus { PREPARED_NOT_AUTHORIZED }
    public enum VendorTimeoutStatus { NATURAL_CASES_OBSERVED_NOT_CONFIGURE_QUALIFIED }
    public enum TargetType { STATIC_LIBRARY, EXECUTABLE }
    /** Exact command-stage identities; graph metadata itself is not a native command terminal. */
    public enum ActualStage {
        ENV_TOOL_PROBE("env-tool-probe", false, false),
        VERSION_CMAKE("version-cmake", true, false),
        VERSION_NINJA("version-ninja", true, false),
        VERSION_CL_HELP("version-cl-help", true, false),
        VENDOR_TIMEOUT_ONE("vendor-timeout-one", true, false),
        VENDOR_TIMEOUT_TWO("vendor-timeout-two", true, false),
        CONFIGURE_NEXT01("configure-next01", true, false),
        CONFIGURED_COMMANDS("configured-commands", true, true),
        TWO_TARGET_BUILD("two-target-build", true, true),
        COMPILER_ACTIVE_DEPENDENCIES("compiler-active-dependencies", true, true),
        DEFENDER_REGISTER_TWO("defender-register-two", true, true),
        KINSHIP_PRODUCER("kinship-producer", true, true),
        COMBATROLES_PRODUCER("combatroles-producer", true, true);
        private final String wireId;
        private final boolean environmentRequired;
        private final boolean graphRequired;
        ActualStage(String wireId, boolean environmentRequired, boolean graphRequired) {
            this.wireId = wireId; this.environmentRequired = environmentRequired; this.graphRequired = graphRequired;
        }
        public String wireId() { return wireId; }
    }
    public record Config(Stage stage, Path resourceCard, Path toolsReceipt, Path plan, Path operationSource) {
        public Config {
            if (stage == null) throw new IllegalArgumentException("finite stage required");
            for (Path path : List.of(resourceCard, toolsReceipt, plan, operationSource)) {
                if (!path.isAbsolute()) throw new IllegalArgumentException("absolute pinned inputs required");
            }
        }
    }
    public record RegistrationExecution(Config config, Path reviewedPlan, String reviewedPlanSha256) {
        public RegistrationExecution {
            if (config == null || config.stage() != Stage.REGISTER || reviewedPlan == null || !reviewedPlan.isAbsolute()
                    || reviewedPlanSha256 == null || !reviewedPlanSha256.matches("[0-9a-f]{64}")) {
                throw new IllegalArgumentException("REGISTER requires the concrete Root-reviewed plan and canonical SHA-256");
            }
        }
    }
    public record ResourceCard(String schema, String machineId, String observedAtUtc, String reviewAtUtc,
            String owner, ResourceStatus status, Stage allowedStage, long memoryLimitBytes, long scratchLimitBytes, int timeoutSeconds,
            ControlBuild.FileRef releaseRef, ControlBuild.FileRef partReallocationRef,
            ControlBuild.FileRef toolsReceiptRef, ControlBuild.FileRef toolsAcceptedReadbackRef,
            ControlBuild.FileRef packageRequestRef, ControlBuild.FileRef sourceManifestRef,
            List<ControlBuild.FileRef> requiredPriorActualRefs, List<String> outputRoots) {
        public ResourceCard {
            requiredPriorActualRefs = List.copyOf(requiredPriorActualRefs); outputRoots = List.copyOf(outputRoots);
            if (!"xar.shared-native-stage-resource-card/v2".equals(schema) || !MACHINE.equals(machineId)
                    || !"/root/native_fixture09".equals(owner) || status != ResourceStatus.ADMITTED_SINGLE_STAGE
                    || allowedStage == null || memoryLimitBytes < (16L << 20) || memoryLimitBytes > stageMemoryLimit(allowedStage)
                    || allowedStage == Stage.VENDOR_TIMEOUTS && memoryLimitBytes != ENV_MEMORY
                    || scratchLimitBytes < 4096 || scratchLimitBytes > stageScratchLimit(allowedStage)
                    || timeoutSeconds < 1 || timeoutSeconds > stageTimeout(allowedStage)
                    || !Instant.parse(observedAtUtc).isBefore(Instant.parse(reviewAtUtc)) || outputRoots.isEmpty()) {
                throw new IllegalArgumentException("finite exact native stage authority required");
            }
        }
    }
    public record IncludeDirectory(String path, boolean system) { }
    public record CommandFragment(String fragment, String role) { }
    public record CompileGroup(String language, String languageStandard, List<String> compileCommandFragments,
            List<String> definitions, List<IncludeDirectory> includeDirectories) {
        public CompileGroup {
            compileCommandFragments = List.copyOf(compileCommandFragments); definitions = List.copyOf(definitions);
            includeDirectories = List.copyOf(includeDirectories);
        }
    }
    /** language and lto are null only when absent from the original File API object. */
    public record LinkData(String language, Boolean lto, List<CommandFragment> commandFragments) {
        public LinkData { commandFragments = List.copyOf(commandFragments); }
    }
    public record Target(String name, String id, TargetType type, ControlBuild.FileRef definitionRef,
            List<ControlBuild.FileRef> translationUnits, List<String> artifacts,
            List<String> dependencyIds, List<CompileGroup> compileGroups, LinkData link, LinkData archive) {
        public Target {
            translationUnits = List.copyOf(translationUnits); artifacts = List.copyOf(artifacts);
            dependencyIds = List.copyOf(dependencyIds); compileGroups = List.copyOf(compileGroups);
        }
    }
    public record Graph(String schema, String machineId, String observedAtUtc, GraphStatus status,
            ControlBuild.FileRef configureReceiptRef, List<Target> targets,
            List<ControlBuild.FileRef> configuredInputRefs, List<ControlBuild.FileRef> configuredToolRefs, List<ControlBuild.FileRef> projectSourceRefs,
            ControlBuild.FileRef runtimeSourcesRef, int runtimeTranslationUnitCount,
            List<String> activeHeaderEvidenceBoundary) {
        public Graph {
            targets = List.copyOf(targets); configuredInputRefs = List.copyOf(configuredInputRefs); configuredToolRefs = List.copyOf(configuredToolRefs);
            projectSourceRefs = List.copyOf(projectSourceRefs);
            activeHeaderEvidenceBoundary = List.copyOf(activeHeaderEvidenceBoundary);
        }
    }
    public record SourceManifest(String schema, String machineId, String observedAtUtc,
            List<ControlBuild.FileRef> sourceRefs, List<ControlBuild.FileRef> toolRefs,
            List<ControlBuild.FileRef> operationRuntimeRefs) {
        public SourceManifest {
            sourceRefs = sorted(sourceRefs); toolRefs = sorted(toolRefs);
            operationRuntimeRefs = sorted(operationRuntimeRefs);
        }
    }
    /** Two observed vendor terminals only; compiler reuse and configure drain remain unqualified. */
    public record VendorTimeouts(String schema, String machineId, String observedAtUtc, VendorTimeoutStatus status,
            String stageDeadlineAtUtc, ControlBuild.FileRef vendorRef, ControlBuild.FileRef sourceManifestRef,
            ControlBuild.FileRef toolsReceiptRef, ControlBuild.FileRef environmentRef,
            ControlBuild.FileRef firstActualRef, VctipProbeFacts.Analysis firstAnalysis,
            ControlBuild.FileRef secondActualRef, VctipProbeFacts.Analysis secondAnalysis) {
        public VendorTimeouts {
            if (!"xar.native-vendor-timeouts/v1".equals(schema) || !MACHINE.equals(machineId)
                    || status != VendorTimeoutStatus.NATURAL_CASES_OBSERVED_NOT_CONFIGURE_QUALIFIED
                    || vendorRef == null || sourceManifestRef == null || toolsReceiptRef == null || environmentRef == null
                    || firstActualRef == null || secondActualRef == null || firstAnalysis == null || secondAnalysis == null)
                throw new IllegalArgumentException("complete typed vendor observations required");
            Instant.parse(observedAtUtc); Instant.parse(stageDeadlineAtUtc);
        }
    }
    public record Dependencies(String schema, String machineId, String observedAtUtc, String scope,
            ControlBuild.FileRef rawRef, List<ControlBuild.FileRef> dependencyRefs) {
        public Dependencies {
            dependencyRefs = List.copyOf(dependencyRefs);
            if (!"xar.native-actual-compiler-dependencies/v1".equals(schema) || !MACHINE.equals(machineId)
                    || scope == null || scope.isBlank() || rawRef == null || dependencyRefs.isEmpty()) {
                throw new IllegalArgumentException("actual typed compiler dependency closure required");
            }
            Instant.parse(observedAtUtc);
        }
    }
    public record RegistrationExecutable(String target, ControlBuild.FileRef fileRef) { }
    public record PreparedRegistration(String schema, String machineId, String observedAtUtc,
            String deadlineAtUtc, String owner, RegistrationPreparationStatus status, String nativeBuildRoot,
            ControlBuild.FileRef resourceCardRef, ControlBuild.FileRef toolsReceiptRef,
            ControlBuild.FileRef sourceManifestRef, ControlBuild.FileRef configuredGraphRef,
            ControlBuild.FileRef buildActualRef, ControlBuild.FileRef dependencyRef,
            ControlBuild.FileRef manifestRef, ControlBuild.FileRef reviewPlanRef,
            List<RegistrationExecutable> executables) {
        public PreparedRegistration { executables = List.copyOf(executables); }
    }
    /** RED may have no returned owner/result or file evidence; null never means a zero-child Job. */
    public record Actual(String schema, String machineId, String observedAtUtc, ActualStatus status, String stageId,
            String stageDeadlineAtUtc,
            List<String> command, String cwd, ControlBuild.FileRef environmentRef,
            ControlBuild.FileRef resourceCardRef, ControlBuild.FileRef toolsReceiptRef,
            ControlBuild.FileRef sourceManifestRef, ControlBuild.FileRef configuredGraphRef,
            List<ControlBuild.FileRef> toolRefs, List<ControlBuild.FileRef> linkedArtifactRefs,
            WindowsJobProcess.ProcessIdentity ownerIdentity, WindowsJobProcess.CommandResult result,
            NativeLifecycleTerminal.Assessment lifecycle, boolean sourceUnchanged,
            ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef,
            List<ControlBuild.FileRef> outputRefs, String error) {
        public Actual {
            command = List.copyOf(command); toolRefs = List.copyOf(toolRefs);
            linkedArtifactRefs = List.copyOf(linkedArtifactRefs); outputRefs = List.copyOf(outputRefs);
            if (!"xar.shared-native-stage-actual/v2".equals(schema) || !MACHINE.equals(machineId)
                    || status == null || stageId == null || stageId.isBlank()
                    || lifecycle == null || !lifecycle.equals(NativeLifecycleTerminal.assess(result))) {
                throw new IllegalArgumentException("exact current native actual and causal lifecycle assessment required");
            }
            Instant.parse(observedAtUtc); Instant.parse(stageDeadlineAtUtc);
            if (status == ActualStatus.PASS && (!lifecycle.successful() || error != null || !sourceUnchanged
                    || ownerIdentity == null || !ownerIdentity.equals(result.identity()))) {
                throw new IllegalArgumentException("PASS requires unchanged sources and a naturally settled matching owner");
            }
        }
    }
    private record Context(Config config, Instant deadline, ResourceCard card, ControlBuild.FileRef cardRef,
            ControlBuild.FileRef toolsReceiptRef, JsonNode plan, List<ControlBuild.FileRef> sourceRefs,
            List<ControlBuild.FileRef> toolRefs, List<ControlBuild.FileRef> runtimeRefs, Map<String, String> baseEnv) { }
    private enum DiagnosticInvocation { NOT_RETURNED, RETURNED }
    private record JobDiagnosticRecord(String schema, String machineId, String observedAtUtc,
            DiagnosticInvocation invocation, WindowsJobProcess.JobDiagnosticOutcome diagnostic) { }

    public static void run(Config config) throws IOException, InterruptedException {
        Context context = prepare(config);
        switch (config.stage()) {
            case ENV -> environment(context);
            case VERSIONS -> versions(context);
            case VENDOR_TIMEOUTS -> vendorTimeouts(context);
            case CONFIGURE -> configure(context);
            case GRAPH -> graph(context);
            case BUILD -> build(context);
            case REGISTER -> register(context);
            case KINSHIP -> kinship(context);
            case COMBAT -> combat(context);
        }
    }

    private static Context prepare(Config config) throws IOException {
        return prepare(config, null);
    }

    private static Context prepare(Config config, Instant reviewedRegistrationDeadline) throws IOException {
        require(MACHINE.equals(WindowsJobProcess.currentMachineId()), "actual native machine mismatch");
        ControlBuild.BuildReceipt tools = readCompletedToolsReceipt(config.toolsReceipt());
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, "qualified shared tools runtime required");
        ResourceCard card = JSON.readValue(bytes(config.resourceCard(), 262144), ResourceCard.class);
        require(card.allowedStage() == config.stage(), "resource card belongs to another native stage");
        card.releaseRef().verify(); card.partReallocationRef().verify(); card.toolsReceiptRef().verify();
        card.toolsAcceptedReadbackRef().verify(); card.packageRequestRef().verify(); card.sourceManifestRef().verify();
        verify(card.requiredPriorActualRefs());
        require(card.toolsReceiptRef().equals(ControlBuild.FileRef.measure(config.toolsReceipt()))
                && card.packageRequestRef().equals(ControlBuild.FileRef.measure(config.plan())), "native card exact package/tools binding mismatch");
        JsonNode release = read(Path.of(card.releaseRef().path()), 262144);
        Instant releaseDeadline = Instant.parse(card.reviewAtUtc());
        require(!releaseDeadline.isAfter(Instant.parse(text(release, "review_at_utc"))), "native card cannot extend release expiry");
        Instant stageDeadline = Instant.now().plusSeconds(card.timeoutSeconds());
        Instant deadline = stageDeadline.isBefore(releaseDeadline) ? stageDeadline : releaseDeadline;
        if (reviewedRegistrationDeadline != null) {
            require(config.stage() == Stage.REGISTER, "a reviewed registration deadline belongs only to REGISTER");
            deadline = deadline.isBefore(reviewedRegistrationDeadline) ? deadline : reviewedRegistrationDeadline;
            NativeProjectExeUac.requireSharedStageDeadline(reviewedRegistrationDeadline.toString(), deadline.toString());
        }
        require(MACHINE.equals(text(release, "machine_id")), "native release machine mismatch");
        for (String output : card.outputRoots()) {
            Path path = Path.of(output).toAbsolutePath().normalize();
            require(path.startsWith(BUILD) || path.startsWith(SCRATCH), "native stage output outside its two exact roots");
        }
        require(Instant.now().isBefore(deadline), "native slot expired");
        PlannedInputs inputs = plannedInputs(config.plan(), config.operationSource(), tools);
        JsonNode plan = inputs.plan();
        require(card.owner().equals(text(plan, "owner")), "native card owner differs from exact package");
        List<ControlBuild.FileRef> sources = inputs.sources(), pins = inputs.tools(), runtime = inputs.runtime();
        SourceManifest admission = JSON.readValue(bytes(Path.of(card.sourceManifestRef().path()), 2097152), SourceManifest.class);
        require(admission.schema().equals("xar.native-stage-source-manifest/v1") && MACHINE.equals(admission.machineId()), "native source admission manifest required");
        verify(admission.sourceRefs()); verify(admission.toolRefs()); verify(admission.operationRuntimeRefs());
        require(admission.sourceRefs().contains(ControlBuild.FileRef.measure(config.operationSource()))
                && admission.sourceRefs().contains(ControlBuild.FileRef.measure(config.plan())) && admission.sourceRefs().contains(ref(plan.get("source_union_ref")))
                && new HashSet<>(admission.operationRuntimeRefs()).equals(new HashSet<>(runtime)), "native admission does not bind this compiled operation and original source plan");
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        // Minimal bootstrap values only; vcvars output itself is explicitly allowlisted.
        for (String name : List.of("SystemRoot", "ComSpec", "PATH", "PATHEXT", "ProgramFiles", "ProgramFiles(x86)",
                "ProgramData", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS")) {
            String value = System.getenv(name); if (value != null) environment.put(name, value);
        }
        for (String name : List.of("TEMP", "TMP", "TMPDIR")) environment.put(name, SCRATCH.toString());
        environment.put("VSCMD_SKIP_SENDTELEMETRY", "1"); environment.put("PYTHONDONTWRITEBYTECODE", "1");
        return new Context(config, deadline, card, ControlBuild.FileRef.measure(config.resourceCard()),
                ControlBuild.FileRef.measure(config.toolsReceipt()), plan, List.copyOf(sources), List.copyOf(pins),
                List.copyOf(runtime), Map.copyOf(environment));
    }

    private record PlannedInputs(JsonNode plan, List<ControlBuild.FileRef> sources,
            List<ControlBuild.FileRef> tools, List<ControlBuild.FileRef> runtime) { }

    private static PlannedInputs plannedInputs(Path planPath, Path operationSource, ControlBuild.BuildReceipt tools) throws IOException {
        JsonNode plan = read(planPath, 65536);
        require("xar.prisoners-combatroles-shared-native-build-plan.v1".equals(text(plan, "schema"))
                && MACHINE.equals(text(plan, "machine_id"))
                && SOURCE.equals(Path.of(text(plan, "source_root")))
                && BUILD.equals(Path.of(text(plan, "build_root"))) && SCRATCH.equals(Path.of(text(plan, "scratch_root"))),
                "exact native source, fresh build and scratch plan roots required");
        List<ControlBuild.FileRef> sources = new ArrayList<>();
        ControlBuild.FileRef unionRef = ref(plan.get("source_union_ref")); unionRef.verify();
        JsonNode union = read(Path.of(unionRef.path()), 131072);
        require(array(union, "unresolved").isEmpty(), "unresolved original quoted include inputs");
        sources.addAll(refs(array(union, "source_refs"))); sources.addAll(refs(array(plan, "source_cmake_refs")));
        require(array(plan, "bootstrap_source_refs").isEmpty(), "shared environment capture cannot consume attempt source adapters");
        NativeBuildEnvironment.readConfiguration(plan.get("environment"), SCRATCH);
        sources.add(ControlBuild.FileRef.measure(planPath)); sources.add(unionRef);
        sources.add(ControlBuild.FileRef.measure(operationSource));
        sources.add(ControlBuild.FileRef.measure(REPO.resolve("tools/register_project_exe_exclusions.py")));
        sources.add(ControlBuild.FileRef.measure(REPO.resolve("tools/project_exe_exclusion_broker_client.py")));
        List<ControlBuild.FileRef> pins = refs(array(plan, "tool_refs"));
        require(pins.size() == 6, "six exact native tool pins required");
        pins.add(tools.javaExecutableRef());
        pins.add(ControlBuild.FileRef.measure(REPO.resolve("tools/.venv/Scripts/python.exe")));
        pins.add(ControlBuild.FileRef.measure(Path.of(System.getenv("SystemRoot")).resolve("System32/cmd.exe")));
        pins.add(vendorPin());
        List<ControlBuild.FileRef> runtime;
        try {
            Path location = Path.of(NativeFixtureBuild.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path environmentLocation = Path.of(NativeBuildEnvironment.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            runtime = environmentOperationRuntimeClosure(location, environmentLocation, ControlBuild.producerClosure(), tools.completeDeployment());
        } catch (java.net.URISyntaxException error) { throw new IOException("operation runtime URI", error); }
        verify(sources); verify(pins); verify(runtime);
        return new PlannedInputs(plan, List.copyOf(sources), List.copyOf(pins), List.copyOf(runtime));
    }

    public record EnvironmentPreparation(String schema, String machineId, String observedAtUtc,
            EnvironmentPreparationStatus status, ControlBuild.FileRef planRef, ControlBuild.FileRef toolsReceiptRef,
            ControlBuild.FileRef operationSourceRef, ControlBuild.FileRef admissionManifestRef,
            long environmentMemoryLimitBytes, long freshScratchLimitBytes) {
        public EnvironmentPreparation {
            if (!"xar.native-environment-preparation/v1".equals(schema) || !MACHINE.equals(machineId)
                    || status != EnvironmentPreparationStatus.PREPARED_NOT_AUTHORIZED || planRef == null || toolsReceiptRef == null
                    || operationSourceRef == null || admissionManifestRef == null || environmentMemoryLimitBytes != ENV_MEMORY
                    || freshScratchLimitBytes != ENV_SCRATCH_CAP) throw new IllegalArgumentException("exact metadata preparation only");
            Instant.parse(observedAtUtc);
        }
    }

    /** Produces complete source/runtime metadata for Root review; starts no command and grants no native stage. */
    public static EnvironmentPreparation prepareEnvironmentAdmission(Path planPath, Path toolsReceipt,
            Path operationSource, Path outputManifest) throws IOException {
        for (Path input : List.of(planPath, toolsReceipt, operationSource, outputManifest))
            require(input.isAbsolute(), "absolute environment preparation paths required");
        require(MACHINE.equals(WindowsJobProcess.currentMachineId()), "actual environment preparation machine mismatch");
        require(!Files.exists(BUILD, LinkOption.NOFOLLOW_LINKS) && !Files.exists(SCRATCH, LinkOption.NOFOLLOW_LINKS), "fresh native roots required");
        ControlBuild.BuildReceipt tools = readCompletedToolsReceipt(toolsReceipt);
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, "accepted shared tools required");
        PlannedInputs inputs = plannedInputs(planPath, operationSource, tools);
        SharedSourceFiles.plainAncestors(outputManifest);
        require(Files.isDirectory(outputManifest.getParent(), LinkOption.NOFOLLOW_LINKS), "existing admitted metadata output parent required");
        publish(outputManifest, new SourceManifest("xar.native-stage-source-manifest/v1", MACHINE, Instant.now().toString(),
                inputs.sources(), inputs.tools(), inputs.runtime()));
        return new EnvironmentPreparation("xar.native-environment-preparation/v1", MACHINE, Instant.now().toString(),
                EnvironmentPreparationStatus.PREPARED_NOT_AUTHORIZED, ControlBuild.FileRef.measure(planPath),
                ControlBuild.FileRef.measure(toolsReceipt), ControlBuild.FileRef.measure(operationSource),
                ControlBuild.FileRef.measure(outputManifest), ENV_MEMORY, ENV_SCRATCH_CAP);
    }

    /** Complete historical software evidence only; current execution still requires this stage's independent card. */
    public static ControlBuild.BuildReceipt readCompletedToolsReceipt(Path receiptPath) throws IOException {
        require(receiptPath != null && receiptPath.isAbsolute(), "absolute completed tools receipt required");
        ControlBuild.BuildReceipt tools = ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(receiptPath));
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, "completed shared build-tools runtime required");
        return tools;
    }

    private static void environment(Context context) throws IOException, InterruptedException {
        require(!Files.exists(BUILD) && !Files.exists(SCRATCH), "fresh native roots required");
        NativeBuildEnvironment.readConfiguration(context.plan().get("environment"), SCRATCH);
        List<Path> classPath = new ArrayList<>(ControlBuild.producerClosure().stream().map(pin -> Path.of(pin.path())).toList());
        try {
            Path location = Path.of(NativeBuildEnvironment.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            if (Files.isDirectory(location, LinkOption.NOFOLLOW_LINKS)) classPath.addFirst(location);
        } catch (java.net.URISyntaxException error) { throw new IOException("shared environment runtime URI", error); }
        List<String> arguments = NativeBuildEnvironment.bootstrapArguments(tool(context, "vcvars64.bat"),
                tool(context, "java.exe"), classPath, SCRATCH, MACHINE);
        // CONFIGURE creates BUILD after the environment and version stages have succeeded.
        Files.createDirectory(SCRATCH);
        manifest(context, "BASE-SOURCE-MANIFEST09.json", context.sourceRefs());
        command(context, "env-tool-probe", Path.of(System.getenv("SystemRoot")).resolve("System32/cmd.exe"),
                arguments, REPO, context.baseEnv(), 120, null, null,
                List.of(SCRATCH.resolve(NativeBuildEnvironment.SNAPSHOT_NAME)), List.of());
    }

    /** Both new producer and native caller must come from the same measured operation module. */
    public static List<ControlBuild.FileRef> environmentOperationRuntimeClosure(Path operationLocation, Path environmentLocation,
            List<ControlBuild.FileRef> runningDeployment, List<ControlBuild.FileRef> acceptedDeployment) throws IOException {
        require(operationLocation != null && operationLocation.isAbsolute() && environmentLocation != null && environmentLocation.isAbsolute(),
                "absolute native caller and environment producer locations required");
        require(operationLocation.toRealPath().equals(environmentLocation.toRealPath()),
                "shared environment producer is outside the measured native caller module");
        return operationRuntimeClosure(operationLocation, runningDeployment, acceptedDeployment);
    }

    /** The formal JAR is accepted only as the same already-qualified complete running deployment. */
    public static List<ControlBuild.FileRef> operationRuntimeClosure(Path operationLocation,
            List<ControlBuild.FileRef> runningDeployment, List<ControlBuild.FileRef> acceptedDeployment) throws IOException {
        require(operationLocation != null && operationLocation.isAbsolute() && runningDeployment != null
                && acceptedDeployment != null && runningDeployment.size() == 6 && acceptedDeployment.size() == 6,
                "exact operation location and complete six-piece deployments required");
        Set<ControlBuild.FileRef> running = new HashSet<>(runningDeployment), accepted = new HashSet<>(acceptedDeployment);
        require(running.size() == 6 && accepted.size() == 6 && running.equals(accepted),
                "running operation deployment differs from accepted tools receipt");
        verify(runningDeployment);
        Path location = operationLocation.toRealPath();
        List<ControlBuild.FileRef> runtime = new ArrayList<>(runningDeployment);
        if (Files.isRegularFile(location, LinkOption.NOFOLLOW_LINKS)) {
            require(location.getFileName().toString().endsWith(".jar")
                    && running.contains(ControlBuild.FileRef.measure(location)),
                    "operation JAR is outside the accepted exact running deployment");
        } else {
            require(Files.isDirectory(location, LinkOption.NOFOLLOW_LINKS), "finite operation class directory or accepted JAR required");
            try (var files = Files.walk(location)) {
                for (Path path : files.filter(p -> Files.isRegularFile(p, LinkOption.NOFOLLOW_LINKS)).toList()) {
                    String name = path.getFileName().toString();
                    require((name.startsWith("NativeFixtureBuild") || name.startsWith("NativeBuildEnvironment") || name.startsWith("NativeProjectExeUac")
                            || name.startsWith("NativeProjectExeRegistration") || name.startsWith("NativeLifecycleTerminal"))
                            && !name.contains("Regression") && path.toString().endsWith(".class"), "unrelated operation runtime class");
                    runtime.add(ControlBuild.FileRef.measure(path));
                }
            }
        }
        return sorted(runtime);
    }

    private static void versions(Context context) throws IOException, InterruptedException {
        accepted("env-tool-probe"); Map<String, String> env = nativeEnvironment();
        manifest(context, "BASE-SOURCE-MANIFEST09.json", context.sourceRefs());
        command(context, "version-cmake", tool(context, "cmake.exe"), List.of("--version"), SCRATCH, env, 120,
                environmentRef(), null, List.of(), List.of());
        command(context, "version-ninja", tool(context, "ninja.exe"), List.of("--version"), SCRATCH, env, 120,
                environmentRef(), null, List.of(), List.of());
        command(context, "version-cl-help", tool(context, "cl.exe"), List.of("/help"), SCRATCH, env, 120,
                environmentRef(), null, List.of(), List.of());
    }

    private static void vendorTimeouts(Context context) throws IOException, InterruptedException {
        accepted("version-cmake"); accepted("version-ninja"); accepted("version-cl-help");
        require(!Files.exists(BUILD, LinkOption.NOFOLLOW_LINKS), "vendor probes cannot populate a build root");
        Path cohortPath = SCRATCH.resolve("VENDOR-TIMEOUTS01.json");
        require(!Files.exists(cohortPath), "vendor observations are append-only");
        manifest(context, "BASE-SOURCE-MANIFEST09.json", context.sourceRefs());
        Map<String, String> env = nativeEnvironment();
        Actual first = command(context, ActualStage.VENDOR_TIMEOUT_ONE.wireId(), tool(context, "vctip.exe"),
                VctipProbeFacts.arguments(VctipProbeFacts.ProbeCase.IDLE_ONE), SCRATCH, env, 30, environmentRef(), null, List.of(), List.of());
        Actual second = command(context, ActualStage.VENDOR_TIMEOUT_TWO.wireId(), tool(context, "vctip.exe"),
                VctipProbeFacts.arguments(VctipProbeFacts.ProbeCase.IDLE_TWO), SCRATCH, env, 30, environmentRef(), null, List.of(), List.of());
        VendorTimeouts value = new VendorTimeouts("xar.native-vendor-timeouts/v1", MACHINE, Instant.now().toString(),
                VendorTimeoutStatus.NATURAL_CASES_OBSERVED_NOT_CONFIGURE_QUALIFIED, context.deadline().toString(), vendorPin(),
                first.sourceManifestRef(), first.toolsReceiptRef(), first.environmentRef(),
                ControlBuild.FileRef.measure(actualPath(first.stageId())), vendorAnalysis(first, VctipProbeFacts.ProbeCase.IDLE_ONE),
                ControlBuild.FileRef.measure(actualPath(second.stageId())), vendorAnalysis(second, VctipProbeFacts.ProbeCase.IDLE_TWO));
        guard(context); publish(cohortPath, value); readVendorTimeouts(cohortPath);
    }

    private static void configure(Context context) throws IOException, InterruptedException {
        accepted("version-cmake"); accepted("version-ninja"); accepted("version-cl-help");
        Path vendorPath = SCRATCH.resolve("VENDOR-TIMEOUTS01.json");
        VendorTimeouts vendor = readVendorTimeouts(vendorPath);
        List<ControlBuild.FileRef> vendorInputs = List.of(vendor.firstActualRef(), vendor.secondActualRef(), ControlBuild.FileRef.measure(vendorPath));
        require(context.card().requiredPriorActualRefs().containsAll(vendorInputs)
                && vendor.toolsReceiptRef().equals(context.toolsReceiptRef()) && vendor.environmentRef().equals(environmentRef())
                && vendor.sourceManifestRef().equals(ControlBuild.FileRef.measure(SCRATCH.resolve("BASE-SOURCE-MANIFEST09.json"))),
                "configure card must consume the exact prior vendor observations and unchanged inputs");
        require(!Files.exists(BUILD, LinkOption.NOFOLLOW_LINKS), "new Release configure root must be absent"); Files.createDirectory(BUILD);
        require(!Files.exists(BUILD.resolve("CMakeCache.txt")), "old native CMakeCache forbidden");
        Path query = BUILD.resolve(".cmake/api/v1/query"); Files.createDirectories(query);
        for (String name : List.of("codemodel-v2", "cmakeFiles-v1")) {
            Path path = query.resolve(name);
            if (Files.exists(path, LinkOption.NOFOLLOW_LINKS)) require(!Files.isSymbolicLink(path)
                    && Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && Files.size(path) == 0, "existing query must be the original empty regular file");
            else Files.createFile(path);
        }
        manifest(context, "BASE-SOURCE-MANIFEST09.json", context.sourceRefs());
        List<String> args = new ArrayList<>(List.of("-S", SOURCE.toString(), "-B", BUILD.toString(), "-G", "Ninja",
                "-DBUILD_TESTING=ON", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_TRY_COMPILE_CONFIGURATION=Release",
                "-DCMAKE_MAKE_PROGRAM=" + tool(context, "ninja.exe"), "-DCMAKE_CXX_COMPILER=" + tool(context, "cl.exe"),
                "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=" + BUILD.resolve("bin"),
                "-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY=" + BUILD.resolve("lib"),
                "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=" + BUILD.resolve("lib")));
        command(context, CONFIGURE_ID, tool(context, "cmake.exe"), args, SCRATCH, nativeEnvironment(), 180,
                environmentRef(), null, List.of(BUILD.resolve("CMakeCache.txt"), BUILD.resolve("ck3_12002_runtime_sources.txt")), vendorInputs);
    }

    private static void graph(Context context) throws IOException {
        Actual configured = accepted(CONFIGURE_ID);
        Path reply = BUILD.resolve(".cmake/api/v1/reply");
        List<Path> indexes;
        try (var files = Files.list(reply)) { indexes = files.filter(p -> p.getFileName().toString().startsWith("index-") && p.toString().endsWith(".json")).toList(); }
        require(indexes.size() == 1, "one fresh File API index required");
        Path indexPath = indexes.getFirst(); JsonNode index = read(indexPath, 1048576);
        JsonNode modelObject = uniqueKind(array(index, "objects"), "codemodel");
        Path modelPath = confined(reply, text(modelObject, "jsonFile")); JsonNode model = read(modelPath, 4194304);
        require(SOURCE.equals(Path.of(text(model.get("paths"), "source"))) && BUILD.equals(Path.of(text(model.get("paths"), "build"))), "configured source/build mismatch");
        ArrayNode configs = array(model, "configurations"); require(configs.size() == 1, "one Ninja configuration required");
        require("Release".equals(text(configs.get(0), "name")), "Release configuration required");
        Map<String, JsonNode> rows = new LinkedHashMap<>(); Map<String, String> names = new LinkedHashMap<>();
        for (JsonNode row : array(configs.get(0), "targets")) {
            require(rows.put(text(row, "id"), row) == null && names.put(text(row, "name"), text(row, "id")) == null, "duplicate configured target");
        }
        List<ControlBuild.FileRef> configuredInputs = new ArrayList<>(List.of(ControlBuild.FileRef.measure(indexPath),
                ControlBuild.FileRef.measure(modelPath), ControlBuild.FileRef.measure(BUILD.resolve("CMakeCache.txt")),
                ControlBuild.FileRef.measure(BUILD.resolve("build.ninja")), ControlBuild.FileRef.measure(BUILD.resolve("CMakeFiles/rules.ninja"))));
        List<Target> targets = new ArrayList<>(); Set<String> visited = new HashSet<>(); ArrayDeque<String> pending = new ArrayDeque<>();
        for (String target : TARGETS) { require(names.containsKey(target), "required target absent: " + target); pending.add(names.get(target)); }
        Map<Path, ControlBuild.FileRef> sourcePins = new LinkedHashMap<>();
        for (ControlBuild.FileRef pin : context.sourceRefs()) sourcePins.put(Path.of(pin.path()), pin);
        List<Path> quotedRoots = new ArrayList<>(); List<Path> search = new ArrayList<>(); search.add(SOURCE.resolve("include")); search.add(SOURCE.resolve("src"));
        while (!pending.isEmpty()) {
            String id = pending.remove(); if (!visited.add(id)) continue;
            require(visited.size() <= 8 && rows.containsKey(id), "unbounded or foreign target dependency");
            JsonNode row = rows.get(id); Path targetPath = confined(reply, text(row, "jsonFile")); JsonNode data = read(targetPath, 2097152);
            String name = text(data, "name"); require(id.equals(text(data, "id")) && Set.of(KINSHIP, COMBAT, RUNTIME).contains(name), "unexpected selected target closure");
            List<ControlBuild.FileRef> tus = new ArrayList<>();
            for (JsonNode source : array(data, "sources")) {
                if (!source.has("compileGroupIndex")) continue;
                long groupIndex = integer(source, "compileGroupIndex");
                require(data.has("compileGroups") && groupIndex < array(data, "compileGroups").size(), "actual source compile-group index out of range");
                Path path = resolveSource(text(source, "path"));
                require(path.startsWith(SOURCE) || path.startsWith(BUILD), "selected translation unit escapes source/build");
                ControlBuild.FileRef pin = ControlBuild.FileRef.measure(path); tus.add(pin); sourcePins.put(path, pin); quotedRoots.add(path);
            }
            List<String> dependencies = new ArrayList<>();
            if (data.has("dependencies")) for (JsonNode dep : array(data, "dependencies")) { String next = text(dep, "id"); dependencies.add(next); pending.add(next); }
            List<String> artifacts = new ArrayList<>();
            for (JsonNode artifact : array(data, "artifacts")) artifacts.add(confined(BUILD, text(artifact, "path")).toString());
            List<CompileGroup> groups = new ArrayList<>();
            if (data.has("compileGroups")) for (JsonNode group : array(data, "compileGroups")) {
                require("CXX".equals(text(group, "language")), "C++ compile group required");
                List<IncludeDirectory> includes = new ArrayList<>();
                if (group.has("includes")) for (JsonNode include : array(group, "includes")) {
                    String directory = text(include, "path"); search.add(Path.of(directory).toAbsolutePath().normalize());
                    includes.add(new IncludeDirectory(directory, include.has("isSystem") && bool(include, "isSystem")));
                }
                List<String> fragments = new ArrayList<>();
                if (group.has("compileCommandFragments")) for (JsonNode fragment : array(group, "compileCommandFragments")) fragments.add(text(fragment, "fragment"));
                List<String> definitions = new ArrayList<>();
                if (group.has("defines")) for (JsonNode define : array(group, "defines")) definitions.add(text(define, "define"));
                groups.add(new CompileGroup(text(group, "language"), group.has("languageStandard") ? text(group.get("languageStandard"), "standard") : null,
                        fragments, definitions, includes));
            }
            targets.add(new Target(name, id, TargetType.valueOf(text(data, "type")), ControlBuild.FileRef.measure(targetPath), tus,
                    artifacts, dependencies, groups, linkData(data.get("link")), linkData(data.get("archive"))));
            configuredInputs.add(ControlBuild.FileRef.measure(targetPath));
        }
        require(targets.size() == 3, "exact two executables plus runtime closure required");
        for (Target target : targets) {
            configuredPrimaryArtifact(BUILD, target.name(), target.type(), target.artifacts());
        }
        JsonNode cmakeObject = uniqueKind(array(index, "objects"), "cmakeFiles");
        Path cmakePath = confined(reply, text(cmakeObject, "jsonFile")); configuredInputs.add(ControlBuild.FileRef.measure(cmakePath));
        for (JsonNode input : array(read(cmakePath, 2097152), "inputs")) {
            Path path = resolveSource(text(input, "path"));
            require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS), "missing configured CMake input: " + path);
            configuredInputs.add(ControlBuild.FileRef.measure(path));
        }
        collectQuoted(quotedRoots, search, sourcePins);
        Target runtime = targets.stream().filter(t -> t.name().equals(RUNTIME)).findFirst().orElseThrow();
        Path runtimeFile = BUILD.resolve("ck3_12002_runtime_sources.txt");
        Set<Path> listed = new HashSet<>();
        for (String line : Files.readAllLines(runtimeFile, StandardCharsets.UTF_8)) if (!line.isBlank()) listed.add(resolveSource(line.strip()));
        require(listed.equals(new HashSet<>(runtime.translationUnits().stream().map(r -> Path.of(r.path())).toList())), "generated runtime sources differ from actual target compile sources");
        List<ControlBuild.FileRef> project = sorted(sourcePins.values().stream().toList()); verify(project); verify(configuredInputs);
        List<ControlBuild.FileRef> configuredTools = configuredTools(context);
        Graph graph = new Graph("xar.native-configured-selected-graph/v1", MACHINE, Instant.now().toString(), GraphStatus.CONFIGURED_SOURCE_FROZEN_NOT_BUILT,
                ControlBuild.FileRef.measure(actualPath(CONFIGURE_ID)), targets, configuredInputs, configuredTools, project,
                ControlBuild.FileRef.measure(runtimeFile), runtime.translationUnits().size(), List.of(
                "File API compileGroups and selected translation units are actual configured inputs.",
                "Project quoted include closure is frozen before build; compiler-active dependency paths come from fresh Ninja deps after build.",
                "System headers are post-build actual dependency pins, not claimed as pre-build byte-frozen inputs."));
        publish(SCRATCH.resolve("CONFIGURED-GRAPH01.json"), graph);
        manifest(context, "CONFIGURED-SOURCE-MANIFEST01.json", project);
        guard(context);
        require(configured.result().passed(), "configure terminal changed");
        System.out.println("CONFIGURED exact_runtime_translation_units=" + runtime.translationUnits().size());
    }

    private static void build(Context context) throws IOException, InterruptedException {
        Graph graph = acceptedGraph(); verify(graph.projectSourceRefs()); verify(graph.configuredInputRefs()); verify(graph.configuredToolRefs());
        ControlBuild.FileRef graphRef = ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-GRAPH01.json"));
        Map<String, String> env = nativeEnvironment();
        command(context, "configured-commands", tool(context, "ninja.exe"), List.of("-C", BUILD.toString(), "-t", "commands", KINSHIP, COMBAT),
                SCRATCH, env, 120, environmentRef(), graphRef, List.of(), List.of());
        List<Path> artifacts = List.of(BUILD.resolve("lib/" + RUNTIME + ".lib"), BUILD.resolve("bin/" + KINSHIP + ".exe"), BUILD.resolve("bin/" + COMBAT + ".exe"), BUILD.resolve(".ninja_log"));
        command(context, "two-target-build", tool(context, "cmake.exe"), List.of("--build", BUILD.toString(), "--target", KINSHIP, COMBAT, "--parallel", "1", "--verbose"),
                SCRATCH, env, 1800, environmentRef(), graphRef, artifacts, List.of());
        command(context, "compiler-active-dependencies", tool(context, "ninja.exe"), List.of("-C", BUILD.toString(), "-t", "deps"),
                SCRATCH, env, 120, environmentRef(), graphRef, List.of(BUILD.resolve(".ninja_deps")), artifactRefs());
        dependencyManifest(graph);
    }

    /** Pure preparation; no process, UAC, settings write or successful registration is claimed. */
    public static PreparedRegistration prepareRegistration(Config config) throws IOException {
        require(config != null && config.stage() == Stage.REGISTER, "REGISTER240 card required for exact preparation");
        Context context = prepare(config); guard(context);
        Path path = SCRATCH.resolve("DEFENDER-SELECTED-TWO-MANIFEST01.json");
        publish(path, registrationManifest(context));
        List<RegistrationExecutable> executables = new ArrayList<>();
        for (String name : TARGETS.stream().sorted().toList()) executables.add(new RegistrationExecutable(name,
                ControlBuild.FileRef.measure(BUILD.resolve("bin/" + name + ".exe"))));
        List<ControlBuild.FileRef> closure = new ArrayList<>(context.sourceRefs());
        closure.addAll(context.toolRefs()); closure.addAll(context.runtimeRefs());
        NativeProjectExeUac.Plan plan = new NativeProjectExeUac.Plan("xar.exact-two-exe-uac-plan/v2", MACHINE,
                Instant.now().toString(), context.deadline().toString(), "/root/native_fixture09", 190,
                new NativeProjectExeUac.NativeBuildRoot(BUILD.toString()), context.cardRef(), ControlBuild.FileRef.measure(path),
                ControlBuild.FileRef.measure(actualPath("two-target-build")),
                ControlBuild.FileRef.measure(SCRATCH.resolve("ACTUAL-COMPILER-DEPENDENCIES01.json")),
                ControlBuild.FileRef.measure(REPO.resolve("tools/.venv/Scripts/python.exe")),
                ControlBuild.FileRef.measure(REPO.resolve("tools/register_project_exe_exclusions.py")),
                sorted(closure.stream().distinct().toList()), executables.stream()
                        .map(item -> new NativeProjectExeUac.SelectedExecutable(item.target(), item.fileRef())).toList(),
                SCRATCH.toString(), SCRATCH.resolve("DEFENDER-SELECTED-TWO-ACTUAL01.json").toString(),
                SCRATCH.resolve("DEFENDER-REGISTRATION-INTENT01.json").toString(),
                SCRATCH.resolve("DEFENDER-REGISTRATION-LAUNCH01.json").toString(),
                SCRATCH.resolve("DEFENDER-REGISTRATION-RESULT01.json").toString());
        Path reviewPlan = SCRATCH.resolve("DEFENDER-REGISTRATION-PLAN01.json");
        publish(reviewPlan, plan);
        NativeProjectExeUac.Review review = NativeProjectExeUac.review(reviewPlan);
        publish(SCRATCH.resolve("DEFENDER-REGISTRATION-REVIEW01.json"), review);
        PreparedRegistration prepared = new PreparedRegistration("xar.native-prepared-registration/v1", MACHINE,
                Instant.now().toString(), context.deadline().toString(), "/root/native_fixture09",
                RegistrationPreparationStatus.PREPARED_NOT_SUBMITTED, BUILD.toString(), context.cardRef(), context.toolsReceiptRef(),
                ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-SOURCE-MANIFEST01.json")),
                ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-GRAPH01.json")),
                ControlBuild.FileRef.measure(actualPath("two-target-build")),
                ControlBuild.FileRef.measure(SCRATCH.resolve("ACTUAL-COMPILER-DEPENDENCIES01.json")),
                ControlBuild.FileRef.measure(path), ControlBuild.FileRef.measure(reviewPlan), executables);
        verify(context.sourceRefs()); verify(context.toolRefs()); verify(context.runtimeRefs()); guard(context);
        publish(SCRATCH.resolve("DEFENDER-REGISTRATION-PREPARED01.json"), prepared);
        return prepared;
    }

    public static void executeRegistration(RegistrationExecution execution) throws IOException, InterruptedException {
        ControlBuild.FileRef planRef = ControlBuild.FileRef.measure(execution.reviewedPlan());
        require(planRef.sha256().equals(execution.reviewedPlanSha256()), "Root-reviewed registration plan bytes drifted");
        NativeProjectExeUac.Plan plan = NativeProjectExeUac.parsePlan(bytes(execution.reviewedPlan(), 2097152));
        Context context = prepare(execution.config(), Instant.parse(plan.deadlineAtUtc()));
        PreparedRegistration prepared = JSON.readValue(bytes(SCRATCH.resolve("DEFENDER-REGISTRATION-PREPARED01.json"), 2097152), PreparedRegistration.class);
        require(prepared.reviewPlanRef().equals(planRef) && prepared.resourceCardRef().equals(context.cardRef())
                && prepared.deadlineAtUtc().equals(context.deadline().toString()), "execute must consume the original prepared plan, card and deadline");
        NativeProjectExeUac.requireSharedStageDeadline(plan.deadlineAtUtc(), context.deadline().toString());
        require(plan.owner().equals("/root/native_fixture09") && Path.of(plan.nativeBuildRoot().path()).equals(BUILD)
                && Path.of(plan.outputRoot()).equals(SCRATCH), "registration plan changed exact owner/build/scratch");
        NativeProjectExeUac.review(execution.reviewedPlan());
        List<String> arguments = new ArrayList<>(List.of("-Xms16m", "-Xmx128m", "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=2",
                "-Dfile.encoding=UTF-8", "-Djava.io.tmpdir=" + WORK.resolve("scratch"), "-Djna.tmpdir=" + WORK.resolve("scratch"),
                "-cp", registrationClassPath(context), NativeProjectExeUac.class.getName(), "execute-approved-plan",
                execution.reviewedPlan().toString(), execution.reviewedPlanSha256(), context.deadline().toString()));
        List<ControlBuild.FileRef> linked = new ArrayList<>(artifactRefs()); linked.add(planRef); linked.add(prepared.manifestRef());
        linked.add(prepared.buildActualRef()); linked.add(prepared.dependencyRef());
        linked.add(ControlBuild.FileRef.measure(SCRATCH.resolve("DEFENDER-REGISTRATION-PREPARED01.json")));
        ControlBuild.FileRef javaExecutable = readCompletedToolsReceipt(context.config().toolsReceipt()).javaExecutableRef();
        javaExecutable.verify();
        command(context, "defender-register-two", Path.of(javaExecutable.path()),
                arguments, SCRATCH, context.baseEnv(), 240, environmentRef(),
                ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-GRAPH01.json")),
                List.of(Path.of(plan.helperReceiptPath()), Path.of(plan.intentPath()), Path.of(plan.launchObservationPath()), Path.of(plan.resultPath())), sorted(linked));
    }

    private static String registrationClassPath(Context context) throws IOException {
        try {
            Path classes = Path.of(NativeFixtureBuild.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            List<String> entries = new ArrayList<>(); entries.add(classes.toString());
            for (ControlBuild.FileRef ref : ControlBuild.producerClosure()) { ref.verify(); entries.add(ref.path()); }
            verify(context.runtimeRefs()); return String.join(java.io.File.pathSeparator, entries);
        } catch (java.net.URISyntaxException failure) { throw new IOException("registration classpath URI", failure); }
    }

    private static ObjectNode registrationManifest(Context context) throws IOException {
        accepted("two-target-build"); acceptedCompilerDependencies(); Graph graph = acceptedGraph();
        verify(graph.projectSourceRefs()); verify(graph.configuredInputRefs());
        ObjectNode root = JSON.createObjectNode(); root.put("schema", "xar.project-exe-exclusions.v1"); root.put("repo", REPO.toRealPath().toString());
        root.put("source_dir", SOURCE.toRealPath().toString()); root.put("build_dir", BUILD.toRealPath().toString()); root.put("configuration", "Release");
        root.set("requested_targets", JSON.valueToTree(TARGETS)); root.putNull("external_candidate");
        ControlBuild.FileRef index = graph.configuredInputRefs().stream().filter(r -> Path.of(r.path()).getFileName().toString().startsWith("index-")).findFirst().orElseThrow();
        ControlBuild.FileRef model = graph.configuredInputRefs().stream().filter(r -> Path.of(r.path()).getFileName().toString().startsWith("codemodel-")).findFirst().orElseThrow();
        root.set("cmake_index", shortRef(index)); root.set("cmake_codemodel", shortRef(model));
        ArrayNode provenance = root.putArray("target_provenance"); ArrayNode files = root.putArray("files");
        // The original collector uses a LIFO walk seeded in requested_targets order.
        for (String name : List.of(COMBAT, KINSHIP)) {
            Target target = graph.targets().stream().filter(t -> t.name().equals(name)).findFirst().orElseThrow();
            ObjectNode row = provenance.addObject(); row.put("path", target.definitionRef().path()); row.put("sha256", target.definitionRef().sha256());
            row.put("target", name); row.put("target_id", target.id()); row.put("source", SOURCE.toRealPath().toString());
        }
        for (String name : TARGETS.stream().sorted().toList()) {
            Target target = graph.targets().stream().filter(t -> t.name().equals(name)).findFirst().orElseThrow();
            ControlBuild.FileRef pin = ControlBuild.FileRef.measure(configuredPrimaryArtifact(BUILD, target.name(), target.type(), target.artifacts()).toRealPath());
            ObjectNode row = files.addObject(); row.put("path", pin.path()); row.put("size", pin.bytes()); row.put("sha256", pin.sha256()); row.put("target", name); row.put("target_id", target.id());
        }
        guard(context); return root;
    }

    private static void register(Context context) throws IOException, InterruptedException {
        throw new IOException("REGISTER execution is unavailable until the qualified reviewed Java caller is bound; pure prepare-registration remains separate");
    }

    private static void kinship(Context context) throws IOException, InterruptedException {
        acceptedCompilerDependencies(); acceptedDefender(); accepted("defender-register-two"); Path out = SCRATCH.resolve("kinship-whole6");
        require(!Files.exists(out), "fresh six-case native output required");
        command(context, "kinship-producer", BUILD.resolve("bin/" + KINSHIP + ".exe"), List.of(out.toString()), SCRATCH,
                nativeEnvironment(), 120, environmentRef(), ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-GRAPH01.json")),
                CASES.stream().map(name -> out.resolve(name + ".json")).toList(), artifactRefs());
    }

    private static void combat(Context context) throws IOException, InterruptedException {
        acceptedCompilerDependencies(); acceptedDefender(); accepted("kinship-producer"); Path out = SCRATCH.resolve("combat-whole14");
        require(!Files.exists(out), "fresh fourteen-scene native output required");
        Path raw = out.resolve("ck3_12003_army_combat_roles_phase_rule24_pins_wire.json");
        command(context, "combatroles-producer", BUILD.resolve("bin/" + COMBAT + ".exe"), List.of("--wire-dir", out.toString()), SCRATCH,
                nativeEnvironment(), 120, environmentRef(), ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-GRAPH01.json")),
                List.of(raw), artifactRefs());
    }

    private static Actual command(Context context, String id, Path executable, List<String> args, Path cwd,
            Map<String, String> env, int timeout, ControlBuild.FileRef environment, ControlBuild.FileRef graph,
            List<Path> outputs, List<ControlBuild.FileRef> linked) throws IOException, InterruptedException {
        require(!Files.exists(actualPath(id)), "stage actual is append-only; no unknown replay");
        Path stdout = SCRATCH.resolve(id + ".stdout.log"), stderr = SCRATCH.resolve(id + ".stderr.log");
        Path diagnosticPath = id.equals(CONFIGURE_ID) ? SCRATCH.resolve(id + ".job-members.json") : null;
        WindowsJobProcess.JobDiagnosticOutcome diagnostic = null;
        List<Path> expectedOutputs = new ArrayList<>(outputs);
        Graph selected = null; WindowsJobProcess.CommandResult result = null;
        WindowsJobProcess.ProcessIdentity ownerIdentity = null; String error = null;
        try {
            guard(context); verify(context.sourceRefs()); verify(context.toolRefs()); verify(context.runtimeRefs()); verify(linked);
            selected = graph == null ? null : acceptedGraph();
            if (selected != null) { verify(selected.projectSourceRefs()); verify(selected.configuredInputRefs()); verify(selected.configuredToolRefs()); }
            WindowsJobProcess.ConsoleMode mode = id.equals(CONFIGURE_ID) || id.equals("two-target-build")
                    ? WindowsJobProcess.ConsoleMode.DETACHED : WindowsJobProcess.ConsoleMode.NO_WINDOW;
            try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(executable, args, cwd, env, stdout, stderr, context.card().memoryLimitBytes()), mode)) {
                ownerIdentity = child.identity();
                Runnable periodic = () -> {
                    try { guard(context); logBudget(); }
                    catch (IOException failure) { throw new IllegalStateException(failure.getMessage(), failure); }
                };
                if (id.equals(CONFIGURE_ID) || id.equals("two-target-build")) {
                    WindowsJobProcess.AwaitResult awaited = child.await(Duration.ofSeconds(timeout), context.deadline(), periodic, diagnosticPath,
                            WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE);
                    result = awaited.commandResult(); diagnostic = awaited.diagnostic();
                } else result = child.await(Duration.ofSeconds(timeout), context.deadline(), periodic);
            }
        } catch (IOException | RuntimeException | InterruptedException failure) {
            if (failure instanceof InterruptedException) Thread.currentThread().interrupt();
            error = failure.getClass().getName() + ": " + failure.getMessage();
        }
        boolean unchanged = false; List<ControlBuild.FileRef> outputRefs = new ArrayList<>();
        if (diagnosticPath != null) {
            try {
                Path outcome = SCRATCH.resolve(id + ".job-diagnostic-outcome.json");
                publish(outcome, new JobDiagnosticRecord("xar.native-stage-job-diagnostic-outcome/v1", MACHINE, Instant.now().toString(),
                        diagnostic == null ? DiagnosticInvocation.NOT_RETURNED : DiagnosticInvocation.RETURNED, diagnostic));
                expectedOutputs.add(outcome);
                if (diagnostic != null && diagnostic.state() == WindowsJobProcess.DiagnosticWriteState.WRITTEN) {
                    ControlBuild.FileRef pin = diagnostic.sidecarRef();
                    require(pin != null && Path.of(pin.path()).equals(diagnosticPath) && pin.bytes() <= 65536, "bounded exact owned Job diagnostic sidecar required");
                    pin.verify(); expectedOutputs.add(diagnosticPath);
                }
            } catch (IOException | RuntimeException failure) {
                String detail = "diagnostic persistence: " + failure.getClass().getName() + ": " + failure.getMessage();
                error = error == null ? detail : error + "; " + detail;
            }
        }
        try {
            verify(context.sourceRefs()); verify(context.toolRefs()); verify(context.runtimeRefs()); verify(linked);
            if (selected != null) { verify(selected.projectSourceRefs()); verify(selected.configuredInputRefs()); verify(selected.configuredToolRefs()); }
            unchanged = true; guard(context);
            for (Path path : expectedOutputs) {
                ControlBuild.FileRef pin = measureIfPresent(path); if (pin != null) outputRefs.add(pin);
            }
            require(NativeLifecycleTerminal.assess(result).successful(), "actual naturally settled successful child terminal unavailable or failed");
            logBudget();
            require(outputRefs.size() == expectedOutputs.size(), "successful stage omitted required output evidence");
            validateOutput(id, stdout, context, result);
        } catch (IOException | RuntimeException failure) {
            String detail = failure.getClass().getName() + ": " + failure.getMessage();
            error = error == null ? detail : error + "; postcheck: " + detail;
        }
        List<String> argv = new ArrayList<>(); argv.add(executable.toString()); argv.addAll(args);
        Path manifest = SCRATCH.resolve(graph == null ? "BASE-SOURCE-MANIFEST09.json" : "CONFIGURED-SOURCE-MANIFEST01.json");
        List<ControlBuild.FileRef> actualTools = mergeToolRefs(context.toolRefs(), selected == null ? List.of() : selected.configuredToolRefs());
        ControlBuild.FileRef manifestRef = measureIfPresent(manifest), stdoutRef = measureIfPresent(stdout), stderrRef = measureIfPresent(stderr);
        if (manifestRef == null || stdoutRef == null || stderrRef == null) error = error == null
                ? "required metadata evidence unavailable" : error + "; required metadata evidence unavailable";
        Actual actual = new Actual("xar.shared-native-stage-actual/v2", MACHINE, Instant.now().toString(), error == null ? ActualStatus.PASS : ActualStatus.RED, id,
                context.deadline().toString(), argv, cwd.toString(), environment, context.cardRef(), context.toolsReceiptRef(), manifestRef, graph,
                sorted(actualTools), linked, ownerIdentity, result, NativeLifecycleTerminal.assess(result), unchanged, stdoutRef, stderrRef, outputRefs, error);
        publish(actualPath(id), actual);
        System.out.println(id + " " + actual.status() + (result == null ? " terminal=unavailable" : " exit=" + result.exitCode() + " Jobactive=" + result.accounting().activeProcesses()));
        require(error == null, "native stage RED retained: " + error); return actual;
    }

    private static void manifest(Context context, String name, List<ControlBuild.FileRef> refs) throws IOException {
        List<ControlBuild.FileRef> tools = mergeToolRefs(context.toolRefs(),
                name.equals("CONFIGURED-SOURCE-MANIFEST01.json") ? acceptedGraph().configuredToolRefs() : List.of());
        Path target = SCRATCH.resolve(name);
        SourceManifest current = new SourceManifest("xar.native-stage-source-manifest/v1", MACHINE, Instant.now().toString(),
                sorted(refs), sorted(tools), context.runtimeRefs());
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) {
            SourceManifest original = JSON.readValue(bytes(target, 2097152), SourceManifest.class);
            require(original.schema().equals(current.schema()) && original.machineId().equals(current.machineId())
                    && original.sourceRefs().equals(current.sourceRefs()) && original.toolRefs().equals(current.toolRefs())
                    && original.operationRuntimeRefs().equals(current.operationRuntimeRefs()), "immutable stage source manifest drifted");
            verify(original.sourceRefs()); verify(original.toolRefs()); verify(original.operationRuntimeRefs());
        } else publish(target, current);
    }
    private static void validateOutput(String id, Path stdout, Context context, WindowsJobProcess.CommandResult result) throws IOException {
        if (id.equals(ActualStage.VENDOR_TIMEOUT_ONE.wireId()) || id.equals(ActualStage.VENDOR_TIMEOUT_TWO.wireId())) {
            VctipProbeFacts.ProbeCase probe = id.equals(ActualStage.VENDOR_TIMEOUT_ONE.wireId()) ? VctipProbeFacts.ProbeCase.IDLE_ONE : VctipProbeFacts.ProbeCase.IDLE_TWO;
            require(VctipProbeFacts.analyze(probe, result, bytes(stdout, 65536), bytes(SCRATCH.resolve(id + ".stderr.log"), 65536))
                    .observation() == VctipProbeFacts.Observation.NATURAL_ZERO_EXIT_OBSERVED, "vendor idle timeout observation failed");
        }
        if (id.equals("env-tool-probe")) nativeEnvironment();
        if (id.equals("kinship-producer")) {
            String actual = Files.readString(stdout, StandardCharsets.UTF_8);
            for (String name : CASES) {
                require(Files.size(SCRATCH.resolve("kinship-whole6/" + name + ".json")) <= 131072, "raw kinship output cap exceeded");
                require(actual.contains("FIRST kinship " + name + " whole_collection=4"), "real kinship scenario incomplete");
            }
            require(actual.contains("FIRST kinship groups=3 cases=6 complete"), "six kinship scenarios incomplete");
        }
        if (id.equals("combatroles-producer")) {
            JsonNode wire = read(SCRATCH.resolve("combat-whole14/ck3_12003_army_combat_roles_phase_rule24_pins_wire.json"), 16777216);
            JsonNode samples = wire.get("samples"); require(samples != null && samples.isObject() && samples.size() == 14, "whole combat fourteen samples required");
        }
        if (id.equals("defender-register-two")) acceptedDefender(context.deadline().toString());
    }
    /** File API declares an optional same-name PDB even for Release; only the main artifact is required. */
    public static Path configuredPrimaryArtifact(Path buildRoot, String name, TargetType type, List<String> artifacts) throws IOException {
        require(buildRoot != null && buildRoot.isAbsolute() && name != null && type != null && artifacts != null,
                "typed configured artifact inputs required");
        boolean runtime = name.equals(RUNTIME);
        require(runtime || TARGETS.contains(name), "foreign configured target");
        require(type == (runtime ? TargetType.STATIC_LIBRARY : TargetType.EXECUTABLE), "configured target type mismatch");
        Path primary = buildRoot.resolve((runtime ? "lib/" : "bin/") + name + (runtime ? ".lib" : ".exe")).normalize();
        Set<Path> allowed = new HashSet<>(); allowed.add(primary);
        if (!runtime) allowed.add(buildRoot.resolve("bin/" + name + ".pdb").normalize());
        Set<Path> actual = new HashSet<>();
        for (String artifact : artifacts) {
            require(artifact != null && !artifact.isBlank(), "configured artifact path missing");
            Path path = Path.of(artifact); require(path.isAbsolute(), "absolute configured artifact required");
            require(actual.add(path.normalize()), "duplicate configured artifact");
        }
        require(actual.contains(primary) && allowed.containsAll(actual), "exact primary and optional same-name PDB declaration required");
        return primary;
    }
    private static LinkData linkData(JsonNode row) throws IOException {
        if (row == null) return null;
        require(row.isObject(), "typed File API link/archive object required"); List<CommandFragment> fragments = new ArrayList<>();
        if (row.has("commandFragments")) for (JsonNode fragment : array(row, "commandFragments")) fragments.add(new CommandFragment(text(fragment, "fragment"), fragment.has("role") ? text(fragment, "role") : null));
        return new LinkData(row.has("language") ? text(row, "language") : null, row.has("lto") ? bool(row, "lto") : null, fragments);
    }
    /** Strict typed PASS/causal decoding only; this does not verify any referenced file or grant execution. */
    public static Actual parseActual(byte[] raw, ActualStage expectedStage) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= 1048576 && expectedStage != null,
                "bounded native actual and exact expected command stage required");
        Actual value = JSON.readValue(raw, Actual.class);
        require(value != null && value.schema().equals("xar.shared-native-stage-actual/v2") && value.machineId().equals(MACHINE)
                && value.stageId().equals(expectedStage.wireId()) && value.status() == ActualStatus.PASS && value.error() == null && value.sourceUnchanged()
                && value.result() != null && value.lifecycle().equals(NativeLifecycleTerminal.assess(value.result()))
                && value.lifecycle().successful() && value.ownerIdentity() != null
                && value.ownerIdentity().equals(value.result().identity()) && value.stdoutRef() != null && value.stderrRef() != null
                && value.sourceManifestRef() != null && value.resourceCardRef() != null && value.toolsReceiptRef() != null
                && !value.command().isEmpty() && value.cwd() != null && !value.toolRefs().isEmpty()
                && value.result().identity().executable() != null,
                "native actual lacks a complete naturally successful matching stage terminal");
        WindowsJobProcess.Accounting accounting = value.result().accounting();
        require(accounting.memoryLimitBytes() >= (16L << 20) && accounting.peakJobMemoryBytes() >= 0
                && accounting.peakJobMemoryBytes() <= accounting.memoryLimitBytes() && accounting.limitFlags() == 8704,
                "native actual memory/Job enforcement evidence is incomplete");
        require(!expectedStage.environmentRequired || value.environmentRef() != null, "stage environment reference required");
        require(!expectedStage.graphRequired || value.configuredGraphRef() != null, "stage configured graph reference required");
        try {
            Path executable = Path.of(value.command().getFirst()), ownerExecutable = Path.of(value.result().identity().executable());
            require(executable.isAbsolute() && ownerExecutable.isAbsolute() && Path.of(value.cwd()).isAbsolute()
                    && executable.normalize().equals(ownerExecutable.normalize()), "command and actual owner executable differ");
        } catch (java.nio.file.InvalidPathException invalid) { throw new IOException("invalid native actual path", invalid); }
        return value;
    }

    /** Historical terminal plus every source/tool/runtime and direct evidence file; no present-stage authority is granted. */
    public static Actual readActual(Path path, ActualStage expectedStage) throws IOException {
        require(path != null && path.isAbsolute(), "absolute original native actual path required");
        Actual value = parseActual(bytes(path, 1048576), expectedStage);
        value.resourceCardRef().verify(); value.toolsReceiptRef().verify();
        value.sourceManifestRef().verify(); value.stdoutRef().verify(); value.stderrRef().verify();
        if (value.environmentRef() != null) value.environmentRef().verify();
        if (value.configuredGraphRef() != null) value.configuredGraphRef().verify();
        verifyUniqueRefs(value.toolRefs()); verifyUniqueRefs(value.outputRefs()); verifyUniqueRefs(value.linkedArtifactRefs());
        SourceManifest manifest = JSON.readValue(bytes(Path.of(value.sourceManifestRef().path()), 2097152), SourceManifest.class);
        require(manifest != null && "xar.native-stage-source-manifest/v1".equals(manifest.schema()) && MACHINE.equals(manifest.machineId())
                && !manifest.sourceRefs().isEmpty() && !manifest.toolRefs().isEmpty() && !manifest.operationRuntimeRefs().isEmpty()
                && new HashSet<>(manifest.toolRefs()).equals(new HashSet<>(value.toolRefs())), "complete original stage source/tool manifest required");
        try { Instant.parse(manifest.observedAtUtc()); }
        catch (java.time.DateTimeException | NullPointerException invalid) { throw new IOException("invalid original stage source manifest observation", invalid); }
        verifyUniqueRefs(manifest.sourceRefs()); verifyUniqueRefs(manifest.toolRefs()); verifyUniqueRefs(manifest.operationRuntimeRefs());
        return value;
    }

    /** One file can serve both bootstrap and configured-tool roles; conflicting evidence is never merged. */
    static List<ControlBuild.FileRef> mergeToolRefs(List<ControlBuild.FileRef> base, List<ControlBuild.FileRef> configured) throws IOException {
        Map<String, ControlBuild.FileRef> merged = new TreeMap<>();
        for (List<ControlBuild.FileRef> role : List.of(base, configured)) for (ControlBuild.FileRef pin : role) {
            Path path = Path.of(pin.path());
            require(path.isAbsolute(), "absolute tool file required");
            String key = path.normalize().toString().toLowerCase(java.util.Locale.ROOT);
            ControlBuild.FileRef previous = merged.putIfAbsent(key, pin);
            require(previous == null || previous.bytes() == pin.bytes() && previous.sha256().equals(pin.sha256()),
                    "conflicting tool evidence for one canonical path");
        }
        return List.copyOf(merged.values());
    }

    private static ControlBuild.FileRef vendorPin() throws IOException {
        ControlBuild.FileRef pin = ControlBuild.FileRef.measure(Path.of(VctipProbeFacts.VENDOR.path()));
        require(pin.bytes() == VctipProbeFacts.VENDOR.bytes() && pin.sha256().equals(VctipProbeFacts.VENDOR.sha256()), "pinned vendor executable drifted");
        return pin;
    }

    private static VctipProbeFacts.Analysis vendorAnalysis(Actual actual, VctipProbeFacts.ProbeCase probe) throws IOException {
        require(probe == VctipProbeFacts.ProbeCase.IDLE_ONE || probe == VctipProbeFacts.ProbeCase.IDLE_TWO, "only declared idle cases allowed");
        ControlBuild.FileRef pin = vendorPin();
        require(actual.command().size() == 2 && Path.of(actual.command().getFirst()).normalize().equals(Path.of(pin.path()).normalize())
                && actual.command().get(1).equals(VctipProbeFacts.arguments(probe).getFirst()) && actual.toolRefs().contains(pin), "exact pinned vendor arguments and tool role required");
        VctipProbeFacts.Analysis value = VctipProbeFacts.analyze(probe, actual.result(),
                bytes(Path.of(actual.stdoutRef().path()), 65536), bytes(Path.of(actual.stderrRef().path()), 65536));
        require(value.observation() == VctipProbeFacts.Observation.NATURAL_ZERO_EXIT_OBSERVED
                && value.qualification() == VctipProbeFacts.Qualification.NONE && actual.result().elapsedSeconds() < 30,
                "vendor observation cannot qualify a compiler or cleaned Job");
        return value;
    }

    /** Historical file-bound vendor observations, without granting present-stage or configure authority. */
    public static VendorTimeouts readVendorTimeouts(Path path) throws IOException {
        require(path != null && path.isAbsolute(), "absolute vendor observation path required");
        VendorTimeouts value = JSON.readValue(bytes(path, 262144), VendorTimeouts.class);
        require(value != null, "typed vendor observations required");
        for (ControlBuild.FileRef pin : List.of(value.vendorRef(), value.sourceManifestRef(), value.toolsReceiptRef(),
                value.environmentRef(), value.firstActualRef(), value.secondActualRef())) pin.verify();
        require(value.vendorRef().equals(vendorPin()), "vendor observation names another executable");
        Actual first = readActual(Path.of(value.firstActualRef().path()), ActualStage.VENDOR_TIMEOUT_ONE);
        Actual second = readActual(Path.of(value.secondActualRef().path()), ActualStage.VENDOR_TIMEOUT_TWO);
        require(!first.ownerIdentity().equals(second.ownerIdentity()) && !value.firstActualRef().equals(value.secondActualRef())
                && first.stageDeadlineAtUtc().equals(value.stageDeadlineAtUtc()) && second.stageDeadlineAtUtc().equals(value.stageDeadlineAtUtc()),
                "both distinct vendor processes must retain their original shared deadline");
        Instant firstAt = Instant.parse(first.observedAtUtc()), secondAt = Instant.parse(second.observedAtUtc()), at = Instant.parse(value.observedAtUtc());
        require(!firstAt.isAfter(secondAt) && !secondAt.isAfter(at) && at.isBefore(Instant.parse(value.stageDeadlineAtUtc())), "vendor chronology differs from the original stage window");
        for (Actual actual : List.of(first, second)) require(actual.sourceManifestRef().equals(value.sourceManifestRef())
                && actual.toolsReceiptRef().equals(value.toolsReceiptRef()) && actual.environmentRef().equals(value.environmentRef()), "vendor source/tools/environment changed between cases");
        require(value.firstAnalysis().equals(vendorAnalysis(first, VctipProbeFacts.ProbeCase.IDLE_ONE))
                && value.secondAnalysis().equals(vendorAnalysis(second, VctipProbeFacts.ProbeCase.IDLE_TWO)), "stored vendor analysis differs from the original raw terminals");
        return value;
    }

    private static void verifyUniqueRefs(List<ControlBuild.FileRef> refs) throws IOException {
        Set<String> paths = new HashSet<>();
        for (ControlBuild.FileRef ref : refs) {
            require(paths.add(Path.of(ref.path()).normalize().toString().toLowerCase(java.util.Locale.ROOT)), "duplicate native evidence file path");
            ref.verify();
        }
    }

    private static Actual accepted(String id) throws IOException {
        for (ActualStage stage : ActualStage.values()) if (stage.wireId().equals(id)) return readActual(actualPath(id), stage);
        throw new IOException("unknown native command-stage identity: " + id);
    }
    private static Graph acceptedGraph() throws IOException {
        accepted(CONFIGURE_ID); Graph graph = JSON.readValue(bytes(SCRATCH.resolve("CONFIGURED-GRAPH01.json"), 2097152), Graph.class);
        require(graph.schema().equals("xar.native-configured-selected-graph/v1") && graph.machineId().equals(MACHINE)
                && graph.status() == GraphStatus.CONFIGURED_SOURCE_FROZEN_NOT_BUILT && graph.targets().size() == 3 && graph.runtimeTranslationUnitCount() > 0, "actual configured selected graph required");
        require(graph.configureReceiptRef().equals(ControlBuild.FileRef.measure(actualPath(CONFIGURE_ID))), "configured graph must bind the current successful configure actual");
        graph.configureReceiptRef().verify(); graph.runtimeSourcesRef().verify(); return graph;
    }
    private static void acceptedDefender() throws IOException {
        Actual registration = accepted("defender-register-two");
        PreparedRegistration prepared = JSON.readValue(bytes(SCRATCH.resolve("DEFENDER-REGISTRATION-PREPARED01.json"), 2097152), PreparedRegistration.class);
        ControlBuild.FileRef preparedRef = ControlBuild.FileRef.measure(SCRATCH.resolve("DEFENDER-REGISTRATION-PREPARED01.json"));
        require(registration.linkedArtifactRefs().contains(preparedRef), "accepted registration did not bind original preparation bytes");
        List<String> tail = List.of("execute-approved-plan", prepared.reviewPlanRef().path(),
                prepared.reviewPlanRef().sha256(), registration.stageDeadlineAtUtc());
        require(registration.command().size() >= tail.size()
                && registration.command().subList(registration.command().size() - tail.size(), registration.command().size()).equals(tail),
                "accepted registration command differs from original reviewed plan/SHA/Context deadline");
        acceptedDefender(registration.stageDeadlineAtUtc());
    }
    private static void acceptedDefender(String originalContextDeadlineAtUtc) throws IOException {
        PreparedRegistration prepared = JSON.readValue(bytes(SCRATCH.resolve("DEFENDER-REGISTRATION-PREPARED01.json"), 2097152), PreparedRegistration.class);
        require(prepared.deadlineAtUtc().equals(originalContextDeadlineAtUtc), "prepared deadline differs from original actual REGISTER Context");
        prepared.reviewPlanRef().verify();
        NativeProjectExeUac.Plan plan = NativeProjectExeUac.parsePlan(bytes(Path.of(prepared.reviewPlanRef().path()), 2097152));
        NativeProjectExeRegistration.Qualification qualification = NativeProjectExeRegistration.readVerified(
                Path.of(prepared.reviewPlanRef().path()), prepared.reviewPlanRef().sha256(), originalContextDeadlineAtUtc,
                ControlBuild.FileRef.measure(Path.of(plan.resultPath())));
        require(qualification.planRef().equals(prepared.reviewPlanRef())
                && qualification.helperReceiptRef().equals(ControlBuild.FileRef.measure(Path.of(plan.helperReceiptPath())))
                && qualification.executables().stream().map(NativeProjectExeUac.SelectedExecutable::target).collect(java.util.stream.Collectors.toSet())
                        .equals(new HashSet<>(TARGETS)), "causal direct-admin result differs from the exact prepared two-target registration");
        for (NativeProjectExeUac.SelectedExecutable executable : qualification.executables()) {
            require(executable.fileRef().equals(ControlBuild.FileRef.measure(BUILD.resolve("bin/" + executable.target() + ".exe"))),
                    "Defender verified executable differs from the current actual build");
        }
    }
    private static void dependencyManifest(Graph graph) throws IOException {
        Path raw = SCRATCH.resolve("compiler-active-dependencies.stdout.log");
        Map<Path, ControlBuild.FileRef> pins = new LinkedHashMap<>();
        Set<Path> frozen = new HashSet<>(graph.projectSourceRefs().stream().map(r -> Path.of(r.path())).toList());
        try (var reader = Files.newBufferedReader(raw, StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.startsWith("    ")) continue; String name = line.strip(); if (name.isEmpty()) continue;
                Path path = Path.of(name); if (!path.isAbsolute()) path = BUILD.resolve(path); path = path.toAbsolutePath().normalize();
                require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS), "actual compiler dependency absent: " + path);
                if (path.startsWith(SOURCE)) require(frozen.contains(path), "actual project compiler dependency was not frozen: " + path);
                if (!pins.containsKey(path)) pins.put(path, ControlBuild.FileRef.measure(path));
                require(pins.size() <= 12000, "finite actual compiler dependencies exceeded");
            }
        }
        require(!pins.isEmpty(), "fresh actual Ninja compiler dependencies missing");
        publish(SCRATCH.resolve("ACTUAL-COMPILER-DEPENDENCIES01.json"), new Dependencies("xar.native-actual-compiler-dependencies/v1", MACHINE,
                Instant.now().toString(), "post-build actual dependencies; project inputs verified against pre-build freeze; system headers observed after build only",
                ControlBuild.FileRef.measure(raw), sorted(pins.values().stream().toList())));
    }
    /** Decode only. Qualification additionally verifies actual output and dependency file identities. */
    public static Dependencies parseDependencies(byte[] raw) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= 2097152, "bounded dependency manifest bytes required");
        Dependencies value = JSON.readValue(raw, Dependencies.class); require(value != null, "dependency object required"); return value;
    }
    private static void acceptedCompilerDependencies() throws IOException {
        Actual actual = accepted("compiler-active-dependencies");
        Dependencies dependencies = parseDependencies(bytes(SCRATCH.resolve("ACTUAL-COMPILER-DEPENDENCIES01.json"), 2097152));
        require(dependencies.rawRef().equals(actual.stdoutRef()), "typed dependencies do not bind actual compiler output");
        dependencies.rawRef().verify(); verify(dependencies.dependencyRefs());
    }
    private static List<ControlBuild.FileRef> configuredTools(Context context) throws IOException {
        Set<String> required = Set.of("CMAKE_AR", "CMAKE_LINKER", "CMAKE_MT", "CMAKE_RC_COMPILER", "CMAKE_CXX_COMPILER");
        Map<String, Path> paths = new LinkedHashMap<>();
        for (String line : Files.readAllLines(BUILD.resolve("CMakeCache.txt"), StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#") || line.startsWith("//")) continue;
            int colon = line.indexOf(':'), equals = line.indexOf('='); if (colon < 0 || equals <= colon) continue;
            String name = line.substring(0, colon);
            if (required.contains(name)) {
                Path path = Path.of(line.substring(equals + 1)); require(path.isAbsolute(), "configured native tool must be absolute: " + name);
                require(paths.put(name, path.toAbsolutePath().normalize()) == null, "duplicate configured native tool");
            }
        }
        require(paths.keySet().equals(required), "complete configured compiler/archive/link/resource tools required");
        require(paths.get("CMAKE_CXX_COMPILER").equals(tool(context, "cl.exe")) && paths.get("CMAKE_LINKER").equals(tool(context, "link.exe")), "configured compiler/linker differ from exact original pins");
        List<ControlBuild.FileRef> pins = new ArrayList<>(); for (Path path : paths.values()) pins.add(ControlBuild.FileRef.measure(path)); return sorted(pins);
    }
    private static void collectQuoted(List<Path> initial, List<Path> search, Map<Path, ControlBuild.FileRef> pins) throws IOException {
        ArrayDeque<Path> pending = new ArrayDeque<>(initial); Set<Path> visited = new HashSet<>();
        while (!pending.isEmpty()) {
            Path path = pending.remove(); if (!visited.add(path)) continue; require(visited.size() <= 1500, "finite quoted include closure exceeded");
            Matcher matcher = INCLUDE.matcher(new String(bytes(path, 2097152), StandardCharsets.UTF_8));
            while (matcher.find()) {
                String name = matcher.group(2); boolean quoted = matcher.group(1).equals("\"");
                List<Path> roots = new ArrayList<>(); if (quoted) roots.add(path.getParent()); roots.addAll(search);
                Path found = null;
                for (Path root : roots) { Path candidate = root.resolve(name).normalize(); if (Files.isRegularFile(candidate, LinkOption.NOFOLLOW_LINKS)) { found = candidate.toAbsolutePath().normalize(); break; } }
                require(found != null || !quoted, "unresolved selected quoted include " + name + " from " + path);
                if (found == null) continue;
                if (found.startsWith(SOURCE) || found.startsWith(BUILD)) {
                    if (!pins.containsKey(found)) pins.put(found, ControlBuild.FileRef.measure(found)); pending.add(found);
                }
            }
        }
    }
    private static Map<String, String> nativeEnvironment() throws IOException {
        NativeBuildEnvironment.Snapshot snapshot = NativeBuildEnvironment.read(SCRATCH, MACHINE,
                bytes(SCRATCH.resolve(NativeBuildEnvironment.SNAPSHOT_NAME), 65536));
        Map<String, String> result = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        result.putAll(snapshot.values()); result.put("PYTHONDONTWRITEBYTECODE", "1");
        return Map.copyOf(result);
    }
    private static ControlBuild.FileRef environmentRef() throws IOException { return ControlBuild.FileRef.measure(SCRATCH.resolve("VCVARS-ENVIRONMENT01.properties")); }
    private static List<ControlBuild.FileRef> artifactRefs() throws IOException {
        return List.of(ControlBuild.FileRef.measure(BUILD.resolve("lib/" + RUNTIME + ".lib")),
                ControlBuild.FileRef.measure(BUILD.resolve("bin/" + KINSHIP + ".exe")), ControlBuild.FileRef.measure(BUILD.resolve("bin/" + COMBAT + ".exe")));
    }
    private static Path tool(Context context, String name) throws IOException {
        List<Path> matches = context.toolRefs().stream().map(r -> Path.of(r.path())).filter(p -> p.getFileName().toString().equalsIgnoreCase(name)).toList();
        require(matches.size() == 1, "one exact pinned tool required: " + name); return matches.getFirst();
    }
    private static void guard(Context context) throws IOException {
        context.cardRef().verify(); require(Instant.now().isBefore(context.deadline()), "native resource card expired");
        long combinedBuild = footprint(BUILD);
        for (Path previous : PREVIOUS_BUILDS) combinedBuild = Math.addExact(combinedBuild, footprint(previous));
        require(combinedBuild <= BUILD_CAP && footprint(SCRATCH) <= context.card().scratchLimitBytes(), "finite combined native output cap exceeded");
        if (context.config().stage() == Stage.ENV || context.config().stage() == Stage.VENDOR_TIMEOUTS)
            require(!Files.exists(BUILD, LinkOption.NOFOLLOW_LINKS), "ENV/vendor cannot create or populate the build root");
    }
    private static void logBudget() throws IOException {
        long ordinary = 0;
        try (var paths = Files.list(SCRATCH)) {
            for (Path path : paths.toList()) {
                String name = path.getFileName().toString();
                if (!name.endsWith(".stdout.log") && !name.endsWith(".stderr.log")) continue;
                if (name.equals("compiler-active-dependencies.stdout.log")) require(Files.size(path) <= DEPENDENCY_EVIDENCE_CAP, "actual dependency evidence exceeds separate sixteen MiB cap");
                else ordinary = Math.addExact(ordinary, Files.size(path));
            }
        }
        require(ordinary <= LOG_CAP, "aggregate ordinary native stdout/stderr exceeds two MiB cap");
    }
    private static long footprint(Path root) throws IOException {
        return inventoryFootprint(root, path -> { });
    }
    @FunctionalInterface public interface InventoryCheck { void beforeCheck(Path path) throws IOException; }
    /** Shared mutable traversal preserves root/reparse/I/O guards; this wrapper adds native entry guards. */
    public static long inventoryFootprint(Path root, InventoryCheck observer) throws IOException {
        java.util.concurrent.atomic.AtomicLong entries = new java.util.concurrent.atomic.AtomicLong();
        long logical = ControlBuild.mutableInventoryBytes(root, path -> {
            require(entries.incrementAndGet() <= 25000, "bounded native output inventory required"); observer.beforeCheck(path);
        });
        return Math.addExact(logical, Math.multiplyExact(entries.get(), 4096));
    }
    private static Path actualPath(String id) { return SCRATCH.resolve(id + ".actual.json"); }
    public static long stageMemoryLimit(Stage stage) {
        java.util.Objects.requireNonNull(stage); return stage == Stage.ENV || stage == Stage.VENDOR_TIMEOUTS ? ENV_MEMORY : MEMORY;
    }
    public static long stageScratchLimit(Stage stage) {
        java.util.Objects.requireNonNull(stage); return stage == Stage.ENV || stage == Stage.VENDOR_TIMEOUTS ? ENV_SCRATCH_CAP : SCRATCH_CAP;
    }
    private static int stageTimeout(Stage stage) {
        return switch (stage) {
            case BUILD -> 1800;
            case CONFIGURE -> 180;
            case REGISTER -> 240;
            case ENV, VERSIONS, VENDOR_TIMEOUTS, GRAPH, KINSHIP, COMBAT -> 120;
        };
    }
    private static Path resolveSource(String name) { Path path = Path.of(name); return (path.isAbsolute() ? path : SOURCE.resolve(path)).toAbsolutePath().normalize(); }
    private static Path confined(Path root, String name) throws IOException { Path path = root.resolve(name).toAbsolutePath().normalize(); require(path.startsWith(root), "configured artifact/reply escapes exact root"); return path; }
    private static JsonNode uniqueKind(ArrayNode values, String kind) throws IOException {
        List<JsonNode> found = new ArrayList<>(); for (JsonNode row : values) if (kind.equals(text(row, "kind"))) found.add(row);
        require(found.size() == 1, "one configured " + kind + " object required"); return found.getFirst();
    }
    private static ObjectNode shortRef(ControlBuild.FileRef pin) { ObjectNode row = JSON.createObjectNode(); row.put("path", pin.path()); row.put("sha256", pin.sha256()); return row; }
    private static List<ControlBuild.FileRef> sorted(List<ControlBuild.FileRef> refs) { return refs.stream().sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList(); }
    private static List<ControlBuild.FileRef> refs(ArrayNode rows) throws IOException { List<ControlBuild.FileRef> result = new ArrayList<>(); for (JsonNode row : rows) result.add(ref(row)); return result; }
    private static ControlBuild.FileRef ref(JsonNode row) throws IOException { return new ControlBuild.FileRef(text(row, "path"), integer(row, "bytes"), text(row, "sha256")); }
    private static void verify(List<ControlBuild.FileRef> refs) throws IOException { for (ControlBuild.FileRef ref : refs) ref.verify(); }
    private static ControlBuild.FileRef measureIfPresent(Path path) {
        try { return Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) ? ControlBuild.FileRef.measure(path) : null; }
        catch (IOException unavailable) { return null; }
    }
    private static long integer(JsonNode object, String key) throws IOException { JsonNode value = object == null ? null : object.get(key); require(value != null && value.isIntegralNumber() && value.canConvertToLong() && value.longValue() >= 0, "exact nonnegative integer required: " + key); return value.longValue(); }
    private static boolean bool(JsonNode object, String key) throws IOException { JsonNode value = object == null ? null : object.get(key); require(value != null && value.isBoolean(), "exact boolean required: " + key); return value.booleanValue(); }
    private static String text(JsonNode object, String key) throws IOException { JsonNode value = object == null ? null : object.get(key); require(value != null && value.isTextual() && !value.textValue().isBlank(), "nonempty text required: " + key); return value.textValue(); }
    private static List<String> arguments(JsonNode object, String key, int size) throws IOException { ArrayNode rows = array(object, key); require(rows.size() == size, "exact bootstrap argc required"); List<String> result = new ArrayList<>(); for (JsonNode row : rows) { require(row.isTextual(), "bootstrap argument text required"); result.add(row.textValue()); } return result; }
    private static ArrayNode array(JsonNode object, String key) throws IOException { JsonNode value = object == null ? null : object.get(key); require(value != null && value.isArray(), "array required: " + key); return (ArrayNode) value; }
    private static JsonNode read(Path path, int maximum) throws IOException { JsonNode value = JSON.readTree(bytes(path, maximum)); require(value != null && value.isObject(), "JSON object required: " + path); return value; }
    private static byte[] bytes(Path path, int maximum) throws IOException { require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(path), "plain input file required: " + path); try (InputStream input = Files.newInputStream(path)) { byte[] raw = input.readNBytes(maximum + 1); require(raw.length <= maximum, "bounded input exceeded: " + path); return raw; } }
    private static void publish(Path path, Object value) throws IOException { byte[] raw = JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(value); require(raw.length <= 2097152, "finite native metadata cap exceeded"); Files.write(path, raw, StandardOpenOption.CREATE_NEW); }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length == 9 && args[0].equals("prepare-environment")) {
            Map<String, String> values = new LinkedHashMap<>();
            Set<String> keys = Set.of("--tools-receipt", "--plan", "--operation-source", "--output-manifest");
            for (int index = 1; index < args.length; index += 2)
                require(keys.contains(args[index]) && values.putIfAbsent(args[index], args[index + 1]) == null, "unknown or duplicate environment preparation argument");
            require(values.keySet().equals(keys), "exact environment preparation arguments required");
            EnvironmentPreparation prepared = prepareEnvironmentAdmission(Path.of(values.get("--plan")), Path.of(values.get("--tools-receipt")),
                    Path.of(values.get("--operation-source")), Path.of(values.get("--output-manifest")));
            System.out.println(JSON.writeValueAsString(prepared)); return;
        }
        boolean prepareOnly = args.length == 11 && args[0].equals("prepare-registration");
        boolean executeReviewed = args.length == 15 && args[0].equals("execute-registration");
        int first = prepareOnly || executeReviewed ? 1 : 0;
        require(args.length - first == (executeReviewed ? 14 : 10), "five stage key/value arguments and explicit reviewed plan/SHA for execution required"); Map<String, String> values = new LinkedHashMap<>();
        Set<String> keys = new HashSet<>(Set.of("--stage", "--resource-card", "--tools-receipt", "--plan", "--operation-source"));
        if (executeReviewed) keys.addAll(Set.of("--reviewed-plan", "--reviewed-plan-sha256"));
        for (int index = first; index < args.length; index += 2) require(keys.contains(args[index]) && values.putIfAbsent(args[index], args[index + 1]) == null, "unknown or duplicate native argument");
        require(values.keySet().equals(keys), "all exact native arguments required");
        Config config = new Config(Stage.valueOf(values.get("--stage")), Path.of(values.get("--resource-card")), Path.of(values.get("--tools-receipt")), Path.of(values.get("--plan")), Path.of(values.get("--operation-source")));
        if (prepareOnly) { PreparedRegistration prepared = prepareRegistration(config); System.out.println(prepared.status() + " deadline=" + prepared.deadlineAtUtc()); }
        else if (executeReviewed) executeRegistration(new RegistrationExecution(config,
                Path.of(values.get("--reviewed-plan")), values.get("--reviewed-plan-sha256")));
        else run(config);
    }
}
