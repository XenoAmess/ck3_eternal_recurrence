package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Actual software packets -> one transport/coordinator -> Life/Clock -> ordered Status -> cold physical archive.
 * Controlled protocol inputs grant no actual CK3 or Root installation qualification. */
final class LifeAdvanceLifecycleTest {
    @TempDir Path temporary;
    private final List<Fixture> actualFixtures=new ArrayList<>();
    @AfterEach void closeOriginalTransports() throws IOException {
        for(Fixture fixture:actualFixtures)fixture.actual.close();
        actualFixtures.clear();
    }
    private static final BigInteger START = BigInteger.valueOf(ActionWriterIntegrationFixture.INITIAL_DATE_RAW);
    private static final Set<OperationKey> STEPS = Set.of(new OperationKey("set-speed-1"), new OperationKey("resume-map"), new OperationKey("pause-map"));
    private static final Set<String> CAPS = Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP);
    private static RawJson raw(Obj value) { return new RawJson(DriverJson.encode(value)); }
    private static Value reference(ExactRef value) { return org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(org.xar.ck3.control.contracts.StrictJson.canonical(value.toJson())); }
    private static Obj json(String value) { return DriverJson.object(value.getBytes(StandardCharsets.UTF_8), RawJson.MAXIMUM_BYTES); }
    private static Status sentinel(State state) {
        return new Status(state, new CrossJsDecimalUInt64("37"), START.intValueExact(), START.add(AdvancePlan.DAY).intValueExact(), START.intValueExact(),
                0, 1, Mode.TERMINAL_OR_SENTINEL, 0, 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false);
    }
    private static Obj nativeToken(String step, String status, Status sentinel) {
        var fields = new java.util.LinkedHashMap<String, Value>();
        fields.put("step", new Text(step)); fields.put("accepted", new Bool(true)); fields.put("status", new Text(status));
        fields.put("tactical_daily_sentinel", org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(
                org.xar.ck3.control.contracts.StrictJson.canonical(SentinelObservation.toJson(sentinel))));
        return new Obj(fields);
    }
    @Test void armThenNewModalCancelsWithoutResumeAndSettlesAtSameNativeRevision() {
        Fixture fixture = new Fixture(true, false, false);
        ActionPorts.PostconditionResult result = fixture.life.run(fixture.parent, fixture);
        ActionPorts.CompositeControlObserved terminal = assertInstanceOf(ActionPorts.CompositeControlObserved.class, result);
        assertEquals(List.of(fixture.plan.armStep(), ClockStatusRead.CANCEL_PREFIX + "37"), fixture.steps);
        assertTrue(fixture.children.stream().allMatch(value -> value.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied));
        assertEquals(fixture.parent.before().frame().identity().nativeRevision(), terminal.observation().semantic().after().frame().identity().nativeRevision());
        ActionState.CompositeControlApplied settlement = new ActionState.CompositeControlApplied(terminal.observation());
        CompositeExecution execution = fixture.execution();
        ActionEffects.validateComposite(fixture.parent, execution, settlement);
        ActionEffects.validateCompositeChildren(execution, settlement, fixture.children);
        ActionReceipt receipt = new ActionReceipt(1, 100, fixture.parent, ActionCodec.bodySha256(fixture.parent), new ActionState.CompositeSettled(execution, settlement));
        LifeAdvanceEvidence.verifyRecorded(receipt, fixture.archive, fixture::rebuild, new AdvanceClockArchivedReplay(fixture::complete));
        assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
        Obj compatible = DriverJson.object(AdvanceResult.compatibleResult(receipt, fixture.archive).orElseThrow().bytes(), RawJson.MAXIMUM_BYTES);
        assertEquals(new IntegerValue(BigInteger.ZERO), compatible.get("elapsed_days"));
        assertEquals(new Bool(false), compatible.get("calendar_progress_verified"));
        assertEquals(new IntegerValue(BigInteger.ZERO), compatible.get("saved_day_credit"));
        assertEquals(sentinel(State.IDLE), ClockStatusRead.decode(terminal.observation().terminalStatus().original()));
        byte[] encoded = ActionReceiptCodec.encodeReceipt(receipt, fixture.archive);
        assertEquals(receipt, ActionReceiptCodec.decodeReceipt(encoded, fixture.archive));
    }
    @Test void finalFreshSpeedDriftRefusesResumeAndRetainsTheOriginalCanonicalArmCleanup() throws Exception {
        Fixture fixture=new Fixture(false,false,false,false,false,1,true);
        fixture.speedDriftBeforeResume=true;
        ActionReceipt receipt=fixture.actual.coordinator.execute(fixture.parent);
        var pending=assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());
        assertTrue(pending.reason().contains("native resume fresh speed differs from original immutable plan"));
        assertEquals(List.of(fixture.plan.armStep(),ClockStatusRead.CANCEL_PREFIX+"37"),fixture.steps);
        assertFalse(fixture.resumed);
        assertTrue(fixture.canceled);
        assertEquals(5,fixture.actualSpeed);
        assertFalse(receipt.visibleGameplay());
        assertFalse(receipt.eligibleAdvance());
        var canonicalChildren=fixture.actual.writer.locked(same->{
            var children=new ArrayList<ActionReceipt>();
            for(var child:pending.execution().children())
                children.add(ContinuityActionJournal.lookup(same.head().state(),child.actionId(),fixture.archive.withSession(same)).orElseThrow());
            return List.copyOf(children);
        });
        assertEquals(2,canonicalChildren.size());
        assertTrue(canonicalChildren.stream().allMatch(ActionReceipt::settled));
        var cancel=assertInstanceOf(ActionState.Settled.class,canonicalChildren.getLast().state());
        assertInstanceOf(ActionState.ControlApplied.class,cancel.settlement());
        int writes=fixture.actual.nativeActionWrites();
        assertEquals(receipt,fixture.actual.reopenAndReturnExisting(fixture.parent));
        assertEquals(writes,fixture.actual.nativeActionWrites(),"cold read cannot resume or resubmit the refused clock");
    }
    @Test void unknownResumeExecutesTheActualPrimitivePendingBranchAndNeverCancelsOrReplays() {
        Fixture fixture = new Fixture(false, true, false);
        ActionPorts.Pending pending = assertInstanceOf(ActionPorts.Pending.class, fixture.life.run(fixture.parent, fixture));
        assertTrue(pending.reason().contains("unresolved"));
        assertEquals(List.of(fixture.plan.armStep(), "resume-map"), fixture.steps);
        assertFalse(fixture.children.getLast().settled());
        assertFalse(fixture.steps.stream().anyMatch(value -> value.startsWith(ClockStatusRead.CANCEL_PREFIX) || value.equals("pause-map")));
    }
    @Test void actualClockChildrenRetainTransportOrderAndColdArchiveRejectsAPreSubmissionStatusAsFreshness() throws Exception {
        Fixture fixture=new Fixture(true,false,false);
        var before=fixture.current(fixture.parent,fixture.parent.deadline());
        var request=new PlanningReadRequest(before.identity(),before.source(),before.sessionId(),new OperationKey(ClockStatusRead.STEP),
                new Obj(Map.of()),fixture.parent.deadline());
        var prior=assertInstanceOf(PlanningReadResult.Known.class,fixture.read(fixture.installedStatus.get(),request)).receipt();
        assertInstanceOf(ActionPorts.CompositeControlObserved.class,fixture.life.run(fixture.parent,fixture));
        int writes=fixture.actual.nativeActionWrites(),queries=fixture.actual.nativeReadWrites();
        for(ActionReceipt child:fixture.children) {
            var settled=assertInstanceOf(ActionState.Settled.class,child.state());
            var control=assertInstanceOf(ActionState.ControlApplied.class,settled.settlement());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,settled.dispatch());
            NativeRequestChronology.requireSampledAfter(control.read(),settled.attempt(),ack);
            assertEquals(ack.custody().orElseThrow().custodyEpoch(),control.read().original().custody().orElseThrow().custodyEpoch());
            assertTrue(control.read().original().custody().orElseThrow().writeEntered().order()
                    .compareTo(ack.custody().orElseThrow().responseReceived().order())>0);
            assertThrows(IllegalArgumentException.class,()->NativeRequestChronology.requireSampledAfter(prior,settled.attempt(),ack));
            assertEquals(child,fixture.actual.reopenAndReturnExisting(child.command()),"cold actual archive reads must retain original custody without another submission");
        }
        assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());
    }
    @Test void actualExactDayTimeoutRetainsThePreStatusFailureAndRealCleanupWithoutStopCredit() throws Exception {
        Fixture fixture=new Fixture(false,false,false,false,false,1,true);fixture.exactStopFailure=true;
        ActionReceipt receipt=fixture.actual.coordinator.execute(fixture.parent);
        var pending=assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());
        var canonicalChildren=fixture.actual.writer.locked(same->{
            var children=new ArrayList<ActionReceipt>();
            for(var child:pending.execution().children())
                children.add(ContinuityActionJournal.lookup(same.head().state(),child.actionId(),fixture.archive.withSession(same)).orElseThrow());
            return List.copyOf(children);
        });
        assertEquals(ExactDayClockFailure.MESSAGE,pending.reason());
        assertEquals(List.of(fixture.plan.armStep(),"resume-map","pause-map",ClockStatusRead.CANCEL_PREFIX+"37"),fixture.steps);
        assertTrue(canonicalChildren.stream().allMatch(ActionReceipt::settled));
        var pauseChild=canonicalChildren.stream().filter(child->child.command().operation().value().equals("pause-map")).findFirst().orElseThrow();
        var pauseState=assertInstanceOf(ActionState.Settled.class,pauseChild.state());
        var actualPause=assertInstanceOf(ActionState.PauseConfirmed.class,pauseState.settlement());
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,pauseChild.outcome());
        assertTrue(pauseChild.applied().isEmpty());assertFalse(pauseChild.visibleGameplay());assertFalse(pauseChild.eligibleAdvance());
        assertEquals(Set.copyOf(PauseConfirmation.actualValues()),Set.copyOf(actualPause.observation().actual()));
        int pauseWrites=fixture.actual.nativeActionWrites(),pauseReads=fixture.actual.nativeReadWrites(),pausePackets=fixture.actual.nativePacketReads();
        byte[] pauseLedger=fixture.actual.ledgerBytes();
        var pausedOriginal=AdvancePrimitiveEvidence.load(pauseChild,fixture.archive,fixture::complete);
        assertEquals(actualPause.observation().after(),pausedOriginal.identity());assertTrue(AdvancePolicy.truth(pausedOriginal.semantic(),"paused"));
        new AdvancePrimitiveArchivedReplay(fixture::complete).verify(pauseChild,fixture.archive);
        assertEquals(pauseChild,fixture.actual.reopenAndReturnExisting(pauseChild.command()));
        assertArrayEquals(pauseLedger,fixture.actual.ledgerBytes());assertEquals(pauseWrites,fixture.actual.nativeActionWrites());
        assertEquals(pauseReads,fixture.actual.nativeReadWrites());assertEquals(pausePackets,fixture.actual.nativePacketReads());
        assertFalse(fixture.actualStatusResponsePhases.contains("resume-map"),"the original timeout precedes normal Status; cleanup owns the later reads");
        assertTrue(fixture.actualStatusResponsePhases.contains("pause-map"));
        fixture.retainedParent=Optional.of(receipt);
        var diagnostic=new ExactDayClockFailureEvidence(fixture::complete).project(receipt,fixture.archive).orElseThrow();
        Obj projected=DriverJson.object(diagnostic.diagnostic().bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new Text(ExactDayClockFailureEvidence.PUBLIC_SCHEMA),projected.get("schema"));
        assertEquals(new Bool(false),projected.get("normal_status_query_attempted"));
        assertEquals(new Bool(false),projected.get("stop_validation_attempted"));
        assertEquals(Nil.INSTANCE,projected.get("stopped_status"));
        assertEquals(new Bool(false),projected.get("stop_credit"));
        assertEquals(new IntegerValue(BigInteger.ZERO),projected.get("credit"));
        assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
        byte[] archived=ActionReceiptCodec.encodeReceipt(receipt,fixture.archive);
        assertEquals(receipt,ActionReceiptCodec.decodeReceipt(archived,fixture.archive));
        int frames=fixture.reads,requests=fixture.requests,writes=fixture.actual.nativeActionWrites(),queries=fixture.actual.nativeReadWrites();
        var retained=assertInstanceOf(ActionPorts.Pending.class,fixture.life.observe(fixture.parent,pending.execution()));
        assertEquals(ExactDayClockFailure.MESSAGE,retained.reason());
        assertEquals(frames,fixture.reads);assertEquals(requests,fixture.requests);
        assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());
    }
    @Test void aRealPostCancelStatusCannotReplaceTheOriginalPreCancelCleanupRead() {
        Fixture fixture=new Fixture(false,false,false);fixture.exactStopFailure=true;
        var pending=assertInstanceOf(ActionPorts.Pending.class,fixture.life.run(fixture.parent,fixture));
        var original=new ActionReceipt(1,100,fixture.parent,ActionCodec.bodySha256(fixture.parent),
                new ActionState.CompositeUnknown(fixture.execution(),pending.reason(),pending.evidence()));
        assertTrue(new ExactDayClockFailureEvidence(fixture::complete).project(original,fixture.archive).isPresent());
        int actionWrites=fixture.actual.nativeActionWrites();
        var current=fixture.current(fixture.parent,fixture.parent.deadline());
        var request=new PlanningReadRequest(current.identity(),current.source(),current.sessionId(),new OperationKey(ClockStatusRead.STEP),
                new Obj(Map.of()),fixture.parent.deadline());
        var later=assertInstanceOf(PlanningReadResult.Known.class,fixture.read(fixture.installedStatus.get(),request)).receipt();
        assertEquals(State.IDLE,ClockStatusRead.decode(later.original()).state());
        ExactRef laterRef=fixture.archive.preserveRead(later);
        ExactRef originalFinal=pending.evidence().getLast();
        Obj basis=DriverJson.object(fixture.archive.loadMaterial(originalFinal).bytes(),RawJson.MAXIMUM_BYTES);
        ExactRef changed=fixture.archive.preserveMaterial(raw(basis.with("cleanup_status_read",reference(laterRef))));
        List<ExactRef> evidence=new ArrayList<>(pending.evidence());evidence.set(evidence.size()-1,changed);
        var forged=new ActionReceipt(1,100,fixture.parent,ActionCodec.bodySha256(fixture.parent),
                new ActionState.CompositeUnknown(fixture.execution(),pending.reason(),evidence));
        assertThrows(IllegalArgumentException.class,()->new ExactDayClockFailureEvidence(fixture::complete).project(forged,fixture.archive));
        assertEquals(actionWrites,fixture.actual.nativeActionWrites());
        assertFalse(forged.visibleGameplay());assertFalse(forged.eligibleAdvance());
    }
    @Test void actualWatchPreparationAndSharedClockPreserveEveryPublishedArmyAndRealTerminalEvidence() {
        Fixture fixture=new Fixture(false,false,false,true,true,1);
        assertEquals(WarDailyWatch.POLICY,fixture.plan.policy()); assertEquals(2,fixture.plan.speed());
        assertEquals(List.of(11,22,33),fixture.plan.watchArmyIds());
        assertEquals(fixture.plan,AdvancePlan.decode(object(org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(DriverJson.encode(fixture.plan.json())),"plan roundtrip")));
        var result=assertInstanceOf(ActionPorts.EffectObserved.class,fixture.life.run(fixture.parent,fixture));
        assertEquals(List.of("set-speed-2",fixture.plan.armStep(),"resume-map"),fixture.steps);
        assertTrue(fixture.plan.armStep().endsWith("-a-3-11-22-33"));
        var receipt=new ActionReceipt(1,100,fixture.parent,ActionCodec.bodySha256(fixture.parent),new ActionState.CompositeSettled(fixture.execution(),new ActionState.Applied(result.observation())));
        LifeAdvanceEvidence.verifyRecorded(receipt,fixture.archive,fixture::rebuild,new AdvanceClockArchivedReplay(fixture::complete));
        Obj compatible=DriverJson.object(AdvanceResult.compatibleResult(receipt,fixture.archive).orElseThrow().bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new IntegerValue(BigInteger.ONE),compatible.get("elapsed_days")); assertEquals(new IntegerValue(BigInteger.ZERO),compatible.get("saved_day_credit"));
        Obj watch=object(compatible.get("war_daily_watch_v1"),"actual watch result");
        assertEquals(new Arr(List.of(new IntegerValue(BigInteger.valueOf(11)),new IntegerValue(BigInteger.valueOf(22)),new IntegerValue(BigInteger.valueOf(33)))),watch.get("watch_army_ids"));
        assertEquals(new Bool(false),watch.get("prediction_ready")); assertEquals(new Bool(false),watch.get("retreat_authorized"));
    }
    @Test void actualWatchKeepsAZeroDayBoundaryAsControlOnlyAndUnknownResumeAsNeverReplayFailure() {
        Fixture boundary=new Fixture(true,false,false,true,false,2);
        var observed=assertInstanceOf(ActionPorts.CompositeControlObserved.class,boundary.life.run(boundary.parent,boundary));
        assertEquals(List.of(boundary.plan.armStep(),ClockStatusRead.CANCEL_PREFIX+"37"),boundary.steps);
        assertEquals(new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),observed.observation().semantic().actual().stream().filter(value -> value.field().value().equals("timeline.advance_verified")).findFirst().orElseThrow());
        Fixture unknown=new Fixture(false,true,false,true,false,2);
        var failure=assertInstanceOf(ActionPorts.Pending.class,unknown.life.run(unknown.parent,unknown));
        assertEquals(List.of(unknown.plan.armStep(),"resume-map"),unknown.steps);
        var receipt=new ActionReceipt(1,100,unknown.parent,ActionCodec.bodySha256(unknown.parent),new ActionState.CompositeUnknown(unknown.execution(),failure.reason(),failure.evidence()));
        RawJson preserved=WarDailyWatchUnresolved.read(receipt,unknown.archive).orElseThrow(); Obj body=DriverJson.object(preserved.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new Text(WarDailyWatchUnresolved.SCHEMA),body.get("schema")); assertEquals(new Bool(true),body.get("never_replay"));
        assertEquals(new IntegerValue(BigInteger.ZERO),body.get("saved_day_credit"));
        assertTrue(AdvanceHistory.unresolvedWarWatch(List.of(new Obj(Map.of("result",body)))));
        ExactRef wrongRequest=unknown.archive.preserveMaterial(raw(body.with("native_request_id",new Text("foreign-native-request"))));
        var changed=new ActionReceipt(1,100,unknown.parent,ActionCodec.bodySha256(unknown.parent),new ActionState.CompositeUnknown(unknown.execution(),failure.reason(),List.of(failure.evidence().getFirst(),wrongRequest)));
        assertThrows(IllegalArgumentException.class,() -> WarDailyWatchUnresolved.read(changed,unknown.archive));
        var missingOriginal=new ActionReceipt(1,100,unknown.parent,ActionCodec.bodySha256(unknown.parent),new ActionState.CompositeUnknown(unknown.execution(),failure.reason(),List.of(failure.evidence().getLast())));
        assertThrows(IllegalArgumentException.class,() -> WarDailyWatchUnresolved.read(missingOriginal,unknown.archive));
        int frames=unknown.reads,requests=unknown.requests;
        assertInstanceOf(ActionPorts.Pending.class,unknown.life.observe(unknown.parent,unknown.execution()));
        assertEquals(frames,unknown.reads); assertEquals(requests,unknown.requests); assertEquals(2,unknown.steps.size());
    }
    @Test void actualCompletedLifeConsumerKeepsItsRetainedEndpointAfterANewerReadyFrame() {
        Fixture fixture=new Fixture(false,false,false,true,true,1);
        var result=assertInstanceOf(ActionPorts.EffectObserved.class,fixture.life.run(fixture.parent,fixture));
        var receipt=new ActionReceipt(1,100,fixture.parent,ActionCodec.bodySha256(fixture.parent),
                new ActionState.CompositeSettled(fixture.execution(),new ActionState.Applied(result.observation())));
        var completed=AdvanceCompletedRead.read(receipt,fixture.archive).orElseThrow();
        var endpoint=completed.endingFrame(fixture::rebuild,fixture.archive);
        assertEquals(result.observation().after(),endpoint.identity());
        var later=fixture.current(fixture.parent,fixture.parent.deadline());
        assertNotEquals(endpoint.identity().frame().snapshotId(),later.identity().frame().snapshotId());
        int writes=fixture.actual.nativeActionWrites(),queries=fixture.actual.nativeReadWrites();
        var retained=completed.endingFrame(fixture::rebuild,fixture.archive);
        assertEquals(endpoint,retained);assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());
        var unknown=new ActionReceipt(1,100,fixture.parent,ActionCodec.bodySha256(fixture.parent),
                new ActionState.CompositeUnknown(fixture.execution(),"outcome remains unknown",List.of(endpoint.originalEvidence())));
        assertTrue(AdvanceCompletedRead.read(unknown,fixture.archive).isEmpty());
        assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());
    }
    @Test void actualCanonicalLifeParentAndItsSoleCoordinatorChildrenFeedTheRealCycleReducer() throws Exception {
        Fixture fixture=new Fixture(false,false,false,true,true,1,true);
        var semantics=new NativeSemanticEvidenceVerifier((same,ref,maximum)->fixture.actual.archive.readArtifact(same,ref,maximum));
        var cycles=new OrdinaryCycleTransitions(fixture.archive,semantics,
                (same,owner,pair,proof)->{throw new IOException("this Life-to-Cycle fixture has not performed a physical SAVE");},
                new OriginalWindowReducer.Policy(10958),fixture.actual.writer::requireSession);
        cycles.bindTerminalFrameLoader(fixture.actual.frameLoader());
        for(String kind:cycles.kinds())fixture.actual.bindAdditionalTransitionAuthority(kind,cycles);
        var batches=new ContinuityBatchJournal(fixture.actual.writer,cycles);
        var input=fixture.initial;var publicSteps=Set.of(new OperationKey("life-advance-one-day"),new OperationKey("set-speed-1"),
                new OperationKey("set-speed-2"),new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map"));
        var publicRequest=new PlanningRequest(input.identity(),fixture.source,input.sessionId(),fixture.parent.deadline(),
                new PlanningObservation(input.semantic(),List.of(),publicSteps,fixture.captures.get(input).lease().bridgeCapabilities(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var commands=new LifeAdvanceCommands(fixture.life);int beforePublicWrites=fixture.actual.nativeActionWrites(),beforePublicReads=fixture.actual.nativeReadWrites();
        byte[] beforePublicLedger=fixture.actual.ledgerBytes();
        assertThrows(IllegalArgumentException.class,()->commands.preparePublic(publicRequest,new OperationKey("pause-map"),"wrong-public-life"));
        assertEquals(beforePublicWrites,fixture.actual.nativeActionWrites());assertEquals(beforePublicReads,fixture.actual.nativeReadWrites());assertArrayEquals(beforePublicLedger,fixture.actual.ledgerBytes());
        ActionCommand publicParent=commands.preparePublic(publicRequest,new OperationKey("life-advance-one-day"),"public-life-original");
        assertEquals("public-life-original",publicParent.actionId());assertEquals(publicRequest.before(),publicParent.before());
        assertEquals(publicRequest.source(),publicParent.source());assertEquals(new Claims(Set.of(),Set.of(),Set.of(),Set.of()),publicParent.claims());
        var publicPlan=AdvancePlan.decode(publicParent);assertTrue(publicPlan.exactOneDay());assertEquals(START,publicPlan.startingDateRaw());
        assertEquals(publicPlan.expected(),publicParent.expected().values());assertEquals(AdvancePlan.OBSERVER,publicParent.expected().observerSchema());
        ActionReceipt parent=fixture.actual.coordinator.execute(publicParent);
        assertEquals(publicParent,parent.command());
        assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,parent.outcome());
        int nativeWritesBeforePublic=fixture.actual.nativeActionWrites(),nativeReadsBeforePublic=fixture.actual.nativeReadWrites();
        int packetReadsBeforePublic=fixture.actual.nativePacketReads(),domainCapturesBeforePublic=fixture.reads,queriesBeforePublic=fixture.requests;
        byte[] ledgerBeforePublic=fixture.actual.ledgerBytes();
        var originalRecorded=LifeAdvanceEvidence.readRecorded(parent,fixture.archive,fixture::rebuild,new AdvanceClockArchivedReplay(fixture::complete));
        var compatibleOriginal=originalRecorded.originalCompatible().orElseThrow();
        assertEquals(compatibleOriginal.body(),fixture.archive.loadMaterial(compatibleOriginal.original()));
        RawJson publicResult=org.xar.ck3.control.service.root.RootLifeAdvancePublicResult.encode(compatibleOriginal.body());
        RawJson restoredResult=org.xar.ck3.control.service.root.RootLifeAdvancePublicResult.decode(publicResult);
        assertEquals(DriverJson.object(compatibleOriginal.body().bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(restoredResult.bytes(),RawJson.MAXIMUM_BYTES));
        Obj publicTree=DriverJson.object(publicResult.bytes(),RawJson.MAXIMUM_BYTES);
        assertInstanceOf(Text.class,publicTree.get("starting_revision"));assertInstanceOf(Text.class,publicTree.get("native_revision"));
        assertEquals(new IntegerValue(BigInteger.ONE),publicTree.get("elapsed_days"));
        assertEquals(new IntegerValue(BigInteger.ZERO),publicTree.get("saved_day_credit"));
        assertArrayEquals(ledgerBeforePublic,fixture.actual.ledgerBytes());
        assertEquals(nativeWritesBeforePublic,fixture.actual.nativeActionWrites());assertEquals(nativeReadsBeforePublic,fixture.actual.nativeReadWrites());
        assertEquals(packetReadsBeforePublic,fixture.actual.nativePacketReads());assertEquals(domainCapturesBeforePublic,fixture.reads);assertEquals(queriesBeforePublic,fixture.requests);
        var settled=assertInstanceOf(ActionState.CompositeSettled.class,parent.state());
        assertFalse(settled.execution().children().isEmpty());
        var actualReceipts=fixture.actual.writer.locked(same->ContinuityActionJournal.receipts(same.head().state(),fixture.archive.withSession(same)));
        assertTrue(actualReceipts.contains(parent));
        for(var child:settled.execution().children())assertTrue(actualReceipts.stream().anyMatch(receipt->receipt.command().actionId().equals(child.actionId())
                &&receipt.bodySha256().equals(child.bodySha256())&&receipt.outcome()==(receipt.command().operation().value().equals("pause-map")
                        ?ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT:ActionReceipt.Outcome.APPLIED_CONFIRMED)));
        var owner=fixture.actual.observationIdentity();batches.retainCycle(owner,parent);
        var fresh=fixture.current(fixture.parent,fixture.parent.deadline());
        SessionPorts.SemanticEvidence actualAfter=fixture.captures.get(fresh).lease().semantic();
        int writes=fixture.actual.nativeActionWrites(),queries=fixture.actual.nativeReadWrites();
        var proof=batches.settleCycle(owner,parent,actualAfter);
        assertEquals(1,proof.completedCycles());assertEquals(actualAfter,proof.semantic());
        var current=fixture.actual.writer.locked(same->same.head().state());
        assertEquals(0,current.settledCycles());assertEquals(START.longValueExact(),current.settledDateRaw());
        assertEquals(1,current.toJson().get(OrdinaryCycleTransitions.STATE_FIELD).get("completed_cycles").longValue());
        assertFalse(current.toJson().has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD));
        long originalSequence=current.sequence();batches.retainCycle(owner,parent);
        assertEquals(proof,batches.settleCycle(owner,parent,actualAfter));
        long actualSequence=fixture.actual.writer.locked(same->same.head().state().sequence());assertEquals(originalSequence,actualSequence);
        assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());
        assertTrue(fixture.actual.actualReadCatalog().contracts().contains(fixture.installedStatus.get()));
        batches.requireStore(fixture.actual.writer);
        // Another facade around the same physical writer is not the identical configured store.
        ContinuityStorePort alias=new ContinuityStorePort(){
            @Override public WriterContracts.Prepared preview(WriterContracts.Request request)throws IOException{return fixture.actual.writer.preview(request);}
            @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared)throws IOException{return fixture.actual.writer.commit(prepared);}
            @Override public ExactRef persistedHead()throws IOException{return fixture.actual.writer.persistedHead();}
            @Override public <T>T locked(ContinuityStorePort.SessionWork<T> work)throws IOException{return fixture.actual.writer.locked(work);}
        };
        assertThrows(IllegalArgumentException.class,()->batches.requireStore(alias));
        var stale=new java.util.concurrent.atomic.AtomicReference<ContinuityStorePort.Session>();
        fixture.actual.writer.locked(same->{stale.set(same);return null;});
        fixture.actual.writer.locked(same->{
            assertNotSame(stale.get(),same);
            assertThrows(IOException.class,()->batches.cycleProof(owner,actualAfter),"unborrowed entry must still reject nested original writer sessions");
            assertEquals(proof,batches.cycleProof(same,owner,actualAfter).orElseThrow());
            var metadata=new SessionPorts.JournalInput(owner,"actual-borrowed-cycle",SessionPorts.JournalKind.BATCH_STARTED,
                    Optional.empty(),Optional.empty(),Optional.empty(),List.of());
            assertThrows(IllegalArgumentException.class,()->batches.cycleProof(stale.get(),owner,actualAfter));
            assertThrows(IllegalArgumentException.class,()->batches.commit(stale.get(),metadata));
            long previous=same.head().state().sequence();
            var committed=batches.commit(same,metadata);
            assertEquals(previous+1,same.head().state().sequence());assertEquals(same.persistedHead(),committed.persistedHead());
            assertEquals(0,committed.committedSavedDays());
            assertEquals(proof,batches.cycleProof(same,owner,actualAfter).orElseThrow());
            return null;
        });
        assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());
    }
    @Test void canonicalAppliedAndZeroDayControlReadTheirOriginalFullMaterialsWithoutAnotherQueryOrArchiveWrite() throws Exception {
        for(boolean control:List.of(false,true)) {
            Fixture fixture=control?new Fixture(true,false,false,false,false,1,true)
                    :new Fixture(false,false,false,true,true,1,true);
            ActionReceipt original=fixture.actual.coordinator.execute(fixture.parent);
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,original.outcome());
            var settlement=assertInstanceOf(ActionState.CompositeSettled.class,original.state());
            if(control)assertInstanceOf(ActionState.CompositeControlApplied.class,settlement.settlement());
            else assertInstanceOf(ActionState.Applied.class,settlement.settlement());
            fixture.actual.writer.locked(same->{
                assertEquals(original,ContinuityActionJournal.lookup(same.head().state(),original.command().actionId(),fixture.archive.withSession(same)).orElseThrow());
                return null;
            });
            byte[] wire=ActionReceiptCodec.encodeReceipt(original,fixture.archive);
            ActionReceipt restored=ActionReceiptCodec.decodeReceipt(wire,fixture.archive);assertEquals(original,restored);
            var archive=new ReadOnlyLifeArchive(fixture.archive);
            int writes=fixture.actual.nativeActionWrites(),queries=fixture.actual.nativeReadWrites(),frames=fixture.reads,packets=fixture.actual.nativePacketReads();
            long sequence=fixture.actual.sequence();
            var replay=new AdvanceClockArchivedReplay(fixture::complete);
            var recorded=LifeAdvanceEvidence.readRecorded(restored,archive,fixture::rebuild,replay);
            assertEquals(original.command().before(),recorded.starting().identity());
            assertEquals(ActionEffects.observation(original).orElseThrow().after(),recorded.ending().identity());
            assertEquals(fixture.initial.identity(),fixture.rebuild(original.command(),recorded.starting(),archive).identity());
            var compatible=recorded.originalCompatible().orElseThrow();
            assertArrayEquals(archive.loadMaterial(compatible.original()).bytes(),compatible.body().bytes());
            assertArrayEquals(AdvanceResult.compatibleResult(original,fixture.archive).orElseThrow().bytes(),compatible.body().bytes());
            assertEquals(recorded,LifeAdvanceEvidence.readRecorded(restored,archive,fixture::rebuild,replay));
            assertEquals(!control,AdvanceCompletedRead.read(original,fixture.archive).isPresent());
            if(control) {
                var result=DriverJson.object(compatible.body().bytes(),RawJson.MAXIMUM_BYTES);
                assertEquals(new IntegerValue(BigInteger.ZERO),result.get("elapsed_days"));
                assertEquals(new Bool(false),result.get("calendar_progress_verified"));
            }
            assertTrue(archive.reads>0);assertEquals(sequence,fixture.actual.sequence());
            assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());assertEquals(frames,fixture.reads);assertEquals(packets,fixture.actual.nativePacketReads());
        }
    }
    @Test void actualUnknownAndHostileAckOnlyLifeInputsFailBeforeTouchingArchiveOrRebuildingFrames() throws Exception {
        Fixture fixture=new Fixture(false,true,false,false,false,1,true);
        ActionReceipt unknown=fixture.actual.coordinator.execute(fixture.parent);
        assertInstanceOf(ActionState.CompositeUnknown.class,unknown.state());
        var actualChild=fixture.actual.writer.locked(same->ContinuityActionJournal.receipts(same.head().state(),fixture.archive.withSession(same)).stream()
                .filter(value->value.state() instanceof ActionState.Settled&&value.ack().isPresent()).findFirst().orElseThrow());
        var childState=assertInstanceOf(ActionState.Settled.class,actualChild.state());
        // Hostile DATA only: an actual child's ACK cannot become a semantic observation for this parent.
        var ackOnly=new ActionReceipt(unknown.version(),unknown.sequence(),unknown.command(),unknown.bodySha256(),
                new ActionState.AckReceived(childState.attempt(),actualChild.ack().orElseThrow()));
        var archive=new ReadOnlyLifeArchive(fixture.archive);
        int writes=fixture.actual.nativeActionWrites(),queries=fixture.actual.nativeReadWrites(),frames=fixture.reads,packets=fixture.actual.nativePacketReads();
        long sequence=fixture.actual.sequence();
        for(ActionReceipt input:List.of(unknown,ackOnly))assertThrows(IllegalArgumentException.class,
                ()->LifeAdvanceEvidence.readRecorded(input,archive,(parent,retained,store)->{throw new AssertionError("unobserved Life cannot rebuild a frame");},
                        new AdvanceClockArchivedReplay(fixture::complete)));
        assertEquals(0,archive.reads);assertEquals(sequence,fixture.actual.sequence());
        assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());assertEquals(frames,fixture.reads);assertEquals(packets,fixture.actual.nativePacketReads());
    }
    @Test void canonicalLifeRecordedReaderRejectsChangedRebuiltOriginalSemanticWithoutFreshCapture() throws Exception {
        Fixture fixture=new Fixture(true,false,false,false,false,1,true);
        ActionReceipt receipt=fixture.actual.coordinator.execute(fixture.parent);
        assertInstanceOf(ActionState.CompositeSettled.class,receipt.state());
        var archive=new ReadOnlyLifeArchive(fixture.archive);
        int writes=fixture.actual.nativeActionWrites(),queries=fixture.actual.nativeReadWrites(),frames=fixture.reads,packets=fixture.actual.nativePacketReads();
        long sequence=fixture.actual.sequence();
        assertThrows(IllegalArgumentException.class,()->LifeAdvanceEvidence.readRecorded(receipt,archive,(parent,retained,store)->{
            var actual=fixture.rebuild(parent,retained,store);
            return new AdvanceObservationPort.Frame(actual.identity(),actual.source(),actual.sessionId(),
                    actual.semantic().with("active_wars",new Arr(List.of(json("{\"war_id\":88}")))),actual.provenance(),actual.observedAt(),actual.originalEvidence());
        },new AdvanceClockArchivedReplay(fixture::complete)));
        assertTrue(archive.reads>0);assertEquals(sequence,fixture.actual.sequence());
        assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(queries,fixture.actual.nativeReadWrites());assertEquals(frames,fixture.reads);assertEquals(packets,fixture.actual.nativePacketReads());
    }
    /** A narrow archive test observer: original reads delegate, every attempted preserve fails the regression. */
    private static final class ReadOnlyLifeArchive implements ActionPorts.OutcomeArchive {
        private final ActionPorts.OutcomeArchive original; int reads;
        ReadOnlyLifeArchive(ActionPorts.OutcomeArchive original){this.original=java.util.Objects.requireNonNull(original);}
        private <T>T read(java.util.function.Supplier<T> work){reads++;return work.get();}
        private AssertionError write(){return new AssertionError("recorded Life reader cannot preserve new material");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw write();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){return read(()->original.load(ref));}
        @Override public ExactRef preserveRequest(NativeRequest value){throw write();}
        @Override public NativeRequest loadRequest(ExactRef ref){return read(()->original.loadRequest(ref));}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){return read(()->original.referenceOf(value));}
        @Override public ExactRef requestReferenceOf(NativeRequest value){return read(()->original.requestReferenceOf(value));}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw write();}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){return read(()->original.loadRead(ref));}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){return read(()->original.readReferenceOf(value));}
        @Override public ExactRef preserveRecord(ActionRecord value){throw write();}
        @Override public ActionRecord loadRecord(ExactRef ref){return read(()->original.loadRecord(ref));}
        @Override public ExactRef recordReferenceOf(ActionRecord value){return read(()->original.recordReferenceOf(value));}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw write();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){return read(()->original.loadReceipt(ref));}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){return read(()->original.receiptReferenceOf(value));}
        @Override public ExactRef preserveMaterial(RawJson value){throw write();}
        @Override public RawJson loadMaterial(ExactRef ref){return read(()->original.loadMaterial(ref));}
        @Override public ExactRef materialReferenceOf(RawJson value){return read(()->original.materialReferenceOf(value));}
        @Override public ExactRef materialReference(String sha,long bytes){return read(()->original.materialReference(sha,bytes));}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw write();}
        @Override public byte[] loadNativeFrame(ExactRef ref){return read(()->original.loadNativeFrame(ref));}
    }
    @Test void actualWatchRejectsChangedRosterBeforeArmAndDoesNotTreatTargetDateAsAPausedStop() {
        Fixture changed=new Fixture(false,false,false,true,false,1); changed.rosterDriftAfterSpeed=true;
        var failure=assertInstanceOf(ActionPorts.Pending.class,changed.life.run(changed.parent,changed));
        assertEquals(List.of("set-speed-2"),changed.steps);
        var receipt=new ActionReceipt(1,100,changed.parent,ActionCodec.bodySha256(changed.parent),new ActionState.CompositeUnknown(changed.execution(),failure.reason(),failure.evidence()));
        assertTrue(WarDailyWatchUnresolved.read(receipt,changed.archive).isPresent());
        Fixture lag=new Fixture(false,false,false,true,true,1); lag.laggingPause=true;
        assertInstanceOf(ActionPorts.EffectObserved.class,lag.life.run(lag.parent,lag));
        assertTrue(lag.postResumeReads>=3); assertFalse(lag.steps.contains("pause-map"));
        assertTrue(lag.produced.values().stream().anyMatch(frame -> frame.identity().frame().identity().dateRaw().equals(START.add(AdvancePlan.DAY)) && !AdvancePolicy.truth(frame.semantic(),"paused")));
    }
    @Test void retainedUnknownResumeDoesNotReadAnEntryFrameOrNativeStateOrSubmitAgain() {
        Fixture fixture = new Fixture(false, true, false);
        assertInstanceOf(ActionPorts.Pending.class, fixture.life.run(fixture.parent, fixture));
        List<String> originalSteps = List.copyOf(fixture.steps);
        int nativeFrames = fixture.reads, requests = fixture.requests;
        ActionPorts.Pending pending = assertInstanceOf(ActionPorts.Pending.class, fixture.life.observe(fixture.parent, fixture.execution()));
        assertTrue(pending.reason().contains("original durable life child is still unresolved"));
        assertEquals(originalSteps, fixture.steps);
        assertEquals(nativeFrames, fixture.reads);
        assertEquals(requests, fixture.requests);
        assertEquals(0, fixture.entryReads);
    }
    @Test void actualCoordinatorUnknownChildRefusalCannotEscapeOrStartCleanup() {
        Fixture fixture = new Fixture(false, true, false);
        CompositeActionPort.Children guarded = new CompositeActionPort.Children() {
            @Override public String nextActionId() { return fixture.nextActionId(); }
            @Override public List<ActionReceipt> completed() {
                if (fixture.children.stream().anyMatch(value -> !value.settled()))
                    throw new IllegalStateException("composite child is unknown or body changed; do not continue");
                return fixture.completed();
            }
            @Override public ActionReceipt submit(ActionCommand command) {
                ActionReceipt child = fixture.submit(command);
                if (!child.settled()) throw new IllegalStateException("composite child outcome is unknown; no following primitive or cleanup may submit");
                return child;
            }
        };
        ActionPorts.Pending pending = assertInstanceOf(ActionPorts.Pending.class, fixture.life.run(fixture.parent, guarded));
        assertTrue(pending.reason().contains("no replay"));
        assertFalse(pending.evidence().isEmpty());
        assertEquals(List.of(fixture.plan.armStep(), "resume-map"), fixture.steps);
        assertFalse(fixture.children.getLast().settled());
        assertEquals(0, fixture.entryReads);
    }
    @Test void retainedChildBodyConflictRefusesBeforeFreshNativeOrEntryReads() {
        Fixture fixture = new Fixture(false, true, false);
        assertInstanceOf(ActionPorts.Pending.class, fixture.life.run(fixture.parent, fixture));
        CompositeExecution original = fixture.execution();
        List<CompositeExecution.Child> changed = new ArrayList<>(original.children());
        CompositeExecution.Child first = changed.getFirst();
        changed.set(0, new CompositeExecution.Child(first.actionId(), "d".repeat(64)));
        CompositeExecution conflict = new CompositeExecution(original.handlerId(), original.startedAt(), original.guard(), changed);
        int nativeFrames = fixture.reads, requests = fixture.requests;
        assertThrows(IllegalArgumentException.class, () -> fixture.life.observe(fixture.parent, conflict));
        assertEquals(nativeFrames, fixture.reads);
        assertEquals(requests, fixture.requests);
        assertEquals(0, fixture.entryReads);
        assertEquals(List.of(fixture.plan.armStep(), "resume-map"), fixture.steps);
    }
    @Test void sameRevisionResumeAckAndModalCannotBypassTheOrdinaryPrimitiveEffectGuard() {
        Fixture fixture = new Fixture(false, false, true);
        assertInstanceOf(ActionPorts.Pending.class, fixture.life.run(fixture.parent, fixture));
        assertEquals(List.of(fixture.plan.armStep(), "resume-map"), fixture.steps);
        assertFalse(fixture.children.getLast().settled());
        assertTrue(fixture.children.getLast().state() instanceof ActionState.Unknown unknown && unknown.reason().contains("later native frame"));
    }
    @Test void rootEntryReplayUsesTheUnifiedGuardOriginalsAndPreservesPushProvenance() {
        Fixture fixture = new Fixture(false, false, false);
        var original = fixture.current(fixture.parent, fixture.parent.deadline());
        var guard = fixture.guard(fixture.parent.operation(), original);
        LifeAdvanceRootReplay replay = new LifeAdvanceRootReplay(fixture::complete);
        int nativeFrames = fixture.reads, requests = fixture.requests;
        var restored = replay.read(fixture.parent, guard, fixture.archive).orElseThrow();
        assertEquals(original, restored);
        assertInstanceOf(ObservationProvenance.Push.class, restored.provenance());
        assertEquals(nativeFrames, fixture.reads);
        assertEquals(requests, fixture.requests);
        assertTrue(fixture.steps.isEmpty());
        var missing = new GuardEvidence(guard.origin(), guard.source(), guard.sessionId(), guard.connectionGeneration(), guard.operation(),
                guard.nativeEvidence(), guard.capabilityEvidence(), guard.authorityId(), guard.observedAt(), guard.validUntil());
        assertTrue(replay.read(fixture.parent, missing, fixture.archive).isEmpty());
    }
    @Test void actualPushCannotBeReconstructedAsAnInventedHistoricalQuery() {
        Fixture fixture = new Fixture(false, false, false);
        var original = fixture.current(fixture.parent, fixture.parent.deadline());
        ExactRef semantic = fixture.archive.preserveMaterial(raw(original.semantic()));
        ExactRef driver = ExactRef.fromJson(toNode(original.semantic().get("java_driver_facts_evidence")));
        var query = new LifeAdvanceEvidence.FrameRecord(original.identity(), new ObservationProvenance.Query(original.identity().frame().snapshotId()),
                original.observedAt(), original.originalEvidence(), driver, semantic);
        assertThrows(IllegalArgumentException.class, () -> new LifeAdvanceRootReplay(fixture::complete).rebuild(fixture.parent, query, fixture.archive));
        assertEquals(1, fixture.reads);
        assertEquals(0, fixture.requests);
        assertTrue(fixture.steps.isEmpty());
    }
    @Test void lifeBasisRejectsMissingNullAndWrongTypedObservationProvenance() {
        Fixture fixture = new Fixture(true, false, false);
        var control = assertInstanceOf(ActionPorts.CompositeControlObserved.class, fixture.life.run(fixture.parent, fixture)).observation();
        Obj original = DriverJson.object(fixture.archive.loadMaterial(control.semantic().supportingEvidence().getFirst()).bytes(), RawJson.MAXIMUM_BYTES);
        Obj start = object(original.get("starting"), "starting");
        Map<String, Value> missing = new HashMap<>(start.members()); missing.remove("observation_provenance");
        List<Obj> malformed = new ArrayList<>(); malformed.add(new Obj(missing));
        for (Value value : List.of(Nil.INSTANCE, new Bool(false), new Text("native:1"))) malformed.add(start.with("observation_provenance", value));
        Obj provenance = object(start.get("observation_provenance"), "provenance");
        malformed.add(start.with("observation_provenance", provenance.with("native_revision", new IntegerValue(BigInteger.ONE))));
        for (Obj changed : malformed) {
            ExactRef basis = fixture.archive.preserveMaterial(raw(original.with("starting", changed)));
            ActionReceipt proposed = fixture.withBasis(control, basis);
            assertThrows(IllegalArgumentException.class, () -> LifeAdvanceEvidence.verifyRecorded(proposed, fixture.archive,
                    fixture::rebuild, new AdvanceClockArchivedReplay(fixture::complete)));
        }
    }
    @Test void recordedLifeEvidenceRejectsAChangedOriginalFrameAndFalseDayCredit() {
        Fixture fixture = new Fixture(true, false, false);
        var control = assertInstanceOf(ActionPorts.CompositeControlObserved.class, fixture.life.run(fixture.parent, fixture)).observation();
        var settled = new ActionState.CompositeControlApplied(control);
        var receipt = new ActionReceipt(1, 100, fixture.parent, ActionCodec.bodySha256(fixture.parent), new ActionState.CompositeSettled(fixture.execution(), settled));
        assertThrows(IllegalArgumentException.class, () -> LifeAdvanceEvidence.verifyRecorded(receipt, fixture.archive, (parent, retained, archive) -> {
            var original = fixture.rebuild(parent, retained, archive);
            return new AdvanceObservationPort.Frame(original.identity(), original.source(), original.sessionId(), original.semantic().with("active_wars", new Arr(List.of(json("{\"war_id\":88}")))),
                    original.provenance(), original.observedAt(), original.originalEvidence());
        }, new AdvanceClockArchivedReplay(fixture::complete)));
        List<ExpectedValue> changed = new ArrayList<>(control.semantic().actual());
        changed.remove(new ExpectedBoolean(new FieldKey("timeline.advance_verified"), false));
        changed.add(new ExpectedBoolean(new FieldKey("timeline.advance_verified"), true));
        var semantic = control.semantic();
        var fake = new ActionState.EffectObservation(semantic.after(), semantic.source(), semantic.sessionId(), semantic.observerSchema(), changed,
                semantic.provenance(), semantic.observedAt(), semantic.originalEvidence(), semantic.supportingEvidence());
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validateComposite(fixture.parent, fixture.execution(),
                new ActionState.CompositeControlApplied(new CompositeControlObservation(control.terminalStatus(), control.supportingReads(), fake))));
    }
    @Test void compatibleControlResultUsesTheFullFrameParserAndRejectsWrongOrMissingReferenceFields() {
        Fixture fixture = new Fixture(true, false, false);
        var control = assertInstanceOf(ActionPorts.CompositeControlObserved.class, fixture.life.run(fixture.parent, fixture)).observation();
        var receipt = new ActionReceipt(1, 100, fixture.parent, ActionCodec.bodySha256(fixture.parent), new ActionState.CompositeSettled(fixture.execution(), new ActionState.CompositeControlApplied(control)));
        RawJson result = AdvanceResult.compatibleResult(receipt, fixture.archive).orElseThrow();
        Obj complete = DriverJson.object(result.bytes(), RawJson.MAXIMUM_BYTES).with("large_original_diagnostic", new Text("x".repeat(150_000)));
        ExactRef large = fixture.archive.preserveMaterial(raw(complete));
        List<ExpectedValue> values = control.semantic().actual().stream().filter(value -> !value.field().value().startsWith("advance.result.")).collect(java.util.stream.Collectors.toCollection(ArrayList::new));
        values.add(new ExpectedText(new FieldKey("advance.result.path"), large.path())); values.add(new ExpectedText(new FieldKey("advance.result.sha256"), large.sha256()));
        values.add(new ExpectedInteger(new FieldKey("advance.result.bytes"), BigInteger.valueOf(large.bytes())));
        ActionReceipt withLarge = fixture.withActual(control, values);
        assertEquals(raw(complete), AdvanceResult.compatibleResult(withLarge, fixture.archive).orElseThrow());
        values.removeIf(value -> value.field().value().equals("advance.result.bytes"));
        assertThrows(IllegalArgumentException.class, () -> AdvanceResult.compatibleResult(fixture.withActual(control, values), fixture.archive));
    }
    /** Domain timeout input only; native custody timestamps always come from the shared real transport clock. */
    private static final class DomainClock extends Clock {
        private Instant advanced;
        @Override public java.time.ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(java.time.ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC domain clock required");return this;}
        @Override public Instant instant(){return advanced==null?Instant.now():advanced;}
        void advance(Duration step){advanced=instant().plus(step);}
    }
    @Test void pendingDatePolicyConsumesTheActualCapturedControlDriverFrameWithoutSecondNativeCapture() {
        var source=new PendingCaptureData();var fixture=source.fixture;
        var borrowed=new java.util.concurrent.atomic.AtomicReference<ContinuityStorePort.Session>();
        var scope=new PendingUiLifeAdvance.Scope(borrowed::get);var observations=scope.observations(fixture);
        var readiness=scope.readiness((command,frame)->{throw new AssertionError("no ordinary Ready or policy fallback");});
        fixture.inOriginal(same->{borrowed.set(same);long sequence=same.head().state().sequence();
            scope.within(source,()->{
                var frame=observations.current(source.command,source.command.deadline());
                int reads=fixture.actual.nativePacketReads(),captures=source.captures,writes=fixture.actual.nativeActionWrites();
                var facts=readiness.inspect(source.command,frame);
                assertEquals(frame.identity(),facts.observed());assertEquals(1,facts.crownRetryMaximumDays());
                assertEquals(source.last.originalDriver(),facts.originalHistoryEvidence());
                assertEquals(source.last.actualKnown().originalHistoryBasis(),source.last.originalHistoryBasis());
                assertArrayEquals(source.last.actualKnown().driver().encode(),fixture.archive.loadMaterial(source.last.originalDriver()).bytes());
                assertEquals(source.control,fixture.archive.loadReceipt(fixture.archive.receiptReferenceOf(source.control)));
                assertEquals(captures,source.captures);assertEquals(1,captures);
                assertEquals(reads,fixture.actual.nativePacketReads());assertEquals(writes,fixture.actual.nativeActionWrites());
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,frame));
                assertEquals(captures,source.captures);assertEquals(reads,fixture.actual.nativePacketReads());return null;
            });
            assertFalse(scope.active());assertEquals(sequence,same.head().state().sequence());borrowed.set(null);return null;
        });
    }
    @Test void pendingDateWrongFrameNextAndFailedCaptureCannotReuseTheFormerControlData() {
        var source=new PendingCaptureData();var fixture=source.fixture;
        var borrowed=new java.util.concurrent.atomic.AtomicReference<ContinuityStorePort.Session>();
        var scope=new PendingUiLifeAdvance.Scope(borrowed::get);var observations=scope.observations(fixture);
        var readiness=scope.readiness((command,frame)->{throw new AssertionError("no ordinary policy capture");});
        fixture.inOriginal(same->{borrowed.set(same);
            scope.within(source,()->{
                var first=observations.current(source.command,source.command.deadline());
                var different=fixture.current(source.command,source.command.deadline());assertNotEquals(first,different);
                int reads=fixture.actual.nativePacketReads(),captures=source.captures;
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,different));
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,first));
                assertEquals(captures,source.captures);assertEquals(reads,fixture.actual.nativePacketReads());
                source.failAfterCapture=true;
                assertThrows(UncheckedIOException.class,()->observations.current(source.command,source.command.deadline()));
                source.failAfterCapture=false;reads=fixture.actual.nativePacketReads();captures=source.captures;
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,source.last.originalFrame()));
                assertEquals(captures,source.captures);assertEquals(reads,fixture.actual.nativePacketReads());
                var beforeNext=observations.current(source.command,source.command.deadline());
                var next=observations.next(source.command,beforeNext.identity(),source.command.deadline());
                assertEquals(1,source.nextCaptures);assertNotEquals(beforeNext,next);
                reads=fixture.actual.nativePacketReads();captures=source.captures;
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,beforeNext));
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,next));
                assertEquals(captures,source.captures);assertEquals(reads,fixture.actual.nativePacketReads());
                var fresh=observations.current(source.command,source.command.deadline());
                assertEquals(fresh.identity(),readiness.inspect(source.command,fresh).observed());return null;
            });
            borrowed.set(null);return null;
        });
    }
    @Test void pendingDatePreparationStaleSessionInvalidSourceAndScopeExitClearOnlyCapturedData() {
        var source=new PendingCaptureData();var fixture=source.fixture;
        var borrowed=new java.util.concurrent.atomic.AtomicReference<ContinuityStorePort.Session>();
        var stale=new java.util.concurrent.atomic.AtomicReference<ContinuityStorePort.Session>();
        try{fixture.actual.writer.locked(same->{stale.set(same);return null;});}catch(IOException failure){throw new UncheckedIOException(failure);}
        var scope=new PendingUiLifeAdvance.Scope(borrowed::get);var observations=scope.observations(fixture);
        var readiness=scope.readiness((command,frame)->{throw new AssertionError("no ordinary Ready capture");});
        fixture.inOriginal(same->{borrowed.set(same);assertNotSame(stale.get(),same);
            scope.within(source,()->{
                var frame=observations.current(source.command,source.command.deadline());
                var setter=AdvancePrimitives.child(source.command,frame,"pending-data-preparation-only","set-speed-1",source.command.deadline());
                var base=AdvancePrimitives.prepareRequest(setter);int reads=fixture.actual.nativePacketReads(),writes=fixture.actual.nativeActionWrites();
                assertEquals(base,scope.prepare(same,setter,RequestIds.forCommand(setter),base));
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,frame));
                assertEquals(reads,fixture.actual.nativePacketReads());assertEquals(writes,fixture.actual.nativeActionWrites());
                var sessionFrame=observations.current(source.command,source.command.deadline());borrowed.set(stale.get());
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,sessionFrame));borrowed.set(same);
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,sessionFrame));
                var sourceFrame=observations.current(source.command,source.command.deadline());source.valid=false;
                assertThrows(UncheckedIOException.class,()->readiness.inspect(source.command,sourceFrame));source.valid=true;
                assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,sourceFrame));
                observations.current(source.command,source.command.deadline());return null; // Intentionally leave one unconsumed DATA capture.
            });
            assertFalse(scope.active());int captures=source.captures,reads=fixture.actual.nativePacketReads();
            PendingUiLifeAdvance.Source other=new PendingUiLifeAdvance.Source(){
                @Override public ActionCommand originalParent(){return source.originalParent();}
                @Override public void requireCurrent(ContinuityStorePort.Session current)throws IOException{source.requireCurrent(current);}
                @Override public <T>T withCurrent(ContinuityStorePort.Session current,Instant deadline,PendingUiLifeAdvance.Work<T> work)throws IOException{return source.withCurrent(current,deadline,work);}
                @Override public <T>T withNext(ContinuityStorePort.Session current,ObservationIdentity after,Instant deadline,PendingUiLifeAdvance.Work<T> work)throws IOException{return source.withNext(current,after,deadline,work);}
                @Override public NativeRequest preparePreclock(ContinuityStorePort.Session current,ActionCommand child,String requestId,NativeRequest base){throw new AssertionError("DATA source cannot grant preclock");}
            };
            scope.within(other,()->{assertThrows(IllegalArgumentException.class,()->readiness.inspect(source.command,source.last.originalFrame()));return null;});
            assertFalse(scope.active());assertEquals(captures,source.captures);assertEquals(reads,fixture.actual.nativePacketReads());
            borrowed.set(null);return null;
        });
    }
    /** Unregistered interface DATA only. The retained arm is a real canonical clock control, never a business Close,
     * M3 cause, pending publication, clearance permission or Root Ready. No continuation or Native submission is installed. */
    private final class PendingCaptureData implements PendingUiLifeAdvance.Source {
        final Fixture fixture; final ActionReceipt control; final ActionCommand ancestor; final ActionCommand command;
        PendingUiLifeAdvance.Current last; int captures, nextCaptures; boolean valid=true,failAfterCapture;
        PendingCaptureData() {
            fixture=new Fixture(false,false,false);
            control=fixture.submit(AdvancePrimitives.child(fixture.parent,fixture.initial,"pending-cache-real-arm",fixture.plan.armStep(),fixture.parent.deadline()));
            var settled=assertInstanceOf(ActionState.Settled.class,control.state());
            assertInstanceOf(ActionState.ControlApplied.class,settled.settlement());
            assertFalse(control.visibleGameplay());assertFalse(control.eligibleAdvance());
            last=fixture.inOriginal(same->captureData(fixture.current(fixture.parent,fixture.parent.deadline())));
            var frame=last.originalFrame();var lease=fixture.captures.get(frame).lease();var id=frame.identity();
            var terminal=new LifecycleIdentity(id.machineId(),id.game(),frame.sessionId(),lease.frame().connectionGeneration(),
                    new LifecycleIdentity.Subject(BigInteger.valueOf(71),"interface-data-predecessor",1,1),
                    new LifecycleIdentity.Frame(id.frame().snapshotId(),id.frame().revision(),id.frame().identity().nativeRevision(),id.frame().identity().dateRaw(),true,true),
                    new LifecycleIdentity.Character(id.frame().identity().player(),true),LifecycleIdentity.TerminalReason.CHANGED,
                    new LifecycleIdentity.Evidence(frame.originalEvidence(),lease.originalHello(),last.originalHistoryBasis(),last.originalDriver(),fixture.source.sourceRef()),frame.observedAt());
            var expected=new LifecycleExpectedPostcondition(terminal,fixture.source,"unregistered-pending-data/v1",LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,
                    List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),
                            new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false)));
            ancestor=new ActionCommand("interface-data-parent",new CommandOrigin.LifecycleTerminal(terminal),fixture.source,frame.sessionId(),expected.operation().key(),
                    new Obj(Map.of()),new CommandExpectation.LifecycleTerminal(expected),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),fixture.parent.deadline());
            var plan=new AdvancePlan(START,START.add(AdvancePlan.DAY),1,1,PendingUiLifeAdvance.POLICY,true,AdvancePlan.ClockMode.EXACT_SENTINEL,Optional.empty());
            command=new ActionCommand("interface-pending-life",id,fixture.source,frame.sessionId(),new OperationKey("life-advance"),new Obj(Map.of(AdvancePlan.KEY,plan.json())),
                    new ExpectedPostcondition(1,id,fixture.source,AdvancePlan.OBSERVER,plan.expected()),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),fixture.parent.deadline());
        }
        private PendingUiLifeAdvance.Current captureData(AdvanceObservationPort.Frame frame) {
            var actual=fixture.captures.get(frame).lease();var known=actual.driver();
            ExactRef driver=fixture.archive.preserveMaterial(new RawJson(known.driver().encode()));
            ExactRef receipt=fixture.archive.receiptReferenceOf(control);
            var applied=(ActionState.ControlApplied)((ActionState.Settled)control.state()).settlement();
            ExactRef originalRead=fixture.archive.readReferenceOf(applied.read());
            // These are retained original control refs for carrier DATA. Only the genuine Root issuer can assign
            // business pending/Close/clearance roles; this interface source cannot qualify or submit any child.
            return new PendingUiLifeAdvance.Current(frame,known,driver,known.originalHistoryBasis(),receipt,receipt,originalRead,control,
                    actual.executableSteps(),actual.bridgeCapabilities());
        }
        @Override public ActionCommand originalParent(){return ancestor;}
        @Override public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            fixture.actual.writer.requireSession(same);if(!valid)throw new IOException("unregistered DATA source invalidated");
        }
        @Override public <T>T withCurrent(ContinuityStorePort.Session same,Instant deadline,PendingUiLifeAdvance.Work<T> work)throws IOException {
            requireCurrent(same);captures++;last=captureData(fixture.current(command,deadline));T result=work.run(last);
            if(failAfterCapture)throw new IOException("actual callback failed after capture");return result;
        }
        @Override public <T>T withNext(ContinuityStorePort.Session same,ObservationIdentity after,Instant deadline,PendingUiLifeAdvance.Work<T> work)throws IOException {
            nextCaptures++;return withCurrent(same,deadline,work);
        }
        @Override public NativeRequest preparePreclock(ContinuityStorePort.Session same,ActionCommand child,String requestId,NativeRequest base) {
            throw new AssertionError("DATA carrier test cannot mint private preclock originals");
        }
    }
    private final class Fixture implements AdvanceObservationPort, PlanningReadPort, CompositeActionPort.Children {
        final ActionWriterIntegrationFixture actual;
        final ActionPorts.OutcomeArchive archive;
        final G2Source source;
        final Instant began=Instant.now();
        final DomainClock domainClock=new DomainClock();
        final List<ActionReceipt> children = new ArrayList<>();
        Optional<ActionReceipt> retainedParent=Optional.empty();
        final List<String> steps = new ArrayList<>();
        final List<String> actualStatusResponsePhases=new ArrayList<>();
        final Map<ExactRef,AdvanceObservationPort.Frame> produced = new HashMap<>();
        private record Captured(ReadinessAuthority.LeaseSnapshot lease,WriterContracts.Head head) { }
        final Map<AdvanceObservationPort.Frame,Captured> captures=new HashMap<>();
        final java.util.concurrent.atomic.AtomicReference<ReadContract<Status>> installedStatus=new java.util.concurrent.atomic.AtomicReference<>();
        final boolean modalAfterArm,unknownResume,modalAfterResume,watchMode,finishDay,canonicalMode;
        private record InstalledLife(AdvancePrimitives primitives,LifeAdvanceComposite life) { }
        boolean armed,canceled,resumed,rosterDriftAfterSpeed,laggingPause,exactStopFailure,pausedByCleanup;
        boolean speedDriftBeforeResume;
        int postArmParentReads;
        int reads,requests,entryReads,actualSpeed,nativeRevision=1,postResumeReads;
        final Obj nativeBase;
        final Obj base;
        final AdvanceObservationPort.Frame initial;
        final AdvancePlan plan;
        final ActionCommand parent;
        final AdvancePrimitives primitives;
        final LifeAdvanceComposite life;
        Fixture(boolean modalAfterArm,boolean unknownResume,boolean modalAfterResume) {
            this(modalAfterArm,unknownResume,modalAfterResume,false,false,1);
        }
        Fixture(boolean modalAfterArm,boolean unknownResume,boolean modalAfterResume,boolean watchMode,boolean finishDay,int initialSpeed) {
            this(modalAfterArm,unknownResume,modalAfterResume,watchMode,finishDay,initialSpeed,false);
        }
        Fixture(boolean modalAfterArm,boolean unknownResume,boolean modalAfterResume,boolean watchMode,boolean finishDay,int initialSpeed,boolean canonicalMode) {
            this.modalAfterArm=modalAfterArm;this.unknownResume=unknownResume;this.modalAfterResume=modalAfterResume;
            this.watchMode=watchMode;this.finishDay=finishDay;this.canonicalMode=canonicalMode;actualSpeed=initialSpeed;
            Obj packetState=json("""
                    {"paused":true,"map_ready":true,"speed":1,"date_raw":%d,
                     "local_player_id":0,"played_character":{"character_id":73,"alive":true},
                     "active_event":null,"pending_character_interaction":null,"one_life_terminal":false,"one_life_terminal_reason":null,
                     "diagnostics":{"bridge_pid":42,"connection_generation":5},"player_armies":[],"active_wars":[],
                     "top_exclusive_modal_choice_hint":{"status":"absent","owner_verified":true},"war_objective_assault_supported":true}
                    """.formatted(START));
            if(watchMode) {
                Obj own=watchArmy(11,73,2510,true),ally=watchArmy(22,40000,2511,false),enemy=watchArmy(33,50000,3011,false);
                packetState=packetState.with("player_armies",new Arr(List.of(own))).with("active_wars",new Arr(List.of(new Obj(Map.of(
                        "war_id",new IntegerValue(BigInteger.ONE),"player_side",new Text("attacker"),"player_relative_war_score",new IntegerValue(BigInteger.ZERO),
                        "allied_armies",new Arr(List.of(own,ally)),"enemy_armies",new Arr(List.of(enemy)))))));
            }
            nativeBase=packetState;
            String arm=ClockStatusRead.ARM_PREFIX+START+"-to-"+START.add(AdvancePlan.DAY)+"-speed-"+(watchMode?2:1)
                    +"-mode-terminal-a-"+(watchMode?"3-11-22-33":"0");
            var operations=new ArrayList<>(List.of("set-speed-1","set-speed-2","set-speed-5",arm,
                    ClockStatusRead.CANCEL_PREFIX+"37","resume-map","pause-map"));
            var scenarios=new ArrayList<ActionWriterIntegrationFixture.SoftwareActionScenario>();
            for(String step:operations) {
                OperationKey operation=new OperationKey(step);
                String capability=step.equals(arm)?ClockStatusRead.ARM_CAP:step.startsWith(ClockStatusRead.CANCEL_PREFIX)?ClockStatusRead.CANCEL_CAP:"game.command."+step;
                scenarios.add(new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,capability,this::observePrimitive,
                        ()->dispatchOriginal(step),Optional.of(()->raw(nativeToken(step,canceled?"canceled":"available",currentStatus()))),Optional.empty(),canonicalMode,Optional.empty()));
            }
            var readScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(ExactCk3Build.CK3_12004.executableSha256(),
                    "life-clock-software-fixture",reviewed->{
                        ReadContract<Status> contract=ClockStatusRead.registeredContract(reviewed);
                        assertTrue(installedStatus.compareAndSet(null,contract));return List.of(contract);
                    },request->{
                        assertEquals(ClockStatusRead.STEP,request.step());
                        actualStatusResponsePhases.add(steps.isEmpty()?"before_action":steps.getLast());
                        return raw(nativeToken(ClockStatusRead.STEP,"available",currentStatus()));
                    },Optional.of(ExactCk3Build.CK3_12004.version()),Set.of("game.state.pending-character-interaction"));
            var installedLife=new java.util.concurrent.atomic.AtomicReference<InstalledLife>();
            var compositeScenarios=canonicalMode?List.of(new ActionWriterIntegrationFixture.SoftwareCompositeScenario(LifeAdvanceComposite.HANDLER,
                    Set.of(new OperationKey("life-advance"),new OperationKey("life-advance-one-day")),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),context->{
                        InstalledLife graph=createCanonicalGraph(context);assertTrue(installedLife.compareAndSet(null,graph));
                        var replay=new LifeAdvanceRootReplay(context.frames());
                        return new ActionWriterIntegrationFixture.SoftwareCompositeInstallation(graph.life(),List.of(
                                replay.binding(new OperationKey("life-advance"),context.source().sourceRef()),
                                replay.binding(new OperationKey("life-advance-one-day"),context.source().sourceRef())));
                    })):List.<ActionWriterIntegrationFixture.SoftwareCompositeScenario>of();
            try {
                actual=new ActionWriterIntegrationFixture(temporary.resolve("life-"+actualFixtures.size()),false,readScenario,scenarios,compositeScenarios);
                actualFixtures.add(this);archive=actual.archive;source=actual.observationSource();
            }catch(IOException failure){throw new UncheckedIOException(failure);}
            initial=current(null,began.plusSeconds(30));base=initial.semantic();
            Set<OperationKey> available=watchMode?Set.of(new OperationKey("life-advance-one-day"),new OperationKey("set-speed-1"),
                    new OperationKey("set-speed-2"),new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map")):STEPS;
            Set<String> capabilities=captures.get(initial).lease().bridgeCapabilities();
            if(canonicalMode) {
                InstalledLife graph=Optional.ofNullable(installedLife.get()).orElseThrow();primitives=graph.primitives();life=graph.life();
            }else {
            var status=new ClockStatusRead(this,installedStatus.get(),archive);
            AdvanceReadiness.Port readiness=(command,frame)->{
                ExactRef facts=ExactRef.fromJson(toNode(frame.semantic().get("java_driver_facts_evidence")));
                return watchMode?AdvanceHistory.verifiedFacts(command,frame,List.of(),available,capabilities,45,true,facts)
                        :new AdvanceReadiness.Facts(frame.identity(),STEPS,capabilities,false,false,false,45,facts);
            };
            AdvanceClock clock=new AdvanceClock(this,status,readiness,domainClock,16,Duration.ofSeconds(1),Duration.ofSeconds(2));
            primitives=new AdvancePrimitives(this,status,domainClock,16);
            life=new LifeAdvanceComposite(this,readiness,clock,status,new ActionSnapshotReader(new SnapshotJournal(this)),archive,domainClock,
                    (command,guard,store)->{entryReads++;return Optional.empty();});
            }
            String session=actual.observationIdentity().sessionId();
            if(watchMode) {
                var request=new PlanningRequest(initial.identity(),source,session,began.plusSeconds(30),
                        new PlanningObservation(base,List.of(),available,capabilities,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
                var original=new ActionCommand("fixture-life",initial.identity(),source,session,new OperationKey("life-advance-one-day"),new Obj(Map.of()),
                        new ExpectedPostcondition(1,initial.identity(),source,"fixture/skeleton",List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                        new Claims(Set.of(),Set.of(),Set.of(),Set.of()),began.plusSeconds(30));
                parent=life.prepare(request,original);plan=AdvancePlan.decode(parent);
            }else {
                plan=new AdvancePlan(START,START.add(AdvancePlan.DAY),1,1,"fixture_exact_native_clock",true,AdvancePlan.ClockMode.EXACT_SENTINEL,Optional.empty());
                parent=new ActionCommand("fixture-life",initial.identity(),source,session,new OperationKey("life-advance"),
                        new Obj(Map.of(AdvancePlan.KEY,plan.json())),new ExpectedPostcondition(1,initial.identity(),source,AdvancePlan.OBSERVER,plan.expected()),
                        new Claims(Set.of(),Set.of(),Set.of(),Set.of()),began.plusSeconds(30));
            }
            assertEquals(arm,plan.armStep(),"software input and the actual prepared policy must address one exact native arm");
            // Constructor bootstrap is real capture, but test counters start at the first domain observation.
            reads=0;
        }
        private InstalledLife createCanonicalGraph(ActionWriterIntegrationFixture.SoftwareCompositeContext context) {
            var status=new ClockStatusRead(this,installedStatus.get(),context.archive());
            Set<OperationKey> available=watchMode?Set.of(new OperationKey("life-advance-one-day"),new OperationKey("set-speed-1"),
                    new OperationKey("set-speed-2"),new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map")):STEPS;
            AdvanceReadiness.Port readiness=(command,frame)->{
                ExactRef facts=ExactRef.fromJson(toNode(frame.semantic().get("java_driver_facts_evidence")));
                return watchMode?AdvanceHistory.verifiedFacts(command,frame,List.of(),available,context.bridgeCapabilities(),45,true,facts)
                        :new AdvanceReadiness.Facts(frame.identity(),STEPS,context.bridgeCapabilities(),false,false,false,45,facts);
            };
            var clock=new AdvanceClock(this,status,readiness,domainClock,16,Duration.ofSeconds(1),Duration.ofSeconds(2));
            return new InstalledLife(new AdvancePrimitives(this,status,domainClock,16),new LifeAdvanceComposite(this,readiness,clock,status,
                    new ActionSnapshotReader(context.journal()),context.archive(),domainClock,new LifeAdvanceRootReplay(context.frames())));
        }
        private static Obj watchArmy(int id,int owner,int province,boolean controllable) {
            return new Obj(Map.of("army_id",new IntegerValue(BigInteger.valueOf(id)),"owner_character_id",new IntegerValue(BigInteger.valueOf(owner)),
                    "current_province_id",new IntegerValue(BigInteger.valueOf(province)),"move_target_province_id",Nil.INSTANCE,
                    "in_combat",new Bool(false),"retreating",new Bool(false),"controllable",new Bool(controllable),
                    "army_state",new Text("regular"),"army_state_code",new IntegerValue(BigInteger.ONE),"route_province_ids",new Arr(List.of())));
        }
        @FunctionalInterface private interface SameWork<T> { T run(ContinuityStorePort.Session same)throws IOException; }
        private <T> T inOriginal(SameWork<T> work) {
            try {
                var held=actual.writer.activeSession();
                if(held.isPresent())return archive.inSession(held.orElseThrow(),ignored->{
                    try{return work.run(held.orElseThrow());}catch(IOException failure){throw new UncheckedIOException(failure);}
                });
                return actual.writer.locked(same->archive.inSession(same,ignored->{
                    try{return work.run(same);}catch(IOException failure){throw new UncheckedIOException(failure);}
                }));
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private boolean sameOriginalHead(WriterContracts.Head expected,WriterContracts.Head actual) {
            return org.xar.ck3.control.continuity.ContinuityJson.same(expected.state().toJson(),actual.state().toJson())
                    &&expected.documents().equals(actual.documents())&&expected.absent().equals(actual.absent())
                    &&expected.indexRepairs().equals(actual.indexRepairs())&&expected.snapshotNeedsRecovery()==actual.snapshotNeedsRecovery();
        }
        @Override public AdvanceObservationPort.Frame current(ActionCommand command,Instant deadline) {
            reads++;
            // The held ordinary entry is the actual archived Root frame. Until a child
            // has entered, replay its unchanged source/head instead of inventing a new entry.
            if(initial!=null && steps.isEmpty() && children.isEmpty())return inOriginal(same->{
                var original=captures.get(initial);
                if(original==null || !canonicalMode&&!sameOriginalHead(original.head(),same.head()))throw new IOException("original Life entry writer point drifted");
                RootGuardEvidence.requireHistory(guard(command.operation(),initial),archive,same);
                return initial;
            });
            // The external speed change appears only after an unchanged post-arm parent
            // frame; the arm child's own independent Status observation stays untouched.
            if(speedDriftBeforeResume&&armed&&!resumed&&!canceled&&command.actionId().equals(parent.actionId())
                    &&++postArmParentReads==2) {actualSpeed=5;nativeRevision++;}
            if(watchMode&&resumed)postResumeReads++;
            if(exactStopFailure&&resumed&&!pausedByCleanup){
                // Actual software PUSH observations may advance while the calendar stays fixed.
                nativeRevision++;domainClock.advance(Duration.ofMillis(500));
            }
            int version=nativeRevision+(watchMode&&resumed&&finishDay?(laggingPause&&postResumeReads>=3?2:1):0);
            Obj state=nativeBase.with("speed",new IntegerValue(BigInteger.valueOf(actualSpeed)));
            if(exactStopFailure&&resumed&&!pausedByCleanup)state=state.with("paused",new Bool(false));
            if(watchMode&&resumed&&finishDay)state=state.with("date_raw",new IntegerValue(START.add(AdvancePlan.DAY)));
            if(watchMode&&resumed&&finishDay&&laggingPause&&postResumeReads<3)state=state.with("paused",new Bool(false));
            if(rosterDriftAfterSpeed&&nativeRevision>1) {
                Obj war=object(array(state.get("active_wars"),"wars").getFirst(),"war");
                Obj enemy=object(array(war.get("enemy_armies"),"enemies").getFirst(),"enemy")
                        .with("current_province_id",new IntegerValue(BigInteger.valueOf(3012)));
                state=state.with("active_wars",new Arr(List.of(war.with("enemy_armies",new Arr(List.of(enemy))))));
            }
            if(armed&&modalAfterArm||resumed&&modalAfterResume)state=state.with("top_exclusive_modal_choice_hint",
                    json("{\"status\":\"present\",\"source\":\"application_main_pump_observed_modal_receiver\",\"owner_verified\":true,\"max_observation_age_ms\":2000,\"opaque_root_id\":\"fixture-modal-1\"}"));
            String snapshot="native:"+version;
            var packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",snapshot).put("revision",version);
            packet.set("state",StrictJson.parse(DriverJson.encode(state)));
            boolean ordinaryObservation=AdvancePolicy.truth(state,"paused")&&state.get("top_exclusive_modal_choice_hint") instanceof Obj hint
                    &&new Text("absent").equals(hint.get("status"));
            return inOriginal(same->{
                actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(packet)));
                for(int count=0;count<32;count++) {
                    AdvanceObservationPort.Frame captured;
                    if(ordinaryObservation)captured=actual.collector.currentOwned(same,actual.observationIdentity(),deadline,lease->{
                        var complete=lease.frame();
                        var provenance=new ObservationProvenance.Push(complete.identity().frame().snapshotId(),
                                complete.identity().frame().identity().nativeRevision(),complete.originalEvidence());
                        var frame=new AdvanceObservationPort.Frame(complete.identity(),complete.source(),complete.sessionId(),complete.semantic(),
                                provenance,complete.observedAt(),complete.originalEvidence());
                        captures.put(frame,new Captured(lease,same.head()));produced.put(frame.originalEvidence(),frame);return frame;
                    });
                    else {
                        NativeObservationPort.ObservedFrame observed;
                        try{observed=actual.physicalInputs().transport().observe(deadline);}
                        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("original software native observation interrupted",interrupted);}
                        ExactRef nativeFrame=archive.preserveNativeFrame(observed);
                        captured=actual.driverAuthority().withFrozenRawObservation(observed,same,frozen->{
                            var result=actual.physicalInputs().observationAssembler().assemble(observed,frozen.facts(),nativeFrame);
                            if(!(result instanceof DriverObservationAssembler.Complete complete))throw new IOException("actual post-action native/Driver frame is incomplete");
                            var provenance=new ObservationProvenance.Push(complete.identity().frame().snapshotId(),
                                    complete.identity().frame().identity().nativeRevision(),complete.originalEvidence());
                            var frame=new AdvanceObservationPort.Frame(complete.identity(),complete.source(),complete.sessionId(),complete.semantic(),provenance,
                                    complete.observedAt(),complete.originalEvidence());produced.put(frame.originalEvidence(),frame);return frame;
                        });
                    }
                    if(captured.identity().frame().snapshotId().equals(snapshot))return captured;
                }
                throw new IOException("the exact queued original software native frame was not observed within its bound");
            });
        }
        @Override public AdvanceObservationPort.Frame next(ActionCommand command,ObservationIdentity after,Instant deadline){return current(command,deadline);}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            requests++;
            return inOriginal(same->actual.reads.read(same,contract,request));
        }
        @Override public String nextActionId(){return "fixture-life.child."+(children.size()+1);}
        @Override public List<ActionReceipt> completed(){return List.copyOf(children);}
        @Override public ActionReceipt submit(ActionCommand command) {
            if(!canonicalMode)steps.add(command.operation().value());requests++;
            ActionReceipt receipt=actual.coordinator.execute(command);
            children.add(receipt);return receipt;
        }
        private void dispatchOriginal(String step)throws IOException {
            if(canonicalMode)steps.add(step);
            if(step.equals("resume-map")&&unknownResume)throw new IOException("original resume entered its actual native write; ACK unavailable");
            if(step.startsWith("set-speed-")){actualSpeed=Integer.parseInt(step.substring(10));if(watchMode)nativeRevision++;}
            if(step.startsWith(ClockStatusRead.ARM_PREFIX))armed=true;
            if(step.startsWith(ClockStatusRead.CANCEL_PREFIX))canceled=true;
            if(step.equals("resume-map")){resumed=true;if(exactStopFailure)nativeRevision++;}
            if(step.equals("pause-map")){pausedByCleanup=true;nativeRevision++;}
        }
        private ActionPorts.PostconditionResult observePrimitive(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
            return primitives.observe(command,attempt,dispatch);
        }
        private Status currentStatus() {
            if(!watchMode)return sentinel(canceled?State.IDLE:State.ARMED);
            boolean stop=resumed&&finishDay;int end=START.add(AdvancePlan.DAY).intValueExact();
            return new Status(canceled?State.IDLE:stop?State.TRIGGERED:State.ARMED,new CrossJsDecimalUInt64("37"),START.intValueExact(),end,
                    stop?end:START.intValueExact(),stop?end:0,2,Mode.TERMINAL_OR_SENTINEL,3,0,stop?1:0,0,stop?1:0,
                    stop?List.of("date_deadline"):List.of(),0,stop?0:-1,stop,stop,false,false);
        }
        private GuardEvidence guard(OperationKey operation,AdvanceObservationPort.Frame frame) {
            Captured captured=Optional.ofNullable(captures.get(frame)).orElseThrow();var lease=captured.lease();
            ExactRef capabilities=archive.preserveMaterial(raw(lease.capabilities()));
            ExactRef original=RootGuardEvidence.preserve(lease,operation,"fixture-recorded-life-entry",capabilities,archive,captured.head());
            return new GuardEvidence(frame.identity(),frame.source(),frame.sessionId(),lease.frame().connectionGeneration(),operation,
                    frame.originalEvidence(),lease.originalHello(),"fixture-recorded-life-entry",frame.observedAt(),began.plusSeconds(30),List.of(original));
        }
        CompositeExecution execution() {
            return new CompositeExecution(life.handlerId(),began,guard(parent.operation(),initial),
                    children.stream().map(value->new CompositeExecution.Child(value.command().actionId(),value.bodySha256())).toList());
        }
        AdvanceObservationPort.Frame rebuild(ActionCommand parent,LifeAdvanceEvidence.FrameRecord retained,ActionPorts.OutcomeArchive store) {
            return new LifeAdvanceRootReplay(this::complete).rebuild(parent,retained,store);
        }
        DriverObservationAssembler.Complete complete(NativeEffectEvidence.FrameBasis retained,ActionPorts.OutcomeArchive store) {
            return actual.frameLoader().load(retained,store);
        }
        ActionReceipt withActual(CompositeControlObservation control,List<ExpectedValue> values) {
            var effect=control.semantic();var changed=new ActionState.EffectObservation(effect.after(),effect.source(),effect.sessionId(),
                    effect.observerSchema(),List.copyOf(values),effect.provenance(),effect.observedAt(),effect.originalEvidence(),effect.supportingEvidence());
            return new ActionReceipt(1,100,parent,ActionCodec.bodySha256(parent),new ActionState.CompositeSettled(execution(),
                    new ActionState.CompositeControlApplied(new CompositeControlObservation(control.terminalStatus(),control.supportingReads(),changed))));
        }
        ActionReceipt withBasis(CompositeControlObservation control,ExactRef basis) {
            var effect=control.semantic();
            var changed=new ActionState.EffectObservation(effect.after(),effect.source(),effect.sessionId(),effect.observerSchema(),effect.actual(),
                    effect.provenance(),effect.observedAt(),effect.originalEvidence(),List.of(basis));
            return new ActionReceipt(1,100,parent,ActionCodec.bodySha256(parent),new ActionState.CompositeSettled(execution(),
                    new ActionState.CompositeControlApplied(new CompositeControlObservation(control.terminalStatus(),control.supportingReads(),changed))));
        }
    }
    private static final class SnapshotJournal implements ActionJournal {
        private final Fixture fixture;
        SnapshotJournal(Fixture fixture) { this.fixture = fixture; }
        @Override public <T> T locked(Function<LockedJournal,T> work) {
            return work.apply(new LockedJournal() {
                @Override public Optional<ActionReceipt> find(String actionId) {
                    if(fixture.retainedParent.isPresent()&&actionId.equals(fixture.parent.actionId()))return fixture.retainedParent;
                    if (fixture.parent != null && actionId.equals(fixture.parent.actionId())) return Optional.of(new ActionReceipt(1,100,fixture.parent,ActionCodec.bodySha256(fixture.parent),new ActionState.CompositeRunning(fixture.execution())));
                    return fixture.children.stream().filter(value -> value.command().actionId().equals(actionId)).findFirst();
                }
                @Override public ActionJournal.Snapshot snapshot() { return new ActionJournal.Snapshot(100,"a".repeat(64),List.copyOf(fixture.children),new ActionJournal.MissingHistoryBasis()); }
                @Override public List<ActionReceipt> unresolved() { return fixture.children.stream().filter(value -> !value.settled()).toList(); }
                @Override public ActionReceipt append(ActionCommand command, String digest, ActionState next) { throw new IllegalStateException("reconciliation fixture cannot mutate the journal"); }
            });
        }
        @Override public <T> T locked(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session session, Function<LockedJournal,T> work) { throw new IllegalStateException("unexpected borrowed journal call"); }
    }
}
