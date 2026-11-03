package org.xar.ck3.study.m6.full238;

import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;

/** Same-allocator branch including real recursive frames and temporary cleanup. */
public final class TransferEqualAllocator238 {
    private TransferEqualAllocator238() { }
    public static void run(Frame f) {
        var r=f.r;var m=f.memory;
        r.rax=m.readQword(r.rcx);
        r.r8=0x8L;
        r.rdx=m.readQword(r.rsi);
        f.indirect(0x21A508FL,m.readQword(r.rax+0x10L));
        r.rbp=0L;
        m.writeQword(r.rsi,r.rbp);
        m.writeQword(r.rsi+0x8L,r.rbp);
        r.rax=m.readQword(r.r14+0x10L);
        if(m.readQword(r.rsi+0x10L)==r.rax) {
            r.rax=m.readQword(r.r14);
            m.writeQword(r.rsi,r.rax);
            m.writeQword(r.r14,r.rbp);
            r.rcx=Integer.toUnsignedLong(m.readDword(r.rsi+0xCL));
            r.rax=Integer.toUnsignedLong(m.readDword(r.r14+0xCL));
            m.writeDword(r.rsi+0xCL,(int)r.rax);
            m.writeDword(r.r14+0xCL,(int)r.rcx);
            r.rcx=Integer.toUnsignedLong(m.readDword(r.rsi+0x8L));
            r.rax=Integer.toUnsignedLong(m.readDword(r.r14+0x8L));
            m.writeDword(r.rsi+0x8L,(int)r.rax);
            m.writeDword(r.r14+0x8L,(int)r.rcx);
            return;
        }
        r.rax=Integer.toUnsignedLong(m.readDword(r.r14+0xCL));
        r.rdi=r.rsi;
        boolean negative=(int)r.rax<0;
        if(negative) r.rdi=r.r14;
        r.rbx=r.rsi;
        if(!negative) r.rbx=r.r14;
        r.rax=f.image+0x46B3A90L;
        m.writeQword(r.rsp+0x40L,r.rax);
        r.rax=f.image+0x54DE260L;
        m.writeQword(r.rsp+0x448L,r.rax);
        m.writeQword(r.rsp+0x20L,r.rbp);
        m.writeQword(r.rsp+0x28L,r.rbp);
        r.rax=r.rsp+0x40L;
        m.writeQword(r.rsp+0x30L,r.rax);
        r.rdx=r.rdi;
        r.rcx=r.rsp+0x20L;
        f.recursive(0x21A511AL);
        r.rdx=r.rbx;
        r.rcx=r.rdi;
        f.recursive(0x21A5126L);
        r.rdx=r.rsp+0x20L;
        r.rcx=r.rbx;
        f.recursive(0x21A5133L);
        r.rdx=m.readQword(r.rsp+0x20L);
        if(r.rdx==0L) return;
        m.writeDword(r.rsp+0x2CL,(int)r.rbp);
        r.rcx=m.readQword(r.rsp+0x30L);
        r.rax=m.readQword(r.rcx);
        r.r8=0x8L;
        f.indirect(0x21A5159L,m.readQword(r.rax+0x10L));
    }
}
