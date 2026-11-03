package org.xar.ck3.study.m6.full239;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.study.m6.full238.TransferFull238Api.*;

/** Exact represented normal402-byte move body; all external child effects are185 opaque. */
public final class Move4Full239 {
    private Move4Full239() { }
    public static NormalReturn execute(Entry entry,Memory memory,Calls calls,Floating floating,Budget budget) {
        budget.before(0xB2EEE0L,entry.rspBits(),0L);
        Frame f=new Frame(entry,memory,calls,floating,budget,child->Swap4Full239.execute(child,memory,calls,floating,budget));
        var r=f.r;long s=f.entrySP;
        memory.writeQword(s-0x8L,r.rbp);memory.writeQword(s-0x10L,r.r14);memory.writeQword(s-0x18L,r.r15);
        r.rsp=s-0x48L;
        r.r14=r.rcx;r.r15=r.rdx;
        r.rcx=memory.readQword(r.rcx+0x10L);
        if(r.rcx==memory.readQword(r.rdx+0x10L)) return MoveEqual239.run(f);
        r.rbp=0L;
        memory.writeQword(r.rsp+0x50L,r.rbx);
        memory.writeDword(r.r14+0xCL,(int)r.rbp);
        r.rbx=memory.readQword(r.rdx);
        memory.writeQword(r.rsp+0x28L,r.r12);
        r.r12=(long)memory.readDword(r.rdx+0xCL);
        r.r12<<=0x2;
        r.rax=r.rbx+r.r12;
        if(r.rbx!=r.rax) {
            r.rax=Integer.toUnsignedLong(memory.readDword(r.r14+0x8L));
            memory.writeQword(r.rsp+0x58L,r.rsi);
            memory.writeQword(r.rsp+0x60L,r.rdi);
            memory.writeQword(r.rsp+0x20L,r.r13);
            r.r13=r.r12;r.r13>>=0x2;
            if((int)r.r13>(int)r.rax) MoveGrowth239.run(f);else MoveInPlace239.run(f);
            r.rdi=memory.readQword(r.rsp+0x60L);
            r.rsi=memory.readQword(r.rsp+0x58L);
            r.r13=memory.readQword(r.rsp+0x20L);
        }
        r.r12=memory.readQword(r.rsp+0x28L);
        r.rax=r.r14;
        r.rbx=memory.readQword(r.rsp+0x50L);
        memory.writeDword(r.r15+0xCL,(int)r.rbp);
        r.rsp+=0x30L;
        r.r15=memory.readQword(r.rsp);r.rsp+=0x8L;
        r.r14=memory.readQword(r.rsp);r.rsp+=0x8L;
        r.rbp=memory.readQword(r.rsp);r.rsp+=0x8L;
        long rip=memory.readQword(r.rsp);r.rsp+=0x8L;
        return new NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
}
