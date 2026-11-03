package org.xar.ck3.research.m3.callee68fcfp268;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Three finite public-DATA protocol witnesses for the original 168-byte 42568FC body.
 * Oracle 10c1c93116314ab7e2c809630cc4735ef647f8ba1d3cd0d7ae1c254c7b717b69
 * was frozen before this author read any new268 API entity or implementation.
 * Old246/current267 original sources were visible. This final source is candidate-visible.
 * All low/high RAM bytes and opaque offers are artificial DATA, not Native RAM or a child
 * algorithm. No binder, hardware exception, RFLAGS, upper YMM, loaded or Game claim.
 * Expected values and traces are frozen literals, never generated from executed SUT output.
 */
public final class Callee68fcProtocol268Manual {
    private Callee68fcProtocol268Manual() { }

    private static final int NORMAL = 0;
    private static final int NULL_RCX = 1;
    private static final int STOPPED = 2;
    private static final long IMAGE = 0x0000000140000000L;
    private static final long ENTRY_SP = 0x0000000000014808L;
    private static final String INITIAL_RAM_SHA256 = "e884670b3abdc9556d7f7e651b2304fb74cb2cd88663165db3692660a98ec05b";
    private static final String NORMAL_RAM_SHA256 = "db18c7a9a23b3a79edd5a85a12e77ab3724fc32c4c5018256e6def121b63e612";
    private static final String STOPPED_RAM_SHA256 = "a794c9e889d83d8396b00f896920e7b14df9f5d2a5db107a915a517ae874a561";

    private static final VolatileBits ENTRY_V = new VolatileBits(
            0xA123456789ABCDEFL, 0x0000000000011000L, 0xB23456789ABCDEF0L,
            0xC3456789ABCDEF01L, 0xD456789ABCDEF012L, 0xE56789ABCDEF0123L, 0xF6789ABCDEF01234L,
            new Bits128(0x1111000000000000L, 0xEEEE000000000000L), new Bits128(0x1212010101010101L, 0xEEEF000100010001L), new Bits128(0x1313020202020202L, 0xEEF0000200020002L),
            new Bits128(0x1414030303030303L, 0xEEF1000300030003L), new Bits128(0x1515040404040404L, 0xEEF2000400040004L), new Bits128(0x1616050505050505L, 0xEEF3000500050005L));
    private static final VolatileBits NULL_ENTRY_V = new VolatileBits(
            0xA123456789ABCDEFL, 0x0000000000000000L, 0xB23456789ABCDEF0L,
            0xC3456789ABCDEF01L, 0xD456789ABCDEF012L, 0xE56789ABCDEF0123L, 0xF6789ABCDEF01234L,
            new Bits128(0x1111000000000000L, 0xEEEE000000000000L), new Bits128(0x1212010101010101L, 0xEEEF000100010001L), new Bits128(0x1313020202020202L, 0xEEF0000200020002L),
            new Bits128(0x1414030303030303L, 0xEEF1000300030003L), new Bits128(0x1515040404040404L, 0xEEF2000400040004L), new Bits128(0x1616050505050505L, 0xEEF3000500050005L));
    private static final NonvolatileBits ENTRY_N = new NonvolatileBits(
            0x8123456789ABCDEFL, 0x923456789ABCDEF0L, 0xA3456789ABCDEF01L, 0xB456789ABCDEF012L,
            0xC56789ABCDEF0123L, 0xD6789ABCDEF01234L, 0xE789ABCDEF012345L, 0xF89ABCDEF0123456L,
            new Bits128(0x9765432101234567L, 0xA876543210123456L));
    private static final VolatileBits CALL_V = new VolatileBits(
            0x00000000000110F8L, 0x0000000000013300L, 0x0000000146500008L,
            0x0000000000000000L, 0x00000000FFFFFFFFL, 0xE56789ABCDEF0123L, 0xF6789ABCDEF01234L,
            new Bits128(0x1111000000000000L, 0xEEEE000000000000L), new Bits128(0x1212010101010101L, 0xEEEF000100010001L), new Bits128(0x1313020202020202L, 0xEEF0000200020002L),
            new Bits128(0x1414030303030303L, 0xEEF1000300030003L), new Bits128(0x1515040404040404L, 0xEEF2000400040004L), new Bits128(0x1616050505050505L, 0xEEF3000500050005L));
    private static final VolatileBits POST_V = new VolatileBits(
            0x76543210FEDCBA98L, 0x6543210FEDCBA987L, 0x543210FEDCBA9876L,
            0x43210FEDCBA98765L, 0x3210FEDCBA987654L, 0x210FEDCBA9876543L, 0x10FEDCBA98765432L,
            new Bits128(0xABC0000000000000L, 0x1230000000000000L), new Bits128(0xABC1010101010101L, 0x1232020202020202L), new Bits128(0xABC2020202020202L, 0x1234040404040404L),
            new Bits128(0xABC3030303030303L, 0x1236060606060606L), new Bits128(0xABC4040404040404L, 0x1238080808080808L), new Bits128(0xABC5050505050505L, 0x123A0A0A0A0A0A0AL));
    private static final VolatileBits STOPPED_V = new VolatileBits(
            0x8182838485868788L, 0x9192939495969798L, 0x543210FEDCBA9876L,
            0x43210FEDCBA98765L, 0xA1A2A3A4A5A6A7A8L, 0x210FEDCBA9876543L, 0x10FEDCBA98765432L,
            new Bits128(0xABC0000000000000L, 0x1230000000000000L), new Bits128(0xABC1010101010101L, 0x1232020202020202L), new Bits128(0xABC2020202020202L, 0x1234040404040404L),
            new Bits128(0xABC3030303030303L, 0x1236060606060606L), new Bits128(0xABC4040404040404L, 0x1238080808080808L), new Bits128(0xABC5050505050505L, 0x123A0A0A0A0A0A0AL));

