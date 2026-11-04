package org.xar.ck3.research.m3.manualprecision307;

import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.hashfpgate305.HashFpGate305;
import org.xar.ck3.research.m5.GovernmentCaller153Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Three independently frozen source-visible Precision prefixes; no hardware trap claim. */
public final class HashFpGatePrecision307 {
    private HashFpGatePrecision307() { }
    private static final long IMAGE = 0x00000001a0000000L;
    private static final long RSP = 0x0000000000b73008L;
    private static final long ORIGIN = 0xC39CCAL;
    private static int groups;
    private static int memoryOperations;
    private static int budgetCalls;

    public static void main(String[] args) {
        firstCvtdqPrecision();
        secondCvtdqPrecision();
        divisionPrecision();
        System.out.println("groups=" + groups + "|stopped=" + groups
                + "|memoryOperations=" + memoryOperations + "|budgetCalls=" + budgetCalls);
    }

    private static void firstCvtdqPrecision() {
        Fixture f = new Fixture("first_cvtdq_precision", 0x11L, 0x02000003L, true,
                new QueueFp604Api.Mxcsr(0x0004, 0x1005), 0xC39CF8L,
                new Bits128(0x02000003L, 0),
                new Bits128(0x1020304050607080L, 0x90a0b0c0d0e0f001L),
                new QueueFp604Api.Mxcsr(0x0024, 0x1025));
        report(f, runPrecisionCase(f));
    }

    private static void secondCvtdqPrecision() {
        Fixture f = new Fixture("second_cvtdq_precision", 0xfe000001L, 0xfffffff0L, false,
                new QueueFp604Api.Mxcsr(0x0010, 0x1012), 0xC39CFFL,
                new Bits128(0xc1800000L, 0), new Bits128(0xfe000001L, 0),
                new QueueFp604Api.Mxcsr(0x0030, 0x1032));
        report(f, runPrecisionCase(f));
    }

    private static void divisionPrecision() {
        Fixture f = new Fixture("division_precision", 2, 7, true,
                new QueueFp604Api.Mxcsr(0x0008, 0x1009), 0xC39D02L,
                new Bits128(0x40e00000L, 0), new Bits128(0x40000000L, 0),
                new QueueFp604Api.Mxcsr(0x0028, 0x1029));
        report(f, runPrecisionCase(f));
    }

    private static QueueFp604Api.Stopped runPrecisionCase(Fixture f) {
        var result = HashFpGate305.execute(f.input, f.memory);
        check(result instanceof HashFpGate305.NotCompleted, f.label + "|not NotCompleted");
        var stopped = ((HashFpGate305.NotCompleted) result).stopped();
        check(stopped.reason() == QueueFp604Api.StopReason.ARCHITECTURAL_FP_CONDITION, f.label + "|reason mismatch");
        check(stopped.raisedConditionBits() == 0x20, f.label + "|raisedConditionBits mismatch");
        check(stopped.originCallSiteRva() == ORIGIN, f.label + "|origin mismatch");
        check(stopped.snapshot().instructionRva() == f.expectedPc, f.label + "|PC mismatch");
        check(stopped.snapshot().currentState().equals(f.expectedEntry), f.label + "|entry mismatch");
        check(stopped.snapshot().directionFlagSet() == f.df, f.label + "|DF mismatch");
        check(stopped.snapshot().mxcsr().equals(f.expectedMxcsr), f.label + "|mxcsr mismatch");
        check((stopped.snapshot().mxcsr().knownMaskBits() & 0x6000) == 0, f.label + "|RC bits known");
        check(f.input.base().mxcsr().equals(f.before), f.label + "|input mxcsr mismatch");
        check(f.input.base().base().entry().equals(f.entry), f.label + "|input entry mismatch");
        check(f.memory.operations == 0, f.label + "|memory operations");
        check(f.budget.calls == 0, f.label + "|budget calls");
        return stopped;
    }

