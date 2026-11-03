package org.xar.ck3.study.m6.full238;

import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;

/** Owner fallback for the exact different-allocator branch prefix and shared source clear. */
public final class TransferDifferent238 {
    private TransferDifferent238() { }
    public static void run(Frame f) {
        var r=f.r;var m=f.memory;
        r.rbp=0L;
        m.writeDword(r.rsi+0xCL,(int)r.rbp);
        r.r15=(long)m.readDword(r.rdx+0xCL);
        r.r15<<=0x4;
        r.rbx=m.readQword(r.rdx);
        r.rdi=r.r15+r.rbx;
        if(r.rbx!=r.rdi) {
            r.r15>>=0x4;
            r.rax=Integer.toUnsignedLong(m.readDword(r.rsi+0x8L));
            if((int)r.r15>(int)r.rax) TransferGrowth238.run(f);
            else TransferInPlace238.run(f);
        }
        m.writeDword(r.r14+0xCL,(int)r.rbp);
    }
}
