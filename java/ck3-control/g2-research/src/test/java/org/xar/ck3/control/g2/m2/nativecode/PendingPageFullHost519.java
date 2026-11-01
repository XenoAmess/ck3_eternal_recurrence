package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.PendingPageFullData519;
import org.xar.ck3.control.g2.m2.nativecode.FullPage495Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingPageReserveFullState2A321F0;

public final class PendingPageFullHost519 {
    private PendingPageFullHost519() { }

    public static void verify(PendingPageFullData519.Scene scene) {
        Objects.requireNonNull(scene);
        Objects.requireNonNull(scene.entry());
        Objects.requireNonNull(scene.steps());
        Objects.requireNonNull(scene.initialMemory());
        Objects.requireNonNull(scene.finalMemory());

        if (scene.steps().size() > 4096) {
            throw new AssertionError("Script too long");
        }

        boolean expectedStop = scene.expectedBudgetStop();
        boolean hasExpectedResult = scene.expectedResult() != null;

        if (expectedStop && hasExpectedResult) {
            throw new AssertionError("Expected stop cannot have result");
        }
        if (!expectedStop && !hasExpectedResult) {
            throw new AssertionError("Normal scene must have result");
        }

        List<PendingPageFullData519.Step> steps = scene.steps();
        int[] cursor = new int[1];
        Map<Long, Byte> bytes = new HashMap<>();

        // Seed initial memory (unlogged)
        for (PendingPageFullData519.Cell c : scene.initialMemory()) {
            seed(bytes, c.addressBits(), c.valueBits(), c.widthBytes());
        }

        // Create shared memory implementation
        MemoryImpl memory = new MemoryImpl(bytes, cursor, steps);

        // Create shared calls implementation
        CallsImpl calls = new CallsImpl(bytes, cursor, steps, memory);

        // Create budget implementation
        RuntimeException marker = new RuntimeException("BudgetStop");
        BudgetImpl budget = new BudgetImpl(cursor, steps, marker);

        // Create Input
        FullPage495Api.Input input = new FullPage495Api.Input(
            scene.entry(),
            scene.directionFlagSet(),
            budget
        );

        // Execute target
        FullCopy437Api.CallResult actualResult = null;
        boolean stopped = false;

        try {
            actualResult = PendingPageReserveFullState2A321F0.execute(input, memory, calls);
        } catch (RuntimeException e) {
            if (e == marker) {
                stopped = true;
            } else {
                throw e;
            }
        }

        // Verify script consumption
        if (cursor[0] != steps.size()) {
            throw new AssertionError("Script not fully consumed: " + cursor[0] + " of " + steps.size());
        }

        // Verify mode match
        if (expectedStop && !stopped) {
            throw new AssertionError("Expected stop but target returned normally");
        }
        if (!expectedStop && stopped) {
            throw new AssertionError("Unexpected stop");
        }

        // Verify result if normal
        if (!expectedStop) {
            if (!actualResult.equals(scene.expectedResult())) {
                throw new AssertionError("Result mismatch");
            }
        }

        // Verify final memory (unlogged)
        for (PendingPageFullData519.Cell c : scene.finalMemory()) {
            long actual = peek(bytes, c.addressBits(), c.widthBytes());
            if (actual != c.valueBits()) {
                throw new AssertionError("Final cell mismatch at " + Long.toHexString(c.addressBits()));
            }
        }
    }

    private static void seed(Map<Long, Byte> bytes, long address, long value, int width) {
        if (width == 1) {
            if (value < 0 || value > 0xFF) throw new AssertionError("Invalid seed width 1");
            bytes.put(address, (byte) value);
        } else if (width == 4) {
            if (value < 0 || value > 0xFFFFFFFFL) throw new AssertionError("Invalid seed width 4");
            for (int i = 0; i < 4; i++) {
                bytes.put(address + i, (byte) (value >>> (8 * i)));
            }
        } else if (width == 8) {
            for (int i = 0; i < 8; i++) {
                bytes.put(address + i, (byte) (value >>> (8 * i)));
            }
        } else {
            throw new AssertionError("Invalid seed width");
        }
    }

