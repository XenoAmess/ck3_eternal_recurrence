package org.xar.ck3.research.m3.indexed225;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.out224.OutHelper224Api;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;

public final class IndexedLookupFromOutBinding225 {
    private IndexedLookupFromOutBinding225() { }

    public static OutHelper224Api.Ports bind(long moduleBase, IndexedHelper225Api.Memory captured, IndexedHelper225Api.Ports child, OutHelper224Api.Ports fallback) {
        return new OutHelper224Api.Ports() {
            @Override
            public long call424e448(NativeTaskMemory memory, long siteRva, int ecx, long rdx, long r8, long r9) {
                if (memory != captured) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x424E643L) {
                    throw new IllegalArgumentException("Site mismatch");
                }
                IndexedHelper225Api.Input input = new IndexedHelper225Api.Input(moduleBase, ecx, rdx, r8, r9);
                return IndexedLookupHelper424E448.execute(captured, child, input);
            }

            @Override
            public long tail43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, long rcx, long rdx) {
                return fallback.tail43dbba8(memory, siteRva, actualTarget, liveRax, rcx, rdx);
            }
        };
    }
}