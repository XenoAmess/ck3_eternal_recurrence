package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Raw owned normal boundary of the held 271-byte RF, not a formal Native object signature. */
public final class GovernmentLookup167Api {
    private GovernmentLookup167Api() { }

    /** Actual callee-entry RSP after CALL has pushed the return RIP into owned memory. */
    public record Entry(long imageBaseBits, long calleeRspBits,
            VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }
    public record Result(long returnRipBits, long callerRspBits,
            VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public Result { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }
    /**
     * Before each actual entry at 3F8A6F0 (contended rollback) or 3F8A6F8 (poll read).
     * May reject unsupported work. Exhaustion never supplies a fictitious normal return.
     */
    @FunctionalInterface public interface SpinBudget {
        void beforeStep(long instructionRva, long lockAddressBits);
    }
    @FunctionalInterface public interface Target {
        Result execute(Entry entry, Memory memory, Calls calls, SpinBudget spinBudget);
    }
}
