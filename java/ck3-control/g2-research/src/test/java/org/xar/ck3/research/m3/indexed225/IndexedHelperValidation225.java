package org.xar.ck3.research.m3.indexed225;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class IndexedHelperValidation225 {
    private IndexedHelperValidation225() { }
    private static int groups, events, memoryEvents, exchangeEvents, portEvents, opaqueWrites, finalCells, invocations;
    private record Step(String kind, long address, long[] args, long result, Runnable after) { }
    private static final class Fixture implements IndexedHelper225Api.Memory, IndexedHelper225Api.Ports {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Step> expected = new ArrayList<>();
        private int cursor;
        void seed32(long a, int v) { put(a, v, 4); }
        void seed64(long a, long v) { put(a, v, 8); }
        private void put(long a, long v, int width) {
            for (int i = 0; i < width; i++) bytes.put(a + i, (byte) (v >>> (i * 8)));
        }
        private long raw(long a, int width) {
            long v = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(a + i);
                if (b == null) throw new AssertionError("Missing byte " + Long.toHexString(a + i));
                v |= Byte.toUnsignedLong(b) << (8 * i);
            }
            return v;
        }
        private void want(String kind, long a, long result, Runnable after, long... args) {
            expected.add(new Step(kind, a, args.clone(), result, after));
        }
        void wantR64(long a, long v) { want("R64", a, v, null); }
        void wantR32(long a, int v) { want("R32", a, Integer.toUnsignedLong(v), null); }
        void wantExchange(long a, long newValue, long observedOld) { want("X64", a, observedOld, null, newValue); }
        void wantOpaque64(long a, long newValue) { want("E64", a, newValue, null); }
        void want478(long site, long code, long rcx, int edx, int r8d, long result, Runnable after) {
            want("P478", site, result, after, code, rcx, edx, r8d);
        }
        void want738(long site, long code, int result, Runnable after) {
            want("P738", site, result, after, code);
        }
        void wantA60(long site, long rcx, long rdx, int r8d, int result, Runnable after) {
            want("PA60", site, result, after, rcx, rdx, r8d);
        }
        void want7c0(long site, long code, long rcx, Runnable after) {
            want("P7C0", site, 0, after, code, rcx);
        }
        void want680(long site, long code, long rcx, long rdx, long result, Runnable after) {
            want("P680", site, result, after, code, rcx, rdx);
        }
        private Step take(String kind, long a, long... args) {
            if (cursor >= expected.size()) throw new AssertionError("Extra " + kind);
            Step s = expected.get(cursor++);
            if (!s.kind().equals(kind) || s.address() != a || !Arrays.equals(s.args(), args))
                throw new AssertionError("Trace " + (cursor - 1) + " expected " + s.kind() + " got " + kind);
            events++;
            if (kind.startsWith("P")) portEvents++;
            else if (kind.equals("E64")) opaqueWrites++;
            else { memoryEvents++; if (kind.equals("X64")) exchangeEvents++; }
            return s;
        }
        void opaqueWrite64(long a, long v) {
            Step s = take("E64", a);
            if (s.result() != v) throw new AssertionError("Opaque value");
            put(a, v, 8);
        }
        private void identity(IndexedHelper225Api.Memory m) {
            if (m != this) throw new AssertionError("Memory identity");
        }
        private void after(Step s) { if (s.after() != null) s.after().run(); }
        private long read(String kind, long a, int width) {
            Step s = take(kind, a); long v = raw(a, width);
            if (s.result() != v) throw new AssertionError("Read " + kind);
            return v;
        }
        private void write(String kind, long a, long v, int width) {
            Step s = take(kind, a);
            long mask = width == 8 ? -1L : (1L << (8 * width)) - 1;
            if ((s.result() & mask) != (v & mask)) throw new AssertionError("Write " + kind);
            put(a, v, width);
        }
        @Override public long readPointer(long a) { return read("R64", a, 8); }
        @Override public int readInt32(long a) { return (int) read("R32", a, 4); }
        @Override public void writeInt32(long a, int v) { write("W32", a, v, 4); }
        @Override public void writeInt64(long a, long v) { write("W64", a, v, 8); }
        @Override public long exchangeInt64(long a, long newValue) {
            Step s = take("X64", a, newValue);
            long old = raw(a, 8);
            if (old != s.result()) throw new AssertionError("Observed exchange old");
            put(a, newValue, 8);
            return old;
        }
        @Override public long call43da478(IndexedHelper225Api.Memory m, long site, long code, long rcx, int edx, int r8d) {
            identity(m); Step s = take("P478", site, code, rcx, edx, r8d); after(s); return s.result();
        }
        @Override public int call43da738(IndexedHelper225Api.Memory m, long site, long code) {
            identity(m); Step s = take("P738", site, code); after(s); return (int) s.result();
        }
        @Override public int call4246a60(IndexedHelper225Api.Memory m, long site, long rcx, long rdx, int r8d) {
            identity(m); Step s = take("PA60", site, rcx, rdx, r8d); after(s); return (int) s.result();
        }
        @Override public void call43da7c0(IndexedHelper225Api.Memory m, long site, long code, long rcx) {
            identity(m); Step s = take("P7C0", site, code, rcx); after(s);
        }
        @Override public long call43da680(IndexedHelper225Api.Memory m, long site, long code, long rcx, long rdx) {
            identity(m); Step s = take("P680", site, code, rcx, rdx); after(s); return s.result();
        }
        void check64(long a, long v) {
            if (raw(a, 8) != v) throw new AssertionError("Final QWORD");
            finalCells++;
        }
        void finish() {
            if (cursor != expected.size()) throw new AssertionError("Unconsumed " + (expected.size() - cursor));
        }
    }
    private static void invoke(Fixture f, long base, int index, long name, long begin, long end, long expected) {
        invocations++;
        long actual = IndexedLookupHelper424E448.execute(f, f, new IndexedHelper225Api.Input(base, index, name, begin, end));
        if (actual != expected) throw new AssertionError("Full RAX " + Long.toHexString(actual));
    }
