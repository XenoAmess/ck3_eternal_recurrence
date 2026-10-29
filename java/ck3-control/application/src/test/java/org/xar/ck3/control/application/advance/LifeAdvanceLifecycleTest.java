package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
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
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
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
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Exercises Life -> Clock -> actual primitive observer/reducer -> Status -> archive consumer.
 * The protocol fixture is offline; this suite grants no actual CK3 or Root installation qualification. */
final class LifeAdvanceLifecycleTest {
    private static final Instant NOW = Instant.parse("2026-10-23T17:00:00Z");
    private static final BigInteger START = BigInteger.valueOf(53_288_256);
    private static final ExactRef DEFINITION = new ExactRef("fixture/actual-native-definition.json", 1, "b".repeat(64));
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", DEFINITION);
    private static final Set<OperationKey> STEPS = Set.of(new OperationKey("set-speed-1"), new OperationKey("resume-map"), new OperationKey("pause-map"));
    private static final Set<String> CAPS = Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP);
    private static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);
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
    private static ObservationIdentity identity(Obj semantic) {
        return new ObservationIdentity(SOURCE.machineId(), new GameGeneration(4242, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(29829), integer(semantic.get("native_revision"), "native_revision"), integer(semantic.get("date_raw"), "date_raw")),
                        text(semantic.get("snapshot_id"), "snapshot_id"), integer(semantic.get("revision"), "revision"), text(semantic.get("episode_run_id"), "episode")), 1);
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
    @Test void unknownResumeExecutesTheActualPrimitivePendingBranchAndNeverCancelsOrReplays() {
        Fixture fixture = new Fixture(false, true, false);
        ActionPorts.Pending pending = assertInstanceOf(ActionPorts.Pending.class, fixture.life.run(fixture.parent, fixture));
        assertTrue(pending.reason().contains("unresolved"));
        assertEquals(List.of(fixture.plan.armStep(), "resume-map"), fixture.steps);
        assertFalse(fixture.children.getLast().settled());
        assertFalse(fixture.steps.stream().anyMatch(value -> value.startsWith(ClockStatusRead.CANCEL_PREFIX) || value.equals("pause-map")));
    }
    @Test void actualArmControlKeepsItsDispatchAndIndependentStatusChronologyWhileHistoricalAckIsRefused() {
        Fixture fixture = new Fixture(true, false, false);
        assertInstanceOf(ActionPorts.CompositeControlObserved.class, fixture.life.run(fixture.parent, fixture));
        ActionReceipt arm = fixture.children.getFirst();
        var settled = assertInstanceOf(ActionState.Settled.class, arm.state());
        var control = assertInstanceOf(ActionState.ControlApplied.class, settled.settlement());
        var acknowledgement = assertInstanceOf(NativeActionPort.AckReceived.class, settled.dispatch());
        NativeRequestChronology submission = acknowledgement.custody().orElseThrow();
        NativeRequestChronology independent = control.read().original().custody().orElseThrow();
        assertTrue(independent.writeEntered().order().compareTo(submission.responseReceived().order()) > 0);
        assertEquals(submission.custodyEpoch(), independent.custodyEpoch());
        assertDoesNotThrow(() -> ActionEffects.validate(arm.command(), settled.attempt(), settled.dispatch(), control));
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(arm.command(), settled.attempt(), control));
        var historical = new NativeActionPort.AckReceived(acknowledgement.requestId(), acknowledgement.nativeOk(),
                acknowledgement.originalResultToken(), acknowledgement.originalFrame(), acknowledgement.originalPacket(), acknowledgement.outbound());
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(arm.command(), settled.attempt(), historical, control));
        assertEquals(List.of(fixture.plan.armStep(), ClockStatusRead.CANCEL_PREFIX + "37"), fixture.steps);
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
    @Test void unifiedRootGuardProducerBindsTheSoftwareWriterPointAndMissingV3PointIsRejected() {
        Fixture fixture = new Fixture(false, false, false);
        var original = fixture.current(fixture.parent, fixture.parent.deadline());
        var guard = fixture.guard(fixture.parent.operation(), original);
        assertEquals(new RootGuardEvidence.WriterPoint(fixture.originalHead.state().sequence(), fixture.originalHead.digest()),
                RootGuardEvidence.writerPoint(guard, fixture.archive));
        Obj basis = object(parse(fixture.archive.loadMaterial(guard.supportingEvidence().getFirst()).bytes()), "actual unified Root basis");
        var fields = new HashMap<String, Value>(basis.members()); fields.remove("writer_point");
        ExactRef missing = fixture.archive.preserveMaterial(raw(new Obj(fields)));
        var invalid = new GuardEvidence(guard.origin(), guard.source(), guard.sessionId(), guard.connectionGeneration(), guard.operation(),
                guard.nativeEvidence(), guard.capabilityEvidence(), guard.authorityId(), guard.observedAt(), guard.validUntil(), List.of(missing));
        assertThrows(IllegalArgumentException.class, () -> RootGuardEvidence.writerPoint(invalid, fixture.archive));
        assertThrows(IllegalArgumentException.class, () -> new LifeAdvanceRootReplay(fixture::complete).read(fixture.parent, invalid, fixture.archive));
        assertTrue(fixture.steps.isEmpty()); assertEquals(0, fixture.requests);
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
    private record CampaignPreparation(Fixture fixture, PlanningRequest request, LifeAdvanceCommands commands) { }
    private static CampaignPreparation campaignPreparation() { return campaignPreparation(CAPS); }
    private static CampaignPreparation campaignPreparation(Set<String> bridgeCapabilities) {
        Fixture fixture=new Fixture(false,false,false);
        Set<OperationKey> available=Set.of(new OperationKey("life-advance"),new OperationKey("life-advance-one-day"),
                new OperationKey("set-speed-1"),new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map"));
        var request=new PlanningRequest(identity(fixture.base),SOURCE,"fixture-session",NOW.plusSeconds(30),
                new PlanningObservation(fixture.base,List.of(),available,bridgeCapabilities,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        AdvanceReadiness.Port readiness=(command,frame)->new AdvanceReadiness.Facts(frame.identity(),available,bridgeCapabilities,false,false,false,45,DEFINITION);
        var status=new ClockStatusRead(fixture,DEFINITION,fixture.archive);
        var clock=new AdvanceClock(fixture,status,readiness,CLOCK,16,Duration.ofSeconds(1),Duration.ofSeconds(2));
        var shared=new LifeAdvanceComposite(fixture,readiness,clock,status,new ActionSnapshotReader(new SnapshotJournal(fixture)),
                fixture.archive,CLOCK,(command,guard,store)->{fail("preparation must not acquire a submitted lifecycle entry");return Optional.empty();});
        return new CampaignPreparation(fixture,request,new LifeAdvanceCommands(shared));
    }
    private static CampaignDeadline.Cap campaignCap(int boundaryDays) {
        BigInteger boundary=START.add(AdvancePlan.DAY.multiply(BigInteger.valueOf(boundaryDays)));
        return new CampaignDeadline.Cap("campaign-fixture",CampaignDeadline.CALENDAR_PROFILE,START,START.add(AdvancePlan.DAY),
                boundary,START.add(AdvancePlan.DAY.multiply(BigInteger.valueOf(360))),START.add(AdvancePlan.DAY),CampaignDeadline.Status.ADVANCE);
    }
    private static Obj campaignSelection(String step) {
        return new Obj(Map.of("selected_step",new Text(step),"reason",new Text("source-bound campaign preparation")));
    }
    @Test void actualLifeProducerCarriesCampaignCapFromThirtyDaysToNativeTargetAndPreservesExactDay() {
        var actual=campaignPreparation();var generic=new OperationKey("life-advance");var detail=campaignSelection(generic.value());
        ActionCommand normal=actual.commands().prepare(actual.request(),generic,new Obj(Map.of()),detail).orElseThrow();
        assertEquals(30,AdvancePlan.decode(normal).horizonDays());
        assertEquals(AdvancePlan.ClockMode.POLLED,AdvancePlan.decode(normal).clockMode());
        assertTrue(AdvancePlan.decode(normal).campaignDeadline().isEmpty());
        var cap=campaignCap(1);Obj maximum=new Obj(Map.of("maximum_target_date_raw",new IntegerValue(cap.boundaryDateRaw())));
        ActionCommand limited=actual.commands().prepare(actual.request(),generic,maximum,detail,cap).orElseThrow();
        AdvancePlan plan=AdvancePlan.decode(limited);
        assertEquals(1,plan.horizonDays());assertFalse(plan.exactOneDay());
        assertEquals(AdvancePlan.ClockMode.CAMPAIGN_SENTINEL,plan.clockMode());
        assertEquals(cap.boundaryDateRaw(),plan.targetDateRaw());
        assertEquals(cap.boundaryDateRaw(),plan.campaignDeadline().orElseThrow().boundaryDateRaw());
        assertEquals(cap.endpointDateRaw(),plan.campaignDeadline().orElseThrow().endpointDateRaw());
        assertEquals(plan.targetDateRaw().intValueExact(),AdvancePrimitives.armSpec(plan.armStep()).targetDateRaw());
        assertEquals(plan.expected(),limited.expected().values());
        var exact=new OperationKey("life-advance-one-day");
        ActionCommand oneDay=actual.commands().prepare(actual.request(),exact,maximum,campaignSelection(exact.value()),cap).orElseThrow();
        AdvancePlan exactPlan=AdvancePlan.decode(oneDay);
        assertTrue(exactPlan.exactOneDay());assertEquals(1,exactPlan.horizonDays());
        assertEquals(AdvancePlan.ClockMode.EXACT_SENTINEL,exactPlan.clockMode());
        assertTrue(exactPlan.campaignDeadline().isPresent());
        assertEquals(exactPlan.expected(),oneDay.expected().values());
        assertTrue(actual.fixture().steps.isEmpty());assertTrue(actual.fixture().children.isEmpty());assertEquals(0,actual.fixture().requests);
    }
    @Test void actualLifeProducerRetainsEarlierMaximumWithoutInventingCalendarBoundaryAndRoundTripsThePlan() {
        var actual=campaignPreparation();var operation=new OperationKey("life-advance");var cap=campaignCap(5);
        BigInteger maximum=START.add(AdvancePlan.DAY.multiply(BigInteger.TWO));
        Obj arguments=new Obj(Map.of("maximum_target_date_raw",new IntegerValue(maximum)));
        ActionCommand command=actual.commands().prepare(actual.request(),operation,arguments,campaignSelection(operation.value()),cap).orElseThrow();
        AdvancePlan plan=AdvancePlan.decode(command);var retained=plan.campaignDeadline().orElseThrow();
        assertEquals(2,plan.horizonDays());assertEquals(maximum,plan.targetDateRaw());
        assertEquals(maximum,retained.requestedTargetDateRaw());assertEquals(cap.boundaryDateRaw(),retained.boundaryDateRaw());
        assertEquals(cap.endpointDateRaw(),retained.endpointDateRaw());assertEquals(AdvancePlan.ClockMode.CAMPAIGN_SENTINEL,plan.clockMode());
        ActionCommand decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
        assertEquals(command,decoded);assertEquals(plan,AdvancePlan.decode(decoded));
        assertEquals(plan.targetDateRaw().intValueExact(),AdvancePrimitives.armSpec(AdvancePlan.decode(decoded).armStep()).targetDateRaw());
        assertEquals(plan.expected(),decoded.expected().values());
        ActionCommand dataOnly=actual.commands().prepare(actual.request(),operation,arguments,campaignSelection(operation.value())).orElseThrow();
        assertEquals(2,AdvancePlan.decode(dataOnly).horizonDays());assertTrue(AdvancePlan.decode(dataOnly).campaignDeadline().isEmpty());
        assertEquals(AdvancePlan.ClockMode.POLLED,AdvancePlan.decode(dataOnly).clockMode());
        assertTrue(actual.fixture().steps.isEmpty());assertTrue(actual.fixture().children.isEmpty());assertEquals(0,actual.fixture().requests);
    }
    @Test void actualLifeProducerRejectsWrongTypedAndNonForwardWholeDayMaximums() {
        var actual=campaignPreparation();var operation=new OperationKey("life-advance");var cap=campaignCap(5);
        for(Value invalid:List.<Value>of(new Bool(true),new DecimalValue("2.0"),Nil.INSTANCE,new IntegerValue(START),
                new IntegerValue(START.subtract(AdvancePlan.DAY)),new IntegerValue(START.add(BigInteger.ONE)))) {
            Obj arguments=new Obj(Map.of("maximum_target_date_raw",invalid));
            assertThrows(IllegalArgumentException.class,()->actual.commands().prepare(actual.request(),operation,arguments,
                    campaignSelection(operation.value()),cap));
        }
        assertTrue(actual.fixture().steps.isEmpty());assertTrue(actual.fixture().children.isEmpty());assertEquals(0,actual.fixture().requests);
    }
    @Test void missingAdvertisedSentinelDoesNotDowngradeCampaignCapOrBreakPolledPreparation() {
        var actual=campaignPreparation(Set.of());var operation=new OperationKey("life-advance");
        var detail=campaignSelection(operation.value());Obj arguments=new Obj(Map.of());
        ActionCommand normal=actual.commands().prepare(actual.request(),operation,arguments,detail).orElseThrow();
        assertEquals(30,AdvancePlan.decode(normal).horizonDays());
        assertEquals(AdvancePlan.ClockMode.POLLED,AdvancePlan.decode(normal).clockMode());
        assertTrue(AdvancePlan.decode(normal).campaignDeadline().isEmpty());
        int reads=actual.fixture().reads;
        assertTrue(actual.commands().prepare(actual.request(),operation,arguments,detail,campaignCap(1)).isEmpty());
        assertEquals(reads,actual.fixture().reads);
        assertTrue(actual.fixture().steps.isEmpty());assertTrue(actual.fixture().children.isEmpty());assertEquals(0,actual.fixture().requests);
    }
    private static final class Fixture implements AdvanceObservationPort, PlanningReadPort, CompositeActionPort.Children {
        final MemoryArchive archive = new MemoryArchive();
        final WriterContracts.Head originalHead = softwareHead();
        final java.util.UUID custodyEpoch = java.util.UUID.randomUUID();
        long observationTicks; long endpointOrder;
        final List<ActionReceipt> children = new ArrayList<>(); final List<String> steps = new ArrayList<>();
        final Map<ExactRef, AdvanceObservationPort.Frame> produced = new HashMap<>();
        final boolean modalAfterArm; final boolean unknownResume; final boolean modalAfterResume; final boolean watchMode; final boolean finishDay;
        boolean armed; boolean canceled; boolean resumed; boolean rosterDriftAfterSpeed; boolean laggingPause;
        int reads; int requests; int entryReads; int actualSpeed; int nativeRevision=1; int postResumeReads;
        final Obj base; final AdvancePlan plan; final ActionCommand parent; final AdvancePrimitives primitives; final LifeAdvanceComposite life;
        private static WriterContracts.Head softwareHead() {
            Obj state = json("""
                    {"schema":"root.ck3.continuity-window/v1","sequence":100,"window_id":1,
                     "start_date_raw":53288256,"target_date_raw":53288280,"target_days":1,
                     "status":"running","last_settled_cycles":0,"last_settled_date_raw":53288256}
                    """).with("machine_id", new Text(SOURCE.machineId()));
            return new WriterContracts.Head(ContinuityState.fromJson(toNode(state), SOURCE.machineId()),
                    List.of(), List.of(), List.of(), false);
        }
        Fixture(boolean modalAfterArm, boolean unknownResume, boolean modalAfterResume) {
            this(modalAfterArm,unknownResume,modalAfterResume,false,false,1);
        }
        Fixture(boolean modalAfterArm, boolean unknownResume, boolean modalAfterResume, boolean watchMode, boolean finishDay, int initialSpeed) {
            this.modalAfterArm = modalAfterArm; this.unknownResume = unknownResume; this.modalAfterResume = modalAfterResume;
            this.watchMode=watchMode; this.finishDay=finishDay; this.actualSpeed=initialSpeed;
            ExactRef manifest = archive.preserveMaterial(raw(json("{\"schema\":\"fixture-original-driver-facts\",\"actual_full_driver\":true}")));
            Obj initial = json("""
                    {"snapshot_id":"native:1","revision":1,"native_revision":1,"date_raw":53288256,
                     "paused":true,"map_ready":true,"speed":1,"episode_run_id":"fixture-episode","episode_character_id":29829,
                     "local_player_id":0,"played_character":{"character_id":29829,"alive":true},
                     "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
                     "diagnostics":{"bridge_pid":4242,"connection_generation":1},"player_armies":[],"active_wars":[],
                     "top_exclusive_modal_choice_hint":{"status":"absent"},"war_objective_assault_supported":true}
                    """).with("java_driver_facts_evidence", reference(manifest));
            if (watchMode) {
                Obj own=watchArmy(11,29829,2510,true), ally=watchArmy(22,40000,2511,false), enemy=watchArmy(33,50000,3011,false);
                Obj hello=new Obj(Map.of("ck3_build_match",new Bool(true),"expected_ck3_version",new Text(ExactCk3Build.CK3_12004.version()),"expected_ck3_sha256",new Text(ExactCk3Build.CK3_12004.executableSha256())));
                initial=initial.with("speed",new IntegerValue(BigInteger.valueOf(initialSpeed))).with("one_life_terminal",new Bool(false))
                        .with("top_exclusive_modal_choice_hint",json("{\"status\":\"absent\",\"owner_verified\":true}"))
                        .with("diagnostics",json("{\"bridge_pid\":4242,\"connection_generation\":1,\"connected\":true}").with("hello",hello))
                        .with("player_armies",new Arr(List.of(own))).with("active_wars",new Arr(List.of(new Obj(Map.of("war_id",new IntegerValue(BigInteger.ONE),
                                "player_relative_war_score",new IntegerValue(BigInteger.ZERO),"allied_armies",new Arr(List.of(own,ally)),"enemy_armies",new Arr(List.of(enemy)))))));
            }
            base=initial;
            ClockStatusRead status = new ClockStatusRead(this, DEFINITION, archive);
            Set<OperationKey> available=watchMode ? Set.of(new OperationKey("life-advance-one-day"),new OperationKey("set-speed-1"),new OperationKey("set-speed-2"),new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map")) : STEPS;
            Set<String> capabilities=watchMode ? new java.util.HashSet<>(CAPS) : CAPS;
            if (watchMode) capabilities.add("game.state.pending-character-interaction");
            AdvanceReadiness.Port readiness = (command, frame) -> watchMode ? AdvanceHistory.verifiedFacts(command,frame,List.of(),available,capabilities,45,true,manifest)
                    : new AdvanceReadiness.Facts(frame.identity(), STEPS, CAPS, false, false, false, 45, manifest);
            AdvanceClock clock = new AdvanceClock(this, status, readiness, CLOCK, 16, Duration.ofSeconds(1), Duration.ofSeconds(2));
            primitives = new AdvancePrimitives(this, status, CLOCK, 16);
            life = new LifeAdvanceComposite(this, readiness, clock, status, new ActionSnapshotReader(new SnapshotJournal(this)), archive, CLOCK,
                    (command, guard, store) -> { entryReads++; return Optional.empty(); });
            if (watchMode) {
                var request=new PlanningRequest(identity(base),SOURCE,"fixture-session",NOW.plusSeconds(30),
                        new PlanningObservation(base,List.of(),available,capabilities,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
                var original=new ActionCommand("fixture-life",identity(base),SOURCE,"fixture-session",new OperationKey("life-advance-one-day"),new Obj(Map.of()),
                        new ExpectedPostcondition(1,identity(base),SOURCE,"fixture/skeleton",List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                        new Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
                parent=life.prepare(request,original); plan=AdvancePlan.decode(parent);
            } else {
                plan = new AdvancePlan(START, START.add(AdvancePlan.DAY), 1, 1, "fixture_exact_native_clock", true, AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty());
                parent = new ActionCommand("fixture-life", identity(base), SOURCE, "fixture-session", new OperationKey("life-advance"),
                        new Obj(Map.of(AdvancePlan.KEY, plan.json())), new ExpectedPostcondition(1, identity(base), SOURCE, AdvancePlan.OBSERVER, plan.expected()),
                        new Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
            }
        }
        private static Obj watchArmy(int id,int owner,int province,boolean controllable) {
            return new Obj(Map.of("army_id",new IntegerValue(BigInteger.valueOf(id)),"owner_character_id",new IntegerValue(BigInteger.valueOf(owner)),
                    "current_province_id",new IntegerValue(BigInteger.valueOf(province)),"move_target_province_id",Nil.INSTANCE,"in_combat",new Bool(false),
                    "retreating",new Bool(false),"controllable",new Bool(controllable),"army_state",new Text("regular"),"army_state_code",new IntegerValue(BigInteger.ONE),"route_province_ids",new Arr(List.of())));
        }
        @Override public AdvanceObservationPort.Frame current(ActionCommand command, Instant deadline) {
            reads++;
            Obj semantic = base;
            if (watchMode) {
                if (resumed) postResumeReads++;
                int revision=nativeRevision+(resumed && finishDay ? laggingPause && postResumeReads>=3 ? 2 : 1 : 0);
                semantic=semantic.with("speed",new IntegerValue(BigInteger.valueOf(actualSpeed))).with("native_revision",new IntegerValue(BigInteger.valueOf(revision)))
                        .with("revision",new IntegerValue(BigInteger.valueOf(revision))).with("snapshot_id",new Text("native:"+revision));
                if (resumed && finishDay) semantic=semantic.with("date_raw",new IntegerValue(START.add(AdvancePlan.DAY)));
                if (resumed && finishDay && laggingPause && postResumeReads<3) semantic=semantic.with("paused",new Bool(false));
                if (rosterDriftAfterSpeed && nativeRevision>1) {
                    Obj war=object(array(semantic.get("active_wars"),"wars").getFirst(),"war");
                    Obj enemy=object(array(war.get("enemy_armies"),"enemies").getFirst(),"enemy").with("current_province_id",new IntegerValue(BigInteger.valueOf(3012)));
                    semantic=semantic.with("active_wars",new Arr(List.of(war.with("enemy_armies",new Arr(List.of(enemy))))));
                }
            }
            if (armed && modalAfterArm || resumed && modalAfterResume) semantic = semantic.with("top_exclusive_modal_choice_hint",
                    json("{\"status\":\"present\",\"source\":\"application_main_pump_observed_modal_receiver\",\"owner_verified\":true,\"max_observation_age_ms\":2000,\"opaque_root_id\":\"fixture-modal-1\"}"))
                    .with("revision", new IntegerValue(BigInteger.TWO)).with("snapshot_id", new Text("native:modal"));
            ExactRef packet = archive.preserveMaterial(raw(new Obj(Map.of("semantic", semantic, "actual_read", new Text("semantic-" + reads)))));
            var observed = identity(semantic);
            var provenance = new ObservationProvenance.Push(observed.frame().snapshotId(), observed.frame().identity().nativeRevision(), packet);
            var frame = new AdvanceObservationPort.Frame(observed, SOURCE, "fixture-session", semantic, provenance, nextObservation(), packet);
            produced.put(packet, frame); return frame;
        }
        @Override public AdvanceObservationPort.Frame next(ActionCommand command, ObservationIdentity after, Instant deadline) { return current(command, deadline); }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            String id = "status-query-" + ++requests;
            var frame = current(parent, request.deadline());
            var binding = guard(request.operation(), frame);
            var readGuard = new PlanningReadGuard(binding, true, true, true, "c".repeat(64));
            var exchange = write(id, ClockStatusRead.STEP, frame);
            var ack = ack(exchange, nativeToken(ClockStatusRead.STEP, "available", currentStatus()));
            var receipt = new PlanningReadReceipt(request, contract.contractId(), id, readGuard, readGuard, ack);
            ExactRef originalReceipt = archive.preserveRead(receipt); return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, originalReceipt);
        }
        @Override public String nextActionId() { return "fixture-life.child." + (children.size() + 1); }
        @Override public List<ActionReceipt> completed() { return List.copyOf(children); }
        @Override public ActionReceipt submit(ActionCommand command) {
            steps.add(command.operation().value()); String id = "child-native-" + ++requests;
            var frame = current(parent, command.deadline());
            var attempt = new ActionState.Attempt(id, frame.observedAt(), guard(command.operation(), frame), primitives.prepare(command));
            archive.preserveRequest(attempt.preparedRequest());
            var exchange = write(id, command.operation().value(), frame);
            NativeActionPort.DispatchOutcome dispatch;
            if (command.operation().value().equals("resume-map") && unknownResume)
                dispatch = new NativeActionPort.Unknown(id, "original resume write outcome unknown", exchange.outbound().originalPacket(), Optional.empty());
            else {
                if (command.operation().value().startsWith("set-speed-")) { actualSpeed=Integer.parseInt(command.operation().value().substring(10)); if (watchMode) nativeRevision++; }
                if (command.operation().value().equals(plan.armStep())) armed = true;
                if (command.operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX)) canceled = true;
                if (command.operation().value().equals("resume-map")) resumed = true;
                dispatch = ack(exchange, nativeToken(command.operation().value(), canceled ? "canceled" : "available", currentStatus()));
            }
            ActionPorts.PostconditionResult observed = primitives.observe(command, attempt, dispatch);
            ActionState state;
            if (observed instanceof ActionPorts.Pending pending) state = new ActionState.Unknown(Optional.of(attempt), Optional.of(dispatch), pending.reason(), pending.evidence());
            else {
                ActionState.Settlement settlement = observed instanceof ActionPorts.ControlObserved value ? value.observation()
                        : new ActionState.Applied(((ActionPorts.EffectObserved) observed).observation());
                try { ActionEffects.validate(command, attempt, dispatch, settlement); state = new ActionState.Settled(attempt, dispatch, settlement); }
                catch (IllegalArgumentException invalid) { state = new ActionState.Unknown(Optional.of(attempt), Optional.of(dispatch), invalid.getMessage(), List.of(frame.originalEvidence())); }
            }
            ActionReceipt receipt = new ActionReceipt(1, children.size() + 1, command, ActionCodec.bodySha256(command), state);
            children.add(receipt); archive.preserveReceipt(receipt); return receipt;
        }
        private Status currentStatus() {
            if (!watchMode) return sentinel(canceled ? State.IDLE : State.ARMED);
            boolean stop=resumed && finishDay; int end=START.add(AdvancePlan.DAY).intValueExact();
            return new Status(canceled ? State.IDLE : stop ? State.TRIGGERED : State.ARMED,new CrossJsDecimalUInt64("37"),START.intValueExact(),end,
                    stop ? end : START.intValueExact(),stop ? end : 0,2,Mode.TERMINAL_OR_SENTINEL,3,0,stop ? 1 : 0,0,stop ? 1 : 0,
                    stop ? List.of("date_deadline") : List.of(),0,stop ? 0 : -1,stop,stop,false,false);
        }
        private record SoftwareExchange(NativeActionPort.OutboundPacket outbound,
                NativeRequestChronology.Event entered, NativeRequestChronology.Event completed) { }
        private Instant nextObservation() { return NOW.plusMillis(++observationTicks); }
        private NativeRequestChronology.Event endpointEvent() {
            return new NativeRequestChronology.Event(BigInteger.valueOf(++endpointOrder), nextObservation());
        }
        private static byte[] packet(RawJson frame) {
            byte[] body = frame.bytes();
            return java.nio.ByteBuffer.allocate(body.length + 4).order(java.nio.ByteOrder.LITTLE_ENDIAN)
                    .putInt(body.length).put(body).array();
        }
        /** Software I/O edge only: record actual local write/receive calls, not times inferred from SEM or ACK meaning. */
        private SoftwareExchange write(String id, String step, AdvanceObservationPort.Frame before) {
            RawJson original = raw(new Obj(Map.of("type", new Text("execute_step"), "protocol_version", new IntegerValue(BigInteger.ONE),
                    "request_id", new Text(id), "step", new Text(step),
                    "expected_revision", new IntegerValue(before.identity().frame().identity().nativeRevision()))));
            var entered = endpointEvent();
            var wire = new java.io.ByteArrayOutputStream(); wire.writeBytes(packet(original));
            var completed = endpointEvent();
            return new SoftwareExchange(new NativeActionPort.OutboundPacket(id, wire.toByteArray()), entered, completed);
        }
        private NativeActionPort.AckReceived ack(SoftwareExchange exchange, Obj token) {
            String id = exchange.outbound().requestId(); RawJson result = raw(token);
            RawJson original = raw(new Obj(Map.of("type", new Text("command_result"), "protocol_version", new IntegerValue(BigInteger.ONE),
                    "request_id", new Text(id), "ok", new Bool(true), "result", token)));
            byte[] received = new java.io.ByteArrayInputStream(packet(original)).readAllBytes();
            var response = endpointEvent();
            var session = new NativeObservationPort.TransportSession(SOURCE.machineId(), parent.before().game(), BigInteger.ONE, "fixture-session");
            var custody = new NativeRequestChronology(session, custodyEpoch, id,
                    NativeRequestChronology.PacketIdentity.of(exchange.outbound().originalPacket()),
                    NativeRequestChronology.PacketIdentity.of(received), exchange.entered(), exchange.completed(), response);
            var ack = new NativeActionPort.AckReceived(id, true, Optional.of(result), original, received,
                    Optional.of(exchange.outbound()), Optional.of(custody));
            custody.verify(ack); archive.preserve(ack); return ack;
        }
        private GuardEvidence guard(OperationKey operation, AdvanceObservationPort.Frame frame) {
            ExactRef semantic = archive.preserveMaterial(raw(frame.semantic()));
            Value driver = frame.semantic().get("java_driver_facts_evidence");
            ExactRef driverRef = ExactRef.fromJson(toNode(driver));
            var assembled = complete(new NativeEffectEvidence.FrameBasis(frame.originalEvidence(), driverRef), archive);
            var originalSemantic = new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(
                    frame.identity(), semantic, frame.originalEvidence(), driverRef, driverRef, frame.observedAt());
            var originals = new RootGuardEvidence.PhysicalReadOriginals(assembled, originalSemantic,
                    DEFINITION, DEFINITION, driverRef, driverRef);
            ExactRef originalBasis = RootGuardEvidence.preservePhysicalRead(originals, operation,
                    "fixture-real-primitive-observer", archive, originalHead);
            return new GuardEvidence(frame.identity(), SOURCE, "fixture-session", BigInteger.ONE, operation, frame.originalEvidence(), DEFINITION,
                    "fixture-real-primitive-observer", frame.observedAt(), NOW.plusSeconds(30), List.of(originalBasis));
        }
        CompositeExecution execution() {
            var start = produced.values().stream().filter(value -> value.identity().equals(parent.before())).min(java.util.Comparator.comparing(AdvanceObservationPort.Frame::observedAt)).orElseThrow();
            return new CompositeExecution(life.handlerId(), NOW, guard(parent.operation(), start), children.stream().map(value -> new CompositeExecution.Child(value.command().actionId(), value.bodySha256())).toList());
        }
        AdvanceObservationPort.Frame rebuild(ActionCommand parent, LifeAdvanceEvidence.FrameRecord retained, ActionPorts.OutcomeArchive store) {
            return Optional.ofNullable(produced.get(retained.nativeFrame())).orElseThrow();
        }
        DriverObservationAssembler.Complete complete(NativeEffectEvidence.FrameBasis retained, ActionPorts.OutcomeArchive store) {
            var original = Optional.ofNullable(produced.get(retained.nativeFrame())).orElseThrow();
            assertEquals(reference(retained.driverFacts()), original.semantic().get("java_driver_facts_evidence"));
            return new DriverObservationAssembler.Complete(original.identity(), original.source(), original.sessionId(), BigInteger.ONE,
                    original.semantic(), original.originalEvidence(), original.observedAt(), DriverObservationAssembler.bindingSha256(original.semantic()));
        }
        ActionReceipt withActual(CompositeControlObservation control, List<ExpectedValue> values) {
            var effect = control.semantic(); var changed = new ActionState.EffectObservation(effect.after(), effect.source(), effect.sessionId(), effect.observerSchema(), List.copyOf(values),
                    effect.provenance(), effect.observedAt(), effect.originalEvidence(), effect.supportingEvidence());
            return new ActionReceipt(1, 100, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeSettled(execution(),
                    new ActionState.CompositeControlApplied(new CompositeControlObservation(control.terminalStatus(), control.supportingReads(), changed))));
        }
        ActionReceipt withBasis(CompositeControlObservation control, ExactRef basis) {
            var effect = control.semantic();
            var changed = new ActionState.EffectObservation(effect.after(), effect.source(), effect.sessionId(), effect.observerSchema(), effect.actual(),
                    effect.provenance(), effect.observedAt(), effect.originalEvidence(), List.of(basis));
            return new ActionReceipt(1, 100, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeSettled(execution(),
                    new ActionState.CompositeControlApplied(new CompositeControlObservation(control.terminalStatus(), control.supportingReads(), changed))));
        }
    }
    private static final class SnapshotJournal implements ActionJournal {
        private final Fixture fixture;
        SnapshotJournal(Fixture fixture) { this.fixture = fixture; }
        @Override public <T> T locked(Function<LockedJournal,T> work) {
            return work.apply(new LockedJournal() {
                @Override public Optional<ActionReceipt> find(String actionId) {
                    if (fixture.parent != null && actionId.equals(fixture.parent.actionId())) return Optional.of(new ActionReceipt(1,100,fixture.parent,ActionCodec.bodySha256(fixture.parent),new ActionState.CompositeRunning(fixture.execution())));
                    return fixture.children.stream().filter(value -> value.command().actionId().equals(actionId)).findFirst();
                }
                @Override public ActionJournal.Snapshot snapshot() { return new ActionJournal.Snapshot(100,fixture.originalHead.digest(),List.copyOf(fixture.children),new ActionJournal.MissingHistoryBasis()); }
                @Override public List<ActionReceipt> unresolved() { return fixture.children.stream().filter(value -> !value.settled()).toList(); }
                @Override public ActionReceipt append(ActionCommand command, String digest, ActionState next) { throw new IllegalStateException("reconciliation fixture cannot mutate the journal"); }
            });
        }
        @Override public <T> T locked(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session session, Function<LockedJournal,T> work) { throw new IllegalStateException("unexpected borrowed journal call"); }
    }
    private static final class MemoryArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,RawJson> materials = new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes = new HashMap<>();
        private final Map<NativeActionPort.DispatchOutcome,ExactRef> outcomeRefs = new HashMap<>();
        private final Map<ExactRef,PlanningReadReceipt> reads = new HashMap<>();
        private final Map<PlanningReadReceipt,ExactRef> readRefs = new HashMap<>();
        private final Map<ExactRef,ActionReceipt> receipts = new HashMap<>();
        private final Map<ActionReceipt,ExactRef> receiptRefs = new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests = new HashMap<>();
        private final Map<NativeRequest,ExactRef> requestRefs = new HashMap<>();
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) {
            ExactRef ref = preserveMaterial(raw(new Obj(Map.of("native_request_id", new Text(value.requestId()))))); outcomes.put(ref, value); outcomeRefs.put(value, ref); return ref;
        }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { return Optional.ofNullable(outcomes.get(ref)).orElseThrow(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { return Optional.ofNullable(outcomeRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) {
            preserve(value.original()); ExactRef ref = preserveMaterial(raw(new Obj(Map.of("read_request_id", new Text(value.requestId()))))); reads.put(ref, value); readRefs.put(value, ref); return ref;
        }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { return Optional.ofNullable(reads.get(ref)).orElseThrow(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { return Optional.ofNullable(readRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) {
            ExactRef ref = preserveMaterial(raw(new Obj(Map.of("action_id", new Text(value.command().actionId()), "sequence", new IntegerValue(BigInteger.valueOf(value.sequence())), "body", new Text(value.bodySha256())))));
            receipts.put(ref, value); receiptRefs.put(value, ref); return ref;
        }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { return Optional.ofNullable(receipts.get(ref)).orElseThrow(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { return Optional.ofNullable(receiptRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveMaterial(RawJson value) {
            ExactRef ref = new ExactRef("D:/software-fixtures/life-advance/archive/" + DriverJson.sha256(value.bytes()) + ".json", value.bytes().length, DriverJson.sha256(value.bytes())); materials.put(ref, value); return ref;
        }
        @Override public RawJson loadMaterial(ExactRef ref) { return Optional.ofNullable(materials.get(ref)).orElseThrow(); }
        @Override public RawJson loadFullMaterial(ExactRef ref) {
            byte[] original = loadMaterial(ref).bytes();
            assertEquals(ref.bytes(), original.length); assertEquals(ref.sha256(), ActionCodec.sha256(original));
            return RawJson.fullMaterial(original);
        }
        @Override public ExactRef materialReferenceOf(RawJson value) {
            ExactRef ref = new ExactRef("D:/software-fixtures/life-advance/archive/" + DriverJson.sha256(value.bytes()) + ".json", value.bytes().length, DriverJson.sha256(value.bytes()));
            if (!value.equals(materials.get(ref))) throw new IllegalStateException("unarchived original material"); return ref;
        }
        @Override public ExactRef preserveRequest(NativeRequest value) {
            ExactRef ref = preserveMaterial(raw(new Obj(Map.of("step", new Text(value.step()), "capability", value.requiredCapability().<Value>map(Text::new).orElse(Nil.INSTANCE)))));
            requests.put(ref, value); requestRefs.put(value, ref); return ref;
        }
        @Override public NativeRequest loadRequest(ExactRef ref) { return Optional.ofNullable(requests.get(ref)).orElseThrow(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { return Optional.ofNullable(requestRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { throw new IllegalStateException("unused record archive"); }
        @Override public ActionRecord loadRecord(ExactRef ref) { throw new IllegalStateException("unused record archive"); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { throw new IllegalStateException("unused record archive"); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw new IllegalStateException("offline fixture native frame storage is explicit"); }
        @Override public byte[] loadNativeFrame(ExactRef ref) { return loadMaterial(ref).bytes(); }
    }
}
