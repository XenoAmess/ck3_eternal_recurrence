package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class GovernmentLookupHelper176Calls {
    private GovernmentLookupHelper176Calls() { }

    public static GovernmentNormalizeFull174Api.Calls bind(long imageBase,
            GovernmentLookupHelper176Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls fallback,
            GovernmentLookupHelper176Api.LoopBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(budget);
        return new NormalizerBridge(imageBase, memory, fallback, budget);
    }

    private static final class NormalizerBridge implements GovernmentNormalizeFull174Api.Calls {
        private final long imageBase;
        private final GovernmentLookupHelper176Api.Memory memory;
        private final GovernmentPrimaryTail155Api.Calls fallback;
        private final GovernmentLookupHelper176Api.LoopBudget budget;

        NormalizerBridge(long imageBase, GovernmentLookupHelper176Api.Memory memory,
                GovernmentPrimaryTail155Api.Calls fallback, GovernmentLookupHelper176Api.LoopBudget budget) {
            this.imageBase = imageBase;
            this.memory = memory;
            this.fallback = fallback;
            this.budget = budget;
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
            Objects.requireNonNull(call);
            long target = call.targetRva();
            long site = call.callSiteRva();
            if (target == 0x3f5f970L && (site == 0x30a2d73L || site == 0x30a2e59L)) {
                return handleHelperCall(call);
            }
            return fallback.invoke(call);
        }

        private GovernmentPrimaryTail155Api.VolatileBits handleHelperCall(GovernmentPrimaryTail155Api.OpaqueCall call) {
            long site = call.callSiteRva();
            long rsp = call.rspBits();
            long calleeRsp = rsp - 8L;
            long returnRip = imageBase + site + 5L;

            // Materialize outer return address in shared memory
            memory.writeQword(calleeRsp, returnRip);

            // Construct helper entry with original bits
            GovernmentLookupHelper176Api.Entry entry = new GovernmentLookupHelper176Api.Entry(
                    imageBase,
                    calleeRsp,
                    call.volatileBits(),
                    call.nonvolatileBits()
            );

            // Create helper calls port
            GovernmentLookupHelper176Api.Calls helperCalls = new HelperCalls(fallback);

            // Execute helper core
            GovernmentLookupHelper176Api.NormalReturn result = GovernmentLookupHelper176.execute(
                    entry, memory, helperCalls, budget
            );

            // Validate return RIP
            if (result.returnRipBits() != returnRip) {
                throw new IllegalStateException("Return RIP mismatch: expected " + Long.toHexString(returnRip) + " got " + Long.toHexString(result.returnRipBits()));
            }

            // Validate caller RSP
            if (result.callerRspBits() != rsp) {
                throw new IllegalStateException("Caller RSP mismatch: expected " + Long.toHexString(rsp) + " got " + Long.toHexString(result.callerRspBits()));
            }

            // Validate nonvolatile bits preservation
            GovernmentPrimaryTail155Api.NonvolatileBits originalNV = call.nonvolatileBits();
            GovernmentPrimaryTail155Api.NonvolatileBits resultNV = result.nonvolatileBits();
            if (!resultNV.equals(originalNV)) {
                throw new IllegalStateException("Nonvolatile bits mismatch");
            }

            return result.volatileBits();
        }
    }

    private static final class HelperCalls implements GovernmentLookupHelper176Api.Calls {
        private final GovernmentPrimaryTail155Api.Calls fallback;

        HelperCalls(GovernmentPrimaryTail155Api.Calls fallback) {
            this.fallback = fallback;
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
            return fallback.invoke(call);
        }
    }
}
