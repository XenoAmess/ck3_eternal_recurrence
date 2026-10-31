package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Raw normal entry/return of held three-RF193B. No formal Native object or enum signature is asserted. */
public final class GovernmentRowResolve164Api {
    private GovernmentRowResolve164Api() { }

    /** RSP is the actual callee-entry value AFTER CALL pushed its return address into owned Memory. */
    public record Entry(long imageBaseBits, long calleeRspBits,
            VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }

    /** All represented volatile output plus actual restored registers and the RET stack result. */
    public record Result(long returnRipBits, long callerRspBits,
            VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public Result { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }

    /** Existing raw Calls returns every represented volatile bit; its normal nonvolatile ABI is a port precondition. */
    @FunctionalInterface public interface Target {
        Result execute(Entry entry, Memory memory, Calls calls);
    }
}
