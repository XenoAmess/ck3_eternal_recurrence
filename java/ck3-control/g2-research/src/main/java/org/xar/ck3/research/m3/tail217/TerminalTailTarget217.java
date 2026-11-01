package org.xar.ck3.research.m3.tail217;

import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api.Memory;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api.Ports;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api.Input;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api.Outcome;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api.NormalReturn;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api.Trap;

public final class TerminalTailTarget217 {
    private TerminalTailTarget217() { }

    public static Outcome execute(Memory memory, Ports ports, Input input) {
        long E = input.scratch().entryRsp();
        long base = input.moduleBase();
        int ecx = input.ecx();
        int edx = input.edx();
        int r8d = input.r8d();

        // 1. Entry homes
        memory.writeInt32(E + 0x18L, r8d);
        memory.writeInt32(E + 0x10L, edx);

        // 2. Initial branch on register r8d
        if (r8d == 0) {
            // 3. IAT resolution and call
            long target = memory.readPointer(base + 0x43DA620L);
            long q = ports.call43da620(memory, 0x42421E7L, target, 0);

            if (q != 0L) {
                // 4. Validation chain
                int mz = memory.readUnsigned16(q);
                if (mz == 0x5A4D) {
                    int offset32 = memory.readInt32(q + 0x3CL);
                    long h = q + (long)offset32;
                    int sig = memory.readInt32(h);
                    if (sig == 0x4550) {
                        int word18 = memory.readUnsigned16(h + 0x18L);
                        if (word18 == 0x20B) {
                            int count84 = memory.readInt32(h + 0x84L);
                            if (Integer.compareUnsigned(count84, 0xE) > 0) {
                                int fieldF8 = memory.readInt32(h + 0xF8L);
                                if (fieldF8 != 0) {
                                    // 5. Direct callee port
                                    ports.call42422d0(memory, 0x424222AL, ecx);
                                }
                            }
                        }
                    }
                }
            }
        }

        // 6. Local writes (ordered)
        memory.write8(E + 0x20L, 0);
        memory.writeInt64(E - 0x28L, E + 0x10L);
        memory.writeInt64(E - 0x20L, E + 0x18L);
        memory.writeInt64(E - 0x18L, E + 0x20L);
        memory.writeInt32(E - 0x34L, 2);
        memory.writeInt32(E - 0x30L, 2);

        // 7. Helper call
        long rcx = E - 0x38L;
        long rdx = E - 0x30L;
        long r8 = E - 0x28L;
        long r9 = E - 0x34L;
        long helperRAX = ports.call42420c0(memory, 0x4242266L, rcx, rdx, r8, r9);

        // 8. Post-helper branch
        int freshHome = memory.readInt32(E + 0x18L);
        if (freshHome != 0) {
            return new NormalReturn(helperRAX);
        }

        // 9. Terminal call and trap
        ports.call4242284(memory, 0x424227EL, ecx);
        return Trap.INT3_4242283;
    }
}