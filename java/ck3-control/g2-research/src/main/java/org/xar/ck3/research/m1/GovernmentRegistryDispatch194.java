package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import java.util.Objects;

public final class GovernmentRegistryDispatch194 {
    private GovernmentRegistryDispatch194() { }

    public static GovernmentCallee164Api.NormalReturn execute(GovernmentCallee164Api.Entry entry, GovernmentPrimaryTail155Api.Memory memory, GovernmentPrimaryTail155Api.Calls calls) {
        Registers r = GovernmentCallee164Api.registers(entry);
        long imageBase = entry.imageBaseBits();
        long workRsp = entry.frameRspBits();

        // 0424DB38: mov qword ptr [rsp + 8], rbx
        memory.writeQword(workRsp + 8, r.rbx);
        // 0424DB3D: mov qword ptr [rsp + 0x20], r9
        memory.writeQword(workRsp + 0x20, r.r9);
        // 0424DB42: push rdi
        workRsp -= 8;
        memory.writeQword(workRsp, r.rdi);
        // 0424DB43: sub rsp, 0x20
        workRsp -= 0x20;

        // 0424DB47: mov rbx, r9
        r.rbx = r.r9;
        // 0424DB4A: mov rdi, r8
        r.rdi = r.r8;
        // 0424DB4D: mov ecx, dword ptr [rdx]
        r.rcx = Integer.toUnsignedLong(memory.readDword(r.rdx));

        // 0424DB4F: call 0x4247ffc
        long call1Target = 0x4247FFC;
        long call1Site = 0x424DB4F;
        long call1PreRsp = workRsp;
        memory.writeQword(call1PreRsp - 8, imageBase + 0x424DB54);
        VolatileBits v1 = calls.invoke(new OpaqueCall(call1Site, call1Target, call1PreRsp, r.volatileBits(), r.nonvolatileBits()));
        r.apply(v1);
        // workRsp remains call1PreRsp because invoke completes the call including RET

        // 0424DB54: nop
        // 0424DB55: mov rcx, rdi
        r.rcx = r.rdi;

        // 0424DB58: call 0x424dbb0
        long call2Target = 0x424DBB0;
        long call2Site = 0x424DB58;
        long call2PreRsp = workRsp;
        memory.writeQword(call2PreRsp - 8, imageBase + 0x424DB5D);
        VolatileBits v2 = calls.invoke(new OpaqueCall(call2Site, call2Target, call2PreRsp, r.volatileBits(), r.nonvolatileBits()));
        r.apply(v2);
        // workRsp remains call2PreRsp

        // 0424DB5D: mov edi, eax
        r.rdi = r.rax & 0xFFFFFFFFL;
        // 0424DB5F: mov ecx, dword ptr [rbx]
        r.rcx = Integer.toUnsignedLong(memory.readDword(r.rbx));

        // 0424DB61: call 0x4248050
        long call3Target = 0x4248050;
        long call3Site = 0x424DB61;
        long call3PreRsp = workRsp;
        memory.writeQword(call3PreRsp - 8, imageBase + 0x424DB66);
        VolatileBits v3 = calls.invoke(new OpaqueCall(call3Site, call3Target, call3PreRsp, r.volatileBits(), r.nonvolatileBits()));
        r.apply(v3);
        // workRsp remains call3PreRsp

        // 0424DB66: mov eax, edi
        r.rax = r.rdi & 0xFFFFFFFFL;
        // 0424DB68: mov rbx, qword ptr [rsp + 0x30]
        r.rbx = memory.readQword(workRsp + 0x30);
        // 0424DB6D: add rsp, 0x20
        workRsp += 0x20;
        // 0424DB71: pop rdi
        r.rdi = memory.readQword(workRsp);
        workRsp += 8;
        // 0424DB72: ret
        long returnRip = memory.readQword(workRsp);
        workRsp += 8;

        return new GovernmentCallee164Api.NormalReturn(r.volatileBits(), r.nonvolatileBits(), returnRip, workRsp);
    }
}