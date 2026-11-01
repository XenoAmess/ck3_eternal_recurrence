package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStaticDispatch4267630;

public final class RequestStaticDispatch4267630232 {
    private RequestStaticDispatch4267630232() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(calls);

        VolatileBits v = entry.volatileBits();
        TailTarget target = new TailTarget(entry, calls);
        // Reuse existing scalar API exactly once. The result is discarded as per contract.
        RequestStaticDispatch4267630.execute(v.rcxBits(), v.raxBits(), target);

        return target.capturedNR;
    }

    private static final class TailTarget implements RequestStaticDispatch4267630.TailTarget {
        private final Entry entry;
        private final GovernmentCrtBoundary185Api.Calls calls;
        private NormalReturn capturedNR;

        TailTarget(Entry entry, GovernmentCrtBoundary185Api.Calls calls) {
            this.entry = entry;
            this.calls = calls;
        }

        @Override
        public int jumpRax(long targetRax, long knownRcx) {
            // Issue exactly one 185.Tail at sourceRVA 4267630, kind INDIRECT_ABSOLUTE,
            // targetBits = actual callback target Rax, Entry = original entry object.
            Tail transfer = new Tail(
                0x4267630L,
                TargetKind.INDIRECT_ABSOLUTE,
                targetRax,
                entry
            );
            
            // Capture calls.tail's original full NR.
            NormalReturn nr = calls.tail(transfer);
            Objects.requireNonNull(nr);
            this.capturedNR = nr;

            // Supply true low EAX to the old scalar int callback contract.
            return (int) nr.volatileBits().raxBits();
        }
    }
}