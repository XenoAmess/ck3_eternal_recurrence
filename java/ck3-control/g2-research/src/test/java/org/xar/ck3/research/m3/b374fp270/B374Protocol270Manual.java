package org.xar.ck3.research.m3.b374fp270;

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
 * Two finite direct-body witnesses from original374 source PC/RAM/explicitoffer DATA.
 * Oracle157c556867ecea1acae9a97a44f00b42505da24ad092e1ef869a777163f366d7
 * was frozen before actual270 API/whole entity reads. OldB374/current267 originals were
 * visible; this final source is candidate-visible, not whole blind.
 * This is not a267 binding Normal case: artificial opaque writes change saved N slots,
 * whose fresh restored values must reach the tail. Every lower result remains DATA.
 * The source oracle has78/14 local PCs; this manual does not pretend to trace instructions.
 * RawRF/UW/fullPEbuild receipt NOT_HELD. No Native/fullABI/hardware/loaded/Game proof.
 * Only mechanical RAM/port/hash/assertion code is reused from the author's268 host.
 */
public final class B374Protocol270Manual {
    private B374Protocol270Manual() { }

    private static final long IMAGE = 0x0000000160000000L;
    private static final long ENTRY_SP = 0x0000000000027808L;
    private static final String INITIAL_RAM_SHA256 = "7684ae42be64d068d96ef99d3e6f1cc2ba104e506102cca5f164571517bccd1e";
    private static final String NORMAL_RAM_SHA256 = "f618a846c32d1d5b15f1b90c5cd3596bdb51b5554376fa5701dd78632b731fc2";
    private static final String STOPPED_RAM_SHA256 = "b3d11357e9cf83cd2696ac0cfe285b2b62db907ce104a1280eb6425a21ec2ba4";

