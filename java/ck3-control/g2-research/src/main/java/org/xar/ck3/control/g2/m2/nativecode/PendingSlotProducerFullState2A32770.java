package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.control.g2.m2.nativecode.FullSlotProducer479Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

public final class PendingSlotProducerFullState2A32770 {
    private PendingSlotProducerFullState2A32770() { }

    public static FullCopy437Api.CallResult execute(
            FullSlotProducer479Api.Input input,
            FullSlotProducer479Api.Memory memory,
            FullSlotProducer479Api.Calls calls) {

        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();
        boolean df = input.directionFlagSet();
        GovernmentCrtBoundary185Api.LoopBudget budget = input.budget();

        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(imageBase, rsp, entry.volatileBits(), entry.nonvolatileBits()));

        // Prologue: save RBX, R8, push RBP, RSI, RDI, R12, R13, R14, R15, sub 0x20
        memory.writeQword(r.rsp + 0x10, r.rbx);
        memory.writeQword(r.rsp + 0x18, r.r8);
        r.rsp -= 8; memory.writeQword(r.rsp, r.rbp);
        r.rsp -= 8; memory.writeQword(r.rsp, r.rsi);
        r.rsp -= 8; memory.writeQword(r.rsp, r.rdi);
        r.rsp -= 8; memory.writeQword(r.rsp, r.r12);
        r.rsp -= 8; memory.writeQword(r.rsp, r.r13);
        r.rsp -= 8; memory.writeQword(r.rsp, r.r14);
        r.rsp -= 8; memory.writeQword(r.rsp, r.r15);
        r.rsp -= 0x20;

        // 2A32789: mov r13, r9
        r.r13 = r.r9;
        // 2A3278C: mov r12, rdx
        r.r12 = r.rdx;
        // 2A3278F: lea rbx, [rcx + 8]
        r.rbx = r.rcx + 8;
        // 2A32793: cmp byte ptr [rbx + 0x40], 0
        int flag40 = memory.readUnsignedByte(r.rbx + 0x40);
        // 2A32797: jne 0x2a3292a
        if (flag40 != 0) {
            return finishFallback(r, memory, imageBase, df);
        }
        // 2A3279D: cmp byte ptr [rbx + 0x41], 0
        int flag41 = memory.readUnsignedByte(r.rbx + 0x41);
        // 2A327A1: jne 0x2a3292a
        if (flag41 != 0) {
            return finishFallback(r, memory, imageBase, df);
        }
        // 2A327A7: cmp dword ptr [rbx + 0x38], 0xffffff
        int head = memory.readDword(r.rbx + 0x38);
        // 2A327AE: jne 0x2a327db
        if (head != 0xFFFFFF) {
            return continueAfterGrow(r, memory, imageBase, df, budget, calls);
        }

        // Grow path: 2A327B0
        // 2A327B0: mov ecx, dword ptr [rbx + 0x24]
        int capacity = memory.readDword(r.rbx + 0x24);
        r.rcx = Integer.toUnsignedLong(capacity);
        // 2A327B3: lea eax, [rcx + rcx] -> DWORD wrapping
        r.rax = Integer.toUnsignedLong((int)(r.rcx + r.rcx));
        // 2A327B6: mov edx, 0xfffffe
        r.rdx = 0xFFFFFE;
        // 2A327BB: cmp eax, 0xffffff
        // 2A327C0: cmovb edx, eax -> DWORD wrapping
        if (Integer.compareUnsigned((int) r.rax, 0xFFFFFF) < 0) {
            r.rdx = r.rax;
        }
        // 2A327C3: cmp ecx, edx
        // 2A327C5: je 0x2a3292a
        if (Integer.compareUnsigned((int) r.rcx, (int) r.rdx) == 0) {
            return finishFallback(r, memory, imageBase, df);
        }
        // 2A327CB: mov rcx, rbx
        r.rcx = r.rbx;
        // 2A327CE: call 0x1acdfb0
        df = invokeCall(r, memory, calls, imageBase, df, 0x2A327CEL, 0x1ACDFB0L, 0x2A327D3L, 5);
        // 2A327D3: test al, al
        // 2A327D5: je 0x2a3292a
        if ((r.rax & 0xFF) == 0) {
            return finishFallback(r, memory, imageBase, df);
        }

