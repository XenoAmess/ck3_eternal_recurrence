package org.xar.ck3.research.m3.terminal213;

import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.terminal213.TerminalSignal213Api;

public final class TerminalSignal423283C {
    private TerminalSignal423283C() { }

    public static void execute(Terminal207Api.Memory memory, TerminalSignal213Api.Ports ports, TerminalSignal213Api.Input input) {
        long moduleBase = input.moduleBase();
        long E = input.calleeEntryRsp();
        int ecx = input.ecx();
        int edx = input.edx();
        int r8d = input.r8d();

        long B = E - 0x608L;
        long RBP = E - 0x508L;

        // 1. Prologue: Save RBX, RSI, push RBP, RDI, R14, setup stack
        // Excluded per contract: NV save/push/pop/CPU RET. We only track B and RBP for business logic.

        // 2. Cookie Setup
        // 4232859: mov rax, [rip+0x11fc858] -> R64 M+542F0B8
        long cookieSrc = memory.readPointer(moduleBase + 0x542F0B8L);
        // 4232860: xor rax, rsp
        long cookieVal = cookieSrc ^ B;
        // 4232863: mov [rbp+0x4e0], rax -> W64 B+5E0
        memory.writeInt64(B + 0x5E0L, cookieVal);

        // 3. Initial Argument Setup for 4224800
        // 423286a: mov edi, r8d
        // 423286d: mov esi, edx
        // 423286f: mov ebx, ecx
        // 4232871: cmp ecx, 0xffffffff
        // 4232874: je 0x423287b
        // 4232876: call 0x4224800
        if (ecx != -1) {
            ports.call4224800Initial(memory, 0x4232876L, ecx, edx, r8d);
        }

        // 4. First 4226F10 Call
        // 423287b: xor edx, edx (EDX=0)
        // 423287d: lea rcx, [rsp+0x70] -> RCX = B+70
        // 4232882: mov r8d, 0x98
        // 4232888: call 0x4226f10
        ports.call4226f10(memory, 0x4232888L, B + 0x70L, 0, 0x98);

        // 5. Second 4226F10 Call
        // 423288d: xor edx, edx (EDX=0)
        // 423288f: lea rcx, [rbp+0x10] -> RCX = RBP+10 = B+110
        // 4232893: mov r8d, 0x4d0
        // 4232899: call 0x4226f10
        ports.call4226f10(memory, 0x4232899L, B + 0x110L, 0, 0x4D0);

        // 6. Setup for 43DA418
        // 423289e: lea rax, [rsp+0x70] -> RAX = B+70
        // 42328a3: mov [rsp+0x48], rax -> W64 B+48 = B+70
        memory.writeInt64(B + 0x48L, B + 0x70L);
        // 42328a8: lea rcx, [rbp+0x10] -> RCX = B+110
        // 42328ac: lea rax, [rbp+0x10] -> RAX = B+110
        // 42328b0: mov [rsp+0x50], rax -> W64 B+50 = B+110
        memory.writeInt64(B + 0x50L, B + 0x110L);
        // 42328b5: call [rip+0x1a7b5d] -> IAT 43DA418
        long code43DA418 = memory.readPointer(moduleBase + 0x43DA418L);
        ports.call43da418(memory, 0x42328B5L, code43DA418, B + 0x110L);

        // 7. Setup for 43DA2A0
        // 42328bb: mov r14, [rbp+0x108] -> R14 = fresh memory[B+0x208]
        long capturedR14 = memory.readPointer(B + 0x208L);
        // 42328c2: lea rdx, [rsp+0x40] -> RDX = B+40
        // 42328c7: mov rcx, r14 -> RCX = capturedR14
        // 42328ca: xor r8d, r8d -> R8D = 0
        // 42328cd: call [rip+0x1a79cd] -> IAT 43DA2A0
        long code43DA2A0 = memory.readPointer(moduleBase + 0x43DA2A0L);
        long lookupRAX = ports.call43da2a0(memory, 0x42328CDL, code43DA2A0, capturedR14, B + 0x40L, 0);

        // 8. Conditional Branch on lookupRAX
        // 42328d3: test rax, rax
        // 42328d6: je 0x423290e
        if (lookupRAX != 0) {
            // 42328d8: and [rsp+0x38], 0 -> RMW B+38
            long oldB38 = memory.readPointer(B + 0x38L);
            memory.writeInt64(B + 0x38L, 0L);

            // 42328de: lea rcx, [rsp+0x58] -> RCX = B+58
            // 42328e3: mov rdx, [rsp+0x40] -> RDX = fresh memory[B+0x40]
            long rdxVal = memory.readPointer(B + 0x40L);
            // 42328e8: mov r9, rax -> R9 = lookupRAX
            // 42328eb: mov [rsp+0x30], rcx -> W64 B+30 = B+58
            memory.writeInt64(B + 0x30L, B + 0x58L);
            // 42328f0: mov r8, r14 -> R8 = capturedR14
            // 42328f3: lea rcx, [rsp+0x60] -> RCX = B+60
            // 42328f8: mov [rsp+0x28], rcx -> W64 B+28 = B+60
            memory.writeInt64(B + 0x28L, B + 0x60L);
            // 42328fd: lea rcx, [rbp+0x10] -> RCX = B+110
            // 4232901: mov [rsp+0x20], rcx -> W64 B+20 = B+110
            memory.writeInt64(B + 0x20L, B + 0x110L);
            // 4232906: xor ecx, ecx -> ECX = 0
            // 4232908: call [rip+0x1a799a] -> IAT 43DA2A8
            long code43DA2A8 = memory.readPointer(moduleBase + 0x43DA2A8L);
            ports.call43da2a8(memory, 0x4232908L, code43DA2A8, 0, rdxVal, capturedR14, lookupRAX, B);
        }

        // 9. Return Address Reads and Writes
        // 423290e: mov rax, [rbp+0x508] -> R64 E (since RBP+508 = E-508+508 = E)
        long retAddr1 = memory.readPointer(E);
        // 4232915: mov [rbp+0x108], rax -> W64 B+208 = retAddr1
        memory.writeInt64(B + 0x208L, retAddr1);

        // 423291c: lea rax, [rbp+0x508] -> RAX = E
        // 4232923: add rax, 8 -> RAX = E+8
        // 4232927: mov [rsp+0x70], esi -> W32 B+70 = EDX (esi was edx)
        memory.writeInt32(B + 0x70L, edx);
        // 423292b: mov [rbp+0xa8], rax -> W64 B+1A8 = E+8
        memory.writeInt64(B + 0x1A8L, E + 8L);

        // 4232932: mov rax, [rbp+0x508] -> R64 E (Second fresh read)
        long retAddr2 = memory.readPointer(E);
        // 4232939: mov [rbp-0x80], rax -> W64 B+80 = retAddr2
        memory.writeInt64(B + 0x80L, retAddr2);

        // 423293d: mov [rsp+0x74], edi -> W32 B+74 = R8D (edi was r8d)
        memory.writeInt32(B + 0x74L, r8d);

        // 10. Call 43DA6A0
        // 4232941: call [rip+0x1a7d59] -> IAT 43DA6A0
        long code43DA6A0 = memory.readPointer(moduleBase + 0x43DA6A0L);
        int savedEAX = ports.call43da6a0(memory, 0x4232941L, code43DA6A0);

        // 11. Call 43DA770
        // 4232947: xor ecx, ecx -> ECX = 0
        // 4232949: mov edi, eax -> EDI = savedEAX
        // 423294b: call [rip+0x1a7e1f] -> IAT 43DA770
        long code43DA770 = memory.readPointer(moduleBase + 0x43DA770L);
        ports.call43da770(memory, 0x423294BL, code43DA770, 0);

        // 12. Call 43DA2B0
        // 4232951: lea rcx, [rsp+0x48] -> RCX = B+48
        // 4232956: call [rip+0x1a7954] -> IAT 43DA2B0
        long code43DA2B0 = memory.readPointer(moduleBase + 0x43DA2B0L);
        int testEAX = ports.call43da2b0(memory, 0x4232956L, code43DA2B0, B + 0x48L);

        // 13. Conditional Repeat 4224800
        // 423295c: test eax, eax
        // 423295e: jne 0x4232970
        // 4232960: test edi, edi
        // 4232962: jne 0x4232970
        // 4232964: cmp ebx, 0xffffffff
        // 4232967: je 0x4232970
        // 4232969: mov ecx, ebx
        // 423296b: call 0x4224800
        if (testEAX == 0 && savedEAX == 0 && ecx != -1) {
            ports.call4224800Repeat(memory, 0x423296BL, ecx);
        }

        // 14. Final Cookie Read and 4224700
        // 4232970: mov rcx, [rbp+0x4e0] -> R64 B+5E0
        long finalCookie = memory.readPointer(B + 0x5E0L);
        // 4232977: xor rcx, rsp -> RCX = finalCookie ^ B
        long finalRCX = finalCookie ^ B;
        // 423297a: call 0x4224700
        ports.call4224700(memory, 0x423297AL, finalRCX);

        // 15. Epilogue (Excluded per contract: NV restore/RET)
    }
}