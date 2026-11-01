package org.xar.ck3.research.m3.out224;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.gs223.GsFlag223Api;
import org.xar.ck3.research.m3.out224.OutHelper224Api;

public final class OutHelperFromGsBinding224 {
    private OutHelperFromGsBinding224() { }

    public static GsFlag223Api.Ports bind(NativeTaskMemory captured, long moduleBase,
            OutHelper224Api.Ports child, GsFlag223Api.Ports fallback) {
        if (captured == null) throw new NullPointerException("captured");
        if (child == null) throw new NullPointerException("child");
        if (fallback == null) throw new NullPointerException("fallback");

        return new GsFlag223Api.Ports() {
            @Override
            public long readGs60(NativeTaskMemory memory, long siteRva) {
                return fallback.readGs60(memory, siteRva);
            }

            @Override
            public void call424e620(NativeTaskMemory memory, long siteRva, long rcx) {
                if (memory != captured) {
                    throw new IllegalArgumentException("memory mismatch");
                }
                if (siteRva != 0x425921BL) {
                    throw new IllegalArgumentException("site mismatch");
                }
                OutHelper424E620.execute(captured, child, new OutHelper224Api.Input(moduleBase, rcx));
            }
        };
    }
}