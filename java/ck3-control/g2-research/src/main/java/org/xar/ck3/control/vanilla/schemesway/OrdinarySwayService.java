package org.xar.ck3.control.vanilla.schemesway;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;

/** Ordinary planner consumer. The native/formal port retains custody, admission and once-only sending. */
public final class OrdinarySwayService {
    public static final String STEP = "ordinary-sway-opportunity-v1";
    private final SourceBoundSwayReevaluationCache cache = new SourceBoundSwayReevaluationCache();

    public record Capabilities(boolean formalQuery, boolean formalAction, boolean lifecycleReader) {
        public boolean formal() { return formalQuery && formalAction; }
    }
    public record Wrapper(String snapshotId, BigInteger publicRevision) {
        public Wrapper { text(snapshotId); Objects.requireNonNull(publicRevision); require(publicRevision.signum() > 0, "positive public revision required"); }
    }
    public record Captured(G2Source source, Wrapper wrapper, Step selectedStep,
            Optional<Frame> frame, Optional<Root> root, Capabilities capabilities) {
        public Captured {
            Objects.requireNonNull(source); Objects.requireNonNull(wrapper); Objects.requireNonNull(selectedStep);
            Objects.requireNonNull(frame); Objects.requireNonNull(root); Objects.requireNonNull(capabilities);
        }
    }
    public record Inputs(Ledger ledger, Optional<State> state) {
        public Inputs { Objects.requireNonNull(ledger); Objects.requireNonNull(state); }
    }
    public enum StageReason { STAGED, PRESERVE_SELECTED_STEP, FRAME_ABSENT, CAPTURED_FRAME_CHANGED,
        READERS_DISABLED, INPUTS_ABSENT, INPUTS_UNAVAILABLE, NO_JOB, JOB_READER_DISABLED }
    public record Staged(Frame frame, Decision decision) {
        public Staged {
            Objects.requireNonNull(frame); Objects.requireNonNull(decision);
            require(decision.job().isPresent() && decision.state().isPresent(), "complete staged job required");
            require(decision.state().orElseThrow().actorCharacterId() == frame.actorCharacterId(), "foreign scheduler actor");
            Job kind = decision.job().orElseThrow();
            require(kind == Job.COMPLETE_NO_RELATION || decision.targetCharacterId().isPresent(), "job target required");
            require(kind != Job.RECONCILE_PENDING && kind != Job.OBSERVE_APPLIED || decision.actionId().isPresent(), "original action required");
        }
    }
    public record StageResult(StageReason reason, Optional<Staged> staged, Optional<Decision> decision,
            Optional<String> error) {
        public StageResult {
            Objects.requireNonNull(reason); Objects.requireNonNull(staged); Objects.requireNonNull(decision); Objects.requireNonNull(error);
            require((reason == StageReason.STAGED) == staged.isPresent(), "stage result branch mismatch");
        }
    }
    @FunctionalInterface
    public interface InputPort { Optional<Inputs> loadInputs() throws Unavailable; }

    /** Drift is tested before the port: a family retry must cause zero ledger/state I/O. */
    public StageResult stage(Captured captured, InputPort inputs) {
        Objects.requireNonNull(captured); Objects.requireNonNull(inputs);
        if (captured.selectedStep() != Step.LIFE_ADVANCE) { return preserved(StageReason.PRESERVE_SELECTED_STEP); }
        if (captured.frame().isEmpty()) { return preserved(StageReason.FRAME_ABSENT); }
        Frame frame = captured.frame().orElseThrow();
        if (!captured.wrapper().snapshotId().equals(frame.snapshotId())
                || !captured.wrapper().publicRevision().equals(frame.publicRevision())) {
            return preserved(StageReason.CAPTURED_FRAME_CHANGED);
        }
        if (!captured.capabilities().formal() && !captured.capabilities().lifecycleReader()) {
            return preserved(StageReason.READERS_DISABLED);
        }
        try {
            Optional<Inputs> available = inputs.loadInputs();
            if (available.isEmpty()) { return preserved(StageReason.INPUTS_ABSENT); }
            Inputs current = available.orElseThrow();
            Request request = new Request(captured.source(), captured.frame(), captured.selectedStep(), captured.root(),
                    current.ledger(), current.state(), false);
            Decision decision;
            synchronized (cache) { decision = cache.evaluate(request).decision(); }
            if (decision.job().isEmpty()) { return new StageResult(StageReason.NO_JOB, Optional.empty(), Optional.of(decision), Optional.empty()); }
            boolean enabled = decision.job().orElseThrow() == Job.OBSERVE_APPLIED
                    ? captured.capabilities().lifecycleReader() : captured.capabilities().formal();
            if (!enabled) { return new StageResult(StageReason.JOB_READER_DISABLED, Optional.empty(), Optional.of(decision), Optional.empty()); }
            return new StageResult(StageReason.STAGED, Optional.of(new Staged(frame, decision)), Optional.of(decision), Optional.empty());
        } catch (Unavailable | IllegalArgumentException failure) {
            return new StageResult(StageReason.INPUTS_UNAVAILABLE, Optional.empty(), Optional.empty(), Optional.of(message(failure)));
        }
    }

