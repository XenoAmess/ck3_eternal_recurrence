package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotKnownPageData531.Cell;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotKnownPageData531.Read;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotKnownPageData531.Write;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotKnownPageData531.RootInvoke;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotKnownPageData531.PageInvoke;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotKnownPageData531.Step;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotKnownPageData531.Scene;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotProducerWithKnownPageContextAndInit528;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotProducerWithKnownContextAndInit521;
import org.xar.ck3.control.g2.m2.nativecode.FullSlotProducer479Api;
import org.xar.ck3.control.g2.m2.nativecode.FullPage495Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

public final class PendingSlotKnownPageHost531 {
    private PendingSlotKnownPageHost531() { }

    public static void verify(Scene scene) {
        Objects.requireNonNull(scene);
        Objects.requireNonNull(scene.entry());
        Objects.requireNonNull(scene.steps());
        Objects.requireNonNull(scene.expectedResult());
        Objects.requireNonNull(scene.finalMemory());

        if (scene.steps().size() > 4096) {
            throw new AssertionError("Script too long");
        }

        List<Step> steps = scene.steps();
        int[] cursor = new int[1];

        // Validate initial cells
        for (Cell c : scene.initialMemory()) {
            validateLiteral(c);
        }

        // Create Memory implementation sharing the cursor
        MemoryImpl memory = new MemoryImpl(steps, cursor);

        // Seed initial memory (unlogged)
        for (Cell c : scene.initialMemory()) {
            memory.seed(c.addressBits(), c.lowBits(), c.highBits(), c.widthBytes());
        }

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

        // Create Calls adapter sharing the cursor and memory
        FullSlotProducer479Api.Calls rootCalls = new RootCallsImpl(steps, cursor, memory);
        PendingSlotProducerWithKnownContextAndInit521.ContextCalls contextCalls = new ContextCallsImpl();
        PendingSlotProducerWithKnownPageContextAndInit528.PageCalls pageCalls = new PageCallsImpl(steps, cursor, memory, budget);

        // Execute target
        FullCopy437Api.CallResult actualResult = PendingSlotProducerWithKnownPageContextAndInit528.execute(
            input,
            memory,
            rootCalls,
            contextCalls,
            pageCalls
        );

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
            validateLiteral(c);

            long actualLow = 0;
            long actualHigh = 0;

            if (c.widthBytes() == 1) {
                actualLow = memory.readRaw(c.addressBits(), 1);
                actualHigh = 0;
            } else if (c.widthBytes() == 4) {
                actualLow = memory.readRaw(c.addressBits(), 4);
                actualHigh = 0;
            } else if (c.widthBytes() == 8) {
                actualLow = memory.readRaw(c.addressBits(), 8);
                actualHigh = 0;
            } else if (c.widthBytes() == 16) {
                actualLow = memory.readRaw(c.addressBits(), 8);
                actualHigh = memory.readRaw(c.addressBits() + 8, 8);
            }

            if (actualLow != c.lowBits() || actualHigh != c.highBits()) {
                throw new AssertionError("Final cell mismatch at " + Long.toHexString(c.addressBits()));
            }
        }
    }

    private static void validateLiteral(Cell c) {
        if (c.widthBytes() != 1 && c.widthBytes() != 4 && c.widthBytes() != 8 && c.widthBytes() != 16) {
            throw new AssertionError("Invalid cell width");
        }
        if (c.widthBytes() == 1) {
            if (c.lowBits() < 0 || c.lowBits() > 0xFFL) throw new AssertionError("Invalid cell value width 1");
            if (c.highBits() != 0) throw new AssertionError("Invalid cell high bits for width 1");
        } else if (c.widthBytes() == 4) {
            if (c.lowBits() < 0 || c.lowBits() > 0xFFFFFFFFL) throw new AssertionError("Invalid cell value width 4");
            if (c.highBits() != 0) throw new AssertionError("Invalid cell high bits for width 4");
        } else if (c.widthBytes() == 8) {
            if (c.highBits() != 0) throw new AssertionError("Invalid cell high bits for width 8");
        } else if (c.widthBytes() == 16) {
            // Both limbs are raw 64-bit, no bounds check needed beyond type
        }
    }

    private static void validateLiteral(Read r) {
        if (r.widthBytes() != 1 && r.widthBytes() != 4 && r.widthBytes() != 8 && r.widthBytes() != 16) {
            throw new AssertionError("Invalid read width");
        }
        if (r.widthBytes() == 1) {
            if (r.lowBits() < 0 || r.lowBits() > 0xFFL) throw new AssertionError("Invalid read value width 1");
            if (r.highBits() != 0) throw new AssertionError("Invalid read high bits for width 1");
        } else if (r.widthBytes() == 4) {
            if (r.lowBits() < 0 || r.lowBits() > 0xFFFFFFFFL) throw new AssertionError("Invalid read value width 4");
            if (r.highBits() != 0) throw new AssertionError("Invalid read high bits for width 4");
        } else if (r.widthBytes() == 8) {
            if (r.highBits() != 0) throw new AssertionError("Invalid read high bits for width 8");
        } else if (r.widthBytes() == 16) {
            // Both limbs are raw 64-bit
        }
    }

    private static void validateLiteral(Write w) {
        if (w.widthBytes() != 1 && w.widthBytes() != 4 && w.widthBytes() != 8 && w.widthBytes() != 16) {
            throw new AssertionError("Invalid write width");
        }
        if (w.widthBytes() == 1) {
            if (w.lowBits() < 0 || w.lowBits() > 0xFFL) throw new AssertionError("Invalid write value width 1");
            if (w.highBits() != 0) throw new AssertionError("Invalid write high bits for width 1");
        } else if (w.widthBytes() == 4) {
            if (w.lowBits() < 0 || w.lowBits() > 0xFFFFFFFFL) throw new AssertionError("Invalid write value width 4");
            if (w.highBits() != 0) throw new AssertionError("Invalid write high bits for width 4");
        } else if (w.widthBytes() == 8) {
            if (w.highBits() != 0) throw new AssertionError("Invalid write high bits for width 8");
        } else if (w.widthBytes() == 16) {
            // Both limbs are raw 64-bit
        }
    }

    private static class MemoryImpl implements PendingSlotProducerWithKnownPageContextAndInit528.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Step> steps;
        private final int[] cursor;

        MemoryImpl(List<Step> steps, int[] cursor) {
            this.steps = steps;
            this.cursor = cursor;
        }

        void seed(long address, long low, long high, int width) {
            for (int i = 0; i < width; i++) {
                long val = (i < 8) ? (low >>> (8 * i)) : (high >>> (8 * (i - 8)));
                bytes.put(address + i, (byte) val);
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
            validateLiteral(r);
            if (r.widthBytes() != 1) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = readRaw(addressBits, 1);
            if (actual != r.lowBits()) throw new AssertionError("Value mismatch");
            return (int) actual;
        }

        @Override
        public int readDword(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            Read r = (Read) s;
            validateLiteral(r);
            if (r.widthBytes() != 4) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = readRaw(addressBits, 4);
            if (actual != r.lowBits()) throw new AssertionError("Value mismatch");
            return (int) actual;
        }

        @Override
        public long readQword(long addressBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected read: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Read)) throw new AssertionError("Expected Read at cursor " + (cursor[0] - 1));
            Read r = (Read) s;
            validateLiteral(r);
            if (r.widthBytes() != 8) throw new AssertionError("Width mismatch");
            if (r.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long actual = readRaw(addressBits, 8);
            if (actual != r.lowBits()) throw new AssertionError("Value mismatch");
            return actual;
        }

        @Override
        public Bits128 read128(long addressBits) {
            throw new UnsupportedOperationException("Unsupported read128");
        }

        @Override
        public void writeByte(long addressBits, int valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            validateLiteral(w);
            if (w.widthBytes() != 1) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long normalized = Integer.toUnsignedLong(valueBits) & 0xFFL;
            if (normalized != w.lowBits()) throw new AssertionError("Value mismatch");
            writeRaw(addressBits, normalized, 1);
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            validateLiteral(w);
            if (w.widthBytes() != 4) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long normalized = Integer.toUnsignedLong(valueBits);
            if (normalized != w.lowBits()) throw new AssertionError("Value mismatch");
            writeRaw(addressBits, normalized, 4);
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            if (cursor[0] >= steps.size()) throw new AssertionError("Unexpected write: script exhausted");
            Step s = steps.get(cursor[0]++);
            if (!(s instanceof Write)) throw new AssertionError("Expected Write at cursor " + (cursor[0] - 1));
            Write w = (Write) s;
            validateLiteral(w);
            if (w.widthBytes() != 8) throw new AssertionError("Width mismatch");
            if (w.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            if (valueBits != w.lowBits()) throw new AssertionError("Value mismatch");
            writeRaw(addressBits, valueBits, 8);
        }

        @Override
        public void write128(long addressBits, Bits128 valueBits) {
            throw new UnsupportedOperationException("Unsupported write128");
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

    private static class RootCallsImpl implements FullSlotProducer479Api.Calls {
        private final List<Step> steps;
        private final int[] cursor;
        private final MemoryImpl memory;

        RootCallsImpl(List<Step> steps, int[] cursor, MemoryImpl memory) {
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
            if (!(step instanceof RootInvoke)) {
                throw new AssertionError("Expected RootInvoke at cursor " + (cursor[0] - 1));
            }
            RootInvoke inv = (RootInvoke) step;

            if (!inv.frame().equals(frame)) {
                throw new AssertionError("CallFrame mismatch at cursor " + (cursor[0] - 1));
            }

            for (Write w : inv.effects()) {
                validateLiteral(w);
                if (w.widthBytes() == 1) {
                    memory.writeByte(w.addressBits(), (int) w.lowBits());
                } else if (w.widthBytes() == 4) {
                    memory.writeDword(w.addressBits(), (int) w.lowBits());
                } else if (w.widthBytes() == 8) {
                    memory.writeQword(w.addressBits(), w.lowBits());
                } else if (w.widthBytes() == 16) {
                    memory.write128(w.addressBits(), new Bits128(w.lowBits(), w.highBits()));
                } else {
                    throw new AssertionError("Invalid effect width");
                }
            }

            return inv.result();
        }
    }

    private static class ContextCallsImpl implements PendingSlotProducerWithKnownContextAndInit521.ContextCalls {
        @Override
        public FullCopy437Api.CallResult invoke(PendingSlotProducerWithKnownContextAndInit521.Memory memoryParam, GovernmentCrtBoundary185Api.LoopBudget budgetParam, FullContext493Api.CallFrame frame) {
            throw new AssertionError("ContextCalls invoked in negative scene");
        }
    }

    private static class PageCallsImpl implements PendingSlotProducerWithKnownPageContextAndInit528.PageCalls {
        private final List<Step> steps;
        private final int[] cursor;
        private final MemoryImpl memory;
        private final GovernmentCrtBoundary185Api.LoopBudget originalBudget;

        PageCallsImpl(List<Step> steps, int[] cursor, MemoryImpl memory, GovernmentCrtBoundary185Api.LoopBudget originalBudget) {
            this.steps = steps;
            this.cursor = cursor;
            this.memory = memory;
            this.originalBudget = originalBudget;
        }

        @Override
        public FullCopy437Api.CallResult invoke(PendingSlotProducerWithKnownPageContextAndInit528.Memory memoryParam, GovernmentCrtBoundary185Api.LoopBudget budgetParam, FullPage495Api.CallFrame frame) {
            if (memoryParam != memory) {
                throw new AssertionError("Memory identity mismatch");
            }
            if (budgetParam != originalBudget) {
                throw new AssertionError("Budget identity mismatch");
            }

            if (cursor[0] >= steps.size()) {
                throw new AssertionError("Unexpected invoke: script exhausted");
            }
            Step step = steps.get(cursor[0]++);
            if (!(step instanceof PageInvoke)) {
                throw new AssertionError("Expected PageInvoke at cursor " + (cursor[0] - 1));
            }
            PageInvoke inv = (PageInvoke) step;

            if (!inv.frame().equals(frame)) {
                throw new AssertionError("PageCallFrame mismatch at cursor " + (cursor[0] - 1));
            }

            for (Write w : inv.effects()) {
                validateLiteral(w);
                if (w.widthBytes() == 1) {
                    memory.writeByte(w.addressBits(), (int) w.lowBits());
                } else if (w.widthBytes() == 4) {
                    memory.writeDword(w.addressBits(), (int) w.lowBits());
                } else if (w.widthBytes() == 8) {
                    memory.writeQword(w.addressBits(), w.lowBits());
                } else if (w.widthBytes() == 16) {
                    memory.write128(w.addressBits(), new Bits128(w.lowBits(), w.highBits()));
                } else {
                    throw new AssertionError("Invalid effect width");
                }
            }

            return inv.result();
        }
    }
}