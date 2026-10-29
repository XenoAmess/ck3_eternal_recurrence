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
import org.xar.ck3.control.build.CiBootstrap.JavaUtf8Invocation;

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

    public static final String CURRENT_PLAN_SCHEMA = "xar.current-native-fixture-build-plan/v1";
    public static final String CURRENT_HOLY_PLAN_SCHEMA = "xar.current-native-fixture-build-plan/v2";
    public static final String CURRENT_CARD_SCHEMA = "xar.shared-native-stage-resource-card/v3";
    private static final ObjectMapper CURRENT_JSON = RootNativePlanJson.mapper();
    public enum FixtureTarget {
        COMBATROLES_COMMANDER(COMBAT, true, List.of()),
        HOLY_ORDER_WAR_ELIGIBILITY("xar_ck3_12003_holy_order_war_eligibility_test", false,
                holySources("war_eligibility")),
        HOLY_ORDER_SERVICE_LIFECYCLE("xar_ck3_12003_holy_order_service_lifecycle_test", false,
                holySources("service_lifecycle")),
        HOLY_ORDER_TROOP_ASSOCIATION("xar_ck3_12003_holy_order_troop_association_test", false,
                holySources("troop_association")),
        HOLY_ORDER_HIRE_COST_CONTEXT("xar_ck3_12003_holy_order_hire_cost_context_test", true,
                List.of("src/ck3_12003_holy_order_hire_cost_context_test.cpp")),
        HOLY_ORDER_CURRENT_REINFORCEMENT("xar_ck3_12003_holy_order_current_reinforcement_test", true,
                List.of("src/ck3_12003_holy_order_current_reinforcement_test.cpp"));
        private final String targetName;
        private final boolean usesRuntime;
        private final List<String> sourceRelativePaths;
        FixtureTarget(String targetName, boolean usesRuntime, List<String> sourceRelativePaths) {
            this.targetName=targetName; this.usesRuntime=usesRuntime; this.sourceRelativePaths=List.copyOf(sourceRelativePaths);
        }
        public String targetName() { return targetName; }
        public boolean usesRuntime() { return usesRuntime; }
        public boolean holy() {
            return switch(this) {
                case HOLY_ORDER_WAR_ELIGIBILITY,HOLY_ORDER_SERVICE_LIFECYCLE,HOLY_ORDER_TROOP_ASSOCIATION,
                        HOLY_ORDER_HIRE_COST_CONTEXT,HOLY_ORDER_CURRENT_REINFORCEMENT -> true;
                case COMBATROLES_COMMANDER -> false;
            };
        }
        public List<String> sourceRelativePaths() { return sourceRelativePaths; }
        public ActualStage buildStage() {
            return this==COMBATROLES_COMMANDER ? ActualStage.COMBATROLES_TARGET_BUILD : ActualStage.HOLY_FIXTURE_TARGET_BUILD;
        }
        public Set<String> closureNames() { return usesRuntime ? Set.of(targetName,RUNTIME) : Set.of(targetName); }
        private static List<String> holySources(String kind) {
            return List.of("src/ck3_12003_holy_order_"+kind+"_test.cpp",
                    "src/ck3_12003_player_holy_order_context.cpp",
                    "src/ck3_12003_holy_order_current_reinforcement.cpp",
                    "src/ck3_12003_player_holy_order_wire.cpp");
        }
    }
    public record CurrentFixturePlan(String schema, String machineId, String ownerTask,
            Path canonicalRepository, ControlBuild.FileRef qualifiedToolsBuildRef,
            ControlBuild.FileRef retainedSourceActualRef, ControlBuild.FileRef compileSourceBindingRef,
            ControlBuild.FileRef environmentActualRef, Path compileSourceRoot, Path buildRoot, Path scratchRoot,
            FixtureTarget target, List<NativeBridgeBuild.Definition> definitions, int parallelJobs,
            long buildAllocationLimitBytes) {
        public CurrentFixturePlan {
            boolean commander=CURRENT_PLAN_SCHEMA.equals(schema) && target==FixtureTarget.COMBATROLES_COMMANDER;
            boolean holy=CURRENT_HOLY_PLAN_SCHEMA.equals(schema) && target!=null && target.holy();
            if ((!commander && !holy) || !MACHINE.equals(machineId)
                    || !"/root/native_fixtures63".equals(ownerTask)
                    || parallelJobs < 1 || parallelJobs > 2 || buildAllocationLimitBytes < (16L << 20)
                    || buildAllocationLimitBytes > (8L << 30))
                throw new IllegalArgumentException("Versioned finite single-fixture plan required");
            for (Path root : List.of(canonicalRepository, compileSourceRoot, buildRoot, scratchRoot))
                if (!root.isAbsolute() || !root.equals(root.toAbsolutePath().normalize()))
                    throw new IllegalArgumentException("Absolute normalized fixture roots required");
            if (overlap(compileSourceRoot, buildRoot) || overlap(compileSourceRoot, scratchRoot)
                    || overlap(buildRoot, scratchRoot))
                throw new IllegalArgumentException("Overlapping fixture roots");
            java.util.Objects.requireNonNull(qualifiedToolsBuildRef);
            java.util.Objects.requireNonNull(retainedSourceActualRef);
            java.util.Objects.requireNonNull(compileSourceBindingRef);
            java.util.Objects.requireNonNull(environmentActualRef);
            definitions = List.copyOf(definitions);
            if (definitions.size() > 512 || definitions.stream().map(NativeBridgeBuild.Definition::option).distinct().count() != definitions.size())
                throw new IllegalArgumentException("Unique bounded source-declared fixture options required");
        }
    }
    public static CurrentFixturePlan readCurrentPlan(ControlBuild.FileRef pin) throws IOException {
        pin.verify(); CurrentFixturePlan plan = CURRENT_JSON.readValue(bytes(Path.of(pin.path()), 262144), CurrentFixturePlan.class);
        pin.verify(); return plan;
    }
    private static boolean overlap(Path left, Path right) { return left.startsWith(right) || right.startsWith(left); }

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
        COMBATROLES_TARGET_BUILD("combatroles-target-build", true, true),
        HOLY_FIXTURE_TARGET_BUILD("holy-fixture-target-build", true, true),
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
            boolean legacy = "xar.shared-native-stage-resource-card/v2".equals(schema) && "/root/native_fixture09".equals(owner);
            boolean current = CURRENT_CARD_SCHEMA.equals(schema) && "/root/native_fixtures63".equals(owner)
                    && Set.of(Stage.BUILD, Stage.REGISTER, Stage.COMBAT).contains(allowedStage);
            if ((!legacy && !current) || !MACHINE.equals(machineId)
                    || status != ResourceStatus.ADMITTED_SINGLE_STAGE
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

    public record RetainedFixtureFile(SharedSourceFiles.Witness original, SharedSourceFiles.Witness retained) {
        public RetainedFixtureFile {
            if(original==null || retained==null || original.source().bytes()!=retained.source().bytes()
                    || !original.source().sha256().equals(retained.source().sha256())
                    || original.nativeFile().volumeSerialDecimal().equals(retained.nativeFile().volumeSerialDecimal())
                        && original.nativeFile().fileIdDecimal().equals(retained.nativeFile().fileIdDecimal()))
                throw new IllegalArgumentException("A retained copy needs equal bytes and independent original/copy identities");
        }
    }
    public record CurrentStageRetention(String schema,String machineId,ControlBuild.FileRef fixturePlanRef,
            String stageId,List<RetainedFixtureFile> files) {
        public CurrentStageRetention {
            boolean commander="xar.current-fixture-retained-stage-files/v1".equals(schema)
                    && Set.of(CONFIGURE_ID,"configured-graph",ActualStage.COMBATROLES_TARGET_BUILD.wireId()).contains(stageId);
            boolean holy="xar.current-fixture-retained-stage-files/v2".equals(schema)
                    && Set.of(CONFIGURE_ID,"configured-graph",ActualStage.HOLY_FIXTURE_TARGET_BUILD.wireId()).contains(stageId);
            if((!commander && !holy) || !MACHINE.equals(machineId))
                throw new IllegalArgumentException("Explicit current generated-file retention required");
            files=List.copyOf(files);
            if(files.isEmpty() || files.size()>256 || files.stream().map(row->row.original().source().path()).distinct().count()!=files.size())
                throw new IllegalArgumentException("Unique finite original generated files required");
        }
    }
    private static Path retentionPath(CurrentFixturePlan plan,String stage) {
        return plan.scratchRoot().resolve(stage+".retained-files.json");
    }
    private static ControlBuild.FileRef retainCurrentStageFiles(Context context,String stage,List<ControlBuild.FileRef> refs) throws IOException {
        var plan=context.current();Path directory=plan.scratchRoot().resolve(stage+".retained-files");
        require(!Files.exists(directory,LinkOption.NOFOLLOW_LINKS),"Generated-file retention is append-only");
        SharedSourceFiles.plainAncestors(directory);guard(context);Files.createDirectory(directory);
        var rows=new ArrayList<RetainedFixtureFile>();
        for(var ref:refs.stream().distinct().toList()) {
            Path original=Path.of(ref.path());if(!original.startsWith(plan.buildRoot()))continue;
            long growth=Math.addExact(Math.multiplyExact((ref.bytes()+4095)/4096,4096),4096);
            require(Math.addExact(footprint(plan.scratchRoot()),Math.addExact(growth,2097152))<=context.card().scratchLimitBytes(),
                    "Actual generated-file retention exceeds admitted scratch capacity");
            Path copy=directory.resolve(rows.size()+"-"+original.getFileName());
            rows.add(retainFixtureFile(ref,copy));guard(context);
        }
        require(!rows.isEmpty(),"A current stage must retain its actual generated files");
        Path output=retentionPath(plan,stage);
        publish(output,new CurrentStageRetention(retentionSchema(plan),MACHINE,
                ControlBuild.FileRef.measure(context.config().plan()),stage,rows));return ControlBuild.FileRef.measure(output);
    }
    private static CurrentStageRetention retainedStage(CurrentFixturePlan plan,ControlBuild.FileRef planRef,String stage) throws IOException {
        Path path=retentionPath(plan,stage);CurrentStageRetention value=JSON.readValue(bytes(path,2097152),CurrentStageRetention.class);
        require(value.schema().equals(retentionSchema(plan)) && retentionStages(plan).contains(stage)
                && value.stageId().equals(stage) && value.fixturePlanRef().equals(planRef),"Retained stage belongs to another fixture");
        ControlBuild.FileRef mapRef=ControlBuild.FileRef.measure(path);
        if(stage.equals("configured-graph")) {
            Graph graph=JSON.readValue(bytes(plan.scratchRoot().resolve("CONFIGURED-GRAPH01.json"),2097152),Graph.class);
            require(graph.configuredInputRefs().contains(mapRef),"Configured graph omitted its original retention map");
        } else {
            Actual actual=parseActual(bytes(plan.scratchRoot().resolve(stage+".actual.json"),1048576),
                    stage.equals(CONFIGURE_ID)?ActualStage.CONFIGURE_NEXT01:plan.target().buildStage());
            require(actual.outputRefs().contains(mapRef),"Original actual omitted its retention map");
        }
        Path directory=plan.scratchRoot().resolve(stage+".retained-files");
        for(var row:value.files()) {
            require(Path.of(row.original().source().path()).startsWith(plan.buildRoot())
                    && Path.of(row.retained().source().path()).getParent().equals(directory),"Retained generated file escaped its roots");
            SharedSourceFiles.assertUnchanged(row.retained());
        }
        return value;
    }
    private static RetainedFixtureFile retainedFile(CurrentFixturePlan plan,ControlBuild.FileRef planRef,ControlBuild.FileRef original) throws IOException {
        for(String stage:retentionStages(plan)) {
            Path path=retentionPath(plan,stage);if(!Files.exists(path,LinkOption.NOFOLLOW_LINKS))continue;
            var retained=retainedStage(plan,planRef,stage);
            for(var row:retained.files())if(row.original().source().equals(original))return row;
        }
        throw new IOException("Original generated file lacks exact immutable-stage evidence: "+original.path());
    }
    private static void verifyCurrentRefs(CurrentFixturePlan plan,ControlBuild.FileRef planRef,List<ControlBuild.FileRef> refs) throws IOException {
        Set<String> names=new HashSet<>();
        for(var ref:refs) {
            require(names.add(Path.of(ref.path()).normalize().toString().toLowerCase(java.util.Locale.ROOT)),"Duplicate current evidence path");
            if(Path.of(ref.path()).startsWith(plan.buildRoot()))retainedFile(plan,planRef,ref);
            else ref.verify();
        }
    }
    private static void verifyCurrentLiveGenerated(CurrentFixturePlan plan,ControlBuild.FileRef planRef) throws IOException {
        verifyCurrentLiveGenerated(plan,planRef,null);
    }
    private static void verifyCurrentLiveGenerated(CurrentFixturePlan plan,ControlBuild.FileRef planRef,String activeStage) throws IOException {
        for(String stage:retentionStages(plan)) {
            if(stage.equals(activeStage))continue;
            Path path=retentionPath(plan,stage);if(!Files.exists(path,LinkOption.NOFOLLOW_LINKS))continue;
            for(var row:retainedStage(plan,planRef,stage).files())SharedSourceFiles.assertUnchanged(row.original());
        }
    }
    public static ControlBuild.FileRef linkedExecutableRef(Actual actual,Path originalPath) throws IOException {
        var refs=actual.linkedArtifactRefs().stream().filter(ref->Path.of(ref.path()).equals(originalPath)).toList();
        require(refs.size()==1,"One original linked executable required");
        JsonNode card=read(Path.of(actual.resourceCardRef().path()),262144);
        if(CURRENT_CARD_SCHEMA.equals(card.path("schema").asText())) {
            var plan=readCurrentPlan(currentFixtureCard(actual.resourceCardRef()).packageRequestRef());
            retainedFile(plan,currentFixtureCard(actual.resourceCardRef()).packageRequestRef(),refs.getFirst());
        } else refs.getFirst().verify();
        return refs.getFirst();
    }
    static RetainedFixtureFile retainFixtureFile(ControlBuild.FileRef original,Path copy) throws IOException {
        var before=SharedSourceFiles.observe(Path.of(original.path()));
        require(before.source().equals(original),"Generated input changed before retention");
        SharedSourceFiles.plainAncestors(copy);Files.copy(Path.of(original.path()),copy);
        var retained=SharedSourceFiles.observe(copy);SharedSourceFiles.assertUnchanged(before);
        return new RetainedFixtureFile(before,retained);
    }
    private static List<ControlBuild.FileRef> measureAllPresent(List<Path> paths) throws IOException {
        var refs=new ArrayList<ControlBuild.FileRef>();
        for(Path path:paths) { var ref=measureIfPresent(path);if(ref!=null)refs.add(ref); }return List.copyOf(refs);
    }
    private static List<ControlBuild.FileRef> immutableCurrentRefs(CurrentFixturePlan plan,ControlBuild.FileRef planRef,
            List<ControlBuild.FileRef> originals) throws IOException {
        var refs=new ArrayList<ControlBuild.FileRef>();
        for(var original:originals)refs.add(Path.of(original.path()).startsWith(plan.buildRoot())
                ?retainedFile(plan,planRef,original).retained().source():original);
        return sorted(refs.stream().distinct().toList());
    }
    public static ControlBuild.FileRef currentFixtureRetainedExecutable(CurrentFixtureRegistrationInputs inputs) throws IOException {
        return retainedFile(inputs.plan(),inputs.fixturePlanRef(),inputs.executableRef()).retained().source();
    }

    private record Context(Config config, Instant deadline, ResourceCard card, ControlBuild.FileRef cardRef,
            ControlBuild.FileRef toolsReceiptRef, JsonNode plan, List<ControlBuild.FileRef> sourceRefs,
            List<ControlBuild.FileRef> toolRefs, List<ControlBuild.FileRef> runtimeRefs, Map<String, String> baseEnv,
            CurrentFixturePlan current, CompileSourceBinding.Binding binding,
            List<SharedSourceFiles.Witness> compileBefore, NativeBridgeBuild.Actual environment) {
        Context(Config config, Instant deadline, ResourceCard card, ControlBuild.FileRef cardRef,
                ControlBuild.FileRef toolsReceiptRef, JsonNode plan, List<ControlBuild.FileRef> sourceRefs,
                List<ControlBuild.FileRef> toolRefs, List<ControlBuild.FileRef> runtimeRefs, Map<String, String> baseEnv) {
            this(config, deadline, card, cardRef, toolsReceiptRef, plan, sourceRefs, toolRefs, runtimeRefs, baseEnv,
                    null, null, List.of(), null);
        }
        Path sourceRoot() { return current == null ? SOURCE : current.compileSourceRoot(); }
        Path buildRoot() { return current == null ? BUILD : current.buildRoot(); }
        Path scratchRoot() { return current == null ? SCRATCH : current.scratchRoot(); }
        List<String> targets() { return current == null ? TARGETS : List.of(current.target().targetName()); }
    }
    private enum DiagnosticInvocation { NOT_RETURNED, RETURNED }
    private record JobDiagnosticRecord(String schema, String machineId, String observedAtUtc,
            DiagnosticInvocation invocation, WindowsJobProcess.JobDiagnosticOutcome diagnostic) { }

    public static void run(Config config) throws IOException, InterruptedException {
        Context context = prepare(config);
        if (context.current() != null) {
            switch (config.stage()) {
                case BUILD -> { configure(context); graph(context); build(context); }
                case COMBAT -> combat(context);
                case REGISTER -> register(context);
                default -> throw new IOException("Current single-fixture request supports BUILD/REGISTER/COMBAT only");
            }
            return;
        }
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

    private record CurrentInputs(CurrentFixturePlan plan, CompileSourceBinding.Binding binding,
            NativeBridgeBuild.Actual environment, NativeBridgeBuild.Request environmentRequest,
            List<ControlBuild.FileRef> sources, List<ControlBuild.FileRef> tools, List<ControlBuild.FileRef> runtime) { }
    private static CurrentInputs currentInputs(Path planPath, Path operationSource, ControlBuild.BuildReceipt tools) throws IOException {
        ControlBuild.FileRef planRef = ControlBuild.FileRef.measure(planPath);
        CurrentFixturePlan plan = readCurrentPlan(planRef);
        require(plan.canonicalRepository().toRealPath().equals(REPO.toRealPath())
                && plan.qualifiedToolsBuildRef().equals(ControlBuild.FileRef.measure(Path.of(plan.qualifiedToolsBuildRef().path())))
                && tools.equals(ControlBuild.verifiedCompletedReceipt(plan.qualifiedToolsBuildRef()))
                && tools.completeDeployment().equals(ControlBuild.producerClosure())
                && tools.completeDeployment().equals(ControlBuild.producerClosure(NativeFixtureBuild.class)),
                "Exact qualified fixture producer required");
        CompileSourceBinding.Binding binding = CompileSourceBinding.readHistorical(plan.compileSourceBindingRef());
        require(binding.retainedSourceActualRef().equals(plan.retainedSourceActualRef())
                && binding.compileSourceRoot().equals(plan.compileSourceRoot()), "Exact shared compile-source binding required");
        // Historical retained Source and current Binding/ENV qualify their producers independently.
        CompileSourceBinding.sourceActual(binding);
        NativeBridgeBuild.Actual environment = NativeBridgeBuild.readAccepted(plan.environmentActualRef(), NativeBridgeBuild.Stage.ENV);
        NativeBridgeBuild.Request request = NativeBridgeBuild.readRequest(environment.requestRef());
        requireCurrentEnvironmentBinding(plan,binding,request);
        ControlBuild.FileRef operation = ControlBuild.FileRef.measure(operationSource);
        require(tools.sourcePins().contains(operation), "Qualified fixture operation source required");
        var sources = new ArrayList<>(CompileSourceBinding.retainedSources(binding));
        sources.addAll(List.of(planRef, operation, plan.retainedSourceActualRef(), plan.compileSourceBindingRef(),
                plan.environmentActualRef(), environment.requestRef(), plan.qualifiedToolsBuildRef()));
        List<ControlBuild.FileRef> runtime = ControlBuild.producerClosure();
        List<ControlBuild.FileRef> pins = mergeToolRefs(request.tools().references(), environment.toolRefs());
        verify(sources); verify(pins); verify(runtime);
        return new CurrentInputs(plan, binding, environment, request, sorted(sources), sorted(pins), runtime);
    }
    /** Content matching after real ENV qualification; historical matching never opens mutable compile files. */
    static void requireCurrentEnvironmentBinding(CurrentFixturePlan plan,CompileSourceBinding.Binding binding,
            NativeBridgeBuild.Request request) throws IOException {
        require(NativeBridgeBuild.BOUND_REQUEST_SCHEMA.equals(request.schema()) && request.stage()==NativeBridgeBuild.Stage.ENV
                && request.machineId().equals(plan.machineId()) && binding.machineId().equals(plan.machineId())
                && request.qualifiedToolsBuild().equals(plan.qualifiedToolsBuildRef())
                && binding.producerToolsBuildRef().equals(plan.qualifiedToolsBuildRef())
                && plan.compileSourceBindingRef().equals(request.compileSourceBindingRef())
                && binding.retainedSourceActualRef().equals(plan.retainedSourceActualRef())
                && binding.compileSourceRoot().equals(plan.compileSourceRoot())
                && request.sourceRoot().equals(binding.compileSourceRoot())
                && request.completeSources().equals(CompileSourceBinding.compileSources(binding))
                && request.canonicalRepository().equals(plan.canonicalRepository())
                && request.buildRoot().equals(plan.buildRoot()) && request.definitions().equals(plan.definitions()),
                "Fixture bound ENV/source/options/build differ");
    }
    private static EnvironmentPreparation prepareCurrentAdmission(Path planPath, Path toolsReceipt,
            Path operationSource, Path outputManifest) throws IOException {
        var tools = readCompletedToolsReceipt(toolsReceipt);
        CurrentInputs inputs = currentInputs(planPath, operationSource, tools);
        require(inputs.plan().qualifiedToolsBuildRef().equals(ControlBuild.FileRef.measure(toolsReceipt)),
                "Admission tools input differs from exact current plan");
        CompileSourceBinding.observeLive(inputs.binding());
        require(outputManifest.toAbsolutePath().normalize().equals(inputs.plan().scratchRoot().resolve("BASE-SOURCE-MANIFEST09.json")),
                "Exact current fixture admission output required");
        SharedSourceFiles.plainAncestors(outputManifest);
        require(Files.isDirectory(outputManifest.getParent(), LinkOption.NOFOLLOW_LINKS), "Admitted existing fixture metadata parent required");
        publish(outputManifest, new SourceManifest("xar.native-stage-source-manifest/v1", MACHINE, Instant.now().toString(),
                inputs.sources(), inputs.tools(), inputs.runtime()));
        return new EnvironmentPreparation("xar.native-environment-preparation/v1", MACHINE, Instant.now().toString(),
                EnvironmentPreparationStatus.PREPARED_NOT_AUTHORIZED, ControlBuild.FileRef.measure(planPath),
                ControlBuild.FileRef.measure(toolsReceipt), ControlBuild.FileRef.measure(operationSource),
                ControlBuild.FileRef.measure(outputManifest), ENV_MEMORY, ENV_SCRATCH_CAP);
    }
    private static Context prepareCurrent(Config config, ResourceCard card, ControlBuild.BuildReceipt tools) throws IOException {
        require(card.allowedStage() == config.stage() && Set.of(Stage.BUILD, Stage.REGISTER, Stage.COMBAT).contains(config.stage()),
                "Current fixture authority belongs to another stage");
        CurrentInputs inputs = currentInputs(config.plan(), config.operationSource(), tools);
        CurrentFixturePlan plan = inputs.plan();
        requireCurrentStage(plan,config.stage());
        require(card.owner().equals(plan.ownerTask()) && card.toolsReceiptRef().equals(plan.qualifiedToolsBuildRef())
                && card.packageRequestRef().equals(ControlBuild.FileRef.measure(config.plan()))
                && card.sourceManifestRef().equals(ControlBuild.FileRef.measure(plan.scratchRoot().resolve("BASE-SOURCE-MANIFEST09.json"))),
                "Fixture card differs from the source/build plan");
        for (ControlBuild.FileRef pin : List.of(card.releaseRef(), card.partReallocationRef(), card.toolsReceiptRef(),
                card.toolsAcceptedReadbackRef(), card.packageRequestRef(), card.sourceManifestRef())) pin.verify();
        verify(card.requiredPriorActualRefs());
        JsonNode release = read(Path.of(card.releaseRef().path()), 262144);
        require(MACHINE.equals(text(release, "machine_id"))
                && !Instant.parse(card.reviewAtUtc()).isAfter(Instant.parse(text(release, "review_at_utc"))),
                "Fixture card extends capacity");
        for (String name : card.outputRoots()) {
            Path root = Path.of(name).toAbsolutePath().normalize();
            require(root.startsWith(plan.buildRoot()) || root.startsWith(plan.scratchRoot()), "Fixture output escapes roots");
        }
        require(card.outputRoots().stream().map(Path::of).anyMatch(plan.buildRoot()::equals)
                && card.outputRoots().stream().map(Path::of).anyMatch(plan.scratchRoot()::equals), "Both current fixture roots must be admitted");
        ProjectStoragePolicy.requireBulkOutput(plan.buildRoot()); ProjectStoragePolicy.requireBulkOutput(plan.scratchRoot());
        SourceManifest admission = JSON.readValue(bytes(Path.of(card.sourceManifestRef().path()), 2097152), SourceManifest.class);
        require(admission.schema().equals("xar.native-stage-source-manifest/v1") && admission.machineId().equals(MACHINE)
                && admission.sourceRefs().equals(inputs.sources()) && admission.toolRefs().equals(inputs.tools())
                && admission.operationRuntimeRefs().equals(inputs.runtime()), "Complete actual fixture admission changed");
        Instant now = Instant.now(), deadline = now.plusSeconds(card.timeoutSeconds()), review = Instant.parse(card.reviewAtUtc());
        if (review.isBefore(deadline)) deadline = review;
        require(!now.isBefore(Instant.parse(card.observedAtUtc())) && now.isBefore(deadline), "Current fixture stage expired or not yet opened");
        Map<String,String> env = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        var snapshot = NativeBuildEnvironment.read(inputs.environmentRequest().stageRoot(), MACHINE,
                bytes(Path.of(inputs.environment().snapshotRef().path()), 65536));
        env.putAll(snapshot.values()); for (String key : List.of("TEMP","TMP","TMPDIR")) env.put(key, plan.scratchRoot().toString());
        env.put("PYTHONDONTWRITEBYTECODE","1"); env.put("VSCMD_SKIP_SENDTELEMETRY","1");
        List<SharedSourceFiles.Witness> before = config.stage() == Stage.BUILD ? CompileSourceBinding.observeLive(inputs.binding()) : List.of();
        return new Context(config, deadline, card, ControlBuild.FileRef.measure(config.resourceCard()), plan.qualifiedToolsBuildRef(),
                CURRENT_JSON.valueToTree(plan), inputs.sources(), inputs.tools(), inputs.runtime(), Map.copyOf(env),
                plan, inputs.binding(), before, inputs.environment());
    }
    private static void guardCurrent(Context context) throws IOException {
        context.cardRef().verify(); context.card().releaseRef().verify();
        require(Instant.now().isBefore(context.deadline()), "Current fixture resource card expired");
        require(footprint(context.buildRoot()) <= context.current().buildAllocationLimitBytes()
                && footprint(context.scratchRoot()) <= context.card().scratchLimitBytes(), "Current fixture allocation exhausted");
        verify(context.sourceRefs());
    }
    static void prepareCurrentCMakeQuery(CurrentFixturePlan plan, List<ControlBuild.FileRef> qualifiedToolRefs) throws IOException {
        NativeBridgeBuild.requireReusableCMakeCache(plan.compileSourceRoot(), plan.buildRoot(),
                toolRef(qualifiedToolRefs, "cl.exe"), toolRef(qualifiedToolRefs, "ninja.exe"));
        Path query = plan.buildRoot().resolve(".cmake/api/v1/query"); Files.createDirectories(query);
        for (String name : List.of("codemodel-v2","cmakeFiles-v1")) {
            Path path = query.resolve(name);
            if (!Files.exists(path, LinkOption.NOFOLLOW_LINKS)) Files.createFile(path);
            else require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(path) && Files.size(path)==0,
                    "Exact empty regular File API query required");
        }
    }
    private static void configureCurrent(Context context) throws IOException, InterruptedException {
        CurrentFixturePlan plan = context.current();
        guard(context);
        prepareCurrentCMakeQuery(plan, context.toolRefs());
        Path cache = plan.buildRoot().resolve("CMakeCache.txt");
        List<String> argv = new ArrayList<>(List.of("-S", plan.compileSourceRoot().toString(), "-B", plan.buildRoot().toString(),
                "-G","Ninja","-U","XAR_*","-DBUILD_TESTING=ON","-DCMAKE_BUILD_TYPE=Release","-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                "-DCMAKE_MAKE_PROGRAM="+tool(context,"ninja.exe"),"-DCMAKE_CXX_COMPILER="+tool(context,"cl.exe"),
                "-DCMAKE_C_COMPILER="+tool(context,"cl.exe")));
        plan.definitions().forEach(value -> argv.add("-D"+value.option()+"="+value.value().name()));
        manifest(context, "BASE-SOURCE-MANIFEST09.json", context.sourceRefs());
        command(context, CONFIGURE_ID, tool(context,"cmake.exe"), argv, plan.scratchRoot(), nativeEnvironment(context), 180,
                environmentRef(context), null, plan.target().usesRuntime()
                        ? List.of(cache,plan.buildRoot().resolve("ck3_12002_runtime_sources.txt")) : List.of(cache), List.of());
    }
    private static Path actualPath(Context context, String id) { return context.scratchRoot().resolve(id+".actual.json"); }
    private static Path resolveSource(Context context, String name) {
        Path path = Path.of(name); return (path.isAbsolute() ? path : context.sourceRoot().resolve(path)).toAbsolutePath().normalize();
    }
    private static List<ControlBuild.FileRef> retainedProjectPins(Context context, List<ControlBuild.FileRef> pins) throws IOException {
        var result = new ArrayList<ControlBuild.FileRef>();
        for (ControlBuild.FileRef pin : pins) result.add(context.current()!=null && Path.of(pin.path()).startsWith(context.sourceRoot())
                ? CompileSourceBinding.retainedFor(context.binding(), pin) : pin);
        return sorted(result.stream().distinct().toList());
    }
    private static Actual accepted(Context context, String id) throws IOException {
        for (ActualStage stage : ActualStage.values()) if (stage.wireId().equals(id)) return readActual(actualPath(context,id),stage);
        throw new IOException("Unknown exact fixture stage: "+id);
    }
    private static Graph acceptedGraph(Context context) throws IOException {
        return context.current()==null?acceptedGraph():currentGraph(context.current(),ControlBuild.FileRef.measure(context.config().plan()));
    }
    private static Path primaryArtifact(Context context,Target target) throws IOException {
        return context.current()==null?configuredPrimaryArtifact(BUILD,target.name(),target.type(),target.artifacts())
                :currentPrimaryArtifact(context.buildRoot(),target);
    }
    private static Map<String,String> nativeEnvironment(Context context) throws IOException {
        return context.current()==null?nativeEnvironment():context.baseEnv();
    }
    private static ControlBuild.FileRef environmentRef(Context context) throws IOException {
        return context.current()==null?environmentRef():context.environment().snapshotRef();
    }
    private static List<ControlBuild.FileRef> artifactRefs(Context context) throws IOException {
        if(context.current()==null)return artifactRefs();
        var refs=new ArrayList<ControlBuild.FileRef>();
        for(Target target:acceptedGraph(context).targets())if(target.name().equals(context.current().target().targetName()))refs.add(ControlBuild.FileRef.measure(primaryArtifact(context,target)));
        return sorted(refs);
    }
    private static void acceptedCompilerDependencies(Context context) throws IOException {
        Actual actual=accepted(context,"compiler-active-dependencies");
        Dependencies dependencies=parseDependencies(bytes(context.scratchRoot().resolve("ACTUAL-COMPILER-DEPENDENCIES01.json"),2097152));
        require(dependencies.rawRef().equals(actual.stdoutRef()),"Actual compiler dependency source differs"); dependencies.rawRef().verify();
        for(var pin:retainedProjectPins(context,dependencies.dependencyRefs()))pin.verify();
    }

    public record CurrentSourceTerminal(String schema, String stageId, SharedSourceFiles.Witness bindingWitness,
            List<SharedSourceFiles.Witness> before, List<SharedSourceFiles.Witness> after, MsvcAuxiliaryPolicy.Outcome auxiliary) {
        public CurrentSourceTerminal {
            boolean commander="xar.current-fixture-source-terminal/v1".equals(schema)
                    && Set.of(CONFIGURE_ID,ActualStage.COMBATROLES_TARGET_BUILD.wireId()).contains(stageId);
            boolean holy="xar.current-fixture-source-terminal/v2".equals(schema)
                    && Set.of(CONFIGURE_ID,ActualStage.HOLY_FIXTURE_TARGET_BUILD.wireId()).contains(stageId);
            if (!commander && !holy)
                throw new IllegalArgumentException("Exact current fixture compiler command required");
            before=List.copyOf(before); after=List.copyOf(after);
        }
    }
    static void requireCurrentSourceTerminal(CurrentSourceTerminal proof, CompileSourceBinding.Binding binding,
            ControlBuild.FileRef bindingRef, Actual actual, NativeBridgeBuild.Actual environment) throws IOException {
        require(proof.stageId().equals(actual.stageId()) && proof.bindingWitness().source().equals(bindingRef)
                && SharedSourceFiles.observe(Path.of(bindingRef.path())).equals(proof.bindingWitness())
                && !proof.before().isEmpty() && proof.before().equals(proof.after())
                && proof.before().size()==CompileSourceBinding.compileSources(binding).size()
                && new HashSet<>(proof.before().stream().map(SharedSourceFiles.Witness::source).toList())
                    .equals(new HashSet<>(CompileSourceBinding.compileSources(binding))), "Incomplete original compile identities");
        Set<String> retainedIds=binding.rows().stream().map(row->row.retainedWitness().nativeFile())
                .map(file->file.volumeSerialDecimal()+":"+file.fileIdDecimal()).collect(java.util.stream.Collectors.toSet());
        require(proof.before().stream().map(SharedSourceFiles.Witness::nativeFile)
                .noneMatch(file->retainedIds.contains(file.volumeSerialDecimal()+":"+file.fileIdDecimal())),
                "Compile identities cannot alias the retained snapshot");
        var outcome=proof.auxiliary(); var request=NativeBridgeBuild.readRequest(environment.requestRef());
        require(outcome!=null && outcome.completed() && outcome.originalRoot().identity().equals(actual.ownerIdentity())
                && actual.result().passed() && outcome.binding().toolchain().equals(NativeBridgeBuild.environmentCompilerBinding(environment)),
                "MSVC root/compiler/Job terminal differ");
        outcome.binding().requireRequest(ControlBuild.FileRef.measure(Path.of(actual.command().getFirst())),actual.toolRefs());
        outcome.binding().toolchain().requireCompiler(request.tools().compiler());
    }
    public static ResourceCard currentFixtureCard(ControlBuild.FileRef ref) throws IOException {
        ref.verify(); ResourceCard card=JSON.readValue(bytes(Path.of(ref.path()),262144),ResourceCard.class);
        require(CURRENT_CARD_SCHEMA.equals(card.schema()),"Explicit current fixture card required"); return card;
    }
    private static void readCurrentActual(Actual actual) throws IOException {
        ResourceCard card=currentFixtureCard(actual.resourceCardRef());
        CurrentFixturePlan plan=readCurrentPlan(card.packageRequestRef());
        var binding=CompileSourceBinding.readHistorical(plan.compileSourceBindingRef());
        require(binding.retainedSourceActualRef().equals(plan.retainedSourceActualRef())
                && binding.compileSourceRoot().equals(plan.compileSourceRoot())
                && card.owner().equals(plan.ownerTask()) && card.toolsReceiptRef().equals(plan.qualifiedToolsBuildRef())
                && actual.toolsReceiptRef().equals(plan.qualifiedToolsBuildRef())
                && !Instant.parse(actual.observedAtUtc()).isAfter(Instant.parse(card.reviewAtUtc()))
                && !Instant.parse(actual.observedAtUtc()).isAfter(Instant.parse(actual.stageDeadlineAtUtc())),
                "Fixture plan/owner/window differs");
        CompileSourceBinding.sourceActual(binding);
        require(Path.of(actual.stdoutRef().path()).equals(plan.scratchRoot().resolve(actual.stageId()+".stdout.log"))
                && Path.of(actual.stderrRef().path()).equals(plan.scratchRoot().resolve(actual.stageId()+".stderr.log"))
                && actual.result().accounting().memoryLimitBytes()==card.memoryLimitBytes()
                && !Instant.parse(actual.stageDeadlineAtUtc()).isAfter(Instant.parse(card.reviewAtUtc()))
                && !Instant.parse(actual.observedAtUtc()).isBefore(Instant.parse(card.observedAtUtc())),
                "Fixture source/terminal authority differs");
        Stage stage=actual.stageId().equals("combatroles-producer")?Stage.COMBAT:Stage.BUILD;
        requireCurrentStage(plan,stage);
        require(card.allowedStage()==stage && Set.of(CONFIGURE_ID,"configured-commands",plan.target().buildStage().wireId(),
                "compiler-active-dependencies","combatroles-producer").contains(actual.stageId()),"Wrong current fixture stage");
        verify(List.of(card.releaseRef(),card.partReallocationRef(),card.toolsAcceptedReadbackRef(),card.sourceManifestRef()));
        verify(card.requiredPriorActualRefs());
        SourceManifest manifest=JSON.readValue(bytes(Path.of(actual.sourceManifestRef().path()),2097152),SourceManifest.class);
        require(manifest.sourceRefs().containsAll(CompileSourceBinding.retainedSources(binding))
                && manifest.sourceRefs().containsAll(List.of(card.packageRequestRef(),plan.compileSourceBindingRef(),
                    plan.retainedSourceActualRef(),plan.environmentActualRef(),plan.qualifiedToolsBuildRef())),
                "Incomplete fixture retained-source manifest");
        var environment=NativeBridgeBuild.readAccepted(plan.environmentActualRef(),NativeBridgeBuild.Stage.ENV);
        requireCurrentEnvironmentBinding(plan,binding,NativeBridgeBuild.readRequest(environment.requestRef()));
        require(actual.environmentRef().equals(environment.snapshotRef()),"Original current fixture ENV differs");
        if(plan.target()!=FixtureTarget.COMBATROLES_COMMANDER && actual.configuredGraphRef()!=null) {
            Path graphPath=plan.scratchRoot().resolve("CONFIGURED-GRAPH01.json");
            require(actual.configuredGraphRef().equals(ControlBuild.FileRef.measure(graphPath)),
                    "Holy actual must bind its own configured target graph");
            requireCurrentGraphShape(plan,JSON.readValue(bytes(graphPath,2097152),Graph.class));
        }
        if(actual.stageId().equals(plan.target().buildStage().wireId()))
            require(actual.command().equals(List.of(NativeBridgeBuild.readRequest(environment.requestRef()).tools().cmake().path(),
                    "--build",plan.buildRoot().toString(),"--target",plan.target().targetName(),"--parallel",Integer.toString(plan.parallelJobs()),"--verbose"))
                    && Path.of(actual.cwd()).equals(plan.scratchRoot()),"Exact selected single-fixture build command");
        if (Set.of(CONFIGURE_ID,plan.target().buildStage().wireId()).contains(actual.stageId())) {
            Path path=plan.scratchRoot().resolve(actual.stageId()+".source-terminal.json");
            require(actual.outputRefs().contains(ControlBuild.FileRef.measure(path)),"Original current source terminal missing");
            var terminal=CURRENT_JSON.readValue(bytes(path,16<<20),CurrentSourceTerminal.class);
            require(terminal.schema().equals(terminalSchema(plan)),"Compiler terminal belongs to another plan version");
            requireCurrentSourceTerminal(terminal,binding,plan.compileSourceBindingRef(),actual,environment);
        }
        if(actual.stageId().equals("combatroles-producer")) {
            Actual build=readActual(plan.scratchRoot().resolve("combatroles-target-build.actual.json"),ActualStage.COMBATROLES_TARGET_BUILD);
            require(card.requiredPriorActualRefs().contains(ControlBuild.FileRef.measure(plan.scratchRoot().resolve("combatroles-target-build.actual.json"))),
                    "COMBAT must bind its exact original single-target build");
            requireCurrentRegistration(plan,card,build);
        }
    }

    public record CurrentFixtureRegistrationInputs(CurrentFixturePlan plan, ControlBuild.FileRef fixturePlanRef,
            ControlBuild.FileRef cardRef, ControlBuild.FileRef buildActualRef, ControlBuild.FileRef executableRef,
            List<ControlBuild.FileRef> inputs) {
        public CurrentFixtureRegistrationInputs { inputs=List.copyOf(inputs); }
    }
    public static CurrentFixtureRegistrationInputs currentRegistrationInputs(ControlBuild.FileRef planRef,
            ControlBuild.FileRef cardRef, ControlBuild.FileRef buildRef) throws IOException {
        var value=readHistoricalCurrentRegistrationInputs(planRef,cardRef,buildRef); revalidateCurrentRegistration(value); return value;
    }
    public static CurrentFixtureRegistrationInputs readHistoricalCurrentRegistrationInputs(ControlBuild.FileRef planRef,
            ControlBuild.FileRef cardRef, ControlBuild.FileRef buildRef) throws IOException {
        CurrentFixturePlan plan=readCurrentPlan(planRef); ResourceCard card=currentFixtureCard(cardRef);
        require(card.allowedStage()==Stage.REGISTER && card.packageRequestRef().equals(planRef)
                && card.toolsReceiptRef().equals(plan.qualifiedToolsBuildRef()) && card.requiredPriorActualRefs().contains(buildRef)
                && Path.of(buildRef.path()).equals(currentBuildActualPath(plan)),
                "Exact current single-target BUILD and REGISTER card required");
        Actual build=readActual(Path.of(buildRef.path()),plan.target().buildStage());
        require(currentFixtureCard(build.resourceCardRef()).packageRequestRef().equals(planRef),"Another fixture build plan");
        Graph graph=currentGraph(plan,planRef); Target target=graph.targets().stream().filter(row->row.name().equals(plan.target().targetName())).findFirst().orElseThrow();
        Path executable=currentPrimaryArtifact(plan.buildRoot(),target);
        var executableRefs=build.outputRefs().stream().filter(ref->Path.of(ref.path()).equals(executable)).toList();
        require(executableRefs.size()==1,"One original built selected fixture EXE required");ControlBuild.FileRef exe=executableRefs.getFirst();
        require(build.outputRefs().contains(exe),"Actual single-target build omitted its declared fixture EXE");
        var inputs=new ArrayList<>(CompileSourceBinding.retainedSources(CompileSourceBinding.readHistorical(plan.compileSourceBindingRef())));
        inputs.addAll(List.of(planRef,cardRef,buildRef,exe,plan.qualifiedToolsBuildRef(),plan.compileSourceBindingRef(),
                plan.retainedSourceActualRef(),plan.environmentActualRef(),build.sourceManifestRef(),build.configuredGraphRef()));
        inputs.addAll(build.toolRefs()); inputs.addAll(build.outputRefs()); inputs.addAll(graph.configuredInputRefs()); inputs.addAll(graph.configuredToolRefs());
        inputs.addAll(card.requiredPriorActualRefs()); inputs.addAll(List.of(card.releaseRef(),card.partReallocationRef(),card.toolsAcceptedReadbackRef(),card.sourceManifestRef()));
        verifyCurrentRefs(plan,planRef,inputs.stream().distinct().toList()); return new CurrentFixtureRegistrationInputs(plan,planRef,cardRef,buildRef,exe,immutableCurrentRefs(plan,planRef,inputs));
    }
    public static void revalidateCurrentRegistration(CurrentFixtureRegistrationInputs inputs) throws IOException {
        verifyCurrentRefs(inputs.plan(),inputs.fixturePlanRef(),inputs.inputs());verifyCurrentLiveGenerated(inputs.plan(),inputs.fixturePlanRef());
        ResourceCard card=currentFixtureCard(inputs.cardRef()); Instant now=Instant.now();
        require(!now.isBefore(Instant.parse(card.observedAtUtc())) && now.isBefore(Instant.parse(card.reviewAtUtc()))
                && MACHINE.equals(WindowsJobProcess.currentMachineId()),"Fixture REGISTER authority unavailable");
        JsonNode release=read(Path.of(card.releaseRef().path()),262144);
        require(MACHINE.equals(text(release,"machine_id")) && !Instant.parse(card.reviewAtUtc()).isAfter(Instant.parse(text(release,"review_at_utc"))),
                "Fixture REGISTER cannot extend its real capacity release");
        var plan=inputs.plan(); var binding=CompileSourceBinding.readHistorical(plan.compileSourceBindingRef());
        var terminal=CURRENT_JSON.readValue(bytes(plan.scratchRoot().resolve(plan.target().buildStage().wireId()+".source-terminal.json"),16<<20),CurrentSourceTerminal.class);
        CompileSourceBinding.assertLiveUnchanged(binding,terminal.after());
        require(footprint(plan.buildRoot())<=plan.buildAllocationLimitBytes() && footprint(plan.scratchRoot())<=card.scratchLimitBytes(),
                "Current fixture REGISTER allocation exhausted");
    }
    private static Graph currentGraph(CurrentFixturePlan plan,ControlBuild.FileRef planRef) throws IOException {
        Actual configured=readActual(plan.scratchRoot().resolve(CONFIGURE_ID+".actual.json"),ActualStage.CONFIGURE_NEXT01);
        Graph graph=JSON.readValue(bytes(plan.scratchRoot().resolve("CONFIGURED-GRAPH01.json"),2097152),Graph.class);
        requireCurrentGraphShape(plan,graph);
        require(graph.configureReceiptRef().equals(ControlBuild.FileRef.measure(plan.scratchRoot().resolve(CONFIGURE_ID+".actual.json")))
                && currentFixtureCard(configured.resourceCardRef()).packageRequestRef().equals(planRef),"Exact current configured target graph required");
        verifyCurrentRefs(plan,planRef,graph.configuredInputRefs()); verify(graph.configuredToolRefs()); verifyCurrentRefs(plan,planRef,graph.projectSourceRefs());
        if(graph.runtimeSourcesRef()!=null)verifyCurrentRefs(plan,planRef,List.of(graph.runtimeSourcesRef()));
        return graph;
    }
    static void requireCurrentStage(CurrentFixturePlan plan,Stage stage) throws IOException {
        require(stage==Stage.BUILD || stage==Stage.REGISTER
                || stage==Stage.COMBAT && plan.target()==FixtureTarget.COMBATROLES_COMMANDER,
                "Holy fixture plans grant BUILD/REGISTER only; COMBAT requires Commander v1");
    }
    private static String graphSchema(CurrentFixturePlan plan) {
        return plan.target()==FixtureTarget.COMBATROLES_COMMANDER
                ? "xar.native-configured-selected-graph/v2" : "xar.native-configured-selected-graph/v3";
    }
    private static String terminalSchema(CurrentFixturePlan plan) {
        return plan.target()==FixtureTarget.COMBATROLES_COMMANDER
                ? "xar.current-fixture-source-terminal/v1" : "xar.current-fixture-source-terminal/v2";
    }
    private static String retentionSchema(CurrentFixturePlan plan) {
        return plan.target()==FixtureTarget.COMBATROLES_COMMANDER
                ? "xar.current-fixture-retained-stage-files/v1" : "xar.current-fixture-retained-stage-files/v2";
    }
    private static List<String> retentionStages(CurrentFixturePlan plan) {
        return List.of(CONFIGURE_ID,"configured-graph",plan.target().buildStage().wireId());
    }
    private static Path currentBuildActualPath(CurrentFixturePlan plan) {
        return plan.scratchRoot().resolve(plan.target().buildStage().wireId()+".actual.json");
    }
    /** Shared by the actual File API producer and historical reader; this grants no command terminal. */
    static void requireCurrentGraphShape(CurrentFixturePlan plan,Graph graph) throws IOException {
        FixtureTarget selected=plan.target();
        require(graph!=null && graphSchema(plan).equals(graph.schema()) && MACHINE.equals(graph.machineId())
                && graph.status()==GraphStatus.CONFIGURED_SOURCE_FROZEN_NOT_BUILT
                && graph.targets().size()==selected.closureNames().size()
                && graph.targets().stream().map(Target::name).collect(java.util.stream.Collectors.toSet()).equals(selected.closureNames())
                && graph.targets().stream().map(Target::id).distinct().count()==graph.targets().size(),
                "Exact versioned single-fixture target closure required");
        Target executable=graph.targets().stream().filter(row->row.name().equals(selected.targetName())).findFirst().orElseThrow();
        require(executable.type()==TargetType.EXECUTABLE,"Selected fixture must be an executable");
        if(selected.usesRuntime()) {
            Target runtime=graph.targets().stream().filter(row->row.name().equals(RUNTIME)).findFirst().orElseThrow();
            require(runtime.type()==TargetType.STATIC_LIBRARY && graph.runtimeSourcesRef()!=null
                    && graph.runtimeTranslationUnitCount()>0
                    && graph.runtimeTranslationUnitCount()==runtime.translationUnits().size(),
                    "Actual runtime source list and translation units required");
            if(selected!=FixtureTarget.COMBATROLES_COMMANDER)
                require(executable.dependencyIds().equals(List.of(runtime.id())) && runtime.dependencyIds().isEmpty(),
                        "Holy runtime closure must contain exactly the selected executable and dependency-free runtime");
        } else require(graph.runtimeSourcesRef()==null && graph.runtimeTranslationUnitCount()==0
                && executable.dependencyIds().isEmpty(),"Standalone Holy fixture cannot import a runtime closure");
        if(selected!=FixtureTarget.COMBATROLES_COMMANDER) {
            Set<Path> expected=selected.sourceRelativePaths().stream().map(plan.compileSourceRoot()::resolve)
                    .collect(java.util.stream.Collectors.toSet());
            require(executable.translationUnits().size()==expected.size()
                    && executable.translationUnits().stream().map(ref->Path.of(ref.path())).collect(java.util.stream.Collectors.toSet()).equals(expected),
                    "Exact Holy target translation units required");
            Set<String> required=selected.usesRuntime()
                    ? (selected==FixtureTarget.HOLY_ORDER_HIRE_COST_CONTEXT ? Set.of("NOMINMAX","NDEBUG") : Set.of("NOMINMAX"))
                    : Set.of("NOMINMAX","XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1");
            require(!executable.compileGroups().isEmpty()
                    && executable.compileGroups().stream().allMatch(group->"CXX".equals(group.language()) && group.definitions().containsAll(required)),
                    "Actual target-specific Holy compiler definitions required");
        }
    }
    static Path currentPrimaryArtifact(Path buildRoot,Target target) throws IOException {
        boolean executable=java.util.Arrays.stream(FixtureTarget.values()).anyMatch(value->value.targetName().equals(target.name()));
        require((executable || RUNTIME.equals(target.name())) && target.type()==(executable?TargetType.EXECUTABLE:TargetType.STATIC_LIBRARY),
                "Only a finite declared fixture executable or its runtime library is allowed");
        String name=target.name()+(target.type()==TargetType.EXECUTABLE?".exe":".lib");
        List<Path> matches=target.artifacts().stream().map(Path::of).map(path->path.toAbsolutePath().normalize())
                .filter(path->path.getFileName().toString().equals(name)).toList();
        require(matches.size()==1 && matches.getFirst().startsWith(buildRoot),"One exact configured current primary artifact required");
        Path primary=matches.getFirst(); Set<Path> allowed=Set.of(primary,primary.resolveSibling(target.name()+".pdb"));
        Set<Path> observed=new HashSet<>();
        for(String nameValue:target.artifacts()) {
            Path path=Path.of(nameValue);
            require(path.isAbsolute() && path.equals(path.normalize()) && allowed.contains(path) && observed.add(path),
                    "Foreign or duplicate primary/PDB artifact");
        }
        return primary;
    }
    private static ObjectNode currentFixtureManifest(CurrentFixtureRegistrationInputs inputs) throws IOException {
        var plan=inputs.plan(); Graph graph=currentGraph(plan,inputs.fixturePlanRef());
        Target target=graph.targets().stream().filter(row->row.name().equals(plan.target().targetName())).findFirst().orElseThrow();
        ObjectNode root=JSON.createObjectNode();root.put("schema","xar.project-exe-exclusions.v1");
        root.put("repo",plan.canonicalRepository().toRealPath().toString());root.put("source_dir",plan.compileSourceRoot().toString());
        root.put("build_dir",plan.buildRoot().toString());root.put("configuration","Release");
        root.set("requested_targets",JSON.valueToTree(List.of(plan.target().targetName())));root.put("external_candidate","java-native-launch-reviewed-source");
        for(String kind:List.of("index-","codemodel-")) {
            var refs=graph.configuredInputRefs().stream().filter(ref->Path.of(ref.path()).getFileName().toString().startsWith(kind)).toList();
            require(refs.size()==1,"Unique actual File API provenance required");root.set(kind.equals("index-")?"cmake_index":"cmake_codemodel",shortRef(refs.getFirst()));
        }
        ObjectNode provenance=root.putArray("target_provenance").addObject();
        provenance.put("path",target.definitionRef().path());provenance.put("sha256",target.definitionRef().sha256());
        provenance.put("target",plan.target().targetName());provenance.put("target_id",target.id());
        Path targetSource=plan.compileSourceRoot().resolve(text(read(Path.of(retainedFile(plan,inputs.fixturePlanRef(),target.definitionRef()).retained().source().path()),2097152).get("paths"),"source")).normalize();
        require(targetSource.startsWith(plan.compileSourceRoot()),"Foreign actual CMake executable source");
        provenance.put("source",targetSource.toString());
        ObjectNode file=root.putArray("files").addObject();var exe=inputs.executableRef();verifyCurrentRefs(plan,inputs.fixturePlanRef(),List.of(exe));
        file.put("path",exe.path());file.put("size",exe.bytes());file.put("sha256",exe.sha256());file.put("target",plan.target().targetName());file.put("target_id",target.id());
        return root;
    }
    public static ControlBuild.FileRef prepareCurrentFixtureManifest(CurrentFixtureRegistrationInputs inputs,Path output) throws IOException {
        revalidateCurrentRegistration(inputs);
        require(output.equals(inputs.plan().scratchRoot().resolve("BUILT-FIXTURE-MANIFEST01.json")),"Exact finite current fixture manifest output required");
        publish(output,currentFixtureManifest(inputs));return ControlBuild.FileRef.measure(output);
    }
    public static void requireCurrentFixtureManifest(CurrentFixtureRegistrationInputs inputs,ControlBuild.FileRef manifest) throws IOException {
        manifest.verify();require(Path.of(manifest.path()).equals(inputs.plan().scratchRoot().resolve("BUILT-FIXTURE-MANIFEST01.json"))
                && read(Path.of(manifest.path()),2097152).equals(currentFixtureManifest(inputs)),"Fixture manifest differs from actual graph/EXE");
    }
    private static List<ControlBuild.FileRef> requireCurrentRegistration(CurrentFixturePlan plan,ResourceCard card,Actual build) throws IOException {
        var matches=new ArrayList<ControlBuild.FileRef>();
        for(var ref:card.requiredPriorActualRefs())if("xar.native-built-fixture-uac-result/v1".equals(read(Path.of(ref.path()),32 << 20).path("schema").asText()))matches.add(ref);
        require(matches.size()==1,"One exact completed built-fixture registration required");
        var resultRef=matches.getFirst();JsonNode raw=read(Path.of(resultRef.path()),32 << 20);
        var planRef=JSON.treeToValue(raw.get("plan_ref"),ControlBuild.FileRef.class);
        var result=NativeProjectExeUac.readCurrentFixtureRegistrationResult(planRef,resultRef);
        require(result.fixturePlanRef().equals(card.packageRequestRef())
                && result.buildActualRef().equals(ControlBuild.FileRef.measure(currentBuildActualPath(plan)))
                && build.outputRefs().contains(result.executableRef()),"Registered fixture belongs to another actual build");
        return List.of(resultRef,planRef);
    }
    private static List<ControlBuild.FileRef> requireCurrentRegistration(Context context) throws IOException {
        return requireCurrentRegistration(context.current(),context.card(),accepted(context,context.current().target().buildStage().wireId()));
    }

    private static Context prepare(Config config) throws IOException {
        return prepare(config, null);
    }

    private static Context prepare(Config config, Instant reviewedRegistrationDeadline) throws IOException {
        require(MACHINE.equals(WindowsJobProcess.currentMachineId()), "actual native machine mismatch");
        ControlBuild.BuildReceipt tools = readCompletedToolsReceipt(config.toolsReceipt());
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, "qualified shared tools runtime required");
        ResourceCard card = JSON.readValue(bytes(config.resourceCard(), 262144), ResourceCard.class);
        if (CURRENT_CARD_SCHEMA.equals(card.schema())) return prepareCurrent(config, card, tools);
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
        if (Set.of(CURRENT_PLAN_SCHEMA,CURRENT_HOLY_PLAN_SCHEMA).contains(read(planPath, 262144).path("schema").asText()))
            return prepareCurrentAdmission(planPath, toolsReceipt, operationSource, outputManifest);
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
        if (context.current() != null) { configureCurrent(context); return; }
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
        Path SOURCE = context.sourceRoot(), BUILD = context.buildRoot(), SCRATCH = context.scratchRoot();
        List<String> TARGETS = context.targets();
        Actual configured = accepted(context, CONFIGURE_ID);
        Path reply = BUILD.resolve(".cmake/api/v1/reply");
        List<Path> indexes;
        try (var files = Files.list(reply)) { indexes = files.filter(p -> p.getFileName().toString().startsWith("index-") && p.toString().endsWith(".json")).toList(); }
        require(!indexes.isEmpty() && (context.current() != null || indexes.size() == 1), "one current File API index required");
        indexes = indexes.stream().sorted(Comparator.comparing(path -> path.getFileName().toString())).toList();
        Path indexPath = indexes.getLast(); JsonNode index = read(indexPath, 1048576);
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
            String name = text(data, "name"); require(id.equals(text(data, "id"))
                    && (context.current() == null ? Set.of(KINSHIP, COMBAT, RUNTIME) : context.current().target().closureNames()).contains(name), "unexpected selected target closure");
            List<ControlBuild.FileRef> tus = new ArrayList<>();
            for (JsonNode source : array(data, "sources")) {
                if (!source.has("compileGroupIndex")) continue;
                long groupIndex = integer(source, "compileGroupIndex");
                require(data.has("compileGroups") && groupIndex < array(data, "compileGroups").size(), "actual source compile-group index out of range");
                Path path = resolveSource(context, text(source, "path"));
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
        require(targets.size() == (context.current() == null ? 3 : context.current().target().closureNames().size()), "exact selected executable/runtime closure required");
        for (Target target : targets) {
            primaryArtifact(context, target);
        }
        JsonNode cmakeObject = uniqueKind(array(index, "objects"), "cmakeFiles");
        Path cmakePath = confined(reply, text(cmakeObject, "jsonFile")); configuredInputs.add(ControlBuild.FileRef.measure(cmakePath));
        for (JsonNode input : array(read(cmakePath, 2097152), "inputs")) {
            Path path = resolveSource(context, text(input, "path"));
            require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS), "missing configured CMake input: " + path);
            configuredInputs.add(ControlBuild.FileRef.measure(path));
        }
        collectQuoted(quotedRoots, search, sourcePins, SOURCE, BUILD);
        Target runtime = targets.stream().filter(t -> t.name().equals(RUNTIME)).findFirst().orElse(null);
        require(runtime!=null || context.current()!=null && !context.current().target().usesRuntime(),"Expected runtime dependency absent");
        Path runtimeFile = BUILD.resolve("ck3_12002_runtime_sources.txt");
        if(runtime!=null) {
            Set<Path> listed = new HashSet<>();
            for (String line : Files.readAllLines(runtimeFile, StandardCharsets.UTF_8)) if (!line.isBlank()) listed.add(resolveSource(context, line.strip()));
            require(listed.equals(new HashSet<>(runtime.translationUnits().stream().map(r -> Path.of(r.path())).toList())), "generated runtime sources differ from actual target compile sources");
        }
        List<ControlBuild.FileRef> project = retainedProjectPins(context, sourcePins.values().stream().toList());
        configuredInputs = new ArrayList<>(retainedProjectPins(context, configuredInputs));
        verify(project); verify(configuredInputs);
        if(context.current()!=null) {
            var retainedInputs=new ArrayList<>(configuredInputs);retainedInputs.addAll(project);
            if(runtime!=null)retainedInputs.add(ControlBuild.FileRef.measure(runtimeFile));
            configuredInputs.add(retainCurrentStageFiles(context,"configured-graph",retainedInputs));
        }
        List<ControlBuild.FileRef> configuredTools = configuredTools(context);
        Graph graph = new Graph(context.current() == null ? "xar.native-configured-selected-graph/v1" : graphSchema(context.current()), MACHINE, Instant.now().toString(), GraphStatus.CONFIGURED_SOURCE_FROZEN_NOT_BUILT,
                ControlBuild.FileRef.measure(actualPath(context, CONFIGURE_ID)), targets, configuredInputs, configuredTools, project,
                runtime==null?null:ControlBuild.FileRef.measure(runtimeFile), runtime==null?0:runtime.translationUnits().size(), List.of(
                "File API compileGroups and selected translation units are actual configured inputs.",
                "Project quoted include closure is frozen before build; compiler-active dependency paths come from fresh Ninja deps after build.",
                "System headers are post-build actual dependency pins, not claimed as pre-build byte-frozen inputs."));
        if(context.current()!=null)requireCurrentGraphShape(context.current(),graph);
        publish(SCRATCH.resolve("CONFIGURED-GRAPH01.json"), graph);
        manifest(context, "CONFIGURED-SOURCE-MANIFEST01.json", project);
        guard(context);
        require(configured.result().passed(), "configure terminal changed");
        System.out.println("CONFIGURED exact_runtime_translation_units=" + graph.runtimeTranslationUnitCount());
    }

    private static void build(Context context) throws IOException, InterruptedException {
        Path BUILD = context.buildRoot(), SCRATCH = context.scratchRoot();
        Graph graph = acceptedGraph(context); verify(graph.projectSourceRefs()); verify(graph.configuredInputRefs()); verify(graph.configuredToolRefs());
        ControlBuild.FileRef graphRef = ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-GRAPH01.json"));
        Map<String, String> env = nativeEnvironment(context);
        List<String> commands = new ArrayList<>(List.of("-C", BUILD.toString(), "-t", "commands")); commands.addAll(context.targets());
        command(context, "configured-commands", tool(context, "ninja.exe"), commands,
                SCRATCH, env, 120, environmentRef(context), graphRef, List.of(), List.of());
        List<Path> artifacts = new ArrayList<>();
        if (context.current() == null) artifacts.addAll(List.of(BUILD.resolve("lib/" + RUNTIME + ".lib"),
                BUILD.resolve("bin/" + KINSHIP + ".exe"), BUILD.resolve("bin/" + COMBAT + ".exe")));
        else artifacts.add(primaryArtifact(context,graph.targets().stream().filter(target->target.name().equals(context.current().target().targetName())).findFirst().orElseThrow()));
        if (context.current() == null) artifacts.add(BUILD.resolve(".ninja_log"));
        List<String> arguments = new ArrayList<>(List.of("--build", BUILD.toString(), "--target"));
        arguments.addAll(context.targets()); arguments.addAll(List.of("--parallel",
                Integer.toString(context.current() == null ? 1 : context.current().parallelJobs()), "--verbose"));
        command(context, context.current() == null ? "two-target-build" : context.current().target().buildStage().wireId(),
                tool(context, "cmake.exe"), arguments, SCRATCH, env, 1800, environmentRef(context), graphRef, artifacts, List.of());
        command(context, "compiler-active-dependencies", tool(context, "ninja.exe"), List.of("-C", BUILD.toString(), "-t", "deps"),
                SCRATCH, env, 120, environmentRef(context), graphRef, context.current()==null?List.of(BUILD.resolve(".ninja_deps")):List.of(), artifactRefs(context));
        dependencyManifest(graph, context);
    }

    /** Pure preparation; no process, UAC, settings write or successful registration is claimed. */
    public static PreparedRegistration prepareRegistration(Config config) throws IOException {
        require(config != null && config.stage() == Stage.REGISTER, "REGISTER240 card required for exact preparation");
        Context context = prepare(config); guard(context);
        require(context.current() == null, "Current fixture uses the explicit built-fixture UAC plan");
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
        ControlBuild.BuildReceipt tools = readCompletedToolsReceipt(context.config().toolsReceipt());
        JavaUtf8Invocation.ClassTarget target = registrationTarget(tools);
        var root = JavaUtf8Invocation.captureOutputRoot(SCRATCH);
        JavaUtf8Invocation.Launch invocation = registrationInvocation(target, root, planRef, context.deadline().toString(),
                pending -> guardRegistrationInvocation(context, pending));
        List<ControlBuild.FileRef> linked = new ArrayList<>(artifactRefs()); linked.add(planRef); linked.add(prepared.manifestRef());
        linked.add(prepared.buildActualRef()); linked.add(prepared.dependencyRef());
        linked.add(ControlBuild.FileRef.measure(SCRATCH.resolve("DEFENDER-REGISTRATION-PREPARED01.json")));
        linked.add(ControlBuild.FileRef.measure(Path.of(invocation.publication().envelope().path())));
        ControlBuild.FileRef javaExecutable = tools.javaExecutableRef();
        javaExecutable.verify();
        command(context, "defender-register-two", Path.of(javaExecutable.path()),
                invocation.physicalArguments(), SCRATCH, context.baseEnv(), 240, environmentRef(),
                ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-GRAPH01.json")),
                List.of(Path.of(plan.helperReceiptPath()), Path.of(plan.intentPath()), Path.of(plan.launchObservationPath()), Path.of(plan.resultPath()),
                        JavaUtf8Invocation.preparationPath(invocation.logicalRequest()),
                        SCRATCH.resolve(REGISTRATION_NATIVE_SOURCES), SCRATCH.resolve(REGISTRATION_PREPARATION_WITNESS)),
                sorted(linked), invocation, new JavaUtf8Invocation.ClassCarrier(target.classpath()));
    }

    private static final String REGISTRATION_INVOCATION = "DEFENDER-JAVA-INVOCATION01.bin";
    private static final String REGISTRATION_NATIVE_SOURCES = "DEFENDER-JAVA-NATIVE-SOURCES01.json";
    private static final String REGISTRATION_PREPARATION_WITNESS = "DEFENDER-JAVA-PREPARATION-WITNESS01.json";

    private static JavaUtf8Invocation.ClassTarget registrationTarget(ControlBuild.BuildReceipt tools) throws IOException {
        List<JavaUtf8Invocation.ClasspathPin> classpath = new ArrayList<>();
        JavaUtf8Invocation.ClasspathPin origin = null;
        for (ControlBuild.FileRef ref : tools.completeDeployment()) {
            ref.verify(); Path path = Path.of(ref.path());
            JavaUtf8Invocation.ClasspathPin pin = JavaUtf8Invocation.captureClasspath(path); classpath.add(pin);
            String name = path.getFileName().toString();
            if (name.startsWith("ck3-control-build-tools-") && name.endsWith(".jar")) {
                require(origin == null, "one exact qualified tools main origin required"); origin = pin;
            }
        }
        require(origin != null, "qualified tools main jar is absent");
        return new JavaUtf8Invocation.ClassTarget(NativeProjectExeUac.class.getName(), origin, classpath);
    }

    static List<String> registrationVmOptions(Path temporary) {
        return List.of("-Xms16m", "-Xmx128m", "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=2",
                "-Dfile.encoding=UTF-8", "-Djava.io.tmpdir=" + temporary, "-Djna.tmpdir=" + temporary);
    }

    static List<String> registrationLogicalArguments(ControlBuild.FileRef plan, String originalDeadline) throws IOException {
        plan.verify(); Instant.parse(originalDeadline);
        return List.of("execute-approved-plan", plan.path(), plan.sha256(), originalDeadline);
    }

    /** Pure invocation publication under the caller's actual output guard; it grants no registration authority. */
    static JavaUtf8Invocation.Launch registrationInvocation(JavaUtf8Invocation.ClassTarget target,
            JavaUtf8Invocation.DirectoryIdentity root, ControlBuild.FileRef plan, String originalDeadline,
            JavaUtf8Invocation.OutputGuard outputGuard) throws IOException {
        require(NativeProjectExeUac.class.getName().equals(target.mainClass()), "exact registration main required");
        var request = new JavaUtf8Invocation.Request(target, List.of(), registrationLogicalArguments(plan, originalDeadline), root);
        var publication = JavaUtf8Invocation.publish(request, root, REGISTRATION_INVOCATION, outputGuard);
        return JavaUtf8Invocation.launch(publication, new JavaUtf8Invocation.ClassCarrier(target.classpath()),
                registrationVmOptions(Path.of(root.path())));
    }

    private static void guardRegistrationInvocation(Context context, long pendingBytes) throws IOException {
        require(pendingBytes > 0 && pendingBytes <= (8L << 20) + 8192, "bounded invocation publication required");
        guard(context);
        require(Math.addExact(footprint(SCRATCH), Math.addExact(pendingBytes, 4096)) <= context.card().scratchLimitBytes(),
                "pending invocation exceeds the original native scratch cap");
    }

    static void requireRegistrationRequest(JavaUtf8Invocation.Request actual, JavaUtf8Invocation.ClassTarget target,
            JavaUtf8Invocation.DirectoryIdentity root, ControlBuild.FileRef plan, String deadline) throws IOException {
        require(actual.equals(new JavaUtf8Invocation.Request(target, List.of(), registrationLogicalArguments(plan, deadline), root)),
                "registration invocation changed original target/runtime/arguments/evidence root");
    }

    static void requireRegistrationSourceOutputsAbsent(JavaUtf8Invocation.Launch invocation) throws IOException {
        Path root = Path.of(invocation.logicalRequest().evidenceRoot().path());
        for (Path path : List.of(JavaUtf8Invocation.preparationPath(invocation.logicalRequest()),
                root.resolve(REGISTRATION_NATIVE_SOURCES), root.resolve(REGISTRATION_PREPARATION_WITNESS))) {
            require(Files.notExists(path, LinkOption.NOFOLLOW_LINKS), "original registration source output already exists or is unavailable; UNKNOWN cannot replay");
        }
    }

    /** Actual child output custody uses the shared native witness, never a JDK optional provider key. */
    static SharedSourceFiles.Witness registrationPreparationWitness(JavaUtf8Invocation.Launch invocation) throws IOException {
        Path path = JavaUtf8Invocation.preparationPath(invocation.logicalRequest());
        SharedSourceFiles.Witness original = SharedSourceFiles.observe(path);
        JavaUtf8Invocation.inspectPreparation(JavaUtf8Invocation.captureFile(path), invocation.publication());
        SharedSourceFiles.assertUnchanged(original); return original;
    }

    /** Cold evidence checks source continuity for the same actual terminal; original success/admission guards remain separate. */
    static void requireRegistrationSources(JavaUtf8Invocation.Launch invocation, JavaUtf8Invocation.Carrier carrier,
            WindowsJobProcess.CommandResult actual, SharedSourceFiles.Witness preparation,
            JavaUtf8NativeCustody.Evidence sources) throws IOException {
        require(invocation != null && carrier != null && actual != null && preparation != null
                && preparation.source() != null && preparation.nativeFile() != null && sources != null,
                "complete original registration preparation and native source evidence required");
        require(sources.terminal().equals(actual) && sources.identity().equals(actual.identity()),
                "registration native sources belong to a different original child terminal");
        JavaUtf8NativeCustody.requireCurrent(sources, invocation, carrier);
        Path path = JavaUtf8Invocation.preparationPath(invocation.logicalRequest());
        require(Path.of(preparation.source().path()).equals(path), "registration preparation witness changed its original output path");
        SharedSourceFiles.assertUnchanged(preparation);
        JavaUtf8Invocation.inspectPreparation(JavaUtf8Invocation.captureFile(path), invocation.publication());
        SharedSourceFiles.assertUnchanged(preparation);
    }

    /** Only the exact former ASCII class invocation is retained for historical reads; new execution never emits it. */
    static boolean historicalRegistrationCommand(List<String> command, ControlBuild.FileRef plan, String deadline) throws IOException {
        if (command.size() != 15 || command.stream().anyMatch(value -> value.chars().anyMatch(character -> character > 127))) return false;
        return command.subList(1, 8).equals(registrationVmOptions(WORK.resolve("scratch")))
                && command.get(8).equals("-cp") && !command.get(9).isBlank()
                && command.get(10).equals(NativeProjectExeUac.class.getName())
                && command.subList(11, 15).equals(registrationLogicalArguments(plan, deadline));
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
        Path BUILD = context.buildRoot(), SCRATCH = context.scratchRoot();
        if (context.current() == null) { acceptedCompilerDependencies(); acceptedDefender(); accepted("kinship-producer"); }
        else { requireCurrentStage(context.current(),Stage.COMBAT); acceptedCompilerDependencies(context); requireCurrentRegistration(context); }
        Path out = SCRATCH.resolve("combat-whole14");
        require(!Files.exists(out), "fresh fourteen-scene native output required");
        Path raw = out.resolve("ck3_12003_army_combat_roles_phase_rule24_pins_wire.json");
        Path executable = context.current() == null ? BUILD.resolve("bin/" + COMBAT + ".exe")
                : primaryArtifact(context, acceptedGraph(context).targets().stream().filter(target -> target.name().equals(COMBAT)).findFirst().orElseThrow());
        command(context, "combatroles-producer", executable, List.of("--wire-dir", out.toString()), SCRATCH,
                nativeEnvironment(context), 120, environmentRef(context), ControlBuild.FileRef.measure(SCRATCH.resolve("CONFIGURED-GRAPH01.json")),
                List.of(raw), context.current()==null?artifactRefs(context):mergeToolRefs(artifactRefs(context),requireCurrentRegistration(context)));
    }

    private static Actual command(Context context, String id, Path executable, List<String> args, Path cwd,
            Map<String, String> env, int timeout, ControlBuild.FileRef environment, ControlBuild.FileRef graph,
            List<Path> outputs, List<ControlBuild.FileRef> linked) throws IOException, InterruptedException {
        return command(context, id, executable, args, cwd, env, timeout, environment, graph, outputs, linked, null, null);
    }

    private static Actual command(Context context, String id, Path executable, List<String> args, Path cwd,
            Map<String, String> env, int timeout, ControlBuild.FileRef environment, ControlBuild.FileRef graph,
            List<Path> outputs, List<ControlBuild.FileRef> linked, JavaUtf8Invocation.Launch invocation,
            JavaUtf8Invocation.Carrier carrier) throws IOException, InterruptedException {
        Path SCRATCH = context.scratchRoot();
        require((invocation == null) == (carrier == null)
                && id.equals("defender-register-two") == (invocation != null), "current registration requires its explicit original UTF8 invocation");
        require(!Files.exists(actualPath(context, id)), "stage actual is append-only; no unknown replay");
        Path stdout = SCRATCH.resolve(id + ".stdout.log"), stderr = SCRATCH.resolve(id + ".stderr.log");
        Path diagnosticPath = id.equals(CONFIGURE_ID) ? SCRATCH.resolve(id + ".job-members.json") : null;
        WindowsJobProcess.JobDiagnosticOutcome diagnostic = null;
        boolean currentCompiler = context.current()!=null && Set.of(CONFIGURE_ID,context.current().target().buildStage().wireId()).contains(id);
        MsvcAuxiliaryPolicy.Outcome auxiliary = null;
        List<SharedSourceFiles.Witness> compileBefore = List.of();
        SharedSourceFiles.Witness bindingWitness = null;
        List<Path> expectedOutputs = new ArrayList<>(outputs);
        Graph selected = null; WindowsJobProcess.CommandResult result = null;
        WindowsJobProcess.ProcessIdentity ownerIdentity = null; String error = null;
        try {
            guard(context); verify(context.sourceRefs()); verify(context.toolRefs()); verify(context.runtimeRefs()); verify(linked);
            if(context.current()!=null && context.config().stage()==Stage.BUILD) {
                compileBefore=CompileSourceBinding.assertLiveUnchanged(context.binding(),context.compileBefore());
                bindingWitness=SharedSourceFiles.observe(Path.of(context.current().compileSourceBindingRef().path()));
            }
            selected = graph == null ? null : acceptedGraph(context);
            if(context.current()!=null)verifyCurrentLiveGenerated(context.current(),ControlBuild.FileRef.measure(context.config().plan()),id);
            if (selected != null) { verify(selected.projectSourceRefs()); verify(selected.configuredInputRefs()); verify(selected.configuredToolRefs()); }
            WindowsJobProcess.ConsoleMode mode = id.equals(CONFIGURE_ID) || id.equals("two-target-build") || currentCompiler
                    ? WindowsJobProcess.ConsoleMode.DETACHED : WindowsJobProcess.ConsoleMode.NO_WINDOW;
            try (JavaUtf8NativeCustody.Held nativeInputs = invocation == null ? null : JavaUtf8NativeCustody.acquire(invocation, carrier)) {
                long evidenceQuote = 0;
                if (nativeInputs != null) {
                    requireRegistrationSourceOutputsAbsent(invocation);
                    evidenceQuote = nativeInputs.maximumEvidenceBytes(executable);
                    long preparationQuote = Math.addExact(8192L, 4L * JavaUtf8Invocation.preparationPath(invocation.logicalRequest())
                            .toString().getBytes(StandardCharsets.UTF_8).length);
                    guardRegistrationInvocation(context, Math.addExact(evidenceQuote, preparationQuote));
                    nativeInputs.requireCurrent();
                }
                Runnable auxiliaryGuard=()-> { try { guard(context); logBudget(context); } catch(IOException failure) { throw new IllegalStateException(failure); } };
                MsvcAuxiliaryPolicy.ExecutionBinding execution = currentCompiler ? new MsvcAuxiliaryPolicy.ExecutionBinding(
                        "xar.exact-msvc-owned-execution/v1",NativeBridgeBuild.environmentCompilerBinding(context.environment()),
                        ControlBuild.FileRef.measure(executable)) : null;
                if(execution!=null) {
                    execution.requireRequest(ControlBuild.FileRef.measure(executable),context.toolRefs());
                    auxiliary=MsvcAuxiliaryPolicy.notEntered(execution,"Original fixture compiler command has not entered MSVC completion");
                }
                try (var heldImages=execution==null?null:MsvcAuxiliaryPolicy.retain(execution,context.deadline(),auxiliaryGuard);
                        WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(executable, args, cwd, env, stdout, stderr, context.card().memoryLimitBytes()), mode)) {
                    ownerIdentity = child.identity();
                    if (nativeInputs != null) nativeInputs.attach(child);
                    Runnable periodic = () -> {
                        try { guard(context); logBudget(context); }
                        catch (IOException failure) { throw new IllegalStateException(failure.getMessage(), failure); }
                    };
                    if (nativeInputs != null) periodic = nativeInputs.guard(periodic);
                    if (heldImages!=null) {
                        var awaited=child.awaitWithMsvcAuxiliaries(Duration.ofSeconds(timeout),context.deadline(),periodic,
                                SCRATCH.resolve(id+".before-cleanup.json"),heldImages);
                        result=awaited.original().commandResult(); auxiliary=awaited.auxiliaryCleanup();
                    } else if (id.equals(CONFIGURE_ID) || id.equals("two-target-build")) {
                        WindowsJobProcess.AwaitResult awaited = child.await(Duration.ofSeconds(timeout), context.deadline(), periodic, diagnosticPath,
                                WindowsJobProcess.RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE);
                        result = awaited.commandResult(); diagnostic = awaited.diagnostic();
                    } else result = child.await(Duration.ofSeconds(timeout), context.deadline(), periodic);
                    // Keep this exact returned result before any source proof can fail; RED never erases its real terminal.
                    if (nativeInputs != null) {
                        JavaUtf8NativeCustody.Evidence sources = nativeInputs.verifyTerminal(result).evidence();
                        byte[] evidence = JavaUtf8NativeCustody.encodeEvidence(sources);
                        require(evidence.length <= evidenceQuote, "actual original native source proof exceeded its quoted bound");
                        logBudget(context); Files.write(SCRATCH.resolve(REGISTRATION_NATIVE_SOURCES), evidence, StandardOpenOption.CREATE_NEW);
                        SharedSourceFiles.Witness preparation = registrationPreparationWitness(invocation);
                        publish(SCRATCH.resolve(REGISTRATION_PREPARATION_WITNESS), preparation);
                        requireRegistrationSources(invocation, carrier, result, preparation, sources);
                    }
                }
            }
        } catch (IOException | RuntimeException | InterruptedException failure) {
            if (failure instanceof InterruptedException) Thread.currentThread().interrupt();
            error = failure.getClass().getName() + ": " + failure.getMessage();
        }
        boolean unchanged = false; List<ControlBuild.FileRef> outputRefs = new ArrayList<>();
        if(currentCompiler) {
            List<SharedSourceFiles.Witness> after=List.of();
            try { after=CompileSourceBinding.assertLiveUnchanged(context.binding(),compileBefore); }
            catch(IOException|RuntimeException failure) { error=(error==null?"":error+"; ")+"compile source postcheck: "+failure; }
            try {
                Path proof=SCRATCH.resolve(id+".source-terminal.json");
                publish(proof,new CurrentSourceTerminal(terminalSchema(context.current()),id,bindingWitness,compileBefore,after,auxiliary));
                expectedOutputs.add(proof);
                Path cleanup=SCRATCH.resolve(id+".before-cleanup.json");
                if(Files.exists(cleanup,LinkOption.NOFOLLOW_LINKS)) expectedOutputs.add(cleanup);
            } catch(IOException|RuntimeException failure) { error=(error==null?"":error+"; ")+"compiler terminal persistence: "+failure; }
        }
        if(currentCompiler) {
            try { expectedOutputs.add(Path.of(retainCurrentStageFiles(context,id,measureAllPresent(outputs)).path())); }
            catch(IOException|RuntimeException failure) { error=(error==null?"":error+"; ")+"generated-file retention: "+failure; }
        }
        if (diagnosticPath != null && !currentCompiler) {
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
            if(context.current()!=null)verifyCurrentLiveGenerated(context.current(),ControlBuild.FileRef.measure(context.config().plan()),id);
            if (selected != null) { verify(selected.projectSourceRefs()); verify(selected.configuredInputRefs()); verify(selected.configuredToolRefs()); }
            if(context.current()!=null && context.config().stage()==Stage.BUILD)
                CompileSourceBinding.assertLiveUnchanged(context.binding(),compileBefore);
            if(currentCompiler) require(auxiliary!=null && auxiliary.completed(),"Real compiler auxiliary completion missing");
            unchanged = true; guard(context);
            for (Path path : expectedOutputs) {
                ControlBuild.FileRef pin = measureIfPresent(path); if (pin != null) outputRefs.add(pin);
            }
            require(NativeLifecycleTerminal.assess(result).successful(), "actual naturally settled successful child terminal unavailable or failed");
            logBudget(context);
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
        publish(actualPath(context, id), actual);
        System.out.println(id + " " + actual.status() + (result == null ? " terminal=unavailable" : " exit=" + result.exitCode() + " Jobactive=" + result.accounting().activeProcesses()));
        require(error == null, "native stage RED retained: " + error); return actual;
    }

    private static void manifest(Context context, String name, List<ControlBuild.FileRef> refs) throws IOException {
        Path SCRATCH = context.scratchRoot();
        List<ControlBuild.FileRef> tools = mergeToolRefs(context.toolRefs(),
                name.equals("CONFIGURED-SOURCE-MANIFEST01.json") ? acceptedGraph(context).configuredToolRefs() : List.of());
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
        Path SCRATCH = context.scratchRoot();
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
        verifyUniqueRefs(value.toolRefs());
        JsonNode authority=read(Path.of(value.resourceCardRef().path()),262144);
        if(CURRENT_CARD_SCHEMA.equals(authority.path("schema").asText())) {
            var card=currentFixtureCard(value.resourceCardRef());var plan=readCurrentPlan(card.packageRequestRef());
            verifyCurrentRefs(plan,card.packageRequestRef(),value.outputRefs());verifyCurrentRefs(plan,card.packageRequestRef(),value.linkedArtifactRefs());
        } else { verifyUniqueRefs(value.outputRefs());verifyUniqueRefs(value.linkedArtifactRefs()); }
        SourceManifest manifest = JSON.readValue(bytes(Path.of(value.sourceManifestRef().path()), 2097152), SourceManifest.class);
        require(manifest != null && "xar.native-stage-source-manifest/v1".equals(manifest.schema()) && MACHINE.equals(manifest.machineId())
                && !manifest.sourceRefs().isEmpty() && !manifest.toolRefs().isEmpty() && !manifest.operationRuntimeRefs().isEmpty()
                && new HashSet<>(manifest.toolRefs()).equals(new HashSet<>(value.toolRefs())), "complete original stage source/tool manifest required");
        try { Instant.parse(manifest.observedAtUtc()); }
        catch (java.time.DateTimeException | NullPointerException invalid) { throw new IOException("invalid original stage source manifest observation", invalid); }
        if(CURRENT_CARD_SCHEMA.equals(authority.path("schema").asText())) {
            var planRef=currentFixtureCard(value.resourceCardRef()).packageRequestRef();
            verifyCurrentRefs(readCurrentPlan(planRef),planRef,manifest.sourceRefs());
        } else verifyUniqueRefs(manifest.sourceRefs());
        verifyUniqueRefs(manifest.toolRefs()); verifyUniqueRefs(manifest.operationRuntimeRefs());
        if(CURRENT_CARD_SCHEMA.equals(authority.path("schema").asText())) readCurrentActual(value);
        else require(expectedStage!=ActualStage.COMBATROLES_TARGET_BUILD && expectedStage!=ActualStage.HOLY_FIXTURE_TARGET_BUILD,
                "Legacy authority cannot build current fixture");
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
        return vendorAnalysis(actual, probe, vendorPin());
    }

    private static VctipProbeFacts.Analysis vendorAnalysis(Actual actual, VctipProbeFacts.ProbeCase probe,
            ControlBuild.FileRef pin) throws IOException {
        require(probe == VctipProbeFacts.ProbeCase.IDLE_ONE || probe == VctipProbeFacts.ProbeCase.IDLE_TWO, "only declared idle cases allowed");
        require(actual.command().size() == 2 && Path.of(actual.command().getFirst()).normalize().equals(Path.of(pin.path()).normalize())
                && actual.command().get(1).equals(VctipProbeFacts.arguments(probe).getFirst()) && actual.toolRefs().contains(pin), "exact pinned vendor arguments and tool role required");
        VctipProbeFacts.Analysis value = VctipProbeFacts.analyze(probe, actual.result(),
                bytes(Path.of(actual.stdoutRef().path()), 65536), bytes(Path.of(actual.stderrRef().path()), 65536), pin);
        require(value.observation() == VctipProbeFacts.Observation.NATURAL_ZERO_EXIT_OBSERVED
                && value.qualification() == VctipProbeFacts.Qualification.NONE && actual.result().elapsedSeconds() < 30,
                "vendor observation cannot qualify a compiler or cleaned Job");
        return value;
    }

    /** Historical file-bound vendor observations, without granting present-stage or configure authority. */
    public static VendorTimeouts readVendorTimeouts(Path path) throws IOException {
        require(path != null && path.isAbsolute(), "absolute vendor observation path required");
        return readVendorTimeouts(path, vendorPin());
    }

    /** Shared file-bound DATA reader; no stage caller may replace the public fixed-vendor boundary. */
    static VendorTimeouts readVendorTimeouts(Path path, ControlBuild.FileRef expectedVendor) throws IOException {
        require(path != null && path.isAbsolute(), "absolute vendor observation path required");
        require(expectedVendor != null, "exact expected vendor DATA pin required");
        expectedVendor.verify();
        VendorTimeouts value = JSON.readValue(bytes(path, 262144), VendorTimeouts.class);
        require(value != null, "typed vendor observations required");
        for (ControlBuild.FileRef pin : List.of(value.vendorRef(), value.sourceManifestRef(), value.toolsReceiptRef(),
                value.environmentRef(), value.firstActualRef(), value.secondActualRef())) pin.verify();
        require(value.vendorRef().equals(expectedVendor), "vendor observation names another executable");
        Actual first = readActual(Path.of(value.firstActualRef().path()), ActualStage.VENDOR_TIMEOUT_ONE);
        Actual second = readActual(Path.of(value.secondActualRef().path()), ActualStage.VENDOR_TIMEOUT_TWO);
        require(!first.ownerIdentity().equals(second.ownerIdentity()) && !value.firstActualRef().equals(value.secondActualRef())
                && first.stageDeadlineAtUtc().equals(value.stageDeadlineAtUtc()) && second.stageDeadlineAtUtc().equals(value.stageDeadlineAtUtc()),
                "both distinct vendor processes must retain their original shared deadline");
        Instant firstAt = Instant.parse(first.observedAtUtc()), secondAt = Instant.parse(second.observedAtUtc()), at = Instant.parse(value.observedAtUtc());
        require(!firstAt.isAfter(secondAt) && !secondAt.isAfter(at) && at.isBefore(Instant.parse(value.stageDeadlineAtUtc())), "vendor chronology differs from the original stage window");
        for (Actual actual : List.of(first, second)) require(actual.sourceManifestRef().equals(value.sourceManifestRef())
                && actual.toolsReceiptRef().equals(value.toolsReceiptRef()) && actual.environmentRef().equals(value.environmentRef()), "vendor source/tools/environment changed between cases");
        require(value.firstAnalysis().equals(vendorAnalysis(first, VctipProbeFacts.ProbeCase.IDLE_ONE, expectedVendor))
                && value.secondAnalysis().equals(vendorAnalysis(second, VctipProbeFacts.ProbeCase.IDLE_TWO, expectedVendor)), "stored vendor analysis differs from the original raw terminals");
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
        ControlBuild.BuildReceipt originalTools = readCompletedToolsReceipt(Path.of(registration.toolsReceiptRef().path()));
        originalTools.javaExecutableRef().verify();
        require(Path.of(registration.command().getFirst()).toRealPath().equals(Path.of(originalTools.javaExecutableRef().path()).toRealPath()),
                "accepted registration changed the original qualified Java executable");
        if (!historicalRegistrationCommand(registration.command(), prepared.reviewPlanRef(), registration.stageDeadlineAtUtc())) {
            var root = JavaUtf8Invocation.captureOutputRoot(SCRATCH);
            var target = registrationTarget(originalTools);
            Path envelope = SCRATCH.resolve(REGISTRATION_INVOCATION);
            ControlBuild.FileRef envelopeRef = ControlBuild.FileRef.measure(envelope);
            require(registration.linkedArtifactRefs().contains(envelopeRef), "registration omitted original invocation envelope custody");
            var publication = new JavaUtf8Invocation.Publication(JavaUtf8Invocation.captureFile(envelope));
            var carrier = new JavaUtf8Invocation.ClassCarrier(target.classpath());
            List<String> options = registrationVmOptions(SCRATCH);
            List<String> physical = registration.command().subList(1, registration.command().size());
            require(physical.equals(JavaUtf8Invocation.launch(publication, carrier, options).physicalArguments()),
                    "accepted registration physical command differs from its exact original envelope");
            var invocation = JavaUtf8Invocation.launch(publication, carrier, options);
            var logical = JavaUtf8Invocation.inspect(physical, carrier, options);
            requireRegistrationRequest(logical, target, root, prepared.reviewPlanRef(), registration.stageDeadlineAtUtc());
            Path preparation = JavaUtf8Invocation.preparationPath(logical);
            ControlBuild.FileRef preparationRef = ControlBuild.FileRef.measure(preparation);
            require(registration.outputRefs().contains(preparationRef), "registration omitted original child preparation custody");
            Path sourcePath = SCRATCH.resolve(REGISTRATION_NATIVE_SOURCES), witnessPath = SCRATCH.resolve(REGISTRATION_PREPARATION_WITNESS);
            ControlBuild.FileRef sourceRef = ControlBuild.FileRef.measure(sourcePath), witnessRef = ControlBuild.FileRef.measure(witnessPath);
            require(registration.outputRefs().contains(sourceRef) && registration.outputRefs().contains(witnessRef),
                    "current UTF8 registration omitted original continuously held native sources or preparation witness");
            JavaUtf8NativeCustody.Evidence sources = JavaUtf8NativeCustody.decodeEvidence(bytes(sourcePath, JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES));
            SharedSourceFiles.Witness originalPreparation = JSON.readValue(bytes(witnessPath, 131072), SharedSourceFiles.Witness.class);
            requireRegistrationSources(invocation, carrier, registration.result(), originalPreparation, sources);
        }
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
    private static void dependencyManifest(Graph graph, Context context) throws IOException {
        Path SOURCE = context.sourceRoot(), BUILD = context.buildRoot(), SCRATCH = context.scratchRoot();
        Path raw = SCRATCH.resolve("compiler-active-dependencies.stdout.log");
        Map<Path, ControlBuild.FileRef> pins = new LinkedHashMap<>();
        Set<Path> frozen = new HashSet<>(graph.projectSourceRefs().stream().map(r -> Path.of(r.path())).toList());
        try (var reader = Files.newBufferedReader(raw, StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.startsWith("    ")) continue; String name = line.strip(); if (name.isEmpty()) continue;
                Path path = Path.of(name); if (!path.isAbsolute()) path = BUILD.resolve(path); path = path.toAbsolutePath().normalize();
                require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS), "actual compiler dependency absent: " + path);
                if (path.startsWith(SOURCE)) {
                    if (context.current() == null) require(frozen.contains(path), "actual project compiler dependency was not frozen: " + path);
                    else CompileSourceBinding.retainedFor(context.binding(), ControlBuild.FileRef.measure(path)).verify();
                }
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
        Path BUILD = context.buildRoot();
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
    private static void collectQuoted(List<Path> initial, List<Path> search, Map<Path, ControlBuild.FileRef> pins, Path SOURCE, Path BUILD) throws IOException {
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
    private static ControlBuild.FileRef toolRef(List<ControlBuild.FileRef> qualifiedToolRefs, String name) throws IOException {
        List<ControlBuild.FileRef> matches = qualifiedToolRefs.stream()
                .filter(ref -> Path.of(ref.path()).getFileName().toString().equalsIgnoreCase(name)).toList();
        require(matches.size() == 1, "one exact pinned tool required: " + name); return matches.getFirst();
    }
    private static Path tool(Context context, String name) throws IOException {
        return Path.of(toolRef(context.toolRefs(), name).path());
    }
    private static void guard(Context context) throws IOException {
        if (context.current() != null) { guardCurrent(context); return; }
        context.cardRef().verify(); require(Instant.now().isBefore(context.deadline()), "native resource card expired");
        long combinedBuild = footprint(BUILD);
        for (Path previous : PREVIOUS_BUILDS) combinedBuild = Math.addExact(combinedBuild, footprint(previous));
        require(combinedBuild <= BUILD_CAP && footprint(SCRATCH) <= context.card().scratchLimitBytes(), "finite combined native output cap exceeded");
        if (context.config().stage() == Stage.ENV || context.config().stage() == Stage.VENDOR_TIMEOUTS)
            require(!Files.exists(BUILD, LinkOption.NOFOLLOW_LINKS), "ENV/vendor cannot create or populate the build root");
    }
    private static void logBudget() throws IOException { logBudget(SCRATCH); }
    private static void logBudget(Context context) throws IOException { logBudget(context.scratchRoot()); }
    private static void logBudget(Path SCRATCH) throws IOException {
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
    private static void publish(Path path, Object value) throws IOException { byte[] raw = JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(value); require(raw.length <= (value instanceof CurrentSourceTerminal ? 16 << 20 : 2097152), "finite native metadata cap exceeded"); Files.write(path, raw, StandardOpenOption.CREATE_NEW); }
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
