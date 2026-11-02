package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner single raw iteration after both model candidates were rejected. */
public final class GeneralSearchStep294 {
    private GeneralSearchStep294() { }

    public static void step(Registers r,GovernmentCrtBoundary185Api.Memory memory,boolean leftShorter) {
        r.rcx=r.rdx;r.rcx>>>=1;r.rax=r.rcx+r.rcx*4L;
        long probe=r.r9+r.rax*8L;
        int score=memory.readDword(probe);r.r8=probe;
        boolean advance=leftShorter ? score>(int)r.r10 : (int)r.r10<=score;
        if(advance) {
            r.rax=-1L;r.r9=r.r8+0x28L;r.rax-=r.rcx;r.rdx+=r.rax;
        } else r.rdx=r.rcx;
    }
}
