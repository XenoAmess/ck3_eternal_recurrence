package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/**
 * Implementation of the normal native function at RVA 0x2D1B7F0.
 * Corrected first model prototype; normal raw state and owned ports only.
 */
public final class GovernmentRowResolve164 {

    private static long u32(int bits) {
        return Integer.toUnsignedLong(bits);
    }

    /**
     * Executes the target function logic.
     * @param entry The raw entry state (RSP after CALL, registers).
     * @param memory The owned memory interface.
     * @param calls The opaque calls interface.
     * @return The result containing return RIP, caller RSP, and register states.
     */
    public static GovernmentRowResolve164Api.Result execute(
            GovernmentRowResolve164Api.Entry entry,
            Memory memory,
            Calls calls) {

        Registers r = org.xar.ck3.research.m5.GovernmentCompaction160Api.registers(
                new org.xar.ck3.research.m5.GovernmentCompaction160Api.Entry(entry.imageBaseBits(),
                        entry.calleeRspBits(), entry.volatileBits(), entry.nonvolatileBits()));

        memory.writeQword(r.rsp + 0x10L, r.rsi);
        r.rsp -= 8L;
        memory.writeQword(r.rsp, r.rdi);
        r.rsp -= 0x20L;

        int tag = memory.readUnsignedByte(r.rcx + 0x0CL);
        r.rax = u32(tag);

        r.rsi = r.rdx;
        r.rdi = r.rcx;

        if (tag != 2) {
            return executeNonFastPath(r, memory, calls, entry.imageBaseBits());
        }

        r.rax = 0L;
        r.rsi = memory.readQword(r.rsp + 0x38L);
        r.rsp += 0x20L;
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8L;
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8L;

        return new GovernmentRowResolve164Api.Result(
            returnRip,
            r.rsp,
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
    }

    private static GovernmentRowResolve164Api.Result executeNonFastPath(
            Registers r,
            Memory memory,
            Calls calls, long imageBase) {

        memory.writeQword(r.rsp + 0x30L, r.rbx);

        if ((r.rax & 0xFFL) == 0L) {
            return executeFallback(r, memory, calls, imageBase);
        }

        r.rbx = u32(memory.readDword(r.rcx + 0x08L));

        OpaqueCall call1 = new OpaqueCall(
            0x2D1B821L, // Site
            0x3F8A7E0L, // Target
            r.rsp,      // Current RSP
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v1 = calls.invoke(call1);
        r.apply(v1);

        r.rdx = u32((int)r.rbx);
        r.rcx = r.rax;

        OpaqueCall call2 = new OpaqueCall(
            0x2D1B82BL, // Site
            0x3F8A6D0L, // Target
            r.rsp,
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v2 = calls.invoke(call2);
        r.apply(v2);

        long val1 = memory.readQword(r.rax + 0x10L);
        if (val1 == 0L) {
            return executeFallback(r, memory, calls, imageBase);
        }

        r.rbx = u32(memory.readDword(r.rdi + 0x08L));
        memory.writeByte(r.rdi + 0x0CL, 2);

        OpaqueCall call3 = new OpaqueCall(
            0x2D1B83EL, // Site
            0x3F8A7E0L, // Target
            r.rsp,
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v3 = calls.invoke(call3);
        r.apply(v3);

        r.rdx = u32((int)r.rbx);
        r.rcx = r.rax;

        OpaqueCall call4 = new OpaqueCall(
            0x2D1B848L, // Site
            0x3F8A6D0L, // Target
            r.rsp,
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v4 = calls.invoke(call4);
        r.apply(v4);

        long capacity = memory.readQword(r.rax + 0x18L);
        r.r8 = u32(memory.readDword(r.rax + 0x10L));
        if (Long.compareUnsigned(capacity, 0x10L) < 0) {
            r.rdx = r.rax;
        } else {
            r.rax = memory.readQword(r.rax);
            r.rdx = r.rax;
        }

        OpaqueCall call5 = new OpaqueCall(
            0x2D1B85EL, // Site
            0x3F7E220L, // Target
            r.rsp,
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v5 = calls.invoke(call5);
        r.apply(v5);

        r.rdx = u32((int)r.rax);
        r.rcx = r.rsi;

        OpaqueCall call6 = new OpaqueCall(
            0x2D1B868L, // Site
            0xABF7E0L,  // Target
            r.rsp,
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v6 = calls.invoke(call6);
        r.apply(v6);

        r.rbx = memory.readQword(r.rsp + 0x30L);
        r.rcx = 0L;
        memory.writeQword(r.rdi, r.rax);

        int magic = memory.readDword(r.rax + 0x38L);
        int cl = (magic == 0x4744624F) ? 0 : 1;
        r.rcx = u32(cl);
        r.rax = r.rcx;

        r.rsi = memory.readQword(r.rsp + 0x38L);
        r.rsp += 0x20L;
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8L;
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8L;

        return new GovernmentRowResolve164Api.Result(
            returnRip,
            r.rsp,
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
    }

    private static GovernmentRowResolve164Api.Result executeFallback(
            Registers r,
            Memory memory,
            Calls calls, long imageBase) {

        r.rbx = memory.readQword(r.rsp + 0x30L);
        r.rsi = memory.readQword(r.rsp + 0x38L);
        memory.writeByte(r.rdi + 0x0CL, 2);
        long globalAddr = imageBase + 0x5D1E2A8L;
        r.rax = memory.readQword(globalAddr);

        memory.writeQword(r.rdi, r.rax);
        r.rax = 2L;
        r.rsp += 0x20L;
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8L;
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8L;

        return new GovernmentRowResolve164Api.Result(
            returnRip,
            r.rsp,
            new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
            new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
    }
}
