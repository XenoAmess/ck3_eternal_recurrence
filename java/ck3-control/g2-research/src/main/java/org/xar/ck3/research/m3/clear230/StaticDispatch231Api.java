package org.xar.ck3.research.m3.clear230;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Existing business projection: the real downstream int is ignored by clear230. */
public interface StaticDispatch231Api {
    @FunctionalInterface
    interface TailPort {
        int jumpRax(NativeTaskMemory memory, long siteRva, long targetRax,
                    long knownRcx, EncodedClear230Api.IndirectArguments arguments);
    }
}
