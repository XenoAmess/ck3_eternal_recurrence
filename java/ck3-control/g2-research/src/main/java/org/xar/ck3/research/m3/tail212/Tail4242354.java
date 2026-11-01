package org.xar.ck3.research.m3.tail212;

import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.tail212.TerminalTail212Api;

public final class Tail4242354 {
    private Tail4242354() { }

    public static long execute(Terminal207Api.Memory memory, TerminalTail212Api.Ports ports, long rcx) {
        // 1. XOR R8D,R8D clears whole R8 (r8d = 0)
        int r8d = 0;

        // 2. LEA EDX,[R8+2] establishes unsigned32 EDX = 2
        int edx = 2;

        // 3. JMP 42421C8 -> call tail42421c8 with site 0x424235B, unchanged rcx, edx=2, r8d=0
        return ports.tail42421c8(memory, 0x424235BL, rcx, edx, r8d);
    }
}