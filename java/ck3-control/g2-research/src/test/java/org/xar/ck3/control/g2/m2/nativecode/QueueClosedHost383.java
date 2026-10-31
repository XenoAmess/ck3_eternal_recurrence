package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.QueueClosedData383.Op;
import org.xar.ck3.control.g2.m2.nativecode.QueueClosedData383.Scene;
import org.xar.ck3.control.g2.m2.nativecode.QueueClosedData383.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingQueueUpdateWithKnownCopy3727EC0.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingQueueUpdateWithKnownCopy3727EC0.Calls;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;

/** Generic strict script host for QueueClosedData383 scenes. */
public final class QueueClosedHost383 {
    private QueueClosedHost383() { }

    public static int verify() {
        List<Scene> scenes = QueueClosedCases383.scenes();
        if (scenes.size() != 1) throw new AssertionError("exactly 1 scene required");
        for (Scene scene : scenes) {
            if (scene.steps().size() > 128) throw new AssertionError("finite script 0..128");
            Script script = new Script(scene.steps());
            PendingQueueUpdateWithKnownCopy3727EC0.update(script, script, scene.receiver(), scene.moduleBase(), scene.stackSlot());
            if (script.cursor != scene.steps().size()) throw new AssertionError("unconsumed steps " + script.cursor);
        }
        return 1;
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

        @Override public int read8(long address) {
            Step step = read(Op.R8, address, 2);
            return step.values().get(1).intValue();
        }

        @Override public int read16(long address) {
            Step step = read(Op.R16, address, 2);
            return step.values().get(1).intValue();
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

        @Override public Bits256 read256(long address) {
            Step step = read(Op.R256, address, 5);
            return new Bits256(new Bits128(step.values().get(1).longValue(), step.values().get(2).longValue()), new Bits128(step.values().get(3).longValue(), step.values().get(4).longValue()));
        }

        @Override public void write8(long address, int value) {
            write(Op.W8, address, Integer.toUnsignedLong(value) & 0xFFL);
        }

        @Override public void write16(long address, int value) {
            write(Op.W16, address, Integer.toUnsignedLong(value) & 0xFFFFL);
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

        @Override public void write256(long address, Bits256 value) {
            write(Op.W256, address, value.low128().low(), value.low128().high(), value.high128().low(), value.high128().high());
        }

        @Override public void storeFence() {
            Step step = next(Op.FENCE);
            if (!step.values().isEmpty() || step.returned() != 0) throw new AssertionError("fence at step " + (cursor - 1));
        }

        @Override public int compareExchange32(long address, int expected, int desired) {
            Step step = next(Op.CAS);
            if (step.values().size() != 3 || step.values().get(0).longValue() != address || step.values().get(1).longValue() != Integer.toUnsignedLong(expected) || step.values().get(2).longValue() != Integer.toUnsignedLong(desired)) {
                throw new AssertionError("CAS at step " + (cursor - 1));
            }
            return (int) step.returned();
        }

        @Override public void pause(Memory memory) {
            call(Op.PAUSE, memory, false);
        }

        @Override public long allocate(Memory memory, long target, long rcx, long rdx, int r8d) {
            return call(Op.ALLOC, memory, true, target, rcx, rdx, Integer.toUnsignedLong(r8d));
        }

        @Override public void release(Memory memory, long target, long rcx, long rdx, int r8d) {
            call(Op.FREE, memory, false, target, rcx, rdx, Integer.toUnsignedLong(r8d));
        }
    }
}