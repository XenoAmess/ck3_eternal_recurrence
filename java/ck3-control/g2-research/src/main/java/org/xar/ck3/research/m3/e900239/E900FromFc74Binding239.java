package org.xar.ck3.research.m3.e900239;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.e900239.E900Api239;

public final class E900FromFc74Binding239 {
    public static Fc74Api238.Ports bind(long moduleBase, NativeTaskMemory capturedMemory, E900Api239.Ports child, Fc74Api238.Ports fallback) {
        if (capturedMemory == null || child == null || fallback == null) {
            throw new NullPointerException("Null dependency");
        }

        return new Fc74Api238.Ports() {
            @Override
            public int callIat43da738(NativeTaskMemory memory, long siteRva, long actualTarget, int entryEcxBits) {
                return fallback.callIat43da738(memory, siteRva, actualTarget, entryEcxBits);
            }

            @Override
            public long call424e900(NativeTaskMemory memory, long siteRva, int ecxBits) {
                if (memory != capturedMemory || siteRva != 0x424FC96L) {
                    throw new IllegalArgumentException("Invalid active call qualification");
                }
                E900Api239.Input input = new E900Api239.Input(moduleBase, ecxBits);
                return E900Target424E900.execute(memory, child, input);
            }

            @Override
            public int call424e948(NativeTaskMemory memory, long siteRva, int ecxBits, long rdxBits) {
                return fallback.call424e948(memory, siteRva, ecxBits, rdxBits);
            }

            @Override
            public long call424e2ec(NativeTaskMemory memory, long siteRva, long rcxBits, long rdxBits) {
                return fallback.call424e2ec(memory, siteRva, rcxBits, rdxBits);
            }

            @Override
            public void call424e364(NativeTaskMemory memory, long siteRva, long rcxBits) {
                fallback.call424e364(memory, siteRva, rcxBits);
            }

            @Override
            public void call424f8a8(NativeTaskMemory memory, long siteRva, long rcxBits) {
                fallback.call424f8a8(memory, siteRva, rcxBits);
            }

            @Override
            public void callIat43da420(NativeTaskMemory memory, long siteRva, long actualTarget, int ecxBits) {
                fallback.callIat43da420(memory, siteRva, actualTarget, ecxBits);
            }
        };
    }
}