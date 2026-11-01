package org.xar.ck3.research.m3.abort220;

import org.xar.ck3.research.m3.abort220.TerminalAbort220Api.Memory;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api.Ports;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api.Input;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api.Trap;

public final class TerminalAbort4242284 {
    private TerminalAbort4242284() { }

    public static Trap execute(Memory memory, Ports ports, Input input) {
        long E = input.scratch().entryRsp();
        long base = input.moduleBase();
        int entryEcx = input.ecx();

        // 1. Call 42591F8@424228C with known entryECX
        int eax = ports.call42591f8(memory, 0x424228CL, entryEcx);

        // 2. Branch on low EAX == 1
        if (eax != 1) {
            // 3. Read GS60 pointer at 4242296
            long gsPointer = ports.readGs60(memory, 0x4242296L);

            // 4. Fresh R32[gsPointer+BC], unsigned shift 8 -> liveEDX
            int r32 = memory.readInt32(gsPointer + 0xBC);
            int liveEdx = r32 >>> 8;

            // 5. Check bit 0 of shifted value
            if ((liveEdx & 1) == 0) {
                // 6. Fresh R64[base+43DA798] -> call 43DA798@42422AD
                long target798 = memory.readPointer(base + 0x43DA798L);
                long liveRax = gsPointer;
                long rcxFrom798 = ports.call43da798(memory, 0x42422ADL, target798, liveRax, liveEdx);

                // 7. Fresh R64[base+43DA778] -> call 43DA778@42422B8
                long target778 = memory.readPointer(base + 0x43DA778L);
                ports.call43da778(memory, 0x42422B8L, target778, rcxFrom798, entryEcx);
            }
        }

        // 8. Converge to 42422be logic
        // Call 42422d0@42422C0 with ECX entry and child entry E = own E - 30 hex.
        long childE = E - 0x30L;
        ports.call42422d0(memory, 0x42422C0L, entryEcx, childE);

        // 9. Then 42422c5: mov ecx ebx, call 43da558@42422C7.
        long target558 = memory.readPointer(base + 0x43DA558L);
        ports.call43da558(memory, 0x42422C7L, target558, entryEcx);

        // 10. Reached INT3 at 42422CD returns explicit softwareTrap
        return Trap.INT3_42422CD;
    }
}