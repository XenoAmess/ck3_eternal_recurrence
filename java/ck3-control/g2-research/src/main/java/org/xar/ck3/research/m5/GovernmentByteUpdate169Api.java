package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;

/** Raw callee entry/normal return for both complete integer bodies; no Native/EH/flags/loaded claims. */
public final class GovernmentByteUpdate169Api {
    private GovernmentByteUpdate169Api() { }

    /** frameRspBits is AFTER CALL pushed its owned return QWORD; snapshots retain full incoming RBX/R12. */
    public record Entry(long imageBaseBits, long frameRspBits, VolatileBits volatileBits, NonvolatileBits nonvolatileBits, Mxcsr32 mxcsr) {
        public Entry { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); Objects.requireNonNull(mxcsr); }
    }

    /** Actual RET memory read and caller RSP, all resulting V/N; output/home aliasing may change restored NV. */
    public record NormalReturn(VolatileBits volatileBits, NonvolatileBits nonvolatileBits, long returnRipBits, long callerRspBits, Mxcsr32 mxcsr) {
        public NormalReturn { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); Objects.requireNonNull(mxcsr); }
    }

    public interface Memory extends GovernmentPrimaryTail155Api.Memory { }

    /**
     * Called at actual headers3F7E120/180/1B0 before corresponding native work; pure permit/reject only.
     * r9dBits is low32 zero-extended; r8Bits is raw cursor. rbxBits is current raw RBX:
     * prefix120 uses EBX fill remaining, block180 uses end pointer, tail1B0 retains that raw value.
     * Never clamp signed counts or raw pointer wrap. Full455B integer/no-SSE source preserves XMM/MXCSR.
     */
    public interface LoopBudget {
        void beforeIteration(long headerRva, long r8Bits, long r9dBits, long rbxBits);
    }

}
