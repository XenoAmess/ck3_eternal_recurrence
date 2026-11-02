package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Thin binder between actualBridge293 and matureMerge297. This is a factory for the
 * existing 185 Calls interface, not an implementation of either algorithm. Only the
 * exact DIRECT_RVA normal site 0x1A8335D and tail site 0x1A833A2 (both targeting
 * 0x1A81AB0) route to MergeRangeFullState297.execute. Every unmatched invoke/tail
 * forwards the original same Call/Tail object once to the original fallback.
 */
public final class BridgeMergeCalls298 {
    private BridgeMergeCalls298() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback,
            GovernmentCrtBoundary185Api.LoopBudget budget) {

        final long normalSite = 0x1A8335DL;
        final long tailSite = 0x1A833A2L;
        final long target = 0x1A81AB0L;
        final long retRip = imageBaseBits + 0x1A83362L;

        return new GovernmentCrtBoundary185Api.Calls() {

            @Override
            public org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                // Normal invoke: ONLY exact DIRECT_RVA site 0x1A8335D / target 0x1A81AB0 executes the new target.
                if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && call.callSiteRva() == normalSite
                        && call.targetBits() == target) {
                    // BridgeFullState293 already wrote [call.rspBits()-8] = image + 0x1A83362, and Call.rspBits
                    // is PRECALLSP, so the actual target EntrySP is call.rspBits()-8 with the actual call V/N
                    // and bound image. Same Memory and budget; the target's unknown opaque ports go to the
                    // original fallback explicitly. No second push, no RET pre-read, no synthesized full state,
                    // no N-after-mutation/defaults, no replacement of the full Call with a scalar.
                    GovernmentCrtBoundary185Api.NormalReturn normal =
                        MergeRangeFullState297.execute(
                            new GovernmentCrtBoundary185Api.Entry(
                                imageBaseBits,
                                call.rspBits() - 8L,
                                call.volatileBits(),
                                call.nonvolatileBits()),
                            memory,
                            fallback,
                            budget);

                    // On actual NR require returnRipBits = image + 0x1A83362 AND callerRspBits = call.rspBits AND
                    // actual nonvolatileBits equal the offered immutable call.nonvolatileBits (record value equality).
                    // Mismatch throws UnsupportedOperationException; actual effects remain.
                    if (normal.returnRipBits() != retRip
                            || normal.callerRspBits() != call.rspBits()
                            || !normal.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new UnsupportedOperationException(
                            "normal return identity mismatch at DIRECT_RVA site 0x1A8335D");
                    }

                    // Return the full actual NR volatileBits only after the guard; no fake flags or native qualification.
                    return normal.volatileBits();
                }

                // Every unmatched invoke (wrong site/target/kind) forwards the original same Call object once to
                // the original fallback and returns the original full V/NR unchanged.
                return fallback.invoke(call);
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                // Tail: ONLY exact DIRECT_RVA jumpSite 0x1A833A2 / target 0x1A81AB0 routes to the mature target.
                if (transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && transfer.jumpSiteRva() == tailSite
                        && transfer.targetBits() == target) {
                    // Pass transfer.entry() UNCHANGED as the actual target entry, including its actual
                    // imageBaseBits/SP/all V/N. Same Memory/fallback/budget. Tail caller 293 has already executed
                    // its local epilogue and holds the actual target SP: NO second push, no RET pre-read, no
                    // image/SP rebinding, no extra NR normal guard here.
                    // Return the exact actual target NormalReturn object VERBATIM (it may itself come from opaque
                    // 776). Propagate actual exceptions unchanged. This does not implement unknown 776/COPY/RFLAGS/
                    // DF/EH/hardware.
                    return MergeRangeFullState297.execute(
                        transfer.entry(),
                        memory,
                        fallback,
                        budget);
                }

                // Unmatched tail forwards the original same Tail object once to the original fallback and returns
                // the original full V/NR unchanged.
                return fallback.tail(transfer);
            }

            @Override
            public long readGsQword58() {
                // readGsQword58 forwards exactly. No Memory/loopbudget eligibility reads, no new qualifier/global
                // state/threads.
                return fallback.readGsQword58();
            }
        };
    }
}
