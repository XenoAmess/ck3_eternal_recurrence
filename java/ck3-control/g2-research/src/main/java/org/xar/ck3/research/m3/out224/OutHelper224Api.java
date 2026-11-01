package org.xar.ck3.research.m3.out224;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Source-owned supplied-storage projection of 78B 424E620, excluding full CPU ABI. */
public final class OutHelper224Api {
    private OutHelper224Api() { }
    public record Input(long moduleBase, long entryRcx) { }
    public interface Ports {
        long call424e448(NativeTaskMemory memory, long siteRva, int ecx,
                        long rdx, long r8, long r9);
        long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget,
                        long liveRax, long rcx, long rdx);
    }
}
