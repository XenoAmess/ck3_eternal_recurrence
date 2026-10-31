package org.xar.ck3.control.g2.m2.nativecode;

/** Actual199-byte role-copy/full-ID lookup block27563E1..27564A8.
 * This is a finite block of the held full1473B function, not a whole-function claim.
 */
public final class PendingComponentRoles27563E1 {
    private PendingComponentRoles27563E1() { }
    public interface Memory {
        int read32(long address);
        long read64(long address);
        void write32(long address, int value);
    }
    public record Resolved(long r14, long r15, long rdi) { }
    public static Resolved resolve(Memory memory, long componentAddress, long contextAddress, long moduleBase) {
        // 1. Role-copy: read 3 DWORDs from context, write to component
        int eax = memory.read32(contextAddress + 0x2d8);
        memory.write32(componentAddress + 0x250, eax);
        int ecx = memory.read32(contextAddress + 0x2e8);
        memory.write32(componentAddress + 0x254, ecx);
        int edx = memory.read32(contextAddress + 0x2dc);
        memory.write32(componentAddress + 0x258, edx);

        // 2. Load global R10 (QWORD at moduleBase + 0x5c67568)
        long r10 = memory.read64(moduleBase + 0x5c67568);

        // 3. If R10 is null, use fallback global (QWORD at moduleBase + 0x5c67570)
        if (r10 == 0) {
            long fallback = memory.read64(moduleBase + 0x5c67570);
            return new Resolved(fallback, fallback, fallback);
        }

        // 4. Load capacity EDI (DWORD at R10 + 0x2c)
        int edi = memory.read32(r10 + 0x2c);

        // 5. Load fallback global R11 (QWORD at moduleBase + 0x5c67570)
        long r11 = memory.read64(moduleBase + 0x5c67570);

        // 6. Resolve R14 (first role ID)
        long r14;
        int r8d = eax & 0xffffff;
        if (Integer.compareUnsigned(r8d, edi) >= 0) {
            r14 = r11;
        } else {
            long r9 = (long) r8d * 2;
            long r8 = memory.read64(r10 + 0x20);
            long slot = memory.read64(r8 + r9 * 8 + 0x8);
            if (slot == 0) {
                r14 = r11;
            } else {
                int idAtSlot = memory.read32(slot + 0x18);
                if (idAtSlot == eax) {
                    r14 = slot;
                } else {
                    r14 = r11;
                }
            }
        }

        // 7. Resolve R15 (second role ID)
        long r15;
        int eax2 = ecx & 0xffffff;
        if (Integer.compareUnsigned(eax2, edi) >= 0) {
            r15 = r11;
        } else {
            long r8_2 = (long) eax2 * 2;
            long rax = memory.read64(r10 + 0x20);
            long slot2 = memory.read64(rax + r8_2 * 8 + 0x8);
            if (slot2 == 0) {
                r15 = r11;
            } else {
                int idAtSlot2 = memory.read32(slot2 + 0x18);
                if (idAtSlot2 == ecx) {
                    r15 = slot2;
                } else {
                    r15 = r11;
                }
            }
        }

        // 8. Resolve RDI (third role ID)
        long rdi;
        int eax3 = edx & 0xffffff;
        if (Integer.compareUnsigned(eax3, edi) >= 0) {
            rdi = r11;
        } else {
            long rcx = (long) eax3 * 2;
            long rax2 = memory.read64(r10 + 0x20);
            long slot3 = memory.read64(rax2 + rcx * 8 + 0x8);
            if (slot3 == 0) {
                rdi = r11;
            } else {
                int idAtSlot3 = memory.read32(slot3 + 0x18);
                if (idAtSlot3 == edx) {
                    rdi = slot3;
                } else {
                    rdi = r11;
                }
            }
        }

        return new Resolved(r14, r15, rdi);
    }
}
