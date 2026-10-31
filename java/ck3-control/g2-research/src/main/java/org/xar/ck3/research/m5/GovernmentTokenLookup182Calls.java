package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Calls;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class GovernmentTokenLookup182Calls {
    private GovernmentTokenLookup182Calls() { }

    public static GovernmentNormalizeFull174Api.Calls bind(long imageBase,
            GovernmentTokenLookup182Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls fallback,
            GovernmentTokenLookup182Api.Pause pause,
            GovernmentTokenLookup182Api.LoopBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(pause);
        Objects.requireNonNull(budget);
        return new Bridge(imageBase, memory, fallback, pause, budget);
    }

    private static final class Bridge implements GovernmentNormalizeFull174Api.Calls {
        private final long imageBase;
        private final GovernmentTokenLookup182Api.Memory memory;
        private final GovernmentPrimaryTail155Api.Calls fallback;
        private final GovernmentTokenLookup182Api.Pause pause;
        private final GovernmentTokenLookup182Api.LoopBudget budget;

        Bridge(long imageBase, GovernmentTokenLookup182Api.Memory memory,
                GovernmentPrimaryTail155Api.Calls fallback,
                GovernmentTokenLookup182Api.Pause pause,
                GovernmentTokenLookup182Api.LoopBudget budget) {
            this.imageBase = imageBase;
            this.memory = memory;
            this.fallback = fallback;
            this.pause = pause;
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

            if (target == 0x3f4f8e0L && (site == 0x30a2d3eL || site == 0x30a2e24L)) {
                return handleTokenLookup(call);
            }
            return fallback.invoke(call);
        }

        private GovernmentPrimaryTail155Api.VolatileBits handleTokenLookup(GovernmentPrimaryTail155Api.OpaqueCall call) {
            long site = call.callSiteRva();
            long rsp = call.rspBits();
            long calleeRsp = rsp - 8L;
            long returnRip = imageBase + site + 5L;

            // Construct Entry for the token lookup core using the already materialized callee state.
            // No duplicate stack write is performed here.
            GovernmentTokenLookup182Api.Entry entry = new GovernmentTokenLookup182Api.Entry(
                    imageBase,
                    calleeRsp,
                    call.volatileBits(),
                    call.nonvolatileBits()
            );

            // Create a child Calls port that delegates to the original fallback,
            // preventing recursive interception of inner calls by this bridge.
            GovernmentTokenLookup182Api.Calls tokenCalls = new ChildCalls(fallback);

            // Execute the core. The core owns its internal lock/pause/budget interactions.
            GovernmentTokenLookup182Api.NormalReturn result = GovernmentTokenLookup182.execute(
                    entry,
                    memory,
                    tokenCalls,
                    pause,
                    budget
            );

            // Validate return RIP matches the expected post-CALL address.
            if (result.returnRipBits() != returnRip) {
                throw new IllegalStateException("Return RIP mismatch: expected " + Long.toHexString(returnRip) + " got " + Long.toHexString(result.returnRipBits()));
            }

            // Validate caller RSP matches the original pre-CALL RSP.
            if (result.callerRspBits() != rsp) {
                throw new IllegalStateException("Caller RSP mismatch: expected " + Long.toHexString(rsp) + " got " + Long.toHexString(result.callerRspBits()));
            }

            // Validate nonvolatile bits preservation.
            GovernmentPrimaryTail155Api.NonvolatileBits originalNV = call.nonvolatileBits();
            GovernmentPrimaryTail155Api.NonvolatileBits resultNV = result.nonvolatileBits();
            if (!resultNV.equals(originalNV)) {
                throw new IllegalStateException("Nonvolatile bits mismatch");
            }

            // Return the entire volatile bits unchanged from the core execution.
            return result.volatileBits();
        }
    }

    private static final class ChildCalls implements GovernmentTokenLookup182Api.Calls {
        private final GovernmentPrimaryTail155Api.Calls fallback;

        ChildCalls(GovernmentPrimaryTail155Api.Calls fallback) {
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
