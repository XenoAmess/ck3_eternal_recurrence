package org.xar.ck3.research.m3.f780fp264;

import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Two finite public-DATA protocol witnesses from original63 ASM.
 * Oracle264 was sealed before any new264 body read. Opaque children only offer
 * explicit immutable states and listed writes to the same finite RAM.
 * No Native, hardware atomicity, ABI, EH or opaque-child algorithm qualification.
 */
public final class F780Protocol264Manual {
    private F780Protocol264Manual() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 0) throw new IllegalArgumentException("No arguments accepted");
        runCase(false);
        runCase(true);
        System.out.print("F780Protocol264Manual: 2 finite cases completed\n");
    }

    private static void runCase(boolean firstStopped) throws Exception {
        Fixture f = new Fixture();
        int[] callCount = {0};
        F780Fp264Api.Calls offered = actual -> {
            int ordinal = ++callCount[0];
            if (ordinal == 1) {
                if (!actual.original().equals(f.firstCall)
                        || !actual.childEntry().equals(f.firstChild)
                        || actual.directionFlagSet() != true
                        || actual.preMxcsr() != f.fpEntry
                        || actual.returnRipBits() != 0x000000018424F79CL) {
                    throw new AssertionError("First complete frame differs from sealed DATA");
                }
                if (firstStopped) return f.firstStopped;
                f.ram.writeQword(0x0000000000003900L, 0x0000000000003C00L);
                f.ram.writeQword(0x0000000000003C00L, 0x0000000000003D00L);
                f.ram.writeQword(0x0000000000003D88L, 0x0000000000003980L);
                f.ram.writeDword(0x0000000000003980L, 0x7FFFFFFF);
                return f.firstNormal;
            }
            if (ordinal == 2 && !firstStopped) {
                if (!actual.original().equals(f.secondCall)
                        || !actual.childEntry().equals(f.secondChild)
                        || actual.directionFlagSet() != false
                        || actual.preMxcsr() != f.fpAfterFirst
                        || actual.returnRipBits() != 0x000000018424F7B4L) {
                    throw new AssertionError("Second complete frame differs from sealed DATA");
                }
                f.ram.writeQword(0x0000000000003010L, 0xDDBBCCAA99887766L);
                f.ram.writeQword(0x0000000000003000L, 0x1029384756AABBCCL);
                f.ram.writeQword(0x0000000000003008L, 0x0000000180654321L);
                return f.secondNormal;
            }
            throw new AssertionError("Unexpected opaque call ordinal " + ordinal);
        };
        QueueFp604Api.Input input = new QueueFp604Api.Input(
                new FullCopy437Api.Input(f.entry, true, (header, guard) -> {
                    throw new AssertionError("Straight-line original63 used loop budget");
                }), f.fpEntry);
        QueueFp604Api.Outcome actual = F780FullState264.execute(input, f.ram, offered);
        List<String> expectedTrace = firstStopped ? f.stoppedTrace : f.normalTrace;
        if (!f.ram.trace.equals(expectedTrace)) {
            throw new AssertionError("Memory effect trace differs: " + f.ram.trace
                    + " expected " + expectedTrace);
        }
        if (callCount[0] != (firstStopped ? 1 : 2)
                || f.ram.atomicCalls != (firstStopped ? 0 : 1)) {
            throw new AssertionError("Opaque call or indivisible increment count differs");
        }
        if (firstStopped) {
            if (actual != f.firstStopped) {
                throw new AssertionError("First Stopped identity was reconstructed or lost");
            }
        } else {
            if (!(actual instanceof QueueFp604Api.Normal normal)
                    || !normal.base().equals(f.expectedNormal.base())
                    || normal.postMxcsr() != f.fpAfterSecond) {
                throw new AssertionError("Final complete V/N/SP/RIP/DF/partialFP differs");
            }
        }
        String ramHash = HexFormat.of().formatHex(
                MessageDigest.getInstance("SHA-256").digest(f.ram.bytes));
        String expectedHash = firstStopped
                ? "ecf37404af3e1c8c978b106d5857638f69661c82b8ac77453f6762381eb75bbf"
                : "4cf6d10e3053da5387d617e108c3b635616846dc84f618db04fe5d14f7bfc7ba";
        if (!ramHash.equals(expectedHash)) {
            throw new AssertionError("Finite RAM differs from sealed byte image: " + ramHash);
        }
    }

    private static final class Fixture {
        final QueueFp604Api.Mxcsr fpEntry = new QueueFp604Api.Mxcsr(0x0020, 0x0021);
        final QueueFp604Api.Mxcsr fpAfterFirst = new QueueFp604Api.Mxcsr(0x0102, 0x0103);
        final QueueFp604Api.Mxcsr fpAfterSecond = new QueueFp604Api.Mxcsr(0x0201, 0x0303);
        final QueueFp604Api.Mxcsr fpStopped = new QueueFp604Api.Mxcsr(0x0001, 0x0005);
        final GovernmentPrimaryTail155Api.VolatileBits entryV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xE101112233445566L, 0xE102112233445566L, 0x0000000000003800L, 0x0000000000003900L, 0x0000000000003980L, 0xE106112233445566L, 0xE107112233445566L,
                new GovernmentPrimaryTail155Api.Bits128(0xE110112233445566L, 0xE111112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE112112233445566L, 0xE113112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE114112233445566L, 0xE115112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE116112233445566L, 0xE117112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE118112233445566L, 0xE119112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE11A112233445566L, 0xE11B112233445566L));
        final GovernmentPrimaryTail155Api.NonvolatileBits entryN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x2233445566778899L, 0x33445566778899AAL, 0x445566778899AABBL, 0x66778899AABBCCDDL, 0x778899AABBCCDDEEL, 0x8899AABBCCDDEEFFL, 0x99AABBCCDDEEFF10L, 0xAABBCCDDEEFF1021L,
                new GovernmentPrimaryTail155Api.Bits128(0xBBCDDFF102132435L, 0xCCDEEFF213243546L));
        final GovernmentPrimaryTail155Api.VolatileBits firstV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xE101112233445566L, 0x00000000F2345678L, 0x0000000000003800L, 0x0000000000003900L, 0x0000000000003980L, 0xE106112233445566L, 0xE107112233445566L,
                new GovernmentPrimaryTail155Api.Bits128(0xE110112233445566L, 0xE111112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE112112233445566L, 0xE113112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE114112233445566L, 0xE115112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE116112233445566L, 0xE117112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE118112233445566L, 0xE119112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xE11A112233445566L, 0xE11B112233445566L));
        final GovernmentPrimaryTail155Api.VolatileBits secondV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x0000000000003980L, 0x0000000080000000L, 0xA303112233445566L, 0xA304112233445566L, 0xA305112233445566L, 0xA306112233445566L, 0xA307112233445566L,
                new GovernmentPrimaryTail155Api.Bits128(0xA310112233445566L, 0xA311112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA312112233445566L, 0xA313112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA314112233445566L, 0xA315112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA316112233445566L, 0xA317112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA318112233445566L, 0xA319112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA31A112233445566L, 0xA31B112233445566L));
        final GovernmentPrimaryTail155Api.NonvolatileBits callN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x0000000000003980L, 0x33445566778899AAL, 0x445566778899AABBL, 0x0000000000003900L, 0x778899AABBCCDDEEL, 0x8899AABBCCDDEEFFL, 0x99AABBCCDDEEFF10L, 0xAABBCCDDEEFF1021L,
                new GovernmentPrimaryTail155Api.Bits128(0xBBCDDFF102132435L, 0xCCDEEFF213243546L));
        final GovernmentPrimaryTail155Api.VolatileBits postFirstV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xA301112233445566L, 0xA302112233445566L, 0xA303112233445566L, 0xA304112233445566L, 0xA305112233445566L, 0xA306112233445566L, 0xA307112233445566L,
                new GovernmentPrimaryTail155Api.Bits128(0xA310112233445566L, 0xA311112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA312112233445566L, 0xA313112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA314112233445566L, 0xA315112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA316112233445566L, 0xA317112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA318112233445566L, 0xA319112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xA31A112233445566L, 0xA31B112233445566L));
        final GovernmentPrimaryTail155Api.VolatileBits postSecondV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xB701112233445566L, 0xB702112233445566L, 0xB703112233445566L, 0xB704112233445566L, 0xB705112233445566L, 0xB706112233445566L, 0xB707112233445566L,
                new GovernmentPrimaryTail155Api.Bits128(0xB710112233445566L, 0xB711112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xB712112233445566L, 0xB713112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xB714112233445566L, 0xB715112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xB716112233445566L, 0xB717112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xB718112233445566L, 0xB719112233445566L),
                new GovernmentPrimaryTail155Api.Bits128(0xB71A112233445566L, 0xB71B112233445566L));
        final GovernmentPrimaryTail155Api.NonvolatileBits finalN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0xDDBBCCAA99887766L, 0x33445566778899AAL, 0x445566778899AABBL, 0x1029384756AABBCCL, 0x778899AABBCCDDEEL, 0x8899AABBCCDDEEFFL, 0x99AABBCCDDEEFF10L, 0xAABBCCDDEEFF1021L,
                new GovernmentPrimaryTail155Api.Bits128(0xBBCDDFF102132435L, 0xCCDEEFF213243546L));
        final GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(0x0000000180000000L, 0x0000000000003008L, entryV, entryN);
        final GovernmentCrtBoundary185Api.Call firstCall = new GovernmentCrtBoundary185Api.Call(
                0x000000000424F797L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x0000000004247FFCL, 0x0000000000002FE0L, firstV, callN);
        final GovernmentCrtBoundary185Api.Entry firstChild = new GovernmentCrtBoundary185Api.Entry(0x0000000180000000L, 0x0000000000002FD8L, firstV, callN);
        final GovernmentCrtBoundary185Api.Call secondCall = new GovernmentCrtBoundary185Api.Call(
                0x000000000424F7AFL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x0000000004248050L, 0x0000000000002FE0L, secondV, callN);
        final GovernmentCrtBoundary185Api.Entry secondChild = new GovernmentCrtBoundary185Api.Entry(0x0000000180000000L, 0x0000000000002FD8L, secondV, callN);
        final QueueFp604Api.Normal firstNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postFirstV, 0x000000018424F79CL, 0x0000000000002FE0L, callN),
                false), fpAfterFirst);
        final QueueFp604Api.Normal secondNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postSecondV, 0x000000018424F7B4L, 0x0000000000002FE0L, callN),
                true), fpAfterSecond);
        final QueueFp604Api.Normal expectedNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postSecondV, 0x0000000180654321L, 0x0000000000003010L, finalN),
                true), fpAfterSecond);
        final QueueFp604Api.Stopped firstStopped = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(firstChild, 0x0000000004247FFCL, false, fpStopped),
                0, 0x000000000424F797L);
        final List<String> normalTrace = List.of(
                "W64@3010=2233445566778899",
                "W64@3028=3980",
                "W64@3000=66778899aabbccdd",
                "R32@3800=f2345678",
                "W64@2fd8=18424f79c",
                "W64@3900=3c00",
                "W64@3c00=3d00",
                "W64@3d88=3980",
                "W32@3980=7fffffff",
                "R64@3900=3c00",
                "R64@3c00=3d00",
                "R64@3d88=3980",
                "A32@3980=1/7fffffff/80000000",
                "R32@3980=80000000",
                "W64@2fd8=18424f7b4",
                "W64@3010=ddbbccaa99887766",
                "W64@3000=1029384756aabbcc",
                "W64@3008=180654321",
                "R64@3010=ddbbccaa99887766",
                "R64@3000=1029384756aabbcc",
                "R64@3008=180654321");
        final List<String> stoppedTrace = List.of(
                "W64@3010=2233445566778899",
                "W64@3028=3980",
                "W64@3000=66778899aabbccdd",
                "R32@3800=f2345678",
                "W64@2fd8=18424f79c");
        final Ram ram = new Ram();

        Fixture() {
            ram.seed(0x0000000000003008L, 8, 0x0000000180123456L);
            ram.seed(0x0000000000003800L, 4, 0xF2345678L);
            ram.seed(0x0000000000003900L, 8, 0x0000000000003A00L);
            ram.seed(0x0000000000003A00L, 8, 0x0000000000003B00L);
            ram.seed(0x0000000000003B88L, 8, 0x0000000000003E00L);
            ram.seed(0x0000000000003E00L, 4, 0x11223344L);
            ram.seed(0x0000000000003980L, 4, 0x7FFFFFFEL);
        }
    }

    /** Exact-width finite host storage; unused protocol methods fail explicitly. */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long BASE = 0x2000L;
        private final byte[] bytes = new byte[0x3000];
        private final List<String> trace = new ArrayList<>();
        private int atomicCalls;

        Ram() {
            for (int i = 0; i < bytes.length; i++) bytes[i] = (byte) (i * 53 + 0x2D);
        }

        private int index(long address, int width) {
            if (width < 1 || address < BASE || address - BASE > bytes.length - width) {
                throw new UnsupportedOperationException("Access outside finite RAM");
            }
            return (int) (address - BASE);
        }

        private long loadRaw(long address, int width) {
            int start = index(address, width);
            long value = 0;
            for (int i = 0; i < width; i++) {
                value |= (bytes[start + i] & 0xFFL) << (8 * i);
            }
            return value;
        }

        private void storeRaw(long address, int width, long value) {
            int start = index(address, width);
            for (int i = 0; i < width; i++) {
                bytes[start + i] = (byte) (value >>> (8 * i));
            }
        }

        void seed(long address, int width, long value) {
            storeRaw(address, width, value);
        }

        private void effect(String op, long address, long value) {
            trace.add(op + "@" + Long.toUnsignedString(address, 16)
                    + "=" + Long.toUnsignedString(value, 16));
        }

        @Override public int readDword(long address) {
            int value = (int) loadRaw(address, 4);
            effect("R32", address, Integer.toUnsignedLong(value));
            return value;
        }

        @Override public long readQword(long address) {
            long value = loadRaw(address, 8);
            effect("R64", address, value);
            return value;
        }

        @Override public void writeDword(long address, int value) {
            storeRaw(address, 4, Integer.toUnsignedLong(value));
            effect("W32", address, Integer.toUnsignedLong(value));
        }

        @Override public void writeQword(long address, long value) {
            storeRaw(address, 8, value);
            effect("W64", address, value);
        }

        @Override public synchronized int lockedXaddDword(long address, int addend) {
            int before = (int) loadRaw(address, 4);
            int after = before + addend;
            storeRaw(address, 4, Integer.toUnsignedLong(after));
            atomicCalls++;
            trace.add("A32@" + Long.toUnsignedString(address, 16) + "="
                    + Integer.toUnsignedString(addend, 16) + "/"
                    + Integer.toUnsignedString(before, 16) + "/"
                    + Integer.toUnsignedString(after, 16));
            return before;
        }

        @Override public int readUnsignedByte(long address) { throw new UnsupportedOperationException("Unused readUnsignedByte"); }
        @Override public int readUnsignedWord(long address) { throw new UnsupportedOperationException("Unused readUnsignedWord"); }
        @Override public void writeByte(long address, int value) { throw new UnsupportedOperationException("Unused writeByte"); }
        @Override public void writeWord(long address, int value) { throw new UnsupportedOperationException("Unused writeWord"); }
        @Override public GovernmentPrimaryTail155Api.Bits128 read128(long address) { throw new UnsupportedOperationException("Unused read128"); }
        @Override public void write128(long address, GovernmentPrimaryTail155Api.Bits128 value) { throw new UnsupportedOperationException("Unused write128"); }
        @Override public void write128NonTemporal(long address, GovernmentPrimaryTail155Api.Bits128 value) { throw new UnsupportedOperationException("Unused write128NonTemporal"); }
        @Override public FullCopy437Api.Bits256 read256(long address) { throw new UnsupportedOperationException("Unused read256"); }
        @Override public void write256(long address, FullCopy437Api.Bits256 value) { throw new UnsupportedOperationException("Unused write256"); }
        @Override public void write256NonTemporal(long address, FullCopy437Api.Bits256 value) { throw new UnsupportedOperationException("Unused write256NonTemporal"); }
        @Override public void sfence() { throw new UnsupportedOperationException("Unused sfence"); }
    }
}
