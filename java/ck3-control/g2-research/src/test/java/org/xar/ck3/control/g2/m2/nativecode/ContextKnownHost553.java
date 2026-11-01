package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullContext493Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextWithKnownConstructor551;
import org.xar.ck3.control.g2.m2.nativecode.ContextKnownData553;

public final class ContextKnownHost553 {

    private static final int MAX_STEPS = 512;

    public static void verify(ContextKnownData553.Scene scene) {
        Objects.requireNonNull(scene);
        if (scene.steps().size() > MAX_STEPS) {
            throw new IllegalArgumentException("Step count exceeds limit");
        }

        // 1. Initialize Shared RAM
        Map<Long, Byte> ram = new HashMap<>();
        for (ContextKnownData553.Cell cell : scene.initialMemory()) {
            validateCell(cell);
            seedRam(ram, cell);
        }

        // 2. Initialize Cursor
        int[] cursor = {0};

        // 3. Create Budget (Concrete implementation of 185.LoopBudget)
        GovernmentCrtBoundary185Api.LoopBudget budget = new LoopBudgetImpl();

        // 4. Create Memory (Concrete implementation of 493.Memory)
        MemoryImpl memory = new MemoryImpl(ram, cursor, scene);

        // 5. Create Input
        FullContext493Api.Input input = new FullContext493Api.Input(
            scene.entry(),
            scene.directionFlagSet(),
            budget
        );

        // 6. Create Calls
        FullContext493Api.Calls fallback = new FallbackCallsImpl(memory, cursor, scene);
        PendingContextWithKnownConstructor551.ConstructorCalls constructors = new ConstructorCallsImpl(memory, cursor, scene, budget);

        // 7. Execute Target
        FullCopy437Api.CallResult result = PendingContextWithKnownConstructor551.execute(input, memory, fallback, constructors);

        // 8. Verify Result
        if (!result.equals(scene.expectedResult())) {
            throw new AssertionError("Result mismatch");
        }

        // 9. Verify Final Memory
        for (ContextKnownData553.Cell cell : scene.finalMemory()) {
            validateCell(cell);
            if (!checkRam(ram, cell)) {
                throw new AssertionError("Final memory mismatch");
            }
        }

        // 10. Verify Complete Consumption
        if (cursor[0] != scene.steps().size()) {
            throw new AssertionError("Steps not fully consumed");
        }
    }

    private static void validateCell(ContextKnownData553.Cell cell) {
        int w = cell.widthBytes();
        if (w != 1 && w != 2 && w != 4 && w != 8 && w != 16) {
            throw new IllegalArgumentException("Invalid width: " + w);
        }
        long low = cell.lowBits();
        long high = cell.highBits();
        if (w == 1) {
            if (low < 0 || low > 0xFF || high != 0) throw new IllegalArgumentException("Invalid 1-byte cell");
        } else if (w == 2) {
            if (low < 0 || low > 0xFFFF || high != 0) throw new IllegalArgumentException("Invalid 2-byte cell");
        } else if (w == 4) {
            if (low < 0 || low > 0xFFFFFFFFL || high != 0) throw new IllegalArgumentException("Invalid 4-byte cell");
        } else if (w == 8) {
            if (high != 0) throw new IllegalArgumentException("Invalid 8-byte cell high");
        } else if (w == 16) {
            // Both low and high are raw 64-bit values
        }
    }

    private static void seedRam(Map<Long, Byte> ram, ContextKnownData553.Cell cell) {
        long addr = cell.addressBits();
        int w = cell.widthBytes();
        long low = cell.lowBits();
        long high = cell.highBits();
        for (int i = 0; i < w; i++) {
            long byteVal;
            if (i < 8) {
                byteVal = (low >>> (i * 8)) & 0xFF;
            } else {
                byteVal = (high >>> ((i - 8) * 8)) & 0xFF;
            }
            ram.put(addr + i, (byte) byteVal);
        }
    }

    private static boolean checkRam(Map<Long, Byte> ram, ContextKnownData553.Cell cell) {
        long addr = cell.addressBits();
        int w = cell.widthBytes();
        long low = cell.lowBits();
        long high = cell.highBits();
        for (int i = 0; i < w; i++) {
            long byteVal;
            if (i < 8) {
                byteVal = (low >>> (i * 8)) & 0xFF;
            } else {
                byteVal = (high >>> ((i - 8) * 8)) & 0xFF;
            }
            Byte actual = ram.get(addr + i);
            if (actual == null) return false;
            if ((actual & 0xFFL) != byteVal) return false;
        }
        return true;
    }

