package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

public final class GovernmentThreadHeader178 {
    private GovernmentThreadHeader178() { }

    public static GovernmentCallee164Api.NormalReturn execute(
            GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentThreadHeader178Api.Ports ports,
            GovernmentThreadHeader178Api.WaitBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(ports);
        Objects.requireNonNull(budget);

        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(entry);
        long imageBase = entry.imageBaseBits();
        long rsp = entry.frameRspBits();

        // 04223A84: push rbx
        memory.writeQword(rsp - 8, r.rbx);
        rsp -= 8;

        // 04223A86: sub rsp, 0x20
        rsp -= 0x20;

        // 04223A8A: mov rbx, rcx
        r.rbx = r.rcx;

        // 04223A8D: lea rcx, [rip + 0x1a39084] -> 0x5c5cb18
        r.rcx = imageBase + 0x5c5cb18;

        // 04223A94: call qword ptr [rip + 0x1b6a66] -> 0x43da500
        long callSiteRsp = rsp;
        memory.writeQword(rsp - 8, imageBase + 0x4223A9A);
        rsp -= 8;

        GovernmentThreadHeader178Api.IatCall iatCall = new GovernmentThreadHeader178Api.IatCall(
                0x4223A94,
                0x43da500,
                callSiteRsp,
                false,
                r.volatileBits(),
                r.nonvolatileBits()
        );

        GovernmentPrimaryTail155Api.VolatileBits vPost = ports.invokeIat(iatCall);
        r.apply(vPost);

        rsp += 8;

        while (true) {
            // 04223A9A: cmp dword ptr [rbx], 0
            int guardVal = memory.readDword(r.rbx);

            if (guardVal != 0) {
                // 04223A9D: jne 0x4223ab0
                // 04223AB0: cmp dword ptr [rbx], -1
                int guardVal2 = memory.readDword(r.rbx);

                if (guardVal2 == -1) {
                    // 04223AB3: je 0x4223aa4
                    // 04223AA4: mov ecx, 0x64
                    budget.beforeWait(0x4223AA4, r.rbx, guardVal2);
                    r.rcx = 0x64;

                    // 04223AA9: call 0x4223b30
                    long waitCallSiteRsp = rsp;
                    memory.writeQword(rsp - 8, imageBase + 0x4223AAE);
                    rsp -= 8;

                    GovernmentPrimaryTail155Api.OpaqueCall opaqueCall = new GovernmentPrimaryTail155Api.OpaqueCall(
                            0x4223AA9,
                            0x4223B30,
                            waitCallSiteRsp,
                            r.volatileBits(),
                            r.nonvolatileBits()
                    );

                    GovernmentPrimaryTail155Api.VolatileBits vWait = ports.invoke(opaqueCall);
                    r.apply(vWait);

                    rsp += 8;

                    // 04223AAE: jmp 0x4223a9a
                    continue;
                } else {
                    // 04223AB5: mov rax, qword ptr gs:[0x58]
                    r.rax = ports.readGsQword58();

                    // 04223ABE: mov ecx, dword ptr [rip + 0x1a39100] -> 0x5c5cbc4
                    r.rcx = Integer.toUnsignedLong(memory.readDword(imageBase + 0x5c5cbc4));

                    // 04223AC4: mov r8d, 0x10
                    r.r8 = 0x10;

                    // 04223ACA: mov rdx, qword ptr [rax + rcx*8]
                    r.rdx = memory.readQword(r.rax + (r.rcx * 8));

                    // 04223ACE: mov eax, dword ptr [rip + 0x120b5bc] -> 0x542f090
                    r.rax = Integer.toUnsignedLong(memory.readDword(imageBase + 0x542f090));

                    // 04223AD4: mov dword ptr [r8 + rdx], eax
                    memory.writeDword(r.r8 + r.rdx, (int) r.rax);

                    // 04223AD8: lea rcx, [rip + 0x1a39039] -> 0x5c5cb18
                    r.rcx = imageBase + 0x5c5cb18;

                    // 04223ADF: add rsp, 0x20
                    rsp += 0x20;

                    // 04223AE3: pop rbx
                    r.rbx = memory.readQword(rsp);
                    rsp += 8;

                    // 04223AE4: jmp qword ptr [rip + 0x1b6a05] -> 0x43da4f0
                    GovernmentThreadHeader178Api.IatCall tailCall = new GovernmentThreadHeader178Api.IatCall(
                            0x4223AE4,
                            0x43da4f0,
                            rsp,
                            true,
                            r.volatileBits(),
                            r.nonvolatileBits()
                    );

                    GovernmentPrimaryTail155Api.VolatileBits vTail = ports.invokeIat(tailCall);
                    r.apply(vTail);

                    long retRip = memory.readQword(rsp);
                    return new GovernmentCallee164Api.NormalReturn(
                            r.volatileBits(),
                            r.nonvolatileBits(),
                            retRip,
                            rsp + 8
                    );
                }
            } else {
                // 04223A9F: or dword ptr [rbx], 0xffffffff
                int currentGuard = memory.readDword(r.rbx);
                memory.writeDword(r.rbx, currentGuard | 0xFFFFFFFF);

                // 04223AA2: jmp 0x4223ad8
                // 04223AD8: lea rcx, [rip + 0x1a39039] -> 0x5c5cb18
                r.rcx = imageBase + 0x5c5cb18;

                // 04223ADF: add rsp, 0x20
                rsp += 0x20;

                // 04223AE3: pop rbx
                r.rbx = memory.readQword(rsp);
                rsp += 8;

                // 04223AE4: jmp qword ptr [rip + 0x1b6a05] -> 0x43da4f0
                GovernmentThreadHeader178Api.IatCall tailCall = new GovernmentThreadHeader178Api.IatCall(
                        0x4223AE4,
                        0x43da4f0,
                        rsp,
                        true,
                        r.volatileBits(),
                        r.nonvolatileBits()
                );

                GovernmentPrimaryTail155Api.VolatileBits vTail = ports.invokeIat(tailCall);
                r.apply(vTail);

                long retRip = memory.readQword(rsp);
                return new GovernmentCallee164Api.NormalReturn(
                        r.volatileBits(),
                        r.nonvolatileBits(),
                        retRip,
                        rsp + 8
                );
            }
        }
    }
}