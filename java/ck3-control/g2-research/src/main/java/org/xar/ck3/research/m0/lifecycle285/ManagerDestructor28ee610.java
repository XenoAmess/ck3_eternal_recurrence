package org.xar.ck3.research.m0.lifecycle285;

import org.xar.ck3.research.m0.manager283.ManagerDeleteArrayA07b00Calls;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held199B normal-return projection; reuses the actual108B child, not unknown callees. */
public final class ManagerDestructor28ee610 {
    private ManagerDestructor28ee610() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback,GovernmentCrtBoundary185Api.LoopBudget budget) {
        GovernmentCrtBoundary185Api.Calls calls=ManagerDeleteArrayA07b00Calls.bind(
                entry.imageBaseBits(),memory,fallback,budget);
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(r.rsp+8L,r.rbx);
        r.rsp-=8L;
        memory.writeQword(r.rsp,r.rdi);
        r.rsp-=0x20L;
        r.rax=entry.imageBaseBits()+0x4763EE0L;
        r.rdi=0L;
        memory.writeQword(r.rcx,r.rax);
        r.rbx=r.rcx;
        r.rdx=memory.readQword(r.rcx+0x88L);
        if(r.rdx!=0L) {
            memory.writeDword(r.rcx+0x94L,(int)r.rdi);
            r.r8=4L;
            r.rcx=memory.readQword(r.rcx+0x98L);
            r.rax=memory.readQword(r.rcx);
            virtual(entry.imageBaseBits(),r,memory,calls,0x28EE649L);
            memory.writeQword(r.rbx+0x88L,r.rdi);
            memory.writeDword(r.rbx+0x90L,(int)r.rdi);
        }
        r.rdx=memory.readQword(r.rbx+0x70L);
        if(r.rdx!=0L) {
            r.rcx=memory.readQword(r.rbx+0x80L);
            r.r8=4L;
            memory.writeDword(r.rbx+0x7CL,(int)r.rdi);
            r.rax=memory.readQword(r.rcx);
            virtual(entry.imageBaseBits(),r,memory,calls,0x28EE675L);
            memory.writeQword(r.rbx+0x70L,r.rdi);
            memory.writeDword(r.rbx+0x78L,(int)r.rdi);
        }
        r.rcx=r.rbx+0x58L;
        invoke(entry.imageBaseBits(),r,memory,calls,0x28EE683L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0xA07B00L,5L);
        r.rdx=memory.readQword(r.rbx+0x40L);
        if(r.rdx!=0L) {
            r.rcx=memory.readQword(r.rbx+0x50L);
            r.r8=4L;
            memory.writeDword(r.rbx+0x4CL,(int)r.rdi);
            r.rax=memory.readQword(r.rcx);
            virtual(entry.imageBaseBits(),r,memory,calls,0x28EE6A1L);
            memory.writeQword(r.rbx+0x40L,r.rdi);
            memory.writeDword(r.rbx+0x48L,(int)r.rdi);
        }
        r.rdi=memory.readQword(r.rbx+0x20L);
        invoke(entry.imageBaseBits(),r,memory,calls,0x28EE6AFL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0xB15000L,5L);
        if(r.rdi!=r.rax) {
            r.rcx=memory.readQword(r.rbx+0x38L);
            r.r8=4L;
            r.rdx=r.rdi;
            r.rax=memory.readQword(r.rcx);
            virtual(entry.imageBaseBits(),r,memory,calls,0x28EE6C9L);
        }
        r.rbx=memory.readQword(r.rsp+0x30L);
        r.rsp+=0x20L;
        r.rdi=memory.readQword(r.rsp);
        r.rsp+=8L;
        return new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(),memory.readQword(r.rsp),r.rsp+8L,r.nonvolatileBits());
    }

    private static void virtual(long image,Registers r,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,long site) {
        long target=memory.readQword(r.rax+0x10L);
        invoke(image,r,memory,calls,site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,3L);
    }
    private static void invoke(long image,Registers r,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,long site,GovernmentCrtBoundary185Api.TargetKind kind,
            long target,long length) {
        memory.writeQword(r.rsp-8L,image+site+length);
        r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(
                site,kind,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
}
