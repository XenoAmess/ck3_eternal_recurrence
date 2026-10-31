package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Exact actual caller adapter for the DIRECT_RVA CALL at 0x34EF74E targeting 0x34F04D0.
 * This adapter constructs the child Entry for the target function, delegates the call,
 * and verifies the normal return contract.
 */
public final class LoadRowReferenceStorage34f04d0196Calls {

    private static final long CALL_SITE_RVA = 0x34EF74EL;
    private static final long TARGET_RVA = 0x34F04D0L;
    private static final long NEXT_RVA = 0x34EF753L;

    /**
     * Binds the adapter to the image base, memory, and delegate calls.
     */
    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls delegate) {
        return new Adapter(imageBaseBits, memory, delegate);
    }

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long imageBaseBits;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls delegate;

        Adapter(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls delegate) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.delegate = delegate;
        }

        @Override
        public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.callSiteRva() == CALL_SITE_RVA
                    && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == TARGET_RVA) {
                // Construct the child Entry for the target function 0x34F04D0.
                // The caller owns the return push, so the child's RSP is callerRSP - 8.
                long childRspBits = call.rspBits() - 8L;

                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                    imageBaseBits,
                    childRspBits,
                    call.volatileBits(),
                    call.nonvolatileBits()
                );

                // Delegate the execution of the target function via the new execute method.
                GovernmentCrtBoundary185Api.NormalReturn result = LoadRowReferenceStorage34f04d0196.execute(
                    childEntry,
                    memory,
                    delegate
                );

                // Verify normal return contract:
                // 1. Return RIP must be imageBase + NEXT_RVA
                if (result.returnRipBits() != imageBaseBits + NEXT_RVA) {
                    throw new IllegalStateException("Return RIP mismatch");
                }
                // 2. Caller RSP must be entryRSP + 8 (which equals original call.rspBits())
                if (result.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("Caller RSP mismatch");
                }
                // 3. Nonvolatile bits must be equal to the input nonvolatile bits
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("Nonvolatile bits changed unexpectedly");
                }

                // Return all volatile bits from the normal return.
                return result.volatileBits();
            }

            // For all other calls, delegate directly.
            return delegate.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            return delegate.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return delegate.readGsQword58();
        }
    }
}
