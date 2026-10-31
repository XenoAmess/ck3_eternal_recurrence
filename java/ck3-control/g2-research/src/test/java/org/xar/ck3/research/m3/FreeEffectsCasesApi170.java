package org.xar.ck3.research.m3;

import java.util.List;

/** Test data only; observable read/callback order is independent from the target. */
public final class FreeEffectsCasesApi170 {
    private FreeEffectsCasesApi170() { }
    public record Word(long address,long value) { }
    public record Scenario(String id,long moduleBase,long receiver,long rows,long alignment,
        FreeEffectsApi170.Targets targets,List<Word> initialWords,int heapFreeReturn,
        int lastErrorBits,int mappedBits,int initialCell,int expectedFinalCell,
        List<String> expectedEvents,FreeEffectsApi170.Outcome expectedOutcome) { }
}
