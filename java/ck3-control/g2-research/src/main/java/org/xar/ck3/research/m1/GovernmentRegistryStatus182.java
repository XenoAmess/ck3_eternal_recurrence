package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import java.util.Objects;

public final class GovernmentRegistryStatus182 {

    public static GovernmentCallee164Api.NormalReturn execute(
            GovernmentCallee164Api.Entry e,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls calls) {

        Objects.requireNonNull(e);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        // Initialize registers from the callee entry (post-CALL push state)
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(e);

        // 04223F24: sub rsp, 0x28
        r.rsp -= 0x28;

        // 04223F28: call 0x4223ee8
        // The call site RSP is r.rsp (after sub). CALL pushes RIP = imageBase + 0x4223F2D.
        // Real CALL pushes memory at callSiteRsp-8.
        long callSiteRsp = r.rsp;
        long pushedRip = e.imageBaseBits() + 0x4223F2DL;
        memory.writeQword(callSiteRsp - 8, pushedRip);

        // Build OpaqueCall for the nested callee
        // Metadata callSiteRva/targetRva are RVAs WITHOUT imageBase.
        // Calls.rspBits is source CALL-site RSP before push.
        GovernmentPrimaryTail155Api.OpaqueCall opaqueCall = new GovernmentPrimaryTail155Api.OpaqueCall(
                0x4223F28L, // callSiteRva
                0x4223EE8L, // targetRva
                callSiteRsp, // rspBits (source CALL-site RSP before push)
                r.volatileBits(),
                r.nonvolatileBits()
        );

        // Invoke the nested callee via Calls
        GovernmentPrimaryTail155Api.VolatileBits returnedV = calls.invoke(opaqueCall);

        // Apply returned volatile bits (normal ABI precondition preserves nonvolatile)
        r.apply(returnedV);

        // 04223F2D: neg rax
        // NEG RAX sets CF iff original full64 RAX != 0.
        long originalRax = r.rax;
        boolean cf = (originalRax != 0);
        r.rax = -r.rax;

        // 04223F30: sbb eax, eax
        // SBB EAX,EAX is EAX - EAX - CF = -CF.
        // If CF is true (1), result is -1 (0xFFFFFFFF in 32-bit). If CF is false (0), result is 0.
        // Every EAX write zeroextends high32 RAX.
        int eaxResult = cf ? -1 : 0;
        r.rax = Integer.toUnsignedLong(eaxResult);

        // 04223F32: neg eax
        // NEG EAX: EAX = -EAX.
        // If EAX was -1 (0xFFFFFFFF), -(-1) is 1. If EAX was 0, -0 is 0.
        // Zeroextends high32 RAX.
        eaxResult = -eaxResult;
        r.rax = Integer.toUnsignedLong(eaxResult);

        // 04223F34: dec eax
        // DEC EAX: EAX = EAX - 1.
        // If EAX was 1, 1-1 is 0. If EAX was 0, 0-1 is -1 (0xFFFFFFFF).
        // Zeroextends high32 RAX.
        eaxResult = eaxResult - 1;
        r.rax = Integer.toUnsignedLong(eaxResult);

        // 04223F36: add rsp, 0x28
        r.rsp += 0x28;

        // 04223F3A: ret
        // RET pops RIP from stack. The stack was modified by the CALL push.
        // We need to read the actual memory at the current RSP to get the return RIP.
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8;

        // Construct NormalReturn
        GovernmentPrimaryTail155Api.NonvolatileBits restoredN = r.nonvolatileBits();
        GovernmentPrimaryTail155Api.VolatileBits finalV = r.volatileBits();

        return new GovernmentCallee164Api.NormalReturn(
                finalV,
                restoredN,
                returnRip,
                r.rsp
        );
    }
}