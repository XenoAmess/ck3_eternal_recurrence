package org.xar.ck3.research.m3.indexed225;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Supplied-memory normal470B business boundary; no CPU, EH or hardware atomicity claim. */
public interface IndexedHelper225Api {
    interface Memory extends NativeTaskMemory {
        /** One QWORD exchange effect returning its observed old bits. */
        long exchangeInt64(long address, long newValue);
    }
    record Input(long moduleBase, int index, long nameAddress, long listBegin, long listEnd) { }
    interface Ports {
        long call43da478(Memory memory, long siteRva, long actualTarget, long rcx, int edx, int r8d);
        int call43da738(Memory memory, long siteRva, long actualTarget);
        int call4246a60(Memory memory, long siteRva, long rcx, long rdx, int r8d);
        void call43da7c0(Memory memory, long siteRva, long actualTarget, long rcx);
        long call43da680(Memory memory, long siteRva, long actualTarget, long rcx, long rdx);
    }
}
