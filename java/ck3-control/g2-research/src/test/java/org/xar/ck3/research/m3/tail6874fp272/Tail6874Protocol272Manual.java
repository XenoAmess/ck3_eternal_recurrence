package org.xar.ck3.research.m3.tail6874fp272;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.tail6670fp271.Tail6670Fp271Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Four finite normal39 artificial-DATA cases, owner candidate-visible manual.
 * Original numeric result/RET oracle was frozen before new272candidate reads;
 * detailed fixture/hash literals were expanded before this Testbody, without SUT execution.
 * No old269 cases/expectations or outputs reused, only mechanical memory/hash ports.
 * Same64 bytes per case; sentinel deliberately unmapped. Software XADD returns actual oldbits.
 * No hardware atomicity, RFLAGS/EH, NativeFP, fullABI, loaded/Game or performance claim.
 */
public final class Tail6874Protocol272Manual {
    private Tail6874Protocol272Manual() { }
    private static final long IMAGE = 0x0000000140000000L;
    private static final long ENTRY_SP = 0x0000000000001800L;
    private static final boolean[] DFS = {true, false, true, false};
    private static final int[] FP_VALUES = {0x0041, 0x0101, 0x0000, 0x8000};
    private static final int[] FP_MASKS = {0x0065, 0x01C5, 0x0000, 0x8001};
    private static final int[] ATOMIC_COUNTS = {0, 0, 1, 1};
    private static final long[] RCXS = {0x0000000000000000L, 0x00000001444271D0L, 0x00000000000016BCL, 0x00000000000016A4L};
    private static final long[] INITIAL_RETS = {0x1020304050607080L, 0x2233445566778899L, 0x5566778899AABBCCL, 0x89ABCDEF7FFFFFFFL};
    private static final int[] INITIAL_COUNTERS = {0x10203040, 0x10203040, 0xFFFFFFFF, 0xA1B2C3D4};
    private static final long[] EXPECTED_RAX = {0x000000007FFFFFFFL, 0x000000007FFFFFFFL, 0x0000000000000000L, 0x0000000080000000L};
    private static final long[] EXPECTED_RETS = {0x1020304050607080L, 0x2233445566778899L, 0x5566778899AABBCCL, 0x89ABCDEF80000000L};
    private static final String[] INITIAL_RAM_SHA256 = {
        "5982f66ae51c0111d97c8a3b72973981541211dd6c3e974bfb227590738d364d",
        "8d118ca193db1c92ee3bff3a8eb686b303c62cbc33f75af41778c1886a9971e0",
        "9b944ad5e5ba899496026869d19d65591d953b9db1c2845b96298faa65a3d602",
        "b706d7f84c270bb4de61522652311534788c52b4c8451a9c3d852902eebef866"
    };
    private static final String[] EXPECTED_RAM_SHA256 = {
        "5982f66ae51c0111d97c8a3b72973981541211dd6c3e974bfb227590738d364d",
        "8d118ca193db1c92ee3bff3a8eb686b303c62cbc33f75af41778c1886a9971e0",
        "0a4a677508eb92137f553e9b568697b3ca1b95556345597c0be387bcb45f550f",
        "412e66cec2067de92f6d05b87bc9ff4b3195b91f1963723a90ad092b1468525d"
    };
    private static final List<List<String>> EXPECTED_EVENTS = List.of(
        List.of("R64 0000000000001800 1020304050607080"),
        List.of("R64 0000000000001800 2233445566778899"),
        List.of("X32 0000000000001818 00000001 FFFFFFFF 00000000", "R64 0000000000001800 5566778899AABBCC"),
        List.of("X32 0000000000001800 00000001 7FFFFFFF 80000000", "R64 0000000000001800 89ABCDEF80000000")
    );

    private static final NonvolatileBits N = new NonvolatileBits(
        0xA101020304050607L, 0xA202030405060708L, 0xA303040506070809L, 0xA40405060708090AL,
        0xA505060708090A0BL, 0xA6060708090A0B0CL, 0xA70708090A0B0C0DL, 0xA808090A0B0C0D0EL,
        new Bits128(0x99AABBCCDDEEFF01L, 0x0122334455667788L));

