package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Pure API contract for the complete held 322-byte function at RVA 0x37282B0.
 * Defines the exact call frames and opaque interaction model for the six direct/indirect calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class EmbeddedElements578Api {
    private EmbeddedElements578Api() { }

    /**
     * Exact call frame for one of the six call instructions in the 322-byte body.
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

            if (site == 0x37282E1L) {
                // Direct call to 0x889780
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x889780L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 37282E1");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x37282E6L) {
                    throw new IllegalArgumentException("Invalid return RIP for 37282E1");
                }
            } else if (site == 0x3728316L) {
                // Indirect call via R9 (CALL R9)
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 3728316");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for 3728316");
                }
                // Target is represented in current volatile bits (R9)
                if (target != call.volatileBits().r9Bits()) {
                    throw new IllegalArgumentException("Target mismatch for 3728316");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3728319L) {
                    throw new IllegalArgumentException("Invalid return RIP for 3728316");
                }
            } else if (site == 0x372833BL) {
                // Direct call to 0x37295B0
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x37295B0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 372833B");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3728340L) {
                    throw new IllegalArgumentException("Invalid return RIP for 372833B");
                }
            } else if (site == 0x372836CL) {
                // Direct call to 0xDBDB80
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0xDBDB80L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 372836C");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3728371L) {
                    throw new IllegalArgumentException("Invalid return RIP for 372836C");
                }
            } else if (site == 0x3728398L) {
                // Indirect call via memory at RAX (CALL [RAX])
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 3728398");
                }
                if (instructionLength != 2) {
                    throw new IllegalArgumentException("Invalid instruction length for 3728398");
                }
                // Target is read from memory at RAX; cannot be recomputed by pure API.
                // The producer must carry the actual targetBits.
                if (returnRipBits != childEntry.imageBaseBits() + 0x372839AL) {
                    throw new IllegalArgumentException("Invalid return RIP for 3728398");
                }
            } else if (site == 0x37283B6L) {
                // Direct call to 0x37297F0
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x37297F0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 37283B6");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x37283BBL) {
                    throw new IllegalArgumentException("Invalid return RIP for 37283B6");
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