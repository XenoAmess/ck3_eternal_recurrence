package org.xar.ck3.research.m3.fc74238;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Normal supplied-storage business projection; no physical frame, NV, flags or EH result. */
public final class Fc74Api238 {
    private Fc74Api238() { }

    public record Input(long moduleBase, int entryEcxBits) { }

    public interface Ports {
        int callIat43da738(NativeTaskMemory memory, long siteRva, long actualTarget, int entryEcxBits);
        long call424e900(NativeTaskMemory memory, long siteRva, int ecxBits);
        int call424e948(NativeTaskMemory memory, long siteRva, int ecxBits, long rdxBits);
        long call424e2ec(NativeTaskMemory memory, long siteRva, long rcxBits, long rdxBits);
        void call424e364(NativeTaskMemory memory, long siteRva, long rcxBits);
        void call424f8a8(NativeTaskMemory memory, long siteRva, long rcxBits);
        default void call424f8a8(NativeTaskMemory memory, long siteRva, long rcxBits, long calleeEntryRsp) {
            call424f8a8(memory, siteRva, rcxBits);
        }
        void callIat43da420(NativeTaskMemory memory, long siteRva, long actualTarget, int ecxBits);
    }
}
