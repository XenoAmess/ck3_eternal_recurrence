package org.xar.ck3.control.application.presentation;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.function.Consumer;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/**
 * Bounded, in-memory observations of the existing planner/coordinator. No command,
 * writer, native call, restore permission, file publication or screen-draw proof.
 */
public final class DecisionDisplay {
    public static final int MAX_HISTORY = 8;
    public static final int MAX_IDENTITIES = 128;
    public static final int MAX_REASON_CHARS = 1600;

    public enum Status {
        PLANNED, WAITING, PLANNING_STOPPED, PREPARING, RECONCILING,
        ACK_RECEIVED, UNRESOLVED, SEND_CONFIRMED, CONFIRMED, REJECTED_BEFORE_DISPATCH,
        REJECTED, TERMINAL_WITHOUT_EFFECT, CALL_UNAVAILABLE
    }
    public enum Delivery { NOT_ATTEMPTED, RENDERER_UPDATED, UNAVAILABLE }

    /** The original sealed origin retains exact Game birth, episode and both revisions. */
    public record Context(CommandOrigin origin, G2Source source, String sessionId) {
        public Context {
            Objects.requireNonNull(origin); Objects.requireNonNull(source); StrictJson.text(sessionId);
            StrictJson.require(origin.machineId().equals(source.machineId()), "display context machine differs");
        }
    }
    public record Identity(Context context, String actionId, String bodySha256, OperationKey operation) {
        public Identity {
            Objects.requireNonNull(context); Objects.requireNonNull(operation);
            StrictJson.require(actionId != null && actionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"), "display original action ID required");
            StrictJson.require(bodySha256 != null && bodySha256.matches("[0-9a-f]{64}"), "display complete original action SHA required");
        }
        public static Identity from(ActionCommand original) {
            Objects.requireNonNull(original);
            return new Identity(new Context(original.origin(), original.source(), original.sessionId()),
                    original.actionId(), ActionCodec.bodySha256(original), original.operation());
        }
    }
    /** Request and receipt sequence are actual canonical observations, absent before an attempt exists. */
    public record Card(Context context, Optional<Identity> action, List<Identity> parents,
            String policy, String phase, String rationale, Status status,
            Optional<String> attemptRequestId, OptionalLong receiptSequence, Instant observedAt) {
        public Card {
            Objects.requireNonNull(context); Objects.requireNonNull(action); parents = List.copyOf(parents);
            StrictJson.text(policy); StrictJson.text(phase); Objects.requireNonNull(rationale);
            StrictJson.require(rationale.length() <= MAX_REASON_CHARS, "bounded optional display rationale required");
            Objects.requireNonNull(status); Objects.requireNonNull(attemptRequestId); Objects.requireNonNull(receiptSequence); Objects.requireNonNull(observedAt);
            StrictJson.require(parents.size() <= 2, "display parent nesting exceeds original coordinator bound");
            action.ifPresent(id -> StrictJson.require(id.context().equals(context), "display card crossed original action context"));
            for (Identity parent : parents) {
                StrictJson.require(parent.context().origin().machineId().equals(context.origin().machineId())
                        && parent.context().origin().game().equals(context.origin().game())
                        && parent.context().sessionId().equals(context.sessionId()), "display child crossed original parent Game/session");
            }
            attemptRequestId.ifPresent(StrictJson::text);
            if (receiptSequence.isPresent()) StrictJson.safe(receiptSequence.getAsLong(), 1);
            StrictJson.require(receiptSequence.isEmpty() || action.isPresent(), "receipt display requires its original action");
        }
    }
    public record Snapshot(long publication, Optional<Card> current, List<Card> history, Delivery delivery,
            Optional<String> diagnostic) {
        public Snapshot {
            StrictJson.safe(publication, 0); Objects.requireNonNull(current); history = List.copyOf(history);
            StrictJson.require(history.size() <= MAX_HISTORY, "finite decision history required");
            Objects.requireNonNull(delivery); Objects.requireNonNull(diagnostic);
        }
    }
    public record Failure(long publication, String reason) {
        public Failure { StrictJson.safe(publication, 0); StrictJson.text(reason); }
    }
    @FunctionalInterface public interface Renderer {
        /** Returning acknowledges this renderer update only, never OS composition or a recorded frame. */
        void render(Snapshot actual) throws IOException;
    }

    private final Clock clock;
    private final Renderer renderer;
    private final Consumer<Failure> diagnostics;
    private final LinkedHashMap<Identity, Card> identities = new LinkedHashMap<>();
    private final LinkedHashMap<Identity, Card> history = new LinkedHashMap<>();
    private Snapshot snapshot = new Snapshot(0, Optional.empty(), List.of(), Delivery.NOT_ATTEMPTED, Optional.empty());

