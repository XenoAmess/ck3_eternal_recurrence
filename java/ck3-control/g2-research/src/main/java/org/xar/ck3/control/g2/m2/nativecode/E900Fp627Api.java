package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.Fc74Fp626Api;

/**
 * Source-scoped carrier for E900 FP/DF knowledge in the queue/append context.
 * No FP implementation, no native proof, no old file rewrite.
 */
public final class E900Fp627Api {
    private E900Fp627Api() { }

    /**
     * Exact call frame for the direct call to 424E448 in the 70B E900 body.
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

            if (site != 0x424E922L) {
                throw new IllegalArgumentException("Invalid call site for E900 CallFrame");
            }
            if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                throw new IllegalArgumentException("Invalid kind for 424E922");
            }
            if (target != 0x424E448L) {
                throw new IllegalArgumentException("Invalid direct target for 424E922");
            }
            // Return RIP = imageBase + 0x424E927
            if (returnRipBits() != imageBase + 0x424E927L) {
                throw new IllegalArgumentException("Invalid return RIP for 424E922");
            }
        }

        public long returnRipBits() {
            long site = original.callSiteRva();
            long imageBase = childEntry.imageBaseBits();
            if (site == 0x424E922L) return imageBase + 0x424E927L;
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
     * Exact tail frame for the indirect jumps at 424E933 or 424E93F in the 70B E900 body.
     * Validates the tail site, kind, target, and entry consistency with the caller frame.
     */
    public record TailFrame(
        GovernmentCrtBoundary185Api.Tail original,
        Fc74Fp626Api.CallFrame caller,
        boolean directionFlagSet,
        QueueFp604Api.Mxcsr preMxcsr
    ) {
        public TailFrame(GovernmentCrtBoundary185Api.Tail original,
                         Fc74Fp626Api.CallFrame caller,
                         boolean directionFlagSet, QueueFp604Api.Mxcsr preMxcsr) {
            this.original = original;
            this.caller = caller;
            this.directionFlagSet = directionFlagSet;
            this.preMxcsr = preMxcsr;
            Objects.requireNonNull(original);
            Objects.requireNonNull(caller);
            Objects.requireNonNull(preMxcsr);

            // Caller must be the actual FC96 DIRECT 424E900 frame
            if (caller.original().callSiteRva() != 0x424FC96L ||
                caller.original().kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA ||
                caller.original().targetBits() != 0x424E900L) {
                throw new IllegalArgumentException("Caller frame mismatch");
            }

            // Validate exact tail site, kind, and target
            long site = original.jumpSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = original.kind();
            long target = original.targetBits();
            long imageBase = original.entry().imageBaseBits();

            if (site != 0x424E933L && site != 0x424E93FL) {
                throw new IllegalArgumentException("Invalid tail site for E900 TailFrame");
            }
            if (kind != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) {
                throw new IllegalArgumentException("Invalid kind for E900 tail");
            }
            // Full raw 64-bit actual target carried (no positivity/normalization/reread)
            // No validation of target value itself, just that it's present.

            // Entry consistency: imageBase and rsp must match caller's childEntry
            if (imageBase != caller.childEntry().imageBaseBits()) {
                throw new IllegalArgumentException("Tail entry imageBase mismatch");
            }
            if (original.entry().rspBits() != caller.childEntry().rspBits()) {
                throw new IllegalArgumentException("Tail entry rsp mismatch");
            }
        }

        public long returnRipBits() {
            return caller.returnRipBits();
        }

        /**
         * Validates the normal return from the opaque tail callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(FullCopy437Api.CallResult result) {
            if (result.normalReturn().returnRipBits() != this.returnRipBits()) {
                throw new IllegalArgumentException("Return RIP mismatch");
            }
            if (result.normalReturn().callerRspBits() != this.original.entry().rspBits() + 8) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!result.normalReturn().nonvolatileBits().equals(this.original.entry().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Interface for E900 calls.
     */
    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
        QueueFp604Api.Outcome tail(TailFrame frame);
    }
}