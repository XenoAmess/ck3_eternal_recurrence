package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Pure API contract for the complete held 251-byte function at RVA 0x260E040.
 * Defines the exact call frames and opaque interaction model for the two indirect calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class EmbeddedVector565Api {
    private EmbeddedVector565Api() { }

    /**
     * Exact call frame for one of the two indirect calls in the 251-byte body.
     * Validates the call site, kind, target, return RIP, and child entry consistency.
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

            // Child RSP must be exactly 8 bytes below call RSP (return address push)
            if (childEntry.rspBits() != call.rspBits() - 8) {
                throw new IllegalArgumentException("Child RSP mismatch");
            }

            // Child volatile and nonvolatile bits must match the call's pre-state
            if (!childEntry.volatileBits().equals(call.volatileBits())) {
                throw new IllegalArgumentException("Child V mismatch");
            }
            if (!childEntry.nonvolatileBits().equals(call.nonvolatileBits())) {
                throw new IllegalArgumentException("Child N mismatch");
            }

            // Validate exact call site, kind, target, and instruction length
            long site = call.callSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = call.kind();
            long target = call.targetBits();

            if (site == 0x260E098L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 260E098");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for 260E098");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x260E09BL) {
                    throw new IllegalArgumentException("Invalid return RIP for 260E098");
                }
            } else if (site == 0x260E0E1L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 260E0E1");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for 260E0E1");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x260E0E4L) {
                    throw new IllegalArgumentException("Invalid return RIP for 260E0E1");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(FullCopy437Api.CallResult result) {
            if (result.normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (result.normalReturn().callerRspBits() != this.call().rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!result.normalReturn().nonvolatileBits().equals(this.call().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Opaque interaction model for the two indirect calls.
     * Each invoke must return a complete CallResult with actual post-state.
     */
    public interface Calls {
        /**
         * Handles an indirect call to one of the two targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        FullCopy437Api.CallResult invoke(CallFrame frame);
    }
}