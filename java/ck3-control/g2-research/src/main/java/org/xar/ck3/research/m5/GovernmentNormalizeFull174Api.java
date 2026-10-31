package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/**
 * API declarations for the full-register normalizer model of 30A2CC0.
 * Entry represents the state immediately after the CALL push (pre-prologue).
 * NormalReturn captures the raw absolute return RIP and the caller's restored RSP.
 */
public final class GovernmentNormalizeFull174Api {
    private GovernmentNormalizeFull174Api() { }

    /**
     * State at the callee entry point (after CALL push, before prologue).
     * rspBits is the RSP address immediately after CALL pushes its return QWORD; the prologue has not run.
     */
    public record Entry(long imageBaseBits, long rspBits, VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public Entry {
            Objects.requireNonNull(volatileBits);
            Objects.requireNonNull(nonvolatileBits);
        }
    }

    /**
     * Result of normal execution.
     * returnRipBits is the raw absolute address read from the stack at the RET instruction.
     * callerRspBits is the RSP value after the RET (entry.rspBits + 8).
     */
    public record NormalReturn(VolatileBits volatileBits, long returnRipBits, long callerRspBits, NonvolatileBits nonvolatileBits) {
        public NormalReturn {
            Objects.requireNonNull(volatileBits);
            Objects.requireNonNull(nonvolatileBits);
        }
    }

    /**
     * Owned memory view reusing the supplied tail API shape.
     * Includes lockedXaddDword via inheritance from GovernmentCaller153Api.Memory.
     */
    public interface Memory extends GovernmentPrimaryTail155Api.Memory {
    }

    /**
     * Owned normal-call view; NV preservation and represented-machine inputs remain the supplied port preconditions.
     * Provides generic invoke(OpaqueCall) and readGsQword58().
     */
    public interface Calls extends GovernmentPrimaryTail155Api.Calls {
    }
}
