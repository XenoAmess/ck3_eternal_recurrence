package org.xar.ck3.control.application.driver;

import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.driver.DriverPendingEpisodeSource.*;

/** One deterministic DATA projection shared by Root precommit and the sole Driver CAS verifier. */
public final class DriverPendingEpisodeMutations {
    private DriverPendingEpisodeMutations(){ }
    public record Projection(DriverStateSnapshot.Complete driver,OpportunityJson.Obj auxiliary,
            SuccessorUiObligation obligation,Optional<RawJson> result) {
        public Projection {Objects.requireNonNull(driver);Objects.requireNonNull(auxiliary);Objects.requireNonNull(obligation);Objects.requireNonNull(result);}
    }
    public record Prepared(Projection projection,ExactRef beforeDriver,ExactRef afterDriver,ExactRef afterAuxiliary,
            ExactRef beforeObligation,ExactRef afterObligation,Optional<ExactRef> originalResult) {
        public Prepared {Objects.requireNonNull(projection);Objects.requireNonNull(beforeDriver);Objects.requireNonNull(afterDriver);
            Objects.requireNonNull(afterAuxiliary);Objects.requireNonNull(beforeObligation);Objects.requireNonNull(afterObligation);Objects.requireNonNull(originalResult);}
    }
    public static Projection project(DriverSnapshotFacts.Known current,SuccessorUiObligation before,Change change) {
        Objects.requireNonNull(current);Objects.requireNonNull(before);Objects.requireNonNull(change);
        var retained=SuccessorUiObligationCodec.decode(DriverJson.encode(current.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));
        StrictJson.require(retained.equals(before)&&before.blocksOrdinaryActionsAndSave()
                &&current.stamp().game().equals(before.binding().predecessor().game())
                &&current.stamp().episodeEpoch()==Math.addExact(before.binding().predecessor().subject().episodeEpoch(),1)
                &&current.driver().session().actorId().equals(before.binding().successorCharacterId())
                &&current.driver().session().episodeRunId().equals(before.binding().successorEpisodeRunId()),
                "pending mutation lost its actual current new subject and canonical obligation");
        SuccessorUiObligation after;
        if(change instanceof Observe value)after=SuccessorUiObligationReducer.observe(before,value.value());
        else if(change instanceof EnterClose value)after=SuccessorUiObligationReducer.enterClose(before,value.value());
        else if(change instanceof RetainResult value)after=SuccessorUiObligationReducer.retainCloseReceipt(before,value.value());
        else if(change instanceof RetainPostconditions value)after=SuccessorUiObligationReducer.retainClosePostconditions(before,value.value());
        else if(change instanceof Reconcile value)after=SuccessorUiObligationReducer.retainVerifiedReconciliation(before,value.value());
        else if(change instanceof Rebind value)after=SuccessorUiObligationReducer.rebind(before,value.value());
        else if(change instanceof Finalize value) {
            var observed=SuccessorUiObligationReducer.observe(before,value.currentObservation());
            var reduction=SuccessorUiObligationReducer.finalEpisode(current,observed,value.value(),value.currentFrame(),value.matchedEstate(),value.observedAtUtc());
            after=SuccessorUiObligationCodec.decode(DriverJson.encode(reduction.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));
            StrictJson.require(!after.blocksOrdinaryActionsAndSave()&&after.binding().equals(before.binding())
                    &&reduction.driver().session().equals(current.driver().session())
                    &&reduction.driver().commandHistory().equals(current.driver().commandHistory()),
                    "final pending projection must preserve the actual new episode/history and genuinely complete its obligation");
            return new Projection(reduction.driver(),reduction.auxiliary(),after,Optional.of(new RawJson(reduction.result())));
        } else throw new IllegalArgumentException("unknown finite pending mutation");
        StrictJson.require(after.blocksOrdinaryActionsAndSave(),"only genuine final M3 projection can lift the pending gate");
        return new Projection(current.driver(),SuccessorUiObligationReducer.withState(current.auxiliary(),after),after,Optional.empty());
    }
    /** Retains exact projection originals before the real Root domain commit; this supplies no publication token. */
    public static Prepared prepare(DriverSnapshotFacts.Known current,SuccessorUiObligation before,Change change,OutcomeArchive originals) {
        var projection=project(current,before,change);
        return new Prepared(projection,originals.materialReferenceOf(new RawJson(current.driver().encode())),
                retain(originals,new RawJson(projection.driver().encode())),retain(originals,new RawJson(DriverJson.encode(projection.auxiliary()))),
                originals.materialReferenceOf(new RawJson(SuccessorUiObligationCodec.encode(before))),
                retain(originals,new RawJson(SuccessorUiObligationCodec.encode(projection.obligation()))),
                projection.result().map(value->retain(originals,value)));
    }
    private static ExactRef retain(OutcomeArchive originals,RawJson body) {
        ExactRef ref=originals.preserveMaterial(body);
        StrictJson.require(ref.equals(originals.materialReferenceOf(body))&&Arrays.equals(originals.loadMaterial(ref).bytes(),body.bytes()),
                "pending mutation original differs from its actual projection");return ref;
    }
}
