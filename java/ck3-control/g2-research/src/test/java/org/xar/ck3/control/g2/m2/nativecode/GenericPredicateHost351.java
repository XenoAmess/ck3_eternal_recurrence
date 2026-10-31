package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PredicateData351.Op;
import org.xar.ck3.control.g2.m2.nativecode.PredicateData351.Scene;
import org.xar.ck3.control.g2.m2.nativecode.PredicateData351.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedClassify3727580.Memory;

/** Generic host for PredicateData351 scenes. */
public final class GenericPredicateHost351 {
    private GenericPredicateHost351() { }

    public static int verify() {
        List<Scene> scenes = PredicateCases351.scenes();
        if (scenes.size() != 4) throw new AssertionError("exactly 4 scenes required");
        for (Scene scene : scenes) {
            if (scene.steps().size() > 128) throw new AssertionError("finite script 0..128");
            Script script = new Script(scene.steps());
            int actual = PendingEmbeddedClassify3727580.classify(script, scene.receiver());
            if (actual != scene.expectedAL()) throw new AssertionError("AL mismatch");
            if (script.cursor != scene.steps().size()) throw new AssertionError("unconsumed steps " + script.cursor);
        }
        return 4;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static final class Script implements Memory {
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

        @Override public int read8(long address) {
            Step step = read(Op.R8, address, 2);
            return step.values().get(1).intValue() & 0xFF;
        }

        @Override public int read32(long address) {
            Step step = read(Op.R32, address, 2);
            return step.values().get(1).intValue();
        }

        @Override public long read64(long address) {
            Step step = read(Op.R64, address, 2);
            return step.values().get(1).longValue();
        }
    }
}