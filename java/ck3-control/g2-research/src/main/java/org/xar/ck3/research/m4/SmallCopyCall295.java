package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

public final class SmallCopyCall295 {
    private SmallCopyCall295() { }

    public static void invoke(long imageBaseBits, Registers r, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls) {
        long preSP = r.rsp;
        memory.writeQword(preSP - 8L, imageBaseBits + 0x1A8124CL);
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
            0x1A81247L,
            GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            0x4226860L,
            preSP,
            r.volatileBits(),
            r.nonvolatileBits()
        );
        var returned = calls.invoke(call);
        r.apply(returned);
    }
}