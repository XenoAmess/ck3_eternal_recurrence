package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.governance.OrdinaryFeastPolicy;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.m6.ActivityFinalState;
import org.xar.ck3.control.g2.m6.ActivityFinalStateCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;

/** Actual Start material -> one shared hosted decoder -> M6 reducer. No missing-instance terminal inference. */
public final class FeastFinalSettlement {
    private final RootRuntimeContext context;
    private final GovernanceActivityRuntime activity;
    private final RootActivityFinalReadBridge bridge;
    public FeastFinalSettlement(RootRuntimeContext actual,GovernanceActivityRuntime activity) {
        context=java.util.Objects.requireNonNull(actual);this.activity=java.util.Objects.requireNonNull(activity);
        bridge=new RootActivityFinalReadBridge(activity.definitions(),context.archive(),context.frameLoader());
    }
    public Optional<FeastDomainRuntime.FinalRetention> observe(ContinuityStorePort.Session same,
            PlanningRequest request,FeastDomainRuntime.ActivityOrigin origin)throws IOException {
        var start=requireStart(same,origin.originalStart());var effect=ActionEffects.observation(start).orElseThrow();
        // An old physical Game requires the central saved-source adoption proof before a new live sample can join it.
        if(!effect.after().game().equals(request.before().game()))return Optional.empty();
        context.writer().requireSession(same);context.requireCurrent(request.deadline());
        StrictJson.require(request.before().game().equals(context.game().generation())&&request.source().equals(context.source())&&request.sessionId().equals(context.game().sessionId()),"actual final planning Game/source/session differs");
        var before=origin.finalState().isPresent()?restore(same,origin):ActivityFinalState.empty(identity(start),effect.after());
        if(before.firstFinal().isPresent())return Optional.empty();
        final ActivityNativeContracts.Packet packet;
        try{packet=activity.hosted(same,request);}catch(IOException unavailable){return Optional.empty();}
        var observed=bridge.observe(before,packet,request.before(),same);
        if(observed.state().firstFinal().isEmpty())return Optional.empty();
        byte[] encoded=ActivityFinalStateCodec.encode(observed.state());var original=context.archive().preserveArtifact(same,encoded,1_048_576);
        return Optional.of(new FeastDomainRuntime.FinalRetention(original,observed.state().identity().activityFullId(),observed.state().identity().hostCharacterId()));
    }
    public ActivityFinalState.State restoreArtifact(ContinuityStorePort.Session same,ExactRef artifact)throws IOException {
        return bridge.restore(context.archive().readArtifact(same,artifact,131072),same);
    }
    /** Mandatory during owning finance reads and every final-state import, including cold original replay. */
    public ActivityFinalState.State restore(ContinuityStorePort.Session same,FeastDomainRuntime.ActivityOrigin origin)throws IOException {
        var start=requireStart(same,origin.originalStart());var retained=origin.finalState().orElseThrow(()->new IOException("no retained final original"));
        byte[] bytes=context.archive().readArtifact(same,retained.state(),1_048_576);var state=bridge.restore(bytes,same);
        var effect=ActionEffects.observation(start).orElseThrow();
        StrictJson.require(state.identity().equals(identity(start))&&state.origin().equals(effect.after())
                &&state.identity().activityFullId()==retained.activityFullId()&&state.identity().hostCharacterId()==retained.hostCharacterId()
                &&state.firstFinal().isPresent(),"retained Feast terminal crossed its original actual Start material");return state;
    }
    public ActionReceipt requireStart(ContinuityStorePort.Session same,ExactRef reference)throws IOException {
        context.writer().requireSession(same);var archive=context.archive().withSession(same);var start=archive.loadReceipt(reference);
        var canonical=ContinuityActionJournal.lookup(same.head().state(),start.command().actionId(),archive).orElseThrow(()->new IOException("original Feast Start absent from canonical history"));
        StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(start,archive),ActionReceiptCodec.encodeReceipt(canonical,archive))
                &&start.command().operation().equals(OrdinaryFeastPolicy.START)&&start.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                &&start.state() instanceof ActionState.Settled,"final Activity origin must be exact canonical material Start");
        var settled=(ActionState.Settled)start.state();ActionEffects.validate(start.command(),settled.attempt(),settled.settlement());
        context.bindings().actualArchivedVerifier(OrdinaryFeastPolicy.START).orElseThrow(()->new IOException("actual Feast Start replay verifier absent")).verifier().verify(same.head(),start,archive);
        identity(start);return start;
    }
    private static ActivityFinalState.Identity identity(ActionReceipt start) {
        var effect=ActionEffects.observation(start).orElseThrow();
        return new ActivityFinalState.Identity(start.command().actionId(),number(effect,"feast.activity_id"),number(effect,"feast.host_character_id"),"activity_feast");
    }
    private static long number(ActionState.EffectObservation effect,String key) {
        var selected=effect.actual().stream().filter(value->value.field().value().equals(key)).toList();
        StrictJson.require(selected.size()==1&&selected.getFirst() instanceof ExpectedInteger,"exact material Feast ID missing or duplicated");
        return ((ExpectedInteger)selected.getFirst()).value().longValueExact();
    }
}
