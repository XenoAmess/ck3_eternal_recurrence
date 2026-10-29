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
import java.util.Objects;
import org.xar.ck3.control.build.CiBootstrap.JavaUtf8Invocation;

/** The durable CI route: qualify tools under a native Job, then run the same build and consumers. */
public final class ControlCi {
    private ControlCi() {}
    public static final String ACTUAL_SCHEMA = "xar.java-control-CI-actual/v8";
    public static final String SOFTWARE_SCHEMA="xar.java-control-CI-software-actual/v2";
    public enum QualificationScope { SOFTWARE_ONLY_NOT_POSTQUALIFIED }
    public static final String MANAGED_ROOT_PLAN_SCHEMA="xar.root-local-full-software-plan/v2";
    public static final String QUALIFIED_JAVA_SCHEMA = "xar.control-ci-qualified-java/v2";
    public static final String FIXTURE_REQUEST_SCHEMA = "xar.java-control-CI-fixture-request/v1";
    public static final String FIXTURE_PRODUCTION_SCHEMA = "xar.java-control-CI-fixture-production-request/v1";
    public static final String CURRENT_FIXTURE_PRODUCTION_SCHEMA = "xar.java-control-CI-fixture-production-request/v2";
    public static final String PLANNED_FIXTURE_PRODUCTION_SCHEMA = "xar.java-control-CI-planned-fixture-production-request/v1";
    public enum Stage { EXPECTED_MAVEN_RED, PERSON10_ACTUAL, REACTOR, ROOT_INVOCATION_ACTUAL, REACTOR_TEST_CLOSURE, MAP_CONSUMERS,
        SDK_SENTINEL_STATIC, MONTHLY_STATIC, SUPPLEMENTAL, FRESH_SDK, CANONICAL_THIRTY }
    public enum StageState { NOT_RUN, STARTED, PASS, RED }
    public enum PipelineState { PASS, RED }
    public enum ExecutionPurpose { HOSTED_CI, ROOT_LOCAL_FULL_SOFTWARE }
    public static final String ROOT_CARD_SCHEMA = "xar.root-local-full-software-card/v1";
    public static final String POSTQUALIFIED_ROOT_CARD_SCHEMA = "xar.root-local-full-software-card/v2";
    public static final String ROOT_PLAN_SCHEMA = "xar.root-local-full-software-plan/v1";
    public record RootSoftwareExecutionCard(String schema, ExecutionPurpose purpose, String machineId,
            String observedAtUtc, String reviewAtUtc, String ownerTask, String slotId,
            ControlBuild.FileRef resourcePlanRef, ControlBuild.FileRef runtimeBindingRef,
            ControlBuild.FileRef capacityReleaseRef, ControlBuild.FileRef toolsBuildReceiptRef,
            ControlBuild.FileRef reactorBuildReceiptRef, ControlBuild.SourceLimitProfile sourceLimitProfile,
            ControlBuild.FileRef toolsPostqualificationRef) {
        public RootSoftwareExecutionCard {
            if ((!ROOT_CARD_SCHEMA.equals(schema) && !POSTQUALIFIED_ROOT_CARD_SCHEMA.equals(schema)) || purpose != ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE
                    || machineId == null || machineId.isBlank() || ownerTask == null || ownerTask.isBlank()
                    || ownerTask.equals("github-actions-java-ci") || slotId == null || !slotId.matches("[a-z0-9][a-z0-9-]{0,63}")
                    || resourcePlanRef == null || runtimeBindingRef == null || capacityReleaseRef == null
                    || toolsBuildReceiptRef == null || reactorBuildReceiptRef == null || sourceLimitProfile == null
                    || sourceLimitProfile == ControlBuild.SourceLimitProfile.STANDARD_8_MIB) {
                throw new IllegalArgumentException("Explicit Root software purpose, finite resources and normal G2 reactor required");
            }
            if (POSTQUALIFIED_ROOT_CARD_SCHEMA.equals(schema) && toolsPostqualificationRef == null)
                throw new IllegalArgumentException("Current Root card requires actual complete-Own plus large-input proof");
            if (!Instant.parse(observedAtUtc).isBefore(Instant.parse(reviewAtUtc))) throw new IllegalArgumentException("Finite Root software window required");
        }
        /** Historical DATA constructor; the execution reader refuses this unpostqualified card. */
        public RootSoftwareExecutionCard(String schema, ExecutionPurpose purpose, String machineId,
                String observedAtUtc, String reviewAtUtc, String ownerTask, String slotId,
                ControlBuild.FileRef resourcePlanRef, ControlBuild.FileRef runtimeBindingRef,
                ControlBuild.FileRef capacityReleaseRef, ControlBuild.FileRef toolsBuildReceiptRef,
                ControlBuild.FileRef reactorBuildReceiptRef, ControlBuild.SourceLimitProfile sourceLimitProfile) {
            this(schema,purpose,machineId,observedAtUtc,reviewAtUtc,ownerTask,slotId,resourcePlanRef,runtimeBindingRef,
                    capacityReleaseRef,toolsBuildReceiptRef,reactorBuildReceiptRef,sourceLimitProfile,null);
        }
    }
    public static final String ROOT_INVOCATION_INPUTS_SCHEMA="xar.java-root-invocation-actual-inputs/v1";
    public enum RootInvocationProductionRole { JAVA_RUNTIME_LAUNCH, ROOT_STARTUP_INVOCATION, ROOT_NATIVE_AUTHORITY }
    public record RootInvocationProductionJar(RootInvocationProductionRole role,
            @com.fasterxml.jackson.annotation.JsonProperty("source_ref") ControlBuild.FileRef source) {
        public RootInvocationProductionJar {
            Objects.requireNonNull(role); Objects.requireNonNull(source);
            if(source.bytes()<1 || source.bytes()>(512L<<20) || !source.path().endsWith(".jar"))
                throw new IllegalArgumentException("Exact bounded original production JAR required");
        }
    }
    /** Memory model uses Instants; the one private wire model below owns their JSON representation. */
    public record RootInvocationInputsPlan(String schema,String machineId,Instant observedAt,Instant reviewAt,
            ControlBuild.FileRef packageManifest,ControlBuild.FileRef invocation,Path stdout,Path stderr,
            long memoryLimitBytes,List<RootInvocationProductionJar> productionJars) {
        public RootInvocationInputsPlan {
            if(!ROOT_INVOCATION_INPUTS_SCHEMA.equals(schema) || machineId==null || machineId.isBlank()
                    || observedAt==null || reviewAt==null || !observedAt.isBefore(reviewAt)
                    || reviewAt.isAfter(observedAt.plusSeconds(86400)) || packageManifest==null
                    || packageManifest.bytes()<1 || packageManifest.bytes()>(4L<<20) || invocation==null
                    || invocation.bytes()<1 || invocation.bytes()>65536 || stdout==null || stderr==null
                    || !stdout.isAbsolute() || !stderr.isAbsolute() || !stdout.normalize().equals(stdout)
                    || !stderr.normalize().equals(stderr) || stdout.equals(stderr)
                    || memoryLimitBytes<(64L<<20) || memoryLimitBytes>(32L<<30))
                throw new IllegalArgumentException("Finite exact genuine package/invocation source plan required");
            productionJars=List.copyOf(productionJars);
            var roles=new HashSet<RootInvocationProductionRole>();
            for(var jar:productionJars) if(!roles.add(jar.role())) throw new IllegalArgumentException("Duplicate production JAR role");
            if(!roles.equals(java.util.EnumSet.allOf(RootInvocationProductionRole.class)))
                throw new IllegalArgumentException("Exactly all three original production class roles required");
        }
    }
    private record RootInvocationInputsWire(String schema,String machineId,String observedAtUtc,String reviewAtUtc,
            ControlBuild.FileRef packageManifestRef,ControlBuild.FileRef invocationRef,String stdout,String stderr,
            long memoryLimitBytes,List<RootInvocationProductionJar> productionJars) { }
    public static byte[] encodeRootInvocationInputsPlan(RootInvocationInputsPlan plan)throws IOException {
        Objects.requireNonNull(plan);
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(new RootInvocationInputsWire(plan.schema(),plan.machineId(),
                plan.observedAt().toString(),plan.reviewAt().toString(),plan.packageManifest(),plan.invocation(),
                plan.stdout().toString(),plan.stderr().toString(),plan.memoryLimitBytes(),plan.productionJars()));
        if(raw.length>65536) throw new IOException("Finite actual invocation plan exceeded its bound");
        return raw;
    }
    public static RootInvocationInputsPlan decodeRootInvocationInputsPlan(byte[] original)throws IOException {
        if(original==null || original.length<1 || original.length>65536) throw new IOException("Bounded actual invocation input plan required");
        var wire=ControlBuild.strictMapper().readValue(original,RootInvocationInputsWire.class);
        try {
            return new RootInvocationInputsPlan(wire.schema(),wire.machineId(),Instant.parse(wire.observedAtUtc()),
                    Instant.parse(wire.reviewAtUtc()),wire.packageManifestRef(),wire.invocationRef(),
                    Path.of(wire.stdout()),Path.of(wire.stderr()),wire.memoryLimitBytes(),wire.productionJars());
        } catch(IllegalArgumentException|java.time.DateTimeException|NullPointerException invalid) {
            throw new IOException("Strict actual invocation input plan differs",invalid);
        }
    }

    public sealed interface RootLocalInputs permits RootLocalPlan,RootManagedPlan {
        String schema(); ExecutionPurpose purpose(); ControlBuild.FileRef softwareExecutionCardRef();
        ControlBuild.FileRef fixtureProductionRequestRef();
        default ControlBuild.FileRef postqualificationPlanRef(){ return null; }
    }
    public record RootManagedPlan(String schema,ExecutionPurpose purpose,ControlBuild.FileRef softwareExecutionCardRef,
            ControlBuild.FileRef fixtureProductionRequestRef,ControlBuild.FileRef postqualificationPlanRef) implements RootLocalInputs {
        public RootManagedPlan {
            if(!MANAGED_ROOT_PLAN_SCHEMA.equals(schema)||purpose!=ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE
                    ||softwareExecutionCardRef==null||fixtureProductionRequestRef==null||postqualificationPlanRef==null)
                throw new IllegalArgumentException("Managed current complete plan requires every actual pinned input");
        }
    }
    public record RootLocalPlan(String schema, ExecutionPurpose purpose, ControlBuild.FileRef softwareExecutionCardRef,
            ControlBuild.FileRef fixtureProductionRequestRef) implements RootLocalInputs {
        public RootLocalPlan {
            if (!ROOT_PLAN_SCHEMA.equals(schema) || purpose != ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE
                    || softwareExecutionCardRef == null || fixtureProductionRequestRef == null) {
                throw new IllegalArgumentException("Root-local card and complete actual fixture production inputs required");
            }
        }
    }
    private record LocalExecution(ControlBuild.FileRef planRef, RootLocalInputs plan, RootSoftwareExecutionCard card) { }
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
    /** Original source facts only. The qualified child supplies its actual completed tools receipt. */
    public record PlannedFixtureProductionRequest(String schema, String machineId, String reviewAtUtc,
            ControlBuild.FileRef sdkProductionPlanRef, RootSoftwareFixtureHandoff.Request softwareFixture,
            ControlBuild.FileRef currentOracleInputsRef) {
        public PlannedFixtureProductionRequest {
            if (!PLANNED_FIXTURE_PRODUCTION_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()
                    || sdkProductionPlanRef == null || softwareFixture == null || currentOracleInputsRef == null
                    || sdkProductionPlanRef.bytes() < 1 || sdkProductionPlanRef.bytes() > MAX_CONFIG_BYTES
                    || currentOracleInputsRef.bytes() < 1 || currentOracleInputsRef.bytes() > FullParityCurrentBindings.MAX_INPUT_BYTES)
                throw new IllegalArgumentException("Original SDK source plan, host request and current oracle inputs required");
            Instant.parse(reviewAtUtc);
        }
    }
    public record PlannedFixtureBinding(String schema, String machineId, ControlBuild.FileRef plannedRequestRef,
            ControlBuild.FileRef actualQualifiedToolsBuildRef, ControlBuild.FileRef sdkProductionInputsRef,
            ControlBuild.FileRef fixtureProductionRequestRef) {
        public PlannedFixtureBinding {
            if (!"xar.java-control-CI-planned-fixture-binding/v1".equals(schema) || machineId == null || machineId.isBlank()
                    || plannedRequestRef == null || actualQualifiedToolsBuildRef == null || sdkProductionInputsRef == null
                    || fixtureProductionRequestRef == null) throw new IllegalArgumentException("Actual source-plan binding provenance required");
        }
    }
    record Invocation(Path planPath, Path toolsReceiptPath, ControlBuild.FileRef fixtureRequestRef,
            ControlBuild.FileRef fixtureProductionRequestRef, ControlBuild.FileRef plannedFixtureProductionRequestRef) { }
    enum SoftwareFixtureInputKind { PRODUCER_GOLDEN_PLAN, HOST_FIXTURE_PLAN }
    record SoftwareFixtureInputsInvocation(SoftwareFixtureInputKind kind, ControlBuild.FileRef sourcePlanRef, Path outputRoot) { }
    record CheckoutSoftwareFixtureInputsInvocation(Path javaSourceRoot, Path outputRoot) { }
    record CheckoutProducerGoldenSourcesInvocation(Path javaSourceRoot, Path output) { }
    record FixtureWriterInvocation(Path planPath, ControlBuild.FileRef freshConfigRef,
            ControlBuild.FileRef canonicalConfigRef, Path outputRoot) { }
    private static final long MAX_CONFIG_BYTES = 4L << 20;

