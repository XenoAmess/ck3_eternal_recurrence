package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class GovernmentSharedManager167 {

    private GovernmentSharedManager167() { }

    public static NormalReturn execute(Entry entry, GovernmentSharedManager167Api.Memory memory, Calls calls) {
        Registers r = GovernmentCallee164Api.registers(entry);
        long image = entry.imageBaseBits();
        long S = entry.frameRspBits();

        // Prologue: sub rsp, 28h
        long W = S - 0x28L;
        r.rsp = W;

        // mov rax, qword ptr gs:[58h]
        long gs58 = calls.readGsQword58();
        r.rax = gs58;

        // mov edx, 10h
        r.rdx = 0x10L;

        // mov rcx, qword ptr [rax]
        r.rcx = memory.readQword(r.rax);

        // mov eax, dword ptr [rdx+rcx]
        int val1 = memory.readDword(r.rdx + r.rcx);
        r.rax = Integer.toUnsignedLong(val1);

        // cmp dword ptr [05DC1388h], eax
        int globalVal = memory.readDword(image + 0x5DC1388L);
        boolean jgTaken = (globalVal > val1);

        if (jgTaken) {
            // jg 0000000003F8A80C
            return executeBranch2D0B4B5(r, memory, calls, image, W, S);
        }

        // lea rax, [05DC1390h]
        r.rax = image + 0x5DC1390L;

        // add rsp, 28h
        r.rsp = W + 0x28L;

        // ret
        long rip = memory.readQword(r.rsp);
        r.rsp = r.rsp + 8L;
        return new NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, r.rsp);
    }

    private static NormalReturn executeBranch2D0B4B5(Registers r, Memory memory, Calls calls, long image, long W, long S) {
        // lea rcx, [05DC1388h]
        r.rcx = image + 0x5DC1388L;

        // call 0000000004223A84
        VolatileBits vBefore1 = r.volatileBits();
        NonvolatileBits nBefore1 = r.nonvolatileBits();
        OpaqueCall call1 = new OpaqueCall(0x3F8A813L, 0x4223A84L, W, vBefore1, nBefore1);
        VolatileBits vAfter1 = calls.invoke(call1);
        r.apply(vAfter1);

        // cmp dword ptr [05DC1388h], 0FFFFFFFFh
        int globalVal2 = memory.readDword(image + 0x5DC1388L);
        boolean jneTaken = (globalVal2 != 0xFFFFFFFF);

        if (jneTaken) {
            // jne 0000000003F8A800
            // lea rax, [05DC1390h]
            r.rax = image + 0x5DC1390L;
            // add rsp, 28h
            r.rsp = W + 0x28L;
            // ret
            long rip = memory.readQword(r.rsp);
            r.rsp = r.rsp + 8L;
            return new NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, r.rsp);
        }

        // mov eax, 1
        r.rax = 1L;

        // lock xadd byte ptr [05DC1360h], al
        int oldByte = memory.lockedXaddByte(image + 0x5DC1360L, (int)r.rax);
        r.rax = Integer.toUnsignedLong(oldByte);

        // mov byte ptr [05DC1390h], al
        memory.writeByte(image + 0x5DC1390L, (int)r.rax);

        // call 0000000002D88870
        VolatileBits vBefore2 = r.volatileBits();
        NonvolatileBits nBefore2 = r.nonvolatileBits();
        OpaqueCall call2 = new OpaqueCall(0x3F8A834L, 0x2D88870L, W, vBefore2, nBefore2);
        VolatileBits vAfter2 = calls.invoke(call2);
        r.apply(vAfter2);

        // movss xmm0, dword ptr [049F6430h]
        int scalarVal = memory.readDword(image + 0x49F6430L);
        r.x0 = new GovernmentPrimaryTail155Api.Bits128(Integer.toUnsignedLong(scalarVal), 0L);

        // lea rcx, [043D7BE0h]
        r.rcx = image + 0x43D7BE0L;

        // xor edx, edx
        r.rdx = 0L;

        // mov qword ptr [05DC13A0h], rax
        memory.writeQword(image + 0x5DC13A0L, r.rax);

        // lea rax, [054E8EA8h]
        r.rax = image + 0x54E8EA8L;

        // movss dword ptr [05DC13B4h], xmm0
        memory.writeDword(image + 0x5DC13B4L, (int)r.x0.lowBits());

        // mov qword ptr [05DC13B8h], rax
        memory.writeQword(image + 0x5DC13B8L, r.rax);

        // lea rax, [054DE218h]
        r.rax = image + 0x54DE218L;

        // mov qword ptr [05DC13D0h], rax
        memory.writeQword(image + 0x5DC13D0L, r.rax);

        // mov qword ptr [05DC13A8h], rdx
        memory.writeQword(image + 0x5DC13A8L, r.rdx);

        // mov byte ptr [05DC13B0h], dl
        memory.writeByte(image + 0x5DC13B0L, (int)r.rdx);

        // mov qword ptr [05DC13C0h], rdx
        memory.writeQword(image + 0x5DC13C0L, r.rdx);

        // mov qword ptr [05DC13C8h], rdx
        memory.writeQword(image + 0x5DC13C8L, r.rdx);

        // mov dword ptr [05DC13D8h], edx
        memory.writeDword(image + 0x5DC13D8L, (int)r.rdx);

        // call 0000000004223F24
        VolatileBits vBefore3 = r.volatileBits();
        NonvolatileBits nBefore3 = r.nonvolatileBits();
        OpaqueCall call3 = new OpaqueCall(0x3F8A896L, 0x4223F24L, W, vBefore3, nBefore3);
        VolatileBits vAfter3 = calls.invoke(call3);
        r.apply(vAfter3);

        // lea rcx, [05DC1388h]
        r.rcx = image + 0x5DC1388L;

        // call 0000000004223A24
        VolatileBits vBefore4 = r.volatileBits();
        NonvolatileBits nBefore4 = r.nonvolatileBits();
        OpaqueCall call4 = new OpaqueCall(0x3F8A8A2L, 0x4223A24L, W, vBefore4, nBefore4);
        VolatileBits vAfter4 = calls.invoke(call4);
        r.apply(vAfter4);

        // lea rax, [05DC1390h]
        r.rax = image + 0x5DC1390L;

        // add rsp, 28h
        r.rsp = W + 0x28L;

        // ret
        long rip = memory.readQword(r.rsp);
        r.rsp = r.rsp + 8L;
        return new NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, r.rsp);
    }
}
