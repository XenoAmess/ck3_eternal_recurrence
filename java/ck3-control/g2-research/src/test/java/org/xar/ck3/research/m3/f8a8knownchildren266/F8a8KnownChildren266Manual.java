package org.xar.ck3.research.m3.f8a8knownchildren266;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.f8a8fp263.F8a8Fp263Api;
import org.xar.ck3.research.m3.f8a8fp263.F8a8FullState263;
import org.xar.ck3.research.m3.f780fp264.F780Fp264Api;
import org.xar.ck3.research.m3.f780fp264.F780FromF8a8264;
import org.xar.ck3.research.m3.f800fp265.F800Fp265Api;
import org.xar.ck3.research.m3.f800fp265.F800FromF8a8265;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Finite single-TU whole266 manual; later software validation is recorded separately.
 * Owner oracle is candidate-visible/source-derived, explicitly not blind.
 * Existing263/264/265 subjects were read before the original-ASM oracle freeze.
 * D4/G8 values below are artificial public DATA: Native contents are NOT_HELD.
 * No new production wrapper, callee algorithm or Native qualification.
 */
public final class F8a8KnownChildren266Manual {
    private F8a8KnownChildren266Manual() { }

    public static void main(String[] args) {
        if (args.length != 0) throw new IllegalArgumentException("No arguments accepted");
        runNormal();
        runMiddleStopped();
    }

    private static void runNormal() {
        Fixture fixture = new Fixture(false);
        QueueFp604Api.Input input = fixture.input;
        FullCopy437Api.Memory memory = fixture.ram;
        GovernmentCrtBoundary185Api.LoopBudget budget = fixture.budget;
        F780Fp264Api.Calls calls264 = fixture.calls264;
        F800Fp265Api.Calls calls265 = fixture.calls265;
        F8a8Fp263Api.Calls foreignRootNeverCalled = fixture.foreignRootNeverCalled;

        // Bind existing265 into inner Calls (F8a8Fp263Api.Calls) for the F96A edge
        F8a8Fp263Api.Calls innerCalls = F800FromF8a8265.bind(memory, budget, calls265, foreignRootNeverCalled);

        // Bind existing264 into outer Calls (F8a8Fp263Api.Calls) for the F955 edge
        F8a8Fp263Api.Calls outerCalls = F780FromF8a8264.bind(memory, budget, calls264, innerCalls);

        // Invoke existing263 whole entry exactly once
        QueueFp604Api.Outcome outcome = F8a8FullState263.execute(input, memory, outerCalls);

        // Assert full represented result/identity
        Checks.equal(fixture.expectedNormal, outcome, "normal outcome");
        Checks.same(fixture.fpAfter5, ((QueueFp604Api.Normal) outcome).postMxcsr(), "post MXCSR identity");

        // Assert observed counts
        Checks.equal(2, fixture.calls264Count, "calls264Count");
        Checks.equal(3, fixture.calls265Count, "calls265Count");
        Checks.equal(fixture.expectedNormalOpaqueCalls, fixture.opaqueCallCount, "opaqueCallCount");
        Checks.equal(fixture.expectedAtomicCalls, fixture.ram.atomicCallCount(), "atomicCalls");
        Checks.equal(fixture.expectedForeignRootCalls, fixture.foreignRootCount, "foreignRootCount");
        Checks.equal(fixture.expectedBudgetCalls, fixture.budgetCalls, "budgetCalls");

        // Assert literal RAM trace and hash
        Checks.equal(fixture.expectedNormalTrace, fixture.ram.traceSnapshot(), "RAM trace");
        Checks.equal(fixture.expectedNormalRamSha256, fixture.ram.serializedSha256(), "RAM SHA256");
    }