private static void cachedSentinelAndEmpty() {
    // Scene 1: Valid cached pointer (decoded != -1, != 0)
    // Index -1 selects function-table address = base + 0x5C5D790 + unsignedIndex * 8
    long base1 = 0x10000000L;
    int idx1 = -1;
    long addr1 = base1 + 0x5C5D790L + Integer.toUnsignedLong(idx1) * 8L;
    long cookie1 = 0x123456789ABCDEF0L;
    long encoded1 = 0x0000000000000000L;
    // Decode: ROR64(0 ^ cookie1, 0x30) = ROR64(cookie1, 48)
    // 0x123456789ABCDEF0 rotated right by 48 is 0x56789ABCDEF01234
    long decoded1 = 0x56789ABCDEF01234L;

    Fixture f1 = new Fixture();
    f1.seed64(addr1, encoded1);
    f1.seed64(base1 + 0x542F0B8L, cookie1);
    f1.wantR64(addr1, encoded1);
    f1.wantR64(base1 + 0x542F0B8L, cookie1);
    invoke(f1, base1, idx1, 0L, 0L, 0L, decoded1);
    f1.finish();
    groups++;

    // Scene 2: Sentinel -1 (decoded == -1)
    long base2 = 0x20000000L;
    int idx2 = 0;
    long addr2 = base2 + 0x5C5D790L;
    long cookie2 = 0x0000000000000000L;
    long encoded2 = 0xFFFFFFFFFFFFFFFFL; // ROR64(-1 ^ 0, 0) = -1
    long decoded2 = -1L;

    Fixture f2 = new Fixture();
    f2.seed64(addr2, encoded2);
    f2.seed64(base2 + 0x542F0B8L, cookie2);
    f2.wantR64(addr2, encoded2);
    f2.wantR64(base2 + 0x542F0B8L, cookie2);
    invoke(f2, base2, idx2, 0L, 0L, 0L, 0L);
    f2.finish();
    groups++;

    // Scene 3: Empty list, failure path (decoded == 0, begin == end)
    // Uses initial cookie for failure encoding.
    long base3 = 0x30000000L;
    int idx3 = 1;
    long addr3 = base3 + 0x5C5D790L + 8L;
    long cookie3 = 0x0000000000000001L;
    long encoded3 = 0x0000000000000001L; // ROR64(1 ^ 1, 1) = 0
    long decoded3 = 0L;

    // Failure encode: ROR64(-1, 64 - (cookie3 & 63)) XOR cookie3
    // cookie3 & 63 = 1. Shift = 63.
    // ROR64(-1, 63) = -1 (all 1s rotated is all 1s).
    // -1 XOR 1 = 0xFFFFFFFFFFFFFFFEL
    long failEncoded3 = 0xFFFFFFFFFFFFFFFEL;

    Fixture f3 = new Fixture();
    f3.seed64(addr3, encoded3);
    f3.seed64(base3 + 0x542F0B8L, cookie3);
    f3.wantR64(addr3, encoded3);
    f3.wantR64(base3 + 0x542F0B8L, cookie3);
    // Exchange at function table with failure marker
    f3.wantExchange(addr3, failEncoded3, encoded3);
    invoke(f3, base3, idx3, 0L, 0L, 0L, 0L);
    f3.finish();
    f3.check64(addr3, failEncoded3);
    groups++;
  }

