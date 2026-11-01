package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Explicit full-state projection API for the 262-byte context copy 3076B60.
 * Defines the contract for executing the complete normal CFG with opaque callee ports.
 * This API does not implement the algorithm but provides the necessary types and guards.
 */
public final class FullContext493Api {
    private FullContext493Api() { }

    /**
     * Strong union of memory interfaces required for the full state execution.
     * Ensures all operations address the same shared byte storage.
     * Extends FullCopy437Api.Memory to inherit exact read/write DWORD/QWORD/128.
     */
    public interface Memory extends FullCopy437Api.Memory {
        // Inherited methods from FullCopy437Api.Memory:
        // int readUnsignedWord(long addressBits);
        // Bits256 read256(long addressBits);
        // void write256(long addressBits, Bits256 valueBits);
        // void write256NonTemporal(long addressBits, Bits256 valueBits);
        // Inherited from GovernmentMemoryFill206Api.Memory:
        // void writeWord(long addressBits, int valueBits);
        // void write128NonTemporal(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits);
        // void sfence();
        // Inherited from GovernmentCrtBoundary185Api.Memory:
        // int readDword(long addressBits);
        // long readQword(long addressBits);
        // int readUnsignedByte(long addressBits);
        // void writeDword(long addressBits, int valueBits);
        // void writeQword(long addressBits, long valueBits);
        // void writeByte(long addressBits, int lowByteBits);
        // Bits128 read128(long addressBits);
        // void write128(long addressBits, Bits128 valueBits);
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
     * Prevent duplicatedfields from contradicting. Validate exact original callsite/kind/directtarget/length from FIVE suppliedcalls.
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
            
            // Validate exact original callsite/kind/directtarget/length from FIVE suppliedcalls
            if (site == 0x3076B8CL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x373ACF0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 3076B8C");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3076B91L) {
                    throw new IllegalArgumentException("Invalid return RIP for 3076B8C");
                }
            } else if (site == 0x3076BA0L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x373ACF0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 3076BA0");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3076BA5L) {
                    throw new IllegalArgumentException("Invalid return RIP for 3076BA0");
                }
            } else if (site == 0x3076C1FL) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x105D2D0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 3076C1F");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3076C24L) {
                    throw new IllegalArgumentException("Invalid return RIP for 3076C1F");
                }
            } else if (site == 0x3076C39L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0xBCB7C0L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 3076C39");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3076C3EL) {
                    throw new IllegalArgumentException("Invalid return RIP for 3076C39");
                }
            } else if (site == 0x3076C49L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || target != 0x2503880L || instructionLength != 5) {
                    throw new IllegalArgumentException("Invalid call site 3076C49");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x3076C4EL) {
                    throw new IllegalArgumentException("Invalid return RIP for 3076C49");
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
     * Source has NO Tail/GS/loop instruction; only Calls.invoke is needed.
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