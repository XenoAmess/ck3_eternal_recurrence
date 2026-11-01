package org.xar.ck3.research.m3.out234;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Explicit normal downstream result; not an int extension or a full CPU result. */
public interface OutStaticDispatch234Api {
    @FunctionalInterface
    interface TailPort {
        long jumpRax(NativeTaskMemory memory, long siteRva, long targetRax,
                     long knownRcx, long knownRdx);
    }
}
