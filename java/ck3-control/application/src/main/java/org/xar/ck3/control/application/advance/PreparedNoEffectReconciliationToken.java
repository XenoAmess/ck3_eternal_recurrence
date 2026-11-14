package org.xar.ck3.control.application.advance;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.PreparedCleanupAction;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** One actual Life source's read-only fifth-child reconciliation capability.
 * Not a continuation token, Native permit, ACK, current-world lease or day credit.
 * Its package issuer must first qualify exact backend/OS originals and revalidate
 * the original current canonical parent/fifth child under the actual writer. */
public final class PreparedNoEffectReconciliationToken {
    private final LifeAdvanceComposite issuer;
    private final PreparedCleanupNoEffectProof.Verified proof;
    private final Instant issuedAt,deadline;
    PreparedNoEffectReconciliationToken(LifeAdvanceComposite actualIssuer,PreparedCleanupNoEffectProof.Verified proof,
            Instant issuedAt,Instant deadline) {
        issuer=Objects.requireNonNull(actualIssuer);this.proof=Objects.requireNonNull(proof);
        this.issuedAt=Objects.requireNonNull(issuedAt);this.deadline=Objects.requireNonNull(deadline);
        require(issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(Duration.ofMinutes(10)))
                &&!issuedAt.isBefore(proof.freshSnapshotAck().custody().orElseThrow().responseReceived().observedAt()),
                "prepared NoEffect reconciliation needs its own finite source window after the observed originals");
    }
    boolean issuedBy(LifeAdvanceComposite actual){return issuer==actual;}
    public PreparedCleanupNoEffectProof.Verified proof(){return proof;}
    public ExactRef proofReference(){return proof.proofReference();}
    public ActionReceipt parentReceipt(){return proof.parentReceipt();}
    public ExactRef parentReference(){return proof.parentReference();}
    public List<ActionReceipt> children(){return proof.children();}
    public List<ExactRef> childReferences(){return proof.childReferences();}
    public ActionReceipt child5(){return proof.child5();}
    public ExactRef child5Reference(){return proof.child5Reference();}
    public PreparedCleanupAction originalPreparedState(){return proof.originalPreparedState();}
    public ExactRef preparationReference(){return proof.preparationReference();}
    public ExactRef authorizationReference(){return proof.authorizationReference();}
    public Instant issuedAt(){return issuedAt;}
    public Instant deadline(){return deadline;}
}