    private static final VolatileBits ENTRY_V = new VolatileBits(
        0xE0D0C0B0A0908070L, 0x0000000000022000L, 0x1122AABB3344CCDDL,
        0x2233BBCC4455DDEEL, 0x3344CCDD5566EEFFL, 0x4455DDEE6677FF00L, 0x5566EEFF77880011L,
        new Bits128(0x1020000000000000L, 0xA0B0000000000000L), new Bits128(0x1031001100110011L, 0xA0B1000200030004L), new Bits128(0x1042002200220022L, 0xA0B2000400060008L),
        new Bits128(0x1053003300330033L, 0xA0B300060009000CL), new Bits128(0x1064004400440044L, 0xA0B40008000C0010L), new Bits128(0x1075005500550055L, 0xA0B5000A000F0014L));
    private static final NonvolatileBits ENTRY_N = new NonvolatileBits(
        0xA101020304050607L, 0xB202030405060708L, 0xC303040506070809L, 0xD40405060708090AL,
        0xE505060708090A0BL, 0xF6060708090A0B0CL, 0x870708090A0B0C0DL, 0x9808090A0B0C0D0EL,
        new Bits128(0xABCDEF0011223344L, 0x5566778899AABBCCL));
    private static final VolatileBits CALL_V = new VolatileBits(
        0x0000000000000000L, 0x0000000000024000L, 0x1122AABB3344CCDDL,
        0x2233BBCC4455DDEEL, 0x3344CCDD5566EEFFL, 0x4455DDEE6677FF00L, 0x5566EEFF77880011L,
        new Bits128(0x1020000000000000L, 0xA0B0000000000000L), new Bits128(0x1031001100110011L, 0xA0B1000200030004L), new Bits128(0x1042002200220022L, 0xA0B2000400060008L),
        new Bits128(0x1053003300330033L, 0xA0B300060009000CL), new Bits128(0x1064004400440044L, 0xA0B40008000C0010L), new Bits128(0x1075005500550055L, 0xA0B5000A000F0014L));
    private static final NonvolatileBits CALL_N = new NonvolatileBits(
        0x0000000000022000L, 0xB202030405060708L, 0xC303040506070809L, 0xD40405060708090AL,
        0xE505060708090A0BL, 0xF6060708090A0B0CL, 0x870708090A0B0C0DL, 0x9808090A0B0C0D0EL,
        new Bits128(0xABCDEF0011223344L, 0x5566778899AABBCCL));
    private static final VolatileBits POST_CALL_V = new VolatileBits(
        0x0716253443526170L, 0x1827364554637281L, 0x2938475665748392L,
        0x3A495867768594A3L, 0x4B5A69788796A5B4L, 0x5C6B7A8998A7B6C5L, 0x6D7C8B9AA9B8C7D6L,
        new Bits128(0x1234000000000000L, 0x5678000000000000L), new Bits128(0x1235010202030304L, 0x567C05060708090AL), new Bits128(0x1236020404060608L, 0x56800A0C0E101214L),
        new Bits128(0x123703060609090CL, 0x56840F1215181B1EL), new Bits128(0x12380408080C0C10L, 0x568814181C202428L), new Bits128(0x1239050A0A0F0F14L, 0x568C191E23282D32L));
    private static final VolatileBits TAIL_V = new VolatileBits(
        0x000000016542F498L, 0x0000000000022000L, 0x2938475665748392L,
        0x3A495867768594A3L, 0x4B5A69788796A5B4L, 0x5C6B7A8998A7B6C5L, 0x6D7C8B9AA9B8C7D6L,
        new Bits128(0x1234000000000000L, 0x5678000000000000L), new Bits128(0x1235010202030304L, 0x567C05060708090AL), new Bits128(0x1236020404060608L, 0x56800A0C0E101214L),
        new Bits128(0x123703060609090CL, 0x56840F1215181B1EL), new Bits128(0x12380408080C0C10L, 0x568814181C202428L), new Bits128(0x1239050A0A0F0F14L, 0x568C191E23282D32L));
    private static final NonvolatileBits TAIL_N = new NonvolatileBits(
        0x1011121314151617L, 0x2021222324252627L, 0x3031323334353637L, 0x4041424344454647L,
        0xE505060708090A0BL, 0xF6060708090A0B0CL, 0x870708090A0B0C0DL, 0x9808090A0B0C0D0EL,
        new Bits128(0xABCDEF0011223344L, 0x5566778899AABBCCL));
    private static final VolatileBits POST_TAIL_V = new VolatileBits(
        0x8899AABBCCDDEEFFL, 0x7766554433221100L, 0x66554433221100FFL,
        0x554433221100FFEEL, 0x4433221100FFEEDDL, 0x33221100FFEEDDCCL, 0x221100FFEEDDCCBBL,
        new Bits128(0x9ABC000000000000L, 0xDEF0000000000000L), new Bits128(0x9ABD112223334445L, 0xDEF1010101010101L), new Bits128(0x9ABE22444666888AL, 0xDEF2020202020202L),
        new Bits128(0x9ABF33666999CCCFL, 0xDEF3030303030303L), new Bits128(0x9AC044888CCD1114L, 0xDEF4040404040404L), new Bits128(0x9AC155AAB0005559L, 0xDEF5050505050505L));
    private static final VolatileBits STOPPED_V = new VolatileBits(
        0xDEADBEEF00112233L, 0xAABBCCDD44556677L, 0x2938475665748392L,
        0x3A495867768594A3L, 0x4B5A69788796A5B4L, 0x5C6B7A8998A7B6C5L, 0x6D7C8B9AA9B8C7D6L,
        new Bits128(0x1234000000000000L, 0x5678000000000000L), new Bits128(0x1235010202030304L, 0x567C05060708090AL), new Bits128(0x1236020404060608L, 0x56800A0C0E101214L),
        new Bits128(0x123703060609090CL, 0x56840F1215181B1EL), new Bits128(0x12380408080C0C10L, 0x568814181C202428L), new Bits128(0x1239050A0A0F0F14L, 0x568C191E23282D32L));

