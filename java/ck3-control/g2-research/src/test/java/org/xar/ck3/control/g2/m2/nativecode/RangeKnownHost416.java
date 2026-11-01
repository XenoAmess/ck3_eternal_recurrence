package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;

public final class RangeKnownHost416 {
    private RangeKnownHost416() { }

    public static int verify() {
        List<RangeKnownData416.Scene> scenes = RangeKnownCases416.scenes();
        if (scenes.size() != 1) {
            throw new AssertionError("Expected exactly 1 scene");
        }
        RangeKnownData416.Scene scene = scenes.get(0);
        List<RangeKnownData416.Step> steps = List.copyOf(scene.steps());
        if (steps.size() > 512) {
            throw new AssertionError("Too many steps");
        }

        Script script = new Script(steps);
        PendingContextRangeWithKnownOrderBCB7C0.insert(script, script, script, scene.input());

        if (script.cursor != steps.size()) {
            throw new AssertionError("Incomplete script consumption");
        }
        return 1;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static final class Script implements PendingContextRangeWithKnownOrderBCB7C0.Memory, PendingContextRangeWithKnownOrderBCB7C0.Calls, RangeOrder410Api.LoopBudget {
        private final List<RangeKnownData416.Step> steps;
        private int cursor = 0;

        Script(List<RangeKnownData416.Step> steps) {
            this.steps = steps;
        }

        private RangeKnownData416.Step nextStep(RangeKnownData416.Op op, int arity) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Unexpected call: no more steps");
            }
            RangeKnownData416.Step step = steps.get(cursor);
            if (step.op() != op) {
                throw new AssertionError("Unexpected op: expected " + op + " got " + step.op());
            }
            if (step.values().size() != arity) {
                throw new AssertionError("Unexpected arity: expected " + arity + " got " + step.values().size());
            }
            if (step.returned() != 0) {
                throw new AssertionError("Unexpected returned: expected 0 got " + step.returned());
            }
            cursor++;
            return step;
        }

        private void checkAddress(RangeKnownData416.Step step, long address) {
            if (step.values().get(0) != address) {
                throw new AssertionError("Unexpected address: expected " + step.values().get(0) + " got " + address);
            }
        }

        @Override
        public int read8(long address) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.R8, 2);
            checkAddress(step, address);
            long val = step.values().get(1);
            if (val < 0 || val > 255) {
                throw new AssertionError("Invalid R8 value: " + val);
            }
            return (int) val;
        }

        @Override
        public int read16(long address) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.R16, 2);
            checkAddress(step, address);
            long val = step.values().get(1);
            if (val < 0 || val > 65535) {
                throw new AssertionError("Invalid R16 value: " + val);
            }
            return (int) val;
        }

        @Override
        public int read32(long address) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.R32, 2);
            checkAddress(step, address);
            long val = step.values().get(1);
            if (val < 0 || val > 0xFFFFFFFFL) {
                throw new AssertionError("Invalid R32 value: " + val);
            }
            return (int) val;
        }

        @Override
        public long read64(long address) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.R64, 2);
            checkAddress(step, address);
            return step.values().get(1);
        }

        @Override
        public Bits128 read128(long address) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.R128, 3);
            checkAddress(step, address);
            return new Bits128(step.values().get(1), step.values().get(2));
        }

        @Override
        public Bits256 read256(long address) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.R256, 5);
            checkAddress(step, address);
            Bits128 low = new Bits128(step.values().get(1), step.values().get(2));
            Bits128 high = new Bits128(step.values().get(3), step.values().get(4));
            return new Bits256(low, high);
        }

        @Override
        public void write8(long address, int value) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.W8, 2);
            checkAddress(step, address);
            long val = step.values().get(1);
            if (val < 0 || val > 255) {
                throw new AssertionError("Invalid W8 value: " + val);
            }
            if (val != (value & 0xFF)) {
                throw new AssertionError("Unexpected W8 value: expected " + val + " got " + (value & 0xFF));
            }
        }

        @Override
        public void write16(long address, int value) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.W16, 2);
            checkAddress(step, address);
            long val = step.values().get(1);
            if (val < 0 || val > 65535) {
                throw new AssertionError("Invalid W16 value: " + val);
            }
            if (val != (value & 0xFFFF)) {
                throw new AssertionError("Unexpected W16 value: expected " + val + " got " + (value & 0xFFFF));
            }
        }

        @Override
        public void write32(long address, int value) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.W32, 2);
            checkAddress(step, address);
            long val = step.values().get(1);
            if (val < 0 || val > 0xFFFFFFFFL) {
                throw new AssertionError("Invalid W32 value: " + val);
            }
            if (val != Integer.toUnsignedLong(value)) {
                throw new AssertionError("Unexpected W32 value: expected " + val + " got " + Integer.toUnsignedLong(value));
            }
        }

        @Override
        public void write64(long address, long value) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.W64, 2);
            checkAddress(step, address);
            long val = step.values().get(1);
            if (val != value) {
                throw new AssertionError("Unexpected W64 value: expected " + val + " got " + value);
            }
        }

        @Override
        public void write128(long address, Bits128 value) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.W128, 3);
            checkAddress(step, address);
            if (step.values().get(1) != value.low() || step.values().get(2) != value.high()) {
                throw new AssertionError("Unexpected W128 value");
            }
        }

        @Override
        public void write256(long address, Bits256 value) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.W256, 5);
            checkAddress(step, address);
            if (step.values().get(1) != value.low128().low() || step.values().get(2) != value.low128().high() ||
                step.values().get(3) != value.high128().low() || step.values().get(4) != value.high128().high()) {
                throw new AssertionError("Unexpected W256 value");
            }
        }

        @Override
        public void storeFence() {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.FENCE, 0);
        }

        @Override
        public void beforeStep(int headerRva, long frontPointer) {
            RangeKnownData416.Step step = nextStep(RangeKnownData416.Op.STEP, 2);
            if (step.values().get(0) != Integer.toUnsignedLong(headerRva)) {
                throw new AssertionError("Unexpected STEP headerRva");
            }
            if (step.values().get(1) != frontPointer) {
                throw new AssertionError("Unexpected STEP frontPointer");
            }
        }

        @Override
        public long allocate(PendingContextRangeWithKnownOrderBCB7C0.Memory memory, long target, long rcx, long rdx, int r8d) {
            throw new AssertionError("allocate called unexpectedly");
        }

        @Override
        public void release(PendingContextRangeWithKnownOrderBCB7C0.Memory memory, long target, long rcx, long rdx, int r8d) {
            throw new AssertionError("release called unexpectedly");
        }
    }
}