package org.xar.ck3.control.admission.batchtiming;

import java.math.BigInteger;
import java.util.Optional;

/** Process-local, single-use timing state; the caller supplies already observed timestamps. */
public final class FullLifecycleTiming {
    private final boolean enabled;
    private Pending pending;
    private boolean dropped;

    public FullLifecycleTiming(boolean enabled) { this.enabled = enabled; }

    public void beforePublish(BigInteger sequence, BigInteger observedMonotonicNs) {
        pending = null;
        dropped = false;
        if (!enabled) { return; }
        if (sequence == null || sequence.signum() <= 0 || observedMonotonicNs == null
                || observedMonotonicNs.signum() < 0) {
            dropped = true;
            return;
        }
        pending = new Pending(sequence, observedMonotonicNs);
    }

    /** A missing end is a failed observation; following an old request does not observe a new end. */
    public Optional<FullBatchTiming.Wall> afterReceipt(BigInteger sequence, BigInteger observedMonotonicNs) {
        Pending previous = pending;
        boolean wasDropped = dropped;
        pending = null;
        dropped = false;
        if (!enabled || wasDropped || sequence == null || sequence.signum() <= 0) { return Optional.empty(); }
        if (previous == null || !previous.sequence().equals(sequence)) {
            return Optional.of(FullBatchTiming.Wall.unobserved(sequence));
        }
        if (observedMonotonicNs == null || observedMonotonicNs.compareTo(previous.started()) < 0) {
            return Optional.empty();
        }
        return Optional.of(new FullBatchTiming.Wall(sequence,
                FullBatchTiming.Origin.NEW_SUBMISSION_SAME_PRODUCER, previous.started(),
                observedMonotonicNs, observedMonotonicNs.subtract(previous.started())));
    }

    public void discard() { pending = null; dropped = true; }
    private record Pending(BigInteger sequence, BigInteger started) { }
}
