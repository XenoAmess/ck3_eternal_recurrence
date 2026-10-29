package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic.Kind;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastCodec;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.application.planning.governance.FeastObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Production factories, decision branch and strict decoders; explicit unit I/O doubles grant no native qualification. */
final class OrdinaryGovernanceFactoriesTest {
    static PlanningRequest feastRequest() {
        var original = request(); var old = original.observations(); var actions = new HashSet<>(old.actionSteps());
        actions.addAll(OrdinaryFeastPolicy.OWNED);
        var observation = new PlanningObservation(old.snapshot(), old.history(), actions, old.bridgeCapabilities(), old.battleSpeedReadiness(),
                old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), old.initialLifestyleFocusRequired());
        return new PlanningRequest(original.before(), original.source(), original.sessionId(), original.deadline(), observation);
    }
    private static Optional<ExpectedPostcondition> unitExpected(OperationKey operation, PlanningRequest request, Obj arguments) {
        return Optional.of(new ExpectedPostcondition(1, request.before(), request.source(), "unit-feast/v1",
                List.of(new ExpectedBoolean(new FieldKey("unit.feast_poststate"), true))));
    }
    private static final class Feasts implements FeastObservationSupplier {
        State state; Planner planner = new Planner(Kind.ABSENT, new Obj(java.util.Map.of())); Hosted hosted;
        Obj root = new Obj(java.util.Map.of()).with("capital_province_id", n(123)); int plannerReads; int budgetReads;
        ActivityConfigurationModels.Frame frame; boolean confirmReady = true; boolean destinationLegal = true;
        Feasts(PlanningRequest request) {
            var identity = request.before().frame().identity();
            frame = new ActivityConfigurationModels.Frame(identity.nativeRevision(), identity.dateRaw(), identity.player());
            state = new State(request.before(), request.sessionId(), CadenceModels.State.empty(request.before().frame().episodeRunId()),
                    Optional.empty(), Optional.empty(), List.of(), new Obj(java.util.Map.of()));
            hosted = new Hosted(request.before().frame().identity().player(), HostedFeastCodec.decode(encode(new Arr(List.of()))), new Obj(java.util.Map.of()));
        }
        @Override public Read<State> state(PlanningRequest request) { return new Known<>(state, List.of(REF)); }
        @Override public Read<Planner> planner(PlanningRequest request) { plannerReads++; return new Known<>(planner, List.of(REF)); }
        @Override public Read<Hosted> hosted(PlanningRequest request) { return new Known<>(hosted, List.of(REF)); }
        @Override public Read<Obj> root(PlanningRequest request) { return new Known<>(root, List.of(REF)); }
        @Override public Read<OrdinaryFinanceCollector.Spending> spending(PlanningRequest request) {
            budgetReads++; return new Unavailable<>("unit input absent; no synthetic spending/market observation");
        }
        @Override public Read<OrdinaryFinanceCollector.Feast> feast(PlanningRequest request, OrdinaryFinanceCollector.Spending spending) {
            return new Unavailable<>("unit actual stage5 inputs absent");
        }
        @Override public Read<ActivityConfigurationModels.StageOne> stageOne(PlanningRequest request) {
            return new Known<>(new ActivityConfigurationModels.StageOne(frame, confirmReady, true, true, confirmReady, new Obj(java.util.Map.of())), List.of(REF));
        }
        @Override public Read<ActivityConfigurationModels.StageTwo> stageTwo(PlanningRequest request) {
            return new Known<>(new ActivityConfigurationModels.StageTwo(frame, true, new Obj(java.util.Map.of())), List.of(REF));
        }
        @Override public Read<ActivityConfigurationModels.Location> location(PlanningRequest request, int provinceId) {
            var rows = List.of(new ActivityConfigurationModels.ConfigurationRow(0, Optional.empty(), 0, true),
                    new ActivityConfigurationModels.ConfigurationRow(1, Optional.empty(), 0, false));
            return new Known<>(new ActivityConfigurationModels.Location(frame, rows, Optional.of(0), true, 1,
                    List.of(new ActivityConfigurationModels.Candidate(provinceId, destinationLegal)), false, new Obj(java.util.Map.of())), List.of(REF));
        }
    }
    @Test void factoryConsumesOriginalCouncilPendingBeforeMissingCapabilitiesCanFallThrough() {
        var base = feastRequest(); var observed = base.observations();
        var request = new PlanningRequest(base.before(), base.source(), base.sessionId(), base.deadline(),
                new PlanningObservation(observed.snapshot(), observed.history(), observed.actionSteps(), java.util.Set.of(),
                        observed.battleSpeedReadiness(), observed.actionFacts(), observed.campaignGoal(),
                        observed.crossRunPlan(), observed.initialLifestyleFocusRequired()));
        var delegated = new GovernanceFixtures.Supplier(request); var old = delegated.state;
        int[] nativeReads = { 0 };
        var factory = new OrdinaryGovernancePolicies(delegated, new GovernanceCouncilSupplier.CouncilReadPort() {
            @Override public Read<CouncilSelection.Query> readPrivate(PlanningRequest current, CouncilSelection.Position position) {
                nativeReads[0]++; throw new AssertionError("pending must not query private candidates");
            }
            @Override public Read<CouncilSelection.Query> readCore(PlanningRequest current) {
                nativeReads[0]++; throw new AssertionError("pending must not query public candidates");
            }
        }, REF, new OrdinaryFeastPolicy(REF, new Feasts(request), OrdinaryGovernanceFactoriesTest::unitExpected));
        for (String episode : List.of(request.before().frame().episodeRunId(), "other-episode")) {
            Obj pending = new Obj(java.util.Map.of()).with("stage", new Text("submission_unresolved"))
                    .with("episode_run_id", new Text(episode)).with("action_request_id", new Text("original-council-request"))
                    .with("pre_native_revision", n(8)).with("pre_date_raw", n(100)).with("action_ack", Nil.INSTANCE);
            Obj body = new Obj(java.util.Map.of()).with("schema", new Text(GovernanceDomainDocument.COUNCIL_SCHEMA))
                    .with("pending", pending).with("applied", Nil.INSTANCE);
            var decoded = GovernanceStateSupplier.decodeLegacyCouncil(request, encode(body));
            assertEquals(episode.equals(request.before().frame().episodeRunId()) ? DomainStatus.PENDING : DomainStatus.UNKNOWN,
                    decoded.status());
            delegated.state = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), Optional.of(decoded), old.crown());
            assertInstanceOf(OrdinaryPolicy.Wait.class, factory.coreCouncil().evaluate(request, OrdinaryPolicy.Draft.empty()));
            assertInstanceOf(OrdinaryPolicy.Wait.class, factory.stages().get(2).evaluate(request, advance(request)));
            assertEquals(0, nativeReads[0]); assertEquals(pending, delegated.state.council().orElseThrow().legacyPending().orElseThrow());
            assertEquals(body, parse(encode(delegated.state.council().orElseThrow().originalBody())));
        }
        Obj clear = new Obj(java.util.Map.of()).with("schema", new Text(GovernanceDomainDocument.COUNCIL_SCHEMA))
                .with("pending", Nil.INSTANCE).with("applied", Nil.INSTANCE);
        var clearState = GovernanceStateSupplier.decodeLegacyCouncil(request, encode(clear));
        delegated.state = new Durable(old.observed(), old.sessionId(), old.cadence(), old.opening(), Optional.of(clearState), old.crown());
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, factory.coreCouncil().evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(0, nativeReads[0]); assertEquals(clear, delegated.state.council().orElseThrow().originalBody());
    }
    @Test void factoryReturnsFiveConcreteDistinctStagesAndBindsTheSameRealCouncilAtCore() {
        var request = feastRequest(); var feast = new OrdinaryFeastPolicy(REF, new Feasts(request), OrdinaryGovernanceFactoriesTest::unitExpected);
        var delegated = new GovernanceFixtures.Supplier(request);
        var factory = new OrdinaryGovernancePolicies(delegated, new GovernanceCouncilSupplier.CouncilReadPort() {
            @Override public Read<CouncilSelection.Query> readPrivate(PlanningRequest current, CouncilSelection.Position position) { return delegated.council(current, position); }
            @Override public Read<CouncilSelection.Query> readCore(PlanningRequest current) { return delegated.coreCouncil(current); }
        }, REF, feast);
        assertEquals(List.of(PlanningStage.OPENING_LIFESTYLE_FOCUS, PlanningStage.LIFESTYLE, PlanningStage.COUNCIL,
                PlanningStage.CROWN_AUTHORITY, PlanningStage.FEAST), factory.stages().stream().map(OrdinaryPolicy::stage).toList());
        assertTrue(factory.stages().getFirst() instanceof GovernancePolicies.Opening);
        assertSame(feast, factory.stages().getLast());
        var core = assertInstanceOf(OrdinaryPolicy.Replace.class, factory.coreCouncil().evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(GovernancePolicies.CORE_COUNCIL, core.draft().command().orElseThrow().operation());
        assertThrows(UnsupportedOperationException.class, () -> factory.stages().clear());
    }
    @Test void absentPlannerSelectsTheRealConfigurationOperationAndDoesNotDependOnMercenaryMarket() {
        var request = feastRequest(); var supplier = new Feasts(request); var policy = new OrdinaryFeastPolicy(REF, supplier, OrdinaryGovernanceFactoriesTest::unitExpected);
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request)));
        var command = selected.draft().command().orElseThrow();
        assertEquals(OrdinaryFeastPolicy.CONFIGURE, command.operation()); assertEquals(new Obj(java.util.Map.of()), command.arguments().get("native_arguments"));
        assertNull(command.arguments().get("resume_stage2")); assertEquals(0, supplier.budgetReads);
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command))); policy.revalidate(command, request);
        supplier.root = supplier.root.with("capital_province_id", n(124));
        assertThrows(IllegalArgumentException.class, () -> policy.revalidate(command, request));
    }
    @Test void stageTwoResumesItsActualConfigurationAndMissingMaterialHandlerCannotProposeAnAction() {
        var request = feastRequest(); var supplier = new Feasts(request); supplier.planner = new Planner(Kind.FEAST_STAGE_TWO, new Obj(java.util.Map.of()));
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class,
                new OrdinaryFeastPolicy(REF, supplier, OrdinaryGovernanceFactoriesTest::unitExpected).evaluate(request, advance(request)));
        assertEquals(OrdinaryFeastPolicy.DESTINATION, selected.draft().command().orElseThrow().operation());
        assertEquals(n(123), object(selected.draft().command().orElseThrow().arguments().get("native_arguments"), "native fields").get("province_id"));
        assertInstanceOf(OrdinaryPolicy.Defer.class, new OrdinaryFeastPolicy(REF, supplier, (operation, fresh, args) -> Optional.empty()).evaluate(request, advance(request)));
    }
    @Test void stageOneSelectsConfirmAndLegalDestinationIsRequiredBeforeStageFive() {
        var request = feastRequest(); var supplier = new Feasts(request);
        var policy = new OrdinaryFeastPolicy(REF, supplier, OrdinaryGovernanceFactoriesTest::unitExpected);
        supplier.planner = new Planner(Kind.FEAST_STAGE_ONE, new Obj(java.util.Map.of()));
        var confirm = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request))).draft().command().orElseThrow();
        assertEquals(OrdinaryFeastPolicy.CONFIRM, confirm.operation()); policy.revalidate(confirm, request);
        supplier.confirmReady = false;
        assertInstanceOf(OrdinaryPolicy.Annotate.class, policy.evaluate(request, advance(request)));
        assertThrows(IllegalArgumentException.class, () -> policy.revalidate(confirm, request));
        supplier.planner = new Planner(Kind.FEAST_STAGE_TWO, new Obj(java.util.Map.of())); supplier.destinationLegal = false;
        assertInstanceOf(OrdinaryPolicy.Annotate.class, policy.evaluate(request, advance(request)));
        supplier.destinationLegal = true;
        var destination = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request))).draft().command().orElseThrow();
        assertEquals(OrdinaryFeastPolicy.DESTINATION, destination.operation());
        assertFalse(OrdinaryFeastPolicy.START.equals(destination.operation())); assertEquals(0, supplier.budgetReads);
    }
    @Test void nativeConfigurationActorOrDateDriftCannotAuthorizeConfirm() {
        var request = feastRequest(); var supplier = new Feasts(request); supplier.planner = new Planner(Kind.FEAST_STAGE_ONE, new Obj(java.util.Map.of()));
        supplier.frame = new ActivityConfigurationModels.Frame(supplier.frame.nativeRevision(), supplier.frame.dateRaw().add(BigInteger.ONE), supplier.frame.actorId());
        assertInstanceOf(OrdinaryPolicy.Defer.class, new OrdinaryFeastPolicy(REF, supplier,
                OrdinaryGovernanceFactoriesTest::unitExpected).evaluate(request, advance(request)));
    }
    @Test void originalUnknownFeastCommandIsReconciledBeforeCadenceOrAnyNewPlannerRead() {
        var request = feastRequest(); var supplier = new Feasts(request); var effects = new java.util.concurrent.atomic.AtomicInteger();
        var policy = new OrdinaryFeastPolicy(REF, supplier, (operation, fresh, arguments) -> {
            effects.incrementAndGet(); return unitExpected(operation, fresh, arguments);
        });
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request))).draft().command().orElseThrow();
        var original = new ActionReceipt(1, 1, selected, ActionCodec.bodySha256(selected), new ActionState.Unknown(Optional.empty(), Optional.empty(), "unit unknown", List.of(REF)));
        ActionPorts.OutcomeArchive archive = (ActionPorts.OutcomeArchive) java.lang.reflect.Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class}, (p, m, a) -> { throw new AssertionError("archive called"); });
        var encoded = ActionReceiptCodec.encodeReceipt(original, archive);
        var decoded = ActionReceiptCodec.decodeReceipt(encoded, archive);
        assertEquals(original.command(), decoded.command()); assertEquals(original.bodySha256(), decoded.bodySha256());
        assertEquals(original.command().actionId(), decoded.command().actionId()); assertEquals(original.sequence(), decoded.sequence());
        var originalUnknown = assertInstanceOf(ActionState.Unknown.class, original.state()); var decodedUnknown = assertInstanceOf(ActionState.Unknown.class, decoded.state());
        assertEquals(originalUnknown.reason(), decodedUnknown.reason()); assertEquals(originalUnknown.evidence(), decodedUnknown.evidence());
        assertTrue(decodedUnknown.attempt().isEmpty()); assertTrue(decodedUnknown.dispatch().isEmpty());
        assertArrayEquals(ActionCodec.encodeCommand(selected), ActionCodec.encodeCommand(decoded.command()));
        assertArrayEquals(encoded, ActionReceiptCodec.encodeReceipt(decoded, archive));
        assertFalse(decoded.settled()); assertEquals(ActionReceipt.Outcome.UNRESOLVED, decoded.outcome());
        supplier.state = new State(request.before(), request.sessionId(), supplier.state.cadence(), Optional.empty(), Optional.empty(), List.of(decoded), new Obj(java.util.Map.of()));
        int previousReads = supplier.plannerReads; int previousBudgetReads = supplier.budgetReads; int previousEffects = effects.get();
        var decision = assertInstanceOf(OrdinaryPolicy.ReconcileExisting.class, policy.evaluate(request, advance(request)));
        assertEquals(selected.actionId(), decision.actionId()); assertEquals(previousReads, supplier.plannerReads); assertEquals(previousBudgetReads, supplier.budgetReads);
        assertEquals(previousEffects, effects.get());
    }
    @Test void ordinaryFeastPreservesAnEarlierActionAndUnavailableStageFiveFundingDoesNotCompleteCadence() {
        var request = feastRequest(); var supplier = new Feasts(request); var policy = new OrdinaryFeastPolicy(REF, supplier, OrdinaryGovernanceFactoriesTest::unitExpected);
        assertInstanceOf(OrdinaryPolicy.NotApplicable.class, policy.evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(0, supplier.plannerReads);
        supplier.planner = new Planner(Kind.FEAST_STAGE_FIVE, new Obj(java.util.Map.of()));
        assertInstanceOf(OrdinaryPolicy.Defer.class, policy.evaluate(request, advance(request))); assertEquals(1, supplier.budgetReads);
    }
    @Test void currentReadableOngoingFlagsOverrideMatchingRetainedTerminalAndStampNeverEndsFeast() {
        var actor = BigInteger.valueOf(29829); var terminal = Optional.of(new Terminal(BigInteger.valueOf(18), actor));
        Obj identity = new Obj(java.util.Map.of()).with("activity_id", n(18)).with("host_character_id", n(29829)).with("activity_type_key", new Text("activity_feast"));
        var unread = new Hosted(actor, HostedFeastCodec.decode(encode(new Arr(List.of(identity)))), new Obj(java.util.Map.of()));
        assertFalse(unread.unresolved(terminal)); assertTrue(unread.unresolved(Optional.empty()));
        Obj ongoing = identity.with("terminal_flags_observed", new Bool(true)).with("native_completed", new Bool(false)).with("native_invalidated", new Bool(false));
        assertTrue(new Hosted(actor, HostedFeastCodec.decode(encode(new Arr(List.of(ongoing)))), new Obj(java.util.Map.of())).unresolved(terminal));
        Obj stamp = identity.with("native_completion_stamp_observed", new Bool(true)).with("native_completion_stamp_raw", n(1));
        assertTrue(new Hosted(actor, HostedFeastCodec.decode(encode(new Arr(List.of(stamp)))), new Obj(java.util.Map.of())).unresolved(Optional.empty()));
        var wrongActor = Optional.of(new Terminal(BigInteger.valueOf(18), BigInteger.valueOf(29830))); assertTrue(unread.unresolved(wrongActor));
    }
    static Obj diagnostic(PlanningRequest request) {
        var frame = request.before().frame().identity();
        return new Obj(java.util.Map.of()).with("schema", new Text("activity-planner-diag-private-read-v1")).with("snapshot_revision", new IntegerValue(frame.nativeRevision())).with("date_raw", new IntegerValue(frame.dateRaw())).with("actor_character_id", new IntegerValue(frame.player())).with("planner_status", new Text("planner_absent")).with("planner_present", new Bool(false)).with("widget_attached", new Bool(false)).with("widget_visible", new Bool(false)).with("planning_stage", Nil.INSTANCE).with("host_view_activity_key_source", new Text("host_view_current_type")).with("host_view_activity_key", Nil.INSTANCE).with("configured_cost_state", new Text("unknown")).with("final_can_start_state", new Text("unknown")).with("raw_pointer_fields_persisted", new Bool(false));
    }
    @Test void plannerBoundaryRejectsWrongTypesMissingFieldsAndClaimsBeyondNativeDiagnostic() {
        var request = feastRequest(); Obj absent = diagnostic(request);
        assertEquals(Kind.ABSENT, FeastObservationCollector.decodePlanner(request, absent).kind());
        Obj stage2 = absent.with("planner_status", new Text("observed")).with("planner_present", new Bool(true))
                .with("planning_stage", n(2)).with("host_view_activity_key", new Text("activity_feast"));
        assertEquals(Kind.FEAST_STAGE_TWO, FeastObservationCollector.decodePlanner(request, stage2).kind());
        for (Value token : List.of(new Bool(true), new DecimalValue("2.0"), new Text("2")))
            assertThrows(IllegalArgumentException.class, () -> FeastObservationCollector.decodePlanner(request, stage2.with("planning_stage", token)));
        assertThrows(IllegalArgumentException.class, () -> FeastObservationCollector.decodePlanner(request, absent.with("final_can_start_state", new Text("available"))));
        assertThrows(IllegalArgumentException.class, () -> FeastObservationCollector.decodePlanner(request, new Obj(java.util.Map.of())));
    }
    @Test void unavailableCouncilStillRequiresItsCompletePublicAndNativeSourceFrame() {
        var request = request(); var role = CouncilSelection.Position.STEWARD;
        Obj unavailable = councilRaw(request, role, 10, 12, 11).with("status", new Text("unavailable"));
        assertEquals(CouncilSelection.Outcome.QUERY_UNAVAILABLE, CouncilSelection.choose(CouncilSelection.decode(request, role, unavailable)).outcome());
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role, new Obj(java.util.Map.of()).with("status", new Text("unavailable"))));
        var source = object(unavailable.get("source_frame"), "source frame");
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role,
                unavailable.with("source_frame", source.with("paused", new Bool(false)))));
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role,
                unavailable.with("queried_native_revision", new Bool(true))));
    }
}
