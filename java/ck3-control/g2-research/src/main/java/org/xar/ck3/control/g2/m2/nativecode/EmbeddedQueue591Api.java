package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import java.util.Objects;

/**
 * Pure API contract for the complete held 103-byte function at RVA 0x3727EC0.
 * Defines the exact call frames and opaque interaction model for the two direct calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class EmbeddedQueue591Api {
    private EmbeddedQueue591Api() { }

    /**
     * Nested public Memory extends FullCopy437Api.Memory and adds only compareExchangeDword.
     * Its atomic result is the actual old DWORD; store desired only when old==expected.
     */
    public interface Memory extends FullCopy437Api.Memory {
        int compareExchangeDword(long addressBits, int expectedBits, int desiredBits);
    }

    /**
     * Exact call frame for one of the two direct call instructions in the 103-byte body.
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

            if (site == 0x3727ECFL) {
                // Direct call to 0x3727580
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x3727580L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 3727ECF");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3727ED4L) {
                    throw new IllegalArgumentException("Invalid return RIP for 3727ECF");
                }
            } else if (site == 0x3727F0DL) {
                // Direct call to 0x880340
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x880340L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 3727F0D");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3727F12L) {
                    throw new IllegalArgumentException("Invalid return RIP for 3727F0D");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(FullCopy437Api.CallResult actualResult) {
            if (actualResult.normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (actualResult.normalReturn().callerRspBits() != this.call().rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!actualResult.normalReturn().nonvolatileBits().equals(this.call().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Opaque interaction model for the two direct call instructions.
     * Each invoke must return a complete CallResult with actual post-state.
     * PAUSE has no represented V/N/DF/Memory effects and is not a call.
     */
    public interface Calls {
        /**
         * Handles a direct call to one of the two targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        FullCopy437Api.CallResult invoke(CallFrame frame);
    }
}