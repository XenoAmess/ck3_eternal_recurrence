package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held normal286 only; COPY remains a full-state opaque normal/tail port. */
public final class PassFullState299 {
    private PassFullState299() { }
    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        push(r,memory,r.rbp);push(r,memory,r.r14);push(r,memory,r.r15);r.rsp-=0x20L;
        r.rbp=memory.readQword(r.rsp+0x60L);r.r14=r.r9;r.rax=r.r8;r.r15=r.rdx;r.r10=r.rcx;
        if(r.r9<r.rbp) {
            memory.writeQword(r.rsp+0x40L,r.rbx);r.rcx=r.r9+r.r9*4L;
            memory.writeQword(r.rsp+0x48L,r.rsi);memory.writeQword(r.rsp+0x50L,r.rdi);
            memory.writeQword(r.rsp+0x58L,r.r12);r.r12=r.rcx*8L;
            do {
                budget.beforeStep(0x1A82380L,r.r10);
                r.rbp-=r.r14;r.rbx=r.r12+r.r10;r.rcx=r.r14;
                if(r.rbp<r.r14)r.rcx=r.rbp;
                r.rbp-=r.rcx;r.rcx+=r.r14;r.rdx=r.rcx+r.rcx*4L;
                r.rsi=r.r10+r.rdx*8L;r.rdx=r.rbx;
                for(;;) {
                    budget.beforeStep(0x1A823A2L,r.r10);
                    r.rcx=Integer.toUnsignedLong(memory.readDword(r.r10));r.rdi=r.rax+0x28L;
                    if(memory.readDword(r.rdx)>(int)r.rcx) {
                        var row=Copy40Row291.transfer(memory,r.rdx,r.rax);
                        r.x0=row.xmm0();r.x1=row.xmm1();r.rdx+=0x28L;
                        if(r.rdx==r.rsi){r.rbx-=r.r10;r.rdx=r.r10;break;}
                    } else {
                        var row=Copy40Row291.transfer(memory,r.r10,r.rax);
                        r.x0=row.xmm0();r.x1=row.xmm1();r.r10+=0x28L;
                        if(r.r10==r.rbx){r.rbx=r.rsi;r.rbx-=r.rdx;break;}
                    }
                    r.rax=r.rdi;
                }
                r.r8=r.rbx;r.rcx=r.rdi;
                long preSP=r.rsp;
                memory.writeQword(preSP-8L,entry.imageBaseBits()+0x1A82410L);
                r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(
                        0x1A8240BL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226860L,
                        preSP,r.volatileBits(),r.nonvolatileBits())));
                r.rax=r.rbx+r.rdi;r.r10=r.rsi;
            } while(r.r14<r.rbp);
            r.r12=memory.readQword(r.rsp+0x58L);r.rdi=memory.readQword(r.rsp+0x50L);
            r.rsi=memory.readQword(r.rsp+0x48L);r.rbx=memory.readQword(r.rsp+0x40L);
        }
        r.r15-=r.r10;r.rdx=r.r10;r.r8=r.r15;r.rcx=r.rax;r.rsp+=0x20L;
        r.r15=pop(r,memory);r.r14=pop(r,memory);r.rbp=pop(r,memory);
        return calls.tail(new GovernmentCrtBoundary185Api.Tail(0x1A82449L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226860L,
                new GovernmentCrtBoundary185Api.Entry(entry.imageBaseBits(),r.rsp,
                        r.volatileBits(),r.nonvolatileBits())));
    }
    private static void push(Registers r,GovernmentCrtBoundary185Api.Memory m,long bits) {
        r.rsp-=8L;m.writeQword(r.rsp,bits);
    }
    private static long pop(Registers r,GovernmentCrtBoundary185Api.Memory m) {
        long bits=m.readQword(r.rsp);r.rsp+=8L;return bits;
    }
}
