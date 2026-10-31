package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Actual two-entry489B local phase, with two raw continuations; no native RET. */
public final class GovernmentEarlierRows161Api {
    private GovernmentEarlierRows161Api() { }
    public enum EntryPoint { AT_30A33B8,AT_30A33C2 }
    public record Entry(long imageBaseBits,EntryPoint entryPoint,long frameRspBits,
            VolatileBits volatileBits,NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(entryPoint);Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    public record Join(long nextRva,long imageBaseBits,long frameRspBits,
            VolatileBits volatileBits,NonvolatileBits nonvolatileBits) { }
    public interface LoopBudget {
        /** Actual loop header, current raw cursor and fixed end; rejection never clamps signed counts. */
        void beforeIteration(long headerRva,long cursorBits,long fixedEndBits);
    }
    public static Registers registers(Entry e) {
        return GovernmentCompaction160Api.registers(new GovernmentCompaction160Api.Entry(
                e.imageBaseBits(),e.frameRspBits(),e.volatileBits(),e.nonvolatileBits()));
    }
    public static Join join(Entry e,Registers r,long nextRva) {
        return new Join(nextRva,e.imageBaseBits(),r.rsp,r.volatileBits(),r.nonvolatileBits());
    }
}
