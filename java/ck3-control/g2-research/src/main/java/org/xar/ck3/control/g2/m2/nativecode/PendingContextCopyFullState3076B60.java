package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.control.g2.m2.nativecode.FullContext493Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

public final class PendingContextCopyFullState3076B60 {
    private PendingContextCopyFullState3076B60() { }

    public static FullCopy437Api.CallResult execute(
            FullContext493Api.Input input,
            FullContext493Api.Memory memory,
            FullContext493Api.Calls calls) {

        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();
        boolean df = input.directionFlagSet();
        GovernmentCrtBoundary185Api.LoopBudget budget = input.budget();

        // Initialize registers from entry
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(imageBase, rsp, entry.volatileBits(), entry.nonvolatileBits()));

        // 3076B60: mov qword ptr [rsp + 0x10], rbx
        memory.writeQword(r.rsp + 0x10, r.rbx);
        // 3076B65: mov qword ptr [rsp + 0x18], rsi
        memory.writeQword(r.rsp + 0x18, r.rsi);
        // 3076B6A: mov qword ptr [rsp + 8], rcx
        memory.writeQword(r.rsp + 0x08, r.rcx);
        // 3076B6F: push rdi
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.rdi);
        // 3076B70: push r14
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.r14);
        // 3076B72: push r15
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.r15);
        // 3076B74: sub rsp, 0x20
        r.rsp -= 0x20;

        // 3076B78: mov r14, rdx
        r.r14 = r.rdx;
        // 3076B7B: mov r15, rcx
        r.r15 = r.rcx;

        // 3076B7E: mov rax, qword ptr [rdx]
        r.rax = memory.readQword(r.rdx);
        // 3076B81: mov qword ptr [rcx], rax
        memory.writeQword(r.rcx, r.rax);
        // 3076B84: add rcx, 8
        r.rcx += 8;
        // 3076B88: add rdx, 8
        r.rdx += 8;

        // 3076B8C: call 0x373acf0
        df = invokeDirect(r, memory, calls, imageBase, df, 0x3076B8CL, 0x373ACF0L, 0x3076B91L);

        // 3076B92: lea rcx, [r15 + 0x170]
        r.rcx = r.r15 + 0x170;
        // 3076B99: lea rdx, [r14 + 0x170]
        r.rdx = r.r14 + 0x170;

        // 3076BA0: call 0x373acf0
        df = invokeDirect(r, memory, calls, imageBase, df, 0x3076BA0L, 0x373ACF0L, 0x3076BA5L);

        // 3076BA6: mov eax, dword ptr [r14 + 0x2d8]
        r.rax = Integer.toUnsignedLong(memory.readDword(r.r14 + 0x2d8));
        // 3076BAD: mov dword ptr [r15 + 0x2d8], eax
        memory.writeDword(r.r15 + 0x2d8, (int) r.rax);
        // 3076BB4: mov eax, dword ptr [r14 + 0x2dc]
        r.rax = Integer.toUnsignedLong(memory.readDword(r.r14 + 0x2dc));
        // 3076BBB: mov dword ptr [r15 + 0x2dc], eax
        memory.writeDword(r.r15 + 0x2dc, (int) r.rax);
        // 3076BC2: mov eax, dword ptr [r14 + 0x2e0]
        r.rax = Integer.toUnsignedLong(memory.readDword(r.r14 + 0x2e0));
        // 3076BC9: mov dword ptr [r15 + 0x2e0], eax
        memory.writeDword(r.r15 + 0x2e0, (int) r.rax);
        // 3076BD0: mov eax, dword ptr [r14 + 0x2e4]
        r.rax = Integer.toUnsignedLong(memory.readDword(r.r14 + 0x2e4));
        // 3076BD7: mov dword ptr [r15 + 0x2e4], eax
        memory.writeDword(r.r15 + 0x2e4, (int) r.rax);
        // 3076BDE: mov eax, dword ptr [r14 + 0x2e8]
        r.rax = Integer.toUnsignedLong(memory.readDword(r.r14 + 0x2e8));
        // 3076BE5: mov dword ptr [r15 + 0x2e8], eax
        memory.writeDword(r.r15 + 0x2e8, (int) r.rax);
        // 3076BEC: mov eax, dword ptr [r14 + 0x2ec]
        r.rax = Integer.toUnsignedLong(memory.readDword(r.r14 + 0x2ec));
        // 3076BF3: mov dword ptr [r15 + 0x2ec], eax
        memory.writeDword(r.r15 + 0x2ec, (int) r.rax);

        // 3076BFA: movups xmm0, xmmword ptr [r14 + 0x2f0]
        r.x0 = memory.read128(r.r14 + 0x2f0);
        // 3076C02: movups xmmword ptr [r15 + 0x2f0], xmm0
        memory.write128(r.r15 + 0x2f0, r.x0);

        // 3076C0A: movsxd rbx, dword ptr [r14 + 0x30c]
        r.rbx = (long) memory.readDword(r.r14 + 0x30c);
        // 3076C11: mov rdi, qword ptr [r14 + 0x300]
        r.rdi = memory.readQword(r.r14 + 0x300);
        // 3076C18: lea rcx, [r15 + 0x300]
        r.rcx = r.r15 + 0x300;

        // 3076C1F: call 0x105d2d0
        df = invokeDirect(r, memory, calls, imageBase, df, 0x3076C1FL, 0x105D2D0L, 0x3076C24L);

        // 3076C24: lea r9, [rdi + rbx]
        r.r9 = r.rdi + r.rbx;
        // 3076C28: mov r8, rdi
        r.r8 = r.rdi;
        // 3076C2B: mov edx, dword ptr [r15 + 0x30c]
        r.rdx = Integer.toUnsignedLong(memory.readDword(r.r15 + 0x30c));
        // 3076C32: lea rcx, [r15 + 0x300]
        r.rcx = r.r15 + 0x300;

        // 3076C39: call 0xbcb7c0
        df = invokeDirect(r, memory, calls, imageBase, df, 0x3076C39L, 0xBCB7C0L, 0x3076C3EL);

        // 3076C3F: lea rcx, [r15 + 0x330]
        r.rcx = r.r15 + 0x330;
        // 3076C46: mov rdx, r14
        r.rdx = r.r14;

        // 3076C49: call 0x2503880
        df = invokeDirect(r, memory, calls, imageBase, df, 0x3076C49L, 0x2503880L, 0x3076C4EL);

        // 3076C4F: mov rax, r15
        r.rax = r.r15;
        // 3076C52: mov rbx, qword ptr [rsp + 0x48]
        r.rbx = memory.readQword(r.rsp + 0x48);
        // 3076C57: mov rsi, qword ptr [rsp + 0x50]
        r.rsi = memory.readQword(r.rsp + 0x50);
        // 3076C5C: add rsp, 0x20
        r.rsp += 0x20;
        // 3076C60: pop r15
        r.r15 = memory.readQword(r.rsp);
        r.rsp += 8;
        // 3076C62: pop r14
        r.r14 = memory.readQword(r.rsp);
        r.rsp += 8;
        // 3076C64: pop rdi
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8;
        // 3076C65: ret
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8;

        return new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(),
                returnRip,
                r.rsp,
                r.nonvolatileBits()),
            df);
    }

    private static long unsigned(int bits) { return Integer.toUnsignedLong(bits); }

    private static boolean invokeDirect(GovernmentPrimaryTail155Api.Registers r, FullContext493Api.Memory memory,
            FullContext493Api.Calls calls, long imageBase, boolean df, long site, long target, long continuation) {
        long preSP = r.rsp;
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, preSP,
                r.volatileBits(), r.nonvolatileBits());
        GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                imageBase, preSP - 8, call.volatileBits(), call.nonvolatileBits());
        FullContext493Api.CallFrame frame = new FullContext493Api.CallFrame(call, child, df, 5, imageBase + continuation);
        memory.writeQword(child.rspBits(), frame.returnRipBits());
        r.rsp = child.rspBits();
        FullCopy437Api.CallResult result = calls.invoke(frame);
        frame.checkNormalReturn(result);
        r.apply(result.normalReturn().volatileBits());
        r.rsp = result.normalReturn().callerRspBits();
        return result.postDirectionFlagSet();
    }
}