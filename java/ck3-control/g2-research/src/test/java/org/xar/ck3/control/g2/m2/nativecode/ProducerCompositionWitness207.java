package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.ProducerCompositionScenario207.Op;
import org.xar.ck3.control.g2.m2.nativecode.ProducerCompositionScenario207.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

/** Owner strict global script after two rejected model hosts. */
public final class ProducerCompositionWitness207 {
    private ProducerCompositionWitness207() { }
    public static void main(String[] args) { System.out.println(verify()); }
    public static int verify() {
        int passed = 0;
        for (var scene : ProducerCompositionCases207.scenes()) {
            Script memory = new Script(scene.steps());
            long result = PendingSlotWithContextCopies2A32770.produce(memory, memory, scene.input());
            if (result != scene.expected() || memory.cursor != memory.steps.size())
                throw new AssertionError(scene.name() + " return/script exhaustion");
            if (memory.steps.size() != 176) throw new AssertionError("fixture callback count");
            passed++;
        }
        return passed;
    }
    private static final class Script implements PendingSlotWithContextCopies2A32770.Memory,
            PendingSlotWithContextCopies2A32770.Calls {
        private final List<Step> steps;
        private int cursor;
        Script(List<Step> steps) { this.steps = List.copyOf(steps); }
        private Step next(Op op, long address) {
            if (cursor >= steps.size()) throw new AssertionError("extra " + op);
            Step step = steps.get(cursor++);
            if (step.op() != op || step.a() != address)
                throw new AssertionError("step " + (cursor - 1) + " expected " + step
                        + " actual " + op + "@" + Long.toHexString(address));
            return step;
        }
        private void values(Step step, long b, long c, long d) {
            if (step.b() != b || step.c() != c || step.d() != d)
                throw new AssertionError("step " + (cursor - 1) + " value/argument mismatch");
        }
        @Override public int read8(long a) { return (int) next(Op.R8, a).b(); }
        @Override public int read32(long a) { return (int) next(Op.R32, a).b(); }
        @Override public long read64(long a) { return next(Op.R64, a).b(); }
        @Override public Bits128 read128(long a) {
            Step step = next(Op.R128, a); return new Bits128(step.b(), step.c());
        }
        @Override public void write8(long a, int v) { values(next(Op.W8, a), v & 0xffL, 0, 0); }
        @Override public void write16(long a, int v) { values(next(Op.W16, a), v & 0xffffL, 0, 0); }
        @Override public void write32(long a, int v) { values(next(Op.W32, a), Integer.toUnsignedLong(v), 0, 0); }
        @Override public void write64(long a, long v) { values(next(Op.W64, a), v, 0, 0); }
        @Override public void write128(long a, Bits128 v) { values(next(Op.W128, a), v.low(), v.high(), 0); }
        private Step call(Object memory, Op op, long rcx) {
            if (memory != this) throw new AssertionError("callee memory identity");
            return next(op, rcx);
        }
        private boolean allocation(Object memory, Op op, long rcx, int edx) {
            Step step = call(memory, op, rcx);
            if (step.b() != Integer.toUnsignedLong(edx) || step.d() != 0
                    || (step.c() != 0 && step.c() != 1))
                throw new AssertionError("allocation argument/lowAL script");
            return step.c() == 1;
        }
        @Override public boolean call1ACDFB0(PendingSlotProducer2A32770.Memory m, long r, int d) {
            return allocation(m, Op.GROW, r, d);
        }
        @Override public boolean call2A321F0(PendingSlotProducer2A32770.Memory m, long r, int d) {
            return allocation(m, Op.PAGE, r, d);
        }
        @Override public void call105D2D0(PendingContextCopy3076B60.Memory m, long r) {
            values(call(m, Op.C105, r), 0, 0, 0);
        }
        @Override public void callBCB7C0(PendingContextCopy3076B60.Memory m,
                long r, int d, long r8, long r9) {
            values(call(m, Op.CBCB, r), Integer.toUnsignedLong(d), r8, r9);
        }
        @Override public void call2503880(PendingContextCopy3076B60.Memory m, long r, long d) {
            values(call(m, Op.C250, r), d, 0, 0);
        }
        @Override public void call8895D0(PendingEmbeddedCopy373ACF0.Memory m, long r, long d) {
            values(call(m, Op.C889, r), d, 0, 0);
        }
        @Override public void call37282B0(PendingEmbeddedCopy373ACF0.Memory m, long r, long d) {
            values(call(m, Op.C37282, r), d, 0, 0);
        }
        @Override public void call260E040(PendingEmbeddedCopy373ACF0.Memory m, long r, long d) {
            values(call(m, Op.C260, r), d, 0, 0);
        }
        @Override public void call3727180(PendingEmbeddedCopy373ACF0.Memory m, long r, long d) {
            values(call(m, Op.C37271, r), d, 0, 0);
        }
    }
}
