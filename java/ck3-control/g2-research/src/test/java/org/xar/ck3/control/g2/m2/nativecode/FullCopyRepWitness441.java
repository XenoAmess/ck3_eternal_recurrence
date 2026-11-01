package org.xar.ck3.control.g2.m2.nativecode;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.CallResult;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Bits256;

public final class FullCopyRepWitness441 {
    private FullCopyRepWitness441() { }

    static final long E = 0x8100000000009008L;
    static final long M = 0x0000003300000000L;
    static final long B = 0x8100000000001000L;
    static final long RET = 0xAABBCCDD11223344L;

    static int assertions = 0;

    static void eq(Object e, Object a, String why) {
        assertions++;
        if (!Objects.equals(e, a)) throw new AssertionError(why + " expected=" + e + " actual=" + a);
    }

    static Bits128 x(long n) { return new Bits128(n, ~n); }

    static VolatileBits v(long seed, long ax, long cx, long dx, long r8, long r9, long r10, long r11) {
        return new VolatileBits(ax, cx, dx, r8, r9, r10, r11, x(seed + 0x10), x(seed + 0x20), x(seed + 0x30), x(seed + 0x40), x(seed + 0x50), x(seed + 0x60));
    }

    static NonvolatileBits n(long bx, long bp, long si, long di) {
        return new NonvolatileBits(bx, bp, si, di, 0x2005, 0x2006, 0x2007, 0x2008, x(0x2060));
    }

    static NonvolatileBits n() { return n(0x2001, 0x2002, 0x2003, 0x2004); }

    record Ev(String op, long address, long bits) { }
    static Ev e(String op, long a, long b) { return new Ev(op, a, b); }

    static final class Mem implements FullCopy437Api.Memory {
        final Map<Long, Byte> bytes = new HashMap<>();
        final List<Ev> trace = new ArrayList<>();

        int byteAt(long a) {
            Byte b = bytes.get(a);
            if (b == null) throw new UnsupportedOperationException("unseeded " + Long.toUnsignedString(a, 16));
            return Byte.toUnsignedInt(b);
        }

        long peek(long a, int width) {
            long r = 0;
            for (int i = 0; i < width; i++) r |= (long) byteAt(a + i) << (i * 8);
            return r;
        }

        void seed(long a, long bits, int width) {
            for (int i = 0; i < width; i++) bytes.put(a + i, (byte) (bits >>> (8 * i)));
        }

        @Override public int readUnsignedByte(long a) { int r = byteAt(a); trace.add(e("R8", a, r)); return r; }
        @Override public int readDword(long a) { throw new UnsupportedOperationException("unusedDWORD"); }
        @Override public long readQword(long a) { long r = peek(a, 8); trace.add(e("R64", a, r)); return r; }
        @Override public void writeByte(long a, int b) { seed(a, b, 1); trace.add(e("W8", a, b & 255L)); }
        @Override public void writeDword(long a, int b) { throw new UnsupportedOperationException("unusedDWORD"); }
        @Override public void writeQword(long a, long b) { seed(a, b, 8); trace.add(e("W64", a, b)); }
        @Override public int lockedXaddDword(long a, int b) { throw new UnsupportedOperationException("unused atomic"); }
        @Override public Bits128 read128(long a) { throw new UnsupportedOperationException("unused128"); }
        @Override public void write128(long a, Bits128 b) { throw new UnsupportedOperationException("unused128"); }
        @Override public void writeWord(long a, int b) { throw new UnsupportedOperationException("unusedWORD"); }
        @Override public void write128NonTemporal(long a, Bits128 b) { throw new UnsupportedOperationException("unusedNT"); }
        @Override public void sfence() { throw new UnsupportedOperationException("unusedFENCE"); }
        @Override public int readUnsignedWord(long a) { throw new UnsupportedOperationException("unusedWORD"); }
        @Override public Bits256 read256(long a) { throw new UnsupportedOperationException("unused256"); }
        @Override public void write256(long a, Bits256 b) { throw new UnsupportedOperationException("unused256"); }
        @Override public void write256NonTemporal(long a, Bits256 b) { throw new UnsupportedOperationException("unusedNT256"); }
    }

