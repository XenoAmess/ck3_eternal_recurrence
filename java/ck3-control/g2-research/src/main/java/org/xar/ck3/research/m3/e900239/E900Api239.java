package org.xar.ck3.research.m3.e900239;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Normal supplied-storage tail projection of exact70B424E900; no physical CPU/EH state. */
public final class E900Api239 {
    private E900Api239() { }
    public record Input(long moduleBase, int entryEcxBits) { }
    public interface Ports {
        long call424e448(NativeTaskMemory memory, long siteRva, int ecxBits,
                        long rdxBits, long r8Bits, long r9Bits);
        long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget,
                         long liveRax, int ecxBits);
        long tail43da460(NativeTaskMemory memory, long siteRva, long actualTarget,
                         long liveRax, int ecxBits);
    }
}
