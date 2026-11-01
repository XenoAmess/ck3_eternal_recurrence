package org.xar.ck3.research.m3.dispatch219;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper218Api;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;

/** Actual218 middlebinding: only call42420f8@42420E0 active; other ports exact fallback. */
public final class DispatchMiddleBinding219 {
    private DispatchMiddleBinding219() { }

    public static DispatchHelper218Api.Ports bind(DispatchMiddle219Api.Memory captured, long moduleBase, DispatchMiddle219Api.Ports child, DispatchHelper218Api.Ports fallback) {
        return new DispatchHelper218Api.Ports() {
            @Override
            public void enter(NativeTaskMemory memory, long siteRva, int ecx) {
                fallback.enter(memory, siteRva, ecx);
            }

            @Override
            public void call42420f8(NativeTaskMemory memory, long siteRva, long rcx) {
                if (memory != captured || siteRva != 0x42420E0L) {
                    throw new IllegalArgumentException("Wrong memory or site for active call42420f8");
                }
                DispatchMiddle219Api.Input input = new DispatchMiddle219Api.Input(moduleBase, rcx);
                DispatchMiddle42420F8.execute(captured, child, input);
            }

            @Override
            public void call42420f8(NativeTaskMemory memory, long siteRva, long rcx, long calleeEntryRsp) {
                if (memory != captured || siteRva != 0x42420E0L) {
                    throw new IllegalArgumentException("Wrong memory or site for active call42420f8");
                }
                DispatchMiddle219Api.Input input = new DispatchMiddle219Api.Input(moduleBase, rcx);
                DispatchMiddle42420F8.execute(captured, child, input, calleeEntryRsp);
            }

            @Override
            public long leave(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx) {
                return fallback.leave(memory, siteRva, ecx, liveRbx);
            }
        };
    }
}