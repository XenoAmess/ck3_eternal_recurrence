package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.indexed229.AtomicIndexedMemory229;
import org.xar.ck3.control.g2.m2.nativecode.E900Fp627Api;
import org.xar.ck3.control.g2.m2.nativecode.Indexed448Fp628Api;
import org.xar.ck3.control.g2.m2.nativecode.Fc74Fp626Api;

/**
 * Thin assembly composing KnownFc74E900Fp627 and KnownE900IndexedFp628.
 * No new algorithm, no state repair, no execution claim.
 */
public final class KnownFc74IndexedFp629 {
    private KnownFc74IndexedFp629() { }

    public static Fc74Fp626Api.Calls bind(AtomicIndexedMemory229 memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Indexed448Fp628Api.Calls inner,
            E900Fp627Api.Calls e900Foreign,
            Fc74Fp626Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(inner);
        Objects.requireNonNull(e900Foreign);
        Objects.requireNonNull(foreign);

        // Compose the inner E900 layer using the indexed memory and budget
        E900Fp627Api.Calls e900Layer = KnownE900IndexedFp628.bind(memory, budget, inner, e900Foreign);

        // Compose the outer FC74 layer using the composed E900 layer
        return KnownFc74E900Fp627.bind(memory, e900Layer, foreign);
    }
}