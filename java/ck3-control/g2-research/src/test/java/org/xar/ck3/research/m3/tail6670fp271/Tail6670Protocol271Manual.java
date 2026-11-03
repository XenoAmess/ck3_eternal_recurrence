package org.xar.ck3.research.m3.tail6670fp271;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.fa90fp267.Fa90Fp267Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Two finite public-DATA protocol witnesses for the original 139-byte 4256670 prefix.
 * Oracle 85069c8d4e9c4e63cba9cb952fc9e772f05003887dccea553b73e6fee0762c66
 * was frozen before the public proposal and all new271 API/implementation reads.
 * Existing249/current267 originals were visible; this final source is candidate-visible.
 * All RAM and lower outcomes are artificial DATA, not Native contents or a272 algorithm.
 * The direct Normal RIP intentionally differs from the prior267 return slot DATA.
 * Only the Stopped case uses actual267 FAE7 binding; no parent267 Normal acceptance claim.
 * No local RET/push, hardware, RFLAGS, upperYMM, RF/UW, loaded or Game proof.
 * The retained98-PC path is a source fact; this public fixture observes ports, not PCs.
 */
public final class Tail6670Protocol271Manual {
    private Tail6670Protocol271Manual() { }

    private static final long IMAGE = 0x0000000170000000L;
    private static final long ENTRY_SP = 0x0000000000036808L;
    private static final String INITIAL_RAM_SHA256 = "c401eabc2ac2f99fd2334e709c1ffafa9ccd4080b698432ddaf07a419455d28d";
    private static final String FINAL_RAM_SHA256 = "24084342da763eff3e19f877ddda748b3b4ab488a3c5e5705725affff96239a3";
    private static final VolatileBits INPUT_V = new VolatileBits(
        0xFFEEDDCCBBAA9988L, 0x0000000000031000L, 0x1020304050607080L, 0xC1D2E3F405162738L, 0xDDAABBCC11223344L, 0x7A6B5C4D3E2F1091L, 0x8B7C6D5E4F3021A2L,
        new Bits128(0x2134000000000000L, 0xBACD000000000000L),
        new Bits128(0x2135020304050607L, 0xBACE112223334445L),
        new Bits128(0x21360406080A0C0EL, 0xBACF22444666888AL),
        new Bits128(0x213706090C0F1215L, 0xBAD033666999CCCFL),
        new Bits128(0x2138080C1014181CL, 0xBAD144888CCD1114L),
        new Bits128(0x21390A0F14191E23L, 0xBAD255AAB0005559L));
    private static final VolatileBits TAIL_V = new VolatileBits(
        0x00000000000310F8L, 0x0000000000033402L, 0x0000000176600008L, 0x0000000000000000L, 0xDDAABBCC11223344L, 0x7A6B5C4D3E2F1091L, 0x8B7C6D5E4F3021A2L,
        new Bits128(0x2134000000000000L, 0xBACD000000000000L),
        new Bits128(0x2135020304050607L, 0xBACE112223334445L),
        new Bits128(0x21360406080A0C0EL, 0xBACF22444666888AL),
        new Bits128(0x213706090C0F1215L, 0xBAD033666999CCCFL),
        new Bits128(0x2138080C1014181CL, 0xBAD144888CCD1114L),
        new Bits128(0x21390A0F14191E23L, 0xBAD255AAB0005559L));
    private static final VolatileBits NORMAL_V = new VolatileBits(
        0x1123581321345589L, 0x223469243245669AL, 0x33457A35435677ABL, 0x44568B46546788BCL, 0x55679C57657899CDL, 0x6678AD687689AADEL, 0x7789BE79879ABBEFL,
        new Bits128(0x3157000000000000L, 0x4268000000000000L),
        new Bits128(0x3158020203030404L, 0x426C050506060707L),
        new Bits128(0x3159040406060808L, 0x42700A0A0C0C0E0EL),
        new Bits128(0x315A060609090C0CL, 0x42740F0F12121515L),
        new Bits128(0x315B08080C0C1010L, 0x4278141418181C1CL),
        new Bits128(0x315C0A0A0F0F1414L, 0x427C19191E1E2323L));
    private static final VolatileBits STOP_V = new VolatileBits(
        0xAABB001122334455L, 0xBBCC112233445566L, 0x33457A35435677ABL, 0x44568B46546788BCL, 0x55679C57657899CDL, 0x6678AD687689AADEL, 0x7789BE79879ABBEFL,
        new Bits128(0x3157000000000000L, 0x4268000000000000L),
        new Bits128(0x3158020203030404L, 0x426C050506060707L),
        new Bits128(0x3159040406060808L, 0x42700A0A0C0C0E0EL),
        new Bits128(0x315A060609090C0CL, 0x42740F0F12121515L),
        new Bits128(0x315B08080C0C1010L, 0x4278141418181C1CL),
        new Bits128(0x315C0A0A0F0F1414L, 0x427C19191E1E2323L));
    private static final NonvolatileBits INPUT_N = new NonvolatileBits(
        0xA011223344556677L, 0xB122334455667788L, 0xC233445566778899L, 0xD3445566778899AAL, 0xE45566778899AABBL, 0xF566778899AABBCCL, 0x86778899AABBCCDDL, 0x978899AABBCCDDEEL,
        new Bits128(0x1029384756ABCDEFL, 0xFFEEDDCCBBAA0099L));
    private static final QueueFp604Api.Mxcsr PRE_NORMAL = new QueueFp604Api.Mxcsr(0x2001, 0x23C5);
    private static final QueueFp604Api.Mxcsr POST_NORMAL = new QueueFp604Api.Mxcsr(0x8001, 0xA085);
    private static final QueueFp604Api.Mxcsr PRE_BOUND = new QueueFp604Api.Mxcsr(0x0041, 0x8145);
    private static final QueueFp604Api.Mxcsr OPAQUE_STOP = new QueueFp604Api.Mxcsr(0x0100, 0x0105);

