package org.xar.ck3.control.application.lifecycle;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Private-mint domain evidence; JSON, expectedEpisode and observer DATA do not construct an action proof. */
public sealed interface LifecycleTransitionProof permits LifecycleTransitionProof.Death, LifecycleTransitionProof.ContinueSuccessor, LifecycleTransitionProof.NextEpisode, LifecycleTransitionProof.ActorSwitch, LifecycleTransitionProof.Recorded {
    enum Kind { DEATH, CONTINUE_SUCCESSOR, NEXT_EPISODE, ACTOR_SWITCH }
    Kind kind();
    void validateParent(ActionCommand parent);
    List<ExactRef> originalEvidence();
    byte[] encodedResult();
    default byte[] encode(){return LifecycleProofCodec.encode(this);}
    abstract sealed class Base permits Death, ContinueSuccessor, NextEpisode, ActorSwitch {
        final Object issuer;
        final ActionCommand parent;
        final LifecyclePublication publication;
        final List<ExactRef> evidence;
        final byte[] result;
        Base(Object issuer,ActionCommand parent,LifecycleCommit commit,List<ExactRef> evidence,byte[] result) {
            this.issuer=Objects.requireNonNull(issuer);this.parent=Objects.requireNonNull(parent);this.publication=new LifecyclePublication.Warm(Objects.requireNonNull(commit));
            this.evidence=List.copyOf(evidence);StrictJson.require(!this.evidence.isEmpty(),"original lifecycle evidence required");
            this.result=result.clone();LifecycleJson.parse(result,LifecycleProofCodec.MAX_RESULT_BYTES);
        }
        Base(Object issuer,ActionCommand parent,LifecyclePublication.RecordedEvent publication,List<ExactRef> evidence,byte[] result) {
            this.issuer=Objects.requireNonNull(issuer);this.parent=Objects.requireNonNull(parent);this.publication=Objects.requireNonNull(publication);
            this.evidence=List.copyOf(evidence);StrictJson.require(!this.evidence.isEmpty(),"original lifecycle evidence required");
            this.result=result.clone();LifecycleJson.parse(result,LifecycleProofCodec.MAX_RESULT_BYTES);
        }
        public final void validateParent(ActionCommand actual) {
            StrictJson.require(ActionCodec.bodySha256(parent).equals(ActionCodec.bodySha256(actual)),"lifecycle proof belongs to another complete parent command");
            String operation=switch(((LifecycleTransitionProof)this).kind()) {case DEATH->"death-terminal";case CONTINUE_SUCCESSOR->"continue-as-reconciled-successor";case NEXT_EPISODE->"start-next-episode";case ACTOR_SWITCH->parent.operation().value();};
            StrictJson.require(actual.operation().value().equals(operation),"wrong lifecycle proof branch");
            StrictJson.require(publication.detailsObject().get("parent_action_id").textValue().equals(actual.actionId()),"lifecycle commit belongs to another parent");
        }
        public final List<ExactRef> originalEvidence(){return evidence;}
        public final LifecycleCommit commit(){return publication.warmCommit().orElseThrow(()->new IllegalStateException("recorded cold publication has no warm Prepared"));}
        public final LifecyclePublication publication(){return publication;}
        public final byte[] encodedResult(){return result.clone();}
    }
    final class Death extends Base implements LifecycleTransitionProof {
        Death(Object issuer,ActionCommand parent,LifecycleCommit commit,List<ExactRef> evidence,byte[] result){super(issuer,parent,commit,evidence,result);}
        @Override public Kind kind(){return Kind.DEATH;}
    }
    final class ContinueSuccessor extends Base implements LifecycleTransitionProof {
        ContinueSuccessor(Object issuer,ActionCommand parent,LifecyclePublication.RecordedEvent publication,List<ExactRef> evidence,byte[] result){super(issuer,parent,publication,evidence,result);}
        ContinueSuccessor(Object issuer,ActionCommand parent,LifecycleCommit commit,List<ExactRef> evidence,byte[] result){super(issuer,parent,commit,evidence,result);}
        @Override public Kind kind(){return Kind.CONTINUE_SUCCESSOR;}
    }
    final class NextEpisode extends Base implements LifecycleTransitionProof {
        NextEpisode(Object issuer,ActionCommand parent,LifecycleCommit commit,List<ExactRef> evidence,byte[] result){super(issuer,parent,commit,evidence,result);}
        @Override public Kind kind(){return Kind.NEXT_EPISODE;}
    }
    final class ActorSwitch extends Base implements LifecycleTransitionProof {
        ActorSwitch(Object issuer,ActionCommand parent,LifecycleCommit commit,List<ExactRef> evidence,byte[] result){super(issuer,parent,commit,evidence,result);}
        @Override public Kind kind(){return Kind.ACTOR_SWITCH;}
    }
    /** Strict immutable representation of already recorded facts. Decoding gives no submitter, child or grant. */
    final class Recorded implements LifecycleTransitionProof {
        final Kind kind; final String parentId,bodySha,operation,eventIdentity;
        final List<org.xar.ck3.control.continuity.writer.WriterContracts.Pin> documents;
        final List<ExactRef> evidence; final byte[] result;
        Recorded(Kind kind,String parentId,String bodySha,String operation,String eventIdentity,
                List<org.xar.ck3.control.continuity.writer.WriterContracts.Pin> documents,List<ExactRef> evidence,byte[] result){
            this.kind=kind;this.parentId=parentId;this.bodySha=bodySha;this.operation=operation;this.eventIdentity=eventIdentity;
            this.documents=List.copyOf(documents);this.evidence=List.copyOf(evidence);this.result=result.clone();
        }
        @Override public Kind kind(){return kind;}
        @Override public void validateParent(ActionCommand actual){StrictJson.require(parentId.equals(actual.actionId())&&bodySha.equals(ActionCodec.bodySha256(actual))&&operation.equals(actual.operation().value()),"recorded lifecycle scope differs");}
        @Override public List<ExactRef> originalEvidence(){return evidence;}
        @Override public byte[] encodedResult(){return result.clone();}
    }
}
