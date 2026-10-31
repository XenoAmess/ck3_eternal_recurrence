package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentEarlierRows161Api.Entry;
import org.xar.ck3.research.m5.GovernmentEarlierRows161Api.EntryPoint;
import org.xar.ck3.research.m5.GovernmentEarlierRows161Api.Join;
import org.xar.ck3.research.m5.GovernmentEarlierRows161Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Whole owner takeover after two incomplete rounds. Exact normal local ports, no downstream execution. */
public final class GovernmentEarlierRows161 {
    private GovernmentEarlierRows161() { }
    private static long u32(int bits) { return Integer.toUnsignedLong(bits); }
    private static void call(Registers r,Calls calls,long site,long target) {
        r.apply(calls.invoke(new OpaqueCall(site,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
    private static void xadd(Registers r,Memory memory,long counter) {
        r.rax=u32((int)r.r15);r.rax=u32(memory.lockedXaddDword(counter,(int)r.rax));
    }
    public static Join execute(Entry entry,Memory memory,Calls calls,LoopBudget budget) {
        Registers r=GovernmentEarlierRows161Api.registers(entry);
        long image=entry.imageBaseBits(),counter=image+0x5c6a9dcL;
        if(entry.entryPoint()==EntryPoint.AT_30A33B8) { r.r13=0;r.rcx=image+0x448d018L; }
        r.rsi=memory.readQword(r.rdi+0x450L);
        r.r12=((long)memory.readDword(r.rdi+0x45cL)<<4)+r.rsi;
        r.rbx=image+0x45d26f0L;
        if(r.rsi==r.r12)return GovernmentEarlierRows161Api.join(entry,r,0x30a35a4L);
        r.rax=image+0x48b7d98L;r.r13=0x158;
        do {
            budget.beforeIteration(0x30a33f4L,r.rsi,r.r12);
            if(memory.readUnsignedByte(r.rsi+0xcL)!=0) {
                memory.writeQword(r.rbp-0x70L,r.rax);
                memory.writeDword(r.rbp-0x68L,0x20);memory.writeByte(r.rbp-0x64L,0);
                r.r14=r.rdi+0x18L;
                r.rdx=memory.readQword(image+0x5c671d0L);
                if(r.rdx==0) {
                    memory.writeQword(r.rbp-0x80L,r.rcx);
                    memory.writeDword(r.rbp-0x78L,0x1e);memory.writeByte(r.rbp-0x74L,(int)r.rdx);
                    r.x0=memory.read128(r.rbp-0x80L);memory.write128(r.rbp+0x110L,r.x0);
                    r.r9=u32((int)r.rdx+0x64);r.r8=0;r.rdx=r.rbp+0x110L;r.rcx=u32((int)r.r15);
                    call(r,calls,0x30a3448L,0x3f8b640L);
                    r.rdx=memory.readQword(image+0x5c671d0L);
                }
                r.x0=memory.read128(r.rbp-0x70L);memory.write128(r.rbp+0xd0L,r.x0);
                r.rcx=r.rsi;
                call(r,calls,0x30a3463L,0x30aa170L);
                r.rax=u32((int)r.rax-(int)r.r15);
                if((int)r.rax==0) {
                    r.rbx=u32(memory.readDword(r.rsi+8));
                    call(r,calls,0x30a34f9L,0x3f8a7e0L);
                    r.rdx=u32((int)r.rbx);r.rcx=r.rax;
                    call(r,calls,0x30a3503L,0x3f8a6d0L);
                    r.rbx=r.rax;r.rcx=calls.readGsQword58();r.rdx=memory.readQword(r.rcx);
                    if(memory.readUnsignedByte(r.r13+r.rdx)==0) {
                        r.rcx=u32(memory.readDword(counter));
                        if((int)r.rcx<0x186a0) {
                            r.rcx=0x10000;
                            call(r,calls,0x30a3533L,0x3f5f970L);
                            if(r.rax!=0) {
                                memory.writeQword(r.rsp+0x38L,r.r14);
                                r.rcx=r.rbp+0xd0L;memory.writeQword(r.rsp+0x30L,r.rcx);
                                memory.writeQword(r.rsp+0x28L,r.rbx);
                                r.rcx=image+0x45d1a30L;memory.writeQword(r.rsp+0x20L,r.rcx);
                                r.r8=0x4b;r.rdx=image+0x45d2690L;r.rcx=r.rax;
                                call(r,calls,0x30a356fL,0x2850890L);
                                xadd(r,memory,counter);
                            }
                        }
                    }
                    r.rbx=image+0x45d26f0L;
                } else if((int)r.rax==(int)r.r15) {
                    r.rax=calls.readGsQword58();r.rcx=memory.readQword(r.rax);
                    if(memory.readUnsignedByte(r.r13+r.rcx)==0) {
                        r.rax=u32(memory.readDword(counter));
                        if((int)r.rax<0x186a0) {
                            r.rcx=0x10000;
                            call(r,calls,0x30a34a9L,0x3f5f970L);
                            if(r.rax!=0) {
                                memory.writeQword(r.rsp+0x30L,r.r14);
                                r.rcx=r.rbp+0xd0L;memory.writeQword(r.rsp+0x28L,r.rcx);
                                memory.writeQword(r.rsp+0x20L,r.rbx);
                                r.r9=4;r.r8=u32((int)r.r9+0x4c);r.rdx=image+0x45d2690L;r.rcx=r.rax;
                                call(r,calls,0x30a34e1L,0xc0e0b0L);
                                xadd(r,memory,counter);
                            }
                        }
                    }
                }
                r.rax=image+0x48b7d98L;
            }
            r.rsi+=0x10L;
            r.rcx=image+0x448d018L;
        } while(r.rsi!=r.r12);
        return GovernmentEarlierRows161Api.join(entry,r,0x30a35a1L);
    }
}
