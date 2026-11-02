package org.xar.ck3.research.m4;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
public final class MergeRangeFullState297 {
    private MergeRangeFullState297() { }
    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        long image = entry.imageBaseBits();
        long E = entry.rspBits();
        if (r.rdx == r.r8) {
            long rip = memory.readQword(E);
            return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, E + 8L, r.nonvolatileBits());
        }
        r.rsp -= 8L;
        memory.writeQword(r.rsp, r.rbx);
        r.rsp -= 0x60L;
        long G = r.rsp;
        r.r10 = r.r8;
        r.rbx = r.rcx;
        if (r.rcx == r.rdx) {
            r.rsp += 0x60L;
            r.rbx = memory.readQword(r.rsp);
            r.rsp += 8L;
            long rip = memory.readQword(r.rsp);
            r.rsp += 8L;
            return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits());
        }
        int eax = memory.readDword(r.rdx);
        r.rax = Integer.toUnsignedLong(eax);
        while (true) {
            budget.beforeStep(0x1A81AD0L, r.rbx);
            int rbxVal = memory.readDword(r.rbx);
            if (eax > rbxVal) {
                break;
            }
            r.rbx += 0x28L;
            r.r9--;
            if (r.rbx == r.rdx) {
                break;
            }
        }
        if (r.rbx == r.rdx) {
             r.rsp += 0x60L;
             r.rbx = memory.readQword(r.rsp);
             r.rsp += 8L;
             long rip = memory.readQword(r.rsp);
             r.rsp += 8L;
             return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits());
        }
        r.rcx = memory.readQword(G + 0x90L);
        memory.writeQword(G + 0x70L, r.rdi);
        while (true) {
            budget.beforeStep(0x1A81B00L, r.r10);
            r.rdi = r.r10;
            r.r8 = r.rcx;
            r.r10 -= 0x28L;
            r.rcx--;
            if (r.rdx == r.r10) {
                break;
            }
            int eax2 = memory.readDword(r.rdx - 0x28L);
            r.rax = Integer.toUnsignedLong(eax2);
            int r10Val = memory.readDword(r.r10);
            if (r10Val <= eax2) {
                continue;
            }
            r.rcx = r.rbx;
            if (r.r9 == 1L) {
                r.x0 = memory.read128(r.rbx);
                r.rdi -= r.rdx;
                r.r8 = r.rdi;
                memory.write128(G + 0x40L, r.x0);
                r.x0 = memory.read128(r.rbx + 0x10L);
                memory.write128(G + 0x50L, r.x0);
                r.x0 = new Bits128(memory.readQword(r.rbx + 0x20L), 0L);
                memory.writeQword(G + 0x78L, r.x0.lowBits());
                long preSP = r.rsp;
                long expectedRip = image + 0x1A81B4EL;
                memory.writeQword(preSP - 8L, expectedRip);
                GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                        0x1A81B49L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4226860L, preSP,
                        r.volatileBits(), r.nonvolatileBits());
                VolatileBits returnedV = calls.invoke(call);
                r.apply(returnedV);
                r.x0 = memory.read128(G + 0x40L);
                r.x1 = memory.read128(G + 0x50L);
                memory.write128(r.rdi + r.rbx, r.x0);
                r.x0 = new Bits128(memory.readQword(G + 0x78L), 0L);
                memory.write128(r.rdi + r.rbx + 0x10L, r.x1);
                memory.writeQword(r.rdi + r.rbx + 0x20L, r.x0.lowBits());
                r.rdi = memory.readQword(G + 0x70L);
                r.rsp += 0x60L;
                r.rbx = memory.readQword(r.rsp);
                r.rsp += 8L;
                long rip = memory.readQword(r.rsp);
                r.rsp += 8L;
                return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits());
            } else {
                int bl = memory.readUnsignedByte(G + 0xA8L);
                r.rax = Integer.toUnsignedLong(bl);
                memory.writeByte(G + 0xA8L, (int)r.rax);
                memory.writeQword(G + 0x90L, r.r8);
                r.r8 = r.rdi;
                r.rdi = memory.readQword(G + 0x70L);
                r.rsp += 0x60L;
                r.rbx = memory.readQword(r.rsp);
                r.rsp += 8L;
                GovernmentCrtBoundary185Api.Tail tail = new GovernmentCrtBoundary185Api.Tail(
                        0x1A81B9CL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x1A82450L,
                        new GovernmentCrtBoundary185Api.Entry(image, r.rsp, r.volatileBits(), r.nonvolatileBits()));
                GovernmentCrtBoundary185Api.NormalReturn tailReturn = calls.tail(tail);
                return tailReturn;
            }
        }
        r.x0 = memory.read128(r.rdx);
        memory.write128(G + 0x50L, r.x0);
        r.x0 = memory.read128(r.rdx + 0x10L);
        memory.write128(G + 0x40L, r.x0);
        r.x0 = new Bits128(memory.readQword(r.rdx + 0x20L), 0L);
        r.rdx -= r.rbx;
        r.r10 -= r.rdx;
        memory.writeQword(G + 0x78L, r.x0.lowBits());
        r.r8 = r.rdx;
        r.rdx = r.rbx;
        r.rcx = r.r10 + 0x28L;
        long preSP = r.rsp;
        long expectedRip = image + 0x1A81BD2L;
        memory.writeQword(preSP - 8L, expectedRip);
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                0x1A81BCDL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4226860L, preSP,
                r.volatileBits(), r.nonvolatileBits());
        VolatileBits returnedV = calls.invoke(call);
        r.apply(returnedV);
        r.x0 = memory.read128(G + 0x50L);
        r.rdi = memory.readQword(G + 0x70L);
        r.x1 = memory.read128(G + 0x40L);
        memory.write128(r.rbx, r.x0);
        r.x0 = new Bits128(memory.readQword(G + 0x78L), 0L);
        memory.write128(r.rbx + 0x10L, r.x1);
        memory.writeQword(r.rbx + 0x20L, r.x0.lowBits());
        r.rsp += 0x60L;
        r.rbx = memory.readQword(r.rsp);
        r.rsp += 8L;
        long rip = memory.readQword(r.rsp);
        r.rsp += 8L;
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits());
    }
}
