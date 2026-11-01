package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api;

public final class PendingSlotArrayReserveFullState1ACE4B0 {
    private PendingSlotArrayReserveFullState1ACE4B0() { }

    public static PendingSlotCapacityFullState412Api.CallResult execute(
            PendingSlotCapacityFullState412Api.Input input,
            PendingSlotCapacityFullState412Api.Memory memory,
            PendingSlotCapacityFullState412Api.Calls calls) {

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();
        boolean df = input.directionFlagSet();
        GovernmentCrtBoundary185Api.LoopBudget budget = input.budget();


        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(imageBase, rsp, entry.volatileBits(), entry.nonvolatileBits()));

        memory.writeQword(r.rsp + 0x18, r.rbx);

        r.rsp -= 8;
        memory.writeQword(r.rsp, r.rdi);

        r.rsp -= 0x20;

        r.rbx = r.rcx;

        r.rdi = Integer.toUnsignedLong((int) r.rdx);

        int currentCapacity = memory.readDword(r.rcx + 0x8);
        if ((int) r.rdx <= currentCapacity) {
            return epilogue(r, imageBase, memory, calls, df);
        }

        r.rcx = memory.readQword(r.rcx + 0x10);

        r.rdx = r.rdi;

        memory.writeQword(r.rsp + 0x30, r.rbp);

        r.r8 = 8;

        r.rdx <<= 4;

        memory.writeQword(r.rsp + 0x38, r.rsi);

        r.rax = memory.readQword(r.rcx);

        long targetAddr = memory.readQword(r.rax + 0x8);

        long preSP = r.rsp;
        long childRSP = preSP - 8;

        long returnRIP = imageBase + 0x1ACE4E4L;
        memory.writeQword(childRSP, returnRIP);

        GovernmentCrtBoundary185Api.Call callObj = new GovernmentCrtBoundary185Api.Call(
            0x1ACE4E1L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, targetAddr, preSP, r.volatileBits(), r.nonvolatileBits());

        GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
            imageBase, childRSP, r.volatileBits(), r.nonvolatileBits());

        PendingSlotCapacityFullState412Api.CallFrame frame = new PendingSlotCapacityFullState412Api.CallFrame(
            callObj, childEntry, df, 3, returnRIP);

        PendingSlotCapacityFullState412Api.CallResult result = calls.invoke(frame);
        frame.checkNormalReturn(result);

        r.apply(result.normalReturn().volatileBits());
        r.rsp = result.normalReturn().callerRspBits();
        df = result.postDirectionFlagSet();

        r.rsi = (long) memory.readDword(r.rbx + 0xc);

        r.rbp = r.rax;

        if (r.rsi <= 0) {
            r.rcx = memory.readQword(r.rbx + 0x10);
            r.r8 = 8;
            r.rdx = memory.readQword(r.rbx);
            r.rax = memory.readQword(r.rcx);
            long targetAddr2 = memory.readQword(r.rax + 0x10);

            long preSP2 = r.rsp;
            long childRSP2 = preSP2 - 8;
            long returnRIP2 = imageBase + 0x1ACE517L;
            memory.writeQword(childRSP2, returnRIP2);

            GovernmentCrtBoundary185Api.Call callObj2 = new GovernmentCrtBoundary185Api.Call(
                0x1ACE514L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, targetAddr2, preSP2, r.volatileBits(), r.nonvolatileBits());

            GovernmentCrtBoundary185Api.Entry childEntry2 = new GovernmentCrtBoundary185Api.Entry(
                imageBase, childRSP2, r.volatileBits(), r.nonvolatileBits());

            PendingSlotCapacityFullState412Api.CallFrame frame2 = new PendingSlotCapacityFullState412Api.CallFrame(
                callObj2, childEntry2, df, 3, returnRIP2);

            PendingSlotCapacityFullState412Api.CallResult result2 = calls.invoke(frame2);
            frame2.checkNormalReturn(result2);

            r.apply(result2.normalReturn().volatileBits());
            r.rsp = result2.normalReturn().callerRspBits();
            df = result2.postDirectionFlagSet();

            memory.writeQword(r.rbx, r.rbp);
            r.rbp = memory.readQword(r.rsp + 0x30);
            memory.writeDword(r.rbx + 0xc, (int) r.rsi);
            r.rsi = memory.readQword(r.rsp + 0x38);
            memory.writeDword(r.rbx + 0x8, (int) r.rdi);

            return epilogue(r, imageBase, memory, calls, df);
        }

        r.rdx = memory.readQword(r.rbx);
        r.r8 = r.rsi;
        r.r8 <<= 4;
        r.rcx = r.rax;
        long preSP3 = r.rsp;
        long childRSP3 = preSP3 - 8;
        long returnRIP3 = imageBase + 0x1ACE501L;
        memory.writeQword(childRSP3, returnRIP3);

        GovernmentCrtBoundary185Api.Call callObj3 = new GovernmentCrtBoundary185Api.Call(
            0x1ACE4FCL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4226860L, preSP3, r.volatileBits(), r.nonvolatileBits());

        GovernmentCrtBoundary185Api.Entry childEntry3 = new GovernmentCrtBoundary185Api.Entry(
            imageBase, childRSP3, r.volatileBits(), r.nonvolatileBits());

        PendingSlotCapacityFullState412Api.CallFrame frame3 = new PendingSlotCapacityFullState412Api.CallFrame(
            callObj3, childEntry3, df, 5, returnRIP3);

        PendingSlotCapacityFullState412Api.CallResult result3 = calls.invoke(frame3);
        frame3.checkNormalReturn(result3);

        r.apply(result3.normalReturn().volatileBits());
        r.rsp = result3.normalReturn().callerRspBits();
        df = result3.postDirectionFlagSet();

        r.rsi = Integer.toUnsignedLong(memory.readDword(r.rbx + 0xc));

        r.rcx = memory.readQword(r.rbx + 0x10);
        r.r8 = 8;
        r.rdx = memory.readQword(r.rbx);
        r.rax = memory.readQword(r.rcx);
        long targetAddr4 = memory.readQword(r.rax + 0x10);

        long preSP4 = r.rsp;
        long childRSP4 = preSP4 - 8;
        long returnRIP4 = imageBase + 0x1ACE517L;
        memory.writeQword(childRSP4, returnRIP4);

        GovernmentCrtBoundary185Api.Call callObj4 = new GovernmentCrtBoundary185Api.Call(
            0x1ACE514L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, targetAddr4, preSP4, r.volatileBits(), r.nonvolatileBits());

        GovernmentCrtBoundary185Api.Entry childEntry4 = new GovernmentCrtBoundary185Api.Entry(
            imageBase, childRSP4, r.volatileBits(), r.nonvolatileBits());

        PendingSlotCapacityFullState412Api.CallFrame frame4 = new PendingSlotCapacityFullState412Api.CallFrame(
            callObj4, childEntry4, df, 3, returnRIP4);

        PendingSlotCapacityFullState412Api.CallResult result4 = calls.invoke(frame4);
        frame4.checkNormalReturn(result4);

        r.apply(result4.normalReturn().volatileBits());
        r.rsp = result4.normalReturn().callerRspBits();
        df = result4.postDirectionFlagSet();

        memory.writeQword(r.rbx, r.rbp);
        r.rbp = memory.readQword(r.rsp + 0x30);
        memory.writeDword(r.rbx + 0xc, (int) r.rsi);
        r.rsi = memory.readQword(r.rsp + 0x38);
        memory.writeDword(r.rbx + 0x8, (int) r.rdi);

        return epilogue(r, imageBase, memory, calls, df);
    }

    private static PendingSlotCapacityFullState412Api.CallResult epilogue(
            GovernmentPrimaryTail155Api.Registers r,
            long imageBase,
            PendingSlotCapacityFullState412Api.Memory memory,
            PendingSlotCapacityFullState412Api.Calls calls,
            boolean df) {

        r.rbx = memory.readQword(r.rsp + 0x40);
        r.rsp += 0x20;
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8;
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8;

        return new PendingSlotCapacityFullState412Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(),
                returnRip,
                r.rsp,
                r.nonvolatileBits()),
            df);
    }
}