    private static void runMiddleStopped() {
        Fixture fixture = new Fixture(true);
        GovernmentCrtBoundary185Api.LoopBudget budget = fixture.budget;
        FullCopy437Api.Memory memory = fixture.ram;
        QueueFp604Api.Input input = fixture.input;

        // Bind existing265 into inner Calls (F800Fp265Api.Calls) using fixture.offer265
        F800Fp265Api.Calls calls265 = fixture.calls265;

        // Bind existing264 into outer Calls (F780Fp264Api.Calls) using fixture.offer264
        F780Fp264Api.Calls calls264 = fixture.calls264;

        // Bind existing263 whole entry (F8a8Fp263Api.Calls) using fixture.foreignRootNeverCalled
        // This is the root caller for F8A8. The F8A8 body calls F780 (via 264) and F800 (via 265).
        // We need to compose the calls such that:
        // 1. F8A8 (263) invokes F780 (264) and F800 (265).
        // 2. F780 (264) invokes its opaque children (offer264).
        // 3. F800 (265) invokes its opaque children (offer265).

        // The F8a8FullState263.execute expects F8a8Fp263Api.Calls.
        // The F8a8Fp263Api.Calls.invoke receives a CallFrame for the calls made by F8A8.
        // F8A8 makes two calls: to F780 (site 424F955) and to F800 (site 424F96A).
        // We must route these to the respective FullState executors.

        F8a8Fp263Api.Calls inner = F800FromF8a8265.bind(memory, budget, calls265, fixture.foreignRootNeverCalled);
        F8a8Fp263Api.Calls calls263 = F780FromF8a8264.bind(memory, budget, calls264, inner);

        // Execute the whole F8A8 entry exactly once
        QueueFp604Api.Outcome result = F8a8FullState263.execute(input, memory, calls263);

        // Assert Stopped outcome
        if (!(result instanceof QueueFp604Api.Stopped)) {
            throw new AssertionError("Expected Stopped outcome, got " + result);
        }
        QueueFp604Api.Stopped stopped = (QueueFp604Api.Stopped) result;

        // Assert identity of the stopped outcome matches the fixture's expected stopped
        Checks.same(fixture.stopped, stopped, "stopped outcome identity");

        // Assert counts
        Checks.equal(2, fixture.calls264Count, "calls264Count");
        Checks.equal(2, fixture.calls265Count, "calls265Count");
        Checks.equal(4, fixture.opaqueCallCount, "opaqueCallCount");
        Checks.equal(0, fixture.foreignRootCount, "foreignRootCount");
        Checks.equal(0, fixture.budgetCalls, "budgetCalls");
        Checks.equal(1, fixture.ram.atomicCallCount(), "atomicCallCount");

        // Assert RAM trace
        List<String> actualTrace = fixture.ram.traceSnapshot();
        Checks.equal(fixture.expectedMiddleStoppedTrace, actualTrace, "RAM trace");

        // Assert RAM hash
        String actualHash = fixture.ram.serializedSha256();
        Checks.equal(fixture.expectedMiddleStoppedRamSha256, actualHash, "RAM hash");
    }

    /** Literal complete tuples, built from public immutable records, not subject constructors. */
    private record ExpectedFrame(GovernmentCrtBoundary185Api.Call original,
            GovernmentCrtBoundary185Api.Entry childEntry, boolean df,
            QueueFp604Api.Mxcsr fp, long returnRip) {
        void check(GovernmentCrtBoundary185Api.Call actualOriginal,
                GovernmentCrtBoundary185Api.Entry actualChild, boolean actualDf,
                QueueFp604Api.Mxcsr actualFp, long actualReturnRip) {
            Checks.equal(original, actualOriginal, "complete original185 Call");
            Checks.equal(childEntry, actualChild, "complete child185 Entry");
            Checks.equal(df, actualDf, "preDF");
            Checks.same(fp, actualFp, "partial preMXCSR object");
            Checks.equal(returnRip, actualReturnRip, "owned return RIP");
        }
    }

    private static final class Checks {
        private Checks() { }
        static void equal(Object expected, Object actual, String label) {
            if (!Objects.equals(expected, actual)) {
                throw new AssertionError(label + ": expected " + expected + ", actual " + actual);
            }
        }
        static void same(Object expected, Object actual, String label) {
            if (expected != actual) throw new AssertionError(label + ": identity differs");
        }
    }

