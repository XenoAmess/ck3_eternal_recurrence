package org.xar.ck3.research.m3.gs223;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api;
import org.xar.ck3.research.m3.abort220.TerminalAbort4242284;

public final class GsFlagValidation223 {
    private GsFlagValidation223() { }
    private static int groups, events, memoryEvents, portEvents, opaqueWrites;
    private static int finalCells, directInvocations, parentInvocations;
    private record Step(String kind, long address, long[] args, long value, Runnable after) { }

    private static final class Fixture implements TerminalAbort220Api.Memory, GsFlag223Api.Ports {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Step> expected = new ArrayList<>();
        private int cursor;
        void seed32(long a, int v) { put(a, v, 4); }
        void seed64(long a, long v) { put(a, v, 8); }
        private void put(long a, long value, int width) {
            for (int i = 0; i < width; i++) bytes.put(a + i, (byte) (value >>> (8 * i)));
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
        private void want(String kind, long a, long value, Runnable after, long... args) {
            expected.add(new Step(kind, a, args.clone(), value, after));
        }
        void wantR64(long a, long v) { want("R64", a, v, null); }
        void wantR32(long a, int v) { want("R32", a, Integer.toUnsignedLong(v), null); }
        void wantW32(long a, int v) { want("W32", a, Integer.toUnsignedLong(v), null); }
        void wantGs(long site, long value, Runnable after) { want("PGS", site, value, after); }
        void wantChild(long site, long rcx, Runnable after) { want("PCHILD", site, 0, after, rcx); }
        void wantOpaque32(long a, int value) { want("E32", a, Integer.toUnsignedLong(value), null); }
        void opaqueWrite32(long a, int value) {
            Step s = take("E32", a);
            if (s.value() != Integer.toUnsignedLong(value)) throw new AssertionError("Opaque DWORD");
            put(a, value, 4);
        }
        private Step take(String kind, long a, long... args) {
            if (cursor >= expected.size()) throw new AssertionError("Extra " + kind);
            Step s = expected.get(cursor++);
            if (!s.kind().equals(kind) || s.address() != a || !Arrays.equals(s.args(), args))
                throw new AssertionError("Trace " + (cursor - 1) + " expected " + s.kind() + " got " + kind);
            events++;
            if (kind.startsWith("P")) portEvents++;
            else if (kind.equals("E32")) opaqueWrites++;
            else memoryEvents++;
            return s;
        }
        private void identity(NativeTaskMemory memory) {
            if (memory != this) throw new AssertionError("Memory identity");
        }
        private void after(Step s) { if (s.after() != null) s.after().run(); }
        private long read(String kind, long a, int width) {
            Step s = take(kind, a); long value = raw(a, width);
            if (value != s.value()) throw new AssertionError("Read " + kind);
            return value;
        }
        private void write(String kind, long a, long value, int width) {
            Step s = take(kind, a);
            long mask = width == 8 ? -1L : (1L << (width * 8)) - 1;
            if ((value & mask) != (s.value() & mask)) throw new AssertionError("Write " + kind);
            put(a, value, width);
        }
        @Override public long readPointer(long a) { return read("R64", a, 8); }
        @Override public int readInt32(long a) { return (int) read("R32", a, 4); }
        @Override public void writeInt32(long a, int v) { write("W32", a, v, 4); }
        @Override public void writeInt64(long a, long v) { write("W64", a, v, 8); }
        @Override public int readUnsigned8(long a) { return (int) read("R8", a, 1); }
        @Override public int readUnsigned16(long a) { return (int) read("R16", a, 2); }
        @Override public void write8(long a, int v) { write("W8", a, v, 1); }
        @Override public long readGs60(NativeTaskMemory memory, long site) {
            identity(memory); Step s = take("PGS", site); after(s); return s.value();
        }
        @Override public void call424e620(NativeTaskMemory memory, long site, long rcx) {
            identity(memory); Step s = take("PCHILD", site, rcx); after(s);
        }
        void check64(long a, long value) {
            if (raw(a, 8) != value) throw new AssertionError("Final QWORD");
            finalCells++;
        }
        void finish() {
            if (cursor != expected.size()) throw new AssertionError("Unconsumed steps " + (expected.size() - cursor));
        }
    }

