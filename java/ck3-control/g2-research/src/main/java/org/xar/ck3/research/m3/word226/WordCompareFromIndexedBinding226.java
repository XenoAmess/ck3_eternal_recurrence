package org.xar.ck3.research.m3.word226;

import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m3.word226.WordCompare226Api;

public final class WordCompareFromIndexedBinding226 {
    private WordCompareFromIndexedBinding226() { }

    public static IndexedHelper225Api.Ports bind(WordCompareBinding226Api.Memory captured, WordCompare226Api algorithm, IndexedHelper225Api.Ports fallback) {
        return new IndexedHelper225Api.Ports() {
            @Override
            public long call43da478(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx, int edx, int r8d) {
                return fallback.call43da478(memory, siteRva, actualTarget, rcx, edx, r8d);
            }

            @Override
            public int call43da738(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget) {
                return fallback.call43da738(memory, siteRva, actualTarget);
            }

            @Override
            public int call4246a60(IndexedHelper225Api.Memory memory, long siteRva, long rcx, long rdx, int r8d) {
                if (memory != captured || (siteRva != 0x424E514L && siteRva != 0x424E52AL)) {
                    throw new IllegalArgumentException("Invalid active site or memory identity");
                }
                WordCompare226Api.Result result = algorithm.execute(captured, rcx, rdx, Integer.toUnsignedLong(r8d));
                return result.difference32();
            }

            @Override
            public void call43da7c0(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx) {
                fallback.call43da7c0(memory, siteRva, actualTarget, rcx);
            }

            @Override
            public long call43da680(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx, long rdx) {
                return fallback.call43da680(memory, siteRva, actualTarget, rcx, rdx);
            }
        };
    }
}