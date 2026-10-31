package org.xar.ck3.research.m5;

import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Generic fixture encoding/copying only; contains no subject algorithm. */
final class GovernmentCrtCallee186WitnessData {
    static final long IMAGE = 0x2400_0000_0000_0000L;
    static final long GLOBAL = IMAGE + 0x5C5CB68L;

    private GovernmentCrtCallee186WitnessData() {}

    static Map<Long, Integer> words(long... addressValuePairs) {
        if ((addressValuePairs.length & 1) != 0) throw new IllegalArgumentException("Unpaired qword");
        Map<Long, Integer> bytes = new HashMap<>();
        for (int p = 0; p < addressValuePairs.length; p += 2) {
            for (int b = 0; b < 8; b++) {
                long address = addressValuePairs[p] + b;
                int value = (int) ((addressValuePairs[p + 1] >>> (8 * b)) & 0xFFL);
                if (bytes.putIfAbsent(address, value) != null) {
                    throw new IllegalArgumentException("Overlapping fixture qwords");
                }
            }
        }
        return Map.copyOf(bytes);
    }

    static Map<Long, Integer> overlay(Map<Long, Integer> known, Map<Long, Integer> writes) {
        Map<Long, Integer> bytes = new HashMap<>(known);
        bytes.putAll(writes);
        return Map.copyOf(bytes);
    }

    static VolatileBits v(long tag, long rax, long rcx, long rdx) {
        return new VolatileBits(rax, rcx, rdx, tag + 0x108, tag + 0x109,
                tag + 0x10A, tag + 0x10B,
                new Bits128(tag + 0x200, tag + 0x201),
                new Bits128(tag + 0x210, tag + 0x211),
                new Bits128(tag + 0x220, tag + 0x221),
                new Bits128(tag + 0x230, tag + 0x231),
                new Bits128(tag + 0x240, tag + 0x241),
                new Bits128(tag + 0x250, tag + 0x251));
    }

    static VolatileBits registers(VolatileBits data, long rax, long rcx, long rdx) {
        return new VolatileBits(rax, rcx, rdx, data.r8Bits(), data.r9Bits(),
                data.r10Bits(), data.r11Bits(), data.xmm0(), data.xmm1(),
                data.xmm2(), data.xmm3(), data.xmm4(), data.xmm5());
    }

    static NonvolatileBits n(long tag, long rbx) {
        return new NonvolatileBits(rbx, tag + 0x105, tag + 0x106, tag + 0x107,
                tag + 0x10C, tag + 0x10D, tag + 0x10E, tag + 0x10F,
                new Bits128(tag + 0x260, tag + 0x261));
    }

    static NonvolatileBits rbx(NonvolatileBits data, long value) {
        return new NonvolatileBits(value, data.rbpBits(), data.rsiBits(),
                data.rdiBits(), data.r12Bits(), data.r13Bits(), data.r14Bits(),
                data.r15Bits(), data.xmm6());
    }
}
