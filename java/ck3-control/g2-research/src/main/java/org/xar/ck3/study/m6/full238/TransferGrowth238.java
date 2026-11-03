package org.xar.ck3.study.m6.full238;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;

/** Exact growth block; unknown floating environment is an explicit three-operation port. */
public final class TransferGrowth238 {
    private TransferGrowth238() { }
    public static void run(Frame f) {
        var r=f.r;var m=f.memory;
        r.x0=new Bits128(Integer.toUnsignedLong((int)r.rax),0L);
        r.x0=f.floating.convertSignedDwords(r.x0);
        int multiplier=m.readDword(f.image+0x49F64F0L);
        r.x0=f.floating.multiplyLowSingle(r.x0,multiplier);
        r.rax=Integer.toUnsignedLong(f.floating.truncateLowSingle(r.x0));
        r.r13=Integer.toUnsignedLong((int)r.r15);
        if((int)r.r15<(int)r.rax) r.r13=r.rax;
        r.rax=m.readQword(r.rcx);
        r.rdx=Integer.toUnsignedLong((int)r.r13);
        r.rdx<<=0x4;
        r.r8=Integer.toUnsignedLong((int)(r.rbp+0x8L));
        long target=m.readQword(r.rax+0x8L);
        f.indirect(0x21A51B9L,target);
        r.r12=r.rax;
        r.rcx=r.rax;
        r.rcx-=r.rbx;
        do {
            f.budget.before(0x21A51D0L,r.rbx,r.rdi);
            r.x0=m.read128(r.rbx);
            m.write128(r.rcx+r.rbx,r.x0);
            r.rbx+=0x10L;
        } while(r.rbx!=r.rdi);
        r.rdx=m.readQword(r.rsi);
        r.rcx=(long)m.readDword(r.rsi+0xCL);
        r.rcx<<=0x4;
        r.rcx+=r.rdx;
        r.rax=(long)(int)r.r15;
        r.rax<<=0x4;
        r.rax+=r.r12;
        if(r.rdx!=r.rcx) {
            do {
                f.budget.before(0x21A5200L,r.rdx,r.rcx);
                r.x0=m.read128(r.rdx);
                m.write128(r.rax,r.x0);
                r.rax+=0x10L;
                r.rdx+=0x10L;
            } while(r.rdx!=r.rcx);
            r.rdx=m.readQword(r.rsi);
        }
        r.rcx=m.readQword(r.rsi+0x10L);
        r.rax=m.readQword(r.rcx);
        r.r8=0x8L;
        target=m.readQword(r.rax+0x10L);
        f.indirect(0x21A5223L,target);
        m.writeQword(r.rsi,r.r12);
        m.writeDword(r.rsi+0xCL,(int)r.r15);
        m.writeDword(r.rsi+0x8L,(int)r.r13);
    }
}