    static final class Budget implements GovernmentCrtBoundary185Api.LoopBudget {
        int count = 0;
        int limit;
        List<Ev> trace;
        Budget(int limit, List<Ev> trace) { this.limit = limit; this.trace = trace; }
        @Override public void beforeStep(long h, long c) {
            count++;
            if (count > limit) throw new AssertionError("budget exceeded");
            trace.add(e("STEP", h, c));
        }
    }

    static void runCase(long dest, long source, long count, boolean df, long expectedRip, long expectedSp, List<Ev> expectedTrace, NonvolatileBits expectedN) {
        Mem mem = new Mem();

        mem.seed(E, RET, 8);
        if (df) {
            mem.seed(B + 0x102L, 0xA6, 1);
            mem.seed(B + 0x101L, 0xB7, 1);
        } else if (count == 17) {
            for (int i = 0; i < 17; i++) mem.seed(B + 0x100L + i, 0x40 + i, 1);
        }

        long seed = 0x1000L;
        long rax = 0x8877665544332211L;
        long rcx = dest;
        long rdx = source;
        long r8 = count;
        long r9 = 0x1009L;
        long r10 = 0x100AL;
        long r11 = 0x100BL;

        VolatileBits inV = v(seed, rax, rcx, rdx, r8, r9, r10, r11);
        NonvolatileBits inN = n();

        Budget budget = new Budget((int) count + 1, mem.trace);
        Input input = new Input(new GovernmentCrtBoundary185Api.Entry(M, E, inV, inN), df, budget);
        VolatileBits expectedV = v(seed, rax, 0L, rdx, r8, r9, r10, r11);
        CallResult expected = new CallResult(new NormalReturn(expectedV, expectedRip, expectedSp, expectedN), df);
        CallResult actual = FullCopyRep4226840.execute(input, mem);
        eq(expected, actual, "whole declared V/N/XMM/actualRET/SP/DF");
        eq((int) count, budget.count, "exact finite budget count");

        eq(expectedTrace, mem.trace, "Trace");
    }

    static void case0() {
        List<Ev> expectedTrace = List.of(
            e("W64", 0x8100000000009000L, 0x0000000000002004L),
            e("W64", 0x8100000000008FF8L, 0x0000000000002003L),
            e("R64", 0x8100000000008FF8L, 0x0000000000002003L),
            e("R64", 0x8100000000009000L, 0x0000000000002004L),
            e("R64", 0x8100000000009008L, 0xAABBCCDD11223344L)
        );
        runCase(0x8100000000001000L, 0x8100000000001100L, 0, false, 0xAABBCCDD11223344L, 0x8100000000009010L, expectedTrace, n());
    }

    static void case1() {
        List<Ev> expectedTrace = List.of(
            e("W64", 0x8100000000009000L, 0x0000000000002004L),
            e("W64", 0x8100000000008FF8L, 0x0000000000002003L),
            e("STEP", 0x000000000422684BL, 0x8100000000001002L),
            e("R8", 0x8100000000001102L, 0x00000000000000A6L),
            e("W8", 0x8100000000001002L, 0x00000000000000A6L),
            e("STEP", 0x000000000422684BL, 0x8100000000001001L),
            e("R8", 0x8100000000001101L, 0x00000000000000B7L),
            e("W8", 0x8100000000001001L, 0x00000000000000B7L),
            e("R64", 0x8100000000008FF8L, 0x0000000000002003L),
            e("R64", 0x8100000000009000L, 0x0000000000002004L),
            e("R64", 0x8100000000009008L, 0xAABBCCDD11223344L)
        );
        runCase(0x8100000000001002L, 0x8100000000001102L, 2, true, 0xAABBCCDD11223344L, 0x8100000000009010L, expectedTrace, n());
    }

