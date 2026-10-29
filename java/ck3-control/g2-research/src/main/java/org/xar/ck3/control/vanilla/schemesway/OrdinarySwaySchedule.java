package org.xar.ck3.control.vanilla.schemesway;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.planning.swayreuse.ReusedSwayOpportunity.ObservationGap;

/** Pure ordinary opportunity scheduling. It grants neither native rank nor submit permission. */
public final class OrdinarySwaySchedule {
    public static final BigInteger RAW_PER_DAY = BigInteger.valueOf(24);
    public static final BigInteger MONTH_RAW = BigInteger.valueOf(720);
    private OrdinarySwaySchedule() { }

    public enum Step { LIFE_ADVANCE, OTHER }
    public enum Context { CLEAR, MANDATORY, UNAVAILABLE }
    public enum Job { QUERY_SELECTED_TARGET, RECONCILE_PENDING, OBSERVE_APPLIED, COMPLETE_NO_RELATION }
    public enum Outcome { NO_OPERATION, APPLIED, PENDING, OBSERVED, UNAVAILABLE }
    public enum Reason {
        PRESERVE_SELECTED_STEP, FRAME_UNAVAILABLE, PRESERVE_MANDATORY_CONTEXT,
        PRESERVE_ORIGINAL_PENDING, UNRESOLVED_OTHER_ACTOR, PENDING_READ_NOT_DUE,
        EXISTING_PENDING_READ_ONLY, MONTHLY_OBSERVATION_NOT_DUE,
        NEW_IDENTITY_OR_MONTHLY_OBSERVATION, ORIGINAL_STORAGE_REUSED_TERMINAL_UNKNOWN,
        ORIGINAL_TERMINAL_ALREADY_OBSERVED, NO_APPLIED_INSTANCE_TO_OBSERVE,
        SAME_FRAME_ROOT_UNAVAILABLE, FRONTIER_UNAVAILABLE, OPPORTUNITY_CHECK_NOT_DUE,
        OBSERVED_EMPTY_FRONTIER, ROUND_ROBIN_DIRECT_LANDED_VASSAL
    }

    /** Public and native revisions are intentionally independent. */
    public record Frame(String snapshotId, BigInteger publicRevision, BigInteger nativeRevision,
            BigInteger dateRaw, long actorCharacterId, boolean paused, boolean mapReady,
            boolean alive, Context context) {
        public Frame {
            text(snapshotId); positive(publicRevision); positive(nativeRevision);
            Objects.requireNonNull(dateRaw); character(actorCharacterId); Objects.requireNonNull(context);
        }
    }

    /** Empty optional frontier means unavailable; present empty list is an observed empty frontier. */
    public record Root(boolean available, long actorCharacterId, boolean alive,
            BigInteger nativeRevision, BigInteger dateRaw, Optional<List<Long>> frontier) {
        public Root {
            character(actorCharacterId); positive(nativeRevision); Objects.requireNonNull(dateRaw);
            Objects.requireNonNull(frontier);
            frontier = frontier.map(List::copyOf);
        }
    }

    public record Pending(String actionId, long actorCharacterId, long targetCharacterId) {
        public Pending { text(actionId); character(actorCharacterId); character(targetCharacterId); }
    }

    /** Reuse is the existing canonical Java observation gap, never an inferred terminal. */
    public record Resolved(Identity identity, boolean applied, boolean postconditionVerified,
            boolean terminalObserved, Optional<ObservationGap> reuseGap) {
        public Resolved {
            Objects.requireNonNull(identity); Objects.requireNonNull(reuseGap);
            if (reuseGap.isPresent()) {
                ObservationGap gap = reuseGap.orElseThrow();
                require(gap.actionId().equals(identity.actionId())
                        && gap.actorCharacterId() == identity.actorCharacterId()
                        && gap.targetCharacterId() == identity.targetCharacterId()
                        && gap.schemeInstanceId() == identity.schemeInstanceId()
                        && gap.schemeInstanceGeneration() == identity.schemeInstanceGeneration(), "foreign storage reuse identity");
                require(!terminalObserved, "reuse cannot replace an observed terminal");
            }
        }
    }