    // Literal frozen port trace, independently derived from original ASM and artificial DATA.
    private static final List<String> EXPECTED_TRACE = List.of(
        "X32 0000000000031010 00000001 FFFFFFFF 00000000",
        "R64 00000000000310E0 00000000000310F0",
        "X32 00000000000310F0 00000001 000331FF 00033200",
        "R64 00000000000310F0 0000000000033200",
        "X32 0000000000033200 00000001 FFFFFFFF 00000000",
        "R64 00000000000310E8 0000000000000000",
        "R64 0000000000031100 0000000176600000",
        "X32 0000000176600000 00000001 7FFFFFFF 80000000",
        "R64 0000000000031028 000000017542F498",
        "R64 0000000000031020 0000000000000000",
        "R64 0000000000031048 0000000000000055",
        "R64 0000000000031058 0000000000000000",
        "R64 0000000000031040 0000000000000001",
        "R64 0000000000031050 0000000000000000",
        "R64 0000000000031068 0000000000000066",
        "R64 0000000000031078 0000000000031088",
        "X32 0000000000031088 00000001 7542F497 7542F498",
        "R64 0000000000031060 0000000000000001",
        "R64 0000000000031070 0000000000031120",
        "X32 0000000000031120 00000001 00033400 00033401",
        "R64 0000000000031088 000000017542F498",
        "R64 0000000000031080 0000000000000000",
        "R64 00000000000310A8 0000000000000077",
        "R64 00000000000310B8 0000000176600000",
        "X32 0000000176600000 00000001 80000000 80000001",
        "R64 00000000000310A0 0000000000000001",
        "R64 00000000000310B0 0000000000033200",
        "X32 0000000000033200 00000001 00000000 00000001",
        "R64 00000000000310C8 0000000000000088",
        "R64 00000000000310D8 0000000000031120",
        "X32 0000000000031120 00000001 00033401 00033402",
        "R64 00000000000310C0 0000000000000001",
        "R64 00000000000310D0 0000000176600008",
        "X32 0000000176600008 00000001 FFFFFFFF 00000000",
        "R64 0000000000031120 0000000000033402"
    );

