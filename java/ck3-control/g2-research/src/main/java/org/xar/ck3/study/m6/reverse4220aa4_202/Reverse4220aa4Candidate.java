package org.xar.ck3.study.m6.reverse4220aa4_202;

import org.xar.ck3.study.m6.reverse4220aa4_202.Reverse4220aa4Inputs.Input;
import org.xar.ck3.study.m6.reverse4220aa4_202.Reverse4220aa4Inputs.Memory;
import org.xar.ck3.study.m6.reverse4220aa4_202.Reverse4220aa4Inputs.Effects;
import org.xar.ck3.study.m6.reverse4220aa4_202.Reverse4220aa4Inputs.Word32;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16;

public final class Reverse4220aa4Candidate {

    public static long apply(Input input, Memory memory, Effects effects) {
        long begin = input.beginRaw64();
        long end = input.endRaw64();
        long imageBase = input.imageBaseRaw64();

        // 4220AA4: mov rax, rdx
        long rax = end;
        // 4220AA7: mov r8, rcx
        long r8 = begin;
        // 4220AAA: sub rax, rcx
        rax = rax - begin;
        // 4220AAD: cmp rax, 0x40
        // 4220AB1: jb 0x144220aff
        if (Long.compareUnsigned(rax, 0x40L) < 0) {
            return fallback(rax, r8, end, memory);
        }

        // 4220AB3: bt dword ptr [rip + 0x120e5e1], 5
        // Global address is exactRIP-derived0x542f09c
        int featureVal = memory.read32(imageBase + 0x542f09cL);
        boolean hasFeature = (featureVal & (1 << 5)) != 0;

        // 4220ABB: jae 0x144220aff
        if (!hasFeature) {
            return fallback(rax, r8, end, memory);
        }

        // AVX32 loop
        // 4220ABD: shr rax, 1
        rax = rax >>> 1;
        // 4220AC0: movabs rcx, 0x7fffffffffffffe0
        // 4220ACA: and rax, rcx
        rax = rax & 0x7fffffffffffffe0L;
        // 4220ACD: add rax, r8
        rax = rax + r8;

        while (r8 != rax) {
            // 4220AD0: vpermq ymm1, ymmword ptr [r8], 0x4e
            Word32 w0 = memory.read32Bytes(r8);
            Word32 ymm1 = permq(w0);
            // 4220AD6: sub rdx, 0x20
            end = end - 0x20;
            // 4220ADA: vpshufd ymm3, ymm1, 0x1b
            Word32 ymm3 = pshufd32(ymm1);
            // 4220ADF: vpermq ymm1, ymmword ptr [rdx], 0x4e
            Word32 w1 = memory.read32Bytes(end);
            ymm1 = permq(w1);
            // 4220AE5: vpshufd ymm2, ymm1, 0x1b
            Word32 ymm2 = pshufd32(ymm1);
            // 4220AEA: vmovdqu ymmword ptr [r8], ymm2
            memory.write32Bytes(r8, ymm2);
            // 4220AEF: add r8, 0x20
            r8 = r8 + 0x20;
            // 4220AF3: vmovdqu ymmword ptr [rdx], ymm3
            memory.write32Bytes(end, ymm3);
        }

        // 4220AFC: vzeroupper
        effects.vzeroUpper();

        return fallback(rax, r8, end, memory);
    }