    public record Ledger(Optional<Pending> pending, Optional<Resolved> resolved) {
        public Ledger { Objects.requireNonNull(pending); Objects.requireNonNull(resolved); }
        public static Ledger empty() { return new Ledger(Optional.empty(), Optional.empty()); }
    }

    /** Immutable scheduler state, independent of original material and terminal ledgers. */
    public record State(long actorCharacterId, Optional<Long> lastTargetCharacterId,
            int noOperationCount, Optional<BigInteger> lastCheckDateRaw,
            Optional<BigInteger> nextCheckDateRaw, Optional<List<Long>> frontierMembership,
            Optional<String> lastObservationAttemptActionId, Optional<String> lastTerminalActionId,
            Optional<Job> lastJobKind) {
        public State {
            character(actorCharacterId); Objects.requireNonNull(lastTargetCharacterId);
            lastTargetCharacterId.ifPresent(OrdinarySwaySchedule::character);
            require(noOperationCount >= 0 && noOperationCount <= 2, "invalid no-operation state");
            Objects.requireNonNull(lastCheckDateRaw); Objects.requireNonNull(nextCheckDateRaw);
            Objects.requireNonNull(frontierMembership); frontierMembership = frontierMembership.map(List::copyOf);
            Objects.requireNonNull(lastObservationAttemptActionId); lastObservationAttemptActionId.ifPresent(OrdinarySwaySchedule::text);
            Objects.requireNonNull(lastTerminalActionId); lastTerminalActionId.ifPresent(OrdinarySwaySchedule::text);
            Objects.requireNonNull(lastJobKind);
        }
        public static State initial(long actor) {
            return new State(actor, Optional.empty(), 0, Optional.empty(), Optional.empty(), Optional.empty(),
                    Optional.empty(), Optional.empty(), Optional.empty());
        }
    }

    /** Source identity participates in equality and therefore in the exact cache key. */
    public record Request(G2Source source, Optional<Frame> frame, Step selectedStep,
            Optional<Root> root, Ledger ledger, Optional<State> state, boolean activeObservationOnly) {
        public Request {
            Objects.requireNonNull(source); Objects.requireNonNull(frame); Objects.requireNonNull(selectedStep);
            Objects.requireNonNull(root); Objects.requireNonNull(ledger); Objects.requireNonNull(state);
            require(source.exactBuild().equals("1.20.0.4"), "scheduler source must identify exact supported build");
        }
    }

    public record Decision(Optional<Job> job, Reason reason, Optional<Long> targetCharacterId,
            Optional<String> actionId, Optional<State> state) {
        public Decision {
            Objects.requireNonNull(job); Objects.requireNonNull(reason); Objects.requireNonNull(targetCharacterId);
            Objects.requireNonNull(actionId); Objects.requireNonNull(state);
        }
        public boolean submitAllowed() { return false; }
        public boolean nativeAiRankClaimed() { return false; }
        public boolean terminalOrUsefulGainClaimed() { return false; }
    }

