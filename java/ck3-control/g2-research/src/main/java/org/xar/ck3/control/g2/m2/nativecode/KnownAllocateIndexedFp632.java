package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageFp619;
import org.xar.ck3.control.g2.m2.nativecode.KnownFc74IndexedWordFp631;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;
import org.xar.ck3.control.g2.m2.nativecode.KnownErrorFc74Fp626;
import org.xar.ck3.control.g2.m2.nativecode.KnownHeapAllocateFp623;
import org.xar.ck3.control.g2.m2.nativecode.Indexed448Fp628Api;
import org.xar.ck3.control.g2.m2.nativecode.E900Fp627Api;
import org.xar.ck3.control.g2.m2.nativecode.Fc74Fp626Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Leaf-specific capability-union factory composing KnownFc74IndexedWordFp631 and KnownErrorFc74Fp626.
 * No new algorithm, no state repair, no execution claim.
 */
public final class KnownAllocateIndexedFp632 {
    private KnownAllocateIndexedFp632() { }

    /**
     * Nested Memory interface combining KnownPageFp619.Memory and KnownFc74IndexedWordFp631.Memory.
     * Ensures the same memory object supports both atomic QWORD exchange and exact 16-bit reads.
     */
    public interface Memory extends KnownPageFp619.Memory, KnownFc74IndexedWordFp631.Memory {
        @Override int readUnsigned16(long addressBits);
    }

    /**
     * Binds the composed FC74 -> E900 -> Indexed448 -> WordCompare chain using a single Memory instance.
     * First composes the WordCompare layer, then the Indexed448 layer, then the E900 layer, then the FC74 layer.
     */
    public static KnownHeapAllocateFp623.AllocateCalls bind(Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Indexed448Fp628Api.Calls indexedForeign,
            E900Fp627Api.Calls e900Foreign,
            Fc74Fp626Api.Calls fc74Foreign,
            KnownAllocateErrorFp625.ErrorCalls errorForeign,
            KnownHeapAllocateFp623.AllocateCalls allocateForeign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(indexedForeign);
        Objects.requireNonNull(e900Foreign);
        Objects.requireNonNull(fc74Foreign);
        Objects.requireNonNull(errorForeign);
        Objects.requireNonNull(allocateForeign);

        // Compose the FC74 layer using the same memory, budget, and foreign calls
        Fc74Fp626Api.Calls fc = KnownFc74IndexedWordFp631.bind(memory, budget, indexedForeign, e900Foreign, fc74Foreign);

        // Compose the Error layer using the same memory, fc, and errorForeign
        KnownAllocateErrorFp625.ErrorCalls errors = KnownErrorFc74Fp626.bind(memory, fc, errorForeign);

        // Compose the Allocate layer using the same memory, errors, and allocateForeign
        return KnownAllocateErrorFp625.bind(memory, errors, allocateForeign);
    }
}