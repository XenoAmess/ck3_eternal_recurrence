package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owned normal103B boundary; no CRT or Windows lock implementation, current TLS or Game claim. */
public final class GovernmentThreadHeader178Api {
    private GovernmentThreadHeader178Api() { }

    /** rspBits is the original CALL-site RSP for CALL, and unchanged entry RSP for tail JMP. */
    public record IatCall(long callSiteRva,long slotRva,long rspBits,boolean tailJump,
            VolatileBits volatileBits,NonvolatileBits nonvolatileBits) {
        public IatCall {Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits);}
    }

    /**
     * Direct4223B30 remains the inherited actual OpaqueCall port. Static import slots are distinct
     * from resolved function RVAs. Every normal port supplies full represented volatile poststate
     * and preserves the offered nonvolatile state, or rejects unrepresented behavior.
     */
    public interface Ports extends Calls {
        VolatileBits invokeIat(IatCall call);
    }

    /** Owned finite observation before the real wait edge; throws rather than silently clamping. */
    public interface WaitBudget {
        void beforeWait(long loopHeaderRva,long guardAddress,int observedGuard);
    }
}
