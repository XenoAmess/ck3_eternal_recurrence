package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class LoadRowReferenceCallee337c040203 {
    private LoadRowReferenceCallee337c040203() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {

        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();

        // SUB RSP, 0x28
        long workingRsp = rsp - 0x28;

        // MOV R10, RCX
        long r10 = entry.volatileBits().rcxBits();
        long rcx = entry.volatileBits().rcxBits();

        // MOV EDX, 1
        long edx = 1L;

        // MOV ECX, [RCX+0x14]
        long addr = rcx + 0x14;
        int val = memory.readDword(addr);
        rcx = Integer.toUnsignedLong(val);

        // INC ECX
        rcx = (rcx + 1) & 0xFFFFFFFFL;

        // CALL 0x86E160
        long callSite1 = 0x337C051L;
        long target1 = 0x86E160L;

        // Write return address to stack
        memory.writeQword(workingRsp - 8, imageBase + callSite1 + 5);

        GovernmentCrtBoundary185Api.Call call1 = new GovernmentCrtBoundary185Api.Call(
            callSite1,
            GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            target1,
            workingRsp,
            new GovernmentPrimaryTail155Api.VolatileBits(
                entry.volatileBits().raxBits(), rcx, edx, entry.volatileBits().r8Bits(),
                entry.volatileBits().r9Bits(), r10, entry.volatileBits().r11Bits(),
                entry.volatileBits().xmm0(), entry.volatileBits().xmm1(), entry.volatileBits().xmm2(),
                entry.volatileBits().xmm3(), entry.volatileBits().xmm4(), entry.volatileBits().xmm5()
            ),
            entry.nonvolatileBits()
        );

        GovernmentPrimaryTail155Api.VolatileBits v1 = calls.invoke(call1);

        // CMP EAX, 0x1F
        int eax = (int) v1.raxBits();

        // JGE 0x337C069
        if (eax >= 0x1F) {
            // Fatal branch
            // MOV RDX, R10
            long rdx = v1.r10Bits();

            // LEA RCX, [RSP+0x30]
            long rcx2 = workingRsp + 0x30;

            // CALL 0x86F210
            long callSite2 = 0x337C071L;
            long target2 = 0x86F210L;

            memory.writeQword(workingRsp - 8, imageBase + callSite2 + 5);

            GovernmentCrtBoundary185Api.Call call2 = new GovernmentCrtBoundary185Api.Call(
                callSite2,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                target2,
                workingRsp,
                new GovernmentPrimaryTail155Api.VolatileBits(
                    v1.raxBits(), rcx2, rdx, v1.r8Bits(), v1.r9Bits(), v1.r10Bits(), v1.r11Bits(),
                    v1.xmm0(), v1.xmm1(), v1.xmm2(), v1.xmm3(), v1.xmm4(), v1.xmm5()
                ),
                entry.nonvolatileBits()
            );

            GovernmentPrimaryTail155Api.VolatileBits v2 = calls.invoke(call2);

            // CALL 0x4232CF4
            long callSite3 = 0x337C076L;
            long target3 = 0x4232CF4L;

            memory.writeQword(workingRsp - 8, imageBase + callSite3 + 5);

            GovernmentCrtBoundary185Api.Call call3 = new GovernmentCrtBoundary185Api.Call(
                callSite3,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                target3,
                workingRsp,
                new GovernmentPrimaryTail155Api.VolatileBits(
                    v2.raxBits(), v2.rcxBits(), v2.rdxBits(), v2.r8Bits(), v2.r9Bits(), v2.r10Bits(), v2.r11Bits(),
                    v2.xmm0(), v2.xmm1(), v2.xmm2(), v2.xmm3(), v2.xmm4(), v2.xmm5()
                ),
                entry.nonvolatileBits()
            );

            calls.invoke(call3);

            // INT3
            throw new UnsupportedOperationException("Terminal INT3 reached");
        } else {
            // Normal branch
            // MOV EDX, EAX
            long edx2 = Integer.toUnsignedLong(eax);

            // MOV RCX, R10
            long rcx3 = v1.r10Bits();

            // ADD RSP, 0x28
            long finalRsp = workingRsp + 0x28;

            // JMP 0x337C0C0
            long jumpSite = 0x337C064L;
            long tailTarget = 0x337C0C0L;

            GovernmentCrtBoundary185Api.Tail tail = new GovernmentCrtBoundary185Api.Tail(
                jumpSite,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                tailTarget,
                new GovernmentCrtBoundary185Api.Entry(
                    imageBase,
                    finalRsp,
                    new GovernmentPrimaryTail155Api.VolatileBits(
                        v1.raxBits(), rcx3, edx2, v1.r8Bits(), v1.r9Bits(), v1.r10Bits(), v1.r11Bits(),
                        v1.xmm0(), v1.xmm1(), v1.xmm2(), v1.xmm3(), v1.xmm4(), v1.xmm5()
                    ),
                    entry.nonvolatileBits()
                )
            );

            return calls.tail(tail);
        }
    }
}