package org.xar.ck3.research.m3.e948240;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.e948240.E948Api240.Ports;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m3.indexed225.IndexedLookupHelper424E448;

/** Mature adapter for 424E448; reuses existing 225 algorithm via explicit strong memory. */
public final class E948IndexedLookupBinding240 {
    private E948IndexedLookupBinding240() { }

    public static Ports bind(long moduleBase, IndexedHelper225Api.Memory capturedMemory, IndexedHelper225Api.Ports child, Ports fallback) {
        if (capturedMemory == null) {
            throw new RuntimeException("Null capturedMemory");
        }
        if (child == null) {
            throw new RuntimeException("Null child");
        }
        if (fallback == null) {
            throw new RuntimeException("Null fallback");
        }

        return new Ports() {
            @Override
            public long call424e448(NativeTaskMemory memory, long siteRva, int ecxBits, long rdxBits, long r8Bits, long r9Bits) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424E971L) {
                    throw new RuntimeException("Invalid callsite");
                }
                return IndexedLookupHelper424E448.execute(
                    capturedMemory,
                    child,
                    new IndexedHelper225Api.Input(moduleBase, ecxBits, rdxBits, r8Bits, r9Bits)
                );
            }

            @Override
            public long callIat43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, int ecxBits, long rdxBits) {
                return fallback.callIat43dbba8(memory, siteRva, actualTarget, liveRax, ecxBits, rdxBits);
            }

            @Override
            public long callIat43da470(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, int ecxBits, long rdxBits) {
                return fallback.callIat43da470(memory, siteRva, actualTarget, liveRax, ecxBits, rdxBits);
            }
        };
    }
}