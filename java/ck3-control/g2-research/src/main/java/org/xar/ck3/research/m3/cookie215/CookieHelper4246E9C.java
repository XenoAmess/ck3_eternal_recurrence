package org.xar.ck3.research.m3.cookie215;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class CookieHelper4246E9C {
    private CookieHelper4246E9C() { }

    public static long execute(CookieHelper215Api.Input input, NativeTaskMemory memory,
            CookieHelper215Api.Ports ports) {
        long moduleBase = input.moduleBase();
        long rdxAddress = input.rdxAddress();
        long r9Address = input.r9Address();

        // 1. Read DWORD[entryRDX] to ECX
        int ecx = memory.readInt32(rdxAddress);

        // 2. Call enter at 0x4246EB0
        ports.enter(memory, 0x4246EB0L, ecx);

        // 3. Read fresh QWORD[base+0x542F0B8]
        long cookieRaw = memory.readPointer(moduleBase + 0x542F0B8L);

        // 4. Save original low6 for rotation
        int rot = (int) (cookieRaw & 0x3FL);

        // 5. Read fresh QWORD[base+0x5C5D318] and XOR
        long xorVal = memory.readPointer(moduleBase + 0x5C5D318L);
        long decoded = cookieRaw ^ xorVal;

        // 6. Rotate right 64 by saved rot
        decoded = Long.rotateRight(decoded, rot);

        // 7. Read fresh DWORD[entryR9] to ECX
        int ecx2 = memory.readInt32(r9Address);

        // 8. Call leave at 0x4246ECE with decoded liveRBX
        ports.leave(memory, 0x4246ECEL, ecx2, decoded);

        // 9. Return same saved decoded full64
        return decoded;
    }
}