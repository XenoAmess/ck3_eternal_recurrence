package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppend597Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;

/**
 * Pure API contract for the complete held 351-byte function at RVA 0xADD0D0.
 * Defines the exact call frames and opaque interaction model for the seven legal CALL instructions
 * found in the body. No implementation, no target execution, no state repair.
 */
public final class Add4Fp639Api {
    private Add4Fp639Api() { }

    /**
     * Nested public Memory extends QueueAppend597Api.Memory unchanged.
     */
    public interface Memory extends QueueAppend597Api.Memory {
    }

    /**
     * Exact call frame for one of the seven legal call instructions in the 351-byte body.
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

            if (site == 0xADD153L) {
                // Indirect call at ADD153: FF 50 08 (3 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for ADD153");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for ADD153");
                }
                // Return RIP = imageBase + 0xADD156
                if (returnRipBits != imageBase + 0xADD156L) {
                    throw new IllegalArgumentException("Invalid return RIP for ADD153");
                }
            } else if (site == 0xADD16DL) {
                // Direct call at ADD16D: E8 EE 96 74 03 (5 bytes), target 0x4226860
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for ADD16D");
                }
                if (target != 0x4226860L) {
                    throw new IllegalArgumentException("Invalid direct target for ADD16D");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for ADD16D");
                }
                // Return RIP = imageBase + 0xADD172
                if (returnRipBits != imageBase + 0xADD172L) {
                    throw new IllegalArgumentException("Invalid return RIP for ADD16D");
                }
            } else if (site == 0xADD17CL) {
                // Direct call at ADD17C: E8 DF 96 74 03 (5 bytes), target 0x4226860
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for ADD17C");
                }
                if (target != 0x4226860L) {
                    throw new IllegalArgumentException("Invalid direct target for ADD17C");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for ADD17C");
                }
                // Return RIP = imageBase + 0xADD181
                if (returnRipBits != imageBase + 0xADD181L) {
                    throw new IllegalArgumentException("Invalid return RIP for ADD17C");
                }
            } else if (site == 0xADD1A0L) {
                // Direct call at ADD1A0: E8 BB 96 74 03 (5 bytes), target 0x4226860
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for ADD1A0");
                }
                if (target != 0x4226860L) {
                    throw new IllegalArgumentException("Invalid direct target for ADD1A0");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for ADD1A0");
                }
                // Return RIP = imageBase + 0xADD1A5
                if (returnRipBits != imageBase + 0xADD1A5L) {
                    throw new IllegalArgumentException("Invalid return RIP for ADD1A0");
                }
            } else if (site == 0xADD1B5L) {
                // Indirect call at ADD1B5: FF 50 10 (3 bytes), target is dynamic from memory
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                    throw new IllegalArgumentException("Invalid kind for ADD1B5");
                }
                if (instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid instruction length for ADD1B5");
                }
                // Return RIP = imageBase + 0xADD1B8
                if (returnRipBits != imageBase + 0xADD1B8L) {
                    throw new IllegalArgumentException("Invalid return RIP for ADD1B5");
                }
            } else if (site == 0xADD1F7L) {
                // Direct call at ADD1F7: E8 64 96 74 03 (5 bytes), target 0x4226860
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for ADD1F7");
                }
                if (target != 0x4226860L) {
                    throw new IllegalArgumentException("Invalid direct target for ADD1F7");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for ADD1F7");
                }
                // Return RIP = imageBase + 0xADD1FC
                if (returnRipBits != imageBase + 0xADD1FCL) {
                    throw new IllegalArgumentException("Invalid return RIP for ADD1F7");
                }
            } else if (site == 0xADD219L) {
                // Direct call at ADD219: E8 32 37 EF FF (5 bytes), target 0x9D0950
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    throw new IllegalArgumentException("Invalid kind for ADD219");
                }
                if (target != 0x9D0950L) {
                    throw new IllegalArgumentException("Invalid direct target for ADD219");
                }
                if (instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid instruction length for ADD219");
                }
                // Return RIP = imageBase + 0xADD21E
                if (returnRipBits != imageBase + 0xADD21EL) {
                    throw new IllegalArgumentException("Invalid return RIP for ADD219");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(QueueFp604Api.Normal offered) {
            Objects.requireNonNull(offered);
            FullCopy437Api.CallResult actual = offered.base();
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
     * Opaque interaction model for the seven call instructions.
     * Each invoke must return a complete Outcome with actual post-state.
     */
    public interface Calls {
        /**
         * Handles a call to one of the seven targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}