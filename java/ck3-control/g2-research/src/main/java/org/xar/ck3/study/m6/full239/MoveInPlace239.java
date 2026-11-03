package org.xar.ck3.study.m6.full239;

import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;

/** Non-growth block does not replace opaque whole-state COPY or Reverse algorithms. */
public final class MoveInPlace239 {
    private MoveInPlace239() { }
    public static void run(Frame f) {
        var r=f.r;var m=f.memory;
        r.rcx=m.readQword(r.r14);r.r8=r.r12;r.rdx=r.rbx;
        Transfer4Calls239.direct(f,0xB2EFFEL,0x4226860L);
        r.rax=(long)m.readDword(r.r14+0xCL);r.rbx=m.readQword(r.r14);
        r.rdx=Integer.toUnsignedLong((int)(r.rax+r.r13));r.rdi=r.rbx+r.rax*0x4L;
        m.writeDword(r.r14+0xCL,(int)r.rdx);r.rax=(long)(int)r.rdx;r.rsi=r.rbx+r.rax*0x4L;
        if(r.rbx==r.rdi || r.rdi==r.rsi)return;
        r.rdx=r.rdi;r.rcx=r.rbx;Transfer4Calls239.direct(f,0xB2F02DL,0x4220AA4L);
        r.rdx=r.rsi;r.rcx=r.rdi;Transfer4Calls239.direct(f,0xB2F038L,0x4220AA4L);
        r.rdx=r.rsi;r.rcx=r.rbx;Transfer4Calls239.direct(f,0xB2F043L,0x4220AA4L);
    }
}
