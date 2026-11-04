package org.xar.ck3.research.m3.hashfpgateboundary308.manual;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.hashfpgate305.HashFpGate305;
import org.xar.ck3.research.m5.GovernmentCaller153Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Four finite knowledge/unsupported/ordinary-read software boundaries.
 * No hardware/OS fault or fullHash claim; no internal register observation at an exception.
 */
public final class HashFpGateBoundary308 {
    private HashFpGateBoundary308() { }

    private enum Scene { MISSING_PM_CF8, MISSING_RC_CFF, READ_FAILURE_D06, NAN_UNSUPPORTED_D06 }

    public static void main(String[] ignored) {
        for (Scene scene : Scene.values()) run(scene);
        System.out.println("HashFpGateBoundary308: 4 cases passed");
    }

    private static void run(Scene scene) {
        // All public DATA and sentinel construction is outside the execute catch.
        Fixture f = new Fixture(scene);
        if (scene == Scene.READ_FAILURE_D06) {
            RuntimeException caught = null;
            try {
                f.entries++;
                HashFpGate305.execute(f.input, f.ram);
            } catch (RuntimeException ordinary) {
                caught = ordinary;
            }
            require(caught == f.ram.failure, "same ordinary Memory exception");
            // Public API exposes no internal register bank on this exceptional path.
        } else {
            f.entries++;
            HashFpGate305.Result actual = HashFpGate305.execute(f.input, f.ram);
            assertStopped(f, actual);
        }
        assertMemoryPrefix(f);
    }

    // Exact model assertion method; owner fixture and literal expectations unchanged.
    private static void assertStopped(Fixture f, HashFpGate305.Result actual) {
        require(actual instanceof HashFpGate305.NotCompleted, "NotCompleted expected");
        HashFpGate305.NotCompleted notCompleted = (HashFpGate305.NotCompleted) actual;
        QueueFp604Api.Stopped stopped = notCompleted.stopped();
        require(stopped.reason() == f.expectedReason, "reason mismatch");
        require(stopped.raisedConditionBits() == 0, "raisedConditionBits mismatch");
        require(stopped.originCallSiteRva() == 0xfedcba9876543210L, "originCallSiteRva mismatch");
        QueueFp604Api.Snapshot snapshot = stopped.snapshot();
        require(snapshot.instructionRva() == f.expectedPC, "instructionRva mismatch");
        require(snapshot.currentState().equals(f.expectedEntry), "currentState mismatch");
        require(snapshot.directionFlagSet(), "directionFlagSet mismatch");
        require(snapshot.mxcsr().equals(f.fp), "mxcsr mismatch");
    }

    private static final class Fixture {
        private final Scene scene;
        private final Ram ram;
        private final QueueFp604Api.Mxcsr fp;
        private int entries, budgetCalls;
        private final GovernmentCrtBoundary185Api.LoopBudget budget = (header, guard) -> {
            budgetCalls++;
            throw new AssertionError("gate has no loop");
        };
        private final HashFpGate305.Input input;
        private final GovernmentCrtBoundary185Api.Entry expectedEntry;
        private final QueueFp604Api.StopReason expectedReason;
        private final long expectedPC;