    public enum FormalStatus { APPLIED, RECEIPT_PENDING, POSTCONDITION_PENDING, SUBMISSION_UNRESOLVED,
        PENDING_RECOVERY, NO_POSITIVE_OPPORTUNITY, ALREADY_APPLIED, OTHER_OBSERVED }
    public enum Followup { FINISH_SELECTED_RELATION, RETURN_TO_OPPORTUNITY_SELECTION, NATIVE_START_UNAVAILABLE, OTHER }
    public sealed interface CheckResult permits FormalResult, LifecycleResult, LocalResult { }
    public record FormalResult(FormalStatus status, boolean postconditionVerified, Optional<String> actionId,
            Optional<Followup> followup, ProjectionJson evidence) implements CheckResult {
        public FormalResult {
            Objects.requireNonNull(status); Objects.requireNonNull(actionId); actionId.ifPresent(OrdinarySwayService::text);
            Objects.requireNonNull(followup); Objects.requireNonNull(evidence);
        }
    }
    public enum LifecycleStatus { OBSERVED, UNAVAILABLE }
    public record LifecycleResult(LifecycleStatus status, ProjectionJson evidence) implements CheckResult {
        public LifecycleResult { Objects.requireNonNull(status); Objects.requireNonNull(evidence); }
    }
    public enum LocalStatus { KNOWN_EMPTY_RELATION_FRONTIER, PENDING_IDENTITY_CHANGED,
        ORIGINAL_PENDING_PRESERVED, UNAVAILABLE, INPUTS_ABSENT }
    public record LocalResult(LocalStatus status, Optional<String> error) implements CheckResult {
        public LocalResult { Objects.requireNonNull(status); Objects.requireNonNull(error); }
    }
    public record Receipt(Job job, Optional<Long> targetCharacterId, Outcome outcome, CheckResult result,
            State schedulerState, Optional<String> stateWriteError) {
        public Receipt {
            Objects.requireNonNull(job); Objects.requireNonNull(targetCharacterId); Objects.requireNonNull(outcome);
            Objects.requireNonNull(result); Objects.requireNonNull(schedulerState); Objects.requireNonNull(stateWriteError);
        }
        public boolean samePidOrRuntimeClaim() { return false; }
    }
    public record OrdinaryContinuation(ProjectionJson outcome, ProjectionJson followingPlan) {
        public OrdinaryContinuation { Objects.requireNonNull(outcome); Objects.requireNonNull(followingPlan); }
    }
    public sealed interface Execution permits Started, Continued { }
    public record Started(FormalResult result, Receipt receipt) implements Execution {
        public Started { Objects.requireNonNull(result); Objects.requireNonNull(receipt); }
    }
    public record Continued(OrdinaryContinuation ordinary, Optional<Receipt> receipt,
            Optional<LocalResult> unavailable) implements Execution {
        public Continued {
            Objects.requireNonNull(ordinary); Objects.requireNonNull(receipt); Objects.requireNonNull(unavailable);
            require(receipt.isPresent() != unavailable.isPresent(), "one optional-work result branch required");
        }
    }

    /** Implemented by the single ordinary host after its before-submit hook, never by a policy or test runner. */
    public interface ExecutionPort extends InputPort {
        FormalResult queryAndConsume(Frame expectedFrame, long targetCharacterId) throws Unavailable;
        LifecycleResult observeLifecycle(Frame expectedFrame) throws Unavailable;
        Optional<String> saveScheduler(State state);
        OrdinaryContinuation executeFreshOrdinary();
    }
    public static final class Unavailable extends RuntimeException {
        private static final long serialVersionUID = 1L;
        public Unavailable(String message) { super(message); }
    }

