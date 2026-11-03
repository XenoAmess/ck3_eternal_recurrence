package org.xar.ck3.research.m3.callee68d4fp269;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.callee68fcfp268.Callee68fcFp268Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Four finite normal37 public-DATA witnesses, with independently frozen269 expectations.
 * Oracle 8633dc975c9ca96f8930ed39e8e10679ffc0b0991a46e897d3b91329e6ae099c
 * was sealed before this author read selected269 entities. Old247/current268 originals
 * were visible; this final manual is candidate-visible, not whole blind.
 * Only mechanical RAM port/hash/assertion code is reused from this author's268 host.
 * No268 case, expected tuple, DATA recipe, hash or executed output supplies269 expectations.
 * All64 bytes per case are artificial DATA. The sentinel address is deliberately unmapped.
 * No opaque child, Stopped, foreign, default FP, hardware/EH/loaded/Game claim.
 */
public final class Callee68d4Protocol269Manual {
    private Callee68d4Protocol269Manual() { }

    private static final int BOUND_CASE = 3;
    private static final long IMAGE = 0x0000000150000000L;
    private static final long ENTRY_SP = 0x0000000000018008L;
    private static final boolean[] DFS = {false, true, true, false};
    private static final int[] ATOMIC_COUNTS = {0, 0, 1, 1};
    private static final int[] FP_VALUES = {0x0041, 0x2002, 0x0101, 0x0004};
    private static final int[] FP_MASKS = {0x0065, 0x2203, 0x01C5, 0xA105};
    private static final long[] INITIAL_RETS = {
        0x1122334455667788L, 0x2233445566778899L, 0x89ABCDEF00000000L, 0x000000015425699FL
    };
    private static final int[] INITIAL_COUNTERS = {
        0x10203040, 0x10203040, 0x10203040, 0x80000001
    };
    private static final long[] EXPECTED_RETS = {
        0x1122334455667788L, 0x2233445566778899L, 0x89ABCDEFFFFFFFFFL, 0x000000015425699FL
    };
    private static final String[] INITIAL_RAM_SHA256 = {
        "a322969f327243d63b6794f63be87a2e35c6d4237d7d0f2cb47ab59c500a3b31",
        "16956525804c734afde964f2cfabaa2ea6d75a97aefe869546c0bc44a16afa95",
        "996147e539fc7bfb5c7b66b87c80fcaf66eefd9927f782422f00d52d12ea4199",
        "36cba27f5eabf4d3da9a81e17a9624aa7157a0bdb8b83674aaab05622927cd94"
    };
    private static final String[] EXPECTED_RAM_SHA256 = {
        "a322969f327243d63b6794f63be87a2e35c6d4237d7d0f2cb47ab59c500a3b31",
        "16956525804c734afde964f2cfabaa2ea6d75a97aefe869546c0bc44a16afa95",
        "d269f8c1fa4fb34d0966602fad026b5799bbe4d69099eda8c0a359dc86e6c692",
        "cd3fd1b85b6edf11fcd42c519db0cd8297f67c0704a9e9abdb86a06018d680db"
    };
    private static final VolatileBits[] ENTRY_V = {
        new VolatileBits(
            0xFEDCBA9876543210L, 0x0000000000000000L, 0x8877665544332211L,
            0xFFEEDDCCBBAA0099L, 0x1029384756ABCDEFL, 0xA0B1C2D3E4F50617L, 0x7061524334251607L,
            new Bits128(0x0123000000000000L, 0xFEDC000000000000L), new Bits128(0x0134223344556677L, 0xFEDAFEFEFEFEFEFFL), new Bits128(0x0145446688AACCEEL, 0xFED9FDFDFDFDFDFEL),
            new Bits128(0x01566699CD003365L, 0xFED8FCFCFCFCFCFDL), new Bits128(0x016788CD115599DCL, 0xFED7FBFBFBFBFBFCL), new Bits128(0x0178AB0055AB0053L, 0xFED6FAFAFAFAFAFBL)),
        new VolatileBits(
            0xFEDCBA9876543210L, 0x00000001544271D0L, 0x8877665544332211L,
            0xFFEEDDCCBBAA0099L, 0x1029384756ABCDEFL, 0xA0B1C2D3E4F50617L, 0x7061524334251607L,
            new Bits128(0x0123000000000000L, 0xFEDC000000000000L), new Bits128(0x0134223344556677L, 0xFEDAFEFEFEFEFEFFL), new Bits128(0x0145446688AACCEEL, 0xFED9FDFDFDFDFDFEL),
            new Bits128(0x01566699CD003365L, 0xFED8FCFCFCFCFCFDL), new Bits128(0x016788CD115599DCL, 0xFED7FBFBFBFBFBFCL), new Bits128(0x0178AB0055AB0053L, 0xFED6FAFAFAFAFAFBL)),
        new VolatileBits(
            0xFEDCBA9876543210L, 0x0000000000017EACL, 0x8877665544332211L,
            0xFFEEDDCCBBAA0099L, 0x1029384756ABCDEFL, 0xA0B1C2D3E4F50617L, 0x7061524334251607L,
            new Bits128(0x0123000000000000L, 0xFEDC000000000000L), new Bits128(0x0134223344556677L, 0xFEDAFEFEFEFEFEFFL), new Bits128(0x0145446688AACCEEL, 0xFED9FDFDFDFDFDFEL),
            new Bits128(0x01566699CD003365L, 0xFED8FCFCFCFCFCFDL), new Bits128(0x016788CD115599DCL, 0xFED7FBFBFBFBFBFCL), new Bits128(0x0178AB0055AB0053L, 0xFED6FAFAFAFAFAFBL)),
        new VolatileBits(
            0xFEDCBA9876543210L, 0x0000000000017EC4L, 0x8877665544332211L,
            0xFFEEDDCCBBAA0099L, 0x1029384756ABCDEFL, 0xA0B1C2D3E4F50617L, 0x7061524334251607L,
            new Bits128(0x0123000000000000L, 0xFEDC000000000000L), new Bits128(0x0134223344556677L, 0xFEDAFEFEFEFEFEFFL), new Bits128(0x0145446688AACCEEL, 0xFED9FDFDFDFDFDFEL),
            new Bits128(0x01566699CD003365L, 0xFED8FCFCFCFCFCFDL), new Bits128(0x016788CD115599DCL, 0xFED7FBFBFBFBFBFCL), new Bits128(0x0178AB0055AB0053L, 0xFED6FAFAFAFAFAFBL))
    };
    private static final VolatileBits[] EXPECTED_V = {
        new VolatileBits(
            0x000000007FFFFFFFL, 0x0000000000000000L, 0x8877665544332211L,
            0xFFEEDDCCBBAA0099L, 0x1029384756ABCDEFL, 0xA0B1C2D3E4F50617L, 0x7061524334251607L,
            new Bits128(0x0123000000000000L, 0xFEDC000000000000L), new Bits128(0x0134223344556677L, 0xFEDAFEFEFEFEFEFFL), new Bits128(0x0145446688AACCEEL, 0xFED9FDFDFDFDFDFEL),
            new Bits128(0x01566699CD003365L, 0xFED8FCFCFCFCFCFDL), new Bits128(0x016788CD115599DCL, 0xFED7FBFBFBFBFBFCL), new Bits128(0x0178AB0055AB0053L, 0xFED6FAFAFAFAFAFBL)),
        new VolatileBits(
            0x000000007FFFFFFFL, 0x00000001544271D0L, 0x8877665544332211L,
            0xFFEEDDCCBBAA0099L, 0x1029384756ABCDEFL, 0xA0B1C2D3E4F50617L, 0x7061524334251607L,
            new Bits128(0x0123000000000000L, 0xFEDC000000000000L), new Bits128(0x0134223344556677L, 0xFEDAFEFEFEFEFEFFL), new Bits128(0x0145446688AACCEEL, 0xFED9FDFDFDFDFDFEL),
            new Bits128(0x01566699CD003365L, 0xFED8FCFCFCFCFCFDL), new Bits128(0x016788CD115599DCL, 0xFED7FBFBFBFBFBFCL), new Bits128(0x0178AB0055AB0053L, 0xFED6FAFAFAFAFAFBL)),
        new VolatileBits(
            0x00000000FFFFFFFFL, 0x0000000000017EACL, 0x8877665544332211L,
            0xFFEEDDCCBBAA0099L, 0x1029384756ABCDEFL, 0xA0B1C2D3E4F50617L, 0x7061524334251607L,
            new Bits128(0x0123000000000000L, 0xFEDC000000000000L), new Bits128(0x0134223344556677L, 0xFEDAFEFEFEFEFEFFL), new Bits128(0x0145446688AACCEEL, 0xFED9FDFDFDFDFDFEL),
            new Bits128(0x01566699CD003365L, 0xFED8FCFCFCFCFCFDL), new Bits128(0x016788CD115599DCL, 0xFED7FBFBFBFBFBFCL), new Bits128(0x0178AB0055AB0053L, 0xFED6FAFAFAFAFAFBL)),
        new VolatileBits(
            0x0000000080000000L, 0x0000000000017EC4L, 0x8877665544332211L,
            0xFFEEDDCCBBAA0099L, 0x1029384756ABCDEFL, 0xA0B1C2D3E4F50617L, 0x7061524334251607L,
            new Bits128(0x0123000000000000L, 0xFEDC000000000000L), new Bits128(0x0134223344556677L, 0xFEDAFEFEFEFEFEFFL), new Bits128(0x0145446688AACCEEL, 0xFED9FDFDFDFDFDFEL),
            new Bits128(0x01566699CD003365L, 0xFED8FCFCFCFCFCFDL), new Bits128(0x016788CD115599DCL, 0xFED7FBFBFBFBFBFCL), new Bits128(0x0178AB0055AB0053L, 0xFED6FAFAFAFAFAFBL))
    };
    private static final NonvolatileBits ENTRY_N = new NonvolatileBits(
        0x9101020304050607L, 0x9202030405060708L, 0x9303040506070809L, 0x940405060708090AL,
        0x9505060708090A0BL, 0x96060708090A0B0CL, 0x970708090A0B0C0DL, 0x9808090A0B0C0D0EL,
        new Bits128(0x99AABBCCDDEEFF00L, 0x0011223344556677L));
    private static final List<List<String>> EXPECTED_EVENTS = List.of(
        List.of("R64 0000000000018008 1122334455667788"),
        List.of("R64 0000000000018008 2233445566778899"),
        List.of("X32 0000000000018008 FFFFFFFF 00000000 FFFFFFFF", "R64 0000000000018008 89ABCDEFFFFFFFFF"),
        List.of("X32 0000000000018020 FFFFFFFF 80000001 80000000", "R64 0000000000018008 000000015425699F")
    );

