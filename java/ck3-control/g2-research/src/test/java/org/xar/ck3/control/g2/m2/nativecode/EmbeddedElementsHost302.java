package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsData302.Op;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsData302.Scene;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsData302.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedElements37282B0;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedElements37282B0.Memory;

/** Finite, globally ordered scripted callbacks; no default memory or target-derived expectations. */
public final class EmbeddedElementsHost302 {
    private EmbeddedElementsHost302() { }

    public static int verify() {
        List<Scene> scenes = EmbeddedElementsCases302.scenes();
        if (scenes.size() != 4) throw new AssertionError("exactly 4 scenes required");
        for (Scene scene : scenes) {
            if (scene.steps().isEmpty() && scene.steps().size() > 512) throw new AssertionError("finite script");
            // Selfguard case legitimately 0 steps, but loop condition above allows 0..512
            if (scene.steps().size() > 512) throw new AssertionError("finite script");

            Script script = new Script(scene.steps());
            long actual = PendingEmbeddedElements37282B0.copy(script, script, scene.destination(), scene.source(), scene.moduleBase());

            if (actual != scene.expectedReturn()) throw new AssertionError("full64 return mismatch");
            if (script.cursor != scene.steps().size()) throw new AssertionError("unconsumed steps " + script.cursor);
        }
        return 4;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static final class Script implements PendingEmbeddedElements37282B0.Memory, PendingEmbeddedElements37282B0.Calls {
        private final List<Step> steps;
        private int cursor;

        Script(List<Step> steps) {
            this.steps = List.copyOf(steps);
            this.cursor = 0;
        }

        private Step next(Op op) {
            if (cursor == steps.size()) throw new AssertionError("extra " + op);
            Step step = steps.get(cursor++);
            if (step.op() != op) throw new AssertionError("step " + (cursor - 1) + ": expected " + step.op() + ", got " + op);
            return step;
        }

        private Step read(Op op, long address, int width) {
            Step step = next(op);
            if (step.values().size() != width || step.values().get(0).longValue() != address || step.returned() != 0) {
                throw new AssertionError("read " + op + " at step " + (cursor - 1));
            }
            return step;
        }

        private void write(Op op, Long... values) {
            Step step = next(op);
            if (!step.values().equals(List.of(values)) || step.returned() != 0) {
                throw new AssertionError("write " + op + " at step " + (cursor - 1));
            }
        }

        private long call(Op op, Memory memory, boolean returns, Long... values) {
            if (memory != this) throw new AssertionError("same Memory required");
            Step step = next(op);
            if (!step.values().equals(List.of(values)) || (!returns && step.returned() != 0)) {
                throw new AssertionError("call " + op + " at step " + (cursor - 1));
            }
            return step.returned();
        }

        @Override public int read8(long address) {
            return read(Op.R8, address, 2).values().get(1).intValue();
        }

        @Override public int read32(long address) {
            return read(Op.R32, address, 2).values().get(1).intValue();
        }

        @Override public long read64(long address) {
            return read(Op.R64, address, 2).values().get(1).longValue();
        }

        @Override public void write8(long address, int value) {
            write(Op.W8, address, (long) (value & 0xff));
        }

        @Override public void write32(long address, int value) {
            write(Op.W32, address, Integer.toUnsignedLong(value));
        }

        @Override public void write64(long address, long value) {
            write(Op.W64, address, value);
        }

        @Override public void call889780(Memory memory, long rcx, long rdx) {
            call(Op.PREP, memory, false, rcx, rdx);
        }

        @Override public long allocate(Memory memory, long target, long rcx, long rdx, int r8d) {
            return call(Op.ALLOC, memory, true, target, rcx, rdx, Integer.toUnsignedLong(r8d));
        }

        @Override public void callDBDB80(Memory memory, long rcx, long rdx, int r8d, int r9d) {
            call(Op.REPLACE, memory, false, rcx, rdx, Integer.toUnsignedLong(r8d), Integer.toUnsignedLong(r9d));
        }

        @Override public void virtualDestroy(Memory memory, long target, long rcx, long rdx) {
            call(Op.DESTROY, memory, false, target, rcx, rdx);
        }

        @Override public void copy16_21A5050(Memory memory, long destinationHeader, long sourceHeader) {
            call(Op.COPY16HEAD, memory, false, destinationHeader, sourceHeader);
        }

        @Override public void copy4_B2EEE0(Memory memory, long destinationHeader, long sourceHeader) {
            call(Op.COPY4HEAD, memory, false, destinationHeader, sourceHeader);
        }

        @Override public void copy16_8C70B0(Memory memory, long destinationHeader, long rdxZero, long begin, long end) {
            call(Op.COPY16RANGE, memory, false, destinationHeader, rdxZero, begin, end);
        }

        @Override public void copy4_ADD0D0(Memory memory, long destinationHeader, long rdxZero, long begin, long end) {
            call(Op.COPY4RANGE, memory, false, destinationHeader, rdxZero, begin, end);
        }

        @Override public org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16 read16(long address) {
            Step step = next(Op.R128);
            if (step.values().size() != 3 || step.values().get(0).longValue() != address || step.returned() != 0) {
                throw new AssertionError("read16 at step " + (cursor - 1));
            }
            return new org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16(step.values().get(1).longValue(), step.values().get(2).longValue());
        }

        @Override public void write16(long address, org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16 value) {
            Step step = next(Op.W128);
            if (step.values().size() != 3 || step.values().get(0).longValue() != address || step.values().get(1).longValue() != value.lowRaw64() || step.values().get(2).longValue() != value.highRaw64() || step.returned() != 0) {
                throw new AssertionError("write16 at step " + (cursor - 1));
            }
        }

        @Override public long range16Virtual8(Memory memory, long target, long rcx, long rdx, long r8, long r9) {
            return call(Op.RANGE16_ALLOC, memory, true, target, rcx, rdx, r8, r9);
        }

        @Override public void range16Virtual16(Memory memory, long target, long rcx, long rdx, long r8, long r9) {
            call(Op.RANGE16_FREE, memory, false, target, rcx, rdx, r8, r9);
        }

        @Override public void range16Direct8F8550(Memory memory, long rcx, long rdx, long r8, long r9) {
            call(Op.RANGE16_DIRECT, memory, false, rcx, rdx, r8, r9);
        }
    }
}