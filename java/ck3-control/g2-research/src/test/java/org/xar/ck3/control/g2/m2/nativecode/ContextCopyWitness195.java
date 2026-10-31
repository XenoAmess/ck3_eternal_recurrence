package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.ContextCopyScenario195.Op;
import org.xar.ck3.control.g2.m2.nativecode.ContextCopyScenario195.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

/** Owner strict script after two rejected whole model hosts; no target-derived values. */
public final class ContextCopyWitness195 {
    private ContextCopyWitness195() { }
    public static void main(String[] args) { System.out.println(verify()); }
    public static int verify() {
        int count = 0;
        for (var scene : ContextCopyCases195.scenes()) {
            Script memory = new Script(scene.steps());
            long result = PendingContextCopy3076B60.copy(memory, memory,
                    scene.destination(), scene.source());
            if (result != scene.destination() || memory.cursor != memory.steps.size())
                throw new AssertionError(scene.name() + " return or script exhaustion");
            count++;
        }
        return count;
    }
    private static final class Script implements PendingContextCopy3076B60.Memory,
            PendingContextCopy3076B60.Calls {
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
        @Override public int read32(long address) { return (int) next(Op.R32, address).b(); }
        @Override public long read64(long address) { return next(Op.R64, address).b(); }
        @Override public Bits128 read128(long address) {
            Step step = next(Op.R128, address);
            return new Bits128(step.b(), step.c());
        }
        @Override public void write8(long address, int value) {
            throw new AssertionError("unexpected byte write");
        }
        @Override public void write32(long address, int value) {
            values(next(Op.W32, address), Integer.toUnsignedLong(value), 0, 0);
        }
        @Override public void write64(long address, long value) {
            values(next(Op.W64, address), value, 0, 0);
        }
        @Override public void write128(long address, Bits128 value) {
            values(next(Op.W128, address), value.low(), value.high(), 0);
        }
        private void call(PendingContextCopy3076B60.Memory memory, Op op,
                long rcx, long b, long c, long d) {
            if (memory != this) throw new AssertionError("callee memory mismatch");
            values(next(op, rcx), b, c, d);
        }
        @Override public void call373ACF0(PendingContextCopy3076B60.Memory memory,
                long rcx, long rdx) { call(memory, Op.C373, rcx, rdx, 0, 0); }
        @Override public void call105D2D0(PendingContextCopy3076B60.Memory memory,
                long rcx) { call(memory, Op.C105, rcx, 0, 0, 0); }
        @Override public void callBCB7C0(PendingContextCopy3076B60.Memory memory,
                long rcx, int edx, long r8, long r9) {
            call(memory, Op.CBCB, rcx, Integer.toUnsignedLong(edx), r8, r9);
        }
        @Override public void call2503880(PendingContextCopy3076B60.Memory memory,
                long rcx, long rdx) { call(memory, Op.C250, rcx, rdx, 0, 0); }
    }
}