    public DecisionDisplay(Clock clock, Renderer renderer, Consumer<Failure> diagnostics) {
        this.clock = Objects.requireNonNull(clock); this.renderer = Objects.requireNonNull(renderer);
        this.diagnostics = Objects.requireNonNull(diagnostics);
    }
    public synchronized Snapshot snapshot() { return snapshot; }

    /** Called with the actual returned whole ordinary plan, after its publication scope has exited. */
    public void planned(PlanningRequest original, PlanningResult actual) {
        safely(() -> {
            Objects.requireNonNull(original); Objects.requireNonNull(actual);
            StrictJson.require(actual.trace().before().equals(original.before()), "display plan crossed actual observation");
            Optional<OrdinaryPolicy.Draft> draft = actual.trace().finalPlan();
            Optional<Identity> action = Optional.empty();
            if (actual instanceof PlanningResult.ActionSelected selected) {
                StrictJson.require(draft.flatMap(OrdinaryPolicy.Draft::command).filter(selected.command()::equals).isPresent(), "display selected command differs from whole plan");
                action = Optional.of(Identity.from(selected.command()));
            }
            Context context = new Context(new CommandOrigin.Gameplay(original.before()), original.source(), original.sessionId());
            action.ifPresent(id -> StrictJson.require(id.context().equals(context), "display chosen command crossed planning context"));
            Status status = actual instanceof PlanningResult.ActionSelected ? Status.PLANNED
                    : actual instanceof PlanningResult.Stopped || actual instanceof PlanningResult.IncompleteMigration
                    ? Status.PLANNING_STOPPED : Status.WAITING;
            String reason = switch (actual) {
                case PlanningResult.ActionSelected ignored -> draft.orElseThrow().reason();
                case PlanningResult.ReadOnlyWait wait -> wait.reason();
                case PlanningResult.RefreshRequired refresh -> refresh.reason();
                case PlanningResult.Stopped stopped -> stopped.detail();
                case PlanningResult.IncompleteMigration incomplete -> "当前生产规划阶段缺失：" + incomplete.missingStages();
                case PlanningResult.ExistingActionReconciliation ignored -> actual.trace().visits().isEmpty()
                        ? "核对原账本中的既有操作；不重复提交。" : actual.trace().visits().getLast().reason();
            };
            publish(new Card(context, action, List.of(), bounded(draft.map(OrdinaryPolicy.Draft::policy).orElse("planner"), 240),
                    bounded(draft.map(OrdinaryPolicy.Draft::phase).orElse("current"), 240),
                    bounded(reason, MAX_REASON_CHARS), status, Optional.empty(), OptionalLong.empty(), clock.instant()));
        });
    }

