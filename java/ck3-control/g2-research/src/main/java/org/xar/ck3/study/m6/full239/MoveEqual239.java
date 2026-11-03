package org.xar.ck3.study.m6.full239;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;

/** Equal-allocator move path calls the actual opposite swap body with one owned5-byte push. */
public final class MoveEqual239 {
    private MoveEqual239() { }
    public static NormalReturn run(Frame f) {
        var r=f.r;var m=f.memory;
        r.rax=m.readQword(r.rcx);r.r8=0x4L;r.rdx=m.readQword(r.r14);
        f.indirect(0xB2EF06L,m.readQword(r.rax+0x10L));
        r.rbp=0L;r.rdx=r.r15;r.rcx=r.r14;
        m.writeQword(r.r14,r.rbp);m.writeQword(r.r14+0x8L,r.rbp);
        f.recursive(0xB2EF18L);
        r.rax=r.r14;r.rsp+=0x30L;
        r.r15=m.readQword(r.rsp);r.rsp+=0x8L;
        r.r14=m.readQword(r.rsp);r.rsp+=0x8L;
        r.rbp=m.readQword(r.rsp);r.rsp+=0x8L;
        long rip=m.readQword(r.rsp);r.rsp+=0x8L;
        return new NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
}