    private static final class ParentFallback implements TerminalAbort220Api.Ports {
        private final Fixture f;
        ParentFallback(Fixture f) { this.f = f; }
        @Override public int call42591f8(TerminalAbort220Api.Memory m, long site, int ecx) {
            f.identity(m); Step s = f.take("POLD3", site, ecx); f.after(s); return (int) s.value();
        }
        @Override public int call42591f8(TerminalAbort220Api.Memory m, long site, int ecx, long entry) {
            f.identity(m); Step s = f.take("POLD4", site, ecx, entry); f.after(s); return (int) s.value();
        }
        @Override public long readGs60(TerminalAbort220Api.Memory m, long site) {
            f.identity(m); Step s = f.take("PPARENTGS", site); f.after(s); return s.value();
        }
        @Override public long call43da798(TerminalAbort220Api.Memory m, long site, long code, long rax, int edx) {
            f.identity(m); Step s = f.take("P798", site, code, rax, edx); f.after(s); return s.value();
        }
        @Override public void call43da778(TerminalAbort220Api.Memory m, long site, long code, long rcx, int edx) {
            f.identity(m); Step s = f.take("P778", site, code, rcx, edx); f.after(s);
        }
        @Override public void call42422d0(TerminalAbort220Api.Memory m, long site, int ecx, long entry) {
            f.identity(m); Step s = f.take("PLOOKUP", site, ecx, entry); f.after(s);
        }
        @Override public void call43da558(TerminalAbort220Api.Memory m, long site, long code, int ecx) {
            f.identity(m); Step s = f.take("P558", site, code, ecx); f.after(s);
        }
    }

    private static void invoke(Fixture f, long entry, int expected) {
        directInvocations++;
        int actual = GsFlag42591F8.execute(f, f, new GsFlag223Api.Scratch(entry));
        if (actual != expected) throw new AssertionError("EAX " + actual + " expected " + expected);
    }
    private static void signedNegativeStillInitializesLowSlot() {
        Fixture f = new Fixture();
        long entry = 0x51000000L, slot = entry + 8;
        long g = 0xF100000000002000L, p = 0xE200000000003000L;
        f.seed64(slot, 0x11223344DEADBEEFL);
        f.seed64(g + 0x20L, p);
        f.seed32(p + 8, 0x80000000);
        f.wantW32(slot, 0);
        f.wantGs(0x4259204L, g, null);
        f.wantR64(g + 0x20L, p);
        f.wantR32(p + 8, 0x80000000);
        invoke(f, entry, 1);
        f.finish();
        f.check64(slot, 0x1122334400000000L);
        groups++;
    }

    private static void nonnegativeChildWithoutWriteReturnsOne() {
        Fixture f = new Fixture();
        long entry = 0x52000000L, slot = entry + 8;
        long g = 0xD300000000004000L, p = 0xC400000000005000L;
        f.seed64(slot, 0x55667788778899AAL);
        f.seed64(g + 0x20L, p);
        f.seed32(p + 8, 0);
        f.wantW32(slot, 0);
        f.wantGs(0x4259204L, g, null);
        f.wantR64(g + 0x20L, p);
        f.wantR32(p + 8, 0);
        f.wantChild(0x425921BL, slot, null);
        f.wantR32(slot, 0);
        invoke(f, entry, 1);
        f.finish();
        f.check64(slot, 0x5566778800000000L);
        groups++;
    }

