package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Raw owned normal-port frames; no imported routine identity or OS/ABI proof. */
public final class GovernmentCrtBoundary185Api {
    private GovernmentCrtBoundary185Api() { }
    public record Entry(long imageBaseBits,long rspBits,VolatileBits volatileBits,NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    public record NormalReturn(VolatileBits volatileBits,long returnRipBits,long callerRspBits,NonvolatileBits nonvolatileBits) {
        public NormalReturn { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    public interface Memory extends GovernmentPrimaryTail155Api.Memory { }
    public enum TargetKind { DIRECT_RVA, INDIRECT_ABSOLUTE }
    /** CALL: rspBits is BEFORE the owned push; targetBits interpretation follows kind. */
    public record Call(long callSiteRva,TargetKind kind,long targetBits,long rspBits,VolatileBits volatileBits,NonvolatileBits nonvolatileBits) {
        public Call { Objects.requireNonNull(kind);Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    /** Tail JMP owns no new push or RET: entry is the actual target entry after local epilogue. */
    public record Tail(long jumpSiteRva,TargetKind kind,long targetBits,Entry entry) {
        public Tail { Objects.requireNonNull(kind);Objects.requireNonNull(entry); }
    }
    public interface Calls {
        VolatileBits invoke(Call call);
        NormalReturn tail(Tail transfer);
        long readGsQword58();
    }
    public interface LoopBudget { void beforeStep(long loopHeaderRva,long guardAddressBits); }
}