private static void loadExchangeResolveRefreshesCookie() {
    groups++;
    Fixture f = new Fixture();
    long base = 0x10000000L;
    int index = 0x1C;
    long name = 0x4427010L;
    long begin = 0x442700CL;
    long end = 0x4427010L;
    long path = 0x44269D0L;
    long iat478 = 0x43DA478L;
    long iat7C0 = 0x43DA7C0L;
    long iat680 = 0x43DA680L;
    long site478 = 0x424E4EBL;
    long site7C0 = 0x424E574L;
    long site680 = 0x424E5A0L;
    long site5D4 = 0x424E5D4L;
    long site5AB = 0x424E5ABL;
    long funcCacheAddr = base + 0x5C5D790L + Integer.toUnsignedLong(index) * 8L;
    long modCacheAddr = base + 0x5C5D6F0L + Integer.toUnsignedLong(0) * 8L;
    long patTableAddr = base + 0x44269D0L + Integer.toUnsignedLong(0) * 8L;
    long cookieAddr = base + 0x542F0B8L;

    // Initial values
    long initialCookie = 0x542F0B8L;
    long initialEncoded = 0x542F0B8L; // Decodes to 0: ROR64(0x542F0B8 ^ 0x542F0B8, 0x542F0B8 & 63) = 0
    long oldModule = 0x1111111111111111L;
    long newModule = 0x2222222222222222L;
    long foundCookie = 0x542F0B9L;
    long successCookie = 0x542F0BAL;
    long symbol = 0x3333333333333333L;
    // Fixed literal: cookie low6=58, ROR64(symbol,6)=CCCCCCCCCCCCCCCC.
    // XOR with 000000000542F0BA gives CCCCCCCCC98E3C76.
    long encoded = 0xCCCCCCCCC98E3C76L;

    // Seed backing
    f.seed64(funcCacheAddr, initialEncoded);
    f.seed64(modCacheAddr, 0L);
    f.seed64(patTableAddr, path);
    f.seed64(cookieAddr, initialCookie);
    f.seed64(base + iat478, iat478);
    f.seed64(base + iat7C0, iat7C0);
    f.seed64(base + iat680, iat680);
    f.seed32(begin, 0);

    // 1. Initial function table read (decodes to 0)
    f.wantR64(funcCacheAddr, initialEncoded);
    f.wantR64(cookieAddr, initialCookie);

    // 2. Module list loop: read DWORD at begin (index 0)
    f.wantR32(begin, 0);
    f.wantR64(modCacheAddr, 0L);

    // 3. Path table read
    f.wantR64(patTableAddr, path);

    // 4. Fresh IAT read for 478
    f.wantR64(base + iat478, iat478);

    // 5. Call 478@424E4EB (load module)
    f.want478(site478, iat478, path, 0, 0x800, newModule, () -> {
        // Opaque write to module cache BEFORE exchange
        f.opaqueWrite64(modCacheAddr, oldModule);
    });
    f.wantOpaque64(modCacheAddr, oldModule);

    // 6. Exchange module cache (observed old is nonzero due to opaque write)
    f.wantExchange(modCacheAddr, newModule, oldModule);

    // 7. Fresh IAT read for 7C0
    f.wantR64(base + iat7C0, iat7C0);

    // 8. Call 7C0@424E574 (release callback)
    f.want7c0(site7C0, iat7C0, newModule, () -> {
        // Mutate cookie during release
        f.opaqueWrite64(cookieAddr, foundCookie);
    });
    f.wantOpaque64(cookieAddr, foundCookie);

    // 9. Fresh cookie read at 5D4
    f.wantR64(cookieAddr, foundCookie);

    // 10. Fresh IAT read for 680
    f.wantR64(base + iat680, iat680);

    // 11. Call 680@424E5A0 (resolve)
    f.want680(site680, iat680, newModule, name, symbol, () -> {
        // Mutate cookie during resolve
        f.opaqueWrite64(cookieAddr, successCookie);
    });
    f.wantOpaque64(cookieAddr, successCookie);

    // 12. Fresh cookie read at 5AB
    f.wantR64(cookieAddr, successCookie);

    // 13. Encode and exchange function table
    f.wantExchange(funcCacheAddr, encoded, initialEncoded);

    // 14. Final checks
    invoke(f, base, index, name, begin, end, symbol);
    f.check64(modCacheAddr, newModule);
    f.check64(funcCacheAddr, encoded);
    f.check64(cookieAddr, successCookie);
    f.finish();
}

    public static void main(String[] args) {
        cachedSentinelAndEmpty();
        loadExchangeResolveRefreshesCookie();
        if (groups != 4 || invocations != 4) throw new AssertionError("Group/invocation count");
        System.out.println("groups=" + groups + " events=" + events + " memory=" + memoryEvents
                + " exchange=" + exchangeEvents + " ports=" + portEvents + " opaqueWrites=" + opaqueWrites
                + " finalCells=" + finalCells + " invocations=" + invocations);
    }

}
