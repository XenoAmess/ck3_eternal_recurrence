package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;
import java.util.List;
import java.util.ArrayList;

public final class RangeOrderHost410 {
    private RangeOrderHost410() { }

    public static int verify() {
        List<RangeOrderData410.Scene> scenes = RangeOrderCases410.scenes();
        if (scenes.size() != 7) {
            throw new AssertionError("Expected exactly 7 scenes");
        }
        int passCount = 0;
        for (RangeOrderData410.Scene scene : scenes) {
            if (scene.steps().size() > 512) {
                throw new AssertionError("Steps count exceeds 512");
            }
            Script script = new Script(scene.steps());
            if (scene.composition()) {
                RangeOrder410Api.Input input = new RangeOrder410Api.Input(scene.first(), scene.middle(), scene.last(), scene.moduleBase());
                long actualReturn = PendingRangeOrder9CF240.apply(script, script, input);
                if (actualReturn != scene.expectedReturn()) {
                    throw new AssertionError("Upper return mismatch");
                }
            } else {
                PendingByteReverse42208E8.reverse(script, script, scene.first(), scene.last(), scene.moduleBase());
                if (scene.expectedReturn() != 0L) {
                    throw new AssertionError("Leaf expected return must be 0");
                }
            }
            if (script.cursor != script.steps.size()) {
                throw new AssertionError("Unconsumed steps");
            }
            passCount++;
        }
        return passCount;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static class Script implements RangeOrder410Api.Memory, RangeOrder410Api.LoopBudget {
        private final List<RangeOrderData410.Step> steps;
        private int cursor = 0;

        Script(List<RangeOrderData410.Step> steps) {
            this.steps = List.copyOf(steps);
        }

        private RangeOrderData410.Step nextStep(RangeOrderData410.Op expectedOp) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Missing step");
            }
            RangeOrderData410.Step step = steps.get(cursor++);
            if (step.op() != expectedOp) {
                throw new AssertionError("Wrong op");
            }
            if (step.returned() != 0L) {
                throw new AssertionError("Step returned non-zero");
            }
            return step;
        }

        @Override
        public int read8(long address) {
            RangeOrderData410.Step step = nextStep(RangeOrderData410.Op.R8);
            List<Long> vals = step.values();
            if (vals.size() != 2) throw new AssertionError("R8 width mismatch");
            if (vals.get(0) != address) throw new AssertionError("R8 address mismatch");
            long bits = vals.get(1);
            if (bits < 0 || bits > 255) throw new AssertionError("R8 bits out of range");
            return (int) bits;
        }

        @Override
        public int read32(long address) {
            RangeOrderData410.Step step = nextStep(RangeOrderData410.Op.R32);
            List<Long> vals = step.values();
            if (vals.size() != 2) throw new AssertionError("R32 width mismatch");
            if (vals.get(0) != address) throw new AssertionError("R32 address mismatch");
            long bits = vals.get(1);
            if (bits < 0 || bits > 0xFFFFFFFFL) throw new AssertionError("R32 bits out of range");
            return (int) bits;
        }

        @Override
        public Bits128 read128(long address) {
            RangeOrderData410.Step step = nextStep(RangeOrderData410.Op.R128);
            List<Long> vals = step.values();
            if (vals.size() != 3) throw new AssertionError("R128 width mismatch");
            if (vals.get(0) != address) throw new AssertionError("R128 address mismatch");
            return new Bits128(vals.get(1), vals.get(2));
        }

        @Override
        public Bits256 read256(long address) {
            RangeOrderData410.Step step = nextStep(RangeOrderData410.Op.R256);
            List<Long> vals = step.values();
            if (vals.size() != 5) throw new AssertionError("R256 width mismatch");
            if (vals.get(0) != address) throw new AssertionError("R256 address mismatch");
            Bits128 low = new Bits128(vals.get(1), vals.get(2));
            Bits128 high = new Bits128(vals.get(3), vals.get(4));
            return new Bits256(low, high);
        }

        @Override
        public void write8(long address, int value) {
            RangeOrderData410.Step step = nextStep(RangeOrderData410.Op.W8);
            List<Long> vals = step.values();
            if (vals.size() != 2) throw new AssertionError("W8 width mismatch");
            if (vals.get(0) != address) throw new AssertionError("W8 address mismatch");
            long expected = (long) (value & 0xFF);
            if (vals.get(1) != expected) throw new AssertionError("W8 value mismatch");
        }

        @Override
        public void write128(long address, Bits128 value) {
            RangeOrderData410.Step step = nextStep(RangeOrderData410.Op.W128);
            List<Long> vals = step.values();
            if (vals.size() != 3) throw new AssertionError("W128 width mismatch");
            if (vals.get(0) != address) throw new AssertionError("W128 address mismatch");
            if (vals.get(1) != value.low()) throw new AssertionError("W128 low mismatch");
            if (vals.get(2) != value.high()) throw new AssertionError("W128 high mismatch");
        }

        @Override
        public void write256(long address, Bits256 value) {
            RangeOrderData410.Step step = nextStep(RangeOrderData410.Op.W256);
            List<Long> vals = step.values();
            if (vals.size() != 5) throw new AssertionError("W256 width mismatch");
            if (vals.get(0) != address) throw new AssertionError("W256 address mismatch");
            if (vals.get(1) != value.low128().low()) throw new AssertionError("W256 w0 mismatch");
            if (vals.get(2) != value.low128().high()) throw new AssertionError("W256 w1 mismatch");
            if (vals.get(3) != value.high128().low()) throw new AssertionError("W256 w2 mismatch");
            if (vals.get(4) != value.high128().high()) throw new AssertionError("W256 w3 mismatch");
        }

        @Override
        public void beforeStep(int headerRva, long frontPointer) {
            RangeOrderData410.Step step = nextStep(RangeOrderData410.Op.STEP);
            List<Long> vals = step.values();
            if (vals.size() != 2) throw new AssertionError("STEP width mismatch");
            long expectedRva = Integer.toUnsignedLong(headerRva);
            if (vals.get(0) != expectedRva) throw new AssertionError("STEP rva mismatch");
            if (vals.get(1) != frontPointer) throw new AssertionError("STEP front mismatch");
        }
    }
}