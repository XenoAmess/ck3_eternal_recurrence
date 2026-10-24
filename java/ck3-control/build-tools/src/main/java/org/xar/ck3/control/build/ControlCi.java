package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;
import java.util.TreeMap;

/** The durable CI route: qualify tools under a native Job, then run the same build and consumers. */
public final class ControlCi {
    private ControlCi() {}
    public static final String ACTUAL_SCHEMA = "xar.java-control-CI-actual/v6";
    public static final String FIXTURE_REQUEST_SCHEMA = "xar.java-control-CI-fixture-request/v1";
    public static final String FIXTURE_PRODUCTION_SCHEMA = "xar.java-control-CI-fixture-production-request/v1";
    public static final String CURRENT_FIXTURE_PRODUCTION_SCHEMA = "xar.java-control-CI-fixture-production-request/v2";
    public enum Stage { EXPECTED_MAVEN_RED, REACTOR, REACTOR_TEST_CLOSURE, MAP_CONSUMERS,
        SDK_SENTINEL_STATIC, MONTHLY_STATIC, SUPPLEMENTAL, FRESH_SDK, CANONICAL_THIRTY }
    public enum StageState { NOT_RUN, STARTED, PASS, RED }
    public enum PipelineState { PASS, RED }
    public enum ExecutionPurpose { HOSTED_CI, ROOT_LOCAL_FULL_SOFTWARE }
    public static final String ROOT_CARD_SCHEMA = "xar.root-local-full-software-card/v1";
    public static final String ROOT_PLAN_SCHEMA = "xar.root-local-full-software-plan/v1";
    public record RootSoftwareExecutionCard(String schema, ExecutionPurpose purpose, String machineId,
            String observedAtUtc, String reviewAtUtc, String ownerTask, String slotId,
            ControlBuild.FileRef resourcePlanRef, ControlBuild.FileRef runtimeBindingRef,
            ControlBuild.FileRef capacityReleaseRef, ControlBuild.FileRef toolsBuildReceiptRef,
            ControlBuild.FileRef reactorBuildReceiptRef, ControlBuild.SourceLimitProfile sourceLimitProfile) {
        public RootSoftwareExecutionCard {
            if (!ROOT_CARD_SCHEMA.equals(schema) || purpose != ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE
                    || machineId == null || machineId.isBlank() || ownerTask == null || ownerTask.isBlank()
                    || ownerTask.equals("github-actions-java-ci") || slotId == null || !slotId.matches("[a-z0-9][a-z0-9-]{0,63}")
                    || resourcePlanRef == null || runtimeBindingRef == null || capacityReleaseRef == null
                    || toolsBuildReceiptRef == null || reactorBuildReceiptRef == null || sourceLimitProfile == null
                    || sourceLimitProfile == ControlBuild.SourceLimitProfile.STANDARD_8_MIB) {
                throw new IllegalArgumentException("Explicit Root software purpose, finite resources and normal G2 reactor required");
            }
            if (!Instant.parse(observedAtUtc).isBefore(Instant.parse(reviewAtUtc))) throw new IllegalArgumentException("Finite Root software window required");
        }
    }
    public record RootLocalPlan(String schema, ExecutionPurpose purpose, ControlBuild.FileRef softwareExecutionCardRef,
            ControlBuild.FileRef fixtureProductionRequestRef) {
        public RootLocalPlan {
            if (!ROOT_PLAN_SCHEMA.equals(schema) || purpose != ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE
                    || softwareExecutionCardRef == null || fixtureProductionRequestRef == null) {
                throw new IllegalArgumentException("Root-local card and complete actual fixture production inputs required");
            }
        }
    }
    private record LocalExecution(ControlBuild.FileRef planRef, RootLocalPlan plan, RootSoftwareExecutionCard card) { }
    public record StageActual(Stage stage, StageState state, ControlBuild.FileRef evidenceRef, String error) {
        public StageActual {
            if (stage == null || state == null || state == StageState.PASS && (evidenceRef == null || error != null))
                throw new IllegalArgumentException("Explicit actual pipeline stage required");
            if (state == StageState.NOT_RUN && (evidenceRef != null || error != null)) throw new IllegalArgumentException("Unstarted stage cannot claim evidence");
        }
    }
    public record FixtureRequest(String schema, String machineId, String reviewAtUtc,
            ControlBuild.FileRef freshSdkConfigRef, ControlBuild.FileRef canonicalConfigRef) {
        public FixtureRequest {
            if (!FIXTURE_REQUEST_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
                    || freshSdkConfigRef == null || canonicalConfigRef == null) throw new IllegalArgumentException("Complete pinned fixture request required");
            Instant.parse(reviewAtUtc);
        }
    }
    public sealed interface FixtureProductionInputs permits FixtureProductionRequest, CurrentFixtureProductionRequest {
        String machineId(); String reviewAtUtc(); ControlBuild.FileRef sdkProductionInputsRef(); RootSoftwareFixtureHandoff.Request softwareFixture();
    }
    public record FixtureProductionRequest(String schema, String machineId, String reviewAtUtc,
            ControlBuild.FileRef sdkProductionInputsRef, RootSoftwareFixtureHandoff.Request softwareFixture) implements FixtureProductionInputs {
        public FixtureProductionRequest {
            if (!FIXTURE_PRODUCTION_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
                    || sdkProductionInputsRef == null || softwareFixture == null) {
                throw new IllegalArgumentException("Pinned SDK inputs and original same-host fixture request required");
            }
            Instant.parse(reviewAtUtc);
        }
    }
    public record CurrentFixtureProductionRequest(String schema, String machineId, String reviewAtUtc,
            ControlBuild.FileRef sdkProductionInputsRef, RootSoftwareFixtureHandoff.Request softwareFixture,
            ControlBuild.FileRef currentOracleInputsRef) implements FixtureProductionInputs {
        public CurrentFixtureProductionRequest {
            if (!CURRENT_FIXTURE_PRODUCTION_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
                    || sdkProductionInputsRef == null || softwareFixture == null || currentOracleInputsRef == null
                    || currentOracleInputsRef.bytes() <= 0 || currentOracleInputsRef.bytes() > FullParityCurrentBindings.MAX_INPUT_BYTES) {
                throw new IllegalArgumentException("R3 requires original SDK/host and complete exact current oracle inputs");
            }
            Instant.parse(reviewAtUtc);
        }
    }
    record Invocation(Path planPath, Path toolsReceiptPath, ControlBuild.FileRef fixtureRequestRef,
            ControlBuild.FileRef fixtureProductionRequestRef) { }
    record FixtureWriterInvocation(Path planPath, ControlBuild.FileRef freshConfigRef,
            ControlBuild.FileRef canonicalConfigRef, Path outputRoot) { }
    private static final long MAX_CONFIG_BYTES = 4L << 20;

