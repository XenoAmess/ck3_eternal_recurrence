package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInitData291.Op;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInitData291.Scene;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInitData291.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedInit8895D0.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedInit8895D0.Calls;

/** Finite, globally ordered scripted callbacks; no default memory or target-derived expectations. */
public final class EmbeddedInitHost291 {
    private EmbeddedInitHost291() { }

    public static int verify() {
        List<Scene> scenes = EmbeddedInitCases291.scenes();
        if (scenes.size() != 1) throw new AssertionError("exactly one scene required");
        for (Scene scene : scenes) {
            if (scene.steps().isEmpty() || scene.steps().size() > 64) throw new AssertionError("finite script 1..64");
            Script script = new Script(scene.steps());
            long actual = PendingEmbeddedInit8895D0.initialize(script, script, scene.receiver(), scene.moduleBase());
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
            if (step.values().size() != width || step.values().get(0).longValue() != address) throw new AssertionError("read " + op + " at step " + (cursor - 1));
            return step;
        }

        private void write(Op op, Long... values) {
            Step step = next(op);
            if (!step.values().equals(List.of(values))) throw new AssertionError("write " + op + " at step " + (cursor - 1));
        }

        private long call(Op op, Memory memory, boolean returns, Long... values) {
            if (memory != this) throw new AssertionError("same Memory required");
            Step step = next(op);
            if (!step.values().equals(List.of(values))) throw new AssertionError("call " + op + " at step " + (cursor - 1));
            if (returns) {
                 // CALL10/CALL20 in this context do not return values in the provided interface,
                 // but the generic pattern expects handling if needed.
                 // The interface PendingEmbeddedInit8895D0.Calls has void returns.
                 // So we just validate.
            }
            return 0L;
        }

        @Override public long read64(long address) {
            Step step = read(Op.R64, address, 2);
            return step.values().get(1).longValue();
        }

        @Override public void write32(long address, int value) {
            write(Op.W32, address, Integer.toUnsignedLong(value));
        }

        @Override public void write64(long address, long value) {
            write(Op.W64, address, value);
        }

        @Override public void virtual10(Memory memory, long target, long rcx, long rdx, int r8d) {
            call(Op.CALL10, memory, false, target, rcx, rdx, Integer.toUnsignedLong(r8d));
        }

        @Override public void virtual20(Memory memory, long target, long rcx, long rdx, long r8) {
            call(Op.CALL20, memory, false, target, rcx, rdx, r8);
        }
    }
}