    private static final List<String> NORMAL_EVENTS = List.of(
        "X32 0000000000011010 FFFFFFFF 00000000 FFFFFFFF",
        "R64 00000000000110E0 00000000000110F0",
        "X32 00000000000110F0 FFFFFFFF 00013201 00013200",
        "R64 00000000000110F0 0000000000013200",
        "X32 0000000000013200 FFFFFFFF 00000000 FFFFFFFF",
        "R64 00000000000110E8 0000000000000000",
        "R64 0000000000011100 0000000146500000",
        "X32 0000000146500000 FFFFFFFF 80000000 7FFFFFFF",
        "R64 0000000000011028 000000014542F498",
        "R64 0000000000011020 0000000000000000",
        "R64 0000000000011048 0000000000000055",
        "R64 0000000000011058 0000000000000000",
        "R64 0000000000011040 0000000000000001",
        "R64 0000000000011050 0000000000000000",
        "R64 0000000000011068 0000000000000066",
        "R64 0000000000011078 0000000000011088",
        "X32 0000000000011088 FFFFFFFF 4542F499 4542F498",
        "R64 0000000000011060 0000000000000001",
        "R64 0000000000011070 0000000000011120",
        "X32 0000000000011120 FFFFFFFF 00013302 00013301",
        "R64 0000000000011088 000000014542F498",
        "R64 0000000000011080 0000000000000000",
        "R64 00000000000110A8 0000000000000077",
        "R64 00000000000110B8 0000000146500000",
        "X32 0000000146500000 FFFFFFFF 7FFFFFFF 7FFFFFFE",
        "R64 00000000000110A0 0000000000000001",
        "R64 00000000000110B0 0000000000013200",
        "X32 0000000000013200 FFFFFFFF FFFFFFFF FFFFFFFE",
        "R64 00000000000110C8 0000000000000088",
        "R64 00000000000110D8 0000000000011120",
        "X32 0000000000011120 FFFFFFFF 00013301 00013300",
        "R64 00000000000110C0 0000000000000001",
        "R64 00000000000110D0 0000000146500008",
        "X32 0000000146500008 FFFFFFFF 00000001 00000000",
        "R64 0000000000011120 0000000000013300",
        "W64 00000000000147D8 000000014425699F",
        "W64 0000000000014808 0246813579ABCDE0",
        "R64 0000000000014808 0246813579ABCDE0"
    );
    private static final List<String> NULL_EVENTS = List.of(
        "R64 0000000000014808 ABCDEF1020304050"
    );
    private static final List<String> PREFIX_EVENTS = List.of(
        "X32 0000000000011010 FFFFFFFF 00000000 FFFFFFFF",
        "R64 00000000000110E0 00000000000110F0",
        "X32 00000000000110F0 FFFFFFFF 00013201 00013200",
        "R64 00000000000110F0 0000000000013200",
        "X32 0000000000013200 FFFFFFFF 00000000 FFFFFFFF",
        "R64 00000000000110E8 0000000000000000",
        "R64 0000000000011100 0000000146500000",
        "X32 0000000146500000 FFFFFFFF 80000000 7FFFFFFF",
        "R64 0000000000011028 000000014542F498",
        "R64 0000000000011020 0000000000000000",
        "R64 0000000000011048 0000000000000055",
        "R64 0000000000011058 0000000000000000",
        "R64 0000000000011040 0000000000000001",
        "R64 0000000000011050 0000000000000000",
        "R64 0000000000011068 0000000000000066",
        "R64 0000000000011078 0000000000011088",
        "X32 0000000000011088 FFFFFFFF 4542F499 4542F498",
        "R64 0000000000011060 0000000000000001",
        "R64 0000000000011070 0000000000011120",
        "X32 0000000000011120 FFFFFFFF 00013302 00013301",
        "R64 0000000000011088 000000014542F498",
        "R64 0000000000011080 0000000000000000",
        "R64 00000000000110A8 0000000000000077",
        "R64 00000000000110B8 0000000146500000",
        "X32 0000000146500000 FFFFFFFF 7FFFFFFF 7FFFFFFE",
        "R64 00000000000110A0 0000000000000001",
        "R64 00000000000110B0 0000000000013200",
        "X32 0000000000013200 FFFFFFFF FFFFFFFF FFFFFFFE",
        "R64 00000000000110C8 0000000000000088",
        "R64 00000000000110D8 0000000000011120",
        "X32 0000000000011120 FFFFFFFF 00013301 00013300",
        "R64 00000000000110C0 0000000000000001",
        "R64 00000000000110D0 0000000146500008",
        "X32 0000000146500008 FFFFFFFF 00000001 00000000",
        "R64 0000000000011120 0000000000013300",
        "W64 00000000000147D8 000000014425699F"
    );

