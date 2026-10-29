package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.ServiceLoader;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.LongSupplier;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.driver.DriverCapabilityRuntime;
import org.xar.ck3.control.application.driver.DriverPublicPlanningInputsAssertions;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicPlanningRpcAssertions;
import org.xar.ck3.control.service.mcp.PublicPlanningRpcAssertions.Consumer;
import org.xar.ck3.control.service.mcp.PublicPlanningRpcAssertions.ExpectedFailure;
import org.xar.ck3.control.service.mcp.RootPublicPlanPresentation;

/**
 * Actual registered producer -> complete ordinary planner -> public boundary.
 * A provider must open the real installed Root/software Native source and original Python oracle.
 * These tests do not construct a Source, Managed, Ready, replacement observation or expected public plan.
 * Missing actual providers and unfinished branch producers fail as NOT_RUN, never skip.
 */
public final class RootPublicPlanningUnionActualTest {
    public enum Scenario {
        READY, RUNNING, DEAD_SAME_ACTOR, PENDING_UNKNOWN, ORDINARY_GATE_WAITING,
        CHANGED_PLAYER, MISSING_PLAYER, NATIVE_CAMPAIGN_TERMINAL, CHANGED_STALE_EXPECTATION, CHANGED_FRESH_BINDING_DIFFERS, GENERIC_EXECUTE_OBSERVED,
        RETRY_HEIR_PRECONDITION, RETRY_LOCAL_REVISION, RETRY_EXECUTOR_NOT_ENTERED,
        RETRY_PREFLIGHT_REVISION, RETRY_PREFLIGHT_SNAPSHOT, RETRY_FACTION_PENDING,
        NONRETRY_UNKNOWN_ACTION, RETRY_SECOND_FAILURE
    }
    public record OriginalOracle(RawJson output, ExactRef service, ExactRef strategy, ExactRef retry) {
        public OriginalOracle {
            Objects.requireNonNull(output); Objects.requireNonNull(service);
            Objects.requireNonNull(strategy); Objects.requireNonNull(retry);
        }
    }
    public record CapabilityOracle(ExactRef nativeDriverSource, ExactRef actualInput, ExactRef actualOutput) {
        public CapabilityOracle { Objects.requireNonNull(nativeDriverSource);Objects.requireNonNull(actualInput);Objects.requireNonNull(actualOutput); }
    }
    public record CapabilityOriginals(DriverStateAssembler authority, DriverCapabilityRuntime runtime,
            RootExecutableBindings bindings, ActionPorts.OutcomeArchive archive, CapabilityOracle oracle) {
        public CapabilityOriginals { Objects.requireNonNull(authority); Objects.requireNonNull(runtime);
            Objects.requireNonNull(bindings); Objects.requireNonNull(archive); Objects.requireNonNull(oracle); }
    }
    public record SuccessionMetrics(LongSupplier rootQueries, LongSupplier retainedReconciliations,
            LongSupplier publicCaptures) {
        public SuccessionMetrics { Objects.requireNonNull(rootQueries);Objects.requireNonNull(retainedReconciliations);
            Objects.requireNonNull(publicCaptures); }
    }
    public record Inputs(RootInstalledCatalog catalog, PublicBindings registry, RawJson originalArguments,
            Instant deadline, Optional<OriginalOracle> oracle, Optional<ExpectedFailure> originalFailure,
            CapabilityOriginals capabilities, SuccessionMetrics successionMetrics,
            LongSupplier businessPackets, LongSupplier readyPublications, LongSupplier planningAttempts) {
        public Inputs {
            Objects.requireNonNull(catalog); Objects.requireNonNull(registry); Objects.requireNonNull(originalArguments);
            Objects.requireNonNull(capabilities); Objects.requireNonNull(successionMetrics);
            Objects.requireNonNull(deadline); Objects.requireNonNull(oracle); Objects.requireNonNull(originalFailure);
            Objects.requireNonNull(businessPackets); Objects.requireNonNull(readyPublications); Objects.requireNonNull(planningAttempts);
            assertTrue(oracle.isPresent() ^ originalFailure.isPresent(), "one actual original outcome required");
        }
    }
    /** Each transport/scenario opens a fresh genuine fixture. EXECUTE is never replayed for transport coverage. */
    public interface InputsProducer { Inputs open(Scenario scenario, Consumer consumer) throws Exception; }

