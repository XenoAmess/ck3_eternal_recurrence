package org.xar.ck3.research.m3.tail249;

import org.xar.ck3.research.m3.callee246.Callee68fcApi246.Memory;
import org.xar.ck3.research.m3.tail249.Tail6670Api249.Input;
import org.xar.ck3.research.m3.tail249.Tail6670Api249.Ports;

/** Exact-width address operations for supplied storage; no process attachment. */
public final class Tail4256670249 {
    private Tail4256670249() { }

    public static void execute(Memory memory, Ports ports, Input input) {
        long base = input.moduleBase();
        long rcx = input.entryRcx();

        // 1. Unconditional atomic increment at [rcx + 0x10]
        memory.atomicAddInt32(rcx + 0x10L, 1);

        // 2. Four fresh pointer checks in source order (E0, F0, E8, 100)
        long p1 = memory.readPointer(rcx + 0xE0L);
        if (p1 != 0) {
            memory.atomicAddInt32(p1, 1);
        }

        long p2 = memory.readPointer(rcx + 0xF0L);
        if (p2 != 0) {
            memory.atomicAddInt32(p2, 1);
        }

        long p3 = memory.readPointer(rcx + 0xE8L);
        if (p3 != 0) {
            memory.atomicAddInt32(p3, 1);
        }

        long p4 = memory.readPointer(rcx + 0x100L);
        if (p4 != 0) {
            memory.atomicAddInt32(p4, 1);
        }

        // 3. Six iterations with cursor initialized once
        long cursor = rcx + 0x38L;
        long sentinel = base + 0x542F498L;
        long liveRdx = 0L; // Initialized to satisfy compiler, overwritten in loop

        for (int i = 0; i < 6; i++) {
            // Per-iteration LEA liveRDX reset (sentinel address calculation, no memory read)
            liveRdx = sentinel;

            // First independent guard/load/INC sequence
            long guard1 = memory.readPointer(cursor - 0x10L);
            if (guard1 != sentinel) {
                long candidate1 = memory.readPointer(cursor);
                liveRdx = candidate1; // Overwrite liveRdx even if zero
                if (candidate1 != 0) {
                    memory.atomicAddInt32(candidate1, 1);
                }
            }

            // Second independent guard/load/INC sequence
            long guard2 = memory.readPointer(cursor - 0x18L);
            if (guard2 != 0) {
                long candidate2 = memory.readPointer(cursor - 0x8L);
                liveRdx = candidate2; // Overwrite liveRdx even if zero
                if (candidate2 != 0) {
                    memory.atomicAddInt32(candidate2, 1);
                }
            }

            // Advance cursor and decrement counter
            cursor += 0x20L;
        }

        // 4. Final fresh RCX and opaque tail transfer
        long finalRcx = memory.readPointer(rcx + 0x120L);
        long finalRax = cursor; // Advanced cursor after 6 iterations
        long finalR8 = 0L;      // Counter exhausted

        // Pass four actual full64 values in API order; R9 is unknown and omitted
        ports.tail4256874(memory, 0x42566F6L, finalRcx, liveRdx, finalRax, finalR8);
    }
}