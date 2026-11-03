package org.xar.ck3.research.m3.f800fp265;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Source-scoped carrier for MXCSR knowledge in the F800 context.
 * Defines the exact call frames and opaque interaction model for the three direct calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class F800Fp265Api {
    private F800Fp265Api() { }

    /**
     * Exact call frame for one of the three legal direct call instructions in the 69-byte body.
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

            if (site == 0x424F817L) {
                // Direct call to 0x4247FFC
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4247FFCL) {
                    throw new IllegalArgumentException("Invalid call site 424F817");
                }
                // Return RIP = imageBase + 0x424F81C
                if (imageBase + 0x424F81CL != imageBase + site + 5L) {
                     throw new IllegalArgumentException("Invalid return RIP calculation for 424F817");
                }
            } else if (site == 0x424F82DL) {
                // Direct call to 0x424FA90
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424FA90L) {
                    throw new IllegalArgumentException("Invalid call site 424F82D");
                }
                // Return RIP = imageBase + 0x424F832
                if (imageBase + 0x424F832L != imageBase + site + 5L) {
                     throw new IllegalArgumentException("Invalid return RIP calculation for 424F82D");
                }
            } else if (site == 0x424F835L) {
                // Direct call to 0x4248050
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4248050L) {
                    throw new IllegalArgumentException("Invalid call site 424F835");
                }
                // Return RIP = imageBase + 0x424F83A
                if (imageBase + 0x424F83AL != imageBase + site + 5L) {
                     throw new IllegalArgumentException("Invalid return RIP calculation for 424F835");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        public long returnRipBits() {
            long site = original.callSiteRva();
            long imageBase = childEntry.imageBaseBits();
            if (site == 0x424F817L) return imageBase + 0x424F81CL;
            if (site == 0x424F82DL) return imageBase + 0x424F832L;
            if (site == 0x424F835L) return imageBase + 0x424F83AL;
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