package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.LongSupplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwnerCodec;

/** One native clock slice inside the original composite's durable Children transaction. No loop/backend/pipe/writer. */
public final class AdvanceClock {
    public enum ProgressStatus { POSTCONDITION, MODAL_INTERRUPTED, BOUNDARY_INTERRUPTED, WALL_TIMEOUT_WITH_DATE_PROGRESS, INITIALIZATION_CANCELLED }
    public record Diagnostics(BigInteger startingDateRaw, BigInteger endingDateRaw, int elapsedDays,
            int requestedHorizonDays, int timelineSpeed, String timelinePolicy, ProgressStatus progressStatus,
            Optional<Status> armed, Optional<Status> stopped, boolean canceled,
            List<String> childActionIds, long fullWallNanos, Optional<ClockStatusRead.Observation> nativeStopRead) {
        public Diagnostics {
            Objects.requireNonNull(startingDateRaw); Objects.requireNonNull(endingDateRaw);
            require(endingDateRaw.compareTo(startingDateRaw) >= 0 && endingDateRaw.subtract(startingDateRaw).mod(AdvancePlan.DAY).signum() == 0
                    && elapsedDays == endingDateRaw.subtract(startingDateRaw).divide(AdvancePlan.DAY).intValueExact()
                    && fullWallNanos >= 0, "actual observed date delta and complete clock wall time required");
            Objects.requireNonNull(armed); Objects.requireNonNull(stopped); childActionIds = List.copyOf(childActionIds);
            Objects.requireNonNull(nativeStopRead); require(stopped.isPresent() == nativeStopRead.isPresent()
                    && (nativeStopRead.isEmpty() || stopped.orElseThrow().equals(nativeStopRead.orElseThrow().status())), "native stop needs its exact original independent Status receipt");
        }
    }
    public record Outcome(AdvanceObservationPort.Frame endingFrame, Diagnostics diagnostics) {
        public Outcome { Objects.requireNonNull(endingFrame); Objects.requireNonNull(diagnostics); }
    }
    public static final class ChildUnresolved extends IllegalStateException {
        private static final long serialVersionUID = 1L;
        // In-process failure context; durable evidence uses the existing JSON publisher.
        @SuppressWarnings("serial")
        private final ActionReceipt receipt;
        ChildUnresolved(ActionReceipt receipt) { super("durable native child unresolved; no replay or cleanup: " + receipt.command().actionId()); this.receipt = receipt; }
        public ActionReceipt receipt() { return receipt; }
    }
    private final AdvanceObservationPort observations;
    private final ClockStatusRead statuses;
    private final AdvanceReadiness.Port readiness;
    private final AdvanceWait waits;
    private final Clock clock;
    private final LongSupplier nanos;
    private final Duration commandTimeout;
    private final Duration advanceTimeout;
    public AdvanceClock(AdvanceObservationPort observations, ClockStatusRead statuses, AdvanceReadiness.Port readiness,
            Clock clock, int maximumFrames, Duration commandTimeout, Duration advanceTimeout) {
        this(observations, statuses, readiness, clock, maximumFrames, commandTimeout, advanceTimeout, System::nanoTime);
    }
    public AdvanceClock(AdvanceObservationPort observations, ClockStatusRead statuses, AdvanceReadiness.Port readiness,
            Clock clock, int maximumFrames, Duration commandTimeout, Duration advanceTimeout, LongSupplier nanos) {
        this.observations = Objects.requireNonNull(observations); this.statuses = Objects.requireNonNull(statuses);
        this.readiness = Objects.requireNonNull(readiness); this.clock = Objects.requireNonNull(clock); this.nanos = Objects.requireNonNull(nanos);
        this.waits = new AdvanceWait(observations, clock, maximumFrames);
        require(!commandTimeout.isNegative() && !commandTimeout.isZero() && commandTimeout.compareTo(Duration.ofMinutes(5)) <= 0
                && !advanceTimeout.isNegative() && !advanceTimeout.isZero() && advanceTimeout.compareTo(Duration.ofHours(1)) <= 0, "finite actual timeout configuration required");
        this.commandTimeout = commandTimeout; this.advanceTimeout = advanceTimeout;
    }
    /** Reused by route/war/death composites. The caller still owns its own parent postcondition. */
    public Outcome executeExact(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame starting,
            int preferredSpeed, String proofKind) {
        return executeExactDetailed(parent, children, starting, preferredSpeed, proofKind).outcome();
    }
    public record ExactOutcome(AdvancePlan plan, Outcome outcome) {
        public ExactOutcome { Objects.requireNonNull(plan); Objects.requireNonNull(outcome); }
    }
    /** Returns the actual normalized plan, including capability-based speed and clock-mode selection. */
    public ExactOutcome executeExactDetailed(ActionCommand parent, CompositeActionPort.Children children,
            AdvanceObservationPort.Frame starting, int preferredSpeed, String proofKind) {
        require(preferredSpeed >= 1 && preferredSpeed <= 5, "validated preferred native speed required");
        AdvanceReadiness.Facts facts = readiness.inspect(parent, starting);
        int speed = "contact_free".equals(proofKind) && facts.actionSteps().contains(new OperationKey("set-speed-" + preferredSpeed)) ? preferredSpeed : 1;
        String policy = "contact_free".equals(proofKind) ? "exact_one_day_contact_free_speed_" + speed
                : "battle_identity_materialization".equals(proofKind) ? "exact_one_day_battle_identity_materialization" : "exact_one_day_unavoidable_contact";
        BigInteger start = starting.identity().frame().identity().dateRaw();
        AdvancePlan plan = new AdvancePlan(start, start.add(AdvancePlan.DAY), 1, speed, policy, true,
                ClockStatusRead.available(facts.bridgeCapabilities()) ? AdvancePlan.ClockMode.EXACT_SENTINEL : AdvancePlan.ClockMode.POLLED, Optional.empty());
        return new ExactOutcome(plan, execute(parent, children, starting, plan));
    }
    public Outcome execute(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame starting, AdvancePlan plan) {
        long begun = nanos.getAsLong();
        AdvanceReadiness.verify(parent, starting, plan, readiness.inspect(parent, starting));
        require(starting.identity().frame().identity().dateRaw().equals(plan.startingDateRaw()), "advance plan starting date differs");
        plan.dailyWatch().ifPresent(watch -> require(watch.starting().equals(starting.identity()), "daily watch differs from original immutable entry frame"));
        AdvanceObservationPort.Frame current = starting;
        Optional<Status> armed = Optional.empty(), stopped = Optional.empty(); boolean canceled = false;
        Optional<ClockStatusRead.Observation> nativeStopRead = Optional.empty();
        int childStart = children.completed().size();
        if (integer(current.semantic().get("speed"), "speed").intValueExact() != plan.speed()) {
            ActionReceipt setter = submit(parent, children, current, "set-speed-" + plan.speed(), bounded(parent, commandTimeout));
            require(setter.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED, "native speed setter was definitively rejected");
            current = current(parent); final int speed = plan.speed();
            current = waits.until(parent, current, frame -> integer(frame.semantic().get("speed"), "speed").intValueExact() == speed, bounded(parent, commandTimeout));
            require(integer(current.semantic().get("speed"), "speed").intValueExact() == speed, "native timeline speed was not independently observed");
        }
        if (plan.clockMode() != AdvancePlan.ClockMode.POLLED) {
            AdvanceObservationPort.Frame actualBeforeArm = current;
            plan.dailyWatch().ifPresent(watch -> require(watch.readyToArm(actualBeforeArm), "daily watch owner/complete roster/speed changed before original arm"));
            require(AdvancePolicy.truth(current.semantic(), "paused") && current.identity().frame().identity().dateRaw().equals(plan.startingDateRaw()), "native arm requires same actual paused date");
            ActionReceipt receipt = submit(parent, children, current, plan.armStep(), bounded(parent, commandTimeout));
            require(receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED, "native sentinel arm was definitively rejected");
            NativeActionPort.AckReceived ack = receipt.ack().orElseThrow(() -> new IllegalStateException("durable arm has no original ACK"));
            Status arm = AdvancePrimitives.acknowledgedSentinel(ack, plan.armStep()); validateArm(arm, plan);
            armed = Optional.of(arm); current = current(parent);
        }
        // A freshly observed modal can arrive after arm while the map never ran. In that
        // case the only mutation still needed is cancellation of our confirmed generation.
        // An actually submitted resume remains non-replayable, including UNKNOWN.
        if (AdvanceProgress.boundary(current, starting, plan).isEmpty()) current = resume(parent, children, current, starting, plan);
        Instant progressDeadline = bounded(parent, advanceTimeout);
        final AdvanceObservationPort.Frame original = starting;
        final boolean nativeClock = plan.clockMode() != AdvancePlan.ClockMode.POLLED;
        current = waits.until(parent, current, frame -> plan.dailyWatch().isPresent() ? watchedStop(plan, frame, starting.identity().frame().revision())
                : AdvancePolicy.truth(frame.semantic(), "paused")
                || (nativeClock ? frame.identity().frame().identity().dateRaw().compareTo(plan.targetDateRaw()) < 0
                    && AdvanceProgress.boundary(frame, original, plan).isPresent()
                    : AdvanceProgress.boundary(frame, original, plan).isPresent()), progressDeadline);
        if (plan.exactOneDay() && plan.clockMode() == AdvancePlan.ClockMode.EXACT_SENTINEL && plan.dailyWatch().isEmpty()
                && !AdvancePolicy.truth(current.semantic(), "paused")
                && AdvanceProgress.newModal(current.semantic(), starting.identity(), Optional.of(starting.semantic())).isEmpty()) {
            // This is before the normal Status query or stop validation. Cleanup remains Life's original authority.
            throw new ExactDayClockFailure.StopNotObserved(parent, plan, starting, current, armed.orElseThrow(), childStart,
                    children.completed().subList(childStart, children.completed().size()));
        }
        boolean observedProgress = AdvancePolicy.truth(current.semantic(), "paused") || AdvanceProgress.boundary(current, starting, plan).isPresent();
        current = pause(parent, children, current, plan.dailyWatch());
        AdvanceObservationPort.Frame actualPaused = current;
        plan.dailyWatch().ifPresent(watch -> require(watch.sameOwner(actualPaused)
                && integer(actualPaused.semantic().get("speed"), "speed").intValueExact() == 2, "daily watch stopped owner/connection/speed changed"));
        require(AdvancePolicy.truth(current.semantic(), "paused"), "native paused ending state is unavailable");
        BigInteger end = current.identity().frame().identity().dateRaw();
        require(end.compareTo(plan.startingDateRaw()) >= 0, "native date regressed");
        if (plan.exactOneDay() || nativeClock) require(end.compareTo(plan.targetDateRaw()) <= 0, "native exact/campaign date clock overshot; never replay");
        ProgressStatus progress = observedProgress ? ProgressStatus.POSTCONDITION : ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS;
        if (!observedProgress) require(end.compareTo(plan.startingDateRaw()) > 0, "bounded native timeline observed neither date change nor lawful progress");
        if (armed.isPresent()) {
            ClockStatusRead.Observation read = statuses.observe(parent, current, bounded(parent, commandTimeout));
            nativeStopRead = Optional.of(read);
            Status status = read.status(); Status arm = armed.orElseThrow(); stopped = Optional.of(status);
            if (status.state() == State.ARMED && end.compareTo(plan.targetDateRaw()) < 0) {
                require(AdvanceProgress.boundary(current, starting, plan).isPresent(), "armed clock paused early without an actual event/terminal/modal/war boundary");
                require(sameSlot(arm, status) && !status.abnormal(), "native early-boundary sentinel slot changed");
                AdvanceObservationPort.Frame beforeCancel = current;
                ActionReceipt cancel = submit(parent, children, current, ClockStatusRead.CANCEL_PREFIX + arm.generation().decimal(), bounded(parent, commandTimeout));
                require(cancel.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED, "native early-boundary cancel was definitively rejected");
                canceled = true;
                // Cancellation changes the control slot and need not publish a later semantic
                // native revision. Read the slot, then independently acquire current SEM.
                ClockStatusRead.Observation canceledRead = statuses.observe(parent, beforeCancel, bounded(parent, commandTimeout));
                validateCancellation(arm, canceledRead.status(), plan, end);
                stopped = Optional.of(canceledRead.status()); nativeStopRead = Optional.of(canceledRead);
                AdvanceObservationPort.Frame afterStatus = current(parent);
                requireAfterControl(parent, beforeCancel, canceledRead, afterStatus);
                require(sameBoundary(beforeCancel, afterStatus), "native early boundary changed after independent canceled Status");
                if (plan.dailyWatch().isPresent()) require(plan.dailyWatch().orElseThrow().boundary(beforeCancel).equals(plan.dailyWatch().orElseThrow().boundary(afterStatus)), "daily watch actual early boundary changed after cancel");
                current = afterStatus;
                progress = AdvanceProgress.newModal(current.semantic(), starting.identity(), Optional.of(starting.semantic())).isPresent()
                        ? ProgressStatus.MODAL_INTERRUPTED : ProgressStatus.BOUNDARY_INTERRUPTED;
            } else {
                validateStop(arm, status, plan, end);
                // Status is a separate real query and may acquire newer guard frames.
                // Keep the actual endpoint after that query on normal stops as well.
                AdvanceObservationPort.Frame afterStatus = current(parent);
                requireAfterControl(parent, current, read, afterStatus);
                require(sameBoundary(current, afterStatus), "native triggered boundary changed after independent terminal Status");
                current = afterStatus;
            }
        } else if (AdvanceProgress.newModal(current.semantic(), starting.identity(), Optional.of(starting.semantic())).isPresent()
                && end.compareTo(plan.targetDateRaw()) < 0) progress = ProgressStatus.MODAL_INTERRUPTED;
        // Typed event policy is the next ordinary turn's owner. The current actual pause/event
        // is retained; no lossy-title/default-option selection occurs inside a timeline clock.
        List<String> ids = children.completed().subList(childStart, children.completed().size()).stream().map(receipt -> receipt.command().actionId()).toList();
        AdvanceObservationPort.Frame actualEnding = current;
        plan.dailyWatch().ifPresent(watch -> require(watch.sameOwner(actualEnding)
                && integer(actualEnding.semantic().get("speed"), "speed").intValueExact() == 2, "daily watch actual post-Status ending owner/speed changed"));
        if (plan.dailyWatch().isPresent()) watchedBoundary(plan, actualEnding);
        return new Outcome(current, new Diagnostics(plan.startingDateRaw(), end, end.subtract(plan.startingDateRaw()).divide(AdvancePlan.DAY).intValueExact(),
                plan.horizonDays(), plan.speed(), plan.policy(), progress, armed, stopped, canceled, ids, elapsed(begun), nativeStopRead));
    }
    public ActionReceipt submit(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame frame, String step, Instant deadline) {
        require(children.completed().stream().allMatch(ActionReceipt::settled), "UNKNOWN child cannot be followed by another native mutation");
        require(!step.equals("resume-map") || children.completed().stream().noneMatch(value -> value.command().operation().value().equals("resume-map")),
                "a submitted resume cannot be retried, even after a settled rejection");
        ActionReceipt result = children.submit(AdvancePrimitives.child(parent, frame, children.nextActionId(), step, deadline));
        if (!result.settled()) throw new ChildUnresolved(result);
        return result;
    }
    private AdvanceObservationPort.Frame resume(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame snapshot,
            AdvanceObservationPort.Frame starting, AdvancePlan plan) {
        if (!AdvancePolicy.truth(snapshot.semantic(), "paused")) {
            require(plan.dailyWatch().isEmpty(), "daily watch was already running before its original single resume; no replay or control takeover"); return snapshot;
        }
        Instant deadline = bounded(parent, commandTimeout); AdvanceObservationPort.Frame fresh = current(parent);
        AdvanceWait.binding(parent, starting, fresh);
        if (plan.dailyWatch().isPresent()) require(AdvancePolicy.truth(fresh.semantic(), "paused"), "daily watch fresh pre-resume map is already running; no duplicate resume");
        // This last actual read may acquire a new event after the arm read. Do not
        // discard that boundary or submit a resume merely because the older read was clear.
        if (!resumeRequired(starting, fresh, plan)) return fresh;
        require(integer(fresh.semantic().get("speed"), "speed").intValueExact() == plan.speed(),
                "native resume fresh speed differs from original immutable plan");
        plan.dailyWatch().ifPresent(watch -> require(watch.readyToArm(fresh), "daily watch complete roster/owner/speed changed before single resume"));
        if (!AdvancePolicy.truth(fresh.semantic(), "paused")) return fresh;
        require(TimelineOwner.resumeOwner(owner(snapshot), owner(fresh)).sameFacts(), "native resume owner changed before submission");
        ActionReceipt resume = submit(parent, children, fresh, "resume-map", deadline);
        require(resume.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED, "native resume was definitively rejected; never retry resume");
        AdvanceObservationPort.Frame result = current(parent);
        if (plan.dailyWatch().isPresent()) {
            Instant watchDeadline = bounded(parent, advanceTimeout);
            result = waits.until(parent, result, frame -> watchedStop(plan, frame, fresh.identity().frame().revision()), watchDeadline);
            require(watchedStop(plan, result, fresh.identity().frame().revision()), "daily watch observed no newer paused frame or lawful early boundary; never replay");
            return result;
        }
        result = waits.until(parent, result, frame -> !AdvancePolicy.truth(frame.semantic(), "paused")
                || AdvanceProgress.newModal(frame.semantic(), snapshot.identity(), Optional.of(snapshot.semantic())).isPresent()
                || plan.clockMode() != AdvancePlan.ClockMode.POLLED && frame.identity().frame().identity().dateRaw().compareTo(plan.startingDateRaw()) > 0, deadline);
        require(!AdvancePolicy.truth(result.semantic(), "paused") || AdvanceProgress.newModal(result.semantic(), snapshot.identity(), Optional.of(snapshot.semantic())).isPresent()
                || plan.clockMode() != AdvancePlan.ClockMode.POLLED && result.identity().frame().identity().dateRaw().compareTo(plan.startingDateRaw()) > 0,
                "native resume ACK has no running/native-stop readback; replay forbidden");
        return result;
    }
    public static boolean resumeRequired(AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame current, AdvancePlan plan) {
        if (plan.dailyWatch().isPresent() && watchedBoundary(plan, current)) return false;
        return AdvancePolicy.truth(current.semantic(), "paused") && AdvanceProgress.boundary(current, starting, plan).isEmpty();
    }
    private static boolean watchedBoundary(AdvancePlan plan, AdvanceObservationPort.Frame frame) {
        var boundary = plan.dailyWatch().orElseThrow().boundary(frame);
        require(boundary.isEmpty() || switch (boundary.orElseThrow()) {
            case ACTIVE_EVENT, PENDING_INTERACTION, EXCLUSIVE_MODAL_OR_UNKNOWN -> true;
            default -> false;
        }, "daily watch frame crossed owner/connection/unknown/map boundary; no further mutation");
        return boundary.isPresent();
    }
    private static boolean watchedStop(AdvancePlan plan, AdvanceObservationPort.Frame frame, BigInteger originalResumeRevision) {
        boolean boundary = watchedBoundary(plan, frame);
        return boundary && frame.identity().frame().identity().dateRaw().compareTo(plan.targetDateRaw()) < 0
                || AdvancePolicy.truth(frame.semantic(), "paused") && frame.identity().frame().revision().compareTo(originalResumeRevision) > 0;
    }
    /** The original bounded idempotent pause retries are allowed only after an observed definitive rejection. */
    public AdvanceObservationPort.Frame pause(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame snapshot) {
        // Life cleanup must recover the exact frozen watch from its original parent.
        // Route/battle callers have their own typed plans and must not be decoded as Life.
        Optional<WarDailyWatch.Context> watch = LifeAdvanceComposite.accepts(parent.operation().value())
                ? AdvancePlan.decode(parent).dailyWatch() : Optional.empty();
        return pause(parent, children, snapshot, watch);
    }
    private AdvanceObservationPort.Frame pause(ActionCommand parent, CompositeActionPort.Children children, AdvanceObservationPort.Frame snapshot,
            Optional<WarDailyWatch.Context> watch) {
        require(children.completed().stream().allMatch(ActionReceipt::settled),
                "unresolved original child forbids cleanup pause reads or mutation");
        requirePauseFrame(parent, watch, snapshot);
        if (AdvancePolicy.truth(snapshot.semantic(), "paused")) return snapshot;
        Instant deadline = bounded(parent, commandTimeout); AdvanceObservationPort.Frame current = current(parent);
        requirePauseFrame(parent, watch, current);
        if (AdvancePolicy.truth(current.semantic(), "paused")) return current;
        for (int attempt = 0; attempt < 3; attempt++) {
            requirePauseFrame(parent, watch, current);
            ActionReceipt receipt = submit(parent, children, current, "pause-map", deadline);
            boolean rejectedMap = receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected rejected
                    && rejected.reason().equals("CK3 map state is unavailable");
            boolean confirmedPause = receipt.state() instanceof ActionState.Settled actual && actual.settlement() instanceof ActionState.PauseConfirmed;
            require(confirmedPause || rejectedMap, "native pause rejected or lacks its typed independent paused Push");
            AdvanceObservationPort.Frame previous = current; current = current(parent);
            requirePauseFrame(parent, watch, current);
            if (AdvancePolicy.truth(current.semantic(), "paused")) return current;
            // An accepted pause with no effect remains UNKNOWN in the sole child reducer and never
            // reaches this retry. Only the original explicit map-unavailable terminal rejection permits this bounded recovery.
            require(rejectedMap && clock.instant().isBefore(deadline), "pause ACK without actual pause cannot authorize a replay");
            current = waits.until(parent, current, frame -> AdvancePolicy.truth(frame.semantic(), "paused")
                    || frame.identity().frame().identity().nativeRevision().compareTo(previous.identity().frame().identity().nativeRevision()) > 0,
                    deadline.isBefore(clock.instant().plusSeconds(1)) ? deadline : clock.instant().plusSeconds(1));
            requirePauseFrame(parent, watch, current);
            if (AdvancePolicy.truth(current.semantic(), "paused")) return current;
            if (TimelineOwner.pauseOwner(owner(snapshot), owner(current)).sameFacts()) continue;
            AdvanceObservationPort.Frame settled = observations.next(parent, current.identity(), deadline);
            require(TimelineOwner.popupOwner(owner(snapshot), owner(current), owner(settled)).sameFacts(), "pause retry owner or popup changed");
            requirePauseFrame(parent, watch, settled);
            current = settled;
        }
        throw new IllegalStateException("bounded native pause attempts did not observe paused state");
    }
    /** One control-frame rule for live cleanup and archive replay of original Watch pauses. */
    static void requirePauseFrame(ActionCommand parent, Optional<WarDailyWatch.Context> watch, AdvanceObservationPort.Frame frame) {
        require(frame.source().equals(parent.source()) && frame.sessionId().equals(parent.sessionId())
                && frame.identity().game().equals(parent.before().game())
                && frame.identity().machineId().equals(parent.before().machineId()),
                "pause control frame left the original source/session/Game/machine");
        if (watch.isEmpty()) return;
        var context = watch.orElseThrow();
        require(context.starting().equals(parent.before()), "pause watch differs from the frozen original parent entry");
        var boundary = context.boundary(frame);
        require(context.sameOwner(frame) && integer(frame.semantic().get("speed"), "speed").intValueExact() == 2
                && (boundary.isEmpty() || switch (boundary.orElseThrow()) {
                    case ACTIVE_EVENT, PENDING_INTERACTION, EXCLUSIVE_MODAL_OR_UNKNOWN -> true;
                    default -> false;
                }), "daily watch fresh control frame changed owner/connection/speed/map; no further mutation");
    }
    private AdvanceObservationPort.Frame current(ActionCommand parent) {
        AdvanceObservationPort.Frame frame = observations.current(parent, parent.deadline());
        require(frame.source().equals(parent.source()) && frame.sessionId().equals(parent.sessionId()) && frame.identity().game().equals(parent.before().game()), "fresh observation left original held connection"); return frame;
    }
    private Instant bounded(ActionCommand parent, Duration duration) { Instant candidate = clock.instant().plus(duration); return candidate.isBefore(parent.deadline()) ? candidate : parent.deadline(); }
    private long elapsed(long begun) { long result = nanos.getAsLong() - begun; require(result >= 0, "monotonic full clock wall time regressed"); return result; }
    private static TimelineOwner.Frame owner(AdvanceObservationPort.Frame frame) { return TimelineOwnerCodec.frame(toNode(frame.semantic())); }
    private static boolean sameBoundary(AdvanceObservationPort.Frame first, AdvanceObservationPort.Frame second) {
        for (String key : List.of("active_event", "pending_character_interaction", "top_exclusive_modal_choice_hint", "one_life_terminal_reason"))
            if (!Objects.equals(first.semantic().get(key), second.semantic().get(key))) return false;
        return true;
    }
    private static boolean sameSlot(Status arm, Status current) {
        return current.generation().equals(arm.generation()) && current.startingDateRaw() == arm.startingDateRaw()
                && current.targetDateRaw() == arm.targetDateRaw() && current.speed() == arm.speed() && current.mode() == arm.mode()
                && current.armyCount() == arm.armyCount() && current.combatCount() == arm.combatCount();
    }
    /** Cleanup may inspect only the original slot; matching a generation alone cannot authorize cancellation. */
    public static void requireSameSlot(Status arm, Status current) {
        require(sameSlot(Objects.requireNonNull(arm), Objects.requireNonNull(current)),
                "native cleanup Status differs from the original arm slot");
    }
    /** A cancel ACK is insufficient. Its independent Status must retain the exact original slot. */
    public static void validateCancellation(Status arm, Status stop, AdvancePlan plan, BigInteger endingDateRaw) {
        long delta = endingDateRaw.subtract(plan.startingDateRaw()).longValueExact();
        require(delta >= 0 && delta % 24 == 0 && endingDateRaw.compareTo(plan.targetDateRaw()) < 0
                && sameSlot(arm, stop) && stop.state() == State.IDLE && !stop.abnormal()
                && stop.completedDailyTicks() <= delta / 24
                && stop.lastObservedDateRaw() == (long) arm.startingDateRaw() + stop.completedDailyTicks() * 24
                && stop.triggerDateRaw() == 0 && stop.intermediatePauseCount() == 0 && stop.triggerFlags() == 0
                && stop.triggerReasons().isEmpty() && stop.signedDateDeltaFromTargetRaw() == 0 && stop.overshootDays() == -1
                && !stop.pauseWrapperCalled() && !stop.pauseObserved() && !stop.terminalObserved(),
                "independent canceled sentinel Status does not prove the same slot/date/generation");
    }
    /** The semantic read is separate from the Status packet; no synthetic native revision is needed. */
    public static void requireAfterControl(ActionCommand parent, AdvanceObservationPort.Frame previous,
            ClockStatusRead.Observation terminal, AdvanceObservationPort.Frame ending) {
        AdvanceWait.binding(parent, previous, ending);
        require(AdvancePolicy.truth(ending.semantic(), "paused") && AdvancePolicy.truth(ending.semantic(), "map_ready")
                && ending.identity().frame().identity().dateRaw().equals(previous.identity().frame().identity().dateRaw())
                && ending.identity().frame().identity().nativeRevision().compareTo(previous.identity().frame().identity().nativeRevision()) >= 0
                && ending.identity().frame().revision().compareTo(previous.identity().frame().revision()) >= 0
                && ending.identity().frame().revision().compareTo(terminal.receipt().after().binding().observed().frame().revision()) >= 0
                && ending.identity().frame().identity().nativeRevision().compareTo(terminal.receipt().after().binding().observed().frame().identity().nativeRevision()) >= 0
                && !ending.provenance().equals(previous.provenance()) && ending.provenance().independentOf(terminal.receipt().requestId())
                && !ending.observedAt().isBefore(terminal.receipt().after().binding().observedAt())
                && !ending.originalEvidence().equals(terminal.originalEvidence()),
                "control terminal requires a fresh independent stable paused semantic read after Status");
    }
    /** Shared zero-day arm-to-cancel proof. A submitted resume with no new native revision remains UNKNOWN. */
    public static CompositeControlObservation compositeControlTerminal(ActionCommand parent, ClockStatusRead.Observation terminal,
            List<ActionReceipt> actions, ActionState.EffectObservation semantic) {
        require(terminal.status().state() == State.IDLE && actions.stream().allMatch(ActionReceipt::settled)
                && actions.stream().noneMatch(value -> value.command().operation().value().equals("resume-map")),
                "same-revision interruption must have only settled children and no submitted resume");
        String cancelStep = ClockStatusRead.CANCEL_PREFIX + terminal.status().generation().decimal();
        List<PlanningReadReceipt> supporting = new ArrayList<>();
        for (ActionReceipt action : actions) if (action.command().operation().value().equals(cancelStep)) {
            require(action.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied,
                    "generation cancellation needs its real independently observed child settlement");
            ActionState.ControlApplied control = (ActionState.ControlApplied) ((ActionState.Settled) action.state()).settlement();
            require(!control.read().requestId().equals(terminal.receipt().requestId())
                    && ClockStatusRead.decode(control.read().original()).equals(terminal.status()),
                    "parent terminal must be a separate read of the same confirmed canceled slot");
            supporting.add(control.read());
        }
        require(supporting.size() == 1, "exactly one original generation-bound cancel child required");
        return new CompositeControlObservation(terminal.receipt(), supporting, semantic);
    }
    public static void validateArm(Status arm, AdvancePlan plan) {
        require(arm.state() == State.ARMED && SentinelObservation.nativeGeneration(arm).signum() > 0
                && arm.startingDateRaw() == plan.startingDateRaw().intValueExact() && arm.targetDateRaw() == plan.targetDateRaw().intValueExact()
                && arm.lastObservedDateRaw() == plan.startingDateRaw().intValueExact() && arm.triggerDateRaw() == 0
                && arm.speed() == plan.speed() && arm.mode() == Mode.TERMINAL_OR_SENTINEL && arm.armyCount() == plan.watchArmyIds().size() && arm.combatCount() == 0
                && arm.completedDailyTicks() == 0 && arm.intermediatePauseCount() == 0 && arm.triggerFlags() == 0 && arm.triggerReasons().isEmpty()
                && arm.signedDateDeltaFromTargetRaw() == 0 && arm.overshootDays() == -1 && !arm.pauseWrapperCalled() && !arm.pauseObserved()
                && !arm.terminalObserved() && !arm.abnormal(), "native sentinel arm status does not prove the original requested paused clock");
    }
    public static void validateStop(Status arm, Status stop, AdvancePlan plan, BigInteger endingDateRaw) {
        long days = endingDateRaw.subtract(plan.startingDateRaw()).divide(AdvancePlan.DAY).longValueExact(); int end = endingDateRaw.intValueExact();
        require(sameSlot(arm, stop) && stop.state() == State.TRIGGERED && !stop.abnormal() && stop.lastObservedDateRaw() == end
                && stop.triggerDateRaw() == end && stop.combatCount() == 0 && !stop.triggerReasons().isEmpty() && stop.triggerFlags() != 0 && stop.pauseObserved()
                && stop.signedDateDeltaFromTargetRaw() == end - plan.targetDateRaw().intValueExact() && stop.overshootDays() == 0
                && days > 0 && stop.completedDailyTicks() == days, "native sentinel generation/date/tick/paused stop postcondition differs");
        require(stop.triggerReasons().contains("date_deadline") == endingDateRaw.equals(plan.targetDateRaw()), "native date deadline reason differs from actual end date");
        boolean nativePause = stop.triggerReasons().contains("native_pause");
        require(stop.intermediatePauseCount() == (nativePause ? 1 : 0) && stop.pauseWrapperCalled() != nativePause, "native stop pause ownership differs");
    }
}