    private sealed interface PipelineEvidence permits Receipt,SoftwareReceipt {
        String schema();
        String machineId();
        String startedAtUtc();
        String observedAtUtc();
        PipelineState status();
        String error();
        ControlBuild.FileRef planRef();
        ControlBuild.FileRef capacityReleaseRef();
        ControlBuild.FileRef toolsBuildReceiptRef();
        WindowsJobProcess.CommandResult qualifiedPipeline();
        ControlBuild.FileRef reactorBuildReceiptRef();
        ControlBuild.FileRef consumerReceiptRef();
        List<ControlBuild.FileRef> pythonStaticReceiptRefs();
        ControlBuild.FileRef supplementalFixtureReceiptRef();
        ControlBuild.FileRef reactorTestClosureReceiptRef();
        ControlBuild.FileRef fixtureRequestRef();
        ControlBuild.FileRef fixtureProductionRequestRef();
        ExecutionPurpose purpose();
        ControlBuild.FileRef rootLocalPlanRef();
        List<StageActual> stages();
        ControlBuild.FileRef toolsPostqualificationRef();
    }
    private static final List<Stage> SOFTWARE_STAGES=java.util.Arrays.stream(Stage.values())
            .filter(stage->stage!=Stage.PERSON10_ACTUAL&&stage!=Stage.ROOT_INVOCATION_ACTUAL).toList();
    private static List<StageActual> softwareStages(List<StageActual> all) {
        return all.stream().filter(value->SOFTWARE_STAGES.contains(value.stage())).toList();
    }
    private static List<StageActual> notExecutedActualStages() {
        return List.of(new StageActual(Stage.PERSON10_ACTUAL,StageState.NOT_RUN,null,null),
                new StageActual(Stage.ROOT_INVOCATION_ACTUAL,StageState.NOT_RUN,null,null));
    }
    public record SoftwareReceipt(QualificationScope qualificationScope,String schema, String machineId, String startedAtUtc, String observedAtUtc,
            PipelineState status, String error, ControlBuild.FileRef planRef, ControlBuild.FileRef capacityReleaseRef,
            ControlBuild.FileRef toolsBuildReceiptRef, WindowsJobProcess.CommandResult qualifiedPipeline,
            ControlBuild.FileRef reactorBuildReceiptRef, ControlBuild.FileRef consumerReceiptRef,
            List<ControlBuild.FileRef> pythonStaticReceiptRefs, ControlBuild.FileRef supplementalFixtureReceiptRef,
            ControlBuild.FileRef reactorTestClosureReceiptRef, ControlBuild.FileRef fixtureRequestRef,
            ControlBuild.FileRef fixtureProductionRequestRef,
            ExecutionPurpose purpose, ControlBuild.FileRef rootLocalPlanRef,
            List<StageActual> stages,
            List<StageActual> postqualificationStages,ControlBuild.FileRef toolsPostqualificationRef) implements PipelineEvidence {
        public SoftwareReceipt {
            postqualificationStages=List.copyOf(postqualificationStages);
            if(qualificationScope!=QualificationScope.SOFTWARE_ONLY_NOT_POSTQUALIFIED
                    ||!notExecutedActualStages().equals(postqualificationStages))
                throw new IllegalArgumentException("Software qualification must explicitly report both actual stages NOT_EXECUTED");

            if (!SOFTWARE_SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact hosted/local software-only receipt contract required");
            if (purpose == null || (purpose == ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE) != (rootLocalPlanRef != null)
                    || purpose == ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE && fixtureProductionRequestRef == null) {
                throw new IllegalArgumentException("Exact hosted or Root-local software provenance required");
            }
            if (status == null || status == PipelineState.PASS && error != null) throw new IllegalArgumentException("Typed actual pipeline outcome required");
            pythonStaticReceiptRefs = List.copyOf(pythonStaticReceiptRefs);
            stages = List.copyOf(stages);
            if (stages.size() != SOFTWARE_STAGES.size()) throw new IllegalArgumentException("Every actual pipeline stage must be preserved");
            for (int index = 0; index < stages.size(); index++) if (stages.get(index).stage() != SOFTWARE_STAGES.get(index)) throw new IllegalArgumentException("Unique ordered pipeline stages required");
            if (status == PipelineState.PASS) {
                if(toolsPostqualificationRef==null)throw new IllegalArgumentException("Software PASS requires real complete-Own and two-JUnit Tools proof");
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
        /** Legacy source constructor retains no mechanical qualification. */
        public SoftwareReceipt(QualificationScope qualificationScope,String schema,String machineId,String startedAtUtc,String observedAtUtc,
                PipelineState status,String error,ControlBuild.FileRef planRef,ControlBuild.FileRef capacityReleaseRef,
                ControlBuild.FileRef toolsBuildReceiptRef,WindowsJobProcess.CommandResult qualifiedPipeline,
                ControlBuild.FileRef reactorBuildReceiptRef,ControlBuild.FileRef consumerReceiptRef,List<ControlBuild.FileRef> pythonStaticReceiptRefs,
                ControlBuild.FileRef supplementalFixtureReceiptRef,ControlBuild.FileRef reactorTestClosureReceiptRef,
                ControlBuild.FileRef fixtureRequestRef,ControlBuild.FileRef fixtureProductionRequestRef,ExecutionPurpose purpose,
                ControlBuild.FileRef rootLocalPlanRef,List<StageActual> stages,List<StageActual> postqualificationStages) {
            this(qualificationScope,schema,machineId,startedAtUtc,observedAtUtc,status,error,planRef,capacityReleaseRef,toolsBuildReceiptRef,
                    qualifiedPipeline,reactorBuildReceiptRef,consumerReceiptRef,pythonStaticReceiptRefs,supplementalFixtureReceiptRef,
                    reactorTestClosureReceiptRef,fixtureRequestRef,fixtureProductionRequestRef,purpose,rootLocalPlanRef,stages,postqualificationStages,null);
        }
    }
    public record Receipt(String schema, String machineId, String startedAtUtc, String observedAtUtc,
            PipelineState status, String error, ControlBuild.FileRef planRef, ControlBuild.FileRef capacityReleaseRef,
            ControlBuild.FileRef toolsBuildReceiptRef, WindowsJobProcess.CommandResult qualifiedPipeline,
            ControlBuild.FileRef reactorBuildReceiptRef, ControlBuild.FileRef consumerReceiptRef,
            List<ControlBuild.FileRef> pythonStaticReceiptRefs, ControlBuild.FileRef supplementalFixtureReceiptRef,
            ControlBuild.FileRef reactorTestClosureReceiptRef, ControlBuild.FileRef fixtureRequestRef,
            ControlBuild.FileRef fixtureProductionRequestRef,
            ExecutionPurpose purpose, ControlBuild.FileRef rootLocalPlanRef,
            ControlBuild.FileRef postqualificationPlanRef,List<StageActual> stages,ControlBuild.FileRef toolsPostqualificationRef) implements PipelineEvidence {
        public Receipt {
            if (!ACTUAL_SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact complete managed CI actual v8 contract required");
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
                if(toolsPostqualificationRef==null)throw new IllegalArgumentException("Complete PASS requires real complete-Own and two-JUnit Tools proof");
                if(postqualificationPlanRef==null||purpose!=ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE)
                    throw new IllegalArgumentException("Complete PASS requires the same issued managed actual integration plan");
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
        public Receipt(String schema, String machineId, String startedAtUtc, String observedAtUtc,
            PipelineState status, String error, ControlBuild.FileRef planRef, ControlBuild.FileRef capacityReleaseRef,
            ControlBuild.FileRef toolsBuildReceiptRef, WindowsJobProcess.CommandResult qualifiedPipeline,
            ControlBuild.FileRef reactorBuildReceiptRef, ControlBuild.FileRef consumerReceiptRef,
            List<ControlBuild.FileRef> pythonStaticReceiptRefs, ControlBuild.FileRef supplementalFixtureReceiptRef,
            ControlBuild.FileRef reactorTestClosureReceiptRef, ControlBuild.FileRef fixtureRequestRef,
            ControlBuild.FileRef fixtureProductionRequestRef,
            ExecutionPurpose purpose, ControlBuild.FileRef rootLocalPlanRef,
            List<StageActual> stages) {
            this(schema,machineId,startedAtUtc,observedAtUtc,status,error,planRef,capacityReleaseRef,toolsBuildReceiptRef,qualifiedPipeline,reactorBuildReceiptRef,consumerReceiptRef,pythonStaticReceiptRefs,supplementalFixtureReceiptRef,reactorTestClosureReceiptRef,fixtureRequestRef,fixtureProductionRequestRef,purpose,rootLocalPlanRef,null,stages,null);
        }
        public Receipt(String schema,String machineId,String startedAtUtc,String observedAtUtc,PipelineState status,String error,
                ControlBuild.FileRef planRef,ControlBuild.FileRef capacityReleaseRef,ControlBuild.FileRef toolsBuildReceiptRef,
                WindowsJobProcess.CommandResult qualifiedPipeline,ControlBuild.FileRef reactorBuildReceiptRef,ControlBuild.FileRef consumerReceiptRef,
                List<ControlBuild.FileRef> pythonStaticReceiptRefs,ControlBuild.FileRef supplementalFixtureReceiptRef,
                ControlBuild.FileRef reactorTestClosureReceiptRef,ControlBuild.FileRef fixtureRequestRef,ControlBuild.FileRef fixtureProductionRequestRef,
                ExecutionPurpose purpose,ControlBuild.FileRef rootLocalPlanRef,ControlBuild.FileRef postqualificationPlanRef,List<StageActual> stages) {
            this(schema,machineId,startedAtUtc,observedAtUtc,status,error,planRef,capacityReleaseRef,toolsBuildReceiptRef,qualifiedPipeline,
                    reactorBuildReceiptRef,consumerReceiptRef,pythonStaticReceiptRefs,supplementalFixtureReceiptRef,reactorTestClosureReceiptRef,
                    fixtureRequestRef,fixtureProductionRequestRef,purpose,rootLocalPlanRef,postqualificationPlanRef,stages,null);
        }

    }


    public static final String POSTQUALIFICATION_SCHEMA="xar.control-ci-postqualification-plan/v1";
    public enum Person10ProductionMode { PRODUCE_FROM_REQUEST, REUSE_COMPLETE_ACTUAL }
    public record Person10ActualInput(Person10ProductionMode mode,ControlBuild.FileRef original) {
        public Person10ActualInput { Objects.requireNonNull(mode);Objects.requireNonNull(original); }
    }
    public record RootPackageProductionInput(ControlBuild.FileRef requestRef,ControlBuild.FileRef invocationRef,
            org.xar.ck3.control.build.runtime.JavaRuntimePackage.WritePermit writePermit,long commandMemoryLimitBytes) {
        public RootPackageProductionInput {
            if(requestRef==null||invocationRef==null||writePermit==null||commandMemoryLimitBytes<(64L<<20)||commandMemoryLimitBytes>(32L<<30))
                throw new IllegalArgumentException("Actual Root request, invocation and issued finite allocation permit required");
        }
    }
    public record PostqualificationPlan(String schema,String machineId,String reviewAtUtc,Person10ActualInput person10,
            RootPackageProductionInput root,List<ControlBuild.FileRef> junitRuntime) {
        public PostqualificationPlan {
            if(!POSTQUALIFICATION_SCHEMA.equals(schema)||machineId==null||machineId.isBlank()||person10==null||root==null)
                throw new IllegalArgumentException("Both unconditional actual integration inputs are mandatory");
            Instant.parse(reviewAtUtc);junitRuntime=List.copyOf(junitRuntime);
            var names=new HashSet<String>();long bytes=0;
            for(var pin:junitRuntime) {
                if(!pin.path().endsWith(".jar")||pin.bytes()<1||pin.bytes()>(16L<<20)||!names.add(pin.path()))
                    throw new IllegalArgumentException("Exact unique actual JUnit runtime JARs required");
                bytes=Math.addExact(bytes,pin.bytes());
            }
            if(junitRuntime.isEmpty()||junitRuntime.size()>32||bytes>(64L<<20))
                throw new IllegalArgumentException("Finite original JUnit runtime closure required");
        }
    }
    private record RootMaterializationInput(String schema,ControlBuild.FileRef resourcePlan,ControlBuild.FileRef release,
            ControlBuild.FileRef reactor,RootPackageProductionInput input,Path inputsDestination,String reviewAtUtc) { }
    private record IntegrationActual(String schema,Stage stage,String machineId,String startedAtUtc,String observedAtUtc,
            String reviewAtUtc,ControlBuild.FileRef postqualificationPlanRef,ControlBuild.FileRef toolsReceipt,
            ControlBuild.FileRef reactorReceipt,List<ControlBuild.FileRef> data,List<SharedSourceFiles.Witness> inputWitnesses,
            ControlBuild.FileRef compileTerminal,ControlBuild.FileRef javaTerminal,ControlBuild.FileRef nativeEvidence,
            List<ControlBuild.FileRef> carrier,List<String> physicalArguments,List<String> startupOptions,
            ControlBuild.FileRef stdout,ControlBuild.FileRef stderr,int expectedTests) {
        IntegrationActual {
            if(!"xar.control-ci-actual-integration/v1".equals(schema)||stage!=Stage.PERSON10_ACTUAL&&stage!=Stage.ROOT_INVOCATION_ACTUAL
                    ||expectedTests!=(stage==Stage.PERSON10_ACTUAL?1:2))
                throw new IllegalArgumentException("Exact mandatory actual integration stage/count required");
            data=List.copyOf(data);inputWitnesses=List.copyOf(inputWitnesses);carrier=List.copyOf(carrier);
            physicalArguments=List.copyOf(physicalArguments);startupOptions=List.copyOf(startupOptions);
            if(data.size()!=3||inputWitnesses.isEmpty()||inputWitnesses.size()>256||carrier.size()!=1)
                throw new IllegalArgumentException("Complete original input/evidence closure required");
        }
    }
    private static PostqualificationPlan readPostqualificationPlan(ControlBuild.FileRef reference,CiBootstrap.Plan resources)throws IOException {
        var input=readPinned(reference,PostqualificationPlan.class,MAX_CONFIG_BYTES);
        if(!input.machineId().equals(resources.machineId())||!Instant.now().isBefore(Instant.parse(input.reviewAtUtc()))
                ||Instant.parse(input.reviewAtUtc()).isAfter(CiBootstrap.pipelineTiming(resources).workDeadline()))
            throw new IOException("Actual integration plan must use the same live managed machine/deadline");
        input.person10().original().verify();input.root().requestRef().verify();input.root().invocationRef().verify();
        input.root().writePermit().actualStorageEvidence().verify();for(var jar:input.junitRuntime())jar.verify();
        return input;
    }
    private static RootManagedPlan writeRootManagedPlan(ControlBuild.FileRef cardRef,ControlBuild.FileRef fixtures,
            ControlBuild.FileRef postqualification,Path destination)throws IOException {
        var card=readPinned(cardRef,RootSoftwareExecutionCard.class,65536);
        if(!POSTQUALIFIED_ROOT_CARD_SCHEMA.equals(card.schema())||card.toolsPostqualificationRef()==null)
            throw new IOException("Current complete plan requires the exact actual full-Own/two-JUnit Root card");
        requireToolsPostqualification(card.toolsPostqualificationRef(),card.toolsBuildReceiptRef());
        var resources=readPinned(card.resourcePlanRef(),CiBootstrap.Plan.class,MAX_CONFIG_BYTES);
        if(CiBootstrap.pipelineProfile(resources)!=CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE)
            throw new IOException("Current complete entry requires a fresh explicit "+CiBootstrap.MANAGED_PLAN_SCHEMA+" resource plan");
        readFixtureProductionRequest(fixtures,resources);readPostqualificationPlan(postqualification,resources);
        var result=new RootManagedPlan(MANAGED_ROOT_PLAN_SCHEMA,ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE,cardRef,fixtures,postqualification);
        ProjectStoragePolicy.requireBulkOutput(destination);SharedSourceFiles.plainAncestors(destination);
        ControlBuild.revalidateCiResources(resources,Path.of(card.capacityReleaseRef().path()),65536);
        publish(destination,result);cardRef.verify();fixtures.verify();postqualification.verify();return result;
    }

    public static final String SDK_PLAN_CONFIGURATION_SCHEMA = "xar.control-ci-sdk-plan-configuration/v1";

    /** Source declarations only; the actual intent producer supplies machine, review and reactor requirements. */
    public record SdkPlanConfiguration(String schema, ControlBuild.FileRef preparedIntentsRef,
            SdkSourceAssembly.LegacyConstraint legacyConstraint, SdkSourceAssembly.Source32Reuse source32Reuse,
            long sharedViewPhysicalHardBytes, long allocationUnitBytes, long perDirectoryGuardBytes,
            ControlBuild.FileRef producerGoldenPlanRef, SdkStageConfigurationProducer.InterpreterInputs interpreter,
            SdkStageConfigurationProducer.FreshInputs fresh, SdkStageConfigurationProducer.CanonicalInputs canonical,
            List<RootSoftwareChildBootstrap.Environment> bootstrapEnvironment) {
        public SdkPlanConfiguration {
            if (!SDK_PLAN_CONFIGURATION_SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact SDK plan source-configuration schema required");
            Objects.requireNonNull(preparedIntentsRef); Objects.requireNonNull(legacyConstraint); Objects.requireNonNull(source32Reuse);
            Objects.requireNonNull(producerGoldenPlanRef); Objects.requireNonNull(interpreter); Objects.requireNonNull(fresh); Objects.requireNonNull(canonical);
            bootstrapEnvironment = List.copyOf(bootstrapEnvironment);
        }
    }
    record SdkPlanWriterInvocation(ControlBuild.FileRef configurationRef, Path destination, long maxNativeBytes) { }

    /** Runs only the unchanged canonical30 step; it grants no fresh-SDK or complete-pipeline qualification. */
    public static ControlBuild.FileRef runCanonicalThirty(ControlBuild.FileRef canonicalRef,
            ControlBuild.FileRef resourcePlanRef, ControlBuild.FileRef capacityReleaseRef) throws IOException, InterruptedException {
        var canonical = readPinned(canonicalRef, CanonicalColdWarmStage.Config.class, MAX_CONFIG_BYTES);
        var resources = readPinned(resourcePlanRef, CiBootstrap.Plan.class, MAX_CONFIG_BYTES);
        var release = readPinned(capacityReleaseRef, ControlBuild.CapacityRelease.class, MAX_CONFIG_BYTES);
        requireCanonicalThirtyBindings(canonical, resources, release, capacityReleaseRef);
        if (!ControlCi.class.getProtectionDomain().getCodeSource().getLocation().equals(
                ControlBuild.class.getProtectionDomain().getCodeSource().getLocation()))
            throw new IOException("Canonical-only entry requires the same actual shared producer");
        List<ControlBuild.FileRef> runtime = resources.bootstrapRuntimeClosure().stream().map(ControlCi::ref)
                .sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList();
        if (resources.sourcePins().isEmpty() || !runtime.equals(ControlBuild.producerClosure()))
            throw new IOException("Canonical-only entry requires the exact actual producer closure and source pins");
        for (var pin : resources.sourcePins()) ref(pin).verify();
        FreshSdkFixtureStage.ResourceGuard guard = pending -> {
            canonicalRef.verify(); resourcePlanRef.verify(); capacityReleaseRef.verify();
            ControlBuild.revalidateCiResources(resources, Path.of(capacityReleaseRef.path()), pending);
        };
        guard.revalidate(0);
        var actual = CanonicalColdWarmStage.run(canonical, guard);
        for (var pin : resources.sourcePins()) ref(pin).verify();
        for (var pin : runtime) pin.verify();
        guard.revalidate(0); actual.verify(); return actual;
    }

    /** Tuple validation is followed by the unchanged physical storage/resource guard before any output. */
    static void requireCanonicalThirtyBindings(CanonicalColdWarmStage.Config canonical, CiBootstrap.Plan resources,
            ControlBuild.CapacityRelease release, ControlBuild.FileRef capacityReleaseRef) throws IOException {
        Path repository = Path.of(resources.repoRoot()).toRealPath();
        Path artifacts = Path.of(resources.workRoot()).resolve("artifacts").toRealPath();
        if (canonical.bootstrapMode() != CanonicalColdWarmStage.BootstrapMode.NONE || canonical.rootBootstrapRef() != null
                || !canonical.executionCardRef().equals(capacityReleaseRef)
                || !canonical.machineId().equals(resources.machineId()) || !canonical.machineId().equals(release.machineId())
                || !canonical.reviewAtUtc().equals(resources.reviewAtUtc()) || !canonical.reviewAtUtc().equals(release.reviewAtUtc())
                || !resources.ownerTask().equals(release.ownerTask()) || !ref(resources.policyRef()).equals(release.policyRef())
                || !resources.parts().equals(release.parts()) || !resources.volumes().equals(release.volumes())
                || !resources.quotaOverrides().equals(release.quotaOverrides())
                || canonical.commandMemoryBytes() > release.memoryLimitBytes()
                || !Path.of(canonical.repository()).toRealPath().equals(repository)
                || !Path.of(canonical.pythonExecutable().path()).toRealPath().equals(Path.of(resources.pythonExecutable()).toRealPath())
                || !Path.of(canonical.workflowRef().path()).toRealPath().equals(repository.resolve(".github/workflows/static-ci.yml").toRealPath())
                || !Path.of(canonical.workRoot()).getParent().toRealPath().equals(artifacts))
            throw new IOException("Canonical-only scope requires NONE and the same exact machine, clock, inputs and admitted resources");
    }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length > 0 && arguments[0].equals("--canonical-thirty")) {
            if (arguments.length != 12 || !arguments[4].equals("--resources") || !arguments[8].equals("--capacity-release"))
                throw new IllegalArgumentException("Exact canonical Config, resource Plan and capacity release path/bytes/SHA required");
            var actual = runCanonicalThirty(argumentRef(arguments, 1), argumentRef(arguments, 5), argumentRef(arguments, 9));
            System.out.println("CANONICAL_THIRTY_ONLY_NO_FRESH_SDK_OR_PIPELINE_QUALIFICATION "
                    + ControlBuild.strictMapper().writeValueAsString(actual)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--postqualify-tools")) {
            if (arguments.length != 4) throw new IllegalArgumentException("Exact typed postqualification input path/bytes/SHA required");
            System.out.println("ACCEPTED_MECHANICAL_LARGE_INPUTS_AFTER_COMPLETE_OWN " + postqualifyTools(argumentRef(arguments,1)));
            return;
        }
        if (arguments.length > 0 && arguments[0].equals("--verify-tools-postqualification")) {
            if (arguments.length != 4) throw new IllegalArgumentException("Exact original mechanical proof path/bytes/SHA required");
            requireToolsPostqualification(argumentRef(arguments,1),null);
            System.out.println("VERIFIED_MECHANICAL_ONLY_NO_SOFTWARE_FULL_OR_GAME_QUALIFICATION"); return;
        }
        if(arguments.length>0&&arguments[0].equals("--write-root-local-complete-plan")) {
            if(arguments.length!=14||!arguments[4].equals("--fixture-production-request")
                    ||!arguments[8].equals("--postqualification-plan")||!arguments[12].equals("--output"))
                throw new IllegalArgumentException("Exact actual card, fixture, postqualification refs and new output required");
            writeRootManagedPlan(argumentRef(arguments,1),argumentRef(arguments,5),argumentRef(arguments,9),Path.of(arguments[13]));
            System.out.println("WROTE_ROOT_LOCAL_COMPLETE_PLAN "+ControlBuild.strictMapper().writeValueAsString(ControlBuild.FileRef.measure(Path.of(arguments[13]))));return;
        }
        if(arguments.length>0&&arguments[0].equals("--materialize-root-invocation-inputs")) {
            if(arguments.length!=4)throw new IllegalArgumentException("One exact actual Root materialization request required");
            materializeRootInvocationInputs(argumentRef(arguments,1));return;
        }
        if(arguments.length==2&&arguments[0].equals("--verify-software-receipts")) {
            requireCompletedSoftwarePipeline(Path.of(arguments[1]).toRealPath());return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-sdk-production-plan")) {
            var invocation = sdkPlanWriterInvocation(arguments);
            var result = writeSdkProductionPlan(invocation.configurationRef(), invocation.destination(), invocation.maxNativeBytes());
            System.out.println("WROTE_SDK_PRODUCTION_PLAN " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--bind-root-local-planned-fixture-production")) {
            var result = bindRootLocalPlannedFixtureProduction(rootLocalBinderInvocation(arguments));
            System.out.println("BOUND_ONLY_NO_SDK_EXECUTION_OR_GAME " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--root-local-full-software")) {
            if (arguments.length != 4) throw new IllegalArgumentException("One exact Root-local plan path/bytes/SHA required");
            var planRef = argumentRef(arguments, 1);
            var local = readRootLocalExecution(planRef);
            var resources = readPinned(local.card().resourcePlanRef(), CiBootstrap.Plan.class, MAX_CONFIG_BYTES);
            prepareLocalWorkRoot(resources);
            runQualified(Path.of(local.card().resourcePlanRef().path()), resources, Path.of(local.card().toolsBuildReceiptRef().path()),
                    null, local.plan().fixtureProductionRequestRef(), null, local); return;
        }
        if (arguments.length == 4 && arguments[0].equals("--write-person10-corpus-manifest") && arguments[2].equals("--output")) {
            var result = Person10NativeCorpus.produce(Path.of(arguments[1]), Path.of(arguments[3]));
            System.out.println("WROTE_PERSON10_CORPUS_MANIFEST " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-checkout-producer-golden-sources")) {
            var invocation = checkoutProducerGoldenSourcesInvocation(arguments);
            var result = FreshSdkFixtureStage.writeCheckoutProducerGoldenSources(invocation.javaSourceRoot(), invocation.output());
            System.out.println("WROTE_CHECKOUT_PRODUCER_GOLDEN_SOURCES " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-checkout-software-fixture-inputs")) {
            var invocation = checkoutSoftwareFixtureInputsInvocation(arguments);
            var result = RootSoftwareFixtureInputsProducer.produceFromCheckout(invocation.javaSourceRoot(), invocation.outputRoot());
            System.out.println("WROTE_SOFTWARE_FIXTURE_INPUTS " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && (arguments[0].equals("--write-software-fixture-inputs")
                || arguments[0].equals("--write-host-software-fixture-inputs"))) {
            var invocation = softwareFixtureInputsInvocation(arguments);
            var result = switch (invocation.kind()) {
                case PRODUCER_GOLDEN_PLAN -> RootSoftwareFixtureInputsProducer.produce(invocation.sourcePlanRef(), invocation.outputRoot());
                case HOST_FIXTURE_PLAN -> RootSoftwareFixtureInputsProducer.produceFromHostFixturePlan(invocation.sourcePlanRef(), invocation.outputRoot());
            };
            System.out.println("WROTE_SOFTWARE_FIXTURE_INPUTS " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-current-oracle-inputs")) {
            if (arguments.length != 5 || !arguments[1].equals("--java-source-root") || !arguments[3].equals("--output")) {
                throw new IllegalArgumentException("Actual selected Java source root and fresh R3 oracle-input output required");
            }
            var result = FullParityCurrentBindings.produce(Path.of(arguments[2]), System.getenv(), Path.of(arguments[4]));
            System.out.println("WROTE_CURRENT_ORACLE_INPUTS " + ControlBuild.strictMapper().writeValueAsString(result)); return;
        }
        if (arguments.length > 0 && arguments[0].equals("--write-planned-fixture-production-request")) {
            if (arguments.length != 14 || !arguments[4].equals("--software-fixture-inputs")
                    || !arguments[8].equals("--current-oracle-inputs") || !arguments[12].equals("--output"))
                throw new IllegalArgumentException("Pinned SDK source plan, host/current inputs and fresh output required");
            var sdkRef = argumentRef(arguments, 1); var sdk = SdkStageConfigurationProducer.readPlan(sdkRef);
            var hostRef = argumentRef(arguments, 5); var host = readPinned(hostRef, RootSoftwareFixtureHandoff.Request.class, MAX_CONFIG_BYTES);
            var currentRef = argumentRef(arguments, 9);
            var request = new PlannedFixtureProductionRequest(PLANNED_FIXTURE_PRODUCTION_SCHEMA, sdk.machineId(), sdk.reviewAtUtc(), sdkRef, host, currentRef);
            var result = writePlannedFixtureProductionRequest(request, Path.of(arguments[13]));
            sdkRef.verify(); hostRef.verify(); currentRef.verify();
            System.out.println("WROTE_PLANNED_FIXTURE_PRODUCTION_REQUEST " + ControlBuild.strictMapper().writeValueAsString(result)); return;
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
        if (invocation.plannedFixtureProductionRequestRef() != null) readPlannedFixtureProductionRequest(invocation.plannedFixtureProductionRequestRef(), plan);
        if (invocation.toolsReceiptPath() == null) qualify(planPath, plan, invocation.fixtureRequestRef(), invocation.fixtureProductionRequestRef(), invocation.plannedFixtureProductionRequestRef());
        else runQualified(planPath, plan, invocation.toolsReceiptPath(), invocation.fixtureRequestRef(), invocation.fixtureProductionRequestRef(), invocation.plannedFixtureProductionRequestRef(), null);
    }

    static Invocation invocation(String[] args) throws IOException {
        if (args.length < 2 || !args[0].equals("--bootstrap-plan")) throw new IllegalArgumentException("Exact bootstrap plan required");
        Path plan = Path.of(args[1]).toRealPath(), tools = null; ControlBuild.FileRef fixtures = null, production = null, planned = null;
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
                case "--planned-fixture-production-request" -> {
                    if (planned != null || index + 3 >= args.length) throw new IllegalArgumentException("One exact planned fixture production request required");
                    planned = argumentRef(args, index + 1); index += 3;
                }
                default -> throw new IllegalArgumentException("Unknown CI arguments");
            }
        }
        requireOneFixtureRoute(fixtures, production, planned);
        return new Invocation(plan, tools, fixtures, production, planned);
    }


    static SdkPlanWriterInvocation sdkPlanWriterInvocation(String[] args) throws IOException {
        if (args.length != 8 || !args[0].equals("--write-sdk-production-plan")
                || !args[4].equals("--output") || !args[6].equals("--max-native-bytes")
                || !args[7].matches("[1-9][0-9]{0,8}"))
            throw new IllegalArgumentException("Pinned SDK source configuration, fresh output and finite native bound required");
        Path output = Path.of(args[5]); long maximum = Long.parseLong(args[7]);
        if (!output.isAbsolute() || !output.normalize().equals(output) || output.getParent() == null
                || maximum > 16L << 20)
            throw new IllegalArgumentException("Canonical SDK plan output and metadata-only native bound required");
        return new SdkPlanWriterInvocation(argumentRef(args, 1), output, maximum);
    }

    /** Produces a plan through the existing SDK writer; source declarations cannot claim a qualified build. */
    public static ControlBuild.FileRef writeSdkProductionPlan(ControlBuild.FileRef configurationRef, Path destination,
            long maxNativeBytes) throws IOException {
        if (!destination.isAbsolute() || !destination.normalize().equals(destination) || destination.getParent() == null
                || maxNativeBytes < 1 || maxNativeBytes > 16L << 20)
            throw new IllegalArgumentException("Canonical output and finite metadata-only native bound required");
        SharedSourceFiles.plainAncestors(destination);
        if (Files.exists(destination, java.nio.file.LinkOption.NOFOLLOW_LINKS) || !Files.isDirectory(destination.getParent()))
            throw new IOException("Fresh SDK plan file with an existing admitted parent required");
        SharedSourceFiles.plainAncestors(Path.of(configurationRef.path()));
        var configuration = readPinned(configurationRef, SdkPlanConfiguration.class, MAX_CONFIG_BYTES);
        var preparedRef = configuration.preparedIntentsRef();
        SharedSourceFiles.plainAncestors(Path.of(preparedRef.path()));
        var prepared = readPinned(preparedRef, SdkSourceIntent.PreparedIntents.class, MAX_CONFIG_BYTES);
        var intentRefs = List.of(prepared.baselineIntentRef(), prepared.legacyIntentRef(), prepared.consumerIntentRef());
        if (!prepared.generatedRefs().containsAll(intentRefs) || prepared.inputRefs().isEmpty())
            throw new IOException("The actual source-intent producer receipt must retain all three generated intents and originals");
        for (var ref : prepared.inputRefs()) ref.verify();
        for (var ref : prepared.generatedRefs()) ref.verify();
        var intents = new ArrayList<SdkSourceIntent.Intent>();
        var requirements = new TreeMap<String, SdkSourceIntent.RequiredReactorSource>();
        var views = List.of(SdkSourceIntent.View.BASELINE, SdkSourceIntent.View.LEGACY, SdkSourceIntent.View.CONSUMER);
        for (int index = 0; index < intentRefs.size(); index++) {
            var intent = readPinned(intentRefs.get(index), SdkSourceIntent.Intent.class, MAX_CONFIG_BYTES);
            if (intent.view() != views.get(index)) throw new IOException("Source-intent receipt exchanged its declared view");
            intents.add(intent);
            var resolved = SdkSourceIntent.resolve(intentRefs.get(index));
            for (var required : resolved.requiredReactorSources()) {
                var prior = requirements.putIfAbsent(required.relativePath().toLowerCase(java.util.Locale.ROOT), required);
                if (prior != null && !prior.equals(required)) throw new IOException("Conflicting actual source-intent reactor requirements");
            }
        }
        var first = intents.getFirst();
        for (var intent : intents) if (!intent.machineId().equals(first.machineId()) || !intent.reviewAtUtc().equals(first.reviewAtUtc()))
            throw new IOException("One actual machine and finite source-intent review required");
        var plan = new SdkStageConfigurationProducer.ProductionPlan(SdkStageConfigurationProducer.PLAN_SCHEMA,
                first.machineId(), first.reviewAtUtc(), intentRefs.get(0), intentRefs.get(1), intentRefs.get(2),
                configuration.legacyConstraint(), configuration.source32Reuse(), configuration.sharedViewPhysicalHardBytes(),
                configuration.allocationUnitBytes(), configuration.perDirectoryGuardBytes(), configuration.producerGoldenPlanRef(),
                List.copyOf(requirements.values()), configuration.interpreter(), configuration.fresh(), configuration.canonical(),
                configuration.bootstrapEnvironment());
        long unit = NativeStorageGeometry.read(destination.getParent()).clusterBytes();
        if (unit < 1 || unit > 1L << 20) throw new IOException("Bounded actual SDK metadata allocation unit required");
        FreshSdkFixtureStage.ResourceGuard guard = pending -> {
            if (pending < 0 || !Instant.now().isBefore(Instant.parse(plan.reviewAtUtc())))
                throw new IOException("SDK plan source window expired or pending allocation is invalid");
            configurationRef.verify(); preparedRef.verify(); SharedSourceFiles.plainAncestors(destination);
            long used = Files.exists(destination, java.nio.file.LinkOption.NOFOLLOW_LINKS)
                    ? SharedSourceFiles.nativeFile(destination).allocatedBytes() : 0;
            long reserved = Math.multiplyExact(Math.floorDiv(Math.addExact(pending, unit - 1), unit), unit);
            if (Math.addExact(unit, Math.addExact(used, reserved)) > maxNativeBytes)
                throw new IOException("SDK plan metadata exceeds its admitted native bound");
        };
        var result = SdkStageConfigurationProducer.writePlan(plan, destination, guard);
        for (var ref : prepared.inputRefs()) ref.verify();
        for (var ref : prepared.generatedRefs()) ref.verify();
        configurationRef.verify(); preparedRef.verify(); result.verify(); guard.revalidate(0);
        return result;
    }

    static CheckoutProducerGoldenSourcesInvocation checkoutProducerGoldenSourcesInvocation(String[] args) {
        if (args.length != 5 || !args[0].equals("--write-checkout-producer-golden-sources")
                || !args[1].equals("--java-source-root") || !args[3].equals("--output"))
            throw new IllegalArgumentException("Actual Java checkout and fresh golden-source metadata output required");
        Path source = Path.of(args[2]), output = Path.of(args[4]);
        if (!source.isAbsolute() || !source.normalize().equals(source)
                || !output.isAbsolute() || !output.normalize().equals(output))
            throw new IllegalArgumentException("Canonical absolute Java checkout and golden-source metadata output required");
        return new CheckoutProducerGoldenSourcesInvocation(source, output);
    }

    static CheckoutSoftwareFixtureInputsInvocation checkoutSoftwareFixtureInputsInvocation(String[] args) {
        if (args.length != 5 || !args[0].equals("--write-checkout-software-fixture-inputs")
                || !args[1].equals("--java-source-root") || !args[3].equals("--output-root"))
            throw new IllegalArgumentException("Actual Java checkout and fresh software-fixture output required");
        Path source = Path.of(args[2]), output = Path.of(args[4]);
        if (!source.isAbsolute() || !source.normalize().equals(source)
                || !output.isAbsolute() || !output.normalize().equals(output))
            throw new IllegalArgumentException("Canonical absolute Java checkout and software-fixture output required");
        return new CheckoutSoftwareFixtureInputsInvocation(source, output);
    }

    static SoftwareFixtureInputsInvocation softwareFixtureInputsInvocation(String[] args) throws IOException {
        if (args.length != 6 || !args[4].equals("--output-root"))
            throw new IllegalArgumentException("Exact original plan path/bytes/SHA and fresh output root required");
        SoftwareFixtureInputKind kind = switch (args[0]) {
            case "--write-software-fixture-inputs" -> SoftwareFixtureInputKind.PRODUCER_GOLDEN_PLAN;
            case "--write-host-software-fixture-inputs" -> SoftwareFixtureInputKind.HOST_FIXTURE_PLAN;
            default -> throw new IllegalArgumentException("Explicit original software-fixture source kind required");
        };
        Path output = Path.of(args[5]);
        if (!output.isAbsolute() || !output.normalize().equals(output))
            throw new IllegalArgumentException("Canonical absolute software-fixture output root required");
        return new SoftwareFixtureInputsInvocation(kind, argumentRef(args, 1), output);
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

    private record RootSoftwareAuthority(ControlBuild.FileRef reference, RootSoftwareExecutionCard card, CiBootstrap.Plan resources, ControlBuild.BuildReceipt reactor) { }

    private static RootSoftwareAuthority readRootSoftwareAuthority(ControlBuild.FileRef reference) throws IOException {
        var card = readPinned(reference, RootSoftwareExecutionCard.class, 65536);
        if (!POSTQUALIFIED_ROOT_CARD_SCHEMA.equals(card.schema()) || card.toolsPostqualificationRef() == null)
            throw new IOException("NOT EXECUTED: legacy Root card has no actual complete Own plus Source38 two-JUnit proof");
        var mechanical=requireToolsPostqualification(card.toolsPostqualificationRef(),card.toolsBuildReceiptRef());
        var resources = readPinned(card.resourcePlanRef(), CiBootstrap.Plan.class, MAX_CONFIG_BYTES);
        var binding = SharedOwnedCommandBinding.read(card.runtimeBindingRef());
        binding.standingRef().verify(); binding.deliveryRef().verify(); binding.launcherSourceRef().verify();
        var standing = readPinned(binding.standingRef(), com.fasterxml.jackson.databind.JsonNode.class, MAX_CONFIG_BYTES);
        var delivery = readPinned(binding.deliveryRef(), com.fasterxml.jackson.databind.JsonNode.class, MAX_CONFIG_BYTES);
        if(!ControlBuild.strictMapper().treeToValue(standing.required("qualified_own_readback_ref"),ControlBuild.FileRef.class).equals(mechanical.fullOwnActualRef()))
            throw new IOException("Root runtime must retain the same unchanged complete Own used by the actual mechanical proof");
        SharedOwnedCommandBinding.verifyAuthority(standing, binding.standingExpectation(), card.machineId());
        SharedOwnedCommandBinding.verifyAuthority(delivery, binding.deliveryExpectation(), card.machineId());
        if (!card.machineId().equals(WindowsJobProcess.currentMachineId()) || !card.machineId().equals(binding.machineId())
                || !card.machineId().equals(resources.machineId()) || !card.ownerTask().equals(resources.ownerTask())
                || !card.observedAtUtc().equals(resources.observedAtUtc()) || !card.reviewAtUtc().equals(resources.reviewAtUtc())
                || !CiBootstrap.supportedPlanSchema(resources.schema())
                || Instant.parse(card.reviewAtUtc()).isAfter(Instant.parse(jsonText(standing, "review_at_utc")))) {
            throw new IOException("Root software card does not match its actual local resources and current runtime window");
        }
        requireRootSlot(resources, card, standing);
        CiBootstrap.requireCompletePipeline(resources);
        var tools = ControlBuild.verifiedCompletedReceipt(card.toolsBuildReceiptRef());
        var reactor = ControlBuild.verifiedCompletedReceipt(card.reactorBuildReceiptRef());
        var loaded = ControlBuild.producerClosure();
        if (tools.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME || !tools.completeDeployment().equals(loaded)
                || reactor.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR || reactor.sourceLimitProfile() != card.sourceLimitProfile()
                || card.sourceLimitProfile() != reactorSourceProfile(resources)
                || !reactor.machineId().equals(card.machineId()) || !tools.machineId().equals(card.machineId())
                || !runtimeRef(standing, "qualified_tools_ref").equals(card.toolsBuildReceiptRef())
                || !runtimeRefs(standing, "runtime_closure").equals(loaded) || !runtimeRefs(delivery, "complete_runtime").equals(loaded)
                || !resources.bootstrapRuntimeClosure().stream().map(ControlCi::ref).sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList().equals(loaded)
                || !resources.sourcePins().stream().map(ControlCi::ref).sorted(Comparator.comparing(ControlBuild.FileRef::path)).toList().equals(tools.sourcePins())) {
            throw new IOException("Only exact qualified tools and the accepted normal selected G2 reactor may enter local software validation");
        }
        card.toolsBuildReceiptRef().verify(); card.reactorBuildReceiptRef().verify(); card.capacityReleaseRef().verify();
        requireJUnit(Path.of(tools.deploymentRoot()).resolve("surefire-reports"), tools);
        return new RootSoftwareAuthority(reference, card, resources, reactor);
    }

    private static LocalExecution readRootLocalExecution(ControlBuild.FileRef reference) throws IOException {
        var localNode=readPinned(reference,com.fasterxml.jackson.databind.JsonNode.class,65536);
        String schema=jsonText(localNode,"schema");
        RootLocalInputs local=ROOT_PLAN_SCHEMA.equals(schema) ? readPinned(reference,RootLocalPlan.class,65536)
                : MANAGED_ROOT_PLAN_SCHEMA.equals(schema) ? readPinned(reference,RootManagedPlan.class,65536)
                : throwUnknownRootPlan();
        var authority = readRootSoftwareAuthority(local.softwareExecutionCardRef());
        var card = authority.card(); var resources = authority.resources();
        if(local instanceof RootManagedPlan) {
            if(CiBootstrap.pipelineProfile(resources)!=CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE)
                throw new IOException("Managed full actual route requires its distinct "+CiBootstrap.MANAGED_PLAN_SCHEMA+" resources");
            readPostqualificationPlan(local.postqualificationPlanRef(),resources);
        }
        CiBootstrap.requireCompletePipeline(resources);
        if(local instanceof RootManagedPlan && CiBootstrap.pipelineProfile(resources)!=CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE)
            throw new IOException("Managed full plan needs separately issued "+CiBootstrap.MANAGED_PLAN_SCHEMA+" resources");
        var production = readFixtureProductionRequest(local.fixtureProductionRequestRef(), resources);
        var sdk = SdkStageConfigurationProducer.readInputs(production.sdkProductionInputsRef());
        if (!sdk.fresh().executionCardRef().equals(local.softwareExecutionCardRef())
                || !sdk.canonical().executionCardRef().equals(local.softwareExecutionCardRef())) {
            throw new IOException("Both complete SDK groups must consume the same issued Root software card");
        }
        var result = new LocalExecution(reference, local, card); revalidateLocalExecution(result); return result;
    }

    record RootLocalBinderInvocation(ControlBuild.FileRef cardRef, ControlBuild.FileRef plannedRef) { }

    static RootLocalBinderInvocation rootLocalBinderInvocation(String[] args) throws IOException {
        if (args.length != 8 || !args[0].equals("--bind-root-local-planned-fixture-production")
                || !args[4].equals("--planned-fixture-production-request"))
            throw new IllegalArgumentException("Exact original Root card and planned fixture path/bytes/SHA required");
        return new RootLocalBinderInvocation(argumentRef(args, 1), argumentRef(args, 5));
    }

    static void requireRootLocalSdkCards(ControlBuild.FileRef card, SdkStageConfigurationProducer.ProductionPlan sdk) throws IOException {
        if (card == null || !card.equals(sdk.fresh().executionCardRef()) || !card.equals(sdk.canonical().executionCardRef()))
            throw new IOException("Both complete SDK groups must retain this exact original Root software card");
    }

    static void requireRootLocalBindingWindow(Instant now, Instant workDeadline, Instant cardReview, Instant sourceReview) throws IOException {
        if (Duration.between(now, earlier(workDeadline, earlier(cardReview, sourceReview))).compareTo(Duration.ofSeconds(900)) < 0)
            throw new IOException("Root-local metadata binding needs 900 unspent seconds within all original deadlines");
    }

    static ControlBuild.FileRef bindRootLocalPlannedFixtureProduction(RootLocalBinderInvocation invocation) throws IOException {
        var authority = readRootSoftwareAuthority(invocation.cardRef());
        var card = authority.card(); var resources = authority.resources();
        var request = readPlannedFixtureProductionRequest(invocation.plannedRef(), resources);
        var sdk = SdkStageConfigurationProducer.readPlan(request.sdkProductionPlanRef());
        requireRootLocalSdkCards(invocation.cardRef(), sdk);
        var reactor = authority.reactor();
        SdkStageConfigurationProducer.requireReactorSources(sdk.requiredReactorSources(), Path.of(reactor.sourceRoot()), reactor.sourcePins());
        SdkStageConfigurationProducer.requireReactorSources(sdk.requiredReactorSources(), Path.of(reactor.compiledSourceRoot()), reactor.compiledSourcePins());
        if (reactor.sourceLimitProfile().currentParity()) {
            var executed = FullParityCurrentBindings.completedBuildBindings(reactor);
            if (!executed.inputsRef().equals(request.currentOracleInputsRef()))
                throw new IOException("Local binder must retain the current oracle inputs executed by this accepted reactor");
            FullParityCurrentBindings.requireExecutedInputs(FullParityCurrentBindings.readInputs(request.currentOracleInputsRef()), executed);
        }
        requireRootLocalBindingWindow(Instant.now(), CiBootstrap.pipelineTiming(resources).workDeadline(),
                Instant.parse(card.reviewAtUtc()), Instant.parse(sdk.reviewAtUtc()));
        FreshSdkFixtureStage.ResourceGuard guard = pending -> {
            authority.reference().verify(); invocation.plannedRef().verify();
            card.resourcePlanRef().verify(); card.runtimeBindingRef().verify(); card.capacityReleaseRef().verify();
            if (!Instant.now().isBefore(Instant.parse(card.reviewAtUtc()))) throw new IOException("Root-local software card expired");
            var binding = SharedOwnedCommandBinding.read(card.runtimeBindingRef());
            binding.standingRef().verify(); binding.deliveryRef().verify(); binding.launcherSourceRef().verify();
            CiBootstrap.pipelineTiming(resources).remainingWork(Instant.now());
            ControlBuild.revalidateCiResources(resources, Path.of(card.capacityReleaseRef().path()), pending);
        };
        guard.revalidate(7L * 8192); prepareLocalWorkRoot(resources); guard.revalidate(0);
        var result = bindPlannedFixtureProduction(invocation.plannedRef(), card.toolsBuildReceiptRef(), resources,
                Path.of(resources.workRoot()).resolve("artifacts/planned-fixture-production"), guard);
        SdkStageConfigurationProducer.requireReactorSources(sdk.requiredReactorSources(), Path.of(reactor.sourceRoot()), reactor.sourcePins());
        SdkStageConfigurationProducer.requireReactorSources(sdk.requiredReactorSources(), Path.of(reactor.compiledSourceRoot()), reactor.compiledSourcePins());
        result.verify(); guard.revalidate(0); return result;
    }

    private static RootLocalInputs throwUnknownRootPlan()throws IOException { throw new IOException("Unknown exact Root-local plan version"); }

    static void requireRootSlot(CiBootstrap.Plan resources, RootSoftwareExecutionCard card,
            com.fasterxml.jackson.databind.JsonNode standing) throws IOException {
        var timing = CiBootstrap.pipelineTiming(resources); timing.remainingWork(Instant.now());
        com.fasterxml.jackson.databind.JsonNode slot = null;
        var slots = standing.get("slots");
        if (slots == null || !slots.isArray() || slots.size() > 64) throw new IOException("Explicit finite runtime slots required");
        for (var candidate : slots) if (card.slotId().equals(jsonText(candidate, "slot_id"))) {
            if (slot != null) throw new IOException("Duplicate admitted Root software slot"); slot = candidate;
        }
        if(slot!=null&&CiBootstrap.pipelineProfile(resources)==CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE
                &&jsonLong(slot,"worker_memory_limit_bytes")<(6L<<30))
            throw new IOException("Managed full producer chain requires an actual six-GiB ancestor Job lease");
        if (slot == null || !card.ownerTask().equals(jsonText(slot, "coordinator"))
                || Duration.between(timing.observedAt(), timing.outerDeadline()).compareTo(Duration.ofSeconds(jsonLong(slot, "timeout_seconds"))) > 0
                || !Path.of(resources.workRoot()).toAbsolutePath().normalize().startsWith(Path.of(jsonText(slot, "output_root")).toAbsolutePath().normalize())) {
            throw new IOException("The actual standing slot cannot admit this whole software deadline or output root");
        }
    }

    private static Instant earlier(Instant left,Instant right){return left.isBefore(right)?left:right;}
    private static ControlBuild.FileRef sourceFor(ControlBuild.BuildReceipt build,String relative)throws IOException {
        Path expected=Path.of(build.sourceRoot()).resolve(relative).toRealPath();
        var values=build.sourcePins().stream().filter(pin->Path.of(pin.path()).toAbsolutePath().normalize().equals(expected)).toList();
        if(values.size()!=1)throw new IOException("Actual qualified source closure lacks "+relative);
        values.getFirst().verify();return values.getFirst();
    }
    private static List<ControlBuild.FileRef> jarClosure(ControlBuild.BuildReceipt build)throws IOException {
        var jars=build.completeDeployment().stream().filter(pin->pin.path().endsWith(".jar")).toList();
        if(jars.isEmpty())throw new IOException("Actual packaged production JAR deployment required");
        for(var jar:jars)jar.verify();return jars;
    }
    private static ControlBuild.FileRef jarProviding(ControlBuild.BuildReceipt build,String type)throws IOException {
        var matches=new ArrayList<ControlBuild.FileRef>();
        for(var jar:jarClosure(build))try(var opened=new java.util.jar.JarFile(jar.path(),false)) {
            if(opened.getJarEntry(type.replace('.','/')+".class")!=null)matches.add(jar);
        }
        if(matches.size()!=1)throw new IOException("One original packaged provider required: "+type);return matches.getFirst();
    }
    private static void materializeRootInvocationInputs(ControlBuild.FileRef original)throws Exception {
        var input=readPinned(original,RootMaterializationInput.class,MAX_CONFIG_BYTES);
        if(!"xar.control-ci-root-materialization/v1".equals(input.schema()))throw new IOException("Exact Root materialization contract required");
        var resources=readPinned(input.resourcePlan(),CiBootstrap.Plan.class,MAX_CONFIG_BYTES);
        if(CiBootstrap.pipelineProfile(resources)!=CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE)
            throw new IOException("Only issued managed resources permit actual package production");
        Instant deadline=Instant.parse(input.reviewAtUtc());
        if(deadline.isAfter(CiBootstrap.pipelineTiming(resources).workDeadline())||!Instant.now().isBefore(deadline))
            throw new IOException("Original Root production deadline unavailable");
        var reactor=ControlBuild.verifiedCompletedReceipt(input.reactor());
        if(reactor.targetKind()!=ControlBuild.TargetKind.SERVICE_FAST_JAR)throw new IOException("Accepted whole service required");
        var request=org.xar.ck3.control.build.runtime.JavaRuntimePackageCodec.readRequest(input.input().requestRef());
        Path work=Path.of(resources.workRoot()).toAbsolutePath().normalize();
        var permit=input.input().writePermit();
        if(!request.machineId().equals(resources.machineId())||!request.serviceBuildActual().equals(input.reactor())
                ||!Path.of(request.outputRoot()).startsWith(work.resolve("artifacts"))
                ||!permit.actualStorageEvidence().equals(input.release())||!permit.machineId().equals(resources.machineId())
                ||!permit.exactOutputRoot().equals(request.outputRoot())
                ||Instant.parse(permit.expiresAtUtc()).isAfter(CiBootstrap.pipelineTiming(resources).workDeadline())
                ||Instant.parse(request.reviewAtUtc()).isAfter(CiBootstrap.pipelineTiming(resources).workDeadline()))
            throw new IOException("Genuine package request/permit crossed the issued reactor, resources or window");
        var authorityJar=jarProviding(reactor,"org.xar.ck3.control.service.root.RootPackageNativeVerifier");
        Class<?> type=Class.forName("org.xar.ck3.control.service.root.RootPackageNativeVerifier",true,ControlCi.class.getClassLoader());
        Path loaded=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        if(!ControlBuild.FileRef.measure(loaded).equals(authorityJar))throw new IOException("Fixed authority must load from the accepted original service JAR");
        Object authorityObject=type.getDeclaredConstructor().newInstance();
        if(!(authorityObject instanceof org.xar.ck3.control.build.runtime.JavaRuntimePackage.NativeAuthorityVerifier authority))
            throw new IOException("Fixed actual authority has the wrong shared typed contract");
        var gate=new org.xar.ck3.control.build.runtime.JavaRuntimePackage.CapacityGate() {
            @Override public org.xar.ck3.control.build.runtime.JavaRuntimePackage.WritePermit acquire(
                    org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request exact,
                    org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Quote quote)throws IOException {
                if(!exact.equals(request)||quote.contentBytes()<1)throw new IOException("Actual reviewed request/quote required");
                if(permit.allocationUnitBytes()!=NativeStorageGeometry.read(Path.of(request.outputRoot()).getParent()).clusterBytes())
                    throw new IOException("Issued package allocation unit differs from actual native geometry");
                revalidate(permit,0);return permit;
            }
            @Override public void revalidate(org.xar.ck3.control.build.runtime.JavaRuntimePackage.WritePermit exact,long used)throws IOException {
                if(!exact.equals(permit)||used<0||used>permit.allocationUpperBytes()||!Instant.now().isBefore(deadline)
                        ||!Instant.now().isBefore(Instant.parse(permit.expiresAtUtc())))throw new IOException("Original package capacity/deadline expired");
                original.verify();input.resourcePlan().verify();input.reactor().verify();input.input().requestRef().verify();
                permit.actualStorageEvidence().verify();
                ControlBuild.revalidateCiPackageResources(resources,Path.of(input.release().path()),
                        new ControlBuild.PackagePendingAllocation(permit,used));
            }
        };
        var reviewed=org.xar.ck3.control.build.runtime.JavaRuntimePackage.review(request,authority);
        if(!(reviewed instanceof org.xar.ck3.control.build.runtime.JavaRuntimePackage.ReviewAvailable acceptedReview))
            throw new IOException("Genuine package review unavailable: "+reviewed);
        var produced=org.xar.ck3.control.build.runtime.JavaRuntimePackage.produce(acceptedReview,authority,gate);
        if(!(produced instanceof org.xar.ck3.control.build.runtime.JavaRuntimePackage.PackageAvailable available))
            throw new IOException("Genuine package production unavailable: "+produced);
        var reread=org.xar.ck3.control.build.runtime.JavaRuntimePackage.readAccepted(available.value().manifestRef(),authority);
        if(!(reread instanceof org.xar.ck3.control.build.runtime.JavaRuntimePackage.PackageAvailable current))
            throw new IOException("Genuine package current readback unavailable: "+reread);
        var accepted=current.value();accepted.verifyCurrent();
        var roles=new ArrayList<RootInvocationProductionJar>();
        for(var role:RootInvocationProductionRole.values()) {
            String binary=switch(role) {
                case JAVA_RUNTIME_LAUNCH->"org.xar.ck3.control.build.runtime.JavaRuntimeLaunch";
                case ROOT_STARTUP_INVOCATION->"org.xar.ck3.control.build.runtime.RootStartupInvocation";
                case ROOT_NATIVE_AUTHORITY->"org.xar.ck3.control.service.root.RootPackageNativeVerifier";
            };
            var providers=accepted.manifest().layout().applicationClasses().stream()
                    .filter(row->row.binaryName().equals(binary)&&row.kind()==org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.ProviderKind.ORIGINAL).toList();
            if(providers.size()!=1)throw new IOException("One accepted original production class provider required: "+binary);
            String relative="quarkus-app/"+providers.getFirst().relativeJar();
            var outputs=accepted.manifest().outputFiles().stream().filter(row->row.relativePath().equals(relative)).toList();
            if(outputs.size()!=1)throw new IOException("Accepted original class JAR is missing");
            outputs.getFirst().original().verify();roles.add(new RootInvocationProductionJar(role,outputs.getFirst().original()));
        }
        var plan=new RootInvocationInputsPlan(ROOT_INVOCATION_INPUTS_SCHEMA,resources.machineId(),Instant.now(),
                Instant.parse(request.reviewAtUtc()),accepted.manifestRef(),input.input().invocationRef(),
                input.inputsDestination().getParent().resolve("root-command.stdout.log"),
                input.inputsDestination().getParent().resolve("root-command.stderr.log"),input.input().commandMemoryLimitBytes(),roles);
        byte[] bytes=encodeRootInvocationInputsPlan(plan);gate.revalidate(permit,permit.allocationUpperBytes());
        ControlBuild.revalidateCiResources(resources,Path.of(input.release().path()),bytes.length+4096L);
        Files.write(input.inputsDestination(),bytes,StandardOpenOption.CREATE_NEW);
        if(!plan.equals(decodeRootInvocationInputsPlan(Files.readAllBytes(input.inputsDestination()))))throw new IOException("Actual plan roundtrip changed");
        original.verify();accepted.verifyCurrent();
        System.out.println("PRODUCED_GENUINE_ROOT_INVOCATION_INPUTS "+ControlBuild.FileRef.measure(input.inputsDestination()));
    }

    private static List<String> ownArguments(ToolsInputPostqualification.Input input,Path output) {
        var args=new ArrayList<String>();
        for(var pin:input.fullOwn().arguments(input.toolsReceiptRef())) {
            args.add(pin.path());args.add(Long.toString(pin.bytes()));args.add(pin.sha256());
        }
        var manifest=input.fullOwn().boundedInputManifestRef();
        args.add(manifest.path());args.add(Long.toString(manifest.bytes()));args.add(manifest.sha256());
        args.add(output.toString());return List.copyOf(args);
    }
    /** Metadata producer only; the unchanged full Own and two real JUnit methods remain mandatory. */
    public static ControlBuild.FileRef writeToolsPostqualificationInput(ToolsInputPostqualification.Input input,Path output)throws IOException {
        var plan=readPinned(input.resourcePlanRef(),CiBootstrap.Plan.class,MAX_CONFIG_BYTES);
        var tools=ControlBuild.verifiedCompletedReceipt(input.toolsReceiptRef());
        Path root=Path.of(plan.workRoot()).toAbsolutePath().normalize(),target=output.toAbsolutePath().normalize();
        if(!output.isAbsolute()||!output.equals(target)||!target.startsWith(root)||target.equals(root)
                ||!input.machineId().equals(plan.machineId())||!tools.machineId().equals(plan.machineId())
                ||tools.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME||Instant.parse(input.observedAtUtc()).isAfter(Instant.now())
                ||!plan.machineId().equals(WindowsJobProcess.currentMachineId())
                ||Instant.parse(input.reviewAtUtc()).isAfter(CiBootstrap.pipelineTiming(plan).workDeadline()))
            throw new IOException("Actual same-machine original Tools input and admitted fresh output required");
        for(var pin:input.fullOwn().arguments(input.toolsReceiptRef()))pin.verify();
        input.fullOwn().producerSourceRef().verify();input.fullOwn().boundedInputManifestRef().verify();
        for(var pin:input.junitRuntime())pin.verify();for(var pin:input.largeInputs())pin.verify();
        input.capacityReleaseRef().verify();ProjectStoragePolicy.requireBulkOutput(target);SharedSourceFiles.plainAncestors(target);
        ControlBuild.revalidateCiResources(plan,Path.of(input.capacityReleaseRef().path()),1L<<20);publish(target,input);
        var result=ControlBuild.FileRef.measure(target);
        if(!input.equals(readPinned(result,ToolsInputPostqualification.Input.class,MAX_CONFIG_BYTES)))throw new IOException("Typed original Tools input roundtrip changed");
        return result;
    }
    private static ToolsInputPostqualification.Execution postqualificationExecution(TestCompilation compile,StageJava java) {
        return new ToolsInputPostqualification.Execution(compile.terminal(),java.terminal(),java.nativeEvidence(),java.carrier(),
                java.arguments(),java.options(),java.stdout(),java.stderr(),compile.inputs());
    }
    private static ControlBuild.FileRef postqualifyTools(ControlBuild.FileRef inputRef)throws IOException,InterruptedException {
        var inputWitness=SharedSourceFiles.observe(Path.of(inputRef.path()));
        if(!inputWitness.source().equals(inputRef))throw new IOException("Original postqualification input identity changed");
        var input=readPinned(inputRef,ToolsInputPostqualification.Input.class,MAX_CONFIG_BYTES);
        var plan=readPinned(input.resourcePlanRef(),CiBootstrap.Plan.class,MAX_CONFIG_BYTES);
        var timing=CiBootstrap.pipelineTiming(plan);Instant start=Instant.now();
        Instant end=earlier(Instant.parse(input.reviewAtUtc()),earlier(timing.workDeadline(),start.plusSeconds(900)));
        if(!input.machineId().equals(plan.machineId())||!plan.machineId().equals(WindowsJobProcess.currentMachineId())
                ||Instant.parse(input.observedAtUtc()).isBefore(timing.observedAt())||Instant.parse(input.observedAtUtc()).isAfter(start)||!start.isBefore(end))
            throw new IOException("Original actual postqualification machine/window unavailable");
        if(Duration.between(start,end).compareTo(Duration.ofSeconds(900))<0)
            throw new IOException("NOT EXECUTED: complete original Own plus two-JUnit bounds require900 unspent seconds");
        var tools=ControlBuild.verifiedCompletedReceipt(input.toolsReceiptRef());
        if(tools.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME||!tools.completeDeployment().equals(ControlBuild.producerClosure()))
            throw new IOException("Postqualification must run in this complete actual qualified Tools archive");
        requireJUnit(Path.of(tools.deploymentRoot()).resolve("surefire-reports"),tools);
        Path release=Path.of(input.capacityReleaseRef().path());
        input.capacityReleaseRef().verify();ControlBuild.revalidateCiResources(plan,release,16L<<20);
        Path root=Path.of(plan.workRoot()).resolve("artifacts/tools-postqualification");
        ProjectStoragePolicy.requireBulkOutput(root);SharedSourceFiles.plainAncestors(root);Files.createDirectories(root.getParent());Files.createDirectory(root);
        Path ownRoot=Files.createDirectory(root.resolve("own"));Path ownOutput=ownRoot.resolve("actual.json");
        input.fullOwn().producerSourceRef().verify();
        var ownCompile=compileActual(plan,release,ownRoot.resolve("compile"),List.of(input.fullOwn().producerSourceRef()),jarClosure(tools),end,List.of(inputWitness));
        Instant ownEnd=earlier(end,Instant.now().plusSeconds(300));
        var ownRun=stageJava(plan,release,ownRoot.resolve("run"),ToolsInputPostqualification.OWN_CLASS,
                actualClasspath(jarClosure(tools),ownCompile.classes(),List.of()),List.of(),ownArguments(input,ownOutput),512L<<20,ownEnd,end,List.of(inputWitness));
        var ownRef=ControlBuild.FileRef.measure(ownOutput);requireFullOwnOutput(ownRef,input,tools);
        var ownExecution=postqualificationExecution(ownCompile,ownRun);
        requirePostqualificationExecution(ownExecution,ToolsInputPostqualification.OWN_CLASS,List.of(input.fullOwn().producerSourceRef()),
                List.of(),ownArguments(input,ownOutput),plan,tools,List.of());
        var bindingAndSpec=produceLargeInputSpec(root,input,ownRef,plan,tools,end);
        var testSource=sourceFor(tools,"src/test/java/org/xar/ck3/control/build/SharedOwnedCommandInputCountActualRegression.java");
        var cp=new ArrayList<>(jarClosure(tools));cp.addAll(input.junitRuntime());
        var testCompile=compileActual(plan,release,root.resolve("compile"),List.of(testSource),cp,end,List.of(inputWitness));
        var props=ToolsInputPostqualification.properties(bindingAndSpec.binding(),bindingAndSpec.spec());
        var testRun=stageJava(plan,release,root.resolve("junit"),ToolsInputPostqualification.TEST_CLASS,
                actualClasspath(jarClosure(tools),testCompile.classes(),input.junitRuntime()),props,List.of(),512L<<20,
                earlier(end,Instant.now().plusSeconds(300)),end,List.of(inputWitness));
        var testExecution=postqualificationExecution(testCompile,testRun);
        var request=SharedOwnedCommand.parseRequest(readPinned(bindingAndSpec.spec(),com.fasterxml.jackson.databind.JsonNode.class,1L<<20));
        var actual=new ToolsInputPostqualification.Actual(ToolsInputPostqualification.ACTUAL_SCHEMA,
                ToolsInputPostqualification.Scope.MECHANICAL_LARGE_INPUTS_AFTER_COMPLETE_INTEGRATED_OWN_ONLY,plan.machineId(),start.toString(),
                Instant.now().toString(),end.toString(),inputRef,inputWitness,input.toolsReceiptRef(),ownRef,ownExecution,
                ControlBuild.FileRef.measure(ownRoot.resolve("input-guard.actual.json")),bindingAndSpec.binding(),
                bindingAndSpec.spec(),testExecution,ControlBuild.FileRef.measure(request.outputRoot().resolve("terminal.json")),2);
        requireToolsPostqualificationValue(actual,input,plan,tools);
        ControlBuild.revalidateCiResources(plan,release,1L<<20);Path output=root.resolve("actual.json");publish(output,actual);
        var result=ControlBuild.FileRef.measure(output);requireToolsPostqualification(result,input.toolsReceiptRef());return result;
    }
    private record BindingAndSpec(ControlBuild.FileRef binding,ControlBuild.FileRef spec) { }
    private static BindingAndSpec produceLargeInputSpec(Path root,ToolsInputPostqualification.Input input,ControlBuild.FileRef own,
            CiBootstrap.Plan plan,ControlBuild.BuildReceipt tools,Instant deadline)throws IOException {
        String owner="/root/ci_tools_postqualification",slot="postqualification",run="large-inputs-2048";
        Path slotRoot=Files.createDirectory(root.resolve("native-command"));Path temp=Files.createDirectory(root.resolve("native-tmp"));
        Path aggregate=Files.createDirectory(root.resolve("private-tmp"));
        var json=ControlBuild.strictMapper();var executable=ControlBuild.FileRef.measure(Path.of(System.getenv("SystemRoot")).resolve("System32/hostname.exe"));
        var launcher=sourceFor(tools,"src/main/java/org/xar/ck3/control/build/SharedOwnedCommand.java");
        var standing=json.createObjectNode();standing.put("schema","xar.control-ci-postqualification-standing/v1");
        standing.put("status","AUTHORIZED_CONTROLLED_MECHANICAL_REGRESSION");standing.put("machine_id",plan.machineId());
        standing.put("review_at_utc",deadline.toString());standing.put("native_tmp_root",temp.toString());
        standing.put("private_temporary_aggregate_root",aggregate.toString());
        standing.set("source_grant_ref",json.valueToTree(input.resourcePlanRef()));
        standing.set("capacity_release_ref",json.valueToTree(input.capacityReleaseRef()));
        standing.set("qualified_tools_ref",json.valueToTree(input.toolsReceiptRef()));standing.set("qualified_own_readback_ref",json.valueToTree(own));
        standing.set("runtime_closure",json.valueToTree(tools.completeDeployment()));standing.set("allowed_executables",json.valueToTree(List.of(executable)));
        var grant=standing.putArray("slots").addObject();grant.put("slot_id",slot);grant.put("serial",true);grant.put("coordinator",owner);
        grant.put("output_root",slotRoot.toString());grant.put("output_cap_bytes",32L<<20);grant.put("worker_memory_limit_bytes",512L<<20);
        grant.put("outer_memory_budget_bytes",256L<<20);grant.put("timeout_seconds",120);
        Path standingPath=root.resolve("standing.json");writePostqualificationJson(standingPath,standing);var standingRef=ControlBuild.FileRef.measure(standingPath);
        var delivery=json.createObjectNode();delivery.put("schema","xar.control-ci-postqualification-delivery/v1");
        delivery.put("status","ACTUAL_COMPLETE_TOOLS_AND_FULL_OWN");delivery.put("machine_id",plan.machineId());
        delivery.set("complete_runtime",json.valueToTree(tools.completeDeployment()));
        delivery.set("qualified_tools_ref",json.valueToTree(input.toolsReceiptRef()));delivery.set("qualified_own_readback_ref",json.valueToTree(own));
        Path deliveryPath=root.resolve("delivery.json");writePostqualificationJson(deliveryPath,delivery);var deliveryRef=ControlBuild.FileRef.measure(deliveryPath);
        var binding=new SharedOwnedCommandBinding(SharedOwnedCommandBinding.SCHEMA,plan.machineId(),launcher,standingRef,deliveryRef,temp,aggregate,
                new SharedOwnedCommandBinding.AuthorityExpectation("xar.control-ci-postqualification-standing/v1","AUTHORIZED_CONTROLLED_MECHANICAL_REGRESSION"),
                new SharedOwnedCommandBinding.AuthorityExpectation("xar.control-ci-postqualification-delivery/v1","ACTUAL_COMPLETE_TOOLS_AND_FULL_OWN"));
        Path bindingPath=root.resolve("binding.json");writePostqualificationJson(bindingPath,binding.toJson());var bindingRef=ControlBuild.FileRef.measure(bindingPath);
        var spec=json.createObjectNode();spec.put("schema","xar.shared-owned-command-spec/v2");spec.put("machine_id",plan.machineId());
        spec.put("owner",owner);spec.put("coordinator",owner);spec.put("slot_id",slot);spec.putNull("borrowed_slot_id");spec.put("run_id",run);
        spec.set("standing_ref",json.valueToTree(standingRef));spec.set("launcher_source_ref",json.valueToTree(launcher));
        spec.set("executable",json.valueToTree(executable));spec.putArray("arguments");spec.put("cwd",plan.repoRoot());spec.putObject("environment");
        for(var pin:input.largeInputs())pin.verify();spec.set("inputs",json.valueToTree(input.largeInputs()));
        spec.put("output_root",SharedOwnedCommand.commandOutputRoot(slotRoot,owner,run).toString());
        spec.put("timeout_seconds",120);spec.put("memory_limit_bytes",512L<<20);spec.put("root_exit_drain_policy","UNTIL_COMMAND_DEADLINE");
        spec.putNull("operation_card_ref");spec.put("temporary_policy","SLOT_PRIVATE");
        try { SharedOwnedCommand.validateStanding(SharedOwnedCommand.parseRequest(spec),binding,standing); }
        catch(IOException rejected) { throw rejected; }
        catch(Exception rejected) { throw new IOException("Actual controlled standing rejected",rejected); }
        Path specPath=root.resolve("spec.json");writePostqualificationJson(specPath,spec);return new BindingAndSpec(bindingRef,ControlBuild.FileRef.measure(specPath));
    }
    private static void writePostqualificationJson(Path path,com.fasterxml.jackson.databind.JsonNode value)throws IOException {
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(value);
        if(raw.length>(1<<20))throw new IOException("Postqualification metadata exceeds existing1MiB bound");
        Files.write(path,raw,StandardOpenOption.CREATE_NEW);
    }
    private static void requireFullOwnOutput(ControlBuild.FileRef ref,ToolsInputPostqualification.Input input,ControlBuild.BuildReceipt tools)throws IOException {
        var own=readPinned(ref,com.fasterxml.jackson.databind.JsonNode.class,128L<<10);var json=ControlBuild.strictMapper();
        if(!ToolsInputPostqualification.OWN_SCHEMA.equals(jsonText(own,"schema"))||!ToolsInputPostqualification.OWN_SCOPE.equals(jsonText(own,"scope"))
                ||!input.machineId().equals(jsonText(own,"machine_id"))
                ||!json.treeToValue(own.required("build_receipt_ref"),ControlBuild.FileRef.class).equals(input.toolsReceiptRef())
                ||!json.treeToValue(own.required("materialized_map_ref"),ControlBuild.FileRef.class).equals(input.fullOwn().materializedMapRef())
                ||!json.treeToValue(own.required("historical_completed_receipt_ref"),ControlBuild.FileRef.class).equals(input.fullOwn().historicalCompletedReceiptRef())
                ||!json.treeToValue(own.required("genuine_historical_capture_ref"),ControlBuild.FileRef.class).equals(input.fullOwn().genuineHistoricalCaptureRef())
                ||!java.util.Arrays.asList(json.treeToValue(own.required("complete_running_runtime"),ControlBuild.FileRef[].class)).equals(tools.completeDeployment()))
            throw new IOException("Actual unchanged full Own did not bind the same complete verified Tools and original inputs");
        if(!own.required("historical_live_lease_rejected").isBoolean()||!own.required("historical_live_lease_rejected").booleanValue()
                ||!own.required("genuine_capture_live_lease_rejected").isBoolean()||!own.required("genuine_capture_live_lease_rejected").booleanValue())
            throw new IOException("Original complete Own historical rejection assertions were not passed");
    }
    private static void requirePostqualificationExecution(ToolsInputPostqualification.Execution proof,String targetName,
            List<ControlBuild.FileRef> sources,List<JavaUtf8Invocation.Property> properties,List<String> arguments,
            CiBootstrap.Plan plan,ControlBuild.BuildReceipt tools,List<ControlBuild.FileRef> junit)throws IOException {
        for(var witness:proof.inputs())SharedSourceFiles.assertUnchanged(witness);
        for(var source:sources)if(proof.inputs().stream().noneMatch(item->item.source().equals(source)))
            throw new IOException("Postqualification compiler witness omitted its actual original source");
        var compile=readPinned(proof.compileTerminal(),WindowsJobProcess.CommandResult.class,MAX_CONFIG_BYTES);
        var terminal=readPinned(proof.javaTerminal(),WindowsJobProcess.CommandResult.class,MAX_CONFIG_BYTES);
        if(!compile.passed()||!terminal.passed()||!Path.of(compile.identity().executable()).equals(Path.of(plan.javaHome()).resolve("bin/javac.exe"))
                ||!Path.of(terminal.identity().executable()).equals(Path.of(plan.javaHome()).resolve("bin/java.exe")))
            throw new IOException("Original actual compiler and child Jobs must exit0 and drain Job0");
        if(proof.carrier().size()!=1||!tools.completeDeployment().contains(proof.carrier().getFirst()))throw new IOException("Actual carrier is not this qualified original Tools JAR");
        var carrier=new JavaUtf8Invocation.ClassCarrier(List.of(JavaUtf8Invocation.captureClasspath(Path.of(proof.carrier().getFirst().path()))));
        var logical=JavaUtf8Invocation.inspect(proof.physicalArguments(),carrier,proof.startupOptions());
        if(!(logical.target() instanceof JavaUtf8Invocation.ClassTarget target)||!target.mainClass().equals(targetName)
                ||!logical.arguments().equals(arguments)||!logical.properties().equals(properties))throw new IOException("Exact unfiltered original postqualification invocation changed");
        Path classes=Path.of(proof.compileTerminal().path()).getParent().resolve("classes").toRealPath();
        var expected=new HashSet<String>();for(var pin:jarClosure(tools))expected.add(pin.path());for(var pin:junit)expected.add(pin.path());expected.add(classes.toString());
        var actual=new HashSet<String>();
        for(var pin:target.classpath()) {
            if(!actual.add(pin.path()))throw new IOException("Duplicate actual postqualification classpath");
            if(pin instanceof JavaUtf8Invocation.DirectoryClasspath directory) {
                if(!Path.of(directory.path()).toRealPath().equals(classes))throw new IOException("Production target/classes is not a qualified JAR");
                for(var file:directory.files()) {
                    String type=classes.relativize(Path.of(file.path())).toString().replace('\\','/').replace('/','.').replaceAll("\\.class$","");
                    if(!type.equals(targetName)&&!type.startsWith(targetName+"$"))throw new IOException("Postqualification test directory contains a production override");
                }
            }
        }
        if(!actual.equals(expected))throw new IOException("Postqualification escaped the exact original production/JUnit closure");
        var publication=new JavaUtf8Invocation.Publication(JavaUtf8Invocation.captureFile(Path.of(proof.physicalArguments().get(proof.physicalArguments().size()-4))));
        var launch=JavaUtf8Invocation.launch(publication,carrier,proof.startupOptions());
        if(!launch.physicalArguments().equals(proof.physicalArguments()))throw new IOException("Postqualification physical invocation changed");
        var nativeProof=JavaUtf8NativeCustody.decodeEvidence(readOriginalBytes(proof.nativeEvidence(),JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES));
        if(!nativeProof.terminal().equals(terminal))throw new IOException("Actual native child terminal changed");
        JavaUtf8NativeCustody.requireCurrent(nativeProof,launch,carrier);
        JavaUtf8Invocation.inspectPreparation(JavaUtf8Invocation.captureFile(JavaUtf8Invocation.preparationPath(logical)),publication);
        proof.stdout().verify();proof.stderr().verify();
    }
    public static ToolsInputPostqualification.Actual requireToolsPostqualification(ControlBuild.FileRef reference,ControlBuild.FileRef expectedTools)throws IOException {
        var actual=readPinned(reference,ToolsInputPostqualification.Actual.class,MAX_CONFIG_BYTES);
        if(expectedTools!=null&&!actual.toolsReceiptRef().equals(expectedTools))throw new IOException("Mechanical proof belongs to another Tools build");
        var input=readPinned(actual.inputRef(),ToolsInputPostqualification.Input.class,MAX_CONFIG_BYTES);
        var plan=readPinned(input.resourcePlanRef(),CiBootstrap.Plan.class,MAX_CONFIG_BYTES);
        var tools=ControlBuild.verifiedCompletedReceipt(input.toolsReceiptRef());
        requireToolsPostqualificationValue(actual,input,plan,tools);reference.verify();return actual;
    }
    private static void requireToolsPostqualificationValue(ToolsInputPostqualification.Actual actual,ToolsInputPostqualification.Input input,
            CiBootstrap.Plan plan,ControlBuild.BuildReceipt tools)throws IOException {
        SharedSourceFiles.assertUnchanged(actual.inputWitness());
        for(var pin:input.fullOwn().arguments(input.toolsReceiptRef()))pin.verify();
        input.fullOwn().producerSourceRef().verify();input.fullOwn().boundedInputManifestRef().verify();
        var originalGuard=readPinned(actual.fullOwnInputGuardRef(),BoundedSourceInputGuard.Receipt.class,MAX_CONFIG_BYTES);
        if(!"xar.bounded-source-input-readback/v1".equals(originalGuard.schema())||!"MATCH".equals(originalGuard.postcheck())
                ||!plan.machineId().equals(originalGuard.machineId())||!"/root/tools_c15".equals(originalGuard.taskOwner())
                ||!originalGuard.manifestRef().equals(input.fullOwn().boundedInputManifestRef())
                ||originalGuard.observations().size()!=originalGuard.files()+1||originalGuard.observations().size()>1025)
            throw new IOException("Unchanged complete Own input-guard actual is mandatory");
        for(var witness:originalGuard.observations())SharedSourceFiles.assertUnchanged(witness);
        if(!actual.machineId().equals(plan.machineId())||!input.machineId().equals(plan.machineId())
                ||!plan.machineId().equals(WindowsJobProcess.currentMachineId())
                ||!actual.toolsReceiptRef().equals(input.toolsReceiptRef())||!tools.machineId().equals(plan.machineId())
                ||Instant.parse(actual.reviewAtUtc()).isAfter(Instant.parse(input.reviewAtUtc()))
                ||Instant.parse(actual.reviewAtUtc()).isAfter(CiBootstrap.pipelineTiming(plan).workDeadline()))
            throw new IOException("Original mechanical proof machine, Tools or deadline changed");
        requireFullOwnOutput(actual.fullOwnActualRef(),input,tools);
        requirePostqualificationExecution(actual.fullOwnExecution(),ToolsInputPostqualification.OWN_CLASS,List.of(input.fullOwn().producerSourceRef()),
                List.of(),ownArguments(input,Path.of(actual.fullOwnActualRef().path())),plan,tools,List.of());
        var binding=SharedOwnedCommandBinding.read(actual.bindingRef());
        var standing=readPinned(binding.standingRef(),com.fasterxml.jackson.databind.JsonNode.class,1L<<20);
        var json=ControlBuild.strictMapper();
        var delivery=readPinned(binding.deliveryRef(),com.fasterxml.jackson.databind.JsonNode.class,1L<<20);
        SharedOwnedCommandBinding.verifyAuthority(standing,binding.standingExpectation(),plan.machineId());
        SharedOwnedCommandBinding.verifyAuthority(delivery,binding.deliveryExpectation(),plan.machineId());
        if(!json.treeToValue(standing.required("qualified_tools_ref"),ControlBuild.FileRef.class).equals(input.toolsReceiptRef())
                ||!json.treeToValue(standing.required("qualified_own_readback_ref"),ControlBuild.FileRef.class).equals(actual.fullOwnActualRef())
                ||!json.treeToValue(standing.required("source_grant_ref"),ControlBuild.FileRef.class).equals(input.resourcePlanRef())
                ||!json.treeToValue(standing.required("capacity_release_ref"),ControlBuild.FileRef.class).equals(input.capacityReleaseRef())
                ||!java.util.Arrays.asList(json.treeToValue(delivery.required("complete_runtime"),ControlBuild.FileRef[].class)).equals(tools.completeDeployment())
                ||!binding.launcherSourceRef().equals(sourceFor(tools,"src/main/java/org/xar/ck3/control/build/SharedOwnedCommand.java"))
                ||!Instant.parse(jsonText(standing,"review_at_utc")).equals(Instant.parse(actual.reviewAtUtc())))
            throw new IOException("Mechanical standing lost the same actual complete Own and Tools");
        var spec=SharedOwnedCommand.parseRequest(readPinned(actual.specRef(),com.fasterxml.jackson.databind.JsonNode.class,1L<<20));
        if(!spec.inputs().equals(input.largeInputs())||!spec.arguments().isEmpty()||spec.timeoutSeconds()!=120||spec.memoryLimitBytes()!=(512L<<20)
                ||!spec.schema().equals("xar.shared-owned-command-spec/v2")||!spec.environment().isEmpty()
                ||!spec.standingRef().equals(binding.standingRef())||!spec.cwd().equals(Path.of(plan.repoRoot()))
                ||!spec.executable().equals(ControlBuild.FileRef.measure(Path.of(System.getenv("SystemRoot")).resolve("System32/hostname.exe"))))
            throw new IOException("Original controlled actual large-input Spec changed");
        requirePostqualificationExecution(actual.junitExecution(),ToolsInputPostqualification.TEST_CLASS,
                List.of(sourceFor(tools,"src/test/java/org/xar/ck3/control/build/SharedOwnedCommandInputCountActualRegression.java")),
                ToolsInputPostqualification.properties(actual.bindingRef(),actual.specRef()),List.of(),plan,tools,input.junitRuntime());
        if(actual.junitExecution().stdout().bytes()>(1L<<20)||!Files.readString(Path.of(actual.junitExecution().stdout().path())).lines().anyMatch(ToolsInputPostqualification.MARKER::equals))
            throw new IOException("Actual exact2/2 JUnit success marker missing");
        var nativeTerminal=SharedOwnedCommand.readNativeTerminal(actual.commandTerminalRef()).terminal();
        if(!actual.specRef().equals(nativeTerminal.requestRef())||nativeTerminal.status()!=SharedOwnedCommand.Status.PASS||!nativeTerminal.childStarted()
                ||nativeTerminal.child()==null||!nativeTerminal.child().passed()||nativeTerminal.inputPrecheck()!=SharedOwnedCommand.Check.MATCH
                ||nativeTerminal.inputPostcheck()!=SharedOwnedCommand.Check.MATCH||nativeTerminal.runtimePostcheck()!=SharedOwnedCommand.Check.MATCH
                ||!nativeTerminal.completeRuntime().equals(tools.completeDeployment())||nativeTerminal.inputBefore().size()!=spec.inputs().size()+2)
            throw new IOException("Every real original input must have matching before/periodic/post native evidence");
        if(!nativeTerminal.inputBefore().getFirst().source().equals(actual.bindingRef())||!nativeTerminal.inputBefore().get(1).source().equals(spec.executable()))
            throw new IOException("Native binding/executable witness order changed");
        for(int index=0;index<nativeTerminal.inputBefore().size();index++) {
            var witness=nativeTerminal.inputBefore().get(index);SharedSourceFiles.assertUnchanged(witness);
            if(index>=2&&!witness.source().equals(spec.inputs().get(index-2)))throw new IOException("Individual original input identity/order changed");
        }
    }

    private record StageJava(ControlBuild.FileRef terminal,ControlBuild.FileRef nativeEvidence,
            List<ControlBuild.FileRef> carrier,List<String> arguments,List<String> options,
            ControlBuild.FileRef stdout,ControlBuild.FileRef stderr) { }
    private static StageJava stageJava(CiBootstrap.Plan plan,Path release,Path root,String target,
            List<JavaUtf8Invocation.ClasspathPin> classpath,List<JavaUtf8Invocation.Property> properties,List<String> arguments,
            long memory,Instant deadline,Instant settlementDeadline)throws IOException,InterruptedException {
        return stageJava(plan,release,root,target,classpath,properties,arguments,memory,deadline,settlementDeadline,List.of());
    }
    private static StageJava stageJava(CiBootstrap.Plan plan,Path release,Path root,String target,
            List<JavaUtf8Invocation.ClasspathPin> classpath,List<JavaUtf8Invocation.Property> properties,List<String> arguments,
            long memory,Instant deadline,Instant settlementDeadline,List<SharedSourceFiles.Witness> dataWitnesses)throws IOException,InterruptedException {
        dataWitnesses=List.copyOf(dataWitnesses);final var guardedData=dataWitnesses;
        for(var witness:guardedData)SharedSourceFiles.assertUnchanged(witness);
        var timing=CiBootstrap.pipelineTiming(plan);
        if(!Instant.now().isBefore(deadline)||deadline.isAfter(settlementDeadline)||settlementDeadline.isAfter(timing.workDeadline()))throw new IOException("Original stage deadline unavailable");
        Files.createDirectory(root);
        var pins=new ArrayList<JavaUtf8Invocation.ClasspathPin>();
        for(var pin:classpath){if(!pin.equals(JavaUtf8Invocation.captureClasspath(Path.of(pin.path()))))throw new IOException("Actual stage classpath drifted");pins.add(pin);}
        var origin=pins.stream().filter(pin-> {
            try {
                Path value=Path.of(pin.path());
                if(Files.isDirectory(value))return Files.isRegularFile(value.resolve(target.replace('.','/')+".class"));
                try(var jar=new java.util.jar.JarFile(value.toFile(),false)){return jar.getJarEntry(target.replace('.','/')+".class")!=null;}
            }catch(IOException invalid){throw new java.io.UncheckedIOException(invalid);}
        }).toList();
        if(origin.size()!=1)throw new IOException("One exact actual class origin required for "+target);
        var output=JavaUtf8Invocation.captureOutputRoot(root);
        var request=new JavaUtf8Invocation.Request(new JavaUtf8Invocation.ClassTarget(target,origin.getFirst(),pins),properties,arguments,output);
        JavaUtf8Invocation.OutputGuard guard=pending->{
            for(var witness:guardedData)SharedSourceFiles.assertUnchanged(witness);
            if(!Instant.now().isBefore(settlementDeadline))throw new IOException("Original actual stage settlement window expired");
            for(var pin:classpath)if(!pin.equals(JavaUtf8Invocation.captureClasspath(Path.of(pin.path()))))throw new IOException("Actual stage classpath changed");
            ControlBuild.revalidateCiResources(plan,release,pending);
        };
        var publication=JavaUtf8Invocation.publish(request,output,"actual-invocation.bin",guard);
        var carrier=currentJavaCarrier();
        var options=List.of("-Xms32m","-Xmx192m","-XX:MaxMetaspaceSize=96m","-XX:ReservedCodeCacheSize=64m",
                "-XX:ActiveProcessorCount=2","-Djava.io.tmpdir="+Path.of(plan.workRoot()).resolve("scratch"),
                "-Djna.tmpdir="+Path.of(plan.workRoot()).resolve("scratch"));
        var launch=JavaUtf8Invocation.launch(publication,carrier,options);
        Path stdout=root.resolve("stdout.log"),stderr=root.resolve("stderr.log"),terminal=root.resolve("terminal.json");
        var env=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());
        env.remove("JAVA_TOOL_OPTIONS");env.remove("JDK_JAVA_OPTIONS");
        if(target.equals(ToolsInputPostqualification.OWN_CLASS))env.remove("XAR_ORACLE_PYTHON");
        env.put("TEMP",Path.of(plan.workRoot()).resolve("scratch").toString());env.put("TMP",env.get("TEMP"));
        var command=new WindowsJobProcess.CommandSpec(Path.of(plan.javaHome()).resolve("bin/java.exe"),launch.physicalArguments(),
                Path.of(plan.repoRoot()),env,stdout,stderr,memory);
        var prepared=new QualifiedJavaLaunch(command,launch,carrier,options);
        var nativeRef=runQualifiedChild(prepared,Duration.between(Instant.now(),deadline),deadline,terminal,
                root.resolve("native-sources.json"),guard);
        requireQualifiedPreparation(prepared);
        return new StageJava(ControlBuild.FileRef.measure(terminal),nativeRef,
                List.of(ControlBuild.FileRef.measure(Path.of(carrier.classpath().getFirst().path()))),launch.physicalArguments(),options,
                ControlBuild.FileRef.measure(stdout),ControlBuild.FileRef.measure(stderr));
    }
    private record TestCompilation(Path classes,ControlBuild.FileRef terminal,List<SharedSourceFiles.Witness> inputs) { }
    private static String javacArgument(String value)throws IOException {
        if(value.indexOf('\n')>=0||value.indexOf('\r')>=0||value.indexOf(0)>=0)throw new IOException("Single-line actual javac argument required");
        return "\""+value.replace("\\","\\\\").replace("\"","\\\"")+"\"";
    }
    private static TestCompilation compileActual(CiBootstrap.Plan plan,Path release,Path root,
            List<ControlBuild.FileRef> sources,List<ControlBuild.FileRef> classpath,Instant deadline)throws IOException,InterruptedException {
        return compileActual(plan,release,root,sources,classpath,deadline,List.of());
    }
    private static TestCompilation compileActual(CiBootstrap.Plan plan,Path release,Path root,
            List<ControlBuild.FileRef> sources,List<ControlBuild.FileRef> classpath,Instant deadline,
            List<SharedSourceFiles.Witness> dataWitnesses)throws IOException,InterruptedException {
        Files.createDirectory(root);Path classes=Files.createDirectory(root.resolve("classes"));
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        witnesses.addAll(List.copyOf(dataWitnesses));
        for(var pin:java.util.stream.Stream.concat(sources.stream(),classpath.stream()).toList()){
            pin.verify();var witness=SharedSourceFiles.observe(Path.of(pin.path()));
            if(!witness.source().equals(pin))throw new IOException("Actual compiler input drifted");witnesses.add(witness);
        }
        var args=new ArrayList<>(List.of("--release","21","-encoding","UTF-8","-Xlint:all","-Werror","-cp",
                String.join(java.io.File.pathSeparator,classpath.stream().map(ControlBuild.FileRef::path).toList()),"-d",classes.toString()));
        args.addAll(sources.stream().map(ControlBuild.FileRef::path).toList());
        StringBuilder text=new StringBuilder();for(String arg:args)text.append(javacArgument(arg)).append('\n');
        ControlBuild.revalidateCiResources(plan,release,16L<<20);
        Path argumentFile=root.resolve("javac.args");Files.writeString(argumentFile,text,java.nio.charset.StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        var env=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());
        env.remove("JAVA_TOOL_OPTIONS");env.remove("JDK_JAVA_OPTIONS");env.put("TEMP",Path.of(plan.workRoot()).resolve("scratch").toString());env.put("TMP",env.get("TEMP"));
        var command=new WindowsJobProcess.CommandSpec(Path.of(plan.javaHome()).resolve("bin/javac.exe"),
                List.of("-J-Xms32m","-J-Xmx192m","-J-XX:MaxMetaspaceSize=96m","-J-XX:ReservedCodeCacheSize=64m",
                        "-J-XX:ActiveProcessorCount=2","-J-Dfile.encoding=UTF-8","@"+argumentFile),
                Path.of(plan.repoRoot()),env,root.resolve("stdout.log"),root.resolve("stderr.log"),512L<<20);
        WindowsJobProcess.CommandResult terminal;
        try(var child=WindowsJobProcess.start(command)) {
            terminal=child.await(Duration.ofSeconds(120),earlier(deadline,Instant.now().plusSeconds(120)),()->{
                try{for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);ControlBuild.revalidateCiResources(plan,release,0);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
        }
        Path terminalPath=root.resolve("terminal.json");publish(terminalPath,terminal);
        for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);
        if(!terminal.passed())throw new IOException("Actual persistent integration source compilation failed: "+terminal);
        return new TestCompilation(classes,ControlBuild.FileRef.measure(terminalPath),List.copyOf(witnesses));
    }

    private static List<JavaUtf8Invocation.ClasspathPin> actualClasspath(List<ControlBuild.FileRef> production,
            Path testClasses,List<ControlBuild.FileRef> junit)throws IOException {
        var pins=new ArrayList<JavaUtf8Invocation.ClasspathPin>();
        for(var file:production){file.verify();pins.add(JavaUtf8Invocation.captureClasspath(Path.of(file.path())));}
        if(testClasses!=null)pins.add(JavaUtf8Invocation.captureClasspath(testClasses));
        for(var file:junit){file.verify();pins.add(JavaUtf8Invocation.captureClasspath(Path.of(file.path())));}return List.copyOf(pins);
    }
    private static ControlBuild.FileRef runPerson10Actual(CiBootstrap.Plan resources,Path release,ControlBuild.FileRef postRef,
            PostqualificationPlan input,ControlBuild.FileRef toolsRef,ControlBuild.BuildReceipt tools)throws IOException,InterruptedException {
        Instant start=Instant.now(),deadline=earlier(CiBootstrap.pipelineTiming(resources).workDeadline(),start.plusSeconds(5160));
        Path root=Files.createDirectory(Path.of(resources.workRoot()).resolve("artifacts/person10-actual"));
        ControlBuild.FileRef actualRef;
        if(input.person10().mode()==Person10ProductionMode.PRODUCE_FROM_REQUEST) {
            var original=Person10NativeCorpusBuild.readRequest(input.person10().original());
            if(!original.producerRuntimeBuild().equals(toolsRef)||!original.machineId().equals(resources.machineId())
                    ||!original.limits().capacityEvidence().equals(ControlBuild.FileRef.measure(release))
                    ||!original.limits().ownerTask().equals(resources.ownerTask()))
                throw new IOException("Person10 request must consume this actual qualified tools build and issued capacity owner");
            Instant productionEnd=earlier(original.limits().deadline(),earlier(deadline, start.plusSeconds(4500)));
            var limits=new NativeBridgeRootGate.Limits(original.limits().ownerTask(),original.limits().capacityEvidence(),productionEnd,
                    original.limits().memoryLimitBytes(),original.limits().outputAllocationLimitBytes(),Math.min(3600,original.limits().timeoutSeconds()));
            var request=new Person10NativeCorpusBuild.Request(original.schema(),original.machineId(),original.environmentActual(),
                    original.producerRuntimeBuild(),original.compiledAddon(),original.buildRoot(),original.outputRoot(),original.temporaryRoot(),
                    original.parallelJobs(),original.existingResearchCache(),limits);
            var requestRef=Person10NativeCorpusBuild.writeRequest(request,root.resolve("actual-request.json"));
            stageJava(resources,release,root.resolve("native-producer"),Person10NativeCorpusBuild.class.getName(),
                    actualClasspath(jarClosure(tools),null,List.of()),List.of(),List.of(requestRef.path(),requestRef.sha256()),4L<<30,productionEnd,deadline);
            actualRef=ControlBuild.FileRef.measure(request.outputRoot().resolve(Person10NativeCorpusBuild.ACTUAL_NAME));
        } else actualRef=input.person10().original();
        var actual=Person10NativeCorpusBuild.readProduced(actualRef);
        var request=Person10NativeCorpusBuild.readRequest(actual.requestRef());
        if(actual.status()!=Person10NativeCorpusBuild.Status.PASS||!request.producerRuntimeBuild().equals(toolsRef))
            throw new IOException("Complete current Person10 producer actual is mandatory");
        Instant reviewEnd=earlier(deadline,Instant.now().plusSeconds(600));
        var production=jarClosure(tools);var compileCp=new ArrayList<>(production);compileCp.addAll(input.junitRuntime());
        var compiled=compileActual(resources,release,root.resolve("compile"),
                List.of(sourceFor(tools,"src/test/java/org/xar/ck3/control/build/Person10NativeCorpusBuildActualRegression.java")),compileCp,reviewEnd);
        var props=List.of(new JavaUtf8Invocation.Property("xar.person10.nativeCorpus",request.corpusRoot().toString()),
                new JavaUtf8Invocation.Property("xar.person10.nativeCorpus.manifest",actual.corpusManifest().path()),
                new JavaUtf8Invocation.Property("xar.person10.nativeCorpus.manifest.sha256",actual.corpusManifest().sha256()));
        var data=List.of(actualRef,actual.requestRef(),actual.corpusManifest());
        var originalInputs=actualInputs(compiled,data);
        var run=stageJava(resources,release,root.resolve("junit"),"org.xar.ck3.control.build.Person10NativeCorpusBuildActualRegression",
                actualClasspath(production,compiled.classes(),input.junitRuntime()),props,List.of(),512L<<20,reviewEnd,deadline);
        var proof=new IntegrationActual("xar.control-ci-actual-integration/v1",Stage.PERSON10_ACTUAL,resources.machineId(),start.toString(),
                Instant.now().toString(),deadline.toString(),postRef,toolsRef,null,data,
                originalInputs,compiled.terminal(),run.terminal(),run.nativeEvidence(),run.carrier(),run.arguments(),run.options(),run.stdout(),run.stderr(),1);
        Path output=root.resolve("actual.json");publish(output,proof);var pin=ControlBuild.FileRef.measure(output);
        requireIntegrationActual(pin,Stage.PERSON10_ACTUAL,resources,postRef,toolsRef,null);return pin;
    }
    private static ControlBuild.FileRef runRootInvocationActual(CiBootstrap.Plan resources,Path release,ControlBuild.FileRef resourcePlanRef,ControlBuild.FileRef postRef,
            PostqualificationPlan input,ControlBuild.FileRef toolsRef,ControlBuild.BuildReceipt tools,
            ControlBuild.FileRef reactorRef,ControlBuild.BuildReceipt reactor)throws IOException,InterruptedException {
        Instant start=Instant.now(),deadline=earlier(CiBootstrap.pipelineTiming(resources).workDeadline(),start.plusSeconds(3060));
        Path root=Files.createDirectory(Path.of(resources.workRoot()).resolve("artifacts/root-invocation-actual"));
        Path actualInputs=root.resolve("inputs.json");Instant productionEnd=earlier(deadline,start.plusSeconds(1800));
        var materialization=new RootMaterializationInput("xar.control-ci-root-materialization/v1",resourcePlanRef,
                ControlBuild.FileRef.measure(release),reactorRef,input.root(),actualInputs,productionEnd.toString());
        Path configured=root.resolve("materialization.json");publish(configured,materialization);
        var production=new ArrayList<>(jarClosure(tools));
        for(var jar:jarClosure(reactor)) {
            try(var opened=new java.util.jar.JarFile(jar.path(),false)){
                if(opened.getJarEntry(ControlCi.class.getName().replace('.','/')+".class")!=null)continue;
            }
            if(!production.contains(jar))production.add(jar);
        }
        var configuredRef=ControlBuild.FileRef.measure(configured);
        stageJava(resources,release,root.resolve("package-producer"),ControlCi.class.getName(),
                actualClasspath(production,null,List.of()),List.of(),
                List.of("--materialize-root-invocation-inputs",configuredRef.path(),Long.toString(configuredRef.bytes()),configuredRef.sha256()),2L<<30,productionEnd,deadline);
        var inputsRef=ControlBuild.FileRef.measure(actualInputs);var invocation=decodeRootInvocationInputsPlan(Files.readAllBytes(actualInputs));
        var manifest=org.xar.ck3.control.build.runtime.JavaRuntimePackageCodec.readManifest(invocation.packageManifest());
        // Original production JARs are mandatory here: Native source custody may bind those exact originals.
        var actualProduction=manifest.outputFiles().stream().filter(row->row.relativePath().endsWith(".jar")).map(row->row.original()).distinct().toList();
        Instant reviewEnd=earlier(deadline,Instant.now().plusSeconds(1200));
        var cp=new ArrayList<>(actualProduction);cp.addAll(input.junitRuntime());
        var compiled=compileActual(resources,release,root.resolve("compile"),List.of(
                sourceFor(reactor,"local-service/src/test/java/org/xar/ck3/control/build/runtime/RootInvocationDeploymentActualRegression.java"),
                sourceFor(reactor,"local-service/src/test/java/org/xar/ck3/control/build/runtime/RootInvocationDeploymentInputsProducer.java")),cp,reviewEnd);
        var props=List.of(new JavaUtf8Invocation.Property("xar.root.invocation.actual-inputs.path",inputsRef.path()),
                new JavaUtf8Invocation.Property("xar.root.invocation.actual-inputs.bytes",Long.toString(inputsRef.bytes())),
                new JavaUtf8Invocation.Property("xar.root.invocation.actual-inputs.sha256",inputsRef.sha256()));
        var data=List.of(inputsRef,invocation.packageManifest(),invocation.invocation());
        var originalInputs=actualInputs(compiled,data);
        var run=stageJava(resources,release,root.resolve("junit"),"org.xar.ck3.control.build.runtime.RootInvocationDeploymentActualRegression",
                actualClasspath(actualProduction,compiled.classes(),input.junitRuntime()),props,List.of(),512L<<20,reviewEnd,deadline);
        var proof=new IntegrationActual("xar.control-ci-actual-integration/v1",Stage.ROOT_INVOCATION_ACTUAL,resources.machineId(),start.toString(),
                Instant.now().toString(),deadline.toString(),postRef,toolsRef,reactorRef,data,
                originalInputs,compiled.terminal(),run.terminal(),run.nativeEvidence(),run.carrier(),run.arguments(),run.options(),run.stdout(),run.stderr(),2);
        Path output=root.resolve("actual.json");publish(output,proof);var pin=ControlBuild.FileRef.measure(output);
        requireIntegrationActual(pin,Stage.ROOT_INVOCATION_ACTUAL,resources,postRef,toolsRef,reactorRef);return pin;
    }

    private static List<SharedSourceFiles.Witness> actualInputs(TestCompilation compiled,List<ControlBuild.FileRef> data)throws IOException {
        var values=new ArrayList<>(compiled.inputs());
        for(var pin:data){pin.verify();var witness=SharedSourceFiles.observe(Path.of(pin.path()));
            if(!witness.source().equals(pin))throw new IOException("Actual input path/content drifted");values.add(witness);}
        return List.copyOf(values);
    }

    private static IntegrationActual requireIntegrationActual(ControlBuild.FileRef reference,Stage expected,CiBootstrap.Plan resources,
            ControlBuild.FileRef postRef,ControlBuild.FileRef toolsRef,ControlBuild.FileRef reactorRef)throws IOException {
        var proof=readPinned(reference,IntegrationActual.class,MAX_CONFIG_BYTES);
        if(proof.stage()!=expected||!proof.machineId().equals(resources.machineId())||!proof.postqualificationPlanRef().equals(postRef)
                ||!proof.toolsReceipt().equals(toolsRef)||!Objects.equals(proof.reactorReceipt(),reactorRef)
                ||!Instant.parse(proof.startedAtUtc()).isBefore(Instant.parse(proof.observedAtUtc()))
                ||Instant.parse(proof.observedAtUtc()).isAfter(Instant.parse(proof.reviewAtUtc()))
                ||Instant.parse(proof.reviewAtUtc()).isAfter(CiBootstrap.pipelineTiming(resources).workDeadline()))
            throw new IOException("Mandatory integration original stage/machine/source/deadline changed");
        readPostqualificationPlan(postRef,resources);
        for(var pin:proof.data())pin.verify();for(var witness:proof.inputWitnesses())SharedSourceFiles.assertUnchanged(witness);
        var compile=readPinned(proof.compileTerminal(),WindowsJobProcess.CommandResult.class,MAX_CONFIG_BYTES);
        var terminal=readPinned(proof.javaTerminal(),WindowsJobProcess.CommandResult.class,MAX_CONFIG_BYTES);
        if(!compile.passed()||!terminal.passed()||!Path.of(compile.identity().executable()).getFileName().toString().equalsIgnoreCase("javac.exe")
                ||!Path.of(terminal.identity().executable()).equals(Path.of(resources.javaHome()).resolve("bin/java.exe")))
            throw new IOException("Original actual compiler and JUnit Jobs must both exit0/drain Job0");
        if(proof.carrier().size()!=1)throw new IOException("One exact packaged qualified carrier required");
        var tools=ControlBuild.verifiedCompletedReceipt(toolsRef);
        if(!tools.completeDeployment().contains(proof.carrier().getFirst()))throw new IOException("Actual carrier escaped the qualified producer");
        var carrier=new JavaUtf8Invocation.ClassCarrier(List.of(JavaUtf8Invocation.captureClasspath(Path.of(proof.carrier().getFirst().path()))));
        var logical=JavaUtf8Invocation.inspect(proof.physicalArguments(),carrier,proof.startupOptions());
        String name=expected==Stage.PERSON10_ACTUAL?"org.xar.ck3.control.build.Person10NativeCorpusBuildActualRegression"
                :"org.xar.ck3.control.build.runtime.RootInvocationDeploymentActualRegression";
        if(!(logical.target() instanceof JavaUtf8Invocation.ClassTarget target)||!target.mainClass().equals(name)||!logical.arguments().isEmpty())
            throw new IOException("Mandatory exact persistent actual class and unfiltered main required");
        Path compiledRoot=Path.of(proof.compileTerminal().path()).getParent().resolve("classes").toRealPath();
        for(var item:target.classpath())if(item instanceof JavaUtf8Invocation.DirectoryClasspath directory) {
            if(!Path.of(directory.path()).toRealPath().equals(compiledRoot))throw new IOException("Production classes cannot be supplied by target/classes");
            for(var file:directory.files()) {
                String relative=compiledRoot.relativize(Path.of(file.path())).toString().replace('\\','/');
                String type=relative.replace('/','.').replaceAll("\\.class$","");
                if(!type.equals(name)&&!type.startsWith(name+"$")
                        &&!(expected==Stage.ROOT_INVOCATION_ACTUAL&&(type.equals("org.xar.ck3.control.build.runtime.RootInvocationDeploymentInputsProducer")
                                ||type.startsWith("org.xar.ck3.control.build.runtime.RootInvocationDeploymentInputsProducer$"))))
                    throw new IOException("Test-only compilation contains an unrelated production override: "+type);
            }
        }
        var publication=new JavaUtf8Invocation.Publication(JavaUtf8Invocation.captureFile(Path.of(proof.physicalArguments().get(proof.physicalArguments().size()-4))));
        var launch=JavaUtf8Invocation.launch(publication,carrier,proof.startupOptions());
        if(!launch.physicalArguments().equals(proof.physicalArguments()))throw new IOException("Actual persistent main physical arguments drifted");
        var nativeProof=JavaUtf8NativeCustody.decodeEvidence(readOriginalBytes(proof.nativeEvidence(),JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES));
        if(!nativeProof.terminal().equals(terminal)||!nativeProof.terminal().passed())throw new IOException("Original JUnit terminal/native identity mismatch");
        JavaUtf8NativeCustody.requireCurrent(nativeProof,launch,carrier);
        var prepared=JavaUtf8Invocation.captureFile(JavaUtf8Invocation.preparationPath(logical));
        JavaUtf8Invocation.inspectPreparation(prepared,publication);
        proof.stdout().verify();proof.stderr().verify();
        String marker=expected==Stage.PERSON10_ACTUAL?"PASS_PERSON10_ACTUAL_JUNIT_1":"PASS_ROOT_INVOCATION_ACTUAL_JUNIT_2";
        if(proof.stdout().bytes()>(1L<<20)||!Files.readString(Path.of(proof.stdout().path()),java.nio.charset.StandardCharsets.UTF_8).lines().anyMatch(marker::equals))
            throw new IOException("Real JUnit found/started/succeeded count marker missing");
        if(expected==Stage.PERSON10_ACTUAL) {
            var actual=Person10NativeCorpusBuild.readProduced(proof.data().getFirst());
            if(!actual.requestRef().equals(proof.data().get(1))||!actual.corpusManifest().equals(proof.data().get(2)))
                throw new IOException("Actual whole native corpus binding changed");
            var original=Person10NativeCorpusBuild.readRequest(actual.requestRef());
            if(!original.producerRuntimeBuild().equals(toolsRef))throw new IOException("Native corpus uses another qualified tools build");
        } else {
            if(proof.data().size()!=3)throw new IOException("Complete original Root input/manifest/invocation evidence required");
            var original=decodeRootInvocationInputsPlan(Files.readAllBytes(Path.of(proof.data().getFirst().path())));
            if(!original.packageManifest().equals(proof.data().get(1))||!original.invocation().equals(proof.data().get(2)))
                throw new IOException("Genuine package/invocation binding changed");
            var manifest=org.xar.ck3.control.build.runtime.JavaRuntimePackageCodec.readManifest(original.packageManifest());
            if(!manifest.request().serviceBuildActual().equals(reactorRef))throw new IOException("Actual imported package crossed the accepted reactor");
            var allowed=manifest.outputFiles().stream().filter(row->row.relativePath().endsWith(".jar")).map(row->row.original()).toList();
            for(var role:original.productionJars()) {
                role.source().verify();
                if(!allowed.contains(role.source())||target.classpath().stream().noneMatch(pin->pin.path().equals(role.source().path())))
                    throw new IOException("All three original production source JAR roles must be in this actual child's classpath");
            }
        }
        reference.verify();return proof;
    }

    private static byte[] readOriginalBytes(ControlBuild.FileRef reference,int maximum)throws IOException {
        if(reference.bytes()<1||reference.bytes()>maximum)throw new IOException("Finite exact binary original required");
        reference.verify();byte[] bytes=Files.readAllBytes(Path.of(reference.path()));reference.verify();
        if(bytes.length!=reference.bytes())throw new IOException("Original binary input changed");return bytes;
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
            case G2_FULL_PARITY_20261024_R3, G2_FULL_PARITY_20261024_R4, G2_FULL_PARITY_20261024_R5, G2_FULL_PARITY_20261024_R6, G2_FULL_PARITY_20261025_R7 -> ReactorTestClosure.g2FullParityCurrentRequirements();
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
            if (profile.currentParity()
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
        if (!CiBootstrap.supportedPlanSchema(plan.schema()) || !plan.machineId().equals(WindowsJobProcess.currentMachineId())
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
            ControlBuild.FileRef fixtureProduction, ControlBuild.FileRef plannedFixtureProduction) throws IOException, InterruptedException {
        if (fixtureRequest != null || fixtureProduction != null || plannedFixtureProduction != null) {
            CiBootstrap.requireCompletePipeline(plan);
        }
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
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        environment.remove("JAVA_TOOL_OPTIONS"); environment.remove("JDK_JAVA_OPTIONS");
        environment.putAll(bindOracleEnvironment(plan, environment));
        if (plannedFixtureProduction != null) {
            var planned = readPlannedFixtureProductionRequest(plannedFixtureProduction, plan);
            bindCurrentOracleEnvironment(environment, planned.currentOracleInputsRef());
        }
        environment.put("XAR_MACHINE_ID", plan.machineId());
        for (String name : List.of("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")) environment.put(name, "1");
        environment.put("TEMP", root.resolve("scratch").toString()); environment.put("TMP", root.resolve("scratch").toString());
        JavaUtf8Invocation.OutputGuard guard = pending -> {
            timing.remainingWork(Instant.now());
            for (var pin : tools.completeDeployment()) pin.verify();
            ControlBuild.revalidateCiResources(plan, releasePath, pending);
        };
        QualifiedJavaLaunch prepared = qualifiedJavaLaunch(plan, planPath, toolsReceipt,
                Path.of(tools.deploymentRoot()).resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar"),
                fixtureRequest, fixtureProduction, plannedFixtureProduction, environment, currentJavaCarrier(), guard);
        var evidence = new QualifiedJavaEvidence(QUALIFIED_JAVA_SCHEMA, plan.machineId(),
                timing.workDeadline().toString(), prepared.command().arguments());
        Path evidencePath = root.resolve("logs/qualified-control-invocation.json");
        byte[] evidenceBytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(evidence);
        if (evidenceBytes.length > 65536) throw new IOException("Bounded qualified invocation evidence required");
        guard.require(evidenceBytes.length + 4096L);
        publish(evidencePath, evidence); var evidenceRef = ControlBuild.FileRef.measure(evidencePath);
        requireQualifiedJava(readQualifiedJavaEvidence(evidenceRef), prepared.carrier(),
                prepared.startupOptions(), plan.machineId(), timing.workDeadline(), prepared.launch().logicalRequest());
        Duration remaining = timing.remainingWork(Instant.now());
        runQualifiedChild(prepared, remaining, timing.workDeadline(),
                root.resolve("logs/control-ci-bootstrap-terminal.json"),
                root.resolve("logs/qualified-control-native-sources.json"), guard);
        requireQualifiedJava(readQualifiedJavaEvidence(evidenceRef), prepared.carrier(),
                prepared.startupOptions(), plan.machineId(), timing.workDeadline(), prepared.launch().logicalRequest());
        requireQualifiedPreparation(prepared);
    }

    /**
     * The original owned child and original Job terminal remain authoritative.
     * Native custody supplies source continuity; it does not turn an unsuccessful
     * child into a successful pipeline or create a second process owner.
     */
    static ControlBuild.FileRef runQualifiedChild(QualifiedJavaLaunch original, Duration remaining,
            Instant deadline, Path terminalPath, Path nativeEvidencePath,
            JavaUtf8Invocation.OutputGuard originalGuard) throws IOException, InterruptedException {
        try (var held = JavaUtf8NativeCustody.acquire(original.launch(), original.carrier())) {
            long quotedEvidence = held.maximumEvidenceBytes(original.command().executable());
            originalGuard.require(Math.addExact(quotedEvidence, 8192L));
            held.requireCurrent();
            try (var child = WindowsJobProcess.start(original.command())) {
                held.attach(child);
                var result = child.await(remaining, deadline, held.guard(() -> {
                    try { originalGuard.require(0); }
                    catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
                }));
                IOException failure = result.passed() ? null
                        : new IOException("Qualified Java pipeline did not exit cleanly: " + result);
                // Publish the original terminal before interpreting source custody or preparation.
                try { publish(terminalPath, result); }
                catch (IOException publication) {
                    if (failure == null) failure = publication; else failure.addSuppressed(publication);
                }
                ControlBuild.FileRef evidence = null;
                try {
                    var settled = held.verifyTerminal(result);
                    byte[] bytes = JavaUtf8NativeCustody.encodeEvidence(settled.evidence());
                    if (bytes.length > quotedEvidence) throw new IOException("Actual native source evidence exceeded its original quote");
                    originalGuard.require(Math.addExact(bytes.length, 4096L));
                    Files.write(nativeEvidencePath, bytes, StandardOpenOption.CREATE_NEW);
                    evidence = ControlBuild.FileRef.measure(nativeEvidencePath);
                    var cold = readQualifiedNativeEvidence(evidence, original);
                    if (!cold.equals(settled.evidence()) || !cold.terminal().equals(result))
                        throw new IOException("Persisted source continuity differs from this original Job terminal");
                } catch (IOException custody) {
                    if (failure == null) failure = custody; else failure.addSuppressed(custody);
                } catch (RuntimeException custody) {
                    if (failure == null) throw custody; else failure.addSuppressed(custody);
                }
                if (failure != null) throw failure;
                return java.util.Objects.requireNonNull(evidence);
            }
        }
    }

    /** Parsed evidence is DATA; only the held lifecycle above consumes an actual owned Job. */
    static JavaUtf8NativeCustody.Evidence readQualifiedNativeEvidence(ControlBuild.FileRef original,
            QualifiedJavaLaunch launch) throws IOException {
        if (original.bytes() < 1 || original.bytes() > JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES)
            throw new IOException("Bounded original native source evidence required");
        var witness = SharedSourceFiles.observe(Path.of(original.path()));
        if (!witness.source().equals(original)) throw new IOException("Actual native evidence pin differs");
        SharedSourceFiles.assertUnchanged(witness);
        byte[] bytes;
        try (var input = Files.newInputStream(Path.of(original.path()))) {
            bytes = input.readNBytes(JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES + 1);
        }
        if (bytes.length != original.bytes()) throw new IOException("Actual native evidence length differs");
        var evidence = JavaUtf8NativeCustody.decodeEvidence(bytes);
        JavaUtf8NativeCustody.requireCurrent(evidence, launch.launch(), launch.carrier());
        SharedSourceFiles.assertUnchanged(witness);
        return evidence;
    }

    /** Invocation DATA, not a tools/build qualification. The original writer/resource guard remains mandatory. */
    record QualifiedJavaLaunch(WindowsJobProcess.CommandSpec command, JavaUtf8Invocation.Launch launch,
            JavaUtf8Invocation.ClassCarrier carrier, List<String> startupOptions) {
        QualifiedJavaLaunch { startupOptions = List.copyOf(startupOptions); }
    }
    record QualifiedJavaEvidence(String schema, String machineId, String deadlineUtc,
            List<String> physicalArguments) {
        QualifiedJavaEvidence {
            if (!QUALIFIED_JAVA_SCHEMA.equals(schema) || machineId == null || machineId.isBlank())
                throw new IllegalArgumentException("Exact qualified invocation evidence required");
            Instant.parse(deadlineUtc); physicalArguments = List.copyOf(physicalArguments);
        }
    }
    static QualifiedJavaLaunch qualifiedJavaLaunch(CiBootstrap.Plan plan, Path planPath, Path toolsReceipt,
            Path qualifiedJar, ControlBuild.FileRef completed, ControlBuild.FileRef production,
            Map<String, String> environment, JavaUtf8Invocation.ClassCarrier carrier,
            JavaUtf8Invocation.OutputGuard guard) throws IOException {
        return qualifiedJavaLaunch(plan, planPath, toolsReceipt, qualifiedJar, completed, production, null,
                environment, carrier, guard);
    }
    static QualifiedJavaLaunch qualifiedJavaLaunch(CiBootstrap.Plan plan, Path planPath, Path toolsReceipt,
            Path qualifiedJar, ControlBuild.FileRef completed, ControlBuild.FileRef production, ControlBuild.FileRef planned,
            Map<String, String> environment, JavaUtf8Invocation.ClassCarrier carrier,
            JavaUtf8Invocation.OutputGuard guard) throws IOException {
        Path root = Path.of(plan.workRoot());
        var logical = new ArrayList<>(List.of("--bootstrap-plan", planPath.toString(),
                "--qualified-tools-receipt", toolsReceipt.toString()));
        forwardFixtureRequests(logical, completed, production, planned);
        var origin = JavaUtf8Invocation.captureClasspath(qualifiedJar);
        var target = new JavaUtf8Invocation.ClassTarget(ControlCi.class.getName(), origin, List.of(origin));
        var output = JavaUtf8Invocation.captureOutputRoot(root.resolve("scratch"));
        var request = new JavaUtf8Invocation.Request(target, List.of(), logical, output);
        var publication = JavaUtf8Invocation.publish(request, output, "qualified-utf8.bin", guard);
        List<String> options = List.of("-Xms32m", "-Xmx128m", "-XX:MaxMetaspaceSize=96m",
                "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m",
                "-Djava.io.tmpdir=" + root.resolve("scratch"), "-Djna.tmpdir=" + root.resolve("scratch"));
        var launch = JavaUtf8Invocation.launch(publication, carrier, options);
        var command = new WindowsJobProcess.CommandSpec(Path.of(plan.javaHome()).resolve("bin/java.exe"),
                launch.physicalArguments(), Path.of(plan.repoRoot()), environment,
                root.resolve("logs/qualified-control.stdout.log"), root.resolve("logs/qualified-control.stderr.log"), 2L << 30);
        return new QualifiedJavaLaunch(command, launch, carrier, options);
    }
    static JavaUtf8Invocation.ClassCarrier currentJavaCarrier() throws IOException {
        try {
            Path origin = Path.of(CiBootstrap.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            for (Class<?> actual : List.of(ControlCi.class, ControlBuild.class))
                if (!origin.equals(Path.of(actual.getProtectionDomain().getCodeSource().getLocation().toURI())))
                    throw new IOException("CI carrier must use its same actual loaded tools origin");
            return new JavaUtf8Invocation.ClassCarrier(List.of(JavaUtf8Invocation.captureClasspath(origin)));
        } catch (java.net.URISyntaxException invalid) { throw new IOException("Actual CI carrier URI invalid", invalid); }
    }
    static Invocation requireQualifiedJava(QualifiedJavaEvidence evidence, JavaUtf8Invocation.ClassCarrier carrier,
            List<String> startupOptions, String machine, Instant deadline, JavaUtf8Invocation.Request expected) throws IOException {
        if (!evidence.machineId().equals(machine) || !evidence.deadlineUtc().equals(deadline.toString()))
            throw new IOException("Qualified invocation machine/deadline differs from its original plan");
        var logical = JavaUtf8Invocation.inspect(evidence.physicalArguments(), carrier, startupOptions);
        if (!logical.equals(expected)
                || !(logical.target() instanceof JavaUtf8Invocation.ClassTarget target)
                || !target.mainClass().equals(ControlCi.class.getName()) || !logical.properties().isEmpty())
            throw new IOException("Actual qualified invocation is not the original ControlCi target");
        return invocation(logical.arguments().toArray(String[]::new));
    }
    static QualifiedJavaEvidence readQualifiedJavaEvidence(ControlBuild.FileRef original) throws IOException {
        var witness = SharedSourceFiles.observe(Path.of(original.path()));
        if (!witness.source().equals(original)) throw new IOException("Actual invocation evidence pin differs");
        SharedSourceFiles.assertUnchanged(witness);
        var row = readPinned(original, com.fasterxml.jackson.databind.JsonNode.class, 65536);
        if (row == null || !row.isObject()) throw new IOException("Actual qualified invocation object required");
        for (String name : List.of("schema", "machine_id", "deadline_utc"))
            if (!row.path(name).isTextual()) throw new IOException("Exact qualified invocation text fields required");
        var args = row.get("physical_arguments");
        if (args == null || !args.isArray()) throw new IOException("Actual physical arguments array required");
        for (var value : args) if (!value.isTextual()) throw new IOException("Physical argv tokens must remain exact JSON strings");
        var result = ControlBuild.strictMapper().treeToValue(row, QualifiedJavaEvidence.class);
        SharedSourceFiles.assertUnchanged(witness);
        return result;
    }
    /** Actual same-JVM target preparation, additional to the unchanged required successful Job terminal. */
    static JavaUtf8Invocation.Preparation requireQualifiedPreparation(QualifiedJavaLaunch original) throws IOException {
        Path path = JavaUtf8Invocation.preparationPath(original.launch().logicalRequest());
        var witness = SharedSourceFiles.observe(path);
        SharedSourceFiles.assertUnchanged(witness);
        var preparedFile = JavaUtf8Invocation.captureFile(path);
        var prepared = JavaUtf8Invocation.inspectPreparation(preparedFile, original.launch().publication());
        SharedSourceFiles.assertUnchanged(witness);
        return prepared;
    }

    static void forwardFixtureRequests(List<String> arguments, ControlBuild.FileRef completed, ControlBuild.FileRef production) throws IOException {
        forwardFixtureRequests(arguments, completed, production, null);
    }

    /** Keep the explicit canonical oracle source distinct from the selected Java reactor source. */
    static Map<String, String> bindOracleEnvironment(CiBootstrap.Plan plan, Map<String, String> environment) throws IOException {
        return CiBootstrap.OracleEnvironment.bindSelectedInterpreter(Path.of(plan.pythonExecutable()), environment);
    }

    /** Forward the exact already validated selection before the qualified child's first environment read. */
    static void bindCurrentOracleEnvironment(Map<String, String> environment, ControlBuild.FileRef selected) throws IOException {
        selected.verify();
        environment.put("XAR_FULL_PARITY_CURRENT_INPUTS", selected.path());
        environment.put("XAR_FULL_PARITY_CURRENT_INPUTS_SHA256", selected.sha256());
    }

    static void requireOneFixtureRoute(ControlBuild.FileRef completed, ControlBuild.FileRef production, ControlBuild.FileRef planned) {
        if ((completed == null ? 0 : 1) + (production == null ? 0 : 1) + (planned == null ? 0 : 1) > 1)
            throw new IllegalArgumentException("One completed, production or planned fixture route required");
    }

    static void forwardFixtureRequests(List<String> arguments, ControlBuild.FileRef completed,
            ControlBuild.FileRef production, ControlBuild.FileRef planned) throws IOException {
        requireOneFixtureRoute(completed, production, planned);
        ControlBuild.FileRef selected = completed != null ? completed : production != null ? production : planned;
        if (selected == null) return;
        selected.verify();
        arguments.addAll(List.of(completed != null ? "--fixture-stage-request" : production != null
                        ? "--fixture-production-request" : "--planned-fixture-production-request",
                selected.path(), Long.toString(selected.bytes()), selected.sha256()));
    }

    private static void runQualified(Path planPath, CiBootstrap.Plan plan, Path toolsReceiptPath,
            ControlBuild.FileRef fixtureRequestRef, ControlBuild.FileRef suppliedFixtureProductionRef,
            ControlBuild.FileRef plannedFixtureProductionRef, LocalExecution local) throws IOException, InterruptedException {
        String started = Instant.now().toString(); Path root = Path.of(plan.workRoot());
        Path oracleRepository = Path.of(bindOracleEnvironment(plan, System.getenv()).get("XAR_ORACLE_REPO"));
        CiBootstrap.PipelineTiming timing = CiBootstrap.pipelineTiming(plan);
        Path releasePath = local == null ? root.resolve("logs/ci-capacity-release.json") : Path.of(local.card().capacityReleaseRef().path());
        ControlBuild.BuildReceipt tools = ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(toolsReceiptPath));
        if (tools.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME || !tools.completeDeployment().equals(ControlBuild.producerClosure())) {
            throw new IOException("Actual running qualified jar/lib must exactly equal the qualified build closure");
        }
        ControlBuild.FileRef planRef = ControlBuild.FileRef.measure(planPath), releaseRef = ControlBuild.FileRef.measure(releasePath), toolsRef = ControlBuild.FileRef.measure(toolsReceiptPath);
        ControlBuild.FileRef mechanicalRef = local == null ? ControlBuild.FileRef.measure(root.resolve("artifacts/tools-postqualification/actual.json")) : local.card().toolsPostqualificationRef();
        requireToolsPostqualification(mechanicalRef,toolsRef);
        requireOneFixtureRoute(fixtureRequestRef, suppliedFixtureProductionRef, plannedFixtureProductionRef);
        if (fixtureRequestRef != null || suppliedFixtureProductionRef != null || plannedFixtureProductionRef != null) {
            CiBootstrap.requireCompletePipeline(plan);
        }
        ControlBuild.FileRef fixtureProductionRef = suppliedFixtureProductionRef;
        String failure = null; ControlBuild.FileRef reactorRef = null, consumerRef = null, supplementalRef = null, reactorClosureRef = null;
        List<ControlBuild.FileRef> staticRefs = new ArrayList<>();
        List<StageActual> stages = initialStages(); Stage current = null; Path currentEvidence = null;
        MapAdmissionCi.Session retainedService = null;
        boolean managed=local!=null&&local.plan() instanceof RootManagedPlan;
        if(managed&&CiBootstrap.pipelineProfile(plan)!=CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE)
            throw new IOException("Only "+CiBootstrap.MANAGED_PLAN_SCHEMA+" resources may execute full actual qualification");
        ControlBuild.FileRef postRef=managed?local.plan().postqualificationPlanRef():null;
        PostqualificationPlan post=managed?readPostqualificationPlan(postRef,plan):null;
        boolean complete = false;
        try {
            if (local == null) {
                current = Stage.EXPECTED_MAVEN_RED; currentEvidence = root.resolve("logs/build-ci-expected-maven-red.json"); start(stages, current);
                ControlBuild.FileRef expectedMavenRef = requireExpectedMavenFailure(plan, releasePath); pass(stages, current, expectedMavenRef);
            } else readRootLocalExecution(local.planRef());
            if(managed) {
                current=Stage.PERSON10_ACTUAL;currentEvidence=root.resolve("artifacts/person10-actual/actual.json");start(stages,current);
                pass(stages,current,runPerson10Actual(plan,releasePath,postRef,post,toolsRef,tools));
            }
            current = Stage.REACTOR; currentEvidence = root.resolve("logs/build-ci-reactor.json"); start(stages, current);
            if (plannedFixtureProductionRef != null) {
                fixtureProductionRef = bindPlannedFixtureProduction(plannedFixtureProductionRef, toolsRef, plan,
                        root.resolve("artifacts/planned-fixture-production"), pending -> {
                            timing.remainingWork(Instant.now()); plannedFixtureProductionRef.verify(); toolsRef.verify();
                            ControlBuild.revalidateCiResources(plan, releasePath, pending);
                        });
            }
            requireFullParityFixtureProduction(local == null ? reactorSourceProfile(plan)
                    : local.card().sourceLimitProfile(), fixtureProductionRef);
            Path reactorPath = local == null ? root.resolve("logs/build-ci-reactor.json") : Path.of(local.card().reactorBuildReceiptRef().path());
            ControlBuild.BuildReceipt reactor = local == null ? ControlBuild.build(config(plan, Path.of(plan.repoRoot()).resolve("java/ck3-control"),
                    releasePath, "ci-reactor", ControlBuild.TargetKind.SERVICE_FAST_JAR)) : ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(reactorPath));
            reactorRef = ControlBuild.FileRef.measure(reactorPath);
            if (!reactor.status().equals("PASS")) throw new IOException("Complete reactor failed");
            requireCurrentFixtureExecution(reactor, fixtureProductionRef);
            pass(stages, current, reactorRef);
            if(managed) {
                current=Stage.ROOT_INVOCATION_ACTUAL;currentEvidence=root.resolve("artifacts/root-invocation-actual/actual.json");start(stages,current);
                pass(stages,current,runRootInvocationActual(plan,releasePath,planRef,postRef,post,toolsRef,tools,reactorRef,reactor));
            }
            current = Stage.REACTOR_TEST_CLOSURE; currentEvidence = root.resolve("logs/reactor-test-closure.json"); start(stages, current);
            var requirements = httpRequirements(reactor.sourceLimitProfile());
            reactorClosureRef = ReactorTestClosure.run(reactorPath, currentEvidence, requirements);
            if (!reactorClosureRef.equals(ReactorTestClosure.requireAccepted(currentEvidence, reactorPath, requirements))) throw new IOException("Reactor report closure changed before pipeline adoption");
            pass(stages, current, reactorClosureRef);
            current = Stage.MAP_CONSUMERS; currentEvidence = root.resolve("artifacts/map-ci/logs/actual.json"); start(stages, current);
            var mapConfig = new MapAdmissionCi.Config(oracleRepository, reactorPath, root.resolve("artifacts/map-ci"),
                    Path.of(plan.javaHome()).resolve("bin/java.exe"), Path.of(plan.pythonExecutable()), timing.workDeadline(), 8089,
                    CiBootstrap.pipelineProfile(plan));
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
                        oracleRepository, pythonStaticRoot(root, kind), Path.of(plan.pythonExecutable()),
                        root.resolve("scratch"), timing.workDeadline(), plan.machineId()));
                staticRefs.add(ref); pass(stages, current, ref);
            }
            requirePythonStaticReceipts(root);
            current = Stage.SUPPLEMENTAL; currentEvidence = root.resolve("artifacts/supplemental-fixtures/actual.json"); start(stages, current);
            supplementalRef = SupplementalFixtureCi.run(new SupplementalFixtureCi.Config(oracleRepository,
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
                final ControlBuild.FileRef selectedProductionRef = fixtureProductionRef;
                final MapAdmissionCi.Session sameHost = retainedService;
                FreshSdkFixtureStage.ResourceGuard guard = pending -> {
                    timing.remainingWork(Instant.now());
                    selectedRequestRef.verify();
                    if (selectedProductionRef != null) selectedProductionRef.verify();
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
            PipelineState result=complete&&failure==null?PipelineState.PASS:PipelineState.RED;
            if(managed) publishPipeline(root.resolve("logs/control-ci-actual.json"),new Receipt(ACTUAL_SCHEMA,plan.machineId(),started,Instant.now().toString(),
                    result,failure,planRef,releaseRef,toolsRef,null,reactorRef,consumerRef,List.copyOf(staticRefs),supplementalRef,
                    reactorClosureRef,fixtureRequestRef,fixtureProductionRef,ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE,local.planRef(),postRef,stages,mechanicalRef),root);
            else {
                publishPipeline(root.resolve("logs/control-ci-software-actual.json"),new SoftwareReceipt(QualificationScope.SOFTWARE_ONLY_NOT_POSTQUALIFIED,
                        SOFTWARE_SCHEMA,plan.machineId(),started,Instant.now().toString(),result,failure,planRef,releaseRef,toolsRef,null,
                        reactorRef,consumerRef,List.copyOf(staticRefs),supplementalRef,reactorClosureRef,fixtureRequestRef,fixtureProductionRef,
                        local==null?ExecutionPurpose.HOSTED_CI:ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE,local==null?null:local.planRef(),
                        softwareStages(stages),notExecutedActualStages(),mechanicalRef),root);
                System.out.println("SOFTWARE_ONLY_NOT_POSTQUALIFIED: PERSON10_ACTUAL NOT_EXECUTED; ROOT_INVOCATION_ACTUAL NOT_EXECUTED; FULL_CI_NOT_QUALIFIED");
            }

        }
        if (!complete || failure != null) throw new IOException(failure);
    }

    /** Execute the original failing producer path, not just the source-postcheck helper. */
    private static ControlBuild.FileRef requireExpectedMavenFailure(CiBootstrap.Plan plan, Path release) throws IOException, InterruptedException {
        Path fixture = Path.of(plan.repoRoot()).resolve("java/ck3-control/build-tools/src/test/resources/maven-failure");
        ControlBuild.BuildReceipt actual = ControlBuild.build(config(plan, fixture, release, "ci-expected-maven-red", ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, 900));
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
    static PlannedFixtureProductionRequest decodePlannedFixtureProductionRequest(byte[] bytes) throws IOException {
        if (bytes == null || bytes.length < 1 || bytes.length > MAX_CONFIG_BYTES)
            throw new IOException("Bounded planned fixture production request required");
        return ControlBuild.strictMapper().readValue(bytes, PlannedFixtureProductionRequest.class);
    }

    private static SdkStageConfigurationProducer.ProductionPlan verifyPlannedFixtureInputs(PlannedFixtureProductionRequest request) throws IOException {
        var sdk = SdkStageConfigurationProducer.readPlan(request.sdkProductionPlanRef());
        if (!request.machineId().equals(WindowsJobProcess.currentMachineId()) || !request.machineId().equals(sdk.machineId())
                || !request.reviewAtUtc().equals(sdk.reviewAtUtc()) || !Instant.now().isBefore(Instant.parse(request.reviewAtUtc())))
            throw new IOException("One current source-bound SDK plan and software fixture required");
        for (var input : SdkStageConfigurationProducer.planInputRefs(sdk)) input.verify();
        for (var input : request.softwareFixture().originalFixtureRefs()) input.verify();
        for (var input : request.softwareFixture().originalRequestRefs()) input.verify();
        request.softwareFixture().probeRequestRef().verify(); request.softwareFixture().probePayloadRef().verify();
        var current = FullParityCurrentBindings.readInputs(request.currentOracleInputsRef()); FullParityCurrentBindings.verify(current);
        if (!current.machineId().equals(request.machineId()) || !current.pythonRef().equals(sdk.interpreter().pythonExecutable()))
            throw new IOException("SDK source plan and all current inputs must use the same actual interpreter and machine");
        return sdk;
    }

    public static ControlBuild.FileRef writePlannedFixtureProductionRequest(PlannedFixtureProductionRequest request, Path destination) throws IOException {
        verifyPlannedFixtureInputs(request);
        Path output = destination.toAbsolutePath().normalize(); SharedSourceFiles.plainAncestors(output);
        ProjectStoragePolicy.requireBulkOutput(output.getParent()); publish(output, request);
        var actual = ControlBuild.FileRef.measure(output);
        var decoded = decodePlannedFixtureProductionRequest(Files.readAllBytes(output));
        if (!decoded.equals(request)) throw new IOException("Planned fixture production request roundtrip differs");
        verifyPlannedFixtureInputs(decoded); actual.verify(); return actual;
    }

    static PlannedFixtureProductionRequest readPlannedFixtureProductionRequest(ControlBuild.FileRef ref, CiBootstrap.Plan plan) throws IOException {
        var request = readPinned(ref, PlannedFixtureProductionRequest.class, MAX_CONFIG_BYTES);
        var sdk = verifyPlannedFixtureInputs(request);
        if (!request.machineId().equals(plan.machineId())
                || Instant.parse(request.reviewAtUtc()).isAfter(CiBootstrap.pipelineTiming(plan).workDeadline())
                || !sdk.interpreter().pythonExecutable().equals(ControlBuild.FileRef.measure(Path.of(plan.pythonExecutable()))))
            throw new IOException("Planned fixture must use this pipeline machine, interpreter and work deadline");
        ref.verify(); return request;
    }

    /** The qualified child has already checked its loaded archive against the actual completed build. */
    static ControlBuild.FileRef bindPlannedFixtureProduction(ControlBuild.FileRef plannedRef, ControlBuild.FileRef toolsRef,
            CiBootstrap.Plan plan, Path freshOutputRoot, FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        var request = readPlannedFixtureProductionRequest(plannedRef, plan);
        guard.revalidate(4096); plannedRef.verify(); toolsRef.verify();
        Path output = freshOutputRoot.toAbsolutePath().normalize(); SharedSourceFiles.plainAncestors(output);
        ProjectStoragePolicy.requireBulkOutput(output); Files.createDirectory(output);
        var sdkRef = SdkStageConfigurationProducer.bindAndWriteInputs(request.sdkProductionPlanRef(), toolsRef,
                output.resolve("sdk-production-inputs.json"), guard);
        var production = new CurrentFixtureProductionRequest(CURRENT_FIXTURE_PRODUCTION_SCHEMA, request.machineId(), request.reviewAtUtc(),
                sdkRef, request.softwareFixture(), request.currentOracleInputsRef());
        verifyProductionInputs(production); guard.revalidate(0);
        Path productionPath = output.resolve("fixture-production-request.json"); publishPlannedBindingDocument(productionPath, production, guard);
        var productionRef = ControlBuild.FileRef.measure(productionPath);
        if (!readFixtureProductionRequest(productionRef, plan).equals(production)) throw new IOException("Bound fixture production request roundtrip differs");
        var binding = new PlannedFixtureBinding("xar.java-control-CI-planned-fixture-binding/v1", request.machineId(), plannedRef, toolsRef, sdkRef, productionRef);
        Path bindingPath = output.resolve("binding.json"); publishPlannedBindingDocument(bindingPath, binding, guard);
        if (!readPinned(ControlBuild.FileRef.measure(bindingPath), PlannedFixtureBinding.class, MAX_CONFIG_BYTES).equals(binding))
            throw new IOException("Actual planned fixture binding roundtrip differs");
        verifyPlannedFixtureInputs(request);
        guard.revalidate(0); plannedRef.verify(); toolsRef.verify(); sdkRef.verify(); productionRef.verify(); return productionRef;
    }

    private static void publishPlannedBindingDocument(Path destination, Record value, FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        byte[] bytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value);
        if (bytes.length < 1 || bytes.length > MAX_CONFIG_BYTES) throw new IOException("Bounded planned fixture binding metadata required");
        guard.revalidate(Math.addExact(bytes.length, 4096L));
        Files.write(destination, bytes, StandardOpenOption.CREATE_NEW); guard.revalidate(0);
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
        if (!reactor.sourceLimitProfile().currentParity()) return;
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

    static SdkSourceAssembly.SharedCapacityGate sdkCapacityGate(CiBootstrap.Plan plan, Path release,
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
                long usable = store.getUsableSpace(), unit = NativeStorageGeometry.read(group).clusterBytes();
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
        CanonicalOracleEnvironment.bind(Path.of(fresh.canonicalRepository()), Path.of(plan.pythonExecutable()), Map.of());
        FreshSdkFixtureStage.ProducerGoldenSources golden = FreshSdkFixtureStage.readProducerGoldenSources(fresh.producerGoldenPlanRef());
        RootSoftwareChildBootstrap.Configuration bootstrap = RootSoftwareChildBootstrap.readConfiguration(fresh.rootBootstrapRef());
        var client = bootstrap.client().source();
        FreshSdkFixtureStage.requireDeclaredProducerMachine(golden, plan.machineId());
        if (!bootstrap.machineId().equals(plan.machineId()))
            throw new IOException("Root bootstrap machine differs from the actual pipeline");
        FreshSdkFixtureStage.requireDeclaredProducerCohort(golden,
                new SdkSourceAssembly.Digest(client.bytes(), client.sha256()), java.util.Optional.empty());
        for (ControlBuild.FileRef input : FreshSdkFixtureStage.producerGoldenInputs(golden)) input.verify();
        for (ControlBuild.FileRef input : RootSoftwareChildBootstrap.inputRefs(bootstrap)) input.verify();
        fresh.pythonExecutable().verify(); fresh.rootBootstrapRef().verify();
        Path artifacts = Path.of(plan.workRoot()).resolve("artifacts").toRealPath();
        if (!fresh.machineId().equals(plan.machineId()) || !canonical.machineId().equals(plan.machineId())
                || !Path.of(fresh.canonicalRepository()).toRealPath().equals(Path.of(canonical.repository()).toRealPath())
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

    static ControlBuild.SourceLimitProfile reactorSourceProfile(CiBootstrap.Plan plan) {
        return CiBootstrap.completeProfile(CiBootstrap.pipelineProfile(plan))
                ? ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261025_R7
                : ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R6;
    }

    private static ControlBuild.Config config(CiBootstrap.Plan plan, Path source, Path release, String attempt, ControlBuild.TargetKind target) {
        return config(plan,source,release,attempt,target,ControlBuild.maximumBuildTimeoutSeconds(target));
    }
    private static ControlBuild.Config config(CiBootstrap.Plan plan,Path source,Path release,String attempt,
            ControlBuild.TargetKind target,int timeoutSeconds) {
        int maximum=ControlBuild.maximumBuildTimeoutSeconds(target);
        if(timeoutSeconds<1||timeoutSeconds>maximum)throw new IllegalArgumentException("Bounded selected build stage timeout required");
        return new ControlBuild.Config(source, Path.of(plan.workRoot()), release, attempt, plan.ownerTask(), null,
                Path.of(plan.javaHome()), CiBootstrap.MINIMUM_MAVEN_VERSION, timeoutSeconds, target,
                source.equals(Path.of(plan.repoRoot()).resolve("java/ck3-control"))
                        ? reactorSourceProfile(plan)
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

    private static StageActual stageEvidence(PipelineEvidence actual,Stage stage)throws IOException {
        var values=actual.stages().stream().filter(value->value.stage()==stage).toList();
        if(values.size()!=1)throw new IOException("One exact actual stage required: "+stage);return values.getFirst();
    }
    private static void requireCompletedPythonStaticPipeline(Path root)throws IOException {
        Path path=root.resolve("logs/control-ci-actual.json");
        var actual=readPinned(ControlBuild.FileRef.measure(path),Receipt.class,65536);
        requirePipelineEvidence(root,actual,path);
        requireManagedEvidence(actual);
        System.out.println("ACCEPTED_CONTROL_CI_V8_MANAGED_ALL_11 "+ControlBuild.FileRef.measure(path));
    }
    private static void requireManagedEvidence(Receipt actual)throws IOException {
        var resources=readPinned(actual.planRef(),CiBootstrap.Plan.class,MAX_CONFIG_BYTES);
        if(CiBootstrap.pipelineProfile(resources)!=CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE
                ||actual.purpose()!=ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE)
            throw new IOException("Full actual qualification requires its distinct "+CiBootstrap.MANAGED_PLAN_SCHEMA+" contract");
        var local=readRootLocalExecution(actual.rootLocalPlanRef());
        if(!(local.plan() instanceof RootManagedPlan)||!local.plan().postqualificationPlanRef().equals(actual.postqualificationPlanRef()))
            throw new IOException("Full actual receipt lost the same originally issued postqualification inputs");
        requireIntegrationActual(stageEvidence(actual,Stage.PERSON10_ACTUAL).evidenceRef(),Stage.PERSON10_ACTUAL,resources,
                actual.postqualificationPlanRef(),actual.toolsBuildReceiptRef(),null);
        requireIntegrationActual(stageEvidence(actual,Stage.ROOT_INVOCATION_ACTUAL).evidenceRef(),Stage.ROOT_INVOCATION_ACTUAL,resources,
                actual.postqualificationPlanRef(),actual.toolsBuildReceiptRef(),actual.reactorBuildReceiptRef());
    }
    private static void requireCompletedSoftwarePipeline(Path root)throws IOException {
        Path path=root.resolve("logs/control-ci-software-actual.json");
        var actual=readPinned(ControlBuild.FileRef.measure(path),SoftwareReceipt.class,65536);
        requirePipelineEvidence(root,actual,path);
        System.out.println("ACCEPTED_SOFTWARE_ONLY: PERSON10_ACTUAL NOT_EXECUTED; ROOT_INVOCATION_ACTUAL NOT_EXECUTED; FULL_CI_NOT_QUALIFIED");
    }

    private static void requirePipelineEvidence(Path root,PipelineEvidence actual,Path path)throws IOException {
        List<ControlBuild.FileRef> refs = requirePythonStaticReceipts(root);
        if (!actual.machineId().equals(WindowsJobProcess.currentMachineId()) || actual.status() != PipelineState.PASS
                || actual.error() != null || !actual.pythonStaticReceiptRefs().equals(refs)
                || actual.planRef() == null || actual.capacityReleaseRef() == null || actual.toolsBuildReceiptRef() == null
                || actual.reactorBuildReceiptRef() == null || actual.consumerReceiptRef() == null || actual.supplementalFixtureReceiptRef() == null
                || actual.reactorTestClosureReceiptRef() == null) {
            throw new IOException("Complete emitted software/full evidence must bind all requested stage outcomes and actual reactor report closure");
        }
        actual.planRef().verify(); actual.capacityReleaseRef().verify(); actual.toolsBuildReceiptRef().verify();
        if(actual.toolsPostqualificationRef()==null)throw new IOException("Missing real complete-Own plus two-JUnit proof");
        requireToolsPostqualification(actual.toolsPostqualificationRef(),actual.toolsBuildReceiptRef());
        actual.reactorBuildReceiptRef().verify(); actual.consumerReceiptRef().verify();
        ControlBuild.FileRef supplemental = SupplementalFixtureCi.requireAccepted(root.resolve("artifacts/supplemental-fixtures/actual.json"), WindowsJobProcess.currentMachineId());
        if (!supplemental.equals(actual.supplementalFixtureReceiptRef())) throw new IOException("Completed CI must bind the exact accepted supplemental receipt");
        var reactor = ControlBuild.verifiedCompletedReceipt(actual.reactorBuildReceiptRef());
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
                    ||!local.card().toolsPostqualificationRef().equals(actual.toolsPostqualificationRef())
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
            StageActual fresh = stageEvidence(actual,Stage.FRESH_SDK), canonical = stageEvidence(actual,Stage.CANONICAL_THIRTY);
            if (!Path.of(fresh.evidenceRef().path()).toRealPath().equals(Path.of(freshConfig.workRoot()).resolve("actual.json").toRealPath())
                    || !Path.of(canonical.evidenceRef().path()).toRealPath().equals(Path.of(canonicalConfig.workRoot()).resolve("actual.json").toRealPath())) throw new IOException("Requested fixture output ownership differs");
            if (!FreshSdkFixtureStage.requireAccepted(Path.of(fresh.evidenceRef().path()), guard).equals(fresh.evidenceRef())
                    || !CanonicalColdWarmStage.requireAccepted(Path.of(canonical.evidenceRef().path()), guard).equals(canonical.evidenceRef())) throw new IOException("Exact accepted fixture stage actuals required");
            request.freshSdkConfigRef().verify(); request.canonicalConfigRef().verify();
        }

    }
    private static void requireStageRef(PipelineEvidence actual, Stage stage, ControlBuild.FileRef expected) throws IOException {
        if (!expected.equals(stageEvidence(actual,stage).evidenceRef())) throw new IOException("Actual stage evidence binding differs: " + stage);
    }

    private static void publishPipeline(Path path,PipelineEvidence actual,Path root)throws IOException {
        if(actual.status()==PipelineState.PASS)try {
            requirePipelineEvidence(root,actual,path);
            if(actual instanceof Receipt managed)requireManagedEvidence(managed);
        } catch(IOException|RuntimeException invalid) {
            if(actual instanceof Receipt)publish(path,new Receipt(actual.schema(),actual.machineId(),actual.startedAtUtc(),actual.observedAtUtc(),PipelineState.RED,append(actual.error(),"Final actual source/evidence adoption failed: "+invalid.getMessage()),actual.planRef(),actual.capacityReleaseRef(),actual.toolsBuildReceiptRef(),actual.qualifiedPipeline(),actual.reactorBuildReceiptRef(),actual.consumerReceiptRef(),actual.pythonStaticReceiptRefs(),actual.supplementalFixtureReceiptRef(),actual.reactorTestClosureReceiptRef(),actual.fixtureRequestRef(),actual.fixtureProductionRequestRef(),actual.purpose(),actual.rootLocalPlanRef(),((Receipt)actual).postqualificationPlanRef(),actual.stages(),actual.toolsPostqualificationRef()));
            else publish(path,new SoftwareReceipt(QualificationScope.SOFTWARE_ONLY_NOT_POSTQUALIFIED,actual.schema(),actual.machineId(),actual.startedAtUtc(),actual.observedAtUtc(),PipelineState.RED,append(actual.error(),"Final actual source/evidence adoption failed: "+invalid.getMessage()),actual.planRef(),actual.capacityReleaseRef(),actual.toolsBuildReceiptRef(),actual.qualifiedPipeline(),actual.reactorBuildReceiptRef(),actual.consumerReceiptRef(),actual.pythonStaticReceiptRefs(),actual.supplementalFixtureReceiptRef(),actual.reactorTestClosureReceiptRef(),actual.fixtureRequestRef(),actual.fixtureProductionRequestRef(),actual.purpose(),actual.rootLocalPlanRef(),actual.stages(),((SoftwareReceipt)actual).postqualificationStages(),actual.toolsPostqualificationRef()));
            throw new IOException("Final actual evidence could not be adopted",invalid);
        }
        publish(path,(Record)actual);
    }

    private static void publish(Path path, Record value) throws IOException {
        try { Files.write(path, ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value), StandardOpenOption.CREATE_NEW); }
        catch (IOException unavailable) {
            if (value instanceof Receipt actual) {
                Receipt red = new Receipt(actual.schema(), actual.machineId(), actual.startedAtUtc(), actual.observedAtUtc(), PipelineState.RED,
                        append(actual.error(), "CI actual publication unavailable: " + unavailable.getMessage()), actual.planRef(), actual.capacityReleaseRef(),
                        actual.toolsBuildReceiptRef(), actual.qualifiedPipeline(), actual.reactorBuildReceiptRef(), actual.consumerReceiptRef(),
                        actual.pythonStaticReceiptRefs(), actual.supplementalFixtureReceiptRef(), actual.reactorTestClosureReceiptRef(), actual.fixtureRequestRef(), actual.fixtureProductionRequestRef(), actual.purpose(), actual.rootLocalPlanRef(), actual.postqualificationPlanRef(), actual.stages(), actual.toolsPostqualificationRef());
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
