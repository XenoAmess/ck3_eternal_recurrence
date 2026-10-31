package org.xar.ck3.research.m5;

/** Owner implementation after two model source failures; existing region algorithms are reused. */
public final class GovernmentJoined159 {
    private GovernmentJoined159() { }
    public static GovernmentPrimarySuffix155Api.Entry suffixEntry(GovernmentPreprefix159Api.Join join) {
        if (join.nextRva() != 0x30a3eb3L) {
            throw new UnsupportedOperationException("unsupported continuation nextRva: "
                    + Long.toHexString(join.nextRva()));
        }
        GovernmentPrimaryTail155Api.NonvolatileBits n=join.nonvolatileBits();
        return new GovernmentPrimarySuffix155Api.Entry(join.imageBaseBits(),n.rdiBits(),
                (int)n.r12Bits(),n.rsiBits(),n.r15Bits(),n.rbpBits(),join.frameRspBits(),
                n.r13Bits(),n.r14Bits(),n.xmm6());
    }
    public static GovernmentJoined159Api.Result execute(GovernmentPreprefix159Api.Entry entry,
            GovernmentPrimarySuffix155Api.Memory memory, GovernmentPrimaryTail155Api.Calls preprefixCalls,
            InternedLookup155Api.Calls lookupCalls, GovernmentCaller153Api.Calls prefixCalls,
            GovernmentPrimarySuffix155Api.VolatileBoundary boundary,
            GovernmentPrimaryTail155Api.Calls tailCalls, GovernmentPrimaryTail155Api.LoopBudget budget) {
        GovernmentPreprefix159Api.Join joined=GovernmentPreprefix159.execute(entry,memory,preprefixCalls);
        GovernmentPrimarySuffix155Api.Result result=GovernmentPrimarySuffix155.execute(
                suffixEntry(joined),memory,lookupCalls,prefixCalls,boundary,tailCalls,budget);
        return new GovernmentJoined159Api.Result(joined,result);
    }
}
