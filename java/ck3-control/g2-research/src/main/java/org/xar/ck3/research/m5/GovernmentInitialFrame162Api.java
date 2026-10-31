package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owned normal612B boundary. Model R2 API skeleton retained with owner ABI corrections; no native RET/EH claim. */
public final class GovernmentInitialFrame162Api {
    private GovernmentInitialFrame162Api() { }

    /** Original raw state BEFORE first PUSH; RBP and XMM6 are in incomingNonvolatile once. */
    public record Entry(long imageBaseBits,long originalRspBits,
            VolatileBits incomingVolatile,NonvolatileBits incomingNonvolatile) {
        public Entry { Objects.requireNonNull(incomingVolatile);Objects.requireNonNull(incomingNonvolatile); }
    }

    /** Only actual normalJoin3162; computed RBP is in nonvolatileBits, frame saves stay in shared Memory. */
    public record Join(long nextRva,long imageBaseBits,long frameRspBits,
            VolatileBits volatileBits,NonvolatileBits nonvolatileBits) {
        public Join { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }

    /** Actual3040 allocation-attempt header and raw RBX capacity; pure permit/reject, no clamp or native EH. */
    public interface LoopBudget { void beforeAttempt(long headerRva,long capacityBits); }

    /**
     * One shared exact byte-addressed memory for eight PUSHes, dynamic frame, saved XMM6,
     * initialized/uninitialized stack source bytes and callback aliases. Missing reads unsupported.
     * MOVAPS alignment and normal access are owned preconditions; no zero-fill or implicit heap.
     * Legacy F2 0F10 xmm1,m64 loads low64 and clears represented high64; memory source must exist.
     */
    public interface Memory extends GovernmentPrimaryTail155Api.Memory { }

    /**
     * All ten calls use inherited full OpaqueCall prestate and returned full VolatileBits.
     * RSP is actual caller-side RSP; represented NV normal preservation and normal return are preconditions.
     * Probe42247B0 preRAX=12F8/preRCX=original incomingRCX; postRAX drives SUBRSP,
     * postRCX drives RDI. Neither result is minted or assumed preserved by this contract.
     * Void40EC530 producer cannot fill unknown other volatile bits; port must own them or reject.
     * Shared-memory effects supplied by the owned call implementation; unrepresented inputs unsupported.
     * GS58 inherited port supplies root pointer; actual pointee is read from shared Memory.
     */
    public interface Calls extends GovernmentPrimaryTail155Api.Calls { }
}