    public static Decision plan(Request request) {
        Objects.requireNonNull(request);
        if (request.selectedStep() != Step.LIFE_ADVANCE && !request.activeObservationOnly()) {
            return none(Reason.PRESERVE_SELECTED_STEP, request.state());
        }
        if (request.frame().isEmpty()) { return none(Reason.FRAME_UNAVAILABLE, request.state()); }
        Frame frame = request.frame().orElseThrow();
        if (!frame.paused() || !frame.mapReady() || !frame.alive()) {
            return none(Reason.FRAME_UNAVAILABLE, request.state());
        }
        if (frame.context() != Context.CLEAR) { return none(Reason.PRESERVE_MANDATORY_CONTEXT, request.state()); }
        State state = request.state().filter(value -> value.actorCharacterId() == frame.actorCharacterId())
                .orElseGet(() -> State.initial(frame.actorCharacterId()));
        if (request.ledger().pending().isPresent()) {
            Pending pending = request.ledger().pending().orElseThrow();
            if (request.activeObservationOnly()) { return none(Reason.PRESERVE_ORIGINAL_PENDING, state); }
            if (pending.actorCharacterId() != frame.actorCharacterId()) { return none(Reason.UNRESOLVED_OTHER_ACTOR, state); }
            if (state.lastJobKind().equals(Optional.of(Job.RECONCILE_PENDING)) && !due(state, frame.dateRaw())) {
                return none(Reason.PENDING_READ_NOT_DUE, state);
            }
            return job(Job.RECONCILE_PENDING, Reason.EXISTING_PENDING_READ_ONLY,
                    pending.targetCharacterId(), Optional.of(pending.actionId()), state);
        }
        Optional<Resolved> applied = request.ledger().resolved().filter(value -> value.applied()
                && value.postconditionVerified() && value.identity().actorCharacterId() == frame.actorCharacterId());
        if (applied.isPresent()) {
            Resolved resolved = applied.orElseThrow();
            Identity identity = resolved.identity();
            boolean reused = resolved.reuseGap().filter(gap -> gap.sourceDateRaw().compareTo(frame.dateRaw()) <= 0).isPresent();
            if (!resolved.terminalObserved() && !reused) {
                boolean newAction = !state.lastObservationAttemptActionId().equals(Optional.of(identity.actionId()));
                if (!newAction && !due(state, frame.dateRaw())) { return none(Reason.MONTHLY_OBSERVATION_NOT_DUE, state); }
                return job(Job.OBSERVE_APPLIED, Reason.NEW_IDENTITY_OR_MONTHLY_OBSERVATION,
                        identity.targetCharacterId(), Optional.of(identity.actionId()), state);
            }
            if (request.activeObservationOnly()) {
                return none(reused ? Reason.ORIGINAL_STORAGE_REUSED_TERMINAL_UNKNOWN
                        : Reason.ORIGINAL_TERMINAL_ALREADY_OBSERVED, state);
            }
            if (resolved.terminalObserved() && !state.lastTerminalActionId().equals(Optional.of(identity.actionId()))) {
                state = copy(state, state.lastTargetCharacterId(), 0, state.lastCheckDateRaw(), Optional.empty(),
                        state.frontierMembership(), state.lastObservationAttemptActionId(), Optional.of(identity.actionId()), state.lastJobKind());
            }
        }
        if (request.activeObservationOnly()) { return none(Reason.NO_APPLIED_INSTANCE_TO_OBSERVE, state); }
        if (request.root().isEmpty()) { return none(Reason.SAME_FRAME_ROOT_UNAVAILABLE, state); }
        Root root = request.root().orElseThrow();
        if (!root.available() || root.actorCharacterId() != frame.actorCharacterId() || !root.alive()
                || !root.nativeRevision().equals(frame.nativeRevision()) || !root.dateRaw().equals(frame.dateRaw())) {
            return none(Reason.SAME_FRAME_ROOT_UNAVAILABLE, state);
        }
        if (root.frontier().isEmpty()) { return none(Reason.FRONTIER_UNAVAILABLE, state); }
        List<Long> targets = root.frontier().orElseThrow();
        if (targets.stream().anyMatch(value -> value == null || value <= 0 || value > 0xffff_ffffL
                || value == frame.actorCharacterId()) || new HashSet<>(targets).size() != targets.size()) {
            return none(Reason.FRONTIER_UNAVAILABLE, state);
        }
        List<Long> membership = new ArrayList<>(targets); membership.sort(Long::compare);
        if (!state.frontierMembership().equals(Optional.of(membership))) {
            state = copy(state, state.lastTargetCharacterId(), 0, state.lastCheckDateRaw(), Optional.empty(),
                    Optional.of(membership), state.lastObservationAttemptActionId(), state.lastTerminalActionId(), state.lastJobKind());
        }
        if (!due(state, frame.dateRaw())) { return none(Reason.OPPORTUNITY_CHECK_NOT_DUE, state); }
        if (targets.isEmpty()) {
            return new Decision(Optional.of(Job.COMPLETE_NO_RELATION), Reason.OBSERVED_EMPTY_FRONTIER,
                    Optional.empty(), Optional.empty(), Optional.of(state));
        }
        int index = state.lastTargetCharacterId().map(targets::indexOf).orElse(-1) + 1;
        return job(Job.QUERY_SELECTED_TARGET, Reason.ROUND_ROBIN_DIRECT_LANDED_VASSAL,
                targets.get(index % targets.size()), Optional.empty(), state);
    }