    private static final GovernmentCrtBoundary185Api.Call EXPECTED_CALL =
        new GovernmentCrtBoundary185Api.Call(
            0x42567F2L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x425689CL,
            0x00000000000277E0L, CALL_V, CALL_N);
    private static final GovernmentCrtBoundary185Api.Entry EXPECTED_CHILD =
        new GovernmentCrtBoundary185Api.Entry(
            IMAGE, 0x00000000000277D8L, CALL_V, CALL_N);
    private static final GovernmentCrtBoundary185Api.Tail EXPECTED_TAIL =
        new GovernmentCrtBoundary185Api.Tail(
            0x425686DL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424E364L,
            new GovernmentCrtBoundary185Api.Entry(IMAGE, ENTRY_SP, TAIL_V, TAIL_N));

    private static final List<String> NORMAL_EVENTS = List.of(
        "W64 0000000000027810 A101020304050607",
        "W64 0000000000027818 B202030405060708",
        "W64 0000000000027820 C303040506070809",
        "W64 0000000000027800 D40405060708090A",
        "R64 00000000000220F8 0000000000000000",
        "R64 0000000000022100 0000000000000000",
        "R64 0000000000022120 0000000000024000",
        "W64 00000000000277D8 00000001642567F7",
        "W64 0000000000027810 1011121314151617",
        "W64 0000000000027818 2021222324252627",
        "W64 0000000000027820 3031323334353637",
        "W64 0000000000027800 4041424344454647",
        "W64 0000000000027808 0F1E2D3C4B5A6978",
        "R64 0000000000022028 000000016542F498",
        "R64 0000000000022020 0000000000000000",
        "R64 0000000000022048 000000016542F498",
        "R64 0000000000022040 0000000000000000",
        "R64 0000000000022068 000000016542F498",
        "R64 0000000000022060 0000000000000000",
        "R64 0000000000022088 000000016542F498",
        "R64 0000000000022080 0000000000000000",
        "R64 00000000000220A8 000000016542F498",
        "R64 00000000000220A0 0000000000000000",
        "R64 00000000000220C8 000000016542F498",
        "R64 00000000000220C0 0000000000000000",
        "R64 0000000000027810 1011121314151617",
        "R64 0000000000027818 2021222324252627",
        "R64 0000000000027820 3031323334353637",
        "R64 0000000000027800 4041424344454647"
    );
    private static final List<String> PREFIX_EVENTS = List.of(
        "W64 0000000000027810 A101020304050607",
        "W64 0000000000027818 B202030405060708",
        "W64 0000000000027820 C303040506070809",
        "W64 0000000000027800 D40405060708090A",
        "R64 00000000000220F8 0000000000000000",
        "R64 0000000000022100 0000000000000000",
        "R64 0000000000022120 0000000000024000",
        "W64 00000000000277D8 00000001642567F7"
    );

    public static void main(String[] args) {
        runCase(false);
        runCase(true);
        System.out.print("B374Protocol270Manual: 2 finite cases completed\n");
    }

    private static void runCase(boolean stoppedAtCall) {
        Fixture f = new Fixture(stoppedAtCall);
        Checks.equal(INITIAL_RAM_SHA256, f.ram.serializedSha256(), "initial entire RAM");
        Checks.equal(List.of(), f.ram.traceSnapshot(), "DATA setup is not a port event");

        QueueFp604Api.Outcome actual = B374FullState270.execute(f.input, f.ram, f);

        if (stoppedAtCall) {
            Checks.same(f.stoppedOffer, actual, "Stopped exact outcome identity");
            Checks.equal(PREFIX_EVENTS, f.ram.traceSnapshot(), "Stopped exact prefix");
            Checks.equal(STOPPED_RAM_SHA256, f.ram.serializedSha256(), "Stopped entire RAM");
        } else {
            Checks.same(f.tailOffer, actual, "whole actual opaque Tail Outcome identity");
            QueueFp604Api.Normal normal = (QueueFp604Api.Normal) actual;
            GovernmentCrtBoundary185Api.NormalReturn result = normal.base().normalReturn();
            Checks.equal(POST_TAIL_V, result.volatileBits(), "complete actual tail post V/XMM0..5");
            Checks.equal(TAIL_N, result.nonvolatileBits(), "complete actual tail post N/XMM6");
            Checks.equal(0x0F1E2D3C4B5A6978L, result.returnRipBits(), "explicit opaque tail offered RIP");
            Checks.equal(0x0000000000027810L, result.callerRspBits(), "tail offered caller SP");
            Checks.equal(true, normal.base().postDirectionFlagSet(), "explicit tail post DF");
            Checks.same(f.postTailFp, normal.postMxcsr(), "tail post partial FP identity");
            Checks.equal(NORMAL_EVENTS, f.ram.traceSnapshot(), "normal exact memory events");
            Checks.equal(NORMAL_RAM_SHA256, f.ram.serializedSha256(), "normal entire RAM");
        }
        Checks.equal(1, f.callCount, "mandatory normal CALL count");
        Checks.equal(stoppedAtCall ? 0 : 1, f.tailCount, "tail JMP count");
        Checks.equal(0, f.ram.atomicCallCount(), "minimal selected path has no atomic effect");
        Checks.equal(0, f.budgetCalls, "fixed six rows have no budget callback");
    }

