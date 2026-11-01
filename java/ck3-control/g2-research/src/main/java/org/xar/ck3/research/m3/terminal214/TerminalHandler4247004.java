package org.xar.ck3.research.m3.terminal214;

import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.Memory;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.Ports;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.Input;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.Outcome;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.NormalReturn;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.Trap;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.DispatchR8;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.DispatchRdx;

public final class TerminalHandler4247004 {
    private TerminalHandler4247004() { }

    public static Outcome execute(Memory memory, Ports ports, Input input) {
        long moduleBase = input.moduleBase();
        int codeBits = input.codeBits();
        long H = input.scratch().entryRsp();
        long B = input.scratch().bodyRsp();

        // Prologue: AND [B+78],0; MOV [B+70],1
        memory.readInt32(B + 0x78);
        memory.writeInt32(B + 0x78, 0);
        memory.write8(B + 0x70, 1);

        long rdi = 0L;
        long r13 = 0L;
        boolean r14b = true;

        // Selector
        if (codeBits == 2) {
            rdi = moduleBase + 0x5C5D308L;
        } else if (codeBits == 21) {
            rdi = moduleBase + 0x5C5D310L;
        } else if (codeBits == 6 || codeBits == 22) {
            rdi = moduleBase + 0x5C5D318L;
        } else if (codeBits == 15) {
            rdi = moduleBase + 0x5C5D320L;
        } else if (codeBits == 4 || codeBits == 8 || codeBits == 11) {
            // FC74 path
            long header = ports.call424fc74(memory, 0x424707DL, codeBits, B - 8L);
            if (header == 0L) {
                return new NormalReturn(0xFFFFFFFFL);
            }
            r13 = header;
            long tableStart = memory.readPointer(header);
            long count = memory.readPointer(moduleBase + 0x44268B0L);
            long end = tableStart + (count << 4);
            long cursor = tableStart;
            boolean found = false;
            while (cursor != end) {
                int val = memory.readInt32(cursor + 4);
                if (val == codeBits) {
                    found = true;
                    break;
                }
                cursor += 16;
            }
            if (!found) {
                long errCell = ports.call423b18c(memory, 0x42470CAL);
                memory.writeInt32(errCell, 0x16);
                ports.call4232a50(memory, 0x42470D5L);
                return new NormalReturn(0xFFFFFFFFL);
            }
            rdi = cursor + 8;
            r14b = false;
            memory.write8(B + 0x70, 0);
        } else {
            // Invalid code path
            long errCell = ports.call423b18c(memory, 0x42470CAL);
            memory.writeInt32(errCell, 0x16);
            ports.call4232a50(memory, 0x42470D5L);
            return new NormalReturn(0xFFFFFFFFL);
        }

        // AND [B+80],0
        memory.readPointer(B + 0x80);
        memory.writeInt64(B + 0x80, 0L);

        // TEST R14B
        if (r14b) {
            ports.call4247ffc(memory, 0x424711FL, 3);
        }

        // MOV RSI,[RDI]
        long rsi = memory.readPointer(rdi);

        // TEST R14B
        if (r14b) {
            long cookie = memory.readPointer(moduleBase + 0x542F0B8L);
            int shift = (int)(cookie & 0x3F);
            rsi = Long.rotateRight(rsi ^ cookie, shift);
        }

        // CMP RSI,1
        if (rsi == 1L) {
            if (r14b) {
                ports.call4248050(memory, 0x42471EDL, 3);
            }
            return new NormalReturn(0L);
        }

        // TEST RSI
        if (rsi == 0L) {
            if (r14b) {
                ports.call4248050(memory, 0x424725DL, 3);
            }
            ports.call4242354(memory, 0x4247267L, 3);
            return Trap.INT3_424726D;
        }

        // Nonzero, non-1 RSI
        // CMP EBX,11 (unsigned)
        if (codeBits <= 11) {
            // BT R12D,EBX (mask 0x910)
            if ((0x910 & (1 << codeBits)) != 0) {
                // Preprocessing block 7163..719A
                long rax = memory.readPointer(r13 + 8);
                memory.writeInt64(B + 0x80, rax);
                memory.writeInt64(B + 0x30, rax);
                memory.readPointer(r13 + 8);
                memory.writeInt64(r13 + 8, 0L);

                if (codeBits == 8) {
                    long ptr1 = ports.call424faf8(memory, 0x424717EL);
                    int val1 = memory.readInt32(ptr1 + 0x10);
                    memory.writeInt32(B + 0x78, val1);
                    memory.writeInt32(B + 0x20, val1);
                    long ptr2 = ports.call424faf8(memory, 0x424718EL);
                    memory.writeInt32(ptr2 + 0x10, 0x8C);
                }

                // Code 8 clear loop
                if (codeBits == 8) {
                    long start = memory.readPointer(moduleBase + 0x44268C0L);
                    long rax2 = (start << 4) + memory.readPointer(r13);
                    long count2 = memory.readPointer(moduleBase + 0x44268C8L);
                    long rcx2 = rax2 + (count2 << 4);
                    memory.writeInt64(B + 0x28, rax2);
                    while (rax2 != rcx2) {
                        memory.readPointer(rax2 + 8);
                        memory.writeInt64(rax2 + 8, 0L);
                        rax2 += 16;
                        memory.writeInt64(B + 0x28, rax2);
                    }
                } else {
                    // Non-code8 nonzero/non1 paths do fresh cookie read/store
                    long cookie = memory.readPointer(moduleBase + 0x542F0B8L);
                    memory.writeInt64(rdi, cookie);
                }
            } else {
                // Mask bit not set, jump to 71D1
                long cookie = memory.readPointer(moduleBase + 0x542F0B8L);
                memory.writeInt64(rdi, cookie);
            }
        } else {
            // Code > 11, jump to 71D1
            long cookie = memory.readPointer(moduleBase + 0x542F0B8L);
            memory.writeInt64(rdi, cookie);
        }

        // TEST R14B (71E3)
        if (r14b) {
            ports.call4248050(memory, 0x42471EDL, 3);
        }

        // CMP RSI,1 (71F2)
        if (rsi == 1L) {
            return new NormalReturn(0L);
        }

        // Dispatch (71FF)
        if (codeBits == 8) {
            long ptr = ports.call424faf8(memory, 0x4247204L);
            int edx = memory.readInt32(ptr + 0x10);
            long target = memory.readPointer(moduleBase + 0x43DBBA8L);
            DispatchR8 dispatch = new DispatchR8(0x4247218L, moduleBase + 0x43DBBA8L, target, rsi, codeBits, edx);
            ports.callIndirectR8(memory, dispatch);
        } else {
            long target = memory.readPointer(moduleBase + 0x43DBBA8L);
            DispatchRdx dispatch = new DispatchRdx(0x4247229L, moduleBase + 0x43DBBA8L, target, rsi, codeBits);
            ports.callIndirectRdx(memory, dispatch);
        }

        // Restoration (722B)
        if (codeBits <= 11 && (0x910 & (1 << codeBits)) != 0) {
            long rax = memory.readPointer(B + 0x80);
            memory.writeInt64(r13 + 8, rax);
            if (codeBits == 8) {
                long ptr = ports.call424faf8(memory, 0x4247247L);
                int ecx = memory.readInt32(B + 0x78);
                memory.writeInt32(ptr + 0x10, ecx);
            }
        }

        return new NormalReturn(0L);
    }
}