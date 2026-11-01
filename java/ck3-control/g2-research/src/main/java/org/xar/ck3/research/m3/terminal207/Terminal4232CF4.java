package org.xar.ck3.research.m3.terminal207;

import org.xar.ck3.research.m3.terminal207.Terminal207Api.Memory;
import org.xar.ck3.research.m3.terminal207.Terminal207Api.Ports;
import org.xar.ck3.research.m3.terminal207.Terminal207Api.Stop;

public final class Terminal4232CF4 {
    private Terminal4232CF4() { }

    public static Stop trace(Memory memory, Ports ports, long moduleBase) {
        return traceInternal(memory, ports, moduleBase, false, 0L);
    }

    public static Stop trace(Memory memory, Ports ports, long moduleBase, long terminalEntryRsp) {
        return traceInternal(memory, ports, moduleBase, true, terminalEntryRsp);
    }

    private static Stop traceInternal(Memory memory, Ports ports, long moduleBase, boolean hasContext, long terminalEntryRsp) {
        // 1. CALL 4246FB4 (site 0x4232CF8)
        long rawRAX;
        if (hasContext) {
            long S = terminalEntryRsp - 0x30L;
            rawRAX = ports.call4246fb4(memory, 0x4232CF8L, S);
        } else {
            rawRAX = ports.call4246fb4(memory, 0x4232CF8L);
        }

        // 2. TEST RAX,RAX (full 64-bit check)
        if (rawRAX != 0L) {
            // 3. CALL 4247004 (site 0x4232D07) with ECX=0x16
            if (hasContext) {
                ports.call4247004(memory, 0x4232D07L, 0x16, terminalEntryRsp - 0x30L);
            } else {
                ports.call4247004(memory, 0x4232D07L, 0x16);
            }
        }

        // 4. TEST BYTE PTR [RIP+0x11FC4F5], 0x2
        //    Address is moduleBase + 0x542F208
        int flagByte = memory.readUnsigned8(moduleBase + 0x542F208L);
        boolean isSet = (flagByte & 0x2) != 0;

        if (!isSet) {
            // 5. JE 0x4232D3F -> CALL 4242354 (site 0x4232D44) with ECX=3
            if (hasContext) {
                ports.call4242354(memory, 0x4232D44L, 3, terminalEntryRsp - 0x30L);
            } else {
                ports.call4242354(memory, 0x4232D44L, 3);
            }
            // 6. INT3 at 0x4232D49
            return Stop.INT3_4232D49;
        }

        // 7. CALL QWORD PTR [RIP+0x1A7538] (site 0x4232D1A)
        //    Address is moduleBase + 0x43DA258
        long actualCode = memory.readPointer(moduleBase + 0x43DA258L);
        int rawEAX = ports.call43da258(memory, 0x4232D1AL, actualCode, 0x17);

        if (rawEAX != 0) {
            // 8. Nonzero EAX reaches INT 0x29 with ECX=7; JE skips to 0x4232D2B.
            return Stop.INT29_ECX7;
        }

        // 9. CALL 423283C (site 0x4232D3A)
        //    Args: ECX=3, EDX=0x40000015, R8D=1
        if (hasContext) {
            ports.call423283c(memory, 0x4232D3AL, 3, 0x40000015, 1, terminalEntryRsp - 0x30L);
        } else {
            ports.call423283c(memory, 0x4232D3AL, 3, 0x40000015, 1);
        }

        // 10. CALL 4242354 (site 0x4232D44) with ECX=3
        if (hasContext) {
            ports.call4242354(memory, 0x4232D44L, 3, terminalEntryRsp - 0x30L);
        } else {
            ports.call4242354(memory, 0x4232D44L, 3);
        }

        // 11. INT3 at 0x4232D49
        return Stop.INT3_4232D49;
    }
}