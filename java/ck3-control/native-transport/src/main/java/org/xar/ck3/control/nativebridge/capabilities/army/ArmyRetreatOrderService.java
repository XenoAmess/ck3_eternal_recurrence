package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Public and ordinary order consumers of one installed composite and the original Game ActionCoordinator. */
public final class ArmyRetreatOrderService {
    @FunctionalInterface public interface ActionIds { String next(ContinuityStorePort.Session actualSession, Context actualBefore) throws IOException; }
    public record Reply(ActiveRetreatProposal.Order order, Context source, ActionReceipt originalAction, ArmyRetreatDomain.Known durable, Obj value,
            Optional<Obj> nativeSubmission, Optional<ArmyPublicSnapshot> actualAfter) {
        public Reply { Objects.requireNonNull(order); Objects.requireNonNull(source); Objects.requireNonNull(originalAction); Objects.requireNonNull(durable); Objects.requireNonNull(value); Objects.requireNonNull(nativeSubmission); Objects.requireNonNull(actualAfter); require(originalAction.command().before().equals(source.before()), "retreat public reply changed original action source");
            actualAfter.ifPresent(after -> require(after.context().source().equals(source.source()) && after.context().sessionId().equals(source.sessionId())
                    && after.context().before().game().equals(source.before().game()), "public retreat post crossed its actual Game/source/session")); }
    }
    private final ContinuityStorePort writer; private final ArmyRetreatDomain domain; private final ArmyRetreatFrames frames; private final ArmyRetreatComposite composite;
    private final ActionCoordinatorPort actions; private final ActionPorts.OutcomeArchive archive; private final ArmyRetreatService.Deadline deadline; private final ActionIds actionIds;
    public ArmyRetreatOrderService(ContinuityStorePort originalWriter, ArmyRetreatDomain soleDomain, ArmyRetreatFrames actualFrames, ArmyRetreatComposite installedComposite,
            ActionCoordinatorPort originalActions, ActionPorts.OutcomeArchive sameArchive, ArmyRetreatService.Deadline currentDeadline, ActionIds actualRootIds) {
        writer = Objects.requireNonNull(originalWriter); domain = Objects.requireNonNull(soleDomain); frames = Objects.requireNonNull(actualFrames); composite = Objects.requireNonNull(installedComposite);
        actions = Objects.requireNonNull(originalActions); archive = Objects.requireNonNull(sameArchive); deadline = Objects.requireNonNull(currentDeadline); actionIds = Objects.requireNonNull(actualRootIds);
    }
    public Reply order_active_combat_retreat_v1(ArmyCalls.RetreatOrder input) throws InterruptedException {
        try { return writer.locked(session -> { try { var before = frames.current(deadline.current()); var selected = select(session, input, before); return submit(session, before, selected.original(), selected.order(), actionIds.next(session, before.context())); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new InterruptedIo(interrupted); } }); }
        catch (InterruptedIo interrupted) { throw (InterruptedException) interrupted.getCause(); } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    /** Ordinary planner proposals keep their actual assessment but reuse every public token and source guard. */
    public Reply order(ContinuityStorePort.Session session, ActiveRetreatProposal.Order originalProposal, Instant end, String actualActionId) throws IOException, InterruptedException {
        var before = frames.current(end); var old = domain.read(session); ArmyRetreatOrders.matches(old.state(), originalProposal); return submit(session, before, old, originalProposal, actualActionId);
    }
    /** The caller retains its actual held frame and original writer; this produces no Native submission or observation.
     * Root's Army installer must issue its identical original parent family before dispatching the returned command.
     */
    public ActionCommand prepareCommand(ContinuityStorePort.Session session, ArmyCalls.RetreatOrder input,
            ArmyRetreatFrames.Current before, String actualActionId) throws IOException {
        var selected = select(session, input, before);
        return prepare(before, selected.original(), selected.order(), actualActionId);
    }
    private record Selected(ArmyRetreatDomain.Known original, ActiveRetreatProposal.Order order) { }
    private Selected select(ContinuityStorePort.Session session, ArmyCalls.RetreatOrder input,
            ArmyRetreatFrames.Current before) throws IOException {
        Objects.requireNonNull(session); Objects.requireNonNull(input); Objects.requireNonNull(before);
        input.revision().requireCurrent(before.context().before().frame().revision());
        var old = domain.read(session); var order = ArmyRetreatOrders.order(old.state(), input);
        return new Selected(old, order);
    }
    private ActionCommand prepare(ArmyRetreatFrames.Current before, ArmyRetreatDomain.Known old,
            ActiveRetreatProposal.Order order, String actionId) {
        require(before.source().equals(order.source()), "retreat current source differs from the sole original preview");
        return ArmyRetreatComposite.command(actionId, before, new ArmyRetreatComposite.Plan(order, old.original().reference().payload()));
    }
    private Reply submit(ContinuityStorePort.Session session, ArmyRetreatFrames.Current before, ArmyRetreatDomain.Known old, ActiveRetreatProposal.Order order, String actionId) throws IOException, InterruptedException {
        var command = prepare(before, old, order, actionId);
        return presentCommitted(session, actions.execute(session, command));
    }
    /** Present the actual already-dispatched parent. This never calls execute or reconcile.
     * The existing finish engine retains its original durable claim, actual child and read-only poststate handling.
     */
    public Reply presentCommitted(ContinuityStorePort.Session session, ActionReceipt actual) throws IOException {
        Objects.requireNonNull(session); Objects.requireNonNull(actual);
        var plan = ArmyRetreatComposite.decode(actual.command());
        return finish(session, plan.order(), new Context(actual.command().before(), actual.command().source(), actual.command().sessionId(), actual.command().deadline()), actual);
    }
    /** Existing action ID only; ActionCoordinator.reconcile never sends the original native order again. */
    public Reply reconcile(ContinuityStorePort.Session session, ActionReceipt original) throws IOException {
        return presentCommitted(session, actions.reconcile(session, original.command().actionId()));
    }
    private Reply finish(ContinuityStorePort.Session session, ActiveRetreatProposal.Order order, Context source, ActionReceipt parent) throws IOException {
        var bound = archive.withSession(session); var durable = domain.read(session); Optional<ActionReceipt> child = Optional.empty();
        var execution = ActionTransitions.composite(parent.state());
        if (execution.isPresent() && !execution.orElseThrow().children().isEmpty()) {
            require(execution.orElseThrow().children().size() == 1, "retreat never owns a second native move"); var key = execution.orElseThrow().children().getFirst();
            child = ContinuityActionJournal.lookup(session.head().state(), key.actionId(), bound); require(child.isPresent() && child.orElseThrow().bodySha256().equals(key.bodySha256()), "actual retreat child is unavailable or changed");
        }
        Optional<Obj> nativeResult = Optional.empty();
        if (child.isPresent()) {
            var actual = child.orElseThrow(); boolean rejected = actual.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected;
            if (rejected || actual.ack().filter(ack -> ack.nativeOk() && ack.originalResultToken().isPresent()).isPresent()) nativeResult = Optional.of(ArmyRetreatDomain.submission(order, actual));
        }
        Optional<ArmyPublicSnapshot> actualAfter = Optional.empty();
        if (parent.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED) durable = composite.commitApplied(session, parent);
        else if (durable.state().pending().isPresent()) {
            try {
                var actual = frames.current(source.deadline());
                actualAfter = Optional.of(new ArmyPublicSnapshot(actual.context(), actual.actual().semantic()));
                if (nativeResult.isPresent()) durable = domain.apply(session, new ActiveRetreatState.NativeOrderResult(ActiveRetreatState.ClaimKey.of(order), nativeResult.orElseThrow()), new ArmyRetreatDomain.Proof(actual.actual(), actual.actual(), List.of(), child));
                else durable = domain.apply(session, new ActiveRetreatState.UnknownOrder(ActiveRetreatState.ClaimKey.of(order), "original coordinator action unresolved; no replay"), new ArmyRetreatDomain.Proof(actual.actual(), actual.actual(), List.of(), Optional.of(parent)));
            } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException("retreat result source unavailable; original pending/claim remains durable", interrupted); }
        }
        if (actualAfter.isEmpty() && nativeResult.filter(value -> new OpportunityJson.Bool(true).equals(value.get("accepted"))).isPresent()) {
            try { var actual = frames.current(deadline.current()); actualAfter = Optional.of(new ArmyPublicSnapshot(actual.context(), actual.actual().semantic())); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException("public retreat post unavailable; retained action is never resubmitted", interrupted); }
        }
        var n = ArmyJson.empty().put("schema_version", 1).put("contract_stage", ArmyRetreatTokens.STAGE).put("step", parent.command().operation().value())
                .put("status", parent.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED ? "operational_retreat_observed" : "independent_post_pending")
                .put("operational_retreat_verified", parent.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED).put("command_causation_verified", false).put("replay_allowed", false).put("backend_id", "native-headless");
        n.set("order", OpportunityJson.toNode(ActiveRetreatState.order(order))); n.set("underlying_move_result", nativeResult.<com.fasterxml.jackson.databind.JsonNode>map(OpportunityJson::toNode).orElseGet(() -> ArmyJson.empty().nullNode()));
        n.set("independent_post", durable.state().lastPost().<com.fasterxml.jackson.databind.JsonNode>map(OpportunityJson::toNode).orElseGet(() -> ArmyJson.empty().nullNode()));
        return new Reply(order, source, parent, durable, DriverJson.object(ArmyJson.bytes(n), DriverJson.MAX_NATIVE_BYTES), nativeResult, actualAfter);
    }
    public PublicBindings.BoundBinding install(PublicBindings bindings, ExactRef actualSource) {
        return bindings.register(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, ArmyCalls.RetreatOrder.class, Reply.class, this::order_active_combat_retreat_v1,
                args -> { if (!(args instanceof PublicBindings.Value value)) throw new IllegalArgumentException("retreat order requires exact named arguments"); return ArmyCalls.RetreatOrder.class.cast(ArmyCallCodec.decode(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, value.original())); }, ArmyRetreatOrderService::encode,
                new PublicRoutes.Target(ArmyRetreatOrderService.class.getName(), "order_active_combat_retreat_v1", actualSource), PublicRoutes.Status.IMPLEMENTED, "one original coordinator composite; durable claim before dispatch; full independent battle lifecycle; requires exact Root hook/effect registration and verification");
    }
    public static RawJson encode(Reply reply) {
        Obj original = reply.nativeSubmission().orElseThrow(() -> new IllegalStateException("original native retreat result is UNKNOWN; no public ACK can be fabricated and its durable claim cannot replay"));
        return ArmyPublicWire.encode(ArmyRetreatPublicPresenter.order(reply.order(), reply.originalAction().command().operation(), original, reply.actualAfter()), reply.source());
    }
    private static final class InterruptedIo extends IOException { @java.io.Serial private static final long serialVersionUID = 1L; InterruptedIo(InterruptedException original) { super(original); } }
}
