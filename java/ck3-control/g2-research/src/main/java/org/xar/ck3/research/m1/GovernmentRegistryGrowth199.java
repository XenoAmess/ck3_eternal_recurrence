package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Complete held432B normal path. Normal Windows ABI requires DF=0 at entry/after ports.
 * No arbitrary flags/fault/EH/native allocation qualification; both callees remain owned ports. */
public final class GovernmentRegistryGrowth199 {
    private GovernmentRegistryGrowth199() { }
    private static long u32(long value) { return value & 0xFFFF_FFFFL; }
    private static void invoke(Registers r,long imageBase,GovernmentPrimaryTail155Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls calls,long site,long target) {
        memory.writeQword(r.rsp-8,imageBase+site+5);
        r.apply(calls.invoke(new GovernmentPrimaryTail155Api.OpaqueCall(
                site,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
        // The opaque normal call has returned: the source caller resumes at its original pre-CALL SP.
    }
    public static GovernmentCallee164Api.NormalReturn execute(GovernmentCallee164Api.Entry entry,
            GovernmentPrimaryTail155Api.Memory memory,GovernmentPrimaryTail155Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(entry);Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);Objects.requireNonNull(budget);
        Registers r=GovernmentCallee164Api.registers(entry);long imageBase=entry.imageBaseBits();
        // DBB0..DBC4: the exact original stack stores/pushes, then the 0x20-byte local frame.
        memory.writeQword(r.rsp+0x10,r.rbx);
        memory.writeQword(r.rsp+0x18,r.rbp);
        memory.writeQword(r.rsp+0x20,r.rsi);
        r.rsp-=8;memory.writeQword(r.rsp,r.rdi);
        r.rsp-=8;memory.writeQword(r.rsp,r.r14);
        r.rsp-=8;memory.writeQword(r.rsp,r.r15);
        r.rsp-=0x20;
        r.rax=memory.readQword(r.rcx);
        r.rbp=0;
        r.r15=r.rcx;
        r.rbx=memory.readQword(r.rax);
        boolean failed=r.rbx==0;
        if (!failed) {
            // DBDC..DC09: each original RIP load resolves the held RVA542F0B8.
            r.r10=memory.readQword(imageBase+0x542F0B8L);
            r.r9=memory.readQword(r.rbx+8);
            r.rsi=r.r10;
            r.rsi^=memory.readQword(r.rbx);
            r.r9^=r.r10;
            r.rbx=memory.readQword(r.rbx+0x10);
            r.rcx=u32(r.r10);
            r.rcx&=0x3F;
            r.rbx^=r.r10;
            r.rbx=Long.rotateRight(r.rbx,(int)r.rcx);
            r.rsi=Long.rotateRight(r.rsi,(int)r.rcx);
            r.r9=Long.rotateRight(r.r9,(int)r.rcx);
            if (r.r9==r.rbx) {
                // DC0F..DC32: SAR is signed; CMOVA/JB are unsigned; CMOVE consumes ADD's full64 ZF.
                r.rbx-=r.rsi;
                r.rax=0x200;
                r.rbx>>=3;
                r.rdi=r.rbx;
                if (Long.compareUnsigned(r.rbx,r.rax)>0) r.rdi=r.rax;
                r.rax=u32(r.rbp+0x20);
                r.rdi+=r.rbx;
                if (r.rdi==0) r.rdi=r.rax;
                boolean allocated=false;
                if (Long.compareUnsigned(r.rdi,r.rbx)>=0) {
                    r.r8=u32(r.rbp+8);
                    r.rdx=r.rdi;
                    r.rcx=r.rsi;
                    invoke(r,imageBase,memory,calls,0x424DC3EL,0x425B804L);
                    r.rcx=0;
                    r.r14=r.rax;
                    invoke(r,imageBase,memory,calls,0x424DC48L,0x424E364L);
                    allocated=r.r14!=0;
                }
                if (!allocated) {
                    // DC52..DC74 is reached both by unsigned overflow and a zero first R14.
                    r.rdi=r.rbx+4;
                    r.r8=8;
                    r.rdx=r.rdi;
                    r.rcx=r.rsi;
                    invoke(r,imageBase,memory,calls,0x424DC62L,0x425B804L);
                    r.rcx=0;
                    r.r14=r.rax;
                    invoke(r,imageBase,memory,calls,0x424DC6CL,0x424E364L);
                    failed=r.r14==0;
                }
                if (!failed) {
                    r.r10=memory.readQword(imageBase+0x542F0B8L);
                    r.r9=r.r14+r.rbx*8;
                    r.rbx=r.r14+r.rdi*8;
                    r.rsi=r.r14;
                    r.rcx=r.rbx;
                    r.rcx-=r.r9;
                    r.rcx+=7;
                    r.rcx>>>=3;
                    if (Long.compareUnsigned(r.r9,r.rbx)>0) r.rcx=r.rbp;
                    if (r.rcx!=0) {
                        r.rax=r.r10;
                        r.rdi=r.r9;
                        do {
                            budget.beforeStep(0x424DCACL,r.rdi);
                            memory.writeQword(r.rdi,r.rax);
                            r.rdi+=8;
                            r.rcx--;
                        } while (r.rcx!=0);
                        r.r10=memory.readQword(imageBase+0x542F0B8L);
                    }
                }
            }
            if (!failed) append(r,imageBase,memory);
        }
        // DD44 writes EAX, so the architectural result has zero upper32 even after a full-width port result.
        if (failed) r.rax=0xFFFF_FFFFL;
        r.rbx=memory.readQword(r.rsp+0x48);
        r.rbp=memory.readQword(r.rsp+0x50);
        r.rsi=memory.readQword(r.rsp+0x58);
        r.rsp+=0x20;
        r.r15=memory.readQword(r.rsp);r.rsp+=8;
        r.r14=memory.readQword(r.rsp);r.rsp+=8;
        r.rdi=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);r.rsp+=8;
        return new GovernmentCallee164Api.NormalReturn(r.volatileBits(),r.nonvolatileBits(),rip,r.rsp);
    }
    private static void append(Registers r,long imageBase,GovernmentPrimaryTail155Api.Memory memory) {
        // DCB6..DD42: preserve the source's repeated memory loads and low-byte writes.
        r.r8=0x40;
        r.rdi=r.r9+8;
        r.rcx=u32(r.r8);
        r.rax=u32(r.r10);
        r.rax&=0x3F;
        r.rcx=u32(r.rcx-r.rax);
        r.rax=memory.readQword(r.r15+8);
        r.rdx=memory.readQword(r.rax);
        r.rax=u32(r.r8);
        r.rdx=Long.rotateRight(r.rdx,(int)r.rcx);
        r.rdx^=r.r10;
        memory.writeQword(r.r9,r.rdx);
        r.rdx=memory.readQword(imageBase+0x542F0B8L);
        r.rcx=u32(r.rdx);
        r.rcx&=0x3F;
        r.rax=u32(r.rax-r.rcx);
        r.rcx=(r.rcx&~0xFFL)|(r.rax&0xFFL);
        r.rax=memory.readQword(r.r15);
        r.rsi=Long.rotateRight(r.rsi,(int)r.rcx);
        r.rsi^=r.rdx;
        r.rcx=memory.readQword(r.rax);
        memory.writeQword(r.rcx,r.rsi);
        r.rcx=u32(r.r8);
        r.rdx=memory.readQword(imageBase+0x542F0B8L);
        r.rax=u32(r.rdx);
        r.rax&=0x3F;
        r.rcx=u32(r.rcx-r.rax);
        r.rax=memory.readQword(r.r15);
        r.rdi=Long.rotateRight(r.rdi,(int)r.rcx);
        r.rdi^=r.rdx;
        r.rdx=memory.readQword(r.rax);
        memory.writeQword(r.rdx+8,r.rdi);
        r.rdx=memory.readQword(imageBase+0x542F0B8L);
        r.rax=u32(r.rdx);
        r.rax&=0x3F;
        r.r8=u32(r.r8-r.rax);
        r.rax=memory.readQword(r.r15);
        r.rcx=(r.rcx&~0xFFL)|(r.r8&0xFFL);
        r.rbx=Long.rotateRight(r.rbx,(int)r.rcx);
        r.rbx^=r.rdx;
        r.rcx=memory.readQword(r.rax);
        r.rax=0;
        memory.writeQword(r.rcx+0x10,r.rbx);
    }
}
