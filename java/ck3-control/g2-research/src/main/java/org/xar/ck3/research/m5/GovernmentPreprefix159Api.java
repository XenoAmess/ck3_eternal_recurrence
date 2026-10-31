package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Exact normal local two-entry region. Memory, calls and bit snapshots reuse the validated tail API. */
public final class GovernmentPreprefix159Api {
    private GovernmentPreprefix159Api() { }
    public enum EntryPoint { AT_30A3BBA, AT_30A3BC1 }
    public record Entry(long imageBaseBits, EntryPoint entryPoint, long frameRspBits,
            VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public Entry {
            Objects.requireNonNull(entryPoint); Objects.requireNonNull(volatileBits);
            Objects.requireNonNull(nonvolatileBits);
        }
    }
    /** No native RET/type: this is the raw register handoff to instruction30A3EB3. */
    public record Join(long nextRva, long imageBaseBits, long frameRspBits,
            VolatileBits volatileBits, NonvolatileBits nonvolatileBits) {
        public Join { Objects.requireNonNull(volatileBits); Objects.requireNonNull(nonvolatileBits); }
    }
    /** Mechanical adapter only. The preprefix has a raw full-R12 entry, unlike the tail's savedDWORD entry. */
    public static Registers registers(Entry e) {
        NonvolatileBits n=e.nonvolatileBits();
        GovernmentPrimaryTail155Api.Entry seed=new GovernmentPrimaryTail155Api.Entry(
                e.imageBaseBits(),n.rdiBits(),(int)n.r12Bits(),n.rsiBits(),n.r15Bits(),
                n.rbpBits(),e.frameRspBits(),n.r13Bits(),n.r14Bits(),n.xmm6(),e.volatileBits());
        Registers r=new Registers(seed);
        r.rbx=n.rbxBits(); r.r12=n.r12Bits();
        return r;
    }
    public static Join join(Entry e, Registers r) {
        return new Join(0x30a3eb3L,e.imageBaseBits(),r.rsp,r.volatileBits(),r.nonvolatileBits());
    }
}
