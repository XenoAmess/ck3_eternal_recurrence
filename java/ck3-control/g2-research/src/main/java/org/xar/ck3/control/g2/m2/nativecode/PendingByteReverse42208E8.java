package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;

public final class PendingByteReverse42208E8 {
    private PendingByteReverse42208E8() { }

    public static void reverse(RangeOrder410Api.Memory memory, RangeOrder410Api.LoopBudget budget, long begin, long end, long moduleBase) {
        long r8 = begin;
        long rdx = end;
        long rax = rdx - r8; // unsigned difference

        // AVX branch: rax >= 64 and bit 5 of CPU feature
        if (Long.compareUnsigned(rax, 64L) >= 0) {
            int feature = memory.read32(moduleBase + 0x542F09CL);
            if ((feature & (1 << 5)) != 0) {
                // Load AVX mask (32 bytes) from moduleBase + 0x441F540
                Bits256 mask256 = memory.read256(moduleBase + 0x441F540L);
                long maskLo = mask256.low128().low();
                long maskHi = mask256.low128().high();
                long maskHiLo = mask256.high128().low();
                long maskHiHi = mask256.high128().high();

                // rax = rax >> 1; rax &= 0x7fffffffffffffe0L; rax += r8;
                rax = rax >>> 1;
                rax = rax & 0x7fffffffffffffe0L;
                rax = rax + r8;

                // Loop: while r8 != rax
                while (r8 != rax) {
                    budget.beforeStep(0x422091C, r8);

                    // vmovdqu ymm1, [r8] -> read 32 bytes at r8
                    Bits256 front256 = memory.read256(r8);
                    // vpermq ymm1, [r8], 0x4e -> permute qwords [2,3,0,1]
                    Bits256 permutedFront = vpermq256(front256);

                    // vpshufb ymm3, ymm1, ymm4 -> shuffle front with mask
                    Bits256 shuffledFront = vpshufb256(permutedFront, mask256);

                    // rdx -= 0x20
                    rdx = rdx - 0x20L;

                    // vmovdqu ymm1, [rdx] -> read 32 bytes at rdx
                    Bits256 back256 = memory.read256(rdx);
                    // vpermq ymm1, [rdx], 0x4e
                    Bits256 permutedBack = vpermq256(back256);

                    // vpshufb ymm2, ymm1, ymm4 -> shuffle back with mask
                    Bits256 shuffledBack = vpshufb256(permutedBack, mask256);

                    // vmovdqu [r8], ymm2 -> write shuffledBack to r8
                    memory.write256(r8, shuffledBack);

                    // r8 += 0x20
                    r8 = r8 + 0x20L;

                    // vmovdqu [rdx], ymm3 -> write shuffledFront to rdx
                    memory.write256(rdx, shuffledFront);

                    // cmp r8, rax; jne -> loop
                }
            }
        }

        // SSE branch: rax >= 32 and bit 2 of CPU feature
        // Recompute rax = rdx - r8
        rax = rdx - r8;
        if (Long.compareUnsigned(rax, 32L) >= 0) {
            int feature = memory.read32(moduleBase + 0x542F09CL);
            if ((feature & (1 << 2)) != 0) {
                // Load SSE mask (16 bytes) from moduleBase + 0x441F520
                Bits128 mask128 = memory.read128(moduleBase + 0x441F520L);

                // rax = rax >> 1; rax &= 0x7ffffffffffffff0L; rax += r8;
                rax = rax >>> 1;
                rax = rax & 0x7ffffffffffffff0L;
                rax = rax + r8;

                // Loop: while r8 != rax
                while (r8 != rax) {
                    budget.beforeStep(0x422097C, r8);

                    // movdqu xmm1, [r8]
                    Bits128 front128 = memory.read128(r8);

                    // rdx -= 0x10
                    rdx = rdx - 0x10L;

                    // pshufb xmm1, xmm2
                    Bits128 shuffledFront = pshufb128(front128, mask128);

                    // movdqu xmm0, [rdx]
                    Bits128 back128 = memory.read128(rdx);

                    // pshufb xmm0, xmm2
                    Bits128 shuffledBack = pshufb128(back128, mask128);

                    // movdqu [r8], xmm0 -> write shuffledBack to r8
                    memory.write128(r8, shuffledBack);

                    // r8 += 0x10
                    r8 = r8 + 0x10L;

                    // movdqu [rdx], xmm1 -> write shuffledFront to rdx
                    memory.write128(rdx, shuffledFront);

                    // cmp r8, rax; jne -> loop
                }
            }
        }

        // The body is entered before DEC, including an odd central element.
        while (r8 != rdx) {
            budget.beforeStep(0x42209A7, r8);
            rdx -= 1L;
            if (r8 == rdx) return;
            int frontByte = memory.read8(r8) & 0xFF;
            int backByte = memory.read8(rdx) & 0xFF;
            memory.write8(r8, backByte);
            r8 += 1L;
            memory.write8(rdx, frontByte);
        }
    }

