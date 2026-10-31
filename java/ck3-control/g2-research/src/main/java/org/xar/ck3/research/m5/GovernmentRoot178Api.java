package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owned exact-bit normal contract for held3F5C090; no Native formal type or loaded observation. */
public final class GovernmentRoot178Api {
    private GovernmentRoot178Api() { }
    /** State after the caller CALL, before the actual SUB RSP,28 prologue. */
    public record Entry(long imageBaseBits,long rspBits,VolatileBits volatileBits,NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    /** Complete normal RET state, including the fresh stack return address. */
    public record NormalReturn(VolatileBits volatileBits,long returnRipBits,long callerRspBits,NonvolatileBits nonvolatileBits) {
        public NormalReturn { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    public interface Memory extends GovernmentPrimaryTail155Api.Memory { }
    public interface Calls extends GovernmentPrimaryTail155Api.Calls { }
}
