package org.xar.ck3.study.m6.full238;

import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;

/** Instruction-order MOVUPS copy and three equality-controlled reversal loops. */
public final class TransferInPlace238 {
    private TransferInPlace238() { }
    public static void run(Frame f) {
        var r=f.r;var m=f.memory;
        r.rax=m.readQword(r.rsi);
        do {
            f.budget.before(0x21A5240L,r.rbx,r.rdi);
            r.x0=m.read128(r.rbx);
            m.write128(r.rax,r.x0);
            r.rax+=0x10L;
            r.rbx+=0x10L;
        } while(r.rbx!=r.rdi);
        r.rax=(long)m.readDword(r.rsi+0xCL);
        r.r8=m.readQword(r.rsi);
        r.rcx=Integer.toUnsignedLong((int)(r.rax+r.r15));
        m.writeDword(r.rsi+0xCL,(int)r.rcx);
        r.rdx=r.rax;
        r.rdx<<=0x4;
        r.rdx+=r.r8;
        r.rax=(long)(int)r.rcx;
        r.rax<<=0x4;
        r.rax+=r.r8;
        if(r.r8==r.rdx || r.rdx==r.rax) return;
        r.r9=r.r8;
        r.rcx=r.rdx;
        while(true) {
            r.rcx-=0x10L;
            if(r.r9==r.rcx) break;
            f.budget.before(0x21A528EL,r.r9,r.rcx);
            r.x1=m.read128(r.r9);
            r.x0=m.read128(r.rcx);
            m.write128(r.r9,r.x0);
            m.write128(r.rcx,r.x1);
            r.r9+=0x10L;
            if(r.r9==r.rcx) break;
        }
        r.rcx=r.rax;
        while(true) {
            r.rcx-=0x10L;
            if(r.rdx==r.rcx) break;
            f.budget.before(0x21A52B9L,r.rdx,r.rcx);
            r.x1=m.read128(r.rdx);
            r.x0=m.read128(r.rcx);
            m.write128(r.rdx,r.x0);
            m.write128(r.rcx,r.x1);
            r.rdx+=0x10L;
            if(r.rdx==r.rcx) break;
        }
        if(r.r8==r.rax) return;
        while(true) {
            r.rax-=0x10L;
            if(r.r8==r.rax) break;
            f.budget.before(0x21A52DCL,r.r8,r.rax);
            r.x1=m.read128(r.r8);
            r.x0=m.read128(r.rax);
            m.write128(r.r8,r.x0);
            m.write128(r.rax,r.x1);
            r.r8+=0x10L;
            if(r.r8==r.rax) break;
        }
    }
}