    /** Explicit supplied DATA and offer ports only; no SUT execute/binder composition here. */
    private static final class Fixture {
        final boolean middleStopped;
        int calls264Count = 0;
        int calls265Count = 0;
        int opaqueCallCount = 0;
        int foreignRootCount = 0;
        int budgetCalls = 0;
        final QueueFp604Api.Mxcsr fpEntry = new QueueFp604Api.Mxcsr(0x0001, 0x0003);
        final QueueFp604Api.Mxcsr fpAfter1 = new QueueFp604Api.Mxcsr(0x0020, 0x0021);
        final QueueFp604Api.Mxcsr fpAfter2 = new QueueFp604Api.Mxcsr(0x0102, 0x0103);
        final QueueFp604Api.Mxcsr fpAfter3 = new QueueFp604Api.Mxcsr(0x0201, 0x0203);
        final QueueFp604Api.Mxcsr fpAfter4 = new QueueFp604Api.Mxcsr(0x0404, 0x0405);
        final QueueFp604Api.Mxcsr fpAfter5 = new QueueFp604Api.Mxcsr(0x0802, 0x0803);
        final QueueFp604Api.Mxcsr fpStopped = new QueueFp604Api.Mxcsr(0x0010, 0x0030);
        final GovernmentPrimaryTail155Api.VolatileBits entryV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x8401314253647586L, 0x000000000000A000L, 0x8403314253647586L, 0x8404314253647586L, 0x8405314253647586L, 0x8406314253647586L, 0x8407314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0x8430314253647586L, 0x8431314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8432314253647586L, 0x8433314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8434314253647586L, 0x8435314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8436314253647586L, 0x8437314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8438314253647586L, 0x8439314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x843A314253647586L, 0x843B314253647586L));
        final GovernmentPrimaryTail155Api.NonvolatileBits entryN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x1021324354657687L, 0x2132435465768798L, 0x32435465768798A9L, 0x435465768798A9BAL, 0x5465768798A9BACBL, 0x65768798A9BACBDCL, 0x768798A9BACBDCEDL, 0x8798A9BACBDCEDFEL,
                new GovernmentPrimaryTail155Api.Bits128(0x98A9BACBDCEDFE0FL, 0xA9BACBDCEDFE0F10L));
        final GovernmentPrimaryTail155Api.NonvolatileBits outerN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x1021324354657687L, 0x0000000000008000L, 0x32435465768798A9L, 0x435465768798A9BAL, 0x5465768798A9BACBL, 0x65768798A9BACBDCL, 0x768798A9BACBDCEDL, 0x8798A9BACBDCEDFEL,
                new GovernmentPrimaryTail155Api.Bits128(0x98A9BACBDCEDFE0FL, 0xA9BACBDCEDFE0F10L));
        final GovernmentPrimaryTail155Api.NonvolatileBits child264N = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x0000000000008020L, 0x0000000000008000L, 0x32435465768798A9L, 0x0000000000007FE8L, 0x5465768798A9BACBL, 0x65768798A9BACBDCL, 0x768798A9BACBDCEDL, 0x8798A9BACBDCEDFEL,
                new GovernmentPrimaryTail155Api.Bits128(0x98A9BACBDCEDFE0FL, 0xA9BACBDCEDFE0F10L));
        final GovernmentPrimaryTail155Api.NonvolatileBits child265N = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x0000000000007FD0L, 0x0000000000008000L, 0x32435465768798A9L, 0x0000000000007FF0L, 0x5465768798A9BACBL, 0x65768798A9BACBDCL, 0x768798A9BACBDCEDL, 0x8798A9BACBDCEDFEL,
                new GovernmentPrimaryTail155Api.Bits128(0x98A9BACBDCEDFE0FL, 0xA9BACBDCEDFE0F10L));
        final GovernmentPrimaryTail155Api.NonvolatileBits finalN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x1021324354657687L, 0xE1F2031425364758L, 0x32435465768798A9L, 0x435465768798A9BAL, 0x5465768798A9BACBL, 0x65768798A9BACBDCL, 0x768798A9BACBDCEDL, 0x8798A9BACBDCEDFEL,
                new GovernmentPrimaryTail155Api.Bits128(0x98A9BACBDCEDFE0FL, 0xA9BACBDCEDFE0F10L));
        final GovernmentPrimaryTail155Api.VolatileBits outerV1 = new GovernmentPrimaryTail155Api.VolatileBits(
                0x000000000000A000L, 0x0000000000008018L, 0x0000000000008028L, 0x0000000000007FE8L, 0x0000000000008020L, 0x8406314253647586L, 0x8407314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0x8430314253647586L, 0x8431314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8432314253647586L, 0x8433314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8434314253647586L, 0x8435314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8436314253647586L, 0x8437314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8438314253647586L, 0x8439314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x843A314253647586L, 0x843B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits outerV2 = new GovernmentPrimaryTail155Api.VolatileBits(
                0xA801314253647586L, 0x0000000000008018L, 0x0000000000007FD4L, 0x0000000000007FF0L, 0x0000000000007FD0L, 0xA806314253647586L, 0xA807314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0xA830314253647586L, 0xA831314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA832314253647586L, 0xA833314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA834314253647586L, 0xA835314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA836314253647586L, 0xA837314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA838314253647586L, 0xA839314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA83A314253647586L, 0xA83B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits opaqueV1 = new GovernmentPrimaryTail155Api.VolatileBits(
                0x000000000000A000L, 0x0000000000000005L, 0x0000000000008028L, 0x0000000000007FE8L, 0x0000000000008020L, 0x8406314253647586L, 0x8407314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0x8430314253647586L, 0x8431314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8432314253647586L, 0x8433314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8434314253647586L, 0x8435314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8436314253647586L, 0x8437314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x8438314253647586L, 0x8439314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x843A314253647586L, 0x843B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits opaqueV2 = new GovernmentPrimaryTail155Api.VolatileBits(
                0x00000001C542F770L, 0x00000000B13579DFL, 0x9603314253647586L, 0x9604314253647586L, 0x9605314253647586L, 0x9606314253647586L, 0x9607314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0x9630314253647586L, 0x9631314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x9632314253647586L, 0x9633314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x9634314253647586L, 0x9635314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x9636314253647586L, 0x9637314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x9638314253647586L, 0x9639314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x963A314253647586L, 0x963B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits opaqueV3 = new GovernmentPrimaryTail155Api.VolatileBits(
                0xA801314253647586L, 0x0000000000000004L, 0x0000000000007FD4L, 0x0000000000007FF0L, 0x0000000000007FD0L, 0xA806314253647586L, 0xA807314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0xA830314253647586L, 0xA831314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA832314253647586L, 0xA833314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA834314253647586L, 0xA835314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA836314253647586L, 0xA837314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA838314253647586L, 0xA839314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA83A314253647586L, 0xA83B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits opaqueV4 = new GovernmentPrimaryTail155Api.VolatileBits(
                0x0000000000007FE0L, 0x000000000000A000L, 0xBADC0FFEE0112233L, 0xBA04314253647586L, 0xBA05314253647586L, 0xBA06314253647586L, 0xBA07314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0xBA30314253647586L, 0xBA31314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA32314253647586L, 0xBA33314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA34314253647586L, 0xBA35314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA36314253647586L, 0xBA37314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA38314253647586L, 0xBA39314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA3A314253647586L, 0xBA3B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits opaqueV5 = new GovernmentPrimaryTail155Api.VolatileBits(
                0xCC01314253647586L, 0x00000000CAFE0123L, 0xCC03314253647586L, 0xCC04314253647586L, 0xCC05314253647586L, 0xCC06314253647586L, 0xCC07314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0xCC30314253647586L, 0xCC31314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC32314253647586L, 0xCC33314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC34314253647586L, 0xCC35314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC36314253647586L, 0xCC37314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC38314253647586L, 0xCC39314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC3A314253647586L, 0xCC3B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits postV1 = new GovernmentPrimaryTail155Api.VolatileBits(
                0x9601314253647586L, 0x9602314253647586L, 0x9603314253647586L, 0x9604314253647586L, 0x9605314253647586L, 0x9606314253647586L, 0x9607314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0x9630314253647586L, 0x9631314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x9632314253647586L, 0x9633314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x9634314253647586L, 0x9635314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x9636314253647586L, 0x9637314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x9638314253647586L, 0x9639314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0x963A314253647586L, 0x963B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits postV2 = new GovernmentPrimaryTail155Api.VolatileBits(
                0xA801314253647586L, 0xA802314253647586L, 0xA803314253647586L, 0xA804314253647586L, 0xA805314253647586L, 0xA806314253647586L, 0xA807314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0xA830314253647586L, 0xA831314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA832314253647586L, 0xA833314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA834314253647586L, 0xA835314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA836314253647586L, 0xA837314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA838314253647586L, 0xA839314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xA83A314253647586L, 0xA83B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits postV3 = new GovernmentPrimaryTail155Api.VolatileBits(
                0xBA01314253647586L, 0xBA02314253647586L, 0xBA03314253647586L, 0xBA04314253647586L, 0xBA05314253647586L, 0xBA06314253647586L, 0xBA07314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0xBA30314253647586L, 0xBA31314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA32314253647586L, 0xBA33314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA34314253647586L, 0xBA35314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA36314253647586L, 0xBA37314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA38314253647586L, 0xBA39314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xBA3A314253647586L, 0xBA3B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits postV4 = new GovernmentPrimaryTail155Api.VolatileBits(
                0xCC01314253647586L, 0xCC02314253647586L, 0xCC03314253647586L, 0xCC04314253647586L, 0xCC05314253647586L, 0xCC06314253647586L, 0xCC07314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0xCC30314253647586L, 0xCC31314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC32314253647586L, 0xCC33314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC34314253647586L, 0xCC35314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC36314253647586L, 0xCC37314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC38314253647586L, 0xCC39314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xCC3A314253647586L, 0xCC3B314253647586L));
        final GovernmentPrimaryTail155Api.VolatileBits postV5 = new GovernmentPrimaryTail155Api.VolatileBits(
                0xDE01314253647586L, 0xDE02314253647586L, 0xDE03314253647586L, 0xDE04314253647586L, 0xDE05314253647586L, 0xDE06314253647586L, 0xDE07314253647586L,
                new GovernmentPrimaryTail155Api.Bits128(0xDE30314253647586L, 0xDE31314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xDE32314253647586L, 0xDE33314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xDE34314253647586L, 0xDE35314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xDE36314253647586L, 0xDE37314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xDE38314253647586L, 0xDE39314253647586L),
                new GovernmentPrimaryTail155Api.Bits128(0xDE3A314253647586L, 0xDE3B314253647586L));
        final GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(0x00000001C0000000L, 0x0000000000008008L, entryV, entryN);
        final ExpectedFrame outerF955 = new ExpectedFrame(
                new GovernmentCrtBoundary185Api.Call(0x000000000424F955L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                        0x000000000424F780L, 0x0000000000007FB0L, outerV1, outerN),
                new GovernmentCrtBoundary185Api.Entry(0x00000001C0000000L, 0x0000000000007FA8L, outerV1, outerN), true, fpEntry, 0x00000001C424F95AL);
        final ExpectedFrame outerF96A = new ExpectedFrame(
                new GovernmentCrtBoundary185Api.Call(0x000000000424F96AL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                        0x000000000424F800L, 0x0000000000007FB0L, outerV2, outerN),
                new GovernmentCrtBoundary185Api.Entry(0x00000001C0000000L, 0x0000000000007FA8L, outerV2, outerN), true, fpAfter2, 0x00000001C424F96FL);
        final ExpectedFrame opaque1 = new ExpectedFrame(
                new GovernmentCrtBoundary185Api.Call(0x000000000424F797L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                        0x0000000004247FFCL, 0x0000000000007F80L, opaqueV1, child264N),
                new GovernmentCrtBoundary185Api.Entry(0x00000001C0000000L, 0x0000000000007F78L, opaqueV1, child264N), true, fpEntry, 0x00000001C424F79CL);
        final ExpectedFrame opaque2 = new ExpectedFrame(
                new GovernmentCrtBoundary185Api.Call(0x000000000424F7AFL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                        0x0000000004248050L, 0x0000000000007F80L, opaqueV2, child264N),
                new GovernmentCrtBoundary185Api.Entry(0x00000001C0000000L, 0x0000000000007F78L, opaqueV2, child264N), false, fpAfter1, 0x00000001C424F7B4L);
        final ExpectedFrame opaque3 = new ExpectedFrame(
                new GovernmentCrtBoundary185Api.Call(0x000000000424F817L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                        0x0000000004247FFCL, 0x0000000000007F80L, opaqueV3, child265N),
                new GovernmentCrtBoundary185Api.Entry(0x00000001C0000000L, 0x0000000000007F78L, opaqueV3, child265N), true, fpAfter2, 0x00000001C424F81CL);
        final ExpectedFrame opaque4 = new ExpectedFrame(
                new GovernmentCrtBoundary185Api.Call(0x000000000424F82DL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                        0x000000000424FA90L, 0x0000000000007F80L, opaqueV4, child265N),
                new GovernmentCrtBoundary185Api.Entry(0x00000001C0000000L, 0x0000000000007F78L, opaqueV4, child265N), false, fpAfter3, 0x00000001C424F832L);
        final ExpectedFrame opaque5 = new ExpectedFrame(
                new GovernmentCrtBoundary185Api.Call(0x000000000424F835L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                        0x0000000004248050L, 0x0000000000007F80L, opaqueV5, child265N),
                new GovernmentCrtBoundary185Api.Entry(0x00000001C0000000L, 0x0000000000007F78L, opaqueV5, child265N), true, fpAfter4, 0x00000001C424F83AL);
        final QueueFp604Api.Normal normal1 = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postV1, 0x00000001C424F79CL, 0x0000000000007F80L, child264N),
                false), fpAfter1);
        final QueueFp604Api.Normal normal2 = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postV2, 0x00000001C424F7B4L, 0x0000000000007F80L, child264N),
                true), fpAfter2);
        final QueueFp604Api.Normal normal3 = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postV3, 0x00000001C424F81CL, 0x0000000000007F80L, child265N),
                false), fpAfter3);
        final QueueFp604Api.Normal normal4 = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postV4, 0x00000001C424F832L, 0x0000000000007F80L, child265N),
                true), fpAfter4);
        final QueueFp604Api.Normal normal5 = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postV5, 0x00000001C424F83AL, 0x0000000000007F80L, child265N),
                false), fpAfter5);
        final QueueFp604Api.Normal derivedChild264Normal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postV2, 0x00000001C424F95AL, 0x0000000000007FB0L, outerN),
                true), fpAfter2);
        final QueueFp604Api.Normal derivedChild265Normal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postV5, 0x00000001C424F96FL, 0x0000000000007FB0L, outerN),
                false), fpAfter5);
        final QueueFp604Api.Normal expectedNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postV5, 0x00000001C0765432L, 0x0000000000008010L, finalN),
                false), fpAfter5);
        final QueueFp604Api.Stopped stopped = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(opaque4.childEntry(), 0x000000000424FA90L, true, fpStopped),
                0, 0x000000000424F82DL);
        final List<String> expectedNormalTrace = List.of(
                "W64@8000=2132435465768798",
                "W64@7fd8=a000",
                "W64@7fe8=7fd8",
                "W32@8020=5",
                "W32@8028=5",
                "W64@7ff0=7fd8",
                "W64@7ff8=7fe0",
                "W32@7fd0=4",
                "W32@7fd4=4",
                "W64@7fe0=1c5c5dcd8",
                "W32@a028=1",
                "R64@7fd8=a000",
                "W64@a000=1c44267f0",
                "R64@7fd8=a000",
                "W32@a3a8=1",
                "R64@7fd8=a000",
                "W64@a088=1c542f770",
                "R64@7fd8=a000",
                "W16@a0bc=43",
                "R64@7fd8=a000",
                "W16@a1c2=43",
                "R64@7fd8=a000",
                "R64@a3a0=c0dec0de11223344",
                "W64@a3a0=0",
                "W64@7fa8=1c424f95a",
                "W64@7fb0=1021324354657687",
                "W64@7fc8=8020",
                "W64@7fa0=435465768798a9ba",
                "R32@8028=5",
                "W64@7f78=1c424f79c",
                "W32@8020=b13579df",
                "R64@7fe8=7fd8",
                "R64@7fd8=a000",
                "R64@a088=1c542f770",
                "A32@1c542f770=1/7ffffffe/7fffffff",
                "R32@8020=b13579df",
                "W64@7f78=1c424f7b4",
                "W64@7fc8=f00dcafe98765432",
                "R64@7fb0=1021324354657687",
                "R64@7fa0=435465768798a9ba",
                "R64@7fa8=1c424f95a",
                "W64@7fa8=1c424f96f",
                "W64@7fb0=1021324354657687",
                "W64@7fc8=7fd0",
                "W64@7fa0=435465768798a9ba",
                "R32@7fd4=4",
                "W64@7f78=1c424f81c",
                "W64@1c5c5dcd8=badc0ffee0112233",
                "R64@7ff8=7fe0",
                "R64@7fe0=1c5c5dcd8",
                "R64@7ff0=7fd8",
                "R64@1c5c5dcd8=badc0ffee0112233",
                "R64@7fd8=a000",
                "W64@7f78=1c424f832",
                "W32@7fd0=cafe0123",
                "R32@7fd0=cafe0123",
                "W64@7f78=1c424f83a",
                "W64@8000=e1f2031425364758",
                "W64@8008=1c0765432",
                "R64@7fb0=1021324354657687",
                "R64@7fa0=435465768798a9ba",
                "R64@7fa8=1c424f96f",
                "R64@8000=e1f2031425364758",
                "R64@8008=1c0765432");
        final List<String> expectedMiddleStoppedTrace = List.of(
                "W64@8000=2132435465768798",
                "W64@7fd8=a000",
                "W64@7fe8=7fd8",
                "W32@8020=5",
                "W32@8028=5",
                "W64@7ff0=7fd8",
                "W64@7ff8=7fe0",
                "W32@7fd0=4",
                "W32@7fd4=4",
                "W64@7fe0=1c5c5dcd8",
                "W32@a028=1",
                "R64@7fd8=a000",
                "W64@a000=1c44267f0",
                "R64@7fd8=a000",
                "W32@a3a8=1",
                "R64@7fd8=a000",
                "W64@a088=1c542f770",
                "R64@7fd8=a000",
                "W16@a0bc=43",
                "R64@7fd8=a000",
                "W16@a1c2=43",
                "R64@7fd8=a000",
                "R64@a3a0=c0dec0de11223344",
                "W64@a3a0=0",
                "W64@7fa8=1c424f95a",
                "W64@7fb0=1021324354657687",
                "W64@7fc8=8020",
                "W64@7fa0=435465768798a9ba",
                "R32@8028=5",
                "W64@7f78=1c424f79c",
                "W32@8020=b13579df",
                "R64@7fe8=7fd8",
                "R64@7fd8=a000",
                "R64@a088=1c542f770",
                "A32@1c542f770=1/7ffffffe/7fffffff",
                "R32@8020=b13579df",
                "W64@7f78=1c424f7b4",
                "W64@7fc8=f00dcafe98765432",
                "R64@7fb0=1021324354657687",
                "R64@7fa0=435465768798a9ba",
                "R64@7fa8=1c424f95a",
                "W64@7fa8=1c424f96f",
                "W64@7fb0=1021324354657687",
                "W64@7fc8=7fd0",
                "W64@7fa0=435465768798a9ba",
                "R32@7fd4=4",
                "W64@7f78=1c424f81c",
                "W64@1c5c5dcd8=badc0ffee0112233",
                "R64@7ff8=7fe0",
                "R64@7fe0=1c5c5dcd8",
                "R64@7ff0=7fd8",
                "R64@1c5c5dcd8=badc0ffee0112233",
                "R64@7fd8=a000",
                "W64@7f78=1c424f832");
        final String expectedNormalRamSha256 = "f43ce56586fd7ebd516d08b01f8eb7f7dc9f9034c8242a141f1473d9b3f72c33";
        final String expectedMiddleStoppedRamSha256 = "9cb3c15d4dc052e0a2e63f407dc0472265c109b28676376dd985b3c57a384eaf";
        final int expectedNormalOpaqueCalls = 5;
        final int expectedStoppedOpaqueCalls = 4;
        final int expectedAtomicCalls = 1;
        final int expectedForeignRootCalls = 0;
        final int expectedBudgetCalls = 0;
        final SparseRam ram = new SparseRam();
        final GovernmentCrtBoundary185Api.LoopBudget budget = (header, guard) -> {
            budgetCalls++;
            throw new AssertionError("Original straight-line bodies used budget");
        };
        final QueueFp604Api.Input input = new QueueFp604Api.Input(
                new FullCopy437Api.Input(entry, true, budget), fpEntry);
        final F780Fp264Api.Calls calls264 = this::offer264;
        final F800Fp265Api.Calls calls265 = this::offer265;
        final F8a8Fp263Api.Calls foreignRootNeverCalled = frame -> {
            foreignRootCount++;
            throw new AssertionError("Unexpected root foreign frame: " + frame);
        };

        Fixture(boolean middleStopped) {
            this.middleStopped = middleStopped;
            ram.seed(0x0000000000008008L, 8, 0x00000001C0112233L);
            ram.seed(0x000000000000A3A0L, 8, 0xC0DEC0DE11223344L);
        }

        private QueueFp604Api.Outcome offer264(F780Fp264Api.CallFrame actual) {
            int ordinal = ++calls264Count;
            if (ordinal == 1) {
                Checks.equal(1, ++opaqueCallCount, "global opaque ordinal");
                opaque1.check(actual.original(), actual.childEntry(),
                        actual.directionFlagSet(), actual.preMxcsr(), actual.returnRipBits());
                ram.writeDword(0x0000000000008020L, 0xB13579DF);
                return normal1;
            }
            if (ordinal == 2) {
                Checks.equal(2, ++opaqueCallCount, "global opaque ordinal");
                opaque2.check(actual.original(), actual.childEntry(),
                        actual.directionFlagSet(), actual.preMxcsr(), actual.returnRipBits());
                ram.writeQword(0x0000000000007FC8L, 0xF00DCAFE98765432L);
                return normal2;
            }
            throw new AssertionError("Unexpected264 offer ordinal " + ordinal);
        }

        private QueueFp604Api.Outcome offer265(F800Fp265Api.CallFrame actual) {
            int ordinal = ++calls265Count;
            if (ordinal == 1) {
                Checks.equal(3, ++opaqueCallCount, "global opaque ordinal");
                opaque3.check(actual.original(), actual.childEntry(),
                        actual.directionFlagSet(), actual.preMxcsr(), actual.returnRipBits());
                ram.writeQword(0x00000001C5C5DCD8L, 0xBADC0FFEE0112233L);
                return normal3;
            }
            if (ordinal == 2) {
                Checks.equal(4, ++opaqueCallCount, "global opaque ordinal");
                opaque4.check(actual.original(), actual.childEntry(),
                        actual.directionFlagSet(), actual.preMxcsr(), actual.returnRipBits());
                if (middleStopped) return stopped;
                ram.writeDword(0x0000000000007FD0L, 0xCAFE0123);
                return normal4;
            }
            if (ordinal == 3 && !middleStopped) {
                Checks.equal(5, ++opaqueCallCount, "global opaque ordinal");
                opaque5.check(actual.original(), actual.childEntry(),
                        actual.directionFlagSet(), actual.preMxcsr(), actual.returnRipBits());
                ram.writeQword(0x0000000000008000L, 0xE1F2031425364758L);
                ram.writeQword(0x0000000000008008L, 0x00000001C0765432L);
                return normal5;
            }
            throw new AssertionError("Unexpected265 offer ordinal " + ordinal);
        }
    }

    /**
     * One finite sparse storage object: low stack/heap then D4 then G8.
     * Every high-region byte is explicitly artificial seed DATA. No Native contents.
     * Vector/NT/fence effects are host tokens only, with no CPU/alignment proof.
     */
    private static final class SparseRam implements FullCopy437Api.Memory {
        private static final long LOW_BASE = 0x6000L;
        private static final int LOW_LENGTH = 0x6000;
        private static final long DERIVED_ATOMIC = 0x00000001C542F770L;
        private static final long GLOBAL = 0x00000001C5C5DCD8L;
        private final byte[] bytes = new byte[0x600C];
        private final List<String> trace = new ArrayList<>();
        private int atomicCalls = 0;

        SparseRam() {
            for (int i = 0; i < LOW_LENGTH; i++) bytes[i] = (byte) (i * 17 + 0x59);
            seed(DERIVED_ATOMIC, 4, 0x7FFFFFFEL); // Artificial DATA; Native contents NOT_HELD.
            seed(GLOBAL, 8, 0x0123456789ABCDEFL); // Artificial DATA; Native contents NOT_HELD.
        }

        private int index(long address, int width) {
            if (width < 1) throw new UnsupportedOperationException("Invalid exact width");
            if (address >= LOW_BASE && address - LOW_BASE <= LOW_LENGTH - width) {
                return (int) (address - LOW_BASE);
            }
            if (address >= DERIVED_ATOMIC && address - DERIVED_ATOMIC <= 4L - width) {
                return LOW_LENGTH + (int) (address - DERIVED_ATOMIC);
            }
            if (address >= GLOBAL && address - GLOBAL <= 8L - width) {
                return LOW_LENGTH + 4 + (int) (address - GLOBAL);
            }
            throw new UnsupportedOperationException("Address outside finite sparse RAM");
        }

        private long loadRaw(long address, int width) {
            int start = index(address, width);
            if (width > 8) throw new UnsupportedOperationException("Scalar width exceeds8");
            long value = 0;
            for (int i = 0; i < width; i++) value |= (bytes[start + i] & 0xFFL) << (8 * i);
            return value;
        }

        private void storeRaw(long address, int width, long value) {
            int start = index(address, width);
            if (width > 8) throw new UnsupportedOperationException("Scalar width exceeds8");
            for (int i = 0; i < width; i++) bytes[start + i] = (byte) (value >>> (8 * i));
        }

        void seed(long address, int width, long value) {
            storeRaw(address, width, value);
        }

        private void scalarEffect(String op, long address, long value) {
            trace.add(op + "@" + Long.toUnsignedString(address, 16)
                    + "=" + Long.toUnsignedString(value, 16));
        }

        private GovernmentPrimaryTail155Api.Bits128 load128Raw(long address) {
            index(address, 16);
            return new GovernmentPrimaryTail155Api.Bits128(
                    loadRaw(address, 8), loadRaw(address + 8L, 8));
        }

        private void store128Raw(long address, GovernmentPrimaryTail155Api.Bits128 value) {
            Objects.requireNonNull(value);
            index(address, 16);
            storeRaw(address, 8, value.lowBits());
            storeRaw(address + 8L, 8, value.highBits());
        }

        private String bits128(GovernmentPrimaryTail155Api.Bits128 value) {
            return Long.toUnsignedString(value.lowBits(), 16) + "/"
                    + Long.toUnsignedString(value.highBits(), 16);
        }

        List<String> traceSnapshot() { return List.copyOf(trace); }
        int atomicCallCount() { return atomicCalls; }
        byte[] serializedSnapshot() { return bytes.clone(); }
        String serializedSha256() {
            try {
                return HexFormat.of().formatHex(
                        MessageDigest.getInstance("SHA-256").digest(bytes));
            } catch (NoSuchAlgorithmException unavailable) {
                throw new AssertionError(unavailable);
            }
        }

        @Override public int readUnsignedByte(long address) {
            int value = (int) loadRaw(address, 1);
            scalarEffect("R8", address, value);
            return value;
        }
        @Override public int readUnsignedWord(long address) {
            int value = (int) loadRaw(address, 2);
            scalarEffect("R16", address, value);
            return value;
        }
        @Override public int readDword(long address) {
            int value = (int) loadRaw(address, 4);
            scalarEffect("R32", address, Integer.toUnsignedLong(value));
            return value;
        }
        @Override public long readQword(long address) {
            long value = loadRaw(address, 8);
            scalarEffect("R64", address, value);
            return value;
        }
        @Override public void writeByte(long address, int value) {
            storeRaw(address, 1, value & 0xFFL);
            scalarEffect("W8", address, value & 0xFFL);
        }
        @Override public void writeWord(long address, int value) {
            storeRaw(address, 2, value & 0xFFFFL);
            scalarEffect("W16", address, value & 0xFFFFL);
        }
        @Override public void writeDword(long address, int value) {
            storeRaw(address, 4, Integer.toUnsignedLong(value));
            scalarEffect("W32", address, Integer.toUnsignedLong(value));
        }
        @Override public void writeQword(long address, long value) {
            storeRaw(address, 8, value);
            scalarEffect("W64", address, value);
        }
        @Override public synchronized int lockedXaddDword(long address, int addend) {
            int old = (int) loadRaw(address, 4);
            int next = old + addend;
            storeRaw(address, 4, Integer.toUnsignedLong(next));
            atomicCalls++;
            trace.add("A32@" + Long.toUnsignedString(address, 16) + "="
                    + Integer.toUnsignedString(addend, 16) + "/"
                    + Integer.toUnsignedString(old, 16) + "/"
                    + Integer.toUnsignedString(next, 16));
            return old;
        }
        @Override public GovernmentPrimaryTail155Api.Bits128 read128(long address) {
            GovernmentPrimaryTail155Api.Bits128 value = load128Raw(address);
            trace.add("R128@" + Long.toUnsignedString(address, 16) + "=" + bits128(value));
            return value;
        }
        @Override public void write128(long address, GovernmentPrimaryTail155Api.Bits128 value) {
            store128Raw(address, value);
            trace.add("W128@" + Long.toUnsignedString(address, 16) + "=" + bits128(value));
        }
        @Override public void write128NonTemporal(long address, GovernmentPrimaryTail155Api.Bits128 value) {
            store128Raw(address, value);
            trace.add("W128_NT@" + Long.toUnsignedString(address, 16) + "=" + bits128(value));
        }
        @Override public FullCopy437Api.Bits256 read256(long address) {
            index(address, 32);
            FullCopy437Api.Bits256 value = new FullCopy437Api.Bits256(
                    load128Raw(address), load128Raw(address + 16L));
            trace.add("R256@" + Long.toUnsignedString(address, 16) + "="
                    + bits128(value.low()) + "/" + bits128(value.high()));
            return value;
        }
        @Override public void write256(long address, FullCopy437Api.Bits256 value) {
            Objects.requireNonNull(value);
            index(address, 32);
            store128Raw(address, value.low());
            store128Raw(address + 16L, value.high());
            trace.add("W256@" + Long.toUnsignedString(address, 16) + "="
                    + bits128(value.low()) + "/" + bits128(value.high()));
        }
        @Override public void write256NonTemporal(long address, FullCopy437Api.Bits256 value) {
            Objects.requireNonNull(value);
            index(address, 32);
            store128Raw(address, value.low());
            store128Raw(address + 16L, value.high());
            trace.add("W256_NT@" + Long.toUnsignedString(address, 16) + "="
                    + bits128(value.low()) + "/" + bits128(value.high()));
        }
        @Override public void sfence() { trace.add("SFENCE"); }
    }
}
