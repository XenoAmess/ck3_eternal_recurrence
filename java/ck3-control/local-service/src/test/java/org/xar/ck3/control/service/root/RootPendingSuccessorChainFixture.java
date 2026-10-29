package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.lifecycle.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * Real producer-to-consumer choreography. Inputs must come from the actual startup and private M3 pending
 * producer. This helper creates no Managed Game, canonical publication, pending/final token or permission.
 * Missing actual inputs remain MISSING_NOT_RUN; these methods are not standalone passing unit tests.
 */
public final class RootPendingSuccessorChainFixture {
    private RootPendingSuccessorChainFixture(){ }
    public record Step(ActionReceipt original,CompositeContinuationReport actual,
            DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after,WriterContracts.Head head) {
        public Step {Objects.requireNonNull(original);Objects.requireNonNull(actual);Objects.requireNonNull(before);
            Objects.requireNonNull(after);Objects.requireNonNull(head);}
    }
    private record Current(ActionReceipt parent,DriverSnapshotFacts.Known known,WriterContracts.Head head){ }

    /** Tests that identical public token fields cannot replace the real private issuer identity. */
    public static void copiedCarrierCannotAuthorizeAChild(RootApplicationAssembly.Core core,
            RootApplicationSession root,NaturalSuccessionPreparation.PendingToken actual)throws IOException {
        requireOwner(core,root,actual);var before=current(core,root,actual.originalParent().actionId());
        if(!(before.parent().state() instanceof ActionState.CompositeUnknown))
            throw new IOException("actual private pending fixture requires the retained unresolved original parent");
        var copied=new NaturalSuccessionPreparation.PendingToken(){
            public ActionCommand originalParent(){return actual.originalParent();}
            public Instant deadline(){return actual.deadline();}
            public CompositeContinuationToken.Kind kind(){return actual.kind();}
            public SuccessorUiObligation obligation(){return actual.obligation();}
            public ExactRef canonicalDomain(){return actual.canonicalDomain();}
            public ExactRef actualPublishedDriver(){return actual.actualPublishedDriver();}
            public ExactRef canonicalPublicationProof(){return actual.canonicalPublicationProof();}
            public List<ExactRef> evidence(){return actual.evidence();}
        };
        boolean refused=false;
        try{root.continueOriginalComposite(copied);}
        catch(IOException|IllegalArgumentException|IllegalStateException expected){refused=true;}
        if(!refused)throw new IOException("a copied DATA carrier was not rejected by the actual private pending source");
        var after=current(core,root,actual.originalParent().actionId());requireUnchanged(before,after);
    }