    private static void actualParentSuppliesCurrentEntryAndLegacyForwards() {
        Fixture f = new Fixture();
        Fixture foreign = new Fixture();
        ParentFallback fallback = new ParentFallback(f);
        TerminalAbort220Api.Ports bound = GsFlagFromAbortBinding223.bind(f, f, fallback);
        long base = 0x140000000L;
        long entry = 0x53000000L;
        long childEntry = entry - 0x30L;
        long slot = childEntry + 8L;
        int ecx = 0x81234567;
        expectIae(() -> bound.call42591f8(foreign, 0x424228CL, ecx, childEntry));
        expectIae(() -> bound.call42591f8(f, 0x424228DL, ecx, childEntry));
        f.finish();
        foreign.finish();

        f.want("POLD3", 0x777L, Integer.toUnsignedLong(0x80000003), null, -99);
        if (bound.call42591f8(f, 0x777L, -99) != 0x80000003)
            throw new AssertionError("Legacy return");
        long parentGs = 0x9988776655443322L;
        f.want("PPARENTGS", 0x4242296L, parentGs, null);
        if (bound.readGs60(f, 0x4242296L) != parentGs)
            throw new AssertionError("Parent GS forwarding");

        long g = 0xB500000000006000L, p = 0xA600000000007000L;
        long finalCode = 0xFEE1000043DA5580L;
        f.seed64(slot, 0x99AABBCC12345678L);
        f.seed64(g + 0x20L, p);
        f.seed32(p + 8, -1);
        f.seed64(base + 0x43DA558L, finalCode);
        f.wantW32(slot, 0);
        f.wantGs(0x4259204L, g, null);
        f.wantR64(g + 0x20L, p);
        f.wantR32(p + 8, -1);
        f.want("PLOOKUP", 0x42422C0L, 0, null, ecx, childEntry);
        f.wantR64(base + 0x43DA558L, finalCode);
        f.want("P558", 0x42422C7L, 0, null, finalCode, ecx);
        parentInvocations++;
        TerminalAbort220Api.Trap trap = TerminalAbort4242284.execute(f, bound,
                new TerminalAbort220Api.Input(base, ecx, new TerminalAbort220Api.Scratch(entry)));
        if (trap != TerminalAbort220Api.Trap.INT3_42422CD)
            throw new AssertionError("Parent Trap classification");
        f.finish();
        f.check64(slot, 0x99AABBCC00000000L);
        groups++;
    }

    private static void expectIae(Runnable action) {
        try {
            action.run();
        } catch (IllegalArgumentException expected) {
            return;
        }
        throw new AssertionError("Expected IllegalArgumentException");
    }

    public static void main(String[] args) {
        signedNegativeStillInitializesLowSlot();
        nonnegativeChildWithoutWriteReturnsOne();
        callbackChangesLow32PreservesHigh();
        actualParentSuppliesCurrentEntryAndLegacyForwards();
        if (groups != 4 || directInvocations != 3 || parentInvocations != 1)
            throw new AssertionError("Invocation count");
        System.out.println("groups=" + groups + " events=" + events + " memory=" + memoryEvents
                + " ports=" + portEvents + " opaqueWrites=" + opaqueWrites + " finalCells=" + finalCells
                + " direct60=" + directInvocations + " parent74=" + parentInvocations);
    }


private static void callbackChangesLow32PreservesHigh() {
    groups++;
    Fixture f = new Fixture();
    long entry = 0x1000L;
    long slot = entry + 8L;
    int oldLow = 0x12345678;
    int highCanary = 0xCAFEBABE;
    long initialSlotValue = ((long) highCanary << 32) | (long) oldLow;

    f.seed64(slot, initialSlotValue);

    long g = 0x2000L;
    long p = 0x3000L;
    int signedCheck = 0x7fffffff;
    f.seed64(g + 0x20L, p);
    f.seed32(p + 8L, signedCheck);

    f.wantW32(slot, 0);
    f.wantGs(0x4259204L, g, () -> {
        f.opaqueWrite32(slot, 0x11111111);
    });
    f.wantOpaque32(slot, 0x11111111);
    f.wantR64(g + 0x20L, p);
    f.wantR32(p + 8L, signedCheck);
    f.wantChild(0x425921bL, slot, () -> {
        f.opaqueWrite32(slot, 1);
    });
    f.wantOpaque32(slot, 1);
    f.wantR32(slot, 1);

    invoke(f, entry, 0);

    f.check64(slot, ((long) highCanary << 32) | 1L);
    f.finish();
}
}
