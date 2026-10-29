package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual same-writer preview and independent post producers. Every token/claim comes from the sole retreat domain. */
public final class ArmyRetreatService {
    @FunctionalInterface public interface Deadline { Instant current(); }
    @FunctionalInterface public interface TokenPublication { void publish(OperationKey actualOrderStep); }
    public record PreviewReply(ArmyRetreatPreview.Captured captured, ArmyRetreatDomain.Known durable) {
        public PreviewReply { Objects.requireNonNull(captured); Objects.requireNonNull(durable); require(captured.ready() == durable.state().preview().isPresent(), "durable preview differs from its actual availability"); if (captured.ready()) require(durable.state().preview().orElseThrow().equals(captured.value()), "durable preview changed original Native composition"); }
    }
    public record PostReply(ArmyRetreatFrames.Current current, ActiveRetreatPost.Result result, List<PlanningReadReceipt> originals, ArmyRetreatDomain.Known durable) {
        public PostReply { Objects.requireNonNull(current); Objects.requireNonNull(result); originals = List.copyOf(originals); Objects.requireNonNull(durable); require(durable.state().lastPost().equals(Optional.of(result.json())), "durable post differs from its independent lifecycle result"); }
    }
    public record CollectedPost(ArmyRetreatFrames.Current current, ActiveRetreatPost.Result result, List<PlanningReadReceipt> originals) {
        public CollectedPost { Objects.requireNonNull(current); Objects.requireNonNull(result); originals = List.copyOf(originals); }
    }
    private final ContinuityStorePort writer; private final ArmyRetreatDomain domain; private final ArmyRetreatFrames frames; private final ArmyRetreatPreview previews;
    private final ArmyBattleReads battles; private final java.util.function.Supplier<RootReadContractCatalog> catalog; private final Deadline deadline; private final TokenPublication publication;
    public ArmyRetreatService(ContinuityStorePort originalWriter, ArmyRetreatDomain soleDomain, ArmyRetreatFrames actualFrames, ArmyRetreatPreview actualPreviews,
            ArmyBattleReads actualBattles, RootReadContractCatalog exactCatalog, Deadline currentDeadline, TokenPublication actualFamilyPublication) {
        this(originalWriter, soleDomain, actualFrames, actualPreviews, actualBattles, () -> Objects.requireNonNull(exactCatalog), currentDeadline, actualFamilyPublication);
    }
    public ArmyRetreatService(ContinuityStorePort originalWriter, ArmyRetreatDomain soleDomain, ArmyRetreatFrames actualFrames, ArmyRetreatPreview actualPreviews,
            ArmyBattleReads actualBattles, java.util.function.Supplier<RootReadContractCatalog> actualCatalog, Deadline currentDeadline, TokenPublication actualFamilyPublication) {
        writer = Objects.requireNonNull(originalWriter); domain = Objects.requireNonNull(soleDomain); frames = Objects.requireNonNull(actualFrames); previews = Objects.requireNonNull(actualPreviews);
        battles = Objects.requireNonNull(actualBattles); catalog = Objects.requireNonNull(actualCatalog); deadline = Objects.requireNonNull(currentDeadline); publication = Objects.requireNonNull(actualFamilyPublication);
    }
    public PreviewReply preview_active_combat_retreat_v1(ArmyCalls.RetreatPreview input) throws InterruptedException {
        try { return writer.locked(session -> { try { return preview(session, input, deadline.current()); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new InterruptedIo(interrupted); } }); }
        catch (InterruptedIo interrupted) { throw (InterruptedException) interrupted.getCause(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    public PreviewReply preview(ContinuityStorePort.Session session, ArmyCalls.RetreatPreview input, Instant end) throws IOException, InterruptedException {
        writer.requireSession(session);var before = frames.current(end);return preview(session,input,before,false);
    }
    /** Same original domain transition while Root retains its actual borrowed planning scope. */
    public PreviewReply previewBorrowed(ContinuityStorePort.Session session, ArmyCalls.RetreatPreview input,
            ArmyRetreatFrames.Current before) throws IOException {
        writer.requireSession(session);
        try {return preview(session,input,before,true);}
        catch(InterruptedException impossible) {Thread.currentThread().interrupt();throw new IOException("borrowed retreat preview was interrupted",impossible);}
    }
    private PreviewReply preview(ContinuityStorePort.Session session, ArmyCalls.RetreatPreview input,
            ArmyRetreatFrames.Current before,boolean borrowed) throws IOException,InterruptedException {
        input.revision().requireCurrent(before.context().before().frame().revision());
        var started = domain.apply(session, new ActiveRetreatState.StartPreview(before.source()), new ArmyRetreatDomain.Proof(before.actual(), before.actual(), List.of(), Optional.empty()));
        var capture = borrowed ? previews.captureBorrowed(session,input,before) : previews.capture(session, input, before); ArmyRetreatDomain.Known durable = started;
        if (capture.ready()) {
            var target = OpportunityJson.object(capture.value().get("target_preview"), "target preview"); publication.publish(new OperationKey(OpportunityJson.text(target.get("order_step"), "actual order step")));
            durable = domain.apply(session, new ActiveRetreatState.FinishPreview(before.source(), capture.value()), new ArmyRetreatDomain.Proof(before.actual(), capture.after().actual(),
                    List.of(capture.control().receipt(), capture.route().orElseThrow().receipt()), Optional.empty()));
        }
        return new PreviewReply(capture, durable);
    }
    /** Read-only reconciliation: no ActionCoordinator, child submitter or token replacement is reachable here. */
    public PostReply observe(ContinuityStorePort.Session session, Instant end) throws IOException, InterruptedException {
        var collected = collect(session, end); var durable = commit(session, collected); return new PostReply(collected.current(), collected.result(), collected.originals(), durable);
    }
    /** Composite callers retain the pending intent until their authoritative parent settlement is durable. */
    public CollectedPost collect(ContinuityStorePort.Session session, Instant end) throws IOException, InterruptedException {
        var original = domain.read(session); var order = original.state().pending().orElseThrow(() -> new IllegalArgumentException("no original pending retreat to observe"));
        var before = frames.current(end); domain.apply(session, new ActiveRetreatState.StartObserve(before.source()), new ArmyRetreatDomain.Proof(before.actual(), before.actual(), List.of(), Optional.empty()));
        List<PlanningReadReceipt> reads = new ArrayList<>(); var revision = new ArmyCalls.Revision(new Present<>(before.context().before().frame().revision()));
        var transition = battles.read(session, Objects.requireNonNull(catalog.get()), new ArmyBattleReads.Selection(new ArmyCalls.CombatId(PublicMethod.QUERY_BATTLE_TRANSITION_V1, revision, new FullId(order.arguments().expectedCombatId())), before.context())); reads.add(transition.receipt());
        ActiveRetreatPost.Result result = ArmyRetreatDomain.post(order, before, reads);
        if (result instanceof ActiveRetreatPost.Pending pending && pending.terminalQueryRequired()) {
            var terminal = battles.read(session, Objects.requireNonNull(catalog.get()), new ArmyBattleReads.Selection(ArmyRetreatDomain.terminalCall(order, before.context()), before.context())); reads.add(terminal.receipt()); result = ArmyRetreatDomain.post(order, before, reads);
        }
        var after = frames.current(end); ArmyRetreatFrames.same(before, after);
        return new CollectedPost(after, result, reads);
    }
    public ArmyRetreatDomain.Known commit(ContinuityStorePort.Session session, CollectedPost collected) throws IOException {
        return domain.apply(session, new ActiveRetreatState.FinishObserve(collected.current().source(), collected.result()), new ArmyRetreatDomain.Proof(collected.current().actual(), collected.current().actual(), collected.originals(), Optional.empty()));
    }
    public PublicBindings.BoundBinding installPreview(PublicBindings bindings, ExactRef actualSource) {
        return bindings.register(PublicMethod.PREVIEW_ACTIVE_COMBAT_RETREAT_V1, ArmyCalls.RetreatPreview.class, PreviewReply.class, this::preview_active_combat_retreat_v1,
                args -> { if (!(args instanceof PublicBindings.Value value)) throw new IllegalArgumentException("retreat preview requires exact named arguments"); return ArmyCalls.RetreatPreview.class.cast(ArmyCallCodec.decode(PublicMethod.PREVIEW_ACTIVE_COMBAT_RETREAT_V1, value.original())); }, ArmyRetreatService::encode,
                new PublicRoutes.Target(ArmyRetreatService.class.getName(), "preview_active_combat_retreat_v1", actualSource), PublicRoutes.Status.IMPLEMENTED, "actual full battle+route queries and durable single-source token; missing domain initialization rejects; candidate requires Root verification");
    }
    public static RawJson encode(PreviewReply reply) { return ArmyPublicWire.encode(reply.captured().value(), reply.captured().before().context()); }
    public static RawJson encode(PostReply reply) { return ArmyPublicWire.encode(reply.result().json(), reply.current().context()); }
    private static final class InterruptedIo extends IOException { @java.io.Serial private static final long serialVersionUID = 1L; InterruptedIo(InterruptedException original) { super(original); } }
}
