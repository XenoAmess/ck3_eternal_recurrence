package org.xar.ck3.research.m3.dispatch218;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Only supplied-storage body observations of exact56B; prologue/epilogue/RET/NV/CPU/EH are excluded. */
public interface DispatchHelper218Api {
    record Input(long rdxAddress, long r8Address, long r9Address) { }
    interface Ports {
        void enter(NativeTaskMemory memory, long siteRva, int ecx);
        void call42420f8(NativeTaskMemory memory, long siteRva, long rcx);
        long leave(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx);
    }
    /** Result-bearing opaque jump ports; they address the same supplied storage. No invented post-RAX. */
    interface ResultTails {
        void jump43da500(NativeTaskMemory memory, long knownRcx, long knownRax);
        long jump43da4f0(NativeTaskMemory memory, long knownRcx, long knownRax, long liveRbx);
    }
}