    private static long peek(Map<Long, Byte> bytes, long address, int width) {
        long value = 0;
        if (width == 1) {
            Byte b = bytes.get(address);
            if (b == null) throw new AssertionError("Unseeded byte at " + Long.toHexString(address));
            value = b & 0xFFL;
        } else if (width == 4) {
            for (int i = 0; i < 4; i++) {
                Byte b = bytes.get(address + i);
                if (b == null) throw new AssertionError("Unseeded byte at " + Long.toHexString(address + i));
                value |= (long) (b & 0xFF) << (8 * i);
            }
        } else if (width == 8) {
            for (int i = 0; i < 8; i++) {
                Byte b = bytes.get(address + i);
                if (b == null) throw new AssertionError("Unseeded byte at " + Long.toHexString(address + i));
                value |= (long) (b & 0xFF) << (8 * i);
            }
        } else {
            throw new AssertionError("Invalid peek width");
        }
        return value;
    }

    private static class MemoryImpl implements FullPage495Api.Memory {
        private final Map<Long, Byte> bytes;
        private final int[] cursor;
        private final List<PendingPageFullData519.Step> steps;

        MemoryImpl(Map<Long, Byte> bytes, int[] cursor, List<PendingPageFullData519.Step> steps) {
            this.bytes = bytes;
            this.cursor = cursor;
            this.steps = steps;
        }

