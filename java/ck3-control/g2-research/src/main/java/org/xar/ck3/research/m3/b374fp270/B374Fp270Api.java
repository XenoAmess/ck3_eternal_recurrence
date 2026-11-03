package org.xar.ck3.research.m3.b374fp270;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;

/**
 * Source-scoped carrier for MXCSR knowledge in the B374 context.
 * Defines the exact call frames and opaque interaction model for the fourteen direct calls
 * and one tail jump found in the body. No implementation, no target execution, no state repair.
 */
public final class B374Fp270Api {
    private B374Fp270Api() { }

    /**
     * Exact call frame for one of the fourteen legal direct call instructions in the 374-byte body.
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

            if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                throw new IllegalArgumentException("Invalid kind for B374 call");
            }

            if (site == 0x425674DL) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 425674D");
            } else if (site == 0x4256759L) {
                if (target != 0x42552D0L) throw new IllegalArgumentException("Invalid target for 4256759");
            } else if (site == 0x425676FL) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 425676F");
            } else if (site == 0x425677BL) {
                if (target != 0x4255910L) throw new IllegalArgumentException("Invalid target for 425677B");
            } else if (site == 0x4256787L) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 4256787");
            } else if (site == 0x4256793L) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 4256793");
            } else if (site == 0x42567B7L) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 42567B7");
            } else if (site == 0x42567CBL) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 42567CB");
            } else if (site == 0x42567DAL) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 42567DA");
            } else if (site == 0x42567E6L) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 42567E6");
            } else if (site == 0x42567F2L) {
                if (target != 0x425689CL) throw new IllegalArgumentException("Invalid target for 42567F2");
            } else if (site == 0x4256821L) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 4256821");
            } else if (site == 0x4256829L) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 4256829");
            } else if (site == 0x4256843L) {
                if (target != 0x424E364L) throw new IllegalArgumentException("Invalid target for 4256843");
            } else {
                throw new IllegalArgumentException("Unknown call site");
            }
        }

        public long returnRipBits() {
            long site = original.callSiteRva();
            long imageBase = childEntry.imageBaseBits();
            return imageBase + site + 5L;
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
     * Tail frame for the final JMP to 0x424E364.
     * Validates the jump site, kind, target, and entry consistency.
     */
    public record TailFrame(
        GovernmentCrtBoundary185Api.Tail original,
        boolean directionFlagSet,
        QueueFp604Api.Mxcsr preMxcsr
    ) {
        public TailFrame {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);

            // Validate exact jump site, kind, and target
            long site = original.jumpSiteRva();
            GovernmentCrtBoundary185Api.TargetKind kind = original.kind();
            long target = original.targetBits();

            if (site != 0x425686DL) {
                throw new IllegalArgumentException("Invalid tail jump site");
            }
            if (kind != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                throw new IllegalArgumentException("Invalid tail kind");
            }
            if (target != 0x424E364L) {
                throw new IllegalArgumentException("Invalid tail target");
            }
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(QueueFp604Api.Normal normal) {
            Objects.requireNonNull(normal);
            // Tail call does not have a return RIP check because it is a JMP, not a CALL.
            // The contract says: "Deliberately NO expected returnRIP check because noownedCALL/RETread in B374tail."

            // Check caller SP: normal callee RET consumes existing tail entry stack slot (no B374 CALL simulation)
            if (normal.base().normalReturn().callerRspBits() != original.entry().rspBits() + 8L) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }

            // Check nonvolatile bits match the tail entry's nonvolatile bits
            if (!normal.base().normalReturn().nonvolatileBits().equals(original.entry().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Opaque interaction model for the direct call instructions and tail jump.
     * Each invoke must return a complete Outcome with actual post-state.
     */
    public interface Calls {
        /**
         * Handles one of the fourteen direct call sites.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        QueueFp604Api.Outcome invoke(CallFrame frame);

        /**
         * Handles the tail jump to 0x424E364.
         * @param frame The validated tail frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        QueueFp604Api.Outcome tail(TailFrame frame);
    }
}