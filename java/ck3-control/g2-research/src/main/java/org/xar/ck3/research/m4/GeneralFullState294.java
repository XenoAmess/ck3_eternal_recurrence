package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held normal472B raw partition/frame path, actual293 child; no flags/DF/EH qualification. */
public final class GeneralFullState294 {
    private GeneralFullState294() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(r.rsp+8L,r.rbx);memory.writeQword(r.rsp+0x10L,r.rbp);
        memory.writeQword(r.rsp+0x18L,r.rsi);memory.writeQword(r.rsp+0x20L,r.rdi);
        push(r,memory,r.r12);push(r,memory,r.r14);push(r,memory,r.r15);r.rsp-=0x60L;
        r.r14=memory.readQword(r.rsp+0xA0L);
        r.rbp=r.r9;r.r12=r.r8;r.rdi=r.rdx;r.rsi=r.rcx;r.r15=0x6666666666666667L;
        if(r.r9<=r.r14) {
            r.r8-=r.rdx;r.r11=r.r9;r.r9=r.rdx;r.r11>>=1;
            r.rax=r.r11+r.r11*4L;r.rbx=r.rcx+r.rax*8L;
            r.rax=r.r15;divide(r,r.r8);
            if(r.rdx>0) {
                r.r10=Integer.toUnsignedLong(memory.readDword(r.rbx));
                do {
                    budget.beforeStep(0x1A82F80L,r.r9);
                    GeneralSearchStep294.step(r,memory,true);
                } while(r.rdx>0);
            }
            r.rcx=r.r9;r.rax=r.r15;r.rcx-=r.rdi;divide(r,r.rcx);
            memory.writeQword(r.rsp+0x58L,r.rdx);
            memory.writeQword(r.rsp+0x50L,r.r11);
            memory.writeQword(r.rsp+0x48L,r.r9);
            memory.writeQword(r.rsp+0x40L,r.rbx);
        } else {
            r.r11=r.r14;r.rcx=r.rdi;r.r11>>=1;r.rcx-=r.rsi;r.r9=r.rsi;
            r.rax=r.r11+r.r11*4L;r.rbx=r.rdx+r.rax*8L;
            r.rax=r.r15;divide(r,r.rcx);
            if(r.rdx>0) {
                r.r10=Integer.toUnsignedLong(memory.readDword(r.rbx));
                do {
                    budget.beforeStep(0x1A83020L,r.r9);
                    GeneralSearchStep294.step(r,memory,false);
                } while(r.rdx>0);
            }
            memory.writeQword(r.rsp+0x58L,r.r11);
            r.rcx=r.r9;r.rcx-=r.rsi;r.rax=r.r15;divide(r,r.rcx);
            memory.writeQword(r.rsp+0x50L,r.rdx);
            memory.writeQword(r.rsp+0x48L,r.rbx);
            memory.writeQword(r.rsp+0x40L,r.r9);
        }
        r.rax=Integer.toUnsignedLong(memory.readUnsignedByte(r.rsp+0xB8L));
        r.r9=r.rbp;memory.writeByte(r.rsp+0x38L,(int)r.rax);r.r8=r.r12;
        r.rax=memory.readQword(r.rsp+0xB0L);r.rdx=r.rdi;
        memory.writeQword(r.rsp+0x30L,r.rax);r.rcx=r.rsi;
        r.rax=memory.readQword(r.rsp+0xA8L);memory.writeQword(r.rsp+0x28L,r.rax);
        memory.writeQword(r.rsp+0x20L,r.r14);
        GeneralBridgeCall294.invoke(entry.imageBaseBits(),r,memory,calls,budget);

        r.r11=r.rsp+0x60L;
        r.rbx=memory.readQword(r.r11+0x20L);r.rbp=memory.readQword(r.r11+0x28L);
        r.rsi=memory.readQword(r.r11+0x30L);r.rdi=memory.readQword(r.r11+0x38L);
        r.rsp=r.r11;r.r15=pop(r,memory);r.r14=pop(r,memory);r.r12=pop(r,memory);
        long rip=memory.readQword(r.rsp);r.rsp+=8L;
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }

    private static void divide(Registers r,long operand) {
        long high=Math.multiplyHigh(r.rax,operand);r.rax*=operand;r.rdx=high;
        r.rdx>>=4;r.rax=r.rdx;r.rax>>>=63;r.rdx+=r.rax;
    }
    private static void push(Registers r,GovernmentCrtBoundary185Api.Memory m,long bits) {
        r.rsp-=8L;m.writeQword(r.rsp,bits);
    }
    private static long pop(Registers r,GovernmentCrtBoundary185Api.Memory m) {
        long bits=m.readQword(r.rsp);r.rsp+=8L;return bits;
    }
}
