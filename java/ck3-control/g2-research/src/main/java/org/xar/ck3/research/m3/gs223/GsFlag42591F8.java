package org.xar.ck3.research.m3.gs223;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.gs223.GsFlag223Api.Ports;
import org.xar.ck3.research.m3.gs223.GsFlag223Api.Scratch;

/** Exact 60B normal CFG of 42591F8; no CPU/stack/EH or native execution. */
public final class GsFlag42591F8 {
    private GsFlag42591F8() { }

    public static int execute(NativeTaskMemory memory, Ports ports, Scratch scratch) {
        long E = scratch.entryRsp();

        // 1. Initial W32[E+8, 0] before any GS reads or branches
        memory.writeInt32(E + 8, 0);

        // 2. Dynamic GS60 read at 4259204
        long gs = ports.readGs60(memory, 0x4259204L);

        // 3. Fresh R64[gs+0x20] -> P
        long p = memory.readPointer(gs + 0x20);

        // 4. Fresh signed R32[P+8]
        int val = memory.readInt32(p + 8);

        // 5. If negative, return 1 without child call or post-slot read
        if (val < 0) {
            return 1;
        }

        // 6. Opaque child call 424E620@425921B with rcx=E+8
        ports.call424e620(memory, 0x425921BL, E + 8);

        // 7. Fresh post-read R32[E+8]; exactly 1 returns 0, else 1
        int post = memory.readInt32(E + 8);
        return post == 1 ? 0 : 1;
    }
}