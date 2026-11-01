package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInit550Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInitData557;

public final class EmbeddedInitHost557 {

    public static void verify(EmbeddedInitData557.Scene scene) {
        if (scene.steps().size() > 256) {
            throw new IllegalArgumentException("Steps exceed limit");
        }

        // Create fresh per-scene memory instance
        Memory mem = new Memory(scene);

        // Seed initial memory
        for (EmbeddedInitData557.Cell cell : scene.initialMemory()) {
            mem.seedCell(cell);
        }

        // Prepare Input with actual budget
        GovernmentCrtBoundary185Api.LoopBudget budget = new GovernmentCrtBoundary185Api.LoopBudget() {
            @Override
            public void beforeStep(long loopHeaderRva, long guardAddressBits) {
                throw new UnsupportedOperationException("Budget hook not used");
            }
        };
        FullCopy437Api.Input input = new FullCopy437Api.Input(scene.entry(), scene.directionFlagSet(), budget);

        // Prepare Calls capturing the exact same memory instance
        EmbeddedInit550Api.Calls calls = new EmbeddedInit550Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(EmbeddedInit550Api.CallFrame frame) {
                return mem.handleInvoke(frame, scene);
            }
        };

        // Execute
        FullCopy437Api.CallResult result = EmbeddedInitFullState8895D0.execute(input, mem, calls);

        // Verify Result
        if (!result.equals(scene.expectedResult())) {
            throw new AssertionError("Result mismatch");
        }

        // Verify Final Memory
        for (EmbeddedInitData557.Cell cell : scene.finalMemory()) {
            mem.verifyCell(cell);
        }

