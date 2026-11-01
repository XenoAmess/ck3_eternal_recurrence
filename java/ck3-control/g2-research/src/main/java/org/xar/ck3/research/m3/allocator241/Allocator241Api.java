package org.xar.ck3.research.m3.allocator241;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Supplied-storage normal projection; no imported function identity inferred. */
public final class Allocator241Api {
    private Allocator241Api() { }

    public record Input(long moduleBase, long countRaw, long elementBytesRaw) { }

    public interface Ports {
        long allocateImported(NativeTaskMemory memory, long siteRva, long actualTarget, long heapRaw, int flagsRaw32, long byteCountRaw);
        int retryGate(NativeTaskMemory memory, long siteRva);
        int retryCall(NativeTaskMemory memory, long siteRva, long byteCountRaw);
        long failureCellAddress(NativeTaskMemory memory, long siteRva);
    }
}
