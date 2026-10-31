package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Exact-bit owned normal contract for held3F5F970; no formal Native type or loaded state. */
public final class GovernmentLookupHelper176Api {
    private GovernmentLookupHelper176Api() { }
    public record Entry(long imageBaseBits,long rspBits,VolatileBits volatileBits,NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    public record NormalReturn(VolatileBits volatileBits,long returnRipBits,long callerRspBits,NonvolatileBits nonvolatileBits) {
        public NormalReturn { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    public interface Memory extends GovernmentPrimaryTail155Api.Memory { }
    public interface Calls extends GovernmentPrimaryTail155Api.Calls { }
    public interface LoopBudget {
        /** Software stopping port before each actual3F5F9F0 loop-header visit; no iteration invented or skipped. */
        void beforeStep(long headerRva,long nodeBits,long endNodeBits);
    }
}
