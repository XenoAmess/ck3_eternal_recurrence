package org.xar.ck3.control.application.advance;

import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Immutable source-carried DATA for a distinct post-resume-paused cancellation.
 * Construction does not authorize Native dispatch or prove the loaded backend's atomic generation guard. */
public final class LifePostResumePauseCancellation implements CompositeContinuationToken {
    private final LifeAdvanceComposite issuer;
    private final ActionReceipt originalParentReceipt;
    private final ExactRef originalParentReference;
    private final CompositeExecution originalExecution;
    private final List<ActionReceipt> originalChildren;
    private final List<ExactRef> originalChildReferences;
    private final ActionReceipt originalArm;
    private final org.xar.ck3.control.reconciliation.LateOutcome.Status originalArmStatus;
    private final ClockStatusRead.Observation armedStatus;
    private final AdvanceObservationPort.Frame beforeCancel;
    private final BigInteger generation;
    private final Instant issuedAt;
    private final Instant deadline;
    private final ExactRef authorizationReference;

    LifePostResumePauseCancellation(LifeAdvanceComposite issuer, ActionReceipt originalParentReceipt,
            ExactRef originalParentReference, List<ActionReceipt> originalChildren, List<ExactRef> originalChildReferences,
            ClockStatusRead.Observation armedStatus, AdvanceObservationPort.Frame beforeCancel,
            Instant issuedAt, Instant deadline, ExactRef authorizationReference) {
        this.issuer=Objects.requireNonNull(issuer);
        this.originalParentReceipt=Objects.requireNonNull(originalParentReceipt);
        this.originalParentReference=Objects.requireNonNull(originalParentReference);
        this.originalChildren=List.copyOf(originalChildren);
        this.originalChildReferences=List.copyOf(originalChildReferences);
        this.armedStatus=Objects.requireNonNull(armedStatus); this.beforeCancel=Objects.requireNonNull(beforeCancel);
        this.issuedAt=Objects.requireNonNull(issuedAt); this.deadline=Objects.requireNonNull(deadline);
        this.authorizationReference=Objects.requireNonNull(authorizationReference);
        require(deadline.isAfter(issuedAt)&&!deadline.isAfter(issuedAt.plus(Duration.ofMinutes(10))),
                "post-resume pause cancellation needs its own new finite window");
        require(originalParentReference.bytes()>0&&authorizationReference.bytes()>0
                &&!originalParentReference.equals(authorizationReference)
                &&this.originalChildren.size()==this.originalChildReferences.size()
                &&this.originalChildReferences.stream().allMatch(ref->ref.bytes()>0
                    &&!ref.equals(originalParentReference)&&!ref.equals(authorizationReference))
                &&this.originalChildReferences.stream().distinct().count()==this.originalChildReferences.size(),
                "post-resume pause cancellation requires distinct exact original and durable authorization references");
        var original=LifePostResumePauseCleanupProof.original(originalParentReceipt,this.originalChildren);
        this.originalExecution=((ActionState.CompositeUnknown)originalParentReceipt.state()).execution();
        this.originalArm=original.arm(); this.originalArmStatus=original.originalArm();
        this.generation=new BigInteger(original.originalArm().generation().decimal());
        // Only bounded DATA consistency at the actual retained pre-CANCEL event instant. Real current source/backend
        // qualification and durable authorization verification remain mandatory at the actual issuer.
        LifePostResumePauseCleanupProof.requireFreshArmedPaused(original,armedStatus,beforeCancel,issuedAt,deadline,beforeCancel.observedAt());
    }
    boolean issuedBy(LifeAdvanceComposite actual) { return issuer==actual; }
    @Override public ActionCommand originalParent() { return originalParentReceipt.command(); }
    @Override public Instant deadline() { return deadline; }
    @Override public Kind kind() { return Kind.LIFE_POST_RESUME_PAUSE_CANCEL; }
    public ActionReceipt originalParentReceipt() { return originalParentReceipt; }
    public ExactRef originalParentReference() { return originalParentReference; }
    public CompositeExecution originalExecution() { return originalExecution; }
    public List<ActionReceipt> originalChildren() { return originalChildren; }
    public List<ExactRef> originalChildReferences() { return originalChildReferences; }
    public ActionReceipt originalArm() { return originalArm; }
    public org.xar.ck3.control.reconciliation.LateOutcome.Status originalArmStatus() { return originalArmStatus; }
    public ClockStatusRead.Observation armedStatus() { return armedStatus; }
    public PlanningReadReceipt armedRead() { return armedStatus.receipt(); }
    public AdvanceObservationPort.Frame beforeCancel() { return beforeCancel; }
    public BigInteger generation() { return generation; }
    public Instant issuedAt() { return issuedAt; }
    public ExactRef authorizationReference() { return authorizationReference; }
}
