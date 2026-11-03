package org.xar.ck3.study.m6.full239;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;

/** One mechanical owned5-byte direct CALL; child meaning is explicitly opaque185. */
public final class Transfer4Calls239 {
    private Transfer4Calls239() { }
    public static void direct(Frame f,long siteRva,long targetRva) {
        f.memory.writeQword(f.r.rsp-0x8L,f.image+siteRva+0x5L);
        f.r.apply(f.calls.invoke(new Call(siteRva,TargetKind.DIRECT_RVA,targetRva,f.r.rsp,
                f.r.volatileBits(),f.r.nonvolatileBits())));
    }
}