    private static long readRam(Map<Long, Byte> ram, long addr, int w) {
        long low = 0;
        long high = 0;
        for (int i = 0; i < w; i++) {
            Byte b = ram.get(addr + i);
            if (b == null) throw new AssertionError("Unseeded read at " + Long.toHexString(addr + i));
            long val = (long) b & 0xFF;
            if (i < 8) {
                low |= val << (i * 8);
            } else {
                high |= val << ((i - 8) * 8);
            }
        }
        return w == 16 ? low : (w == 8 ? low : (w == 4 ? (low & 0xFFFFFFFFL) : (w == 2 ? (low & 0xFFFFL) : (low & 0xFFL))));
    }

    private static void writeRam(Map<Long, Byte> ram, long addr, int w, long low, long high) {
        for (int i = 0; i < w; i++) {
            long byteVal;
            if (i < 8) {
                byteVal = (low >>> (i * 8)) & 0xFF;
            } else {
                byteVal = (high >>> ((i - 8) * 8)) & 0xFF;
            }
            ram.put(addr + i, (byte) byteVal);
        }
    }

    private static GovernmentPrimaryTail155Api.Bits128 read128Ram(Map<Long, Byte> ram, long addr) {
        long low = 0;
        long high = 0;
        for (int i = 0; i < 16; i++) {
            Byte b = ram.get(addr + i);
            if (b == null) throw new AssertionError("Unseeded read at " + Long.toHexString(addr + i));
            long val = (long) b & 0xFF;
            if (i < 8) {
                low |= val << (i * 8);
            } else {
                high |= val << ((i - 8) * 8);
            }
        }
        return new GovernmentPrimaryTail155Api.Bits128(low, high);
    }

    private static void write128Ram(Map<Long, Byte> ram, long addr, GovernmentPrimaryTail155Api.Bits128 bits) {
        long low = bits.lowBits();
        long high = bits.highBits();
        for (int i = 0; i < 16; i++) {
            long byteVal;
            if (i < 8) {
                byteVal = (low >>> (i * 8)) & 0xFF;
            } else {
                byteVal = (high >>> ((i - 8) * 8)) & 0xFF;
            }
            ram.put(addr + i, (byte) byteVal);
        }
    }

    private static class LoopBudgetImpl implements GovernmentCrtBoundary185Api.LoopBudget {
        public void beforeStep(long loopHeaderRva, long guardAddressBits) {
            throw new UnsupportedOperationException("No loop in source");
        }
    }

    private static class MemoryImpl implements FullContext493Api.Memory {
        private final Map<Long, Byte> ram;
        private final int[] cursor;
        private final ContextKnownData553.Scene scene;

        MemoryImpl(Map<Long, Byte> ram, int[] cursor, ContextKnownData553.Scene scene) {
            this.ram = ram;
            this.cursor = cursor;
            this.scene = scene;
        }

        private void consumeWrite(ContextKnownData553.Write expected) {
            if (cursor[0] >= scene.steps().size()) throw new AssertionError("No step to consume");
            ContextKnownData553.Step step = scene.steps().get(cursor[0]++);
            if (!(step instanceof ContextKnownData553.Write)) throw new AssertionError("Expected Write");
            ContextKnownData553.Write actual = (ContextKnownData553.Write) step;
            validateCell(new ContextKnownData553.Cell(actual.widthBytes(), actual.addressBits(), actual.lowBits(), actual.highBits()));
            if (actual.widthBytes() != expected.widthBytes()) throw new AssertionError("Width mismatch");
            if (actual.addressBits() != expected.addressBits()) throw new AssertionError("Address mismatch");
            if (actual.lowBits() != expected.lowBits()) throw new AssertionError("Low mismatch");
            if (actual.highBits() != expected.highBits()) throw new AssertionError("High mismatch");
        }