    private static final class Fixture implements B374Fp270Api.Calls {
        private final boolean stoppedAtCall;
        private final Ram ram = new Ram();
        private final QueueFp604Api.Mxcsr preFp = new QueueFp604Api.Mxcsr(0x0201, 0xA205);
        private final QueueFp604Api.Mxcsr postCallFp = new QueueFp604Api.Mxcsr(0x0004, 0x0045);
        private final QueueFp604Api.Mxcsr stoppedFp = new QueueFp604Api.Mxcsr(0x0080, 0x0181);
        private final QueueFp604Api.Mxcsr postTailFp = new QueueFp604Api.Mxcsr(0x1001, 0x3185);
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final QueueFp604Api.Input input;
        private final QueueFp604Api.Normal callOffer;
        private final QueueFp604Api.Normal tailOffer;
        private final QueueFp604Api.Stopped stoppedOffer;
        private int callCount;
        private int tailCount;
        private int budgetCalls;

        private Fixture(boolean stoppedAtCall) {
            this.stoppedAtCall = stoppedAtCall;
            budget = (header, address) -> {
                budgetCalls++;
                throw new AssertionError("No budget callback belongs to these fixed six source rows");
            };
            input = new QueueFp604Api.Input(new FullCopy437Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE, ENTRY_SP, ENTRY_V, ENTRY_N),
                true, budget), preFp);
            callOffer = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(
                    POST_CALL_V, 0x00000001642567F7L, 0x00000000000277E0L, CALL_N),
                false), postCallFp);
            tailOffer = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(
                    POST_TAIL_V, 0x0F1E2D3C4B5A6978L, 0x0000000000027810L, TAIL_N),
                true), postTailFp);
            stoppedOffer = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(
                    IMAGE, 0x00000000000277D8L, STOPPED_V, CALL_N),
                    0x425689CL, false, stoppedFp), 0, 0x42567F2L);
        }

        @Override public QueueFp604Api.Outcome invoke(B374Fp270Api.CallFrame frame) {
            callCount++;
            if (callCount != 1) throw new AssertionError("Unexpected normal CALL");
            Checks.equal(EXPECTED_CALL, frame.original(), "full original Call/site/kind/target/SP/V/N");
            Checks.equal(EXPECTED_CHILD, frame.childEntry(), "full child image/SP/V/N");
            Checks.equal(true, frame.directionFlagSet(), "actual CALL DF");
            Checks.same(preFp, frame.preMxcsr(), "actual CALL partial FP identity");
            Checks.equal(0x00000001642567F7L, frame.returnRipBits(), "owned five-byte CALL return");
            Checks.equal(PREFIX_EVENTS, ram.traceSnapshot(), "exact memory before opaque offer");
            Checks.equal(STOPPED_RAM_SHA256, ram.serializedSha256(), "entire RAM before opaque offer");
            if (stoppedAtCall) return stoppedOffer;
            // Explicit immutable public offer plus artificial sameRAM writes, no child algorithm.
            ram.writeQword(0x0000000000027810L, 0x1011121314151617L);
            ram.writeQword(0x0000000000027818L, 0x2021222324252627L);
            ram.writeQword(0x0000000000027820L, 0x3031323334353637L);
            ram.writeQword(0x0000000000027800L, 0x4041424344454647L);
            ram.writeQword(0x0000000000027808L, 0x0F1E2D3C4B5A6978L);
            return callOffer;
        }

        @Override public QueueFp604Api.Outcome tail(B374Fp270Api.TailFrame frame) {
            tailCount++;
            if (stoppedAtCall || callCount != 1 || tailCount != 1) {
                throw new AssertionError("Unexpected tail JMP");
            }
            Checks.equal(EXPECTED_TAIL, frame.original(), "full fresh restored tail entry and source edge");
            Checks.equal(false, frame.directionFlagSet(), "actual tail pre DF");
            Checks.same(postCallFp, frame.preMxcsr(), "actual tail pre partial FP identity");
            Checks.equal(NORMAL_EVENTS, ram.traceSnapshot(), "no synthetic push or local RET read");
            Checks.equal(NORMAL_RAM_SHA256, ram.serializedSha256(), "entire RAM at tail entry");
            return tailOffer; // Complete foreign DATA; no lower algorithm or local RET simulation.
        }
    }

    /** One bounded byte RAM. Sentinels and skipped poison pointers are deliberately unmapped. */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long BASE = 0x0000000000022000L;
        private final byte[] bytes = new byte[0x6000];
        private final ArrayList<String> events = new ArrayList<>();
        private int atomicCalls;

        private Ram() {
            for (int i = 0; i < bytes.length; i++) bytes[i] = (byte) (i * 11 + 0x4D);
            // Exact frozen28-patch DATA recipe, initialization is not logged.
            put64(0x0000000000027808L, 0x13579BDF2468ACE0L);
            put64(0x00000000000220F8L, 0x0000000000000000L);
            put64(0x0000000000022100L, 0x0000000000000000L);
            put64(0x0000000000022120L, 0x0000000000024000L);
            put64(0x0000000000022020L, 0x0000000000000000L);
            put64(0x0000000000022028L, 0x000000016542F498L);
            put64(0x0000000000022030L, 0xDEAD000000003000L);
            put64(0x0000000000022038L, 0xDEAD000000003800L);
            put64(0x0000000000022040L, 0x0000000000000000L);
            put64(0x0000000000022048L, 0x000000016542F498L);
            put64(0x0000000000022050L, 0xDEAD000000003100L);
            put64(0x0000000000022058L, 0xDEAD000000003900L);
            put64(0x0000000000022060L, 0x0000000000000000L);
            put64(0x0000000000022068L, 0x000000016542F498L);
            put64(0x0000000000022070L, 0xDEAD000000003200L);
            put64(0x0000000000022078L, 0xDEAD000000003A00L);
            put64(0x0000000000022080L, 0x0000000000000000L);
            put64(0x0000000000022088L, 0x000000016542F498L);
            put64(0x0000000000022090L, 0xDEAD000000003300L);
            put64(0x0000000000022098L, 0xDEAD000000003B00L);
            put64(0x00000000000220A0L, 0x0000000000000000L);
            put64(0x00000000000220A8L, 0x000000016542F498L);
            put64(0x00000000000220B0L, 0xDEAD000000003400L);
            put64(0x00000000000220B8L, 0xDEAD000000003C00L);
            put64(0x00000000000220C0L, 0x0000000000000000L);
            put64(0x00000000000220C8L, 0x000000016542F498L);
            put64(0x00000000000220D0L, 0xDEAD000000003500L);
            put64(0x00000000000220D8L, 0xDEAD000000003D00L);
        }

        private int index(long address, int width) {
            if (width <= 0 || width > 32) throw new AssertionError("Invalid port width");
            long offset = address - BASE;
            if (Long.compareUnsigned(address, BASE) >= 0
                    && Long.compareUnsigned(offset, bytes.length - width) <= 0) {
                return (int) offset;
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
