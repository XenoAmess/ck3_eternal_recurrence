package org.xar.ck3.control.application.advance;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Immutable capability for one actual source's read-only reconciliation, never a
 * CompositeContinuationToken, Native SubmissionPermit or current observation lease.
 * The package-owned issuer must first verify actual backend qualification and
 * canonical parent/child membership. Caller DATA alone cannot construct this token. */
public final class NoEffectReconciliationToken {
    private final LifeAdvanceComposite issuer;
    private final PostExitCleanupNoEffectProof.Verified proof;
    private final Instant issuedAt,deadline;
    NoEffectReconciliationToken(LifeAdvanceComposite actualIssuer,PostExitCleanupNoEffectProof.Verified proof,
            Instant issuedAt,Instant deadline) {
        issuer=Objects.requireNonNull(actualIssuer);this.proof=Objects.requireNonNull(proof);
        this.issuedAt=Objects.requireNonNull(issuedAt);this.deadline=Objects.requireNonNull(deadline);
        require(issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(Duration.ofMinutes(10)))
                &&!issuedAt.isBefore(proof.freshSnapshotAck().custody().orElseThrow().responseReceived().observedAt()),
                "NoEffect reconciliation requires its own finite source issuance window after the observed originals");
    }
    boolean issuedBy(LifeAdvanceComposite actual){return issuer==actual;}
    public PostExitCleanupNoEffectProof.Verified proof(){return proof;}
    public ExactRef proofReference(){return proof.proofReference();}
    public ActionReceipt parentReceipt(){return proof.parentReceipt();}
    public ExactRef parentReference(){return proof.parentReference();}
    public List<ActionReceipt> children(){return proof.children();}
    public List<ExactRef> childReferences(){return proof.childReferences();}
    public ActionReceipt child4(){return proof.child4();}
    public ExactRef child4Reference(){return proof.child4Reference();}
    public ExactRef authorizationReference(){return proof.authorizationReference();}
    public Instant issuedAt(){return issuedAt;}
    public Instant deadline(){return deadline;}
}
