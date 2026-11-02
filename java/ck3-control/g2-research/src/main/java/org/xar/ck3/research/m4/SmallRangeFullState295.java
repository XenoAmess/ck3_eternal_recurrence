package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held normal259 raw range/frame path; COPY port remains full-state opaque. */
public final class SmallRangeFullState295 {
    private SmallRangeFullState295() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(r.rsp+0x18L,r.rsi);
        r.rsp-=8L;memory.writeQword(r.rsp,r.rdi);r.rsp-=0x40L;
        r.rdi=r.rdx;r.rsi=r.rcx;
        if(r.rcx==r.rdx) return finish(r,memory,true);
        memory.writeQword(r.rsp+0x58L,r.rbx);r.rbx=r.rcx+0x28L;
        if(r.rbx!=r.rdx) {
            do {
                budget.beforeStep(0x1A81210L,r.rbx);
                SmallRowBlocks295.capture(r,memory);
                if((int)r.rcx>memory.readDword(r.rsi)) {
                    r.r8-=r.rsi;r.rcx=r.rbx;r.rcx-=r.r8;
                    r.rdx=r.rsi;r.rcx+=0x28L;
                    SmallCopyCall295.invoke(entry.imageBaseBits(),r,memory,calls);
                    SmallRowBlocks295.restoreFront(r,memory);
                } else {
                    int previous=memory.readDword(r.rbx-0x28L);r.rax=r.rbx-0x28L;
                    if((int)r.rcx>previous) {
                        do {
                            budget.beforeStep(0x1A81280L,r.rax);
                            var copied=Copy40Row291.transfer(memory,r.rax,r.r8);
                            r.x0=copied.xmm0();r.x1=copied.xmm1();
                            r.r8=r.rax;r.rax-=0x28L;
                        } while((int)r.rcx>memory.readDword(r.rax));
                    }
                    memory.write128(r.r8,r.x2);memory.write128(r.r8+0x10L,r.x3);
                    memory.writeQword(r.r8+0x20L,r.x4.lowBits());
                }
                r.rbx+=0x28L;
            } while(r.rbx!=r.rdi);
        }
        return finish(r,memory,false);
    }

    private static GovernmentCrtBoundary185Api.NormalReturn finish(Registers r,
            GovernmentCrtBoundary185Api.Memory memory,boolean empty) {
        if(empty) {
            r.rsi=memory.readQword(r.rsp+0x60L);r.rax=r.rdi;
        } else {
            r.rbx=memory.readQword(r.rsp+0x58L);r.rax=r.rdi;
            r.rsi=memory.readQword(r.rsp+0x60L);
        }
        r.rsp+=0x40L;r.rdi=memory.readQword(r.rsp);r.rsp+=8L;
        long rip=memory.readQword(r.rsp);r.rsp+=8L;
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
}
