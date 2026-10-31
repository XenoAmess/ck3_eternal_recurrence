package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Raw owned normal callee entry. frameRspBits is after CALL pushed its return address. */
public final class GovernmentCallee164Api {
    private GovernmentCallee164Api() { }
    public record Entry(long imageBaseBits, long frameRspBits,
            VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }
    /** Complete represented poststate and actual RET reads; never an inferred business return type. */
    public record NormalReturn(VolatileBits volatileBits, NonvolatileBits nonvolatileBits,
            long returnRipBits, long callerRspBits) {
        public NormalReturn { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }
    /** Mechanical initialization only; no target instruction semantics. */
    public static Registers registers(Entry e) {
        NonvolatileBits n=e.nonvolatileBits();
        Registers r=new Registers(new GovernmentPrimaryTail155Api.Entry(e.imageBaseBits(),
                n.rdiBits(),(int)n.r12Bits(),n.rsiBits(),n.r15Bits(),n.rbpBits(),
                e.frameRspBits(),n.r13Bits(),n.r14Bits(),n.xmm6(),e.volatileBits()));
        r.rbx=n.rbxBits(); r.r12=n.r12Bits();
        return r;
    }
}