    public record Receipt(String schema, String machineId, String startedAtUtc, String observedAtUtc,
            PipelineState status, String error, ControlBuild.FileRef planRef, ControlBuild.FileRef capacityReleaseRef,
            ControlBuild.FileRef toolsBuildReceiptRef, WindowsJobProcess.CommandResult qualifiedPipeline,
            ControlBuild.FileRef reactorBuildReceiptRef, ControlBuild.FileRef consumerReceiptRef,
            List<ControlBuild.FileRef> pythonStaticReceiptRefs, ControlBuild.FileRef supplementalFixtureReceiptRef,
            ControlBuild.FileRef reactorTestClosureReceiptRef, ControlBuild.FileRef fixtureRequestRef,
            ControlBuild.FileRef fixtureProductionRequestRef,
            ExecutionPurpose purpose, ControlBuild.FileRef rootLocalPlanRef,
            List<StageActual> stages) {
        public Receipt {
            if (!ACTUAL_SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact CI actual v6 contract required");
            if (purpose == null || (purpose == ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE) != (rootLocalPlanRef != null)
                    || purpose == ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE && fixtureProductionRequestRef == null) {
                throw new IllegalArgumentException("Exact hosted or Root-local software provenance required");
            }
            if (status == null || status == PipelineState.PASS && error != null) throw new IllegalArgumentException("Typed actual pipeline outcome required");
            pythonStaticReceiptRefs = List.copyOf(pythonStaticReceiptRefs);
            stages = List.copyOf(stages);
            if (stages.size() != Stage.values().length) throw new IllegalArgumentException("Every actual pipeline stage must be preserved");
            for (int index = 0; index < stages.size(); index++) if (stages.get(index).stage() != Stage.values()[index]) throw new IllegalArgumentException("Unique ordered pipeline stages required");
            if (status == PipelineState.PASS) {
                if (fixtureProductionRequestRef != null && fixtureRequestRef == null) {
                    throw new IllegalArgumentException("Requested fixture production cannot pass without its actual generated request");
                }
                for (StageActual stage : stages) {
                    boolean fixture = stage.stage() == Stage.FRESH_SDK || stage.stage() == Stage.CANONICAL_THIRTY;
                    StageState required = fixture && fixtureRequestRef == null
                            || purpose == ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE && stage.stage() == Stage.EXPECTED_MAVEN_RED
                            ? StageState.NOT_RUN : StageState.PASS;
                    if (stage.state() != required) throw new IllegalArgumentException("PASS cannot omit any requested stage");
                }
            }
        }
    }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length > 0 && arguments[0].equals("--root-local-full-software")) {
            if (arguments.length != 4) throw new IllegalArgumentException("One exact Root-local plan path/bytes/SHA required");
            var planRef = argumentRef(arguments, 1);
            var local = readRootLocalExecution(planRef);
            var resources = readPinned(local.card().resourcePlanRef(), CiBootstrap.Plan.class, MAX_CONFIG_BYTES);
            prepareLocalWorkRoot(resources);
            runQualified(Path.of(local.card().resourcePlanRef().path()), resources, Path.of(local.card().toolsBuildReceiptRef().path()),
                    null, local.plan().fixtureProductionRequestRef(), local); return;
        }
        if (arguments.length == 4 && arguments[0].equals("--write-person10-corpus-manifest") && arguments[2].equals("--output")) {
            var result = Person10NativeCorpus.produce(Path.of(arguments[1]), Path.of(arguments[3]));
            System.out.println("WROTE_PERSON10_CORPUS_MANIFEST " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-current-oracle-inputs")) {
            if (arguments.length != 5 || !arguments[1].equals("--java-source-root") || !arguments[3].equals("--output")) {
                throw new IllegalArgumentException("Actual selected Java source root and fresh R3 oracle-input output required");
            }
            var result = FullParityCurrentBindings.produce(Path.of(arguments[2]), System.getenv(), Path.of(arguments[4]));
            System.out.println("WROTE_CURRENT_ORACLE_INPUTS " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-current-fixture-production-request")) {
            if (arguments.length != 14 || !arguments[4].equals("--software-fixture-inputs") || !arguments[8].equals("--current-oracle-inputs") || !arguments[12].equals("--output")) {
                throw new IllegalArgumentException("Pinned SDK/host/current oracle inputs and fresh output required");
            }
            var sdkRef = argumentRef(arguments, 1); var sdk = SdkStageConfigurationProducer.readInputs(sdkRef);
            var hostRef = argumentRef(arguments, 5); var host = readPinned(hostRef, RootSoftwareFixtureHandoff.Request.class, MAX_CONFIG_BYTES);
            var currentRef = argumentRef(arguments, 9);
            var request = new CurrentFixtureProductionRequest(CURRENT_FIXTURE_PRODUCTION_SCHEMA, sdk.machineId(), sdk.reviewAtUtc(), sdkRef, host, currentRef);
            verifyProductionInputs(request); Path output = Path.of(arguments[13]).toAbsolutePath().normalize(); SharedSourceFiles.plainAncestors(output);
            publish(output, request); sdkRef.verify(); hostRef.verify(); currentRef.verify();
            System.out.println("WROTE_CURRENT_FIXTURE_PRODUCTION_REQUEST " + ControlBuild.strictMapper().writeValueAsString(ControlBuild.FileRef.measure(output))); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-fixture-production-request")) {
            if (arguments.length != 10 || !arguments[4].equals("--software-fixture-inputs") || !arguments[8].equals("--output")) {
                throw new IllegalArgumentException("Pinned SDK production inputs, original host fixture inputs and new output required");
            }
            var sdkRef = argumentRef(arguments, 1);
            var sdk = SdkStageConfigurationProducer.readInputs(sdkRef);
            var hostRef = argumentRef(arguments, 5);
            var host = readPinned(hostRef, RootSoftwareFixtureHandoff.Request.class, MAX_CONFIG_BYTES);
            var request = new FixtureProductionRequest(FIXTURE_PRODUCTION_SCHEMA, sdk.machineId(), sdk.reviewAtUtc(), sdkRef, host);
            verifyProductionInputs(request);
            Path output = Path.of(arguments[9]).toAbsolutePath().normalize();
            SharedSourceFiles.plainAncestors(output);
            publish(output, request); sdkRef.verify(); hostRef.verify();
            System.out.println("WROTE_FIXTURE_PRODUCTION_REQUEST " + ControlBuild.strictMapper().writeValueAsString(ControlBuild.FileRef.measure(output))); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-fixture-stage-request")) {
            FixtureWriterInvocation input = fixtureWriterInvocation(arguments);
            CiBootstrap.Plan plan = readPinned(ControlBuild.FileRef.measure(input.planPath()), CiBootstrap.Plan.class, 1L << 20);
            FreshSdkFixtureStage.Config fresh = readPinned(input.freshConfigRef(), FreshSdkFixtureStage.Config.class, MAX_CONFIG_BYTES);
            CanonicalColdWarmStage.Config canonical = readPinned(input.canonicalConfigRef(), CanonicalColdWarmStage.Config.class, MAX_CONFIG_BYTES);
            ControlBuild.FileRef result = writeFixtureRequest(plan, fresh, canonical, input.outputRoot());
            input.freshConfigRef().verify(); input.canonicalConfigRef().verify();
            System.out.println("WROTE_FIXTURE_STAGE_REQUEST " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length == 2 && arguments[0].equals("--verify-static-receipts")) {
            requireCompletedPythonStaticPipeline(Path.of(arguments[1]).toRealPath()); return;
        }
        if (arguments.length == 2 && arguments[0].equals("--verify-reviewed-wal")) {
            System.out.println("ACCEPTED_REVIEWED_WAL " + SupplementalFixtureCi.requireReviewedWalEnvironment(Path.of(arguments[1]).toRealPath(), System.getenv())); return;
        }
        if (arguments.length == 4 && arguments[0].equals("--verify-shared-fixture-junit") && arguments[2].equals("--pytest-stdout")) {
            System.out.println("ACCEPTED_COMPLETE_27 " + SupplementalFixtureCi.requireHaltAndArmyPytest(Path.of(arguments[1]).toRealPath(), Path.of(arguments[3]).toRealPath())); return;
        }
        if (arguments.length == 2 && arguments[0].equals("--verify-shared-fixture-junit")) {
            throw new IOException("Complete selected pytest modules require --pytest-stdout; missing input cannot grant qualification");
        }
        Invocation invocation = invocation(arguments); Path planPath = invocation.planPath();
        if (!"true".equals(System.getenv("GITHUB_ACTIONS"))) throw new IOException("Hosted pipeline execution requires its actual hosted runner; use the typed Root-local entry for local software");
        if (Files.size(planPath) > 1024 * 1024) throw new IOException("Bounded CI plan required");
        CiBootstrap.Plan plan = ControlBuild.strictMapper().readValue(Files.readAllBytes(planPath), CiBootstrap.Plan.class);
        verifyPlan(plan, invocation.toolsReceiptPath() != null);
        if (invocation.fixtureRequestRef() != null) invocation.fixtureRequestRef().verify();
        if (invocation.fixtureProductionRequestRef() != null) readFixtureProductionRequest(invocation.fixtureProductionRequestRef(), plan);
        if (invocation.toolsReceiptPath() == null) qualify(planPath, plan, invocation.fixtureRequestRef(), invocation.fixtureProductionRequestRef());
        else runQualified(planPath, plan, invocation.toolsReceiptPath(), invocation.fixtureRequestRef(), invocation.fixtureProductionRequestRef(), null);
    }

    static Invocation invocation(String[] args) throws IOException {
        if (args.length < 2 || !args[0].equals("--bootstrap-plan")) throw new IllegalArgumentException("Exact bootstrap plan required");
        Path plan = Path.of(args[1]).toRealPath(), tools = null; ControlBuild.FileRef fixtures = null, production = null;
        for (int index = 2; index < args.length; index++) {
            switch (args[index]) {
                case "--qualified-tools-receipt" -> {
                    if (tools != null || ++index >= args.length) throw new IllegalArgumentException("One qualified tools receipt required");
                    tools = Path.of(args[index]).toRealPath();
                }
                case "--fixture-stage-request" -> {
                    if (fixtures != null || index + 3 >= args.length) throw new IllegalArgumentException("One exact fixture request path/bytes/SHA required");
                    String path = Path.of(args[++index]).toRealPath().toString(), bytes = args[++index], sha = args[++index];
                    if (!bytes.matches("[1-9][0-9]{0,8}")) throw new IllegalArgumentException("Bounded decimal fixture request bytes required");
                    fixtures = new ControlBuild.FileRef(path, Long.parseLong(bytes), sha); fixtures.verify();
                }
                case "--fixture-production-request" -> {
                    if (production != null || index + 3 >= args.length) throw new IllegalArgumentException("One exact fixture production request required");
                    production = argumentRef(args, index + 1); index += 3;
                }
                default -> throw new IllegalArgumentException("Unknown CI arguments");
            }
        }
        if (fixtures != null && production != null) throw new IllegalArgumentException("Choose one completed request or one real production request");
        return new Invocation(plan, tools, fixtures, production);
    }

    static FixtureWriterInvocation fixtureWriterInvocation(String[] args) throws IOException {
        if (args.length != 12 || !args[0].equals("--write-fixture-stage-request")
                || !args[2].equals("--fresh-sdk-config") || !args[6].equals("--canonical-config")
                || !args[10].equals("--output-root")) throw new IllegalArgumentException("Exact typed fixture producer arguments required");
        return new FixtureWriterInvocation(Path.of(args[1]).toRealPath(), argumentRef(args, 3),
                argumentRef(args, 7), Path.of(args[11]).toAbsolutePath().normalize());
    }
    private static ControlBuild.FileRef argumentRef(String[] args, int index) throws IOException {
        if (!args[index + 1].matches("[1-9][0-9]{0,7}")) throw new IllegalArgumentException("Bounded positive decimal config bytes required");
        ControlBuild.FileRef ref = new ControlBuild.FileRef(Path.of(args[index]).toRealPath().toString(),
                Long.parseLong(args[index + 1]), args[index + 2]);
        if (ref.bytes() > MAX_CONFIG_BYTES) throw new IOException("Bounded fixture configuration required"); ref.verify(); return ref;
    }
    private static <T> T readPinned(ControlBuild.FileRef ref, Class<T> type, long limit) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > limit) throw new IOException("Bounded pinned JSON required");
        ref.verify(); T value = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(ref.path())), type); ref.verify(); return value;
    }

    private static LocalExecution readRootLocalExecution(ControlBuild.FileRef reference) throws IOException {
        RootLocalPlan local = readPinned(reference, RootLocalPlan.class, 65536);
        var card = readPinned(local.softwareExecutionCardRef(), RootSoftwareExecutionCard.class, 65536);
        var resources = readPinned(card.resourcePlanRef(), CiBootstrap.Plan.class, MAX_CONFIG_BYTES);
        var binding = SharedOwnedCommandBinding.read(card.runtimeBindingRef());
        binding.standingRef().verify(); binding.deliveryRef().verify(); binding.launcherSourceRef().verify();
        var standing = readPinned(binding.standingRef(), com.fasterxml.jackson.databind.JsonNode.class, MAX_CONFIG_BYTES);
        var delivery = readPinned(binding.deliveryRef(), com.fasterxml.jackson.databind.JsonNode.class, MAX_CONFIG_BYTES);
        SharedOwnedCommandBinding.verifyAuthority(standing, binding.standingExpectation(), card.machineId());
        SharedOwnedCommandBinding.verifyAuthority(delivery, binding.deliveryExpectation(), card.machineId());
        if (!card.machineId().equals(WindowsJobProcess.currentMachineId()) || !card.machineId().equals(binding.machineId())
                || !card.machineId().equals(resources.machineId()) || !card.ownerTask().equals(resources.ownerTask())
                || !card.observedAtUtc().equals(resources.observedAtUtc()) || !card.reviewAtUtc().equals(resources.reviewAtUtc())
                || !CiBootstrap.PLAN_SCHEMA.equals(resources.schema())
                || Instant.parse(card.reviewAtUtc()).isAfter(Instant.parse(jsonText(standing, "review_at_utc")))) {
            throw new IOException("Root software card does not match its actual local resources and current runtime window");
        }
        requireRootSlot(resources, card, standing);
        var tools = ControlBuild.acceptedReceipt(Path.of(card.toolsBuildReceiptRef().path()));
        var reactor = ControlBuild.acceptedReceipt(Path.of(card.reactorBuildReceiptRef().path()));
        var loaded = ControlBuild.producerClosure();
        if (tools.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME || !tools.completeDeployment().equals(loaded)
                || reactor.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR || reactor.sourceLimitProfile() != card.sourceLimitProfile()
                || !reactor.machineId().equals(card.machineId()) || !tools.machineId().equals(card.machineId())
                || !runtimeRef(standing, "qualified_tools_ref").equals(card.toolsBuildReceiptRef())
                || !runtimeRefs(standing, "runtime_closure").equals(loaded) || !runtimeRefs(delivery, "complete_runtime").equals(loaded)
                || !resources.bootstrapRuntimeClosure().stream().map(ControlCi::ref).sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList().equals(loaded)
                || !resources.sourcePins().stream().map(ControlCi::ref).sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList().equals(tools.sourcePins())) {
            throw new IOException("Only exact qualified tools and the accepted normal selected G2 reactor may enter local software validation");
        }
        card.toolsBuildReceiptRef().verify(); card.reactorBuildReceiptRef().verify(); card.capacityReleaseRef().verify();
        requireJUnit(Path.of(tools.deploymentRoot()).resolve("surefire-reports"), tools);
        var production = readFixtureProductionRequest(local.fixtureProductionRequestRef(), resources);
        var sdk = SdkStageConfigurationProducer.readInputs(production.sdkProductionInputsRef());
        if (!sdk.fresh().executionCardRef().equals(local.softwareExecutionCardRef())
                || !sdk.canonical().executionCardRef().equals(local.softwareExecutionCardRef())) {
            throw new IOException("Both complete SDK groups must consume the same issued Root software card");
        }
        var result = new LocalExecution(reference, local, card); revalidateLocalExecution(result); return result;
    }

    static void requireRootSlot(CiBootstrap.Plan resources, RootSoftwareExecutionCard card,
            com.fasterxml.jackson.databind.JsonNode standing) throws IOException {
        var timing = CiBootstrap.pipelineTiming(resources); timing.remainingWork(Instant.now());
        com.fasterxml.jackson.databind.JsonNode slot = null;
        var slots = standing.get("slots");
        if (slots == null || !slots.isArray() || slots.size() > 64) throw new IOException("Explicit finite runtime slots required");
        for (var candidate : slots) if (card.slotId().equals(jsonText(candidate, "slot_id"))) {
            if (slot != null) throw new IOException("Duplicate admitted Root software slot"); slot = candidate;
        }
        if (slot == null || !card.ownerTask().equals(jsonText(slot, "coordinator"))
                || Duration.between(timing.observedAt(), timing.outerDeadline()).compareTo(Duration.ofSeconds(jsonLong(slot, "timeout_seconds"))) > 0
                || !Path.of(resources.workRoot()).toAbsolutePath().normalize().startsWith(Path.of(jsonText(slot, "output_root")).toAbsolutePath().normalize())) {
            throw new IOException("The actual standing slot cannot admit this whole software deadline or output root");
        }
    }

    private static String jsonText(com.fasterxml.jackson.databind.JsonNode object, String field) throws IOException {
        var value = object == null ? null : object.get(field);
        if (value == null || !value.isTextual() || value.textValue().isBlank()) throw new IOException("Exact runtime string required: " + field);
        return value.textValue();
    }
    private static long jsonLong(com.fasterxml.jackson.databind.JsonNode object, String field) throws IOException {
        var value = object == null ? null : object.get(field);
        if (value == null || !value.isIntegralNumber() || !value.canConvertToLong() || value.longValue() <= 0) throw new IOException("Exact positive runtime integer required: " + field);
        return value.longValue();
    }
    private static List<ControlBuild.FileRef> runtimeRefs(com.fasterxml.jackson.databind.JsonNode object, String field) throws IOException {
        var values = object.get(field); if (values == null || !values.isArray() || values.size() != 6) throw new IOException("Complete exact six-piece runtime required");
        List<ControlBuild.FileRef> result = new ArrayList<>();
        for (var value : values) { var ref = ControlBuild.strictMapper().treeToValue(value, ControlBuild.FileRef.class); ref.verify(); result.add(ref); }
        return result.stream().sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList();
    }
    private static ControlBuild.FileRef runtimeRef(com.fasterxml.jackson.databind.JsonNode object, String field) throws IOException {
        var value = object.get(field); if (value == null || !value.isObject()) throw new IOException("Exact runtime reference required: " + field);
        var result = ControlBuild.strictMapper().treeToValue(value, ControlBuild.FileRef.class); result.verify(); return result;
    }
    private static void revalidateLocalExecution(LocalExecution local) throws IOException {
        local.planRef().verify(); local.plan().softwareExecutionCardRef().verify(); local.plan().fixtureProductionRequestRef().verify();
        var card = local.card(); card.resourcePlanRef().verify(); card.runtimeBindingRef().verify(); card.capacityReleaseRef().verify();
        if (!Instant.now().isBefore(Instant.parse(card.reviewAtUtc()))) throw new IOException("Root-local software card expired");
        var binding = SharedOwnedCommandBinding.read(card.runtimeBindingRef()); binding.standingRef().verify(); binding.deliveryRef().verify();
    }
    private static void prepareLocalWorkRoot(CiBootstrap.Plan resources) throws IOException {
        Path work = Path.of(resources.workRoot()).toAbsolutePath().normalize(), repo = Path.of(resources.repoRoot()).toRealPath();
        if (work.startsWith(repo) || repo.startsWith(work)) throw new IOException("Root software metadata must remain outside canonical source");
        SharedSourceFiles.plainAncestors(work);
        if (!Files.exists(work, java.nio.file.LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(work);
        for (String part : List.of("m2", "build", "tools", "scratch", "logs", "artifacts")) {
            Path path = work.resolve(part); SharedSourceFiles.plainAncestors(path);
            if (!Files.exists(path, java.nio.file.LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(path);
            else if (!Files.isDirectory(path, java.nio.file.LinkOption.NOFOLLOW_LINKS)) throw new IOException("Plain admitted local work part required");
        }
    }

    static List<ReactorTestClosure.RequiredSuite> httpRequirements(ControlBuild.SourceLimitProfile profile) {
        return switch (profile) {
            case G2_RESEARCH_20261023 -> ReactorTestClosure.g2HttpRequirements();
            case G2_STABILIZATION_20261023 -> ReactorTestClosure.g2StabilizationHttpRequirements();
            case G2_FULL_PARITY_20261024 -> ReactorTestClosure.g2FullParityRequirements();
            case G2_FULL_PARITY_20261024_R2 -> ReactorTestClosure.g2FullParityResumeRequirements();
            case G2_FULL_PARITY_20261024_R3 -> ReactorTestClosure.g2FullParityCurrentRequirements();
            default -> throw new IllegalArgumentException("Explicit complete selected G2 profile required for HTTP report closure");
        };
    }

    /** A full migration claim must use actual original fixture production and its retained host. */
    static void requireFullParityFixtureProduction(ControlBuild.SourceLimitProfile profile,
            ControlBuild.FileRef productionRequest) throws IOException {
        if (profile.fullParity()) {
            if (productionRequest == null) {
                throw new IOException("NOT EXECUTED: full parity requires the actual fixture-production request; fresh SDK and complete cold/warm cannot be omitted");
            }
            productionRequest.verify();
            if (profile == ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3
                    && !(readProductionContract(productionRequest) instanceof CurrentFixtureProductionRequest)) {
                throw new IOException("NOT EXECUTED: R3 requires its explicit current full fixture-production contract");
            }
        }
    }

    /** Produce configuration metadata only; stage execution and accepted actuals remain separate. */
    public static ControlBuild.FileRef writeFixtureRequest(CiBootstrap.Plan plan, FreshSdkFixtureStage.Config fresh,
            CanonicalColdWarmStage.Config canonical, Path outputRoot) throws IOException {
        verifyPlan(plan, true);
        return writeBoundFixtureRequest(plan, fresh, canonical, outputRoot);
    }
    private static ControlBuild.FileRef writeBoundFixtureRequest(CiBootstrap.Plan plan, FreshSdkFixtureStage.Config fresh,
            CanonicalColdWarmStage.Config canonical, Path outputRoot) throws IOException {
        CiBootstrap.PipelineTiming timing = CiBootstrap.pipelineTiming(plan);
        String review = timing.workDeadline().toString();
        requireFixtureBindings(plan, review, fresh, canonical);
        Path artifacts = Path.of(plan.workRoot()).resolve("artifacts").toRealPath();
        Path output = outputRoot.toAbsolutePath().normalize();
        if (!output.getParent().toRealPath().equals(artifacts)
                || output.equals(Path.of(fresh.workRoot()).toAbsolutePath().normalize())
                || output.equals(Path.of(canonical.workRoot()).toAbsolutePath().normalize())) throw new IOException("New distinct direct artifact child required");
        return writeFixtureDocuments(output, plan.machineId(), review, fresh, canonical, () -> {
            timing.remainingWork(Instant.now()); requireFixtureBindings(plan, review, fresh, canonical);
        });
    }

    static ControlBuild.FileRef writeFixtureDocuments(Path output, String machine, String review,
            FreshSdkFixtureStage.Config fresh, CanonicalColdWarmStage.Config canonical, CiBootstrap.IoGuard guard) throws IOException {
        byte[] freshBytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(fresh);
        byte[] canonicalBytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(canonical);
        if (freshBytes.length > MAX_CONFIG_BYTES || canonicalBytes.length > MAX_CONFIG_BYTES) throw new IOException("Bounded serialized stage configurations required");
        guard.check(); Files.createDirectory(output);
        Path freshPath = output.resolve("fresh-sdk-config.json"), canonicalPath = output.resolve("canonical-config.json");
        guard.check(); Files.write(freshPath, freshBytes, StandardOpenOption.CREATE_NEW);
        guard.check(); Files.write(canonicalPath, canonicalBytes, StandardOpenOption.CREATE_NEW);
        var request = new FixtureRequest(FIXTURE_REQUEST_SCHEMA, machine, review,
                ControlBuild.FileRef.measure(freshPath), ControlBuild.FileRef.measure(canonicalPath));
        byte[] requestBytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(request);
        if (requestBytes.length > 65536) throw new IOException("Bounded serialized fixture request required");
        guard.check(); Path requestPath = output.resolve("fixture-stage-request.json");
        Files.write(requestPath, requestBytes, StandardOpenOption.CREATE_NEW);
        request.freshSdkConfigRef().verify(); request.canonicalConfigRef().verify();
        guard.check(); return ControlBuild.FileRef.measure(requestPath);
    }

    private static void verifyPlan(CiBootstrap.Plan plan, boolean qualifiedInvocation) throws IOException {
        if (!CiBootstrap.PLAN_SCHEMA.equals(plan.schema()) || !plan.machineId().equals(WindowsJobProcess.currentMachineId())
                || !Instant.now().isBefore(Instant.parse(plan.reviewAtUtc())) || plan.bootstrapRuntimeClosure().isEmpty()
                || plan.sourcePins().isEmpty()) throw new IOException("Current complete bootstrap plan required");
        CiBootstrap.pipelineTiming(plan).remainingWork(Instant.now());
        for (CiBootstrap.FilePin pin : plan.sourcePins()) ref(pin).verify();
        for (CiBootstrap.FilePin pin : plan.bootstrapRuntimeClosure()) ref(pin).verify();
        List<ControlBuild.FileRef> expected = plan.sourcePins().stream().map(ControlCi::ref).sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList();
        if (!expected.equals(ControlBuild.sourceManifest(Path.of(plan.repoRoot()).resolve("java/ck3-control/build-tools")))) {
            throw new IOException("Bootstrap source closure changed or grew");
        }
        if (!qualifiedInvocation && !ControlBuild.producerClosure().equals(plan.bootstrapRuntimeClosure().stream().map(ControlCi::ref).sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList())) {
            throw new IOException("Current bootstrap runtime differs from plan");
        }
    }

    private static void qualify(Path planPath, CiBootstrap.Plan plan, ControlBuild.FileRef fixtureRequest,
            ControlBuild.FileRef fixtureProduction) throws IOException, InterruptedException {
        Path root = Path.of(plan.workRoot());
        Path releasePath = root.resolve("logs/ci-capacity-release.json");
        CiBootstrap.PipelineTiming timing = CiBootstrap.pipelineTiming(plan);
        timing.remainingWork(Instant.now());
        ControlBuild.CapacityRelease release = ControlBuild.ciCapacityRelease(CiBootstrap.pipelineExecutionPlan(plan));
        publish(releasePath, release);
        Path toolsSource = Path.of(plan.repoRoot()).resolve("java/ck3-control/build-tools");
        ControlBuild.BuildReceipt tools = ControlBuild.build(config(plan, toolsSource, releasePath, "qualified-tools", ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME));
        if (!tools.status().equals("PASS")) throw new IOException("Native Job tools qualification failed");
        Path toolsReceipt = root.resolve("logs/build-qualified-tools.json");
        requireJUnit(Path.of(tools.deploymentRoot()).resolve("surefire-reports"), tools);
        List<String> arguments = new ArrayList<>(List.of("-Xms32m", "-Xmx128m", "-XX:MaxMetaspaceSize=96m",
                "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m", "-Djava.io.tmpdir=" + root.resolve("scratch"),
                "-Djna.tmpdir=" + root.resolve("scratch"), "-cp",
                Path.of(tools.deploymentRoot()).resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar").toString(),
                ControlCi.class.getName(), "--bootstrap-plan", planPath.toString(), "--qualified-tools-receipt", toolsReceipt.toString()));
        forwardFixtureRequests(arguments, fixtureRequest, fixtureProduction);
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.remove("JAVA_TOOL_OPTIONS"); environment.remove("JDK_JAVA_OPTIONS");
        environment.putAll(CanonicalOracleEnvironment.bind(Path.of(plan.repoRoot()), Path.of(plan.pythonExecutable()), environment));
        environment.put("XAR_MACHINE_ID", plan.machineId());
        for (String name : List.of("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")) environment.put(name, "1");
        environment.put("TEMP", root.resolve("scratch").toString()); environment.put("TMP", root.resolve("scratch").toString());
        WindowsJobProcess.CommandResult result;
        Duration remaining = timing.remainingWork(Instant.now());
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(plan.javaHome()).resolve("bin/java.exe"), arguments,
                Path.of(plan.repoRoot()), environment, root.resolve("logs/qualified-control.stdout.log"),
                root.resolve("logs/qualified-control.stderr.log"), 2L << 30))) {
            result = child.await(remaining, timing.workDeadline(), () -> {});
        }
        publish(root.resolve("logs/control-ci-bootstrap-terminal.json"), result);
        if (!result.passed()) throw new IOException("Qualified Java pipeline did not exit cleanly: " + result);
    }

    static void forwardFixtureRequests(List<String> arguments, ControlBuild.FileRef completed, ControlBuild.FileRef production) throws IOException {
        if (completed != null && production != null) throw new IllegalArgumentException("One fixture execution route required");
        ControlBuild.FileRef selected = completed == null ? production : completed;
        if (selected == null) return;
        selected.verify();
        arguments.addAll(List.of(completed == null ? "--fixture-production-request" : "--fixture-stage-request",
                selected.path(), Long.toString(selected.bytes()), selected.sha256()));
    }

    private static void runQualified(Path planPath, CiBootstrap.Plan plan, Path toolsReceiptPath,
            ControlBuild.FileRef fixtureRequestRef, ControlBuild.FileRef fixtureProductionRef, LocalExecution local) throws IOException, InterruptedException {
        String started = Instant.now().toString(); Path root = Path.of(plan.workRoot());
        CiBootstrap.PipelineTiming timing = CiBootstrap.pipelineTiming(plan);
        Path releasePath = local == null ? root.resolve("logs/ci-capacity-release.json") : Path.of(local.card().capacityReleaseRef().path());
        ControlBuild.BuildReceipt tools = ControlBuild.acceptedReceipt(toolsReceiptPath);
        if (tools.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME || !tools.completeDeployment().equals(ControlBuild.producerClosure())) {
            throw new IOException("Actual running qualified jar/lib must exactly equal the qualified build closure");
        }
        ControlBuild.FileRef planRef = ControlBuild.FileRef.measure(planPath), releaseRef = ControlBuild.FileRef.measure(releasePath), toolsRef = ControlBuild.FileRef.measure(toolsReceiptPath);
        String failure = null; ControlBuild.FileRef reactorRef = null, consumerRef = null, supplementalRef = null, reactorClosureRef = null;
        List<ControlBuild.FileRef> staticRefs = new ArrayList<>();
        List<StageActual> stages = initialStages(); Stage current = null; Path currentEvidence = null;
        MapAdmissionCi.Session retainedService = null;
        boolean complete = false;
        try {
            if (local == null) {
                current = Stage.EXPECTED_MAVEN_RED; currentEvidence = root.resolve("logs/build-ci-expected-maven-red.json"); start(stages, current);
                ControlBuild.FileRef expectedMavenRef = requireExpectedMavenFailure(plan, releasePath); pass(stages, current, expectedMavenRef);
            } else readRootLocalExecution(local.planRef());
            current = Stage.REACTOR; currentEvidence = root.resolve("logs/build-ci-reactor.json"); start(stages, current);
            requireFullParityFixtureProduction(local == null ? ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3
                    : local.card().sourceLimitProfile(), fixtureProductionRef);
            Path reactorPath = local == null ? root.resolve("logs/build-ci-reactor.json") : Path.of(local.card().reactorBuildReceiptRef().path());
            ControlBuild.BuildReceipt reactor = local == null ? ControlBuild.build(config(plan, Path.of(plan.repoRoot()).resolve("java/ck3-control"),
                    releasePath, "ci-reactor", ControlBuild.TargetKind.SERVICE_FAST_JAR)) : ControlBuild.acceptedReceipt(reactorPath);
            reactorRef = ControlBuild.FileRef.measure(reactorPath);
            if (!reactor.status().equals("PASS")) throw new IOException("Complete reactor failed");
            requireCurrentFixtureExecution(reactor, fixtureProductionRef);
            pass(stages, current, reactorRef);
            current = Stage.REACTOR_TEST_CLOSURE; currentEvidence = root.resolve("logs/reactor-test-closure.json"); start(stages, current);
            var requirements = httpRequirements(reactor.sourceLimitProfile());
            reactorClosureRef = ReactorTestClosure.run(reactorPath, currentEvidence, requirements);
            if (!reactorClosureRef.equals(ReactorTestClosure.requireAccepted(currentEvidence, reactorPath, requirements))) throw new IOException("Reactor report closure changed before pipeline adoption");
            pass(stages, current, reactorClosureRef);
            current = Stage.MAP_CONSUMERS; currentEvidence = root.resolve("artifacts/map-ci/logs/actual.json"); start(stages, current);
            var mapConfig = new MapAdmissionCi.Config(Path.of(plan.repoRoot()), reactorPath, root.resolve("artifacts/map-ci"),
                    Path.of(plan.javaHome()).resolve("bin/java.exe"), Path.of(plan.pythonExecutable()), timing.workDeadline(), 8089);
            if (fixtureProductionRef == null) MapAdmissionCi.run(mapConfig);
            else {
                var production = readFixtureProductionRequest(fixtureProductionRef, plan);
                retainedService = MapAdmissionCi.retainForSoftwareFixtures(mapConfig, production.softwareFixture());
            }
            consumerRef = ControlBuild.FileRef.measure(root.resolve("artifacts/map-ci/logs/actual.json"));
            pass(stages, current, consumerRef);
            for (var kind : PythonBoundaryStaticStage.Kind.values()) {
                current = kind == PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED ? Stage.SDK_SENTINEL_STATIC : Stage.MONTHLY_STATIC;
                currentEvidence = pythonStaticRoot(root, kind).resolve("actual.json"); start(stages, current);
                ControlBuild.FileRef ref = PythonBoundaryStaticStage.run(new PythonBoundaryStaticStage.Config(kind,
                        Path.of(plan.repoRoot()), pythonStaticRoot(root, kind), Path.of(plan.pythonExecutable()),
                        root.resolve("scratch"), timing.workDeadline(), plan.machineId()));
                staticRefs.add(ref); pass(stages, current, ref);
            }
            requirePythonStaticReceipts(root);
            current = Stage.SUPPLEMENTAL; currentEvidence = root.resolve("artifacts/supplemental-fixtures/actual.json"); start(stages, current);
            supplementalRef = SupplementalFixtureCi.run(new SupplementalFixtureCi.Config(Path.of(plan.repoRoot()),
                    root.resolve("artifacts/supplemental-fixtures"), Path.of(plan.pythonExecutable()), root.resolve("scratch"),
                    timing.workDeadline(), plan.machineId(), null));
            pass(stages, current, supplementalRef);
            if (fixtureRequestRef != null || fixtureProductionRef != null) {
                current = Stage.FRESH_SDK; currentEvidence = null; start(stages, current);
                if (fixtureProductionRef != null) {
                    if (retainedService == null) throw new IOException("Fixture production requires the original retained host");
                    fixtureRequestRef = produceFixtureRequest(plan, reactorRef, fixtureProductionRef, retainedService, releasePath, local);
                }
                FixtureRequest request = readFixtureRequest(fixtureRequestRef, plan);
                FreshSdkFixtureStage.Config fresh = readPinned(request.freshSdkConfigRef(), FreshSdkFixtureStage.Config.class, MAX_CONFIG_BYTES);
                CanonicalColdWarmStage.Config canonical = readPinned(request.canonicalConfigRef(), CanonicalColdWarmStage.Config.class, MAX_CONFIG_BYTES);
                requireFixtureBindings(plan, request, fresh, canonical);
                if (!fresh.deploymentReceiptRef().equals(reactorRef)) throw new IOException("Requested SDK view must consume this pipeline's accepted reactor");
                final ControlBuild.FileRef selectedRequestRef = fixtureRequestRef;
                final MapAdmissionCi.Session sameHost = retainedService;
                FreshSdkFixtureStage.ResourceGuard guard = pending -> {
                    timing.remainingWork(Instant.now());
                    selectedRequestRef.verify();
                    if (fixtureProductionRef != null) fixtureProductionRef.verify();
                    if (local != null) revalidateLocalExecution(local);
                    if (sameHost != null) { sameHost.requireCurrent(); sameHost.verifyImmutableInputs(); }
                    if (!Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))) throw new IOException("Fixture request expired");
                    ControlBuild.revalidateCiResources(plan, releasePath, pending);
                };
                currentEvidence = Path.of(fresh.workRoot()).resolve("actual.json");
                pass(stages, current, FreshSdkFixtureStage.run(fresh, guard));
                current = Stage.CANONICAL_THIRTY; currentEvidence = Path.of(canonical.workRoot()).resolve("actual.json"); start(stages, current);
                pass(stages, current, CanonicalColdWarmStage.run(canonical, guard));
                fixtureRequestRef.verify(); request.freshSdkConfigRef().verify(); request.canonicalConfigRef().verify();
            }
            if (retainedService != null) {
                retainedService.verifyImmutableInputs(); retainedService.close(); retainedService = null;
            }
            complete = true;
        } catch (IOException | RuntimeException error) { failure = error.getClass().getSimpleName() + ": " + error.getMessage(); }
        finally {
            if (retainedService != null) {
                try { retainedService.close(); }
                catch (RuntimeException cleanup) { failure = append(failure, "Original host closure failed: " + cleanup.getMessage()); }
            }
            if (!complete && failure == null) failure = "Pipeline did not complete all validation and cleanup";
            if (current != null && stages.get(current.ordinal()).state() == StageState.STARTED) {
                ControlBuild.FileRef retained = null;
                try { if (currentEvidence != null && Files.isRegularFile(currentEvidence, java.nio.file.LinkOption.NOFOLLOW_LINKS)) retained = ControlBuild.FileRef.measure(currentEvidence); }
                catch (IOException unavailable) { failure = append(failure, "Actual stage evidence reference unavailable: " + unavailable.getMessage()); }
                stages.set(current.ordinal(), new StageActual(current, StageState.RED, retained, failure));
            }
            publish(root.resolve("logs/control-ci-actual.json"), new Receipt(ACTUAL_SCHEMA, plan.machineId(), started, Instant.now().toString(),
                    complete && failure == null ? PipelineState.PASS : PipelineState.RED, failure, planRef, releaseRef,
                    toolsRef, null, reactorRef, consumerRef, List.copyOf(staticRefs), supplementalRef,
                    reactorClosureRef, fixtureRequestRef, fixtureProductionRef,
                    local == null ? ExecutionPurpose.HOSTED_CI : ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, local == null ? null : local.planRef(), stages));
        }
        if (!complete || failure != null) throw new IOException(failure);
    }

    /** Execute the original failing producer path, not just the source-postcheck helper. */
    private static ControlBuild.FileRef requireExpectedMavenFailure(CiBootstrap.Plan plan, Path release) throws IOException, InterruptedException {
        Path fixture = Path.of(plan.repoRoot()).resolve("java/ck3-control/build-tools/src/test/resources/maven-failure");
        ControlBuild.BuildReceipt actual = ControlBuild.build(config(plan, fixture, release, "ci-expected-maven-red", ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME));
        requireExpectedMavenOutcome(actual);
        return ControlBuild.FileRef.measure(Path.of(plan.workRoot()).resolve("logs/build-ci-expected-maven-red.json"));
    }
    private static void requireExpectedMavenOutcome(ControlBuild.BuildReceipt actual) throws IOException {
        if (!actual.status().equals("RED") || actual.mavenResult() == null || actual.mavenResult().exitCode() == 0
                || actual.mavenResult().accounting().activeProcesses() != 0 || actual.mavenResult().stopReason() != null
                || actual.sourcePostcheck().state() != ControlBuild.SourceState.MATCH
                || actual.compiledSourcePostcheck().state() != ControlBuild.SourceState.MATCH) {
            throw new IOException("Expected real Maven model failure lost its terminal result or actual source postchecks");
        }
    }

    static List<StageActual> initialStages() {
        List<StageActual> stages = new ArrayList<>();
        for (Stage stage : Stage.values()) stages.add(new StageActual(stage, StageState.NOT_RUN, null, null)); return stages;
    }
    private static void start(List<StageActual> stages, Stage stage) { stages.set(stage.ordinal(), new StageActual(stage, StageState.STARTED, null, null)); }
    private static void pass(List<StageActual> stages, Stage stage, ControlBuild.FileRef evidence) { stages.set(stage.ordinal(), new StageActual(stage, StageState.PASS, evidence, null)); }
    private static String append(String current, String next) { return current == null ? next : current + "; " + next; }

    static FixtureRequest readFixtureRequest(ControlBuild.FileRef ref, CiBootstrap.Plan plan) throws IOException {
        FixtureRequest request = readPinned(ref, FixtureRequest.class, 65536);
        if (!request.machineId().equals(plan.machineId()) || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))
                || Instant.parse(request.reviewAtUtc()).isAfter(CiBootstrap.pipelineTiming(plan).workDeadline())) throw new IOException("Fixture request machine/deadline differs from current pipeline");
        for (var config : List.of(request.freshSdkConfigRef(), request.canonicalConfigRef())) {
            if (config.bytes() > MAX_CONFIG_BYTES) throw new IOException("Bounded stage configuration required"); config.verify();
        }
        requireFixtureBindings(plan, request,
                readPinned(request.freshSdkConfigRef(), FreshSdkFixtureStage.Config.class, MAX_CONFIG_BYTES),
                readPinned(request.canonicalConfigRef(), CanonicalColdWarmStage.Config.class, MAX_CONFIG_BYTES));
        return request;
    }

    static FixtureProductionInputs readFixtureProductionRequest(ControlBuild.FileRef ref, CiBootstrap.Plan plan) throws IOException {
        FixtureProductionInputs request = readProductionContract(ref);
        verifyProductionInputs(request);
        var sdk = SdkStageConfigurationProducer.readInputs(request.sdkProductionInputsRef());
        if (!request.machineId().equals(plan.machineId())
                || Instant.parse(request.reviewAtUtc()).isAfter(CiBootstrap.pipelineTiming(plan).workDeadline())
                || !sdk.interpreter().pythonExecutable().equals(ControlBuild.FileRef.measure(Path.of(plan.pythonExecutable())))) {
            throw new IOException("Fixture production must use this pipeline machine, interpreter and shared deadline");
        }
        return request;
    }

    static FixtureProductionInputs readProductionContract(ControlBuild.FileRef ref) throws IOException {
        if (ref.bytes() <= 0 || ref.bytes() > MAX_CONFIG_BYTES) throw new IOException("Bounded fixture production contract required");
        ref.verify(); var node = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(ref.path())));
        String schema = jsonText(node, "schema");
        FixtureProductionInputs result = switch (schema) {
            case FIXTURE_PRODUCTION_SCHEMA -> ControlBuild.strictMapper().treeToValue(node, FixtureProductionRequest.class);
            case CURRENT_FIXTURE_PRODUCTION_SCHEMA -> ControlBuild.strictMapper().treeToValue(node, CurrentFixtureProductionRequest.class);
            default -> throw new IOException("Unknown fixture production contract generation");
        };
        ref.verify(); return result;
    }
    private static void verifyProductionInputs(FixtureProductionInputs request) throws IOException {
        var sdk = SdkStageConfigurationProducer.readInputs(request.sdkProductionInputsRef());
        if (!request.machineId().equals(WindowsJobProcess.currentMachineId()) || !request.machineId().equals(sdk.machineId())
                || !request.reviewAtUtc().equals(sdk.reviewAtUtc()) || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))) {
            throw new IOException("One current source-bound SDK/host production input required");
        }
        for (var input : SdkStageConfigurationProducer.inputRefs(sdk)) input.verify();
        for (var input : request.softwareFixture().originalFixtureRefs()) input.verify();
        for (var input : request.softwareFixture().originalRequestRefs()) input.verify();
        request.softwareFixture().probeRequestRef().verify(); request.softwareFixture().probePayloadRef().verify();
        if (request instanceof CurrentFixtureProductionRequest current) {
            var oracle = FullParityCurrentBindings.readInputs(current.currentOracleInputsRef()); FullParityCurrentBindings.verify(oracle);
            if (!oracle.machineId().equals(request.machineId()) || !oracle.pythonRef().equals(sdk.interpreter().pythonExecutable())) {
                throw new IOException("One actual interpreter and machine must bind SDK, host and all R3 oracle inputs");
            }
        }
    }
    private static void requireCurrentFixtureExecution(ControlBuild.BuildReceipt reactor, ControlBuild.FileRef productionRef) throws IOException {
        if (reactor.sourceLimitProfile() != ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3) return;
        if (productionRef == null || !(readProductionContract(productionRef) instanceof CurrentFixtureProductionRequest current)) throw new IOException("R3 actual lacks its exact current production inputs");
        var executed = FullParityCurrentBindings.completedBuildBindings(reactor);
        if (!executed.inputsRef().equals(current.currentOracleInputsRef())) throw new IOException("Executed Maven command selected a different current oracle input file");
        FullParityCurrentBindings.requireExecutedInputs(FullParityCurrentBindings.readInputs(current.currentOracleInputsRef()), executed);
    }

    private static ControlBuild.FileRef produceFixtureRequest(CiBootstrap.Plan plan, ControlBuild.FileRef reactor,
            ControlBuild.FileRef productionRef, MapAdmissionCi.Session service, Path release, LocalExecution local) throws IOException {
        var production = readFixtureProductionRequest(productionRef, plan);
        var inputs = SdkStageConfigurationProducer.readInputs(production.sdkProductionInputsRef());
        service.verifyImmutableInputs();
        var host = service.softwareFixtureAdmission();
        if (!host.buildReceiptRef().equals(reactor)
                || !host.programRef().equals(service.projectionAdmission().programRef())
                || !host.serviceEvidenceRef().equals(service.projectionAdmission().serviceEvidenceRef())) {
            throw new IOException("SDK fixture must use the one retained host and this actual reactor");
        }
        var timing = CiBootstrap.pipelineTiming(plan);
        FreshSdkFixtureStage.ResourceGuard guard = pending -> {
            timing.remainingWork(Instant.now()); productionRef.verify(); production.sdkProductionInputsRef().verify();
            if (local != null) revalidateLocalExecution(local);
            service.requireCurrent(); service.verifyImmutableInputs(); ControlBuild.revalidateCiResources(plan, release, pending);
        };
        Path artifacts = Path.of(plan.workRoot()).resolve("artifacts"), output = artifacts.resolve("sdk-stage-production");
        var configs = SdkStageConfigurationProducer.produce(inputs, reactor, host, output,
                sdkCapacityGate(plan, release, productionRef, inputs, output, guard), (selection, admitted, destination) -> {
                    guard.revalidate(0); service.verifyImmutableInputs();
                    if (!host.equals(admitted)) throw new IOException("Root bootstrap cannot switch its admitted host");
                    var bootstrap = new RootSoftwareChildBootstrap.Configuration(RootSoftwareChildBootstrap.SCHEMA,
                            RootSoftwareChildBootstrap.SCOPE, plan.machineId(), "control-ci:" + plan.observedAtUtc(),
                            new RootSoftwareChildBootstrap.ServiceProof(host.serviceEvidenceRef(), selection.owner().source(), selection.client().source()),
                            selection.sdkLineageBinding(), selection.client(), selection.continuity(), selection.owner(), host.originRef(), host.probeRequestRef(), host.probePayloadRef(),
                            host.originalFixtureRefs(), selection.environment());
                    var ref = RootSoftwareChildBootstrap.writeConfiguration(bootstrap, destination);
                    guard.revalidate(0); service.verifyImmutableInputs(); return ref;
                }, guard);
        service.verifyImmutableInputs();
        for (var input : configs.inputRefs()) input.verify();
        var request = local == null ? writeFixtureRequest(plan, configs.fresh(), configs.canonical(), artifacts.resolve("fixture-stage-request"))
                : writeBoundFixtureRequest(plan, configs.fresh(), configs.canonical(), artifacts.resolve("fixture-stage-request"));
        service.verifyImmutableInputs(); guard.revalidate(0); return request;
    }

    private record SdkStorageObservation(String schema, String machineId, String observedAtUtc, String reviewAtUtc,
            ControlBuild.FileRef capacityReleaseRef, ControlBuild.FileRef productionInputRef, String exactOutputRoot,
            long usableBytes, long allocationUnitBytes, long perDirectoryGuardBytes, long allocationUpperLimitBytes,
            long existingArtifactBytes, long pendingViewLogicalUpperBytes) { }

    private static SdkSourceAssembly.SharedCapacityGate sdkCapacityGate(CiBootstrap.Plan plan, Path release,
            ControlBuild.FileRef productionRef, SdkStageConfigurationProducer.ProductionInputs inputs, Path output,
            FreshSdkFixtureStage.ResourceGuard guard) {
        return new SdkSourceAssembly.SharedCapacityGate() {
            @Override public SdkSourceAssembly.WritePermit acquire(SdkSourceAssembly.SharedQuote quote, ControlBuild.FileRef request) throws IOException {
                guard.revalidate(0); request.verify();
                Path group = Path.of(quote.groupRoot()).toRealPath();
                Long artifactCap = plan.parts().get("artifacts");
                if (!group.startsWith(output.toRealPath()) || group.equals(output.toRealPath())
                        || !quote.machineId().equals(plan.machineId()) || artifactCap == null
                        || inputs.sharedViewPhysicalHardBytes() > artifactCap
                        || quote.cumulativePhysicalHardBytes() > inputs.sharedViewPhysicalHardBytes()) {
                    throw new IOException("SDK views must remain inside this admitted artifact part and its explicit physical bound");
                }
                long existing = ControlBuild.mutableInventoryBytes(Path.of(plan.workRoot()).resolve("artifacts"),
                        path -> CiBootstrap.pipelineTiming(plan).remainingWork(Instant.now()));
                long pending = Math.addExact(quote.allViewLogicalBytes(), Math.addExact(quote.metadataHardBytes(),
                        Math.multiplyExact((long) quote.directories(), inputs.perDirectoryGuardBytes())));
                if (Math.addExact(existing, pending) > artifactCap) throw new IOException("Current artifact part cannot admit the complete three-view logical forecast");
                var store = Files.getFileStore(group);
                long usable = store.getUsableSpace(), unit = store.getBlockSize();
                if (unit != inputs.allocationUnitBytes() || usable < inputs.sharedViewPhysicalHardBytes()) {
                    throw new IOException("Actual output filesystem geometry or free capacity differs from reviewed SDK inputs");
                }
                Path evidence = output.resolve("shared-storage-observation.json");
                publish(evidence, new SdkStorageObservation("xar.sdk-CI-live-storage/v1", plan.machineId(), Instant.now().toString(),
                        inputs.reviewAtUtc(), ControlBuild.FileRef.measure(release), productionRef, group.toString(), usable, unit,
                        inputs.perDirectoryGuardBytes(), inputs.sharedViewPhysicalHardBytes(), existing, pending));
                guard.revalidate(0);
                return new SdkSourceAssembly.WritePermit(plan.machineId(), group.toString(), inputs.reviewAtUtc(),
                        inputs.sharedViewPhysicalHardBytes(), unit, inputs.perDirectoryGuardBytes(), ControlBuild.FileRef.measure(evidence));
            }
            @Override public void revalidate(SdkSourceAssembly.WritePermit permit, long consumed) throws IOException {
                guard.revalidate(0); permit.freshStorageEvidence().verify();
                if (!permit.machineId().equals(plan.machineId()) || !Instant.now().isBefore(Instant.parse(permit.expiresAtUtc()))
                        || consumed < 0 || consumed > permit.allocationUpperLimitBytes()
                        || permit.allocationUpperLimitBytes() != inputs.sharedViewPhysicalHardBytes()
                        || permit.allocationUnitBytes() != inputs.allocationUnitBytes()
                        || permit.perDirectoryGuardBytes() != inputs.perDirectoryGuardBytes()
                        || !Path.of(permit.exactOutputRoot()).toRealPath().startsWith(output.toRealPath())) {
                    throw new IOException("Actual SDK view lease or cumulative allocation bound changed");
                }
            }
        };
    }
    private static void requireFixtureBindings(CiBootstrap.Plan plan, FixtureRequest request, FreshSdkFixtureStage.Config fresh, CanonicalColdWarmStage.Config canonical) throws IOException {
        requireFixtureBindings(plan, request.reviewAtUtc(), fresh, canonical);
    }
    private static void requireFixtureBindings(CiBootstrap.Plan plan, String review, FreshSdkFixtureStage.Config fresh, CanonicalColdWarmStage.Config canonical) throws IOException {
        FreshSdkFixtureStage.ProducerGoldenPlan golden = FreshSdkFixtureStage.readProducerGoldenPlan(fresh.producerGoldenPlanRef());
        RootSoftwareChildBootstrap.Configuration bootstrap = RootSoftwareChildBootstrap.readConfiguration(fresh.rootBootstrapRef());
        var client = bootstrap.client().source();
        if (!golden.machineId().equals(plan.machineId()) || !bootstrap.machineId().equals(plan.machineId())
                || !golden.clientContent().equals(new SdkSourceAssembly.Digest(client.bytes(), client.sha256())))
            throw new IOException("Producer GoldenPlan machine/canonical client differs from shared Root bootstrap");
        for (ControlBuild.FileRef input : FreshSdkFixtureStage.producerGoldenInputs(golden)) input.verify();
        for (ControlBuild.FileRef input : RootSoftwareChildBootstrap.inputRefs(bootstrap)) input.verify();
        fresh.pythonExecutable().verify(); fresh.rootBootstrapRef().verify();
        Path artifacts = Path.of(plan.workRoot()).resolve("artifacts").toRealPath();
        if (!fresh.machineId().equals(plan.machineId()) || !canonical.machineId().equals(plan.machineId())
                || !Path.of(fresh.canonicalRepository()).toRealPath().equals(Path.of(plan.repoRoot()).toRealPath())
                || !Path.of(canonical.repository()).toRealPath().equals(Path.of(plan.repoRoot()).toRealPath())
                || !Path.of(fresh.pythonExecutable().path()).toRealPath().equals(Path.of(plan.pythonExecutable()).toRealPath())
                || !fresh.pythonExecutable().equals(canonical.pythonExecutable())
                || canonical.bootstrapMode() != CanonicalColdWarmStage.BootstrapMode.ROOT_SOFTWARE_FIXTURE
                || !fresh.rootBootstrapRef().equals(canonical.rootBootstrapRef())
                || !Path.of(fresh.workRoot()).getParent().toRealPath().equals(artifacts)
                || !Path.of(canonical.workRoot()).getParent().toRealPath().equals(artifacts)
                || Path.of(fresh.workRoot()).equals(Path.of(canonical.workRoot()))
                || Instant.parse(fresh.reviewAtUtc()).isAfter(Instant.parse(review))
                || Instant.parse(canonical.reviewAtUtc()).isAfter(Instant.parse(review))) throw new IOException("Exact same admitted pipeline roots/interpreter/deadline required");
    }

    private static ControlBuild.Config config(CiBootstrap.Plan plan, Path source, Path release, String attempt, ControlBuild.TargetKind target) {
        return new ControlBuild.Config(source, Path.of(plan.workRoot()), release, attempt, plan.ownerTask(), null,
                Path.of(plan.javaHome()), CiBootstrap.MINIMUM_MAVEN_VERSION, 900, target,
                source.equals(Path.of(plan.repoRoot()).resolve("java/ck3-control"))
                        ? ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3
                        : ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
    }

    private static ControlBuild.FileRef ref(CiBootstrap.FilePin pin) { return new ControlBuild.FileRef(pin.path(), pin.bytes(), pin.sha256()); }

    private static Path pythonStaticRoot(Path root, PythonBoundaryStaticStage.Kind kind) {
        return root.resolve("artifacts/python-static").resolve(kind == PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED
                ? "sdk-sentinel" : "monthly-fixture");
    }

    private static List<ControlBuild.FileRef> requirePythonStaticReceipts(Path root) throws IOException {
        String machine = WindowsJobProcess.currentMachineId();
        List<ControlBuild.FileRef> refs = new ArrayList<>();
        for (var kind : PythonBoundaryStaticStage.Kind.values()) {
            ControlBuild.FileRef receipt = PythonBoundaryStaticStage.requireAccepted(pythonStaticRoot(root, kind).resolve("actual.json"), kind, machine);
            refs.add(receipt);
            System.out.println("ACCEPTED_PYTHON_STATIC " + kind + " " + receipt);
        }
        return List.copyOf(refs);
    }

    private static void requireCompletedPythonStaticPipeline(Path root) throws IOException {
        List<ControlBuild.FileRef> refs = requirePythonStaticReceipts(root);
        Path path = root.resolve("logs/control-ci-actual.json");
        if (Files.size(path) > 65536) throw new IOException("Bounded completed CI actual required");
        Receipt actual = ControlBuild.strictMapper().readValue(Files.readAllBytes(path), Receipt.class);
        if (!actual.machineId().equals(WindowsJobProcess.currentMachineId()) || actual.status() != PipelineState.PASS
                || actual.error() != null || !actual.pythonStaticReceiptRefs().equals(refs)
                || actual.planRef() == null || actual.capacityReleaseRef() == null || actual.toolsBuildReceiptRef() == null
                || actual.reactorBuildReceiptRef() == null || actual.consumerReceiptRef() == null || actual.supplementalFixtureReceiptRef() == null
                || actual.reactorTestClosureReceiptRef() == null) {
            throw new IOException("Complete CI v6 actual must bind all requested stage outcomes and actual reactor report closure");
        }
        actual.planRef().verify(); actual.capacityReleaseRef().verify(); actual.toolsBuildReceiptRef().verify();
        actual.reactorBuildReceiptRef().verify(); actual.consumerReceiptRef().verify();
        ControlBuild.FileRef supplemental = SupplementalFixtureCi.requireAccepted(root.resolve("artifacts/supplemental-fixtures/actual.json"), WindowsJobProcess.currentMachineId());
        if (!supplemental.equals(actual.supplementalFixtureReceiptRef())) throw new IOException("Completed CI must bind the exact accepted supplemental receipt");
        var reactor = ControlBuild.acceptedReceipt(Path.of(actual.reactorBuildReceiptRef().path()));
        requireFullParityFixtureProduction(reactor.sourceLimitProfile(), actual.fixtureProductionRequestRef());
        requireCurrentFixtureExecution(reactor, actual.fixtureProductionRequestRef());
        ControlBuild.FileRef reactorClosure = ReactorTestClosure.requireAccepted(root.resolve("logs/reactor-test-closure.json"),
                Path.of(actual.reactorBuildReceiptRef().path()), httpRequirements(reactor.sourceLimitProfile()));
        if (!reactorClosure.equals(actual.reactorTestClosureReceiptRef())) throw new IOException("Exact accepted reactor report closure required");
        requireStageRef(actual, Stage.REACTOR, actual.reactorBuildReceiptRef());
        requireStageRef(actual, Stage.REACTOR_TEST_CLOSURE, reactorClosure);
        requireStageRef(actual, Stage.MAP_CONSUMERS, actual.consumerReceiptRef());
        requireStageRef(actual, Stage.SUPPLEMENTAL, supplemental);
        for (int index = 0; index < PythonBoundaryStaticStage.Kind.values().length; index++) {
            Stage stage = PythonBoundaryStaticStage.Kind.values()[index] == PythonBoundaryStaticStage.Kind.SDK_SENTINEL_EXTRACTED ? Stage.SDK_SENTINEL_STATIC : Stage.MONTHLY_STATIC;
            requireStageRef(actual, stage, refs.get(index));
        }
        if (actual.purpose() == ExecutionPurpose.HOSTED_CI) {
            Path expectedMavenPath = root.resolve("logs/build-ci-expected-maven-red.json");
            requireStageRef(actual, Stage.EXPECTED_MAVEN_RED, ControlBuild.FileRef.measure(expectedMavenPath));
            requireExpectedMavenOutcome(ControlBuild.readBuildReceiptEnvelope(expectedMavenPath));
        } else {
            var local = readRootLocalExecution(actual.rootLocalPlanRef());
            if (!local.card().resourcePlanRef().equals(actual.planRef()) || !local.card().capacityReleaseRef().equals(actual.capacityReleaseRef())
                    || !local.card().toolsBuildReceiptRef().equals(actual.toolsBuildReceiptRef()) || !local.card().reactorBuildReceiptRef().equals(actual.reactorBuildReceiptRef())
                    || !local.plan().fixtureProductionRequestRef().equals(actual.fixtureProductionRequestRef())) throw new IOException("Root-local actual changed its exact issued card/normal reactor/production inputs");
        }
        for (StageActual stage : actual.stages()) {
            boolean optional = stage.stage() == Stage.FRESH_SDK || stage.stage() == Stage.CANONICAL_THIRTY;
            if (optional && actual.fixtureRequestRef() == null
                    || actual.purpose() == ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE && stage.stage() == Stage.EXPECTED_MAVEN_RED) {
                if (stage.state() != StageState.NOT_RUN) throw new IOException("Unrequested fixture stage cannot claim execution");
            } else {
                if (stage.state() != StageState.PASS || stage.evidenceRef() == null || stage.error() != null) throw new IOException("Requested actual stage did not pass");
                stage.evidenceRef().verify();
            }
        }
        if (actual.fixtureRequestRef() != null) {
            CiBootstrap.Plan plan = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(actual.planRef().path())), CiBootstrap.Plan.class);
            if (actual.fixtureProductionRequestRef() != null) readFixtureProductionRequest(actual.fixtureProductionRequestRef(), plan);
            FixtureRequest request = readFixtureRequest(actual.fixtureRequestRef(), plan);
            FreshSdkFixtureStage.Config freshConfig = readPinned(request.freshSdkConfigRef(), FreshSdkFixtureStage.Config.class, MAX_CONFIG_BYTES);
            CanonicalColdWarmStage.Config canonicalConfig = readPinned(request.canonicalConfigRef(), CanonicalColdWarmStage.Config.class, MAX_CONFIG_BYTES);
            requireFixtureBindings(plan, request, freshConfig, canonicalConfig);
            if (!freshConfig.deploymentReceiptRef().equals(actual.reactorBuildReceiptRef())) throw new IOException("SDK actual must consume this exact reactor receipt");
            FreshSdkFixtureStage.ResourceGuard guard = pending -> {
                actual.fixtureRequestRef().verify();
                if (!Instant.now().isBefore(Instant.parse(request.reviewAtUtc()))) throw new IOException("Fixture request expired");
                ControlBuild.revalidateCiResources(plan, Path.of(actual.capacityReleaseRef().path()), pending);
            };
            StageActual fresh = actual.stages().get(Stage.FRESH_SDK.ordinal()), canonical = actual.stages().get(Stage.CANONICAL_THIRTY.ordinal());
            if (!Path.of(fresh.evidenceRef().path()).toRealPath().equals(Path.of(freshConfig.workRoot()).resolve("actual.json").toRealPath())
                    || !Path.of(canonical.evidenceRef().path()).toRealPath().equals(Path.of(canonicalConfig.workRoot()).resolve("actual.json").toRealPath())) throw new IOException("Requested fixture output ownership differs");
            if (!FreshSdkFixtureStage.requireAccepted(Path.of(fresh.evidenceRef().path()), guard).equals(fresh.evidenceRef())
                    || !CanonicalColdWarmStage.requireAccepted(Path.of(canonical.evidenceRef().path()), guard).equals(canonical.evidenceRef())) throw new IOException("Exact accepted fixture stage actuals required");
            request.freshSdkConfigRef().verify(); request.canonicalConfigRef().verify();
        }
        System.out.println("ACCEPTED_CONTROL_CI_V6 " + actual.purpose() + " " + ControlBuild.FileRef.measure(path));
    }
    private static void requireStageRef(Receipt actual, Stage stage, ControlBuild.FileRef expected) throws IOException {
        if (!expected.equals(actual.stages().get(stage.ordinal()).evidenceRef())) throw new IOException("Actual stage evidence binding differs: " + stage);
    }

    private static void publish(Path path, Record value) throws IOException {
        try { Files.write(path, ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value), StandardOpenOption.CREATE_NEW); }
        catch (IOException unavailable) {
            if (value instanceof Receipt actual) {
                Receipt red = new Receipt(actual.schema(), actual.machineId(), actual.startedAtUtc(), actual.observedAtUtc(), PipelineState.RED,
                        append(actual.error(), "CI actual publication unavailable: " + unavailable.getMessage()), actual.planRef(), actual.capacityReleaseRef(),
                        actual.toolsBuildReceiptRef(), actual.qualifiedPipeline(), actual.reactorBuildReceiptRef(), actual.consumerReceiptRef(),
                        actual.pythonStaticReceiptRefs(), actual.supplementalFixtureReceiptRef(), actual.reactorTestClosureReceiptRef(), actual.fixtureRequestRef(), actual.fixtureProductionRequestRef(), actual.purpose(), actual.rootLocalPlanRef(), actual.stages());
                System.err.println(ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsString(red));
            }
            throw unavailable;
        }
    }

    /** Read actual Surefire XML; a green Maven command alone cannot prove any non-skipped test ran. */
    static void requireJUnit(Path reports, ControlBuild.BuildReceipt tools) throws IOException {
        Set<String> expected = new HashSet<>(); Path sourceRoot = Path.of(tools.sourceRoot()).toRealPath();
        for (var pin : tools.sourcePins()) {
            pin.verify(); Path source = Path.of(pin.path()).toRealPath();
            if (!source.startsWith(sourceRoot)) throw new IOException("Tool test source escapes actual build closure");
            String relative = sourceRoot.relativize(source).toString().replace('\\', '/');
            if (!relative.startsWith("src/test/java/") || !relative.endsWith(".java")) continue;
            String file = source.getFileName().toString();
            // Maven Surefire's unchanged default source patterns. Helper classes do not become expected suites.
            if (!(file.startsWith("Test") || file.endsWith("Test.java") || file.endsWith("Tests.java") || file.endsWith("TestCase.java"))) continue;
            if (!expected.add(relative.substring("src/test/java/".length(), relative.length() - 5).replace('/', '.'))) throw new IOException("Duplicate actual default tool test source");
        }
        requireJUnit(reports, Set.copyOf(expected));
    }
    static void requireJUnit(Path reports, Set<String> expected) throws IOException {
        if (expected.isEmpty()) throw new IOException("Complete explicit default test source suite set required");
        int tests = 0; int files = 0; Set<String> suites = new HashSet<>();
        try (var paths = Files.list(reports)) {
            for (Path path : paths.filter(item -> item.getFileName().toString().matches("TEST-.*\\.xml")).toList()) {
                try {
                    var factory = javax.xml.parsers.DocumentBuilderFactory.newInstance();
                    factory.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING, true);
                    factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
                    factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
                    var suite = factory.newDocumentBuilder().parse(path.toFile()).getDocumentElement();
                    if (!suites.add(suite.getAttribute("name"))) throw new IOException("Duplicate JUnit suite");
                    if (!suite.getTagName().equals("testsuite") || !suite.getAttribute("failures").equals("0")
                            || !suite.getAttribute("errors").equals("0") || !suite.getAttribute("skipped").equals("0")) throw new IOException("JUnit failure/skip or wrong suite");
                    String count = suite.getAttribute("tests"); if (!count.matches("[1-9][0-9]{0,5}")) throw new IOException("Positive bounded actual test count required");
                    if (suite.getAttribute("name").equals("org.xar.ck3.control.build.ProjectionArtifactOwnerNativeLifecycleTest") && !count.equals("6")) throw new IOException("Complete6 actual native Owner lifecycle tests required");
                    if (suite.getAttribute("name").equals("org.xar.ck3.control.build.ProjectionArtifactOwnerV3Test") && !count.equals("11")) throw new IOException("Complete11 actual OwnerV3 tests required");
                    var cases = suite.getElementsByTagName("testcase");
                    if (cases.getLength() != Integer.parseInt(count)) throw new IOException("JUnit summary differs from actual testcase children");
                    for (int index = 0; index < cases.getLength(); index++) {
                        var testcase = (org.w3c.dom.Element) cases.item(index);
                        if (testcase.getElementsByTagName("failure").getLength() != 0 || testcase.getElementsByTagName("error").getLength() != 0
                                || testcase.getElementsByTagName("skipped").getLength() != 0) throw new IOException("Actual JUnit testcase failed/errored/skipped");
                    }
                    tests = Math.addExact(tests, Integer.parseInt(count)); files++;
                } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException | NumberFormatException error) { throw new IOException("Actual JUnit report invalid", error); }
            }
        }
        if (files == 0 || tests < expected.size() || !suites.equals(expected)) throw new IOException("Complete actual default test source/report suite set differs");
    }
}
