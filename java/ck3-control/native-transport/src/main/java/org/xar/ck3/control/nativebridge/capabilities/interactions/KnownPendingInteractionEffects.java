package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Native pending producer -> independent Driver/custody observations -> same-writer original replay. */
public final class KnownPendingInteractionEffects implements NativeEffectRegistry.Observer,ActionPorts.PreparationPort {
    private record Prepared(InteractionModels.Context context,Plan plan) { }
    private final NativeEffectSnapshots snapshots;
    private final PlanningReadPort reads;
    private final ReadContract<RawJson> custody;
    public KnownPendingInteractionEffects(NativeEffectSnapshots actualSnapshots,PlanningReadPort actualReads,
            ReadContract<RawJson> actualPrisonerCollectionZero) {
        snapshots=Objects.requireNonNull(actualSnapshots);reads=Objects.requireNonNull(actualReads);
        custody=Objects.requireNonNull(actualPrisonerCollectionZero);
        need(custody.operation().value().equals(PrisonerNativeQueries.STEP)
                &&custody.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                "actual canonical complete prisoner collection contract zero required");
    }
    public List<NativeEffectRegistry.Binding> bindings(ExactRef actualSource) {
        need(actualSource.bytes()>0,"actual pending effect producer source required");
        return java.util.Arrays.stream(Action.values()).map(action->new NativeEffectRegistry.Binding(
                new OperationKey(action.step()),actualSource,this,this)).toList();
    }
    @Override public NativeRequest prepare(ActionCommand command) {
        return nativeRequest(command);
    }
    /** The exact same producer is shared by Root registration and serialization regressions. */
    public static ActionPorts.PreparationPort preparation() { return KnownPendingInteractionEffects::nativeRequest; }
    private static NativeRequest nativeRequest(ActionCommand command) {
        Prepared prepared=prepared(command);
        ObjectNode fields=F.objectNode().put("pending_interaction_id",prepared.context().controls().pending().instance().value());
        return new NativeRequest(command.operation().value(),"game.command."+command.operation().value(),encode(fields));
    }
    private static Prepared prepared(ActionCommand command) {
        Objects.requireNonNull(command);
        ObjectNode args=InteractionArguments.parseApp(command.arguments());
        eq(args,"mutation_kind","PENDING_REPLY");
        InteractionModels.Context context=InteractionArguments.context(command);
        var pending=context.controls().pending();
        need(context.controls().paused()&&context.controls().mapReady()&&pending!=null,
                "actual paused current pending frame required");
        eq(args,"pending_id",BigInteger.valueOf(pending.instance().value()));
        ObjectNode artifact=object(field(args,"known_pending_plan"));
        Plan plan=KnownPendingInteractionPlanCodec.decode(field(artifact,"java_policy_plan"));
        Action action=plan.selected().orElseThrow(()->new IllegalArgumentException("blocked known plan cannot prepare a reply"));
        need(action.step().equals(command.operation().value()),"stored known selection changed its exact operation");
        need(bool(args,"accept")== (action==Action.ACCEPT)&&bool(args,"acknowledge")== (action==Action.ACKNOWLEDGE),
                "known action flags differ from the exact primitive");
        need(pending.autoAcceptNotification()==(action==Action.ACKNOWLEDGE),"pending reply channel differs from current window");
        JsonNode summary=field(artifact,"pending_character_interaction");
        eq(summary,"instance_id",BigInteger.valueOf(pending.instance().value()));
        eq(summary,"sender_character_id",BigInteger.valueOf(pending.sender().value()));
        JsonNode binding=field(summary,"frame_binding");
        eq(binding,"snapshot_id",command.before().frame().snapshotId());
        eq(binding,"public_revision",command.before().frame().revision());
        eq(binding,"native_revision",context.revision());eq(binding,"date_raw",context.date());
        eq(binding,"pending_interaction_id",BigInteger.valueOf(pending.instance().value()));
        need(command.expected().equals(KnownPendingInteractionPostcondition.expected(command.before(),command.source(),plan)),
                "known pending expected effect differs from the selected policy contract");
        if(action!=Action.ACKNOWLEDGE&&plan.classification()!=Classification.EXPLICIT_NATIVE_REPLY) {
            ObjectNode wrapper=object(field(artifact,"original_context_wrapper"));
            need(KnownPendingInteractionEvidence.equalText(wrapper.get("queried_snapshot_id"),command.before().frame().snapshotId())
                    &&KnownPendingInteractionEvidence.equalInt(wrapper.get("queried_revision"),command.before().frame().revision())
                    &&KnownPendingInteractionEvidence.equalInt(wrapper.get("queried_native_revision"),context.revision()),
                    "known pending original context crossed public/native frame binding");
            PendingContext original=PendingContextCodec.decode(encode(wrapper),context,pending.instance());
            need(original.status()==PendingContext.Status.AVAILABLE&&KnownPendingInteractionRules.classify(original)==plan.classification()
                    &&original.roles().actor()==pending.sender().value(),"known plan classification or sender differs from original context");
            PendingContext.Legal legal=action==Action.ACCEPT?original.legality().accept():original.legality().reject();
            need(legal.available()&&legal.allowed(),"stored original exact native reply legality required");
        }
        return new Prepared(context,plan);
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch) {
        Prepared selected=prepared(command);
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty())
            return NativeEffectRegistry.Projected.pending("original Native reply result is unknown; do not replay",List.of(attempt.guard().nativeEvidence()));
        NativeEffectSnapshots.Pair pair=snapshots.read(command,attempt);
        List<PlanningReadReceipt> actualReads=new ArrayList<>();
        Optional<KnownPendingInteractionPostcondition.PrisonerAfter> prisoners=Optional.empty();
        if(selected.plan().classification()==Classification.KNOWN_RECEIVED_RANSOM) {
            var after=pair.after();
            PlanningReadResult<RawJson> read=reads.read(custody,new PlanningReadRequest(after.identity(),after.source(),after.sessionId(),
                    custody.operation(),PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(),OptionalLong.empty()),ActionObservationWindow.deadline(command)));
            if(read instanceof PlanningReadResult.Known<RawJson> known) {
                NativeEffectSnapshots.requireAfterRead(command,attempt,after,known.receipt(),custody.operation());
                var decoded=PrisonerNativeQueries.decode(known.receipt(),0);
                if(decoded.releaseProjection().isPresent()) {
                    prisoners=Optional.of(new KnownPendingInteractionPostcondition.PrisonerAfter(after.identity(),decoded.releaseProjection().orElseThrow()));
                    actualReads.add(known.receipt());
                }
            }
        }
        var projected=project(command,attempt,dispatch,pair,prisoners);
        if(!(projected.result() instanceof ActionPorts.EffectObserved))return projected;
        ExactRef evidence=snapshots.evidence(command,attempt,pair,actualReads,projected.compatibleResult().orElseThrow());
        return NativeEffectSnapshots.withEvidence(projected,List.of(evidence));
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,NativeEffectSnapshots.Pair pair,
            Optional<KnownPendingInteractionPostcondition.PrisonerAfter> prisoners) {
        Prepared selected=prepared(command);
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty())
            return NativeEffectRegistry.Projected.pending("original Native reply result is unknown; do not replay",List.of(pair.after().originalEvidence()));
        var verified=KnownPendingInteractionPostcondition.verify(new KnownPendingInteractionPostcondition.Input(selected.plan(),
                pair.before().identity(),pair.after().identity(),pair.before().semantic(),pair.after().semantic(),
                ack.originalResultToken().orElseThrow(),prisoners));
        if(!verified.verified())return NativeEffectRegistry.Projected.pending(
                "known reply independent effect incomplete: "+String.join(", ",verified.missing()),List.of(pair.after().originalEvidence()));
        return NativeEffectSnapshots.observed(command,attempt,pair.after(),KnownPendingInteractionPostcondition.SCHEMA,verified.actual(),
                NativeEffectSnapshots.publication(pair.after()),new RawJson(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(verified.compatibleResult())),List.of());
    }
    public static List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers(ExactRef actualSource,NativeEffectEvidence.FrameLoader frames) {
        Objects.requireNonNull(frames);need(actualSource.bytes()>0,"actual archived pending verifier source required");
        return java.util.Arrays.stream(Action.values()).map(action->new NativeRecordedEvidenceVerifier.Binding(new OperationKey(action.step()),actualSource,
                (head,receipt,archive)-> {
                    NativeEffectEvidence.Original original=NativeEffectEvidence.load(receipt,archive,frames);
                    var settled=(ActionState.Settled)receipt.state();
                    Prepared selected=prepared(receipt.command());
                    Optional<KnownPendingInteractionPostcondition.PrisonerAfter> prisoners=Optional.empty();
                    if(selected.plan().classification()==Classification.KNOWN_RECEIVED_RANSOM) {
                        need(original.independentReads().size()==1,"received ransom needs its single actual complete custody observation");
                        PlanningReadReceipt read=original.independentReads().getFirst();
                        NativeEffectSnapshots.requireAfterRead(receipt.command(),settled.attempt(),original.frames().after(),read,
                                new OperationKey(PrisonerNativeQueries.STEP));
                        var collection=PrisonerNativeQueries.decode(read,0).releaseProjection().orElseThrow(
                                ()->new IllegalArgumentException("archived custody projection unavailable"));
                        prisoners=Optional.of(new KnownPendingInteractionPostcondition.PrisonerAfter(original.frames().after().identity(),collection));
                    } else need(original.independentReads().isEmpty(),"ordinary pending lifecycle has no substitute independent read");
                    NativeEffectRegistry.Projected replayed=project(receipt.command(),settled.attempt(),settled.dispatch(),original.frames(),prisoners);
                    replayed=NativeEffectSnapshots.withEvidence(replayed,((ActionState.Applied)settled.settlement()).observation().supportingEvidence());
                    NativeEffectEvidence.requireSame(settled.settlement(),replayed,original.compatibleResult());
                })).toList();
    }
}
