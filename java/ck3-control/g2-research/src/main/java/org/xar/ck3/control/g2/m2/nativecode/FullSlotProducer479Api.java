package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotProducer2A32770;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityKnownCopyFullState456;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Explicit full-state projection API for the 470B caller 2A32770.
 * Defines the contract for executing the complete normal CFG with opaque callee ports.
 * This API does not implement the algorithm but provides the necessary types and guards.
 */
public final class FullSlotProducer479Api {
    private FullSlotProducer479Api() { }

    /**
     * Strong union of memory interfaces required for the full state execution.
     * Ensures all operations address the same shared byte storage.
     */
    public interface Memory extends PendingSlotProducer2A32770.Memory, PendingSlotCapacityKnownCopyFullState456.Memory {
        // Inherited methods from PendingSlotProducer2A32770.Memory:
        // int read8(long address);
        // int read32(long address);
        // long read64(long address);
        // Inherited methods from PendingSlotCapacityKnownCopyFullState456.Memory:
        // (extends PendingSlotCapacityFullState412Api.Memory and FullCopy437Api.Memory)
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
     * Prevent duplicatedfields from contradicting. Validate exact original callsite/kind/directtarget/length from FOUR suppliedcalls.
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
            
            // Validate exact original callsite/kind/directtarget/length from FOUR suppliedcalls
            if (site == 0x2A327CEL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x1ACDFB0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A327CE");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A327D3L) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A327CE");
                }
            } else if (site == 0x2A327E7L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x2A321F0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A327E7");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A327ECL) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A327E7");
                }
            } else if (site == 0x2A328C4L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x3076B60L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A328C4");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A328C9L) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A328C4");
                }
            } else if (site == 0x2A328D0L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x2756120L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 2A328D0");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x2A328D5L) {
                    throw new IllegalArgumentException("Invalid return RIP for 2A328D0");
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