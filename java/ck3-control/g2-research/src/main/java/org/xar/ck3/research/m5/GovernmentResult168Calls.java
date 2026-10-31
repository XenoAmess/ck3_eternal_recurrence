package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentResult168Api.Instance;
import org.xar.ck3.research.m5.GovernmentResult168Api.WorkBudget;

/**
 * Adapter for the specific call site 0x2D0B508 targeting 0x16F40A0.
 * Intercepts the OpaqueCall, materializes the native CALL push, executes the target,
 * validates the return state, and returns the resulting VolatileBits to the caller.
 */
public final class GovernmentResult168Calls {

    private static final long TARGET_SITE = 0x2D0B508L;
    private static final long TARGET_ADDR = 0x16F40A0L;

    public static Calls bind(long imageBaseBits, Memory memory, Calls delegate, WorkBudget budget) {
        return new Adapter(imageBaseBits, memory, delegate, budget);
    }

    private static final class Adapter implements Calls {
        private final long imageBaseBits;
        private final Memory memory;
        private final Calls delegate;
        private final WorkBudget budget;

        Adapter(long imageBaseBits, Memory memory, Calls delegate, WorkBudget budget) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.delegate = delegate;
            this.budget = budget;
        }

        @Override
        public long readGsQword58() {
            return delegate.readGsQword58();
        }

        @Override
        public VolatileBits invoke(OpaqueCall call) {
            if (call.callSiteRva() == TARGET_SITE && call.targetRva() == TARGET_ADDR) {
                return handleTargetCall(call);
            }
            return delegate.invoke(call);
        }

        private VolatileBits handleTargetCall(OpaqueCall call) {
            // 1. Materialize the native CALL push.
            // OpaqueCall.rspBits is the RSP immediately before the CALL (P).
            // The return address is imageBase + site + 5 (length of CALL instruction).
            // The callee entry RSP (S) is P - 8.
            long p = call.rspBits();
            long returnAddr = imageBaseBits + TARGET_SITE + 5L;
            long s = p - 8L;
            memory.writeQword(s, returnAddr);

            // 2. Construct the Entry for the target.
            // The target expects the volatile and nonvolatile bits from the call site.
            Entry entry = new Entry(imageBaseBits, s, call.volatileBits(), call.nonvolatileBits());

            // 3. Execute the target.
            // The target implementation is independent but must be present.
            // We pass the same memory and the actual WorkBudget.
            NormalReturn result = GovernmentResult168.execute(Instance.RESULT_16F40A0, entry, memory, budget);

            // 4. Validate the return state.
            // The adapter assumes normal ABI preservation and same-stack continuation.
            // If the target does not return to the expected RIP and RSP, or fails to preserve
            // nonvolatile state, we throw UnsupportedOperationException.

            // Expected RIP is the instruction immediately after the CALL at the site.
            long expectedRip = imageBaseBits + TARGET_SITE + 5L;
            if (result.returnRipBits() != expectedRip) {
                throw new UnsupportedOperationException("Target returned unexpected RIP: " + Long.toHexString(result.returnRipBits()));
            }

            // Expected caller RSP is P (the RSP before the CALL).
            if (result.callerRspBits() != p) {
                throw new UnsupportedOperationException("Target returned unexpected caller RSP: " + Long.toHexString(result.callerRspBits()));
            }

            // Validate nonvolatile preservation.
            NonvolatileBits incoming = call.nonvolatileBits();
            NonvolatileBits restored = result.nonvolatileBits();
            if (incoming.rbxBits() != restored.rbxBits() ||
                incoming.rbpBits() != restored.rbpBits() ||
                incoming.rsiBits() != restored.rsiBits() ||
                incoming.rdiBits() != restored.rdiBits() ||
                incoming.r12Bits() != restored.r12Bits() ||
                incoming.r13Bits() != restored.r13Bits() ||
                incoming.r14Bits() != restored.r14Bits() ||
                incoming.r15Bits() != restored.r15Bits() ||
                !incoming.xmm6().equals(restored.xmm6())) {
                throw new UnsupportedOperationException("Target failed to preserve nonvolatile state.");
            }

            // 5. Return the complete produced VolatileBits.
            return result.volatileBits();
        }
    }
}