    public static void main(String[] args) {
        runCase(false);
        runCase(true);
        System.out.print("Tail6670Protocol271Manual: 2 finite cases completed\n");
    }

    private static void runCase(boolean boundStopped) {
        Fixture fixture = new Fixture(boundStopped);
        Checks.equal(INITIAL_RAM_SHA256, fixture.ram.serializedSha256(), "initial whole RAM");
        Checks.equal(List.of(), fixture.ram.traceSnapshot(), "setup must be unlogged");
        GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
            IMAGE, ENTRY_SP, INPUT_V, INPUT_N);
        GovernmentCrtBoundary185Api.LoopBudget budget = (site, address) -> {
            fixture.budgetCalls++;
            throw new AssertionError("Unexpected public budget callback");
        };
        QueueFp604Api.Outcome actual;
        if (boundStopped) {
            GovernmentCrtBoundary185Api.Call original = new GovernmentCrtBoundary185Api.Call(
                0x424FAE7L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x4256670L, 0x0000000000036810L, INPUT_V, INPUT_N);
            Fa90Fp267Api.CallFrame parentFrame = new Fa90Fp267Api.CallFrame(
                original, entry, true, PRE_BOUND);
            Checks.bits(0x000000017424FAECL, parentFrame.returnRipBits(), "parent owned RIP DATA");
            Fa90Fp267Api.Calls foreign = frame -> {
                fixture.foreignCalls++;
                throw new AssertionError("Selected FAE7 frame reached foreign");
            };
            actual = Tail6670FromFa90271.bind(fixture.ram, budget, fixture, foreign)
                .invoke(parentFrame);
        } else {
            QueueFp604Api.Input input = new QueueFp604Api.Input(
                new FullCopy437Api.Input(entry, false, budget), PRE_NORMAL);
            actual = Tail6670FullState271.execute(input, fixture.ram, fixture);
        }

