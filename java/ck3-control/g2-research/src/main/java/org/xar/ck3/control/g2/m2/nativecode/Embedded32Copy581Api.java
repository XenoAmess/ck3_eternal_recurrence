package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Pure API contract for the complete held 394-byte function at RVA 0x3727180.
 * Defines the exact call frames and opaque interaction model for the six direct/indirect calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class Embedded32Copy581Api {
    private Embedded32Copy581Api() { }

    /**
     * Exact call frame for one of the six call instructions in the 394-byte body.
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

            if (site == 0x37271BAL) {
                // Direct call to 0x889660
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x889660L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 37271BA");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x37271BFL) {
                    throw new IllegalArgumentException("Invalid return RIP for 37271BA");
                }
            } else if (site == 0x37271EE) {
                // Indirect call via memory at RAX+8 (CALL [RAX+8])
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 37271EE");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for 37271EE");
                }
                // Target is read from memory; cannot be recomputed by pure API.
                // The producer must carry the actual targetBits.
                if (returnRipBits != childEntry.imageBaseBits() + 0x37271F1L) {
                    throw new IllegalArgumentException("Invalid return RIP for 37271EE");
                }
            } else if (site == 0x3727249) {
                // Direct call to 0x8874D0
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x8874D0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 3727249");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x372724EL) {
                    throw new IllegalArgumentException("Invalid return RIP for 3727249");
                }
            } else if (site == 0x372727B) {
                // Indirect call via memory at RAX (CALL [RAX])
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 372727B");
                }
                if (instructionLength != 2) {
                    throw new IllegalArgumentException("Invalid instruction length for 372727B");
                }
                // Target is read from memory; cannot be recomputed by pure API.
                // The producer must carry the actual targetBits.
                if (returnRipBits != childEntry.imageBaseBits() + 0x372727DL) {
                    throw new IllegalArgumentException("Invalid return RIP for 372727B");
                }
            } else if (site == 0x37272F0) {
                // Direct call to 0x37282B0
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x37282B0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 37272F0");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x37272F5L) {
                    throw new IllegalArgumentException("Invalid return RIP for 37272F0");
                }
            } else if (site == 0x37272F8) {
                // Direct call to 0x3727EC0
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x3727EC0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 37272F8");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x37272FDL) {
                    throw new IllegalArgumentException("Invalid return RIP for 37272F8");
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
     * Opaque interaction model for the six call instructions.
     * Each invoke must return a complete CallResult with actual post-state.
     */
    public interface Calls {
        /**
         * Handles a direct or indirect call to one of the six targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        FullCopy437Api.CallResult invoke(CallFrame frame);
    }
}