package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedVector565Api;
import org.xar.ck3.control.g2.m2.nativecode.VectorFullData570;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedVectorFullState260E040;

public final class VectorFullHost570 {

    public static void verify(VectorFullData570.Scene scene) {
        if (scene.steps().size() > 512) {
            throw new IllegalStateException("Step limit exceeded");
        }

        // Validate all cells in initial and final memory
        for (VectorFullData570.Cell cell : scene.initialMemory()) {
            validateCell(cell);
        }
        for (VectorFullData570.Cell cell : scene.finalMemory()) {
            validateCell(cell);
        }
        for (VectorFullData570.Step step : scene.steps()) {
            if (step instanceof VectorFullData570.Read) {
                validateRead((VectorFullData570.Read) step);
            } else if (step instanceof VectorFullData570.Write) {
                validateWrite((VectorFullData570.Write) step);
            } else if (step instanceof VectorFullData570.Invoke) {
                VectorFullData570.Invoke inv = (VectorFullData570.Invoke) step;
                validateFrame(inv.frame());
                validateResult(inv.result());
                for (VectorFullData570.Write w : inv.effects()) {
                    validateWrite(w);
                }
            } else if (step instanceof VectorFullData570.Budget) {
                // Budget steps are validated by the LoopBudget implementation
            }
        }

        // Shared RAM and Cursor
        Map<Long, Byte> ram = new HashMap<>();
        int[] cursor = new int[1];

        // Seed initial memory (unlogged)
        for (VectorFullData570.Cell cell : scene.initialMemory()) {
            seedCell(ram, cell);
        }

        // Prepare Input and Budget
        GovernmentCrtBoundary185Api.Entry entry = scene.entry();
        boolean df = scene.directionFlagSet();

        GovernmentCrtBoundary185Api.LoopBudget budget = new GovernmentCrtBoundary185Api.LoopBudget() {
            @Override
            public void beforeStep(long loopHeaderRva, long guardAddressBits) {
                if (cursor[0] >= scene.steps().size()) {
                    throw new IllegalStateException("Unexpected budget: steps exhausted");
                }
                VectorFullData570.Step step = scene.steps().get(cursor[0]++);
                if (!(step instanceof VectorFullData570.Budget)) {
                    throw new IllegalStateException("Expected Budget step at cursor " + (cursor[0]-1));
                }
                VectorFullData570.Budget b = (VectorFullData570.Budget) step;
                if (b.headerRva() != loopHeaderRva || b.guardAddressBits() != guardAddressBits) {
                    throw new IllegalStateException("Budget mismatch at cursor " + (cursor[0]-1));
                }
            }
        };

        FullCopy437Api.Input input = new FullCopy437Api.Input(entry, df, budget);

        // Prepare Memory Implementation
        FullCopy437Api.Memory memory = new FullCopy437Api.Memory() {
            @Override
            public int readDword(long addressBits) {
                return (int) readCell(ram, 4, addressBits, cursor, scene);
            }
            @Override
            public long readQword(long addressBits) {
                return readCell(ram, 8, addressBits, cursor, scene);
            }
            @Override
            public int readUnsignedByte(long addressBits) {
                throw new UnsupportedOperationException("readUnsignedByte not used in source");
            }
            @Override
            public void writeDword(long addressBits, int valueBits) {
                writeCell(ram, 4, addressBits, Integer.toUnsignedLong(valueBits), 0, cursor, scene);
            }
            @Override
            public int lockedXaddDword(long addressBits, int addendBits) {
                throw new UnsupportedOperationException("lockedXaddDword not used in source");
            }
            @Override
            public void writeQword(long addressBits, long valueBits) {
                writeCell(ram, 8, addressBits, valueBits, 0, cursor, scene);
            }
            @Override
            public void writeByte(long addressBits, int lowByteBits) {
                throw new UnsupportedOperationException("writeByte not used in source");
            }
            @Override
            public Bits128 read128(long addressBits) {
                return read128Cell(ram, addressBits, cursor, scene);
            }
            @Override
            public void write128(long addressBits, Bits128 valueBits) {
                write128Cell(ram, addressBits, valueBits, cursor, scene);
            }
            @Override
            public void writeWord(long addressBits, int valueBits) {
                throw new UnsupportedOperationException("writeWord not used in source");
            }
            @Override
            public void write128NonTemporal(long addressBits, Bits128 valueBits) {
                throw new UnsupportedOperationException("write128NonTemporal not used in source");
            }
            @Override
            public void sfence() {
                throw new UnsupportedOperationException("sfence not used in source");
            }
            @Override
            public int readUnsignedWord(long addressBits) {
                throw new UnsupportedOperationException("readUnsignedWord not used in source");
            }
            @Override
            public FullCopy437Api.Bits256 read256(long addressBits) {
                throw new UnsupportedOperationException("read256 not used in source");
            }
            @Override
            public void write256(long addressBits, FullCopy437Api.Bits256 valueBits) {
                throw new UnsupportedOperationException("write256 not used in source");
            }
            @Override
            public void write256NonTemporal(long addressBits, FullCopy437Api.Bits256 valueBits) {
                throw new UnsupportedOperationException("write256NonTemporal not used in source");
            }
        };

        EmbeddedVector565Api.Calls callsWithMemory = new EmbeddedVector565Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(EmbeddedVector565Api.CallFrame frame) {
                if (cursor[0] >= scene.steps().size()) {
                    throw new IllegalStateException("Unexpected invoke: steps exhausted");
                }
                VectorFullData570.Step step = scene.steps().get(cursor[0]++);
                if (!(step instanceof VectorFullData570.Invoke)) {
                    throw new IllegalStateException("Expected Invoke step at cursor " + (cursor[0]-1));
                }
                VectorFullData570.Invoke inv = (VectorFullData570.Invoke) step;

                if (!inv.frame().equals(frame)) {
                    throw new IllegalStateException("Frame mismatch at cursor " + (cursor[0]-1));
                }

                inv.frame().checkNormalReturn(inv.result());

                for (VectorFullData570.Write effect : inv.effects()) {
                    VectorFullData570.Write w = effect;
                    validateWrite(w);

                    // Perform actual write to RAM via Memory interface
                    if (w.widthBytes() == 4) {
                        memory.writeDword(w.addressBits(), (int) w.lowBits());
                    } else if (w.widthBytes() == 8) {
                        memory.writeQword(w.addressBits(), w.lowBits());
                    } else if (w.widthBytes() == 16) {
                        memory.write128(w.addressBits(), new Bits128(w.lowBits(), w.highBits()));
                    }
                }

                return inv.result();
            }
        };