        private void consumeRead(ContextKnownData553.Read expected) {
            if (cursor[0] >= scene.steps().size()) throw new AssertionError("No step to consume");
            ContextKnownData553.Step step = scene.steps().get(cursor[0]++);
            if (!(step instanceof ContextKnownData553.Read)) throw new AssertionError("Expected Read");
            ContextKnownData553.Read actual = (ContextKnownData553.Read) step;
            validateCell(new ContextKnownData553.Cell(actual.widthBytes(), actual.addressBits(), actual.lowBits(), actual.highBits()));
            if (actual.widthBytes() != expected.widthBytes()) throw new AssertionError("Width mismatch");
            if (actual.addressBits() != expected.addressBits()) throw new AssertionError("Address mismatch");
            if (actual.lowBits() != expected.lowBits()) throw new AssertionError("Low mismatch");
            if (actual.highBits() != expected.highBits()) throw new AssertionError("High mismatch");
        }

        public int readDword(long addressBits) {
            long val = readRam(ram, addressBits, 4);
            ContextKnownData553.Read expected = new ContextKnownData553.Read(4, addressBits, val, 0);
            consumeRead(expected);
            return (int) val;
        }

        public long readQword(long addressBits) {
            long val = readRam(ram, addressBits, 8);
            ContextKnownData553.Read expected = new ContextKnownData553.Read(8, addressBits, val, 0);
            consumeRead(expected);
            return val;
        }

        public int readUnsignedByte(long addressBits) {
            throw new UnsupportedOperationException("Unused");
        }

        public void writeDword(long addressBits, int valueBits) {
            long val = Integer.toUnsignedLong(valueBits);
            ContextKnownData553.Write expected = new ContextKnownData553.Write(4, addressBits, val, 0);
            consumeWrite(expected);
            writeRam(ram, addressBits, 4, val, 0);
        }

        public int lockedXaddDword(long addressBits, int addendBits) {
            throw new UnsupportedOperationException("Unused");
        }

        public void writeQword(long addressBits, long valueBits) {
            ContextKnownData553.Write expected = new ContextKnownData553.Write(8, addressBits, valueBits, 0);
            consumeWrite(expected);
            writeRam(ram, addressBits, 8, valueBits, 0);
        }

        public void writeByte(long addressBits, int lowByteBits) {
            long val = (long) lowByteBits & 0xFF;
            ContextKnownData553.Write expected = new ContextKnownData553.Write(1, addressBits, val, 0);
            consumeWrite(expected);
            writeRam(ram, addressBits, 1, val, 0);
        }

        public GovernmentPrimaryTail155Api.Bits128 read128(long addressBits) {
            GovernmentPrimaryTail155Api.Bits128 bits = read128Ram(ram, addressBits);
            ContextKnownData553.Read expected = new ContextKnownData553.Read(16, addressBits, bits.lowBits(), bits.highBits());
            consumeRead(expected);
            return bits;
        }

        public void write128(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits) {
            ContextKnownData553.Write expected = new ContextKnownData553.Write(16, addressBits, valueBits.lowBits(), valueBits.highBits());
            consumeWrite(expected);
            write128Ram(ram, addressBits, valueBits);
        }

        public void writeWord(long addressBits, int valueBits) {
            long val = (long) valueBits & 0xFFFF;
            ContextKnownData553.Write expected = new ContextKnownData553.Write(2, addressBits, val, 0);
            consumeWrite(expected);
            writeRam(ram, addressBits, 2, val, 0);
        }

        public void write128NonTemporal(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits) {
            throw new UnsupportedOperationException("Unused");
        }

        public void sfence() {
            throw new UnsupportedOperationException("Unused");
        }

        public int readUnsignedWord(long addressBits) {
            throw new UnsupportedOperationException("Unused");
        }

        public FullCopy437Api.Bits256 read256(long addressBits) {
            throw new UnsupportedOperationException("Unused");
        }

        public void write256(long addressBits, FullCopy437Api.Bits256 valueBits) {
            throw new UnsupportedOperationException("Unused");
        }

        public void write256NonTemporal(long addressBits, FullCopy437Api.Bits256 valueBits) {
            throw new UnsupportedOperationException("Unused");
        }
    }

    private static class FallbackCallsImpl implements FullContext493Api.Calls {
        private final MemoryImpl memory;
        private final int[] cursor;
        private final ContextKnownData553.Scene scene;

