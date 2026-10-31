package org.xar.ck3.control.g2.m2.nativecode;

import java.io.DataInputStream;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

/** Replays controlled INPUT effects; expected AL and complete after RAM come only from original native records. */
public final class PendingPageReserveNativeConsumer216 {
    private static final long MAX_BYTES = 64L * 1024 * 1024;
    private static final int PAGE = 0x172000;
    private static final int GUARD = 32;
    private static final int[] BODY_LENGTHS = {72, 8, 8, PAGE, PAGE, 8};
    private PendingPageReserveNativeConsumer216() { }
    private static final class Bounded extends FilterInputStream {
        private long consumed;
        private Bounded(InputStream input) { super(input); }
        private void account(int count) throws IOException {
            if (count > 0) { consumed += count; require(consumed <= MAX_BYTES, "raw oracle exceeds 64MiB"); }
        }
        @Override public int read() throws IOException { int value = in.read(); account(value < 0 ? 0 : 1); return value; }
        @Override public int read(byte[] bytes, int start, int length) throws IOException {
            int count = in.read(bytes, start, length); account(count); return count;
        }
    }
    private static final class Region {
        private final int role;
        private final long rawBase;
        private final byte[] before, actualAfter, replay;
        private Region(int role, long rawBase, byte[] before, byte[] actualAfter) {
            this.role = role; this.rawBase = rawBase; this.before = before;
            this.actualAfter = actualAfter; this.replay = before.clone();
        }
        private int guard() { return role == 5 ? 0 : GUARD; }
        private long body() { return rawBase + guard(); }
    }
    private record Log(int kind, long a, long b, long c, long d) { }
    private record Configuration(int id, long moduleBase, long table, int requested, long home,
            int actualAL, long reserveTarget, int reserveWritesCount, int reserveCount,
            long allocatorReturn, long stackSeed) { }
    public static int verify(InputStream input) throws IOException {
        DataInputStream data = new DataInputStream(new Bounded(input));
        byte[] magic = new byte[8]; data.readFully(magic);
        require(Arrays.equals(magic, "M2PG0216".getBytes(StandardCharsets.US_ASCII)), "oracle magic");
        require(u32(data) == 1, "oracle version"); require(u32(data) == 6, "six oracle cases required");
        try {
            for (int id = 0; id < 6; id++) verifyCase(data, id);
        } catch (UncheckedIOException failure) { throw failure.getCause(); }
        require(data.read() == -1, "trailing oracle bytes");
        return 6;
    }
    private static void verifyCase(DataInputStream data, int expectedId) throws IOException {
        int id = u32(data); require(id == expectedId, "ordered unique case id");
        Configuration c = new Configuration(id, u64(data), u64(data), u32(data), u64(data), u32(data),
                u64(data), u32(data), u32(data), u64(data), u64(data));
        require(c.actualAL() == 0 || c.actualAL() == 1, "case " + id + " invalid AL");
        require(u32(data) == 6, "six regions required");
        Region[] regions = new Region[6];
        for (int role = 0; role < 6; role++) {
            require(u32(data) == role, "ordered unique region role"); long base = u64(data); int length = u32(data);
            int expected = BODY_LENGTHS[role] + (role == 5 ? 0 : 2 * GUARD);
            require(length == expected, "case " + id + " role " + role + " length");
            require(Long.compareUnsigned(base + length, base) > 0, "region wraps unsigned address space");
            byte[] before = new byte[length]; data.readFully(before);
            byte[] after = new byte[length]; data.readFully(after);
            regions[role] = new Region(role, base, before, after);
        }
        for (int i = 0; i < regions.length; i++) for (int j = i + 1; j < regions.length; j++) {
            Region a = regions[i], b = regions[j];
            require(Long.compareUnsigned(a.rawBase + a.before.length, b.rawBase) <= 0
                    || Long.compareUnsigned(b.rawBase + b.before.length, a.rawBase) <= 0, "overlapping owned regions");
        }
        qualifyInputs(c, regions);
        int logCount = u32(data); require(logCount >= 0 && logCount <= 64, "bounded log count");
        Log[] logs = new Log[logCount];
        for (int i = 0; i < logs.length; i++) {
            logs[i] = new Log(u32(data), u64(data), u64(data), u64(data), u64(data));
            require(logs[i].kind() >= 0 && logs[i].kind() <= 4, "known log kind");
        }
        Memory memory = new Memory(c, regions); Calls calls = new Calls(c, memory, logs);
        boolean result = PendingPageReserve2A321F0.ensure(memory, calls,
                new PendingPageReserve2A321F0.Input(c.table(), c.requested(), c.moduleBase(), c.home()));
        require((result ? 1 : 0) == c.actualAL(), "case " + id + " AL differs from original native");
        require(calls.cursor == logs.length, "case " + id + " missing native callbacks");
        for (Region region : regions) {
            int mismatch = Arrays.mismatch(region.replay, region.actualAfter);
            require(mismatch < 0, "case " + id + " role " + region.role + " native RAM differs at offset " + mismatch);
        }
    }
    /** Checks protocol INPUT preparation, never computes expected native after effects. */
    private static void qualifyInputs(Configuration c, Region[] regions) throws IOException {
        require(c.table() == regions[0].body() && c.home() == regions[5].rawBase, "metadata/body/home binding");
        require(c.requested() == switch (c.id()) { case 1 -> 0x80000000; case 2 -> 1024; default -> 1; }, "fixed requested input");
        require(c.reserveTarget() == (c.id() == 4 ? c.home() : regions[2].body()), "fixed reserve target");
        require(c.reserveWritesCount() == (c.id() >= 4 ? 1 : 0)
                && c.reserveCount() == (c.id() >= 4 ? 1 : 0), "fixed reserve count effect");
        require(c.allocatorReturn() == regions[3].body(), "fixed allocator pointer");
        require(c.stackSeed() == (c.id() == 4 ? regions[4].body() : 0), "fixed stack seed");
        for (Region region : regions) {
            byte[] expected = new byte[region.before.length]; Arrays.fill(expected, (byte) 0xCC);
            if (region.role != 5) {
                Arrays.fill(expected, 0, GUARD, (byte) 0xA5);
                Arrays.fill(expected, expected.length - GUARD, expected.length, (byte) 0xA5);
            }
            switch (region.role) {
                case 0 -> {
                    store(expected, GUARD, 8, regions[1].body());
                    store(expected, GUARD + 0xC, 4, c.id() == 2 ? 1 : 0);
                    expected[GUARD + 0x40] = (byte) (c.id() == 0 ? 1 : 0);
                }
                case 1 -> store(expected, GUARD, 8, c.id() == 2 ? regions[4].body() : 0);
                case 2 -> { if (c.id() == 5) store(expected, GUARD, 8, regions[4].body()); }
                case 5 -> store(expected, 0, 8, c.stackSeed());
                default -> { }
            }
            require(Arrays.equals(expected, region.before), "case " + c.id() + " role " + region.role + " controlled before INPUT differs");
            if (region.role != 5) for (int i = 0; i < GUARD; i++) {
                require((region.actualAfter[i] & 255) == 0xA5
                        && (region.actualAfter[region.actualAfter.length - 1 - i] & 255) == 0xA5,
                        "original native guard modified");
            }
        }
    }
    private static void store(byte[] bytes, int offset, int width, long value) {
        for (int i = 0; i < width; i++) bytes[offset + i] = (byte) (value >>> (i * 8));
    }
    private static final class Memory implements PendingPageReserve2A321F0.Memory {
        private final Configuration configuration;
        private final Region[] regions;
        private Memory(Configuration c, Region[] regions) { this.configuration = c; this.regions = regions; }
        private Region region(long address, int width) {
            for (Region r : regions) if (width <= r.replay.length
                    && Long.compareUnsigned(address - r.rawBase, Integer.toUnsignedLong(r.replay.length - width)) <= 0) return r;
            throw mismatch("unmapped width" + width + " address 0x" + Long.toUnsignedString(address, 16));
        }
        private long load(long address, int width) {
            Region r = region(address, width); int offset = (int) (address - r.rawBase); long value = 0;
            for (int i = 0; i < width; i++) value |= (r.replay[offset + i] & 255L) << (8 * i);
            return value;
        }
        @Override public int read8(long address) { return (int) load(address, 1); }
        @Override public int read32(long address) { return (int) load(address, 4); }
        @Override public long read64(long address) { return load(address, 8); }
        @Override public void write32(long address, int value) { write(address, 4, value); }
        @Override public void write64(long address, long value) { write(address, 8, value); }
        private void write(long address, int width, long value) {
            Region r = region(address, width); store(r.replay, (int) (address - r.rawBase), width, value);
        }
        private void fill(long address, long length, int value) {
            for (Region r : regions) {
                int bodyLength = BODY_LENGTHS[r.role];
                if (Long.compareUnsigned(length, Integer.toUnsignedLong(bodyLength)) <= 0
                        && Long.compareUnsigned(address - r.body(), Integer.toUnsignedLong(bodyLength) - length) <= 0) {
                    int offset = (int) (address - r.rawBase);
                    Arrays.fill(r.replay, offset, offset + (int) length, (byte) value); return;
                }
            }
            throw mismatch("controlled set outside owned body/HOME");
        }
        private UncheckedIOException mismatch(String message) {
            return new UncheckedIOException(new IOException("case " + configuration.id() + ": " + message));
        }
    }
    private static final class Calls implements PendingPageReserve2A321F0.Calls {
        private final Configuration c;
        private final Memory memory;
        private final Log[] logs;
        private int cursor;
        private Calls(Configuration c, Memory memory, Log[] logs) { this.c = c; this.memory = memory; this.logs = logs; }
        private void same(PendingPageReserve2A321F0.Memory actual) {
            if (actual != memory) throw memory.mismatch("port received a different Memory");
        }
        private void check(int kind, long a, long b, long cArg, long d) {
            if (cursor >= logs.length) throw memory.mismatch("unexpected callback " + cursor);
            if (!logs[cursor].equals(new Log(kind, a, b, cArg, d))) throw memory.mismatch("callback kind/known args differ at " + cursor);
            cursor++;
        }
        @Override public void call3F7AA40(PendingPageReserve2A321F0.Memory actual, long rcx, int edx, long fifth) {
            same(actual); check(0, rcx, Integer.toUnsignedLong(edx), fifth, 0);
            if (rcx != c.moduleBase() + 0x45B64C8L || edx != c.requested() || fifth != c.moduleBase() + 0x5D1DAD9L)
                throw memory.mismatch("logger known source arguments");
        }
        @Override public void call2A32620(PendingPageReserve2A321F0.Memory actual, long rcx, int edx) {
            same(actual); check(1, rcx, Integer.toUnsignedLong(edx), 0, 0);
            if (rcx != c.table()) throw memory.mismatch("reserve receiver differs from configured table");
            memory.write64(c.table(), c.reserveTarget());
            if (c.reserveWritesCount() == 1) memory.write32(c.table() + 0xC, c.reserveCount());
        }
        @Override public void call4226F10(PendingPageReserve2A321F0.Memory actual, long rcx, int edx, long bytes) {
            same(actual); check(2, rcx, Integer.toUnsignedLong(edx), bytes, 0); memory.fill(rcx, bytes, edx);
        }
        @Override public void call4223F44(PendingPageReserve2A321F0.Memory actual, long rcx, int edx) {
            same(actual); check(3, rcx, Integer.toUnsignedLong(edx), 0, 0);
            if (edx != PAGE || rcx != memory.regions[3].body() && rcx != memory.regions[4].body())
                throw memory.mismatch("free must quarantine an exact owned page body with actual size");
        }
        @Override public long call4223B94(PendingPageReserve2A321F0.Memory actual, int ecx) {
            same(actual); check(4, Integer.toUnsignedLong(ecx), 0, 0, c.allocatorReturn());
            if (ecx != PAGE) throw memory.mismatch("allocation size"); return c.allocatorReturn();
        }
    }
    private static int u32(DataInputStream data) throws IOException { return Integer.reverseBytes(data.readInt()); }
    private static long u64(DataInputStream data) throws IOException { return Long.reverseBytes(data.readLong()); }
    private static void require(boolean accepted, String reason) throws IOException { if (!accepted) throw new IOException(reason); }
    public static void main(String[] args) throws IOException {
        if (args.length != 1) throw new IOException("one raw oracle binary path required");
        try (InputStream input = Files.newInputStream(Path.of(args[0]))) { System.out.println(verify(input)); }
    }
}
