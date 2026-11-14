package org.xar.ck3.control.application.advance;

import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CompositeContinuationToken;
import org.xar.ck3.control.contracts.StrictJson;

/** Separate source-issued child5 preparation authority. Not a Native permit or a
 * renewed child4 token. Actual canonical A and Root/backend qualification must
 * already have been independently replayed by this identical installed source. */
public final class LifePreparedCleanupContinuation implements CompositeContinuationToken {
    private final LifeAdvanceComposite issuer;
    private final PreparedCleanupEvidence.Prepared prepared;
    private final Instant issuedAt,deadline;
    private final java.util.concurrent.atomic.AtomicBoolean claimed=new java.util.concurrent.atomic.AtomicBoolean();
    LifePreparedCleanupContinuation(LifeAdvanceComposite actualIssuer,PreparedCleanupEvidence.Prepared prepared,
            Instant issuedAt,Instant deadline) {
        issuer=Objects.requireNonNull(actualIssuer);this.prepared=Objects.requireNonNull(prepared);
        this.issuedAt=Objects.requireNonNull(issuedAt);this.deadline=Objects.requireNonNull(deadline);
        StrictJson.require(issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(Duration.ofMinutes(10)))
                &&prepared.deadline().equals(deadline),"prepared cleanup requires its new finite operation window");
    }
    /** Only the actual Life source calls this distinct successor constructor after complete C5/Root qualification. */
    static LifePreparedCleanupContinuation successor(LifeAdvanceComposite actualIssuer,PreparedCleanupEvidence.Prepared prepared,
            PreparedCleanupNoEffectProof.Verified predecessorProof,Instant issuedAt,Instant deadline){
        return new LifePreparedCleanupContinuation(actualIssuer,prepared,predecessorProof,issuedAt,deadline);
    }
    private LifePreparedCleanupContinuation(LifeAdvanceComposite actualIssuer,PreparedCleanupEvidence.Prepared prepared,
            PreparedCleanupNoEffectProof.Verified predecessorProof,Instant issuedAt,Instant deadline){
        issuer=Objects.requireNonNull(actualIssuer);this.prepared=Objects.requireNonNull(prepared);
        this.issuedAt=Objects.requireNonNull(issuedAt);this.deadline=Objects.requireNonNull(deadline);Objects.requireNonNull(predecessorProof);
        StrictJson.require(PreparedCleanupSuccessorEvidence.isSuccessor(prepared)&&issuedAt.isBefore(deadline)
                &&!deadline.isAfter(issuedAt.plus(Duration.ofMinutes(20)))&&prepared.deadline().equals(deadline)
                &&prepared.children().getLast().state() instanceof org.xar.ck3.control.application.action.ActionState.PreparedCleanupNoEffectConfirmed,
                "prepared successor needs its distinct finite operation window after canonical C5 NoEffect");
        var terminal=(org.xar.ck3.control.application.action.ActionState.PreparedCleanupNoEffectConfirmed)prepared.children().getLast().state();
        StrictJson.require(terminal.proofReference().equals(predecessorProof.proofReference())
                &&terminal.originalPreparedState().equals(predecessorProof.originalPreparedState()),"prepared successor token changed the complete original C5 proof/state");
    }
    boolean issuedBy(LifeAdvanceComposite actual){return issuer==actual;}
    void claimScope(LifeAdvanceComposite actual){
        StrictJson.require(issuer==actual&&claimed.compareAndSet(false,true),"prepared source token scope already consumed; same-ID collection only");
    }
    public PreparedCleanupEvidence.Prepared prepared(){return prepared;}
    public Instant issuedAt(){return issuedAt;}
    @Override public ActionCommand originalParent(){return prepared.parentReceipt().command();}
    @Override public Instant deadline(){return deadline;}
    @Override public Kind kind(){return Kind.LIFE_PREPARED_CLEANUP;}
}