    public static void main(String[] args) {
        runCase(0);
        runCase(1);
        runCase(2);
        runCase(3);
        System.out.print("Callee68d4Protocol269Manual: 4 finite cases completed\n");
    }

    private static void runCase(int caseId) {
        Fixture f = new Fixture(caseId);
        Checks.equal(INITIAL_RAM_SHA256[caseId], f.ram.serializedSha256(), "initial entire RAM");
        Checks.equal(List.of(), f.ram.traceSnapshot(), "DATA setup has no port events");
        QueueFp604Api.Normal actual;
        if (caseId == BOUND_CASE) {
            // The268-owned return is initial DATA; the269 binder must not push again.
            GovernmentCrtBoundary185Api.Call original = new GovernmentCrtBoundary185Api.Call(
                0x425699AL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x42568D4L,
                0x0000000000018010L, ENTRY_V[caseId], ENTRY_N);
            Callee68fcFp268Api.CallFrame frame = new Callee68fcFp268Api.CallFrame(
                original, f.input.base().entry(), DFS[caseId], f.preFp);
            Callee68fcFp268Api.Calls bound = Callee68d4From68fc269.bind(f.ram, f.budget);
            QueueFp604Api.Outcome outcome = bound.invoke(frame);
            if (!(outcome instanceof QueueFp604Api.Normal normal)) {
                throw new AssertionError("The actual269 binding must return Normal");
            }
            actual = normal;
            // The public API exposes only the outer reference. Inner/outer same-Normal identity
            // remains a source-contract finding, not a fabricated dynamic assertion.
        } else {
            actual = Callee68d4FullState269.execute(f.input, f.ram);
        }
        GovernmentCrtBoundary185Api.NormalReturn result = actual.base().normalReturn();
        Checks.equal(EXPECTED_V[caseId], result.volatileBits(), "complete post V/XMM0..5");
        Checks.equal(ENTRY_N, result.nonvolatileBits(), "complete unchanged N/XMM6");
        Checks.equal(EXPECTED_RETS[caseId], result.returnRipBits(), "fresh RET after old core");
        Checks.equal(0x0000000000018010L, result.callerRspBits(), "entry SP plus8");
        Checks.equal(DFS[caseId], actual.base().postDirectionFlagSet(), "unchanged actual DF");
        Checks.same(f.preFp, actual.postMxcsr(), "same partial input FP object");
        Checks.equal(EXPECTED_EVENTS.get(caseId), f.ram.traceSnapshot(), "exact finite memory trace");
        Checks.equal(EXPECTED_RAM_SHA256[caseId], f.ram.serializedSha256(), "entire post RAM");
        Checks.equal(ATOMIC_COUNTS[caseId], f.ram.atomicCallCount(), "atomic port count");
        Checks.equal(0, f.budgetCalls, "normal37 has no loop/budget call");
    }

