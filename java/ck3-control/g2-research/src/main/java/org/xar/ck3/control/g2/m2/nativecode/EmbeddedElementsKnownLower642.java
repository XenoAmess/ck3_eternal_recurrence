package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Owner-authored composition of the existing 640 lower binding and 637 caller routing. */
public final class EmbeddedElementsKnownLower642 {
    private EmbeddedElementsKnownLower642() { }

    public interface Memory extends EmbeddedElementsFp637.Memory, Element172KnownLower640.Memory {
    }

    public static EmbeddedElementsFp637.Calls bind(
            Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Range16Fp638Api.Calls rangeCalls,
            Add4Fp639Api.Calls addCalls,
            EmbeddedElementsFp637.Calls foreignCalls) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(rangeCalls);
        Objects.requireNonNull(addCalls);
        Objects.requireNonNull(foreignCalls);

        Element172Fp636Api.Calls lowerCalls =
                Element172KnownLower640.bind(memory, budget, rangeCalls, addCalls);
        return EmbeddedElementsFp637.bind172(memory, lowerCalls, foreignCalls);
    }
}
