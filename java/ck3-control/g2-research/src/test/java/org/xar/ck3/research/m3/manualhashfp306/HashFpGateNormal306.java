package org.xar.ck3.research.m3.manualhashfp306;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.hashfpgate305.HashFpGate305;
import org.xar.ck3.research.m5.GovernmentCaller153Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Source-only finite manual witness; no CPU, Native or complete Hash claim. */
public final class HashFpGateNormal306 {
    private HashFpGateNormal306() { }

    private static final long IMAGE = 0x140000000L;
    private static final long SP = 0x81000L;
    private static final long THRESHOLD_ADDRESS = 0x2401cL;
    private static int checks;

    private record Case(String id, HashFpGate305.Input input, CountingBudget budget,
            int thresholdBits, GovernmentCrtBoundary185Api.Entry expectedState,
            boolean expectedDf, QueueFp604Api.Mxcsr expectedMxcsr,
            HashFpGate305.Relation expectedRelation, long expectedNextRva) { }

    private record Read(long address, int value) { }

    private static final class CountingBudget implements GovernmentCrtBoundary185Api.LoopBudget {
        private int calls;
        @Override public void beforeStep(long loopHeaderRva, long guardAddressBits) {
            calls++;
            throw new AssertionError("unexpected loop budget callback");
        }
    }

    /** One explicit mapped DWORD. All unused Memory operations reject, never default to zero. */
    private static final class ThresholdMemory implements GovernmentCaller153Api.Memory {
        private boolean installed;
        private int value;
        private final List<Read> observed = new ArrayList<>();

        void install(int bits) { value = bits; installed = true; }
        int readCount() { return observed.size(); }
        Read readAt(int index) { return observed.get(index); }
        @Override public int readDword(long addressBits) {
            if (!installed || addressBits != THRESHOLD_ADDRESS) {
                throw new AssertionError("unmapped DWORD " + Long.toUnsignedString(addressBits, 16));
            }
            observed.add(new Read(addressBits, value));
            return value;
        }
        @Override public long readQword(long addressBits) {
            throw new AssertionError("unexpected QWORD read");
        }
        @Override public int readUnsignedByte(long addressBits) {
            throw new AssertionError("unexpected BYTE read");
        }
        @Override public void writeDword(long addressBits, int valueBits) {
            throw new AssertionError("unexpected DWORD write");
        }
        @Override public int lockedXaddDword(long addressBits, int addendBits) {
            throw new AssertionError("unexpected atomic DWORD");
        }
    }

    private static GovernmentPrimaryTail155Api.Bits128 bits(long low, long high) {
        return new GovernmentPrimaryTail155Api.Bits128(low, high);
    }

    private static GovernmentPrimaryTail155Api.VolatileBits incoming(long rax, long rcx) {
        return new GovernmentPrimaryTail155Api.VolatileBits(rax, rcx,
                0xc303000000000003L, 0xd408000000000008L, 0xe509000000000009L,
                0xf60a00000000000aL, 0x780b00000000000bL,
                bits(0x1122334455667788L, 0x99aabbccddeeff00L),
                bits(0xabcdef0123456789L, 0x123456789abcdef0L),
                bits(0x2200000000000002L, 0x2280000000000002L),
                bits(0x3300000000000003L, 0x3380000000000003L),
                bits(0x4400000000000004L, 0x4480000000000004L),
                bits(0x5500000000000005L, 0x5580000000000005L));
    }

    private static GovernmentPrimaryTail155Api.NonvolatileBits nonvolatileBits() {
        return new GovernmentPrimaryTail155Api.NonvolatileBits(
                0xb101000000000001L, 0xb202000000000002L,
                0xb303000000000003L, 0xb404000000000004L,
                0xb512000000000012L, 0xb613000000000013L,
                0x24000L, 0xb815000000000015L,
                bits(0xf600000000000006L, 0xf680000000000006L));
    }

