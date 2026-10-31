package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.SlotKnownCompositionData286.Op;
import org.xar.ck3.control.g2.m2.nativecode.SlotKnownCompositionData286.Scene;
import org.xar.ck3.control.g2.m2.nativecode.SlotKnownCompositionData286.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotWithKnownHelpers2A32770.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotWithKnownHelpers2A32770.Calls;

public final class SlotKnownCompositionHost286 {
    private SlotKnownCompositionHost286() { }

    public static int verify() {
        List<Scene> scenes = SlotKnownCompositionCases286.scenes();
        if (scenes.size() != 1) throw new AssertionError("exactly one scene required");
        for (Scene scene : scenes) {
            if (scene.steps().isEmpty() || scene.steps().size() > 512) throw new AssertionError("finite script");
            Script script = new Script(scene.steps());
            long actual = PendingSlotWithKnownHelpers2A32770.produce(script, script, scene.input());
            if (actual != scene.expectedReturn()) throw new AssertionError("full64 return");
            if (script.cursor != scene.steps().size()) throw new AssertionError("unconsumed steps " + script.cursor);
        }
        return 1;
    }

    public static void main(String[] args) { System.out.println(verify()); }

    private static final class Script implements Memory, Calls {
        private final List<Step> steps;
        private int cursor;

        Script(List<Step> steps) {
            this.steps = List.copyOf(steps);
        }

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

        private long call(Op op, PendingContextWithKnownHelpers3076B60.Memory memory, boolean returns, Long... values) {
            if (memory != this) throw new AssertionError("same Memory required");
            Step step = next(op);
            if (!step.values().equals(List.of(values)))
                throw new AssertionError("call " + op + " at step " + (cursor - 1));
            if (returns) {
                // Allocation/getter long return 0 is LEGAL
            } else {
                if (step.returned() != 0) throw new AssertionError("nonzero return for " + op);
            }
            return step.returned();
        }

        @Override public int read8(long a) { return read(Op.R8, a, 2).values().get(1).intValue(); }
        @Override public int read32(long a) { return read(Op.R32, a, 2).values().get(1).intValue(); }
        @Override public long read64(long a) { return read(Op.R64, a, 2).values().get(1).longValue(); }
        @Override public void write8(long a, int v) { write(Op.W8, a, (long) (v & 0xff)); }
        @Override public void write16(long a, int v) { write(Op.W16, a, (long) (v & 0xffff)); }
        @Override public void write32(long a, int v) { write(Op.W32, a, Integer.toUnsignedLong(v)); }
        @Override public void write64(long a, long v) { write(Op.W64, a, v); }
        @Override public void write128(long a, Bits128 v) { write(Op.W128, a, v.low(), v.high()); }
        @Override public Bits128 read128(long a) {
            Step s = read(Op.R128, a, 3);
            return new Bits128(s.values().get(1).longValue(), s.values().get(2).longValue());
        }
        @Override public org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16 read16(long a) {
            Bits128 bits = read128(a);
            return new org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16(bits.low(), bits.high());
        }
        @Override public void write16(long a, org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16 v) {
            write128(a, new Bits128(v.lowRaw64(), v.highRaw64()));
        }

