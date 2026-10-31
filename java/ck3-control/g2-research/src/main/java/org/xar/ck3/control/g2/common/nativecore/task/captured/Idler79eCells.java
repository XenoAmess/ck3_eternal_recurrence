package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Source-bound stride-12 scan; retains the first cells pointer and exact 32-bit span arithmetic. */
public final class Idler79eCells {
    private Idler79eCells() { }
    public static Idler79ePorts.ScanResult scan(long header, int wantedRawDword8, Idler79ePorts.Memory memory) {
        long initialCells = memory.readPointer(header + 0x20);
        long current = initialCells;
        while (memory.readUnsignedByte(current) == 0) {
            current += 12;
        }
        int markerByte = memory.readUnsignedByte(header + 0x30);
        int count = memory.readInt32(header + 0x2C);
        int incrementedCount = count + 1;
        int spanInt32 = markerByte + incrementedCount;
        long signed32span = (long)spanInt32;
        long end = initialCells + (signed32span * 12L);
        if (current == end) {
            return new Idler79ePorts.ScanResult(initialCells, -1);
        }
        int dwordAtCurrent8 = memory.readInt32(current + 8);
        if (dwordAtCurrent8 == wantedRawDword8) {
            int rawDword4 = memory.readInt32(current + 4);
            return new Idler79ePorts.ScanResult(initialCells, rawDword4);
        }
        while (true) {
            current += 12;
            while (memory.readUnsignedByte(current) == 0) {
                current += 12;
            }
            if (current == end) {
                return new Idler79ePorts.ScanResult(initialCells, -1);
            }
            if (memory.readInt32(current + 8) == wantedRawDword8) {
                int rawDword4 = memory.readInt32(current + 4);
                return new Idler79ePorts.ScanResult(initialCells, rawDword4);
            }
        }
    }
}
