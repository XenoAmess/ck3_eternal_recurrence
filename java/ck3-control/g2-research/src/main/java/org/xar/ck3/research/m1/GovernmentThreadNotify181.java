package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api.Memory;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.Ports;

/** Model02 branch framework, owner API/initialRAX/actualRET corrections; no OS effects inferred. */
public final class GovernmentThreadNotify181 {
    private GovernmentThreadNotify181() { }
    public static NormalReturn execute(Entry entry,Memory memory,Ports ports) {
        Registers r=GovernmentCallee164Api.registers(entry);
        long e=entry.frameRspBits(),img=entry.imageBaseBits();r.rsp=e-0x28;
        long g1=img+0x5C5CB48L,g2=img+0x5C5CB08L,g3=img+0x5C5CB10L;
        r.rax=memory.readQword(g1);
        if(r.rax!=0) {
            r.rcx=g2;r.rsp=e;
            r.apply(ports.invokeIat(new IatCall(0x4223B07L,0x43DBBA8L,e,true,r.volatileBits(),r.nonvolatileBits())));
            return new NormalReturn(r.volatileBits(),r.nonvolatileBits(),memory.readQword(e),e+8);
        }
        r.rcx=memory.readQword(g3);long w=e-0x28;
        memory.writeQword(w-8,img+0x4223B1BL);
        r.apply(ports.invokeIat(new IatCall(0x4223B15L,0x43DA5B0L,w,false,r.volatileBits(),r.nonvolatileBits())));
        r.rcx=memory.readQword(g3);r.rsp=e;
        r.apply(ports.invokeIat(new IatCall(0x4223B26L,0x43DA4A8L,e,true,r.volatileBits(),r.nonvolatileBits())));
        return new NormalReturn(r.volatileBits(),r.nonvolatileBits(),memory.readQword(e),e+8);
    }
}