        Checks.same(fixture.offer, actual, "actual lower Outcome identity");
        Checks.equal(1, fixture.tailCalls, "one opaque tail");
        Checks.equal(0, fixture.foreignCalls, "no foreign invocation");
        Checks.equal(0, fixture.budgetCalls, "no public budget steps");
        Checks.equal(10, fixture.ram.atomicCallCount(), "single XADD for each actual INC");
        Checks.equal(EXPECTED_TRACE, fixture.ram.traceSnapshot(), "exact final memory trace");
        Checks.equal(FINAL_RAM_SHA256, fixture.ram.serializedSha256(), "final whole RAM");
        if (boundStopped) {
            if (!(actual instanceof QueueFp604Api.Stopped stopped)) {
                throw new AssertionError("Expected exact opaque Stopped");
            }
            Checks.equal(QueueFp604Api.StopReason.MISSING_POST_STATE, stopped.reason(), "stop reason");
            Checks.equal(new GovernmentCrtBoundary185Api.Entry(
                IMAGE, ENTRY_SP, STOP_V, INPUT_N), stopped.snapshot().currentState(), "full stopped state");
            Checks.bits(0x4256874L, stopped.snapshot().instructionRva(), "opaque stop instruction DATA");
            Checks.equal(false, stopped.snapshot().directionFlagSet(), "opaque stop DF");
            Checks.same(OPAQUE_STOP, stopped.snapshot().mxcsr(), "opaque stop FP identity");
            Checks.equal(0, stopped.raisedConditionBits(), "opaque condition DATA");
            Checks.bits(0x42566F6L, stopped.originCallSiteRva(), "opaque origin DATA");
        } else {
            if (!(actual instanceof QueueFp604Api.Normal normal)) {
                throw new AssertionError("Expected exact opaque Normal");
            }
            Checks.equal(new GovernmentCrtBoundary185Api.NormalReturn(
                NORMAL_V, 0x1234567890ABCDEFL, 0x0000000000036810L, INPUT_N),
                normal.base().normalReturn(), "complete actual opaque Normal state");
            Checks.equal(true, normal.base().postDirectionFlagSet(), "opaque post DF");
            Checks.same(POST_NORMAL, normal.postMxcsr(), "opaque post FP identity");
        }
    }

    private static final class Fixture implements Tail6670Fp271Api.Calls {
        private final boolean boundStopped;
        private final Ram ram = new Ram();
        private final QueueFp604Api.Outcome offer;
        private int tailCalls;
        private int foreignCalls;
        private int budgetCalls;

        private Fixture(boolean boundStopped) {
            this.boundStopped = boundStopped;
            if (boundStopped) {
                offer = new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                    new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(
                        IMAGE, ENTRY_SP, STOP_V, INPUT_N), 0x4256874L, false, OPAQUE_STOP),
                    0, 0x42566F6L);
            } else {
                offer = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                    new GovernmentCrtBoundary185Api.NormalReturn(
                        NORMAL_V, 0x1234567890ABCDEFL, 0x0000000000036810L, INPUT_N), true),
                    POST_NORMAL);
            }
        }

        @Override public QueueFp604Api.Outcome tail(Tail6670Fp271Api.TailFrame frame) {
            tailCalls++;
            Checks.equal(1, tailCalls, "one tail callback");
            Checks.equal(new GovernmentCrtBoundary185Api.Tail(
                0x42566F6L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4256874L,
                new GovernmentCrtBoundary185Api.Entry(IMAGE, ENTRY_SP, TAIL_V, INPUT_N)),
                frame.original(), "exact full tail V/N/SP and transfer");
            Checks.equal(boundStopped, frame.directionFlagSet(), "unchanged entry DF");
            Checks.same(boundStopped ? PRE_BOUND : PRE_NORMAL, frame.preMxcsr(), "same input partial FP");
            Checks.equal(EXPECTED_TRACE, ram.traceSnapshot(), "exact pre-tail memory trace");
            Checks.equal(10, ram.atomicCallCount(), "pre-tail atomic count");
            Checks.equal(FINAL_RAM_SHA256, ram.serializedSha256(), "pre-tail whole RAM");
            return offer; // Explicit immutable public DATA; no lower algorithm or RAM writes.
        }
    }

    /**
     * Mechanical finite RAM only. Port logging/width handling/hash mechanics reuse this
     * author's268 host; no268 DATA, trace, oracle or expectations are reused.
     * Two artificial regions serialize as low24576 then high16 bytes, without headers.
     */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long LOW_BASE = 0x0000000000031000L;
        private static final int LOW_SIZE = 24576;
        private static final long HIGH_BASE = 0x0000000176600000L;
        private static final int HIGH_SIZE = 16;
        private final byte[] bytes = new byte[LOW_SIZE + HIGH_SIZE];
        private final List<String> events = new ArrayList<>();
        private int atomicCalls;

        private Ram() {
            for (int i = 0; i < LOW_SIZE; i++) bytes[i] = (byte) (i * 7 + 0x5B);
            for (int i = 0; i < HIGH_SIZE; i++) bytes[LOW_SIZE + i] = (byte) (i * 23 + 0x91);
            put64(0x0000000000036808L, 0x000000017424FAECL);
            put32(0x0000000000031010L, 0xFFFFFFFF);
            put64(0x00000000000310E0L, 0x00000000000310F0L);
            put64(0x00000000000310F0L, 0x00000000000331FFL);
            put64(0x00000000000310E8L, 0x0000000000000000L);
            put64(0x0000000000031100L, 0x0000000176600000L);
            put32(0x0000000000033200L, 0xFFFFFFFF);
            put32(0x0000000176600000L, 0x7FFFFFFF);
            put32(0x0000000176600008L, 0xFFFFFFFF);
            put64(0x0000000000031120L, 0x0000000000033400L);
            put64(0x0000000000031020L, 0x0000000000000000L);
            put64(0x0000000000031028L, 0x000000017542F498L);
            put64(0x0000000000031030L, 0xDEAD000000004030L);
            put64(0x0000000000031038L, 0xDEAD000000004038L);
            put64(0x0000000000031040L, 0x0000000000000001L);
            put64(0x0000000000031048L, 0x0000000000000055L);
            put64(0x0000000000031050L, 0x0000000000000000L);
            put64(0x0000000000031058L, 0x0000000000000000L);
            put64(0x0000000000031060L, 0x0000000000000001L);
            put64(0x0000000000031068L, 0x0000000000000066L);
            put64(0x0000000000031070L, 0x0000000000031120L);
            put64(0x0000000000031078L, 0x0000000000031088L);
            put64(0x0000000000031080L, 0x0000000000000000L);
            put64(0x0000000000031088L, 0x000000017542F497L);
            put64(0x0000000000031090L, 0xDEAD000000004090L);
            put64(0x0000000000031098L, 0xDEAD000000004098L);
            put64(0x00000000000310A0L, 0x0000000000000001L);
            put64(0x00000000000310A8L, 0x0000000000000077L);
            put64(0x00000000000310B0L, 0x0000000000033200L);
            put64(0x00000000000310B8L, 0x0000000176600000L);
            put64(0x00000000000310C0L, 0x0000000000000001L);
            put64(0x00000000000310C8L, 0x0000000000000088L);
            put64(0x00000000000310D0L, 0x0000000176600008L);
            put64(0x00000000000310D8L, 0x0000000000031120L);
        }

        private int index(long address, int width) {
            if (width <= 0) throw new AssertionError("Invalid RAM width");
            if (address >= LOW_BASE && address - LOW_BASE <= LOW_SIZE - width) {
                return (int) (address - LOW_BASE);
            }
            if (address >= HIGH_BASE && address - HIGH_BASE <= HIGH_SIZE - width) {
                return LOW_SIZE + (int) (address - HIGH_BASE);
            }
            throw new AssertionError("Unmapped artificial RAM address " + hex64(address) + " width " + width);
        }

        private long rawRead(long address, int width) {
            int start = index(address, width);
            long value = 0;
            for (int i = 0; i < width; i++) value |= (long) (bytes[start + i] & 0xFF) << (i * 8);
            return value;
        }

        private void rawWrite(long address, long value, int width) {
            int start = index(address, width);
            for (int i = 0; i < width; i++) bytes[start + i] = (byte) (value >>> (i * 8));
        }

        private void put32(long address, int value) { rawWrite(address, value, 4); }
        private void put64(long address, long value) { rawWrite(address, value, 8); }

        @Override public long readQword(long address) {
            long value = rawRead(address, 8);
            events.add("R64 " + hex64(address) + " " + hex64(value));
            return value;
        }

        @Override public int readDword(long address) {
            int value = (int) rawRead(address, 4);
            events.add("R32 " + hex64(address) + " " + hex32(value));
            return value;
        }

        @Override public int readUnsignedByte(long address) {
            int value = (int) rawRead(address, 1);
            events.add("R8 " + hex64(address) + " " + hex32(value));
            return value;
        }

        @Override public int readUnsignedWord(long address) {
            int value = (int) rawRead(address, 2);
            events.add("R16 " + hex64(address) + " " + hex32(value));
            return value;
        }

        @Override public void writeQword(long address, long value) {
            rawWrite(address, value, 8);
            events.add("W64 " + hex64(address) + " " + hex64(value));
        }

        @Override public void writeDword(long address, int value) {
            rawWrite(address, value, 4);
            events.add("W32 " + hex64(address) + " " + hex32(value));
        }

        @Override public void writeByte(long address, int value) {
            rawWrite(address, value, 1);
            events.add("W8 " + hex64(address) + " " + hex32(value & 0xFF));
        }

        @Override public void writeWord(long address, int value) {
            rawWrite(address, value, 2);
            events.add("W16 " + hex64(address) + " " + hex32(value & 0xFFFF));
        }

        @Override public synchronized int lockedXaddDword(long address, int delta) {
            int old = (int) rawRead(address, 4);
            int updated = old + delta;
            rawWrite(address, updated, 4);
            atomicCalls++;
            events.add("X32 " + hex64(address) + " " + hex32(delta)
                + " " + hex32(old) + " " + hex32(updated));
            return old;
        }

        private Bits128 raw128(long address) {
            index(address, 16);
            return new Bits128(rawRead(address, 8), rawRead(address + 8, 8));
        }

        private void put128(long address, Bits128 value) {
            index(address, 16);
            rawWrite(address, value.lowBits(), 8);
            rawWrite(address + 8, value.highBits(), 8);
        }

        private static String bits128(Bits128 value) {
            return hex64(value.lowBits()) + " " + hex64(value.highBits());
        }

        @Override public Bits128 read128(long address) {
            Bits128 value = raw128(address);
            events.add("R128 " + hex64(address) + " " + bits128(value));
            return value;
        }

        @Override public void write128(long address, Bits128 value) {
            put128(address, value);
            events.add("W128 " + hex64(address) + " " + bits128(value));
        }

        @Override public void write128NonTemporal(long address, Bits128 value) {
            put128(address, value);
            events.add("W128NT " + hex64(address) + " " + bits128(value));
        }

        @Override public FullCopy437Api.Bits256 read256(long address) {
            index(address, 32);
            FullCopy437Api.Bits256 value =
                new FullCopy437Api.Bits256(raw128(address), raw128(address + 16));
            events.add("R256 " + hex64(address) + " " + bits128(value.low()) + " " + bits128(value.high()));
            return value;
        }

        private void put256(long address, FullCopy437Api.Bits256 value) {
            index(address, 32);
            put128(address, value.low());
            put128(address + 16, value.high());
        }

        @Override public void write256(long address, FullCopy437Api.Bits256 value) {
            put256(address, value);
            events.add("W256 " + hex64(address) + " " + bits128(value.low()) + " " + bits128(value.high()));
        }

        @Override public void write256NonTemporal(long address, FullCopy437Api.Bits256 value) {
            put256(address, value);
            events.add("W256NT " + hex64(address) + " " + bits128(value.low()) + " " + bits128(value.high()));
        }

        @Override public void sfence() {
            events.add("SFENCE"); // Separate host token; no hardware fence proof.
        }

        private int atomicCallCount() { return atomicCalls; }
        private List<String> traceSnapshot() { return List.copyOf(events); }
        private byte[] serializedSnapshot() { return bytes.clone(); }

        private String serializedSha256() {
            try {
                byte[] digest = MessageDigest.getInstance("SHA-256").digest(serializedSnapshot());
                StringBuilder result = new StringBuilder(64);
                for (byte value : digest) result.append(String.format(Locale.ROOT, "%02x", value & 0xFF));
                return result.toString();
            } catch (NoSuchAlgorithmException impossible) {
                throw new AssertionError(impossible);
            }
        }

        private static String hex64(long value) {
            return String.format(Locale.ROOT, "%016X", value);
        }

        private static String hex32(int value) {
            return String.format(Locale.ROOT, "%08X", value);
        }
    }

    private static final class Checks {
        private Checks() { }
        private static void equal(Object expected, Object actual, String label) {
            if (!Objects.equals(expected, actual)) {
                throw new AssertionError(label + ": expected " + expected + ", actual " + actual);
            }
        }
        private static void same(Object expected, Object actual, String label) {
            if (expected != actual) throw new AssertionError(label + ": identity differs");
        }
        private static void bits(long expected, long actual, String label) {
            if (expected != actual) {
                throw new AssertionError(label + ": expected " + Long.toUnsignedString(expected, 16)
                    + ", actual " + Long.toUnsignedString(actual, 16));
            }
        }
    }
}
