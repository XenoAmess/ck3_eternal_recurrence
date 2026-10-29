package org.xar.ck3.control.wave2.military.warresults;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Pure ordinary-window priority. Selecting a close never establishes a closed window. */
public final class WarResultsPolicy {
    public static final String QUERY_STEP = "query-war-results-window-v1";
    public static final String CLOSE_STEP = "close-war-results-window-v1";
    public static final String QUERY_CAPABILITY = "game.command.query-war-results-window-v1";
    public static final String CLOSE_CAPABILITY = "game.command.close-war-results-window-v1";
    public static final String SOURCE_SCHEMA = "war-results-window-source-v1";
    public static final String ATTEMPT_SCHEMA = "war-results-window-query-attempt-v1";

    private WarResultsPolicy() { }

    /** The two existing independent UI contracts share ordering, never native authority. */
    public enum WindowKind {
        RESULTS("war-results-window", "ordinary-war-results-window-v1", "war_results_window", "war_results_window_v1", true),
        DECLARED_OVERVIEW("war-declared-overview", "ordinary-war-declared-overview-v1", "war_declared_overview", "war_declared_overview_v1", false);
        private final String command;
        private final String policy;
        private final String phase;
        private final String publicPrefix;
        private final boolean checkDueApplies;
        WindowKind(String command, String policy, String phase, String publicPrefix, boolean checkDueApplies) {
            this.command = command; this.policy = policy; this.phase = phase;
            this.publicPrefix = publicPrefix; this.checkDueApplies = checkDueApplies;
        }
        public String queryStep() { return "query-" + command + "-v1"; }
        public String closeStep() { return "close-" + command + "-v1"; }
        public String queryCapability() { return "game.command." + queryStep(); }
        public String closeCapability() { return "game.command." + closeStep(); }
        public String sourceSchema() { return command + "-source-v1"; }
        public String attemptSchema() { return command + "-query-attempt-v1"; }
        public String inputSchema() { return this == RESULTS ? "xar.ck3.war-results-priority-input/v1" : "xar.ck3.war-declared-overview-priority-input/v1"; }
        public String policy() { return policy; }
        public String phase() { return phase; }
        public String publicPrefix() { return publicPrefix; }
        public boolean checkDueApplies() { return checkDueApplies; }
    }

    public enum FieldPresence { MISSING, NULL, VALUE }

    /** Keeps absent, explicit null, and a present typed observation distinct. */
    public record Field<T>(FieldPresence presence, Optional<T> value) {
        public Field {
            Objects.requireNonNull(presence); Objects.requireNonNull(value);
            if ((presence == FieldPresence.VALUE) != value.isPresent()) {
                throw new IllegalArgumentException("field presence and value disagree");
            }
        }
        public static <T> Field<T> missing() { return new Field<>(FieldPresence.MISSING, Optional.empty()); }
        public static <T> Field<T> nullValue() { return new Field<>(FieldPresence.NULL, Optional.empty()); }
        public static <T> Field<T> of(T value) { return new Field<>(FieldPresence.VALUE, Optional.of(value)); }
        public boolean isValue() { return presence == FieldPresence.VALUE; }
        public boolean is(T expected) { return value.isPresent() && value.orElseThrow().equals(expected); }
        Field<T> bindingExpected() { return presence == FieldPresence.MISSING ? nullValue() : this; }
    }

    public record Binding(Field<String> snapshotId, Field<BigInteger> revision, Field<BigInteger> nativeRevision,
                          Field<BigInteger> dateRaw, Field<BigInteger> actorId, Field<BigInteger> connectionGeneration,
                          Field<String> episodeRunId) {
        public Binding {
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(actorId); Objects.requireNonNull(connectionGeneration);
            Objects.requireNonNull(episodeRunId);
        }
        boolean matches(Binding expected) {
            return matches(snapshotId, expected.snapshotId) && matches(revision, expected.revision)
                    && matches(nativeRevision, expected.nativeRevision) && matches(dateRaw, expected.dateRaw)
                    && matches(actorId, expected.actorId) && matches(connectionGeneration, expected.connectionGeneration)
                    && matches(episodeRunId, expected.episodeRunId);
        }
        private static <T> boolean matches(Field<T> observed, Field<T> expected) {
            return observed.presence() != FieldPresence.MISSING && observed.equals(expected.bindingExpected());
        }
    }

