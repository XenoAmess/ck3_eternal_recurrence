package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.add4range262.Add4Range262;

/**
 * Mechanical byte RAM/events and fully caller-supplied register-bank constructors.
 * Primitive recording body descends from StaticFixture648 (itself ParentFixture647);
 * no parent factory, target algorithm or oracle.
 * Unseeded fixture bytes read as zero. This is owned software RAM, not a physical-memory guarantee.
 */
public final class WholeRotateFixture651 {
    private WholeRotateFixture651() { }

    public record Event(String kind, long address, long a, long b, long c, long d) { }

    public static Event e(String k, long p, long v) {
        return new Event(k, p, v, 0, 0, 0);
    }

    public static Event e128(String k, long p, Bits128 v) {
        return new Event(k, p, v.lowBits(), v.highBits(), 0, 0);
    }

    public static Event e256(String k, long p, FullCopy437Api.Bits256 v) {
        return new Event(k, p, v.low().lowBits(), v.low().highBits(), v.high().lowBits(), v.high().highBits());
    }

    /** Every bit below comes from the caller; no register, image, stack, DF or FP default exists here. */
    public static Bits128 bits128(long low, long high) {
        return new Bits128(low, high);
    }

    public static FullCopy437Api.Bits256 bits256(Bits128 low, Bits128 high) {
        return new FullCopy437Api.Bits256(low, high);
    }

    public static VolatileBits volatileBits(long rax, long rcx, long rdx, long r8, long r9, long r10, long r11,
            Bits128 x0, Bits128 x1, Bits128 x2, Bits128 x3, Bits128 x4, Bits128 x5) {
        return new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
    }

    public static NonvolatileBits nonvolatileBits(long rbx, long rbp, long rsi, long rdi,
            long r12, long r13, long r14, long r15, Bits128 x6) {
        return new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
    }

    public static GovernmentCrtBoundary185Api.Entry entry(long image, long rsp, VolatileBits v, NonvolatileBits n) {
        return new GovernmentCrtBoundary185Api.Entry(image, rsp, v, n);
    }

    public static final class Ram implements Element172KnownLower640.Memory, Add4Range262.Memory {
        public final Map<Long, Byte> bytes = new HashMap<>();
        public final List<Event> events = new ArrayList<>();

        private static void scalarWidth(int bytes) {
            if (bytes < 1 || bytes > 8) throw new IllegalArgumentException("scalar width must be 1..8 bytes");
        }

        /** Scalar raw bits, little endian, 1..8 bytes. Address arithmetic wraps as Java long. */
        public void seed(long p, int w, long value) {
            scalarWidth(w);
            for (int j = 0; j < w; j++) bytes.put(p + j, (byte)(value >>> (8 * j)));
        }

        public long peek(long p, int w) {
            scalarWidth(w);
            long v = 0;
            for (int j = 0; j < w; j++) v |= (bytes.getOrDefault(p + j, (byte)0) & 255L) << (8 * j);
            return v;
        }

        public void seedBytes(long p, byte[] values) {
            java.util.Objects.requireNonNull(values);
            for (int j = 0; j < values.length; j++) bytes.put(p + j, values[j]);
        }

        public byte[] peekBytes(long p, int count) {
            if (count < 0) throw new IllegalArgumentException("negative byte count");
            byte[] out = new byte[count];
            for (int j = 0; j < count; j++) out[j] = bytes.getOrDefault(p + j, (byte)0);
            return out;
        }

        public Map<Long, Byte> fullBytes() {
            return Map.copyOf(bytes);
        }

        public void seed128(long p, Bits128 v) {
            seed(p, 8, v.lowBits());
            seed(p + 8, 8, v.highBits());
        }

        public void seed256(long p, FullCopy437Api.Bits256 v) {
            seed128(p, v.low());
            seed128(p + 16, v.high());
        }

        public void step(long pc, long cursor) {
            events.add(e("BUDGET", pc, cursor));
        }

        @Override public int readDword(long p) {
            int v = (int)peek(p, 4);
            events.add(e("R32", p, v));
            return v;
        }

        @Override public long readQword(long p) {
            long v = peek(p, 8);
            events.add(e("R64", p, v));
            return v;
        }

        @Override public Bits128 read128(long p) {
            Bits128 v = new Bits128(peek(p, 8), peek(p + 8, 8));
            events.add(e128("R128", p, v));
            return v;
        }

        @Override public FullCopy437Api.Bits256 read256(long p) {
            var v = new FullCopy437Api.Bits256(
                new Bits128(peek(p, 8), peek(p + 8, 8)),
                new Bits128(peek(p + 16, 8), peek(p + 24, 8))
            );
            events.add(e256("R256", p, v));
            return v;
        }

        @Override public void writeDword(long p, int v) {
            events.add(e("W32", p, v));
            seed(p, 4, v);
        }

        @Override public void writeQword(long p, long v) {
            events.add(e("W64", p, v));
            seed(p, 8, v);
        }

        @Override public void write128(long p, Bits128 v) {
            events.add(e128("W128", p, v));
            seed(p, 8, v.lowBits());
            seed(p + 8, 8, v.highBits());
        }

        @Override public void write256(long p, FullCopy437Api.Bits256 v) {
            events.add(e256("W256", p, v));
            seed(p, 8, v.low().lowBits());
            seed(p + 8, 8, v.low().highBits());
            seed(p + 16, 8, v.high().lowBits());
            seed(p + 24, 8, v.high().highBits());
        }

        @Override public int readUnsignedByte(long p) {
            int v = (int)peek(p, 1);
            events.add(e("R8", p, v));
            return v;
        }

        @Override public int readUnsignedWord(long p) {
            int v = (int)peek(p, 2);
            events.add(e("R16", p, v));
            return v;
        }

        @Override public void writeByte(long p, int v) {
            events.add(e("W8", p, v & 255));
            seed(p, 1, v);
        }

        @Override public void writeWord(long p, int v) {
            events.add(e("W16", p, v & 65535));
            seed(p, 2, v);
        }

        @Override public int lockedXaddDword(long p, int v) {
            int old = (int)peek(p, 4);
            int sum = old + v;
            events.add(new Event("LOCK_XADD32", p, v, old, sum, 0));
            seed(p, 4, sum);
            return old;
        }

        @Override public void write128NonTemporal(long p, Bits128 v) {
            events.add(e128("W128NT", p, v));
            seed128(p, v);
        }

        @Override public void write256NonTemporal(long p, FullCopy437Api.Bits256 v) {
            events.add(e256("W256NT", p, v));
            seed256(p, v);
        }

        @Override public void sfence() {
            events.add(e("SFENCE", 0, 0));
        }

        @Override public void vzeroUpper() {
            events.add(new Event("VZEROUPPER", 0, 0, 0, 0, 0));
        }
    }
}