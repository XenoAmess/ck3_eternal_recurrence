package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** The production Java owner of life-advance and life-advance-one-day. Native receives only durable children. */
public final class LifeAdvanceComposite implements CompositeActionPort.ZeroGameplayBeforeChildren, CompositeActionPort.LifeControlPrefixSource, CompositeActionPort.OriginalContinuation {
    public static final String HANDLER = "java.native-driver.life-advance.v1";
    private final AdvanceObservationPort observations;
    private final AdvanceReadiness.Port readiness;
    private final AdvanceClock timeline;
    private final ClockStatusRead statuses;
    private final ActionSnapshotReader actions;
    private final ActionPorts.OutcomeArchive archive;
    private final Clock clock;
    private final LifeAdvanceEvidence.EntryFrameReader entryFrames;
    @FunctionalInterface public interface CancellationReads {
        CancellationRead read(ActionCommand parent, CompositeExecution execution, List<ActionReceipt> canonicalChildren, Instant deadline);
    }
    public record CancellationRead(PlanningReadResult.Known<Status> status, AdvanceObservationPort.Frame ending) {
        public CancellationRead { Objects.requireNonNull(status); Objects.requireNonNull(ending);
            require(status.value().equals(ClockStatusRead.decode(status.receipt().original())), "actual physical Status value differs"); }
    }
    private final CancellationReads cancellationReads;
    public LifeAdvanceComposite(AdvanceObservationPort observations, AdvanceReadiness.Port readiness, AdvanceClock timeline,
            ClockStatusRead statuses, ActionSnapshotReader actions, ActionPorts.OutcomeArchive archive, Clock clock,
            LifeAdvanceEvidence.EntryFrameReader entryFrames) {
        this(observations, readiness, timeline, statuses, actions, archive, clock, entryFrames,
                (parent, execution, children, deadline) -> { throw new IllegalStateException("actual Life cancellation terminal reader is not installed"); });
    }
    public LifeAdvanceComposite(AdvanceObservationPort observations, AdvanceReadiness.Port readiness, AdvanceClock timeline,
            ClockStatusRead statuses, ActionSnapshotReader actions, ActionPorts.OutcomeArchive archive, Clock clock,
            LifeAdvanceEvidence.EntryFrameReader entryFrames, CancellationReads cancellationReads) {
        this.cancellationReads = Objects.requireNonNull(cancellationReads);
        this.observations = Objects.requireNonNull(observations); this.readiness = Objects.requireNonNull(readiness);
        this.timeline = Objects.requireNonNull(timeline); this.statuses = Objects.requireNonNull(statuses);
        this.actions = Objects.requireNonNull(actions); this.archive = Objects.requireNonNull(archive); this.clock = Objects.requireNonNull(clock);
        this.entryFrames = Objects.requireNonNull(entryFrames);
    }
    @Override public String handlerId() { return HANDLER; }
    public static boolean accepts(String step) { return "life-advance".equals(step) || "life-advance-one-day".equals(step); }
    @Override public boolean supports(OperationKey operation) { return accepts(operation.value()); }
    /** Common ordinary/family/sway callers retain their own timeout policy and delegate the actual clock here. */
    public ActionCommand prepare(PlanningRequest request, ActionCommand original) {
        require(accepts(original.operation().value()), "ordinary preparation requires an exact registered life operation");
        var frame = observations.current(original, original.deadline());
        require(frame.identity().equals(request.before()), "ordinary life preparation requires the real exact planning frame");
        AdvanceReadiness.Facts facts = readiness.inspect(original, frame);
        require(facts.observed().equals(frame.identity()), "ordinary life readiness differs from the actual frame");
        return AdvanceRewrite.rewriteBound(request, original, original.operation().value(), Optional.empty(), facts);
    }
    /** Composition root installs this as the M7 factory so its actual durable Crown retry bound survives. */
    public ActionCommand rewrite(PlanningRequest request, ActionCommand original, String effectiveStep, CampaignDeadline.Cap cap) {
        var frame = observations.current(original, original.deadline());
        require(frame.identity().equals(request.before()), "life rewrite needs the exact real planning observation");
        AdvanceReadiness.Facts facts = readiness.inspect(original, frame);
        require(facts.observed().equals(frame.identity()), "Crown retry facts differ from the actual planning frame");
        return AdvanceRewrite.rewriteBound(request, original, effectiveStep, Optional.of(cap), facts);
    }
    @Override public void validate(ActionCommand parent) {
        require(supports(parent.operation()), "unregistered life composite");
        AdvancePlan plan = AdvancePlan.decode(parent);
        require(parent.expected().observerSchema().equals(AdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected()), "life expected postcondition was not rebuilt from the exact selected plan");
        require(!parent.operation().value().equals("life-advance-one-day") || plan.exactOneDay(), "one-day operation lost its exact-day contract");
        var frame = observations.current(parent, parent.deadline());
        require(frame.identity().equals(parent.before()), "entry public/native revision changed before durable life intent");
        require(!AdvancePolicy.present(frame.semantic().get("active_event")) && !AdvancePolicy.present(frame.semantic().get("pending_character_interaction"))
                && !AdvancePolicy.modalPresent(frame.semantic()) && !AdvancePolicy.present(frame.semantic().get("one_life_terminal_reason")), "foreground/terminal policy must consume the actual entry boundary before clock advance");
        AdvanceReadiness.verify(parent, frame, plan, readiness.inspect(parent, frame));
    }
    @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) {
        var starting = observations.current(parent, parent.deadline());
        AdvancePlan plan = AdvancePlan.decode(parent);
        require(starting.identity().equals(parent.before()), "entry drift after durable intent cannot rewrite the existing action body");
        try {
            AdvanceClock.Outcome outcome = timeline.execute(parent, children, starting, plan);
            AdvanceResult result = new AdvanceResult(parent, plan, starting, outcome, children.completed());
            ExactRef originalCompatibleResult = archive.preserveMaterial(result.encode(archive));
            ExactRef basis = LifeAdvanceEvidence.preserve(parent, starting, outcome.endingFrame(), outcome.diagnostics().progressStatus(),
                    outcome.diagnostics().nativeStopRead(), children.completed(), Optional.of(originalCompatibleResult), archive);
            return completed(parent, plan, outcome.endingFrame(), outcome.diagnostics().progressStatus(), originalCompatibleResult,
                    outcome.diagnostics().nativeStopRead(), children.completed(), List.of(basis));
        } catch (ExactDayClockFailure.StopNotObserved original) {
            // Persist the typed original failure before any cleanup can change the map.
            ExactRef gate = ExactDayClockFailureEvidence.preserveOriginal(original, actions, archive);
            ExactDayClockFailure.CleanupTrace cleanup = cleanup(parent, children);
            List<ExactRef> evidence = new ArrayList<>(); evidence.add(starting.originalEvidence()); evidence.add(gate);
            try { evidence.add(ExactDayClockFailureEvidence.preserve(original, cleanup, gate, actions, archive)); }
            catch (RuntimeException unavailableOriginals) { /* Retain Pending and canonical children; missing diagnostics grant no replay. */ }
            return new ActionPorts.Pending(ExactDayClockFailure.MESSAGE, evidence);
        } catch (AdvanceClock.ChildUnresolved unknown) {
            // No pause/cancel/resume is sent after any unknown child, even if current UI appears unchanged.
            return failed(parent,plan,starting,unknown);
        } catch (RuntimeException failure) {
            var completed = children.completed();
            if (completed.size() == 1 && completed.getFirst().state() instanceof ActionState.RejectedBeforeDispatch
                    && completed.getFirst().command().operation().value().equals(plan.armStep()))
                return new ActionPorts.CompositeRejectionObserved("original ARM rejected before dispatch; no replay",
                        completed.stream().map(child -> new CompositeExecution.Child(child.command().actionId(), child.bodySha256())).toList());
            // Original diagnostics remain in each exact child. Cleanup stays within this same authority,
            // is bounded by the parent deadline, and is forbidden if any child is unresolved.
            cleanup(parent, children);
            return failed(parent,plan,starting,failure);
        }
    }
    private ActionPorts.Pending failed(ActionCommand parent, AdvancePlan plan, AdvanceObservationPort.Frame starting, RuntimeException failure) {
        List<ExactRef> evidence = new ArrayList<>(); evidence.add(starting.originalEvidence());
        if (plan.dailyWatch().isPresent()) {
            try { evidence.add(WarDailyWatchUnresolved.preserve(parent,plan.dailyWatch().orElseThrow(),starting,failure,actions,archive)); }
            catch (RuntimeException diagnosticUnavailable) { /* Original UNKNOWN and every durable child remain canonical; no diagnostic grants replay. */ }
        }
        return new ActionPorts.Pending("life advance postcondition unavailable; no replay: " + failure.getClass().getSimpleName() + ": "
                + Objects.toString(failure.getMessage(),"unknown"),evidence);
    }
    private ExactDayClockFailure.CleanupTrace cleanup(ActionCommand parent, Children children) {
        Optional<AdvanceObservationPort.Frame> before = Optional.empty();
        Optional<ClockStatusRead.Observation> status = Optional.empty();
        try {
            if (!clock.instant().isBefore(parent.deadline())) return ExactDayClockFailure.CleanupTrace.empty();
            List<ActionReceipt> completed = children.completed();
            if (completed.stream().anyMatch(receipt -> !receipt.settled())) return ExactDayClockFailure.CleanupTrace.empty();
            if (completed.stream().allMatch(receipt -> receipt.state() instanceof ActionState.RejectedBeforeDispatch rejected
                    && rejected.dispatch().proof().stage() == NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                    && rejected.dispatch().proof().requestBytesWritten() == 0)) return ExactDayClockFailure.CleanupTrace.empty();
            var current = observations.current(parent, parent.deadline()); before = Optional.of(current);
            var plan = AdvancePlan.decode(parent);
            if (plan.dailyWatch().isPresent() && !plan.dailyWatch().orElseThrow().sameConnection(current))
                return new ExactDayClockFailure.CleanupTrace(before,status,Optional.empty());
            current = timeline.pause(parent, children, current);
            if (!AdvancePolicy.truth(current.semantic(), "paused")) return new ExactDayClockFailure.CleanupTrace(before,status,Optional.empty());
            Optional<ActionReceipt> arm = children.completed().stream().filter(receipt -> receipt.command().operation().value().startsWith(ClockStatusRead.ARM_PREFIX)).reduce((first, second) -> second);
            if (arm.isEmpty() || children.completed().stream().anyMatch(receipt -> receipt.command().operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX)))
                return new ExactDayClockFailure.CleanupTrace(before,status,Optional.empty());
            ClockStatusRead.Observation actualRead = statuses.observe(parent,current,parent.deadline()); status=Optional.of(actualRead);
            Status actual=actualRead.status();
            Status original=AdvancePrimitives.acknowledgedSentinel(arm.orElseThrow().ack().orElseThrow(),arm.orElseThrow().command().operation().value());
            AdvanceClock.requireSameSlot(original,actual);
            if (actual.state()==State.ARMED && actual.generation().equals(original.generation()))
                timeline.submit(parent,children,current,ClockStatusRead.CANCEL_PREFIX+actual.generation().decimal(),parent.deadline());
            return new ExactDayClockFailure.CleanupTrace(before,status,Optional.empty());
        } catch (RuntimeException unavailable) {
            // No new reads or commands after an UNKNOWN child; its original canonical receipt remains authoritative.
            return new ExactDayClockFailure.CleanupTrace(before,status,Optional.of(unavailable.getClass().getName()+": "+Objects.toString(unavailable.getMessage(),"unavailable")));
        }
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained) {
        require(retained.handlerId().equals(handlerId()), "retained composite handler differs");
        require(parent.origin().acceptsGuard(retained.guard().origin())
                && retained.guard().source().equals(parent.source()) && retained.guard().sessionId().equals(parent.sessionId())
                && retained.guard().operation().equals(parent.operation()) && retained.guard().observed().equals(parent.before()),
                "retained life guard differs from the original command authority");

        // No-child branch: validate exact binding and require no gameplay write before any IO
        if (retained.children().isEmpty()) {
            requireNoGameplayWrite(parent, retained);
            var observation = new CompositeNoGameplayWriteObservation(parent.actionId(), ActionCodec.bodySha256(parent), retained);
            observation.validate(parent, retained);
            return new ActionPorts.CompositeNoGameplayWriteObserved(observation);
        }

        Optional<ActionPorts.Pending> originalFailure = ExactDayClockFailureEvidence.retainedPending(parent, retained, actions, archive);
        if (originalFailure.isPresent()) return originalFailure.orElseThrow();
        List<ActionReceipt> children = new ArrayList<>();
        for (var child : retained.children()) {
            ActionReceipt receipt = actions.find(child.actionId()).orElseThrow(() -> new IllegalStateException("retained child receipt missing"));
            require(receipt.bodySha256().equals(child.bodySha256()), "retained child body conflict");
            if (!receipt.settled()) return new ActionPorts.Pending("original durable life child is still unresolved; reconciliation only", List.of(retained.guard().nativeEvidence()));
            children.add(receipt);
        }
        if (children.stream().anyMatch(child -> child.command().operation().value().startsWith(ClockStatusRead.ARM_PREFIX))
                && children.stream().noneMatch(child -> child.command().operation().value().equals("resume-map"))) {
            if (children.getLast().command().operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX))
                return cancelledInitialization(parent, retained, children, ActionObservationWindow.deadline(parent));
            if (children.size() == 1 && children.getFirst().state() instanceof ActionState.RejectedBeforeDispatch) {
                requireRejectedInitialization(parent, retained, children);
                return new ActionPorts.CompositeRejectionObserved("original ARM rejected before dispatch; no replay", retained.children());
            }
            return new ActionPorts.Pending("original ARM is independently confirmed; source-issued generation cancellation is required before ordinary play",
                    List.of(retained.guard().nativeEvidence()));
        }
        AdvanceClockArchivedReplay.verifyChildBindings(parent, children);
        AdvancePlan plan = AdvancePlan.decode(parent);
        if (children.size() <= 2 && children.stream().allMatch(child ->
                child.command().operation().value().equals("pause-map")
                || child.command().operation().value().equals("set-speed-" + plan.speed()))) {
            try {
                var actualEnding = entryFrames.readChild(children.getLast(), archive);
                if (actualEnding.isEmpty())
                    return new ActionPorts.Pending("original Life initialization lacks its canonical child's independent post-state; reconciliation only",
                            List.of(retained.guard().nativeEvidence()));
                var ending = actualEnding.orElseThrow();
                var interruption = new LifeControlPrefixInterruption(parent.actionId(), ActionCodec.bodySha256(parent), retained,
                        LifeAdvanceEvidence.preserveFrame(ending, archive));
                interruption.validateParent(parent, retained);
                interruption.validateChildren(parent, children);
                interruption.validateFrame(parent, ending, children);
                return new ActionPorts.LifeControlPrefixInterruptedObserved(interruption);
            } catch (RuntimeException unavailable) {
                return new ActionPorts.Pending("original Life initialization post-state remains unconfirmed: "
                        + unavailable.getClass().getSimpleName() + ": " + Objects.toString(unavailable.getMessage(), "unavailable"),
                        List.of(retained.guard().nativeEvidence()));
            }
        }
        Optional<AdvanceObservationPort.Frame> archivedStart = entryFrames.read(parent, retained.guard(), archive);
        if (archivedStart.isEmpty()) return new ActionPorts.Pending("original life start lacks its complete native/Driver guard basis; no fabricated episode or public revision", List.of(retained.guard().nativeEvidence()));
        AdvanceObservationPort.Frame starting = archivedStart.orElseThrow();
        require(starting.identity().equals(parent.before()) && starting.source().equals(parent.source()) && starting.sessionId().equals(parent.sessionId()), "archived life start crossed original authority");
        Instant window = ActionObservationWindow.deadline(parent);
        var current = observations.current(parent, window);
        if (!AdvancePolicy.truth(current.semantic(), "paused") || !current.identity().frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                || !current.identity().frame().identity().player().equals(parent.before().frame().identity().player()))
            return new ActionPorts.Pending("original clock needs an actual paused same-episode/same-actor terminal observation", List.of(current.originalEvidence()));
        BigInteger end = current.identity().frame().identity().dateRaw();
        boolean boundary = AdvanceProgress.boundary(current, starting, plan).isPresent();
        long resumes = children.stream().filter(receipt -> receipt.command().operation().value().equals("resume-map") && receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED).count();
        if (resumes > 1 || end.compareTo(plan.startingDateRaw()) < 0 || (plan.exactOneDay() || plan.clockMode() != AdvancePlan.ClockMode.POLLED) && end.compareTo(plan.targetDateRaw()) > 0)
            return new ActionPorts.Pending("original life timeline lacks matching resume/date proof", List.of(current.originalEvidence()));
        Optional<ClockStatusRead.Observation> terminal = Optional.empty();
        boolean canceled = false;
        if (plan.clockMode() != AdvancePlan.ClockMode.POLLED) {
            ActionReceipt arm = children.stream().filter(receipt -> receipt.command().operation().value().equals(plan.armStep())
                    && receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED).findFirst().orElseThrow(() -> new IllegalStateException("retained exact arm missing"));
            Status armed = AdvancePrimitives.acknowledgedSentinel(arm.ack().orElseThrow(), plan.armStep()); AdvanceClock.validateArm(armed, plan);
            var read = statuses.observe(parent, current, window); Status actual = read.status();
            if (actual.state() == State.TRIGGERED) AdvanceClock.validateStop(armed, actual, plan, end);
            else if (boundary && end.compareTo(plan.targetDateRaw()) < 0 && actual.state() == State.IDLE && actual.generation().equals(armed.generation())
                    && children.stream().anyMatch(receipt -> receipt.command().operation().value().equals(ClockStatusRead.CANCEL_PREFIX + armed.generation().decimal())
                        && receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED)) {
                AdvanceClock.validateCancellation(armed, actual, plan, end); canceled = true;
            } else
                return new ActionPorts.Pending("original native clock stop or generation-bound cancellation remains unconfirmed", List.of(read.originalEvidence()));
            terminal = Optional.of(read);
            var fresh = observations.current(parent, window);
            AdvanceClock.requireAfterControl(parent, current, read, fresh);
            require(AdvanceProgress.boundary(fresh, starting, plan).isPresent() == boundary, "retained life boundary changed after independent clock query");
            current = fresh;
        } else if (end.compareTo(plan.targetDateRaw()) < 0 && !boundary) {
            return new ActionPorts.Pending("original early polled timeline has neither horizon nor actual full-frame boundary proof", List.of(current.originalEvidence()));
        }
        boolean alreadyRunning = !AdvancePolicy.truth(starting.semantic(), "paused") && plan.clockMode() == AdvancePlan.ClockMode.POLLED;
        boolean preResumeBoundary = resumes == 0 && canceled && end.equals(plan.startingDateRaw()) && boundary
                && children.stream().noneMatch(receipt -> receipt.command().operation().value().equals("resume-map"));
        if (resumes != 1 && !alreadyRunning && !preResumeBoundary)
            return new ActionPorts.Pending("original timeline has no observed resume or actual pre-resume cancellation proof", List.of(current.originalEvidence()));
        AdvanceClock.ProgressStatus progress = boundary && end.compareTo(plan.targetDateRaw()) < 0
                ? AdvanceProgress.newModal(current.semantic(), starting.identity(), Optional.of(starting.semantic())).isPresent()
                    ? AdvanceClock.ProgressStatus.MODAL_INTERRUPTED : AdvanceClock.ProgressStatus.BOUNDARY_INTERRUPTED
                : AdvanceClock.ProgressStatus.POSTCONDITION;
        // Reconciliation records actual retained start and fresh end. It does not invent
        // the old full wall time, child transport diagnostic report, or compatible result.
        ExactRef basis = LifeAdvanceEvidence.preserve(parent, starting, current, progress, terminal, children, Optional.empty(), archive);
        return completed(parent, plan, current, progress, null, terminal, children, List.of(basis));
    }
    /** Issues only from the canonical independently confirmed, never-resumed original ARM prefix. */
    public Optional<LifeSentinelCancellation> cancellationToken(ActionReceipt original, Instant deadline) {
        if (!(original.state() instanceof ActionState.CompositeUnknown unknown)) return Optional.empty();
        ActionReceipt current = actions.find(original.command().actionId()).orElseThrow();
        require(current.equals(original), "Life cancellation issuer needs its actual canonical parent");
        var parent = original.command(); var retained = unknown.execution();
        List<ActionReceipt> prefix = canonicalChildren(retained);
        var plan = AdvancePlan.decode(parent);
        if (plan.clockMode() == AdvancePlan.ClockMode.POLLED || prefix.isEmpty()
                || !prefix.getLast().command().operation().value().equals(plan.armStep())) return Optional.empty();
        if (prefix.stream().anyMatch(child -> !child.settled()) || prefix.stream().anyMatch(child ->
                child.command().operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX)
                || child.command().operation().value().equals("resume-map"))) return Optional.empty();
        if (prefix.size() == 1 && prefix.getFirst().state() instanceof ActionState.RejectedBeforeDispatch) {
            requireRejectedInitialization(parent, retained, prefix);
            return Optional.empty();
        }
        ActionReceipt arm = LifeSentinelCancellationProof.prefix(parent, retained, prefix, false);
        var armState = (ActionState.Settled) arm.state();
        PlanningReadReceipt read = ((ActionState.ControlApplied) armState.settlement()).read();
        if (!clock.instant().isBefore(deadline)) return Optional.empty();
        // The new cancellation uses a real fresh read and its own deadline, not a renewed historical query qualification.
        CancellationRead refreshed = cancellationReads.read(parent, retained, prefix, deadline);
        var beforeCancel = refreshed.ending();
        requireCancellationFrame(parent, beforeCancel);
        var status = LifeSentinelCancellationProof.confirmedArm(parent, arm);
        require(refreshed.status().value().equals(status), "fresh independent Status no longer confirms the original ARM slot");
        var custody = LifeSentinelCancellationProof.physical(parent, refreshed.status().receipt());
        require(!beforeCancel.observedAt().isBefore(custody.responseReceived().observedAt()),
                "Life cancellation starting frame predates its fresh independent ARM Status");
        return Optional.of(new LifeSentinelCancellation(this, parent, retained, refreshed.status().receipt(), beforeCancel,
                new BigInteger(status.generation().decimal()), deadline));
    }

    private List<ActionReceipt> canonicalChildren(CompositeExecution retained) {
        var result = new ArrayList<ActionReceipt>();
        for (var bound : retained.children()) {
            ActionReceipt child = actions.find(bound.actionId()).orElseThrow();
            require(child.bodySha256().equals(bound.bodySha256()), "Life cancellation child body differs from canonical history");
            result.add(child);
        }
        return List.copyOf(result);
    }

    private static void requireCancellationFrame(ActionCommand parent, AdvanceObservationPort.Frame frame) {
        LifeSentinelCancellationProof.sameFrame(parent, frame.identity());
        require(frame.source().equals(parent.source()) && frame.sessionId().equals(parent.sessionId())
                && AdvancePolicy.truth(frame.semantic(), "paused") && AdvancePolicy.truth(frame.semantic(), "map_ready"),
                "Life cancellation requires the actual same-date paused-map source frame");
    }

    @Override public void requireContinuation(ActionCommand parent, CompositeExecution retained, CompositeContinuationToken token) {
        require(token instanceof LifeSentinelCancellation, "this Life source issues only sentinel cancellation continuation");
        LifeSentinelCancellation cancellation = (LifeSentinelCancellation) token;
        require(cancellation.issuedBy(this) && cancellation.originalParent().equals(parent), "Life cancellation token has another issuer or parent");
        var original = cancellation.originalExecution();
        require(retained.handlerId().equals(original.handlerId()) && retained.startedAt().equals(original.startedAt())
                && retained.guard().equals(original.guard()) && retained.children().size() >= original.children().size()
                && retained.children().size() <= original.children().size() + 1
                && retained.children().subList(0, original.children().size()).equals(original.children()),
                "Life cancellation changed its original durable prefix");
        var prefix = canonicalChildren(original);
        ActionReceipt arm = LifeSentinelCancellationProof.prefix(parent, original, prefix, false);
        var armState = (ActionState.Settled) arm.state();
        require(ClockStatusRead.decode(cancellation.armedRead().original()).equals(LifeSentinelCancellationProof.confirmedArm(parent, arm))
                && cancellation.generation().equals(new BigInteger(LifeSentinelCancellationProof.confirmedArm(parent, arm).generation().decimal()))
                && !cancellation.deadline().isAfter(cancellation.armedRead().request().deadline()),
                "Life cancellation lost its exact independently confirmed ARM generation");
        var custody = LifeSentinelCancellationProof.physical(parent, cancellation.armedRead());
        require(!cancellation.beforeCancel().observedAt().isBefore(custody.responseReceived().observedAt()),
                "Life cancellation token has no real fresh after-Status paused frame");
        requireCancellationFrame(parent, cancellation.beforeCancel());
        if (retained.children().size() > original.children().size()) {
            var reserved = retained.children().getLast();
            ActionCommand exact = cancellationChild(parent, cancellation, reserved.actionId());
            require(reserved.actionId().equals(ActionIds.child(parent.actionId(), retained.children().size(), exact.operation()))
                    && reserved.bodySha256().equals(ActionCodec.bodySha256(exact)),
                    "Life cancellation reservation is not its one exact source-issued child");
        }
    }

    private static ActionCommand cancellationChild(ActionCommand parent, LifeSentinelCancellation token, String actionId) {
        var step = new OperationKey(ClockStatusRead.CANCEL_PREFIX + token.generation());
        var frame = token.beforeCancel();
        var arguments = new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of());
        // This is a new, source-qualified control child with a new operation deadline; the historical parent is immutable.
        return new ActionCommand(actionId, frame.identity(), parent.source(), parent.sessionId(), step, arguments,
                AdvancePrimitives.expected(frame.identity(), parent.source(), step, arguments), parent.claims(), token.deadline());
    }

    @Override public void requireContinuationChild(ActionCommand parent, CompositeExecution retained,
            CompositeContinuationToken token, ActionCommand child) {
        requireContinuation(parent, retained, token);
        var cancellation = (LifeSentinelCancellation) token;
        require(retained.children().size() == cancellation.originalExecution().children().size()
                && child.actionId().equals(ActionIds.child(parent.actionId(), retained.children().size() + 1, child.operation()))
                && child.equals(cancellationChild(parent, cancellation, child.actionId())),
                "Life continuation permits only its one exact original-generation CANCEL");
    }

    @Override public ActionPorts.PostconditionResult continueOriginal(ActionCommand parent, CompositeExecution retained,
            CompositeContinuationToken token, Children children) {
        requireContinuation(parent, retained, token);
        var cancellation = (LifeSentinelCancellation) token;
        require(clock.instant().isBefore(cancellation.deadline()), "Life cancellation operation deadline expired");
        require(retained.children().size() == cancellation.originalExecution().children().size(),
                "an already reserved cancellation is reconciliation-only and cannot be submitted again");
        ActionCommand command = cancellationChild(parent, cancellation,
                children.nextActionId(new OperationKey(ClockStatusRead.CANCEL_PREFIX + cancellation.generation())));
        ActionReceipt canceled = children.submit(command);
        if (!canceled.settled() || canceled.outcome() != ActionReceipt.Outcome.APPLIED_CONFIRMED)
            return new ActionPorts.Pending("original generation cancellation is unresolved; no retry or resume", List.of(retained.guard().nativeEvidence()));
        return cancelledInitialization(parent, new CompositeExecution(retained.handlerId(), retained.startedAt(), retained.guard(),
                children.completed().stream().map(child -> new CompositeExecution.Child(child.command().actionId(), child.bodySha256())).toList()),
                children.completed(), cancellation.deadline());
    }

    private ActionPorts.PostconditionResult cancelledInitialization(ActionCommand parent, CompositeExecution retained,
            List<ActionReceipt> children, Instant deadline) {
        LifeSentinelCancellationProof.prefix(parent, retained, children, true);
        // Actual fixed physical Status has no ordinary Driver/Ready or action permission.
        CancellationRead terminal = cancellationReads.read(parent, retained, children, deadline);
        var ending = terminal.ending();
        requireCancellationFrame(parent, ending);
        var plan = AdvancePlan.decode(parent);
        var starting = entryFrames.read(parent, retained.guard(), archive).orElseThrow();
        ExactRef basis = LifeAdvanceEvidence.preserveCancelled(parent, starting, ending, terminal.status().receipt(), children, archive);
        var semantic = observation(parent, plan, ending, AdvanceClock.ProgressStatus.INITIALIZATION_CANCELLED, null, List.of(basis));
        var canceled = (ActionState.ControlApplied) ((ActionState.Settled) children.getLast().state()).settlement();
        var control = new CompositeControlObservation(terminal.status().receipt(), List.of(canceled.read()), semantic);
        requireCancelledInitialization(parent, retained, control, children);
        return new ActionPorts.CompositeControlObserved(control);
    }

    /** Pure canonical DATA proof shared by the source's physical read callback and its archive replay. */
    public static void requireCancelledInitializationPrefix(ActionCommand parent, CompositeExecution execution, List<ActionReceipt> canonicalChildren) {
        LifeSentinelCancellationProof.prefix(parent, execution, canonicalChildren, true);
    }
    public static void requireArmedInitializationPrefix(ActionCommand parent, CompositeExecution execution, List<ActionReceipt> canonicalChildren) {
        LifeSentinelCancellationProof.prefix(parent, execution, canonicalChildren, false);
    }
    /** The installed archive verifier separately rebuilds the complete paused ending frame. */
    public static void requireCancelledInitialization(ActionCommand parent, CompositeExecution execution,
            CompositeControlObservation control, List<ActionReceipt> canonicalChildren) {
        LifeSentinelCancellationProof.terminal(parent, execution, control, canonicalChildren);
    }

    /** Exact source-owned rejection: the only durable child was the requested ARM and no request byte was written. */
    public static void requireRejectedInitialization(ActionCommand parent, CompositeExecution execution, List<ActionReceipt> canonicalChildren) {
        require(parent.origin() instanceof CommandOrigin.Gameplay && accepts(parent.operation().value())
                && execution.handlerId().equals(HANDLER), "rejected initialization requires its original Life handler");
        var plan = AdvancePlan.decode(parent);
        require(parent.expected().observerSchema().equals(AdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected())
                && (!parent.operation().value().equals("life-advance-one-day") || plan.exactOneDay()),
                "rejected initialization lost its original Life plan");
        var guard = execution.guard();
        require(parent.origin().acceptsGuard(guard.origin()) && guard.source().equals(parent.source())
                && guard.sessionId().equals(parent.sessionId()) && guard.operation().equals(parent.operation())
                && guard.observed().equals(parent.before()), "rejected initialization parent guard changed");
        require(execution.children().size() == 1 && canonicalChildren.size() == 1,
                "rejected initialization requires its sole original ARM child");
        AdvanceClockArchivedReplay.verifyChildBindings(parent, canonicalChildren);
        var child = canonicalChildren.getFirst(); var command = child.command(); var bound = execution.children().getFirst();
        require(bound.actionId().equals(command.actionId()) && bound.bodySha256().equals(child.bodySha256())
                && plan.clockMode() != AdvancePlan.ClockMode.POLLED && command.operation().value().equals(plan.armStep())
                && command.before().equals(parent.before()) && command.arguments().members().isEmpty()
                && AdvancePrimitives.expected(command.before(), command.source(), command.operation(), command.arguments()).equals(command.expected())
                && child.state() instanceof ActionState.RejectedBeforeDispatch,
                "rejected initialization child differs from its exact unsubmitted ARM");
        var rejected = (ActionState.RejectedBeforeDispatch) child.state(); var attempt = rejected.attempt();
        require(command.origin().acceptsGuard(attempt.guard().origin()) && attempt.guard().observed().equals(command.before())
                && attempt.guard().source().equals(command.source()) && attempt.guard().sessionId().equals(command.sessionId())
                && attempt.guard().operation().equals(command.operation())
                && attempt.preparedRequest().equals(AdvancePrimitives.prepareRequest(command))
                && rejected.dispatch().requestId().equals(attempt.requestId())
                && rejected.dispatch().proof().stage() == NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                && rejected.dispatch().proof().requestBytesWritten() == 0 && child.ack().isEmpty(),
                "rejected initialization requires its actual original zero-dispatch proof");
    }

    @Override public void requireControlPrefixInterruption(ActionCommand parent, CompositeExecution retained,
            LifeControlPrefixInterruption observation, List<ActionReceipt> canonicalChildren) {
        observation.validateParent(parent, retained);
        observation.validateChildren(parent, canonicalChildren);
    }

    @Override public void requireNoGameplayWrite(ActionCommand parent, CompositeExecution retained) {
        requireNoGameplayWriteOriginal(parent, retained);
    }
    /** Same source-owned producer contract for the registered handler and archive-only writer revalidation. */
    public static void requireNoGameplayWriteOriginal(ActionCommand parent, CompositeExecution retained) {
        require(parent.origin() instanceof CommandOrigin.Gameplay, "zero-child Life reconciliation requires its original gameplay parent");
        require(accepts(parent.operation().value()), "unregistered life composite");
        require(retained.handlerId().equals(HANDLER), "retained composite handler differs");
        require(parent.origin().acceptsGuard(retained.guard().origin())
                && retained.guard().source().equals(parent.source()) && retained.guard().sessionId().equals(parent.sessionId())
                && retained.guard().operation().equals(parent.operation()) && retained.guard().observed().equals(parent.before()),
                "retained life guard differs from the original command authority");
        require(retained.children().isEmpty(), "no-gameplay-write requires empty child vector");

        // Validate exact Life plan/operation/expected postcondition without observation IO
        AdvancePlan plan = AdvancePlan.decode(parent);
        require(parent.expected().observerSchema().equals(AdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected()), "life expected postcondition was not rebuilt from the exact selected plan");
        require(!parent.operation().value().equals("life-advance-one-day") || plan.exactOneDay(), "one-day operation lost its exact-day contract");
    }

    private static ActionPorts.PostconditionResult completed(ActionCommand parent, AdvancePlan plan, AdvanceObservationPort.Frame ending,
            AdvanceClock.ProgressStatus status, ExactRef compatibleResult, Optional<ClockStatusRead.Observation> terminal,
            List<ActionReceipt> children, List<ExactRef> evidence) {
        if (!ending.identity().frame().identity().player().equals(parent.before().frame().identity().player()))
            return new ActionPorts.Pending("native episode terminal changed the played actor; original successor authority must consume it", List.of(ending.originalEvidence()));
        ActionState.EffectObservation semantic = observation(parent, plan, ending, status, compatibleResult, evidence);
        if (ending.identity().frame().identity().nativeRevision().equals(parent.before().frame().identity().nativeRevision())
                && ending.identity().frame().identity().dateRaw().equals(plan.startingDateRaw())) {
            require(status == AdvanceClock.ProgressStatus.MODAL_INTERRUPTED || status == AdvanceClock.ProgressStatus.BOUNDARY_INTERRUPTED,
                    "unchanged native frame needs the actual pre-resume boundary terminal");
            return new ActionPorts.CompositeControlObserved(AdvanceClock.compositeControlTerminal(parent,
                    terminal.orElseThrow(() -> new IllegalStateException("zero-day boundary lacks independent generation cancellation Status")), children, semantic));
        }
        return new ActionPorts.EffectObserved(semantic);
    }
    static ActionState.EffectObservation observation(ActionCommand parent, AdvancePlan plan, AdvanceObservationPort.Frame ending,
            AdvanceClock.ProgressStatus status, ExactRef compatibleResult, List<ExactRef> evidence) {
        List<ExpectedValue> actual = new ArrayList<>(plan.expected());
        boolean days = ending.identity().frame().identity().dateRaw().subtract(plan.startingDateRaw()).compareTo(AdvancePlan.DAY) >= 0;
        boolean credit = days && status == AdvanceClock.ProgressStatus.POSTCONDITION
                && !AdvancePolicy.present(ending.semantic().get("one_life_terminal_reason"));
        actual.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), days));
        actual.add(new ExpectedBoolean(new FieldKey("timeline.advance_verified"), days));
        actual.add(new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), credit));
        actual.add(new ExpectedText(new FieldKey("progress_status"), AdvanceResult.progressStatus(status)));
        actual.add(new ExpectedInteger(new FieldKey("advance.ending_date_raw"), ending.identity().frame().identity().dateRaw()));
        if (compatibleResult != null) {
            actual.add(new ExpectedText(new FieldKey("advance.result.sha256"), compatibleResult.sha256()));
            actual.add(new ExpectedInteger(new FieldKey("advance.result.bytes"), BigInteger.valueOf(compatibleResult.bytes())));
            actual.add(new ExpectedText(new FieldKey("advance.result.path"), compatibleResult.path()));
        }
        return new ActionState.EffectObservation(ending.identity(), ending.source(), ending.sessionId(), AdvancePlan.OBSERVER,
                actual, ending.provenance(), ending.observedAt(), ending.originalEvidence(), evidence);
    }
}