        private Fixture(Scene scene) {
            this.scene = scene;
            ram = new Ram(scene);
            fp = switch (scene) {
                case MISSING_PM_CF8 -> new QueueFp604Api.Mxcsr(0x40, 0x6040);
                case MISSING_RC_CFF -> new QueueFp604Api.Mxcsr(0x1040, 0x1040);
                default -> new QueueFp604Api.Mxcsr(0x40, 0x40);
            };
            GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                0x140000000L, 0x9008L,
                v(scene, b(0x8899aabbccddeeffL, 0x1021324354657687L),
                         b(0x99aabbccddeeff00L, 0x2132435465768798L)), n());
            input = new HashFpGate305.Input(
                new QueueFp604Api.Input(new FullCopy437Api.Input(entry, true, budget), fp),
                0xfedcba9876543210L);
            GovernmentPrimaryTail155Api.Bits128 expectedX0;
            GovernmentPrimaryTail155Api.Bits128 expectedX1;
            if (scene == Scene.MISSING_PM_CF8) {
                expectedPC = 0xc39cf8L;
                expectedReason = QueueFp604Api.StopReason.MISSING_FP_INPUT;
                expectedX0 = b(0x01000001L, 0);
                expectedX1 = b(0x99aabbccddeeff00L, 0x2132435465768798L);
            } else if (scene == Scene.MISSING_RC_CFF) {
                expectedPC = 0xc39cffL;
                expectedReason = QueueFp604Api.StopReason.MISSING_FP_INPUT;
                expectedX0 = b(0x3f800000L, 0);
                expectedX1 = b(0x01000001L, 0);
            } else {
                expectedPC = 0xc39d06L;
                expectedReason = QueueFp604Api.StopReason.UNSUPPORTED_FP_DOMAIN;
                expectedX0 = b(0x40000000L, 0);
                expectedX1 = b(0x3fc00000L, 0);
            }
            // READ_FAILURE's expectedEntry documents source-only prefix; never asserted on exception.
            expectedEntry = new GovernmentCrtBoundary185Api.Entry(
                0x140000000L, 0x9008L, v(scene, expectedX0, expectedX1), n());
        }
    }

    private static void assertMemoryPrefix(Fixture f) {
        boolean reachedD06 = f.scene == Scene.READ_FAILURE_D06 || f.scene == Scene.NAN_UNSUPPORTED_D06;
        require(f.entries == 1, "one SUT entry; no replay");
        require(f.budgetCalls == 0, "no budget event");
        require(f.ram.unexpected == 0, "no other Memory effect");
        require(f.ram.reads == (reachedD06 ? 1 : 0), "exact fresh read attempt count");
        List<Effect> expected = reachedD06
            ? List.of(new Effect("R32", 0x66000000101cL)) : List.of();
        require(f.ram.trace.equals(expected), "exact read prefix");
        require(Arrays.equals(f.ram.bytes, f.ram.initial), "all32 bytes unchanged");
    }

    private static GovernmentPrimaryTail155Api.Bits128 b(long low, long high) {
        return new GovernmentPrimaryTail155Api.Bits128(low, high);
    }

    /** Full literal V; only the two expected XMM banks vary in the frozen finite matrix. */
    private static GovernmentPrimaryTail155Api.VolatileBits v(Scene scene,
            GovernmentPrimaryTail155Api.Bits128 x0, GovernmentPrimaryTail155Api.Bits128 x1) {
        long rax = scene == Scene.MISSING_RC_CFF ? 0x8123456701000001L : 0x8123456700000003L;
        long rcx = switch (scene) {
            case MISSING_PM_CF8 -> 0xf123456701000001L;
            case MISSING_RC_CFF -> 0xf123456700000001L;
            default -> 0xf123456700000002L;
        };
        return new GovernmentPrimaryTail155Api.VolatileBits(
            rax, rcx, 0x0123456789abcdefL, 0x0f1e2d3c4b5a6978L,
            0x89abcdef01234567L, 0x76543210fedcba98L, 0xfedcba9876543210L,
            x0, x1,
            b(0xaabbccddeeff0011L, 0x32435465768798a9L),
            b(0xbbccddeeff001122L, 0x435465768798a9baL),
            b(0xccddeeff00112233L, 0x5465768798a9bacbL),
            b(0xddeeff0011223344L, 0x65768798a9bacbdcL));
    }

    private static GovernmentPrimaryTail155Api.NonvolatileBits n() {
        return new GovernmentPrimaryTail155Api.NonvolatileBits(
            0x1111222233334444L, 0x2222333344445555L, 0x3333444455556666L, 0x4444555566667777L,
            0x5555666677778888L, 0x6666777788889999L, 0x660000001000L, 0x777788889999aaaaL,
            b(0x8a8b8c8d8e8f9091L, 0x9293949596979899L));
    }

    private record Effect(String kind, long address) { }

    /** Exact actual153.Memory; the gate's read width and full64 address are constrained. */
    private static final class Ram implements GovernmentCaller153Api.Memory {
        private final Scene scene;
        private final byte[] initial;
        private final byte[] bytes;
        private final RuntimeException failure = new RuntimeException("308 ordinary threshold read");
        private final List<Effect> trace = new ArrayList<>();
        private int reads, unexpected;

        private Ram(Scene scene) {
            this.scene = scene;
            initial = new byte[32];
            Arrays.fill(initial, (byte) 0xa5);
            if (scene == Scene.READ_FAILURE_D06) {
                initial[28] = 0; initial[29] = 0; initial[30] = 0; initial[31] = 0x3f;
            } else {
                initial[28] = 0x45; initial[29] = 0x23;
                initial[30] = (byte) 0xc1; initial[31] = 0x7f;
            }
            bytes = initial.clone();
        }

        @Override public int readDword(long address) {
            reads++;
            trace.add(new Effect("R32", address)); // An attempt, including the throwing case.
            require(address == 0x66000000101cL, "fresh full64 R14+1c address");
            if (scene == Scene.MISSING_PM_CF8 || scene == Scene.MISSING_RC_CFF) {
                throw unused("early threshold read");
            }
            if (scene == Scene.READ_FAILURE_D06) throw failure;
            return (bytes[28] & 0xff) | ((bytes[29] & 0xff) << 8)
                | ((bytes[30] & 0xff) << 16) | ((bytes[31] & 0xff) << 24);
        }

        private AssertionError unused(String method) {
            unexpected++;
            return new AssertionError("unexpected Memory." + method);
        }
        @Override public long readQword(long address) { throw unused("readQword"); }
        @Override public int readUnsignedByte(long address) { throw unused("readUnsignedByte"); }
        @Override public void writeDword(long address, int bits) { throw unused("writeDword"); }
        @Override public int lockedXaddDword(long address, int addend) { throw unused("lockedXaddDword"); }
    }

    private static void require(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }
}
