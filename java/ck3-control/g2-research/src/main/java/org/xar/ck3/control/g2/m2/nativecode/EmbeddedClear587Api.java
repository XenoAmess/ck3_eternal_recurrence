package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;
import java.util.Objects;

/** Pure typed API for the embedded clear segment. No producer body, test, or oracle. */
public final class EmbeddedClear587Api {
    private EmbeddedClear587Api() { }

    /**
     * Represents the single actual 2-byte virtual call at source offset 0x8897A8.
     * The target is carried fresh absolute; no fabricated RAX equality or Memory reads are implied.
     * Child entry state must match the call site's pre-call state adjusted for the push.
     */
    public record CallFrame(
        GovernmentCrtBoundary185Api.Call call,
        GovernmentCrtBoundary185Api.Entry childEntry,
        boolean directionFlagSet,
        int instructionLength,
        long returnRipBits
    ) {
        public CallFrame {
            Objects.requireNonNull(call);
            Objects.requireNonNull(childEntry);

            // Actual source 8897A8 is an INDIRECT_ABSOLUTE call of length 2.
            if (call.kind() != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                throw new IllegalArgumentException("Call kind must be INDIRECT_ABSOLUTE");
            }
            if (instructionLength != 2) {
                throw new IllegalArgumentException("Instruction length must be 2");
            }
            if (call.callSiteRva() != 0x8897A8L) {
                throw new IllegalArgumentException("Invalid call site RVA");
            }

            // Return RIP is the next instruction offset (8897AA) relocated by childEntry.imageBaseBits.
            // 8897AA is the full RVA in the original module.
            if (returnRipBits != childEntry.imageBaseBits() + 0x8897AAL) {
                throw new IllegalArgumentException("Invalid return RIP relocation");
            }

            // Child SP == call.rspBits - 8 (push of return address)
            if (childEntry.rspBits() != call.rspBits() - 8) {
                throw new IllegalArgumentException("Child RSP mismatch");
            }

            // Child V/N == call V/N
            if (!childEntry.volatileBits().equals(call.volatileBits())) {
                throw new IllegalArgumentException("Child Volatile mismatch");
            }
            if (!childEntry.nonvolatileBits().equals(call.nonvolatileBits())) {
                throw new IllegalArgumentException("Child Nonvolatile mismatch");
            }
        }

        /**
         * Pure guard for the normal return of the virtual call.
         * Checks that the return RIP and Caller RSP match the frame's expectations.
         * Checks that the restored nonvolatile bits match the call's nonvolatile bits.
         * No volatile/DF repair or equality default is performed.
         */
        public void checkNormalReturn(FullCopy437Api.CallResult result) {
            Objects.requireNonNull(result);
            Objects.requireNonNull(result.normalReturn());

            // NR.returnRipBits == frame.returnRipBits
            if (result.normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }

            // NR.callerRspBits == call.rspBits
            if (result.normalReturn().callerRspBits() != this.call().rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }

            // NR.nonvolatileBits == call.nonvolatileBits
            if (!result.normalReturn().nonvolatileBits().equals(this.call().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    @FunctionalInterface
    public interface Calls {
        FullCopy437Api.CallResult invoke(CallFrame frame);
    }
}