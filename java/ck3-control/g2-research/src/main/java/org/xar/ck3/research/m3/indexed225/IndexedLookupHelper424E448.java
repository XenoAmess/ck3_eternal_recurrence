package org.xar.ck3.research.m3.indexed225;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class IndexedLookupHelper424E448 {
    private IndexedLookupHelper424E448() { }

    public static long execute(IndexedHelper225Api.Memory memory, IndexedHelper225Api.Ports ports, IndexedHelper225Api.Input input) {
        long base = input.moduleBase();
        long r15 = Integer.toUnsignedLong(input.index());
        long r13 = input.nameAddress();
        long rbp = input.listBegin();
        long r12 = input.listEnd();

        long encoded = memory.readPointer(base + 0x5C5D790L + r15 * 8L);
        long cookie = memory.readPointer(base + 0x542F0B8L);
        long decoded = Long.rotateRight(cookie ^ encoded, (int)(cookie & 63L));

        if (decoded == -1L) {
            return 0L;
        }
        if (decoded != 0L) {
            return decoded;
        }

        if (rbp == r12) {
            // Empty list path: use initial cookie already observed
            long r10 = cookie;
            long rdi = -1L;
            // Simulate failure path for empty list (jump to 593/5E4)
            // At 593: xor ebx,ebx -> ebx=0. test rbx,rbx -> je 5E4
            // At 5E4: mov eax,r10d; mov ecx,0x40; and eax,0x3f; sub ecx,eax; ror rdi,cl; xor rdi,r10; xchg...
            int eax = (int)r10;
            int ecx = 0x40;
            eax &= 0x3f;
            ecx -= eax;
            rdi = Long.rotateRight(rdi, ecx);
            rdi ^= r10;
            memory.exchangeInt64(base + 0x5C5D790L + r15 * 8L, rdi);
            return 0L;
        }

        // Module list loop
        long rsi = 0L; // Loop cursor offset
        long rbx = 0L;
        long r14 = base; // Image base
        boolean found = false;
        long module = 0L;
        boolean wasCached = false;

        while (rbp != r12) {
            int dword = memory.readInt32(rbp);
            rsi = Integer.toUnsignedLong(dword);
            long cacheAddr = base + 0x5C5D6F0L + rsi * 8L;
            long cached = memory.readPointer(cacheAddr);

            if (cached == -1L) {
                rbp += 4L;
                continue;
            }
            if (cached != 0L) {
                module = cached;
                found = true;
                wasCached = true;
                break;
            }

            // cached == 0: fresh path
            long pathPtr = memory.readPointer(base + 0x44269D0L + rsi * 8L);
            r14 = pathPtr; // Temporarily R14 is path

            // Call 43DA478 @ 424E4EB
            long iat478 = memory.readPointer(base + 0x43DA478L);
            long rax478 = ports.call43da478(memory, 0x424E4EBL, iat478, r14, 0, 0x800);
            rbx = rax478;

            if (rbx != 0L) {
                // Success path
                found = true;
                module = rbx;
                wasCached = false;
                break;
            }

            // rbx == 0: Call 43DA738 @ 424E4F9
            long iat738 = memory.readPointer(base + 0x43DA738L);
            int eax738 = ports.call43da738(memory, 0x424E4F9L, iat738);

            if (eax738 == 0x57) {
                // Two direct 4246A60 calls
                long iat4246a60 = 0x4246A60L; // Direct call
                int r8d = 7;
                long rdx1 = base + 0x44226A0L;
                int eax1 = ports.call4246a60(memory, 0x424E514L, r14, rdx1, r8d);
                if (eax1 != 0) {
                    long rdx2 = base + 0x4426EC8L;
                    int eax2 = ports.call4246a60(memory, 0x424E52AL, r14, rdx2, r8d);
                    if (eax2 != 0) {
                        // Retry 43DA478 @ 424E53B
                        long iat478b = memory.readPointer(base + 0x43DA478L);
                        long rax478b = ports.call43da478(memory, 0x424E53BL, iat478b, r14, 0, 0);
                        rbx = rax478b;
                        if (rbx != 0L) {
                            found = true;
                            module = rbx;
                            wasCached = false;
                            break;
                        }
                    }
                }
            }

            // Failure path: cache -1
            memory.exchangeInt64(cacheAddr, -1L);
            rbp += 4L;
        }

        if (!found) {
            // List exhausted: fresh cookie @ 424E58C
            long r10 = memory.readPointer(base + 0x542F0B8L);
            long rdi = -1L;
            int eax = (int)r10;
            int ecx = 0x40;
            eax &= 0x3f;
            ecx -= eax;
            rdi = Long.rotateRight(rdi, ecx);
            rdi ^= r10;
            memory.exchangeInt64(base + 0x5C5D790L + r15 * 8L, rdi);
            return 0L;
        }

        // Found module: reestablish image base @ 424E548
        r14 = base;
        long cacheAddr = base + 0x5C5D6F0L + rsi * 8L;

        if (!wasCached) {
            // Only freshload/retry successfulmodule paththrough548 mayexchange564 thenconditionally7C0
            long oldVal = memory.exchangeInt64(cacheAddr, module);
            if (oldVal != 0L) {
                // Call 43DA7C0 @ 424E574
                long iat7c0 = memory.readPointer(base + 0x43DA7C0L);
                ports.call43da7c0(memory, 0x424E574L, iat7c0, module);
            }
        }

        // Resolve 43DA680 @ 424E5A0
        // All found nonzero module paths have real freshcookie readPointer(base542F0B8) at5D4 BEFORE freshIAT680read/call5A0
        long r10 = memory.readPointer(base + 0x542F0B8L);
        long iat680 = memory.readPointer(base + 0x43DA680L);
        long rax680 = ports.call43da680(memory, 0x424E5A0L, iat680, module, r13);

        if (rax680 != 0L) {
            // Success: fresh cookie @ 424E5AB
            long r10b = memory.readPointer(base + 0x542F0B8L);
            long rdx = rax680;
            int ecx = (int)r10b;
            ecx &= 0x3f;
            int edx = 0x40 - ecx;
            rdx = Long.rotateRight(rdx, edx);
            rdx ^= r10b;
            memory.exchangeInt64(base + 0x5C5D790L + r15 * 8L, rdx);
            return rax680;
        }

        // Failure: fresh cookie @ 424E5DD
        long r10c = memory.readPointer(base + 0x542F0B8L);
        long rdi = -1L;
        int eax = (int)r10c;
        int ecx = 0x40;
        eax &= 0x3f;
        ecx -= eax;
        rdi = Long.rotateRight(rdi, ecx);
        rdi ^= r10c;
        memory.exchangeInt64(base + 0x5C5D790L + r15 * 8L, rdi);
        return 0L;
    }
}