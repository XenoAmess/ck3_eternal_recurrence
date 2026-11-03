package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestRetry4223b94;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.check;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.checkEqual;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.checkFullBytes;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.checkSame;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.e;

/** Two owner failure-prefix groups from the prior private source-literal oracle. */
public final class DefaultRetryFailureBoundary649 {
    private DefaultRetryFailureBoundary649() { }

    private static final VolatileBits ROOT_ERROR_V = new VolatileBits(
            0x8100000000001001L, 0xd000000000002222L, 0x0000000000000044L, 0x8400000000001004L, 0x8500000000001005L, 0x8600000000001006L, 0x8700000000001007L,
            new Bits128(0x1111000000000100L, 0xeeee000000000100L),
            new Bits128(0x1111000000000101L, 0xeeee000000000101L),
            new Bits128(0x1111000000000102L, 0xeeee000000000102L),
            new Bits128(0x1111000000000103L, 0xeeee000000000103L),
            new Bits128(0x1111000000000104L, 0xeeee000000000104L),
            new Bits128(0x1111000000000105L, 0xeeee000000000105L));

    private static final VolatileBits CHILD_ERROR_V = new VolatileBits(
            0x8100000000001001L, 0x0000000000000044L, 0x0000000000000044L, 0x8400000000001004L, 0x8500000000001005L, 0x8600000000001006L, 0x8700000000001007L,
            new Bits128(0x1111000000000100L, 0xeeee000000000100L),
            new Bits128(0x1111000000000101L, 0xeeee000000000101L),
            new Bits128(0x1111000000000102L, 0xeeee000000000102L),
            new Bits128(0x1111000000000103L, 0xeeee000000000103L),
            new Bits128(0x1111000000000104L, 0xeeee000000000104L),
            new Bits128(0x1111000000000105L, 0xeeee000000000105L));

    private static final VolatileBits ZERO_V = new VolatileBits(
            0x0000000000000000L, 0x9200000000002002L, 0x9300000000002003L, 0x9400000000002004L, 0x9500000000002005L, 0x9600000000002006L, 0x9700000000002007L,
            new Bits128(0x3333000000000200L, 0xcccc000000000200L),
            new Bits128(0x3333000000000201L, 0xcccc000000000201L),
            new Bits128(0x3333000000000202L, 0xcccc000000000202L),
            new Bits128(0x3333000000000203L, 0xcccc000000000203L),
            new Bits128(0x3333000000000204L, 0xcccc000000000204L),
            new Bits128(0x3333000000000205L, 0xcccc000000000205L));

    private static final VolatileBits ERROR_HANDLER_INPUT_V = new VolatileBits(
            0x0000000000000000L, 0x0000000000000044L, 0x9300000000002003L, 0x9400000000002004L, 0x9500000000002005L, 0x9600000000002006L, 0x9700000000002007L,
            new Bits128(0x3333000000000200L, 0xcccc000000000200L),
            new Bits128(0x3333000000000201L, 0xcccc000000000201L),
            new Bits128(0x3333000000000202L, 0xcccc000000000202L),
            new Bits128(0x3333000000000203L, 0xcccc000000000203L),
            new Bits128(0x3333000000000204L, 0xcccc000000000204L),
            new Bits128(0x3333000000000205L, 0xcccc000000000205L));

    private static final VolatileBits ERROR_HANDLER_OUTPUT_V = new VolatileBits(
            0xbeef000000000000L, 0xa200000000003002L, 0xa300000000003003L, 0xa400000000003004L, 0xa500000000003005L, 0xa600000000003006L, 0xa700000000003007L,
            new Bits128(0x5555000000000300L, 0xaaaa000000000300L),
            new Bits128(0x5555000000000301L, 0xaaaa000000000301L),
            new Bits128(0x5555000000000302L, 0xaaaa000000000302L),
            new Bits128(0x5555000000000303L, 0xaaaa000000000303L),
            new Bits128(0x5555000000000304L, 0xaaaa000000000304L),
            new Bits128(0x5555000000000305L, 0xaaaa000000000305L));

