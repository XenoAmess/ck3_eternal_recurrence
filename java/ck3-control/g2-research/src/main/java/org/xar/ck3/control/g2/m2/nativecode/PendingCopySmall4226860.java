package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

public final class PendingCopySmall4226860 {
    private PendingCopySmall4226860() { }

    public static void copy(Copy4226860Api.Memory memory, long destination, long source, long bytes, long moduleBase) {
        // Entry precondition: bytes is unsigned 0..15
        // Table dispatch: read32(moduleBase + 0x6090000 + bytes * 4)
        long tableIndex = bytes * 4;
        long tableAddress = moduleBase + 0x6090000 + tableIndex;
        int rva = memory.read32(tableAddress);

        // Switch on actual frozen labels from CFG-CLOSED368.json small16 table
        // Targets in order: 0x422688e, 0x4226974, 0x42268c8, 0x42268ff, 0x422697a, 0x422695f, 0x4226950, 0x42268d0, 0x422696d, 0x4226935, 0x4226926, 0x42268b0, 0x4226943, 0x4226910, 0x42268e8, 0x4226890
        // These correspond to bytes 0..15 respectively

        switch (rva) {
            case 0x422688e: // bytes=0: ret only
                return;
            case 0x4226974: // bytes=1: movzx BYTE, mov BYTE
                {
                    int v = (memory.read8(source) & 0xFF);
                    memory.write8(destination, v);
                }
                return;
            case 0x42268c8: // bytes=2: movzx WORD, mov WORD
                {
                    int v = (memory.read16(source) & 0xFFFF);
                    memory.write16(destination, v);
                }
                return;
            case 0x42268ff: // bytes=3: movzx WORD, movzx BYTE, mov WORD, mov BYTE
                {
                    int v16 = (memory.read16(source) & 0xFFFF);
                    int v8 = (memory.read8(source + 2) & 0xFF);
                    memory.write16(destination, v16);
                    memory.write8(destination + 2, v8);
                }
                return;
            case 0x422697a: // bytes=4: mov DWORD, mov DWORD
                {
                    int v = memory.read32(source);
                    memory.write32(destination, v);
                }
                return;
            case 0x422695f: // bytes=5: mov DWORD, movzx BYTE, mov DWORD, mov BYTE
                {
                    int v32 = memory.read32(source);
                    int v8 = (memory.read8(source + 4) & 0xFF);
                    memory.write32(destination, v32);
                    memory.write8(destination + 4, v8);
                }
                return;
            case 0x4226950: // bytes=6: mov DWORD, movzx WORD, mov DWORD, mov WORD
                {
                    int v32 = memory.read32(source);
                    int v16 = (memory.read16(source + 4) & 0xFFFF);
                    memory.write32(destination, v32);
                    memory.write16(destination + 4, v16);
                }
                return;
            case 0x42268d0: // bytes=7: mov DWORD, movzx WORD, movzx BYTE, mov DWORD, mov WORD, mov BYTE
                {
                    int v32 = memory.read32(source);
                    int v16 = (memory.read16(source + 4) & 0xFFFF);
                    int v8 = (memory.read8(source + 6) & 0xFF);
                    memory.write32(destination, v32);
                    memory.write16(destination + 4, v16);
                    memory.write8(destination + 6, v8);
                }
                return;
            case 0x422696d: // bytes=8: mov QWORD, mov QWORD
                {
                    long v = memory.read64(source);
                    memory.write64(destination, v);
                }
                return;
            case 0x4226935: // bytes=9: mov QWORD, movzx BYTE, mov QWORD, mov BYTE
                {
                    long v64 = memory.read64(source);
                    int v8 = (memory.read8(source + 8) & 0xFF);
                    memory.write64(destination, v64);
                    memory.write8(destination + 8, v8);
                }
                return;
            case 0x4226926: // bytes=10: mov QWORD, movzx WORD, mov QWORD, mov WORD
                {
                    long v64 = memory.read64(source);
                    int v16 = (memory.read16(source + 8) & 0xFFFF);
                    memory.write64(destination, v64);
                    memory.write16(destination + 8, v16);
                }
                return;
            case 0x42268b0: // bytes=11: mov QWORD, movzx WORD, movzx BYTE, mov QWORD, mov WORD, mov BYTE
                {
                    long v64 = memory.read64(source);
                    int v16 = (memory.read16(source + 8) & 0xFFFF);
                    int v8 = (memory.read8(source + 10) & 0xFF);
                    memory.write64(destination, v64);
                    memory.write16(destination + 8, v16);
                    memory.write8(destination + 10, v8);
                }
                return;
            case 0x4226943: // bytes=12: mov QWORD, mov DWORD, mov QWORD, mov DWORD
                {
                    long v64 = memory.read64(source);
                    int v32 = memory.read32(source + 8);
                    memory.write64(destination, v64);
                    memory.write32(destination + 8, v32);
                }
                return;
            case 0x4226910: // bytes=13: mov QWORD, mov DWORD, movzx BYTE, mov QWORD, mov DWORD, mov BYTE
                {
                    long v64 = memory.read64(source);
                    int v32 = memory.read32(source + 8);
                    int v8 = (memory.read8(source + 12) & 0xFF);
                    memory.write64(destination, v64);
                    memory.write32(destination + 8, v32);
                    memory.write8(destination + 12, v8);
                }
                return;
            case 0x42268e8: // bytes=14: mov QWORD, mov DWORD, movzx WORD, mov QWORD, mov DWORD, mov WORD
                {
                    long v64 = memory.read64(source);
                    int v32 = memory.read32(source + 8);
                    int v16 = (memory.read16(source + 12) & 0xFFFF);
                    memory.write64(destination, v64);
                    memory.write32(destination + 8, v32);
                    memory.write16(destination + 12, v16);
                }
                return;
            case 0x4226890: // bytes=15: mov QWORD, mov DWORD, movzx WORD, movzx BYTE, mov QWORD, mov DWORD, mov WORD, mov BYTE
                {
                    long v64 = memory.read64(source);
                    int v32 = memory.read32(source + 8);
                    int v16 = (memory.read16(source + 12) & 0xFFFF);
                    int v8 = (memory.read8(source + 14) & 0xFF);
                    memory.write64(destination, v64);
                    memory.write32(destination + 8, v32);
                    memory.write16(destination + 12, v16);
                    memory.write8(destination + 14, v8);
                }
                return;
            default:
                throw new UnsupportedOperationException("UNKNOWN_SMALL_TARGET");
        }
    }
}