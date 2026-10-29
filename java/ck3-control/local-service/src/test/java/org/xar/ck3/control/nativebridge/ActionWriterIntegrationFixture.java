package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.*;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;

/** Controlled packet/process/source edges exercise the actual collector, guards, writer and physical archive. */
public final class ActionWriterIntegrationFixture implements AutoCloseable {
    /** Software packet edge only. A profile string never qualifies a loaded native module or a live Game. */
    public record SoftwareReadScenario(String profileSha256, String adapterId,
            java.util.function.Function<ExactRef, List<ReadContract<?>>> contracts,
            java.util.function.Function<NativeRequest, RawJson> result, Optional<String> expectedCk3Version, Set<String> extraHelloCapabilities,
            java.util.function.Function<ExactRef,List<RootReadContractCatalog.Family<?,?>>> dynamicFamilies) {
        public SoftwareReadScenario(String profileSha256,String adapterId,java.util.function.Function<ExactRef,List<ReadContract<?>>> contracts,
                java.util.function.Function<NativeRequest,RawJson> result,Optional<String> expectedCk3Version,Set<String> extraHelloCapabilities) {
            this(profileSha256,adapterId,contracts,result,expectedCk3Version,extraHelloCapabilities,ignored->List.of());
        }
        public SoftwareReadScenario(String profileSha256, String adapterId,
                java.util.function.Function<ExactRef, List<ReadContract<?>>> contracts, java.util.function.Function<NativeRequest, RawJson> result) {
            this(profileSha256, adapterId, contracts, result, Optional.empty(), Set.of());
        }
        public SoftwareReadScenario {
            StrictJson.require(profileSha256 != null && profileSha256.matches("[0-9a-f]{64}"), "software profile SHA256 required");
            StrictJson.require(adapterId != null && adapterId.matches("[A-Za-z0-9._-]{1,128}"), "software adapter token required");
            java.util.Objects.requireNonNull(contracts); java.util.Objects.requireNonNull(result);
            java.util.Objects.requireNonNull(dynamicFamilies);
            expectedCk3Version = java.util.Objects.requireNonNull(expectedCk3Version);
            expectedCk3Version.ifPresent(StrictJson::text);
            extraHelloCapabilities = Set.copyOf(extraHelloCapabilities); extraHelloCapabilities.forEach(StrictJson::text);
            StrictJson.require(extraHelloCapabilities.size() <= 32, "bounded explicit software HELLO capabilities required");
        }
    }
    @FunctionalInterface public interface SoftwareDispatch { void run() throws IOException; }
    public record SoftwareActionScenario(OperationKey operation, String requiredCapability,
            ActionPorts.PostconditionPort postcondition, SoftwareDispatch originalDispatch,
            Optional<java.util.function.Supplier<RawJson>> originalResult,
            Optional<java.util.function.Function<ExactRef, NativePrivateActionPermission>> privatePermission, boolean initializeBaseline,
            Optional<ActionPorts.PreparationPort> originalPreparation) {
        public SoftwareActionScenario(OperationKey operation, String requiredCapability, ActionPorts.PostconditionPort postcondition,
                SoftwareDispatch originalDispatch, Optional<java.util.function.Supplier<RawJson>> originalResult,
                Optional<java.util.function.Function<ExactRef, NativePrivateActionPermission>> privatePermission, boolean initializeBaseline) {
            this(operation, requiredCapability, postcondition, originalDispatch, originalResult, privatePermission, initializeBaseline, Optional.empty());
        }
        public SoftwareActionScenario(OperationKey operation, String requiredCapability, ActionPorts.PostconditionPort postcondition, SoftwareDispatch originalDispatch) {
            this(operation, requiredCapability, postcondition, originalDispatch, Optional.empty(), Optional.empty(), false);
        }
        public SoftwareActionScenario(OperationKey operation, String requiredCapability, ActionPorts.PostconditionPort postcondition,
                SoftwareDispatch originalDispatch, java.util.function.Supplier<RawJson> originalResult) {
            this(operation, requiredCapability, postcondition, originalDispatch, Optional.of(java.util.Objects.requireNonNull(originalResult)), Optional.empty(), false);
        }
        public SoftwareActionScenario {
            java.util.Objects.requireNonNull(operation); StrictJson.text(requiredCapability);
            java.util.Objects.requireNonNull(postcondition); java.util.Objects.requireNonNull(originalDispatch);
            originalResult = java.util.Objects.requireNonNull(originalResult); privatePermission = java.util.Objects.requireNonNull(privatePermission);
            originalPreparation = java.util.Objects.requireNonNull(originalPreparation);
        }
    }
    /** Constructor-time graph inputs only; the actual handler and replay must both be installed before any event. */
    public record SoftwareCompositeContext(ContinuityWriter writer,ContinuityActionJournal journal,NativeOutcomeArchive archive,
            NativeReadinessCollector collector,NativeEffectEvidence.FrameLoader frames,G2Source source,Set<String> bridgeCapabilities) {
        public SoftwareCompositeContext {bridgeCapabilities=Set.copyOf(bridgeCapabilities);}
    }
    public record SoftwareCompositeInstallation(CompositeActionPort handler,List<NativeRecordedEvidenceVerifier.Binding> archived) {
        public SoftwareCompositeInstallation {java.util.Objects.requireNonNull(handler);archived=List.copyOf(archived);}
    }
    public record SoftwareCompositeScenario(String handlerId,Set<OperationKey> operations,ReadContract.GuardMode guardMode,
            Optional<String> requiredCapability,java.util.function.Function<SoftwareCompositeContext,SoftwareCompositeInstallation> install) {
        public SoftwareCompositeScenario {
            StrictJson.text(handlerId);operations=Set.copyOf(operations);java.util.Objects.requireNonNull(guardMode);
            requiredCapability=java.util.Objects.requireNonNull(requiredCapability);requiredCapability.ifPresent(StrictJson::text);
            java.util.Objects.requireNonNull(install);StrictJson.require(!operations.isEmpty()&&operations.size()<=8,"finite explicit composite operations required");
        }
    }
    private static final String MACHINE = "action-writer-software-fixture";
    private static final String PIPE = "\\\\.\\pipe\\action-writer-software-fixture";
    private static final String SESSION = "held-action-fixture";
    private static final String AUTHORITY = "root-action-software-fixture";
    private static final String SHA = "0".repeat(64);
    private static final GameGeneration GAME = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final OperationKey ACTION = new OperationKey("pause-map");
    private static final OperationKey COUNCIL = new OperationKey("private-assign-councillor-v1");
    private static final OperationKey PARENT = new OperationKey("fixture-composite");
    private static final OperationKey QUERY = new OperationKey("query-fixture-status");
    public static final int INITIAL_DATE_RAW = CampaignCalendar.dateToRaw("1066.9.15");
    private static final String STATE = """
            {"paused":true,"map_ready":true,"speed":3,"date_raw":%d,
             "played_character":{"character_id":73,"alive":true},"active_event":null,
             "pending_character_interaction":null,"one_life_terminal":false,"one_life_terminal_reason":null,
             "episode_identity_pending":false,"active_wars":[],"player_armies":[],
             "diagnostics":{"bridge_pid":42,"connection_generation":5}}
            """.formatted(INITIAL_DATE_RAW);
    private static final String DRIVER = """
            {"format_version":2,"pipe_name":"\\\\\\\\.\\\\pipe\\\\action-writer-software-fixture","bridge_pid":42,
             "episode_character_id":73,"episode_run_id":"fixture-episode-1","last_checkpoint":null,"command_history":[],
             "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,"campaign_goal":null}
            """;
    public final Path root;
    public final ContinuityWriter writer;
    public final NativeOutcomeArchive archive;
    public final ContinuityActionJournal journal;
    public final ActionCoordinator coordinator;
    public final PlanningReadCoordinator reads;
    public final ReadContract<RawJson> readContract;
    public final NativeReadinessCollector collector;
    private final DriverFrameEvidenceLoader actualFrameLoader;
    private final DriverStateAssembler actualDriver;
    private final DriverObservationAssembler actualObservationAssembler;
    private final OriginalEvidencePort actualOriginals;
    private final Map<OperationKey, SoftwareActionScenario> installedActionScenarios;
    private final RootReadContractCatalog actualReadCatalog;
    private final AtomicReference<ActionContinuityAuthority> actualActionAuthority = new AtomicReference<>();
    private final AtomicReference<PhysicalActionRegistry> actualPhysicalActions = new AtomicReference<>();
    private final ActionPorts.GuardPort physicalSoftwareGuards;
    private final AtomicReference<PlanningReadCoordinator.ReadGuardPort> reconciliationReadGuard = new AtomicReference<>();
    private final AtomicReference<PlanningReadCoordinator.KnownReadObserver> knownReadObserver = new AtomicReference<>();
    private final AtomicReference<java.util.function.BiConsumer<WriterContracts.Head,ActionCommand>> guardObserver = new AtomicReference<>();
    private final AtomicReference<NativeRecordedEvidenceVerifier.ReconciliationGuardVerifier> reconciliationArchivedVerifier = new AtomicReference<>();
    private final java.util.ArrayDeque<GuardObservationRecord> guardObservations = new java.util.ArrayDeque<>();
    public record GuardObservationRecord(String actionId,String operation,Instant before,Instant after,
            long headSequence,String headDigest,Instant callerDeadline,
            Optional<String> thrownClass,Optional<String> thrownMessage) { }
    private void appendGuardObservation(GuardObservationRecord record) {
        synchronized(guardObservations) {
            if(guardObservations.size()==64)guardObservations.removeFirst();
            guardObservations.addLast(record);
        }
    }
    public List<GuardObservationRecord> getGuardObservations(String actionId) {
        synchronized(guardObservations) {
            return guardObservations.stream().filter(row->row.actionId().equals(actionId)).toList();
        }
    }
    /** Test-only Root wrappers receive these original producers; no guard/result DTO is replaced. */
    public record SoftwareReadGuardContext(ContinuityWriter writer,SessionPorts.SessionIdentity identity,
            RootPlanningReadGuard guard,NativeRecordedEvidenceVerifier originals) {
        public SoftwareReadGuardContext {
            java.util.Objects.requireNonNull(writer);java.util.Objects.requireNonNull(identity);
            java.util.Objects.requireNonNull(guard);java.util.Objects.requireNonNull(originals);
        }
    }
    @FunctionalInterface public interface SoftwareReadGuardDecoration {
        PlanningReadCoordinator.ReadGuardPort decorate(SoftwareReadGuardContext actual);
    }
    /** Controlled protocol tests only; neither this callback nor the packet DATA qualifies a Managed Game. */
    @FunctionalInterface public interface SoftwareProtocolWork<T> { T run(NativeGameTransport actual)throws Exception; }
    public <T> T withSoftwareProtocol(NativePacketPort original,NativePipeEndpoint.Config config,
            SoftwareProtocolWork<T> work)throws Exception {
        java.util.Objects.requireNonNull(work);java.util.Objects.requireNonNull(original);java.util.Objects.requireNonNull(config);
        try(var actual=new NativeGameTransport(original,config,16,16)) {return work.run(actual);}
    }
    public record PhysicalInputs(NativeGameTransport transport, DriverStateAssembler driverAssembler,
            DriverObservationAssembler observationAssembler, G2Source source, OriginalEvidencePort originals,
            NativeEffectEvidence.FrameLoader frameLoader) { }
    public PhysicalInputs physicalInputs() {
        return new PhysicalInputs(transport, actualDriver, actualObservationAssembler, source, actualOriginals, actualFrameLoader);
    }
    private final java.util.concurrent.ConcurrentHashMap<String, WriterContracts.TransitionAuthority> extraAuthorities = new java.util.concurrent.ConcurrentHashMap<>();
    private final java.util.concurrent.ConcurrentHashMap<OperationKey, NativeRecordedEvidenceVerifier.Binding> extraVerifiers = new java.util.concurrent.ConcurrentHashMap<>();
    private final List<ReadContract<?>> extraReadContracts;
    public final CouncilContinuationCoordinator continuations;
    public final java.util.ArrayList<CouncilContinuationReceipt> continuationReceipts = new java.util.ArrayList<>();
    public final AtomicReference<CouncilContinuationCoordinator.Boundary> failContinuationAt = new AtomicReference<>();
    public final AtomicInteger continuationCalls = new AtomicInteger();
    public final AtomicInteger childInitialGuardChecks = new AtomicInteger();
    public final AtomicInteger childAckObservationChecks = new AtomicInteger();
    public final AtomicReference<String> childActionId = new AtomicReference<>();
    public int requestedContinuations = 1;
    public final AtomicInteger pendingPreparations = new AtomicInteger();
    public final java.util.concurrent.atomic.AtomicBoolean failPrimitivePreparation = new java.util.concurrent.atomic.AtomicBoolean();
    public final AtomicInteger attemptCompletions = new AtomicInteger();
    public final AtomicReference<ActionReceipt> completedAttempt = new AtomicReference<>();
    public final AtomicInteger sourceChecks = new AtomicInteger();
    public final AtomicInteger nestedPlanningReads = new AtomicInteger();
    public final AtomicInteger collectorLocks = new AtomicInteger();
    public final AtomicInteger intentBarrierChecks = new AtomicInteger();
    public final AtomicInteger stopAtIntentBarrier = new AtomicInteger();
    public final AtomicInteger preparationClaimConsumptions = new AtomicInteger();
    public final java.util.concurrent.atomic.AtomicBoolean checkBarrierInsidePreparation = new java.util.concurrent.atomic.AtomicBoolean();
    public final AtomicReference<ContinuityStorePort.Session> originalHookSession = new AtomicReference<>();
    public final AtomicReference<NativeRequest> originalPreparedAtHook = new AtomicReference<>();
    public final AtomicReference<ActionPorts.PostconditionResult> nextPostcondition = new AtomicReference<>();
    public final AtomicReference<PlanningReadReceipt> lastNestedRead = new AtomicReference<>();
    public final AtomicReference<org.xar.ck3.control.application.planning.PlanningRequest> lastPublishedReady = new AtomicReference<>();
    private final AtomicReference<ActionPorts.IntentPreparationPort> pendingHook = new AtomicReference<>();
    private final AtomicReference<ActionPorts.IntentPreparationPort> additionalBeforeIntent = new AtomicReference<>();
    private final List<DomainBodies.Registration> softwareDomains;
    private final G2Source source;
    private final ScriptedPackets packets;
    private static final NativeWire.Bytes CONTROLLED_SOURCE_PROOF =
            new NativeWire.Bytes(bytes("{\"scope\":\"controlled-test-source\"}"));
    private record InitialObservationData(NativeWire.Bytes nativePacket, NativeWire.Bytes driver,
            NativeWire.Bytes sourceProof, NativeWire.Bytes hello, NativeWire.Bytes heartbeat) { }
    private final InitialObservationData initialObservationData;
    private final NativeGameTransport transport;
    private final StorageWriteGuard storageGuard;
    private final boolean council;
    private final OperationKey action;
    private final boolean compositeMode;
    private final SessionPorts.SessionIdentity identity = new SessionPorts.SessionIdentity(MACHINE, GAME, SESSION);