        @Override
        public int readUnsignedByte(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            PendingPageFullData519.Step s = steps.get(cursor[0]++);
            if (!(s instanceof PendingPageFullData519.Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            PendingPageFullData519.Read r = (PendingPageFullData519.Read) s;
            if (r.widthBytes() != 1) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = peek(bytes, addressBits, 1);
            if (actual != r.valueBits()) throw new AssertionError("Value mismatch");
            return (int) actual;
        }

        @Override
        public int readDword(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            PendingPageFullData519.Step s = steps.get(cursor[0]++);
            if (!(s instanceof PendingPageFullData519.Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            PendingPageFullData519.Read r = (PendingPageFullData519.Read) s;
            if (r.widthBytes() != 4) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = peek(bytes, addressBits, 4);
            if (actual != r.valueBits()) throw new AssertionError("Value mismatch");
            return (int) actual;
        }

        @Override
        public long readQword(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            PendingPageFullData519.Step s = steps.get(cursor[0]++);
            if (!(s instanceof PendingPageFullData519.Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            PendingPageFullData519.Read r = (PendingPageFullData519.Read) s;
            if (r.widthBytes() != 8) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = peek(bytes, addressBits, 8);
            if (actual != r.valueBits()) throw new AssertionError("Value mismatch");
            return actual;
        }

        @Override
        public void writeByte(long addressBits, int lowByteBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            PendingPageFullData519.Step s = steps.get(cursor[0]++);
            if (!(s instanceof PendingPageFullData519.Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            PendingPageFullData519.Write w = (PendingPageFullData519.Write) s;
            if (w.widthBytes() != 1) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long val = lowByteBits & 0xFFL;
            if (val != w.valueBits()) throw new AssertionError("Value mismatch");
            bytes.put(addressBits, (byte) val);
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            PendingPageFullData519.Step s = steps.get(cursor[0]++);
            if (!(s instanceof PendingPageFullData519.Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            PendingPageFullData519.Write w = (PendingPageFullData519.Write) s;
            if (w.widthBytes() != 4) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long val = Integer.toUnsignedLong(valueBits);
            if (val != w.valueBits()) throw new AssertionError("Value mismatch");
            for (int i = 0; i < 4; i++) {
                bytes.put(addressBits + i, (byte) (val >>> (8 * i)));
            }
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            PendingPageFullData519.Step s = steps.get(cursor[0]++);
            if (!(s instanceof PendingPageFullData519.Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            PendingPageFullData519.Write w = (PendingPageFullData519.Write) s;
            if (w.widthBytes() != 8) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            if (valueBits != w.valueBits()) throw new AssertionError("Value mismatch");
            for (int i = 0; i < 8; i++) {
                bytes.put(addressBits + i, (byte) (valueBits >>> (8 * i)));
            }
        }

        @Override
        public int readUnsignedWord(long addressBits) {
            throw new UnsupportedOperationException("Unsupported readUnsignedWord");
        }

        @Override
        public void writeWord(long addressBits, int valueBits) {
            throw new UnsupportedOperationException("Unsupported writeWord");
        }

        @Override
        public Bits128 read128(long addressBits) {
            throw new UnsupportedOperationException("Unsupported read128");
        }

        @Override
        public void write128(long addressBits, Bits128 valueBits) {
            throw new UnsupportedOperationException("Unsupported write128");
        }

        @Override
        public void write128NonTemporal(long addressBits, Bits128 valueBits) {
            throw new UnsupportedOperationException("Unsupported write128NonTemporal");
        }

        @Override
        public FullCopy437Api.Bits256 read256(long addressBits) {
            throw new UnsupportedOperationException("Unsupported read256");
        }

        @Override
        public void write256(long addressBits, FullCopy437Api.Bits256 valueBits) {
            throw new UnsupportedOperationException("Unsupported write256");
        }

        @Override
        public void write256NonTemporal(long addressBits, FullCopy437Api.Bits256 valueBits) {
            throw new UnsupportedOperationException("Unsupported write256NonTemporal");
        }

        @Override
        public void sfence() {
            throw new UnsupportedOperationException("Unsupported sfence");
        }

        @Override
        public int lockedXaddDword(long addressBits, int addendBits) {
            throw new UnsupportedOperationException("Unsupported lockedXaddDword");
        }
    }

    private static class CallsImpl implements FullPage495Api.Calls {
        private final Map<Long, Byte> bytes;
        private final int[] cursor;
        private final List<PendingPageFullData519.Step> steps;
        private final MemoryImpl memory;

        CallsImpl(Map<Long, Byte> bytes, int[] cursor, List<PendingPageFullData519.Step> steps, MemoryImpl memory) {
            this.bytes = bytes;
            this.cursor = cursor;
            this.steps = steps;
            this.memory = memory;
        }

        @Override
        public FullCopy437Api.CallResult invoke(FullPage495Api.CallFrame frame) {
            if (cursor[0] >= steps.size()) {
                throw new AssertionError("Unexpected invoke: script exhausted");
            }
            PendingPageFullData519.Step step = steps.get(cursor[0]++);
            if (!(step instanceof PendingPageFullData519.Invoke)) {
                throw new AssertionError("Expected Invoke at cursor " + (cursor[0] - 1));
            }
            PendingPageFullData519.Invoke inv = (PendingPageFullData519.Invoke) step;

            if (!inv.frame().equals(frame)) {
                throw new AssertionError("CallFrame mismatch at cursor " + (cursor[0] - 1));
            }

            for (PendingPageFullData519.Write w : inv.effects()) {
                if (w.widthBytes() == 1) {
                    if (w.valueBits() < 0 || w.valueBits() > 0xFF) throw new AssertionError("Invalid effect width 1 value");
                    memory.writeByte(w.addressBits(), (int) w.valueBits());
                } else if (w.widthBytes() == 4) {
                    if (w.valueBits() < 0 || w.valueBits() > 0xFFFFFFFFL) throw new AssertionError("Invalid effect width 4 value");
                    memory.writeDword(w.addressBits(), (int) w.valueBits());
                } else if (w.widthBytes() == 8) {
                    memory.writeQword(w.addressBits(), w.valueBits());
                } else {
                    throw new AssertionError("Invalid effect width");
                }
            }

            return inv.result();
        }
    }

    private static class BudgetImpl implements GovernmentCrtBoundary185Api.LoopBudget {
        private final int[] cursor;
        private final List<PendingPageFullData519.Step> steps;
        private final RuntimeException marker;

        BudgetImpl(int[] cursor, List<PendingPageFullData519.Step> steps, RuntimeException marker) {
            this.cursor = cursor;
            this.steps = steps;
            this.marker = marker;
        }

        @Override
        public void beforeStep(long loopHeaderRva, long cursorBits) {
            if (cursor[0] >= steps.size()) {
                throw new AssertionError("Unexpected budget step: script exhausted");
            }
            PendingPageFullData519.Step step = steps.get(cursor[0]++);
            if (!(step instanceof PendingPageFullData519.Budget)) {
                throw new AssertionError("Expected Budget at cursor " + (cursor[0] - 1));
            }
            PendingPageFullData519.Budget b = (PendingPageFullData519.Budget) step;
            if (b.headerRva() != loopHeaderRva) {
                throw new AssertionError("Budget header mismatch");
            }
            if (b.guardAddressBits() != cursorBits) {
                throw new AssertionError("Budget guard mismatch");
            }
            if (b.stop()) {
                throw marker;
            }
        }
    }
}