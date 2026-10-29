package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePendingInteraction;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.PendingId;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.PendingSummary;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RootInteractionContextProjection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import java.util.Optional;

/** The original execute_step pending-context/reply branches, using their installed public owner. */
public final class RootInteractionPublicStepProducts {
    private static final String QUERY="query-pending-character-interaction-context-v1";
    private static final String QUERY_CAPABILITY="game.command."+QUERY;
    private static final String ACCEPT="accept-pending-character-interaction";
    private static final String REJECT="reject-pending-character-interaction";
    private static final String ACKNOWLEDGE="acknowledge-pending-character-interaction";
    private static final Set<String> ACTIONS=Set.of(ACCEPT,REJECT,ACKNOWLEDGE);
    private RootInteractionPublicStepProducts() { }

    /** Products borrow this exact installed object; no new native family, registry or coordinator. */
    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);
        RootRuntimeContext context=actual.context();
        KnownInteractionsRuntimeInstaller interactions=actual.interactions();
        interactions.requireContext(context);
        List<ExactRef> sources=sources(actual,interactions);
        RootPublicStepExecution.OwnerGuard owner=identical->{
            StrictJson.require(identical==context&&actual.context()==context&&actual.interactions()==interactions,
                    "pending execute step crossed its actual installed Root/interaction owner");
            interactions.requireContext(identical);
            StrictJson.require(identical.readCatalog().containsIdentity(interactions.definitions().pendingQuery()),
                    "pending execute step requires its same installed native READ contract");
        };
        var read=new RootPublicStepExecution.Read("known-pending-context",RootInteractionPublicStepProducts::query,
                owner,(original,frame,known,same,caller,archive)->{
                    requireFrame(frame,known);
                    StrictJson.require(original.before().equals(frame.identity())&&original.source().equals(frame.source())
                            &&original.sessionId().equals(frame.sessionId()),"pending execute READ crossed its original held planning frame");
                    // The Python producer checks this exact native capability before inspecting the ID.
                    var request=queryRequest(caller,frame.semantic(),original.observations().bridgeCapabilities(),
                            frame.identity().frame().revision());
                    return InteractionDirectPublicCodec.encode(interactions.queryPublicPending(same,frame,request,original.deadline()));
                },sources,RootPublicStepExecution.ReadValidation.OWNER_ORDERED);
        var action=new RootPublicStepExecution.OwnedAction("known-pending-reply",RootInteractionPublicStepProducts::action,
                owner,(root,installed,caller,deadline)->{
                    StrictJson.require(installed==actual&&root==context.actions(),"pending execute ACTION crossed its actual Root");
                    interactions.requireOwner(root);
                    var observed=new AtomicReference<PendingSummary>();
                    var requested=new AtomicReference<PendingInteractionPublicCodec.Request>();
                    return root.executePublicDecision(deadline,(frame,known,same)->{
                        // current() borrows Root's already active exact lease. It cannot observe again.
                        var request=context.readiness().current(same,frame.identity(),deadline,lease->{
                            StrictJson.require(lease.frame()==frame&&lease.driver()==known,
                                    "pending execute ACTION must borrow its actual original observation lease");
                            requireFrame(frame,known);
                            return actionRequest(caller,frame.semantic(),lease.executableSteps(),frame.identity().frame().revision());
                        });
                        requested.set(request);
                        var decision=interactions.preparePublicPending(same,frame,request,deadline);
                        observed.set(decision.pending());
                        if(decision instanceof KnownInteractionsRuntimeInstaller.NewPending next)
                            return new RootApplicationSession.SubmitPublicAction<RawJson>(next.command());
                        var retained=(KnownInteractionsRuntimeInstaller.RetainedPending)decision;
                        return new RootApplicationSession.RetainPublicResult<RawJson>(interactions.publicPendingResult(
                                same,retained.original(),retained.pending(),retained.requested()));
                    },(receipt,archive,same)->interactions.publicPendingResult(same,receipt,
                            Objects.requireNonNull(observed.get()),Objects.requireNonNull(requested.get()).action()));
                },sources);
        return List.of(read,action);
    }

    static boolean query(OperationKey step){return QUERY.equals(Objects.requireNonNull(step).value());}
    static boolean action(OperationKey step){return ACTIONS.contains(Objects.requireNonNull(step).value());}

    /** Factual argument projection only. The original native contract and Root retain admission. */
    static InteractionDirectPublicCodec.PendingQuery queryRequest(PublicPlanningCodec.ExecuteRequest caller,
            OpportunityJson.Obj snapshot,Set<String> bridgeCapabilities,BigInteger currentRevision)throws IOException {
        Objects.requireNonNull(caller);Objects.requireNonNull(snapshot);Objects.requireNonNull(bridgeCapabilities);
        StrictJson.require(query(caller.step()),"not the exact pending-context execute step");
        if(!bridgeCapabilities.contains(QUERY_CAPABILITY))
            throw fault(PublicServiceFailure.Kind.UNSUPPORTED_STEP,"native DLL cannot query a pending interaction context");
        NativePendingInteraction.Pending pending=pending(snapshot);
        return new InteractionDirectPublicCodec.PendingQuery(new PendingId(pending.instanceId()),revision(caller,currentRevision));
    }

    /** Preserves missing/null/version fields and separates notification ACK from ordinary replies. */
    static PendingInteractionPublicCodec.Request actionRequest(PublicPlanningCodec.ExecuteRequest caller,
            OpportunityJson.Obj snapshot,Set<OperationKey> actualActionSteps,BigInteger currentRevision)throws IOException {
        Objects.requireNonNull(caller);Objects.requireNonNull(snapshot);Objects.requireNonNull(actualActionSteps);
        StrictJson.require(action(caller.step()),"not an exact pending-reply execute step");
        if(!actualActionSteps.contains(caller.step()))
            throw fault(PublicServiceFailure.Kind.UNSUPPORTED_STEP,"actual native action_steps do not advertise "+caller.step().value());
        NativePendingInteraction.Pending pending=pending(snapshot);
        boolean acknowledge=ACKNOWLEDGE.equals(caller.step().value());
        if(pending.autoAcceptNotification()!=acknowledge)throw fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                acknowledge?"CK3 pending character interaction is not an ACK notification":"CK3 pending character interaction requires acknowledgement");
        revision(caller,currentRevision);
        PendingInteractionPublicCodec.Field<BigInteger> expected=caller.expectedRevision() instanceof PublicPlanningCodec.RevisionMissing
                ?PendingInteractionPublicCodec.Field.missing():caller.expectedRevision() instanceof PublicPlanningCodec.RevisionNull
                ?PendingInteractionPublicCodec.Field.nullValue():PendingInteractionPublicCodec.Field.of(((PublicPlanningCodec.RevisionValue)caller.expectedRevision()).value());
        PendingId instance=new PendingId(pending.instanceId());
        return acknowledge?new PendingInteractionPublicCodec.Acknowledge(instance,expected)
                :new PendingInteractionPublicCodec.Reply(ACCEPT.equals(caller.step().value()),PendingInteractionPublicCodec.Field.of(instance),expected);
    }

    private static NativePendingInteraction.Pending pending(OpportunityJson.Obj snapshot) {
        try {
            return NativePendingInteraction.decode(OpportunityJson.toNode(snapshot).path("pending_character_interaction"))
                    .orElseThrow(()->fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"CK3 has no pending character interaction"));
        }catch(IllegalArgumentException invalid) {
            throw fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"CK3 pending character interaction lacks a valid signed full ID");
        }
    }
    private static BigInteger revision(PublicPlanningCodec.ExecuteRequest caller,BigInteger current) {
        Objects.requireNonNull(current);
        if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue value)
            if(!value.value().equals(current))throw fault(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                    "pending execute revision mismatch: expected "+value.value()+", current "+current);
        return current;
    }
    private static PublicServiceFailure fault(PublicServiceFailure.Kind kind,String reason) {
        return new PublicServiceFailure(kind,reason,Optional.empty());
    }
    private static void requireFrame(Complete frame,Known known) {
        Objects.requireNonNull(frame);Objects.requireNonNull(known);
        StrictJson.require(frame.identity().game().equals(known.stamp().game())
                &&frame.identity().frame().episodeRunId().equals(known.stamp().episodeRunId())
                &&frame.identity().frame().identity().player().equals(known.driver().session().actorId()),
                "pending execute must use the original actual Full Driver/Known actor and episode");
        known.observation().ifPresent(facts->StrictJson.require(frame.source().equals(facts.source())
                &&frame.sessionId().equals(facts.transport().sessionId())
                &&frame.identity().frame().snapshotId().equals(facts.snapshotId())
                &&frame.identity().frame().revision().equals(facts.publicRevision())
                &&frame.identity().frame().identity().nativeRevision().equals(facts.nativeRevision()),
                "pending execute Full Driver/Known original native observation differs"));
    }
    private static List<ExactRef> sources(RootInstalledCatalog actual,KnownInteractionsRuntimeInstaller installed)throws IOException {
        var result=new LinkedHashSet<ExactRef>();
        result.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootInteractionPublicStepProducts.class));
        result.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,KnownInteractionsRuntimeInstaller.class));
        result.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,RootInteractionContextProjection.class));
        result.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,InteractionDirectPublicCodec.class));
        result.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,PendingInteractionPublicCodec.class));
        result.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,PublicServiceFailure.class));
        result.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,InteractionCapabilities.class));
        result.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.CONTRACTS,NativePendingInteraction.class));
        result.add(installed.sources().nativeDefinitions().pending());result.add(installed.sources().readDecoder());
        result.add(installed.sources().effects());result.add(installed.sources().effectsDecoder());
        return List.copyOf(result);
    }
}
