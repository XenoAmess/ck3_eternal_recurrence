package org.xar.ck3.research.m3.gs223;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Supplied-storage normal60B only; no CPU/NV/RET/DF/OS projection. */
public interface GsFlag223Api {
    record Scratch(long entryRsp) { }
    interface Ports {
        long readGs60(NativeTaskMemory memory, long siteRva);
        void call424e620(NativeTaskMemory memory, long siteRva, long rcx);
    }
}
