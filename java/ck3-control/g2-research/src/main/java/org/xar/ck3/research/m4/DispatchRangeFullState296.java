package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held normal253: actual small-tail/self-recursion, full-state opaque sort/merge ports. */
public final class DispatchRangeFullState296 {
    private DispatchRangeFullState296() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        push(r,memory,r.rsi);push(r,memory,r.rdi);
        push(r,memory,r.r14);push(r,memory,r.r15);r.rsp-=0x48L;
        r.r15=r.r9;r.rdi=r.r8;r.r14=r.rdx;r.rsi=r.rcx;
        if(r.r8<=0x20L) {
            r.rsp+=0x48L;
            r.r15=pop(r,memory);r.r14=pop(r,memory);
            r.rdi=pop(r,memory);r.rsi=pop(r,memory);
            return SmallRangeFullState295.execute(new GovernmentCrtBoundary185Api.Entry(
                    entry.imageBaseBits(),r.rsp,r.volatileBits(),r.nonvolatileBits()),memory,calls,budget);
        }
        memory.writeQword(r.rsp+0x70L,r.rbx);
        r.rbx=Integer.toUnsignedLong(memory.readUnsignedByte(r.rsp+0x98L));
        memory.writeQword(r.rsp+0x78L,r.rbp);r.rbp=r.rdi;r.rbp>>>=1;r.rdi-=r.rbp;
        memory.writeQword(r.rsp+0x80L,r.r12);memory.writeQword(r.rsp+0x40L,r.r13);
        r.r8=r.rdi;r.r13=memory.readQword(r.rsp+0x90L);
        r.rax=r.rdi+r.rdi*4L;r.r12=r.rcx+r.rax*8L;r.rdx=r.r12;
        if(r.rdi>r.r13) {
            memory.writeByte(r.rsp+0x28L,(int)r.rbx);memory.writeQword(r.rsp+0x20L,r.r13);
            callSelf(r,entry.imageBaseBits(),0x1A81388L,memory,calls,budget);
            r.r9=r.r15;memory.writeByte(r.rsp+0x28L,(int)r.rbx);r.r8=r.rbp;
            memory.writeQword(r.rsp+0x20L,r.r13);r.rdx=r.r14;r.rcx=r.r12;
            callSelf(r,entry.imageBaseBits(),0x1A813A2L,memory,calls,budget);
        } else {
            memory.writeByte(r.rsp+0x20L,(int)r.rbx);
            callOpaque(r,entry.imageBaseBits(),0x1A81363L,0x1A81780L,memory,calls);
            r.r9=r.r15;memory.writeByte(r.rsp+0x20L,(int)r.rbx);
            r.r8=r.rbp;r.rdx=r.r14;r.rcx=r.r12;
            callOpaque(r,entry.imageBaseBits(),0x1A81378L,0x1A81780L,memory,calls);
        }
        memory.writeByte(r.rsp+0x38L,(int)r.rbx);r.r9=r.rdi;
        memory.writeQword(r.rsp+0x30L,r.r13);r.r8=r.r14;
        memory.writeQword(r.rsp+0x28L,r.r15);r.rdx=r.r12;r.rcx=r.rsi;
        memory.writeQword(r.rsp+0x20L,r.rbp);
        callOpaque(r,entry.imageBaseBits(),0x1A813C6L,0x1A81AB0L,memory,calls);
        r.r13=memory.readQword(r.rsp+0x40L);r.r12=memory.readQword(r.rsp+0x80L);
        r.rbp=memory.readQword(r.rsp+0x78L);r.rbx=memory.readQword(r.rsp+0x70L);
        r.rsp+=0x48L;r.r15=pop(r,memory);r.r14=pop(r,memory);
        r.rdi=pop(r,memory);r.rsi=pop(r,memory);
        long rip=memory.readQword(r.rsp);r.rsp+=8L;
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }

    private static void callSelf(Registers r,long image,long site,
            GovernmentCrtBoundary185Api.Memory memory,GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        budget.beforeStep(site,r.r8);long preSP=r.rsp,expected=image+site+5L;
        var offered=r.nonvolatileBits();memory.writeQword(preSP-8L,expected);
        var child=execute(new GovernmentCrtBoundary185Api.Entry(image,preSP-8L,
                r.volatileBits(),offered),memory,calls,budget);
        if(child.returnRipBits()!=expected||child.callerRspBits()!=preSP
                ||!child.nonvolatileBits().equals(offered))
            throw new UnsupportedOperationException("Self call left represented normal continuation");
        r.apply(child.volatileBits());
    }
    private static void push(Registers r,GovernmentCrtBoundary185Api.Memory m,long bits) {
        r.rsp-=8L;m.writeQword(r.rsp,bits);
    }
    private static long pop(Registers r,GovernmentCrtBoundary185Api.Memory m) {
        long bits=m.readQword(r.rsp);r.rsp+=8L;return bits;
    }

    private static GovernmentPrimaryTail155Api.Registers callOpaque(
            GovernmentPrimaryTail155Api.Registers r, long imageBase, long siteRva, long targetRva,
            GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls) {
        long preSP = r.rsp;
        memory.writeQword(preSP - 8L, imageBase + siteRva + 5L);
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, targetRva, preSP,
                r.volatileBits(), r.nonvolatileBits());
        GovernmentPrimaryTail155Api.VolatileBits returned = calls.invoke(call);
        r.apply(returned);
        return r;
    }
}
