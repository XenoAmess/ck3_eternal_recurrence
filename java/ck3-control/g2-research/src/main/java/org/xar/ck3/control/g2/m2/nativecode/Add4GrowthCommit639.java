package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.Add4Fp639Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;

/**
 * Model implementation of the actual 47-byte growth epilogue block [ADD1B8, ADD1E7).
 * This block executes after the 5th growth CALL has returned a Normal outcome.
 * It performs the stack restoration, register reloads, and final RET read.
 * No CALL, FP, prologue, or whole-function orchestration is included.
 */
public final class Add4GrowthCommit639 {
    private Add4GrowthCommit639() { }

    /**
     * Completes the growth epilogue by restoring registers from the stack and constructing the Normal outcome.
     * @param r The current register state after the 5th growth CALL.
     * @param memory The owned memory view.
     * @param df The direction flag state.
     * @param mxcsr The current MXCSR state (must be preserved exactly).
     * @return The QueueFp604Api.Normal outcome representing the completion of the growth block.
     */
    public static QueueFp604Api.Normal finish(Registers r, Add4Fp639Api.Memory memory, boolean df, QueueFp604Api.Mxcsr mxcsr) {
        Objects.requireNonNull(r);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(mxcsr);

        // 1. MOV EAX, R32[RSP+50] (ADD1B8)
        //    Read DWORD at RSP+0x50, zero-extend to RAX.
        int eaxVal = memory.readDword(r.rsp + 0x50L);
        r.rax = Integer.toUnsignedLong(eaxVal);

        // 2. MOV RDI, R64[RSP+68] (ADD1BC)
        //    Read QWORD at RSP+0x68, restore RDI.
        r.rdi = memory.readQword(r.rsp + 0x68L);

        // 3. MOV R12, R64[RSP+20] (ADD1C1)
        //    Read QWORD at RSP+0x20, restore R12.
        r.r12 = memory.readQword(r.rsp + 0x20L);

        // 4. MOV QWORD[R14], RSI (ADD1C6)
        //    Write current RSI to memory at R14.
        memory.writeQword(r.r14, r.rsi);

        // 5. MOV RSI, R64[RSP+60] (ADD1C9)
        //    Read QWORD at RSP+0x60, restore RSI.
        r.rsi = memory.readQword(r.rsp + 0x60L);

        // 6. MOV DWORD[R14+8], EBP (ADD1CE)
        //    Write current EBP (low 32 bits) to memory at R14+8.
        memory.writeDword(r.r14 + 8L, (int)r.rbp);

        // 7. MOV RBP, R64[RSP+58] (ADD1D2)
        //    Read QWORD at RSP+0x58, restore RBP.
        r.rbp = memory.readQword(r.rsp + 0x58L);

        // 8. MOV DWORD[R14+C], EAX (ADD1D7)
        //    Write current EAX (low 32 bits) to memory at R14+0xC.
        memory.writeDword(r.r14 + 0xCL, (int)r.rax);

        // 9. ADD RSP, 0x28 (ADD1DB)
        //    Adjust stack pointer by 0x28.
        r.rsp += 0x28L;

        // 10. POP R15 (ADD1DF)
        //    Read QWORD at RSP, increment RSP, restore R15.
        r.r15 = memory.readQword(r.rsp);
        r.rsp += 8L;

        // 11. POP R14 (ADD1E1)
        //    Read QWORD at RSP, increment RSP, restore R14.
        r.r14 = memory.readQword(r.rsp);
        r.rsp += 8L;

        // 12. POP R13 (ADD1E3)
        //    Read QWORD at RSP, increment RSP, restore R13.
        r.r13 = memory.readQword(r.rsp);
        r.rsp += 8L;

        // 13. POP RBX (ADD1E5)
        //    Read QWORD at RSP, increment RSP, restore RBX.
        r.rbx = memory.readQword(r.rsp);
        r.rsp += 8L;

        // 14. RET (ADD1E6)
        //    Read QWORD at RSP (return address), increment RSP.
        long returnRipBits = memory.readQword(r.rsp);
        r.rsp += 8L;
        long callerRspBits = r.rsp;

        // Construct the NormalReturn with the final state.
        // VolatileBits: RAX, RCX, RDX, R8, R9, R10, R11, XMM0..XMM5
        // NonvolatileBits: RBX, RBP, RSI, RDI, R12, R13, R14, R15, XMM6
        VolatileBits finalV = new VolatileBits(
            r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11,
            r.x0, r.x1, r.x2, r.x3, r.x4, r.x5
        );
        NonvolatileBits finalN = new NonvolatileBits(
            r.rbx, r.rbp, r.rsi, r.rdi, r.r12, r.r13, r.r14, r.r15, r.x6
        );

        GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
            finalV, returnRipBits, callerRspBits, finalN
        );

        // Wrap in FullCopy437Api.CallResult (as required by QueueFp604Api.Normal base)
        // Note: The contract implies the base is a CallResult compatible with the queue context.
        // We construct the Normal outcome directly as per the return type.
        return new QueueFp604Api.Normal(
            new FullCopy437Api.CallResult(nr, df),
            mxcsr
        );
    }
}