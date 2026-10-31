package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Exact supplied8B source: full64 RAX from one current global read; no otherABI or identity. */
public final class LoadPdxWindowValue178 {
    private LoadPdxWindowValue178() { }
    @FunctionalInterface
    public interface Memory { long readPointer(long address); }
    public static long readRax(long moduleBase, Memory memory) {
        long targetRVA = 0x5C6A690L;
        return memory.readPointer(moduleBase + targetRVA);
    }
}
