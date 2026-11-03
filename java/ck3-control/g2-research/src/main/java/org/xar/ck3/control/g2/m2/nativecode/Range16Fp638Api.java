package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;

/**
 * Pure API contract for the complete held 424-byte function at RVA 0x8C70B0.
 * Defines the exact call frames and opaque interaction model for the three direct/indirect calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class Range16Fp638Api {
    private Range16Fp638Api() { }

    /**
     * Nested public Memory extends QueueAppend597Api.Memory unchanged.
     */
    public interface Memory extends QueueAppend597Api.Memory {
    }

    /**
     * Exact call frame for one of the three legal call instructions in the 424-byte body.
     * Validates the call site, kind, target, return RIP, and child entry consistency.
     */
    public record CallFrame(
        GovernmentCrtBoundary185Api.Call call,
        GovernmentCrtBoundary185Api.Entry childEntry,
        boolean directionFlagSet,
        QueueFp604Api.Mxcsr preMxcsr,
        int instructionLength,
        long returnRipBits
    ) {
        public CallFrame {
            Objects.requireNonNull(call);
            Objects.requireNonNull(childEntry);
            Objects.requireNonNull(preMxcsr);

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

            if (site == 0x8C7131L) {
                // Indirect call at 8C7131: FF 50 08 (3 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 8C7131");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for 8C7131");
                }
                // Return RIP = imageBase + 0x8C7134
                if (returnRipBits != imageBase + 0x8C7134L) {
                    throw new IllegalArgumentException("Invalid return RIP for 8C7131");
                }
            } else if (site == 0x8C71D7L) {
                // Indirect call at 8C71D7: FF 50 10 (3 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 8C71D7");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for 8C71D7");
                }
                // Return RIP = imageBase + 0x8C71DA
                if (returnRipBits != imageBase + 0x8C71DAL) {
                    throw new IllegalArgumentException("Invalid return RIP for 8C71D7");
                }
            } else if (site == 0x8C723FL) {
                // Direct call at 8C723F: E8 0C 13 03 00 (5 bytes), target 0x8F8550
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for 8C723F");
                }
                if (target != 0x8F8550L) {
                    throw new IllegalArgumentException("Invalid direct target for 8C723F");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for 8C723F");
                }
                // Return RIP = imageBase + 0x8C7244
                if (returnRipBits != imageBase + 0x8C7244L) {
                    throw new IllegalArgumentException("Invalid return RIP for 8C723F");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(QueueFp604Api.Normal actual) {
            Objects.requireNonNull(actual);
            GovernmentCrtBoundary185Api.NormalReturn nr = actual.base().normalReturn();
            if (nr.returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (nr.callerRspBits() != this.call().rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!nr.nonvolatileBits().equals(this.call().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Opaque interaction model for the three call instructions.
     * Each invoke must return a complete Outcome with actual post-state.
     */
    public interface Calls {
        /**
         * Handles a call to one of the three targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits, DF, and MXCSR.
         */
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}