        return continueAfterGrow(r, memory, imageBase, df, budget, calls);
    }

    private static FullCopy437Api.CallResult continueAfterGrow(
            GovernmentPrimaryTail155Api.Registers r,
            FullSlotProducer479Api.Memory memory,
            long imageBase,
            boolean df,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            FullSlotProducer479Api.Calls calls) {

        // 2A327DB: mov edi, dword ptr [rbx + 0x38]
        int index = memory.readDword(r.rbx + 0x38);
        r.rdi = Integer.toUnsignedLong(index);
        // 2A327DE: mov r15d, edi
        r.r15 = Integer.toUnsignedLong((int) r.rdi);
        // 2A327E1: lea edx, [rdi + 1] -> DWORD wrapping
        r.rdx = Integer.toUnsignedLong((int)(r.rdi + 1));
        // 2A327E4: mov rcx, rbx
        r.rcx = r.rbx;
        // 2A327E7: call 0x2a321f0
        df = invokeCall(r, memory, calls, imageBase, df, 0x2A327E7L, 0x2A321F0L, 0x2A327ECL, 5);
        // 2A327EC: test al, al
        // 2A327EE: je 0x2a3292a
        if ((r.rax & 0xFF) == 0) {
            return finishFallback(r, memory, imageBase, df);
        }

        // 2A327F4: mov ecx, edi
        r.rcx = r.rdi;
        // 2A327F6: shr rcx, 0xa
        r.rcx >>>= 10;
        // 2A327FA: mov rax, qword ptr [rbx]
        r.rax = memory.readQword(r.rbx);
        // 2A327FD: mov rdx, qword ptr [rax + rcx*8]
        r.rdx = memory.readQword(r.rax + r.rcx * 8);
        // 2A32801: mov eax, edi
        r.rax = r.rdi;
        // 2A32803: and eax, 0x3ff
        r.rax &= 0x3FF;
        // 2A32808: imul r14, rax, 0x5c8
        r.r14 = r.rax * 0x5C8;
        // 2A3280F: add r14, rdx
        r.r14 += r.rdx;
        // 2A32812: mov ecx, edi
        r.rcx = r.rdi;
        // 2A32814: add rcx, rcx -> 64-bit
        r.rcx += r.rcx;
        // 2A32817: mov rdx, qword ptr [rbx + 0x18]
        r.rdx = memory.readQword(r.rbx + 0x18);
        // 2A3281B: mov eax, dword ptr [rdx + rcx*8]
        int next = memory.readDword(r.rdx + r.rcx * 8);
        r.rax = Integer.toUnsignedLong(next);
        // 2A3281E: mov dword ptr [rbx + 0x38], eax
        memory.writeDword(r.rbx + 0x38, (int) r.rax);
        // 2A32821: mov eax, dword ptr [rdx + rcx*8]
        int freshNext = memory.readDword(r.rdx + r.rcx * 8);
        r.rax = Integer.toUnsignedLong(freshNext);
        // 2A32824: cmp eax, 0xffffff
        // 2A32829: jae 0x2a32845
        if (Integer.compareUnsigned((int) r.rax, 0xFFFFFF) >= 0) {
            return continueAfterLinking(r, memory, imageBase, df, budget, calls);
        }
        // 2A3282B: add rax, rax -> 64-bit
        r.rax += r.rax;
        // 2A3282E: mov dword ptr [rdx + rax*8 + 4], 0xffffff
        memory.writeDword(r.rdx + r.rax * 8 + 4, 0xFFFFFF);
        // 2A32836: mov rax, qword ptr [rbx + 0x18]
        r.rax = memory.readQword(r.rbx + 0x18);
        // 2A3283A: mov dword ptr [rax + rcx*8], 0xffffff
        memory.writeDword(r.rax + r.rcx * 8, 0xFFFFFF);
        // 2A32841: mov rdx, qword ptr [rbx + 0x18]
        r.rdx = memory.readQword(r.rbx + 0x18);

        return continueAfterLinking(r, memory, imageBase, df, budget, calls);
    }

    private static FullCopy437Api.CallResult continueAfterLinking(
            GovernmentPrimaryTail155Api.Registers r,
            FullSlotProducer479Api.Memory memory,
            long imageBase,
            boolean df,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            FullSlotProducer479Api.Calls calls) {

        // 2A32845: inc dword ptr [rbx + 0x34]
        int count = memory.readDword(r.rbx + 0x34);
        memory.writeDword(r.rbx + 0x34, count + 1);
        // 2A32848: mov byte ptr [rbx + 0x42], 1
        memory.writeByte(r.rbx + 0x42, 1);
        // 2A3284C: mov eax, dword ptr [r14 + 0x10]
        int gen = memory.readDword(r.r14 + 0x10);
        r.rax = Integer.toUnsignedLong(gen);
        // 2A32850: and eax, 0xff000000
        r.rax &= 0xFF000000L;
        // 2A32855: add eax, 0x1000000 -> 32-bit wrap
        r.rax = Integer.toUnsignedLong((int)(r.rax + 0x1000000));
        // 2A3285A: mov qword ptr [rdx + rcx*8 + 8], r14
        memory.writeQword(r.rdx + r.rcx * 8 + 8, r.r14);
        // 2A3285F: mov ecx, dword ptr [rbx + 0x30]
        int highest = memory.readDword(r.rbx + 0x30);
        r.rcx = Integer.toUnsignedLong(highest);
        // 2A32862: cmp ecx, -1
        // 2A32865: je 0x2a3286c
        if (r.rcx == 0xFFFFFFFFL) {
            // 2A3286C: mov dword ptr [rbx + 0x30], edi
            memory.writeDword(r.rbx + 0x30, (int) r.rdi);
        } else {
            // 2A32867: cmp r15d, ecx
            // 2A3286A: jbe 0x2a3286f
            if (Integer.compareUnsigned((int) r.r15, (int) r.rcx) > 0) {
                // 2A3286C: mov dword ptr [rbx + 0x30], edi
                memory.writeDword(r.rbx + 0x30, (int) r.rdi);
            }
        }
        // 2A3286F: or r15d, eax -> DWORD wrapping
        r.r15 = Integer.toUnsignedLong((int)(r.r15 | r.rax));
        // 2A32872: mov qword ptr [rsp + 0x60], r14
        memory.writeQword(r.rsp + 0x60, r.r14);
        // 2A32877: mov rax, qword ptr [rsp + 0x88]
        r.rax = memory.readQword(r.rsp + 0x88);
        // 2A3287F: mov ebp, dword ptr [rax]
        int arg6 = memory.readDword(r.rax);
        r.rbp = Integer.toUnsignedLong(arg6);
        // 2A32881: mov rax, qword ptr [rsp + 0x80]
        r.rax = memory.readQword(r.rsp + 0x80);
        // 2A32889: movzx esi, byte ptr [rax]
        int arg5 = memory.readUnsignedByte(r.rax);
        r.rsi = arg5;
        // 2A3288C: movzx edi, byte ptr [r13]
        int arg4 = memory.readUnsignedByte(r.r13);
        r.rdi = arg4;
        // 2A32891: mov rax, qword ptr [rsp + 0x70]
        r.rax = memory.readQword(r.rsp + 0x70);
        // 2A32896: mov ebx, dword ptr [rax]
        int arg3 = memory.readDword(r.rax);
        r.rbx = Integer.toUnsignedLong(arg3);
        // 2A32898: mov dword ptr [r14 + 0x10], 0xffffffff
        memory.writeDword(r.r14 + 0x10, 0xFFFFFFFF);
        // 2A328A0: mov dword ptr [r14 + 0x14], 0x4368496e
        memory.writeDword(r.r14 + 0x14, 0x4368496E);
        // 2A328A8: lea rax, [rip + 0x1d269a1]
        r.rax = imageBase + 0x4759250L;
        // 2A328AF: mov qword ptr [r14], rax
        memory.writeQword(r.r14, r.rax);
        // 2A328B2: lea rax, [rip + 0x1d269cf]
        r.rax = imageBase + 0x4759288L;
        // 2A328B9: mov qword ptr [r14 + 8], rax
        memory.writeQword(r.r14 + 8, r.rax);
        // 2A328BD: lea rcx, [r14 + 0x18]
        r.rcx = r.r14 + 0x18;
        // 2A328C1: mov rdx, r12
        r.rdx = r.r12;
        // 2A328C4: call 0x3076b60
        df = invokeCall(r, memory, calls, imageBase, df, 0x2A328C4L, 0x3076B60L, 0x2A328C9L, 5);
        // 2A328C9: lea rcx, [r14 + 0x350]
        r.rcx = r.r14 + 0x350;
        // 2A328D0: call 0x2756120
        df = invokeCall(r, memory, calls, imageBase, df, 0x2A328D0L, 0x2756120L, 0x2A328D5L, 5);
        // 2A328D5: xor ecx, ecx
        r.rcx = 0;
        // 2A328D7: mov dword ptr [r14 + 0x5b8], ecx
        memory.writeDword(r.r14 + 0x5B8, (int) r.rcx);
        // 2A328DE: mov dword ptr [r14 + 0x5bc], ebx
        memory.writeDword(r.r14 + 0x5BC, (int) r.rbx);
        // 2A328E5: cmp dword ptr [r12 + 0x2e8], -1
        int ctxVal = memory.readDword(r.r12 + 0x2E8);
        // 2A328EE: setne cl -> writes CL only
        r.rcx = (r.rcx & ~0xFFL) | (ctxVal == -1 ? 0 : 1);
        // 2A328F1: mov dword ptr [r14 + 0x5c0], ecx
        memory.writeDword(r.r14 + 0x5C0, (int) r.rcx);
        // 2A328F8: cmp dil, 1
        // 2A328FC: sete cl -> writes CL only
        r.rcx = (r.rcx & ~0xFFL) | (r.rdi == 1 ? 1 : 0);
        // 2A328FF: mov byte ptr [r14 + 0x5c4], cl
        memory.writeByte(r.r14 + 0x5C4, (int) r.rcx);
        // 2A32906: cmp sil, 1
        // 2A3290A: sete cl -> writes CL only
        r.rcx = (r.rcx & ~0xFFL) | (r.rsi == 1 ? 1 : 0);
        // 2A3290D: mov byte ptr [r14 + 0x5c5], cl
        memory.writeByte(r.r14 + 0x5C5, (int) r.rcx);
        // 2A32914: cmp ebp, 1
        // 2A32917: sete cl -> writes CL only
        r.rcx = (r.rcx & ~0xFFL) | (r.rbp == 1 ? 1 : 0);
        // 2A3291A: mov byte ptr [r14 + 0x5c6], cl
        memory.writeByte(r.r14 + 0x5C6, (int) r.rcx);
        // 2A32921: mov dword ptr [r14 + 0x10], r15d
        memory.writeDword(r.r14 + 0x10, (int) r.r15);
        // 2A32925: mov rax, r14
        r.rax = r.r14;
        // 2A32928: jmp 0x2a32931
        return finishSuccess(r, memory, imageBase, df);
    }

    private static FullCopy437Api.CallResult finishFallback(
            GovernmentPrimaryTail155Api.Registers r,
            FullSlotProducer479Api.Memory memory,
            long imageBase,
            boolean df) {
        // 2A3292A: mov rax, qword ptr [rip + 0x32ec33f]
        r.rax = memory.readQword(imageBase + 0x5D1EC70L);
        // 2A32931: mov rbx, qword ptr [rsp + 0x68]
        r.rbx = memory.readQword(r.rsp + 0x68);
        // 2A32936: add rsp, 0x20
        r.rsp += 0x20;
        // 2A3293A: pop r15
        r.r15 = memory.readQword(r.rsp); r.rsp += 8;
        // 2A3293C: pop r14
        r.r14 = memory.readQword(r.rsp); r.rsp += 8;
        // 2A3293E: pop r13
        r.r13 = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32940: pop r12
        r.r12 = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32942: pop rdi
        r.rdi = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32943: pop rsi
        r.rsi = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32944: pop rbp
        r.rbp = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32945: ret
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8;
        return new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), returnRip, r.rsp, r.nonvolatileBits()),
            df);
    }

    private static FullCopy437Api.CallResult finishSuccess(
            GovernmentPrimaryTail155Api.Registers r,
            FullSlotProducer479Api.Memory memory,
            long imageBase,
            boolean df) {
        // 2A32931: mov rbx, qword ptr [rsp + 0x68]
        r.rbx = memory.readQword(r.rsp + 0x68);
        // 2A32936: add rsp, 0x20
        r.rsp += 0x20;
        // 2A3293A: pop r15
        r.r15 = memory.readQword(r.rsp); r.rsp += 8;
        // 2A3293C: pop r14
        r.r14 = memory.readQword(r.rsp); r.rsp += 8;
        // 2A3293E: pop r13
        r.r13 = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32940: pop r12
        r.r12 = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32942: pop rdi
        r.rdi = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32943: pop rsi
        r.rsi = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32944: pop rbp
        r.rbp = memory.readQword(r.rsp); r.rsp += 8;
        // 2A32945: ret
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8;
        return new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), returnRip, r.rsp, r.nonvolatileBits()),
            df);
    }

    private static boolean invokeCall(
            GovernmentPrimaryTail155Api.Registers r,
            FullSlotProducer479Api.Memory memory,
            FullSlotProducer479Api.Calls calls,
            long imageBase,
            boolean df,
            long site,
            long target,
            long continuation,
            int length) {

        long preSP = r.rsp;
        long childSP = preSP - 8;
        long returnRIP = imageBase + continuation;

        // Physical push
        memory.writeQword(childSP, returnRIP);

        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
            site, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, preSP,
            r.volatileBits(), r.nonvolatileBits());

        GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
            imageBase, childSP, call.volatileBits(), call.nonvolatileBits());

        FullSlotProducer479Api.CallFrame frame = new FullSlotProducer479Api.CallFrame(
            call, childEntry, df, length, returnRIP);

        FullCopy437Api.CallResult result = calls.invoke(frame);
        frame.checkNormalReturn(result);

        r.apply(result.normalReturn().volatileBits());
        r.rsp = result.normalReturn().callerRspBits();
        return result.postDirectionFlagSet();
    }
}