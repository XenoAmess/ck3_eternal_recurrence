package org.xar.ck3.control.application.battleadvance;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Native/child fixture only. These fabricated packets never confer live qualification. */
final class BattleAdvanceFixture implements AdvanceObservationPort, CompositeActionPort.Children, PlanningReadPort,
        BattleAdvanceComposite.EvidenceArchive {
    static final Instant NOW = Instant.now();
    static final ExactRef REF = new ExactRef("D:/test-fixture/battle-original.json", 1, "b".repeat(64));
    static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
    static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
    static final Set<OperationKey> AVAILABLE = Set.of(new OperationKey("battle-decision-epoch-advance"), new OperationKey("battle-terminal-cruise"),
            new OperationKey("committed-route-sentinel-advance"), new OperationKey("war-objective-hold-sentinel-advance"),
            new OperationKey("set-speed-3"), new OperationKey("resume-map"), new OperationKey("pause-map"));
    final Deque<Frame> frames = new ArrayDeque<>();
    final Deque<Status> statusReads = new ArrayDeque<>();
    final List<ActionReceipt> children = new ArrayList<>();
    final List<String> steps = new ArrayList<>();
    final Map<String, ActionReceipt> durable = new HashMap<>();
    String unknownStep;
    String throwingStep;
    boolean throwBeforeReceipt;
    Status actualArm = armed();
    int frameReads;
    BattleAdvanceComposite.Outcome completed;
    BattleAdvanceComposite.Failure failed;

    static Frame frame(int revision, int date, boolean paused, boolean modal) {
        String text = "{\"snapshot_id\":\"frame-" + revision + "\",\"revision\":" + revision + ",\"native_revision\":" + revision
                + ",\"date_raw\":" + date + ",\"episode_run_id\":\"episode-1\",\"episode_character_id\":29829,\"played_character\":{\"character_id\":29829,\"alive\":true},"
                + "\"paused\":" + paused + ",\"map_ready\":true,\"speed\":3,\"active_event\":" + (modal ? "{\"instance_id\":\"event-1\",\"option_count\":2}" : "null")
                + ",\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"active_wars\":[],"
                + "\"player_armies\":[{\"army_id\":0,\"controllable\":true,\"army_state\":\"combat\",\"army_state_code\":2,\"combat_id\":281474976710657,\"in_combat\":true,\"retreating\":false,\"route_province_ids\":[],\"move_target_province_id\":null,\"current_province_id\":7}],"
                + "\"diagnostics\":{\"bridge_pid\":123,\"connection_generation\":1}}";
        var semantic = OpportunityJson.object(OpportunityJson.parse(text.getBytes(StandardCharsets.UTF_8)), "fixture");
        var identity = new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(), GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(revision), BigInteger.valueOf(date)),
                        "frame-" + revision, BigInteger.valueOf(revision), "episode-1"), 1);
        ExactRef nativePacket = new ExactRef("D:/test-fixture/native-frame-" + revision + ".json", 1, "d".repeat(64));
        return new Frame(identity, SOURCE, "session-1", semantic, new ObservationProvenance.Push(identity.frame().snapshotId(), identity.frame().identity().nativeRevision(), nativePacket),
                NOW.plusMillis(revision), nativePacket);
    }
    static Status armed() { return new Status(State.ARMED, new CrossJsDecimalUInt64("1"), 100, 124, 100, 0, 3, Mode.DECISION_EPOCH,
            1, 1, 0, 0, 0, List.of(), 0, -1, false, false, false, false); }
    static Status stopped() { return new Status(State.TRIGGERED, new CrossJsDecimalUInt64("1"), 100, 124, 124, 124, 3, Mode.DECISION_EPOCH,
            1, 1, 1, 0, 1, List.of("date_deadline"), 0, 0, true, true, false, false); }
    static Status idle() { return new Status(State.IDLE, new CrossJsDecimalUInt64("1"), 100, 124, 100, 0, 3, Mode.DECISION_EPOCH,
            1, 1, 0, 0, 0, List.of(), 0, -1, false, false, false, false); }
    static ActionCommand parent() {
        Frame before = frame(1, 100, true, false);
        var step = BattleAdvanceStep.parse("battle-decision-epoch-advance-to-124").orElseThrow();
        var plan = BattleAdvancePlan.create(step, BattleAdvanceFrame.decode(before), BattleAdvancePlan.Configuration.production(Optional.empty()));
        return new ActionCommand("battle-parent", before.identity(), SOURCE, "session-1", new OperationKey(step.literal()),
                new OpportunityJson.Obj(Map.of(BattleAdvancePlan.KEY, plan.json())), new ProposalLifecycle.ExpectedPostcondition(1, before.identity(), SOURCE, BattleAdvancePlan.OBSERVER, plan.expected()),
                new JointBudgetSelector.Claims(Set.of(BigInteger.ZERO), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(3600));
    }
    BattleAdvanceComposite composite() {
        ActionJournal journal = new Journal();
        ClockStatusRead status = new ClockStatusRead(this, REF, archive());
        return new BattleAdvanceComposite(this, new AdvanceWait(this, Clock.fixed(NOW, ZoneOffset.UTC), 4), status,
                BattleAdvancePlan.Configuration.production(Optional.empty()), (parent, frame) -> new AdvanceReadiness.Facts(frame.identity(), AVAILABLE,
                    Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP), false, false, false, 45, REF),
                new ActionSnapshotReader(journal), this, Duration.ofSeconds(30), Duration.ofSeconds(120), Clock.fixed(NOW, ZoneOffset.UTC),
                (original, retained) -> new org.xar.ck3.control.reconciliation.LateOutcome.Budget(1000, 3, 1000, 0, NOW.plusSeconds(1)));
    }
    BattleAdvanceComposite.WindowExecutor windowExecutor() {
        ClockStatusRead status = new ClockStatusRead(this, REF, archive());
        return BattleAdvanceComposite.windowExecutor(this, new AdvanceWait(this, Clock.fixed(NOW, ZoneOffset.UTC), 4), status,
                BattleAdvancePlan.Configuration.production(Optional.empty()), (parent, frame) -> new AdvanceReadiness.Facts(frame.identity(), AVAILABLE,
                    Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP), false, false, false, 45, REF),
                new ActionSnapshotReader(new Journal()), this, Duration.ofSeconds(30), Duration.ofSeconds(120), Clock.fixed(NOW, ZoneOffset.UTC));
    }
    @Override public Frame current(ActionCommand parent, Instant deadline) { frameReads++; return frames.removeFirst(); }
    @Override public Frame next(ActionCommand parent, ProposalLifecycle.ObservationIdentity after, Instant deadline) { return current(parent, deadline); }
    @Override public String nextActionId() { return "child-" + children.size(); }
    @Override public List<ActionReceipt> completed() { return List.copyOf(children); }
    @Override public ActionReceipt submit(ActionCommand child) {
        String step = child.operation().value(); steps.add(step); String requestId = "request-" + child.actionId();
        if (step.equals(throwingStep) && throwBeforeReceipt) throw new IllegalStateException("fixture: submission did not return its receipt");
        if (step.startsWith(BattleAdvancePlan.ARM_PREFIX)) {
            var spec = AdvancePrimitives.armSpec(step);
            actualArm = new Status(State.ARMED, new CrossJsDecimalUInt64("1"), spec.startingDateRaw(), spec.targetDateRaw(), spec.startingDateRaw(), 0, spec.speed(),
                    spec.mode().equals("decision") ? Mode.DECISION_EPOCH : Mode.TERMINAL_OR_SENTINEL, spec.armyIds().size(), spec.armyIds().isEmpty() ? 0 : 1,
                    0, 0, 0, List.of(), 0, -1, false, false, false, false);
        }
        GuardEvidence guard = guard(child.before(), child.operation());
        var attempt = new ActionState.Attempt(requestId, NOW, guard, new NativeRequest(step, "test-native-capability", raw("{}")));
        String status = step.startsWith(BattleAdvancePlan.CANCEL_PREFIX) ? "canceled" : "available";
        String result = "{\"step\":\"" + step + "\",\"accepted\":true,\"status\":\"" + status + "\""
                + (step.startsWith(BattleAdvancePlan.ARM_PREFIX) ? ",\"tactical_daily_sentinel\":" + SentinelObservation.toJson(actualArm) : "") + "}";
        var ack = new NativeActionPort.AckReceived(requestId, true, Optional.of(raw(result)), raw("{\"ok\":true}"), new byte[]{1});
        ActionState.Settlement settlement;
        if (step.startsWith(BattleAdvancePlan.ARM_PREFIX) || step.startsWith(BattleAdvancePlan.CANCEL_PREFIX)) {
            Status observedStatus = step.startsWith(BattleAdvancePlan.ARM_PREFIX) ? actualArm : new Status(State.IDLE, actualArm.generation(), actualArm.startingDateRaw(), actualArm.targetDateRaw(),
                    actualArm.startingDateRaw(), 0, actualArm.speed(), actualArm.mode(), actualArm.armyCount(), actualArm.combatCount(), 0, 0, 0, List.of(), 0, -1, false, false, false, false);
            settlement = new ActionState.ControlApplied(controlRead(child, "independent-" + requestId, observedStatus),
                    AdvancePrimitives.CLOCK_OBSERVER, AdvancePrimitives.statusValues(observedStatus));
        } else if (step.equals("pause-map")) {
            settlement = new ActionState.PauseConfirmed(new ActionState.EffectObservation(child.before(), SOURCE, child.sessionId(),
                    child.expected().observerSchema(), org.xar.ck3.control.application.action.PauseConfirmation.actualValues(),
                    "independent-" + requestId, NOW.plusSeconds(1), REF));
        } else settlement = new ActionState.Applied(new ActionState.EffectObservation(child.before(), SOURCE, child.sessionId(),
                child.expected().observerSchema(), child.expected().values(), "independent-" + requestId, NOW.plusSeconds(1), REF));
        ActionState state = step.equals(unknownStep) || step.equals(throwingStep) ? new ActionState.Unknown(Optional.of(attempt), Optional.of(ack), "lost independent poststate", List.of(REF))
                : new ActionState.Settled(attempt, ack, settlement);
        ActionReceipt receipt = new ActionReceipt(1, children.size() + 1L, child, ActionCodec.bodySha256(child), state);
        children.add(receipt); durable.put(child.actionId(), receipt);
        if (step.equals(throwingStep)) throw new IllegalStateException("fixture: original UNKNOWN persisted before submission threw");
        return receipt;
    }
    private static PlanningReadReceipt controlRead(ActionCommand child, String id, Status status) {
        PlanningReadRequest request = new PlanningReadRequest(child.before(), SOURCE, child.sessionId(), new OperationKey(ClockStatusRead.STEP),
                new OpportunityJson.Obj(Map.of()), child.deadline());
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(raw("{\"step\":\"" + ClockStatusRead.STEP
                + "\",\"accepted\":true,\"status\":\"available\",\"tactical_daily_sentinel\":" + SentinelObservation.toJson(status) + "}")), raw("{}"), new byte[]{1});
        var guard = new PlanningReadGuard(guard(request.before(), request.operation()), true, true, true, "c".repeat(64));
        return new PlanningReadReceipt(request, ClockStatusRead.CONTRACT_ID, id, guard, guard, ack);
    }
    @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
        Status status = statusReads.removeFirst(); String id = "clock-read-" + statusReads.size();
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(raw("{\"step\":\"" + ClockStatusRead.STEP + "\",\"accepted\":true,\"status\":\"available\",\"tactical_daily_sentinel\":" + SentinelObservation.toJson(status) + "}")), raw("{}"), new byte[]{1});
        var guard = new PlanningReadGuard(guard(request.before(), request.operation()), true, true, true, "c".repeat(64));
        var receipt = new PlanningReadReceipt(request, contract.contractId(), id, guard, guard, ack);
        return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, archive().preserveRead(receipt));
    }
    private static GuardEvidence guard(ProposalLifecycle.ObservationIdentity before, OperationKey operation) {
        return new GuardEvidence(before, SOURCE, "session-1", BigInteger.ONE, operation, REF, REF, "fixture-authority", NOW, NOW.plusSeconds(3600));
    }
    @Override public ExactRef completed(ActionCommand parent, BattleAdvanceComposite.Outcome outcome) { completed = outcome; return REF; }
    @Override public ExactRef failed(ActionCommand parent, BattleAdvanceComposite.Failure failure) { failed = failure; return REF; }
    @Override public ExactRef readOnly(ActionCommand parent, BattleAdvanceComposite.ReadOnlyOutcome outcome) { return REF; }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private final class Journal implements ActionJournal, ActionJournal.LockedJournal {
        @Override public <T> T locked(Function<LockedJournal, T> operation) { return operation.apply(this); }
        @Override public Optional<ActionReceipt> find(String id) { return Optional.ofNullable(durable.get(id)); }
        @Override public List<ActionReceipt> unresolved() { return durable.values().stream().filter(row -> !row.settled()).toList(); }
        @Override public ActionReceipt append(ActionCommand command, String digest, ActionState next) { throw new UnsupportedOperationException("this fixture cannot be another writer"); }
    }
    private static ActionPorts.OutcomeArchive archive() {
        return new ActionPorts.OutcomeArchive() {
            @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) { return new ExactRef("D:/test-fixture/original-" + value.requestId() + ".json", 1, "e".repeat(64)); }
            @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { throw new UnsupportedOperationException(); }
            @Override public ExactRef preserveRequest(NativeRequest value) { return REF; }
            @Override public NativeRequest loadRequest(ExactRef ref) { throw new UnsupportedOperationException(); }
            @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { return REF; }
            @Override public ExactRef requestReferenceOf(NativeRequest value) { return REF; }
            @Override public ExactRef preserveRead(PlanningReadReceipt value) { return REF; }
            @Override public PlanningReadReceipt loadRead(ExactRef ref) { throw new UnsupportedOperationException(); }
            @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { return REF; }
            @Override public ExactRef preserveRecord(ActionRecord value) { return REF; }
            @Override public ActionRecord loadRecord(ExactRef ref) { throw new UnsupportedOperationException(); }
            @Override public ExactRef recordReferenceOf(ActionRecord value) { return REF; }
            @Override public ExactRef preserveReceipt(ActionReceipt value) { return REF; }
            @Override public ActionReceipt loadReceipt(ExactRef ref) { throw new UnsupportedOperationException(); }
            @Override public ExactRef receiptReferenceOf(ActionReceipt value) { return REF; }
            @Override public ExactRef preserveMaterial(RawJson value) { return REF; }
            @Override public RawJson loadMaterial(ExactRef ref) { throw new UnsupportedOperationException(); }
            @Override public ExactRef materialReferenceOf(RawJson value) { return REF; }
            @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw new UnsupportedOperationException("fixture does not publish raw native frames"); }
            @Override public byte[] loadNativeFrame(ExactRef value) { throw new UnsupportedOperationException("fixture has no archived full Driver packet"); }
        };
    }
    ActionPorts.OutcomeArchive archiveForTest() { return archive(); }
}
