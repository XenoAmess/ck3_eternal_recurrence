package org.xar.ck3.research.m3.clear230;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.stack229.StackContext229Api;

/**
 * Binding for the 229 caller site to the 230 callee.
 * Validates memory identity and site RVA for the active call, then delegates to the leaf.
 * Passive calls delegate exactly once to the fallback with original arguments.
 */
public final class EncodedClearFromStackBinding230 {

    public static StackContext229Api.Ports bind(
            long moduleBase,
            NativeTaskMemory capturedMemory,
            EncodedClear230Api.Ports childPorts,
            StackContext229Api.Ports fallback) {

        return new StackContext229Api.Ports() {

            @Override
            public void call4247ffc(NativeTaskMemory memory, long siteRva, int ecx) {
                fallback.call4247ffc(memory, siteRva, ecx);
            }

            @Override
            public long call424dd60(NativeTaskMemory memory, long siteRva, long rcx) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x424DB94L) {
                    throw new IllegalArgumentException("Site RVA mismatch");
                }
                return EncodedClear424DD60.execute(capturedMemory, childPorts, new EncodedClear230Api.Input(moduleBase, rcx));
            }

            @Override
            public void call4248050(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx) {
                fallback.call4248050(memory, siteRva, ecx, liveRbx);
            }
        };
    }
}