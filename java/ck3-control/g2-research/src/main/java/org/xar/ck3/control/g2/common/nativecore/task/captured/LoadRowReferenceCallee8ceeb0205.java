package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCaller153Api;

public final class LoadRowReferenceCallee8ceeb0205 {

    private static long add(long a, long b) {
        return a + b;
    }

    private static long sub(long a, long b) {
        return a - b;
    }

    private static int toInt(long v) {
        return (int) v;
    }

    private static long toUnsignedLong(int v) {
        return Integer.toUnsignedLong(v);
    }

    private static GovernmentPrimaryTail155Api.VolatileBits withRax(GovernmentPrimaryTail155Api.VolatileBits v, long rax) {
        return new GovernmentPrimaryTail155Api.VolatileBits(
            rax, v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
            v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5()
        );
    }

    private static GovernmentPrimaryTail155Api.VolatileBits withRcx(GovernmentPrimaryTail155Api.VolatileBits v, long rcx) {
        return new GovernmentPrimaryTail155Api.VolatileBits(
            v.raxBits(), rcx, v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
            v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5()
        );
    }

    private static GovernmentPrimaryTail155Api.VolatileBits withRdx(GovernmentPrimaryTail155Api.VolatileBits v, long rdx) {
        return new GovernmentPrimaryTail155Api.VolatileBits(
            v.raxBits(), v.rcxBits(), rdx, v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
            v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5()
        );
    }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {

        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();
        GovernmentPrimaryTail155Api.VolatileBits v = entry.volatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits nv = entry.nonvolatileBits();

        // 8ceeb0: sub rsp, 0x28
        long workRsp = sub(rsp, 0x28L);

        // 8ceeb4: mov rax, QWORD PTR gs:0x58
        long gs58 = calls.readGsQword58();
        v = withRax(v, gs58);

        // 8ceebd: mov edx, 0x10
        v = withRdx(v, 16L);

        // 8ceec2: mov rcx, QWORD PTR [rax]
        long rcx = memory.readQword(v.raxBits());
        v = withRcx(v, rcx);

        // 8ceec5: mov eax, DWORD PTR [rdx+rcx*1]
        long eax = toUnsignedLong(memory.readDword(add(rcx, 16L)));
        v = withRax(v, eax);

        // 8ceec8: cmp DWORD PTR [rip+0x5398502], eax
        // Global address: image + 0x5C673D0
        long globalAddr = add(imageBase, 0x5C673D0L);
        int globalVal = memory.readDword(globalAddr);
        int eaxInt = toInt(eax);

        // 8ceece: jg 0x8ceedc
        if (globalVal > eaxInt) {
            // 8ceee3: call 0x4223a84
            // 8ceedc: lea rcx, [rip+0x53984ed] # 0x5c673d0
            v = withRcx(v, globalAddr);
            // Push return address to stack before call
            long retAddr = add(imageBase, 0x8CEEE8L);
            memory.writeQword(sub(workRsp, 8L), retAddr);

            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                0x8CEEE3L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x4223A84L,
                workRsp,
                v,
                nv
            );
            v = calls.invoke(call);

            // 8ceee8: cmp DWORD PTR [rip+0x53984e1], 0xffffffff
            // Global address: image + 0x5C673D0
            int freshGuard = memory.readDword(globalAddr);

            if (freshGuard != -1) {
                // 8ceef1: jmp 0x8ceed0 (Skip footer, go to common exit)
                // Common exit: 8ceed0: lea rax, [rip+0x5398509]
                v = withRax(v, add(imageBase, 0x5C673E0L));

                // 8ceed7: add rsp, 0x28
                long finalRsp = add(workRsp, 0x28L);

                // 8ceedb: ret
                long returnRip = memory.readQword(finalRsp);
                long callerRsp = add(finalRsp, 8L);

                return new GovernmentCrtBoundary185Api.NormalReturn(v, returnRip, callerRsp, nv);
            } else {
                // 8ceef1: lea rcx, [rip+0x53984d8]
                v = withRcx(v, globalAddr);

                // 8ceef8: mov BYTE PTR [rip+0x53984e5], 0x0
                memory.writeByte(add(imageBase, 0x5C673E4L), 0);

                // 8ceeff: mov BYTE PTR [rip+0x539852e], 0xff
                memory.writeByte(add(imageBase, 0x5C67434L), 255);

                // 8cef06: call 0x4223a24
                long footerRetAddr = add(imageBase, 0x8CEF0BL);
                memory.writeQword(sub(workRsp, 8L), footerRetAddr);

                GovernmentCrtBoundary185Api.Call footerCall = new GovernmentCrtBoundary185Api.Call(
                    0x8CEF06L,
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    0x4223A24L,
                    workRsp,
                    v,
                    nv
                );
                v = calls.invoke(footerCall);

                // 8cef0b: jmp 0x8ceed0 (Common exit)
                v = withRax(v, add(imageBase, 0x5C673E0L));

                long finalRsp = add(workRsp, 0x28L);
                long returnRip = memory.readQword(finalRsp);
                long callerRsp = add(finalRsp, 8L);

                return new GovernmentCrtBoundary185Api.NormalReturn(v, returnRip, callerRsp, nv);
            }
        } else {
            // Fast path: 8ceed0: lea rax, [rip+0x5398509]
            v = withRax(v, add(imageBase, 0x5C673E0L));

            // 8ceed7: add rsp, 0x28
            long finalRsp = add(workRsp, 0x28L);

            // 8ceedb: ret
            long returnRip = memory.readQword(finalRsp);
            long callerRsp = add(finalRsp, 8L);

            return new GovernmentCrtBoundary185Api.NormalReturn(v, returnRip, callerRsp, nv);
        }
    }
}