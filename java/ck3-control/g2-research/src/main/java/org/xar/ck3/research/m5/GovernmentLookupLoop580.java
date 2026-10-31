package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.CallFrame;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.CallPost;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Calls;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Cpu;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.EaxPost;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Entry;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.IndirectVa;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Join;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Memory;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.StaticRva;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Target;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.VectorPost;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Whole owner normal580B interpreter after two incomplete model rounds. CPU/callees remain owned ports. */
public final class GovernmentLookupLoop580 {
    private GovernmentLookupLoop580() { }
    private static long u32(int bits) { return Integer.toUnsignedLong(bits); }
    private static Mxcsr32 call(Registers r,Mxcsr32 mx,Calls calls,long site,Target target) {
        CallPost post=calls.invoke(new CallFrame(site,target,r.rsp,r.volatileBits(),r.nonvolatileBits(),mx));
        r.apply(post.volatileBits());return post.mxcsr();
    }
    public static Join execute(Entry entry,Memory memory,Calls calls,Cpu cpu,LoopBudget budget) {
        Registers r=GovernmentLookupLoop580Api.registers(entry);
        long image=entry.raw().imageBaseBits();
        Mxcsr32 mx=entry.mxcsr();
        r.rbx=memory.readQword(r.rdi+0x498L);
        r.rax=((long)memory.readDword(r.rdi+0x4A4L)<<5)+r.rbx;
        memory.writeQword(r.rsp+0x68L,r.rax);
        r.rcx=image+0x448D018L;
        if (r.rbx==r.rax) { return GovernmentLookupLoop580Api.join(entry,r,mx,0x30A33C2L); }
        r.r14=image+0x48B7E70L;
        int literal=memory.readDword(image+0x49F64F0L);
        VectorPost vector=cpu.movssMemoryXmm6(0x30A3193L,literal,r.x6,mx);
        r.x6=vector.vectorBits();mx=vector.mxcsr();
        boolean more;
        do {
            budget.beforeIteration(0x30A31A0L,r.rbx,r.rsp+0x68L);
            r.rsi=memory.readQword(image+0x5D1E2B8L);
            if (r.rsi==0L) {
                memory.writeQword(r.rsp+0x70L,r.rcx);
                memory.writeDword(r.rsp+0x78L,0x1E);
                memory.writeByte(r.rsp+0x7CL,(int)r.rsi&255);
                r.x0=memory.read128(r.rsp+0x70L);
                memory.write128(r.rbp+0x100L,r.x0);
                r.r9=u32((int)(r.rsi+0x64L));r.r8=0L;
                r.rdx=r.rbp+0x100L;r.rcx=u32((int)r.r15);
                mx=call(r,mx,calls,0x30A31DCL,new StaticRva(0x3F8B640L));
                r.rsi=memory.readQword(image+0x5D1E2B8L);
            }
            r.rdx=r.rbx;
            if (Long.compareUnsigned(memory.readQword(r.rbx+0x18L),16L)>=0) { r.rdx=memory.readQword(r.rbx); }
            r.r8=u32(memory.readDword(r.rbx+0x10L));
            mx=call(r,mx,calls,0x30A31F9L,new StaticRva(0x3F7E220L));
            r.rdx=u32((int)r.rax);r.rcx=r.rsi;
            mx=call(r,mx,calls,0x30A3203L,new StaticRva(0xEE6A40L));
            r.rsi=r.rax;
            if (memory.readDword(r.rax+0x38L)!=0x4744624F) {
                r.rax=r.rbx;
                if (Long.compareUnsigned(memory.readQword(r.rbx+0x18L),16L)>=0) { r.rax=memory.readQword(r.rbx); }
                memory.writeQword(r.rbp+0x90L,r.rax);
                r.rax=r.rdi+0x18L;
                if (Long.compareUnsigned(memory.readQword(r.rax+0x18L),16L)>=0) { r.rax=memory.readQword(r.rax); }
                memory.writeQword(r.rsp+0x60L,r.rax);
                r.rdx=u32((int)r.r12);r.rax=calls.readGsQword58();r.rcx=memory.readQword(r.rax);
                if (memory.readUnsignedByte(r.rdx+r.rcx)==0) {
                    r.rax=u32(memory.readDword(image+0x5C6A9DCL));
                    if ((int)r.rax<100000) {
                        r.rcx=0x10000L;
                        mx=call(r,mx,calls,0x30A326FL,new StaticRva(0x3F5F970L));
                        if (r.rax!=0L) {
                            r.rcx=r.rbp+0x90L;memory.writeQword(r.rsp+0x30L,r.rcx);
                            r.rcx=r.rsp+0x60L;memory.writeQword(r.rsp+0x28L,r.rcx);
                            memory.writeQword(r.rsp+0x20L,r.r14);
                            r.r9=4L;r.r8=0x15AL;r.rdx=image+0x48B7A48L;r.rcx=r.rax;
                            mx=call(r,mx,calls,0x30A32AEL,new StaticRva(0xB7C9D0L));
                            r.rax=u32((int)r.r15);
                            r.rax=u32(memory.lockedXaddDword(image+0x5C6A9DCL,(int)r.rax));
                        }
                    }
                }
            } else {
                r.rax=memory.readDword(r.rdi+0x48CL);
                r.rcx=u32(memory.readDword(r.rdi+0x488L));
                if ((int)r.rax==(int)r.rcx) {
                    r.r13=u32((int)(r.rax+1L));
                    vector=cpu.movdXmm0(0x30A32EEL,(int)r.rcx,r.x0,mx);r.x0=vector.vectorBits();mx=vector.mxcsr();
                    vector=cpu.cvtdq2psXmm0(0x30A32F2L,r.x0,mx);r.x0=vector.vectorBits();mx=vector.mxcsr();
                    vector=cpu.mulssXmm0(0x30A32F5L,r.x0,r.x6,mx);r.x0=vector.vectorBits();mx=vector.mxcsr();
                    EaxPost converted=cpu.cvttss2siEax(0x30A32F9L,r.x0,mx);r.rax=u32(converted.eaxBits());mx=converted.mxcsr();
                    r.r12=u32((int)r.r13);
                    if ((int)r.r13<(int)r.rax) { r.r12=u32((int)r.rax); }
                    r.rcx=memory.readQword(r.rdi+0x490L);r.rax=memory.readQword(r.rcx);
                    r.rdx=u32((int)r.r12);r.rdx<<=3;r.r8=8L;
                    long indirect=memory.readQword(r.rax+8L);
                    mx=call(r,mx,calls,0x30A331EL,new IndirectVa(indirect));
                    r.r14=r.rax;
                    r.rcx=memory.readDword(r.rdi+0x48CL);
                    memory.writeQword(r.rax+(r.rcx<<3),r.rsi);
                    r.rax=memory.readDword(r.rdi+0x48CL);
                    if ((int)r.rax>0) {
                        r.r8=r.rax;r.r8<<=3;r.rdx=memory.readQword(r.rdi+0x480L);r.rcx=r.r14;
                        mx=call(r,mx,calls,0x30A334BL,new StaticRva(0x4226860L));
                    }
                    r.rcx=memory.readQword(r.rdi+0x490L);r.rax=memory.readQword(r.rcx);
                    r.r8=8L;r.rdx=memory.readQword(r.rdi+0x480L);
                    indirect=memory.readQword(r.rax+0x10L);
                    mx=call(r,mx,calls,0x30A3367L,new IndirectVa(indirect));
                    memory.writeQword(r.rdi+0x480L,r.r14);
                    memory.writeDword(r.rdi+0x48CL,(int)r.r13);memory.writeDword(r.rdi+0x488L,(int)r.r12);
                    r.r14=image+0x48B7E70L;r.r12=0x158L;
                } else {
                    r.rcx=r.rax;r.rax=memory.readQword(r.rdi+0x480L);
                    memory.writeQword(r.rax+(r.rcx<<3),r.rsi);
                    memory.writeDword(r.rdi+0x48CL,memory.readDword(r.rdi+0x48CL)+1);
                }
            }
            r.rbx+=0x20L;
            more=r.rbx!=memory.readQword(r.rsp+0x68L);
            r.rcx=image+0x448D018L;
        } while (more);
        return GovernmentLookupLoop580Api.join(entry,r,mx,0x30A33B8L);
    }
}
