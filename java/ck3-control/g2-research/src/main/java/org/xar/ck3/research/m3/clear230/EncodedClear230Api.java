package org.xar.ck3.research.m3.clear230;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Normal supplied-storage business contract; physical CPU/NV/stack/RET/EH excluded. */
public interface EncodedClear230Api {
    record Input(long moduleBase, long entryRcx) { }

    /** Entry RDX/R9 are unobserved; source establishes both after a normal callback. */
    sealed interface RdxR9 permits EntryUnknown, Reloaded { }
    enum EntryUnknown implements RdxR9 { UNKNOWN }
    record Reloaded(long rdx, long r9) implements RdxR9 { }

    /** ECX is source low6 cookie count (0..63); R8 is current full64 cookie. */
    record IndirectArguments(int ecx, long r8, RdxR9 rdxR9) { }

    interface Ports {
        void call43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget,
                        long liveRax, IndirectArguments arguments);
        void call424e364(NativeTaskMemory memory, long siteRva, long rcx);
    }
}
