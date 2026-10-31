package org.xar.ck3.research.m5;
import java.util.Objects;
/** Raw-bit owned boundary for the complete held353B normal region; no Game memory. */
public final class GovernmentCompaction160Api {
    private GovernmentCompaction160Api() { }
    public record Entry(long imageBaseBits, long frameRspBits,
            GovernmentPrimaryTail155Api.VolatileBits volatileBits,
            GovernmentPrimaryTail155Api.NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }
    public record Join(long nextRva, long imageBaseBits, long frameRspBits,
            GovernmentPrimaryTail155Api.VolatileBits volatileBits,
            GovernmentPrimaryTail155Api.NonvolatileBits nonvolatileBits) { }
    public interface Loops {
        /** Actual loop header/index/observed signed32 limit; may reject unsupported work, never clamp. */
        void beforeIteration(long headerRva, long indexBits, int observedLimitBits);
    }
    public static GovernmentPrimaryTail155Api.Registers registers(Entry e) {
        GovernmentPrimaryTail155Api.NonvolatileBits n=e.nonvolatileBits();
        GovernmentPrimaryTail155Api.Registers r=new GovernmentPrimaryTail155Api.Registers(
                new GovernmentPrimaryTail155Api.Entry(e.imageBaseBits(),n.rdiBits(),(int)n.r12Bits(),
                        n.rsiBits(),n.r15Bits(),n.rbpBits(),e.frameRspBits(),n.r13Bits(),n.r14Bits(),n.xmm6(),e.volatileBits()));
        r.rbx=n.rbxBits();r.r12=n.r12Bits();return r;
    }
    public static Join join(Entry e, GovernmentPrimaryTail155Api.Registers r) {
        return new Join(0x30a38cfL,e.imageBaseBits(),r.rsp,r.volatileBits(),r.nonvolatileBits());
    }
}
