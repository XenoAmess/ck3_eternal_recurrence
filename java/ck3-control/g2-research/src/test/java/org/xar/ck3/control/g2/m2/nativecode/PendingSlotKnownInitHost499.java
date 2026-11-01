package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotFullProducerData489.Cell;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotFullProducerData489.Read;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotFullProducerData489.Write;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotFullProducerData489.Invoke;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotFullProducerData489.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotFullProducerData489.Scene;
import org.xar.ck3.control.g2.m2.nativecode.FullSlotProducer479Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotProducerFullState2A32770;

public final class PendingSlotKnownInitHost499 {
    private PendingSlotKnownInitHost499() { }

    public static void verify(Scene scene) {
        Objects.requireNonNull(scene);
        Objects.requireNonNull(scene.entry());
        Objects.requireNonNull(scene.steps());
        Objects.requireNonNull(scene.expectedResult());
        Objects.requireNonNull(scene.finalMemory());

        if (scene.steps().size() > 512) {
            throw new AssertionError("Script too long");
        }

        List<Step> steps = scene.steps();
        int[] cursor = new int[1]; // Single global cursor holder

        // Validate initial cells
        for (Cell c : scene.initialMemory()) {
            if (c.widthBytes() != 1 && c.widthBytes() != 4 && c.widthBytes() != 8) {
                throw new AssertionError("Invalid initial cell width");
            }
            if (c.widthBytes() == 1 && (c.valueBits() < 0 || c.valueBits() > 0xFF)) {
                throw new AssertionError("Invalid initial cell value width 1");
            }
            if (c.widthBytes() == 4 && (c.valueBits() < 0 || c.valueBits() > 0xFFFFFFFFL)) {
                throw new AssertionError("Invalid initial cell value width 4");
            }
        }

        // Create Memory implementation sharing the cursor
        MemoryImpl memory = new MemoryImpl(steps, cursor);

        // Seed initial memory (unlogged)
        for (Cell c : scene.initialMemory()) {
            memory.seed(c.addressBits(), c.valueBits(), c.widthBytes());
        }

        // Create Calls adapter sharing the cursor and memory
        FullSlotProducer479Api.Calls calls = new CallsImpl(steps, cursor, memory);

        // Create throwing LoopBudget
        GovernmentCrtBoundary185Api.LoopBudget budget = new GovernmentCrtBoundary185Api.LoopBudget() {
            @Override
            public void beforeStep(long loopHeaderRva, long cursorBits) {
                throw new AssertionError("Unexpected budget step");
            }
        };

        // Create Input
        FullSlotProducer479Api.Input input = new FullSlotProducer479Api.Input(
            scene.entry(),
            scene.directionFlagSet(),
            budget
        );

        // Execute target
        FullCopy437Api.CallResult actualResult = PendingSlotProducerWithKnownInit497.execute(input, memory, calls);

        // Verify script consumption
        if (cursor[0] != steps.size()) {
            throw new AssertionError("Script not fully consumed: " + cursor[0] + " of " + steps.size());
        }

        // Verify result
        if (!actualResult.equals(scene.expectedResult())) {
            throw new AssertionError("Result mismatch");
        }

        // Verify final cells
        for (Cell c : scene.finalMemory()) {
            if (c.widthBytes() != 1 && c.widthBytes() != 4 && c.widthBytes() != 8) {
                throw new AssertionError("Invalid final cell width");
            }
            if (c.widthBytes() == 1 && (c.valueBits() < 0 || c.valueBits() > 0xFF)) {
                throw new AssertionError("Invalid final cell value width 1");
            }
            if (c.widthBytes() == 4 && (c.valueBits() < 0 || c.valueBits() > 0xFFFFFFFFL)) {
                throw new AssertionError("Invalid final cell value width 4");
            }
            long actual = memory.readRaw(c.addressBits(), c.widthBytes());
            if (actual != c.valueBits()) {
                throw new AssertionError("Final cell mismatch at " + Long.toHexString(c.addressBits()));
            }
        }
    }

    private static class MemoryImpl implements FullSlotProducer479Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Step> steps;
        private final int[] cursor;

        MemoryImpl(List<Step> steps, int[] cursor) {
            this.steps = steps;
            this.cursor = cursor;
        }

        void seed(long address, long value, int width) {
            for (int i = 0; i < width; i++) {
                bytes.put(address + i, (byte) (value >>> (8 * i)));
            }
        }

