package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

public final class PendingCopyBackward4226860 {
    private PendingCopyBackward4226860() { }

    public static void copy(Copy4226860Api.Memory memory, long destination, long source, long bytes) {
        // Precondition: bytes > 32, source < destination < source + bytes (backward overlap)
        // Entry state: r11 = rcx (dest), r10 = rdx (src), rdx = rdx - rcx (delta), rcx = rcx + bytes (dest_end)

        long r11 = destination;
        long r10 = source;
        long rdx = source - destination; // delta = src - dest (negative in Java long, but used as offset)
        long rcx = destination + bytes;  // dest_end
        long r8 = bytes;

        // 0x4226dfc: movups xmm0, [rcx + rdx*1 - 0x10]
        // Read first 16 bytes from tail of source region
        Bits128 xmm0 = memory.read128(rcx + rdx - 0x10);

        // 0x4226e01: sub rcx, 0x10
        rcx -= 0x10;

        // 0x4226e05: sub r8, 0x10
        r8 -= 0x10;

        // 0x4226e09: test cl, 0xf (check if rcx is aligned to 16)
        // je 0x4226e25 if aligned
        if ((rcx & 0xF) == 0) {
            // Jump to 0x4226e25
            // 0x4226e25: mov r9, r8
            long r9 = r8;
            // 0x4226e28: shr r9, 0x7
            r9 >>>= 7;
            // 0x4226e2c: je 0x4226e9d (if r9 == 0, skip 128-byte loop)
            if (r9 == 0) {
                // Jump to 0x4226e9d
            } else {
                // 0x4226e2e: movaps [rcx], xmm0
                memory.write128(rcx, xmm0);
                // 0x4226e31: jmp 0x4226e47
                // Fall through to 0x4226e47
                // 0x4226e47: movups xmm0, [rcx + rdx*1 - 0x10]
                xmm0 = memory.read128(rcx + rdx - 0x10);
                // 0x4226e4c: movups xmm1, [rcx + rdx*1 - 0x20]
                Bits128 xmm1 = memory.read128(rcx + rdx - 0x20);
                // 0x4226e51: sub rcx, 0x80
                rcx -= 0x80;
                // 0x4226e58: movaps [rcx + 0x70], xmm0
                memory.write128(rcx + 0x70, xmm0);
                // 0x4226e5c: movaps [rcx + 0x60], xmm1
                memory.write128(rcx + 0x60, xmm1);
                // 0x4226e60: movups xmm0, [rcx + rdx*1 + 0x50]
                xmm0 = memory.read128(rcx + rdx + 0x50);
                // 0x4226e65: movups xmm1, [rcx + rdx*1 + 0x40]
                xmm1 = memory.read128(rcx + rdx + 0x40);
                // 0x4226e6a: dec r9
                r9--;
                // 0x4226e6d: movaps [rcx + 0x50], xmm0
                memory.write128(rcx + 0x50, xmm0);
                // 0x4226e71: movaps [rcx + 0x40], xmm1
                memory.write128(rcx + 0x40, xmm1);
                // 0x4226e75: movups xmm0, [rcx + rdx*1 + 0x30]
                xmm0 = memory.read128(rcx + rdx + 0x30);
                // 0x4226e7a: movups xmm1, [rcx + rdx*1 + 0x20]
                xmm1 = memory.read128(rcx + rdx + 0x20);
                // 0x4226e7f: movaps [rcx + 0x30], xmm0
                memory.write128(rcx + 0x30, xmm0);
                // 0x4226e83: movaps [rcx + 0x20], xmm1
                memory.write128(rcx + 0x20, xmm1);
                // 0x4226e87: movups xmm0, [rcx + rdx*1 + 0x10]
                xmm0 = memory.read128(rcx + rdx + 0x10);
                // 0x4226e8c: movups xmm1, [rcx + rdx*1]
                xmm1 = memory.read128(rcx + rdx);
                // 0x4226e90: jne 0x4226e40 (loop back if r9 != 0)
                while (r9 != 0) {
                    // 0x4226e40: movaps [rcx + 0x10], xmm0
                    memory.write128(rcx + 0x10, xmm0);
                    // 0x4226e44: movaps [rcx], xmm1
                    memory.write128(rcx, xmm1);
                    // 0x4226e47: movups xmm0, [rcx + rdx*1 - 0x10]
                    xmm0 = memory.read128(rcx + rdx - 0x10);
                    // 0x4226e4c: movups xmm1, [rcx + rdx*1 - 0x20]
                    xmm1 = memory.read128(rcx + rdx - 0x20);
                    // 0x4226e51: sub rcx, 0x80
                    rcx -= 0x80;
                    // 0x4226e58: movaps [rcx + 0x70], xmm0
                    memory.write128(rcx + 0x70, xmm0);
                    // 0x4226e5c: movaps [rcx + 0x60], xmm1
                    memory.write128(rcx + 0x60, xmm1);
                    // 0x4226e60: movups xmm0, [rcx + rdx*1 + 0x50]
                    xmm0 = memory.read128(rcx + rdx + 0x50);
                    // 0x4226e65: movups xmm1, [rcx + rdx*1 + 0x40]
                    xmm1 = memory.read128(rcx + rdx + 0x40);
                    // 0x4226e6a: dec r9
                    r9--;
                    // 0x4226e6d: movaps [rcx + 0x50], xmm0
                    memory.write128(rcx + 0x50, xmm0);
                    // 0x4226e71: movaps [rcx + 0x40], xmm1
                    memory.write128(rcx + 0x40, xmm1);
                    // 0x4226e75: movups xmm0, [rcx + rdx*1 + 0x30]
                    xmm0 = memory.read128(rcx + rdx + 0x30);
                    // 0x4226e7a: movups xmm1, [rcx + rdx*1 + 0x20]
                    xmm1 = memory.read128(rcx + rdx + 0x20);
                    // 0x4226e7f: movaps [rcx + 0x30], xmm0
                    memory.write128(rcx + 0x30, xmm0);
                    // 0x4226e83: movaps [rcx + 0x20], xmm1
                    memory.write128(rcx + 0x20, xmm1);
                    // 0x4226e87: movups xmm0, [rcx + rdx*1 + 0x10]
                    xmm0 = memory.read128(rcx + rdx + 0x10);
                    // 0x4226e8c: movups xmm1, [rcx + rdx*1]
                    xmm1 = memory.read128(rcx + rdx);
                }
                // 0x4226e92: movaps [rcx + 0x10], xmm0
                memory.write128(rcx + 0x10, xmm0);
                // 0x4226e96: and r8, 0x7f
                r8 &= 0x7F;
                // 0x4226e9a: movaps xmm0, xmm1
                xmm0 = xmm1;
            }
        } else {
            // 0x4226e0e: mov rax, rcx
            long rax = rcx;
            // 0x4226e11: and rcx, 0xfffffffffffffff0
            rcx &= 0xFFFFFFFFFFFFFFF0L;
            // 0x4226e15: movups xmm1, xmm0
            Bits128 xmm1 = xmm0;
            // 0x4226e18: movups xmm0, [rcx + rdx*1]
            xmm0 = memory.read128(rcx + rdx);
            // 0x4226e1c: movups [rax], xmm1
            memory.write128(rax, xmm1);
            // 0x4226e1f: mov r8, rcx
            r8 = rcx;
            // 0x4226e22: sub r8, r11
            r8 -= r11;
            // 0x4226e25: mov r9, r8
            long r9 = r8;
            // 0x4226e28: shr r9, 0x7
            r9 >>>= 7;
            // 0x4226e2c: je 0x4226e9d
            if (r9 == 0) {
                // Jump to 0x4226e9d
            } else {
                // 0x4226e2e: movaps [rcx], xmm0
                memory.write128(rcx, xmm0);
                // 0x4226e31: jmp 0x4226e47
                // Fall through to 0x4226e47
                // 0x4226e47: movups xmm0, [rcx + rdx*1 - 0x10]
                xmm0 = memory.read128(rcx + rdx - 0x10);
                // 0x4226e4c: movups xmm1, [rcx + rdx*1 - 0x20]
                xmm1 = memory.read128(rcx + rdx - 0x20);
                // 0x4226e51: sub rcx, 0x80
                rcx -= 0x80;
                // 0x4226e58: movaps [rcx + 0x70], xmm0
                memory.write128(rcx + 0x70, xmm0);
                // 0x4226e5c: movaps [rcx + 0x60], xmm1
                memory.write128(rcx + 0x60, xmm1);
                // 0x4226e60: movups xmm0, [rcx + rdx*1 + 0x50]
                xmm0 = memory.read128(rcx + rdx + 0x50);
                // 0x4226e65: movups xmm1, [rcx + rdx*1 + 0x40]
                xmm1 = memory.read128(rcx + rdx + 0x40);
                // 0x4226e6a: dec r9
                r9--;
                // 0x4226e6d: movaps [rcx + 0x50], xmm0
                memory.write128(rcx + 0x50, xmm0);
                // 0x4226e71: movaps [rcx + 0x40], xmm1
                memory.write128(rcx + 0x40, xmm1);
                // 0x4226e75: movups xmm0, [rcx + rdx*1 + 0x30]
                xmm0 = memory.read128(rcx + rdx + 0x30);
                // 0x4226e7a: movups xmm1, [rcx + rdx*1 + 0x20]
                xmm1 = memory.read128(rcx + rdx + 0x20);
                // 0x4226e7f: movaps [rcx + 0x30], xmm0
                memory.write128(rcx + 0x30, xmm0);
                // 0x4226e83: movaps [rcx + 0x20], xmm1
                memory.write128(rcx + 0x20, xmm1);
                // 0x4226e87: movups xmm0, [rcx + rdx*1 + 0x10]
                xmm0 = memory.read128(rcx + rdx + 0x10);
                // 0x4226e8c: movups xmm1, [rcx + rdx*1]
                xmm1 = memory.read128(rcx + rdx);
                // 0x4226e90: jne 0x4226e40
                while (r9 != 0) {
                    // 0x4226e40: movaps [rcx + 0x10], xmm0
                    memory.write128(rcx + 0x10, xmm0);
                    // 0x4226e44: movaps [rcx], xmm1
                    memory.write128(rcx, xmm1);
                    // 0x4226e47: movups xmm0, [rcx + rdx*1 - 0x10]
                    xmm0 = memory.read128(rcx + rdx - 0x10);
                    // 0x4226e4c: movups xmm1, [rcx + rdx*1 - 0x20]
                    xmm1 = memory.read128(rcx + rdx - 0x20);
                    // 0x4226e51: sub rcx, 0x80
                    rcx -= 0x80;
                    // 0x4226e58: movaps [rcx + 0x70], xmm0
                    memory.write128(rcx + 0x70, xmm0);
                    // 0x4226e5c: movaps [rcx + 0x60], xmm1
                    memory.write128(rcx + 0x60, xmm1);
                    // 0x4226e60: movups xmm0, [rcx + rdx*1 + 0x50]
                    xmm0 = memory.read128(rcx + rdx + 0x50);
                    // 0x4226e65: movups xmm1, [rcx + rdx*1 + 0x40]
                    xmm1 = memory.read128(rcx + rdx + 0x40);
                    // 0x4226e6a: dec r9
                    r9--;
                    // 0x4226e6d: movaps [rcx + 0x50], xmm0
                    memory.write128(rcx + 0x50, xmm0);
                    // 0x4226e71: movaps [rcx + 0x40], xmm1
                    memory.write128(rcx + 0x40, xmm1);
                    // 0x4226e75: movups xmm0, [rcx + rdx*1 + 0x30]
                    xmm0 = memory.read128(rcx + rdx + 0x30);
                    // 0x4226e7a: movups xmm1, [rcx + rdx*1 + 0x20]
                    xmm1 = memory.read128(rcx + rdx + 0x20);
                    // 0x4226e7f: movaps [rcx + 0x30], xmm0
                    memory.write128(rcx + 0x30, xmm0);
                    // 0x4226e83: movaps [rcx + 0x20], xmm1
                    memory.write128(rcx + 0x20, xmm1);
                    // 0x4226e87: movups xmm0, [rcx + rdx*1 + 0x10]
                    xmm0 = memory.read128(rcx + rdx + 0x10);
                    // 0x4226e8c: movups xmm1, [rcx + rdx*1]
                    xmm1 = memory.read128(rcx + rdx);
                }
                // 0x4226e92: movaps [rcx + 0x10], xmm0
                memory.write128(rcx + 0x10, xmm0);
                // 0x4226e96: and r8, 0x7f
                r8 &= 0x7F;
                // 0x4226e9a: movaps xmm0, xmm1
                xmm0 = xmm1;
            }
        }

        // 0x4226e9d: mov r9, r8
        long r9 = r8;
        // 0x4226ea0: shr r9, 0x4
        r9 >>>= 4;
        // 0x4226ea4: je 0x4226ec0 (if r9 == 0, skip 16-byte loop)
        if (r9 != 0) {
            // 0x4226eb0: movups [rcx], xmm0
            memory.write128(rcx, xmm0);
            // 0x4226eb3: sub rcx, 0x10
            rcx -= 0x10;
            // 0x4226eb7: movups xmm0, [rcx + rdx*1]
            xmm0 = memory.read128(rcx + rdx);
            // 0x4226ebb: dec r9
            r9--;
            // 0x4226ebe: jne 0x4226eb0
            while (r9 != 0) {
                // 0x4226eb0: movups [rcx], xmm0
                memory.write128(rcx, xmm0);
                // 0x4226eb3: sub rcx, 0x10
                rcx -= 0x10;
                // 0x4226eb7: movups xmm0, [rcx + rdx*1]
                xmm0 = memory.read128(rcx + rdx);
                // 0x4226ebb: dec r9
                r9--;
            }
        }

        // 0x4226ec0: and r8, 0xf
        r8 &= 0xF;
        // 0x4226ec4: je 0x4226ece (if r8 == 0, skip final partial)
        if (r8 != 0) {
            // 0x4226ec6: movups xmm1, [r10]
            Bits128 xmm1 = memory.read128(r10);
            // 0x4226eca: movups [r11], xmm1
            memory.write128(r11, xmm1);
        }

        // 0x4226ece: movups [rcx], xmm0
        memory.write128(rcx, xmm0);
        // 0x4226ed1: mov rax, r11
        // 0x4226ed4: ret
    }
}