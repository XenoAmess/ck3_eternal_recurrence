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
public final class LifeAdvanceComposite implements CompositeActionPort.ZeroGameplayBeforeChildren {
    public static final String HANDLER = "java.native-driver.life-advance.v1";
    private final AdvanceObservationPort observations;
    private final AdvanceReadiness.Port readiness;
    private final AdvanceClock timeline;
    private final ClockStatusRead statuses;
    private final ActionSnapshotReader actions;
    private final ActionPorts.OutcomeArchive archive;
    private final Clock clock;
    private final LifeAdvanceEvidence.EntryFrameReader entryFrames;
    public LifeAdvanceComposite(AdvanceObservationPort observations, AdvanceReadiness.Port readiness, AdvanceClock timeline,
            ClockStatusRead statuses, ActionSnapshotReader actions, ActionPorts.OutcomeArchive archive, Clock clock,
            LifeAdvanceEvidence.EntryFrameReader entryFrames) {
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
        AdvanceClockArchivedReplay.verifyChildBindings(parent, children);
        AdvancePlan plan = AdvancePlan.decode(parent);
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