        long readRaw(long address, int width) {
            long result = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(address + i);
                if (b == null) {
                    throw new AssertionError("Unseeded byte at " + Long.toHexString(address + i));
                }
                result |= (long) (b & 0xFF) << (8 * i);
            }
            return result;
        }

        void writeRaw(long address, long value, int width) {
            for (int i = 0; i < width; i++) {
                bytes.put(address + i, (byte) (value >>> (8 * i)));
            }
        }

        @Override
        public int readUnsignedByte(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            Read r = (Read) s;
            if (r.widthBytes() != 1) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = readRaw(addressBits, 1);
            if (actual != r.valueBits()) throw new AssertionError("Value mismatch");
            return (int) actual;
        }

        @Override
        public int readDword(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            Read r = (Read) s;
            if (r.widthBytes() != 4) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = readRaw(addressBits, 4);
            if (actual != r.valueBits()) throw new AssertionError("Value mismatch");
            return (int) actual;
        }

        @Override
        public long readQword(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            Read r = (Read) s;
            if (r.widthBytes() != 8) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = readRaw(addressBits, 8);
            if (actual != r.valueBits()) throw new AssertionError("Value mismatch");
            return actual;
        }

        @Override
        public void writeByte(long addressBits, int valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            if (w.widthBytes() != 1) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long normalized = Integer.toUnsignedLong(valueBits) & 0xFFL;
            if (normalized != w.valueBits()) throw new AssertionError("Value mismatch");
            writeRaw(addressBits, normalized, 1);
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            if (w.widthBytes() != 4) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long normalized = Integer.toUnsignedLong(valueBits);
            if (normalized != w.valueBits()) throw new AssertionError("Value mismatch");
            writeRaw(addressBits, normalized, 4);
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            if (w.widthBytes() != 8) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            if (valueBits != w.valueBits()) throw new AssertionError("Value mismatch");
            writeRaw(addressBits, valueBits, 8);
        }

        @Override
        public int read8(long address) {
            return readUnsignedByte(address);
        }

        @Override
        public int read32(long address) {
            return readDword(address);
        }

        @Override
        public long read64(long address) {
            return readQword(address);
        }

        @Override
        public void write32(long address, int value) {
            writeDword(address, value);
        }

        @Override
        public void write64(long address, long value) {
            writeQword(address, value);
        }

        @Override
        public void write8(long address, int value) {
            writeByte(address, value);
        }

        @Override
        public int readUnsignedWord(long addressBits) {
            throw new UnsupportedOperationException("Unsupported readUnsignedWord");
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
        public void writeWord(long addressBits, int valueBits) {
            throw new UnsupportedOperationException("Unsupported writeWord");
        }

        @Override
        public void write128NonTemporal(long addressBits, Bits128 valueBits) {
            throw new UnsupportedOperationException("Unsupported write128NonTemporal");
        }

        @Override
        public void sfence() {
            throw new UnsupportedOperationException("Unsupported sfence");
        }

        @Override
        public int lockedXaddDword(long addressBits, int addendBits) {
            throw new UnsupportedOperationException("Unsupported lockedXaddDword");
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
    }

    private static class CallsImpl implements FullSlotProducer479Api.Calls {
        private final List<Step> steps;
        private final int[] cursor;
        private final MemoryImpl memory;

        CallsImpl(List<Step> steps, int[] cursor, MemoryImpl memory) {
            this.steps = steps;
            this.cursor = cursor;
            this.memory = memory;
        }

        @Override
        public FullCopy437Api.CallResult invoke(FullSlotProducer479Api.CallFrame frame) {
            if (cursor[0] >= steps.size()) {
                throw new AssertionError("Unexpected invoke: script exhausted");
            }
            Step step = steps.get(cursor[0]++);
            if (!(step instanceof Invoke)) {
                throw new AssertionError("Expected Invoke at cursor " + (cursor[0] - 1));
            }
            Invoke inv = (Invoke) step;

            if (!inv.frame().equals(frame)) {
                throw new AssertionError("CallFrame mismatch at cursor " + (cursor[0] - 1));
            }

            for (Write w : inv.effects()) {
                if (w.widthBytes() == 1 && (w.valueBits() < 0 || w.valueBits() > 0xFFL)) {
                    throw new AssertionError("Invalid effect value width 1");
                }
                if (w.widthBytes() == 4 && (w.valueBits() < 0 || w.valueBits() > 0xFFFFFFFFL)) {
                    throw new AssertionError("Invalid effect value width 4");
                }
                // The same logged write below alone consumes this effect's next global Write.
                if (w.widthBytes() == 1) {
                    memory.writeByte(w.addressBits(), (int) w.valueBits());
                } else if (w.widthBytes() == 4) {
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
}