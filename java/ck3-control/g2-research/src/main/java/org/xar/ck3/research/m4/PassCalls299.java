package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Thin adapter for the normal286 represented scope.
 * Binds the actual PassFullState299 producer to the supplied fallback Calls.
 * Only DIRECT_RVA target 0x1A82330 at sites 0x1A81A39, 0x1A81A65, 0x1A81A82 are handled locally.
 * All other invokes and tails forward to the original fallback object.
 */
public final class PassCalls299 {
    private PassCalls299() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long image,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new Adapter(image, memory, fallback, budget);
    }

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls fallback;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;

        Adapter(long image, GovernmentCrtBoundary185Api.Memory memory,
                GovernmentCrtBoundary185Api.Calls fallback,
                GovernmentCrtBoundary185Api.LoopBudget budget) {
            this.image = image;
            this.memory = memory;
            this.fallback = fallback;
            this.budget = budget;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            // Only handle the three known normal callsites for target 0x1A82330
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x1A82330L
                    && (call.callSiteRva() == 0x1A81A39L
                        || call.callSiteRva() == 0x1A81A65L
                        || call.callSiteRva() == 0x1A81A82L)) {
                // Construct child Entry: imageBase, rspBits-8 (callee entry after push), V, N
                long childRsp = call.rspBits() - 8L;
                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                        image,
                        childRsp,
                        call.volatileBits(),
                        call.nonvolatileBits());

                // Execute the producer
                GovernmentCrtBoundary185Api.NormalReturn childReturn =
                        PassFullState299.execute(childEntry, memory, fallback, budget);

                // Verify RIP: image + site + 5
                long expectedRip = image + call.callSiteRva() + 5L;
                if (childReturn.returnRipBits() != expectedRip) {
                    throw new UnsupportedOperationException("RIP mismatch: expected " + Long.toHexString(expectedRip)
                            + " got " + Long.toHexString(childReturn.returnRipBits()));
                }

                // Verify SP: call.rspBits
                if (childReturn.callerRspBits() != call.rspBits()) {
                    throw new UnsupportedOperationException("SP mismatch: expected " + Long.toHexString(call.rspBits())
                            + " got " + Long.toHexString(childReturn.callerRspBits()));
                }

                // Verify N value equals immutable offered call.N
                GovernmentPrimaryTail155Api.NonvolatileBits offeredN = call.nonvolatileBits();
                GovernmentPrimaryTail155Api.NonvolatileBits returnedN = childReturn.nonvolatileBits();
                if (returnedN.rbxBits() != offeredN.rbxBits()
                        || returnedN.rbpBits() != offeredN.rbpBits()
                        || returnedN.rsiBits() != offeredN.rsiBits()
                        || returnedN.rdiBits() != offeredN.rdiBits()
                        || returnedN.r12Bits() != offeredN.r12Bits()
                        || returnedN.r13Bits() != offeredN.r13Bits()
                        || returnedN.r14Bits() != offeredN.r14Bits()
                        || returnedN.r15Bits() != offeredN.r15Bits()
                        || returnedN.xmm6().lowBits() != offeredN.xmm6().lowBits()
                        || returnedN.xmm6().highBits() != offeredN.xmm6().highBits()) {
                    throw new UnsupportedOperationException("NonvolatileBits mismatch");
                }

                // Return full V from child
                return childReturn.volatileBits();
            }

            // All other invokes forward to fallback
            return fallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            // No matching tail site in 809; forward to fallback
            return fallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            // Forward unchanged
            return fallback.readGsQword58();
        }
    }
}