    /** Runs exactly one actual finite continuation. No event/Close retry or replacement is synthesized. */
    public static Step continueOnce(RootApplicationAssembly.Core core,RootApplicationSession root,
            NaturalSuccessionPreparation.PendingToken actual)throws IOException {
        requireOwner(core,root,actual);var before=current(core,root,actual.originalParent().actionId());
        if(!(before.parent().state() instanceof ActionState.CompositeUnknown unknown))
            throw new IOException("actual original pending parent is not UNKNOWN");
        var result=root.continueOriginalComposite(actual);
        var after=current(core,root,actual.originalParent().actionId());
        int maximumPrimitives=actual.kind()==CompositeContinuationToken.Kind.SUCCESSOR_UI_DATE_ADVANCE?3:1;
        if(!result.parent().equals(after.parent())
                ||!Arrays.equals(ActionCodec.encodeCommand(before.parent().command()),ActionCodec.encodeCommand(after.parent().command()))
                ||result.children().size()>maximumPrimitives)
            throw new IOException("finite continuation changed its original canonical parent or exceeded its closed primitive family");
        var finalCursor=ActionTransitions.composite(after.parent().state()).orElseThrow(
                ()->new IOException("actual original parent lost its retained composite cursor"));
        if(finalCursor.children().size()<unknown.execution().children().size()
                ||finalCursor.children().size()>unknown.execution().children().size()+1)
            throw new IOException("actual continuation discarded an original child or appended more than one top-level child");
        for(int index=0;index<unknown.execution().children().size();index++)
            if(!unknown.execution().children().get(index).equals(finalCursor.children().get(index)))
                throw new IOException("actual continuation rewrote an old child identity or ordinal");
        if(before.known().stamp().episodeEpoch()!=after.known().stamp().episodeEpoch()
                ||!before.known().stamp().game().equals(after.known().stamp().game())
                ||!before.known().driver().session().equals(after.known().driver().session()))
            throw new IOException("pending finalization repeated successor adoption or changed its already-adopted actor/run/epoch");
        var originalHistory=before.known().driver().commandHistory();var currentHistory=after.known().driver().commandHistory();
        if(currentHistory.size()<originalHistory.size())throw new IOException("actual continuation lost original full history");
        for(int index=0;index<originalHistory.size();index++)
            if(!Arrays.equals(originalHistory.get(index).originalRow().json(),currentHistory.get(index).originalRow().json()))
                throw new IOException("actual continuation rewrote original full history");
        if(after.parent().settled()){
            if(!(after.parent().state() instanceof ActionState.CompositeSettled settled)
                    ||!(settled.settlement() instanceof ActionState.LifecycleApplied applied)
                    ||applied.proof().kind()!=LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR)
                throw new IOException("pending UI cannot settle through an ACK or a non-lifecycle result");
            var registry=after.head().state().toJson().path(LifecycleContinuityAuthority.STATE_FIELD).path("transitions");
            var transition=registry.path(after.parent().command().actionId());
            if(!LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED.name().equals(transition.path("phase").asText())
                    ||!transition.path("driver_snapshot").path("expected_epoch").equals(transition.path("driver_snapshot").path("next_epoch")))
                throw new IOException("actual pending successor did not use the canonical metadata-only finalization branch");
            var decoded=LifecycleProofCodec.decodeRecorded(applied.proof().encode());decoded.validateParent(before.parent().command());
            if(!Arrays.equals(decoded.encode(),applied.proof().encode()))
                throw new IOException("actual finalized lifecycle proof lost its recorded source domain during serde");
        }else if(!(after.parent().state() instanceof ActionState.CompositeUnknown))
            throw new IOException("pending continuation lifted quarantine before real final lifecycle publication");
        return new Step(before.parent(),result,before.known(),after.known(),after.head());
    }

    private static void requireOwner(RootApplicationAssembly.Core core,RootApplicationSession root,
            NaturalSuccessionPreparation.PendingToken actual)throws IOException{
        Objects.requireNonNull(core);Objects.requireNonNull(root);Objects.requireNonNull(actual);
        if(!root.ownedBy(core)||root.writer()!=core.writer()||root.archive()!=core.archive()
                ||root.isRetired()||core.sessionAccess().current()!=root
                ||!actual.originalParent().origin().game().equals(root.identity().game())
                ||!actual.originalParent().sessionId().equals(root.identity().sessionId()))
            throw new IOException("actual private pending fixture requires the original current same-Core Root");
    }
    private static Current current(RootApplicationAssembly.Core core,RootApplicationSession root,String id)throws IOException{
        try{return core.withBorrowed(()->{
            var same=core.writer().borrowedSession();
            return root.driver().authority().withFrozenFacts(same,frozen->{
                if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))
                    throw new IOException("actual complete pending Driver is unavailable");
                var parent=frozen.actions().actions().stream().filter(row->row.command().actionId().equals(id)).findFirst()
                        .orElseThrow(()->new IOException("actual canonical pending parent is absent"));
                return new Current(parent,known,same.head());
            });
        });}catch(InterruptedException interrupted){
            Thread.currentThread().interrupt();throw new IOException("actual pending fixture read was interrupted",interrupted);
        }
    }
    private static void requireUnchanged(Current before,Current after)throws IOException{
        if(!before.parent().equals(after.parent())||!before.known().stamp().equals(after.known().stamp())
                ||!Arrays.equals(before.known().driver().encode(),after.known().driver().encode())
                ||!before.head().digest().equals(after.head().digest())
                ||!before.head().documents().equals(after.head().documents())
                ||!before.head().absent().equals(after.head().absent())
                ||!before.head().indexRepairs().equals(after.head().indexRepairs())
                ||before.head().snapshotNeedsRecovery()!=after.head().snapshotNeedsRecovery())
            throw new IOException("a rejected copied pending token changed the actual canonical Driver/parent/Head");
    }
}
