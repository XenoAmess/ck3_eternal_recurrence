package org.xar.ck3.research.m3.stack227;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.stack227.StackContext227Api.Context;
import org.xar.ck3.research.m3.stack227.StackContext227Api.Ports;

/**
 * Exact supplied-storage projection for the actual 58-byte callee at 0x424DE88.
 * Performs only the four explicit prologue writes and the single typed child call.
 * No CPU/stack/RET/NV/EH modeling, no reads of E+10 or E, no zeroing of upper DWORDs.
 */
public final class StackContext424DE88 {
    private StackContext424DE88() { }

    public static long execute(NativeTaskMemory memory, Ports ports, Context context) {
        long E = context.E();
        long entryRCX = context.entryRCX();

        // 1. W64[E+0x08] = entryRCX
        memory.writeInt64(E + 0x08L, entryRCX);

        // 2. W64[E-0x18] = E+0x08
        memory.writeInt64(E - 0x18L, E + 0x08L);

        // 3. W32[E+0x18] = 2
        memory.writeInt32(E + 0x18L, 2);

        // 4. W32[E+0x20] = 2
        memory.writeInt32(E + 0x20L, 2);

        // 5. call424db74(memory, 0x424DEB8, E+0x10, E+0x20, E-0x18, E+0x18)
        long rcx = E + 0x10L;
        long rdx = E + 0x20L;
        long r8 = E - 0x18L;
        long r9 = E + 0x18L;
        long siteRva = 0x424DEB8L;

        return ports.call424db74(memory, siteRva, rcx, rdx, r8, r9);
    }
}