    /** Dispatch fields are retained separately; presence deliberately does not consume them. */
    public record DispatchAck(Field<Boolean> accepted, Field<Boolean> attempted, Field<Boolean> invoked) {
        public DispatchAck { Objects.requireNonNull(accepted); Objects.requireNonNull(attempted); Objects.requireNonNull(invoked); }
    }

    public record Observation(Field<String> validationSchema, Binding binding, Field<Boolean> available,
                              Field<Boolean> postObserved, Field<Boolean> scopeUnchanged, Field<Boolean> postWindowPresent,
                              Field<Boolean> postEffectiveVisible, Field<Boolean> retryDeferred, DispatchAck dispatchAck) {
        public Observation {
            Objects.requireNonNull(validationSchema); Objects.requireNonNull(binding); Objects.requireNonNull(available);
            Objects.requireNonNull(postObserved); Objects.requireNonNull(scopeUnchanged); Objects.requireNonNull(postWindowPresent);
            Objects.requireNonNull(postEffectiveVisible); Objects.requireNonNull(retryDeferred); Objects.requireNonNull(dispatchAck);
        }
    }

    public record Attempt(Field<String> validationSchema, Binding binding, Field<String> status, Field<String> nativeRequestId) {
        public Attempt { Objects.requireNonNull(validationSchema); Objects.requireNonNull(binding); Objects.requireNonNull(status); Objects.requireNonNull(nativeRequestId); }
    }

    public record PendingClose(Field<String> nativeRequestId, Field<String> status) {
        public PendingClose { Objects.requireNonNull(nativeRequestId); Objects.requireNonNull(status); }
    }

    public record Snapshot(Binding binding, Field<Boolean> mapReady, Field<Boolean> paused,
                           Field<Observation> observation, Field<Attempt> queryAttempt, Field<PendingClose> closePending,
                           Field<Boolean> checkDue, Field<BigInteger> nextCheckDateRaw) {
        public Snapshot {
            Objects.requireNonNull(binding); Objects.requireNonNull(mapReady); Objects.requireNonNull(paused);
            Objects.requireNonNull(observation); Objects.requireNonNull(queryAttempt); Objects.requireNonNull(closePending);
            Objects.requireNonNull(checkDue); Objects.requireNonNull(nextCheckDateRaw);
        }
    }

    public record Request(Optional<Snapshot> snapshot, Set<String> actionSteps, Set<String> bridgeCapabilities) {
        public Request {
            Objects.requireNonNull(snapshot); actionSteps = Set.copyOf(actionSteps); bridgeCapabilities = Set.copyOf(bridgeCapabilities);
        }
    }

    public enum WindowPresence { UNKNOWN, ABSENT, HIDDEN, VISIBLE }
    public enum PlanStatus { BLOCKED, READY, PENDING }
    public enum SelectedStep { QUERY, CLOSE, PAUSE_MAP }
    public enum Reason {
        UNKNOWN("war results visibility is unknown"),
        READY_FRAME_REQUIRED("war results requires a paused, ready frame"),
        PAUSE_FIRST("pause the ready map before observing or closing the war results"),
        PAUSE_UNAVAILABLE("war results requires a paused frame and pause-map is unavailable"),
        OBSERVE_PENDING("observe the pending close once without resubmitting it"),
        PENDING_CLOSE("the original war results close is still pending; do not resubmit"),
        DISMISS_VISIBLE("dismiss the observed war results before ordinary actions"),
        CLOSE_UNAVAILABLE("the native war results close capability is unavailable"),
        READ_ALREADY_ATTEMPTED("the current war results read was already attempted; do not repeat it"),
        OBSERVE_ONCE("observe the war results once before ordinary actions");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public String wire(WindowKind kind) {
            if (kind == WindowKind.RESULTS) { return wire; }
            return switch (this) {
                case UNKNOWN -> "war overview visibility is unknown";
                case READY_FRAME_REQUIRED -> "war overview requires a paused, ready frame";
                case PAUSE_FIRST -> "pause the ready map before observing or closing the war overview";
                case PAUSE_UNAVAILABLE -> "war overview requires a paused frame and pause-map is unavailable";
                case OBSERVE_PENDING -> "observe the pending close once without resubmitting it";
                case PENDING_CLOSE -> "the original war overview close is still pending; do not resubmit";
                case DISMISS_VISIBLE -> "dismiss the observed war overview before ordinary actions";
                case CLOSE_UNAVAILABLE -> "the native war overview close capability is unavailable";
                case READ_ALREADY_ATTEMPTED -> "the current war overview read was already attempted; do not repeat it";
                case OBSERVE_ONCE -> "observe the war overview once before ordinary actions";
            };
        }
    }

