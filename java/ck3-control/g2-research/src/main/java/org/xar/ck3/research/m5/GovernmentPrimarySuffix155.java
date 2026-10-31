package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentTierLookupKey150.LookupKey32;

/** Whole owner assembly after two rejected model replies; delegates all region algorithms. */
public final class GovernmentPrimarySuffix155 {
    private GovernmentPrimarySuffix155() { }

    private static final class TrackingCalls implements GovernmentCaller153Api.Calls {
        private final GovernmentPrimarySuffix155Api.Entry entry;
        private final GovernmentPrimarySuffix155Api.Memory memory;
        private final InternedLookup155Api.Calls lookup;
        private final GovernmentCaller153Api.Calls outer;
        private GovernmentCaller153Api.Calls bound;
        private long r14;
        private TrackingCalls(GovernmentPrimarySuffix155Api.Entry entry,
                GovernmentPrimarySuffix155Api.Memory memory, InternedLookup155Api.Calls lookup,
                GovernmentCaller153Api.Calls outer) {
            this.entry = entry; this.memory = memory; this.lookup = lookup; this.outer = outer;
            r14 = entry.incomingR14Bits();
        }
        private GovernmentCaller153Api.Calls delegate() {
            if (bound == null) bound = InternedLookup155Binder.bind(entry.imageBaseBits(), memory, lookup, outer);
            return bound;
        }
        @Override public long call3F4F8E0(LookupKey32 key) {
            long actual = delegate().call3F4F8E0(key);
            r14 = actual;
            return actual;
        }
        @Override public long readGsQword58() { return delegate().readGsQword58(); }
        @Override public long call3F5F970(int ecxBits) { return delegate().call3F5F970(ecxBits); }
        @Override public void callABBAF0(GovernmentCaller153Api.DiagnosticCall call) {
            delegate().callABBAF0(call);
        }
    }

    public static GovernmentPrimarySuffix155Api.Result execute(
            GovernmentPrimarySuffix155Api.Entry entry, GovernmentPrimarySuffix155Api.Memory memory,
            InternedLookup155Api.Calls lookupCalls, GovernmentCaller153Api.Calls outerPrefixCalls,
            GovernmentPrimarySuffix155Api.VolatileBoundary volatileBoundary,
            GovernmentPrimaryTail155Api.Calls tailCalls, GovernmentPrimaryTail155Api.LoopBudget budget) {
        TrackingCalls calls = new TrackingCalls(entry, memory, lookupCalls, outerPrefixCalls);
        GovernmentCaller153Api.Outcome outcome = GovernmentLocalCaller153.execute(
                new GovernmentCaller153Api.Entry(entry.imageBaseBits(), entry.governmentBits(),
                        entry.savedTlsOffsetDwordBits(), entry.savedRsiBits(), (int) entry.savedR15Bits()),
                memory, calls);
        GovernmentPrimarySuffix155Api.VolatileObservation observation =
                volatileBoundary.afterPrefix(entry, outcome, calls.r14);
        if (observation instanceof GovernmentPrimarySuffix155Api.UnavailableVolatile unavailable) {
            throw new GovernmentPrimarySuffix155Api.BoundaryUnavailableException(unavailable.reason());
        }
        if (!(observation instanceof GovernmentPrimarySuffix155Api.AvailableVolatile available)) {
            throw new GovernmentPrimarySuffix155Api.BoundaryUnavailableException("post-prefix volatile state absent");
        }
        GovernmentPrimaryTail155Api.NormalReturn returned = GovernmentPrimaryTail155.execute(
                new GovernmentPrimaryTail155Api.Entry(entry.imageBaseBits(), entry.governmentBits(),
                        entry.savedTlsOffsetDwordBits(), entry.savedRsiBits(), entry.savedR15Bits(),
                        entry.frameRbpBits(), entry.frameRspBits(), entry.incomingR13Bits(), calls.r14,
                        entry.incomingXmm6(), available.bits()),
                memory, tailCalls, budget);
        return new GovernmentPrimarySuffix155Api.Result(outcome, returned);
    }
}