    /** No branch retries a formal call. Unknown/pending outcomes remain with the formal writer. */
    public Execution execute(Staged staged, ExecutionPort port) {
        Objects.requireNonNull(staged); Objects.requireNonNull(port);
        Optional<Inputs> available;
        try { available = port.loadInputs(); }
        catch (Unavailable | IllegalArgumentException failure) {
            return unavailable(port, new LocalResult(LocalStatus.UNAVAILABLE, Optional.of(message(failure))));
        }
        if (available.isEmpty()) { return unavailable(port, new LocalResult(LocalStatus.INPUTS_ABSENT, Optional.empty())); }
        Job kind = staged.decision().job().orElseThrow();
        Outcome outcome = Outcome.UNAVAILABLE;
        CheckResult result;
        boolean actualNewStart = false;
        try {
            if (kind == Job.OBSERVE_APPLIED) {
                LifecycleResult observed = port.observeLifecycle(staged.frame()); result = observed;
                outcome = observed.status() == LifecycleStatus.OBSERVED ? Outcome.OBSERVED : Outcome.UNAVAILABLE;
            } else if (kind == Job.COMPLETE_NO_RELATION) {
                result = new LocalResult(LocalStatus.KNOWN_EMPTY_RELATION_FRONTIER, Optional.empty());
                outcome = Outcome.NO_OPERATION;
            } else {
                Optional<Pending> pending = available.orElseThrow().ledger().pending();
                if (kind == Job.RECONCILE_PENDING && (pending.isEmpty()
                        || !Optional.of(pending.orElseThrow().actionId()).equals(staged.decision().actionId()))) {
                    result = new LocalResult(LocalStatus.PENDING_IDENTITY_CHANGED, Optional.empty());
                } else if (kind == Job.QUERY_SELECTED_TARGET && pending.isPresent()) {
                    result = new LocalResult(LocalStatus.ORIGINAL_PENDING_PRESERVED, Optional.empty()); outcome = Outcome.PENDING;
                } else {
                    FormalResult formal = port.queryAndConsume(staged.frame(), staged.decision().targetCharacterId().orElseThrow());
                    result = formal;
                    actualNewStart = kind == Job.QUERY_SELECTED_TARGET && formal.status() == FormalStatus.APPLIED && formal.postconditionVerified();
                    outcome = classify(formal, actualNewStart);
                }
            }
        } catch (Unavailable | IllegalArgumentException failure) {
            result = new LocalResult(LocalStatus.UNAVAILABLE, Optional.of(message(failure)));
        }
        Optional<String> action = staged.decision().actionId();
        if (action.isEmpty() && result instanceof FormalResult formal) { action = formal.actionId(); }
        State state = complete(staged.decision().state().orElseThrow(), staged.frame().dateRaw(), kind,
                outcome, staged.decision().targetCharacterId(), action);
        Optional<String> writeError;
        try { writeError = port.saveScheduler(state); }
        catch (Unavailable failure) { writeError = Optional.of(message(failure)); }
        Receipt receipt = new Receipt(kind, staged.decision().targetCharacterId(), outcome, result, state, writeError);
        if (actualNewStart && result instanceof FormalResult formal) { return new Started(formal, receipt); }
        return new Continued(port.executeFreshOrdinary(), Optional.of(receipt), Optional.empty());
    }

    private static Outcome classify(FormalResult result, boolean actualNewStart) {
        if (actualNewStart) { return Outcome.APPLIED; }
        return switch (result.status()) {
            case RECEIPT_PENDING, POSTCONDITION_PENDING, SUBMISSION_UNRESOLVED, PENDING_RECOVERY -> Outcome.PENDING;
            case NO_POSITIVE_OPPORTUNITY -> Outcome.NO_OPERATION;
            case ALREADY_APPLIED -> result.followup().filter(value -> value != Followup.OTHER).isPresent()
                    ? Outcome.NO_OPERATION : Outcome.OBSERVED;
            case APPLIED, OTHER_OBSERVED -> Outcome.OBSERVED;
        };
    }
    private static Continued unavailable(ExecutionPort port, LocalResult result) {
        return new Continued(port.executeFreshOrdinary(), Optional.empty(), Optional.of(result));
    }
    private static StageResult preserved(StageReason reason) {
        return new StageResult(reason, Optional.empty(), Optional.empty(), Optional.empty());
    }
    private static String message(Throwable failure) {
        String value = failure.getMessage(); return value == null || value.isBlank() ? failure.getClass().getSimpleName() : value;
    }
    private static void text(String value) { require(value != null && !value.isBlank(), "nonempty text required"); }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
