package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

/** Reused owned byte-memory and literal call assertions; contains no target or expected-state algorithm. */
public final class GovernmentSharedComposition168Fixture {
    private GovernmentSharedComposition168Fixture() { }
    public static void equal(Object expected, Object actual, String what) {
        if (!Objects.equals(expected, actual)) throw new AssertionError(what + " expected=" + expected + " actual=" + actual);
    }
    public static Bits128 vector(long seed) { return new Bits128(seed, ~seed); }
    public static VolatileBits bits(long seed, long rax, long rcx, long rdx) {
        return new VolatileBits(rax, rcx, rdx, seed + 8, seed + 9, seed + 10, seed + 11,
                vector(seed + 0x10), vector(seed + 0x20), vector(seed + 0x30),
                vector(seed + 0x40), vector(seed + 0x50), vector(seed + 0x60));
    }
    public static VolatileBits fields(VolatileBits v, long rax, long rcx, long rdx, long r8, Bits128 x0) {
        return new VolatileBits(rax, rcx, rdx, r8, v.r9Bits(), v.r10Bits(), v.r11Bits(),
                x0, v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
    }
    public static long u32(int value) { return Integer.toUnsignedLong(value); }
    public static OpaqueCall call(long site, long target, long rsp, VolatileBits v, NonvolatileBits n) {
        return new OpaqueCall(site, target, rsp, v, n);
    }
    public record AtomicDword(long address, int addend, int oldValue) { }
    public record AtomicByte(long address, int lowAddend, int oldValue) { }
    public static final class MemoryImage implements GovernmentSharedManager167Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        public final List<AtomicDword> atomicDwords = new ArrayList<>();
        public final List<AtomicByte> atomicBytes = new ArrayList<>();
        @Override public int readUnsignedByte(long address) {
            Byte value = bytes.get(address);
            if (value == null) throw new UnsupportedOperationException("unseeded byte " + Long.toUnsignedString(address, 16));
            return Byte.toUnsignedInt(value);
        }
        @Override public int readDword(long address) {
            int value = 0;
            for (int i = 0; i < 4; i++) value |= readUnsignedByte(address + i) << (8 * i);
            return value;
        }
        @Override public long readQword(long address) {
            long value = 0;
            for (int i = 0; i < 8; i++) value |= (long)readUnsignedByte(address + i) << (8 * i);
            return value;
        }
        @Override public void writeByte(long address, int value) { bytes.put(address, (byte)value); }
        @Override public void writeDword(long address, int value) {
            for (int i = 0; i < 4; i++) writeByte(address + i, value >>> (8 * i));
        }
        @Override public void writeQword(long address, long value) {
            for (int i = 0; i < 8; i++) writeByte(address + i, (int)(value >>> (8 * i)));
        }
        @Override public int lockedXaddDword(long address, int addend) {
            int old = readDword(address); writeDword(address, old + addend);
            atomicDwords.add(new AtomicDword(address, addend, old)); return old;
        }
        @Override public int lockedXaddByte(long address, int addend) {
            int old = readUnsignedByte(address); writeByte(address, old + (addend & 255));
            atomicBytes.add(new AtomicByte(address, addend & 255, old)); return old;
        }
        @Override public Bits128 read128(long address) { return new Bits128(readQword(address), readQword(address + 8)); }
        @Override public void write128(long address, Bits128 value) {
            writeQword(address, value.lowBits()); writeQword(address + 8, value.highBits());
        }
    }
    private record Expected(OpaqueCall call, VolatileBits result, Runnable sideEffect) { }
    public static final class CallScript implements Calls {
        private final List<Expected> expected = new ArrayList<>();
        private final long gsValue;
        private int index, gsReads;
        public CallScript(long gsValue) { this.gsValue = gsValue; }
        public CallScript expect(OpaqueCall call, VolatileBits result, Runnable sideEffect) {
            expected.add(new Expected(call, result, sideEffect)); return this;
        }
        @Override public long readGsQword58() { gsReads++; return gsValue; }
        @Override public VolatileBits invoke(OpaqueCall actual) {
            if (index == expected.size()) throw new AssertionError("unexpected opaque call " + actual);
            Expected e = expected.get(index++); equal(e.call(), actual, "full opaque call " + index);
            e.sideEffect().run(); return e.result();
        }
        public void done(int expectedGsReads) {
            equal(expected.size(), index, "opaque call count"); equal(expectedGsReads, gsReads, "GS reads");
        }
    }
    public record Case(String name, GovernmentRowResolve164Api.Entry entry, MemoryImage memory,
            CallScript delegate, GovernmentLookup167Api.SpinBudget budget,
            GovernmentRowResolve164Api.Result expected, int expectedGsReads, Runnable after) {
        public Case {
            Objects.requireNonNull(name); Objects.requireNonNull(entry); Objects.requireNonNull(memory);
            Objects.requireNonNull(delegate); Objects.requireNonNull(budget); Objects.requireNonNull(expected);
            Objects.requireNonNull(after);
        }
    }
}
