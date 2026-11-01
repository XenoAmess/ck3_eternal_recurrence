package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import java.util.Objects;

/**
 * Explicit full-state projection API for the 130-byte embedded constructor at 0x8895D0.
 * Defines the contract for executing the complete normal CFG with opaque callee ports.
 * This API does not implement the algorithm but provides the necessary types and guards.
 */
public final class EmbeddedInit550Api {
    private EmbeddedInit550Api() { }

    /**
     * Minimal explicit CallFrame record carrying original185.Call, actual child185.Entry,
     * explicit incoming boolean directionFlagSet, actual source instructionLength and actual returnRipBits.
     * Its pure compactconstructor guards nonnulls, child.rspBits==call.rspBits()-8, exact childV.equals(callV) and childN.equals(callN).
     * Prevent duplicatedfields from contradicting. Validate exact original callsite/kind/dynamic-target/length from TWO suppliedcalls.
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
            
            // Validate exact original callsite/kind/dynamic-target/length from TWO suppliedcalls
            if (site == 0x889620L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE || instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid call site 889620");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x889623L) {
                    throw new IllegalArgumentException("Invalid return RIP for 889620");
                }
            } else if (site == 0x889637L) {
                if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE || instructionLength != 3) {
                    throw new IllegalArgumentException("Invalid call site 889637");
                }
                if (returnRipBits != childEntry.imageBaseBits() + 0x88963AL) {
                    throw new IllegalArgumentException("Invalid return RIP for 889637");
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
         * Handles a virtual call.
         * @param frame The call details (site, kind, target, entry).
         * @return The result of the call, including the normal return and post-DF.
         */
        FullCopy437Api.CallResult invoke(CallFrame frame);
    }
}