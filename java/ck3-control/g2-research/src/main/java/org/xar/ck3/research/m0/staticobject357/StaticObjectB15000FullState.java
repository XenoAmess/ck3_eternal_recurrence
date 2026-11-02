package org.xar.ck3.research.m0.staticobject357;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held93B represented normal state; CRT bodies, RFLAGS and native custody remain opaque. */
public final class StaticObjectB15000FullState {
    private StaticObjectB15000FullState() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        long image=entry.imageBaseBits();
        r.rsp-=0x28L;
        r.rax=calls.readGsQword58();
        r.rdx=0x10L;
        r.rcx=memory.readQword(r.rax);
        r.rax=Integer.toUnsignedLong(memory.readDword(r.rdx+r.rcx));
        if(memory.readDword(image+0x5D1EB08L)>(int)r.rax) {
            r.rcx=image+0x5D1EB08L;
            invoke(image,r,memory,calls,0xB15033L,0x4223A84L);
            if(memory.readDword(image+0x5D1EB08L)==-1) {
                r.rcx=image+0x5D1EB08L;
                memory.writeByte(image+0x5D1EAF0L,0);
                memory.writeByte(image+0x5D1EAFCL,0xFF);
                invoke(image,r,memory,calls,0xB15056L,0x4223A24L);
            }
        }
        r.rax=image+0x5D1EAF0L;
        r.rsp+=0x28L;
        return new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(),memory.readQword(r.rsp),r.rsp+8L,r.nonvolatileBits());
    }

    private static void invoke(long image,Registers r,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,long site,long targetRva) {
        memory.writeQword(r.rsp-8L,image+site+5L);
        r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(
                site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,targetRva,
                r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
}
