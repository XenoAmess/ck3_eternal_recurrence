package org.xar.ck3.control.application.advance;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;

/** Source-issued finite cancellation of the original armed, never-resumed Life initialization. */
public final class LifeSentinelCancellation implements CompositeContinuationToken {
    private final LifeAdvanceComposite issuer;
    private final ActionCommand originalParent;
    private final CompositeExecution originalExecution;
    private final PlanningReadReceipt armedRead;
    private final AdvanceObservationPort.Frame beforeCancel;
    private final BigInteger generation;
    private final Instant deadline;

    LifeSentinelCancellation(LifeAdvanceComposite issuer, ActionCommand originalParent, CompositeExecution originalExecution,
            PlanningReadReceipt armedRead, AdvanceObservationPort.Frame beforeCancel, BigInteger generation, Instant deadline) {
        this.issuer = Objects.requireNonNull(issuer); this.originalParent = Objects.requireNonNull(originalParent);
        this.originalExecution = Objects.requireNonNull(originalExecution); this.armedRead = Objects.requireNonNull(armedRead);
        this.beforeCancel = Objects.requireNonNull(beforeCancel); this.generation = Objects.requireNonNull(generation);
        this.deadline = Objects.requireNonNull(deadline);
    }
    boolean issuedBy(LifeAdvanceComposite actual) { return issuer == actual; }
    @Override public ActionCommand originalParent() { return originalParent; }
    @Override public Instant deadline() { return deadline; }
    @Override public Kind kind() { return Kind.LIFE_SENTINEL_CANCEL; }
    public CompositeExecution originalExecution() { return originalExecution; }
    public PlanningReadReceipt armedRead() { return armedRead; }
    public AdvanceObservationPort.Frame beforeCancel() { return beforeCancel; }
    public BigInteger generation() { return generation; }
}
