package org.xar.ck3.control.application.battleadvance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.time.Duration;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.AdvanceReadiness;
import org.xar.ck3.control.application.advance.AdvanceClock;
import org.xar.ck3.control.application.advance.AdvanceWait;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.reconciliation.LateOutcome.Budget;

/** Original one-resume tactical tranche. Native application-main owns every intermediate daily boundary. */
public final class BattleAdvanceComposite implements CompositeActionPort {
    public static final String HANDLER = "native-battle-sentinel-advance/v1";
    private final AdvanceObservationPort observations;
    private final AdvanceWait wait;
    private final ClockStatusRead statuses;
    private final BattleAdvancePlan.Configuration configuration;
    private final AdvanceReadiness.Port readiness;
    private final ActionSnapshotReader receipts;
    private final EvidenceArchive archive;
    private final Duration commandTimeout;
    private final Duration advanceTimeout;
    private final Clock clock;
    private final Optional<ReconciliationBudgetPort> reconcileBudgets;

    /** Existing application evidence archive, separate from the one authoritative ledger writer. */
    public interface EvidenceArchive {
        ExactRef completed(ActionCommand parent, Outcome outcome);
        ExactRef failed(ActionCommand parent, Failure failure);
        ExactRef readOnly(ActionCommand parent, ReadOnlyOutcome outcome);
    }
    /** The unique root supplies a fresh finite read budget clipped to its actual active lease hard deadline. */
    @FunctionalInterface public interface ReconciliationBudgetPort { Budget open(ActionCommand original, CompositeExecution retained); }
    public record ReadOnlyOutcome(Instant startedAt, Instant deadline, Budget budget, Frame first, Status status, ExactRef statusEvidence, Frame ending) {
        public ReadOnlyOutcome {
            Objects.requireNonNull(startedAt); Objects.requireNonNull(deadline); Objects.requireNonNull(budget); Objects.requireNonNull(first);
            Objects.requireNonNull(status); Objects.requireNonNull(statusEvidence); Objects.requireNonNull(ending);
            require(startedAt.isBefore(deadline) && !deadline.isAfter(budget.hardDeadline()) && statusEvidence.bytes() > 0, "actual bounded read-only observation evidence required");
        }
    }
    /** Restricted view of the same engine. It exposes no top-level command or reconciliation route. */
    @FunctionalInterface public interface WindowExecutor {
        Outcome executeWindow(ActionCommand parent, Children children, Frame starting, WindowRequest request) throws InterruptedException;
    }
    public static WindowExecutor windowExecutor(AdvanceObservationPort observations, AdvanceWait wait,
            ClockStatusRead statuses, BattleAdvancePlan.Configuration configuration, AdvanceReadiness.Port readiness,
            ActionSnapshotReader receipts, EvidenceArchive archive, Duration commandTimeout, Duration advanceTimeout, Clock clock) {
        BattleAdvanceComposite engine = new BattleAdvanceComposite(observations, wait, statuses, configuration, readiness,
                receipts, archive, commandTimeout, advanceTimeout, clock, Optional.empty());
        return engine::executeWindow;
    }
    public record WindowRequest(List<Integer> watchArmyIds, int windowEndDateRaw, int speed) {
        public WindowRequest {
            watchArmyIds = List.copyOf(watchArmyIds);
            require(speed >= 1 && speed <= 5 && !watchArmyIds.isEmpty() && watchArmyIds.size() <= 64
                    && watchArmyIds.stream().allMatch(id -> id >= 0) && watchArmyIds.equals(watchArmyIds.stream().distinct().sorted().toList()), "typed route-window watch/speed required");
        }
    }
    public record Outcome(BattleAdvancePlan plan, Frame starting, Frame ending, Status arm, Status stop,
            Optional<BattleAdvanceFrame.Boundary> decisionBoundary, boolean canceled, List<ActionReceipt> actions,
            List<ExactRef> queryEvidence, Optional<BattleAdvanceFrame.HoldState> holdAdmission,
            Optional<BattleAdvanceFrame.HoldState> holdPostStop, ClockStatusRead.Observation nativeStopRead) {
        public Outcome {
            Objects.requireNonNull(plan); Objects.requireNonNull(starting); Objects.requireNonNull(ending); Objects.requireNonNull(arm); Objects.requireNonNull(stop);
            decisionBoundary = Objects.requireNonNull(decisionBoundary); actions = List.copyOf(actions); queryEvidence = List.copyOf(queryEvidence);
            Objects.requireNonNull(holdAdmission); Objects.requireNonNull(holdPostStop);
            Objects.requireNonNull(nativeStopRead); require(nativeStopRead.status().equals(stop)
                    && queryEvidence.contains(nativeStopRead.originalEvidence()), "outcome needs the actual final independently read sentinel Status");
        }
        public int elapsedDays() {
            long delta = (long) BattleAdvanceFrame.decode(ending).owner().dateRaw() - plan.startingDateRaw();
            require(delta >= 0 && delta % 24 == 0, "actual tactical progress must be a nonnegative whole-day delta");
            return Math.toIntExact(delta / 24);
        }
    }
    public record Failure(BattleAdvancePlan plan, Frame starting, Frame lastObserved, List<ActionReceipt> actions,
            List<ExactRef> queryEvidence, Optional<Status> arm, Optional<Status> stop, String reason, Optional<String> cleanupError) {
        public Failure { actions = List.copyOf(actions); queryEvidence = List.copyOf(queryEvidence); Objects.requireNonNull(arm); Objects.requireNonNull(stop); Objects.requireNonNull(reason); Objects.requireNonNull(cleanupError); }
    }
    public BattleAdvanceComposite(AdvanceObservationPort observations, AdvanceWait wait,
            ClockStatusRead statuses, BattleAdvancePlan.Configuration configuration, AdvanceReadiness.Port readiness,
            ActionSnapshotReader receipts, EvidenceArchive archive, Duration commandTimeout, Duration advanceTimeout,
            Clock clock, ReconciliationBudgetPort reconcileBudgets) {
        this(observations, wait, statuses, configuration, readiness, receipts, archive, commandTimeout, advanceTimeout,
                clock, Optional.of(Objects.requireNonNull(reconcileBudgets)));
    }
    private BattleAdvanceComposite(AdvanceObservationPort observations, AdvanceWait wait,
            ClockStatusRead statuses, BattleAdvancePlan.Configuration configuration, AdvanceReadiness.Port readiness,
            ActionSnapshotReader receipts, EvidenceArchive archive, Duration commandTimeout, Duration advanceTimeout,
            Clock clock, Optional<ReconciliationBudgetPort> reconcileBudgets) {
        this.observations = Objects.requireNonNull(observations); this.wait = Objects.requireNonNull(wait);
        this.statuses = Objects.requireNonNull(statuses); this.configuration = Objects.requireNonNull(configuration); this.readiness = Objects.requireNonNull(readiness);
        this.receipts = Objects.requireNonNull(receipts); this.archive = Objects.requireNonNull(archive);
        require(!commandTimeout.isNegative() && !commandTimeout.isZero() && !advanceTimeout.isNegative() && !advanceTimeout.isZero(), "finite positive command/advance timeouts required");
        this.commandTimeout = commandTimeout; this.advanceTimeout = advanceTimeout;
        this.clock = Objects.requireNonNull(clock); this.reconcileBudgets = Objects.requireNonNull(reconcileBudgets);
    }
    @Override public String handlerId() { return HANDLER; }
    @Override public boolean supports(OperationKey operation) { return BattleAdvanceStep.parse(operation.value()).isPresent(); }
    /** Planner producer; output is normalized and serialized before the parent durable intent. */
    public BattleAdvancePlan project(BattleAdvanceStep step, Frame frame) { return BattleAdvancePlan.create(step, BattleAdvanceFrame.decode(frame), configuration); }
    @Override public void validate(ActionCommand parent) {
        BattleAdvancePlan plan = BattleAdvancePlan.decode(parent);
        Frame frame = observations.current(parent, parent.deadline());
        BattleAdvanceFrame.Snapshot start = BattleAdvanceFrame.decode(frame);
        BattleAdvanceFrame.bind(parent, start, true); checkAdmission(parent, frame, Optional.of(parse(parent)));
        require(plan.equals(project(parse(parent), frame)), "durable tactical plan differs from actual paused-frame scope/deadline");
        require(parent.claims().armyIds().containsAll(plan.watchArmyIds().stream().map(BigInteger::valueOf).toList()), "parent must reserve complete actual watched controllable army identities");
        require(parent.expected().observerSchema().equals(BattleAdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected()), "battle expected contract differs from actual plan");
    }
    @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) throws InterruptedException {
        BattleAdvancePlan plan = BattleAdvancePlan.decode(parent);
        Frame starting = observations.current(parent, parent.deadline());
        BattleAdvanceFrame.bind(parent, BattleAdvanceFrame.decode(starting), true);
        require(plan.equals(project(parse(parent), starting)), "battle scope changed after durable parent intent");
        require(parent.claims().armyIds().containsAll(plan.watchArmyIds().stream().map(BigInteger::valueOf).toList()), "parent watch claims differ from actual controlled armies");
        checkAdmission(parent, starting, Optional.of(parse(parent)));
        try { return effect(parent, execute(parent, children, starting, plan, Optional.of(parse(parent)))); }
        catch (Unresolved failure) { return new ActionPorts.Pending(failure.getMessage(), failure.evidence); }
    }
    /** Called by the migrated route-window composite after its real proof collector. Does not settle its parent. */
    public Outcome executeWindow(ActionCommand parent, Children children, Frame starting, WindowRequest request) throws InterruptedException {
        BattleAdvanceFrame.Snapshot start = BattleAdvanceFrame.decode(starting);
        BattleAdvanceFrame.bind(parent, start, true); checkAdmission(parent, starting, Optional.empty());
        require(start.paused() && start.mapReady() && start.decision().isEmpty() && !start.activeCombat(start.watch()) && !start.activeRetreat(start.watch()),
                "route window requires current paused noncombat route inputs");
        Optional<CampaignDeadline.Cap> cap = CampaignDeadline.deadline(configuration.campaignDeadline(), BigInteger.valueOf(start.owner().dateRaw()), BigInteger.valueOf(request.windowEndDateRaw));
        cap.ifPresent(value -> require(value.status() == CampaignDeadline.Status.ADVANCE && value.targetDateRaw().intValueExact() == request.windowEndDateRaw,
                "typed route window was not normalized to campaign deadline"));
        BattleAdvancePlan plan = new BattleAdvancePlan(parent.operation().value(), start.owner().dateRaw(), request.windowEndDateRaw, request.speed,
                Mode.TERMINAL_OR_SENTINEL, BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW, request.watchArmyIds, cap);
        return execute(parent, children, starting, plan, Optional.empty());
    }
    private Outcome execute(ActionCommand parent, Children children, Frame initial, BattleAdvancePlan plan, Optional<BattleAdvanceStep> request) throws InterruptedException {
        Frame current = initial; Status arm = null, stop = null; List<ActionReceipt> actions = new ArrayList<>(); List<ExactRef> queryEvidence = new ArrayList<>();
        ClockStatusRead.Observation nativeStopRead = null;
        Optional<BattleAdvanceFrame.Boundary> decision = Optional.empty(); boolean canceled = false;
        BattleAdvanceFrame.Snapshot starting = BattleAdvanceFrame.decode(initial);
        Optional<BattleAdvanceFrame.HoldState> holdAdmission = request.filter(BattleAdvanceStep.Hold.class::isInstance).map(BattleAdvanceStep.Hold.class::cast)
                .map(hold -> starting.hold(plan.watchArmyIds(), hold));
        try {
            if (starting.speed() != plan.speed()) child(parent, children, current, "set-speed-" + plan.speed(), actions);
            current = wait.until(parent, observations.current(parent, bound(parent, commandTimeout)),
                    frame -> BattleAdvanceFrame.decode(frame).speed() == plan.speed(), bound(parent, commandTimeout));
            require(BattleAdvanceFrame.decode(current).speed() == plan.speed(), "native sentinel did not observe requested speed");
            samePreResume(starting, BattleAdvanceFrame.decode(current));
            checkScopeStillMatches(plan, request, current);
            ActionReceipt armChild = child(parent, children, current, plan.armStep(), actions);
            arm = armStatus(armChild, plan.armStep());
            BattleSentinelValidation.arm(arm, plan.startingDateRaw(), plan.targetDateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds(), plan.scope());
            // Observe once more under the same connection before the only resume, retaining the exact generation.
            ClockStatusRead.Observation armed = statuses.observe(parent, current, bound(parent, commandTimeout));
            queryEvidence.add(armed.originalEvidence()); require(armed.status().equals(arm), "armed sentinel changed before resume");
            current = observations.current(parent, bound(parent, commandTimeout));
            BattleAdvanceFrame.Snapshot beforeResume = BattleAdvanceFrame.decode(current);
            boolean interruptedBeforeResume = freshDecision(starting, beforeResume);
            if (!interruptedBeforeResume) {
                samePreResume(starting, beforeResume); checkScopeStillMatches(plan, request, current);
                child(parent, children, current, "resume-map", actions);
                current = wait.until(parent, observations.current(parent, bound(parent, commandTimeout)), frame -> runningOrStopped(plan, starting, frame), bound(parent, commandTimeout));
                require(runningOrStopped(plan, starting, current), "single resume reached neither running frame nor native sentinel stop or new decision");
            } else require(beforeResume.paused() && beforeResume.mapReady() && starting.owner().same(beforeResume.owner(), false, true),
                    "pre-resume interruption must retain the actual paused owner/date");
            if (!BattleAdvanceFrame.decode(current).paused()) current = wait.until(parent, current,
                    frame -> BattleAdvanceFrame.decode(frame).paused() || BattleAdvanceFrame.decode(frame).decision().isPresent(), bound(parent, advanceTimeout));
            BattleAdvanceFrame.Snapshot observed = BattleAdvanceFrame.decode(current);
            BattleAdvanceFrame.bind(parent, observed, false);
            Optional<BattleAdvanceFrame.Boundary> boundary = BattleAdvanceFrame.boundary(starting, observed);
            boolean newDecision = boundary.filter(value -> value.kind() == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED).isPresent()
                    || boundary.isPresent() && BattleAdvanceFrame.isNew(starting, observed);
            Optional<BattleAdvanceFrame.Boundary> runningBoundary = newDecision && !observed.paused() ? boundary : Optional.empty();
            if (newDecision && observed.paused()) decision = boundary;
            if (!observed.paused()) {
                BattleAdvanceFrame.Snapshot beforePause = observed;
                Frame refreshed = observations.current(parent, bound(parent, commandTimeout)); int pauseCount = 0;
                if (!BattleAdvanceFrame.decode(refreshed).paused()) { child(parent, children, refreshed, "pause-map", actions); pauseCount = 1; }
                current = wait.until(parent, observations.current(parent, bound(parent, commandTimeout)), frame -> BattleAdvanceFrame.decode(frame).paused(), bound(parent, commandTimeout));
                observed = BattleAdvanceFrame.decode(current);
                require(BattleAdvanceFrame.freshPausedBoundary(starting, beforePause, observed, runningBoundary, pauseCount),
                        runningBoundary.isPresent() ? "player decision failed to stabilize on a fresh paused frame" : "timed out before native sentinel pause");
                decision = observed.decision();
            }
            require(observed.paused(), "native sentinel pause not observed");
            ClockStatusRead.Observation status = statuses.observe(parent, current, bound(parent, commandTimeout));
            queryEvidence.add(status.originalEvidence()); stop = status.status(); nativeStopRead = status;
            if (decision.isPresent()) {
                if (stop.state() == State.ARMED) {
                    require(stop.generation().equals(arm.generation()), "player decision armed a different sentinel generation");
                    child(parent, children, current, BattleAdvancePlan.CANCEL_PREFIX + arm.generation().decimal(), actions);
                    canceled = true; status = statuses.observe(parent, current, bound(parent, commandTimeout));
                    queryEvidence.add(status.originalEvidence()); stop = status.status(); nativeStopRead = status;
                } else require(stop.state() == State.TRIGGERED, "decision boundary sentinel is neither armed nor normally triggered");
            }
            Frame post = observations.current(parent, bound(parent, commandTimeout));
            AdvanceClock.requireAfterControl(parent, current, nativeStopRead, post);
            BattleAdvanceFrame.Snapshot ending = BattleAdvanceFrame.decode(post); BattleAdvanceFrame.bind(parent, ending, false);
            require(ending.paused() && ending.mapReady() && ending.owner().dateRaw() == observed.owner().dateRaw(), "fresh stable paused post-stop frame unavailable");
            // Status and SEM are independent reads. The final actual SEM can acquire
            // a new decision after the earlier pause frame; archive replay uses this same endpoint.
            Optional<BattleAdvanceFrame.Boundary> fresh = BattleAdvanceFrame.boundary(starting, ending);
            if (decision.isPresent()) {
                require(fresh.isPresent() && decision.orElseThrow().same(fresh.orElseThrow()), "decision boundary changed before stable post-stop frame");
            } else require(fresh.isEmpty() || fresh.orElseThrow().kind() == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED
                    || BattleAdvanceFrame.isNew(starting, ending), "post-Status decision is not a new original-frame boundary");
            decision = fresh;
            require(starting.owner().same(ending.owner(), decision.filter(value -> value.kind() == BattleAdvanceFrame.Kind.ONE_LIFE_TERMINAL).isPresent(), false), "sentinel connection/episode/player ownership changed");
            Optional<BattleAdvanceFrame.HoldState> holdPost = request.filter(BattleAdvanceStep.Hold.class::isInstance).map(BattleAdvanceStep.Hold.class::cast)
                    .map(hold -> ending.hold(plan.watchArmyIds(), hold));
            require(holdPost.filter(value -> value.status() == BattleAdvanceFrame.HoldStatus.UNAVAILABLE).isEmpty(), "objective hold post-stop scope could not be revalidated");
            if (decision.isPresent()) BattleSentinelValidation.decision(stop, arm, plan.startingDateRaw(), plan.targetDateRaw(), ending.owner().dateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds(), decision.orElseThrow(), canceled);
            else BattleSentinelValidation.stop(stop, arm, plan.startingDateRaw(), plan.targetDateRaw(), ending.owner().dateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds());
            return new Outcome(plan, initial, post, arm, stop, decision, canceled, actions, queryEvidence, holdAdmission, holdPost, nativeStopRead);
        } catch (RuntimeException error) {
            Optional<String> cleanupError = Optional.empty();
            // An unresolved child is globally unknown. The only legal follow-up is a read, never another mutation.
            boolean unresolvedChild = error instanceof SubmissionUnknown || actions.stream().anyMatch(action -> !action.settled())
                    || children.completed().stream().anyMatch(action -> !action.settled());
            if (!unresolvedChild) {
                try {
                    Frame cleanup = observations.current(parent, bound(parent, commandTimeout)); current = cleanup;
                    if (!BattleAdvanceFrame.decode(cleanup).paused()) {
                        child(parent, children, cleanup, "pause-map", actions);
                        current = wait.until(parent, observations.current(parent, bound(parent, commandTimeout)), frame -> BattleAdvanceFrame.decode(frame).paused(), bound(parent, commandTimeout));
                    }
                } catch (RuntimeException cleanup) { cleanupError = Optional.of(cleanup.getClass().getSimpleName() + ": " + cleanup.getMessage()); }
            }
            Failure failure = new Failure(plan, initial, current, actions, queryEvidence, Optional.ofNullable(arm), Optional.ofNullable(stop), error.getClass().getSimpleName() + ": " + error.getMessage(), cleanupError);
            ExactRef evidence = archive.failed(parent, failure);
            throw new Unresolved("native tactical sentinel postcondition failed: " + failure.reason(), List.of(evidence));
        }
    }
    private ActionReceipt child(ActionCommand parent, Children children, Frame frame, String step, List<ActionReceipt> actions) {
        require(actions.stream().allMatch(ActionReceipt::settled), "UNKNOWN child cannot be followed by another mutation");
        ActionCommand child = AdvancePrimitives.child(parent, frame, children.nextActionId(), step, bound(parent, commandTimeout));
        ActionReceipt result;
        try { result = children.submit(child); }
        catch (RuntimeException failedSubmission) { throw new SubmissionUnknown(failedSubmission); }
        actions.add(result);
        require(step.equals("pause-map")
                ? result.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.PauseConfirmed
                : result.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED,
                "native child did not independently confirm its poststate: " + step);
        return result;
    }
    private static Status armStatus(ActionReceipt receipt, String step) {
        NativeActionPort.AckReceived ack = receipt.ack().orElseThrow(() -> new IllegalArgumentException("sentinel arm requires actual native ACK"));
        var result = AdvancePrimitives.nativeResult(ack, step);
        require(result.path("status").isTextual() && result.path("status").textValue().equals("available"), "native sentinel arm ACK envelope inconsistent");
        return AdvancePrimitives.acknowledgedSentinel(ack, step);
    }
    private void checkAdmission(ActionCommand parent, Frame frame, Optional<BattleAdvanceStep> step) {
        AdvanceReadiness.Facts actual = Objects.requireNonNull(readiness.inspect(parent, frame));
        require(actual.observed().equals(frame.identity()), "actual sentinel admission source/frame drift");
        require(!AdvanceReadiness.h3937(frame.semantic()), "H3937 date hold remains active");
        require(actual.bridgeCapabilities().containsAll(Set.of(BattleAdvancePlan.ARM_CAPABILITY, BattleAdvancePlan.STATUS_CAPABILITY)), "native lacks exact sentinel arm/status pair");
        step.ifPresent(value -> {
            String required = value instanceof BattleAdvanceStep.Hold ? "war-objective-hold-sentinel-advance" : value instanceof BattleAdvanceStep.Route
                    ? "committed-route-sentinel-advance" : value instanceof BattleAdvanceStep.Battle battle && battle.requestedTarget().isPresent()
                    ? "battle-decision-epoch-advance" : value.literal();
            require(actual.actionSteps().contains(new OperationKey(required)), "native tactical sentinel composite not advertised: " + required);
        });
    }
    private void checkScopeStillMatches(BattleAdvancePlan plan, Optional<BattleAdvanceStep> request, Frame current) {
        request.ifPresent(step -> require(plan.equals(project(step, current)), "exact subject/route/war/objective scope changed before resume"));
    }
    private static BattleAdvanceStep parse(ActionCommand parent) { return BattleAdvanceStep.parse(parent.operation().value()).orElseThrow(() -> new IllegalArgumentException("unsupported or malformed tactical composite")); }
    private static boolean freshDecision(BattleAdvanceFrame.Snapshot start, BattleAdvanceFrame.Snapshot current) {
        return BattleAdvanceFrame.boundary(start, current).filter(value -> value.kind() == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED
                || BattleAdvanceFrame.isNew(start, current)).isPresent();
    }
    private static boolean runningOrStopped(BattleAdvancePlan plan, BattleAdvanceFrame.Snapshot starting, Frame frame) {
        BattleAdvanceFrame.Snapshot value = BattleAdvanceFrame.decode(frame);
        return !value.paused() || value.owner().dateRaw() > plan.startingDateRaw() || freshDecision(starting, value);
    }
    private static void samePreResume(BattleAdvanceFrame.Snapshot start, BattleAdvanceFrame.Snapshot current) {
        require(current.paused() && current.mapReady() && current.decision().isEmpty() && start.owner().same(current.owner(), false, true)
                && start.watch().equals(current.watch()), "sentinel paused-frame owner/date/watch drifted before resume");
    }
    private Instant bound(ActionCommand parent, Duration timeout) { Instant candidate = clock.instant().plus(timeout); return candidate.isAfter(parent.deadline()) ? parent.deadline() : candidate; }
    private ActionPorts.PostconditionResult effect(ActionCommand parent, Outcome outcome) {
        ExactRef evidence = archive.completed(parent, outcome); Frame ending = outcome.ending();
        if (!ending.identity().frame().identity().player().equals(parent.before().frame().identity().player()))
            return new ActionPorts.Pending("verified one-life terminal changed played actor; hand retained terminal evidence to the unique succession reducer", List.of(evidence));
        boolean controlOnly = outcome.elapsedDays() == 0 && outcome.canceled()
                && outcome.actions().stream().noneMatch(value -> value.command().operation().value().equals("resume-map"));
        List<ExpectedValue> actual = actualValues(outcome.plan(), outcome.elapsedDays(), outcome.decisionBoundary().isEmpty(), controlOnly);
        ActionState.EffectObservation semantic = new ActionState.EffectObservation(ending.identity(), ending.source(), ending.sessionId(),
                BattleAdvancePlan.OBSERVER, actual, ending.provenance(), ending.observedAt(), ending.originalEvidence(), List.of(evidence));
        if (controlOnly && ending.identity().frame().identity().nativeRevision().equals(parent.before().frame().identity().nativeRevision()))
            return new ActionPorts.CompositeControlObserved(AdvanceClock.compositeControlTerminal(parent, outcome.nativeStopRead(), outcome.actions(), semantic));
        return new ActionPorts.EffectObserved(semantic);
    }
    public static List<ExpectedValue> actualValues(BattleAdvancePlan plan, int elapsedDays, boolean decisionClear, boolean controlOnly) {
        require(elapsedDays >= 0 && (!controlOnly || elapsedDays == 0 && !decisionClear), "control interruption cannot claim a completed day or clear decision");
        List<ExpectedValue> actual = new ArrayList<>(plan.expected());
        actual.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), !controlOnly));
        actual.add(new ExpectedBoolean(new FieldKey("timeline.advance_verified"), elapsedDays > 0));
        actual.add(new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), elapsedDays > 0 && decisionClear));
        actual.add(new ExpectedText(new FieldKey("progress_status"), "postcondition"));
        actual.add(new ExpectedInteger(new FieldKey("elapsed_days"), BigInteger.valueOf(elapsedDays)));
        return List.copyOf(actual);
    }
    /** Retained parents cannot replay. Only the existing confirmed arm and resume children permit read-only late-stop proof. */
    @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained) {
        try {
            require(retained.handlerId().equals(HANDLER), "retained composite handler drift");
            require(retained.guard().source().equals(parent.source()) && retained.guard().sessionId().equals(parent.sessionId())
                    && retained.guard().observed().game().equals(parent.before().game()), "retained source/session/Game drift");
            BattleAdvancePlan plan = BattleAdvancePlan.decode(parent); List<ActionReceipt> children = new ArrayList<>();
            for (CompositeExecution.Child child : retained.children()) {
                ActionReceipt receipt = receipts.find(child.actionId()).orElseThrow(() -> new IllegalArgumentException("retained child receipt unavailable"));
                require(receipt.bodySha256().equals(child.bodySha256()), "retained child body changed"); children.add(receipt);
            }
            if (children.stream().anyMatch(child -> !child.settled())) return new ActionPorts.Pending("original child remains UNKNOWN; no tactical replay or cancel is permitted", List.of());
            org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay.verifyChildBindings(parent, children);
            ActionReceipt armChild = children.stream().filter(child -> child.command().operation().value().equals(plan.armStep())).findFirst().orElseThrow();
            require(armChild.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED, "retained original arm is not independently confirmed");
            require(children.stream().anyMatch(child -> child.command().operation().value().equals("resume-map") && child.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED), "retained composite has no confirmed original resume");
            Status arm = armStatus(armChild, plan.armStep());
            BattleSentinelValidation.arm(arm, plan.startingDateRaw(), plan.targetDateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds(), plan.scope());
            Budget budget = Objects.requireNonNull(reconcileBudgets.orElseThrow(() -> new IllegalStateException("window-only engine has no reconciliation authority")).open(parent, retained)); Instant startedAt = clock.instant();
            Instant intervalDeadline = startedAt.plusMillis(budget.maximumDurationMillis()); Instant readDeadline = intervalDeadline.isBefore(budget.hardDeadline()) ? intervalDeadline : budget.hardDeadline();
            require(budget.maximumReads() >= 3 && startedAt.isBefore(readDeadline), "independent read-only late-stop budget unavailable");
            Frame first = observations.current(parent, readDeadline); BattleAdvanceFrame.Snapshot firstState = BattleAdvanceFrame.decode(first); BattleAdvanceFrame.bind(parent, firstState, false);
            require(firstState.owner().connectionGeneration().equals(retained.guard().connectionGeneration()), "retained original connection generation changed");
            ClockStatusRead.Observation status = statuses.observe(parent, first, readDeadline);
            Frame ending = observations.current(parent, readDeadline); BattleAdvanceFrame.Snapshot after = BattleAdvanceFrame.decode(ending); BattleAdvanceFrame.bind(parent, after, false);
            require(!clock.instant().isAfter(readDeadline), "actual read-only reconciliation budget expired");
            require(firstState.paused() && after.paused() && after.mapReady() && firstState.owner().same(after.owner(), false, true), "read-only late stop requires same stable paused frame");
            BattleSentinelValidation.stop(status.status(), arm, plan.startingDateRaw(), plan.targetDateRaw(), after.owner().dateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds());
            // Original starting source evidence remains the durable parent observation; no reconstructed starting frame is invented.
            ExactRef material = archive.readOnly(parent, new ReadOnlyOutcome(startedAt, readDeadline, budget, first, status.status(), status.originalEvidence(), ending));
            return new ActionPorts.Pending("native late stop observed; original parent failure requires the existing writer continuity reducer before credit", List.of(material));
        } catch (RuntimeException unavailable) { return new ActionPorts.Pending("read-only tactical reconciliation unavailable: " + unavailable.getMessage(), List.of()); }
    }
    public static final class Unresolved extends RuntimeException {
        private static final long serialVersionUID = 1L;
        // In-process failure context; durable evidence uses the existing JSON publisher.
        @SuppressWarnings("serial")
        private final List<ExactRef> evidence;
        public Unresolved(String reason, List<ExactRef> evidence) { super(reason); this.evidence = List.copyOf(evidence); }
        public List<ExactRef> evidence() { return evidence; }
    }
    private static final class SubmissionUnknown extends RuntimeException {
        private static final long serialVersionUID = 1L;
        SubmissionUnknown(RuntimeException cause) { super("native child submission threw before its actual receipt returned; no cleanup mutation is permitted", cause); }
    }
}