        // Execute Target
        FullCopy437Api.CallResult actualResult = EmbeddedVectorFullState260E040.execute(input, memory, callsWithMemory);

        // Verify Final State
        if (!actualResult.equals(scene.expectedResult())) {
            throw new IllegalStateException("Final result mismatch");
        }

        // Check Final Memory Cells (Unlogged peek)
        for (VectorFullData570.Cell cell : scene.finalMemory()) {
            verifyCell(ram, cell);
        }

        // Check Step Exhaustion
        if (cursor[0] != scene.steps().size()) {
            throw new IllegalStateException("Steps not fully consumed: expected " + scene.steps().size() + ", got " + cursor[0]);
        }
    }

    private static void validateCell(VectorFullData570.Cell cell) {
        int width = cell.widthBytes();
        long low = cell.lowBits();
        long high = cell.highBits();
        if (width == 4) {
            if (low < 0 || low > 0xFFFFFFFFL || high != 0) throw new IllegalArgumentException("Invalid Cell width 4");
        } else if (width == 8) {
            if (high != 0) throw new IllegalArgumentException("Invalid Cell width 8");
        } else if (width == 16) {
            // raw64 low/high allowed
        } else {
            throw new IllegalArgumentException("Invalid Cell width");
        }
    }

    private static void validateRead(VectorFullData570.Read r) {
        validateCell(new VectorFullData570.Cell(r.widthBytes(), r.addressBits(), r.lowBits(), r.highBits()));
    }

    private static void validateWrite(VectorFullData570.Write w) {
        validateCell(new VectorFullData570.Cell(w.widthBytes(), w.addressBits(), w.lowBits(), w.highBits()));
    }

    private static void validateFrame(EmbeddedVector565Api.CallFrame f) {
        // Frame validation is handled by the constructor of CallFrame in the API
    }

    private static void validateResult(FullCopy437Api.CallResult r) {
        // Result validation is handled by the constructor of CallResult in the API
    }

    private static void seedCell(Map<Long, Byte> ram, VectorFullData570.Cell cell) {
        int width = cell.widthBytes();
        long addr = cell.addressBits();
        long low = cell.lowBits();
        long high = cell.highBits();

        if (width == 4) {
            ram.put(addr, (byte) low);
            ram.put(addr + 1, (byte) (low >>> 8));
            ram.put(addr + 2, (byte) (low >>> 16));
            ram.put(addr + 3, (byte) (low >>> 24));
        } else if (width == 8) {
            for (int i = 0; i < 8; i++) {
                ram.put(addr + i, (byte) (low >>> (i * 8)));
            }
        } else if (width == 16) {
            for (int i = 0; i < 8; i++) {
                ram.put(addr + i, (byte) (low >>> (i * 8)));
            }
            for (int i = 0; i < 8; i++) {
                ram.put(addr + 8 + i, (byte) (high >>> (i * 8)));
            }
        }
    }

    private static long readCell(Map<Long, Byte> ram, int width, long address, int[] cursor, VectorFullData570.Scene scene) {
        if (cursor[0] >= scene.steps().size()) throw new IllegalStateException("Unexpected read: steps exhausted");
        VectorFullData570.Step step = scene.steps().get(cursor[0]++);
        if (!(step instanceof VectorFullData570.Read)) throw new IllegalStateException("Expected Read step");
        VectorFullData570.Read r = (VectorFullData570.Read) step;

        if (r.widthBytes() != width || r.addressBits() != address) {
            throw new IllegalStateException("Read step mismatch");
        }

        long val = 0;
        if (width == 4) {
            for (int i = 0; i < 4; i++) {
                if (!ram.containsKey(address + i)) throw new IllegalStateException("Missing byte at " + (address + i));
                val |= (ram.get(address + i) & 0xFFL) << (i * 8);
            }
        } else if (width == 8) {
            for (int i = 0; i < 8; i++) {
                if (!ram.containsKey(address + i)) throw new IllegalStateException("Missing byte at " + (address + i));
                val |= (ram.get(address + i) & 0xFFL) << (i * 8);
            }
        } else if (width == 16) {
             throw new IllegalStateException("16 byte read handled by read128Cell");
        }

        if (width == 4) {
            if (val != r.lowBits()) throw new IllegalStateException("Read value mismatch");
        } else if (width == 8) {
            if (val != r.lowBits()) throw new IllegalStateException("Read value mismatch");
        }

        return val;
    }

    private static Bits128 read128Cell(Map<Long, Byte> ram, long address, int[] cursor, VectorFullData570.Scene scene) {
        if (cursor[0] >= scene.steps().size()) throw new IllegalStateException("Unexpected read128: steps exhausted");
        VectorFullData570.Step step = scene.steps().get(cursor[0]++);
        if (!(step instanceof VectorFullData570.Read)) throw new IllegalStateException("Expected Read step");
        VectorFullData570.Read r = (VectorFullData570.Read) step;

        if (r.widthBytes() != 16 || r.addressBits() != address) {
            throw new IllegalStateException("Read128 step mismatch");
        }

        long low = 0;
        long high = 0;
        for (int i = 0; i < 8; i++) {
            if (!ram.containsKey(address + i)) throw new IllegalStateException("Missing byte at " + (address + i));
            low |= (ram.get(address + i) & 0xFFL) << (i * 8);
        }
        for (int i = 0; i < 8; i++) {
            if (!ram.containsKey(address + 8 + i)) throw new IllegalStateException("Missing byte at " + (address + 8 + i));
            high |= (ram.get(address + 8 + i) & 0xFFL) << (i * 8);
        }

        if (low != r.lowBits() || high != r.highBits()) {
            throw new IllegalStateException("Read128 value mismatch");
        }

        return new Bits128(low, high);
    }

    private static void writeCell(Map<Long, Byte> ram, int width, long address, long low, long high, int[] cursor, VectorFullData570.Scene scene) {
        if (cursor[0] >= scene.steps().size()) throw new IllegalStateException("Unexpected write: steps exhausted");
        VectorFullData570.Step step = scene.steps().get(cursor[0]++);
        if (!(step instanceof VectorFullData570.Write)) throw new IllegalStateException("Expected Write step");
        VectorFullData570.Write w = (VectorFullData570.Write) step;

        if (w.widthBytes() != width || w.addressBits() != address) {
            throw new IllegalStateException("Write step mismatch");
        }

        if (width == 4) {
            if (w.lowBits() < 0 || w.lowBits() > 0xFFFFFFFFL || w.highBits() != 0) throw new IllegalStateException("Write4 range error");
            if (low != w.lowBits()) throw new IllegalStateException("Write4 value mismatch");
            ram.put(address, (byte) low);
            ram.put(address + 1, (byte) (low >>> 8));
            ram.put(address + 2, (byte) (low >>> 16));
            ram.put(address + 3, (byte) (low >>> 24));
        } else if (width == 8) {
            if (w.highBits() != 0) throw new IllegalStateException("Write8 high error");
            if (low != w.lowBits()) throw new IllegalStateException("Write8 value mismatch");
            for (int i = 0; i < 8; i++) {
                ram.put(address + i, (byte) (low >>> (i * 8)));
            }
        } else if (width == 16) {
             throw new IllegalStateException("16 byte write handled by write128Cell");
        }
    }

    private static void write128Cell(Map<Long, Byte> ram, long address, Bits128 value, int[] cursor, VectorFullData570.Scene scene) {
        if (cursor[0] >= scene.steps().size()) throw new IllegalStateException("Unexpected write128: steps exhausted");
        VectorFullData570.Step step = scene.steps().get(cursor[0]++);
        if (!(step instanceof VectorFullData570.Write)) throw new IllegalStateException("Expected Write step");
        VectorFullData570.Write w = (VectorFullData570.Write) step;

        if (w.widthBytes() != 16 || w.addressBits() != address) {
            throw new IllegalStateException("Write128 step mismatch");
        }

        if (value.lowBits() != w.lowBits() || value.highBits() != w.highBits()) {
            throw new IllegalStateException("Write128 value mismatch");
        }

        for (int i = 0; i < 8; i++) {
            ram.put(address + i, (byte) (value.lowBits() >>> (i * 8)));
        }
        for (int i = 0; i < 8; i++) {
            ram.put(address + 8 + i, (byte) (value.highBits() >>> (i * 8)));
        }
    }

    private static void verifyCell(Map<Long, Byte> ram, VectorFullData570.Cell cell) {
        int width = cell.widthBytes();
        long addr = cell.addressBits();
        long low = cell.lowBits();
        long high = cell.highBits();

        if (width == 4) {
            long val = 0;
            for (int i = 0; i < 4; i++) {
                if (!ram.containsKey(addr + i)) throw new IllegalStateException("Final cell missing byte");
                val |= (ram.get(addr + i) & 0xFFL) << (i * 8);
            }
            if (val != (low & 0xFFFFFFFFL)) throw new IllegalStateException("Final cell mismatch");
        } else if (width == 8) {
            long val = 0;
            for (int i = 0; i < 8; i++) {
                if (!ram.containsKey(addr + i)) throw new IllegalStateException("Final cell missing byte");
                val |= (ram.get(addr + i) & 0xFFL) << (i * 8);
            }
            if (val != low) throw new IllegalStateException("Final cell mismatch");
        } else if (width == 16) {
            long valLow = 0;
            long valHigh = 0;
            for (int i = 0; i < 8; i++) {
                if (!ram.containsKey(addr + i)) throw new IllegalStateException("Final cell missing byte");
                valLow |= (ram.get(addr + i) & 0xFFL) << (i * 8);
            }
            for (int i = 0; i < 8; i++) {
                if (!ram.containsKey(addr + 8 + i)) throw new IllegalStateException("Final cell missing byte");
                valHigh |= (ram.get(addr + 8 + i) & 0xFFL) << (i * 8);
            }
            if (valLow != low || valHigh != high) throw new IllegalStateException("Final cell mismatch");
        }
    }
}