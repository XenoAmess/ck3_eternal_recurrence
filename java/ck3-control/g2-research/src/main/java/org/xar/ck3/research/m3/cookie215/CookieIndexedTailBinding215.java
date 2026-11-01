package org.xar.ck3.research.m3.cookie215;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;

public final class CookieIndexedTailBinding215 {
    private CookieIndexedTailBinding215() { }

    public static CookieHelper215Api.Ports bind(long moduleBase,
            NativeTaskMemory capturedMemory, RequestIndexedTails4247ffc.Ports existingPorts) {
        if (capturedMemory == null) {
            throw new NullPointerException("capturedMemory");
        }
        if (existingPorts == null) {
            throw new NullPointerException("existingPorts");
        }

        return new CookieHelper215Api.Ports() {
            @Override
            public void enter(NativeTaskMemory memory, long siteRva, int ecxBits) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x4246EB0L) {
                    throw new IllegalArgumentException("Invalid site for enter");
                }
                RequestIndexedTails4247ffc.call4247ffc(moduleBase, ecxBits, existingPorts);
            }

            @Override
            public void leave(NativeTaskMemory memory, long siteRva, int ecxBits, long liveRbxBits) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x4246ECEL) {
                    throw new IllegalArgumentException("Invalid site for leave");
                }
                RequestIndexedTails4247ffc.call4248050(moduleBase, ecxBits, liveRbxBits, existingPorts);
            }
        };
    }
}