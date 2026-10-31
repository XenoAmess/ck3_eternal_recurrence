package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Whole owner method after two incomplete model replies. */
public final class GovernmentCompaction160 {
    private GovernmentCompaction160() { }
    private static long u32(int bits) { return Integer.toUnsignedLong(bits); }
    private static void call(Registers r,GovernmentPrimaryTail155Api.Calls calls,long site,long target) {
        r.apply(calls.invoke(new GovernmentPrimaryTail155Api.OpaqueCall(
                site,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
    public static GovernmentCompaction160Api.Join execute(GovernmentCompaction160Api.Entry entry,
            GovernmentPrimaryTail155Api.Memory memory,GovernmentPrimaryTail155Api.Calls calls,
            GovernmentCompaction160Api.Loops loops) {
        Registers r=GovernmentCompaction160Api.registers(entry);
        r.rcx=u32(memory.readDword(r.rdi+0x45cL));
        r.r9=memory.readQword(entry.imageBaseBits()+0x5d1e388L);
        if ((int)r.rcx>0) {
            r.rax=memory.readQword(r.rdi+0x450L);
            for (;;) {
                loops.beforeIteration(0x30a3786L,r.r13,(int)r.rcx);
                int tag=memory.readUnsignedByte(r.rax+12);
                r.rdx=r.r9;
                if (tag==2) r.rdx=memory.readQword(r.rax);
                if (memory.readUnsignedByte(r.rdx+0x1520L)!=(int)(r.r15&255L)) break;
                r.r13=u32((int)r.r13+1);
                r.rax+=16;
                if ((int)r.r13>=(int)r.rcx) break;
            }
        }
        r.r10=(long)(int)r.r13;
        r.r13=u32((int)r.r13+1);
        if ((int)r.r13<(int)r.rcx) {
            r.rax=((long)(int)r.r13)<<4;
            r.r8=r.r10<<4;
            for (;;) {
                loops.beforeIteration(0x30a37c0L,r.r13,(int)r.rcx);
                r.rcx=memory.readQword(r.rdi+0x450L);
                int tag=memory.readUnsignedByte(r.rcx+r.rax+12);
                r.rdx=r.r9;
                if (tag==2) r.rdx=memory.readQword(r.rcx+r.rax);
                if (memory.readUnsignedByte(r.rdx+0x1520L)==(int)(r.r15&255L)) {
                    r.x0=memory.read128(r.rcx+r.rax);
                    memory.write128(r.rcx+r.r8,r.x0);
                    r.r10=u32((int)r.r10+1);
                    r.r8+=16;
                    r.r9=memory.readQword(entry.imageBaseBits()+0x5d1e388L);
                }
                r.r13=u32((int)r.r13+1);
                r.rax+=16;
                r.rcx=u32(memory.readDword(r.rdi+0x45cL));
                if ((int)r.r13>=(int)r.rcx) break;
            }
        }
        r.rbx=u32((int)r.rcx-(int)r.r10);
        r.r9=memory.readQword(r.rdi+0x450L);
        if ((int)r.rbx<=0) {
            r.r14=0x158L;
            return GovernmentCompaction160Api.join(entry,r);
        }
        r.rax=((long)(int)r.rcx)<<4;
        r.rdx=r.r9+r.rax;
        r.r8=r.r9;
        r.r8-=r.rdx;
        r.r8+=r.rax;
        r.rcx=((long)(int)r.r10)<<4;
        r.rcx+=r.r9;
        call(r,calls,0x30a3839L,0x4226860L);
        memory.writeDword(r.rdi+0x45cL,memory.readDword(r.rdi+0x45cL)-(int)r.rbx);
        memory.writeDword(r.rbp+0x1250L,(int)r.rbx);
        r.r14=0x158L;
        r.rax=calls.readGsQword58();
        r.rcx=memory.readQword(r.rax);
        if (memory.readUnsignedByte(r.r14+r.rcx)!=0) return GovernmentCompaction160Api.join(entry,r);
        r.rax=u32(memory.readDword(entry.imageBaseBits()+0x5c6a9dcL));
        if ((int)r.rax>=0x186a0) return GovernmentCompaction160Api.join(entry,r);
        r.rcx=0x10000L;
        call(r,calls,0x30a3876L,0x3f5f970L);
        if (r.rax==0) return GovernmentCompaction160Api.join(entry,r);
        r.rcx=r.rdi+0x18L;
        r.rdx=r.rbp+0x1250L;
        memory.writeQword(r.rsp+0x30L,r.rdx);
        memory.writeQword(r.rsp+0x28L,r.rcx);
        r.rcx=entry.imageBaseBits()+0x48b7d20L;
        memory.writeQword(r.rsp+0x20L,r.rcx);
        r.r9=4;
        r.r8=0x17fL;
        r.rdx=entry.imageBaseBits()+0x48b7a48L;
        r.rcx=r.rax;
        call(r,calls,0x30a38b7L,0xc16b60L);
        r.rax=u32((int)r.r15);
        r.rax=u32(memory.lockedXaddDword(entry.imageBaseBits()+0x5c6a9dcL,(int)r.rax));
        return GovernmentCompaction160Api.join(entry,r);
    }
}
