package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Pure API contract for the complete held 227-byte function at RVA 0x880340.
 * Defines the exact call frames and opaque interaction model for the three direct/indirect calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class QueueAppend597Api {
    private QueueAppend597Api() { }

    /**
     * Nested public Memory extends FullCopy437Api.Memory unchanged.
     */
    public interface Memory extends FullCopy437Api.Memory {
    }

    /**
     * Exact call frame for one of the three legal call instructions in the 227-byte body.
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
            long imageBase = childEntry.imageBaseBits();

            if (site == 0x88039FL) {
                // Indirect call at 88039F: FF 50 08 (3 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 88039F");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for 88039F");
                }
                // Return RIP = imageBase + 0x8803A2
                if (returnRipBits != imageBase + 0x8803A2L) {
                    throw new IllegalArgumentException("Invalid return RIP for 88039F");
                }
            } else if (site == 0x8803C5L) {
                // Direct call at 8803C5: E8 96 64 9A 03 (5 bytes), target 0x4226860
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for 8803C5");
                }
                if (target != 0x4226860L) {
                    throw new IllegalArgumentException("Invalid direct target for 8803C5");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for 8803C5");
                }
                // Return RIP = imageBase + 0x8803CA
                if (returnRipBits != imageBase + 0x8803CAL) {
                    throw new IllegalArgumentException("Invalid return RIP for 8803C5");
                }
            } else if (site == 0x8803DAL) {
                // Indirect call at 8803DA: FF 50 10 (3 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 8803DA");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for 8803DA");
                }
                // Return RIP = imageBase + 0x8803DD
                if (returnRipBits != imageBase + 0x8803DD) {
                    throw new IllegalArgumentException("Invalid return RIP for 8803DA");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(FullCopy437Api.CallResult actual) {
            if (actual.normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (actual.normalReturn().callerRspBits() != this.call().rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!actual.normalReturn().nonvolatileBits().equals(this.call().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Opaque interaction model for the three call instructions.
     * Each invoke must return a complete CallResult with actual post-state.
     */
    public interface Calls {
        /**
         * Handles a call to one of the three targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        FullCopy437Api.CallResult invoke(CallFrame frame);
    }
}