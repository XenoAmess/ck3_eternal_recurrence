package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextFullData507.Cell;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextFullData507.Read;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextFullData507.Write;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextFullData507.Invoke;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextFullData507.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextFullData507.Scene;
import org.xar.ck3.control.g2.m2.nativecode.FullContext493Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopyFullState3076B60;

public final class PendingContextFullHost507 {
    private PendingContextFullHost507() { }

    public static void verify(Scene scene) {
        Objects.requireNonNull(scene);
        Objects.requireNonNull(scene.entry());
        Objects.requireNonNull(scene.steps());
        Objects.requireNonNull(scene.expectedResult());
        Objects.requireNonNull(scene.finalMemory());
        Objects.requireNonNull(scene.initialMemory());

        if (scene.steps().size() > 512) {
            throw new AssertionError("Script too long");
        }

        List<Step> steps = scene.steps();
        int[] cursor = new int[1];

        MemoryImpl memory = new MemoryImpl(steps, cursor);

        for (Cell c : scene.initialMemory()) {
            memory.seed(c.addressBits(), c.valueBits(), c.widthBytes());
        }

        FullContext493Api.Calls calls = new CallsImpl(steps, cursor, memory);

        GovernmentCrtBoundary185Api.LoopBudget budget = new GovernmentCrtBoundary185Api.LoopBudget() {
            @Override
            public void beforeStep(long loopHeaderRva, long cursorBits) {
                throw new AssertionError("Unexpected budget step");
            }
        };

        FullContext493Api.Input input = new FullContext493Api.Input(
            scene.entry(),
            scene.directionFlagSet(),
            budget
        );

        FullCopy437Api.CallResult actualResult = PendingContextCopyFullState3076B60.execute(input, memory, calls);

        if (cursor[0] != steps.size()) {
            throw new AssertionError("Script not fully consumed: " + cursor[0] + " of " + steps.size());
        }

        if (!actualResult.equals(scene.expectedResult())) {
            throw new AssertionError("Result mismatch");
        }

        for (Cell c : scene.finalMemory()) {
            Bits128 actual = memory.readRawBits(c.addressBits(), c.widthBytes());
            if (!actual.equals(c.valueBits())) {
                throw new AssertionError("Final cell mismatch at " + Long.toHexString(c.addressBits()));
            }
        }
    }

    private static class MemoryImpl implements FullContext493Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Step> steps;
        private final int[] cursor;

        MemoryImpl(List<Step> steps, int[] cursor) {
            this.steps = steps;
            this.cursor = cursor;
        }

        void seed(long address, Bits128 value, int width) {
            if (width == 4) {
                if (value.highBits() != 0) throw new AssertionError("Invalid seed width 4 high bits");
                long low = value.lowBits();
                if (low < 0 || low > 0xFFFFFFFFL) throw new AssertionError("Invalid seed width 4 low bits");
                for (int i = 0; i < 4; i++) {
                    bytes.put(address + i, (byte) (low >>> (8 * i)));
                }
            } else if (width == 8) {
                if (value.highBits() != 0) throw new AssertionError("Invalid seed width 8 high bits");
                long low = value.lowBits();
                for (int i = 0; i < 8; i++) {
                    bytes.put(address + i, (byte) (low >>> (8 * i)));
                }
            } else if (width == 16) {
                long low = value.lowBits();
                long high = value.highBits();
                for (int i = 0; i < 8; i++) {
                    bytes.put(address + i, (byte) (low >>> (8 * i)));
                }
                for (int i = 0; i < 8; i++) {
                    bytes.put(address + 8 + i, (byte) (high >>> (8 * i)));
                }
            } else {
                throw new AssertionError("Invalid seed width");
            }
        }

        Bits128 readRawBits(long address, int width) {
            long low = 0;
            long high = 0;
            if (width == 4) {
                for (int i = 0; i < 4; i++) {
                    Byte b = bytes.get(address + i);
                    if (b == null) throw new AssertionError("Unseeded byte at " + Long.toHexString(address + i));
                    low |= (long) (b & 0xFF) << (8 * i);
                }
                return new Bits128(low, 0);
            } else if (width == 8) {
                for (int i = 0; i < 8; i++) {
                    Byte b = bytes.get(address + i);
                    if (b == null) throw new AssertionError("Unseeded byte at " + Long.toHexString(address + i));
                    low |= (long) (b & 0xFF) << (8 * i);
                }
                return new Bits128(low, 0);
            } else if (width == 16) {
                for (int i = 0; i < 8; i++) {
                    Byte b = bytes.get(address + i);
                    if (b == null) throw new AssertionError("Unseeded byte at " + Long.toHexString(address + i));
                    low |= (long) (b & 0xFF) << (8 * i);
                }
                for (int i = 0; i < 8; i++) {
                    Byte b = bytes.get(address + 8 + i);
                    if (b == null) throw new AssertionError("Unseeded byte at " + Long.toHexString(address + 8 + i));
                    high |= (long) (b & 0xFF) << (8 * i);
                }
                return new Bits128(low, high);
            }
            throw new AssertionError("Invalid read width");
        }

