package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Pure API contract for the complete held 233-byte function at RVA 0x373ACF0.
 * Defines the exact call frames and opaque interaction model for the four direct calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class ContextConstructor543Api {
    private ContextConstructor543Api() { }

    /**
     * Exact call frame for one of the four direct calls in the 233-byte body.
     * Validates the call site, target, return RIP, and child entry consistency.
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

            if (site == 0x373AD20L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x8895D0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 373AD20");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x373AD25L) {
                    throw new IllegalArgumentException("Invalid return RIP for 373AD20");
                }
            } else if (site == 0x373ADA1L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x37282B0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 373ADA1");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x373ADA6L) {
                    throw new IllegalArgumentException("Invalid return RIP for 373ADA1");
                }
            } else if (site == 0x373ADAEL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x260E040L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 373ADAE");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x373ADB3L) {
                    throw new IllegalArgumentException("Invalid return RIP for 373ADAE");
                }
            } else if (site == 0x373ADBDL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x3727180L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 373ADBD");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x373ADC2L) {
                    throw new IllegalArgumentException("Invalid return RIP for 373ADBD");
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
     * Opaque interaction model for the four direct calls.
     * Each invoke must return a complete CallResult with actual post-state.
     */
    public interface Calls {
        /**
         * Handles a direct call to one of the four targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        FullCopy437Api.CallResult invoke(CallFrame frame);
    }
}