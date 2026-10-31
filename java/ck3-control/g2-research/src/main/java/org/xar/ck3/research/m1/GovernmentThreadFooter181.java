package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

/** Owner implementation after two rejected candidates; complete held96B normal source only. */
public final class GovernmentThreadFooter181 {
    private GovernmentThreadFooter181() { }
    public static GovernmentCallee164Api.NormalReturn execute(GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,GovernmentThreadHeader178Api.Ports ports) {
        Registers r=GovernmentCallee164Api.registers(entry);long image=entry.imageBaseBits();
        r.rsp-=8;memory.writeQword(r.rsp,r.rbx);r.rsp-=0x20;r.rbx=r.rcx;
        r.rcx=image+0x5C5CB18L;
        memory.writeQword(r.rsp-8,image+0x4223A3AL);
        r.apply(ports.invokeIat(new GovernmentThreadHeader178Api.IatCall(
                0x4223A34L,0x43DA500L,r.rsp,false,r.volatileBits(),r.nonvolatileBits())));
        r.rax=Integer.toUnsignedLong(memory.readDword(image+0x542F090L));
        r.rcx=image+0x5C5CB18L;
        r.rdx=Integer.toUnsignedLong(memory.readDword(image+0x5C5CBC4L));
        r.rax=Integer.toUnsignedLong((int)r.rax+1);
        memory.writeDword(image+0x542F090L,(int)r.rax);memory.writeDword(r.rbx,(int)r.rax);
        r.rax=ports.readGsQword58();r.r9=0x10;
        r.r8=memory.readQword(r.rax+r.rdx*8);
        r.rax=Integer.toUnsignedLong(memory.readDword(image+0x542F090L));
        memory.writeDword(r.r9+r.r8,(int)r.rax);
        memory.writeQword(r.rsp-8,image+0x4223A7AL);
        r.apply(ports.invokeIat(new GovernmentThreadHeader178Api.IatCall(
                0x4223A74L,0x43DA4F0L,r.rsp,false,r.volatileBits(),r.nonvolatileBits())));
        r.rsp+=0x20;r.rbx=memory.readQword(r.rsp);r.rsp+=8;
        return GovernmentThreadNotify181.execute(new GovernmentCallee164Api.Entry(
                image,r.rsp,r.volatileBits(),r.nonvolatileBits()),memory,ports);
    }
}
