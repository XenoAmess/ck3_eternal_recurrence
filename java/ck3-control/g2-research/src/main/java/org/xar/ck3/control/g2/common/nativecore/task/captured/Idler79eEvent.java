package org.xar.ck3.control.g2.common.nativecore.task.captured;
public final class Idler79eEvent {
 private Idler79eEvent() { }
public static byte handle79e(long moduleBase, long eventAddress, Idler79ePorts.Memory memory, Idler79ePorts.Ports ports) {
    // Gate: DWORD[E+8] == 1
    if (memory.readInt32(eventAddress + 8) != 1) {
        return 1;
    }
    // Gate: DWORD[base+5CC1628] == 0
    if (memory.readInt32(moduleBase + 0x5CC1628L) != 0) {
        return 1;
    }

    // Capture key: DWORD[E+4]
    int key = memory.readInt32(eventAddress + 4);

    // Construct Known383e320 projection (stack20, stack28Byte, stack2c, stack34, stack38, stack40)
    // stack20 = base + 476C7B0
    // stack28Byte = 8 (from 'or $0x8,%al' then 'mov %al,0x28(%rsp)')
    // stack2c = 0 (QWORD)
    // stack34 = 0 (DWORD)
    // stack38 = base + 476C848
    // stack40 = key
    long stack20 = moduleBase + 0x476C7B0L;
    int stack28Byte = 8;
    long stack2c = 0L;
    int stack34 = 0;
    long stack38 = moduleBase + 0x476C848L;
    int stack40 = key;

    // Read root: QWORD[base+5C6A520]
    long root = memory.readPointer(moduleBase + 0x5C6A520L);

    if (root != 0) {
        // Check BYTE[root+0x20] != 0
        if (memory.readUnsignedByte(root + 0x20L) != 0) {
            // Check DWORD[root+0x24] == key
            if (memory.readInt32(root + 0x24L) == key) {
                // Fresh read BYTE[root+0x20] for EDX
                int edx = memory.readUnsignedByte(root + 0x20L);

                // Construct Known383e320 with rcx=root, edx=edx, r8d=-1
                Idler79ePorts.Known383e320 known = new Idler79ePorts.Known383e320(
                    root, edx, -1, stack20, stack28Byte, stack2c, stack34, stack38, stack40
                );

                // Call ports.call383e320
                ports.call383e320(known);

                // Reload key: DWORD[E+4] after normal return
                key = memory.readInt32(eventAddress + 4);
            }
        }
    }

    // Fresh read global QWORD[base+5C68C50]
    long globalAddr = memory.readPointer(moduleBase + 0x5C68C50L);

    // Read QWORD[that+A0]
    long r9 = memory.readPointer(globalAddr + 0xA0L);

    // header = thatread + 222E8
    long header = r9 + 0x222E8L;

    // selection = scan(header, key, memory)
    Idler79ePorts.ScanResult selection = Idler79eCells.scan(header, key, memory);

    // finish(header, E, selection, memory, ports)
    Idler79eClear.finish(header, eventAddress, selection, memory, ports);

    return 1;
}
}
