package org.xar.ck3.research.m3.stack229;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Normal business projection of 424DB74; physical stack/NV/RET/EH excluded. */
public interface StackContext229Api {
    record Input(long rdxAddress, long r8Address, long r9Address) { }

    interface Ports {
        void call4247ffc(NativeTaskMemory memory, long siteRva, int ecx);
        long call424dd60(NativeTaskMemory memory, long siteRva, long rcx);
        void call4248050(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx);
    }

    interface Tails {
        void jump43da500(NativeTaskMemory memory, long knownRcx, long liveRax);
        void jump43da4f0(NativeTaskMemory memory, long knownRcx, long liveRax, long liveRbx);
    }
}
