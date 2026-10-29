package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Historical source qualification only. Every branch preserves the actual saved body; none adopts a native instance. */
public sealed interface RestoredFeastOriginal permits RestoredFeastOriginal.NoOriginal,RestoredFeastOriginal.Unqualified,RestoredFeastOriginal.Historical {
    record NoOriginal(ExactRef restorationBasis,DomainBodies.BodyRef savedFeastMember) implements RestoredFeastOriginal {
        public NoOriginal {Objects.requireNonNull(restorationBasis);Objects.requireNonNull(savedFeastMember);}
    }
    enum Reason { SAVED_FEAST_UNAVAILABLE,PENDING_OR_UNKNOWN,FIRST_NATIVE_CONTINUITY_UNPROVEN,ORIGINAL_REPLAY_UNAVAILABLE }
    record Unqualified(Reason reason,String detail,List<ExactRef> originals) implements RestoredFeastOriginal {
        public Unqualified {Objects.requireNonNull(reason);StrictJson.text(detail);originals=List.copyOf(originals);StrictJson.require(!originals.isEmpty(),"actual restoration evidence required");}
    }
    record Historical(RootActivitySavedOriginalGuard.SavedOrigin original) implements RestoredFeastOriginal {
        public Historical {Objects.requireNonNull(original);}
    }
    enum Disposition { NONE,PENDING,FIRST_ACTIVITY,ORDINARY_ACTIVITY }
    static Disposition classify(FeastDomainRuntime.Ledger actual,SavedCheckpointMaterial.Kind kind) {
        Objects.requireNonNull(actual);Objects.requireNonNull(kind);
        if(actual.pending().isPresent())return Disposition.PENDING;
        if(actual.resolved().flatMap(FeastDomainRuntime.Resolved::activity).isEmpty())return Disposition.NONE;
        return kind==SavedCheckpointMaterial.Kind.FIRST_BASELINE?Disposition.FIRST_ACTIVITY:Disposition.ORDINARY_ACTIVITY;
    }
    static RestoredFeastOriginal capture(RootRuntimeContext context,ContinuityStorePort.Session same,
            RootRestorationOriginalProof.Original original,FeastDomainRuntime domain,FeastFinalSettlement settlement)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(original);Objects.requireNonNull(domain);Objects.requireNonNull(settlement);
        var actual=context.restorationOriginal(same);
        StrictJson.require(actual.basis().equals(original.basis())&&actual.material().kind()==original.material().kind()
                &&actual.material().witness().equals(original.material().witness()),"restored FEAST source does not belong to this actual privately admitted context");
        original.requireImportPredecessor(same,same.head());same.requireDomainImportContinuation(original.attachmentHead().sequence(),ContinuityJson.digest(original.attachmentHead().toJson()));
        original.material().requireRetained(same);var refs=List.of(original.basis(),original.material().reference());
        final RootActivitySavedOriginalGuard.SavedBody saved;
        try {saved=RootActivitySavedOriginalGuard.readSavedBody(same,original.originalSavedHead(),domain.registration().producerSources());}
        catch(IOException|IllegalArgumentException failure) {return new Unqualified(Reason.SAVED_FEAST_UNAVAILABLE,failure.getMessage()==null?failure.getClass().getSimpleName():failure.getMessage(),refs);}
        saved.requireUnchanged(same);
        original.material().requireRetained(same);original.requireImportPredecessor(same,same.head());
        same.requireDomainImportContinuation(original.attachmentHead().sequence(),ContinuityJson.digest(original.attachmentHead().toJson()));
        var disposition=classify(saved.ledger(),original.material().kind());
        if(disposition==Disposition.NONE)return new NoOriginal(original.basis(),saved.reference());
        if(disposition==Disposition.PENDING)return new Unqualified(Reason.PENDING_OR_UNKNOWN,"the actual saved FEAST pending/UNKNOWN original is retained; no source is cleared",List.of(original.basis(),saved.reference().payload()));
        if(disposition==Disposition.FIRST_ACTIVITY)return new Unqualified(Reason.FIRST_NATIVE_CONTINUITY_UNPROVEN,"FIRST_BASELINE activity origin is retained; ordinary M6 custody cannot grant native adoption",List.of(original.basis(),saved.reference().payload()));
        try {
            var retained=RootActivitySavedOriginalGuard.require(context,same,original,domain,settlement);retained.requireUnchanged(context,same);
            return new Historical(retained);
        } catch(IOException|IllegalArgumentException failure) {
            return new Unqualified(Reason.ORIGINAL_REPLAY_UNAVAILABLE,failure.getMessage()==null?failure.getClass().getSimpleName():failure.getMessage(),List.of(original.basis(),saved.reference().payload()));
        }
    }
}
