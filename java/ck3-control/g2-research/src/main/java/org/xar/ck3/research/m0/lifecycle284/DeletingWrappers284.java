package org.xar.ck3.research.m0.lifecycle284;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Two exact52B normal-return projections; opaque callees, no native allocation/EH. */
public final class DeletingWrappers284 {
    private DeletingWrappers284() { }

    public static GovernmentCrtBoundary185Api.NormalReturn executePlayerInfo(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        return executeWrapper(entry,memory,calls,0x23DA680L,0x23D9E40L,0x390L);
    }

    public static GovernmentCrtBoundary185Api.NormalReturn executeManager(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        return executeWrapper(entry,memory,calls,0x28EE5D0L,0x28EE610L,0xA0L);
    }

    private static GovernmentCrtBoundary185Api.NormalReturn executeWrapper(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,long functionRva,long destructorRva,long size) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(r.rsp+8L,r.rbx);
        r.rsp-=8L;
        memory.writeQword(r.rsp,r.rdi);
        r.rsp-=0x20L;
        r.rbx=Integer.toUnsignedLong((int)r.rdx);
        r.rdi=r.rcx;
        invoke(entry.imageBaseBits(),r,memory,calls,functionRva+0xFL,destructorRva);
        if((r.rbx&1L)!=0L) {
            r.rdx=size;
            r.rcx=r.rdi;
            invoke(entry.imageBaseBits(),r,memory,calls,functionRva+0x21L,0x4223F44L);
        }
        r.rbx=memory.readQword(r.rsp+0x30L);
        r.rax=r.rdi;
        r.rsp+=0x20L;
        r.rdi=memory.readQword(r.rsp);
        r.rsp+=8L;
        return new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(),memory.readQword(r.rsp),r.rsp+8L,r.nonvolatileBits());
    }

    private static void invoke(long image,Registers r,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,long site,long targetRva) {
        memory.writeQword(r.rsp-8L,image+site+5L);
        r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,targetRva,
                r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
}