    /** All parent commands are fetched by the identical coordinator from its already-held canonical journal. */
    public void preparing(ActionCommand original, Supplier<List<ActionCommand>> actualParents, boolean readOnly) {
        safely(() -> {
            Identity identity = Identity.from(original);
            Card prior = identities.get(identity);
            List<Identity> supplied = actualParents.get().stream().map(Identity::from).toList();
            StrictJson.require(prior == null || prior.parents().isEmpty() || supplied.isEmpty() || prior.parents().equals(supplied),
                    "display cannot replace the canonical parent chain");
            List<Identity> parents = supplied.isEmpty() && prior != null ? prior.parents() : supplied;
            Card parent = null;
            for (int i = parents.size() - 1; i >= 0 && parent == null; i--) parent = identities.get(parents.get(i));
            String reason = prior != null ? prior.rationale() : parent != null
                    ? bounded("所属决策理由：" + parent.rationale(), MAX_REASON_CHARS)
                    : "该步骤来自当前已授权调用；调用者没有提供规划理由。";
            String policy = prior != null ? prior.policy() : parent != null ? parent.policy() : "direct";
            String phase = prior != null ? prior.phase() : parent != null ? parent.phase() : "current";
            publish(new Card(identity.context(), Optional.of(identity), parents, policy, phase, reason,
                    readOnly ? Status.RECONCILING : Status.PREPARING,
                    prior == null ? Optional.empty() : prior.attemptRequestId(),
                    prior == null ? OptionalLong.empty() : prior.receiptSequence(), clock.instant()));
        });
    }
    /** Can also consume a real Controller receipt when a test or source adapter implements the coordinator port. */
    public void returned(ActionReceipt actual) {
        safely(() -> {
            Identity identity = Identity.from(actual.command());
            Card prior = identities.get(identity);
            if (prior == null) {
                prior = new Card(identity.context(), Optional.of(identity), List.of(), "original", "returned",
                        "本条显示消费原账本回执；此前的规划理由未保留。", Status.RECONCILING,
                        Optional.empty(), OptionalLong.empty(), clock.instant());
            }
            Optional<String> request = ActionTransitions.attempt(actual.state()).map(ActionState.Attempt::requestId);
            StrictJson.require(prior.attemptRequestId().isEmpty() || request.isEmpty()
                    || prior.attemptRequestId().equals(request), "display cannot replace the original native attempt");
            if (prior.receiptSequence().isPresent())
                StrictJson.require(actual.sequence() >= prior.receiptSequence().getAsLong(), "display canonical receipt regressed");
            Status status = switch (actual.outcome()) {
                case UNRESOLVED -> actual.state() instanceof ActionState.AckReceived ? Status.ACK_RECEIVED : Status.UNRESOLVED;
                case APPLIED_CONFIRMED -> Status.CONFIRMED;
                case SEND_CONFIRMED -> Status.SEND_CONFIRMED;
                case REJECTED_CONFIRMED -> Status.REJECTED;
                case REJECTED_BEFORE_DISPATCH -> Status.REJECTED_BEFORE_DISPATCH;
                case TERMINAL_WITHOUT_EFFECT -> Status.TERMINAL_WITHOUT_EFFECT;
            };
            Card next = new Card(identity.context(), Optional.of(identity), prior.parents(), prior.policy(), prior.phase(),
                    prior.rationale(), status, request.isPresent() ? request : prior.attemptRequestId(),
                    OptionalLong.of(actual.sequence()), clock.instant());
            // Re-reading the identical canonical result does not manufacture a second audience event.
            if (sameResult(prior, next)) return;
            publish(next);
        });
    }
    /** A thrown call is distinct from a canonical UNKNOWN and never changes a business receipt. */
    public void callUnavailable(ActionCommand original) {
        safely(() -> {
            Identity identity = Identity.from(original); Card prior = identities.get(identity);
            publish(new Card(identity.context(), Optional.of(identity), prior == null ? List.of() : prior.parents(),
                    prior == null ? "original" : prior.policy(), prior == null ? "unavailable" : prior.phase(),
                    prior == null ? "本次调用未返回完整结果；提交与后态以原账本为准。" : prior.rationale(),
                    Status.CALL_UNAVAILABLE, prior == null ? Optional.empty() : prior.attemptRequestId(),
                    prior == null ? OptionalLong.empty() : prior.receiptSequence(), clock.instant()));
        });
    }

    private synchronized void safely(Runnable work) {
        try { work.run(); }
        catch (RuntimeException failure) { unavailable(failure); }
    }
    private void publish(Card current) {
        if (current.action().isPresent()) {
            Identity identity = current.action().orElseThrow();
            for (Identity retained : identities.keySet())
                StrictJson.require(!retained.actionId().equals(identity.actionId())
                        || !retained.context().origin().game().equals(identity.context().origin().game())
                        || !retained.context().sessionId().equals(identity.context().sessionId())
                        || retained.equals(identity), "display action ID cannot acquire a different original body");
            identities.put(identity, current);
            while (identities.size() > MAX_IDENTITIES) identities.remove(identities.keySet().iterator().next());
            history.put(identity, current);
            while (history.size() > MAX_HISTORY) history.remove(history.keySet().iterator().next());
        }
        List<Card> rows = new ArrayList<>(history.values());
        Snapshot candidate = new Snapshot(Math.addExact(snapshot.publication(), 1), Optional.of(current), rows,
                Delivery.NOT_ATTEMPTED, Optional.empty());
        snapshot = candidate;
        try {
            renderer.render(candidate);
            snapshot = new Snapshot(candidate.publication(), candidate.current(), candidate.history(),
                    Delivery.RENDERER_UPDATED, Optional.empty());
        } catch (IOException | RuntimeException failure) { unavailable(failure); }
    }
    private void unavailable(Exception failure) {
        String reason = bounded(failure.getClass().getName() + ": " + String.valueOf(failure.getMessage()), 1000);
        snapshot = new Snapshot(snapshot.publication(), snapshot.current(), snapshot.history(), Delivery.UNAVAILABLE, Optional.of(reason));
        try { diagnostics.accept(new Failure(snapshot.publication(), reason)); }
        catch (RuntimeException ignored) { /* Display diagnostics cannot change native or writer control flow. */ }
    }
    private static boolean sameResult(Card first, Card next) {
        return first.context().equals(next.context()) && first.action().equals(next.action())
                && first.parents().equals(next.parents()) && first.status() == next.status()
                && first.attemptRequestId().equals(next.attemptRequestId())
                && first.receiptSequence().equals(next.receiptSequence());
    }
    static String bounded(String value, int maximum) {
        Objects.requireNonNull(value);
        return value.length() <= maximum ? value : value.substring(0, maximum);
    }
}

