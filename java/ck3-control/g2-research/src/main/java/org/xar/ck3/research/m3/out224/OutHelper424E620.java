package org.xar.ck3.research.m3.out224;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class OutHelper424E620 {
    private OutHelper424E620() { }

    public static long execute(NativeTaskMemory memory, OutHelper224Api.Ports ports, OutHelper224Api.Input input) {
        long moduleBase = input.moduleBase();
        long entryRcx = input.entryRcx();

        long r9 = moduleBase + 0x4427010L;
        int ecx = 0x1c;
        long r8 = moduleBase + 0x442700cL;
        long rdx = moduleBase + 0x4427010L;

        long directRax = ports.call424e448(memory, 0x424e643L, ecx, rdx, r8, r9);

        if (directRax == 0L) {
            return 0x00000000C0000225L;
        }

        long target = memory.readPointer(moduleBase + 0x43dbba8L);
        long tailRcx = 0xfffffffffffffffaL;
        long tailRdx = entryRcx;

        return ports.tail43dbba8(memory, 0x424e65cL, target, directRax, tailRcx, tailRdx);
    }
}