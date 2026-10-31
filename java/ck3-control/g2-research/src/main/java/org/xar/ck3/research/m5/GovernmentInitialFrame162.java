package org.xar.ck3.research.m5;

/** Owner complete normal612B executor after both model body rounds ended incomplete. */
public final class GovernmentInitialFrame162 {
    private GovernmentInitialFrame162() { }
    private static long u32(int bits) { return Integer.toUnsignedLong(bits); }
    private static void call(GovernmentPrimaryTail155Api.Registers r,GovernmentInitialFrame162Api.Calls calls,long site,long target) {
        r.apply(calls.invoke(new GovernmentPrimaryTail155Api.OpaqueCall(site,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
    public static GovernmentInitialFrame162Api.Join execute(GovernmentInitialFrame162Api.Entry entry,
            GovernmentInitialFrame162Api.Memory memory,GovernmentInitialFrame162Api.Calls calls,
            GovernmentInitialFrame162Api.LoopBudget budget) {
        var r=GovernmentCompaction160Api.registers(new GovernmentCompaction160Api.Entry(
                entry.imageBaseBits(),entry.originalRspBits(),entry.incomingVolatile(),entry.incomingNonvolatile()));
        long image=entry.imageBaseBits();
        r.rsp-=8;memory.writeQword(r.rsp,r.rbp);
        r.rsp-=8;memory.writeQword(r.rsp,r.rbx);
        r.rsp-=8;memory.writeQword(r.rsp,r.rsi);
        r.rsp-=8;memory.writeQword(r.rsp,r.rdi);
        r.rsp-=8;memory.writeQword(r.rsp,r.r12);
        r.rsp-=8;memory.writeQword(r.rsp,r.r13);
        r.rsp-=8;memory.writeQword(r.rsp,r.r14);
        r.rsp-=8;memory.writeQword(r.rsp,r.r15);
        r.rbp=r.rsp-0x11f8L;r.rax=0x12f8;
        call(r,calls,0x30a2f2aL,0x42247b0L);
        r.rsp-=r.rax;memory.write128(r.rsp+0x12e0L,r.x6);
        r.rdi=r.rcx;r.r13=0;memory.writeDword(r.rbp+0x1240L,0);
        r.rdx=r.rcx+0x48L;r.rax=r.rbp+0x1240L;
        if(memory.readDword(r.rdx)>0)r.rax=r.rdx;
        r.rax=u32(memory.readDword(r.rax));memory.writeDword(r.rdx,(int)r.rax);
        r.rax=memory.readQword(r.rcx+0x418L);
        if(memory.readDword(r.rax+0x38L)==0x4744624f) {
            r.rdx=r.rcx+0x418L;r.rcx+=0x420L;
            call(r,calls,0x30a2f7bL,0xa11cc0L);
            if((r.rax&255)==0) {
                r.rdx=r.rdi+0x418L;r.rcx=r.rdi+0x420L;
                call(r,calls,0x30a2f92L,0x880340L);
            }
        }
        r.rax=image+0x9d09e0L;memory.writeQword(r.rsp+0x40L,r.rax);memory.writeQword(r.rsp+0x48L,r.r13);
        r.x0=memory.read128(r.rsp+0x40L);memory.write128(r.rbp+0xe0L,r.x0);
        r.x1=new GovernmentPrimaryTail155Api.Bits128(memory.readQword(r.rsp+0x50L),0);
        memory.writeQword(r.rbp+0xf0L,r.x1.lowBits());
        r.rsi=memory.readDword(r.rdi+0x42cL);r.r14=memory.readQword(r.rdi+0x420L);r.r15=r.r14+r.rsi*8;
        if(r.rsi<=0x20L) {
            r.r8=r.rbp+0xe0L;r.rdx=r.r15;r.rcx=r.r14;
            call(r,calls,0x30a2fe7L,0x2be3690L);
        } else {
            r.rax=r.rsi;r.rdx=r.rax<0?-1L:0L;r.rax-=r.rdx;r.rax>>=1;
            r.rbx=r.rsi;r.rbx-=r.rax;r.rax=Long.MAX_VALUE;
            if(r.rbx<r.rax)r.rax=r.rbx;
            boolean local=true;
            if(Long.compareUnsigned(r.rbx,0x200L)>0) {
                r.rbx=r.rax;r.rcx=0x1fffffffffffffffL;
                if(Long.compareUnsigned(r.rax,r.rcx)<=0&&r.rax>0) {
                    for(;;) {
                        budget.beforeAttempt(0x30a3040L,r.rbx);
                        r.rcx=r.rbx*8;r.rdx=image+0x441f580L;
                        call(r,calls,0x30a304fL,0x42242ccL);
                        if(r.rax!=0) {
                            if(Long.compareUnsigned(r.rbx,0x200L)>0) { local=false;break; }
                            r.rcx=r.rax;call(r,calls,0x30a3068L,0x40ec530L);
                            r.rbx=0x200;break;
                        }
                        r.rbx>>>=1;
                        if(r.rbx!=0)continue;
                        r.rax=r.r13;r.rcx=r.rax;call(r,calls,0x30a3068L,0x40ec530L);
                        r.rbx=0x200;break;
                    }
                } else {
                    r.rax=r.r13;r.rcx=r.rax;call(r,calls,0x30a3068L,0x40ec530L);r.rbx=0x200;
                }
            }
            if(local)r.rax=r.rbp+0x1e0L;
            memory.writeQword(r.rbp+0x1d0L,r.rax);memory.writeQword(r.rbp+0x1d8L,r.rbx);
            r.rcx=r.rbp+0xe0L;memory.writeQword(r.rsp+0x28L,r.rcx);memory.writeQword(r.rsp+0x20L,r.rbx);
            r.r9=r.rax;r.r8=r.rsi;r.rdx=r.r15;r.rcx=r.r14;
            call(r,calls,0x30a30a4L,0x30abbb0L);
            if(Long.compareUnsigned(memory.readQword(r.rbp+0x1d8L),0x200L)>0) {
                r.rcx=memory.readQword(r.rbp+0x1d0L);call(r,calls,0x30a30beL,0x40ec530L);
            }
        }
        r.rax=u32(memory.readDword(r.rdi+0x4bcL));r.r15=1;r.r12=0x158;
        if((int)r.rax!=0) {
            r.rcx=u32(memory.readDword(image+0x5450fa4L));
            if((int)r.rax!=(int)r.rcx) {
                memory.writeDword(r.rbp+0x1248L,(int)r.rcx);
                r.rax=calls.readGsQword58();r.rcx=memory.readQword(r.rax);
                if(memory.readUnsignedByte(r.r12+r.rcx)==0) {
                    r.rax=u32(memory.readDword(image+0x5c6a9dcL));
                    if((int)r.rax<0x186a0) {
                        r.rcx=0x10000;call(r,calls,0x30a3113L,0x3f5f970L);
                        if(r.rax!=0) {
                            r.rcx=r.rdi+0x18L;r.rdx=r.rbp+0x1248L;
                            memory.writeQword(r.rsp+0x30L,r.rdx);memory.writeQword(r.rsp+0x28L,r.rcx);
                            r.rcx=image+0x48b7df0L;memory.writeQword(r.rsp+0x20L,r.rcx);
                            r.r9=u32((int)r.r15+3);r.r8=0x152;r.rdx=image+0x48b7a48L;r.rcx=r.rax;
                            call(r,calls,0x30a3152L,0xc16b60L);
                            r.rax=u32((int)r.r15);r.rax=u32(memory.lockedXaddDword(image+0x5c6a9dcL,(int)r.rax));
                        }
                    }
                }
            }
        }
        return new GovernmentInitialFrame162Api.Join(0x30a3162L,image,r.rsp,r.volatileBits(),r.nonvolatileBits());
    }
}
