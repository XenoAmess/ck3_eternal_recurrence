package org.xar.ck3.control.g2.m2.nativecode;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Bits256;

/** Native RAM/RAX differential only; the additional normal-frame checks use owned software inputs. */
public final class FullCopyOriginalRamConsumer455 {
    private FullCopyOriginalRamConsumer455() { }
    private static final int REGION = 8192;
    private static final long SP = 0x8100000000009008L;
    private static final long STACK_START = SP - 16L;
    private static final long STACK_END = SP + 8L;
    private static final long RET = 0xAABBCCDD11223344L;
    private static final long CONTROL_BYTES = 0x60900ACL;
    private static final long[] LENGTHS = {0,15,17,48,64,160,2049};
    private static final long[] DESTINATIONS = {4096,65,65,72,4096,4096,4096};
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
            long dataEnd = checkedEnd(base, REGION, "payload");
            long controlEnd = checkedEnd(module, CONTROL_BYTES, "module controls");
            require(Long.compareUnsigned(STACK_START, STACK_END) < 0, "stack wrap");
            require(!overlaps(base, dataEnd, module, controlEnd), "payload/module overlap");
            require(!overlaps(base, dataEnd, STACK_START, STACK_END), "payload/stack overlap");
            require(!overlaps(module, controlEnd, STACK_START, STACK_END), "module/stack overlap");
            require(Long.compareUnsigned(source - base, REGION - length) <= 0
                    && Long.compareUnsigned(destination - base, REGION - length) <= 0, "payload operation bounds");
            byte[] before = reader.bytes(REGION), actualAfter = reader.bytes(REGION);
            for (int index = 0; index < REGION; index++) {
                require((before[index] & 255) == ((index * 37 + row * 13 + 0x5a) & 255), "BEFORE formula");
            }
            Memory memory = new Memory(before.clone(), base, module, cpu, flag);
            NonvolatileBits offeredN = nonvolatile();
            GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                    module, SP, volatileInput(destination, source, length), offeredN);
            FullCopy437Api.Input ownedInput = new FullCopy437Api.Input(entry, false, new Budget());
            FullCopy437Api.CallResult result;
            try {
                result = FullCopy4226860.execute(ownedInput, memory, new Calls());
            } catch (RuntimeException error) {
                throw new IOException("replay scene " + row, error);
            }
            GovernmentCrtBoundary185Api.NormalReturn normal = result.normalReturn();
            require(normal.volatileBits().raxBits() == nativeReturn && nativeReturn == destination, "replay/native RAX");
            require(normal.returnRipBits() == RET && normal.callerRspBits() == SP + 8, "owned actual RET/SP");
            require(normal.nonvolatileBits().equals(offeredN), "owned normal N");
            require(!result.postDirectionFlagSet(), "owned post DF");
            if (!Arrays.equals(memory.data, actualAfter)) {
                throw new IOException("RAM scene " + row + " first different byte " + Arrays.mismatch(memory.data, actualAfter));
            }
        }
        require(reader.count == 115208L, "wire byte count");
        reader.end();
        return 7;
    }

    private static void require(boolean condition, String detail) throws IOException {
        if (!condition) throw new IOException(detail);
    }
    private static long checkedEnd(long start, long width, String role) throws IOException {
        long end = start + width;
        require(start != 0 && width > 0 && Long.compareUnsigned(end, start) > 0, role + " unsigned wrap");
        return end;
    }
    private static boolean overlaps(long first, long firstEnd, long second, long secondEnd) {
        return Long.compareUnsigned(first, secondEnd) < 0 && Long.compareUnsigned(second, firstEnd) < 0;
    }
    private static Bits128 x(long seed) { return new Bits128(seed, ~seed); }
    private static VolatileBits volatileInput(long destination, long source, long length) {
        return new VolatileBits(0x8877665544332211L, destination, source, length, 0x1009L, 0x100AL, 0x100BL,
                x(0x1010),x(0x1020),x(0x1030),x(0x1040),x(0x1050),x(0x1060));
    }
    private static NonvolatileBits nonvolatile() {
        return new NonvolatileBits(0x2001,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008,x(0x2060));
    }
    private static final class Budget implements GovernmentCrtBoundary185Api.LoopBudget {
        private int count;
        @Override public void beforeStep(long header, long guardAddressBits) {
            if (header != 0x422684BL && header != 0x4226A30L && header != 0x4226B60L
                    && header != 0x4226CF0L && header != 0x4226E47L && header != 0x4226EB0L) {
                throw new UnsupportedOperationException("unexpected loop header " + Long.toUnsignedString(header, 16));
            }
            if (++count > 4096) throw new UnsupportedOperationException("finite replay budget exceeded");
        }
    }
    private static final class Calls implements FullCopy437Api.Calls {
        @Override public FullCopy437Api.CallResult invoke(FullCopy437Api.CallFrame frame) {
            throw new UnsupportedOperationException("unexpected profile0 invoke " + frame);
        }
        @Override public FullCopy437Api.CallResult tail(FullCopy437Api.TailFrame frame) {
            throw new UnsupportedOperationException("unexpected profile0 tail " + frame);
        }
        @Override public long readGsQword58() { throw new UnsupportedOperationException("unexpected profile0 GS"); }
    }

    private static final class Reader {
        private static final long LIMIT = 64L * 1024 * 1024;
        private final InputStream input;
        private long count;
        Reader(InputStream input) { this.input = Objects.requireNonNull(input); }
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

    private record Slice(byte[] bytes, boolean[] valid, int offset) { }
    private static final class Memory implements FullCopy437Api.Memory {
        private final byte[] data;
        private final byte[] stack = new byte[24];
        private final boolean[] valid = new boolean[24];
        private final long base, module;
        private final int cpu, flag;
        Memory(byte[] data, long base, long module, int cpu, int flag) {
            this.data = data; this.base = base; this.module = module; this.cpu = cpu; this.flag = flag;
            for (int index = 0; index < 8; index++) {
                stack[16 + index] = (byte) (RET >>> (index * 8));
                valid[16 + index] = true;
            }
        }
        private Slice span(long address, int width, boolean reading) {
            if (width < 1 || width > 32) throw new IllegalStateException("unsupported width " + width);
            long relative = address - base;
            if (Long.compareUnsigned(relative, REGION - width) <= 0) return new Slice(data, null, (int) relative);
            relative = address - STACK_START;
            if (width <= 24 && Long.compareUnsigned(relative, 24 - width) <= 0) {
                int offset = (int) relative;
                if (reading) for (int index = 0; index < width; index++) {
                    if (!valid[offset + index]) throw new IllegalStateException("uninitialized owned stack read");
                }
                return new Slice(stack, valid, offset);
            }
            throw new IllegalStateException("unmapped width/address " + width + "/" + Long.toUnsignedString(address, 16));
        }
        private long scalar(long address, int width) {
            Slice s = span(address, width, true);
            return little(s.bytes(), s.offset(), width);
        }
        private static void put(Slice s, int local, long value, int width) {
            for (int index = 0; index < width; index++) {
                int offset = s.offset() + local + index;
                s.bytes()[offset] = (byte) (value >>> (index * 8));
                if (s.valid() != null) s.valid()[offset] = true;
            }
        }
        private void scalarWrite(long address, int width, long value) { put(span(address, width, false), 0, value, width); }
        @Override public int readUnsignedByte(long address) {
            if (address == module + 0x5C5CBB0L) return flag;
            return (int) scalar(address, 1);
        }
        @Override public int readUnsignedWord(long address) { return (int) scalar(address, 2); }
        @Override public int readDword(long address) {
            if (address == module + 0x542F098L) return cpu;
            long slot = address - (module + 0x6090000L);
            if (Long.compareUnsigned(slot, TABLES.length * 4L) < 0 && (slot & 3) == 0) return TABLES[(int) (slot / 4)];
            return (int) scalar(address, 4);
        }
        @Override public long readQword(long address) { return scalar(address, 8); }
        @Override public Bits128 read128(long address) {
            Slice s = span(address, 16, true);
            return new Bits128(little(s.bytes(), s.offset(), 8), little(s.bytes(), s.offset() + 8, 8));
        }
        @Override public Bits256 read256(long address) {
            Slice s = span(address, 32, true);
            return new Bits256(new Bits128(little(s.bytes(), s.offset(), 8), little(s.bytes(), s.offset() + 8, 8)),
                    new Bits128(little(s.bytes(), s.offset() + 16, 8), little(s.bytes(), s.offset() + 24, 8)));
        }
        @Override public void writeByte(long address, int value) { scalarWrite(address, 1, value); }
        @Override public void writeWord(long address, int value) { scalarWrite(address, 2, value); }
        @Override public void writeDword(long address, int value) { scalarWrite(address, 4, value); }
        @Override public void writeQword(long address, long value) { scalarWrite(address, 8, value); }
        @Override public void write128(long address, Bits128 value) {
            Slice s = span(address, 16, false);
            put(s, 0, value.lowBits(), 8); put(s, 8, value.highBits(), 8);
        }
        @Override public void write256(long address, Bits256 value) {
            Slice s = span(address, 32, false);
            put(s, 0, value.low().lowBits(), 8); put(s, 8, value.low().highBits(), 8);
            put(s, 16, value.high().lowBits(), 8); put(s, 24, value.high().highBits(), 8);
        }
        @Override public int lockedXaddDword(long address, int addend) { throw new UnsupportedOperationException("profile0 atomic"); }
        @Override public void write128NonTemporal(long address, Bits128 value) { throw new UnsupportedOperationException("profile0 NT128"); }
        @Override public void write256NonTemporal(long address, Bits256 value) { throw new UnsupportedOperationException("profile0 NT256"); }
        @Override public void sfence() { throw new UnsupportedOperationException("profile0 SFENCE"); }
    }
    public static void main(String[] args) throws IOException {
        if (args.length != 1) throw new IllegalArgumentException("one actual wire path required");
        try (InputStream input = Files.newInputStream(Path.of(args[0]))) { System.out.println(verify(input)); }
    }
}
