package org.xar.ck3.control.g2.common.nativecore.task.captured;
public final class Idler79eClear {
 private Idler79eClear() { }
public static void finish(long header, long eventAddress, Idler79ePorts.ScanResult selection, Idler79ePorts.Memory memory, Idler79ePorts.Ports ports) {
    int eax = memory.readInt32(header + 0x28);
    if (eax > 0) {
        long cursor = selection.initialCells();
        while (eax > 0) {
            if (memory.readUnsignedByte(cursor) != 0) {
                memory.writeByte(cursor, (byte)0);
                memory.decrementInt32(header + 0x28);
                eax = memory.readInt32(header + 0x28);
            }
            cursor += 12;
        }
    }
    if (selection.rawDword4() != -1) {
        int edx = memory.readInt32(eventAddress + 8);
        ports.call28eed20(header, edx, selection.rawDword4());
    }
}
}
