package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.CallResult;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Memory;

/**
 * Implements the epilogue block [0x880403, 0x880423) of the 227-byte function at RVA 0x880340.
 * This corresponds to the shared tail after either the growth or non-growth branch.
 * Instructions:
 * 1. MOV RBX, QWORD PTR [RSP+0x38] -> r.rbx = memory.readQword(r.rsp + 0x38)
 * 2. LEA EAX, [RSI-0x1]           -> r.rax = Integer.toUnsignedLong((int)(r.rsi - 1))
 * 3. MOV RSI, QWORD PTR [RSP+0x40] -> r.rsi = memory.readQword(r.rsp + 0x40)
 * 4. MOVSXD RCX, EAX              -> r.rcx = (long)(int)r.rax (sign-extend 32 to 64)
 * 5. LEA RAX, [RDI+RCX*8]         -> r.rax = r.rdi + (r.rcx << 3)
 * 6. MOV RDI, QWORD PTR [RSP+0x48] -> r.rdi = memory.readQword(r.rsp + 0x48)
 * 7. ADD RSP, 0x20                -> r.rsp += 0x20
 * 8. POP R14                    -> r.r14 = memory.readQword(r.rsp); r.rsp += 8
 * 9. RET                        -> returnRip = memory.readQword(r.rsp); r.rsp += 8
 */
public final class QueueAppendEpilogue599 {
    private QueueAppendEpilogue599() { }

    public static CallResult finish(Registers r, Memory memory, boolean directionFlagSet) {
        // 1. MOV RBX, QWORD PTR [RSP+0x38]
        r.rbx = memory.readQword(r.rsp + 0x38);

        // 2. LEA EAX, [RSI-0x1]
        // EAX is 32-bit. RSI is 64-bit. The effective address is RSI - 1.
        // LEA with no scale adds the address to EAX? No, LEA reg, [base] is reg = base.
        // Wait, LEA EAX, [RSI-0x1] means EAX = RSI - 1.
        // In x86-64, LEA reg, [base + scale*index + disp] computes base + scale*index + disp into reg.
        // Here it is LEA EAX, [RSI-0x1]. This is effectively EAX = RSI - 1.
        // Since EAX is 32-bit, the result is truncated to 32 bits and zero-extended to RAX.
        r.rax = Integer.toUnsignedLong((int)(r.rsi - 1));

        // 3. MOV RSI, QWORD PTR [RSP+0x40]
        r.rsi = memory.readQword(r.rsp + 0x40);

        // 4. MOVSXD RCX, EAX
        // Sign-extend 32-bit EAX to 64-bit RCX.
        r.rcx = (long)(int)r.rax;

        // 5. LEA RAX, [RDI+RCX*8]
        // RAX = RDI + RCX * 8.
        // RAX is 64-bit here (LEA RAX, ...).
        r.rax = r.rdi + (r.rcx << 3);

        // 6. MOV RDI, QWORD PTR [RSP+0x48]
        r.rdi = memory.readQword(r.rsp + 0x48);

        // 7. ADD RSP, 0x20
        r.rsp += 0x20;

        // 8. POP R14
        r.r14 = memory.readQword(r.rsp);
        r.rsp += 8;

        // 9. RET
        // Read return address from stack.
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8;

        // Construct the NormalReturn with current state.
        // VolatileBits includes RAX, RCX, RDX, R8, R9, R10, R11, XMM0..5.
        // NonvolatileBits includes RBX, RBP, RSI, RDI, R12, R13, R14, R15, XMM6.
        // The Registers class provides volatileBits() and nonvolatileBits().

        VolatileBits v = r.volatileBits();
        NonvolatileBits n = r.nonvolatileBits();

        NormalReturn normalReturn = new NormalReturn(v, returnRip, r.rsp, n);

        return new CallResult(normalReturn, directionFlagSet);
    }
}