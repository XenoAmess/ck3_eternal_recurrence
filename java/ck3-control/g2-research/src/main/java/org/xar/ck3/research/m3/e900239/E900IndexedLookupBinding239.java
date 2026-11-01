package org.xar.ck3.research.m3.e900239;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m3.indexed225.IndexedLookupHelper424E448;
import org.xar.ck3.research.m3.e900239.E900Api239;

public final class E900IndexedLookupBinding239 {
    private E900IndexedLookupBinding239() { }

    public static E900Api239.Ports bind(long moduleBase,
            IndexedHelper225Api.Memory capturedMemory,
            IndexedHelper225Api.Ports child,
            E900Api239.Ports fallback) {
        if (capturedMemory == null) {
            throw new NullPointerException("capturedMemory");
        }
        if (child == null) {
            throw new NullPointerException("child");
        }
        if (fallback == null) {
            throw new NullPointerException("fallback");
        }

        return new E900Api239.Ports() {
            @Override
            public long call424e448(NativeTaskMemory memory, long siteRva, int ecxBits,
                    long rdxBits, long r8Bits, long r9Bits) {
                if (memory != capturedMemory) {
                    throw new IllegalStateException("Memory identity mismatch");
                }
                if (siteRva != 0x424E922L) {
                    throw new IllegalStateException("Site mismatch");
                }

                IndexedHelper225Api.Input input = new IndexedHelper225Api.Input(
                        moduleBase,
                        ecxBits,
                        rdxBits,
                        r8Bits,
                        r9Bits
                );

                return IndexedLookupHelper424E448.execute(capturedMemory, child, input);
            }

            @Override
            public long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget,
                    long liveRax, int ecxBits) {
                return fallback.tail43dbba8(memory, siteRva, actualTarget, liveRax, ecxBits);
            }

            @Override
            public long tail43da460(NativeTaskMemory memory, long siteRva, long actualTarget,
                    long liveRax, int ecxBits) {
                return fallback.tail43da460(memory, siteRva, actualTarget, liveRax, ecxBits);
            }
        };
    }
}