    static void case2() {
        List<Ev> expectedTrace = List.of(
            e("W64", 0x8100000000009000L, 0x0000000000002004L),
            e("W64", 0x8100000000008FF8L, 0x0000000000002003L),
            e("STEP", 0x000000000422684BL, 0x8100000000008FF8L),
            e("R8", 0x8100000000001100L, 0x0000000000000040L),
            e("W8", 0x8100000000008FF8L, 0x0000000000000040L),
            e("STEP", 0x000000000422684BL, 0x8100000000008FF9L),
            e("R8", 0x8100000000001101L, 0x0000000000000041L),
            e("W8", 0x8100000000008FF9L, 0x0000000000000041L),
            e("STEP", 0x000000000422684BL, 0x8100000000008FFAL),
            e("R8", 0x8100000000001102L, 0x0000000000000042L),
            e("W8", 0x8100000000008FFAL, 0x0000000000000042L),
            e("STEP", 0x000000000422684BL, 0x8100000000008FFBL),
            e("R8", 0x8100000000001103L, 0x0000000000000043L),
            e("W8", 0x8100000000008FFBL, 0x0000000000000043L),
            e("STEP", 0x000000000422684BL, 0x8100000000008FFCL),
            e("R8", 0x8100000000001104L, 0x0000000000000044L),
            e("W8", 0x8100000000008FFCL, 0x0000000000000044L),
            e("STEP", 0x000000000422684BL, 0x8100000000008FFDL),
            e("R8", 0x8100000000001105L, 0x0000000000000045L),
            e("W8", 0x8100000000008FFDL, 0x0000000000000045L),
            e("STEP", 0x000000000422684BL, 0x8100000000008FFEL),
            e("R8", 0x8100000000001106L, 0x0000000000000046L),
            e("W8", 0x8100000000008FFEL, 0x0000000000000046L),
            e("STEP", 0x000000000422684BL, 0x8100000000008FFFL),
            e("R8", 0x8100000000001107L, 0x0000000000000047L),
            e("W8", 0x8100000000008FFFL, 0x0000000000000047L),
            e("STEP", 0x000000000422684BL, 0x8100000000009000L),
            e("R8", 0x8100000000001108L, 0x0000000000000048L),
            e("W8", 0x8100000000009000L, 0x0000000000000048L),
            e("STEP", 0x000000000422684BL, 0x8100000000009001L),
            e("R8", 0x8100000000001109L, 0x0000000000000049L),
            e("W8", 0x8100000000009001L, 0x0000000000000049L),
            e("STEP", 0x000000000422684BL, 0x8100000000009002L),
            e("R8", 0x810000000000110AL, 0x000000000000004AL),
            e("W8", 0x8100000000009002L, 0x000000000000004AL),
            e("STEP", 0x000000000422684BL, 0x8100000000009003L),
            e("R8", 0x810000000000110BL, 0x000000000000004BL),
            e("W8", 0x8100000000009003L, 0x000000000000004BL),
            e("STEP", 0x000000000422684BL, 0x8100000000009004L),
            e("R8", 0x810000000000110CL, 0x000000000000004CL),
            e("W8", 0x8100000000009004L, 0x000000000000004CL),
            e("STEP", 0x000000000422684BL, 0x8100000000009005L),
            e("R8", 0x810000000000110DL, 0x000000000000004DL),
            e("W8", 0x8100000000009005L, 0x000000000000004DL),
            e("STEP", 0x000000000422684BL, 0x8100000000009006L),
            e("R8", 0x810000000000110EL, 0x000000000000004EL),
            e("W8", 0x8100000000009006L, 0x000000000000004EL),
            e("STEP", 0x000000000422684BL, 0x8100000000009007L),
            e("R8", 0x810000000000110FL, 0x000000000000004FL),
            e("W8", 0x8100000000009007L, 0x000000000000004FL),
            e("STEP", 0x000000000422684BL, 0x8100000000009008L),
            e("R8", 0x8100000000001110L, 0x0000000000000050L),
            e("W8", 0x8100000000009008L, 0x0000000000000050L),
            e("R64", 0x8100000000008FF8L, 0x4746454443424140L),
            e("R64", 0x8100000000009000L, 0x4F4E4D4C4B4A4948L),
            e("R64", 0x8100000000009008L, 0xAABBCCDD11223350L)
        );
        NonvolatileBits expectedN = n(0x2001L, 0x2002L, 0x4746454443424140L, 0x4F4E4D4C4B4A4948L);
        runCase(0x8100000000008FF8L, 0x8100000000001100L, 17, false, 0xAABBCCDD11223350L, 0x8100000000009010L, expectedTrace, expectedN);
    }

    public static int verify() {
        case0();
        case1();
        case2();
        return 3;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }
}
