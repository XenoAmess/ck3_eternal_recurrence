package org.xar.ck3.research.m4;

import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestRetry4223b94;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

/** Normal60B boundary; original error CALL+INT3 remains legacy UnexecutedSourcePath. */
public final class Retry60NormalFullState284 {
    private Retry60NormalFullState284() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls, GovernmentCrtBoundary185Api.LoopBudget budget) {
        long image=entry.imageBaseBits(),s=entry.rspBits(),pre=s-0x28L;
        long size=entry.volatileBits().rcxBits();
        var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image,s,entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(s-8,r.rbx);r.rsp=pre;r.rbx=size;
        long out=RequestRetry4223b94.execute(size,new RequestRetry4223b94.Ports(){
            @Override public long call42420b8(long knownRcx){
                r.rcx=knownRcx;budget.beforeStep(0x4223BAEL,knownRcx);
                memory.writeQword(pre-8,image+0x4223BB3L);
                r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(0x4223BAEL,
                        GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x42420B8L,
                        pre,r.volatileBits(),r.nonvolatileBits())));
                return r.rax;
            }
            @Override public int call424cffc(long knownRcx){
                r.rcx=knownRcx;memory.writeQword(pre-8,image+0x4223BA7L);
                r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(0x4223BA2L,
                        GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424CFFCL,
                        pre,r.volatileBits(),r.nonvolatileBits())));
                return(int)r.rax;
            }
        });
        r.rax=out;r.rsp+=0x20L;r.rbx=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);r.rsp+=8;
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
}