    private static Bits256 vpermq256(Bits256 v) {
        // VPERMQ with imm 0x4e selects qwords [2,3,0,1]
        // Bits256 has low128 and high128, each with low and high qwords
        Bits128 lo128 = v.low128();
        Bits128 hi128 = v.high128();
        // qwords: [lo128.low, lo128.high, hi128.low, hi128.high] = [0,1,2,3]
        // permute to [2,3,0,1] = [hi128.low, hi128.high, lo128.low, lo128.high]
        Bits128 newLo = new Bits128(hi128.low(), hi128.high());
        Bits128 newHi = new Bits128(lo128.low(), lo128.high());
        return new Bits256(newLo, newHi);
    }

    private static Bits256 vpshufb256(Bits256 data, Bits256 mask) {
        // VP-SHUFB: for each 128-bit lane, apply PSHUFB with corresponding mask lane
        Bits128 dataLo = data.low128();
        Bits128 dataHi = data.high128();
        Bits128 maskLo = mask.low128();
        Bits128 maskHi = mask.high128();
        Bits128 resLo = pshufb128(dataLo, maskLo);
        Bits128 resHi = pshufb128(dataHi, maskHi);
        return new Bits256(resLo, resHi);
    }

    private static Bits128 pshufb128(Bits128 data, Bits128 mask) {
        // PSHUFB: for each byte position i (0..15):
        //   if mask byte i has bit 7 set -> result byte i = 0
        //   else -> result byte i = data byte (mask byte i & 0x0F)
        long dLo = data.low();
        long dHi = data.high();
        long mLo = mask.low();
        long mHi = mask.high();

        long rLo = 0L;
        long rHi = 0L;

        for (int i = 0; i < 8; i++) {
            int mByte = (int)((mLo >>> (i * 8)) & 0xFF);
            int dByte;
            if ((mByte & 0x80) != 0) {
                dByte = 0;
            } else {
                int idx = mByte & 0x0F;
                if (idx < 8) {
                    dByte = (int)((dLo >>> (idx * 8)) & 0xFF);
                } else {
                    dByte = (int)((dHi >>> ((idx - 8) * 8)) & 0xFF);
                }
            }
            rLo |= ((long)dByte) << (i * 8);
        }

        for (int i = 0; i < 8; i++) {
            int mByte = (int)((mHi >>> (i * 8)) & 0xFF);
            int dByte;
            if ((mByte & 0x80) != 0) {
                dByte = 0;
            } else {
                int idx = mByte & 0x0F;
                if (idx < 8) {
                    dByte = (int)((dLo >>> (idx * 8)) & 0xFF);
                } else {
                    dByte = (int)((dHi >>> ((idx - 8) * 8)) & 0xFF);
                }
            }
            rHi |= ((long)dByte) << (i * 8);
        }

        return new Bits128(rLo, rHi);
    }
}
