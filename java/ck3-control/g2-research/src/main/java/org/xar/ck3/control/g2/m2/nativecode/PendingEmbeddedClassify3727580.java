package org.xar.ck3.control.g2.m2.nativecode;

/** Full81 normal3727580 from actual103 CALL3727ECF, only AL8 result is modeled. */
public final class PendingEmbeddedClassify3727580 {
    private PendingEmbeddedClassify3727580() { }
    public interface Memory {
        int read8(long address);
        int read32(long address);
        long read64(long address);
    }
    public static int classify(Memory memory, long receiver) {
        // Initial CMP DWORD PTR [rcx+0x1c], 0x0
        int initialCount = memory.read32(receiver + 0x1C);

        if (initialCount != 0) {
            // Fresh MOVSXD signed count from [rcx+0x1c]
            int signedCount = memory.read32(receiver + 0x1C);
            // R64 [rcx+0x10] base
            long base = memory.read64(receiver + 0x10);
            // R32 [base + (signedCount << 5) - 0x14] signed field
            // signedCount << 5 is equivalent to signedCount * 32
            long offset = (long)signedCount * 32L;
            long addr = base + offset - 0x14L;
            int field = memory.read32(addr);

            // JG field, -1 if field > -1 (i.e., field >= 0 signed) => AL1 early
            if (field > -1) {
                return 1;
            }
            // Otherwise fall through to second vector logic
        }

        // Second vector logic (executed if initialCount == 0 OR field <= -1)
        // R64 [rcx+0x30] base BEFORE R32 [rcx+0x3c] signed count
        long base2 = memory.read64(receiver + 0x30);
        int signedCount2 = memory.read32(receiver + 0x3C);

        // end = base + (signedCount * 72) wrap64
        // signedCount2 * 72
        long end = base2 + ((long)signedCount2 * 72L);

        // Pointer = base
        long ptr = base2;

        // if ptr == end no R8
        if (ptr == end) {
            // Loop skipped, ptr remains base2
            // CMOVE: pointer = 0 iff ptr == end (which is true here)
            // TEST pointer zero: if result pointer != 0 AL1 ELSE AL0
            // Since ptr == end, CMOVE sets ptr to 0. TEST 0 -> AL0.
            return 0;
        }

        // Else loop
        // The loop continues while ptr != end
        // Inside loop: R8 [ptr+44hex], if low8 != 0 stop at ptr, otherwise ptr += 72 until end
        while (ptr != end) {
            int byteVal = memory.read8(ptr + 0x44L);
            // Mask actual read8 to LOW8 (& 0xFF) before != 0
            if ((byteVal & 0xFF) != 0) {
                break;
            }
            ptr += 72L;
        }

        // After loop actual CMOVE pointer = 0 iff ptr == end
        // Then test pointer zero: if result pointer != 0 AL1 ELSE AL0
        // If ptr == end (loop exhausted without finding flag), CMOVE sets ptr to 0.
        // If ptr != end (found flag), CMOVE leaves ptr as is (non-zero unless ptr was 0).
        // However, the contract specifies: "RETURN1IFF(ptr!=end && ptr!=0L), ELSE0"
        // And "If scan finds flag at address 0/count1/end72, break ptr0 must return AL0, not 1."
        // This implies we check if ptr != end AND ptr != 0.

        if (ptr != end && ptr != 0L) {
            return 1;
        } else {
            return 0;
        }
    }
}