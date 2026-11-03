package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Source-scoped carrier for MXCSR knowledge in the queue/append context.
 * No FP implementation, no native proof, no old file rewrite.
 */
public final class Fc74Fp626Api {
    private Fc74Fp626Api() { }

    /**
     * Exact call frame for one of the legal call instructions in the 204B normal body.
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

            if (site == 0x424FC83L) {
                // Indirect call at 424FC83: FF 15 ... (6 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424FC83");
                }
                // Return RIP = imageBase + 0x424FC89
                if (returnRipBits() != imageBase + 0x424FC89L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FC83");
                }
            } else if (site == 0x424FC96L) {
                // Direct call at 424FC96: E8 ... (5 bytes), target 0x424E900
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E900L) {
                    throw new IllegalArgumentException("Invalid direct target for 424FC96");
                }
                if (returnRipBits() != imageBase + 0x424FC9BL) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FC96");
                }
            } else if (site == 0x424FCB9L) {
                // Direct call at 424FCB9: E8 ... (5 bytes), target 0x424E948
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E948L) {
                    throw new IllegalArgumentException("Invalid direct target for 424FCB9");
                }
                if (returnRipBits() != imageBase + 0x424FCBEL) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FCB9");
                }
            } else if (site == 0x424FCCCL) {
                // Direct call at 424FCCC: E8 ... (5 bytes), target 0x424E2EC
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E2ECL) {
                    throw new IllegalArgumentException("Invalid direct target for 424FCCC");
                }
                if (returnRipBits() != imageBase + 0x424FCD1L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FCCC");
                }
            } else if (site == 0x424FCE1L) {
                // Direct call at 424FCE1: E8 ... (5 bytes), target 0x424E948
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E948L) {
                    throw new IllegalArgumentException("Invalid direct target for 424FCE1");
                }
                if (returnRipBits() != imageBase + 0x424FCE6L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FCE1");
                }
            } else if (site == 0x424FCE8L) {
                // Direct call at 424FCE8: E8 ... (5 bytes), target 0x424E364
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E364L) {
                    throw new IllegalArgumentException("Invalid direct target for 424FCE8");
                }
                if (returnRipBits() != imageBase + 0x424FCEDL) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FCE8");
                }
            } else if (site == 0x424FCF2L) {
                // Direct call at 424FCF2: E8 ... (5 bytes), target 0x424E948
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E948L) {
                    throw new IllegalArgumentException("Invalid direct target for 424FCF2");
                }
                if (returnRipBits() != imageBase + 0x424FCF7L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FCF2");
                }
            } else if (site == 0x424FD03L) {
                // Direct call at 424FD03: E8 ... (5 bytes), target 0x424E948
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E948L) {
                    throw new IllegalArgumentException("Invalid direct target for 424FD03");
                }
                if (returnRipBits() != imageBase + 0x424FD08L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FD03");
                }
            } else if (site == 0x424FD10L) {
                // Direct call at 424FD10: E8 ... (5 bytes), target 0x424F8A8
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424F8A8L) {
                    throw new IllegalArgumentException("Invalid direct target for 424FD10");
                }
                if (returnRipBits() != imageBase + 0x424FD15L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FD10");
                }
            } else if (site == 0x424FD17L) {
                // Direct call at 424FD17: E8 ... (5 bytes), target 0x424E364
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x424E364L) {
                    throw new IllegalArgumentException("Invalid direct target for 424FD17");
                }
                if (returnRipBits() != imageBase + 0x424FD1CL) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FD17");
                }
            } else if (site == 0x424FD21L) {
                // Indirect call at 424FD21: FF 15 ... (6 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for 424FD21");
                }
                if (returnRipBits() != imageBase + 0x424FD27L) {
                    throw new IllegalArgumentException("Invalid return RIP for 424FD21");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        public long returnRipBits() {
            long site = original.callSiteRva();
            long imageBase = childEntry.imageBaseBits();
            if (site == 0x424FC83L) return imageBase + 0x424FC89L;
            if (site == 0x424FC96L) return imageBase + 0x424FC9BL;
            if (site == 0x424FCB9L) return imageBase + 0x424FCBEL;
            if (site == 0x424FCCCL) return imageBase + 0x424FCD1L;
            if (site == 0x424FCE1L) return imageBase + 0x424FCE6L;
            if (site == 0x424FCE8L) return imageBase + 0x424FCEDL;
            if (site == 0x424FCF2L) return imageBase + 0x424FCF7L;
            if (site == 0x424FD03L) return imageBase + 0x424FD08L;
            if (site == 0x424FD10L) return imageBase + 0x424FD15L;
            if (site == 0x424FD17L) return imageBase + 0x424FD1CL;
            if (site == 0x424FD21L) return imageBase + 0x424FD27L;
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
     * Interface for queue calls.
     */
    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}