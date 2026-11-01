package org.xar.ck3.research.m3.e948240;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Normal supplied-storage projection; opaque calls retain their own effects and returns. */
public final class E948Api240 {
    private E948Api240() { }

    public record Input(long moduleBase, int entryEcxBits, long entryRdxBits) { }

    public interface Ports {
        long call424e448(NativeTaskMemory memory, long siteRva, int ecxBits, long rdxBits, long r8Bits, long r9Bits);
        long callIat43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, int ecxBits, long rdxBits);
        long callIat43da470(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, int ecxBits, long rdxBits);
    }
}
