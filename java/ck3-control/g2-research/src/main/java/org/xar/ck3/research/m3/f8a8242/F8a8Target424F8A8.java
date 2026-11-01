package org.xar.ck3.research.m3.f8a8242;

import org.xar.ck3.research.m3.f8a8242.F8a8Api242.Input;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242.Memory;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242.Ports;

/** Explicit normal205B storage operations; opaque calls retain their own behavior. */
public final class F8a8Target424F8A8 {
    private F8a8Target424F8A8() { }

    public static void execute(Memory memory, Ports ports, Input input) {
        long base = input.moduleBase();
        long block = input.blockBits();
        long b = input.scratch().frameRbp();
        memory.writeInt64(b - 0x28L, block);
        memory.writeInt64(b - 0x18L, b - 0x28L);
        memory.writeInt32(b + 0x20L, 5);
        memory.writeInt32(b + 0x28L, 5);
        memory.writeInt64(b - 0x10L, b - 0x28L);
        memory.writeInt64(b - 8L, b - 0x20L);
        memory.writeInt32(b - 0x30L, 4);
        memory.writeInt32(b - 0x2CL, 4);
        memory.writeInt64(b - 0x20L, base + 0x5C5DCD8L);
        memory.writeInt32(block + 0x28L, 1);
        long pointer = memory.readPointer(b - 0x28L);
        memory.writeInt64(pointer, base + 0x44267F0L);
        pointer = memory.readPointer(b - 0x28L);
        memory.writeInt32(pointer + 0x3A8L, 1);
        pointer = memory.readPointer(b - 0x28L);
        memory.writeInt64(pointer + 0x88L, base + 0x542F770L);
        pointer = memory.readPointer(b - 0x28L);
        memory.writeInt16(pointer + 0xBCL, 0x43);
        pointer = memory.readPointer(b - 0x28L);
        memory.writeInt16(pointer + 0x1C2L, 0x43);
        pointer = memory.readPointer(b - 0x28L);
        memory.readPointer(pointer + 0x3A0L);
        memory.writeInt64(pointer + 0x3A0L, 0L);
        ports.call424f780(memory, 0x424F955L, b + 0x18L, b + 0x28L, b - 0x18L, b + 0x20L, b - 0x58L);
        ports.call424f800(memory, 0x424F96AL, b + 0x18L, b - 0x2CL, b - 0x10L, b - 0x30L);
    }
}
