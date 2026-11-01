package org.xar.ck3.research.m3.dispatch218;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Leaf implementation for 42420C0 body region. */
public final class DispatchHelper42420C0 {
    private DispatchHelper42420C0() { }

    public static long execute(NativeTaskMemory memory, DispatchHelper218Api.Ports ports, DispatchHelper218Api.Input input) {
        // Save entry R8 and R9 addresses before callbacks
        long savedR8 = input.r8Address();
        long savedR9 = input.r9Address();

        // 1. Enter: fresh read of ECX from RDX address
        int ecxEnter = memory.readInt32(input.rdxAddress());
        ports.enter(memory, 0x42420D7L, ecxEnter);

        // 2. Middle: call with saved R8
        ports.call42420f8(memory, 0x42420E0L, savedR8);

        // 3. Leave: fresh read of ECX from saved R9 address, pass saved R9 as liveRbx
        int ecxLeave = memory.readInt32(savedR9);
        return ports.leave(memory, 0x42420E8L, ecxLeave, savedR9);
    }
}