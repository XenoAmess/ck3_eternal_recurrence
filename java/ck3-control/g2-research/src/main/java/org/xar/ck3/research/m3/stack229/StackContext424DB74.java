package org.xar.ck3.research.m3.stack229;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.stack229.StackContext229Api.Input;
import org.xar.ck3.research.m3.stack229.StackContext229Api.Ports;

/** Normal business projection of 424DB74; physical stack/NV/RET/EH excluded. */
public final class StackContext424DB74 {
    private StackContext424DB74() { }

    public static long execute(NativeTaskMemory memory, Ports ports, Input input) {
        // Save entry R8 and R9 addresses before callbacks
        long savedR8 = input.r8Address();
        long savedR9 = input.r9Address();

        // 1. Enter: fresh read of ECX from RDX address
        int ecxEnter = memory.readInt32(input.rdxAddress());
        ports.call4247ffc(memory, 0x424DB8BL, ecxEnter);

        // 2. Middle: call with saved R8
        long middleRAX = ports.call424dd60(memory, 0x424DB94L, savedR8);
        int savedLow32 = (int) middleRAX;

        // 3. Leave: fresh read of ECX from saved R9 address, pass saved R9 as liveRbx
        int ecxLeave = memory.readInt32(savedR9);
        ports.call4248050(memory, 0x424DB9DL, ecxLeave, savedR9);

        // Return Integer.toUnsignedLong(savedLow32)
        return Integer.toUnsignedLong(savedLow32);
    }
}