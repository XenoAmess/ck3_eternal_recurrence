package org.xar.ck3.research.m3.e948240;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.e948240.E948Api240;

public final class E948FromFc74Binding240 {
    private E948FromFc74Binding240() { }

    public static Fc74Api238.Ports bind(long moduleBase, NativeTaskMemory capturedMemory, E948Api240.Ports child, Fc74Api238.Ports fallback) {
        if (capturedMemory == null) {
            throw new NullPointerException("capturedMemory");
        }
        if (child == null) {
            throw new NullPointerException("child");
        }
        if (fallback == null) {
            throw new NullPointerException("fallback");
        }

        return new Fc74Api238.Ports() {
            @Override
            public int callIat43da738(NativeTaskMemory memory, long siteRva, long actualTarget, int entryEcxBits) {
                return fallback.callIat43da738(memory, siteRva, actualTarget, entryEcxBits);
            }

            @Override
            public long call424e900(NativeTaskMemory memory, long siteRva, int ecxBits) {
                return fallback.call424e900(memory, siteRva, ecxBits);
            }

            @Override
            public int call424e948(NativeTaskMemory memory, long siteRva, int ecxBits, long rdxBits) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424FCB9L && siteRva != 0x424FCE1L && siteRva != 0x424FCF2L && siteRva != 0x424FD03L) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                E948Api240.Input input = new E948Api240.Input(moduleBase, ecxBits, rdxBits);
                long result = E948Target424E948.execute(memory, child, input);
                return (int) result;
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