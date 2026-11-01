package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedVector565Api;
import java.util.Objects;

public final class EmbeddedVectorFullState260E040 {
    private EmbeddedVectorFullState260E040() { }

    public static FullCopy437Api.CallResult execute(
            FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            EmbeddedVector565Api.Calls calls
    ) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        GovernmentCrtBoundary185Api.LoopBudget budget = input.budget();
        long imageBase = entry.imageBaseBits();
        long E = entry.rspBits();
        long W = E - 0x28L;
        long J = E - 0x30L;

        GovernmentCallee164Api.Entry calleeEntry = new GovernmentCallee164Api.Entry(
            imageBase, E, entry.volatileBits(), entry.nonvolatileBits()
        );
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(calleeEntry);
        boolean df = input.directionFlagSet();

        // 260E040: PUSH RSI
        memory.writeQword(E - 8L, r.rsi);
        // 260E042: SUB RSP, 0x20
        r.rsp = W;

        // 260E046: RSI = RCX
        long D = r.rcx;
        r.rsi = D;

        // 260E049: CMP RCX, RDX
        long S = r.rdx;
        boolean equal = (D == S);

        if (equal) {
            // 260E04C: JE 0x260E132
            // 260E132: RAX = RSI
            r.rax = r.rsi;
            // 260E135: ADD RSP, 0x20
            r.rsp = E - 8L;
            // 260E139: POP RSI
            r.rsi = memory.readQword(E - 8L);
            // 260E13A: RET
            long retRip = memory.readQword(E);
            long callerRsp = E + 8L;

            GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), retRip, callerRsp, r.nonvolatileBits()
            );
            return new FullCopy437Api.CallResult(nr, df);
        }

        // Non-equal path
        // 260E052: MOV Q[W+0x30], RBX
        memory.writeQword(W + 0x30L, r.rbx);

        // 260E057: MOV EBX, DWORD[S+0xC]
        int ebx = memory.readDword(S + 0xC);
        r.rbx = Integer.toUnsignedLong(ebx);

        // 260E05A: MOV Q[W+0x40], RDI
        memory.writeQword(W + 0x40L, r.rdi);

        // 260E05F: MOV RDI, Q[S]
        long P = memory.readQword(S);
        r.rdi = P;

        // 260E062: MOV DWORD[D+0xC], 0
        memory.writeDword(D + 0xC, 0);

        // 260E069: TEST EBX, EBX
        // 260E06B: JLE 0x260E0F4
        if (ebx <= 0) {
            // 260E0F4: MOV DWORD[currentRCX+0xC], EBX
            memory.writeDword(D + 0xC, ebx);
            // 260E0F7: TEST EBX, EBX
            // 260E0F9: JLE 0x260E11F
            if (ebx <= 0) {
                // 260E11F: MOV RBX, Q[W+0x30]
                r.rbx = memory.readQword(W + 0x30L);
                // 260E124: MOV RAX, RSI
                r.rax = r.rsi;
                // 260E127: MOV RDI, Q[W+0x40]
                r.rdi = memory.readQword(W + 0x40L);
                // 260E12C: ADD RSP, 0x20
                r.rsp = E - 8L;
                // 260E130: POP RSI
                r.rsi = memory.readQword(E - 8L);
                // 260E131: RET
                long retRip = memory.readQword(E);
                long callerRsp = E + 8L;

                GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
                    r.volatileBits(), retRip, callerRsp, r.nonvolatileBits()
                );
                return new FullCopy437Api.CallResult(nr, df);
            }

            // 260E0FB: MOV RAX, Q[RSI]
            r.rax = memory.readQword(r.rsi);
            // 260E0FE: XCHG AX, AX
            // 260E100: Final copy loop
            long dstPtr = r.rax;
            long srcPtr = P;
            int count = ebx;
            while (count > 0) {
                budget.beforeStep(0x260E100L, srcPtr);

                GovernmentPrimaryTail155Api.Bits128 xmm0 = memory.read128(srcPtr);
                r.x0 = xmm0;

                count--;
                r.rbx = Integer.toUnsignedLong(count);

                dstPtr += 0x18L;
                r.rax = dstPtr;

                srcPtr += 0x18L;
                r.rdi = srcPtr;

                memory.write128(dstPtr - 0x18L, xmm0);

                long low64 = memory.readQword(srcPtr - 8L);
                r.x1 = new GovernmentPrimaryTail155Api.Bits128(low64, 0L);

                memory.writeQword(dstPtr - 8L, low64);
            }

            // 260E11F: MOV RBX, Q[W+0x30]
            r.rbx = memory.readQword(W + 0x30L);
            // 260E124: MOV RAX, RSI
            r.rax = r.rsi;
            // 260E127: MOV RDI, Q[W+0x40]
            r.rdi = memory.readQword(W + 0x40L);
            // 260E12C: ADD RSP, 0x20
            r.rsp = E - 8L;
            // 260E130: POP RSI
            r.rsi = memory.readQword(E - 8L);
            // 260E131: RET
            long retRip = memory.readQword(E);
            long callerRsp = E + 8L;

            GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), retRip, callerRsp, r.nonvolatileBits()
            );
            return new FullCopy437Api.CallResult(nr, df);
        }

        // Signed C > 0: check capacity
        // 260E071: CMP EBX, DWORD[D+8]
        int capacity = memory.readDword(D + 8);
        // 260E074: JLE 0x260E0F4
        if (ebx <= capacity) {
            // 260E0F4: MOV DWORD[currentRCX+0xC], EBX
            memory.writeDword(D + 0xC, ebx);
            // 260E0F7: TEST EBX, EBX
            // 260E0F9: JLE 0x260E11F
            if (ebx <= 0) {
                // 260E11F: MOV RBX, Q[W+0x30]
                r.rbx = memory.readQword(W + 0x30L);
                // 260E124: MOV RAX, RSI
                r.rax = r.rsi;
                // 260E127: MOV RDI, Q[W+0x40]
                r.rdi = memory.readQword(W + 0x40L);
                // 260E12C: ADD RSP, 0x20
                r.rsp = E - 8L;
                // 260E130: POP RSI
                r.rsi = memory.readQword(E - 8L);
                // 260E131: RET
                long retRip = memory.readQword(E);
                long callerRsp = E + 8L;

                GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
                    r.volatileBits(), retRip, callerRsp, r.nonvolatileBits()
                );
                return new FullCopy437Api.CallResult(nr, df);
            }

            // 260E0FB: MOV RAX, Q[RSI]
            r.rax = memory.readQword(r.rsi);
            // 260E0FE: XCHG AX, AX
            // 260E100: Final copy loop
            long dstPtr = r.rax;
            long srcPtr = P;
            int count = ebx;
            while (count > 0) {
                budget.beforeStep(0x260E100L, srcPtr);

                GovernmentPrimaryTail155Api.Bits128 xmm0 = memory.read128(srcPtr);
                r.x0 = xmm0;

                count--;
                r.rbx = Integer.toUnsignedLong(count);

                dstPtr += 0x18L;
                r.rax = dstPtr;

                srcPtr += 0x18L;
                r.rdi = srcPtr;

                memory.write128(dstPtr - 0x18L, xmm0);

                long low64 = memory.readQword(srcPtr - 8L);
                r.x1 = new GovernmentPrimaryTail155Api.Bits128(low64, 0L);

                memory.writeQword(dstPtr - 8L, low64);
            }

            // 260E11F: MOV RBX, Q[W+0x30]
            r.rbx = memory.readQword(W + 0x30L);
            // 260E124: MOV RAX, RSI
            r.rax = r.rsi;
            // 260E127: MOV RDI, Q[W+0x40]
            r.rdi = memory.readQword(W + 0x40L);
            // 260E12C: ADD RSP, 0x20
            r.rsp = E - 8L;
            // 260E130: POP RSI
            r.rsi = memory.readQword(E - 8L);
            // 260E131: RET
            long retRip = memory.readQword(E);
            long callerRsp = E + 8L;

            GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), retRip, callerRsp, r.nonvolatileBits()
            );
            return new FullCopy437Api.CallResult(nr, df);
        }

        // Growth path: signed C > 0 and C > capacity
        // 260E07A: MOV RCX, Q[D+0x10]
        long allocator = memory.readQword(D + 0x10);
        r.rcx = allocator;

        // 260E07E: LEA RDX, [RBX+RBX*2]
        // 260E082: SHL RDX, 3
        long rdxVal = Integer.toUnsignedLong(ebx) * 24L;
        r.rdx = rdxVal;

        // 260E086: MOV R8D, 8
        r.r8 = 8L;

        // 260E08C: MOV Q[W+0x38], RBP
        memory.writeQword(W + 0x38L, r.rbp);

        // 260E091: MOV RAX, Q[RCX]
        long vptr = memory.readQword(r.rcx);
        r.rax = vptr;

        // 260E094: MOV R9, Q[RAX+8]
        long target = memory.readQword(r.rax + 8L);
        r.r9 = target;

        // 260E098: CALL R9
        long cont098 = imageBase + 0x260E09BL;
        memory.writeQword(J, cont098);

        GovernmentCrtBoundary185Api.Call call098 = new GovernmentCrtBoundary185Api.Call(
            0x260E098L,
            GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
            target,
            r.rsp,
            r.volatileBits(),
            r.nonvolatileBits()
        );
        GovernmentCrtBoundary185Api.Entry childEntry098 = new GovernmentCrtBoundary185Api.Entry(
            imageBase,
            J,
            r.volatileBits(),
            r.nonvolatileBits()
        );
        EmbeddedVector565Api.CallFrame frame098 = new EmbeddedVector565Api.CallFrame(
            call098, childEntry098, df, 3, cont098
        );

        FullCopy437Api.CallResult result098 = calls.invoke(frame098);
        frame098.checkNormalReturn(result098);

        GovernmentCrtBoundary185Api.NormalReturn nr098 = result098.normalReturn();
        r.apply(nr098.volatileBits());
        df = result098.postDirectionFlagSet();

        // 260E09B: MOV R9D, DWORD[RSI+0xC]
        int oldCount = memory.readDword(r.rsi + 0xC);
        r.r9 = Integer.toUnsignedLong(oldCount);

        // 260E09F: MOV RBP, RAX
        long B = r.rax;
        r.rbp = B;

        // 260E0A2: TEST R9D, R9D
        // 260E0A5: JLE 0x260E0D1
        if (oldCount > 0) {
            // 260E0A7: MOV RCX, Q[RSI]
            long oldBase = memory.readQword(r.rsi);
            r.rcx = oldBase;

            // 260E0AA: MOV RDX, RAX
            r.rdx = B;

            // 260E0AD: NOP

            // 260E0B0: Old copy loop header
            long srcPtr = r.rcx;
            long dstPtr = r.rdx;
            int count = oldCount;
            while (count > 0) {
                budget.beforeStep(0x260E0B0L, srcPtr);

                GovernmentPrimaryTail155Api.Bits128 xmm0 = memory.read128(srcPtr);
                r.x0 = xmm0;

                count--;
                r.r9 = Integer.toUnsignedLong(count);

                dstPtr += 0x18L;
                r.rdx = dstPtr;

                srcPtr += 0x18L;
                r.rcx = srcPtr;

                memory.write128(dstPtr - 0x18L, xmm0);

                long low64 = memory.readQword(srcPtr - 8L);
                r.x1 = new GovernmentPrimaryTail155Api.Bits128(low64, 0L);

                memory.writeQword(dstPtr - 8L, low64);
            }
        }

        // 260E0D1: MOV RCX, Q[D+0x10]
        long freshAllocator = memory.readQword(D + 0x10);
        r.rcx = freshAllocator;

        // 260E0D5: MOV R8D, 8
        r.r8 = 8L;

        // 260E0DB: MOV RDX, Q[D]
        long freshBase = memory.readQword(D);
        r.rdx = freshBase;

        // 260E0DE: MOV RAX, Q[RCX]
        long freshVptr = memory.readQword(r.rcx);
        r.rax = freshVptr;

        // 260E0E1: CALL Q[RAX+0x10]
        long target0E1 = memory.readQword(r.rax + 0x10L);
        // Do NOT assign to r.r9

        long cont0E1 = imageBase + 0x260E0E4L;
        memory.writeQword(J, cont0E1);

        GovernmentCrtBoundary185Api.Call call0E1 = new GovernmentCrtBoundary185Api.Call(
            0x260E0E1L,
            GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
            target0E1,
            r.rsp,
            r.volatileBits(),
            r.nonvolatileBits()
        );
        GovernmentCrtBoundary185Api.Entry childEntry0E1 = new GovernmentCrtBoundary185Api.Entry(
            imageBase,
            J,
            r.volatileBits(),
            r.nonvolatileBits()
        );
        EmbeddedVector565Api.CallFrame frame0E1 = new EmbeddedVector565Api.CallFrame(
            call0E1, childEntry0E1, df, 3, cont0E1
        );

        FullCopy437Api.CallResult result0E1 = calls.invoke(frame0E1);
        frame0E1.checkNormalReturn(result0E1);

        GovernmentCrtBoundary185Api.NormalReturn nr0E1 = result0E1.normalReturn();
        r.apply(nr0E1.volatileBits());
        df = result0E1.postDirectionFlagSet();

        // 260E0E4: MOV Q[RSI], RBP
        memory.writeQword(r.rsi, r.rbp);

        // 260E0E7: MOV RBP, Q[W+0x38]
        r.rbp = memory.readQword(W + 0x38L);

        // 260E0EC: MOV DWORD[RSI+8], EBX
        memory.writeDword(r.rsi + 8, ebx);

        // 260E0EF: MOV DWORD[RSI+0xC], EBX
        memory.writeDword(r.rsi + 0xC, ebx);

        // 260E0F2: JMP 0x260E0FB
        // 260E0FB: MOV RAX, Q[RSI]
        r.rax = memory.readQword(r.rsi);

        // 260E0FE: XCHG AX, AX

        // 260E100: Final copy loop
        long dstPtr = r.rax;
        long srcPtr = P;
        int count = ebx;
        while (count > 0) {
            budget.beforeStep(0x260E100L, srcPtr);

            GovernmentPrimaryTail155Api.Bits128 xmm0 = memory.read128(srcPtr);
            r.x0 = xmm0;

            count--;
            r.rbx = Integer.toUnsignedLong(count);

            dstPtr += 0x18L;
            r.rax = dstPtr;

            srcPtr += 0x18L;
            r.rdi = srcPtr;

            memory.write128(dstPtr - 0x18L, xmm0);

            long low64 = memory.readQword(srcPtr - 8L);
            r.x1 = new GovernmentPrimaryTail155Api.Bits128(low64, 0L);

            memory.writeQword(dstPtr - 8L, low64);
        }

        // 260E11F: MOV RBX, Q[W+0x30]
        r.rbx = memory.readQword(W + 0x30L);
        // 260E124: MOV RAX, RSI
        r.rax = r.rsi;
        // 260E127: MOV RDI, Q[W+0x40]
        r.rdi = memory.readQword(W + 0x40L);
        // 260E12C: ADD RSP, 0x20
        r.rsp = E - 8L;
        // 260E130: POP RSI
        r.rsi = memory.readQword(E - 8L);
        // 260E131: RET
        long retRip = memory.readQword(E);
        long callerRsp = E + 8L;

        GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(), retRip, callerRsp, r.nonvolatileBits()
        );
        return new FullCopy437Api.CallResult(nr, df);
    }
}