package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardData449;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardCases449;

public final class FullCopyBackwardWitness449 {
    private FullCopyBackwardWitness449() { }

    public static int verify() {
        List<FullCopyBackwardData449.Scene> scenes = FullCopyBackwardCases449.scenes();
        if (scenes.size() != 3) throw new IllegalArgumentException("Expected 3 scenes");

        long[] counts = new long[3];
        for (int i = 0; i < 3; i++) {
            counts[i] = scenes.get(i).count();
        }
        if (counts[0] != 33 || counts[1] != 273 || counts[2] != 529) {
            throw new IllegalArgumentException("Invalid counts");
        }
        if (counts[0] == counts[1] || counts[1] == counts[2] || counts[0] == counts[2]) {
            throw new IllegalArgumentException("Duplicate counts");
        }

        for (FullCopyBackwardData449.Scene scene : scenes) {
            if (scene.steps().size() > 512) throw new IllegalArgumentException("Step limit exceeded");
            validateScene(scene);
        }
        return 3;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static void validateScene(FullCopyBackwardData449.Scene scene) {
        Script script = new Script(scene.steps());

        // Seed owned regions
        long B = FullCopyBackwardData449.B;
        long E = FullCopyBackwardData449.E;
        long RET = FullCopyBackwardData449.RET;

        for (int i = 0; i < 1024; i++) {
            script.seedByte(B + i, (byte)((B + i - B) & 255));
        }
        script.seedQword(E, RET);

        // Construct Input
        VolatileBits v = FullCopyBackwardData449.incoming(scene.count());
        NonvolatileBits n = FullCopyBackwardData449.nonvolatile();

        GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
            FullCopyBackwardData449.M,
            FullCopyBackwardData449.E,
            v,
            n
        );

        boolean directionFlagSet = false;

        FullCopy437Api.Input input = new FullCopy437Api.Input(
            entry,
            directionFlagSet,
            script
        );

        // Execute Target
        FullCopy437Api.CallResult result = FullCopyBackward446.execute(input, script);

        // Validate Result
        if (!result.equals(scene.expected())) {
            throw new AssertionError("CallResult mismatch");
        }

        // Validate Trace
        if (script.cursor != scene.steps().size()) {
            throw new AssertionError("Step count mismatch");
        }
    }

    private static final class Script implements FullCopy437Api.Memory, GovernmentCrtBoundary185Api.LoopBudget {
        private final Map<Long, Byte> storage = new HashMap<>();
        private int cursor = 0;
        private final List<FullCopyBackwardData449.Step> expectedSteps;
        private final int maxSteps = 512;

        private Script(List<FullCopyBackwardData449.Step> expectedSteps) {
            this.expectedSteps = List.copyOf(expectedSteps);
        }

        private void seedByte(long address, byte value) {
            storage.put(address, value);
        }

        private void seedQword(long address, long value) {
            for (int i = 0; i < 8; i++) {
                storage.put(address + i, (byte)(value >>> (8 * i)));
            }
        }

        private byte getByte(long address) {
            Byte b = storage.get(address);
            if (b == null) throw new AssertionError("Missing backing byte at " + Long.toHexString(address));
            return b;
        }

        private long readQwordInternal(long address) {
            long val = 0;
            for (int i = 0; i < 8; i++) {
                val |= ((long)(getByte(address + i) & 255)) << (8 * i);
            }
            return val;
        }

        private Bits128 read128Internal(long address) {
            long low = 0;
            long high = 0;
            for (int i = 0; i < 8; i++) {
                low |= ((long)(getByte(address + i) & 255)) << (8 * i);
            }
            for (int i = 0; i < 8; i++) {
                high |= ((long)(getByte(address + 8 + i) & 255)) << (8 * i);
            }
            return new Bits128(low, high);
        }

        private void write128Internal(long address, Bits128 value) {
            long low = value.lowBits();
            long high = value.highBits();
            for (int i = 0; i < 8; i++) {
                storage.put(address + i, (byte)(low >>> (8 * i)));
            }
            for (int i = 0; i < 8; i++) {
                storage.put(address + 8 + i, (byte)(high >>> (8 * i)));
            }
        }

        private void checkStep(FullCopyBackwardData449.Op op, List<Long> values) {
            if (cursor >= expectedSteps.size()) throw new AssertionError("Unexpected step");
            if (cursor >= maxSteps) throw new AssertionError("Max steps exceeded");

            FullCopyBackwardData449.Step expected = expectedSteps.get(cursor);
            if (expected.op() != op) throw new AssertionError("Op mismatch at " + cursor);
            if (expected.values().size() != values.size()) throw new AssertionError("Arity mismatch at " + cursor);

            for (int i = 0; i < values.size(); i++) {
                if (!expected.values().get(i).equals(values.get(i))) {
                    throw new AssertionError("Value mismatch at " + cursor + " index " + i);
                }
            }
            cursor++;
        }

        @Override
        public int readDword(long addressBits) {
            throw new UnsupportedOperationException("readDword not used");
        }

        @Override
        public long readQword(long addressBits) {
            long val = readQwordInternal(addressBits);
            checkStep(FullCopyBackwardData449.Op.R64, List.of(addressBits, val));
            return val;
        }

        @Override
        public int readUnsignedByte(long addressBits) {
            throw new UnsupportedOperationException("readUnsignedByte not used");
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            throw new UnsupportedOperationException("writeDword not used");
        }

        @Override
        public int lockedXaddDword(long addressBits, int addendBits) {
            throw new UnsupportedOperationException("lockedXaddDword not used");
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            throw new UnsupportedOperationException("writeQword not used");
        }

        @Override
        public void writeByte(long addressBits, int lowByteBits) {
            throw new UnsupportedOperationException("writeByte not used");
        }

        @Override
        public Bits128 read128(long addressBits) {
            Bits128 val = read128Internal(addressBits);
            checkStep(FullCopyBackwardData449.Op.R128, List.of(addressBits, val.lowBits(), val.highBits()));
            return val;
        }

        @Override
        public void write128(long addressBits, Bits128 valueBits) {
            checkStep(FullCopyBackwardData449.Op.W128, List.of(addressBits, valueBits.lowBits(), valueBits.highBits()));
            write128Internal(addressBits, valueBits);
        }

        @Override
        public void writeWord(long addressBits, int valueBits) {
            throw new UnsupportedOperationException("writeWord not used");
        }

        @Override
        public void write128NonTemporal(long addressBits, Bits128 valueBits) {
            throw new UnsupportedOperationException("write128NonTemporal not used");
        }

        @Override
        public void sfence() {
            throw new UnsupportedOperationException("sfence not used");
        }

        @Override
        public int readUnsignedWord(long addressBits) {
            throw new UnsupportedOperationException("readUnsignedWord not used");
        }

        @Override
        public FullCopy437Api.Bits256 read256(long addressBits) {
            throw new UnsupportedOperationException("read256 not used");
        }

        @Override
        public void write256(long addressBits, FullCopy437Api.Bits256 valueBits) {
            throw new UnsupportedOperationException("write256 not used");
        }

        @Override
        public void write256NonTemporal(long addressBits, FullCopy437Api.Bits256 valueBits) {
            throw new UnsupportedOperationException("write256NonTemporal not used");
        }

        @Override
        public void beforeStep(long loopHeaderRva, long guardAddressBits) {
            checkStep(FullCopyBackwardData449.Op.STEP, List.of(loopHeaderRva, guardAddressBits));
        }
    }
}