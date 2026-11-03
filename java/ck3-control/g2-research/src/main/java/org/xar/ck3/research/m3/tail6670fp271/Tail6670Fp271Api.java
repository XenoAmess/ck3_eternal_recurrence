package org.xar.ck3.research.m3.tail6670fp271;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;

/** Source-scoped normal139 tail protocol; no RF, unwind, Native or hardware claim. */
public final class Tail6670Fp271Api {
    private Tail6670Fp271Api() { }

    /**
     * Exact tail frame for the single JMP at 0x42566F6 to 0x4256874.
     * Validates the jump site, kind, target, and child entry consistency.
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
            if (original.jumpSiteRva() != 0x42566F6L) {
                throw new IllegalArgumentException("Invalid jump site");
            }
            if (original.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                throw new IllegalArgumentException("Invalid kind");
            }
            if (original.targetBits() != 0x4256874L) {
                throw new IllegalArgumentException("Invalid target");
            }
        }

        /**
         * Validates the normal return from the opaque callee against the frame's expectations.
         * Does not repair state or perform memory effects.
         */
        public void checkNormalReturn(QueueFp604Api.Normal normal) {
            Objects.requireNonNull(normal);
            if (normal.base().normalReturn().callerRspBits() != original.entry().rspBits() + 8L) {
                throw new IllegalArgumentException("Caller RSP mismatch");
            }
            if (!normal.base().normalReturn().nonvolatileBits().equals(original.entry().nonvolatileBits())) {
                throw new IllegalArgumentException("Nonvolatile mismatch");
            }
        }
    }

    /**
     * Opaque interaction model for the tail transfer.
     */
    public interface Calls {
        /**
         * Handles the tail transfer to 0x4256874.
         * @param frame The validated tail frame.
         * @return The complete result including post-state volatile/nonvolatile bits and DF.
         */
        QueueFp604Api.Outcome tail(TailFrame frame);
    }
}