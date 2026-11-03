package org.xar.ck3.research.m3.f780fp264;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Source-scoped carrier for MXCSR knowledge in the F780 context.
 * Defines the exact call frames and opaque interaction model for the two direct calls
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class F780Fp264Api {
    private F780Fp264Api() { }

    /**
     * Exact call frame for one of the two direct call instructions in the 63-byte body.
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

            if (site == 0x424F797L) {
                // Direct call to 0x4247FFC (5 bytes)
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4247FFCL) {
                    throw new IllegalArgumentException("Invalid call site 424F797");
                }
                // Return RIP = imageBase + 0x424F79C
                if (imageBase + site + 5L != imageBase + 0x424F79CL) {
                    throw new IllegalArgumentException("Invalid return RIP for 424F797");
                }
            } else if (site == 0x424F7AFL) {
                // Direct call to 0x4248050 (5 bytes)
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4248050L) {
                    throw new IllegalArgumentException("Invalid call site 424F7AF");
                }
                // Return RIP = imageBase + 0x424F7B4
                if (imageBase + site + 5L != imageBase + 0x424F7B4L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424F7AF");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        public long returnRipBits() {
            long site = original.callSiteRva();
            long imageBase = childEntry.imageBaseBits();
            if (site == 0x424F797L) return imageBase + 0x424F79CL;
            if (site == 0x424F7AFL) return imageBase + 0x424F7B4L;
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
     * Opaque interaction model for the two direct call instructions.
     * Each invoke must return a complete Outcome with actual post-state.
     */
    public interface Calls {
        /**
         * Handles a direct call to one of the two targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}