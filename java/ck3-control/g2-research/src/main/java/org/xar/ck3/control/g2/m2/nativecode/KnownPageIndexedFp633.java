package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageFp619;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateIndexedFp632;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;
import org.xar.ck3.control.g2.m2.nativecode.KnownHeapAllocateFp623;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageAllocateFp622;
import org.xar.ck3.control.g2.m2.nativecode.Indexed448Fp628Api;
import org.xar.ck3.control.g2.m2.nativecode.E900Fp627Api;
import org.xar.ck3.control.g2.m2.nativecode.Fc74Fp626Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Leaf-specific capability-union factory composing KnownAllocateIndexedFp632 and KnownPageAllocateFp622.
 * No new algorithm, no state repair, no execution claim.
 */
public final class KnownPageIndexedFp633 {
    private KnownPageIndexedFp633() { }

    /**
     * Nested Memory interface combining KnownPageFp619.Memory and KnownAllocateIndexedFp632.Memory.
     * Ensures the same memory object supports both atomic QWORD exchange and exact 16-bit reads.
     */
    public interface Memory extends KnownPageFp619.Memory, KnownAllocateIndexedFp632.Memory {
        @Override int readUnsigned16(long addressBits);
    }

    /**
     * Binds the composed Page -> Retry -> Allocate -> Error -> FC74 -> E900 -> Indexed448 -> WordCompare chain using a single Memory instance.
     * First composes the Allocate layer, then the Retry layer, then the Page layer.
     */
    public static KnownPageFp619.Calls bind(Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Indexed448Fp628Api.Calls indexedForeign,
            E900Fp627Api.Calls e900Foreign,
            Fc74Fp626Api.Calls fc74Foreign,
            KnownAllocateErrorFp625.ErrorCalls errorForeign,
            KnownHeapAllocateFp623.AllocateCalls allocateForeign,
            KnownPageAllocateFp622.RetryCalls retryForeign,
            KnownPageFp619.Calls pageForeign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(indexedForeign);
        Objects.requireNonNull(e900Foreign);
        Objects.requireNonNull(fc74Foreign);
        Objects.requireNonNull(errorForeign);
        Objects.requireNonNull(allocateForeign);
        Objects.requireNonNull(retryForeign);
        Objects.requireNonNull(pageForeign);

        // Compose the Allocate layer using the same memory, budget, and foreign calls
        KnownHeapAllocateFp623.AllocateCalls allocate = KnownAllocateIndexedFp632.bind(
                memory, budget, indexedForeign, e900Foreign, fc74Foreign, errorForeign, allocateForeign);

        // Compose the Retry layer using the same memory, budget, allocate, and retryForeign
        KnownPageAllocateFp622.RetryCalls retry = KnownHeapAllocateFp623.bind(
                memory, budget, allocate, retryForeign);

        // Compose the Page layer using the same memory, budget, retry, and pageForeign
        return KnownPageAllocateFp622.bind(
                memory, budget, retry, pageForeign);
    }
}