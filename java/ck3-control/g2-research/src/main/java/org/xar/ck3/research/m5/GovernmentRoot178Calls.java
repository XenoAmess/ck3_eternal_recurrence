package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentRoot178Api;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class GovernmentRoot178Calls {
    private GovernmentRoot178Calls() { }

    public static GovernmentLookupHelper176Api.Calls bind(long imageBase,
            GovernmentRoot178Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        return new RootBridge(imageBase, memory, fallback);
    }

    private static final class RootBridge implements GovernmentLookupHelper176Api.Calls {
        private final long imageBase;
        private final GovernmentRoot178Api.Memory memory;
        private final GovernmentPrimaryTail155Api.Calls fallback;

        RootBridge(long imageBase, GovernmentRoot178Api.Memory memory, GovernmentPrimaryTail155Api.Calls fallback) {
            this.imageBase = imageBase;
            this.memory = memory;
            this.fallback = fallback;
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

            if (target == 0x3f5c090L && site == 0x3f5f97bL) {
                return handleRootCall(call);
            }
            return fallback.invoke(call);
        }

        private GovernmentPrimaryTail155Api.VolatileBits handleRootCall(GovernmentPrimaryTail155Api.OpaqueCall call) {
            long site = call.callSiteRva();
            long rsp = call.rspBits();
            long calleeRsp = rsp - 8L;
            long returnRip = imageBase + site + 5L;

            // The actual176 caller core already materialized this CALL return slot.
            // Reuse that same callee entry; do not duplicate its architectural write.

            // Construct Root178 entry with original bits
            GovernmentRoot178Api.Entry entry = new GovernmentRoot178Api.Entry(
                    imageBase,
                    calleeRsp,
                    call.volatileBits(),
                    call.nonvolatileBits()
            );

            // Create root calls port delegating to original fallback
            GovernmentRoot178Api.Calls rootCalls = new RootCalls(fallback);

            // Execute root core
            GovernmentRoot178Api.NormalReturn result = GovernmentRoot178.execute(
                    entry, memory, rootCalls
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

    private static final class RootCalls implements GovernmentRoot178Api.Calls {
        private final GovernmentPrimaryTail155Api.Calls fallback;

        RootCalls(GovernmentPrimaryTail155Api.Calls fallback) {
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
