package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

public final class GovernmentSharedRecord180 {
    private GovernmentSharedRecord180() { }

    public static GovernmentCallee164Api.NormalReturn execute(
            GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(entry);
        long image = entry.imageBaseBits();
        long S = entry.frameRspBits();

        // 02D88870: sub rsp, 0x28
        long W = S - 0x28L;
        r.rsp = W;

        // 02D88874: mov rax, qword ptr gs:[0x58]
        r.rax = calls.readGsQword58();

        // 02D8887D: mov edx, 0x10
        r.rdx = 0x10L;

        // 02D88882: mov rcx, qword ptr [rax]
        r.rcx = memory.readQword(r.rax);

        // 02D88885: mov eax, dword ptr [rdx + rcx]
        int val1 = memory.readDword(r.rdx + r.rcx);
        r.rax = Integer.toUnsignedLong(val1);

        // 02D88888: cmp dword ptr [rip + 0x2fa59ee], eax
        // Target address: image + 0x5D2E27C
        int globalVal = memory.readDword(image + 0x5D2E27CL);

        // 02D8888E: jg 0x2d8889c
        // Signed comparison: globalVal > val1
        if (globalVal > val1) {
            // Jump to 0x2D8889C
            // 02D8889C: lea rcx, [rip + 0x2fa59d9]
            // Target address: image + 0x5D2E27C
            r.rcx = image + 0x5D2E27CL;

            // 02D888A3: call 0x4223a84
            // Push return address: image + 0x2D888A8
            long returnAddr1 = image + 0x2D888A8L;
            memory.writeQword(r.rsp - 8, returnAddr1);
            r.rsp -= 8;

            GovernmentPrimaryTail155Api.OpaqueCall call1 = new GovernmentPrimaryTail155Api.OpaqueCall(
                    0x2D888A3L,
                    0x4223A84L,
                    r.rsp + 8, // Caller site RSP (before push)
                    r.volatileBits(),
                    r.nonvolatileBits()
            );

            GovernmentPrimaryTail155Api.VolatileBits vPost1 = calls.invoke(call1);
            r.apply(vPost1);

            r.rsp += 8; // Pop return address

            // 02D888A8: cmp dword ptr [rip + 0x2fa59cd], -1
            // Target address: image + 0x5D2E27C
            int globalVal2 = memory.readDword(image + 0x5D2E27CL);

            // 02D888AF: jne 0x2d88890
            if (globalVal2 != -1) {
                // Jump to 0x2D88890
                // 02D88890: lea rax, [rip + 0x2fa59e9]
                // Target address: image + 0x5D2E280
                r.rax = image + 0x5D2E280L;

                // 02D88897: add rsp, 0x28
                r.rsp = W + 0x28L;

                // 02D8889B: ret
                long rip = memory.readQword(r.rsp);
                r.rsp = r.rsp + 8L;
                return new GovernmentCallee164Api.NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, r.rsp);
            }

            // Fall through to 0x2D888B1
            // 02D888B1: lea rcx, [rip + 0x2fa59c4]
            // Target address: image + 0x5D2E27C
            r.rcx = image + 0x5D2E27CL;

            // 02D888B8: mov byte ptr [rip + 0x2fa59c5], 0
            // Target address: image + 0x5D2E284
            memory.writeByte(image + 0x5D2E284L, 0);

            // 02D888BF: mov byte ptr [rip + 0x2fa59ee], 0xff
            // Target address: image + 0x5D2E2B4
            memory.writeByte(image + 0x5D2E2B4L, 0xFF);

            // 02D888C6: call 0x4223a24
            // Push return address: image + 0x2D888CB
            long returnAddr2 = image + 0x2D888CBL;
            memory.writeQword(r.rsp - 8, returnAddr2);
            r.rsp -= 8;

            GovernmentPrimaryTail155Api.OpaqueCall call2 = new GovernmentPrimaryTail155Api.OpaqueCall(
                    0x2D888C6L,
                    0x4223A24L,
                    r.rsp + 8, // Caller site RSP (before push)
                    r.volatileBits(),
                    r.nonvolatileBits()
            );

            GovernmentPrimaryTail155Api.VolatileBits vPost2 = calls.invoke(call2);
            r.apply(vPost2);

            r.rsp += 8; // Pop return address

            // 02D888CB: jmp 0x2d88890
            // Jump to 0x2D88890
            // 02D88890: lea rax, [rip + 0x2fa59e9]
            // Target address: image + 0x5D2E280
            r.rax = image + 0x5D2E280L;

            // 02D88897: add rsp, 0x28
            r.rsp = W + 0x28L;

            // 02D8889B: ret
            long rip2 = memory.readQword(r.rsp);
            r.rsp = r.rsp + 8L;
            return new GovernmentCallee164Api.NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip2, r.rsp);
        }

        // Fall through to 0x2D88890
        // 02D88890: lea rax, [rip + 0x2fa59e9]
        // Target address: image + 0x5D2E280
        r.rax = image + 0x5D2E280L;

        // 02D88897: add rsp, 0x28
        r.rsp = W + 0x28L;

        // 02D8889B: ret
        long rip = memory.readQword(r.rsp);
        r.rsp = r.rsp + 8L;
        return new GovernmentCallee164Api.NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, r.rsp);
    }
}