    public static State complete(State state, BigInteger dateRaw, Job jobKind, Outcome outcome,
            Optional<Long> targetCharacterId, Optional<String> actionId) {
        Objects.requireNonNull(state); Objects.requireNonNull(dateRaw); Objects.requireNonNull(jobKind);
        Objects.requireNonNull(outcome); Objects.requireNonNull(targetCharacterId); Objects.requireNonNull(actionId);
        if (state.lastCheckDateRaw().isPresent()) {
            int order = dateRaw.compareTo(state.lastCheckDateRaw().orElseThrow());
            if (order < 0 || (order == 0 && jobKind != Job.OBSERVE_APPLIED && jobKind != Job.RECONCILE_PENDING)) { return state; }
        }
        int count = state.noOperationCount(); BigInteger delay = MONTH_RAW;
        if (outcome == Outcome.NO_OPERATION) { count = Math.min(2, count + 1); delay = count == 2 ? MONTH_RAW : RAW_PER_DAY; }
        else if (outcome == Outcome.APPLIED) { count = 0; }
        Optional<Long> target = state.lastTargetCharacterId();
        if ((outcome == Outcome.NO_OPERATION || outcome == Outcome.APPLIED) && targetCharacterId.isPresent()) {
            character(targetCharacterId.orElseThrow()); target = targetCharacterId;
        }
        Optional<String> attempt = state.lastObservationAttemptActionId();
        if (jobKind == Job.OBSERVE_APPLIED && (outcome == Outcome.OBSERVED || outcome == Outcome.UNAVAILABLE)) { attempt = actionId; }
        return copy(state, target, count, Optional.of(dateRaw), Optional.of(dateRaw.add(delay)), state.frontierMembership(),
                attempt, state.lastTerminalActionId(), Optional.of(jobKind));
    }

    private static boolean due(State state, BigInteger date) {
        return state.lastCheckDateRaw().map(previous -> date.compareTo(previous) > 0).orElse(true)
                && state.nextCheckDateRaw().map(next -> date.compareTo(next) >= 0).orElse(true);
    }
    private static State copy(State state, Optional<Long> target, int count, Optional<BigInteger> previous,
            Optional<BigInteger> next, Optional<List<Long>> members, Optional<String> attempt,
            Optional<String> terminal, Optional<Job> job) {
        return new State(state.actorCharacterId(), target, count, previous, next, members, attempt, terminal, job);
    }
    private static Decision none(Reason reason, State state) { return none(reason, Optional.of(state)); }
    private static Decision none(Reason reason, Optional<State> state) {
        return new Decision(Optional.empty(), reason, Optional.empty(), Optional.empty(), state);
    }
    private static Decision job(Job job, Reason reason, long target, Optional<String> action, State state) {
        return new Decision(Optional.of(job), reason, Optional.of(target), action, Optional.of(state));
    }
    private static void character(long value) { require(value > 0 && value <= 0xffff_ffffL, "actual full32 character ID required"); }
    private static void text(String value) { require(value != null && !value.isBlank(), "nonempty text required"); }
    private static void positive(BigInteger value) { require(value != null && value.signum() > 0, "positive integer required"); }
    private static void require(boolean value, String message) { if (!value) { throw new IllegalArgumentException(message); } }
}
