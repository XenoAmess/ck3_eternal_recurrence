package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.util.HashSet;
import java.util.List;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.contracts.StrictJson;

/** Original endpoint order for Council/LIFE reads. No read, submit, or replacement evidence is created here. */
final class GovernanceReadChronology {
    private GovernanceReadChronology() { }

    static void requireOrderedReads(List<PlanningReadReceipt> reads) {
        StrictJson.require(reads != null && !reads.isEmpty() && reads.size() <= 3002, "complete bounded original governance read group required");
        var identifiers = new HashSet<String>(); NativeRequestChronology previous = null;
        for (PlanningReadReceipt read : reads) {
            StrictJson.require(identifiers.add(read.requestId()), "original governance group repeated a native read request");
            NativeRequestChronology actual = requireAck(read.original(), read.before().binding()); actual.verify(read);
            if (previous != null) requireAfter(previous, actual);
            previous = actual;
        }
    }

    static NativeRequestChronology requireAck(NativeActionPort.AckReceived ack, GuardEvidence guard) {
        NativeRequestChronology actual = ack.custody().orElseThrow(() -> new IllegalArgumentException("original governance endpoint chronology missing; no reconstruction allowed"));
        actual.verify(ack, guard); return actual;
    }

    static void requireAfter(NativeRequestChronology previous, NativeRequestChronology next) {
        StrictJson.require(!previous.requestId().equals(next.requestId()) && previous.session().equals(next.session())
                && previous.custodyEpoch().equals(next.custodyEpoch()), "governance original requests crossed the held connection or custody epoch");
        StrictJson.require(next.writeEntered().order().compareTo(previous.responseReceived().order()) > 0
                && !next.writeEntered().observedAt().isBefore(previous.responseReceived().observedAt()),
                "governance original request was not issued after consuming the preceding native response");
    }
}