        // Verify Exhaustion
        if (mem.cursor != scene.steps().size()) {
            throw new AssertionError("Steps not fully consumed");
        }
    }

    private static class Memory implements FullCopy437Api.Memory {
        private final Map<Long, Byte> RAM = new HashMap<>();
        private int cursor = 0;
        private final EmbeddedInitData557.Scene scene;

        Memory(EmbeddedInitData557.Scene scene) { this.scene = scene; }

        void seedCell(EmbeddedInitData557.Cell cell) {
            int w = cell.widthBytes();
            if (w != 4 && w != 8) throw new IllegalArgumentException("Invalid width");
            long addr = cell.addressBits();
            long val = cell.lowBits();
            if (w == 4 && (val < 0 || val > 0xFFFFFFFFL)) throw new IllegalArgumentException("Invalid DWORD value");
            for (int i = 0; i < w; i++) {
                long byteVal = (val >>> (i * 8)) & 0xFFL;
                RAM.put(addr + i, (byte) byteVal);
            }
        }

        void verifyCell(EmbeddedInitData557.Cell cell) {
            int w = cell.widthBytes();
            if (w != 4 && w != 8) throw new IllegalArgumentException("Invalid width");
            long addr = cell.addressBits();
            long val = cell.lowBits();
            if (w == 4 && (val < 0 || val > 0xFFFFFFFFL)) throw new IllegalArgumentException("Invalid DWORD value");
            for (int i = 0; i < w; i++) {
                Long key = addr + i;
                if (!RAM.containsKey(key)) throw new AssertionError("Missing byte at " + Long.toHexString(key));
                byte actual = RAM.get(key);
                long expected = (val >>> (i * 8)) & 0xFFL;
                if ((actual & 0xFFL) != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(key));
            }
        }

        @Override
        public long readQword(long addressBits) {
            if (cursor >= scene.steps().size()) throw new AssertionError("Exhaustion");
            EmbeddedInitData557.Step step = scene.steps().get(cursor);
            if (!(step instanceof EmbeddedInitData557.Read)) throw new AssertionError("Expected Read");
            EmbeddedInitData557.Read read = (EmbeddedInitData557.Read) step;
            if (read.widthBytes() != 8) throw new AssertionError("Invalid read width");
            if (read.addressBits() != addressBits) throw new AssertionError("Address mismatch");

            long val = 0;
            for (int i = 0; i < 8; i++) {
                Long key = addressBits + i;
                if (!RAM.containsKey(key)) throw new AssertionError("Missing byte at " + Long.toHexString(key));
                byte b = RAM.get(key);
                val |= (b & 0xFFL) << (i * 8);
            }

            if (read.lowBits() != val) throw new AssertionError("Value mismatch");
            cursor++;
            return val;
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            if (cursor >= scene.steps().size()) throw new AssertionError("Exhaustion");
            EmbeddedInitData557.Step step = scene.steps().get(cursor);
            if (!(step instanceof EmbeddedInitData557.Write)) throw new AssertionError("Expected Write");
            EmbeddedInitData557.Write write = (EmbeddedInitData557.Write) step;
            if (write.widthBytes() != 8) throw new AssertionError("Invalid write width");
            if (write.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            if (write.lowBits() != valueBits) throw new AssertionError("Value mismatch");

            for (int i = 0; i < 8; i++) {
                long byteVal = (valueBits >>> (i * 8)) & 0xFFL;
                RAM.put(addressBits + i, (byte) byteVal);
            }
            cursor++;
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            if (cursor >= scene.steps().size()) throw new AssertionError("Exhaustion");
            EmbeddedInitData557.Step step = scene.steps().get(cursor);
            if (!(step instanceof EmbeddedInitData557.Write)) throw new AssertionError("Expected Write");
            EmbeddedInitData557.Write write = (EmbeddedInitData557.Write) step;
            if (write.widthBytes() != 4) throw new AssertionError("Invalid write width");
            if (write.lowBits() < 0 || write.lowBits() > 0xFFFFFFFFL) throw new IllegalArgumentException("Invalid DWORD literal");
            if (write.addressBits() != addressBits) throw new AssertionError("Address mismatch");
            long val = Integer.toUnsignedLong(valueBits);
            if (write.lowBits() != val) throw new AssertionError("Value mismatch");

            for (int i = 0; i < 4; i++) {
                long byteVal = (val >>> (i * 8)) & 0xFFL;
                RAM.put(addressBits + i, (byte) byteVal);
            }
            cursor++;
        }

        private FullCopy437Api.CallResult handleInvoke(EmbeddedInit550Api.CallFrame frame, EmbeddedInitData557.Scene scene) {
            if (cursor >= scene.steps().size()) throw new AssertionError("Exhaustion");
            EmbeddedInitData557.Step step = scene.steps().get(cursor);
            if (!(step instanceof EmbeddedInitData557.Invoke)) throw new AssertionError("Expected Invoke");
            EmbeddedInitData557.Invoke invoke = (EmbeddedInitData557.Invoke) step;

            if (!invoke.frame().equals(frame)) throw new AssertionError("Frame mismatch");

            FullCopy437Api.CallResult result = invoke.result();
            frame.checkNormalReturn(result);

            cursor++;

            for (EmbeddedInitData557.Write effect : invoke.effects()) {
                if (effect.widthBytes() == 4 && (effect.lowBits() < 0 || effect.lowBits() > 0xFFFFFFFFL)) throw new IllegalArgumentException("Invalid effect DWORD value");
                if (effect.widthBytes() == 8) {
                    writeQword(effect.addressBits(), effect.lowBits());
                } else if (effect.widthBytes() == 4) {
                    writeDword(effect.addressBits(), (int) effect.lowBits());
                } else {
                    throw new AssertionError("Invalid effect width");
                }
            }

            return result;
        }

        // Inherited methods from FullCopy437Api.Memory
        @Override
        public int readDword(long addressBits) { throw new UnsupportedOperationException(); }
        @Override
        public int readUnsignedByte(long addressBits) { throw new UnsupportedOperationException(); }
        @Override
        public void writeByte(long addressBits, int lowByteBits) { throw new UnsupportedOperationException(); }
        @Override
        public Bits128 read128(long addressBits) { throw new UnsupportedOperationException(); }
        @Override
        public void write128(long addressBits, Bits128 valueBits) { throw new UnsupportedOperationException(); }

        // Inherited methods from GovernmentMemoryFill206Api.Memory
        @Override
        public void writeWord(long addressBits, int valueBits) { throw new UnsupportedOperationException(); }
        @Override
        public void write128NonTemporal(long addressBits, Bits128 valueBits) { throw new UnsupportedOperationException(); }
        @Override
        public void sfence() { throw new UnsupportedOperationException(); }

        // Inherited methods from FullCopy437Api.Memory
        @Override
        public int readUnsignedWord(long addressBits) { throw new UnsupportedOperationException(); }
        @Override
        public FullCopy437Api.Bits256 read256(long addressBits) { throw new UnsupportedOperationException(); }
        @Override
        public void write256(long addressBits, FullCopy437Api.Bits256 valueBits) { throw new UnsupportedOperationException(); }
        @Override
        public void write256NonTemporal(long addressBits, FullCopy437Api.Bits256 valueBits) { throw new UnsupportedOperationException(); }

        // Inherited methods from GovernmentCaller153Api.Memory
        @Override
        public int lockedXaddDword(long addressBits, int addendBits) { throw new UnsupportedOperationException(); }
    }
}