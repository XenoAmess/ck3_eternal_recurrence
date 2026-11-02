package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held normal577B, exact represented state over owned memory; opaque COPY ports remain explicit. */
public final class RotateFullState292 {
    private RotateFullState292() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(r.rsp+0x18L,r.r14);
        r.rsp-=8L;memory.writeQword(r.rsp,r.r15);
        r.rsp-=0x20L;
        r.r14=r.r8;r.r15=r.rcx;
        if(r.r9==0L) {
            r.rax=r.r8;
            return earlyReturn(r,memory);
        }
        r.rax=memory.readQword(r.rsp+0x50L);
        if(r.rax==0L) {
            r.rax=r.r15;
            return earlyReturn(r,memory);
        }
        r.rcx=memory.readQword(r.rsp+0x60L);
        memory.writeQword(r.rsp+0x30L,r.rbx);
        memory.writeQword(r.rsp+0x38L,r.rdi);

        if(r.r9<=r.rax && r.r9<=r.rcx) {
            r.r8=memory.readQword(r.rsp+0x58L);
            r.rcx=r.r15;
            callCopy40(entry.imageBaseBits(),r,memory,budget);
            r.r14-=r.rdx;
            r.rcx=r.r15;r.r8=r.r14;r.rdi=r.rax;
            callCopy(entry.imageBaseBits(),r,memory,calls,0xF0F1D0L);
            r.rdi-=memory.readQword(r.rsp+0x58L);
            r.rbx=r.r14+r.r15;
            r.rdx=memory.readQword(r.rsp+0x58L);
            r.r8=r.rdi;r.rcx=r.rbx;
            callCopy(entry.imageBaseBits(),r,memory,calls,0xF0F1E9L);
            r.rax=r.rbx;
        } else if(r.rax<=r.rcx) {
            r.rdi=memory.readQword(r.rsp+0x58L);r.rbx=r.rdi;
            if(r.rdx!=r.r14) {
                r.rax=r.rdx;
                do {
                    budget.beforeStep(0xF0F210L,r.rax);
                    var copied=Copy40Row291.transfer(memory,r.rax,r.rbx);
                    r.x0=copied.xmm0();r.x1=copied.xmm1();
                    r.rax+=0x28L;r.rbx+=0x28L;
                } while(r.rax!=r.r14);
            }
            r.rdx-=r.r15;r.r14-=r.rdx;
            r.r8=r.rdx;r.rcx=r.r14;r.rdx=r.r15;
            callCopy(entry.imageBaseBits(),r,memory,calls,0xF0F244L);
            r.rbx-=r.rdi;r.rdx=r.rdi;r.r8=r.rbx;r.rcx=r.r15;
            callCopy(entry.imageBaseBits(),r,memory,calls,0xF0F255L);
            r.rax=r.rbx+r.r15;
        } else {
            if(r.r15!=r.rdx) {
                if(r.rdx==r.r14) {
                    r.r14=r.r15;
                } else {
                    r.rcx=r.r15;r.rax=r.rdx;
                    reverse(r,memory,budget,0xF0F280L);
                    r.rcx=r.rdx;r.rax=r.r14;
                    reverse(r,memory,budget,0xF0F2D0L);
                    r.rcx=r.r15;r.rax=r.r14;
                    if(r.r15!=r.r14) reverse(r,memory,budget,0xF0F320L);
                    r.r14-=r.rdx;
                    r.rax=0x6666666666666667L;
                    long high=Math.multiplyHigh(r.rax,r.r14);
                    r.rax*=r.r14;r.rdx=high;
                    r.rdx>>=4;r.rax=r.rdx;r.rax>>>=63;r.rdx+=r.rax;
                    r.rax=r.rdx+r.rdx*4L;r.r14=r.r15+r.rax*8L;
                }
            }
            r.rax=r.r14;
        }
        r.rbx=memory.readQword(r.rsp+0x30L);
        r.rdi=memory.readQword(r.rsp+0x38L);
        return earlyReturn(r,memory);
    }

    private static void reverse(Registers r,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,long header) {
        for(;;) {
            budget.beforeStep(header,r.rax);
            r.rax-=0x28L;
            if(r.rcx==r.rax) return;
            var swapped=RotateSwap40Block292.transfer(memory,r.rcx,r.rax);
            r.rcx=swapped.lowAfterBits();
            r.x0=swapped.xmm0();r.x1=swapped.xmm1();r.x2=swapped.xmm2();
            r.x3=swapped.xmm3();r.x4=swapped.xmm4();
            if(r.rcx==r.rax) return;
        }
    }

    private static void callCopy40(long image,Registers r,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        long expected=image+0xF0F1C4L;
        memory.writeQword(r.rsp-8L,expected);
        var offered=r.nonvolatileBits();
        var returned=Copy40FullState291.execute(new GovernmentCrtBoundary185Api.Entry(
                image,r.rsp-8L,r.volatileBits(),offered),memory,budget);
        if(returned.returnRipBits()!=expected || returned.callerRspBits()!=r.rsp
                || !returned.nonvolatileBits().equals(offered))
            throw new UnsupportedOperationException("F1BF child left the represented normal continuation");
        r.apply(returned.volatileBits());
    }

    private static void callCopy(long image,Registers r,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,long site) {
        memory.writeQword(r.rsp-8L,image+site+5L);
        r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226860L,
                r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }

    private static GovernmentCrtBoundary185Api.NormalReturn earlyReturn(Registers r,
            GovernmentCrtBoundary185Api.Memory memory) {
        r.r14=memory.readQword(r.rsp+0x40L);r.rsp+=0x20L;
        r.r15=memory.readQword(r.rsp);r.rsp+=8L;
        long rip=memory.readQword(r.rsp);r.rsp+=8L;
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
}
