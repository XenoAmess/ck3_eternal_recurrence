package org.xar.ck3.control.g2.m2.nativecode;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

/** Independent owner protocol consumer; actual native AFTER never backs replay memory. */
public final class CopyOriginalRamConsumer381 {
    private CopyOriginalRamConsumer381() { }
    private static final int REGION = 8192;
    private static final long[] LENGTHS = {0, 15, 17, 48, 64, 160, 2049};
    private static final long[] DESTINATIONS = {4096, 65, 65, 72, 4096, 4096, 4096};
    private static final int[] TABLES = {
        0x422688e,0x4226974,0x42268c8,0x42268ff,0x422697a,0x422695f,0x4226950,0x42268d0,
        0x422696d,0x4226935,0x4226926,0x42268b0,0x4226943,0x4226910,0x42268e8,0x4226890,
        0x4226b56,0x4226b4f,0x4226b41,0x4226b33,0x4226b25,0x4226b11,0x4226afd,0x4226ae9,0x4226ad5,
        0x4226c86,0x4226c7f,0x4226c71,0x4226c63,0x4226c55,0x4226c41,0x4226c2d,0x4226c19,0x4226c05,
        0x4226de2,0x4226ddb,0x4226dcd,0x4226dbf,0x4226db1,0x4226da3,0x4226d95,0x4226d87,0x4226d79
    };
    public static int verify(InputStream input) throws IOException {
        Reader reader = new Reader(input);
        byte[] magic = {0x4d,0x32,0x43,0x50,0x33,0x38,0x31,0};
        require(Arrays.equals(reader.bytes(8), magic), "magic");
        require(reader.u32() == 1 && reader.u32() == 7, "version/count");
        for (int row = 0; row < 7; row++) {
            int scene = reader.u32(), cpu = reader.u32(), flag = reader.u32(), size = reader.u32();
            require(scene == row && cpu == 0 && flag == (row == 6 ? 2 : 0) && size == REGION, "recipe profile");
            long module = reader.u64(), base = reader.u64(), destination = reader.u64(), source = reader.u64();
            long length = reader.u64(), nativeReturn = reader.u64();
            require(module != 0 && base != 0 && source != 0 && destination != 0, "null address");
            require(source == base + 64 && destination == base + DESTINATIONS[row] && length == LENGTHS[row], "recipe addresses");
            require(nativeReturn == destination, "native RAX");
            require(reader.u32() == 1 && reader.u32() == 0, "original bytes/reserved");
            byte[] before = reader.bytes(REGION), actualAfter = reader.bytes(REGION);
            for (int index = 0; index < REGION; index++) {
                require((before[index] & 255) == ((index * 37 + row * 13 + 0x5a) & 255), "BEFORE formula");
            }
            Memory memory = new Memory(before.clone(), base, module, cpu, flag);
            long replayReturn;
            try {
                replayReturn = PendingMemoryCopy4226860.copy(memory, destination, source, length, module);
            } catch (RuntimeException error) {
                throw new IOException("replay scene " + row, error);
            }
            require(replayReturn == nativeReturn && replayReturn == destination, "replay RAX");
            if (!Arrays.equals(memory.data, actualAfter)) {
                throw new IOException("RAM scene " + row + " first different byte " + Arrays.mismatch(memory.data, actualAfter));
            }
        }
        reader.end();
        return 7;
    }
    private static void require(boolean condition, String detail) throws IOException {
        if (!condition) throw new IOException(detail);
    }
    private static final class Reader {
        private static final long LIMIT = 64L * 1024 * 1024;
        private final InputStream input;
        private long count;
        Reader(InputStream input) { this.input = java.util.Objects.requireNonNull(input); }
        byte[] bytes(int size) throws IOException {
            require(size >= 0 && size <= LIMIT - count, "input cap before allocation");
            byte[] result = new byte[size];
            int position = 0;
            while (position < size) {
                int length = input.read(result, position, size - position);
                if (length < 0) throw new IOException("truncated input");
                if (length == 0) {
                    int value = input.read();
                    if (value < 0) throw new IOException("truncated input");
                    result[position++] = (byte) value;
                    count++;
                } else { position += length; count += length; }
                require(count <= LIMIT, "actual input cap");
            }
            return result;
        }
        int u32() throws IOException { return (int) little(bytes(4), 0, 4); }
        long u64() throws IOException { return little(bytes(8), 0, 8); }
        void end() throws IOException {
            int value = input.read();
            if (value >= 0) { count++; require(count <= LIMIT, "EOF cap"); throw new IOException("trailing input"); }
        }
    }
    private static long little(byte[] bytes, int offset, int width) {
        long value = 0;
        for (int index = 0; index < width; index++) value |= (bytes[offset + index] & 255L) << (index * 8);
        return value;
    }
    private static final class Memory implements Copy4226860Api.Memory {
        private final byte[] data;
        private final long base, module;
        private final int cpu, flag;
        Memory(byte[] data, long base, long module, int cpu, int flag) {
            this.data = data; this.base = base; this.module = module; this.cpu = cpu; this.flag = flag;
        }
        private int offset(long address, int width) {
            long relative = address - base;
            if (width < 1 || width > REGION || Long.compareUnsigned(relative, REGION - width) > 0) {
                throw new IllegalStateException("RAM width/address " + width + "/" + Long.toUnsignedString(address, 16));
            }
            return (int) relative;
        }
        private void put(long address, int width, long value) {
            int offset = offset(address, width);
            for (int index = 0; index < width; index++) data[offset + index] = (byte) (value >>> (index * 8));
        }
        @Override public int read8(long address) {
            if (address == module + 0x5c5cbb0L) return flag;
            return data[offset(address, 1)] & 255;
        }
        @Override public int read16(long address) { return (int) little(data, offset(address, 2), 2); }
        @Override public int read32(long address) {
            if (address == module + 0x542f098L) return cpu;
            long slot = address - (module + 0x6090000L);
            if (Long.compareUnsigned(slot, TABLES.length * 4L) < 0 && (slot & 3) == 0) return TABLES[(int) (slot / 4)];
            return (int) little(data, offset(address, 4), 4);
        }
        @Override public long read64(long address) { return little(data, offset(address, 8), 8); }
        @Override public Bits128 read128(long address) {
            int offset = offset(address, 16);
            return new Bits128(little(data, offset, 8), little(data, offset + 8, 8));
        }
        @Override public Bits256 read256(long address) {
            int offset = offset(address, 32);
            return new Bits256(new Bits128(little(data, offset, 8), little(data, offset + 8, 8)),
                    new Bits128(little(data, offset + 16, 8), little(data, offset + 24, 8)));
        }
        @Override public void write8(long address, int value) { put(address, 1, value); }
        @Override public void write16(long address, int value) { put(address, 2, value); }
        @Override public void write32(long address, int value) { put(address, 4, value); }
        @Override public void write64(long address, long value) { put(address, 8, value); }
        @Override public void write128(long address, Bits128 value) {
            int offset = offset(address, 16);
            for (int index = 0; index < 8; index++) {
                data[offset + index] = (byte) (value.low() >>> (index * 8));
                data[offset + 8 + index] = (byte) (value.high() >>> (index * 8));
            }
        }
        @Override public void write256(long address, Bits256 value) {
            offset(address, 32);
            write128(address, value.low128()); write128(address + 16, value.high128());
        }
        @Override public void storeFence() { throw new IllegalStateException("unexpected profile0 storeFence"); }
    }
    public static void main(String[] args) throws IOException {
        if (args.length != 1) throw new IllegalArgumentException("one actual wire path required");
        try (InputStream input = Files.newInputStream(Path.of(args[0]))) { System.out.println("cases=" + verify(input)); }
    }
}