        // Inherited Calls from PendingContextWithKnownHelpers3076B60.Calls
        @Override public void call8895D0(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d) { call(Op.C889, m, false, c, d); }
        @Override public void call37282B0(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d) { call(Op.C37282, m, false, c, d); }
        @Override public void call260E040(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d) { call(Op.C260, m, false, c, d); }
        @Override public void call3727180(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d) { call(Op.C37271, m, false, c, d); }
        @Override public void virtualInit10(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, int e) { call(Op.INIT10, m, false, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void virtualInit20(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, long e) { call(Op.INIT20, m, false, t, c, d, e); }
        @Override public long rangeAllocate(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, int e) { return call(Op.RANGEALLOC, m, true, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void rangeRelease(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, int e) { call(Op.RANGERELEASE, m, false, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void call4226860(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d, long e) { call(Op.COPY, m, false, c, d, e); }
        @Override public void call9CF240(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d, long e) { call(Op.FINALIZE, m, false, c, d, e); }
        @Override public long call25037E0(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d) { return call(Op.REGISTRY, m, true, c, d); }
        @Override public void virtualTail10(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, long e) { call(Op.TAIL10, m, false, t, c, d, e); }
        @Override public void call889780(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d) { call(Op.PREP_ELEMENTS, m, false, c, d); }
        @Override public long elementAllocate(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, int e) { return call(Op.ALLOC_ELEMENTS, m, true, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void callDBDB80(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d, int e, int f) { call(Op.REPLACE_ELEMENTS, m, false, c, d, Integer.toUnsignedLong(e), Integer.toUnsignedLong(f)); }
        @Override public void virtualElementDestroy(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d) { call(Op.DESTROY_ELEMENTS, m, false, t, c, d); }
        @Override public void copy16_21A5050(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d) { call(Op.COPY16_HEAD, m, false, c, d); }
        @Override public void copy4_B2EEE0(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d) { call(Op.COPY4_HEAD, m, false, c, d); }
        @Override public void copy16_8C70B0(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d, long e, long f) { call(Op.COPY16_RANGE, m, false, c, d, e, f); }
        @Override public void copy4_ADD0D0(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d, long e, long f) { call(Op.COPY4_RANGE, m, false, c, d, e, f); }
        @Override public long copy24Allocate(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, int e) { return call(Op.ALLOC24, m, true, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void copy24Release(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, int e) { call(Op.RELEASE24, m, false, t, c, d, Integer.toUnsignedLong(e)); }

        // New 32-byte component callbacks
        @Override public void prepare32_889660(PendingContextWithKnownHelpers3076B60.Memory m, long c) { call(Op.PREP32, m, false, c); }
        @Override public long copy32Allocate(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, int e) { return call(Op.ALLOC32, m, true, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void replace32_8874D0(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d, int e, int f) { call(Op.REPLACE32, m, false, c, d, Integer.toUnsignedLong(e), Integer.toUnsignedLong(f)); }
        @Override public void virtual32Destroy(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d) { call(Op.DESTROY32, m, false, t, c, d); }
        @Override public void finalize32_3727EC0(PendingContextWithKnownHelpers3076B60.Memory m, long c) { call(Op.FINAL32, m, false, c); }

        // New range16 callbacks
        @Override public long range16Virtual8(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, long e, long f) { return call(Op.RANGE16_ALLOC, m, true, t, c, d, e, f); }
        @Override public void range16Virtual16(PendingContextWithKnownHelpers3076B60.Memory m, long t, long c, long d, long e, long f) { call(Op.RANGE16_FREE, m, false, t, c, d, e, f); }
        @Override public void range16Direct8F8550(PendingContextWithKnownHelpers3076B60.Memory m, long c, long d, long e, long f) { call(Op.RANGE16_DIRECT, m, false, c, d, e, f); }

        // Declared Calls in PendingSlotWithKnownHelpers2A32770.Calls
        @Override public boolean call2A321F0(Memory m, long c, int d) {
            if (m != this) throw new AssertionError("same Memory required");
            Step step = next(Op.PAGE);
            if (!step.values().equals(List.of(c, Integer.toUnsignedLong(d))))
                throw new AssertionError("call PAGE at step " + (cursor - 1));
            if (step.returned() != 0 && step.returned() != 1) throw new AssertionError("PAGE return must be 0 or 1");
            return step.returned() == 1;
        }
        @Override public long slotAllocate(Memory m, long t, long c, long d, int e) { return call(Op.SLOTALLOC, m, true, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void slotRelease(Memory m, long t, long c, long d, int e) { call(Op.SLOTRELEASE, m, false, t, c, d, Integer.toUnsignedLong(e)); }
        @Override public void call4226F10(Memory m, long c, int d, long e) { call(Op.SET, m, false, c, Integer.toUnsignedLong(d), e); }

        @Override public int readScalar16(long a) { return read(Op.R16, a, 2).values().get(1).intValue(); }
        @Override public Copy4226860Api.Bits256 read256(long a) {
            Step s = read(Op.R256, a, 5);
            return new Copy4226860Api.Bits256(new Bits128(s.values().get(1).longValue(), s.values().get(2).longValue()), new Bits128(s.values().get(3).longValue(), s.values().get(4).longValue()));
        }
        @Override public void write256(long a, Copy4226860Api.Bits256 v) {
            write(Op.W256, a, v.low128().low(), v.low128().high(), v.high128().low(), v.high128().high());
        }
        @Override public void storeFence() { write(Op.FENCE); }
    }
}