    public record WindowSummary(WindowPresence presence, boolean closePending, Field<String> queryAttemptStatus,
                                Field<Boolean> checkDue, Field<BigInteger> nextCheckDateRaw) {
        public WindowSummary {
            Objects.requireNonNull(presence); Objects.requireNonNull(queryAttemptStatus);
            Objects.requireNonNull(checkDue); Objects.requireNonNull(nextCheckDateRaw);
        }
    }

    public record Plan(PlanStatus status, Optional<SelectedStep> selectedStep, Reason reason, WindowSummary summary) {
        public Plan {
            Objects.requireNonNull(status); Objects.requireNonNull(selectedStep); Objects.requireNonNull(reason); Objects.requireNonNull(summary);
            if ((status == PlanStatus.READY) != selectedStep.isPresent()) { throw new IllegalArgumentException("only ready plans select a step"); }
        }
    }

    /** Deliberately excludes public revision/snapshot ID, matching the original cadence key. */
    public record QueryFrame(Field<BigInteger> nativeRevision, Field<BigInteger> dateRaw, Field<BigInteger> actorId,
                             Field<BigInteger> connectionGeneration, Field<String> episodeRunId, Field<String> originalCloseRequestId) {
        public QueryFrame {
            Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(actorId);
            Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(episodeRunId); Objects.requireNonNull(originalCloseRequestId);
        }
    }

    public static QueryFrame queryFrame(Snapshot snapshot) {
        Objects.requireNonNull(snapshot); Binding binding = snapshot.binding();
        Field<String> request = snapshot.closePending().value().map(PendingClose::nativeRequestId).orElse(Field.nullValue());
        return new QueryFrame(binding.nativeRevision().bindingExpected(), binding.dateRaw().bindingExpected(),
                binding.actorId().bindingExpected(), binding.connectionGeneration().bindingExpected(),
                binding.episodeRunId().bindingExpected(), request.bindingExpected());
    }

    /** No SDK marker, ACK, status string or attempted dispatch can substitute for these post-read flags. */
    public static WindowPresence presence(Observation observation) {
        Objects.requireNonNull(observation);
        if (!observation.available().is(true) || !observation.postObserved().is(true) || !observation.scopeUnchanged().is(true)) {
            return WindowPresence.UNKNOWN;
        }
        if (observation.postWindowPresent().is(false) && observation.postEffectiveVisible().is(false)) { return WindowPresence.ABSENT; }
        if (observation.postWindowPresent().is(true) && observation.postEffectiveVisible().is(false)) { return WindowPresence.HIDDEN; }
        if (observation.postWindowPresent().is(true) && observation.postEffectiveVisible().is(true)) { return WindowPresence.VISIBLE; }
        return WindowPresence.UNKNOWN;
    }

    public static Optional<Plan> plan(Request request) {
        return plan(request, WindowKind.RESULTS);
    }

