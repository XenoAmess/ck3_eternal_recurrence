package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Held78B normal state only; no hardware stack allocation, RFLAGS, or native guard-page/EH claim. */
public final class StackProbe78FullState290 {
    private StackProbe78FullState290() { }

    /** Exact GS:[0x10] data port. It is distinct from the existing GS:[0x58] port. */
    public interface Gs10 { long readGsQword10(); }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory,
            Gs10 gs10, GovernmentCrtBoundary185Api.LoopBudget budget) {
        long s=entry.rspBits();
        VolatileBits v=entry.volatileBits();
        memory.writeQword(s-0x10L,v.r10Bits());
        memory.writeQword(s-8L,v.r11Bits());
        long limit=gs10.readGsQword10();
        StackProbe78Pages290.touch(s+8L,v.raxBits(),limit,memory,budget);
        long r10=memory.readQword(s-0x10L);
        long r11=memory.readQword(s-8L);
        VolatileBits actual=new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),
                v.r9Bits(),r10,r11,v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
        long rip=memory.readQword(s);
        return new GovernmentCrtBoundary185Api.NormalReturn(actual,rip,s+8L,entry.nonvolatileBits());
    }
}