    private static final class Fixture {
        private final Ram ram;
        private final QueueFp604Api.Mxcsr preFp;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final QueueFp604Api.Input input;
        private int budgetCalls;

        private Fixture(int caseId) {
            if (caseId < 0 || caseId > BOUND_CASE) throw new AssertionError("Unknown finite case");
            ram = new Ram(caseId);
            preFp = new QueueFp604Api.Mxcsr(FP_VALUES[caseId], FP_MASKS[caseId]);
            budget = (header, address) -> {
                budgetCalls++;
                throw new AssertionError("No budget step belongs to the37-byte normal body");
            };
            GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                IMAGE, ENTRY_SP, ENTRY_V[caseId], ENTRY_N);
            input = new QueueFp604Api.Input(new FullCopy437Api.Input(entry, DFS[caseId], budget), preFp);
        }
    }

    /** Same64 artificial bytes back every width. This host does not model hardware faults. */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long BASE = 0x0000000000018000L;
        private final byte[] bytes = new byte[64];
        private final ArrayList<String> events = new ArrayList<>();
        private int atomicCalls;

        private Ram(int caseId) {
            for (int i = 0; i < bytes.length; i++) bytes[i] = (byte) (i * 17 + 0x63);
            put64(0x0000000000018008L, INITIAL_RETS[caseId]);
            put32(0x0000000000018020L, INITIAL_COUNTERS[caseId]);
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
