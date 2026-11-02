package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Owner page-write basic block; the provided budget is a software fence, not Native authority. */
public final class StackProbe78Pages290 {
    private StackProbe78Pages290() { }

    public static void touch(long stackTopBits,long requestedBytesBits,long stackLimitBits,
            GovernmentCrtBoundary185Api.Memory memory,GovernmentCrtBoundary185Api.LoopBudget budget) {
        long target=Long.compareUnsigned(stackTopBits,requestedBytesBits)<0?0L:stackTopBits-requestedBytesBits;
        if(Long.compareUnsigned(target,stackLimitBits)>=0)return;
        target&=~0xfffL;
        long page=stackLimitBits;
        do {
            page-=0x1000L;
            budget.beforeStep(0x42247E0L,page);
            memory.writeByte(page,0);
        } while(page!=target);
    }
}