    private static final VolatileBits ROOT_BUDGET_V = new VolatileBits(
            0x8100000000001001L, 0xd000000000002222L, 0xe000000000003333L, 0x8400000000001004L, 0x8500000000001005L, 0x8600000000001006L, 0x8700000000001007L,
            new Bits128(0x1111000000000100L, 0xeeee000000000100L),
            new Bits128(0x1111000000000101L, 0xeeee000000000101L),
            new Bits128(0x1111000000000102L, 0xeeee000000000102L),
            new Bits128(0x1111000000000103L, 0xeeee000000000103L),
            new Bits128(0x1111000000000104L, 0xeeee000000000104L),
            new Bits128(0x1111000000000105L, 0xeeee000000000105L));

    private static final VolatileBits CHILD_BUDGET_V = new VolatileBits(
            0x8100000000001001L, 0xe000000000003333L, 0xe000000000003333L, 0x8400000000001004L, 0x8500000000001005L, 0x8600000000001006L, 0x8700000000001007L,
            new Bits128(0x1111000000000100L, 0xeeee000000000100L),
            new Bits128(0x1111000000000101L, 0xeeee000000000101L),
            new Bits128(0x1111000000000102L, 0xeeee000000000102L),
            new Bits128(0x1111000000000103L, 0xeeee000000000103L),
            new Bits128(0x1111000000000104L, 0xeeee000000000104L),
            new Bits128(0x1111000000000105L, 0xeeee000000000105L));

    private static final NonvolatileBits ROOT_N = new NonvolatileBits(
            0x8000000000000101L, 0x9000000000000202L, 0xa000000000000303L, 0xb000000000000404L, 0xcabcdeff00000505L, 0xd000000000000606L, 0xe000000000000707L, 0xf000000000000808L,
            new Bits128(0x6666000000000606L, 0x9999000000000606L));

    private static final NonvolatileBits ERROR_LOWER_N = new NonvolatileBits(
            0x0000000000000044L, 0x9000000000000202L, 0xa000000000000303L, 0xb000000000000404L, 0xcabcdeff00000505L, 0xd000000000000606L, 0xe000000000000707L, 0xf000000000000808L,
            new Bits128(0x6666000000000606L, 0x9999000000000606L));

    private static StaticRetryFixture649.Ram seededRam(StaticRetryFixture649.Trace trace) {
        StaticRetryFixture649.Ram ram = new StaticRetryFixture649.Ram(trace);
        ram.seedFill(0x70007f88L, 192, 0x5a);
        ram.seedFill(0xb000L, 8, 0xcc);
        ram.seedFill(0xe000000000003333L, 16, 0xdd);
        ram.seedFill(0xd000000000002222L, 16, 0xee);
        ram.seedScalar(0x70008008L, 8, 0x140222222L);
        return ram;
    }

    private static void literalFill(Map<Long, Byte> map, long address, int count, int value) {
        for (int i = 0; i < count; i++) map.put(address + i, (byte) value);
    }

    private static void literalScalar(Map<Long, Byte> map, long address, int width, long value) {
        for (int i = 0; i < width; i++) map.put(address + i, (byte) (value >>> (8 * i)));
    }

    private static Map<Long, Byte> independentInitialBytes() {
        Map<Long, Byte> map = new HashMap<>();
        literalFill(map, 0x70007f88L, 192, 0x5a);
        literalFill(map, 0xb000L, 8, 0xcc);
        literalFill(map, 0xe000000000003333L, 16, 0xdd);
        literalFill(map, 0xd000000000002222L, 16, 0xee);
        literalScalar(map, 0x70008008L, 8, 0x140222222L);
        check(map.size() == 232, "Independent seeded RAM extent");
        return map;
    }

