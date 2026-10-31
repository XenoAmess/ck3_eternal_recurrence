package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.Entry;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.Memory;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.NormalReturn;

/** Whole owner135B after two source-rejected candidates; updater320 remains a separate concrete method. */
public final class GovernmentByteHash169 {
    private GovernmentByteHash169() { }
    private static long u32(int bits) {return Integer.toUnsignedLong(bits);}
    public static NormalReturn execute(Entry entry,Memory memory,LoopBudget budget) {
        var r=GovernmentCompaction160Api.registers(new GovernmentCompaction160Api.Entry(
                entry.imageBaseBits(),entry.frameRspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeDword(r.rsp+8,(int)r.rcx);
        r.rsp-=8;memory.writeQword(r.rsp,r.rbx);
        r.rsp-=0x20;
        r.rax=0;r.rcx=r.rsp+0x30;r.rbx=u32((int)r.r8);
        memory.writeDword(r.rsp+0x30,(int)r.rax);
        r.r9=u32((int)r.r8);memory.writeDword(r.rsp+0x40,(int)r.rax);
        r.r8=r.rdx;r.rdx=r.rsp+0x40;
        long expectedRip=entry.imageBaseBits()+0x3f7e24bL;
        memory.writeQword(r.rsp-8,expectedRip);
        var before=r.nonvolatileBits();
        NormalReturn post=GovernmentByteUpdate169.execute(new Entry(entry.imageBaseBits(),r.rsp-8,
                r.volatileBits(),before,entry.mxcsr()),memory,budget);
        if(post.returnRipBits()!=expectedRip||post.callerRspBits()!=r.rsp
                ||!post.nonvolatileBits().equals(before)||!post.mxcsr().equals(entry.mxcsr())) {
            throw new UnsupportedOperationException("updater normal CALL boundary mismatch");
        }
        r.apply(post.volatileBits());
        r.rdx=u32(memory.readDword(r.rsp+0x40));r.r8=u32((int)r.rdx);
        r.rcx=u32(memory.readDword(r.rsp+0x30));r.r9=u32((int)r.rcx);r.r8&=3;
        if(r.r8!=0) {
            r.rcx=4;r.rcx=u32((int)r.rcx-(int)r.r8);r.rcx=u32((int)r.rcx<<3);
            r.rdx=u32((int)r.rdx>>>((int)r.rcx&31));
            r.rax=u32((int)r.rdx*0xcc9e2d51);r.rax=u32(Integer.rotateLeft((int)r.rax,15));
            r.rcx=u32((int)r.rax*0x1b873593);r.rcx=u32((int)r.rcx^(int)r.r9);
        }
        r.rcx=u32((int)r.rcx^(int)r.rbx);r.rax=u32((int)r.rcx);r.rax>>>=16;
        r.rax=u32((int)r.rax^(int)r.rcx);r.rcx=u32((int)r.rax*0x85ebca6b);
        r.rax=u32((int)r.rcx);r.rax>>>=13;r.rax=u32((int)r.rax^(int)r.rcx);
        r.rcx=u32((int)r.rax*0xc2b2ae35);r.rax=u32((int)r.rcx);r.rax>>>=16;
        r.rax=u32((int)r.rax^(int)r.rcx);
        r.rsp+=0x20;r.rbx=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);r.rsp+=8;
        return new NormalReturn(r.volatileBits(),r.nonvolatileBits(),rip,r.rsp,post.mxcsr());
    }
}
