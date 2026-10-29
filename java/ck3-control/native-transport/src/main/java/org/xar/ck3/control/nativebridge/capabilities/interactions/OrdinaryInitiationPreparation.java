package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.family.EducationPayloadMaterializer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Actual same-writer fresh preflight, shared education materialization and durable claim before the one submitter. */
public final class OrdinaryInitiationPreparation implements ActionPorts.PreparationPort {
    /** Root joins its original Driver observation and source-bound interaction projection in one borrowed session. */
    public interface Frames {
        ActualFrame observe(ContinuityStorePort.Session same, ActionCommand command);
        ActualFrame original(ContinuityStorePort.Session same, ActionCommand command, ActionState.Attempt attempt);
        default ActualFrame after(ContinuityStorePort.Session same, ActionCommand command, ActionState.Attempt attempt) {
            need(!ActionReconciliationScope.activeFor(command),"this legacy frame adapter has no original pending observation scope");
            return observe(same,command);
        }
    }
    @FunctionalInterface public interface SourceBoundProjection { Context project(DriverObservationAssembler.Complete actual, java.time.Instant deadline); }
    /** Real held observation producer; original reconciliation refuses an evicted/unavailable before image. */
    public static Frames heldFrames(HeldDriverObservationPort sameHeld, SourceBoundProjection actualProjection) {
        Objects.requireNonNull(sameHeld); Objects.requireNonNull(actualProjection);
        return new Frames() {
            @Override public ActualFrame observe(ContinuityStorePort.Session same, ActionCommand command) {
                try { var actual = sameHeld.observe(ActionObservationWindow.deadline(command)); return new ActualFrame(actual, actualProjection.project(actual, ActionObservationWindow.deadline(command))); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IllegalStateException("actual ordinary observation interrupted", interrupted); }
            }
            @Override public ActualFrame original(ContinuityStorePort.Session same, ActionCommand command, ActionState.Attempt attempt) {
                var actual = sameHeld.requireRetained(command.before(), attempt.guard().nativeEvidence());
                return new ActualFrame(actual, actualProjection.project(actual, ActionObservationWindow.deadline(command)));
            }
            @Override public ActualFrame after(ContinuityStorePort.Session same, ActionCommand command, ActionState.Attempt attempt) {
                if(!ActionReconciliationScope.activeFor(command)) return observe(same,command);
                try { var actual=ActionReconciliationScope.requireFrame(command,attempt);
                    return new ActualFrame(actual,actualProjection.project(actual,ActionObservationWindow.deadline(command))); }
                catch(IOException failure) { throw new UncheckedIOException("actual original pending observation unavailable",failure); }
            }
        };
    }
    public record ActualFrame(DriverObservationAssembler.Complete actual, Context interaction) {
        public ActualFrame {
            Objects.requireNonNull(actual); Objects.requireNonNull(interaction);
            RootInteractionContextProjection.requireExact(actual, interaction);
        }
    }
    /** Production cold restoration reopens the original native/Driver guard closure. */
    public static Frames heldFrames(java.util.function.Supplier<HeldDriverObservationPort> currentHeld,
            SourceBoundProjection projection, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader originalFrames) {
        Objects.requireNonNull(currentHeld); Objects.requireNonNull(projection); Objects.requireNonNull(archive); Objects.requireNonNull(originalFrames);
        return new Frames() {
            @Override public ActualFrame observe(ContinuityStorePort.Session same, ActionCommand command) {
                try {
                    var actual=Objects.requireNonNull(currentHeld.get()).observe(ActionObservationWindow.deadline(command));
                    return new ActualFrame(actual,projection.project(actual,ActionObservationWindow.deadline(command)));
                } catch(InterruptedException e) { Thread.currentThread().interrupt(); throw new IllegalStateException("actual ordinary read interrupted",e); }
            }
            @Override public ActualFrame original(ContinuityStorePort.Session same, ActionCommand command, ActionState.Attempt attempt) {
                var actual=RootGuardEvidence.loadFrame(attempt.guard(),archive.withSession(same),originalFrames);
                return new ActualFrame(actual,projection.project(actual,command.deadline()));
            }
            @Override public ActualFrame after(ContinuityStorePort.Session same, ActionCommand command, ActionState.Attempt attempt) {
                if(!ActionReconciliationScope.activeFor(command)) return observe(same,command);
                try { var actual=ActionReconciliationScope.requireFrame(command,attempt);
                    return new ActualFrame(actual,projection.project(actual,ActionObservationWindow.deadline(command))); }
                catch(IOException failure) { throw new UncheckedIOException("actual original pending observation unavailable",failure); }
            }
        };
    }
    private final java.util.function.Supplier<NativeGameTransport> transport;
    private final PlanningReadPort reads;
    private final ReadContract<OrdinaryContext> ordinaryQuery;
    private final Frames frames;
    private final OrdinaryClaimDomain claims;
    private final ActionPorts.OutcomeArchive archive;
    private final Optional<GuardianOutgoingEffects> guardian;
    public OrdinaryInitiationPreparation(NativeGameTransport sameTransport, PlanningReadPort sameReads,
            ReadContract<OrdinaryContext> registeredOrdinaryQuery, Frames actualFrames,
            OrdinaryClaimDomain actualClaims, ActionPorts.OutcomeArchive sameArchive) {
        Objects.requireNonNull(sameTransport); transport = () -> sameTransport; reads = Objects.requireNonNull(sameReads);
        ordinaryQuery = Objects.requireNonNull(registeredOrdinaryQuery); frames = Objects.requireNonNull(actualFrames);
        claims = Objects.requireNonNull(actualClaims); archive = Objects.requireNonNull(sameArchive); guardian=Optional.empty();
        need(ordinaryQuery.operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP)
                && ordinaryQuery.requiredCapability().equals(Optional.of(OrdinaryInteractionCodec.QUERY_CAPABILITY)), "genuine registered ordinary query required");
    }
    public OrdinaryInitiationPreparation(NativeGameTransport sameTransport, PlanningReadPort sameReads,
            ReadContract<OrdinaryContext> registeredOrdinaryQuery, Frames actualFrames,
            OrdinaryClaimDomain actualClaims, ActionPorts.OutcomeArchive sameArchive, GuardianOutgoingEffects actualGuardian) {
        this(() -> Objects.requireNonNull(sameTransport),sameReads,registeredOrdinaryQuery,actualFrames,actualClaims,sameArchive,actualGuardian);
        Objects.requireNonNull(sameTransport);
    }
    public OrdinaryInitiationPreparation(java.util.function.Supplier<NativeGameTransport> actualCurrentTransport, PlanningReadPort sameReads,
            ReadContract<OrdinaryContext> registeredOrdinaryQuery, Frames actualFrames,
            OrdinaryClaimDomain actualClaims, ActionPorts.OutcomeArchive sameArchive, GuardianOutgoingEffects actualGuardian) {
        transport=Objects.requireNonNull(actualCurrentTransport); reads=Objects.requireNonNull(sameReads); ordinaryQuery=Objects.requireNonNull(registeredOrdinaryQuery);
        frames=Objects.requireNonNull(actualFrames); claims=Objects.requireNonNull(actualClaims); archive=Objects.requireNonNull(sameArchive);
        guardian=Optional.of(Objects.requireNonNull(actualGuardian));
        need(ordinaryQuery.operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP)
                && ordinaryQuery.requiredCapability().equals(Optional.of(OrdinaryInteractionCodec.QUERY_CAPABILITY)), "genuine registered ordinary query required");
    }
    public GuardianOutgoingEffects guardianEffects() { return guardian.orElseThrow(()->new IllegalStateException("actual guardian effect observer not installed")); }
    @Override public NativeRequest prepare(ActionCommand command) { throw new IllegalStateException("ordinary initiation requires the actual borrowed writer session and coordinator request ID"); }
    @Override public NativeRequest prepare(ActionCommand command, String requestId) { return prepare(command); }
    @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand command, String requestId) {
        need(command.operation().value().equals(OrdinaryInteractionCodec.INITIATE_STEP), "ordinary preparation operation");
        need(requestId != null && requestId.matches("[A-Za-z0-9_.:-]{1,128}"), "actual coordinator request ID");
        return archive.inSession(same, scoped -> prepareBound(same, command, requestId, scoped));
    }
    private NativeRequest prepareBound(ContinuityStorePort.Session same, ActionCommand command, String requestId, ActionPorts.OutcomeArchive scoped) {
        OrdinaryInitiationIntent intent = OrdinaryInitiationIntent.fromJson(command.arguments());
        ActualFrame before = frames.observe(same, command); requireOrigin(command, before.actual());
        need(before.actual().identity().equals(command.before()), "ordinary command origin is stale");
        requireInitiationCapability(before.interaction());
        OrdinaryRequest request = nativeIntent(intent); ObjectNode queryArgs = InteractionArguments.body(before.interaction()); InteractionArguments.ordinary(queryArgs, request);
        var read = reads.read(same, ordinaryQuery, new PlanningReadRequest(command.before(), command.source(), command.sessionId(), ordinaryQuery.operation(), InteractionArguments.app(queryArgs), command.deadline()));
        if (!(read instanceof PlanningReadResult.Known<OrdinaryContext> known)) throw new IllegalStateException("actual ordinary final terms unavailable");
        need(known.value().readyToInitiate() && known.receipt().request().before().equals(before.actual().identity())
                && known.receipt().contractId().equals(ordinaryQuery.contractId()), "actual fresh ordinary preflight is not ready or changed contract");
        ActualFrame current = frames.observe(same, command); requireOrigin(command, current.actual());
        need(current.actual().identity().equals(before.actual().identity())
                && current.actual().fullBindingSha256().equals(before.actual().fullBindingSha256())
                && current.interaction().connectionGeneration().equals(before.interaction().connectionGeneration()), "ordinary preflight crossed its actual frame");
        RawJson original = known.receipt().original().originalResultToken().orElseThrow(() -> new IllegalStateException("actual ordinary query result missing"));
        OrdinaryInteractionCodec.query(original, current.interaction(), request);
        OpportunityJson.Obj projectedQuery = publicQuery(original, current.interaction());
        Optional<ExactRef> originalMaterialization=Optional.empty();
        if (intent.education().isPresent()) {
            OrdinaryInitiationIntent.Education education = intent.education().orElseThrow();
            var materialized = EducationPayloadMaterializer.prepareAndMaterialize(requestId, projectedQuery, current.actual().semantic(),
                    intent.recipientId(), education.childId(), education.guardianId(), education.optionKeys());
            originalMaterialization=Optional.of(scoped.preserveMaterial(new RawJson(DriverJson.encode(materialized.projection()))));
            need(materialized.requestIntent().equals(EducationPayloadMaterializer.materialize(materialized.reviewed(), projectedQuery,
                    current.actual().semantic()).requestIntent()), "education current source materialization changed");
        }
        Context c = current.interaction();
        var identity = new OrdinaryOnceClaims.Identity(command.before().machineId(), command.before().game().pid(),
                command.before().game().creationFiletime().value().toString(), c.actor().longValueExact(), intent.interactionKey(), intent.recipientId());
        var binding = new OrdinaryOnceClaims.Binding(c.before().frame().snapshotId(), c.before().frame().revision().toString(), c.revision().toString(),
                c.date().toString(), c.connectionGeneration().toString(), c.before().frame().episodeRunId());
        // A fresh query may queue a READ publication. Check before a next-intent permit or once-claim can be consumed.
        try { ActionReadPublicationScope.requireClearBeforeIntent(same, command); }
        catch (IOException failure) { throw new UncheckedIOException("actual pre-INTENT READ barrier unavailable; no ordinary claim was consumed", failure); }
        var retainedClaim=claims.claim(same, new OrdinaryOnceClaims.Request(identity, binding, requestId));
        // Claim and permit consumption are already on the original writer before any native submission permit exists.
        var nativeRequest=new NativeRequest(OrdinaryInteractionCodec.INITIATE_STEP, OrdinaryInteractionCodec.INITIATE_CAPABILITY,
                OrdinaryInteractionCodec.request(c, request, true));
        var originals=GuardianOutgoingEffects.preservePreparation(command,requestId,known.receipt(),retainedClaim,nativeRequest,originalMaterialization,scoped);
        return new NativeRequest(nativeRequest.step(),nativeRequest.requiredCapability(),nativeRequest.additionalFields(),originals);
    }
    /** ACK remains pending. This records the first actual later control frame and never invents a business effect. */
    public ActionPorts.PostconditionResult observe(ContinuityStorePort.Session same, ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome outcome) {
        return observeProjected(same,command,attempt,outcome).result();
    }
    public NativeEffectRegistry.Projected observeProjected(ContinuityStorePort.Session same, ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome outcome) {
        return archive.inSession(same, scoped -> {
            need(command.operation().value().equals(OrdinaryInteractionCodec.INITIATE_STEP) && attempt.requestId().equals(outcome.requestId()), "ordinary receipt request identity");
            OrdinaryInitiationIntent intent = OrdinaryInitiationIntent.fromJson(command.arguments());
            ActualFrame original = frames.original(same, command, attempt); requireOrigin(command, original.actual());
            need(original.actual().identity().equals(command.before()),"original ordinary before image differs from its durable action");
            ActualFrame after = frames.after(same, command, attempt); requireOrigin(command, after.actual());
            requireAfterControl(original,after);
            List<ExactRef> evidence = new ArrayList<>(List.of(after.actual().originalEvidence(), scoped.referenceOf(outcome)));
            if (outcome instanceof NativeActionPort.AckReceived ack) {
                need(ack.outbound().isPresent(), "ordinary original outbound packet custody missing");
                // The raw receipt belongs to the attempt's original frame; later state is retained separately.
                OrdinaryInteractionCodec.initiation(ack.originalResultToken().orElseThrow(), original.interaction(), nativeIntent(intent));
                var claim = claims.requireClaim(same, attempt.requestId());
                need(claim.claim().request().binding().snapshotId().equals(command.before().frame().snapshotId())
                        && claim.claim().request().binding().nativeRevisionDecimal().equals(command.before().frame().identity().nativeRevision().toString()),
                        "ordinary receipt claim crossed original frame");
                RawJson publicData=projectPending(ack.originalResultToken().orElseThrow(),original.interaction(),after.actual(),attempt.requestId(),claim.original());
                ExactRef publicRef=scoped.preserveMaterial(publicData);
                if(!GuardianOutgoingEffects.accepts(command))evidence.add(0,OrdinaryPendingPublication.preserve(command,attempt,ack,original,after,claim.original(),publicData,scoped));
                evidence.add(publicRef);
            }
            if(guardian.isPresent() && GuardianOutgoingEffects.accepts(command))
                return guardian.orElseThrow().observe(same,command,attempt,outcome,original,after,scoped);
            return NativeEffectRegistry.Projected.pending("ordinary original request remains pending; independent event/save/outgoing-request effect required", evidence);
        });
    }
    static void requireAfterControl(ActualFrame original,ActualFrame after) {
        need(original.actual().identity().machineId().equals(after.actual().identity().machineId())
                &&original.actual().identity().game().equals(after.actual().identity().game())
                &&original.actual().identity().frame().episodeRunId().equals(after.actual().identity().frame().episodeRunId())
                &&original.actual().source().equals(after.actual().source())&&original.actual().sessionId().equals(after.actual().sessionId()),
                "ordinary after control crossed its original physical source/session");
        var expected = original.actual().identity().frame(); var later = after.actual().identity().frame();
        need(later.identity().dateRaw().equals(expected.identity().dateRaw()) && later.identity().player().equals(expected.identity().player())
                && later.revision().compareTo(expected.revision()) >= 0 && later.identity().nativeRevision().compareTo(expected.identity().nativeRevision()) >= 0,
                "ordinary initiation changed its control identity or regressed revisions");
        need(original.interaction().build() == after.interaction().build()
                && original.interaction().connectionGeneration().equals(after.interaction().connectionGeneration()), "ordinary after exact build/connection changed");
        need(after.interaction().controls().paused() && after.interaction().controls().mapReady() && after.interaction().controls().alive(),
                "ordinary initiation after read lacks the actual living paused map");
        for (String field : List.of("speed", "paused", "map_ready", "local_player_id", "episode_character_id"))
            need(original.actual().semantic().members().containsKey(field) == after.actual().semantic().members().containsKey(field)
                && Objects.equals(original.actual().semantic().get(field), after.actual().semantic().get(field)), "ordinary after control field changed: " + field);
    }
    private void requireInitiationCapability(Context context) {
        try {
            var held=Objects.requireNonNull(transport.get(),"actual current ordinary transport is not adopted");
            var hello = held.originalHello(); var actual = held.diagnostics().session().orElseThrow();
            need(hello.capabilities().contains(OrdinaryInteractionCodec.INITIATE_CAPABILITY)
                    && actual.game().equals(context.before().game()) && actual.machineId().equals(context.before().machineId())
                    && actual.sessionId().equals(context.sessionId()) && actual.connectionGeneration().equals(context.connectionGeneration()),
                    "same held native DLL lacks ordinary initiation or changed identity");
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private static OrdinaryRequest nativeIntent(OrdinaryInitiationIntent intent) { return GuardianOutgoingEffects.nativeIntent(intent); }
    static OpportunityJson.Obj publicQuery(RawJson raw, Context context) {
        ObjectNode n = parse(raw).deepCopy(); n.put("queried_snapshot_id", context.before().frame().snapshotId()).put("queried_revision", context.before().frame().revision())
                .put("queried_native_revision", context.revision()); n.put("ordinary_interaction_context_ready", true);
        return DriverJson.object(encode(n).bytes(), DriverJson.MAX_NATIVE_BYTES);
    }
    static RawJson projectPending(RawJson original, Context before, DriverObservationAssembler.Complete after, String requestId, ExactRef claim) {
        ObjectNode n = parse(original).deepCopy();
        n.put("queried_snapshot_id", before.before().frame().snapshotId()).put("queried_revision", before.before().frame().revision()).put("queried_native_revision", before.revision());
        n.put("after_snapshot_id", after.identity().frame().snapshotId()).put("after_revision", after.identity().frame().revision())
                .put("after_native_revision", after.identity().frame().identity().nativeRevision()).put("after_control_frame_verified", true)
                .put("action_request_id", requestId).put("action_claim_path", claim.path()).put("business_effects_verified", false).put("full_product_acceptance_credit", false);
        return encode(n);
    }
    private static void requireOrigin(ActionCommand command, DriverObservationAssembler.Complete actual) {
        need(actual.identity().machineId().equals(command.before().machineId()) && actual.identity().game().equals(command.before().game())
                && actual.identity().frame().episodeRunId().equals(command.before().frame().episodeRunId())
                && actual.sessionId().equals(command.sessionId()) && actual.source().equals(command.source()), "ordinary full observation crossed Game/source/session/episode");
    }
}
