package org.xar.ck3.control.nativebridge.capabilities.army;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.military.ActiveRetreatPost;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Real child-primitive observer adapter. The parent later replays these originals; it never borrows primitive permission. */
public final class ArmyRetreatReconciliationPost implements ArmyRetreatPostReadCollector {
    public record Scope(ContinuityStorePort.Session same,ReconciliationIdentity identity,Complete actual,Instant deadline){
        public Scope{Objects.requireNonNull(same);Objects.requireNonNull(identity);Objects.requireNonNull(actual);Objects.requireNonNull(deadline);require(actual.identity().equals(identity.factual())&&actual.source().equals(identity.source())&&actual.sessionId().equals(identity.sessionId())&&actual.connectionGeneration().equals(identity.connectionGeneration()),"retreat post scope facts crossed actual reconciliation identity");}
    }
    @FunctionalInterface public interface Current {
        /** Root must borrow currentForCommand from the original private active primitive observer lease. */
        Scope require(ActionCommand original,ActionState.Attempt attempt);
    }
    private final ArmyBattleReconciliationReads reads;private final Supplier<RootReadContractCatalog> catalog;private final Current current;
    public ArmyRetreatReconciliationPost(ArmyBattleReconciliationReads reads,Supplier<RootReadContractCatalog> catalog,Current actualCurrent){this.reads=Objects.requireNonNull(reads);this.catalog=Objects.requireNonNull(catalog);current=Objects.requireNonNull(actualCurrent);}
    /** These exact two possible reads are installed before dispatch; terminal executes only if actual transition requires it. */
    public static List<ArmyBattleReconciliationReads.Selection> selections(ActionCommand command,ReconciliationIdentity identity,Instant deadline){
        var request=ArmyRetreatMoveRequest.decode(command.arguments());var context=new Context(identity.factual(),identity.source(),identity.sessionId(),deadline);var revision=new ArmyCalls.Revision(new Present<>(identity.factual().frame().revision()));
        var transition=new ArmyCalls.CombatId(PublicMethod.QUERY_BATTLE_TRANSITION_V1,revision,new FullId(request.order().arguments().expectedCombatId()));
        return List.of(new ArmyBattleReconciliationReads.Selection(identity,transition,deadline),new ArmyBattleReconciliationReads.Selection(identity,ArmyRetreatDomain.terminalCall(request.order(),context),deadline));
    }
    @Override public List<PlanningReadReceipt> collect(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair frames,OutcomeArchive archive){
        Scope scope=Objects.requireNonNull(current.require(command,attempt));bind(command,attempt,frames,scope.identity());
        var selections=selections(command,scope.identity(),scope.deadline());var originals=new ArrayList<PlanningReadReceipt>();
        originals.add(reads.read(scope.same(),Objects.requireNonNull(catalog.get()),selections.getFirst()).receipt());
        var result=verifyArchived(command,attempt,frames,originals,archive);
        if(result instanceof ActiveRetreatPost.Pending pending&&pending.terminalQueryRequired()){
            var terminal=reads.collect(scope.same(),Objects.requireNonNull(catalog.get()),selections.getLast());
            if(terminal instanceof PlanningReadResult.Known<ArmyBattleReads.Observation> known)originals.add(known.receipt());
        }
        verifyArchived(command,attempt,frames,originals,archive);return List.copyOf(originals);
    }
    @Override public ActiveRetreatPost.Result verifyArchived(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair frames,List<PlanningReadReceipt> post,OutcomeArchive archive){
        require(!post.isEmpty()&&post.size()<=2,"retreat post requires one original transition plus conditional terminal");
        var identity=post.getFirst().request().origin().requireReconciliation();bind(command,attempt,frames,identity);
        for(var receipt:post){NativeRecordedEvidenceVerifier.requireRead(receipt,archive);require(receipt.request().origin() instanceof CommandOrigin.Reconciliation&&receipt.request().origin().requireReconciliation().sameGuardFrame(identity),"retreat independent post crossed original primitive/factual scope");}
        var original=ArmyRetreatMoveRequest.decode(command.arguments());
        return ArmyRetreatDomain.post(original.order(),new ArmyRetreatFrames.Current(frames.after(),post.getFirst().request().deadline()),post);
    }
    private static void bind(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair frames,ReconciliationIdentity identity){
        require(command.expected().observerSchema().equals("xar.ck3.native-active-retreat-move-postcondition/v1"),"ordinary move cannot collect retreat lifecycle reads");
        var original=ArmyRetreatMoveRequest.decode(command.arguments());var pending=identity.pending();
        require(pending.actionId().equals(command.actionId())&&pending.bodySha256().equals(ActionCodec.bodySha256(command))&&pending.requestId().equals(attempt.requestId())&&pending.originalBefore().equals(command.before()),"retreat post borrowed another primitive's actual pending identity");
        require(frames.before().identity().equals(command.before())&&frames.before().originalEvidence().equals(attempt.guard().nativeEvidence())&&frames.before().source().equals(command.source())&&frames.before().sessionId().equals(command.sessionId()),"retreat post before differs from original child/Attempt");
        require(frames.after().identity().equals(identity.factual())&&frames.after().source().equals(identity.source())&&frames.after().sessionId().equals(identity.sessionId())&&frames.after().connectionGeneration().equals(identity.connectionGeneration())&&frames.after().originalEvidence().equals(identity.nativeEvidence()),"retreat post actual after frame differs from live/archived reconciliation originals");
        require(original.order().source().episodeRunId().equals(identity.factual().frame().episodeRunId()),"retreat post changed original episode");
    }
}
