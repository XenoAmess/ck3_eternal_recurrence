package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.Add4Fp639Api;
import org.xar.ck3.control.g2.m2.nativecode.Element150Fp643Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedClearFp645Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsFp637;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsKnownConstruct644;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedClearWithFp645;
import org.xar.ck3.control.g2.m2.nativecode.ParentKnown647Api;

/**
 * Model composition of the actual parent150 port, existing642 routing and sole M3 COPY259 binding,
 * wrapped by the known-clear645 carrier.
 */
public final class EmbeddedElementsAllKnown647 {
    private EmbeddedElementsAllKnown647() { }

    /**
     * Binds the whole-parent647 composition.
     * @param memory Shared memory view.
     * @param budget Loop budget.
     * @param rangeCalls Calls interface for range16.
     * @param unknownCopyTails Handler for unknown COPY tails.
     * @param foreignAddCalls Handler for other legal Add4 frames.
     * @param construct150Calls Calls interface for Element150.
     * @param clearCalls Calls interface for EmbeddedClear.
     * @param foreignParentCalls Handler for other legal parent frames.
     * @return The EmbeddedElementsFp637.Calls implementation.
     */
    public static EmbeddedElementsFp637.Calls bind(
            ParentKnown647Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Range16Fp638Api.Calls rangeCalls,
            FullCopyWithFp613.TailCalls unknownCopyTails,
            Add4Fp639Api.Calls foreignAddCalls,
            Element150Fp643Api.Calls construct150Calls,
            EmbeddedClearFp645Api.Calls clearCalls,
            EmbeddedElementsFp637.Calls foreignParentCalls) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(rangeCalls);
        Objects.requireNonNull(unknownCopyTails);
        Objects.requireNonNull(foreignAddCalls);
        Objects.requireNonNull(construct150Calls);
        Objects.requireNonNull(clearCalls);
        Objects.requireNonNull(foreignParentCalls);

        // Invoke existing644 bind exactly once
        EmbeddedElementsFp637.Calls knownConstructCalls = EmbeddedElementsKnownConstruct644.bind(
                memory,
                budget,
                rangeCalls,
                unknownCopyTails,
                foreignAddCalls,
                construct150Calls,
                foreignParentCalls
        );

        // Invoke existing645 bindClear exactly once around the 644 result
        return EmbeddedClearWithFp645.bindClear(
                memory,
                budget,
                clearCalls,
                knownConstructCalls
        );
    }
}