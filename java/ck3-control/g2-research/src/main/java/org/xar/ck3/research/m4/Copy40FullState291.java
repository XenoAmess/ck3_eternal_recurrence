package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Exact normal60B leaf over supplied byte memory; no memmove, RFLAGS, trap or hardware claim. */
public final class Copy40FullState291 {
    private Copy40FullState291() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        VolatileBits v=entry.volatileBits();
        long source=v.rcxBits(),destination=v.r8Bits(),end=v.rdxBits();
        var x0=v.xmm0();var x1=v.xmm1();
        while(source!=end) {
            budget.beforeStep(0xF0ABA0L,source);
            var copied=Copy40Row291.transfer(memory,source,destination);
            x0=copied.xmm0();x1=copied.xmm1();
            source+=0x28L;destination+=0x28L;
        }
        VolatileBits actual=new VolatileBits(destination,source,end,destination,v.r9Bits(),
                v.r10Bits(),v.r11Bits(),x0,x1,v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
        long rip=memory.readQword(entry.rspBits());
        return new GovernmentCrtBoundary185Api.NormalReturn(actual,rip,entry.rspBits()+8L,entry.nonvolatileBits());
    }
}
