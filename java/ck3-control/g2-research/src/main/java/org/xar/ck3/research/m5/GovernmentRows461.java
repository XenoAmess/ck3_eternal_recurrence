package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Whole owner implementation after two rejected model rounds; owned effects, normal region only. */
public final class GovernmentRows461 {
    private GovernmentRows461() { }
    private static long u32(int bits) { return Integer.toUnsignedLong(bits); }
    private static void call(Registers r, GovernmentPrimaryTail155Api.Calls calls, long site, long target) {
        r.apply(calls.invoke(new OpaqueCall(site,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }

    public static GovernmentRows461Api.Join execute(GovernmentRows461Api.Start start,
            GovernmentCompaction160Api.Entry entry, GovernmentPrimaryTail155Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls calls, GovernmentPrimaryTail155Api.LoopBudget budget) {
        Registers r=GovernmentCompaction160Api.registers(entry);
        long image=entry.imageBaseBits();
        if (start==GovernmentRows461Api.Start.AT_35A1) { r.r13=0L; }
        r.rsi=memory.readQword(r.rdi+0x468L);
        r.r12=((long)memory.readDword(r.rdi+0x474L)<<4)+r.rsi;
        if (r.rsi==r.r12) { return GovernmentRows461Api.join(entry,r); }
        r.rax=image+0x48B7DC0L;
        r.r13=0x158L;
        do {
            budget.beforeIteration(0x30A35D0L,r.rsi,r.r12);
            if (memory.readUnsignedByte(r.rsi+0xCL)!=0) {
                memory.writeQword(r.rbp-0x50L,r.rax);
                memory.writeDword(r.rbp-0x48L,0x20);
                memory.writeByte(r.rbp-0x44L,0);
                r.r14=r.rdi+0x18L;
                r.rdx=memory.readQword(image+0x5C67190L);
                if (r.rdx==0L) {
                    r.rax=image+0x448D018L;
                    memory.writeQword(r.rbp-0x60L,r.rax);
                    memory.writeDword(r.rbp-0x58L,0x1E);
                    memory.writeByte(r.rbp-0x54L,(int)r.rdx&0xFF);
                    r.x0=memory.read128(r.rbp-0x60L);
                    memory.write128(r.rbp+0x120L,r.x0);
                    r.r9=u32((int)(r.rdx+0x64L));
                    r.r8=0L;
                    r.rdx=r.rbp+0x120L;
                    r.rcx=u32((int)r.r15);
                    call(r,calls,0x30A362BL,0x3F8B640L);
                    r.rdx=memory.readQword(image+0x5C67190L);
                }
                r.x0=memory.read128(r.rbp-0x50L);
                memory.write128(r.rbp+0xA0L,r.x0);
                r.rcx=r.rsi;
                call(r,calls,0x30A3646L,0x2D1B7F0L);
                r.rax=u32((int)r.rax-(int)r.r15);
                boolean diagnosticReturned=false;
                if ((int)r.rax==0) {
                    r.rbx=u32(memory.readDword(r.rsi+8L));
                    call(r,calls,0x30A36CAL,0x3F8A7E0L);
                    r.rdx=u32((int)r.rbx);
                    r.rcx=r.rax;
                    call(r,calls,0x30A36D4L,0x3F8A6D0L);
                    r.rbx=r.rax;
                    r.rcx=calls.readGsQword58();
                    r.rdx=memory.readQword(r.rcx);
                    if (memory.readUnsignedByte(r.r13+r.rdx)==0) {
                        r.rcx=u32(memory.readDword(image+0x5C6A9DCL));
                        if ((int)r.rcx<100000) {
                            r.rcx=0x10000L;
                            call(r,calls,0x30A3704L,0x3F5F970L);
                            if (r.rax!=0L) {
                                memory.writeQword(r.rsp+0x38L,r.r14);
                                r.rcx=r.rbp+0xA0L;
                                memory.writeQword(r.rsp+0x30L,r.rcx);
                                memory.writeQword(r.rsp+0x28L,r.rbx);
                                r.rcx=image+0x45D1A30L;
                                memory.writeQword(r.rsp+0x20L,r.rcx);
                                r.r8=0x4BL;
                                r.rdx=image+0x45D2690L;
                                r.rcx=r.rax;
                                call(r,calls,0x30A3740L,0x2850890L);
                                diagnosticReturned=true;
                            }
                        }
                    }
                } else if ((int)r.rax==(int)r.r15) {
                    r.rax=calls.readGsQword58();
                    r.rcx=memory.readQword(r.rax);
                    if (memory.readUnsignedByte(r.r13+r.rcx)==0) {
                        r.rax=u32(memory.readDword(image+0x5C6A9DCL));
                        if ((int)r.rax<100000) {
                            r.rcx=0x10000L;
                            call(r,calls,0x30A3688L,0x3F5F970L);
                            if (r.rax!=0L) {
                                memory.writeQword(r.rsp+0x30L,r.r14);
                                r.rcx=r.rbp+0xA0L;
                                memory.writeQword(r.rsp+0x28L,r.rcx);
                                memory.writeQword(r.rsp+0x20L,r.rbx);
                                r.r9=4L;
                                r.r8=u32((int)(r.r9+0x4CL));
                                r.rdx=image+0x45D2690L;
                                r.rcx=r.rax;
                                call(r,calls,0x30A36C0L,0xC0E0B0L);
                                diagnosticReturned=true;
                            }
                        }
                    }
                }
                if (diagnosticReturned) {
                    r.rax=u32((int)r.r15);
                    r.rax=u32(memory.lockedXaddDword(image+0x5C6A9DCL,(int)r.rax));
                }
                r.rax=image+0x48B7DC0L;
            }
            r.rsi+=0x10L;
            r.rbx=image+0x45D26F0L;
        } while (r.rsi!=r.r12);
        r.r13=0L;
        return GovernmentRows461Api.join(entry,r);
    }
}
