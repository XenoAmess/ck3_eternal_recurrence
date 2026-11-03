package org.xar.ck3.study.m6.full239;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.study.m6.full238.TransferFull238Api.*;

/** Exact227-byte normal helper, including its real path-dependent volatile RAX. */
public final class Swap4Full239 {
    private Swap4Full239() { }
    public static NormalReturn execute(Entry entry,Memory memory,Calls calls,Floating floating,Budget budget) {
        budget.before(0xB2EDF0L,entry.rspBits(),0L);
        Frame f=new Frame(entry,memory,calls,floating,budget,child->Move4Full239.execute(child,memory,calls,floating,budget));
        return executePreparedFrame(f);
    }

    /** Same source body once, on the caller-prepared actual Frame; no entry budget or replay here. */
    public static NormalReturn executePreparedFrame(Frame f) {
        Memory memory=f.memory;
        var r=f.r;long s=f.entrySP;
        memory.writeQword(s+0x8L,r.rbx);memory.writeQword(s+0x10L,r.rsi);memory.writeQword(s-0x8L,r.rdi);
        r.rsp=s-0x458L;
        r.rdi=r.rcx;r.rax=memory.readQword(r.rdx+0x10L);
        if(memory.readQword(r.rcx+0x10L)==r.rax) {
            r.rcx=memory.readQword(r.rcx);r.rax=memory.readQword(r.rdx);
            memory.writeQword(r.rdi,r.rax);memory.writeQword(r.rdx,r.rcx);
            r.rcx=Integer.toUnsignedLong(memory.readDword(r.rdi+0xCL));r.rax=Integer.toUnsignedLong(memory.readDword(r.rdx+0xCL));
            memory.writeDword(r.rdi+0xCL,(int)r.rax);memory.writeDword(r.rdx+0xCL,(int)r.rcx);
            r.rcx=Integer.toUnsignedLong(memory.readDword(r.rdi+0x8L));r.rax=Integer.toUnsignedLong(memory.readDword(r.rdx+0x8L));
            memory.writeDword(r.rdi+0x8L,(int)r.rax);memory.writeDword(r.rdx+0x8L,(int)r.rcx);
        } else {
            r.rcx=Integer.toUnsignedLong(memory.readDword(r.rdx+0xCL));r.rbx=r.rdi;
            boolean less=(int)r.rcx<memory.readDword(r.rdi+0xCL);
            if(less)r.rbx=r.rdx;if(!less)r.rdi=r.rdx;
            r.rax=f.image+0x44BBB10L;memory.writeQword(r.rsp+0x40L,r.rax);
            r.rax=f.image+0x54DE268L;memory.writeQword(r.rsp+0x448L,r.rax);
            r.rsi=0L;memory.writeQword(r.rsp+0x20L,r.rsi);memory.writeQword(r.rsp+0x28L,r.rsi);
            r.rax=r.rsp+0x40L;memory.writeQword(r.rsp+0x30L,r.rax);
            r.rdx=r.rbx;r.rcx=r.rsp+0x20L;f.recursive(0xB2EE82L);
            r.rdx=r.rdi;r.rcx=r.rbx;f.recursive(0xB2EE8EL);
            r.rdx=r.rsp+0x20L;r.rcx=r.rdi;f.recursive(0xB2EE9BL);
            r.rdx=memory.readQword(r.rsp+0x20L);
            if(r.rdx!=0L) {
                memory.writeDword(r.rsp+0x2CL,(int)r.rsi);
                r.rcx=memory.readQword(r.rsp+0x30L);r.rax=memory.readQword(r.rcx);
                r.r8=Integer.toUnsignedLong((int)(r.rsi+0x4L));
                f.indirect(0xB2EEBBL,memory.readQword(r.rax+0x10L));
            }
        }
        r.r11=r.rsp+0x450L;
        r.rbx=memory.readQword(r.r11+0x10L);r.rsi=memory.readQword(r.r11+0x18L);
        r.rsp=r.r11;r.rdi=memory.readQword(r.rsp);r.rsp+=0x8L;
        long rip=memory.readQword(r.rsp);r.rsp+=0x8L;
        return new NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
}
