package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCompaction160Api.Entry;
import org.xar.ck3.research.m5.GovernmentPreprefix159Api.EntryPoint;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner whole-region takeover after two source-rejected model rounds. Normal owned ports only. */
public final class GovernmentPrelude160 {
    private GovernmentPrelude160() { }
    private static long u32(int value) { return Integer.toUnsignedLong(value); }
    private static void call(Registers r,Calls calls,long site,long target) {
        r.apply(calls.invoke(new OpaqueCall(site,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
    private static void descriptor(Memory memory,long at,long label,int length,int tag) {
        memory.writeQword(at,label); memory.writeDword(at+8,length); memory.writeByte(at+12,tag);
    }
    private static GovernmentPreprefix159Api.Entry out(Entry entry,Registers r,EntryPoint mode) {
        return new GovernmentPreprefix159Api.Entry(entry.imageBaseBits(),mode,r.rsp,r.volatileBits(),r.nonvolatileBits());
    }
    private static void xadd(Registers r,Memory memory,long address) {
        r.rax=u32((int)r.r15); r.rax=u32(memory.lockedXaddDword(address,(int)r.rax));
    }
    public static GovernmentPreprefix159Api.Entry execute(Entry entry,Memory memory,Calls calls) {
        Registers r=GovernmentCompaction160Api.registers(entry);
        long image=entry.imageBaseBits(),counter=image+0x5c6a9dcL;
        r.rsi=r.rdi+0x18L;
        if(memory.readUnsignedByte(r.rdi+0x7fcL)!=0) {
            r.rax=image+0x48b7d70L;
            descriptor(memory,r.rbp-0x30L,r.rax,0x20,0);
            r.rdx=memory.readQword(image+0x5d1fc18L);
            if(r.rdx==0) {
                r.rax=image+0x448d018L;
                descriptor(memory,r.rbp-0x40L,r.rax,0x1e,(int)r.rdx);
                r.x0=memory.read128(r.rbp-0x40L); memory.write128(r.rbp+0x130L,r.x0);
                r.r9=u32((int)r.rdx+0x64); r.r8=0; r.rdx=r.rbp+0x130L; r.rcx=u32((int)r.r15);
                call(r,calls,0x30a3934L,0x3f8b640L);
                r.rdx=memory.readQword(image+0x5d1fc18L);
            }
            r.x0=memory.read128(r.rbp-0x30L); memory.write128(r.rbp+0x140L,r.x0);
            r.r9=r.rbp+0x140L; r.r8=r.rsi; r.rcx=r.rdi+0x7f0L;
            call(r,calls,0x30a395dL,0x2850560L);
        }
        if(memory.readUnsignedByte(r.rdi+0x80cL)!=0) {
            r.rax=image+0x48b7cd8L;
            descriptor(memory,r.rbp-0x10L,r.rax,0x1b,0);
            r.rdx=memory.readQword(image+0x5d303d0L);
            if(r.rdx==0) {
                r.rax=image+0x448d018L;
                descriptor(memory,r.rbp-0x20L,r.rax,0x1e,(int)r.rdx);
                r.x0=memory.read128(r.rbp-0x20L); memory.write128(r.rbp+0x150L,r.x0);
                r.r9=u32((int)r.rdx+0x64); r.r8=0; r.rdx=r.rbp+0x150L; r.rcx=u32((int)r.r15);
                call(r,calls,0x30a39c3L,0x3f8b640L);
                r.rdx=memory.readQword(image+0x5d303d0L);
            }
            r.x0=memory.read128(r.rbp-0x10L); memory.write128(r.rbp+0x160L,r.x0);
            r.r9=r.rbp+0x160L; r.r8=r.rsi; r.rcx=r.rdi+0x800L;
            call(r,calls,0x30a39ecL,0x30a9420L);
        }
        if(memory.readUnsignedByte(r.rdi+0x81cL)!=0) {
            r.rax=image+0x48b7cf8L;
            descriptor(memory,r.rbp+0x10L,r.rax,0x18,0);
            r.rdx=memory.readQword(image+0x5d29b70L);
            if(r.rdx==0) {
                r.rax=image+0x448d018L;
                descriptor(memory,r.rbp,r.rax,0x1e,(int)r.rdx);
                r.x0=memory.read128(r.rbp); memory.write128(r.rbp+0x170L,r.x0);
                r.r9=u32((int)r.rdx+0x64); r.r8=0; r.rdx=r.rbp+0x170L; r.rcx=u32((int)r.r15);
                call(r,calls,0x30a3a52L,0x3f8b640L);
                r.rdx=memory.readQword(image+0x5d29b70L);
            }
            r.x0=memory.read128(r.rbp+0x10L); memory.write128(r.rbp+0xb0L,r.x0);
            r.rcx=r.rdi+0x810L;
            call(r,calls,0x30a3a71L,0x2afb4c0L);
            r.rax=u32((int)r.rax-(int)r.r15);
            if((int)r.rax==0) {
                r.rbx=u32(memory.readDword(r.rdi+0x818L));
                call(r,calls,0x30a3b12L,0x3f8a7e0L);
                r.rdx=u32((int)r.rbx); r.rcx=r.rax;
                call(r,calls,0x30a3b1cL,0x3f8a6d0L);
                r.rbx=r.rax; r.r8=u32((int)r.r14);
                r.rcx=calls.readGsQword58(); r.rdx=memory.readQword(r.rcx);
                if(memory.readUnsignedByte(r.r8+r.rdx)!=0) {
                    r.r12=image+0x45d1a30L; r.r13=image+0x45d26f0L;
                    return out(entry,r,EntryPoint.AT_30A3BC1);
                }
                r.rcx=u32(memory.readDword(counter));
                if((int)r.rcx<0x186a0) {
                    r.rcx=0x10000;
                    call(r,calls,0x30a3b4eL,0x3f5f970L);
                    if(r.rax!=0) {
                        memory.writeQword(r.rsp+0x38L,r.rsi);
                        r.rcx=r.rbp+0xb0L; memory.writeQword(r.rsp+0x30L,r.rcx);
                        memory.writeQword(r.rsp+0x28L,r.rbx);
                        r.r12=image+0x45d1a30L; memory.writeQword(r.rsp+0x20L,r.r12);
                        r.r8=0x4b; r.rdx=image+0x45d2690L; r.rcx=r.rax;
                        call(r,calls,0x30a3b8aL,0x2850890L);
                        xadd(r,memory,counter);
                        r.r13=image+0x45d26f0L;
                        return out(entry,r,EntryPoint.AT_30A3BC1);
                    }
                }
            } else if((int)r.rax==(int)r.r15) {
                r.rdx=u32((int)r.r14); r.rax=calls.readGsQword58(); r.rcx=memory.readQword(r.rax);
                if(memory.readUnsignedByte(r.rdx+r.rcx)==0) {
                    r.rax=u32(memory.readDword(counter));
                    if((int)r.rax<0x186a0) {
                        r.rcx=0x10000;
                        call(r,calls,0x30a3ab8L,0x3f5f970L);
                        r.r13=image+0x45d26f0L;
                        if(r.rax!=0) {
                            memory.writeQword(r.rsp+0x30L,r.rsi);
                            r.rcx=r.rbp+0xb0L; memory.writeQword(r.rsp+0x28L,r.rcx);
                            memory.writeQword(r.rsp+0x20L,r.r13);
                            r.r9=4; r.r8=u32((int)r.r9+0x4c); r.rdx=image+0x45d2690L; r.rcx=r.rax;
                            call(r,calls,0x30a3af7L,0xc0e0b0L);
                            xadd(r,memory,counter);
                        }
                        return out(entry,r,EntryPoint.AT_30A3BBA);
                    }
                }
            }
        }
        r.r13=image+0x45d26f0L;
        return out(entry,r,EntryPoint.AT_30A3BBA);
    }
}
