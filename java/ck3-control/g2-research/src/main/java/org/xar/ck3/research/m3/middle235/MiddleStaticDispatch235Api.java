package org.xar.ck3.research.m3.middle235;

import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;

/** Real inner jump result; supplied-storage business arguments, no full CPU result. */
public interface MiddleStaticDispatch235Api {
    @FunctionalInterface
    interface TailPort {
        int jumpRax(DispatchMiddle219Api.Memory memory, long siteRva,
                    long targetRax, long knownRcx, int edx, int r8d);
    }
}
