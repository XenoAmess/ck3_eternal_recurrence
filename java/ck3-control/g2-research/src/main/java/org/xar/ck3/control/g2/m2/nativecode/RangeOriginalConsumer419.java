package org.xar.ck3.control.g2.m2.nativecode;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

/** Verifies the four original RAM observations against separate software replay RAM. */
public final class RangeOriginalConsumer419 {
    private RangeOriginalConsumer419() { }

    private static final int DATA_BYTES = 4096;
    private static final int PROTOCOL_BYTES = 33036;
    private static final long MAXIMUM_BYTES = 64L << 20;
    private static final long CPU_RVA = 0x0542F09CL;
    private static final long SSE_RVA = 0x0441F520L;
    private static final long AVX_RVA = 0x0441F540L;
    private static final byte[] MAGIC = {'M', '2', 'R', '4', '1', '9', '0', '1'};
    private static final byte[] SSE_MASK = HexFormat.of().parseHex("0f0e0d0c0b0a09080706050403020100");
    private static final byte[] AVX_MASK = HexFormat.of().parseHex(
            "0f0e0d0c0b0a090807060504030201000f0e0d0c0b0a09080706050403020100");
    private static final int[][] RECIPES = {
        {0, 0, 0, 64, 64, 64},
        {1, 0, 0, 64, 64, 67},
        {2, 0, 4, 64, 64, 96},
        {3, 1, 0, 64, 66, 69}
    };

    public static int verify(InputStream input) throws IOException {
        Reader reader = new Reader(input);
        if (!Arrays.equals(reader.bytes(8), MAGIC)) throw new IOException("original419 magic differs");
        if (reader.u32() != RECIPES.length) throw new IOException("original419 requires four rows");
        for (int row = 0; row < RECIPES.length; row++) {
            int scene = reader.u32(), kind = reader.u32(), cpu = reader.u32(), unchanged = reader.u32();
            long moduleBase = reader.u64(), dataBase = reader.u64();
            long first = reader.u64(), middle = reader.u64(), last = reader.u64(), returned = reader.u64();
            int[] recipe = RECIPES[row];
            if (scene != recipe[0] || kind != recipe[1] || cpu != recipe[2] || unchanged != 1)
                throw new IOException("original419 row metadata differs at " + row);
            Geometry geometry = new Geometry(moduleBase, dataBase);
            if (first != checkedAdd(dataBase, recipe[3]) || middle != checkedAdd(dataBase, recipe[4])
                    || last != checkedAdd(dataBase, recipe[5]))
                throw new IOException("original419 row coordinates differ at " + row);
            geometry.data.offset(first, 1); geometry.data.offset(middle, 1); geometry.data.offset(last, 1);
            if (kind == 0 && returned != 0) throw new IOException("leaf RAX is unqualified");
            byte[] before = reader.bytes(DATA_BYTES);
            for (int i = 0; i < before.length; i++)
                if ((before[i] & 0xff) != ((i + 0x10) & 0xff))
                    throw new IOException("original419 before pattern differs at " + row + ":" + i);
            byte[] actualAfter = reader.bytes(DATA_BYTES);
            byte[] replay = reader.copy(before);
            Memory memory = new Memory(geometry, cpu, replay);
            Budget budget = new Budget(geometry.data);
            if (kind == 0) {
                PendingByteReverse42208E8.reverse(memory, budget, first, last, moduleBase);
            } else {
                long actual = PendingRangeOrder9CF240.apply(memory, budget,
                        new RangeOrder410Api.Input(first, middle, last, moduleBase));
                if (actual != returned) throw new IOException("original419 upper raw RAX differs");
            }
            if (!Arrays.equals(replay, actualAfter))
                throw new IOException("original419 full replay RAM differs at row " + row);
        }
        if (reader.consumed != PROTOCOL_BYTES) throw new IOException("original419 protocol byte count differs");
        reader.requireEof();
        return RECIPES.length;
    }

    public static void main(String[] args) throws IOException {
        System.out.println(verify(System.in));
    }

    private static long checkedAdd(long base, long offset) {
        if (offset < 0) throw new IllegalArgumentException("negative finite region offset");
        long result = base + offset;
        if (Long.compareUnsigned(result, base) < 0) throw new IllegalArgumentException("unsigned region wraps");
        return result;
    }

    private static final class Region {
        final long base, end;
        final int bytes;
        Region(long base, int bytes) {
            if (bytes <= 0) throw new IllegalArgumentException("positive finite region required");
            this.base = base; this.bytes = bytes; this.end = checkedAdd(base, bytes);
        }
        boolean contains(long address, int width) {
            return width > 0 && width <= bytes && Long.compareUnsigned(address, base) >= 0
                    && Long.compareUnsigned(address - base, bytes - width) <= 0;
        }
        int offset(long address, int width) {
            if (!contains(address, width)) throw new IllegalArgumentException("complete access exceeds unsigned region");
            return (int) (address - base);
        }
        boolean overlaps(Region other) {
            return Long.compareUnsigned(base, other.end) < 0 && Long.compareUnsigned(other.base, end) < 0;
        }
    }

