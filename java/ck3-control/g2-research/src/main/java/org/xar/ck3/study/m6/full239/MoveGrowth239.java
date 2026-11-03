package org.xar.ck3.study.m6.full239;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;

/** Growth path keeps all actual full-state COPY/free boundaries, including zero-byte COPY. */
public final class MoveGrowth239 {
    private MoveGrowth239() { }
    public static void run(Frame f) {
        var r=f.r;var m=f.memory;
        r.x0=new Bits128(Integer.toUnsignedLong((int)r.rax),0L);
        r.r8=Integer.toUnsignedLong((int)(r.rbp+0x4L));
        r.x0=f.floating.convertSignedDwords(r.x0);
        r.rsi=Integer.toUnsignedLong((int)r.r13);
        int multiplier=m.readDword(f.image+0x49F64F0L);
        r.x0=f.floating.multiplyLowSingle(r.x0,multiplier);
        r.rax=Integer.toUnsignedLong(f.floating.truncateLowSingle(r.x0));
        if((int)r.r13<(int)r.rax)r.rsi=r.rax;
        r.rax=m.readQword(r.rcx);r.rdx=Integer.toUnsignedLong((int)r.rsi);r.rdx<<=0x2;
        f.indirect(0xB2EF9EL,m.readQword(r.rax+0x8L));
        r.rdx=m.readQword(r.r14);r.r8=0L;r.rcx=r.rax;r.rdi=r.rax;
        Transfer4Calls239.direct(f,0xB2EFADL,0x4226860L);
        r.r8=r.r12;r.rdx=r.rbx;r.rcx=r.rdi;
        Transfer4Calls239.direct(f,0xB2EFBBL,0x4226860L);
        r.r8=(long)m.readDword(r.r14+0xCL);r.rdx=m.readQword(r.r14);
        r.rax=(long)(int)r.r13;r.r8<<=0x2;r.rcx=r.rdi+r.rax*0x4L;
        Transfer4Calls239.direct(f,0xB2EFD2L,0x4226860L);
        r.rcx=m.readQword(r.r14+0x10L);r.r8=Integer.toUnsignedLong((int)(r.rbp+0x4L));
        r.rdx=m.readQword(r.r14);r.rax=m.readQword(r.rcx);
        f.indirect(0xB2EFE5L,m.readQword(r.rax+0x10L));
        m.writeQword(r.r14,r.rdi);m.writeDword(r.r14+0xCL,(int)r.r13);m.writeDword(r.r14+0x8L,(int)r.rsi);
    }
}