    /** Construction of fixed immutable DATA, not derivation from any SUT output. */
    private static VolatileBits v(long rax, long rcx) {
        return new VolatileBits(rax, rcx, 0xCABBCCDDEEFF0011L, 0xD102030405060708L,
            0xDDAABBCC11223344L, 0xE101020304050607L, 0xE201020304050607L,
            new Bits128(0x0102030405060708L, 0x1112131415161718L),
            new Bits128(0x2122232425262728L, 0x3132333435363738L),
            new Bits128(0x4142434445464748L, 0x5152535455565758L),
            new Bits128(0x6162636465666768L, 0x7172737475767778L),
            new Bits128(0x8182838485868788L, 0x9192939495969798L),
            new Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L));
    }

    public static void main(String[] args) {
        nullAndSentinel();
        atomicWrapAliasAndActualTailBinding();
        System.out.print("Tail6874Protocol272Manual: 4 finite cases completed\n");
    }

    private static void nullAndSentinel() {
        runCase(0, false);
        runCase(1, false);
    }

    private static void atomicWrapAliasAndActualTailBinding() {
        runCase(2, true);
        runCase(3, false);
    }

    private static void runCase(int id, boolean bind) {
        Ram ram = new Ram(id);
        Checks.equal(INITIAL_RAM_SHA256[id], ram.serializedSha256(), "initial full64 RAM");
        Checks.equal(List.of(), ram.traceSnapshot(), "DATA initialization is not a port event");
        QueueFp604Api.Mxcsr fp = new QueueFp604Api.Mxcsr(FP_VALUES[id], FP_MASKS[id]);
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, address) -> {
            throw new AssertionError("normal39 has no loop budget call");
        };
        GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
            IMAGE, ENTRY_SP, v(0xFEDCBA9876543210L, RCXS[id]), N);
        QueueFp604Api.Normal result;
        if (bind) {
            GovernmentCrtBoundary185Api.Tail tail = new GovernmentCrtBoundary185Api.Tail(
                0x42566F6L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4256874L, entry);
            Tail6670Fp271Api.TailFrame frame = new Tail6670Fp271Api.TailFrame(tail, DFS[id], fp);
            QueueFp604Api.Outcome outcome = Tail6874From6670272.bind(ram, budget).tail(frame);
            if (!(outcome instanceof QueueFp604Api.Normal normal)) throw new AssertionError("normal39 must return Normal");
            result = normal;
            // Only outer reference is public; no fabricated dynamic inner/outer identity claim.
        } else {
            QueueFp604Api.Input input = new QueueFp604Api.Input(new FullCopy437Api.Input(entry, DFS[id], budget), fp);
            result = Tail6874FullState272.execute(input, ram);
        }
        GovernmentCrtBoundary185Api.NormalReturn actual = result.base().normalReturn();
        Checks.equal(v(EXPECTED_RAX[id], RCXS[id]), actual.volatileBits(), "all full V/XMM0..5 with source RAXz32");
        Checks.equal(N, actual.nonvolatileBits(), "all N/XMM6 unchanged");
        Checks.equal(EXPECTED_RETS[id], actual.returnRipBits(), "fresh RET follows actual atomic modification");
        Checks.equal(0x0000000000001808L, actual.callerRspBits(), "RET consumes existing8byte slot");
        Checks.equal(DFS[id], result.base().postDirectionFlagSet(), "actual DF unchanged");
        Checks.same(fp, result.postMxcsr(), "same partial/unknown MXCSR object");
        Checks.equal(EXPECTED_EVENTS.get(id), ram.traceSnapshot(), "literal ordered memory effects");
        Checks.equal(ATOMIC_COUNTS[id], ram.atomicCallCount(), "one single atomic or none");
        Checks.equal(EXPECTED_RAM_SHA256[id], ram.serializedSha256(), "literal whole RAM hash");
    }

    /** Same64 artificial bytes back every width. This host does not model hardware faults. */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long BASE = 0x00000000000017F8L;
        private final byte[] bytes = new byte[64];
        private final ArrayList<String> events = new ArrayList<>();
        private int atomicCalls;

        private Ram(int caseId) {
            for (int i = 0; i < bytes.length; i++) bytes[i] = (byte) (i * 13 + 0x35);
            put64(0x0000000000001800L, INITIAL_RETS[caseId]);
            put32(0x0000000000001818L, INITIAL_COUNTERS[caseId]);
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
            if (!Objects.equals(expected, actual)) throw new AssertionError(label + ": expected=" + expected + ", actual=" + actual);
        }
        private static void same(Object expected, Object actual, String label) {
            if (expected != actual) throw new AssertionError(label + ": identity mismatch");
        }
    }
}
