package org.xar.ck3.research.m3.lookup221;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;

/** Independent finite supplied-storage witness; no native execution. */
public final class ModuleLookupValidation221 {
    private ModuleLookupValidation221() { }
    private static int groups;
    private static int events;
    private static int memoryEvents;
    private static int portEvents;
    private static int opaqueWrites;
    private static int finalCells;
    private static int sourceInvocations;

    private record Step(String kind, long address, long[] args, long value, Runnable after) { }

    private static final class Fixture implements TerminalAbort220Api.Memory, ModuleLookup221Api.Ports {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Step> expected = new ArrayList<>();
        private int cursor;

        void seed8(long a, int value) { bytes.put(a, (byte) value); }
        void seed64(long a, long value) { put(a, value, 8); }
        private void put(long a, long value, int width) {
            for (int i = 0; i < width; i++) bytes.put(a + i, (byte) (value >>> (8 * i)));
        }
        private long raw(long a, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(a + i);
                if (b == null) throw new AssertionError("Unseeded byte " + Long.toHexString(a + i));
                value |= Byte.toUnsignedLong(b) << (8 * i);
            }
            return value;
        }
        private void want(String kind, long a, long value, Runnable after, long... args) {
            expected.add(new Step(kind, a, args.clone(), value, after));
        }
        void wantR64(long a, long v) { want("R64", a, v, null); }
        void wantW64(long a, long v) { want("W64", a, v, null); }
        void wantOpaque64(long a, long v) { want("OPAQUE64", a, v, null); }
        void want458(long site, long code, long rcx, long rdx, long r8, int eax, Runnable after) {
            want("P458", site, eax, after, code, rcx, rdx, r8);
        }
        void want680(long site, long code, long rcx, long rdx, long rax, Runnable after) {
            want("P680", site, rax, after, code, rcx, rdx);
        }
        void wantBba8(long site, long code, int ecx, long rax, Runnable after) {
            want("PBBA8", site, 0, after, code, ecx, rax);
        }
        void want7c0(long site, long code, long rcx, Runnable after) {
            want("P7C0", site, 0, after, code, rcx);
        }
        private Step take(String kind, long a, long... args) {
            if (cursor >= expected.size()) throw new AssertionError("Extra " + kind);
            Step s = expected.get(cursor++);
            if (!s.kind().equals(kind) || s.address() != a || !Arrays.equals(s.args(), args))
                throw new AssertionError("Trace " + (cursor - 1) + ": expected " + s.kind() + " got " + kind);
            events++;
            if (kind.startsWith("P")) portEvents++;
            else if (kind.equals("OPAQUE64")) opaqueWrites++;
            else memoryEvents++;
            return s;
        }
        void opaqueWrite64(long a, long value) {
            Step s = take("OPAQUE64", a);
            if (s.value() != value) throw new AssertionError("Opaque value");
            put(a, value, 8);
        }
        private long read(String kind, long a, int width) {
            Step s = take(kind, a);
            long value = raw(a, width);
            if (s.value() != value) throw new AssertionError("Read value " + kind);
            return value;
        }
        private void write(String kind, long a, long value, int width) {
            Step s = take(kind, a);
            long mask = width == 8 ? -1L : (1L << (8 * width)) - 1;
            if ((s.value() & mask) != (value & mask)) throw new AssertionError("Write value " + kind);
            put(a, value, width);
        }
        private void identity(ModuleLookup221Api.Memory memory) {
            if (memory != this) throw new AssertionError("Port memory identity");
        }
        private void after(Step s) { if (s.after() != null) s.after().run(); }
        @Override public long readPointer(long a) { return read("R64", a, 8); }
        @Override public int readInt32(long a) { return (int) read("R32", a, 4); }
        @Override public int readUnsigned8(long a) { return (int) read("R8", a, 1); }
        @Override public int readUnsigned16(long a) { return (int) read("R16", a, 2); }
        @Override public void writeInt32(long a, int value) { write("W32", a, value, 4); }
        @Override public void writeInt64(long a, long value) { write("W64", a, value, 8); }
        @Override public void write8(long a, int value) { write("W8", a, value, 1); }
        @Override public int call43da458(ModuleLookup221Api.Memory memory, long site, long code, long rcx, long rdx, long r8) {
            identity(memory); Step s = take("P458", site, code, rcx, rdx, r8); after(s); return (int) s.value();
        }
        @Override public long call43da680(ModuleLookup221Api.Memory memory, long site, long code, long rcx, long rdx) {
            identity(memory); Step s = take("P680", site, code, rcx, rdx); after(s); return s.value();
        }
        @Override public void call43dbba8(ModuleLookup221Api.Memory memory, long site, long code, int ecx, long rax) {
            identity(memory); Step s = take("PBBA8", site, code, ecx, rax); after(s);
        }
        @Override public void call43da7c0(ModuleLookup221Api.Memory memory, long site, long code, long rcx) {
            identity(memory); Step s = take("P7C0", site, code, rcx); after(s);
        }
        void check64(long a, long value) {
            if (raw(a, 8) != value) throw new AssertionError("Final QWORD");
            finalCells++;
        }
        void check8(long a, int value) {
            if (raw(a, 1) != (value & 255)) throw new AssertionError("Final byte");
            finalCells++;
        }
        void finish() {
            if (cursor != expected.size()) throw new AssertionError("Unconsumed " + (expected.size() - cursor));
        }
    }

    private static void invoke(Fixture f, long base, int ecx, long entry) {
        sourceInvocations++;
        new ModuleLookup42422D0().execute(f, f,
                new ModuleLookup221Api.Input(base, ecx, new ModuleLookup221Api.Scratch(entry)));
    }

    private static void zeroFirstEaxSkipsLookupAndCleanup() {
        Fixture f = new Fixture();
        long base = 0x140000000L;
        long entry = 0x71000000L;
        long slot = entry + 0x10L;
        long code = 0xFFFF800043DA4580L;
        f.seed64(slot, 0xFEDCBA9876543210L);
        f.seed64(slot - 8, 0xA5A5A5A5A5A5A5A5L);
        f.seed64(slot + 8, 0x5A5A5A5A5A5A5A5AL);
        f.seed64(base + 0x43DA458L, code);
        f.wantR64(slot, 0xFEDCBA9876543210L);
        f.wantW64(slot, 0);
        f.wantR64(base + 0x43DA458L, code);
        f.want458(0x42422ECL, code, 0, base + 0x4423EB8L, slot, 0, null);
        f.wantR64(slot, 0);
        invoke(f, base, 0x80000001, entry);
        f.finish();
        f.check64(slot, 0);
        f.check64(slot - 8, 0xA5A5A5A5A5A5A5A5L);
        f.check64(slot + 8, 0x5A5A5A5A5A5A5A5AL);
        groups++;
    }

    private static void nullLookupWithClearedCleanupSlot() {
        Fixture f = new Fixture();
        long base = 0x160000000L;
        long entry = 0x72000000L;
        long slot = entry + 0x10L;
        long firstCode = 0xF100000043DA4580L;
        long lookupCode = 0xE200000043DA6800L;
        long pointer = 0xBEEF000078123400L;
        f.seed64(slot, 0x8000000000000001L);
        f.seed64(slot - 8, 0x3C3C3C3C3C3C3C3CL);
        f.seed64(slot + 8, 0xC3C3C3C3C3C3C3C3L);
        f.seed64(base + 0x43DA458L, firstCode);
        f.seed64(base + 0x43DA680L, lookupCode);
        f.wantR64(slot, 0x8000000000000001L);
        f.wantW64(slot, 0);
        f.wantR64(base + 0x43DA458L, firstCode);
        f.want458(0x42422ECL, firstCode, 0, base + 0x4423EB8L, slot, 1,
                () -> f.opaqueWrite64(slot, pointer));
        f.wantOpaque64(slot, pointer);
        f.wantR64(slot, pointer);
        f.wantR64(base + 0x43DA680L, lookupCode);
        f.want680(0x4242302L, lookupCode, pointer, base + 0x4423ED0L, 0,
                () -> f.opaqueWrite64(slot, 0));
        f.wantOpaque64(slot, 0);
        f.wantR64(slot, 0);
        invoke(f, base, 0x76543210, entry);
        f.finish();
        f.check64(slot, 0);
        f.check64(slot - 8, 0x3C3C3C3C3C3C3C3CL);
        f.check64(slot + 8, 0xC3C3C3C3C3C3C3C3L);
        groups++;
    }

    private static void suppliedTailEntryBindingGuardsAndLegacy() {
        Fixture captured = new Fixture();
        Fixture foreign = new Fixture();
        long base = 0x180000000L;
        long outerEntry = 0x73000000L;
        long suppliedChildEntry = outerEntry - 0x60L;
        int ecx = 0x81234567;
        int[] calls = { 0 };
        ModuleLookup221Api algorithm = new ModuleLookup221Api() {
            @Override public void execute(ModuleLookup221Api.Memory memory,
                    ModuleLookup221Api.Ports ports, ModuleLookup221Api.Input input) {
                calls[0]++;
                if (memory != captured || ports != captured || input.moduleBase() != base
                        || input.entryECX() != ecx || input.scratch().entryRsp() != suppliedChildEntry)
                    throw new AssertionError("Binding input tuple");
            }
        };
        int[] oldCalls = { 0 };
        int[] siblingCalls = { 0 };
        TerminalTailTarget217Api.Ports fallback = new TerminalTailTarget217Api.Ports() {
            @Override public long call43da620(TerminalTailTarget217Api.Memory m, long site, long code, int value) {
                throw new AssertionError("Unexpected fallback IAT");
            }
            @Override public void call42422d0(TerminalTailTarget217Api.Memory m, long site, int value) {
                oldCalls[0]++;
                if (m != foreign || site != 0x111L || value != -33)
                    throw new AssertionError("Legacy tuple");
            }
            @Override public void call42422d0(TerminalTailTarget217Api.Memory m, long site, int value, long entry) {
                throw new AssertionError("Active edge fell back");
            }
            @Override public long call42420c0(TerminalTailTarget217Api.Memory m, long site, long rcx, long rdx, long r8, long r9) {
                throw new AssertionError("Unexpected fallback helper");
            }
            @Override public void call4242284(TerminalTailTarget217Api.Memory m, long site, int value) {
                throw new AssertionError("Unexpected old abort");
            }
            @Override public void call4242284(TerminalTailTarget217Api.Memory m, long site, int value, long entry) {
                siblingCalls[0]++;
                if (m != foreign || site != 0x222L || value != -44 || entry != 0xFEDCBA9876543210L)
                    throw new AssertionError("Sibling tuple");
            }
        };
        TerminalTailTarget217Api.Ports bound = ModuleLookupFromTailBinding221.bind(
                captured, base, algorithm, captured, fallback);
        bound.call42422d0(captured, 0x424222AL, ecx, suppliedChildEntry);
        if (calls[0] != 1) throw new AssertionError("Active invocation count");
        expectIae(() -> bound.call42422d0(foreign, 0x424222AL, ecx, suppliedChildEntry));
        expectIae(() -> bound.call42422d0(captured, 0x424222BL, ecx, suppliedChildEntry));
        if (calls[0] != 1) throw new AssertionError("Guard called algorithm");
        bound.call42422d0(foreign, 0x111L, -33);
        bound.call4242284(foreign, 0x222L, -44, 0xFEDCBA9876543210L);
        if (oldCalls[0] != 1 || siblingCalls[0] != 1)
            throw new AssertionError("Fallback invocation count");
        captured.finish();
        foreign.finish();
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
        zeroFirstEaxSkipsLookupAndCleanup();
        nullLookupWithClearedCleanupSlot();
        nonNullLookupMutatesCleanup();
        suppliedTailEntryBindingGuardsAndLegacy();
        if (groups != 4 || sourceInvocations != 3) throw new AssertionError("Group/invocation count");
        System.out.println("groups=" + groups + " events=" + events + " memory=" + memoryEvents
                + " ports=" + portEvents + " opaqueWrites=" + opaqueWrites
                + " finalCells=" + finalCells + " sourceInvocations=" + sourceInvocations);
    }