    private static long fallback(long rax, long r8, long end, Memory memory) {
        // 4220AFF: mov rax, rdx
        rax = end;
        // 4220B02: sub rax, r8
        rax = rax - r8;
        // 4220B05: cmp rax, 0x20
        // 4220B09: jb 0x144220b60
        if (Long.compareUnsigned(rax, 0x20L) < 0) {
            // Scalar loop
            while (r8 != end) {
                // 4220B49: sub rdx, 4
                end = end - 4;
                // 4220B4D: cmp r8, rdx
                // 4220B50: je 0x144220b65
                if (r8 == end) break;
                // 4220B52: mov ecx, dword ptr [r8]
                int ecx = memory.read32(r8);
                // 4220B55: mov eax, dword ptr [rdx]
                int eax = memory.read32(end);
                rax = Integer.toUnsignedLong(eax);
                // 4220B57: mov dword ptr [r8], eax
                memory.write32(r8, eax);
                // 4220B5A: add r8, 4
                r8 = r8 + 4;
                // 4220B5E: mov dword ptr [rdx], ecx
                memory.write32(end, ecx);
            }
            return rax;
        }

        // SSE16 loop
        // 4220B0B: shr rax, 1
        rax = rax >>> 1;
        // 4220B0E: movabs rcx, 0x7ffffffffffffff0
        // 4220B18: and rax, rcx
        rax = rax & 0x7ffffffffffffff0L;
        // 4220B1B: add rax, r8
        rax = rax + r8;

        while (r8 != rax) {
            // 4220B1E: movdqu xmm0, xmmword ptr [r8]
            Word16 w0 = memory.read16(r8);
            // 4220B23: sub rdx, 0x10
            end = end - 0x10;
            // 4220B27: pshufd xmm2, xmm0, 0x1b
            Word16 xmm2 = pshufd16(w0);
            // 4220B2C: movdqu xmm1, xmmword ptr [rdx]
            Word16 w1 = memory.read16(end);
            // 4220B30: pshufd xmm0, xmm1, 0x1b
            Word16 xmm0 = pshufd16(w1);
            // 4220B35: movdqu xmmword ptr [r8], xmm0
            memory.write16(r8, xmm0);
            // 4220B3A: add r8, 0x10
            r8 = r8 + 0x10;
            // 4220B3E: movdqu xmmword ptr [rdx], xmm2
            memory.write16(end, xmm2);
        }

        // 4220B47: jmp 0x144220b60
        // Scalar loop
        while (r8 != end) {
            // 4220B49: sub rdx, 4
            end = end - 4;
            // 4220B4D: cmp r8, rdx
            // 4220B50: je 0x144220b65
            if (r8 == end) break;
            // 4220B52: mov ecx, dword ptr [r8]
            int ecx = memory.read32(r8);
            // 4220B55: mov eax, dword ptr [rdx]
            int eax = memory.read32(end);
            rax = Integer.toUnsignedLong(eax);
            // 4220B57: mov dword ptr [r8], eax
            memory.write32(r8, eax);
            // 4220B5A: add r8, 4
            r8 = r8 + 4;
            // 4220B5E: mov dword ptr [rdx], ecx
            memory.write32(end, ecx);
        }

        // 4220B65: ret
        return rax;
    }

    private static Word32 permq(Word32 w) {
        // VPERMQ imm 0x4e selects qword lanes 2,3,0,1
        return new Word32(w.q2Raw64(), w.q3Raw64(), w.q0Raw64(), w.q1Raw64());
    }

    private static Word32 pshufd32(Word32 w) {
        // VPSHUFD imm 0x1b reverses DWORD selection within each 128bit lane
        // Lane 0 (q0, q1): d0,d1,d2,d3 -> d3,d2,d1,d0
        // Lane 1 (q2, q3): d4,d5,d6,d7 -> d7,d6,d5,d4
        long q0 = w.q0Raw64();
        long q1 = w.q1Raw64();
        long q2 = w.q2Raw64();
        long q3 = w.q3Raw64();

        long d0 = q0 & 0xFFFFFFFFL;
        long d1 = (q0 >>> 32) & 0xFFFFFFFFL;
        long d2 = q1 & 0xFFFFFFFFL;
        long d3 = (q1 >>> 32) & 0xFFFFFFFFL;

        long new_q0 = (d2 << 32) | d3;
        long new_q1 = (d0 << 32) | d1;

        long d4 = q2 & 0xFFFFFFFFL;
        long d5 = (q2 >>> 32) & 0xFFFFFFFFL;
        long d6 = q3 & 0xFFFFFFFFL;
        long d7 = (q3 >>> 32) & 0xFFFFFFFFL;

        long new_q2 = (d6 << 32) | d7;
        long new_q3 = (d4 << 32) | d5;

        return new Word32(new_q0, new_q1, new_q2, new_q3);
    }

    private static Word16 pshufd16(Word16 w) {
        // PSHUFD imm 0x1b reverses DWORD selection within 128bit lane
        // d0,d1,d2,d3 -> d3,d2,d1,d0
        long low = w.lowRaw64();
        long high = w.highRaw64();

        long d0 = low & 0xFFFFFFFFL;
        long d1 = (low >>> 32) & 0xFFFFFFFFL;
        long d2 = high & 0xFFFFFFFFL;
        long d3 = (high >>> 32) & 0xFFFFFFFFL;

        long new_low = (d2 << 32) | d3;
        long new_high = (d0 << 32) | d1;

        return new Word16(new_low, new_high);
    }
}