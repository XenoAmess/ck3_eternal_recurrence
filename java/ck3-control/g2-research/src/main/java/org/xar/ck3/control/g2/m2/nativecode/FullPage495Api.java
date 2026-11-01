package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Explicit full-state projection API for the 381-byte normal CFG 2A321F0.
 * Defines the contract for executing the complete normal CFG with opaque callee ports.
 * This API does not implement the algorithm but provides the necessary types and guards.
 */
public final class FullPage495Api {
    private FullPage495Api() { }

    /**
     * Strong union of memory interfaces required for the full state execution.
     * Ensures all operations address the same shared byte storage.
     */
    public interface Memory extends FullCopy437Api.Memory {
        // Inherited methods from FullCopy437Api.Memory:
        // int readUnsignedWord(long addressBits);
        // Bits256 read256(long addressBits);
        // void write256(long addressBits, Bits256 valueBits);
        // void write256NonTemporal(long addressBits, Bits256 valueBits);
        // Plus all GovernmentMemoryFill206Api.Memory and GovernmentCrtBoundary185Api.Memory methods.
    }

    /**
     * Explicit input record for the full state execution.
     * Contains the actual entry state, direction flag, and loop budget.
     */
    public record Input(
        GovernmentCrtBoundary185Api.Entry entry,
        boolean directionFlagSet,
        GovernmentCrtBoundary185Api.LoopBudget budget
    ) {
        public Input {
            Objects.requireNonNull(entry);
            Objects.requireNonNull(budget);
        }
    }

    /**
     * Minimal explicit CallFrame record carrying original185.Call, actual child185.Entry,
     * explicit incoming boolean directionFlagSet, actual source instructionLength and actual returnRipBits.
     * Its pure compactconstructor guards nonnulls, child.rspBits==call.rspBits()-8, exact childV.equals(callV) and childN.equals(callN).
     * Prevent duplicatedfields from contradicting. Validate exact original callsite/kind/directtarget/length from EIGHT suppliedcalls.
     * Guard returnRipBits==child.imageBaseBits()+sourceContinuationRVA using each exactsource continuation.
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
            if (childEntry.rspBits() != call.rspBits() - 8) {
                throw new IllegalArgumentException("Child RSP mismatch");
            }
            if (!childEntry.volatileBits().equals(call.volatileBits())) {
                throw new IllegalArgumentException("Child V mismatch");
            }
            if (!childEntry.nonvolatileBits().equals(call.nonvolatileBits())) {
                throw new IllegalArgumentException("Child N mismatch");
            }
            
            long site = call.callSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = call.kind();
            long target = call.targetBits();
            
            // Validate exact original callsite/kind/directtarget/length from EIGHT suppliedcalls
            if (site == 0x2A3221AL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x3F7AA40L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A3221A");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A3221FL) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A3221A");
                }
            } else if (site == 0x2A32258L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x2A32620L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A32258");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A3225DL) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A32258");
                }
            } else if (site == 0x2A3227CL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4226F10L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A3227C");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A32281L) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A3227C");
                }
            } else if (site == 0x2A322A3L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4223F44L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A322A3");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A322A8L) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A322A3");
                }
            } else if (site == 0x2A322DBL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4223B94L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A322DB");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A322E0L) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A322DB");
                }
            } else if (site == 0x2A322EEL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4226F10L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A322EE");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A322F3L) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A322EE");
                }
            } else if (site == 0x2A32312L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4223F44L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A32312");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A32317L) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A32312");
                }
            } else if (site == 0x2A32325L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4226F10L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A32325");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A3232AL) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A32325");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        /**
         * Pure CallFrame checkNormalReturn(CallResult) or equivalent guard verifying actualNR.returnRipBits()==frame.returnRipBits, callerRspBits()==call.rspBits and completeNR.nonvolatileBits().equals(call.nonvolatileBits()).
         * postDF is offered actualstate, NEVER silently forcedequalincomingDF or false.
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
     * Interface for handling calls during the execution.
     * Must return a CallResult for each interaction.
     * Calls is a NEW abstractinterface, not extends185.Calls.
     * Its invoke accepts CallFrame and returns CallResult; this explicitly supplies allfullpostV/N/RIP/SP andpostDF even for precedingreserve/COPY/virtualallocate-release.
     * No Tail or GS ports are defined as the source contains only local JMPs and no GS access.
     */
    public interface Calls {
        /**
         * Handles a direct call.
         * @param frame The call details (site, kind, target, entry).
         * @return The result of the call, including the normal return and post-DF.
         */
        FullCopy437Api.CallResult invoke(CallFrame frame);
    }
}