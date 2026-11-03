package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.e;

/** New owner witness of the new649 router.tail public method only.
 * The independent tail oracle froze before this Java source; no649 candidate was read. */
public final class DefaultAllocateKnownRetryTailBoundary649 {
    private DefaultAllocateKnownRetryTailBoundary649() { }
    private static final long IMAGE = 0x0000000140000000L, SP = 0x000000007100d008L, MARKER = 0x00000000000a1000L;
    private static final long INITIAL_RET = 0x0000000140556677L;
    private static final long FOREIGN_RIP = 0xf000000014778899L, FOREIGN_SP = 0x800000007100d100L;
    private static final VolatileBits FRAME_V = new VolatileBits(
            0xfedcba9876542101L, 0xf00000000000c0d0L, 0xf00000000000c0d0L, 0x800000000000a104L, 0x900000000000a105L, 0xaaaabbbb0000a106L, 0x123456780000a107L,
            new Bits128(0x5100000000000100L, 0xaefffffffffffeffL),
            new Bits128(0x5100000000000101L, 0xaefffffffffffefeL),
            new Bits128(0x5100000000000102L, 0xaefffffffffffefdL),
            new Bits128(0x5100000000000103L, 0xaefffffffffffefcL),
            new Bits128(0x5100000000000104L, 0xaefffffffffffefbL),
            new Bits128(0x5100000000000105L, 0xaefffffffffffefaL));
    private static final NonvolatileBits FRAME_N = new NonvolatileBits(
            0x800000000000b201L, 0xf00000000000b202L, 0x900000000000b203L, 0x123400000000b204L, 0xabcdef120000b205L, 0x800000000000b206L, 0xf00000000000b207L, 0x0fedcba90000b208L,
            new Bits128(0x5200000000000209L, 0xadfffffffffffdf6L));
    private static final VolatileBits POST_V = new VolatileBits(
            0xf00000000000c301L, 0x800000000000c302L, 0x900000000000c303L, 0x123400000000c304L, 0x567800000000c305L, 0x9abc00000000c306L, 0xdef000000000c307L,
            new Bits128(0x6100000000000300L, 0x9efffffffffffcffL),
            new Bits128(0x6100000000000301L, 0x9efffffffffffcfeL),
            new Bits128(0x6100000000000302L, 0x9efffffffffffcfdL),
            new Bits128(0x6100000000000303L, 0x9efffffffffffcfcL),
            new Bits128(0x6100000000000304L, 0x9efffffffffffcfbL),
            new Bits128(0x6100000000000305L, 0x9efffffffffffcfaL));
    private static final NonvolatileBits POST_N = new NonvolatileBits(
            0x900000000000d401L, 0x800000000000d402L, 0xf00000000000d403L, 0x123400000000d404L, 0xfedcba980000d405L, 0x900000000000d406L, 0xf10000000000d407L, 0x1fedcba90000d408L,
            new Bits128(0x6200000000000409L, 0x9dfffffffffffbf6L));

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    // These finite loops expand only the literal fixture and callback write overlays.
    private static void fill(Map<Long, Byte> bytes, long address, int count, int value) {
        for (int i = 0; i < count; i++) bytes.put(address + i, (byte) value);
    }
    private static void scalar(Map<Long, Byte> bytes, long address, int width, long value) {
        for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (8 * i)));
    }
    private static Map<Long, Byte> initialExpectedBytes() {
        Map<Long, Byte> bytes = new HashMap<>();
        fill(bytes, 0x000000007100cfc8L, 128, 0x5a);
        fill(bytes, 0x00000000000a1000L, 8, 0xcc);
        scalar(bytes, 0x000000007100d008L, 8, 0x0000000140556677L);
        check(bytes.size() == 136, "independent initial owned bytes");
        return Map.copyOf(bytes);
    }
    private static Map<Long, Byte> expectedBytes(int marker, long word, long alias) {
        Map<Long, Byte> bytes = new HashMap<>(initialExpectedBytes());
        scalar(bytes, 0x00000000000a1000L, 1, marker);
        scalar(bytes, 0x00000000000a1004L, 4, word);
        scalar(bytes, 0x000000007100d008L, 8, alias);
        check(bytes.size() == 136, "independent final owned bytes");
        return Map.copyOf(bytes);
    }
    private static List<StaticRetryFixture649.Event> normalTrace() {
        return List.of(
                e("FOREIGN_TAIL", 0x00000000008571c8L, 0x00000000040ec530L),
                e("W8", 0x00000000000a1000L, 0x0000000000000061L),
                e("W32", 0x00000000000a1004L, 0x0000000080000001L),
                e("W64", 0x000000007100d008L, 0x8877665544332211L));
    }
    private static List<StaticRetryFixture649.Event> stoppedTrace() {
        return List.of(
                e("FOREIGN_TAIL", 0x00000000008571c8L, 0x00000000040ec530L),
                e("W8", 0x00000000000a1000L, 0x0000000000000062L),
                e("W32", 0x00000000000a1004L, 0x00000000fedcba98L),
                e("W64", 0x000000007100d008L, 0x1122334455667788L));
    }

    private static final class Scene {
        final StaticRetryFixture649.Trace trace = new StaticRetryFixture649.Trace();
        final StaticRetryFixture649.Ram memory = new StaticRetryFixture649.Ram(trace);
        final Map<Long, Byte> before = initialExpectedBytes();
        final QueueFp604Api.Mxcsr inputFp = new QueueFp604Api.Mxcsr(0, 0);
        final DefaultStaticFp648Api.TailFrame frame = new DefaultStaticFp648Api.TailFrame(
                new GovernmentCrtBoundary185Api.Tail(0x8571c8L,
                        GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x40ec530L,
                        new GovernmentCrtBoundary185Api.Entry(IMAGE, SP, FRAME_V, FRAME_N)),
                true, inputFp);
        final GovernmentCrtBoundary185Api.Tail expectedTransfer = new GovernmentCrtBoundary185Api.Tail(
                0x8571c8L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x40ec530L,
                new GovernmentCrtBoundary185Api.Entry(IMAGE, SP, FRAME_V, FRAME_N));
        int retryCount;
        int budgetCount;
        int invokeCount;
        int tailCount;

        Scene() {
            memory.seedFill(0x000000007100cfc8L, 128, 0x5a);
            memory.seedFill(0x00000000000a1000L, 8, 0xcc);
            memory.seedScalar(0x000000007100d008L, 8, 0x0000000140556677L);
            StaticRetryFixture649.checkFullBytes(before, memory, "independent scene seed");
            trace.checkExactly(List.of(), "seeding produces no Memory events");
        }
        DefaultStaticFp648Api.Calls bind(DefaultStaticFp648Api.Calls foreign) {
            KnownPageAllocateFp622.RetryCalls retry = frame649 -> {
                retryCount++;
                throw new AssertionError("router.tail reached retry callback");
            };
            GovernmentCrtBoundary185Api.LoopBudget budget = (pc, size) -> {
                budgetCount++;
                throw new AssertionError("router.tail reached retry budget");
            };
            DefaultStaticFp648Api.Calls router = DefaultAllocateKnownRetry649.bind(
                    memory, retry, budget, foreign);
            check(router != null, "new649 public bind returns its router");
            check(retryCount == 0 && budgetCount == 0 && invokeCount == 0 && tailCount == 0,
                    "bind has no callback or budget effects");
            trace.checkExactly(List.of(), "bind has no Memory or port events");
            StaticRetryFixture649.checkFullBytes(before, memory, "bind leaves every owned byte");
            return router;
        }
        void enteredTail(DefaultStaticFp648Api.TailFrame actual) {
            check(++tailCount == 1, "exactly one foreign tail reach");
            check(actual == frame, "foreign receives SAME actual648 TailFrame");
            check(actual.transfer().equals(expectedTransfer), "complete literal Tail/Entry/V/N/image/SP");
            check(actual.directionFlagSet(), "actual incoming DF");
            check(actual.preMxcsr() == inputFp, "SAME incoming unknown FP");
            check(inputFp.valueBits() == 0 && inputFp.knownMaskBits() == 0, "explicit unknown FP");
            check(retryCount == 0 && budgetCount == 0 && invokeCount == 0,
                    "no retry/invoke/budget on tail route");
            check(memory.trace == trace, "callback operates SAME bound Ram/Trace");
            trace.checkExactly(List.of(), "no eager CALLpush/localguard/RET/read before foreign tail");
            StaticRetryFixture649.checkFullBytes(before, memory, "no bytes changed before callback");
            trace.add(e("FOREIGN_TAIL", 0x8571c8L, 0x40ec530L));
        }
        void complete(List<StaticRetryFixture649.Event> expectedTrace, Map<Long, Byte> expected) {
            check(tailCount == 1 && invokeCount == 0 && retryCount == 0 && budgetCount == 0,
                    "only one tail call; no invoke/retry/budget continuation");
            trace.checkExactly(expectedTrace, "complete ordered tail/Memory events");
            StaticRetryFixture649.checkFullBytes(expected, memory, "all136 owned bytes/padding/RET alias");
        }
    }

    private static void sameForeignNormal() {
        Scene scene = new Scene();
        Map<Long, Byte> bytes = expectedBytes(0x61, 0x80000001L, 0x8877665544332211L);
        List<StaticRetryFixture649.Event> events = normalTrace();
        QueueFp604Api.Mxcsr partial = new QueueFp604Api.Mxcsr(0x40, 0xc0);
        GovernmentCrtBoundary185Api.NormalReturn expectedNR = new GovernmentCrtBoundary185Api.NormalReturn(
                POST_V, FOREIGN_RIP, FOREIGN_SP, POST_N);
        QueueFp604Api.Normal offered = new QueueFp604Api.Normal(
                new FullCopy437Api.CallResult(expectedNR, false), partial);
        check(FOREIGN_SP != SP && FOREIGN_SP != SP + 8 && !POST_N.equals(FRAME_N),
                "foreign SP/N deliberately differ; no local normal guard applies");
        DefaultStaticFp648Api.Calls foreign = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                scene.invokeCount++;
                throw new AssertionError("tail witness reached foreign invoke");
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                scene.enteredTail(frame);
                scene.memory.writeByte(MARKER, 0x61);
                scene.memory.writeDword(MARKER + 4, (int) 0x80000001L);
                scene.memory.writeQword(SP, 0x8877665544332211L);
                return offered;
            }
        };
        DefaultStaticFp648Api.Calls router = scene.bind(foreign);
        QueueFp604Api.Outcome result = router.tail(scene.frame);
        check(result == offered, "new649 tail returns SAME complete foreign Normal");
        QueueFp604Api.Normal normal = (QueueFp604Api.Normal) result;
        check(normal.base().normalReturn().equals(expectedNR), "all changed foreign V/N/RIP/SP bits");
        check(!normal.base().postDirectionFlagSet(), "foreign changed DF retained");
        check(normal.postMxcsr() == partial && partial.valueBits() == 0x40
                && partial.knownMaskBits() == 0xc0, "SAME changed partial current FP");
        scene.complete(events, bytes);
    }
    private static void sameForeignStopped() {
        Scene scene = new Scene();
        Map<Long, Byte> bytes = expectedBytes(0x62, 0xfedcba98L, 0x1122334455667788L);
        List<StaticRetryFixture649.Event> events = stoppedTrace();
        QueueFp604Api.Mxcsr partial = new QueueFp604Api.Mxcsr(8, 12);
        GovernmentCrtBoundary185Api.Entry expectedState = new GovernmentCrtBoundary185Api.Entry(
                IMAGE, SP, FRAME_V, FRAME_N);
        QueueFp604Api.Snapshot snapshot = new QueueFp604Api.Snapshot(
                expectedState, 0x40ec530L, false, partial);
        QueueFp604Api.Stopped offered = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE, snapshot, 0, 0x8571c8L);
        DefaultStaticFp648Api.Calls foreign = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                scene.invokeCount++;
                throw new AssertionError("tail Stop witness reached foreign invoke");
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                scene.enteredTail(frame);
                scene.memory.writeByte(MARKER, 0x62);
                scene.memory.writeDword(MARKER + 4, (int) 0xfedcba98L);
                scene.memory.writeQword(SP, 0x1122334455667788L);
                return offered;
            }
        };
        DefaultStaticFp648Api.Calls router = scene.bind(foreign);
        QueueFp604Api.Outcome result = router.tail(scene.frame);
        check(result == offered, "new649 tail returns SAME pre-existing foreign Stopped");
        QueueFp604Api.Stopped stopped = (QueueFp604Api.Stopped) result;
        check(stopped.snapshot() == snapshot && snapshot.currentState().equals(expectedState),
                "SAME independent complete Snapshot and chosen raw bank");
        check(snapshot.instructionRva() == 0x40ec530L && !snapshot.directionFlagSet()
                && snapshot.mxcsr() == partial, "complete chosen Stop PC/DF/SAME partial FP");
        check(stopped.reason() == QueueFp604Api.StopReason.MISSING_POST_STATE
                && stopped.raisedConditionBits() == 0 && stopped.originCallSiteRva() == 0x8571c8L,
                "complete chosen Stop reason/conditions/origin");
        scene.complete(events, bytes);
    }

    public static void foreignTailOutcomesPreserveIdentity() {
        sameForeignNormal();
        sameForeignStopped();
    }
    public static int verify() {
        foreignTailOutcomesPreserveIdentity();
        return 1;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