    private static Inputs actual(Scenario scenario, Consumer consumer) throws Exception {
        var providers = ServiceLoader.load(InputsProducer.class).stream().toList();
        if (providers.size() != 1)
            throw new IllegalStateException("MISSING_ACTUAL_PUBLIC_PLANNING_UNION_INPUTS_NOT_RUN: " + scenario + "/" + consumer);
        Inputs input = Objects.requireNonNull(providers.getFirst().get().open(scenario, consumer));
        assertInstanceOf(RootApplicationSession.class, input.catalog().context().actions());
        if (scenario == Scenario.GENERIC_EXECUTE_OBSERVED)
            assertEquals(PublicPlanningCodec.ExecuteRequest.class,
                    input.registry().lookup(PublicMethod.EXECUTE_STEP).orElseThrow().requestType());
        else
            assertEquals(PublicPlanningCodec.PlanRequest.class,
                    input.registry().lookup(PublicMethod.PLAN_TURN).orElseThrow().requestType());
        if (input.oracle().isPresent()) {
            OriginalOracle oracle = input.oracle().orElseThrow();
            source(oracle.service(), "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e");
            source(oracle.strategy(), "52b4381758ee712dc8555ac3a31186e13adbe10c3c18dc93b23bca5147934111");
            source(oracle.retry(), "a761179ca74f576950cdeda76649af9f39d8f1c831af21941753b622696cb24f");
        }
        return input;
    }
    private static void source(ExactRef actual, String expected) throws Exception {
        byte[] bytes = Files.readAllBytes(Path.of(actual.path()));
        assertEquals(actual.bytes(), bytes.length);
        assertEquals(expected, actual.sha256());
        assertEquals(actual.sha256(), DriverJson.sha256(bytes));
    }
    private static RootApplicationSession root(Inputs input) {
        return assertInstanceOf(RootApplicationSession.class, input.catalog().context().actions());
    }
    private static OpportunityJson.Obj object(RawJson value) {
        return DriverJson.object(value.bytes(), RawJson.MAXIMUM_BYTES);
    }
    private static void registered(Inputs input, Scenario scenario, Consumer consumer) throws Exception {
        String name = scenario == Scenario.GENERIC_EXECUTE_OBSERVED ? "ck3_execute_step" : "ck3_plan_turn";
        String arguments = new String(input.originalArguments().bytes(), java.nio.charset.StandardCharsets.UTF_8);
        if (input.oracle().isPresent()) {
            RawJson original = input.oracle().orElseThrow().output();
            PublicPlanningRpcAssertions.assertRegisteredResult(consumer, input.registry(), name, arguments, original);
            if (scenario != Scenario.GENERIC_EXECUTE_OBSERVED)
                assertEquals(object(original), RootPublicPlanPresentation.decode(original).original());
        } else PublicPlanningRpcAssertions.assertRegisteredFailure(consumer, input.registry(), name, arguments,
                input.originalFailure().orElseThrow());
    }
    /** Compare actual old Native candidates after the same installed metadata filter; never accept an empty expected fallback. */
    private static void capabilityOracle(Inputs input, NativeReadinessCollector.PublicPlanningObservation observed,
            java.util.Set<org.xar.ck3.control.application.action.OperationKey> actualSteps,
            java.util.Set<String> actualBridge, boolean terminal) throws Exception {
        var originals=input.capabilities().oracle();
        source(originals.nativeDriverSource(),"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
        source(originals.actualInput(),originals.actualInput().sha256());
        source(originals.actualOutput(),originals.actualOutput().sha256());
        var nativeInput=DriverJson.object(Files.readAllBytes(Path.of(originals.actualInput().path())),RawJson.MAXIMUM_BYTES);
        assertEquals(observed.frame().snapshot().semantic(),nativeInput.get("snapshot"));
        assertEquals(DriverJson.object(observed.frame().driver().driver().encode(),RawJson.MAXIMUM_BYTES),nativeInput.get("driver"));
        assertEquals(observed.frame().receivedCapabilities().orElseThrow(),nativeInput.get("received_capabilities"));
        var nativeView=DriverJson.object(Files.readAllBytes(Path.of(originals.actualOutput().path())),RawJson.MAXIMUM_BYTES);
        var diagnostics=OpportunityJson.object(observed.frame().receivedCapabilities().orElseThrow().get("diagnostics"),"actual diagnostics");
        var hello=OpportunityJson.object(diagnostics.get("hello"),"actual HELLO");
        java.util.Set<String> bridge=new java.util.TreeSet<>();
        for(var value:OpportunityJson.array(hello.get("capabilities"),"actual HELLO capabilities"))
            bridge.add(OpportunityJson.text(value,"capability"));
        assertEquals(bridge,actualBridge);
        java.util.Set<org.xar.ck3.control.application.action.OperationKey> expected=new java.util.HashSet<>();
        for(var value:OpportunityJson.array(nativeView.get("action_steps"),"original Native action_steps")) {
            String step=OpportunityJson.text(value,"original Native step");
            if(terminal&&!java.util.Set.of("death-terminal","start-next-episode","continue-as-reconciled-successor").contains(step))continue;
            var key=new org.xar.ck3.control.application.action.OperationKey(step);
            var metadata=input.capabilities().bindings().describeForPublicPlanning(key);
            if(metadata.isEmpty())continue;
            var descriptor=metadata.orElseThrow().descriptor();
            if(descriptor.requiredCapability().filter(required->!bridge.contains(required)).isPresent())continue;
            assertEquals(key,descriptor.operation());
            // The actual DC producer/helper verifies these source pins through its real archive/scope.
            assertTrue(descriptor.implementationSource().bytes()>0 && descriptor.decoderSource().bytes()>0);
            expected.add(key);
        }
        assertEquals(expected,actualSteps,"actual old Native candidates and installed filtering must match exactly");
    }

    private static void completeBranch(Scenario scenario) throws Exception {
        for (Consumer consumer : Consumer.values()) {
            Inputs input = actual(scenario, consumer);
            long business = input.businessPackets().getAsLong();
            long publications = input.readyPublications().getAsLong();
            AtomicReference<NativeReadinessCollector.PublicPlanningObservation> retained = new AtomicReference<>();
            AtomicReference<DriverPublicPlanningInputsAssertions.RetainedScope> capabilityScope = new AtomicReference<>();
            root(input).withPublicPlanning(input.deadline(), (observed, same) -> {
                retained.set(observed); observed.assertCurrent(same);
                Complete complete = assertInstanceOf(Complete.class, observed.frame().joined());
                assertEquals(complete.semantic(), observed.frame().snapshot().semantic());
                if (scenario == Scenario.READY) {
                    var ready = assertInstanceOf(NativeReadinessCollector.PublicReady.class, observed);
                    assertSame(ready.ready().request(), RootPlanningInputsFactory.publicRequest(observed, same, input.deadline()));
                } else {
                    assertInstanceOf(NativeReadinessCollector.PublicObserved.class, observed);
                    PlanningRequest request = RootPlanningInputsFactory.publicRequest(observed, same, input.deadline());
                    assertEquals(complete.identity(), request.before());
                    assertEquals(complete.source(), request.source());
                    assertEquals(complete.sessionId(), request.sessionId());
                    assertEquals(complete.semantic(), request.observations().snapshot());
                    var actualHistory = observed.frame().driver().driver().commandHistory().stream()
                            .map(row -> DriverJson.object(row.originalRow().json(), DriverJson.MAX_NATIVE_BYTES)).toList();
                    assertEquals(actualHistory, request.observations().history());
                    assertTrue(request.observations().crossRunPlan().isPresent(), "actual state body is mandatory, including an empty episode history");
                    if (observed.frame().ordinarySemantic().isEmpty()) {
                        var caps = input.capabilities();
                        try { capabilityScope.set(DriverPublicPlanningInputsAssertions.assertActualRawInputs(
                                caps.authority(), caps.runtime(), caps.bindings(), same, complete,
                                observed.frame().driver(), observed.frame().receivedCapabilities().orElseThrow(), input.deadline())); }
                        catch (Exception failure) { throw new java.io.IOException("actual raw capability producer assertion failed", failure); }
                    }
                    try { capabilityOracle(input,observed,request.observations().actionSteps(),
                            request.observations().bridgeCapabilities(),false); }
                    catch (Exception failure) { throw new java.io.IOException("actual Native capability differential oracle failed",failure); }
                    if (scenario == Scenario.RUNNING) assertFalse(request.observations().paused());
                    if (scenario == Scenario.DEAD_SAME_ACTOR) {
                        var player = OpportunityJson.object(complete.semantic().get("played_character"), "played_character");
                        assertEquals(new OpportunityJson.Bool(false), player.get("alive"));
                    }
                    if (scenario == Scenario.PENDING_UNKNOWN) {
                        assertInstanceOf(DriverStateSnapshot.Incomplete.class, observed.frame().canonicalDriver());
                        assertTrue(request.observations().actionFacts().stream().anyMatch(value -> value.unresolved()));
                    }
                    if (scenario == Scenario.ORDINARY_GATE_WAITING)
                        assertTrue(observed.frame().ordinarySemantic().isPresent(), "ordinary Waiting must retain its actual ordinary source");
                }
                observed.assertCurrent(same); return null;
            });
            if (capabilityScope.get() != null) DriverPublicPlanningInputsAssertions.assertEscaped(capabilityScope.get());
            // The retained DATA cannot acquire a new source or open an old callback.
            root(input).withPublicStandaloneRead(input.deadline(), same -> {
                assertThrows(Exception.class, () -> retained.get().assertCurrent(same));
                assertThrows(Exception.class, () -> RootPlanningInputsFactory.publicRequest(retained.get(), same, input.deadline()));
                return null;
            });
            registered(input, scenario, consumer);
            assertEquals(business, input.businessPackets().getAsLong(), "PLAN never submits a world action");
            if (scenario != Scenario.READY)
                assertEquals(publications, input.readyPublications().getAsLong(), "Observed cannot publish M7 Ready");
        }
    }
    @Test void actualReadyRetainsOriginalRequestAndWholeOrdinaryPipeline() throws Exception { completeBranch(Scenario.READY); }
    @Test void actualRunningUsesRealPublicInputsAndOriginalPublicPlan() throws Exception { completeBranch(Scenario.RUNNING); }
    @Test void actualDeadSameActorUsesTerminalBranchWithoutReadyOrSyntheticActor() throws Exception { completeBranch(Scenario.DEAD_SAME_ACTOR); }
    @Test void actualPendingUnknownPreservesCanonicalFactsAndZeroReplay() throws Exception { completeBranch(Scenario.PENDING_UNKNOWN); }
    @Test void actualOrdinaryWaitingKeepsOriginalCapabilityScope() throws Exception { completeBranch(Scenario.ORDINARY_GATE_WAITING); }

    @Test void actualPartialPlayerJoinMustUseOriginalPreflightWithoutRequest() throws Exception {
        for (Scenario scenario : List.of(Scenario.CHANGED_PLAYER, Scenario.MISSING_PLAYER))
            for (Consumer consumer : Consumer.values()) {
                Inputs input = actual(scenario, consumer);
                long business = input.businessPackets().getAsLong(), publications = input.readyPublications().getAsLong();
                AtomicReference<DriverPublicPlanningInputsAssertions.RetainedTerminalScope> retained = new AtomicReference<>();
                root(input).withPublicPlanning(input.deadline(), (observed, same) -> {
                    assertInstanceOf(NativeReadinessCollector.PublicObserved.class, observed);
                    assertFalse(observed.frame().joined() instanceof Complete);
                    assertThrows(Exception.class, () -> RootPlanningInputsFactory.publicRequest(observed, same, input.deadline()));
                    var actualTerminal = RootPlanningInputsFactory.publicTerminalInputs(observed, same, input.deadline());
                    assertEquals(observed.frame().snapshot().semantic(), actualTerminal.snapshot());
                    try { capabilityOracle(input,observed,actualTerminal.actionSteps(),actualTerminal.bridgeCapabilities(),true); }
                    catch (Exception failure) { throw new java.io.IOException("actual terminal Native capability differential oracle failed",failure); }
                    var caps = input.capabilities();
                    try { retained.set(DriverPublicPlanningInputsAssertions.assertActualTerminalInputs(
                            caps.authority(), caps.runtime(), caps.bindings(), same, observed.frame().snapshot(),
                            observed.frame().driver(), observed.frame().receivedCapabilities().orElseThrow(),
                            input.deadline(), caps.archive())); }
                    catch (Exception failure) { throw new java.io.IOException("actual terminal capability producer assertion failed", failure); }
                    return null;
                });
                DriverPublicPlanningInputsAssertions.assertEscapedTerminal(retained.get());
                registered(input, scenario, consumer); // Must match original producer DATA/fault, not a guessed Waiting.
                assertEquals(business, input.businessPackets().getAsLong());
                assertEquals(publications, input.readyPublications().getAsLong());
            }
    }
    @Test void actualNativeCampaignTerminalUsesItsPrivateConstructorSourceAndPreservesPublicNull() throws Exception {
        for (Consumer consumer : Consumer.values()) {
            Inputs input=actual(Scenario.NATIVE_CAMPAIGN_TERMINAL,consumer);
            long business=input.businessPackets().getAsLong(),ready=input.readyPublications().getAsLong();
            root(input).withPublicPlanning(input.deadline(),(observed,same)->{
                assertInstanceOf(NativeReadinessCollector.PublicObserved.class,observed);
                assertEquals(OpportunityJson.Nil.INSTANCE,observed.frame().snapshot().semantic().get("succession_lifecycle"),
                        "actual native_campaign public snapshot is not overwritten by the private legacy capability variant");
                var caps=input.capabilities();
                try {
                    DriverPublicPlanningInputsAssertions.assertActualConstructorSource(caps.runtime(),caps.authority(),
                            caps.bindings(),caps.archive(),same,observed.frame().snapshot(),observed.frame().driver());
                    var terminal=RootPlanningInputsFactory.publicTerminalInputs(observed,same,input.deadline());
                    capabilityOracle(input,observed,terminal.actionSteps(),terminal.bridgeCapabilities(),true);
                } catch(Exception failure) {
                    throw new java.io.IOException("actual native_campaign constructor/terminal original oracle assertion failed",failure);
                }
                observed.assertCurrent(same);return null;
            });
            registered(input,Scenario.NATIVE_CAMPAIGN_TERMINAL,consumer);
            assertEquals(business,input.businessPackets().getAsLong());
            assertEquals(ready,input.readyPublications().getAsLong());
        }
    }
    @Test void actualChangedStaleExpectationReadsReconcilesAndUsesExactlyOneFreshPublicFrame() throws Exception {
        for (Scenario scenario : List.of(Scenario.CHANGED_STALE_EXPECTATION, Scenario.CHANGED_FRESH_BINDING_DIFFERS))
            for (Consumer consumer : Consumer.values()) {
                // Both genuine fixtures have an actual retained expectation and no reusable current ROOT result.
                Inputs input=actual(scenario,consumer);
                var metrics=input.successionMetrics();
                long world=input.businessPackets().getAsLong(),ready=input.readyPublications().getAsLong();
                long queries=metrics.rootQueries().getAsLong(),reconciles=metrics.retainedReconciliations().getAsLong();
                long captures=metrics.publicCaptures().getAsLong();
                registered(input,scenario,consumer);
                assertEquals(1,metrics.rootQueries().getAsLong()-queries,"one actual lifecycle ROOT query");
                assertEquals(1,metrics.retainedReconciliations().getAsLong()-reconciles,"sole actual Driver reconciliation");
                assertEquals(2,metrics.publicCaptures().getAsLong()-captures,"old capture exits before one new real frame");
                assertEquals(world,input.businessPackets().getAsLong(),"preflight issues no Game mutation");
                assertEquals(ready,input.readyPublications().getAsLong(),"changed terminal does not become Ready");
                var expected=object(input.oracle().orElseThrow().output());
                assertFalse(expected.members().containsKey("readonly_planning_replan_v1"),
                        "normal reconciliation refresh is not a failed-read retry");
                if(scenario==Scenario.CHANGED_FRESH_BINDING_DIFFERS) {
                    var plan=OpportunityJson.object(expected.get("plan"),"actual original plan");
                    assertNotEquals(new OpportunityJson.Text("continue-as-reconciled-successor"),plan.get("selected_step"),
                            "fresh tuple differences withhold continuation and keep original DATA/HOLD");
                }
            }
    }

    @Test void actualObservedGenericExecuteUsesItsOwnGenuineEntryOncePerFixture() throws Exception {
        for (Consumer consumer : Consumer.values()) {
            Inputs input = actual(Scenario.GENERIC_EXECUTE_OBSERVED, consumer);
            long business = input.businessPackets().getAsLong();
            registered(input, Scenario.GENERIC_EXECUTE_OBSERVED, consumer);
            assertEquals(business, input.businessPackets().getAsLong(), "selected readonly original step submits no business action");
        }
    }
    @Test void actualReadonlyRetryRequiresOriginalPrivateProofAndOneFreshWholePlan() throws Exception {
        for (Scenario scenario : List.of(Scenario.RETRY_HEIR_PRECONDITION, Scenario.RETRY_LOCAL_REVISION,
                Scenario.RETRY_EXECUTOR_NOT_ENTERED, Scenario.RETRY_PREFLIGHT_REVISION,
                Scenario.RETRY_PREFLIGHT_SNAPSHOT, Scenario.RETRY_FACTION_PENDING))
            for (Consumer consumer : Consumer.values()) {
                Inputs input = actual(scenario, consumer);
                long business = input.businessPackets().getAsLong(), attempts = input.planningAttempts().getAsLong();
                registered(input, scenario, consumer);
                assertEquals(2, input.planningAttempts().getAsLong() - attempts);
                assertEquals(business, input.businessPackets().getAsLong(), "retry never executes or replays a plan");
                var marker = OpportunityJson.object(object(input.oracle().orElseThrow().output()).get("readonly_planning_replan_v1"), "retry marker");
                assertEquals(new OpportunityJson.IntegerValue(BigInteger.ONE), marker.get("fresh_replans"));
                assertEquals(new OpportunityJson.IntegerValue(BigInteger.ZERO), marker.get("business_actions_replayed"));
            }
    }
    @Test void actualUnknownAndSecondFailureCannotBorrowAnotherRetryBudget() throws Exception {
        for (Scenario scenario : List.of(Scenario.NONRETRY_UNKNOWN_ACTION, Scenario.RETRY_SECOND_FAILURE))
            for (Consumer consumer : Consumer.values()) {
                Inputs input = actual(scenario, consumer);
                assertTrue(input.originalFailure().isPresent());
                long business = input.businessPackets().getAsLong(), attempts = input.planningAttempts().getAsLong();
                registered(input, scenario, consumer);
                assertEquals(scenario == Scenario.RETRY_SECOND_FAILURE ? 2 : 1,
                        input.planningAttempts().getAsLong() - attempts);
                assertEquals(business, input.businessPackets().getAsLong());
            }
    }
}