    public static void main(String[] args) {
        runCase(NORMAL);
        runCase(NULL_RCX);
        runCase(STOPPED);
        System.out.print("Callee68fcProtocol268Manual: 3 finite cases completed\n");
    }

    private static void runCase(int caseId) {
        Fixture f = new Fixture(caseId);
        Checks.equal(INITIAL_RAM_SHA256, f.ram.serializedSha256(), "initial entire RAM");
        Checks.equal(List.of(), f.ram.traceSnapshot(), "initialization is not a port event");

        QueueFp604Api.Outcome actual =
            Callee68fcFullState268.execute(f.input, f.ram, f.calls);

        if (caseId == STOPPED) {
            Checks.same(f.stoppedOffer, actual, "Stopped outcome identity");
            Checks.equal(PREFIX_EVENTS, f.ram.traceSnapshot(), "Stopped exact prefix");
            Checks.equal(STOPPED_RAM_SHA256, f.ram.serializedSha256(), "Stopped entire RAM");
        } else {
            if (!(actual instanceof QueueFp604Api.Normal normal)) {
                throw new AssertionError("Expected Normal for finite case " + caseId);
            }
            GovernmentCrtBoundary185Api.NormalReturn result = normal.base().normalReturn();
            Checks.equal(caseId == NULL_RCX ? NULL_ENTRY_V : POST_V,
                result.volatileBits(), "complete post V/XMM0..5");
            Checks.equal(ENTRY_N, result.nonvolatileBits(), "complete post N/XMM6");
            Checks.equal(caseId == NULL_RCX ? 0xABCDEF1020304050L : 0x0246813579ABCDE0L,
                result.returnRipBits(), "fresh outer RET");
            Checks.equal(0x0000000000014810L, result.callerRspBits(), "outer caller SP");
            Checks.equal(false, normal.base().postDirectionFlagSet(), "explicit post DF");
            Checks.same(caseId == NULL_RCX ? f.preFp : f.postFp,
                normal.postMxcsr(), "partial FP object identity");
            Checks.equal(caseId == NULL_RCX ? NULL_EVENTS : NORMAL_EVENTS,
                f.ram.traceSnapshot(), "exact memory events");
            Checks.equal(caseId == NULL_RCX ? INITIAL_RAM_SHA256 : NORMAL_RAM_SHA256,
                f.ram.serializedSha256(), "complete post RAM");
        }
        Checks.equal(caseId == NULL_RCX ? 0 : 1, f.callCount, "opaque call count");
        Checks.equal(caseId == NULL_RCX ? 0 : 10, f.ram.atomicCallCount(),
            "one atomic port event for each LOCK ADD");
        Checks.equal(0, f.budgetCalls, "fixed six-row body has no budget invocation");
    }

