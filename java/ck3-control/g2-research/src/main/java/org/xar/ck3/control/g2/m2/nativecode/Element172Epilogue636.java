package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Exact straightline epilogue for held172B normal [372987C, 372989C).
 * Implements ONLY the source instructions after the second call returns.
 * Does not execute prologue, calls, or implement old algorithms.
 */
public final class Element172Epilogue636 {
    private Element172Epilogue636() { }

    /**
     * Completes the epilogue using current registers, memory, DF, and MXCSR.
     * @param r Current registers (must reflect state after second call return).
     * @param memory Owned memory view.
     * @param df Current direction flag.
     * @param mxcsr Current MXCSR state (preserved as-is).
     * @return Normal outcome with post-state.
     */
    public static QueueFp604Api.Normal finish(GovernmentPrimaryTail155Api.Registers r,
            GovernmentCrtBoundary185Api.Memory memory, boolean df, QueueFp604Api.Mxcsr mxcsr) {
        Objects.requireNonNull(r);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(mxcsr);

        // 372987C: mov eax, dword ptr [rbx + 0x40]
        r.rax = Integer.toUnsignedLong(memory.readDword(r.rbx + 0x40));

        // 372987F: mov rsi, qword ptr [rsp + 0x38]
        r.rsi = memory.readQword(r.rsp + 0x38);

        // 3729884: mov dword ptr [rdi + 0x40], eax
        memory.writeDword(r.rdi + 0x40, (int)r.rax);

        // 3729887: movzx eax, byte ptr [rbx + 0x44]
        r.rax = Integer.toUnsignedLong(memory.readUnsignedByte(r.rbx + 0x44));

        // 372988B: mov rbx, qword ptr [rsp + 0x30]
        r.rbx = memory.readQword(r.rsp + 0x30);

        // 3729890: mov byte ptr [rdi + 0x44], al
        memory.writeByte(r.rdi + 0x44, (int)r.rax);

        // 3729893: mov rax, rdi
        r.rax = r.rdi;

        // 3729896: add rsp, 0x20
        r.rsp += 0x20;

        // 372989A: pop rdi
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8;

        // 372989B: ret
        long rip = memory.readQword(r.rsp);
        r.rsp += 8;

        // Construct Normal outcome
        GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),
            rip,
            r.rsp,
            r.nonvolatileBits()
        );
        FullCopy437Api.CallResult base = new FullCopy437Api.CallResult(nr, df);
        return new QueueFp604Api.Normal(base, mxcsr);
    }
}