    public ActionWriterIntegrationFixture(Path root, boolean loseAck) throws IOException {
        this(root, loseAck, false);
    }
    public ActionWriterIntegrationFixture(Path root, boolean loseAck, boolean council) throws IOException {
        this(root, loseAck, council, false);
    }
    public ActionWriterIntegrationFixture(Path root, boolean loseAck, boolean council, boolean compositeMode) throws IOException {
        this(root, loseAck, council, compositeMode, Optional.empty(), List.of());
    }
    public ActionWriterIntegrationFixture(Path root, boolean loseAck, SoftwareReadScenario scenario) throws IOException {
        this(root, loseAck, false, false, Optional.of(java.util.Objects.requireNonNull(scenario)), List.of());
    }
    /** Decorate only the original read authority; the existing tracked wire/after path remains intact. */
    public ActionWriterIntegrationFixture(Path root,boolean loseAck,SoftwareReadScenario scenario,
            SoftwareReadGuardDecoration decoration)throws IOException {
        this(root,loseAck,false,false,Optional.of(java.util.Objects.requireNonNull(scenario)),List.of(),List.of(),
                ignored->List.of(),Clock.systemUTC(),java.util.Objects.requireNonNull(decoration));
    }
    /** Fix only the transport receive clock; all original readiness/source checks retain their real clock. */
    public ActionWriterIntegrationFixture(Path root, boolean loseAck, SoftwareReadScenario scenario, Clock receivedClock) throws IOException {
        this(root, loseAck, false, false, Optional.of(java.util.Objects.requireNonNull(scenario)), List.of(), List.of(),
                ignored -> List.of(), java.util.Objects.requireNonNull(receivedClock));
    }
    public ActionWriterIntegrationFixture(Path root, boolean loseAck, SoftwareActionScenario scenario) throws IOException {
        this(root, loseAck, false, false, Optional.empty(), List.of(java.util.Objects.requireNonNull(scenario)));
    }
    public ActionWriterIntegrationFixture(Path root, boolean loseAck, SoftwareReadScenario reads, List<SoftwareActionScenario> actions) throws IOException {
        this(root, loseAck, false, false, Optional.of(java.util.Objects.requireNonNull(reads)), List.copyOf(actions));
    }
    /** Use the explicit finite freshness of the real caller; all original guard checks stay installed. */
    public ActionWriterIntegrationFixture(Path root, boolean loseAck, SoftwareReadScenario reads,
            List<SoftwareActionScenario> actions, Duration readinessValidity) throws IOException {
        this(root, loseAck, false, false, Optional.of(java.util.Objects.requireNonNull(reads)), List.copyOf(actions),
                List.of(), ignored -> List.of(), Clock.systemUTC(), SoftwareReadGuardContext::guard,
                java.util.Objects.requireNonNull(readinessValidity));
    }
    public ActionWriterIntegrationFixture(Path root,boolean loseAck,SoftwareReadScenario reads,List<SoftwareActionScenario> actions,
            List<SoftwareCompositeScenario> composites) throws IOException {
        this(root,loseAck,false,false,Optional.of(java.util.Objects.requireNonNull(reads)),List.copyOf(actions),List.copyOf(composites));
    }
    /** Actual original domain registrations are installed on this same finite software writer before any event. */
    public ActionWriterIntegrationFixture(Path root,boolean loseAck,SoftwareReadScenario reads,List<SoftwareActionScenario> actions,
            List<SoftwareCompositeScenario> composites,
            java.util.function.Function<ExactRef,List<DomainBodies.Registration>> actualDomains) throws IOException {
        this(root,loseAck,false,false,Optional.of(java.util.Objects.requireNonNull(reads)),List.copyOf(actions),List.copyOf(composites),
                java.util.Objects.requireNonNull(actualDomains));
    }
    private ActionWriterIntegrationFixture(Path root, boolean loseAck, boolean council, boolean compositeMode,
            Optional<SoftwareReadScenario> scenario, List<SoftwareActionScenario> actionScenarios) throws IOException {
        this(root,loseAck,council,compositeMode,scenario,actionScenarios,List.of());
    }
    private ActionWriterIntegrationFixture(Path root,boolean loseAck,boolean council,boolean compositeMode,
            Optional<SoftwareReadScenario> scenario,List<SoftwareActionScenario> actionScenarios,List<SoftwareCompositeScenario> compositeScenarios) throws IOException {
        this(root,loseAck,council,compositeMode,scenario,actionScenarios,compositeScenarios,ignored->List.of());
    }
    private ActionWriterIntegrationFixture(Path root,boolean loseAck,boolean council,boolean compositeMode,
            Optional<SoftwareReadScenario> scenario,List<SoftwareActionScenario> actionScenarios,List<SoftwareCompositeScenario> compositeScenarios,
            java.util.function.Function<ExactRef,List<DomainBodies.Registration>> actualDomains) throws IOException {
        this(root,loseAck,council,compositeMode,scenario,actionScenarios,compositeScenarios,actualDomains,Clock.systemUTC());
    }
    private ActionWriterIntegrationFixture(Path root,boolean loseAck,boolean council,boolean compositeMode,
            Optional<SoftwareReadScenario> scenario,List<SoftwareActionScenario> actionScenarios,List<SoftwareCompositeScenario> compositeScenarios,
            java.util.function.Function<ExactRef,List<DomainBodies.Registration>> actualDomains,Clock receivedClock) throws IOException {
        this(root,loseAck,council,compositeMode,scenario,actionScenarios,compositeScenarios,actualDomains,receivedClock,
                SoftwareReadGuardContext::guard);
    }
    private ActionWriterIntegrationFixture(Path root,boolean loseAck,boolean council,boolean compositeMode,
            Optional<SoftwareReadScenario> scenario,List<SoftwareActionScenario> actionScenarios,List<SoftwareCompositeScenario> compositeScenarios,
            java.util.function.Function<ExactRef,List<DomainBodies.Registration>> actualDomains,Clock receivedClock,
            SoftwareReadGuardDecoration decoration) throws IOException {
        this(root,loseAck,council,compositeMode,scenario,actionScenarios,compositeScenarios,actualDomains,receivedClock,
                decoration,Duration.ofSeconds(30));
    }
    private ActionWriterIntegrationFixture(Path root,boolean loseAck,boolean council,boolean compositeMode,
            Optional<SoftwareReadScenario> scenario,List<SoftwareActionScenario> actionScenarios,List<SoftwareCompositeScenario> compositeScenarios,
            java.util.function.Function<ExactRef,List<DomainBodies.Registration>> actualDomains,Clock receivedClock,
            SoftwareReadGuardDecoration decoration,Duration readinessValidity) throws IOException {
        java.util.Objects.requireNonNull(receivedClock);
        java.util.Objects.requireNonNull(readinessValidity);
        actionScenarios = List.copyOf(actionScenarios);
        compositeScenarios=List.copyOf(compositeScenarios);
        Set<OperationKey> softwareCompositeOperations=compositeScenarios.stream().flatMap(value->value.operations().stream()).collect(java.util.stream.Collectors.toUnmodifiableSet());
        StrictJson.require(compositeScenarios.size()<=8&&compositeScenarios.stream().map(SoftwareCompositeScenario::handlerId).distinct().count()==compositeScenarios.size()
                &&compositeScenarios.stream().mapToInt(value->value.operations().size()).sum()==softwareCompositeOperations.size(),"unique finite original software composite scenarios required");
        StrictJson.require(actionScenarios.size() <= 16 && actionScenarios.stream().map(SoftwareActionScenario::operation).distinct().count() == actionScenarios.size(),
                "finite unique exact software action scenarios required");
        installedActionScenarios = actionScenarios.stream().collect(java.util.stream.Collectors.toUnmodifiableMap(SoftwareActionScenario::operation, value -> value));
        this.council = council; this.action = actionScenarios.isEmpty() ? (council ? COUNCIL : ACTION) : actionScenarios.getFirst().operation(); this.compositeMode = compositeMode;
        assertFalse(council && compositeMode, "one controlled fixture route per test");
        var actionOperations = actionScenarios.isEmpty() ? Set.of(action) : Set.copyOf(installedActionScenarios.keySet());
        StrictJson.require(java.util.Collections.disjoint(actionOperations,softwareCompositeOperations)
                &&(!compositeMode||!softwareCompositeOperations.contains(PARENT)),"primitive/composite catalog operations must be disjoint");
        var executableBuilder = new java.util.HashSet<>(actionOperations); if (compositeMode) executableBuilder.add(PARENT);
        executableBuilder.addAll(softwareCompositeOperations);
        Set<OperationKey> executable = Set.copyOf(executableBuilder);
        this.root = root; Files.createDirectory(root);
        Path driverFile = root.resolve("original-driver.json"); Files.writeString(driverFile, DRIVER, StandardOpenOption.CREATE_NEW);
        Path sourceFile = root.resolve("reviewed-fixture-source.txt"); Files.writeString(sourceFile, "controlled fixture source, never a live package qualification", StandardOpenOption.CREATE_NEW);
        ExactRef originalDriver = reference(driverFile), reviewed = reference(sourceFile);
        softwareDomains=List.copyOf(java.util.Objects.requireNonNull(actualDomains).apply(reviewed));
        StrictJson.require(softwareDomains.size()<=16
                &&softwareDomains.stream().map(DomainBodies.Registration::slot).distinct().count()==softwareDomains.size()
                &&softwareDomains.stream().noneMatch(value->value.slot()==DomainBodies.Slot.COUNCIL_CONTINUATION),
                "finite unique additional domain slots must preserve the original Council continuation owner");
        Set<ExactRef> domainSources=softwareDomains.stream().flatMap(value->value.producerSources().stream())
                .collect(java.util.stream.Collectors.toUnmodifiableSet());
        StrictJson.require(domainSources.size()<=64,"bounded actual software domain source closure required");
        for(ExactRef actualSource:domainSources) {
            StrictJson.require(actualSource.bytes()>0&&actualSource.bytes()<=1_048_576,"bounded actual domain producer source required");
            Path actualPath=Path.of(actualSource.path());
            StrictJson.require(Files.isRegularFile(actualPath)&&Files.size(actualPath)==actualSource.bytes(),
                    "domain producer source is not its actual retained file");
            byte[] original=Files.readAllBytes(actualPath);
            StrictJson.require(original.length==actualSource.bytes()&&ActionCodec.sha256(original).equals(actualSource.sha256()),
                    "domain producer source bytes changed before original writer installation");
        }
        source = new G2Source(MACHINE, Instant.now().toString(), scenario.flatMap(SoftwareReadScenario::expectedCk3Version).orElse("software-fixture"), reviewed);
        extraReadContracts = scenario.map(value -> List.copyOf(value.contracts().apply(reviewed))).orElseGet(List::of);
        List<RootReadContractCatalog.Family<?,?>> dynamicFamilies=scenario.map(value->List.copyOf(value.dynamicFamilies().apply(reviewed))).orElseGet(List::of);
        StrictJson.require(dynamicFamilies.size()<=16&&dynamicFamilies.stream().map(RootReadContractCatalog.Family::id).distinct().count()==dynamicFamilies.size()
                &&dynamicFamilies.stream().allMatch(value->value.definitionSource().equals(reviewed)&&value.decoderSource().equals(reviewed)),
                "finite unique dynamic read families must retain the exact reviewed definition/decoder source");
        StrictJson.require(extraReadContracts.size() <= 16
                && extraReadContracts.stream().map(ReadContract::operation).distinct().count() == extraReadContracts.size()
                && extraReadContracts.stream().noneMatch(value -> value.operation().equals(QUERY))
                && extraReadContracts.stream().allMatch(value -> value.sourceRef().equals(reviewed)),
                "finite exact software read contracts must share the actual controlled source, without aliases");
        var bridgeCapabilityBuilder = new java.util.HashSet<>(Set.of("game.command.pause-map", "game.query.fixture-status"));
        actionScenarios.forEach(value -> bridgeCapabilityBuilder.add(value.requiredCapability()));
        extraReadContracts.forEach(value -> value.requiredCapability().ifPresent(bridgeCapabilityBuilder::add));
        dynamicFamilies.forEach(value->value.requiredCapability().ifPresent(bridgeCapabilityBuilder::add));
        scenario.ifPresent(value -> bridgeCapabilityBuilder.addAll(value.extraHelloCapabilities()));
        compositeScenarios.forEach(value->value.requiredCapability().ifPresent(bridgeCapabilityBuilder::add));
        Set<String> bridgeCapabilities = Set.copyOf(bridgeCapabilityBuilder);
        byte[] initialPacket = initialSnapshotPacket();
        var initial = seed(originalDriver);
        if (actionScenarios.stream().anyMatch(SoftwareActionScenario::initializeBaseline)) {
            Path baseline = root.resolve("original-initial-native-packet.bin");
            Files.write(baseline, initialPacket, StandardOpenOption.CREATE_NEW);
            bindInitialSoftwareFrame(initial, baseline, driverFile);
        }
        byte[] seed = ContinuityJson.canonical(initial);
        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
        Files.write(snapshot, seed, StandardOpenOption.CREATE_NEW); Files.write(anchor, seed, StandardOpenOption.CREATE_NEW);
        Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
        var layout = new WriterContracts.Layout(snapshot, reference(anchor), MACHINE);
        storageGuard=StorageWriteGuardTestSupport.create(layout);
        var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 16 * 1024 * 1024),storageGuard);
        assertSame(storageGuard,artifacts.storageGuard());
        continuations = new CouncilContinuationCoordinator(layout.lock(), List.of(reviewed), Clock.systemUTC(), boundary -> {
            if (failContinuationAt.compareAndSet(boundary, null)) throw new IOException("controlled durable boundary " + boundary);
        });
        CouncilContinuationPorts.SeedAuthority seedAuthority = (same, head, manifest, archived) -> {
            same.requireWriter(layout.lock());
            State actual = CouncilContinuationCodec.decodeState(archived.loadMaterial(manifest).bytes());
            assertEquals(MACHINE, actual.machineId()); assertTrue(actual.active().isEmpty()); assertTrue(actual.records().isEmpty());
            assertEquals(0, head.state().sequence(), "software fixture only seeds a measured pristine original window");
            return actual;
        };
        AtomicReference<ActionContinuityAuthority> actualAuthority = actualActionAuthority;
        writer = new ContinuityWriter(layout, List.of(reviewed), new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState previous, WriterContracts.Request request) { throw new AssertionError("detached Head is forbidden"); }
            @Override public String revalidate(WriterContracts.Head head, WriterContracts.Request request) throws IOException { return extraAuthorities.getOrDefault(request.kind(), actualAuthority.get()).revalidate(head, request); }
            @Override public ContinuityState reduce(ContinuityState previous, WriterContracts.Request request) throws IOException { return extraAuthorities.getOrDefault(request.kind(), actualAuthority.get()).reduce(previous, request); }
        }, Clock.systemUTC(), new ContinuityWriter.Extensions(withSoftwareDomains(council ? List.of(continuations.registration(seedAuthority)) : List.of()), Optional.of(artifacts), Optional.empty()),storageGuard);
        archive = new NativeOutcomeArchive(artifacts, writer); journal = new ContinuityActionJournal(writer, archive);
        var issuedReadCatalog=new AtomicReference<RootReadContractCatalog>();
        packets = new ScriptedPackets(loseAck, action, scenario, issuedReadCatalog::get, installedActionScenarios, bridgeCapabilities, initialPacket);
        var permission = new NativePrivateActionPermission(COUNCIL, "controlled-council-test-source", reviewed,
                request -> assertTrue(request.additionalFields().objectFieldNames().isEmpty()), (config, hello, guard, request) -> reviewed);
        var privatePermissions = new java.util.ArrayList<NativePrivateActionPermission>();
        if (council) privatePermissions.add(permission);
        for (var selected : actionScenarios) if (selected.privatePermission().isPresent()) {
            var installed = java.util.Objects.requireNonNull(selected.privatePermission().orElseThrow().apply(reviewed));
            StrictJson.require(installed.operation().equals(selected.operation()) && installed.originalProducerSource().equals(reviewed), "software private permission must retain its exact installed operation and source");
            privatePermissions.add(installed);
        }
        transport = new NativeGameTransport(packets, new NativePipeEndpoint.Config(PIPE, MACHINE, GAME, SESSION, "fixture", scenario.map(SoftwareReadScenario::profileSha256).orElse(SHA), scenario.map(SoftwareReadScenario::adapterId).orElse("fixture-adapter")), 64, 128, List.copyOf(privatePermissions),receivedClock);
        var assembler = new DriverObservationAssembler(); actualObservationAssembler = assembler;
        var auxiliary = DriverJson.object(bytes("{\"episode_binding_state\":\"active_new\",\"driver_state_restored\":false,\"restore_kind\":\"new_episode\",\"driver_state_error\":null,\"cold_candidate_rejection\":null,\"episode_transition_error\":null,\"capability_session_paths\":{\"queue_dir\":null,\"driver_state_path\":null},\"episode_identity_pending\":false}"), DriverJson.MAX_NATIVE_BYTES);
        var imported = DriverFactsRepository.imported(originalDriver, Files.readAllBytes(driverFile), 1, 1, GAME, auxiliary);
        initialObservationData = new InitialObservationData(new NativeWire.Bytes(initialPacket),
                new NativeWire.Bytes(imported.driver().encode()), CONTROLLED_SOURCE_PROOF,
                packets.initialHello, packets.initialHeartbeat);
        var facts = new DriverFactsRepository(imported);
        var producer = new NativeDriverObservationProducer(facts, transport, source,
                original -> archive.preserveMaterial(new RawJson(original)));
        var driver = new DriverStateAssembler(new ActionSnapshotReader(journal), facts, producer); actualDriver = driver;
        driver.bindHistoryArchive(archive, journal::borrowedWriterSession);
        actualFrameLoader = new DriverFrameEvidenceLoader(assembler);
        OriginalEvidencePort originals = (borrowed, ref, maximum) -> archive.readArtifact(borrowed, ref, maximum); actualOriginals = originals;
        var readRef = new AtomicReference<PlanningReadCoordinator>();
        var collectorRef = new AtomicReference<NativeReadinessCollector>();
        readContract = contract(reviewed);
        var installedReads = new java.util.ArrayList<ReadContract<?>>(); installedReads.add(readContract); installedReads.addAll(extraReadContracts);
        RootReadContractCatalog catalog = new RootReadContractCatalog(installedReads.stream().map(value->new RootReadContractCatalog.InstalledRead(value,reviewed)).toList(),dynamicFamilies);
        StrictJson.require(issuedReadCatalog.compareAndSet(null,catalog),"one exact actual read catalog is installed once");actualReadCatalog = catalog;
        var effects = new java.util.ArrayList<NativeEffectRegistry.Binding>();
        for (OperationKey registered : actionOperations.stream().sorted(java.util.Comparator.comparing(OperationKey::value)).toList()) {
        SoftwareActionScenario actionScenario = installedActionScenarios.get(registered);
        Optional<String> required = (council || actionScenario != null && actionScenario.privatePermission().isPresent())
                ? Optional.empty() : Optional.of(actionScenario == null ? "game.command.pause-map" : actionScenario.requiredCapability());
        effects.add(NativeEffectRegistry.Binding.existing(registered, reviewed,
                new ActionPorts.PreparationPort() {
                    @Override public void requireProtocolIdentity(ActionCommand command) {
                        if(actionScenario!=null&&actionScenario.originalPreparation().isPresent())
                            actionScenario.originalPreparation().orElseThrow().requireProtocolIdentity(command);
                        else ActionPorts.PreparationPort.super.requireProtocolIdentity(command);
                    }
                    @Override public NativeRequest prepare(ActionCommand command) {
                        StrictJson.require(actionScenario == null || actionScenario.originalPreparation().isEmpty(),
                                "actual source preparation requires the original borrowed Session and request ID");
                        return prepared(null, command, null);
                    }
                    @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand command, String requestId) {
                        return prepared(same, command, requestId);
                    }
                    private NativeRequest prepared(ContinuityStorePort.Session same, ActionCommand command, String requestId) {
                    if (failPrimitivePreparation.get()) throw new IllegalStateException("controlled read-only primitive preparation failure");
                    if (checkBarrierInsidePreparation.get()) {
                        try { ActionReadPublicationScope.requireClearBeforeIntent(journal.borrowedWriterSession(), command); }
                        catch (IOException failure) { throw new UncheckedIOException(failure); }
                        preparationClaimConsumptions.incrementAndGet();
                    }
                    if (actionScenario != null && actionScenario.originalPreparation().isPresent()) {
                        try { writer.requireSession(same); } catch (IOException failure) { throw new UncheckedIOException(failure); }
                        StrictJson.require(requestId.equals(RequestIds.forCommand(command)),
                                "actual software preparation received another original request identity");
                        NativeRequest actual = java.util.Objects.requireNonNull(actionScenario.originalPreparation().orElseThrow().prepare(same, command, requestId));
                        NativeStepDiscriminator.requireRequest(registered,ExecutableStepBindings.Kind.ACTION,actual);
                        StrictJson.require(actual.requiredCapability().equals(required),"actual source preparation changed its original capability");
                        return actual;
                    }
                    return new NativeRequest(registered.value(), required, raw("{}"));
                    }
                },
                (command, attempt, dispatch) -> {
                    if (actionScenario != null) return actionScenario.postcondition().observe(command, attempt, dispatch);
                    if (compositeMode) {
                        assertEquals(command, ActionCommandScope.current().orElseThrow());
                        try {
                            collectorRef.get().current(journal.borrowedWriterSession(), command.before(), command.deadline(), lease -> {
                                childAckObservationChecks.incrementAndGet(); return null;
                            });
                        } catch (IOException failure) { throw new UncheckedIOException(failure); }
                    }
                    if (council) {
                        for (int index = 0; index < requestedContinuations; index++) {
                            continuationCalls.incrementAndGet();
                            try { continuationReceipts.add(continuations.continueOnce(journal.borrowedWriterSession(), command, attempt, Stage.HELPER_STATUS, command.deadline())); }
                            catch (IOException failure) { throw new UncheckedIOException(failure); }
                        }
                    }
                    return Optional.ofNullable(nextPostcondition.get()).orElseGet(() -> new ActionPorts.Pending("controlled unresolved poststate", List.of(attempt.guard().nativeEvidence())));
                }));
        }
        CompositeActionPort composite = new CompositeActionPort() {
            @Override public String handlerId() { return "controlled-composite-parent"; }
            @Override public boolean supports(OperationKey operation) { return operation.equals(PARENT); }
            @Override public void validate(ActionCommand parent) { assertEquals(PARENT, parent.operation()); }
            @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) {
                try {
                    var same = journal.borrowedWriterSession(); var actual = ActionChildPlanningScope.current(same, same.head()).orElseThrow();
                    assertEquals(parent.actionId(), actual.actionId()); assertEquals(ActionCodec.bodySha256(parent), actual.bodySha256());
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
                var child = new ActionCommand(children.nextActionId(action), parent.before(), parent.source(), parent.sessionId(), action,
                        parent.arguments(), parent.expected(), parent.claims(), parent.deadline()); childActionId.set(child.actionId()); children.submit(child);
                throw new AssertionError("controlled child remains UNKNOWN and cannot return authority for another child");
            }
            @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained) { return new ActionPorts.Pending("controlled unresolved child; collect only", List.of(reviewed)); }
        };
        var compositeBindings = compositeMode ? List.of(new RootExecutableBindings.CompositeBinding(composite, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command.pause-map"), reviewed, reviewed)) : List.<RootExecutableBindings.CompositeBinding>of();
        var actionBindings = effects.stream().map(effect -> {
            var selected = installedActionScenarios.get(effect.operation());
            Optional<String> cap = (council || selected != null && selected.privatePermission().isPresent())
                    ? Optional.empty() : Optional.of(selected == null ? "game.command.pause-map" : selected.requiredCapability());
            return new RootExecutableBindings.ActionBinding(effect, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, cap, reviewed);
        }).toList();
        ContinuityStorePort countedObservationStore = new ContinuityStorePort() {
            @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException { return writer.preview(request); }
            @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException { return writer.commit(prepared); }
            @Override public ExactRef persistedHead() throws IOException { return writer.persistedHead(); }
            @Override public void requireSession(Session borrowed) throws IOException { writer.requireSession(borrowed); }
            @Override public <T> T locked(SessionWork<T> work) throws IOException { collectorLocks.incrementAndGet(); return writer.locked(work); }
        };
        collector = new NativeReadinessCollector(identity, countedObservationStore, transport, driver, assembler,
                (game, deadline) -> new GameLifecycle.Running(game, reviewed),
                (borrowed, role, original) -> archive.preserveArtifact(borrowed, original, role.maximumBytes()),
                new NativeSemanticEvidenceVerifier((borrowed, ref, maximum) -> archive.readArtifact(borrowed, ref, maximum)),
                (borrowed, expected, frame, known, received, process, deadline) -> {
                    writer.requireSession(borrowed); assertEquals(identity, expected); assertEquals(GAME, process.measured());
                    var pin = borrowed.capturePin(reviewed, 65_536); borrowed.verifyPin(pin);
                    var proof = archive.preserveArtifact(borrowed, CONTROLLED_SOURCE_PROOF.value(), 65_536);
                    return new NativeReadinessCollector.SourceQualification(proof, same -> {
                        assertSame(borrowed, same); writer.requireSession(same); same.verifyPin(pin); sourceChecks.incrementAndGet();
                    });
                },
                (borrowed, frame, known, received, deadline) -> new NativeReadinessCollector.ExecutableCapabilities(executable, bridgeCapabilities, Optional.empty()),
                (borrowed, frame, known, received, deadline) -> {
                    var request = new PlanningReadRequest(frame.identity(), source, SESSION, QUERY, new OpportunityJson.Obj(Map.of()), deadline);
                    var result = readRef.get().read(borrowed, readContract, request);
                    assertInstanceOf(PlanningReadResult.Known.class, result,
                            () -> "nested query must borrow the outer actual readiness frame; actual result: "
                                    + (result instanceof PlanningReadResult.Unavailable<?> unavailable ? unavailable.reason() : String.valueOf(result)));
                    var knownRead = (PlanningReadResult.Known<?>) result; lastNestedRead.set(knownRead.receipt()); nestedPlanningReads.incrementAndGet();
                    return new NativeReadinessCollector.PlanningInputs(executable, bridgeCapabilities, Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false, Optional.empty());
                }, new NativeReadiness.Policy(false, false, Optional.of(BigInteger.valueOf(73)), Duration.ZERO, false), readinessValidity, Clock.systemUTC());
        collectorRef.set(collector);
        collector.bindObservationSession(writer::requireSession);
        collector.bindActiveObservationSession(writer::activeSession);
        collector.bindReadyPublication((borrowed, request, frame, known, qualification) -> {
            writer.requireSession(borrowed); qualification.guard().orElseThrow().assertCurrent(borrowed);
            assertEquals(frame.identity(), request.before()); assertEquals(source, request.source()); lastPublishedReady.set(request);
        });
        var allCompositeBindings=new java.util.ArrayList<>(compositeBindings);
        var compositeContext=new SoftwareCompositeContext(writer,journal,archive,collector,actualFrameLoader,source,bridgeCapabilities);
        for(SoftwareCompositeScenario selected:compositeScenarios) {
            String originalHead=writer.locked(same->{StrictJson.require(same.head().state().sequence()==0,"composite install must precede the first canonical event");return same.head().digest();});
            SoftwareCompositeInstallation installed=java.util.Objects.requireNonNull(selected.install().apply(compositeContext));
            StrictJson.require(installed.handler().handlerId().equals(selected.handlerId())
                    &&selected.operations().stream().allMatch(installed.handler()::supports)
                    &&installed.archived().stream().map(NativeRecordedEvidenceVerifier.Binding::operation).collect(java.util.stream.Collectors.toSet()).equals(selected.operations())
                    &&installed.archived().size()==selected.operations().size(),"actual installed composite and exact archived verifier must cover one immutable operation set");
            for(var binding:installed.archived())StrictJson.require(binding.definitionSource().equals(reviewed)
                    &&extraVerifiers.putIfAbsent(binding.operation(),binding)==null,"actual composite replay must bind the same reviewed source exactly once");
            writer.locked(same->{StrictJson.require(same.head().state().sequence()==0&&same.head().digest().equals(originalHead),"composite constructor factory cannot append or replace canonical history");return null;});
            allCompositeBindings.add(new RootExecutableBindings.CompositeBinding(installed.handler(),selected.guardMode(),selected.requiredCapability(),reviewed,reviewed));
        }
        var bindings=RootExecutableBindings.freeze(actionBindings,catalog,List.copyOf(allCompositeBindings),List.copyOf(extraVerifiers.values()),List.of(),64);
        var guards = new RootActionGuard(collector, journal::borrowedWriterSession, archive, source, Clock.systemUTC(), AUTHORITY, originals, bindings);
        ActionPorts.GuardPort trackedGuards = (head, command) -> {
            assertEquals(command, ActionCommandScope.current().orElseThrow());
            var observer=guardObserver.get();
            if(observer!=null)observer.accept(head,command);
            if (childActionId.get() != null && childActionId.get().equals(command.actionId())) {
                var currentParent = ContinuityActionJournal.receipts(head.state(), archive).stream().filter(value -> value.command().operation().equals(PARENT)).findFirst().orElseThrow();
                var running = assertInstanceOf(ActionState.CompositeRunning.class, currentParent.state());
                assertTrue(running.execution().children().contains(new CompositeExecution.Child(command.actionId(), ActionCodec.bodySha256(command))));
                if (ContinuityActionJournal.lookup(head.state(), command.actionId(), archive).isEmpty()) childInitialGuardChecks.incrementAndGet();
            }
            Instant before=Instant.now();
            long sequence=head.state().sequence();String digest=head.digest();
            Optional<String> thrownClass=Optional.empty(),thrownMessage=Optional.empty();
            try { return guards.verify(head, command); }
            catch(RuntimeException|Error failure) {
                thrownClass=Optional.of(failure.getClass().getName());thrownMessage=Optional.ofNullable(failure.getMessage());
                throw failure;
            } finally {
                appendGuardObservation(new GuardObservationRecord(command.actionId(),command.operation().value(),
                        before,Instant.now(),sequence,digest,command.deadline(),thrownClass,thrownMessage));
            }
        };
        physicalSoftwareGuards=trackedGuards;
        var readGuards = new RootPlanningReadGuard(collector, journal::borrowedWriterSession, archive, source, Clock.systemUTC(), AUTHORITY, originals, catalog);
        var decoratedReadGuards=java.util.Objects.requireNonNull(decoration.decorate(new SoftwareReadGuardContext(
                writer,identity,readGuards,new NativeRecordedEvidenceVerifier(archive,journal::borrowedWriterSession,
                        originals,actualFrameLoader,List.copyOf(extraVerifiers.values())))));
        reads = new PlanningReadCoordinator(catalog, journal, new PlanningReadCoordinator.ReadGuardPort() {
            @Override public <T> T withOriginalReadSource(WriterContracts.Head head,PlanningReadRequest request,
                    ReadContract<?> contract,java.util.function.Supplier<T> work) {
                return decoratedReadGuards.withOriginalReadSource(head,request,contract,work);
            }
            @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
                PlanningReadGuard verified;
                if (request.origin() instanceof CommandOrigin.Reconciliation) {
                    var actual = reconciliationReadGuard.get();
                    StrictJson.require(actual != null, "actual software reconciliation read guard is unbound");
                    verified=actual.verify(head, request, contract);
                } else verified=decoratedReadGuards.verify(head, request, contract);
                // Retain only the identical contract which passed the actual original Root guard.
                // Nested collector/status reads finish before their outer guard returns here.
                packets.recordVerifiedRead(contract,request,verified);
                return verified;
            }
            @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
                StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay,
                        "held original READ guard requires the actual gameplay origin");
                return decoratedReadGuards.verifyOriginalCurrent(head,request,contract);
            }
        }, transport, archive, Clock.systemUTC(),new PlanningReadCoordinator.KnownReadObserver() {
            @Override public void afterKnown(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadResult.Known<?> known) {
                var observer=knownReadObserver.get();
                if(observer!=null)observer.afterKnown(same,contract,known);
            }
            @Override public void afterUnavailable(ContinuityStorePort.Session same,ReadContract<?> contract,
                    PlanningReadRequest request,PlanningReadResult.Unavailable<?> unavailable) {
                var observer=knownReadObserver.get();
                if(observer!=null)observer.afterUnavailable(same,contract,request,unavailable);
            }
            @Override public void afterUnavailable(ContinuityStorePort.Session same,ReadContract<?> contract,
                    PlanningReadRequest request,PlanningReadResult.Unavailable<?> unavailable,
                    Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
                var observer=knownReadObserver.get();
                if(observer!=null)observer.afterUnavailable(same,contract,request,unavailable,attempted);
            }
        }); readRef.set(reads);
        ActionPorts.RecordedEvidenceVerifier verifier = (head, proposed) -> {
            var reconciliationVerifier = reconciliationArchivedVerifier.get();
            var actual = reconciliationVerifier == null
                    ? new NativeRecordedEvidenceVerifier(archive, journal::borrowedWriterSession, originals, actualFrameLoader, List.copyOf(extraVerifiers.values()))
                    : new NativeRecordedEvidenceVerifier(archive, journal::borrowedWriterSession, originals, actualFrameLoader, List.copyOf(extraVerifiers.values()), reconciliationVerifier);
            actual.verify(head, proposed);
        };
        actualAuthority.set(new ActionContinuityAuthority(AUTHORITY, archive, trackedGuards, verifier, Clock.systemUTC(),bindings));
        continuations.bind(journal, archive, (same, head, parent, deadline) -> {
            // The software transport keeps this same actual push frame; this does not qualify a live runtime source.
            writer.requireSession(same); GuardEvidence held = ActionTransitions.attempt(parent.state()).orElseThrow().guard();
            for (ExactRef ref : held.supportingEvidence()) same.verifyPin(same.capturePin(ref, WriterContracts.MAX_PIN_BYTES));
            assertTrue(Instant.now().isBefore(held.validUntil())); return held;
        }, new CouncilContinuationPorts.NativePort() {
            @Override public NativeActionPort.DispatchOutcome submit(CouncilContinuationPermit permit, NativeRequest request, Instant deadline) throws InterruptedException { return transport.continueCouncil(permit, request, deadline); }
            @Override public Optional<NativeActionPort.AckReceived> collectOriginalOutcome(String id, Instant deadline) throws IOException, InterruptedException { return transport.collectOriginalOutcome(id, deadline); }
        }, new CouncilContinuationPorts.Policy() {
            @Override public List<ExactRef> prepareEvidence(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent, Stage stage, List<Retained> prior, ActionPorts.OutcomeArchive archived) throws IOException {
                writer.requireSession(same); assertEquals(Stage.HELPER_STATUS, stage); return List.of(reviewed);
            }
            @Override public void verifyIssue(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent, List<Retained> prior, Request next, ActionPorts.OutcomeArchive archived) throws IOException {
                writer.requireSession(same); assertEquals(Stage.HELPER_STATUS, next.stage()); assertEquals(List.of(reviewed), next.supportingEvidence());
            }
            @Override public void verifyOutcome(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent, List<Retained> prior, Entry next, NativeActionPort.DispatchOutcome original, ActionPorts.OutcomeArchive archived) throws IOException {
                writer.requireSession(same); assertEquals(next.request().requestId(), original.requestId());
            }
        });
        if (council) writer.locked(same -> {
            try {
                archive.inSession(same, bound -> {
                    ExactRef manifest = bound.preserveMaterial(new RawJson(CouncilContinuationCodec.encodeState(new State(MACHINE, Optional.empty(), List.of(), Optional.empty()))));
                    try { continuations.adoptOriginal(same, manifest, seedAuthority); } catch (IOException failure) { throw new UncheckedIOException(failure); }
                    return null;
                }); return null;
            } catch (UncheckedIOException failure) { throw failure; }
        });
        pendingHook.set((borrowed, command) -> {
            try { writer.requireSession(borrowed); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            PhysicalActionRegistry physical=actualPhysicalActions.get();
            if (!command.operation().equals(PARENT)&&!softwareCompositeOperations.contains(command.operation())
                    &&(physical==null||physical.find(command.operation()).isEmpty())) {
                try { originalPreparedAtHook.set(ActionPreparationScope.requirePrepared(borrowed, command)); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            originalHookSession.set(borrowed); pendingPreparations.incrementAndGet();
        });
        coordinator = new ActionCoordinator(AUTHORITY, journal, trackedGuards, bindings, transport, bindings.effects(), Clock.systemUTC(), bindings.composites(),
                (borrowed, command) -> {
                    pendingHook.get().prepare(borrowed,command);
                    ActionPorts.IntentPreparationPort additional=additionalBeforeIntent.get();
                    if(additional!=null)additional.prepare(borrowed,command);
                }, (borrowed, actual) -> {
                    try { writer.requireSession(borrowed); assertEquals(actual, ContinuityActionJournal.lookup(borrowed.head().state(), actual.command().actionId(), archive).orElseThrow()); }
                    catch (IOException failure) { throw new UncheckedIOException(failure); }
                    completedAttempt.set(actual); attemptCompletions.incrementAndGet();
                }, (borrowed, command) -> {
                    try { writer.requireSession(borrowed); } catch (IOException failure) { throw new UncheckedIOException(failure); }
                    assertEquals(command, ActionCommandScope.current().orElseThrow());
                    int checked = intentBarrierChecks.incrementAndGet();
                    if (checked == stopAtIntentBarrier.get()) throw new ReadPublicationRequiredException(command, Optional.empty());
                });
    }
    private List<DomainBodies.Registration> withSoftwareDomains(List<DomainBodies.Registration> original) {
        var all=new java.util.ArrayList<DomainBodies.Registration>(List.copyOf(original));all.addAll(softwareDomains);
        StrictJson.require(all.stream().map(DomainBodies.Registration::slot).distinct().count()==all.size(),
                "actual original and additional domain registrations must remain disjoint");
        return List.copyOf(all);
    }
    /** Append the actual domain producer after the original hook, under its identical Session, before the first event. */
    public void bindAdditionalBeforeIntent(ActionPorts.IntentPreparationPort actual)throws IOException {
        java.util.Objects.requireNonNull(actual);
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0&&additionalBeforeIntent.compareAndSet(null,actual),
                    "additional original before-INTENT producer installs once before the first canonical event");return null;
        });
    }
    /** Actual software Gameplay/MMAP source only; both canonical owners receive the identical registry once. */
    public void bindPhysicalActions(PhysicalActionRegistry actual)throws IOException {
        java.util.Objects.requireNonNull(actual);
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0&&actualPhysicalActions.get()==null,
                    "physical software producers install once before the first canonical event");
            for(var binding:actual.installed()) {
                StrictJson.require(binding.transportKind()==org.xar.ck3.control.contracts.presentation.TransportKind.PRESENTATION_MMAP,
                        "this actual software fixture has no qualified frontend/window source");
                for(ExactRef ref:binding.sources())same.verifyPin(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
            }
            StrictJson.require(actualPhysicalActions.compareAndSet(null,actual),"one physical software registry installation attempt");
            // A partial failed installation stays failed; it never gains a retry or a second owner.
            actualActionAuthority.get().bindPhysicalActions(actual);coordinator.bindPhysicalActions(actual);return null;
        });
    }
    /** Reuses the actual tracked Root guard under the original writer/action scope; never constructs a guard. */
    public GuardEvidence physicalSoftwareGuard(WriterContracts.Head actual,ActionCommand command)throws IOException {
        var same=journal.borrowedWriterSession();writer.requireSession(same);
        var installed=actualPhysicalActions.get();
        StrictJson.require(installed!=null&&installed.find(command.operation()).isPresent()
                &&command.origin() instanceof CommandOrigin.Gameplay&&same.head().digest().equals(actual.digest()),
                "actual installed software Gameplay source and identical current canonical head required");
        return physicalSoftwareGuards.verify(actual,command);
    }
    /** Stores constructor-captured software DATA before observation; the original collector still qualifies every received frame. */
    public void preserveInitialObservationData() throws IOException {
        writer.locked(same -> {
            archive.preserveArtifact(same, initialObservationData.nativePacket().value(), ReadinessArchive.Role.NATIVE_PACKET.maximumBytes());
            archive.preserveArtifact(same, initialObservationData.driver().value(), ReadinessArchive.Role.DRIVER.maximumBytes());
            archive.preserveArtifact(same, initialObservationData.sourceProof().value(), 65_536);
            archive.preserveArtifact(same, initialObservationData.hello().value(), ReadinessArchive.Role.HELLO.maximumBytes());
            archive.preserveArtifact(same, initialObservationData.heartbeat().value(), ReadinessArchive.Role.HEARTBEAT.maximumBytes());
            return null;
        });
    }
    public SessionPorts.Ready ready() throws IOException, InterruptedException {
        SessionPorts.Observation actual = collector.observe(identity, Instant.now().plusSeconds(20));
        return assertInstanceOf(SessionPorts.Ready.class, actual, () -> "actual readiness: " + actual + "; native receive: " + transport.diagnostics().production());
    }
    public SessionPorts.SessionIdentity observationIdentity() { return identity; }
    public DriverFrameEvidenceLoader frameLoader() { return actualFrameLoader; }
    public DriverStateAssembler driverAuthority() { return actualDriver; }
    public G2Source observationSource() { return source; }
    public RootReadContractCatalog actualReadCatalog() { return actualReadCatalog; }
    /** Observe the original successful central read. The actual observer may enqueue it for the sole publisher. */
    public void bindKnownReadObserver(PlanningReadCoordinator.KnownReadObserver actual) throws IOException {
        java.util.Objects.requireNonNull(actual);
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0&&knownReadObserver.compareAndSet(null,actual),
                    "actual known-read observer installs once before the first canonical event");
            return null;
        });
    }
    /** Observe both actual Root guard invocations. No guard result or submission authority can be replaced. */
    public void bindGuardObserver(java.util.function.BiConsumer<WriterContracts.Head,ActionCommand> actual) throws IOException {
        java.util.Objects.requireNonNull(actual);
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0&&guardObserver.compareAndSet(null,actual),
                    "actual Root guard observer installs once before the first canonical event");
            return null;
        });
    }
    public void bindReconciliationReadGuard(PlanningReadCoordinator.ReadGuardPort actual) throws IOException {
        java.util.Objects.requireNonNull(actual);
        writer.locked(same -> {
            StrictJson.require(same.head().state().sequence() == 0 && reconciliationReadGuard.compareAndSet(null, actual),
                    "actual reconciliation read guard installs once before the first canonical event"); return null;
        });
    }
    /** Exact actual Root cold-proof verifier, retaining the same immutable domain verifier registry. */
    public void bindReconciliationArchivedVerifier(NativeRecordedEvidenceVerifier.ReconciliationGuardVerifier actual) throws IOException {
        java.util.Objects.requireNonNull(actual);
        writer.locked(same -> {
            StrictJson.require(same.head().state().sequence() == 0 && reconciliationArchivedVerifier.compareAndSet(null, actual),
                    "actual Root reconciliation archived verifier installs once before the first canonical event"); return null;
        });
    }
    /** One-shot exact test routing before any canonical event. The installed implementation performs its real reducer. */
    public void bindAdditionalTransitionAuthority(String exactKind, WriterContracts.TransitionAuthority actual) throws IOException {
        StrictJson.text(exactKind); java.util.Objects.requireNonNull(actual);
        writer.locked(same -> {
            StrictJson.require(same.head().state().sequence() == 0 && !exactKind.equals(ContinuityActionJournal.KIND)
                    && extraAuthorities.putIfAbsent(exactKind, actual) == null, "test authority must be unique and installed before the first event");
            return null;
        });
    }
    /** Complete generic original/guard verification still runs before this real domain callback. */
    public void bindAdditionalArchivedVerifier(NativeRecordedEvidenceVerifier.Binding actual) throws IOException {
        java.util.Objects.requireNonNull(actual);
        writer.locked(same -> {
            StrictJson.require(same.head().state().sequence() == 0 && actionOperationsContains(actual.operation())
                    && extraVerifiers.putIfAbsent(actual.operation(), actual) == null, "exact scenario verifier must be installed once before the first event");
            return null;
        });
    }
    private boolean actionOperationsContains(OperationKey operation) { return installedActionScenarios.isEmpty() ? action.equals(operation) : installedActionScenarios.containsKey(operation); }
    public void enqueueSoftwareNativePacket(byte[] originalPacket) throws IOException { packets.enqueue(originalPacket); }
    public List<ReadContract<?>> extraReadContracts() { return extraReadContracts; }
    public int scenarioReadWrites() { return packets.scenarioReadWrites; }
    /** Lose one explicit scenario READ response, after the endpoint has completed its actual write. */
    public void loseReadAckOnce() throws IOException {
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0,
                    "scenario READ loss installs before the first canonical event");
            packets.loseReadAckOnce(); return null;
        });
    }
    /** Release only the retained original ACK after the actual receive failure; never issue another request. */
    public void releaseLateReadAck() throws IOException { packets.releaseLateReadAck(); }
    /** Hold one actual scenario ACTION response after its write returns, then fail its original receive once. */
    public void loseActionAckOnce()throws IOException {
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0,
                    "scenario ACTION receive failure installs before the first canonical event");
            packets.loseActionAckOnce();return null;
        });
    }
    /** Release exactly the retained original ACTION packet after that real receive failure; never send a new request. */
    public void releaseLateActionAck()throws IOException { packets.releaseLateActionAck(); }
    /** One genuine endpoint rejection for an explicit scenario READ; no caller supplies a response or request ID. */
    public void rejectNextScenarioRead() throws IOException {
        rejectNextScenarioReadAfter(0);
    }
    /** Preselect one bounded occurrence; earlier real scenario READs complete through their original callback. */
    public void rejectNextScenarioReadAfter(int completedScenarioReads) throws IOException {
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0,
                    "scenario READ rejection installs before the first canonical event");
            packets.rejectNextScenarioReadAfter(completedScenarioReads); return null;
        });
    }
    /** The existing native stale-revision error is selected by a fixed typed edge, never caller text. */
    public void rejectNextScenarioReadAsStale() throws IOException {
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0,
                    "scenario stale READ rejection installs before the first canonical event");
            packets.rejectNextScenarioReadAsStale(); return null;
        });
    }
    /** Produce one true native response with a non-object result after the actual guarded READ write. */
    public void malformedNextScenarioReadResult() throws IOException {
        malformedNextScenarioReadResultAfter(0);
    }
    public void malformedNextScenarioReadResultAfter(int completedScenarioReads) throws IOException {
        writer.locked(same->{
            StrictJson.require(same.head().state().sequence()==0,
                    "scenario malformed result installs before the first canonical event");
            packets.malformedNextScenarioReadResultAfter(completedScenarioReads); return null;
        });
    }
    public ActionCommand command(String actionId) throws IOException, InterruptedException {
        return command(actionId, Duration.ofSeconds(25));
    }
    /** Finite software composition input; production frame validity and deadline checks remain independent. */
    public ActionCommand command(String actionId, Duration commandBudget) throws IOException, InterruptedException {
        java.util.Objects.requireNonNull(commandBudget);
        StrictJson.require(!commandBudget.isNegative()&&!commandBudget.isZero()
                &&commandBudget.compareTo(Duration.ofMinutes(2))<=0,"bounded software command budget required");
        var ready = ready(); var request = ready.request();
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, request.before(), source, "paused/v1", List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand(actionId, request.before(), source, SESSION, compositeMode ? PARENT : action, new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), Instant.now().plus(commandBudget));
    }
    public int nativeActionWrites() { return packets.actionWrites; }
    public int nativeReadWrites() { return packets.readWrites; }
    public int continuationWrites() { return packets.continuationWrites; }
    public void loseContinuationAck() { packets.loseContinuationAck = true; }
    public void retainLateContinuationAck() { packets.loseContinuationAck = false; packets.queue.addFirst(packet(packets.lostResult)); }
    public CouncilContinuationReceipt recoverContinuationAfterWriterReopen(String id) throws IOException {
        var layout = new WriterContracts.Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), reference(root.resolve("anchor.json")), MACHINE);
        var restored = new CouncilContinuationCoordinator(layout.lock(), List.of(source.sourceRef()), Clock.systemUTC());
        CouncilContinuationPorts.SeedAuthority neverSeedAgain = (same, head, manifest, archived) -> { throw new AssertionError("recovery cannot seed or clear existing original state"); };
        var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 16 * 1024 * 1024),storageGuard);
        assertSame(storageGuard,store.storageGuard());
        var recoveredWriter = new ContinuityWriter(layout, List.of(source.sourceRef()), new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState state, WriterContracts.Request request) { throw new AssertionError("collect-only recovery cannot append a new world-action transition"); }
            @Override public ContinuityState reduce(ContinuityState state, WriterContracts.Request request) { throw new AssertionError("collect-only recovery cannot replay the original action"); }
        }, Clock.systemUTC(), new ContinuityWriter.Extensions(withSoftwareDomains(List.of(restored.registration(neverSeedAgain))), Optional.of(store), Optional.empty()),storageGuard);
        var recoveredArchive = new NativeOutcomeArchive(store, recoveredWriter);
        restored.bind(new ContinuityActionJournal(recoveredWriter, recoveredArchive), recoveredArchive,
                (same, head, parent, deadline) -> { throw new AssertionError("recovery cannot qualify a new continuation guard"); },
                new CouncilContinuationPorts.NativePort() {
                    @Override public NativeActionPort.DispatchOutcome submit(CouncilContinuationPermit permit, NativeRequest request, Instant deadline) { throw new AssertionError("recovery must never submit"); }
                    @Override public Optional<NativeActionPort.AckReceived> collectOriginalOutcome(String requestId, Instant deadline) throws IOException, InterruptedException { return transport.collectOriginalOutcome(requestId, deadline); }
                }, new CouncilContinuationPorts.Policy() {
                    @Override public List<ExactRef> prepareEvidence(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent, Stage stage, List<Retained> prior, ActionPorts.OutcomeArchive archived) { throw new AssertionError("recovery cannot prepare a new request"); }
                    @Override public void verifyIssue(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent, List<Retained> prior, Request request, ActionPorts.OutcomeArchive archived) { throw new AssertionError("recovery cannot issue"); }
                    @Override public void verifyOutcome(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent, List<Retained> prior, Entry next, NativeActionPort.DispatchOutcome actual, ActionPorts.OutcomeArchive archived) throws IOException {
                        recoveredWriter.requireSession(same); assertEquals(id, actual.requestId());
                    }
                });
        return recoveredWriter.locked(same -> {
            try {
                CouncilContinuationReceipt actual = restored.recover(same, id, Instant.now().plusSeconds(5));
                restored.verifyCanonicalChain(same, same.head(), List.of(actual)); return actual;
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        });
    }
    public ActionReceipt executeCouncil(ActionCommand command) throws IOException, InterruptedException {
        assertTrue(council); AtomicReference<ActionReceipt> actual = new AtomicReference<>();
        assertThrows(IOException.class, () -> transport.withMailbox(command.deadline(), scope -> { actual.set(coordinator.execute(command)); return null; }));
        assertNotNull(actual.get()); return actual.get();
    }
    public int nativePacketReads() { return packets.packetReads; }
    public long sequence() throws IOException { return writer.locked(borrowed -> borrowed.head().state().sequence()); }
    public void failPendingPreparation() { pendingHook.set((borrowed, command) -> { try { writer.requireSession(borrowed); } catch (IOException failure) { throw new UncheckedIOException(failure); } throw new IllegalStateException("controlled pending import failure"); }); }
    public ActionJournal.Snapshot snapshot() { return journal.locked(ActionJournal.LockedJournal::snapshot); }
    public byte[] ledgerBytes() throws IOException { return Files.readAllBytes(root.resolve("ROOT-CONTINUITY-WINDOW.json")); }
    public ActionReceipt reopenAndReturnExisting(ActionCommand command) throws IOException {
        var layout = new WriterContracts.Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), reference(root.resolve("anchor.json")), MACHINE);
        var reopenedArtifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 16 * 1024 * 1024),storageGuard);
        assertSame(storageGuard,reopenedArtifacts.storageGuard());
        var reopenedWriter = new ContinuityWriter(layout, List.of(source.sourceRef()), new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState previous, WriterContracts.Request request) { throw new AssertionError("existing UNKNOWN must not preview a new event"); }
            @Override public ContinuityState reduce(ContinuityState previous, WriterContracts.Request request) { throw new AssertionError("existing UNKNOWN must not reduce a new event"); }
        }, Clock.systemUTC(), new ContinuityWriter.Extensions(softwareDomains, Optional.of(reopenedArtifacts), Optional.empty()),storageGuard);
        var reopenedArchive = new NativeOutcomeArchive(reopenedArtifacts, reopenedWriter);
        var reopenedJournal = new ContinuityActionJournal(reopenedWriter, reopenedArchive);
        var reopened = new ActionCoordinator(AUTHORITY, reopenedJournal,
                (head, next) -> { throw new AssertionError("existing UNKNOWN must not acquire a new action guard"); },
                next -> { throw new AssertionError("existing UNKNOWN must not prepare a new native request"); },
                (permit, request, deadline) -> { throw new AssertionError("existing UNKNOWN must never resubmit"); },
                (next, attempt, dispatch) -> { throw new AssertionError("execute must return the retained receipt, not reconcile implicitly"); }, Clock.systemUTC());
        return reopened.execute(command);
    }
    public void requestMalformedPrimitiveCompositeResult(ActionCommand command) {
        PlanningReadReceipt read = lastNestedRead.get();
        var semantic = new ActionState.EffectObservation(command.before(), source, SESSION, command.expected().observerSchema(), command.expected().values(),
                new ObservationProvenance.Query(read.requestId()), Instant.now(), read.after().binding().nativeEvidence(), List.of());
        nextPostcondition.set(new ActionPorts.CompositeControlObserved(new CompositeControlObservation(read, List.of(), semantic)));
    }
    public static ReadContract<RawJson> contract(ExactRef reviewed) {
        return new ReadContract<>("fixture-status/v1", QUERY, Optional.of("game.query.fixture-status"), "fixture-status",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, reviewed,
                request -> new NativeRequest(QUERY.value(), "game.query.fixture-status", raw("{}")),
                receipt -> receipt.original().originalResultToken().orElseThrow());
    }
    private static ExactRef reference(Path path) throws IOException {
        byte[] original = Files.readAllBytes(path); return new ExactRef(path.toAbsolutePath().normalize().toString(), original.length, ActionCodec.sha256(original));
    }
    private static byte[] initialSnapshotPacket() {
        return packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"fixture-snapshot-1\",\"revision\":1,\"state\":" + STATE + "}");
    }
    /** Explicit controlled baseline DATA, parsed from the same immutable packet and Driver imported by the real producer. */
    private static void bindInitialSoftwareFrame(ObjectNode window, Path originalPacket, Path originalDriver) throws IOException {
        NativeWire.Snapshot snapshot = (NativeWire.Snapshot) NativeWire.decode(Files.readAllBytes(originalPacket));
        var state = NativeWire.object(NativeWire.parse(snapshot.state().value()));
        var driver = NativeWire.object(NativeWire.parse(Files.readAllBytes(originalDriver)));
        var player = NativeWire.object(state.get("played_character"));
        var binding = StrictJson.object();
        binding.put("date_raw", NativeWire.integer(state.get("date_raw"), BigInteger.ZERO, BigInteger.valueOf(Long.MAX_VALUE)));
        binding.put("actor_character_id", NativeWire.integer(player.get("character_id"), BigInteger.ONE, BigInteger.valueOf(Long.MAX_VALUE)));
        binding.put("episode_run_id", StrictJson.text(driver.get("episode_run_id")));
        binding.put("snapshot_id", snapshot.snapshotId()); binding.put("revision", 1); binding.put("native_revision", snapshot.revision());
        window.set("latest_binding", binding); window.set("java_controlled_initial_native_packet", reference(originalPacket).toJson());
    }
    private static ObjectNode seed(ExactRef originalDriver) {
        var row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958); row.put("target_years", 30);
        row.put("calendar_year_days", 365.25); row.put("start_date_raw", INITIAL_DATE_RAW); row.put("target_date_raw", Math.addExact(INITIAL_DATE_RAW, Math.multiplyExact(10_958, CampaignCalendar.TICKS_PER_DAY))); row.put("last_settled_date_raw", INITIAL_DATE_RAW);
        row.put("last_settled_cycles", 0); row.put("manual_repair_count", 0); row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        var game = row.putObject("game_binding"); game.put("pid", 42); game.put("creation_date", "2026-10-24T00:00:00Z"); row.putNull("latest_binding");
        row.putNull("pending_cycle"); row.put("NEXT", 11559); row.set("java_driver_history_baseline", originalDriver.toJson()); return row;
    }
    private static RawJson raw(String value) { return new RawJson(bytes(value)); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] packet(String value) { try { return NativeWire.packet(bytes(value)); } catch (IOException failure) { throw new UncheckedIOException(failure); } }
    private static final class ScriptedPackets implements NativePacketPort {
        private record GuardedRead(ReadContract<?> contract,PlanningReadRequest request,PlanningReadGuard guard) { }
        private final ThreadLocal<GuardedRead> guardedRead=new ThreadLocal<>();
        private enum ReadAckLoss { UNBOUND, ARMED, AWAITING_READ_FAILURE, HELD, RELEASED }
        private enum ReadRejection { UNBOUND, ARMED, REJECTED }
        private enum ReadRejectionKind { ORDINARY, STALE_REVISION }
        private enum MalformedReadResult { UNBOUND, ARMED, PRODUCED }
        private enum ActionAckLoss { UNBOUND, ARMED, AWAITING_READ_FAILURE, HELD, RELEASED }
        final ArrayDeque<byte[]> queue = new ArrayDeque<>(); final boolean loseAck; final OperationKey action; int actionWrites; int readWrites; int packetReads; int continuationWrites;
        boolean loseContinuationAck; String lostResult; int scenarioReadWrites;
        private ReadAckLoss readAckLoss=ReadAckLoss.UNBOUND; private byte[] retainedReadAck;
        private ReadRejection readRejection=ReadRejection.UNBOUND;
        private ReadRejectionKind readRejectionKind=ReadRejectionKind.ORDINARY;
        private MalformedReadResult malformedReadResult=MalformedReadResult.UNBOUND;
        private int rejectedReadOccurrence; private int malformedReadOccurrence;
        private ActionAckLoss actionAckLoss=ActionAckLoss.UNBOUND;private byte[] retainedActionAck;
        final Optional<SoftwareReadScenario> scenario; final java.util.function.Supplier<RootReadContractCatalog> issuedReadCatalog;
        final Map<OperationKey, SoftwareActionScenario> actionScenarios; private byte[] latestSnapshot;
        private BigInteger noticeSequence = BigInteger.ZERO;
        private final NativeWire.Bytes initialHello;
        private final NativeWire.Bytes initialHeartbeat;
        ScriptedPackets(boolean loseAck, OperationKey action, Optional<SoftwareReadScenario> scenario, java.util.function.Supplier<RootReadContractCatalog> issuedReadCatalog,
                Map<OperationKey, SoftwareActionScenario> actionScenarios, Set<String> bridgeCapabilities, byte[] initialPacket) {
            this.loseAck = loseAck; this.action = action; this.scenario = scenario; this.issuedReadCatalog = java.util.Objects.requireNonNull(issuedReadCatalog); this.actionScenarios = Map.copyOf(actionScenarios);
            latestSnapshot = initialPacket.clone();
            ObjectNode hello = StrictJson.object(); hello.put("type", "hello").put("protocol_version", 1).put("pid", 42).put("connection_generation", 5)
                    .put("bridge_version", "fixture").put("expected_ck3_sha256", scenario.map(SoftwareReadScenario::profileSha256).orElse(SHA))
                    .put("game_adapter_id", scenario.map(SoftwareReadScenario::adapterId).orElse("fixture-adapter"))
                    .put("game_adapter_status", "ready").put("ck3_build_match", true);
            scenario.flatMap(SoftwareReadScenario::expectedCk3Version).ifPresent(value -> hello.put("expected_ck3_version", value));
            var caps = hello.putArray("capabilities"); caps.add("game.state.snapshot"); bridgeCapabilities.stream().sorted().forEach(caps::add);
            byte[] helloPacket = packet(new String(StrictJson.canonical(hello), StandardCharsets.UTF_8));
            initialHello = new NativeWire.Bytes(helloPacket); queue.add(helloPacket);
            try {
                byte[] heartbeatPacket = heartbeat((NativeWire.Snapshot) NativeWire.decode(initialPacket));
                initialHeartbeat = new NativeWire.Bytes(heartbeatPacket); queue.add(heartbeatPacket);
            }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
        }
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        synchronized void recordVerifiedRead(ReadContract<?> contract,PlanningReadRequest request,PlanningReadGuard guard) {
            RootReadContractCatalog catalog=java.util.Objects.requireNonNull(issuedReadCatalog.get(),"actual read catalog not installed");
            StrictJson.require(catalog.containsIdentity(contract)&&request.operation().equals(contract.operation())
                    &&guard.guardMode()==contract.guardMode()&&request.origin().acceptsGuard(guard.binding().origin()),
                    "software READ selection requires the identical issued contract and its actual original guard");
            guardedRead.set(new GuardedRead(contract,request,guard));
        }
        synchronized void loseReadAckOnce() throws IOException {
            StrictJson.require(scenario.isPresent()&&scenarioReadWrites==0&&readAckLoss==ReadAckLoss.UNBOUND
                    &&malformedReadResult==MalformedReadResult.UNBOUND,
                    "one scenario READ loss may be bound once before any scenario READ write");
            readAckLoss=ReadAckLoss.ARMED;
        }
        synchronized void releaseLateReadAck() throws IOException {
            StrictJson.require(readAckLoss==ReadAckLoss.HELD&&retainedReadAck!=null,
                    "late READ release requires the original retained ACK and actual receive failure, exactly once");
            queue.addFirst(retainedReadAck); retainedReadAck=null; readAckLoss=ReadAckLoss.RELEASED;
        }
        synchronized void loseActionAckOnce()throws IOException {
            StrictJson.require(!actionScenarios.isEmpty()&&!loseAck&&actionWrites==0&&actionAckLoss==ActionAckLoss.UNBOUND,
                    "one explicit scenario ACTION receive loss requires normal write completion, once before action writes");
            actionAckLoss=ActionAckLoss.ARMED;
        }
        synchronized void releaseLateActionAck()throws IOException {
            StrictJson.require(actionAckLoss==ActionAckLoss.HELD&&retainedActionAck!=null,
                    "late ACTION release requires its actual retained ACK after receive failure, exactly once");
            queue.addFirst(retainedActionAck);retainedActionAck=null;actionAckLoss=ActionAckLoss.RELEASED;
        }
        synchronized void rejectNextScenarioReadAfter(int completedScenarioReads) throws IOException {
            StrictJson.require(scenario.isPresent()&&scenarioReadWrites==0&&readRejection==ReadRejection.UNBOUND
                    &&malformedReadResult==MalformedReadResult.UNBOUND&&completedScenarioReads>=0&&completedScenarioReads<=8,
                    "one scenario READ rejection may be bound once before any scenario READ write");
            rejectedReadOccurrence=completedScenarioReads+1;
            readRejection=ReadRejection.ARMED;
        }
        synchronized void rejectNextScenarioReadAsStale() throws IOException {
            rejectNextScenarioReadAfter(0);
            readRejectionKind=ReadRejectionKind.STALE_REVISION;
        }
        synchronized void malformedNextScenarioReadResultAfter(int completedScenarioReads) throws IOException {
            StrictJson.require(scenario.isPresent()&&scenarioReadWrites==0&&malformedReadResult==MalformedReadResult.UNBOUND
                    &&readAckLoss==ReadAckLoss.UNBOUND&&readRejection==ReadRejection.UNBOUND
                    &&completedScenarioReads>=0&&completedScenarioReads<=8,
                    "one malformed scenario result requires one bounded otherwise normal actual READ occurrence");
            malformedReadOccurrence=completedScenarioReads+1;
            malformedReadResult=MalformedReadResult.ARMED;
        }
        synchronized void enqueue(byte[] originalPacket) throws IOException {
            byte[] measured = java.util.Objects.requireNonNull(originalPacket).clone();
            NativeWire.Frame frame = NativeWire.decode(measured);
            StrictJson.require(frame instanceof NativeWire.Snapshot, "a software state source may only enqueue an original snapshot packet");
            NativeWire.Snapshot previous = (NativeWire.Snapshot) NativeWire.decode(latestSnapshot);
            StrictJson.require(((NativeWire.Snapshot) frame).revision().compareTo(previous.revision()) >= 0, "software raw snapshot regressed");
            queue.addLast(heartbeat((NativeWire.Snapshot) frame)); queue.addLast(measured);
        }
        /** Controlled source publication: mailbox facts come from the same original raw snapshot, never from SEM or a fabricated guard. */
        private byte[] heartbeat(NativeWire.Snapshot snapshot) throws IOException {
            var state = NativeWire.object(NativeWire.parse(snapshot.state().value()));
            StrictJson.require(state.get("paused") != null && state.get("paused").isBoolean(), "original software paused boolean required");
            BigInteger date = NativeWire.integer(state.get("date_raw"), BigInteger.ZERO, StrictJson.UINT64_MAX);
            noticeSequence = noticeSequence.add(BigInteger.ONE);
            StrictJson.require(noticeSequence.compareTo(StrictJson.UINT64_MAX.subtract(BigInteger.valueOf(8))) <= 0, "software heartbeat counter exhausted");
            var body = StrictJson.object(); body.put("type", "heartbeat").put("protocol_version", 1).put("pid", 42);
            body.put("monotonic_ms", noticeSequence); body.put("sequence", noticeSequence);
            body.put("startup_failure_containment_enabled", false).put("startup_particle2_stage_recorder_enabled", false);
            var mailbox = body.putObject("main_thread_query_mailbox_v1");
            mailbox.put("installed", true).put("stop", false).put("failure", 0).put("ready", true).put("executor_submission_enabled", true);
            mailbox.put("date_raw", date); mailbox.put("paused", state.get("paused").booleanValue()); mailbox.put("pump_epochs", noticeSequence.add(BigInteger.valueOf(8)));
            return NativeWire.packet(StrictJson.canonical(body));
        }
        @Override public synchronized byte[] readPacket(Instant deadline) throws IOException {
            packetReads++;
            if(actionAckLoss==ActionAckLoss.AWAITING_READ_FAILURE) {
                actionAckLoss=ActionAckLoss.HELD;
                throw new IOException("controlled scenario ACTION write completed; original ACK retained after receive failure");
            }
            if(readAckLoss==ReadAckLoss.AWAITING_READ_FAILURE) {
                readAckLoss=ReadAckLoss.HELD;
                throw new IOException("controlled scenario READ write completed; original ACK retained after receive failure");
            }
            if (queue.isEmpty()) {
                queue.addLast(heartbeat((NativeWire.Snapshot) NativeWire.decode(latestSnapshot)));
                queue.addLast(latestSnapshot.clone());
            }
            byte[] actual = queue.removeFirst().clone();
            if (NativeWire.decode(actual) instanceof NativeWire.Snapshot snapshot) {
                NativeWire.Snapshot previous = (NativeWire.Snapshot) NativeWire.decode(latestSnapshot);
                StrictJson.require(snapshot.revision().compareTo(previous.revision()) >= 0, "software source publication regressed");
                latestSnapshot = actual.clone();
            }
            return actual;
        }
        @Override public synchronized void writePacket(byte[] original, Instant deadline) throws IOException {
            var request = NativeWire.parse(Arrays.copyOfRange(original, 4, original.length)); String step = NativeWire.text(request.get("step"));
            var wire=NativeWire.decodeExecuteRequest(original);var fields=new RawJson(wire.normalizedAdditionalFields().value());
            List<SoftwareActionScenario> matchingActions=actionScenarios.values().stream().filter(candidate->{
                Optional<String> capability=candidate.privatePermission().isPresent()?Optional.empty():Optional.of(candidate.requiredCapability());
                return NativeStepDiscriminator.matchesRequest(candidate.operation(),ExecutableStepBindings.Kind.ACTION,new NativeRequest(step,capability,fields));
            }).toList();
            StrictJson.require(matchingActions.size()<=1,"one actual original software action selector required");
            SoftwareActionScenario selectedAction=matchingActions.isEmpty()?null:matchingActions.getFirst();
            Optional<String> defaultCapability=action.equals(COUNCIL)?Optional.empty():Optional.of("game.command.pause-map");
            boolean mutation=selectedAction!=null||actionScenarios.isEmpty()&&NativeStepDiscriminator.matchesRequest(action,ExecutableStepBindings.Kind.ACTION,new NativeRequest(step,defaultCapability,fields));
            boolean continuation=step.equals(Stage.HELPER_STATUS.step());
            RawJson extraResult = null; boolean scenarioRead=false;
            if (mutation) actionWrites++; else if (continuation) continuationWrites++; else if (step.equals(QUERY.value())) readWrites++;
            else {
                RootReadContractCatalog catalog=java.util.Objects.requireNonNull(issuedReadCatalog.get(),"actual read catalog not installed");
                GuardedRead actual=guardedRead.get();guardedRead.remove();
                StrictJson.require(actual!=null,"scenario READ has no original guard-verified contract on this submitting thread");
                ReadContract<?> installed=actual.contract();
                StrictJson.require(catalog.containsIdentity(installed)&&actual.request().operation().equals(installed.operation())
                        &&actual.guard().guardMode()==installed.guardMode(),"READ lost its exact original guarded catalog identity");
                var actualRequest = new NativeRequest(step, installed.requiredCapability(), fields);
                NativeStepDiscriminator.requireRequest(installed.operation(),ExecutableStepBindings.Kind.READ,actualRequest);
                BigInteger revision=actual.request().origin().expectedRevision();
                switch(installed.wireProfile()) {
                    case SNAPSHOT_REVISION_ONLY -> StrictJson.require(wire.expectedSnapshotRevision().equals(Optional.of(revision))&&wire.expectedRevision().isEmpty(),"READ snapshot revision differs from the original guarded request");
                    case COUNCIL_MAILBOX_STATUS -> StrictJson.require(wire.expectedRevision().isEmpty()&&wire.expectedSnapshotRevision().isEmpty(),"original Council READ cannot acquire a revision field");
                    case EXECUTE_STEP,G2_PRIVATE_QUERY -> StrictJson.require(wire.expectedRevision().equals(Optional.of(revision))&&wire.expectedSnapshotRevision().isEmpty(),"READ native revision differs from the original guarded request");
                }
                // The actual transport already matches prepared bytes/capability to its private consumed ReadPermit.
                // Do not prepare again, guess a last-issued contract, or choose by step/argument similarity.
                extraResult = java.util.Objects.requireNonNull(scenario.orElseThrow().result().apply(actualRequest));
                extraResult.objectFieldNames(); readWrites++; scenarioReadWrites++; scenarioRead=true;
            }
            if (mutation && selectedAction != null) selectedAction.originalDispatch().run();
            if (mutation && selectedAction != null && selectedAction.originalResult().isPresent()) {
                extraResult = java.util.Objects.requireNonNull(selectedAction.originalResult().orElseThrow().get()); extraResult.objectFieldNames();
            }
            if (mutation && loseAck) throw new IOException("controlled write entered; ACK unavailable");
            String result = extraResult != null ? new String(extraResult.bytes(), StandardCharsets.UTF_8) : mutation && action.equals(COUNCIL) || continuation ? "{\"private_council_transport\":true,\"advertised\":false,\"status\":\"pending\"}" : "{\"actual_status\":\"retained\"}";
            if(scenarioRead&&malformedReadResult==MalformedReadResult.ARMED&&scenarioReadWrites==malformedReadOccurrence) {
                malformedReadResult=MalformedReadResult.PRODUCED;
                result="[]";
            }
            String response = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + NativeWire.text(request.get("request_id")) + "\",\"ok\":true,\"result\":" + result + "}";
            if(scenarioRead&&readRejection==ReadRejection.ARMED&&scenarioReadWrites==rejectedReadOccurrence) {
                readRejection=ReadRejection.REJECTED;
                String rejection=readRejectionKind==ReadRejectionKind.STALE_REVISION
                        ? "nonwar private snapshot revision is stale or malformed" : "controlled scenario READ rejected";
                response="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+NativeWire.text(request.get("request_id"))
                        +"\",\"ok\":false,\"error\":\""+rejection+"\"}";
            }
            if (continuation && loseContinuationAck) { lostResult = response; throw new IOException("controlled continuation write entered; ACK unavailable"); }
            byte[] originalAck=packet(response);
            if(scenarioRead&&readAckLoss==ReadAckLoss.ARMED) {
                retainedReadAck=originalAck; readAckLoss=ReadAckLoss.AWAITING_READ_FAILURE;
                return; // Real transport records writeCompleted before its subsequent receive fails.
            }
            if(mutation&&selectedAction!=null&&actionAckLoss==ActionAckLoss.ARMED) {
                retainedActionAck=originalAck;actionAckLoss=ActionAckLoss.AWAITING_READ_FAILURE;
                return; // The actual transport records writeCompleted before the original receive fails.
            }
            queue.addFirst(originalAck);
        }
        @Override public void close() { guardedRead.remove(); }
    }
    @Override public void close() throws IOException { transport.close(); }
}



