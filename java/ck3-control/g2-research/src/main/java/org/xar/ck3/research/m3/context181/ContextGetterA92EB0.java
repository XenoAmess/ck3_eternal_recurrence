package org.xar.ck3.research.m3.context181;
import org.xar.ck3.research.m3.context181.ContextGetter181Api.*;

/**
 * Source-bound implementation of target a92eb0 (87 bytes).
 * Normal path: read global at moduleBase+0x5D1E2C8. If nonzero, return it.
 * If zero, perform source storage order operations on caller scratch (bodyRsp),
 * call initialize3f8b640, then re-read global and return observed value.
 * No CPU ABI claims, no exception handling, no game logic.
 */
public final class ContextGetterA92EB0 {
    private ContextGetterA92EB0() { }

    public static long get(Memory memory, Ports ports, Input input) {
        long moduleBase = input.moduleBase();
        long bodyRsp = input.scratch().bodyRsp();

        // 1. Read global at moduleBase + 0x5D1E2C8
        long globalAddr = moduleBase + 0x5D1E2C8L;
        long globalVal = memory.readPointer(globalAddr);

        // 2. If nonzero, return immediately (matches jne 0000000000A92F02)
        if (globalVal != 0L) {
            return globalVal;
        }

        // 3. Zero path: source storage order operations
        // mov dword ptr [rsp+28h], 1Eh
        memory.writeInt32(bodyRsp + 0x28L, 0x1E);

        // lea rax, [000000000448D018h] -> rax = moduleBase + 0x448D018
        long descriptor = moduleBase + 0x448D018L;

        // mov qword ptr [rsp+20h], rax
        memory.writeInt64(bodyRsp + 0x20L, descriptor);

        // lea rdx, [rsp+20h] -> rdx = bodyRsp + 0x20 (address of the stored qword)
        long rdx = bodyRsp + 0x20L;

        // mov byte ptr [rsp+2Ch], 0
        memory.write8(bodyRsp + 0x2CL, 0);

        // mov r9d, 64h
        int r9d = 0x64;

        // movaps xmm0, xmmword ptr [rsp+20h]
        // This reads 16 bytes from bodyRsp+0x20. The caller owns this scratch.
        // We must preserve the existing descriptor+0xD..0xF bytes as per contract.
        // read128 returns Bytes16(low, high). The low 8 bytes are the descriptor we just wrote.
        // The high 8 bytes (bytes 8..15) are caller-owned and must be preserved.
        Bytes16 existing = memory.read128(bodyRsp + 0x20L);

        // xor r8d, r8d -> r8d = 0
        int r8d = 0;

        // movdqa xmmword ptr [rsp+20h], xmm0
        // Write back the same 16 bytes. This is a self-write that preserves caller bytes.
        memory.write128(bodyRsp + 0x20L, existing);

        // lea ecx, [r9-63h] -> ecx = r9d - 0x63 = 0x64 - 0x63 = 1
        int ecx = r9d - 0x63;

        // call 0000000003F8B640
        // Args: ECX=1, RDX=bodyRsp+0x20, R8D=0, R9D=0x64
        // The call site RVA is 0xA92EF6 per witness protocol.
        // Return value is ignored.
        ports.initialize3f8b640(memory, 0xA92EF6L, ecx, rdx, r8d, r9d);

        // 4. Fresh global read after callback
        long globalVal2 = memory.readPointer(globalAddr);

        // 5. Return observed global (possibly still 0)
        return globalVal2;
    }
}