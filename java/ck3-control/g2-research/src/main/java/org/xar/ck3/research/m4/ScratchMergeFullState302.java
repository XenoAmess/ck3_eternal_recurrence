package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Whole held normal [1A82450,1A82758), entered at actual function SP.
 * COPY remains an opaque full185 port. Row reuse qualifies normal memory/register
 * results, not exceptional register state across reordered pure GPR increments.
 */
public final class ScratchMergeFullState302 {
    private ScratchMergeFullState302() { }

    public static NormalReturn execute(Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        long image=entry.imageBaseBits();
        memory.writeQword(r.rsp+0x10L,r.rbx);
        r.rsp-=8L;memory.writeQword(r.rsp,r.rdi);r.rsp-=0x60L;
        r.r10=r.rdx;r.rbx=r.rcx;
        r.rdx=memory.readQword(r.rsp+0x90L);r.rdi=r.r8;
        r.rcx=memory.readQword(r.rsp+0xA0L);
        if(r.r9<=r.rdx && r.r9<=r.rcx) {
            r.rdx=memory.readQword(r.rsp+0x98L);r.r8=r.rdx;
            if(r.rbx!=r.r10) {
                r.rax=r.rbx;
                do {
                    budget.beforeStep(0x1A824A0L,r.rax);
                    row(r,memory,r.rax,r.r8);r.rax+=0x28L;r.r8+=0x28L;
                } while(r.rax!=r.r10);
            }
            r.x0=memory.read128(r.r10);
            r.r11=r.r8-0x28L;r.rcx=r.rbx+0x28L;
            memory.write128(r.rbx,r.x0);r.r9=r.r10+0x28L;
            r.x1=memory.read128(r.r10+0x10L);memory.write128(r.rbx+0x10L,r.x1);
            r.x0=new Bits128(memory.readQword(r.r10+0x20L),0L);memory.writeQword(r.rbx+0x20L,r.x0.lowBits());
            while(true) {
                budget.beforeStep(0x1A824F0L,r.rcx);
                int eax=memory.readDword(r.rdx);r.rax=Integer.toUnsignedLong(eax);
                r.rbx=r.rcx+0x28L;
                if(memory.readDword(r.r9)>eax) {
                    row(r,memory,r.r9,r.rcx);r.r9+=0x28L;
                    if(r.r9==r.rdi) {
                        r.r8-=r.rdx;r.rcx=r.rbx;
                        restoreBxDi(r,memory);
                        return calls.tail(new Tail(0x1A8252FL,TargetKind.DIRECT_RVA,0x4226860L,
                                new Entry(image,r.rsp,r.volatileBits(),r.nonvolatileBits())));
                    }
                } else {
                    row(r,memory,r.rdx,r.rcx);r.rdx+=0x28L;
                    if(r.rdx==r.r11)break;
                }
                r.rcx=r.rbx;
            }
            r.x0=memory.read128(r.r11);r.rdi-=r.r9;r.rdx=r.r9;r.r8=r.rdi;r.rcx=r.rbx;
            memory.write128(r.rsp+0x40L,r.x0);
            r.x0=memory.read128(r.r11+0x10L);memory.write128(r.rsp+0x50L,r.x0);
            r.x0=new Bits128(memory.readQword(r.r11+0x20L),0L);memory.writeQword(r.rsp+0x90L,r.x0.lowBits());
            invoke(image,0x1A82588L,r,memory,calls);
            r.x0=memory.read128(r.rsp+0x40L);r.x1=memory.read128(r.rsp+0x50L);
            memory.write128(r.rdi+r.rbx,r.x0);
            r.x0=new Bits128(memory.readQword(r.rsp+0x90L),0L);
            memory.write128(r.rdi+r.rbx+0x10L,r.x1);memory.writeQword(r.rdi+r.rbx+0x20L,r.x0.lowBits());
            restoreBxDi(r,memory);return returned(r,memory);
        }
        if(r.rdx>r.rcx) {
            return ScratchGeneralTail301.execute(new Entry(image,r.rsp,r.volatileBits(),r.nonvolatileBits()),memory,calls,budget);
        }
        memory.writeQword(r.rsp+0x70L,r.rsi);
        r.rsi=memory.readQword(r.rsp+0x98L);r.rdx=r.rsi;
        if(r.r10!=r.rdi) {
            r.rax=r.r10;
            do {
                budget.beforeStep(0x1A825E0L,r.rax);
                row(r,memory,r.rax,r.rdx);r.rax+=0x28L;r.rdx+=0x28L;
            } while(r.rax!=r.rdi);
        }
        r.x0=memory.read128(r.r10-0x28L);r.r8=r.r10-0x28L;r.rdx-=0x28L;r.r9=r.rdi-0x28L;
        memory.write128(r.r9,r.x0);r.x1=memory.read128(r.r8+0x10L);memory.write128(r.r9+0x10L,r.x1);
        r.x0=new Bits128(memory.readQword(r.r8+0x20L),0L);memory.writeQword(r.r9+0x20L,r.x0.lowBits());
        r.r8-=0x28L;
        while(true) {
            budget.beforeStep(0x1A82640L,r.r8);
            int eax=memory.readDword(r.r8);r.rax=Integer.toUnsignedLong(eax);
            r.rcx=r.r9-0x28L;r.r9=r.rcx;
            if(memory.readDword(r.rdx)>eax) {
                row(r,memory,r.r8,r.rcx);
                if(r.rbx!=r.r8){r.r8-=0x28L;continue;}
                r.x0=memory.read128(r.rdx);r.rcx-=0x28L;memory.write128(r.rcx,r.x0);
                r.x1=memory.read128(r.rdx+0x10L);memory.write128(r.rcx+0x10L,r.x1);
                r.x0=new Bits128(memory.readQword(r.rdx+0x20L),0L);r.rdx-=r.rsi;
                memory.writeQword(r.rcx+0x20L,r.x0.lowBits());r.r8=r.rdx;r.rcx-=r.rdx;r.rdx=r.rsi;
                r.rsi=memory.readQword(r.rsp+0x70L);restoreBxDi(r,memory);
                return calls.tail(new Tail(0x1A826A5L,TargetKind.DIRECT_RVA,0x4226860L,
                        new Entry(image,r.rsp,r.volatileBits(),r.nonvolatileBits())));
            }
            row(r,memory,r.rdx,r.rcx);r.rdx-=0x28L;
            if(r.rsi!=r.rdx)continue;
            r.x0=memory.read128(r.r8);r.rcx-=0x28L;r.rdx=r.rbx;memory.write128(r.rcx,r.x0);
            r.x1=memory.read128(r.r8+0x10L);memory.write128(r.rcx+0x10L,r.x1);
            r.x0=new Bits128(memory.readQword(r.r8+0x20L),0L);r.r8-=r.rbx;
            memory.writeQword(r.rcx+0x20L,r.x0.lowBits());r.rcx-=r.r8;
            invoke(image,0x1A826F7L,r,memory,calls);
            r.x0=memory.read128(r.rsi);memory.write128(r.rbx,r.x0);
            r.x1=memory.read128(r.rsi+0x10L);memory.write128(r.rbx+0x10L,r.x1);
            r.x0=new Bits128(memory.readQword(r.rsi+0x20L),0L);
            r.rsi=memory.readQword(r.rsp+0x70L);memory.writeQword(r.rbx+0x20L,r.x0.lowBits());
            restoreBxDi(r,memory);return returned(r,memory);
        }
    }

    private static void row(Registers r,GovernmentCrtBoundary185Api.Memory memory,long source,long destination) {
        Copy40Row291.Result v=Copy40Row291.transfer(memory,source,destination);r.x0=v.xmm0();r.x1=v.xmm1();
    }
    private static void invoke(long image,long site,Registers r,GovernmentCrtBoundary185Api.Memory memory,GovernmentCrtBoundary185Api.Calls calls) {
        memory.writeQword(r.rsp-8L,image+site+5L);
        r.apply(calls.invoke(new Call(site,TargetKind.DIRECT_RVA,0x4226860L,r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
    private static void restoreBxDi(Registers r,GovernmentCrtBoundary185Api.Memory memory) {
        r.rbx=memory.readQword(r.rsp+0x78L);r.rsp+=0x60L;r.rdi=memory.readQword(r.rsp);r.rsp+=8L;
    }
    private static NormalReturn returned(Registers r,GovernmentCrtBoundary185Api.Memory memory) {
        long rip=memory.readQword(r.rsp);r.rsp+=8L;return new NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
}
