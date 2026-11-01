package org.xar.ck3.research.m3.cookie215;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.handler211.Wrapper4246FB4Api211;
import org.xar.ck3.research.m3.cookie215.CookieHelper215Api;
import org.xar.ck3.research.m3.cookie215.CookieHelper4246E9C;

public final class CookieWrapperBinding215 {
    private CookieWrapperBinding215() { }

    public static Wrapper4246FB4Api211.Ports bind(long moduleBase,
            NativeTaskMemory capturedMemory, CookieHelper215Api.Ports ports) {
        java.util.Objects.requireNonNull(capturedMemory, "capturedMemory");
        java.util.Objects.requireNonNull(ports, "ports");

        return new Wrapper4246FB4Api211.Ports() {
            @Override
            public long call4246e9c(NativeTaskMemory memory, long siteRva, long rcx, long rdx, long r8, long r9) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x4246FD8L) {
                    throw new IllegalArgumentException("Invalid site RVA");
                }

                CookieHelper215Api.Input input = new CookieHelper215Api.Input(moduleBase, rdx, r9);
                return CookieHelper4246E9C.execute(input, capturedMemory, ports);
            }
        };
    }
}
