package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentCompaction160Api;

public final class GovernmentLookup167 {

    private static long u32(int bits) {
        return Integer.toUnsignedLong(bits);
    }

    public static GovernmentLookup167Api.Result execute(
            GovernmentLookup167Api.Entry entry, Memory memory, Calls calls,
            GovernmentLookup167Api.SpinBudget spinBudget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(spinBudget);
        Registers r = GovernmentCompaction160Api.registers(new GovernmentCompaction160Api.Entry(
                entry.imageBaseBits(), entry.calleeRspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        r.rsp -= 0x28L;
        r.rax = 2L;
        r.rax = u32(memory.lockedXaddDword(r.rcx + 0x48L, (int)r.rax));
        r.r8 = 0xFFFFFFFEL;
        if ((r.rax & 1L) != 0L) {
            while (true) {
                spinBudget.beforeStep(0x3F8A6F0L, r.rcx + 0x48L);
                r.rax = u32((int)r.r8);
                r.rax = u32(memory.lockedXaddDword(r.rcx + 0x48L, (int)r.rax));
                while (true) {
                    spinBudget.beforeStep(0x3F8A6F8L, r.rcx + 0x48L);
                    r.rax = u32(memory.readDword(r.rcx + 0x48L));
                    if ((r.rax & 1L) == 0L) break;
                }
                r.rax = 2L;
                r.rax = u32(memory.lockedXaddDword(r.rcx + 0x48L, (int)r.rax));
                if ((r.rax & 1L) == 0L) break;
            }
        }
        return finish(r, memory, calls, spinBudget, entry.imageBaseBits(), 0x3F8A711L);
    }

    private static GovernmentLookup167Api.Result finish(
            Registers r, Memory memory, Calls calls, GovernmentLookup167Api.SpinBudget spinBudget, long imageBase, long targetRip) {

        if (targetRip == 0x3F8A711L) {
            r.rdx &= 0xFFFFFFL;

            r.rax = u32(memory.readDword(r.rcx + 0x3CL));

            int priorVal = memory.lockedXaddDword(r.rcx + 0x48L, (int)r.r8);
            r.r8 = u32(priorVal);

            int edxSigned = (int)r.rdx;
            int eaxSigned = (int)r.rax;
            if (edxSigned >= eaxSigned) {
                return handle3F8A733(r, memory, calls, spinBudget, imageBase);
            }

            r.rax = r.rdx;

            r.rax <<= 5;

            r.rax += memory.readQword(r.rcx + 0x30L);

            r.rsp += 0x28L;

            long returnRip = memory.readQword(r.rsp);
            r.rsp += 8L;

            return new GovernmentLookup167Api.Result(
                    returnRip,
                    r.rsp,
                    new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
                    new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
            );
        }

        throw new UnsupportedOperationException("Unexpected target RIP: " + Long.toHexString(targetRip));
    }

    private static GovernmentLookup167Api.Result handle3F8A733(
            Registers r, Memory memory, Calls calls, GovernmentLookup167Api.SpinBudget spinBudget, long imageBase) {

        r.rdx = 0x10L;

        r.rax = calls.readGsQword58();

        r.rcx = memory.readQword(r.rax);

        r.rax = u32(memory.readDword(r.rdx + r.rcx));

        int globalVal = memory.readDword(imageBase + 0x5DC1364L);
        int eaxSigned = (int)r.rax;
        if (globalVal > eaxSigned) {
            return handle3F8A75B(r, memory, calls, spinBudget, imageBase);
        }

        r.rax = imageBase + 0x5DC1368L;

        r.rsp += 0x28L;

        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8L;

        return new GovernmentLookup167Api.Result(
                returnRip,
                r.rsp,
                new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
                new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
    }

    private static GovernmentLookup167Api.Result handle3F8A75B(
            Registers r, Memory memory, Calls calls, GovernmentLookup167Api.SpinBudget spinBudget, long imageBase) {

        r.rcx = imageBase + 0x5DC1364L;

        OpaqueCall call1 = new OpaqueCall(
                0x3F8A762L,
                0x4223A84L,
                r.rsp,
                new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
                new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v1 = calls.invoke(call1);
        r.apply(v1);

        int globalVal = memory.readDword(imageBase + 0x5DC1364L);
        if (globalVal != 0xFFFFFFFF) {
            r.rax = imageBase + 0x5DC1368L;
            r.rsp += 0x28L;
            long returnRip = memory.readQword(r.rsp);
            r.rsp += 8L;
            return new GovernmentLookup167Api.Result(
                    returnRip,
                    r.rsp,
                    new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
                    new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
            );
        }

        memory.writeQword(imageBase + 0x5DC1368L, 0L);

        r.x0 = memory.read128(imageBase + 0x49F6EE0L);

        memory.write128(imageBase + 0x5DC1378L, r.x0);

        r.rcx = 0x20L;

        OpaqueCall call2 = new OpaqueCall(
                0x3F8A790L,
                0x856DB0L,
                r.rsp,
                new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
                new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v2 = calls.invoke(call2);
        r.apply(v2);

        r.x0 = memory.read128(imageBase + 0x49F6EF0L);

        memory.write128(imageBase + 0x5DC1378L, r.x0);

        r.x0 = memory.read128(imageBase + 0x49B95B0L);

        memory.write128(r.rax, r.x0);

        memory.writeByte(r.rax + 0x10L, 0);

        memory.writeQword(imageBase + 0x5DC1368L, r.rax);

        r.rcx = imageBase + 0x43D7BD0L;

        OpaqueCall call3 = new OpaqueCall(
                0x3F8A7C1L,
                0x4223F24L,
                r.rsp,
                new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
                new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v3 = calls.invoke(call3);
        r.apply(v3);


        r.rcx = imageBase + 0x5DC1364L;

        OpaqueCall call4 = new OpaqueCall(
                0x3F8A7CEL,
                0x4223A24L,
                r.rsp,
                new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
                new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
        VolatileBits v4 = calls.invoke(call4);
        r.apply(v4);

        r.rax = imageBase + 0x5DC1368L;

        r.rsp += 0x28L;

        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8L;

        return new GovernmentLookup167Api.Result(
                returnRip,
                r.rsp,
                new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11, r.x0, r.x1, r.x2, r.x3, r.x4, r.x5),
                new NonvolatileBits(r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6)
        );
    }
}
