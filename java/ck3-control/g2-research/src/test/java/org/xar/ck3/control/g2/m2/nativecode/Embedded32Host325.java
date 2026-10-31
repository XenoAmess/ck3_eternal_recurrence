package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32Data325.Op;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32Data325.Scene;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32Data325.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbedded32Copy3727180.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbedded32Copy3727180.Calls;

/** Generic host for Embedded32Data325 scenes. */
public final class Embedded32Host325 {
    private Embedded32Host325() { }

    public static int verify() {
        List<Scene> scenes = Embedded32Cases325.scenes();
        if (scenes.size() != 4) throw new AssertionError("exactly 4 scenes required");
        for (Scene scene : scenes) {
            if (scene.steps().size() > 128) throw new AssertionError("finite script 0..128");
            Script script = new Script(scene.steps());
            long actual = PendingEmbedded32Copy3727180.copy(script, script, scene.destination(), scene.source(), scene.moduleBase());
            if (actual != scene.expectedReturn()) throw new AssertionError("full64 return");
            if (script.cursor != scene.steps().size()) throw new AssertionError("unconsumed steps " + script.cursor);
        }
        return 4;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static final class Script implements Memory, Calls {
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

        @Override public int read32(long address) {
            Step step = read(Op.R32, address, 2);
            return step.values().get(1).intValue();
        }

        @Override public long read64(long address) {
            Step step = read(Op.R64, address, 2);
            return step.values().get(1).longValue();
        }

        @Override public Bits128 read128(long address) {
            Step step = read(Op.R128, address, 3);
            return new Bits128(step.values().get(1).longValue(), step.values().get(2).longValue());
        }

        @Override public void write32(long address, int value) {
            write(Op.W32, address, Integer.toUnsignedLong(value));
        }

        @Override public void write64(long address, long value) {
            write(Op.W64, address, value);
        }

        @Override public void write128(long address, Bits128 value) {
            write(Op.W128, address, value.low(), value.high());
        }

        @Override public void prepare889660(Memory memory, long rcx) {
            call(Op.PREP, memory, false, rcx);
        }

        @Override public long allocate(Memory memory, long target, long rcx, long rdx, int r8d) {
            return call(Op.ALLOC, memory, true, target, rcx, rdx, Integer.toUnsignedLong(r8d));
        }

        @Override public void replace8874D0(Memory memory, long rcx, long rdx, int r8d, int r9d) {
            call(Op.REPLACE, memory, false, rcx, rdx, Integer.toUnsignedLong(r8d), Integer.toUnsignedLong(r9d));
        }

        @Override public void virtualDestroy(Memory memory, long target, long rcx, long rdx) {
            call(Op.DESTROY, memory, false, target, rcx, rdx);
        }

        @Override public void copy37282B0(Memory memory, long rcx, long rdx) {
            call(Op.COPY37282, memory, false, rcx, rdx);
        }

        @Override public void finalize3727EC0(Memory memory, long rcx) {
            call(Op.FINALIZE, memory, false, rcx);
        }
    }
}