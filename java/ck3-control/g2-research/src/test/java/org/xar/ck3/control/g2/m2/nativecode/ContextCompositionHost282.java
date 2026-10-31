package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.ContextCompositionData282.Op;
import org.xar.ck3.control.g2.m2.nativecode.ContextCompositionData282.Scene;
import org.xar.ck3.control.g2.m2.nativecode.ContextCompositionData282.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextWithKnownHelpers3076B60.Memory;

/** Finite, globally ordered scripted callbacks; no default memory or target-derived expectations. */
public final class ContextCompositionHost282 {
    private ContextCompositionHost282() { }
    public static int verify() {
        List<Scene> scenes = ContextCompositionCases282.scenes();
        if (scenes.size() != 1) throw new AssertionError("exactly one scene required");
        for (Scene scene : scenes) {
            if (scene.steps().isEmpty() || scene.steps().size() > 512) throw new AssertionError("finite script");
            Script script = new Script(scene.steps());
            long actual = PendingContextWithKnownHelpers3076B60.copy(script, script,
                    scene.destination(), scene.source(), scene.moduleBase());
            if (actual != scene.expectedReturn()) throw new AssertionError("full64 return");
            if (script.cursor != scene.steps().size()) throw new AssertionError("unconsumed steps " + script.cursor);
        }
        return scenes.size();
    }
    public static void main(String[] args) { System.out.println(verify()); }

    private static final class Script implements Memory, PendingContextWithKnownHelpers3076B60.Calls {
        private final List<Step> steps;
        private int cursor;
        Script(List<Step> steps) { this.steps = List.copyOf(steps); }
        private Step next(Op op) {
            if (cursor == steps.size()) throw new AssertionError("extra " + op);
            Step step = steps.get(cursor++);
            if (step.op() != op) throw new AssertionError("step " + (cursor - 1) + ": expected " + step.op() + ", got " + op);
            return step;
        }
        private Step read(Op op, long address, int width) {
            Step step = next(op);
            if (step.values().size() != width || step.values().get(0).longValue() != address
                    || step.returned() != 0) throw new AssertionError("read " + op + " at step " + (cursor - 1));
            return step;
        }
        private void write(Op op, Long... values) {
            Step step = next(op);
            if (!step.values().equals(List.of(values)) || step.returned() != 0)
                throw new AssertionError("write " + op + " at step " + (cursor - 1));
        }
        private long call(Op op, Memory memory, boolean returns, Long... values) {
            if (memory != this) throw new AssertionError("same Memory required");
            Step step = next(op);
            if (!step.values().equals(List.of(values)) || (!returns && step.returned() != 0))
                throw new AssertionError("call " + op + " at step " + (cursor - 1));
            return step.returned();
        }
        @Override public int read8(long a) { return read(Op.R8, a, 2).values().get(1).intValue(); }
        @Override public int read32(long a) { return read(Op.R32, a, 2).values().get(1).intValue(); }
        @Override public long read64(long a) { return read(Op.R64, a, 2).values().get(1).longValue(); }
        @Override public Bits128 read128(long a) {
            Step s = read(Op.R128, a, 3);
            return new Bits128(s.values().get(1).longValue(), s.values().get(2).longValue());
        }
        @Override public void write8(long a, int v) { write(Op.W8, a, (long) (v & 0xff)); }
        @Override public void write16(long a, int v) { write(Op.W16, a, (long) (v & 0xffff)); }
        @Override public void write32(long a, int v) { write(Op.W32, a, Integer.toUnsignedLong(v)); }
        @Override public void write64(long a, long v) { write(Op.W64, a, v); }
        @Override public void write128(long a, Bits128 v) { write(Op.W128, a, v.low(), v.high()); }
        @Override public void call8895D0(Memory m, long c, long d) { call(Op.C889, m, false, c, d); }
        @Override public void call37282B0(Memory m, long c, long d) { call(Op.C37282, m, false, c, d); }
        @Override public void call260E040(Memory m, long c, long d) { call(Op.C260, m, false, c, d); }
        @Override public void call3727180(Memory m, long c, long d) { call(Op.C37271, m, false, c, d); }
        @Override public void virtualInit10(Memory m, long t, long c, long d, int e) { call(Op.INIT10, m, false, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void virtualInit20(Memory m, long t, long c, long d, long e) { call(Op.INIT20, m, false, t, c, d, e); }
        @Override public long rangeAllocate(Memory m, long t, long c, long d, int e) { return call(Op.RANGEALLOC, m, true, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void rangeRelease(Memory m, long t, long c, long d, int e) { call(Op.RANGERELEASE, m, false, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void call4226860(Memory m, long c, long d, long e) { call(Op.COPY, m, false, c, d, e); }
        @Override public void call9CF240(Memory m, long c, long d, long e) { call(Op.FINALIZE, m, false, c, d, e); }
        @Override public long call25037E0(Memory m, long c, long d) { return call(Op.REGISTRY, m, true, c, d); }
        @Override public void virtualTail10(Memory m, long t, long c, long d, long e) { call(Op.TAIL10, m, false, t, c, d, e); }
    }
}