        void writeRawBits(long address, Bits128 value, int width) {
            if (width == 4) {
                if (value.highBits() != 0) throw new AssertionError("Invalid write width 4 high bits");
                long low = value.lowBits();
                if (low < 0 || low > 0xFFFFFFFFL) throw new AssertionError("Invalid write width 4 low bits");
                for (int i = 0; i < 4; i++) {
                    bytes.put(address + i, (byte) (low >>> (8 * i)));
                }
            } else if (width == 8) {
                if (value.highBits() != 0) throw new AssertionError("Invalid write width 8 high bits");
                long low = value.lowBits();
                for (int i = 0; i < 8; i++) {
                    bytes.put(address + i, (byte) (low >>> (8 * i)));
                }
            } else if (width == 16) {
                long low = value.lowBits();
                long high = value.highBits();
                for (int i = 0; i < 8; i++) {
                    bytes.put(address + i, (byte) (low >>> (8 * i)));
                }
                for (int i = 0; i < 8; i++) {
                    bytes.put(address + 8 + i, (byte) (high >>> (8 * i)));
                }
            } else {
                throw new AssertionError("Invalid write width");
            }
        }

        @Override
        public int readDword(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            Read r = (Read) s;
            if (r.widthBytes() != 4) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            Bits128 actual = readRawBits(addressBits, 4);
            if (!actual.equals(r.valueBits())) throw new AssertionError("Value mismatch");
            return (int) actual.lowBits();
        }

        @Override
        public long readQword(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            Read r = (Read) s;
            if (r.widthBytes() != 8) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            Bits128 actual = readRawBits(addressBits, 8);
            if (!actual.equals(r.valueBits())) throw new AssertionError("Value mismatch");
            return actual.lowBits();
        }

        @Override
        public Bits128 read128(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            Read r = (Read) s;
            if (r.widthBytes() != 16) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            Bits128 actual = readRawBits(addressBits, 16);
            if (!actual.equals(r.valueBits())) throw new AssertionError("Value mismatch");
            return actual;
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            if (w.widthBytes() != 4) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            Bits128 val = new Bits128(Integer.toUnsignedLong(valueBits), 0);
            if (!val.equals(w.valueBits())) throw new AssertionError("Value mismatch");
            writeRawBits(addressBits, val, 4);
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            if (w.widthBytes() != 8) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            Bits128 val = new Bits128(valueBits, 0);
            if (!val.equals(w.valueBits())) throw new AssertionError("Value mismatch");
            writeRawBits(addressBits, val, 8);
        }

        @Override
        public void write128(long addressBits, Bits128 valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            if (w.widthBytes() != 16) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            if (!valueBits.equals(w.valueBits())) throw new AssertionError("Value mismatch");
            writeRawBits(addressBits, valueBits, 16);
        }

        @Override
        public int readUnsignedByte(long addressBits) {
            throw new UnsupportedOperationException("Unsupported readUnsignedByte");
        }

        @Override
        public void writeByte(long addressBits, int lowByteBits) {
            throw new UnsupportedOperationException("Unsupported writeByte");
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
    }

    private static class CallsImpl implements FullContext493Api.Calls {
        private final List<Step> steps;
        private final int[] cursor;
        private final MemoryImpl memory;

        CallsImpl(List<Step> steps, int[] cursor, MemoryImpl memory) {
            this.steps = steps;
            this.cursor = cursor;
            this.memory = memory;
        }

        @Override
        public FullCopy437Api.CallResult invoke(FullContext493Api.CallFrame frame) {
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
                Bits128 v = w.valueBits();
                if (w.widthBytes() == 4) {
                    if (v.highBits() != 0 || v.lowBits() < 0 || v.lowBits() > 0xFFFFFFFFL) {
                        throw new AssertionError("Invalid effect width 4 value");
                    }
                    memory.writeDword(w.addressBits(), (int) v.lowBits());
                } else if (w.widthBytes() == 8) {
                    if (v.highBits() != 0) {
                        throw new AssertionError("Invalid effect width 8 value");
                    }
                    memory.writeQword(w.addressBits(), v.lowBits());
                } else if (w.widthBytes() == 16) {
                    memory.write128(w.addressBits(), v);
                } else {
                    throw new AssertionError("Invalid effect width");
                }
            }

            return inv.result();
        }
    }
}
