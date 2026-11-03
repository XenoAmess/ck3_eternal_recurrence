package org.xar.ck3.research.m3.fa90fp267;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Source-scoped carrier for MXCSR knowledge in the FA90 context.
 * Defines the exact call frames and opaque interaction model for the three direct calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class Fa90Fp267Api {
    private Fa90Fp267Api() { }

    /**
     * Exact call frame for one of the three legal direct call instructions in the 103-byte body.
     * Validates the call site, kind, target, return RIP, and child entry consistency.
     */
    public record CallFrame(
        GovernmentCrtBoundary185Api.Call original,
        GovernmentCrtBoundary185Api.Entry childEntry,
        boolean directionFlagSet,
        QueueFp604Api.Mxcsr preMxcsr
    ) {
        public CallFrame {
            Objects.requireNonNull(original);
            Objects.requireNonNull(childEntry);
            Objects.requireNonNull(preMxcsr);

            // Child RSP must be exactly 8 bytes below call RSP (return address push)
            if (childEntry.rspBits() != original.rspBits() - 8) {
                throw new IllegalArgumentException("Child RSP mismatch");
            }

            // Child volatile and nonvolatile bits must match the call's pre-state
            if (!childEntry.volatileBits().equals(original.volatileBits())) {
                throw new IllegalArgumentException("Child V mismatch");
            }
            if (!childEntry.nonvolatileBits().equals(original.nonvolatileBits())) {
                throw new IllegalArgumentException("Child N mismatch");
            }

            // Validate exact call site, kind, target, and instruction length
            long site = original.callSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = original.kind();
            long target = original.targetBits();
            long imageBase = childEntry.imageBaseBits();

            if (site == 0x424FAACL) {
                // Direct call to 0x42568FC
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x42568FCL) {
                    throw new IllegalArgumentException("Invalid call site 424FAAC");
                }
                // Return RIP = imageBase + 0x424FAB1
                if (imageBase + 0x424FAB1L != imageBase + site + 5L) {
                     throw new IllegalArgumentException("Invalid return RIP calculation for 424FAAC");
                }
            } else if (site == 0x424FAD3L) {
                // Direct call to 0x42566FC
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x42566FCL) {
                    throw new IllegalArgumentException("Invalid call site 424FAD3");
                }
                // Return RIP = imageBase + 0x424FAD8
                if (imageBase + 0x424FAD8L != imageBase + site + 5L) {
                     throw new IllegalArgumentException("Invalid return RIP calculation for 424FAD3");
                }
            } else if (site == 0x424FAE7L) {
                // Direct call to 0x4256670
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4256670L) {
                    throw new IllegalArgumentException("Invalid call site 424FAE7");
                }
                // Return RIP = imageBase + 0x424FAEC
                if (imageBase + 0x424FAECL != imageBase + site + 5L) {
                     throw new IllegalArgumentException("Invalid return RIP calculation for 424FAE7");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        public long returnRipBits() {
            long site = original.callSiteRva();
            long imageBase = childEntry.imageBaseBits();
            if (site == 0x424FAACL) return imageBase + 0x424FAB1L;
            if (site == 0x424FAD3L) return imageBase + 0x424FAD8L;
            if (site == 0x424FAE7L) return imageBase + 0x424FAECL;
            throw new IllegalStateException("Unreachable");
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(QueueFp604Api.Normal normal) {
            Objects.requireNonNull(normal);
            if (normal.base().normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (normal.base().normalReturn().callerRspBits() != this.original.rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!normal.base().normalReturn().nonvolatileBits().equals(this.original.nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Opaque interaction model for the three direct call instructions.
     * Each invoke must return a complete Outcome with actual post-state.
     */
    public interface Calls {
        /**
         * Handles a direct call to one of the three targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}