package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;

/**
 * Source-scoped carrier for Indexed448 FP/DF knowledge in the queue/append context.
 * No FP implementation, no native proof, no old file rewrite.
 */
public final class Indexed448Fp628Api {
    private Indexed448Fp628Api() { }

    /**
     * Exact call frame for one of the legal call instructions in the 470B body.
     * Validates the call site, kind, target, return RIP, and child entry consistency.
     */
    public record CallFrame(
        GovernmentCrtBoundary185Api.Call original,
        GovernmentCrtBoundary185Api.Entry childEntry,
        boolean directionFlagSet,
        QueueFp604Api.Mxcsr preMxcsr
    ) {
        public CallFrame(GovernmentCrtBoundary185Api.Call original,
                         GovernmentCrtBoundary185Api.Entry childEntry,
                         boolean directionFlagSet, QueueFp604Api.Mxcsr preMxcsr) {
            this.original = original;
            this.childEntry = childEntry;
            this.directionFlagSet = directionFlagSet;
            this.preMxcsr = preMxcsr;
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

            if (site == 0x424E4EBL) {
                // Indirect call at 424E4EB: FF 15 ... (6 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424E4EB");
                }
                // Return RIP = imageBase + 0x424E4F1
                if (returnRipBits() != imageBase + 0x424E4F1L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424E4EB");
                }
            } else if (site == 0x424E4F9L) {
                // Indirect call at 424E4F9: FF 15 ... (6 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424E4F9");
                }
                // Return RIP = imageBase + 0x424E4FF
                if (returnRipBits() != imageBase + 0x424E4FFL) {
                    throw new IllegalArgumentException("Invalid return RIP for 424E4F9");
                }
            } else if (site == 0x424E514L) {
                // Direct call at 424E514: E8 ... (5 bytes), target 0x4246A60
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4246A60L) {
                    throw new IllegalArgumentException("Invalid direct target for 424E514");
                }
                // Return RIP = imageBase + 0x424E519
                if (returnRipBits() != imageBase + 0x424E519L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424E514");
                }
            } else if (site == 0x424E52AL) {
                // Direct call at 424E52A: E8 ... (5 bytes), target 0x4246A60
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4246A60L) {
                    throw new IllegalArgumentException("Invalid direct target for 424E52A");
                }
                // Return RIP = imageBase + 0x424E52F
                if (returnRipBits() != imageBase + 0x424E52FL) {
                    throw new IllegalArgumentException("Invalid return RIP for 424E52A");
                }
            } else if (site == 0x424E53BL) {
                // Indirect call at 424E53B: FF 15 ... (6 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424E53B");
                }
                // Return RIP = imageBase + 0x424E541
                if (returnRipBits() != imageBase + 0x424E541L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424E53B");
                }
            } else if (site == 0x424E574L) {
                // Indirect call at 424E574: FF 15 ... (6 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424E574");
                }
                // Return RIP = imageBase + 0x424E57A
                if (returnRipBits() != imageBase + 0x424E57AL) {
                    throw new IllegalArgumentException("Invalid return RIP for 424E574");
                }
            } else if (site == 0x424E5A0L) {
                // Indirect call at 424E5A0: FF 15 ... (6 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424E5A0");
                }
                // Return RIP = imageBase + 0x424E5A6
                if (returnRipBits() != imageBase + 0x424E5A6L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424E5A0");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        public long returnRipBits() {
            long site = original.callSiteRva();
            long imageBase = childEntry.imageBaseBits();
            if (site == 0x424E4EBL) return imageBase + 0x424E4F1L;
            if (site == 0x424E4F9L) return imageBase + 0x424E4FFL;
            if (site == 0x424E514L) return imageBase + 0x424E519L;
            if (site == 0x424E52AL) return imageBase + 0x424E52FL;
            if (site == 0x424E53BL) return imageBase + 0x424E541L;
            if (site == 0x424E574L) return imageBase + 0x424E57AL;
            if (site == 0x424E5A0L) return imageBase + 0x424E5A6L;
            throw new IllegalStateException("Unreachable");
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(FullCopy437Api.CallResult result) {
            if (result.normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (result.normalReturn().callerRspBits() != this.original.rspBits()) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!result.normalReturn().nonvolatileBits().equals(this.original.nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Interface for Indexed448 calls.
     */
    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}