    private static DefaultStaticFp648Api.Calls foreignMustNotRun() {
        return new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                throw new AssertionError("Selected D0 CALL must use known retry binder");
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                throw new AssertionError("No tail in these D0 failure groups");
            }
        };
    }

    /** Captures real escaped exceptions without manufacturing an expected exception. */
    private static final class ParentProbe implements DefaultStaticFp648Api.Calls {
        private final DefaultStaticFp648Api.Calls known;
        private final GovernmentCrtBoundary185Api.Call expectedCall;
        private final GovernmentCrtBoundary185Api.Entry expectedChild;
        private final QueueFp604Api.Mxcsr preFp;
        private int invokeCount;
        private RequestRetry4223b94.UnexecutedSourcePath legacy;
        private UnsupportedOperationException budgetFailure;

        ParentProbe(DefaultStaticFp648Api.Calls known, VolatileBits childV, QueueFp604Api.Mxcsr preFp) {
            this.known = known;
            this.preFp = preFp;
            expectedCall = new GovernmentCrtBoundary185Api.Call(0x8571d7L,
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4223b94L,
                    0x70007fe0L, childV, ROOT_N);
            expectedChild = new GovernmentCrtBoundary185Api.Entry(
                    0x140000000L, 0x70007fd8L, childV, ROOT_N);
        }

        @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
            check(invokeCount == 0, "Exactly one D0 child invocation");
            invokeCount++;
            check(frame != null, "Actual D0 frame exists");
            checkEqual(expectedCall, frame.call(), "Complete parent CALL/site/kind/target/preSP/V/N");
            checkEqual(expectedChild, frame.childEntry(), "Complete B94 child entry image/SP/V/N");
            check(frame.directionFlagSet(), "Parent current DF");
            checkSame(preFp, frame.preMxcsr(), "Same parent unknown FP object");
            check(frame.instructionLength() == 5, "Parent source CALL length");
            check(frame.returnRipBits() == 0x1408571dcL, "Parent source continuation");
            try {
                return known.invoke(frame);
            } catch (RequestRetry4223b94.UnexecutedSourcePath failure) {
                legacy = failure;
                throw failure;
            } catch (UnsupportedOperationException failure) {
                budgetFailure = failure;
                throw failure;
            }
        }

        @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
            throw new AssertionError("Unexpected tail at parent observation boundary");
        }
    }

    private static void checkLower(KnownPageAllocateFp622.RetryCall actual,
            GovernmentCrtBoundary185Api.Call expectedCall,
            GovernmentCrtBoundary185Api.Entry expectedChild, long continuation,
            boolean df, QueueFp604Api.Mxcsr fp) {
        check(actual != null, "Actual lower frame exists");
        checkEqual(expectedCall, actual.original(), "Complete lower CALL/site/kind/target/preSP/V/N");
        checkEqual(expectedChild, actual.childEntry(), "Complete lower child image/SP/V/N");
        check(actual.returnRipBits() == continuation, "Actual lower source continuation");
        check(actual.directionFlagSet() == df, "Actual current lower DF");
        checkSame(fp, actual.preMxcsr(), "Same current lower FP object");
    }

    public static void wholeOriginalErrorBoundaryKeepsPrefix() {
        StaticRetryFixture649.Trace trace = new StaticRetryFixture649.Trace();
        StaticRetryFixture649.Ram ram = seededRam(trace);
        QueueFp604Api.Mxcsr unknown = new QueueFp604Api.Mxcsr(0, 0);
        QueueFp604Api.Mxcsr partialA = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Mxcsr partialB = new QueueFp604Api.Mxcsr(128, 192);
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(
                new GovernmentCrtBoundary185Api.Entry(0x140000000L, 0x70008008L, ROOT_ERROR_V, ROOT_N),
                true, unknown);
        GovernmentCrtBoundary185Api.Call firstCall = new GovernmentCrtBoundary185Api.Call(
                0x4223baeL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x42420b8L,
                0x70007fb0L, CHILD_ERROR_V, ERROR_LOWER_N);
        GovernmentCrtBoundary185Api.Entry firstChild = new GovernmentCrtBoundary185Api.Entry(
                0x140000000L, 0x70007fa8L, CHILD_ERROR_V, ERROR_LOWER_N);
        GovernmentCrtBoundary185Api.Call handlerCall = new GovernmentCrtBoundary185Api.Call(
                0x4223ba2L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424cffcL,
                0x70007fb0L, ERROR_HANDLER_INPUT_V, ERROR_LOWER_N);
        GovernmentCrtBoundary185Api.Entry handlerChild = new GovernmentCrtBoundary185Api.Entry(
                0x140000000L, 0x70007fa8L, ERROR_HANDLER_INPUT_V, ERROR_LOWER_N);
        QueueFp604Api.Normal zeroOffer = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(
                        ZERO_V, 0x144223bb3L, 0x70007fb0L, ERROR_LOWER_N), false), partialA);
        QueueFp604Api.Normal handlerOffer = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(
                        ERROR_HANDLER_OUTPUT_V, 0x144223ba7L, 0x70007fb0L, ERROR_LOWER_N), true), partialB);
        int[] lowerCount = {0};
        KnownPageAllocateFp622.RetryCalls lower = frame -> {
            if (lowerCount[0] == 0) {
                lowerCount[0] = 1;
                checkLower(frame, firstCall, firstChild, 0x144223bb3L, true, unknown);
                trace.add(e("PORT_INVOKE", 0x4223baeL, 0x42420b8L));
                ram.writeByte(0xb000L, 0x31);
                return zeroOffer;
            }
            check(lowerCount[0] == 1, "Only allocator and handler lower calls");
            lowerCount[0] = 2;
            checkLower(frame, handlerCall, handlerChild, 0x144223ba7L, false, partialA);
            trace.add(e("PORT_INVOKE", 0x4223ba2L, 0x424cffcL));
            ram.writeByte(0xb001L, 0x32);
            ram.writeQword(0x70008008L, 0x2122232425262728L);
            return handlerOffer;
        };
        int[] budgetCount = {0};
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, size) -> {
            check(budgetCount[0] == 0, "Only first allocator budget before legacy error");
            budgetCount[0]++;
            check(pc == 0x4223baeL && size == 0x44L, "Exact original error-scene budget arguments");
            trace.add(e("BUDGET", pc, size));
        };
        Map<Long, Byte> expectedBytes = independentInitialBytes();
        literalScalar(expectedBytes, 0x70007fd8L, 8, 0x1408571dcL);
        literalScalar(expectedBytes, 0x70007fd0L, 8, 0x8000000000000101L);
        literalScalar(expectedBytes, 0x70007fa8L, 8, 0x144223bb3L);
        literalScalar(expectedBytes, 0xb000L, 1, 0x31);
        literalScalar(expectedBytes, 0x70007fa8L, 8, 0x144223ba7L);
        literalScalar(expectedBytes, 0xb001L, 1, 0x32);
        literalScalar(expectedBytes, 0x70008008L, 8, 0x2122232425262728L);
        List<StaticRetryFixture649.Event> expectedEvents = List.of(
                e("W64", 0x70007fd8L, 0x1408571dcL),
                e("W64", 0x70007fd0L, 0x8000000000000101L),
                e("BUDGET", 0x4223baeL, 0x44L),
                e("W64", 0x70007fa8L, 0x144223bb3L),
                e("PORT_INVOKE", 0x4223baeL, 0x42420b8L),
                e("W8", 0xb000L, 0x31),
                e("W64", 0x70007fa8L, 0x144223ba7L),
                e("PORT_INVOKE", 0x4223ba2L, 0x424cffcL),
                e("W8", 0xb001L, 0x32),
                e("W64", 0x70008008L, 0x2122232425262728L));
        DefaultStaticFp648Api.Calls known = DefaultAllocateKnownRetry649.bind(
                ram, lower, budget, foreignMustNotRun());
        ParentProbe probe = new ParentProbe(known, CHILD_ERROR_V, unknown);
        RequestRetry4223b94.UnexecutedSourcePath escaped = null;
        try {
            DefaultAllocateWithFp648.fromSlot08(input, ram, probe);
        } catch (RequestRetry4223b94.UnexecutedSourcePath failure) {
            escaped = failure;
        }
        check(escaped != null, "Actual legacy error boundary must escape");
        check(escaped.getClass() == RequestRetry4223b94.UnexecutedSourcePath.class, "Exact legacy exception type");
        checkSame(probe.legacy, escaped, "Same actual legacy exception across outer648");
        check("source error helper remains unexecuted".equals(escaped.getMessage()), "Exact legacy message");
        check(escaped.targetRva() == 0x42207d8L, "Original unexecuted error target");
        check(escaped.trapSiteRva() == 0x4223bc9L, "Original unexecuted INT3 site");
        check(escaped.capturedSizeBits() == 0x44L, "Original captured size");
        check(probe.invokeCount == 1 && lowerCount[0] == 2 && budgetCount[0] == 1, "Exact failure-prefix counts");
        trace.checkExactly(expectedEvents, "Complete legacy error event prefix, with no POP/RET/error helper push");
        checkFullBytes(expectedBytes, ram, "Full legacy error RAM and callback alias retained");
    }

    public static void wholeBudgetThrowBeforeLowerPush() {
        StaticRetryFixture649.Trace trace = new StaticRetryFixture649.Trace();
        StaticRetryFixture649.Ram ram = seededRam(trace);
        QueueFp604Api.Mxcsr unknown = new QueueFp604Api.Mxcsr(0, 0);
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(
                new GovernmentCrtBoundary185Api.Entry(0x140000000L, 0x70008008L, ROOT_BUDGET_V, ROOT_N),
                true, unknown);
        UnsupportedOperationException sentinel = new UnsupportedOperationException("Owned original budget sentinel");
        int[] lowerCount = {0};
        KnownPageAllocateFp622.RetryCalls lower = frame -> {
            lowerCount[0]++;
            throw new AssertionError("Budget failure must precede any lower callback");
        };
        int[] budgetCount = {0};
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, size) -> {
            check(budgetCount[0] == 0, "Budget called once");
            budgetCount[0]++;
            check(pc == 0x4223baeL && size == 0xe000000000003333L, "Full raw original budget arguments");
            trace.add(e("BUDGET", pc, size));
            ram.writeByte(0xb000L, 0x51);
            throw sentinel;
        };
        Map<Long, Byte> expectedBytes = independentInitialBytes();
        literalScalar(expectedBytes, 0x70007fd8L, 8, 0x1408571dcL);
        literalScalar(expectedBytes, 0x70007fd0L, 8, 0x8000000000000101L);
        literalScalar(expectedBytes, 0xb000L, 1, 0x51);
        List<StaticRetryFixture649.Event> expectedEvents = List.of(
                e("W64", 0x70007fd8L, 0x1408571dcL),
                e("W64", 0x70007fd0L, 0x8000000000000101L),
                e("BUDGET", 0x4223baeL, 0xe000000000003333L),
                e("W8", 0xb000L, 0x51));
        DefaultStaticFp648Api.Calls known = DefaultAllocateKnownRetry649.bind(
                ram, lower, budget, foreignMustNotRun());
        ParentProbe probe = new ParentProbe(known, CHILD_BUDGET_V, unknown);
        UnsupportedOperationException escaped = null;
        try {
            DefaultAllocateWithFp648.fromSlot08(input, ram, probe);
        } catch (UnsupportedOperationException failure) {
            escaped = failure;
        }
        checkSame(sentinel, probe.budgetFailure, "Same pre-created sentinel reaches binder boundary");
        checkSame(sentinel, escaped, "Same original budget exception reaches outer648");
        check(probe.invokeCount == 1 && budgetCount[0] == 1 && lowerCount[0] == 0, "No reached lower CALL");
        trace.checkExactly(expectedEvents, "RBX save before budget, no lower push/POP/RET");
        checkFullBytes(expectedBytes, ram, "Complete budget prefix RAM including untouched lower slot");
    }

    public static int verify() {
        wholeOriginalErrorBoundaryKeepsPrefix();
        wholeBudgetThrowBeforeLowerPush();
        return 2;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }
}
