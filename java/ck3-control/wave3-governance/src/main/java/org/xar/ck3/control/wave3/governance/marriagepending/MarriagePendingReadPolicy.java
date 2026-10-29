package org.xar.ck3.control.wave3.governance.marriagepending;

import java.util.Objects;
import static org.xar.ck3.control.wave3.governance.marriagepending.MarriagePendingModel.*;

/** The actual family_marriage_formal_consumer pending branch, lines 603-634. */
public final class MarriagePendingReadPolicy {
    private MarriagePendingReadPolicy() { }
    /** The original foreign-episode/no-pending paths never query current bridge identity. */
    public static boolean requiresCurrentProcess(
            org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel.Ledger ledger, Frame frame) {
        Objects.requireNonNull(ledger); Objects.requireNonNull(frame);
        return ledger.pending() != null && ledger.pending().episode().matches(frame.episodeRunId());
    }
    public static Decision decide(Inputs inputs) {
        Objects.requireNonNull(inputs);
        Pending pending = inputs.pending();
        if (pending == null) { return new NoPending(); }
        if (!requiresCurrentProcess(inputs.ledger(), inputs.frame())) { return new OtherEpisode(); }
        boolean cold = !pending.sourceProcess().matches(inputs.currentProcess());
        boolean checkedHere = pending.lastCheckedProcess().matches(inputs.currentProcess());
        boolean later = inputs.frame().nativeRevision() != null && inputs.frame().nativeRevision().signum() > 0
                && inputs.frame().nativeRevision().compareTo(pending.lastCheckedNativeRevision()) > 0;
        if (cold && !checkedHere || later) { return new ReadResult(pending, cold); }
        return new WaitLater(pending);
    }
}

