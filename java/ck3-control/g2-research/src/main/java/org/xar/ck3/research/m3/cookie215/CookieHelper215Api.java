package org.xar.ck3.research.m3.cookie215;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Explicit business projection of the supplied 69-byte normal body; no CPU/EH/RET model. */
public final class CookieHelper215Api {
    private CookieHelper215Api() { }

    /** Entry RCX/R8 are not consumed by this body. Addresses and base retain all raw64 bits. */
    public record Input(long moduleBase, long rdxAddress, long r9Address) { }

    /** Actual ECX DWORD bits; shared Memory identity is explicit across opaque callbacks. */
    public interface Ports {
        void enter(NativeTaskMemory memory, long siteRva, int ecxBits);
        void leave(NativeTaskMemory memory, long siteRva, int ecxBits, long liveRbxBits);
    }
}
