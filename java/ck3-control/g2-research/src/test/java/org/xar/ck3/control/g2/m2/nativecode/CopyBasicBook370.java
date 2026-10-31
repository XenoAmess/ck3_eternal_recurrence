package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import java.util.ArrayList;
import org.xar.ck3.control.g2.m2.nativecode.CopyWitnessData370.*;

public final class CopyBasicBook370 {
    private CopyBasicBook370() { }

    private static long M = 0x3300000000L;
    private static long S = 0x2200000000L;

    private static long srcByte(long addr) {
        return (addr - S + 0x10) & 0xFF;
    }

    private static long read8(long addr) {
        return srcByte(addr);
    }

    private static long read16(long addr) {
        return (srcByte(addr) | (srcByte(addr + 1) << 8)) & 0xFFFF;
    }

    private static long read32(long addr) {
        return (srcByte(addr) | (srcByte(addr + 1) << 8) | (srcByte(addr + 2) << 16) | (srcByte(addr + 3) << 24)) & 0xFFFFFFFFL;
    }

    private static long read64(long addr) {
        long v = 0;
        for (int i = 0; i < 8; i++) {
            v |= (srcByte(addr + i) << (i * 8));
        }
        return v;
    }

    private static long[] read128(long addr) {
        long low = 0;
        long high = 0;
        for (int i = 0; i < 8; i++) {
            low |= (srcByte(addr + i) << (i * 8));
            high |= (srcByte(addr + 8 + i) << (i * 8));
        }
        return new long[]{low, high};
    }

    private static long[] read256(long addr) {
        long[] l128 = read128(addr);
        long[] h128 = read128(addr + 16);
        return new long[]{l128[0], l128[1], h128[0], h128[1]};
    }

    private static Step r8(long addr) {
        return new Step(Op.R8, List.of(addr, read8(addr)), 0);
    }

    private static Step r16(long addr) {
        return new Step(Op.R16, List.of(addr, read16(addr)), 0);
    }

    private static Step r32(long addr) {
        return new Step(Op.R32, List.of(addr, read32(addr)), 0);
    }

    private static Step r64(long addr) {
        return new Step(Op.R64, List.of(addr, read64(addr)), 0);
    }

    private static Step r128(long addr) {
        long[] v = read128(addr);
        return new Step(Op.R128, List.of(addr, v[0], v[1]), 0);
    }

    private static Step r256(long addr) {
        long[] v = read256(addr);
        return new Step(Op.R256, List.of(addr, v[0], v[1], v[2], v[3]), 0);
    }

    private static Step w8(long addr, long val) {
        return new Step(Op.W8, List.of(addr, val), 0);
    }

    private static Step w16(long addr, long val) {
        return new Step(Op.W16, List.of(addr, val), 0);
    }

    private static Step w32(long addr, long val) {
        return new Step(Op.W32, List.of(addr, val), 0);
    }

    private static Step w64(long addr, long val) {
        return new Step(Op.W64, List.of(addr, val), 0);
    }

    private static Step w128(long addr, long low, long high) {
        return new Step(Op.W128, List.of(addr, low, high), 0);
    }

    private static Step w256(long addr, long l0, long l1, long h0, long h1) {
        return new Step(Op.W256, List.of(addr, l0, l1, h0, h1), 0);
    }

    private static Step fence() {
        return new Step(Op.FENCE, List.of(), 0);
    }

    public static List<CopyWitnessData370.Scene> scenes() {
        List<CopyWitnessData370.Scene> list = new ArrayList<>();

        {
            long d = S + 1;
            long n = 15;
            List<Step> steps = new ArrayList<>();
            steps.add(new Step(Op.R32, List.of(M + 0x6090000L + 15 * 4L, 0x04226890L), 0));

            steps.add(r64(S));
            steps.add(r32(S + 8));
            steps.add(r16(S + 12));
            steps.add(r8(S + 14));

            steps.add(w64(d, read64(S)));
            steps.add(w32(d + 8, read32(S + 8)));
            steps.add(w16(d + 12, read16(S + 12)));
            steps.add(w8(d + 14, read8(S + 14)));

            list.add(new Scene("BasicSMALL", Target.SMALL, d, S, n, M, steps, 0));
        }

        {
            long d = 0x1100000000L;
            long n = 3;
            List<Step> steps = new ArrayList<>();
            steps.add(r8(S));
            steps.add(w8(d, read8(S)));
            steps.add(r8(S + 1));
            steps.add(w8(d + 1, read8(S + 1)));
            steps.add(r8(S + 2));
            steps.add(w8(d + 2, read8(S + 2)));

            list.add(new Scene("BasicREP", Target.REP, d, S, n, M, steps, 0));
        }

        {
            long d = S + 1;
            long n = 17;
            List<Step> steps = new ArrayList<>();

            steps.add(r128(S));
            steps.add(r128(S + 1));
            steps.add(w128(d, read128(S)[0], read128(S)[1]));
            steps.add(w128(d + 1, read128(S + 1)[0], read128(S + 1)[1]));

            list.add(new Scene("BasicDISPATCH", Target.DISPATCH, d, S, n, M, steps, d));
        }

        return list;
    }
}