    /** Mechanical substitution of two independently frozen expected low128 values. */
    private static GovernmentCrtBoundary185Api.Entry expectedState(
            GovernmentCrtBoundary185Api.Entry before, long x0Low, long x1Low) {
        GovernmentPrimaryTail155Api.VolatileBits v = before.volatileBits();
        GovernmentPrimaryTail155Api.VolatileBits after = new GovernmentPrimaryTail155Api.VolatileBits(
                v.raxBits(), v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                bits(x0Low, 0), bits(x1Low, 0), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
        return new GovernmentCrtBoundary185Api.Entry(before.imageBaseBits(), before.rspBits(),
                after, before.nonvolatileBits());
    }

    private static Case literal(String id, long rax, long rcx, boolean df, int fpValue,
            int fpMask, int threshold, long expectedX0, long expectedX1,
            int postValue, int postMask, HashFpGate305.Relation relation,
            long nextRva, long origin) {
        CountingBudget budget = new CountingBudget();
        GovernmentCrtBoundary185Api.Entry before = new GovernmentCrtBoundary185Api.Entry(
                IMAGE, SP, incoming(rax, rcx), nonvolatileBits());
        HashFpGate305.Input input = new HashFpGate305.Input(new QueueFp604Api.Input(
                new FullCopy437Api.Input(before, df, budget),
                new QueueFp604Api.Mxcsr(fpValue, fpMask)), origin);
        return new Case(id, input, budget, threshold, expectedState(before, expectedX0, expectedX1),
                df, new QueueFp604Api.Mxcsr(postValue, postMask), relation, nextRva);
    }

    private static List<Case> cases() {
        return List.of(
                literal("nearest-positive-divide-equal", 0xaL, 3L, true,
                        0x1000, 0x7000, 0x40555555, 0x40400000L, 0x40555555L,
                        0x1020, 0x7020, HashFpGate305.Relation.EQUAL, 0xc39d11L, 0x306001L),
                literal("up-positive-divide-greater", 0xaL, 3L, false,
                        0x5000, 0x7000, 0x40555555, 0x40400000L, 0x40555556L,
                        0x5020, 0x7020, HashFpGate305.Relation.GREATER, 0xc39f28L, 0x306002L),
                literal("down-negative-numerator-conversion-less", 0xfeffffffL, 1L, true,
                        0x3000, 0x7000, 0xcb800000, 0x3f800000L, 0xcb800001L,
                        0x3020, 0x7020, HashFpGate305.Relation.LESS, 0xc39d11L, 0x306003L),
                literal("exact-negative-zero-with-unknown-controls-old-PE", 0L, -2L, false,
                        0x20, 0x20, 0, 0xc0000000L, 0x80000000L,
                        0x20, 0x20, HashFpGate305.Relation.EQUAL, 0xc39d11L, 0x306004L));
    }

    private static void require(boolean condition, String label) {
        checks++;
        if (!condition) throw new AssertionError(label);
    }

    private static void equal(Object actual, Object expected, String label) {
        require(Objects.equals(actual, expected), label + " actual=" + actual + " expected=" + expected);
    }

    private static void runCase(Case c, ThresholdMemory memory) {
        memory.install(c.thresholdBits());
        int startReads = memory.readCount();
        HashFpGate305.Result result = HashFpGate305.execute(c.input(), memory);
        require(result instanceof HashFpGate305.Continued, "expected Continued");
        HashFpGate305.Continued continued = (HashFpGate305.Continued) result;
        QueueFp604Api.Snapshot snapshot = continued.snapshot();
        GovernmentCrtBoundary185Api.Entry actualEntry = snapshot.currentState();
        GovernmentCrtBoundary185Api.Entry expectedEntry = c.expectedState();
        equal(actualEntry.imageBaseBits(), expectedEntry.imageBaseBits(), "imageBaseBits");
        equal(actualEntry.rspBits(), expectedEntry.rspBits(), "rspBits");
        GovernmentPrimaryTail155Api.VolatileBits actualV = actualEntry.volatileBits();
        GovernmentPrimaryTail155Api.VolatileBits expectedV = expectedEntry.volatileBits();
        equal(actualV.raxBits(), expectedV.raxBits(), "raxBits");
        equal(actualV.rcxBits(), expectedV.rcxBits(), "rcxBits");
        equal(actualV.rdxBits(), expectedV.rdxBits(), "rdxBits");
        equal(actualV.r8Bits(), expectedV.r8Bits(), "r8Bits");
        equal(actualV.r9Bits(), expectedV.r9Bits(), "r9Bits");
        equal(actualV.r10Bits(), expectedV.r10Bits(), "r10Bits");
        equal(actualV.r11Bits(), expectedV.r11Bits(), "r11Bits");
        equal(actualV.xmm0().lowBits(), expectedV.xmm0().lowBits(), "xmm0.lowBits");
        equal(actualV.xmm0().highBits(), expectedV.xmm0().highBits(), "xmm0.highBits");
        equal(actualV.xmm1().lowBits(), expectedV.xmm1().lowBits(), "xmm1.lowBits");
        equal(actualV.xmm1().highBits(), expectedV.xmm1().highBits(), "xmm1.highBits");
        equal(actualV.xmm2().lowBits(), expectedV.xmm2().lowBits(), "xmm2.lowBits");
        equal(actualV.xmm2().highBits(), expectedV.xmm2().highBits(), "xmm2.highBits");
        equal(actualV.xmm3().lowBits(), expectedV.xmm3().lowBits(), "xmm3.lowBits");
        equal(actualV.xmm3().highBits(), expectedV.xmm3().highBits(), "xmm3.highBits");
        equal(actualV.xmm4().lowBits(), expectedV.xmm4().lowBits(), "xmm4.lowBits");
        equal(actualV.xmm4().highBits(), expectedV.xmm4().highBits(), "xmm4.highBits");
        equal(actualV.xmm5().lowBits(), expectedV.xmm5().lowBits(), "xmm5.lowBits");
        equal(actualV.xmm5().highBits(), expectedV.xmm5().highBits(), "xmm5.highBits");
        GovernmentPrimaryTail155Api.NonvolatileBits actualN = actualEntry.nonvolatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits expectedN = expectedEntry.nonvolatileBits();
        equal(actualN.rbxBits(), expectedN.rbxBits(), "rbxBits");
        equal(actualN.rbpBits(), expectedN.rbpBits(), "rbpBits");
        equal(actualN.rsiBits(), expectedN.rsiBits(), "rsiBits");
        equal(actualN.rdiBits(), expectedN.rdiBits(), "rdiBits");
        equal(actualN.r12Bits(), expectedN.r12Bits(), "r12Bits");
        equal(actualN.r13Bits(), expectedN.r13Bits(), "r13Bits");
        equal(actualN.r14Bits(), expectedN.r14Bits(), "r14Bits");
        equal(actualN.r15Bits(), expectedN.r15Bits(), "r15Bits");
        equal(actualN.xmm6().lowBits(), expectedN.xmm6().lowBits(), "xmm6.lowBits");
        equal(actualN.xmm6().highBits(), expectedN.xmm6().highBits(), "xmm6.highBits");
        equal(snapshot.directionFlagSet(), c.expectedDf(), "directionFlagSet");
        equal(snapshot.mxcsr().valueBits(), c.expectedMxcsr().valueBits(), "mxcsr.valueBits");
        equal(snapshot.mxcsr().knownMaskBits(), c.expectedMxcsr().knownMaskBits(), "mxcsr.knownMaskBits");
        equal(snapshot.instructionRva(), c.expectedNextRva(), "instructionRva");
        equal(continued.relation(), c.expectedRelation(), "relation");
        require(actualV.xmm0().highBits() == 0 && (actualV.xmm0().lowBits() >>> 32) == 0, "xmm0 upper96 zero");
        require(actualV.xmm1().highBits() == 0 && (actualV.xmm1().lowBits() >>> 32) == 0, "xmm1 upper96 zero");
        require(memory.readCount() == startReads + 1, "one fresh DWORD read");
        Read read = memory.readAt(startReads);
        equal(read.address(), THRESHOLD_ADDRESS, "read address");
        equal(read.value(), c.thresholdBits(), "read value");
        require(c.budget().calls == 0, "no loop budget invocation");
    }

    public static void main(String[] arguments) {
        ThresholdMemory memory = new ThresholdMemory();
        int groups = 0;
        for (Case c : cases()) {
            runCase(c, memory);
            groups++;
        }
        require(groups == 4, "four finite literal cases completed");
        require(memory.readCount() == groups, "one actual threshold read per completed case");
        System.out.println("groups=" + groups + " RAM=" + memory.readCount() + " mixed=" + checks);
    }
}