private static void nonNullLookupMutatesCleanup() {
    groups++;
    long base = 0x10000000L;
    long entry = 0x20000000L;
    long slot = entry + 0x10L;
    int ecx = 0x12345678;

    // IAT Data Addresses (base + RVA)
    long addr458 = base + 0x43DA458L;
    long addr680 = base + 0x43DA680L;
    long addrBBA8 = base + 0x43DBBA8L;
    long addr7C0 = base + 0x43DA7C0L;

    // Stored Code Targets (Values at IAT addresses)
    long code458 = 0x43DA458L;
    long code680 = 0x43DA680L;
    long codeBBA8 = 0x43DBBA8L;
    long code7C0 = 0x43DA7C0L;

    // Pointers and Values
    long oldSlotVal = 0x1111111111111111L;
    long ptr1 = 0x2222222222222222L;
    long ptr2 = 0x3333333333333333L;
    long rax2 = 0x4444444400000000L; // High32 nonzero, Low32 zero
    long rdx1 = base + 0x4423EB8L;
    long rdx2 = base + 0x4423ED0L;

    Fixture f = new Fixture();

    // Seed backing store
    f.seed64(slot, oldSlotVal);
    f.seed8(slot - 1, 0xAA); // Canary 1
    f.seed8(slot + 8, 0xBB); // Canary 2
    f.seed64(slot - 8, 0xAAAAAAAAAAAAAAAAL);
    f.seed64(slot + 8, 0xBBBBBBBBBBBBBBBBL);
    f.seed64(addr458, code458);
    f.seed64(addr680, code680);
    f.seed64(addrBBA8, codeBBA8);
    f.seed64(addr7C0, code7C0);

    // 1. Initial AND: Read old slot, Write 0
    f.wantR64(slot, oldSlotVal);
    f.wantW64(slot, 0L);

    // 2. First IAT call (43DA458)
    f.wantR64(addr458, code458);
    Runnable after458 = () -> f.opaqueWrite64(slot, ptr1);
    f.want458(0x42422ECL, code458, 0L, rdx1, slot, -1, after458);
    f.wantOpaque64(slot, ptr1);

    // 3. Second IAT call (43DA680)
    f.wantR64(slot, ptr1);
    f.wantR64(addr680, code680);
    Runnable after680 = () -> f.opaqueWrite64(addrBBA8, codeBBA8 + 1L);
    f.want680(0x4242302L, code680, ptr1, rdx2, rax2, after680);
    f.wantOpaque64(addrBBA8, codeBBA8 + 1L);

    // 4. Third IAT call (43DBBA8)
    f.wantR64(addrBBA8, codeBBA8 + 1L);
    Runnable afterBBA8 = () -> f.opaqueWrite64(slot, ptr2);
    f.wantBba8(0x424230FL, codeBBA8 + 1L, ecx, rax2, afterBBA8);
    f.wantOpaque64(slot, ptr2);

    // 5. Final cleanup read and call (43DA7C0)
    f.wantR64(slot, ptr2);
    f.wantR64(addr7C0, code7C0);
    f.want7c0(0x424231FL, code7C0, ptr2, null);

    invoke(f, base, ecx, entry);

    // Assertions
    f.check64(slot, ptr2);
    f.check8(slot - 1, 0xAA);
    f.check8(slot + 8, 0xBB);
    f.check64(addrBBA8, codeBBA8 + 1L);
    f.check64(slot - 8, 0xAAAAAAAAAAAAAAAAL);
    f.check64(slot + 8, 0xBBBBBBBBBBBBBBBBL);
    f.finish();
}
}
