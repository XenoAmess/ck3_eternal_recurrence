package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.contracts.ExactRef;

/** One actual Life source's short read-only first-terminal capability for an
 * already reserved sixth command. Not a continuation, Native permit, ACK,
 * NoDispatch witness, current-world lease or gameplay credit. The source-owned
 * issuer must first revalidate actual Root/backend qualification, original WAL
 * and same-lock parent/preparation/first-five/current-child absence or exact
 * idempotent matching terminal. Public DATA verification grants none of these. */
public final class ReservedCleanupNoEffectReconciliationToken {
    private final LifeAdvanceComposite issuer;
    private final ReservedPreparedCleanupNoEffectProof.Verified proof;
    private final Instant issuedAt,deadline;
    private ReservedCleanupNoEffectReconciliationToken(LifeAdvanceComposite actualIssuer,
            ReservedPreparedCleanupNoEffectProof.Verified proof,Instant issuedAt,Instant deadline) {
        issuer=Objects.requireNonNull(actualIssuer);this.proof=Objects.requireNonNull(proof);
        this.issuedAt=Objects.requireNonNull(issuedAt);this.deadline=Objects.requireNonNull(deadline);
        require(issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(Duration.ofMinutes(10)))
                &&!issuedAt.isBefore(proof.freshSnapshotAck().custody().orElseThrow().responseReceived().observedAt()),
                "reserved cleanup reconciliation requires its own finite source window after full original verification");
    }
    static ReservedCleanupNoEffectReconciliationToken issue(LifeAdvanceComposite actualIssuer,
            ReservedPreparedCleanupNoEffectProof.Verified proof,Instant issuedAt,Instant deadline) {
        return new ReservedCleanupNoEffectReconciliationToken(actualIssuer,proof,issuedAt,deadline);
    }
    boolean issuedBy(LifeAdvanceComposite actual){return issuer==actual;}
    public ReservedPreparedCleanupNoEffectProof.Verified proof(){return proof;}
    public ExactRef proofReference(){return proof.proofReference();}
    public ActionReceipt parentReceipt(){return proof.parentReceipt();}
    public ExactRef parentReference(){return proof.parentReference();}
    public List<ActionReceipt> children(){return proof.children();}
    public List<ExactRef> childReferences(){return proof.childReferences();}
    public ActionCommand command(){return proof.command();}
    public ExactRef preparationReference(){return proof.preparationReference();}
    public ExactRef authorizationReference(){return proof.authorizationReference();}
    public Instant issuedAt(){return issuedAt;}
    public Instant deadline(){return deadline;}
}