    public static Optional<Plan> plan(Request request, WindowKind kind) {
        Objects.requireNonNull(kind);
        Objects.requireNonNull(request); if (request.snapshot().isEmpty()) { return Optional.empty(); }
        Snapshot snapshot = request.snapshot().orElseThrow();
        boolean canQuery = request.bridgeCapabilities().contains(kind.queryCapability());
        boolean canClose = request.bridgeCapabilities().contains(kind.closeCapability());
        boolean pending = snapshot.closePending().isValue();
        if (!canQuery && !canClose && !pending) { return Optional.empty(); }
        Optional<Observation> currentObservation = snapshot.observation().value().filter(value ->
                value.validationSchema().is(kind.sourceSchema()) && value.binding().matches(snapshot.binding()));
        Optional<Attempt> currentAttempt = snapshot.queryAttempt().value().filter(value ->
                value.validationSchema().is(kind.attemptSchema()) && value.binding().matches(snapshot.binding()));
        WindowPresence presence = currentObservation.map(WarResultsPolicy::presence).orElse(WindowPresence.UNKNOWN);
        if (presence == WindowPresence.ABSENT || presence == WindowPresence.HIDDEN) { return Optional.empty(); }
        if (presence == WindowPresence.VISIBLE && !pending && currentObservation.orElseThrow().retryDeferred().is(true)) { return Optional.empty(); }
        if (presence == WindowPresence.UNKNOWN && !pending && currentAttempt.map(value -> value.status().is("failed")).orElse(false)) { return Optional.empty(); }
        if (kind.checkDueApplies() && presence == WindowPresence.UNKNOWN && !pending && snapshot.checkDue().is(false)) { return Optional.empty(); }
        SelectedStep selected = null; Reason reason = Reason.UNKNOWN; PlanStatus status = PlanStatus.BLOCKED;
        if (!snapshot.mapReady().is(true)) { reason = Reason.READY_FRAME_REQUIRED; }
        else if (!snapshot.paused().is(true)) {
            if (snapshot.paused().is(false) && request.actionSteps().contains("pause-map")) {
                selected = SelectedStep.PAUSE_MAP; reason = Reason.PAUSE_FIRST; status = PlanStatus.READY;
            } else { reason = Reason.PAUSE_UNAVAILABLE; }
        } else if (presence == WindowPresence.VISIBLE && pending) {
            if (currentAttempt.isEmpty() && canQuery && request.actionSteps().contains(kind.queryStep())) {
                selected = SelectedStep.QUERY; reason = Reason.OBSERVE_PENDING; status = PlanStatus.READY;
            } else { reason = Reason.PENDING_CLOSE; status = PlanStatus.PENDING; }
        } else if (presence == WindowPresence.VISIBLE && canClose && request.actionSteps().contains(kind.closeStep())) {
            selected = SelectedStep.CLOSE; reason = Reason.DISMISS_VISIBLE; status = PlanStatus.READY;
        } else if (presence == WindowPresence.VISIBLE) { reason = Reason.CLOSE_UNAVAILABLE; }
        else if (currentAttempt.isPresent()) { reason = Reason.READ_ALREADY_ATTEMPTED; status = PlanStatus.PENDING; }
        else if (canQuery && request.actionSteps().contains(kind.queryStep())) {
            selected = SelectedStep.QUERY; reason = Reason.OBSERVE_ONCE; status = PlanStatus.READY;
        }
        Field<String> attemptStatus = snapshot.queryAttempt().value().map(Attempt::status).orElse(Field.nullValue());
        return Optional.of(new Plan(status, Optional.ofNullable(selected), reason,
                new WindowSummary(presence, pending, attemptStatus, snapshot.checkDue(), snapshot.nextCheckDateRaw())));
    }

    public static String stepText(SelectedStep selected) {
        return stepText(selected, WindowKind.RESULTS);
    }

    public static String stepText(SelectedStep selected, WindowKind kind) {
        Objects.requireNonNull(kind);
        return switch (selected) { case QUERY -> kind.queryStep(); case CLOSE -> kind.closeStep(); case PAUSE_MAP -> "pause-map"; };
    }

    public static List<String> pendingActions(Plan plan) { return plan.selectedStep().map(value -> List.of(stepText(value))).orElseGet(List::of); }
    public static List<String> pendingActions(Plan plan, WindowKind kind) { return plan.selectedStep().map(value -> List.of(stepText(value, kind))).orElseGet(List::of); }
}
