package org.xar.ck3.research.m3.stack229;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.stack227.StackContext227Api;
import org.xar.ck3.research.m3.stack229.StackContext229Api;

/**
 * Actual227 binder for 424DB74@424DEB8.
 * Implements StackContext227Api.Ports.
 * Nonactive siteRva delegates original fallback once with all unchanged parameters and raw return/exception.
 * Active site validates exact captured Memory identity, then invokes StackContext424DB74.execute exactly once.
 * No factory frame capture, no rederive from E, no writes/reads/push in binder.
 */
public final class StackContextBinding229 {
    private StackContextBinding229() { }

    public static StackContext227Api.Ports bind(NativeTaskMemory captured, StackContext229Api.Ports child, StackContext227Api.Ports fallback) {
        return new StackContext227Api.Ports() {
            @Override
            public long call424db74(NativeTaskMemory memory, long siteRva, long rcx, long rdx, long r8, long r9) {
                if (siteRva != 0x424DEB8L) {
                    return fallback.call424db74(memory, siteRva, rcx, rdx, r8, r9);
                }
                if (memory != captured) {
                    throw new IllegalArgumentException("Wrong memory for active call424db74");
                }
                StackContext229Api.Input input = new StackContext229Api.Input(rdx, r8, r9);
                return StackContext424DB74.execute(captured, child, input);
            }
        };
    }
}