    private static final class Fixture {
        private final int caseId;
        private final Ram ram = new Ram();
        private final QueueFp604Api.Mxcsr preFp;
        private final QueueFp604Api.Mxcsr postFp = new QueueFp604Api.Mxcsr(0x2001, 0xE1C5);
        private final QueueFp604Api.Mxcsr stoppedFp = new QueueFp604Api.Mxcsr(0x0100, 0x0101);
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final QueueFp604Api.Input input;
        private final Callee68fcFp268Api.Calls calls;
        private final GovernmentCrtBoundary185Api.Call expectedCall;
        private final GovernmentCrtBoundary185Api.Entry expectedChild;
        private final QueueFp604Api.Normal normalOffer;
        private final QueueFp604Api.Stopped stoppedOffer;
        private int callCount;
        private int budgetCalls;

        private Fixture(int caseId) {
            if (caseId < NORMAL || caseId > STOPPED) throw new AssertionError("Unknown finite case");
            this.caseId = caseId;
            preFp = caseId == NORMAL ? new QueueFp604Api.Mxcsr(0x1040, 0x31C1)
                : caseId == NULL_RCX ? new QueueFp604Api.Mxcsr(0x0040, 0x01C5)
                : new QueueFp604Api.Mxcsr(0x0004, 0x0905);
            budget = (header, address) -> {
                budgetCalls++;
                throw new AssertionError("No budget step belongs to these fixed six rows");
            };
            GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                IMAGE, ENTRY_SP, caseId == NULL_RCX ? NULL_ENTRY_V : ENTRY_V, ENTRY_N);
            input = new QueueFp604Api.Input(
                new FullCopy437Api.Input(entry, caseId == NORMAL, budget), preFp);

