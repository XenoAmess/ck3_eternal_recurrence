package org.xar.ck3.study.m6.full224;

import java.util.Objects;
import org.xar.ck3.research.m4.Free61FullState201;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/**
 * Generic actual 40EC530 entry implementation.
 * Models the 5-byte JMP to 423543C, then the 17-byte body at 423543C which writes DWORD[SP+0x10]=0,
 * reloads it into EAX (zero-extended to RAX), and JMPs to 424E364.
 * Reuses Free61FullState201.execute for the 424E364 segment.
 * No new CALL push, no own RET, no Title-specific filtering.
 */
public final class DefaultFreeThunks185224 {
    private DefaultFreeThunks185224() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls lower) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(lower);

        // Mechanical initialization using 164 registers helper
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));

        // 423543C: mov dword ptr [rsp + 0x10], 0
        memory.writeDword(r.rsp + 0x10L, 0);

        // 4235444: mov eax, dword ptr [rsp + 0x10]
        // Fresh read, zero-extended to full RAX
        r.rax = Integer.toUnsignedLong(memory.readDword(r.rsp + 0x10L));

        // 4235448: jmp 0x424e364
        // This is a tail jump to the Free61FullState201 entry point.
        // We construct the Entry for 424E364 with current state (image, SP, V, N).
        // No CALL push, no RET. The jump is direct.
        GovernmentCrtBoundary185Api.Entry free61Entry = new GovernmentCrtBoundary185Api.Entry(
                entry.imageBaseBits(),
                r.rsp,
                r.volatileBits(),
                r.nonvolatileBits());

        // Execute the 424E364 segment using the mature Free61FullState201
        return Free61FullState201.execute(free61Entry, memory, lower);
    }
}