package org.xar.ck3.research.m0.manager283;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held [A07B00,A07B6C) raw normal-return projection; no native allocation or EH. */
public final class ManagerDeleteArrayA07b00 {
    private ManagerDeleteArrayA07b00() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(r.rsp+0x10L,r.rbx);
        r.rsp-=8L;
        memory.writeQword(r.rsp,r.rsi);
        r.rsp-=0x20L;
        r.rbx=memory.readQword(r.rcx);
        r.rsi=r.rcx;
        if(r.rbx!=0L) {
            memory.writeQword(r.rsp+0x30L,r.rdi);
            r.rdi=Integer.toUnsignedLong(memory.readDword(r.rcx+0xCL));
            if((int)r.rdi>0) {
                do {
                    budget.beforeStep(0xA07B21L,r.rbx);
                    r.rcx=memory.readQword(r.rbx);
                    if(r.rcx!=0L) {
                        r.rax=memory.readQword(r.rcx);
                        r.rdx=1L;
                        long target=memory.readQword(r.rax);
                        invoke(entry.imageBaseBits(),r,memory,calls,0xA07B31L,target,2L);
                    }
                    r.rdi=Integer.toUnsignedLong((int)r.rdi-1);
                    r.rbx+=8L;
                } while((int)r.rdi>0);
                r.rbx=memory.readQword(r.rsi);
            }
            r.rcx=memory.readQword(r.rsi+0x10L);
            r.rdi=0L;
            memory.writeDword(r.rsi+0xCL,0);
            r.rdx=r.rbx;
            r.rax=memory.readQword(r.rcx);
            r.r8=8L;
            long target=memory.readQword(r.rax+0x10L);
            invoke(entry.imageBaseBits(),r,memory,calls,0xA07B53L,target,3L);
            memory.writeQword(r.rsi,r.rdi);
            memory.writeDword(r.rsi+8L,(int)r.rdi);
            r.rdi=memory.readQword(r.rsp+0x30L);
        }
        r.rbx=memory.readQword(r.rsp+0x38L);
        r.rsp+=0x20L;
        r.rsi=memory.readQword(r.rsp);
        r.rsp+=8L;
        long rip=memory.readQword(r.rsp);
        return new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(),rip,r.rsp+8L,r.nonvolatileBits());
    }

    private static void invoke(long image,Registers r,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,long site,long target,long instructionBytes) {
        memory.writeQword(r.rsp-8L,image+site+instructionBytes);
        r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,
                r.rsp,r.volatileBits(),r.nonvolatileBits())));
    }
}
