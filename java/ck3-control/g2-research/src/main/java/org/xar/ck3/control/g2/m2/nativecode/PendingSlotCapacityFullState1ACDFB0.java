package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import static org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.*;

/** Complete held normal caller with explicit owned full state and physical stack effects. */
public final class PendingSlotCapacityFullState1ACDFB0 {
    private PendingSlotCapacityFullState1ACDFB0() { }

    public static CallResult execute(Input input, Memory memory, Calls calls) {
        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        long imageBase = entry.imageBaseBits();
        boolean df = input.directionFlagSet();
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                imageBase, entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        memory.writeQword(r.rsp + 0x10, r.rbx);
        memory.writeQword(r.rsp + 0x18, r.rbp);
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.rsi);
        r.rsp -= 0x20;
        int flag = memory.readUnsignedByte(r.rcx + 0x40);
        r.rsi = unsigned((int) r.rdx);
        r.rbp = r.rcx;
        if (flag != 0) return finishFalse(r, memory, df);
        r.rbx = unsigned(memory.readDword(r.rcx + 0x24));
        if (Integer.compareUnsigned((int) r.rdx, (int) r.rbx) <= 0) {
            r.rax = (r.rax & ~0xFFL) | 1;
            return finishAfterAl(r, memory, df);
        }
        if (Integer.compareUnsigned((int) r.rdx, 0xFFFFFF) > 0)
            return finishFalse(r, memory, df);
        memory.writeQword(r.rsp + 0x30, r.rdi);
        if ((int) r.rdx > memory.readDword(r.rcx + 0x24)) {
            r.rcx += 0x18;
            df = invokeDirect(r, memory, calls, imageBase, df, 0x1ACDFF3, 0x1ACE4B0, 0x1ACDFF8);
            r.rcx = memory.readDword(r.rbp + 0x24);
            r.rax = unsigned((int) r.rsi);
            r.rax = unsigned((int) r.rax - (int) r.rcx);
            if ((int) r.rax > 0) {
                r.rcx <<= 4;
                r.rdx = 0;
                r.rcx += memory.readQword(r.rbp + 0x18);
                r.r8 = unsigned((int) r.rax);
                r.r8 <<= 4;
                df = invokeDirect(r, memory, calls, imageBase, df, 0x1ACE015, 0x4226F10, 0x1ACE01A);
            }
        }
        r.r10 = unsigned((int) r.rsi - 1);
        memory.writeDword(r.rbp + 0x24, (int) r.rsi);
        r.rcx = unsigned((int) r.r10);
        if (Integer.compareUnsigned((int) r.r10, (int) r.rbx) >= 0) {
            r.r8 = unsigned((int) r.rsi);
            r.r11 = 0;
            while (true) {
                input.budget().beforeStep(0x1ACE030, r.rcx);
                if (Integer.compareUnsigned((int) r.rcx, (int) r.rsi) >= 0) break;
                r.rax = memory.readQword(r.rbp + 0x18);
                r.rdx = unsigned((int) r.rcx);
                r.rdx += r.rdx;
                memory.writeDword(r.rax + r.rdx * 8 + 4, 0xFFFFFF);
                r.rax = memory.readQword(r.rbp + 0x18);
                memory.writeQword(r.rax + r.rdx * 8 + 8, r.r11);
                r.r9 = memory.readQword(r.rbp + 0x18);
                if (Integer.compareUnsigned((int) r.rcx, (int) r.r10) >= 0) {
                    memory.writeDword(r.r9 + r.rdx * 8, 0xFFFFFF);
                } else {
                    r.rax = unsigned((int) r.r8);
                    r.rax += r.rax;
                    memory.writeDword(r.r9 + r.rax * 8 + 4, (int) r.rcx);
                    r.rax = memory.readQword(r.rbp + 0x18);
                    memory.writeDword(r.rax + r.rdx * 8, (int) r.r8);
                }
                r.rcx = unsigned((int) r.rcx - 1);
                r.r8 = unsigned((int) r.r8 - 1);
                if (Integer.compareUnsigned((int) r.rcx, (int) r.rbx) < 0) break;
            }
        }
        if (memory.readDword(r.rbp + 0x38) == 0xFFFFFF) {
            r.rdi = memory.readQword(r.rsp + 0x30);
            r.rax = (r.rax & ~0xFFL) | 1;
            memory.writeDword(r.rbp + 0x38, (int) r.rbx);
            return finishAfterAl(r, memory, df);
        }
        r.rdx = unsigned((int) r.rbx - 1);
        if (Integer.compareUnsigned((int) r.rdx, (int) r.rbx) < 0) {
            r.r8 = memory.readQword(r.rbp + 0x18);
            boolean found = false;
            while (true) {
                input.budget().beforeStep(0x1ACE0B0, r.rdx);
                r.rax = unsigned((int) r.rdx);
                r.rax += r.rax;
                r.rcx = unsigned((int) r.rdx);
                if (memory.readQword(r.r8 + r.rax * 8 + 8) == 0
                        && memory.readDword(r.r8 + r.rax * 8) == 0xFFFFFF) {
                    found = true;
                    break;
                }
                r.rdx = unsigned((int) r.rdx - 1);
                if (Integer.compareUnsigned((int) r.rdx, (int) r.rbx) >= 0) break;
            }
            if (found) {
                r.rcx += r.rcx;
                memory.writeDword(r.r8 + r.rcx * 8, (int) r.rbx);
                r.rcx = r.rbx;
                r.rax = memory.readQword(r.rbp + 0x18);
                r.rcx += r.rcx;
                memory.writeDword(r.rax + r.rcx * 8 + 4, (int) r.rdx);
            }
        }
        r.rdi = memory.readQword(r.rsp + 0x30);
        r.rax = (r.rax & ~0xFFL) | 1;
        return finishAfterAl(r, memory, df);
    }

    private static long unsigned(int bits) { return Integer.toUnsignedLong(bits); }

    private static boolean invokeDirect(Registers r, Memory memory, Calls calls, long imageBase,
            boolean df, long site, long target, long continuation) {
        long preSP = r.rsp;
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, preSP,
                r.volatileBits(), r.nonvolatileBits());
        GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                imageBase, preSP - 8, call.volatileBits(), call.nonvolatileBits());
        CallFrame frame = new CallFrame(call, child, df, 5, imageBase + continuation);
        memory.writeQword(child.rspBits(), frame.returnRipBits());
        r.rsp = child.rspBits();
        CallResult result = calls.invoke(frame);
        frame.checkNormalReturn(result);
        r.apply(result.normalReturn().volatileBits());
        r.rsp = result.normalReturn().callerRspBits();
        return result.postDirectionFlagSet();
    }

    private static CallResult finishFalse(Registers r, Memory memory, boolean df) {
        r.rbx = memory.readQword(r.rsp + 0x38);
        r.rax &= ~0xFFL;
        return finishRest(r, memory, df);
    }

    private static CallResult finishAfterAl(Registers r, Memory memory, boolean df) {
        r.rbx = memory.readQword(r.rsp + 0x38);
        return finishRest(r, memory, df);
    }

    private static CallResult finishRest(Registers r, Memory memory, boolean df) {
        r.rbp = memory.readQword(r.rsp + 0x40);
        r.rsp += 0x20;
        r.rsi = memory.readQword(r.rsp);
        r.rsp += 8;
        long rip = memory.readQword(r.rsp);
        r.rsp += 8;
        return new CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
    }
}
