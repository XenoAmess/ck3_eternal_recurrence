package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Mechanical owned single-thread RAM and trace; no target algorithm or chosen input bank. */
public final class StaticRetryFixture649 {
    private StaticRetryFixture649() { }

    /** Scalar payload a is raw bits; unused payloads are zero. */
    public record Event(String kind, long address, long a, long b, long c, long d) {
        public Event { Objects.requireNonNull(kind); }
    }

    public static Event e(String kind, long address, long value) {
        return new Event(kind, address, value, 0, 0, 0);
    }

    public static Event e128(String kind, long address, Bits128 value) {
        Objects.requireNonNull(value);
        return new Event(kind, address, value.lowBits(), value.highBits(), 0, 0);
    }

    public static final class Trace {
        private final List<Event> events = new ArrayList<>();

        public void add(Event event) { events.add(Objects.requireNonNull(event)); }
        public int size() { return events.size(); }
        public List<Event> snapshot() { return List.copyOf(events); }
        public void checkExactly(List<Event> expected, String message) {
            checkEqual(Objects.requireNonNull(expected), events, message);
        }
    }

    public static Bits128 bits128(long lowBits, long highBits) {
        return new Bits128(lowBits, highBits);
    }

    /** All thirteen volatile fields are explicitly supplied by the caller. */
    public static VolatileBits volatileBits(long rax, long rcx, long rdx,
            long r8, long r9, long r10, long r11,
            Bits128 x0, Bits128 x1, Bits128 x2, Bits128 x3, Bits128 x4, Bits128 x5) {
        return new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
    }

    /** Full raw R12 and every other field come from the caller, with no narrowing. */
    public static NonvolatileBits nonvolatileBits(long rbx, long rbp, long rsi, long rdi,
            long r12, long r13, long r14, long r15, Bits128 x6) {
        return new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
    }

    public static GovernmentCrtBoundary185Api.Entry entry(long image, long rsp,
            VolatileBits v, NonvolatileBits n) {
        return new GovernmentCrtBoundary185Api.Entry(image, rsp, v, n);
    }

    public static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void checkSame(Object expected, Object actual, String message) {
        check(expected == actual, message);
    }

    /** Structural equality for the supplied records, lists and maps. */
    public static void checkEqual(Object expected, Object actual, String message) {
        check(Objects.equals(expected, actual), message);
    }

    public static void checkFullBytes(Map<Long, Byte> expected, Ram actual, String message) {
        checkEqual(Objects.requireNonNull(expected), Objects.requireNonNull(actual).fullBytes(), message);
    }

    /**
     * Exactly the declared185.Memory union. Addresses wrap as raw long bits.
     * Unseeded bytes read as zero in this software fixture; this is no physical-memory guarantee.
     * Primitive traces record one event per declared Memory operation, never per internal byte.
     */
    public static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        public final Trace trace;

        public Ram(Trace trace) { this.trace = Objects.requireNonNull(trace); }

        private static void scalarWidth(int width) {
            if (width < 1 || width > Long.BYTES) {
                throw new IllegalArgumentException("Scalar width must be 1..8");
            }
        }

        /** Initial fixture bytes only; these seeding operations produce no Memory events. */
        public void seedScalar(long address, int width, long value) {
            scalarWidth(width);
            for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (8 * i)));
        }

        public void seedFill(long address, int count, int unsignedByte) {
            if (count < 0 || unsignedByte < 0 || unsignedByte > 255) {
                throw new IllegalArgumentException("Nonnegative count and unsigned byte required");
            }
            for (int i = 0; i < count; i++) bytes.put(address + i, (byte) unsignedByte);
        }

        public void seedBytes(long address, byte[] values) {
            Objects.requireNonNull(values);
            for (int i = 0; i < values.length; i++) bytes.put(address + i, values[i]);
        }

        public void seed128(long address, Bits128 value) {
            Objects.requireNonNull(value);
            seedScalar(address, Long.BYTES, value.lowBits());
            seedScalar(address + Long.BYTES, Long.BYTES, value.highBits());
        }

        /** Pure little-endian inspection; no trace and no inferred target state. */
        public long peekScalar(long address, int width) {
            scalarWidth(width);
            long value = 0;
            for (int i = 0; i < width; i++) {
                value |= (bytes.getOrDefault(address + i, (byte) 0) & 255L) << (8 * i);
            }
            return value;
        }

        public byte[] peekBytes(long address, int count) {
            if (count < 0) throw new IllegalArgumentException("Negative byte count");
            byte[] result = new byte[count];
            for (int i = 0; i < count; i++) result[i] = bytes.getOrDefault(address + i, (byte) 0);
            return result;
        }

        public Map<Long, Byte> fullBytes() { return Map.copyOf(bytes); }

        /** R32/W32 trace payloads are zero-extended raw32 bits; API return remains signed int. */
        @Override public int readDword(long address) {
            int value = (int) peekScalar(address, Integer.BYTES);
            trace.add(e("R32", address, Integer.toUnsignedLong(value)));
            return value;
        }

        @Override public long readQword(long address) {
            long value = peekScalar(address, Long.BYTES);
            trace.add(e("R64", address, value));
            return value;
        }

        @Override public int readUnsignedByte(long address) {
            int value = (int) peekScalar(address, 1);
            trace.add(e("R8", address, value));
            return value;
        }

        @Override public void writeDword(long address, int value) {
            trace.add(e("W32", address, Integer.toUnsignedLong(value)));
            seedScalar(address, Integer.BYTES, Integer.toUnsignedLong(value));
        }

        /** One represented read-modify-write event; no CPU/OS or concurrent atomicity proof. */
        @Override public int lockedXaddDword(long address, int addend) {
            int old = (int) peekScalar(address, Integer.BYTES);
            int sum = old + addend;
            trace.add(new Event("LOCK_XADD32", address, Integer.toUnsignedLong(addend),
                    Integer.toUnsignedLong(old), Integer.toUnsignedLong(sum), 0));
            seedScalar(address, Integer.BYTES, Integer.toUnsignedLong(sum));
            return old;
        }

        @Override public void writeQword(long address, long value) {
            trace.add(e("W64", address, value));
            seedScalar(address, Long.BYTES, value);
        }

        @Override public void writeByte(long address, int value) {
            trace.add(e("W8", address, value & 255L));
            seedScalar(address, 1, value);
        }

        @Override public Bits128 read128(long address) {
            Bits128 value = new Bits128(peekScalar(address, Long.BYTES),
                    peekScalar(address + Long.BYTES, Long.BYTES));
            trace.add(e128("R128", address, value));
            return value;
        }

        @Override public void write128(long address, Bits128 value) {
            Objects.requireNonNull(value);
            trace.add(e128("W128", address, value));
            seed128(address, value);
        }
    }
}
