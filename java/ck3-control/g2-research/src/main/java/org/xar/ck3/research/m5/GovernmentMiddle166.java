package org.xar.ck3.research.m5;
/** Whole owner integration after two source-rejected model rounds; delegates every native-region algorithm. */
public final class GovernmentMiddle166 {
    private GovernmentMiddle166() { }
    public static GovernmentMiddle166Api.Result execute(GovernmentCompaction160Api.Entry entry,
            GovernmentPrimarySuffix155Api.Memory memory, GovernmentPrimaryTail155Api.Calls calls,
            GovernmentCompaction160Api.Loops compactionBudget,
            InternedLookup155Api.Calls lookupCalls, GovernmentCaller153Api.Calls prefixCalls,
            GovernmentPrimarySuffix155Api.VolatileBoundary boundary,
            GovernmentPrimaryTail155Api.LoopBudget tailBudget) {
        GovernmentCompaction160Api.Join compact=GovernmentCompaction160.execute(entry,memory,calls,compactionBudget);
        if(compact.nextRva()!=0x30a38cfL)throw new UnsupportedOperationException("unsupported compaction continuation "+Long.toHexString(compact.nextRva()));
        GovernmentCompaction160Api.Entry after=new GovernmentCompaction160Api.Entry(
                compact.imageBaseBits(),compact.frameRspBits(),compact.volatileBits(),compact.nonvolatileBits());
        GovernmentPreprefix159Api.Entry prelude=GovernmentPrelude160.execute(after,memory,calls);
        GovernmentJoined159Api.Result joined=GovernmentJoined159.execute(
                prelude,memory,calls,lookupCalls,prefixCalls,boundary,calls,tailBudget);
        return new GovernmentMiddle166Api.Result(compact,prelude,joined);
    }
}
