package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.indexed229.AtomicIndexedMemory229;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalTailTarget42421c8213;
import org.xar.ck3.control.g2.m2.nativecode.Indexed448Fp628Api;
import org.xar.ck3.control.g2.m2.nativecode.E900Fp627Api;
import org.xar.ck3.control.g2.m2.nativecode.Fc74Fp626Api;
import org.xar.ck3.control.g2.m2.nativecode.WordCompareFp630;
import org.xar.ck3.control.g2.m2.nativecode.KnownFc74IndexedFp629;

/**
 * Leaf-specific capability-union factory composing KnownFc74IndexedFp629 and WordCompareFp630.
 * No new algorithm, no state repair, no execution claim.
 */
public final class KnownFc74IndexedWordFp631 {
    private KnownFc74IndexedWordFp631() { }

    /**
     * Nested Memory interface combining AtomicIndexedMemory229 and TerminalTailTarget42421c8213.Memory16.
     * Ensures the same memory object supports both atomic QWORD exchange and exact 16-bit reads.
     */
    public interface Memory extends AtomicIndexedMemory229, TerminalTailTarget42421c8213.Memory16 {
        @Override int readUnsigned16(long addressBits);
    }

    /**
     * Binds the composed FC74 -> E900 -> Indexed448 -> WordCompare chain using a single Memory instance.
     * First composes the WordCompare layer, then the Indexed448 layer, then the E900 layer, then the FC74 layer.
     */
    public static Fc74Fp626Api.Calls bind(Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Indexed448Fp628Api.Calls indexedForeign,
            E900Fp627Api.Calls e900Foreign,
            Fc74Fp626Api.Calls fc74Foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(indexedForeign);
        Objects.requireNonNull(e900Foreign);
        Objects.requireNonNull(fc74Foreign);

        // Compose the WordCompare layer using the same memory and indexedForeign
        Indexed448Fp628Api.Calls wordCalls = WordCompareFp630.bind(memory, indexedForeign);

        // Compose the full chain using the same memory, budget, wordCalls, e900Foreign, and fc74Foreign
        return KnownFc74IndexedFp629.bind(memory, budget, wordCalls, e900Foreign, fc74Foreign);
    }
}