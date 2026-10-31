package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

/** Complete original58B normal method. Both actual library callees remain full-state ports. */
public final class GovernmentRegistryEntry183 {
    private GovernmentRegistryEntry183() { }

    public static GovernmentCallee164Api.NormalReturn execute(GovernmentCallee164Api.Entry e,
            GovernmentSharedManager167Api.Memory memory, GovernmentPrimaryTail155Api.Calls calls) {
        Objects.requireNonNull(e); Objects.requireNonNull(memory); Objects.requireNonNull(calls);
        Registers r=GovernmentCallee164Api.registers(e);
        r.rsp-=8;
        memory.writeQword(r.rsp,r.rbx);
        r.rsp-=0x20;
        long global=memory.readQword(e.imageBaseBits()+0x5C5CB68L);
        r.rbx=r.rcx;
        long site,target,continuation;
        if(global==-1L) {
            site=0x4223EFBL;target=0x424DE78L;continuation=0x4223F00L;
        } else {
            r.rdx=r.rbx;
            r.rcx=e.imageBaseBits()+0x5C5CB68L;
            site=0x4223F0CL;target=0x424DEECL;continuation=0x4223F11L;
        }
        memory.writeQword(r.rsp-8,e.imageBaseBits()+continuation);
        r.apply(calls.invoke(new GovernmentPrimaryTail155Api.OpaqueCall(
                site,target,r.rsp,r.volatileBits(),r.nonvolatileBits())));
        r.rdx=0;
        if((int)r.rax==0)r.rdx=r.rbx;
        r.rax=r.rdx;
        r.rsp+=0x20;
        r.rbx=memory.readQword(r.rsp);
        r.rsp+=8;
        long rip=memory.readQword(r.rsp);
        r.rsp+=8;
        return new GovernmentCallee164Api.NormalReturn(
                r.volatileBits(),r.nonvolatileBits(),rip,r.rsp);
    }
}
