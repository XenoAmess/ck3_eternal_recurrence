package org.xar.ck3.study.m6.full238;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.study.m6.full238.TransferFull238Api.*;

/** Owner fallback started during transport-only failures, before decoding any model result. */
public final class TransferFull238 {
    private TransferFull238() { }
    public static NormalReturn execute(Entry entry, Memory memory, Calls calls, Floating floating, Budget budget) {
        budget.before(0x21A5050L,entry.rspBits(),0L);
        Frame f=new Frame(entry,memory,calls,floating,budget,
                child->execute(child,memory,calls,floating,budget));
        var r=f.r;long s=f.entrySP;
        memory.writeQword(s+0x8L,r.rbx);
        memory.writeQword(s+0x10L,r.rbp);
        memory.writeQword(s+0x18L,r.rsi);
        memory.writeQword(s-0x8L,r.rdi);
        memory.writeQword(s-0x10L,r.r12);
        memory.writeQword(s-0x18L,r.r13);
        memory.writeQword(s-0x20L,r.r14);
        memory.writeQword(s-0x28L,r.r15);
        r.rsp=s-0x478L;
        r.r14=r.rdx;r.rsi=r.rcx;
        r.rcx=memory.readQword(r.rcx+0x10L);
        if(r.rcx==memory.readQword(r.rdx+0x10L)) TransferEqualAllocator238.run(f);
        else TransferDifferent238.run(f);
        r.rax=r.rsi;
        r.r11=r.rsp+0x450L;
        r.rbx=memory.readQword(r.r11+0x30L);
        r.rbp=memory.readQword(r.r11+0x38L);
        r.rsi=memory.readQword(r.r11+0x40L);
        r.rsp=r.r11;
        r.r15=memory.readQword(r.rsp);r.rsp+=0x8L;
        r.r14=memory.readQword(r.rsp);r.rsp+=0x8L;
        r.r13=memory.readQword(r.rsp);r.rsp+=0x8L;
        r.r12=memory.readQword(r.rsp);r.rsp+=0x8L;
        r.rdi=memory.readQword(r.rsp);r.rsp+=0x8L;
        long rip=memory.readQword(r.rsp);r.rsp+=0x8L;
        return new NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
}
