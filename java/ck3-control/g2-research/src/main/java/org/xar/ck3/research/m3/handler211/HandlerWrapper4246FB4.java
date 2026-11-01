package org.xar.ck3.research.m3.handler211;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.handler211.Wrapper4246FB4Api211.Ports;

public final class HandlerWrapper4246FB4 {
    private HandlerWrapper4246FB4() { }

    public static long execute(NativeTaskMemory memory, Ports ports, long sourceEntryRsp) {
        // Ordered business Memory effects per MODEL-CONTRACT211:
        // 1. writeInt32(S+0x10, 3)
        // 2. writeInt32(S+0x18, 3)
        // 3. opaque child port at actual site 0x4246FD8 with known pointer args
        //    RCX=S+8, RDX=S+0x18, R8=S+8, R9=S+0x10
        //    RCX and R8 must alias (same value).
        //    Full 64-bit RAX returned unchanged.

        long s = sourceEntryRsp;

        memory.writeInt32(s + 0x10L, 3);
        memory.writeInt32(s + 0x18L, 3);

        long rcx = s + 8L;
        long rdx = s + 0x18L;
        long r8 = s + 8L;
        long r9 = s + 0x10L;

        return ports.call4246e9c(memory, 0x4246FD8L, rcx, rdx, r8, r9);
    }
}