        FallbackCallsImpl(MemoryImpl memory, int[] cursor, ContextKnownData553.Scene scene) {
            this.memory = memory;
            this.cursor = cursor;
            this.scene = scene;
        }

        public FullCopy437Api.CallResult invoke(FullContext493Api.CallFrame frame) {
            if (cursor[0] >= scene.steps().size()) throw new AssertionError("No step to consume");
            ContextKnownData553.Step step = scene.steps().get(cursor[0]++);
            if (!(step instanceof ContextKnownData553.ContextInvoke)) throw new AssertionError("Expected ContextInvoke");
            ContextKnownData553.ContextInvoke actual = (ContextKnownData553.ContextInvoke) step;
            if (!actual.frame().equals(frame)) throw new AssertionError("Frame mismatch");
            frame.checkNormalReturn(actual.result());
            for (ContextKnownData553.Write effect : actual.effects()) {
                validateCell(new ContextKnownData553.Cell(effect.widthBytes(), effect.addressBits(), effect.lowBits(), effect.highBits()));
                if (effect.widthBytes() == 1) {
                    memory.writeByte(effect.addressBits(), (int) effect.lowBits());
                } else if (effect.widthBytes() == 2) {
                    memory.writeWord(effect.addressBits(), (int) effect.lowBits());
                } else if (effect.widthBytes() == 4) {
                    memory.writeDword(effect.addressBits(), (int) effect.lowBits());
                } else if (effect.widthBytes() == 8) {
                    memory.writeQword(effect.addressBits(), effect.lowBits());
                } else if (effect.widthBytes() == 16) {
                    memory.write128(effect.addressBits(), new GovernmentPrimaryTail155Api.Bits128(effect.lowBits(), effect.highBits()));
                } else {
                    throw new AssertionError("Invalid effect width");
                }
            }
            return actual.result();
        }
    }

    private static class ConstructorCallsImpl implements PendingContextWithKnownConstructor551.ConstructorCalls {
        private final MemoryImpl memory;
        private final int[] cursor;
        private final ContextKnownData553.Scene scene;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;

        ConstructorCallsImpl(MemoryImpl memory, int[] cursor, ContextKnownData553.Scene scene, GovernmentCrtBoundary185Api.LoopBudget budget) {
            this.memory = memory;
            this.cursor = cursor;
            this.scene = scene;
            this.budget = budget;
        }

        public FullCopy437Api.CallResult invoke(FullContext493Api.Memory suppliedMemory, GovernmentCrtBoundary185Api.LoopBudget suppliedBudget, ContextConstructor543Api.CallFrame frame) {
            if (suppliedMemory != memory) throw new AssertionError("Memory identity mismatch");
            if (suppliedBudget != budget) throw new AssertionError("Budget identity mismatch");
            if (cursor[0] >= scene.steps().size()) throw new AssertionError("No step to consume");
            ContextKnownData553.Step step = scene.steps().get(cursor[0]++);
            if (!(step instanceof ContextKnownData553.ConstructorInvoke)) throw new AssertionError("Expected ConstructorInvoke");
            ContextKnownData553.ConstructorInvoke actual = (ContextKnownData553.ConstructorInvoke) step;
            if (!actual.frame().equals(frame)) throw new AssertionError("Frame mismatch");
            frame.checkNormalReturn(actual.result());
            for (ContextKnownData553.Write effect : actual.effects()) {
                validateCell(new ContextKnownData553.Cell(effect.widthBytes(), effect.addressBits(), effect.lowBits(), effect.highBits()));
                if (effect.widthBytes() == 1) {
                    memory.writeByte(effect.addressBits(), (int) effect.lowBits());
                } else if (effect.widthBytes() == 2) {
                    memory.writeWord(effect.addressBits(), (int) effect.lowBits());
                } else if (effect.widthBytes() == 4) {
                    memory.writeDword(effect.addressBits(), (int) effect.lowBits());
                } else if (effect.widthBytes() == 8) {
                    memory.writeQword(effect.addressBits(), effect.lowBits());
                } else if (effect.widthBytes() == 16) {
                    memory.write128(effect.addressBits(), new GovernmentPrimaryTail155Api.Bits128(effect.lowBits(), effect.highBits()));
                } else {
                    throw new AssertionError("Invalid effect width");
                }
            }
            return actual.result();
        }
    }
}