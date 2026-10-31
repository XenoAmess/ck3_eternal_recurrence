package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentPreprefix159Api.Entry;
import org.xar.ck3.research.m5.GovernmentPreprefix159Api.EntryPoint;
import org.xar.ck3.research.m5.GovernmentPreprefix159Api.Join;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Complete owner takeover after two source-rejected model rounds. Owned normal local state only. */
public final class GovernmentPreprefix159 {
    private GovernmentPreprefix159() { }
    private static long u32(int bits) { return Integer.toUnsignedLong(bits); }
    private static void invoke(Registers r, Calls calls, long site, long target) {
        r.apply(calls.invoke(new OpaqueCall(site,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
    private static void increment(Registers r, Memory memory, long counter) {
        r.rax=u32((int)r.r15);
        r.rax=u32(memory.lockedXaddDword(counter,(int)r.rax));
    }
    public static Join execute(Entry entry, Memory memory, Calls calls) {
        Registers r=GovernmentPreprefix159Api.registers(entry);
        long image=entry.imageBaseBits(), counter=image+0x5c6a9dcL;
        if(entry.entryPoint()==EntryPoint.AT_30A3BBA) { r.r12=image+0x45d1a30L; }
        r.rdx=memory.readQword(image+0x5d21358L);
        if(r.rdx==0) {
            r.rax=image+0x448d018L;
            memory.writeQword(r.rbp+0x20L,r.rax);
            memory.writeDword(r.rbp+0x28L,0x1e);
            memory.writeByte(r.rbp+0x2cL,(int)r.rdx);
            r.x0=memory.read128(r.rbp+0x20L);
            memory.write128(r.rbp+0x180L,r.x0);
            r.r9=u32((int)r.rdx+0x64); r.r8=0;
            r.rdx=r.rbp+0x180L; r.rcx=u32((int)r.r15);
            invoke(r,calls,0x30a3bffL,0x3f8b640L);
            r.rdx=memory.readQword(image+0x5d21358L);
        }
        r.rcx=r.rdi+0x820L;
        invoke(r,calls,0x30a3c12L,0x2d0b490L);
        if((int)r.rax==(int)r.r15) {
            r.rbx=u32(memory.readDword(r.rdi+0x828L));
            invoke(r,calls,0x30a3c26L,0x3f8a7e0L);
            r.rdx=u32((int)r.rbx); r.rcx=r.rax;
            invoke(r,calls,0x30a3c30L,0x3f8a6d0L);
            r.rbx=r.rax; r.r8=u32((int)r.r14);
            r.rcx=calls.readGsQword58(); r.rdx=memory.readQword(r.rcx);
            if(memory.readUnsignedByte(r.r8+r.rdx)==0) {
                r.rcx=u32(memory.readDword(counter));
                if((int)r.rcx<0x186a0) {
                    r.rcx=0x10000;
                    invoke(r,calls,0x30a3c62L,0x3f5f970L);
                    if(r.rax!=0) {
                        memory.writeQword(r.rsp+0x30L,r.rsi);
                        memory.writeQword(r.rsp+0x28L,r.rbx);
                        r.rcx=image+0x48b75a8L; memory.writeQword(r.rsp+0x20L,r.rcx);
                        r.r9=4; r.r8=0x197; r.rdx=image+0x48b7a48L; r.rcx=r.rax;
                        invoke(r,calls,0x30a3c98L,0xabbaf0L);
                        increment(r,memory,counter);
                    }
                }
            }
        }
        // 30A3CA8 is reached regardless of the preceding compare outcome.
        if(memory.readUnsignedByte(r.rdi+0xdb4L)!=0) {
            r.rax=image+0x46d93d0L;
            memory.writeQword(r.rbp+0x40L,r.rax);
            memory.writeDword(r.rbp+0x48L,0x1c);
            memory.writeByte(r.rbp+0x4cL,0);
            r.rdx=memory.readQword(image+0x5d29880L);
            if(r.rdx==0) {
                r.rax=image+0x448d018L;
                memory.writeQword(r.rbp+0x30L,r.rax);
                memory.writeDword(r.rbp+0x38L,0x1e);
                memory.writeByte(r.rbp+0x3cL,(int)r.rdx);
                r.x0=memory.read128(r.rbp+0x30L);
                memory.write128(r.rbp+0x190L,r.x0);
                r.r9=u32((int)r.rdx+0x64); r.r8=0;
                r.rdx=r.rbp+0x190L; r.rcx=u32((int)r.r15);
                invoke(r,calls,0x30a3d09L,0x3f8b640L);
                r.rdx=memory.readQword(image+0x5d29880L);
            }
            r.x0=memory.read128(r.rbp+0x40L);
            memory.write128(r.rbp+0xc0L,r.x0);
            r.rcx=r.rdi+0xda8L;
            invoke(r,calls,0x30a3d28L,0x30aa240L);
            r.rax=u32((int)r.rax-(int)r.r15);
            if((int)r.rax==0) {
                // 30A3DAD: original lowEAX equals lowR15, not an inferred native boolean.
                r.rbx=u32(memory.readDword(r.rdi+0xdb0L));
                invoke(r,calls,0x30a3db3L,0x3f8a7e0L);
                r.rdx=u32((int)r.rbx); r.rcx=r.rax;
                invoke(r,calls,0x30a3dbdL,0x3f8a6d0L);
                r.rbx=r.rax; r.r8=u32((int)r.r14);
                r.rcx=calls.readGsQword58(); r.rdx=memory.readQword(r.rcx);
                if(memory.readUnsignedByte(r.r8+r.rdx)==0) {
                    r.rcx=u32(memory.readDword(counter));
                    if((int)r.rcx<0x186a0) {
                        r.rcx=0x10000;
                        invoke(r,calls,0x30a3defL,0x3f5f970L);
                        if(r.rax!=0) {
                            memory.writeQword(r.rsp+0x38L,r.rsi);
                            r.rcx=r.rbp+0xc0L; memory.writeQword(r.rsp+0x30L,r.rcx);
                            memory.writeQword(r.rsp+0x28L,r.rbx);
                            memory.writeQword(r.rsp+0x20L,r.r12);
                            r.r8=0x4b; r.rdx=image+0x45d2690L; r.rcx=r.rax;
                            invoke(r,calls,0x30a3e24L,0x2850890L);
                            increment(r,memory,counter);
                        }
                    }
                }
            } else if((int)r.rax==(int)r.r15) {
                // 30A3D3B: compare applies to the already-subtracted32-bit value.
                r.rdx=u32((int)r.r14); r.rax=calls.readGsQword58();
                r.rcx=memory.readQword(r.rax);
                if(memory.readUnsignedByte(r.rdx+r.rcx)==0) {
                    r.rax=u32(memory.readDword(counter));
                    if((int)r.rax<0x186a0) {
                        r.rcx=0x10000;
                        invoke(r,calls,0x30a3d6bL,0x3f5f970L);
                        if(r.rax!=0) {
                            memory.writeQword(r.rsp+0x30L,r.rsi);
                            r.rcx=r.rbp+0xc0L; memory.writeQword(r.rsp+0x28L,r.rcx);
                            memory.writeQword(r.rsp+0x20L,r.r13);
                            r.r9=4; r.r8=u32((int)r.r9+0x4c);
                            r.rdx=image+0x45d2690L; r.rcx=r.rax;
                            invoke(r,calls,0x30a3da3L,0xc0e0b0L);
                            increment(r,memory,counter);
                        }
                    }
                }
            }
        }
        // Single normal suffix30A3E34..30A3EB3; padding bytes remain owned memory.
        r.rax=image+0x46d67b0L;
        memory.writeQword(r.rbp+0x50L,r.rax);
        memory.writeDword(r.rbp+0x58L,0x18);
        memory.writeByte(r.rbp+0x5cL,0);
        r.x0=memory.read128(r.rbp+0x50L); memory.write128(r.rbp+0x1a0L,r.x0);
        r.r8=u32(memory.readDword(r.rdi+0x4ccL));
        r.rdx=r.rbp+0x1a0L; r.rcx=r.rdi;
        invoke(r,calls,0x30a3e67L,0x30a2cc0L);
        memory.writeDword(r.rdi+0x4ccL,(int)r.rax);
        r.rax=image+0x46d97e8L;
        memory.writeQword(r.rbp+0x60L,r.rax);
        memory.writeDword(r.rbp+0x68L,0x1b);
        memory.writeByte(r.rbp+0x6cL,0);
        r.x0=memory.read128(r.rbp+0x60L); memory.write128(r.rbp+0x1b0L,r.x0);
        r.r8=u32(memory.readDword(r.rdi+0x4c8L));
        r.rdx=r.rbp+0x1b0L; r.rcx=r.rdi;
        invoke(r,calls,0x30a3ea5L,0x30a2cc0L);
        memory.writeDword(r.rdi+0x4c8L,(int)r.rax);
        r.r12=u32((int)r.r14);
        return GovernmentPreprefix159Api.join(entry,r);
    }
}
