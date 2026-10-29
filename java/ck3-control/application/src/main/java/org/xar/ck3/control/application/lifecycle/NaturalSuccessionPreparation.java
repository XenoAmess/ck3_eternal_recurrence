package org.xar.ck3.control.application.lifecycle;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CompositeActionPort;
import org.xar.ck3.control.application.action.CompositeContinuationToken;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual natural-succession preparation. Opaque tokens are DATA until their original issuer revalidates them. */
public interface NaturalSuccessionPreparation {
    sealed interface Preparation permits FinalSnapshot,PendingPreparation,PendingFinalized { }
    /** The initial clear path still requires the existing actual natural-M3 verifier and lifecycle reducer. */
    record FinalSnapshot(LifecycleObservationPort.Snapshot actual) implements Preparation {
        public FinalSnapshot {Objects.requireNonNull(actual);}
    }
    record PendingPreparation(PendingToken token) implements Preparation {
        public PendingPreparation {Objects.requireNonNull(token);}
    }
    /** An already-published pending successor cannot be finalized with the old terminal Snapshot. */
    record PendingFinalized(FinalToken token) implements Preparation {
        public PendingFinalized {Objects.requireNonNull(token);}
    }
    interface PendingToken extends CompositeContinuationToken {
        @Override ActionCommand originalParent();
        SuccessorUiObligation obligation();
        ExactRef canonicalDomain();
        ExactRef actualPublishedDriver();
        ExactRef canonicalPublicationProof();
        List<ExactRef> evidence();
    }
    /** Actual Root private implementation binds its M3.Finalized and canonical publication, never a caller DTO. */
    interface FinalToken extends PendingToken {
        LifecycleReducer.Reduction finalReduction();
        DriverSnapshotFacts.Known beforeFinal();
        DriverSnapshotFacts.Known publishedFinal();
        DriverObservationAssembler.FullSnapshot qualifiedFinalFrame();
        RawJson matchedEstate();
        ExactRef m3FinalizationProof();
        WriterContracts.Receipt finalizationReceipt();
        ExactRef canonicalFinalizationDomain();
    }
    Preparation prepareOutcome(ActionCommand originalParent,LifecycleObservationPort.Snapshot original,
            CompositeActionPort.Children actualChildren)throws IOException,InterruptedException;
    void requireCurrent(ActionCommand parent,ContinuityStorePort.Session same,PendingToken identical)throws IOException;
    void requireFinalized(ActionCommand parent,ContinuityStorePort.Session same,FinalToken identical)throws IOException;
    /** The coordinator supplies only its actual finite same-parent continuation Children, never generic observe(). */
    Preparation resumeOutcome(ActionCommand parent,PendingToken identical,CompositeActionPort.Children actualChildren)
            throws IOException,InterruptedException;
}
