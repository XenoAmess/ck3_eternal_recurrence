package org.xar.ck3.control.application.action;

import java.util.Optional;

/** Coordinator-issued proof of zero native dispatch, after same-Game/source/episode guards passed.
 * In-process control signal only; Java object serialization is unsupported for its original domain references. */
public final class PreSubmissionRevisionMismatchException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    // Preserve the actual in-process originals; making their domain graph Serializable would invent a persistence contract.
    @SuppressWarnings("serial")
    private final GuardEvidence current;
    @SuppressWarnings("serial")
    private final Optional<ActionReceipt> zeroDispatchReceipt;
    PreSubmissionRevisionMismatchException(GuardEvidence current, Optional<ActionReceipt> zeroDispatchReceipt) {
        super("native frame changed before this action reached dispatch"); this.current = current; this.zeroDispatchReceipt = zeroDispatchReceipt;
    }
    public GuardEvidence current() { return current; }
    public Optional<ActionReceipt> zeroDispatchReceipt() { return zeroDispatchReceipt; }
    public boolean replanAllowed() { return true; }
}