            expectedCall = new GovernmentCrtBoundary185Api.Call(
                0x425699AL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x42568D4L,
                0x00000000000147E0L, CALL_V, ENTRY_N);
            expectedChild = new GovernmentCrtBoundary185Api.Entry(
                IMAGE, 0x00000000000147D8L, CALL_V, ENTRY_N);
            normalOffer = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(
                    POST_V, 0x000000014425699FL, 0x00000000000147E0L, ENTRY_N),
                false), postFp);
            stoppedOffer = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(
                    IMAGE, 0x00000000000147D8L, STOPPED_V, ENTRY_N),
                    0x42568D4L, true, stoppedFp),
                0, 0x425699AL);
            calls = this::offer;
        }

        private QueueFp604Api.Outcome offer(Callee68fcFp268Api.CallFrame frame) {
            callCount++;
            if (caseId == NULL_RCX || callCount != 1) {
                throw new AssertionError("Unexpected opaque invocation");
            }
            Checks.equal(expectedCall, frame.original(), "entire call site/kind/target/SP/V/N");
            Checks.equal(expectedChild, frame.childEntry(), "entire child image/SP/V/N");
            Checks.equal(caseId == NORMAL, frame.directionFlagSet(), "actual call DF");
            Checks.same(preFp, frame.preMxcsr(), "actual call partial FP identity");
            Checks.equal(0x000000014425699FL, frame.returnRipBits(), "owned CALL return RIP");
            Checks.equal(PREFIX_EVENTS, ram.traceSnapshot(), "exact before-offer memory prefix");
            Checks.equal(STOPPED_RAM_SHA256, ram.serializedSha256(), "entire before-offer RAM");
            Checks.equal(10, ram.atomicCallCount(), "before-offer atomic count");

            // These immutable public-DATA outcomes do not simulate 42568D4.
            if (caseId == STOPPED) return stoppedOffer;
            ram.writeQword(0x0000000000014808L, 0x0246813579ABCDE0L);
            return normalOffer;
        }
    }

    /** Finite sparse byte RAM. High bytes are artificial DATA; no Native content is held. */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long LOW_BASE = 0x0000000000010000L;
        private static final int LOW_LENGTH = 0x5000;
        private static final long HIGH_BASE = 0x0000000146500000L;
        private static final int HIGH_LENGTH = 32;
        private final byte[] bytes = new byte[LOW_LENGTH + HIGH_LENGTH];
        private final ArrayList<String> events = new ArrayList<>();
        private int atomicCalls;

        private Ram() {
            for (int i = 0; i < LOW_LENGTH; i++) bytes[i] = (byte) (i * 29 + 0x37);
            for (int i = 0; i < HIGH_LENGTH; i++) bytes[LOW_LENGTH + i] = (byte) (i * 13 + 0xA7);
            // Exact frozen 34-patch DATA recipe. These initialization writes are not port events.
            put64(0x0000000000014808L, 0xABCDEF1020304050L);
            put32(0x0000000000011010L, 0x00000000);
            put64(0x00000000000110E0L, 0x00000000000110F0L);
            put64(0x00000000000110F0L, 0x0000000000013201L);
            put64(0x00000000000110E8L, 0x0000000000000000L);
            put64(0x0000000000011100L, 0x0000000146500000L);
            put32(0x0000000000013200L, 0x00000000);
            put32(0x0000000146500000L, 0x80000000);
            put32(0x0000000146500008L, 0x00000001);
            put64(0x0000000000011120L, 0x0000000000013302L);
            put64(0x0000000000011020L, 0x0000000000000000L);
            put64(0x0000000000011028L, 0x000000014542F498L);
            put64(0x0000000000011030L, 0xDEAD000000000030L);
            put64(0x0000000000011038L, 0xDEAD000000000038L);
            put64(0x0000000000011040L, 0x0000000000000001L);
            put64(0x0000000000011048L, 0x0000000000000055L);
            put64(0x0000000000011050L, 0x0000000000000000L);
            put64(0x0000000000011058L, 0x0000000000000000L);
            put64(0x0000000000011060L, 0x0000000000000001L);
            put64(0x0000000000011068L, 0x0000000000000066L);
            put64(0x0000000000011070L, 0x0000000000011120L);
            put64(0x0000000000011078L, 0x0000000000011088L);
            put64(0x0000000000011080L, 0x0000000000000000L);
            put64(0x0000000000011088L, 0x000000014542F499L);
            put64(0x0000000000011090L, 0xDEAD000000000090L);
            put64(0x0000000000011098L, 0xDEAD000000000098L);
            put64(0x00000000000110A0L, 0x0000000000000001L);
            put64(0x00000000000110A8L, 0x0000000000000077L);
            put64(0x00000000000110B0L, 0x0000000000013200L);
            put64(0x00000000000110B8L, 0x0000000146500000L);
            put64(0x00000000000110C0L, 0x0000000000000001L);
            put64(0x00000000000110C8L, 0x0000000000000088L);
            put64(0x00000000000110D0L, 0x0000000146500008L);
            put64(0x00000000000110D8L, 0x0000000000011120L);
        }

        private int index(long address, int width) {
            if (width <= 0 || width > 32) throw new AssertionError("Invalid port width");
            long offset = address - LOW_BASE;
            if (Long.compareUnsigned(address, LOW_BASE) >= 0
                    && Long.compareUnsigned(offset, LOW_LENGTH - width) <= 0) {
                return (int) offset;
            }
            offset = address - HIGH_BASE;
            if (Long.compareUnsigned(address, HIGH_BASE) >= 0
                    && Long.compareUnsigned(offset, HIGH_LENGTH - width) <= 0) {
                return LOW_LENGTH + (int) offset;
            }
            throw new AssertionError("Unmapped artificial DATA address " + hex64(address));
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
                throw new AssertionError(label + ": expected=" + expected + ", actual=" + actual);
            }
        }
        private static void same(Object expected, Object actual, String label) {
            if (expected != actual) throw new AssertionError(label + ": identity mismatch");
        }
    }
}
