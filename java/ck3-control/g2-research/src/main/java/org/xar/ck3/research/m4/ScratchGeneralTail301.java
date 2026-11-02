package org.xar.ck3.research.m4;

import java.util.Objects;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/**
 * M4-301: exact existing internal tail-block of the held source776 at
 * [0x1A82450,0x1A82758). This scope is ONLY the ten instructions / 52 bytes
 * [0x1A82724,0x1A82758), the General branch's last basic block. It is NOT
 * complete776 function admission, NOT branch selection, and NOT an implementCOPY.
 *
 * The supplied Entry describes the ACTUAL register bits at PC 0x1A82724 with
 * currentRSP G = originalFunctionE - 0x68 after the existing prologue (already
 * run by the caller). RBX is the actual first pointer, R10 the middle pointer,
 * RDX the actual right count, RCX the actual capacity; all other volatile/8
 * nonvolatile and XMM0..6 exact bits are supplied. Initialization uses the
 * full164 initializer (explicit RBX), never the 155 Registers constructor's
 * implicit RBX overwrite.
 *
 * transfer performs the byte-only write and full-state register/memory
 * operations with fresh savedhomes and true tail ownership (no new CALL push,
 * no RET, no read of the original return word, no bulk copy, no default
 * RFLAGS/DF). execute consumes the actual postblock Entry by directly delegating
 * to the CURRENT mature GeneralFullState294.execute with the same memory/calls/
 * budget, returning its NormalReturn object without adapting fields, without
 * routing a tail through Calls.tail/invoke and without repeating transfer.
 */
public final class ScratchGeneralTail301 {
    private ScratchGeneralTail301() { }

    /** Actual tail JMP site RVA of this block. */
    private static final long JUMP_SITE_RVA = 0x1A82753L;
    /** Actual direct tail target RVA (0x1A82F00). */
    private static final long TARGET_RVA = 0x1A82F00L;

    /**
     * Translate the ten instructions [0x1A82724,0x1A82758) in exact source
     * memory order and widths, then return the exact 185.Tail DIRECT_RVA at
     * site 0x1A82753 targeting 0x1A82F00 with the actual imageBase and the
     * postblock actual Entry (E with full V/N). No validation memory pre-reads
     * and no callee execution happen here.
     */
    public static GovernmentCrtBoundary185Api.Tail transfer(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);

        // Full164 initializer: explicit RBX from the supplied nonvolatile bits.
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(),
                entry.volatileBits(), entry.nonvolatileBits()));

        // 0x1A82724  movzx eax, byte ptr [rsp + 0xa8]  (READ then zero-extend)
        r.rax = Integer.toUnsignedLong(memory.readUnsignedByte(r.rsp + 0xA8L));
        // 0x1A8272C  mov byte ptr [rsp + 0xa8], al     (BYTE-only writeback)
        memory.writeByte(r.rsp + 0xA8L, (int) r.rax);
        // 0x1A82733  mov qword ptr [rsp + 0xa0], rcx   (full RCX capacity QWORD saved)
        memory.writeQword(r.rsp + 0xA0L, r.rcx);
        // 0x1A8273B  mov rcx, rbx                    (RCX takes old RBX)
        r.rcx = r.rbx;
        // 0x1A8273E  mov qword ptr [rsp + 0x90], rdx (full RDX right count QWORD saved)
        memory.writeQword(r.rsp + 0x90L, r.rdx);
        // 0x1A82746  mov rdx, r10                    (RDX takes R10)
        r.rdx = r.r10;
        // 0x1A82749  mov rbx, qword ptr [rsp + 0x78] (RBX fresh QWORD from G+0x78)
        r.rbx = memory.readQword(r.rsp + 0x78L);
        // 0x1A8274E  add rsp, 0x60                   (ADDRSP 0x60)
        r.rsp += 0x60L;
        // 0x1A82752  pop rdi                         (actual RDI pop)
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8L;
        // 0x1A82753  jmp 0x1a82f00                   (true tail: no push, no RET)

        return new GovernmentCrtBoundary185Api.Tail(
                JUMP_SITE_RVA,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                TARGET_RVA,
                new GovernmentCrtBoundary185Api.Entry(
                        entry.imageBaseBits(), r.rsp, r.volatileBits(), r.nonvolatileBits()));
    }

    /**
     * Consume the actual postblock Entry produced by transfer by directly
     * delegating to the CURRENT mature GeneralFullState294.execute with the
     * same memory/calls/budget. The returned NormalReturn object is passed
     * through unchanged: no field adaptation, no extra RET push/read, no
     * tail routed through Calls.invoke/Calls.tail, no repeated transfer.
     */
    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        return GeneralFullState294.execute(transfer(entry, memory).entry(), memory, calls, budget);
    }
}