    private static final class Geometry {
        final Region data, cpu, sse, avx;
        Geometry(long moduleBase, long dataBase) {
            data = new Region(dataBase, DATA_BYTES);
            cpu = new Region(checkedAdd(moduleBase, CPU_RVA), 4);
            sse = new Region(checkedAdd(moduleBase, SSE_RVA), SSE_MASK.length);
            avx = new Region(checkedAdd(moduleBase, AVX_RVA), AVX_MASK.length);
            if (data.overlaps(cpu) || data.overlaps(sse) || data.overlaps(avx))
                throw new IllegalArgumentException("replay data overlaps original readonly controls");
        }
    }

    private static final class Reader {
        private final InputStream input;
        private long reserved, consumed;
        Reader(InputStream input) { this.input = Objects.requireNonNull(input); }
        private void reserve(int bytes) throws IOException {
            if (bytes < 0 || bytes > MAXIMUM_BYTES - reserved)
                throw new IOException("original419 finite input/copy budget exceeded");
            reserved += bytes;
        }
        byte[] bytes(int count) throws IOException {
            reserve(count);
            byte[] result = new byte[count];
            int offset = 0;
            while (offset < result.length) {
                int read = input.read(result, offset, result.length - offset);
                if (read < 0) throw new EOFException("short original419 packet");
                if (read == 0) {
                    int one = input.read();
                    if (one < 0) throw new EOFException("short original419 packet");
                    result[offset++] = (byte) one;
                } else offset += read;
            }
            consumed += count;
            return result;
        }
        byte[] copy(byte[] original) throws IOException {
            reserve(original.length);
            return original.clone();
        }
        int u32() throws IOException {
            byte[] value = bytes(4);
            return (value[0] & 0xff) | ((value[1] & 0xff) << 8)
                    | ((value[2] & 0xff) << 16) | ((value[3] & 0xff) << 24);
        }
        long u64() throws IOException { return word(bytes(8), 0); }
        void requireEof() throws IOException {
            reserve(1);
            if (input.read() != -1) throw new IOException("extra bytes after original419 rows");
        }
    }

    private static long word(byte[] bytes, int offset) {
        long result = 0;
        for (int i = 0; i < 8; i++) result |= (bytes[offset + i] & 0xffL) << (8 * i);
        return result;
    }
    private static void putWord(byte[] bytes, int offset, long value) {
        for (int i = 0; i < 8; i++) bytes[offset + i] = (byte) (value >>> (8 * i));
    }

    private static final class Memory implements RangeOrder410Api.Memory {
        private final Geometry geometry;
        private final int cpuValue;
        private final byte[] data;
        Memory(Geometry geometry, int cpuValue, byte[] replay) {
            this.geometry = geometry; this.cpuValue = cpuValue; this.data = replay;
            if (replay.length != DATA_BYTES) throw new IllegalArgumentException("complete replay RAM required");
        }
        @Override public int read8(long address) {
            return data[geometry.data.offset(address, 1)] & 0xff;
        }
        @Override public int read32(long address) {
            if (address != geometry.cpu.base) throw new IllegalArgumentException("only original CPU DWORD read32 is supported");
            return cpuValue;
        }
        @Override public Bits128 read128(long address) {
            if (geometry.data.contains(address, 16)) {
                int offset = geometry.data.offset(address, 16);
                return new Bits128(word(data, offset), word(data, offset + 8));
            }
            if (address == geometry.sse.base) return new Bits128(word(SSE_MASK, 0), word(SSE_MASK, 8));
            throw new IllegalArgumentException("unsupported complete read128");
        }
        @Override public Bits256 read256(long address) {
            byte[] source;
            int offset;
            if (geometry.data.contains(address, 32)) {
                source = data; offset = geometry.data.offset(address, 32);
            } else if (address == geometry.avx.base) {
                source = AVX_MASK; offset = 0;
            } else throw new IllegalArgumentException("unsupported complete read256");
            long a = word(source, offset), b = word(source, offset + 8);
            long c = word(source, offset + 16), d = word(source, offset + 24);
            return new Bits256(new Bits128(a, b), new Bits128(c, d));
        }
        @Override public void write8(long address, int value) {
            data[geometry.data.offset(address, 1)] = (byte) (value & 0xff);
        }
        @Override public void write128(long address, Bits128 value) {
            int offset = geometry.data.offset(address, 16);
            long low = value.low(), high = value.high();
            putWord(data, offset, low); putWord(data, offset + 8, high);
        }
        @Override public void write256(long address, Bits256 value) {
            int offset = geometry.data.offset(address, 32);
            Bits128 low = value.low128(), high = value.high128();
            long a = low.low(), b = low.high(), c = high.low(), d = high.high();
            putWord(data, offset, a); putWord(data, offset + 8, b);
            putWord(data, offset + 16, c); putWord(data, offset + 24, d);
        }
    }

    private static final class Budget implements RangeOrder410Api.LoopBudget {
        private final Region data;
        private int steps;
        Budget(Region data) { this.data = data; }
        @Override public void beforeStep(int headerRva, long frontPointer) {
            if (headerRva != 0x0422091C && headerRva != 0x0422097C && headerRva != 0x042209A7)
                throw new IllegalArgumentException("unknown original loop header");
            if (steps >= 128) throw new IllegalArgumentException("original419 loop budget exceeded");
            steps++;
            data.offset(frontPointer, 1);
        }
    }
}