    private static void report(Fixture f, QueueFp604Api.Stopped actual) {
        groups++;
        memoryOperations += f.memory.operations;
        budgetCalls += f.budget.calls;
        System.out.println(f.label + "|pc=" + Long.toUnsignedString(actual.snapshot().instructionRva(), 16)
                + "|x0=" + Long.toUnsignedString(actual.snapshot().currentState().volatileBits().xmm0().lowBits(), 16)
                + "|x1=" + Long.toUnsignedString(actual.snapshot().currentState().volatileBits().xmm1().lowBits(), 16)
                + "|mxcsrValue=" + Integer.toHexString(actual.snapshot().mxcsr().valueBits())
                + "|mxcsrKnown=" + Integer.toHexString(actual.snapshot().mxcsr().knownMaskBits())
                + "|memoryOperations=" + f.memory.operations + "|budgetCalls=" + f.budget.calls);
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }

    private static final class Fixture {
        final String label;
        final boolean df;
        final QueueFp604Api.Mxcsr before;
        final QueueFp604Api.Mxcsr expectedMxcsr;
        final long expectedPc;
        final GovernmentCrtBoundary185Api.Entry entry;
        final GovernmentCrtBoundary185Api.Entry expectedEntry;
        final HashFpGate305.Input input;
        final NoMemory memory = new NoMemory();
        final NoBudget budget = new NoBudget();

        Fixture(String label, long rax, long rcx, boolean df, QueueFp604Api.Mxcsr before,
                long expectedPc, Bits128 expectedX0, Bits128 expectedX1,
                QueueFp604Api.Mxcsr expectedMxcsr) {
            this.label = label;
            this.df = df;
            this.before = before;
            this.expectedPc = expectedPc;
            this.expectedMxcsr = expectedMxcsr;
            VolatileBits v = new VolatileBits(rax, rcx, 0x33445566778899aaL,
                    0x0123456789abcdefL, 0xfedcba9876543210L,
                    0x8040201008040201L, 0xf1e2d3c4b5a69788L,
                    new Bits128(0x1122334455667788L, 0x99aabbccddeeff00L),
                    new Bits128(0x1020304050607080L, 0x90a0b0c0d0e0f001L),
                    new Bits128(0xff00ff00aa55aa55L, 0x123456789abcdef0L),
                    new Bits128(0x3141592653589793L, 0x2718281828459045L),
                    new Bits128(0x8000000000000001L, 0x7ffffffffffffffeL),
                    new Bits128(0xdeadbeefcafef00dL, 0x0123456789abcdefL));
            NonvolatileBits n = new NonvolatileBits(0x1111222233334444L,
                    0x550100L, 0x6666777788889901L, 0x44550000L,
                    0xa1a2a3a4a5a6a7a8L, 0xb1b2b3b4b5b6b7b8L, 0x7a0000L, 0x8b0000L,
                    new Bits128(0xc1c2c3c4c5c6c7c8L, 0xd1d2d3d4d5d6d7d8L));
            entry = new GovernmentCrtBoundary185Api.Entry(IMAGE, RSP, v, n);
            VolatileBits expectedV = new VolatileBits(v.raxBits(), v.rcxBits(), v.rdxBits(),
                    v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(), expectedX0, expectedX1,
                    v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
            expectedEntry = new GovernmentCrtBoundary185Api.Entry(IMAGE, RSP, expectedV, n);
            input = new HashFpGate305.Input(new QueueFp604Api.Input(
                    new FullCopy437Api.Input(entry, df, budget), before), ORIGIN);
        }
    }

    private static final class NoMemory implements GovernmentCaller153Api.Memory {
        int operations;
        private AssertionError deny(String method) {
            operations++;
            return new AssertionError("Unexpected Memory operation before Precision stop: " + method);
        }
        @Override public int readDword(long addressBits) { throw deny("readDword"); }
        @Override public long readQword(long addressBits) { throw deny("readQword"); }
        @Override public int readUnsignedByte(long addressBits) { throw deny("readUnsignedByte"); }
        @Override public void writeDword(long addressBits, int valueBits) { throw deny("writeDword"); }
        @Override public int lockedXaddDword(long addressBits, int addendBits) { throw deny("lockedXaddDword"); }
    }

    private static final class NoBudget implements GovernmentCrtBoundary185Api.LoopBudget {
        int calls;
        @Override public void beforeStep(long loopHeaderRva, long guardAddressBits) {
            calls++;
            throw new AssertionError("No source loop event in seven-instruction gate");
        }
    }
}
