package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;
import java.util.Objects;

/**
 * Explicit M2 full-call mode API for PendingSlotCapacity1ACDFB0.
 * Defines the contract for executing the complete 372-byte normal CFG with opaque reserve and set ports.
 * This API does not implement the algorithm but provides the necessary types and guards for the caller.
 */
public final class PendingSlotCapacityFullState412Api {
    private PendingSlotCapacityFullState412Api() { }

    /**
     * Union of memory interfaces required for the full state execution.
     * Ensures all operations address the same shared byte storage.
     */
    public interface Memory extends GovernmentMemoryFill206Api.Memory, PendingSlotCapacity1ACDFB0.Memory, PendingSlotArrayReserve1ACE4B0.Memory {
        // Inherited methods from GovernmentMemoryFill206Api.Memory:
        // void writeWord(long addressBits, int valueBits);
        // void write128NonTemporal(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits);
        // void sfence();
        // Inherited methods from PendingSlotCapacity1ACDFB0.Memory:
        // int read8(long address);
        // int read32(long address);
        // long read64(long address);
        // void write32(long address, int value);
        // void write64(long address, long value);
        // Inherited methods from PendingSlotArrayReserve1ACE4B0.Memory:
        // int read32(long address);
        // long read64(long address);
        // void write32(long address, int value);
        // void write64(long address, long value);
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
     * Represents the result of a call or tail transfer, including the normal return state and direction flag.
     * This is distinct from the standard NormalReturn to explicitly carry the post-DF state.
     */
    public record CallResult(
        GovernmentCrtBoundary185Api.NormalReturn normalReturn,
        boolean postDirectionFlagSet
    ) {
        public CallResult {
            Objects.requireNonNull(normalReturn);
        }
    }

    /**
     * Minimal explicit CallFrame record carrying original185.Call, actual child185.Entry, explicit incoming boolean directionFlagSet, actual source instructionLength and actual returnRipBits.
     * Its pure compactconstructor guards nonnulls, child.rspBits==call.rspBits()-8, exact childV.equals(callV) and childN.equals(callN); use childEntry.imageBaseBits for actualimage.
     * Prevent duplicatedfields from contradicting. Validate exact original callsite/kind/directtarget/length from FIVE suppliedcalls, while INDIRECT_ABSOLUTE targetBits remains actual fresh target, not a guessedRVA.
     * Guard returnRipBits==child.imageBaseBits()+sourceContinuationRVA using each exactsource continuation; not generic site+5.
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
            
            // Validate exact original callsite/kind/directtarget/length from FIVE suppliedcalls
            long site = call.callSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = call.kind();
            long target = call.targetBits();
            
            if (site == 0x1ACDFF3L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x1ACE4B0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 1ACDFF3");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x1ACDFF8L) {
                    throw new IllegalArgumentException("Invalid return RIP for 1ACDFF3");
                }
            } else if (site == 0x1ACE015L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4226F10L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 1ACE015");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x1ACE01AL) {
                    throw new IllegalArgumentException("Invalid return RIP for 1ACE015");
                }
            } else if (site == 0x1ACE4E1L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE || instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid call site 1ACE4E1");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x1ACE4E4L) {
                    throw new IllegalArgumentException("Invalid return RIP for 1ACE4E1");
                }
            } else if (site == 0x1ACE4FCL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x4226860L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 1ACE4FC");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x1ACE501L) {
                    throw new IllegalArgumentException("Invalid return RIP for 1ACE4FC");
                }
            } else if (site == 0x1ACE514L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE || instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid call site 1ACE514");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x1ACE517L) {
                    throw new IllegalArgumentException("Invalid return RIP for 1ACE514");
                }
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        /**
         * Pure CallFrame checkNormalReturn(CallResult) or equivalent guard verifying actualNR.returnRipBits()==frame.returnRipBits, callerRspBits()==call.rspBits and completeNR.nonvolatileBits().equals(call.nonvolatileBits()).
         * postDF is offered actualstate, NEVER silently forcedequalincomingDF or false.
         */
        public void checkNormalReturn(CallResult result) {
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
     * Minimal explicit TailFrame(185.Tail transfer,boolean directionFlagSet), with nonnulltransfer.
     * Tail result is whole actualNR+postDF with arbitraryactualRIP/SP, no CALLpush/forcedcontinuation/normalcallguard/extraRET.
     */
    public record TailFrame(
        GovernmentCrtBoundary185Api.Tail transfer,
        boolean directionFlagSet
    ) {
        public TailFrame {
            Objects.requireNonNull(transfer);
        }
    }

    /**
     * Interface for handling calls and tails during the execution.
     * Must return a CallResult for each interaction.
     * Calls is a NEW abstractinterface, not extends185.Calls.
     * Its invoke accepts CallFrame and returns CallResult; this explicitly supplies allfullpostV/N/RIP/SP andpostDF even for precedingreserve/COPY/virtualallocate-release.
     * Add a minimal TailFrame(185.Tail transfer,boolean directionFlagSet), with nonnulltransfer, and abstract Calls.tail(TailFrame)->CallResult.
     * longreadGsQword58 may remain abstract.
     */
    public interface Calls {
        /**
         * Handles a direct or indirect call.
         * @param frame The call details (site, kind, target, entry).
         * @return The result of the call, including the normal return and post-DF.
         */
        CallResult invoke(CallFrame frame);

        /**
         * Handles a tail transfer.
         * @param frame The tail details (site, kind, target, entry).
         * @return The result of the tail, including the normal return and post-DF.
         */
        CallResult tail(TailFrame frame);

        /**
         * Reads the GS Qword 58.
         * @return The value read.
         */
        long readGsQword58();
    }
}
