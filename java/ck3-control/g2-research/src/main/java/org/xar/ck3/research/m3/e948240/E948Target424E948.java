package org.xar.ck3.research.m3.e948240;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.e948240.E948Api240.Input;
import org.xar.ck3.research.m3.e948240.E948Api240.Ports;

/** Normal supplied-storage business projection; opaque callees retain their own semantics. */
public final class E948Target424E948 {
    private E948Target424E948() { }

    public static long execute(NativeTaskMemory memory, Ports ports, Input input) {
        long base = input.moduleBase();
        int entryEcxBits = input.entryEcxBits();
        long entryRdxBits = input.entryRdxBits();

        // E955: lea r9, [rip + 0x1d85dc] -> base + 0x4426F38
        long r9Bits = base + 0x4426F38L;
        // E95E: lea rdx, [rip + 0x1d22fb] -> base + 0x4420C60
        long rdxBits = base + 0x4420C60L;
        // E965: mov ecx, 6
        int ecxBits = 6;
        // E96A: lea r8, [rip + 0x1d85bf] -> base + 0x4426F30
        long r8Bits = base + 0x4426F30L;

        // E971: call 0x14424e448
        long liveRax = ports.call424e448(memory, 0x424E971L, ecxBits, rdxBits, r8Bits, r9Bits);

        // E976: mov rdx, rbx (restore entryRdxBits)
        // E979: mov ecx, edi (restore entryEcxBits)
        // E97B: test rax, rax
        if (liveRax != 0L) {
            // E980: call qword ptr [rip + 0x18d222] -> base + 0x43DBBA8
            long actualTarget = memory.readPointer(base + 0x43DBBA8L);
            return ports.callIat43dbba8(memory, 0x424E980L, actualTarget, liveRax, entryEcxBits, entryRdxBits);
        } else {
            // E988: call qword ptr [rip + 0x18bae2] -> base + 0x43DA470
            long actualTarget = memory.readPointer(base + 0x43DA470L);
            return ports.callIat43da470(memory, 0x424E988L, actualTarget, liveRax, entryEcxBits, entryRdxBits);
        }
    }
}