package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Pure API contract for the complete held 172-byte function at RVA 0x37297F0.
 * Defines the exact call frames and opaque interaction model for the two direct calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class Element172Fp636Api {
    private Element172Fp636Api() { }

    /**
     * Nested public Memory extends GovernmentCrtBoundary185Api.Memory.
     */
    public interface Memory extends GovernmentCrtBoundary185Api.Memory {
    }

    /**
     * Input wrapper carrying base 185 Entry, direction flag, and explicit MXCSR.
     */
    public record Input(GovernmentCrtBoundary185Api.Entry entry, boolean directionFlagSet, QueueFp604Api.Mxcsr mxcsr) {
        public Input {
            Objects.requireNonNull(entry);
            Objects.requireNonNull(mxcsr);
        }
    }

    /**
     * Exact call frame for one of the two direct call instructions in the 172-byte body.
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

            if (site == 0x3729846L) {
                // Direct call to 0x8C70B0
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for 3729846");
                }
                if (target != 0x8C70B0L) {
                    throw new IllegalArgumentException("Invalid target for 3729846");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for 3729846");
                }
                if (returnRipBits != imageBase + 0x372984BL) {
                    throw new IllegalArgumentException("Invalid return RIP for 3729846");
                }
            } else if (site == 0x3729877L) {
                // Direct call to 0xADD0D0
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for 3729877");
                }
                if (target != 0xADD0D0L) {
                    throw new IllegalArgumentException("Invalid target for 3729877");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for 3729877");
                }
                if (returnRipBits != imageBase + 0x372987CL) {
                    throw new IllegalArgumentException("Invalid return RIP for 3729877");
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
            FullCopy437Api.CallResult base = actual.base();
            if (base.normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (base.normalReturn().callerRspBits() != this.call().rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!base.normalReturn().nonvolatileBits().equals(this.call().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Opaque interaction model for the two direct call instructions.
     * Each invoke must return a complete Outcome with actual post-state.
     */
    public interface Calls {
        /**
         * Handles a direct call to one of the two targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits, DF, and MXCSR.
         */
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}