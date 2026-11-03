package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.Event;
import org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.Ram;
import org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.Trace;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.check;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.checkEqual;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.checkFullBytes;
import static org.xar.ck3.control.g2.m2.nativecode.StaticRetryFixture649.e;

/** Owner source-only witnesses for frozen649 scenes ENTRY_FIRST_NORMAL_CALLEE_RET_ALIAS
 * and WHOLE_ANCESTOR_ACCEPTED_INNER_REJECTED. No649 implementation/model CONTENT read.
 * Generic RET alias proves a callee-entry result only; it is not wholeD0 completion.
 * Expected complete RAM regions and banks predate every target invocation. */
public final class Retry60GenericGuardBoundary649 {
    private Retry60GenericGuardBoundary649() { }
    private static final long IMAGE = 0x140000000L;
    private static final long ROOT_SP = 0x70008008L;
    private static final long T = 0x70007FD8L;
    private static final long PRE = 0x70007FB0L;
    private static final long SIZE = 0xE000000000003333L;
    private static final long MARKER = 0xB000L;
    private static final long GENERIC_RET_ALIAS = 0x3132333435363738L;
    private static final long ROOT_RET_ALIAS = 0x2122232425262728L;

    private static VolatileBits rootV() {
        return new VolatileBits(0x8100000000001001L, 0xd000000000002222L, 0xe000000000003333L, 0x8400000000001004L, 0x8500000000001005L, 0x8600000000001006L, 0x8700000000001007L,
                new Bits128(0x1111000000000100L, 0xeeee000000000100L),
                new Bits128(0x1111000000000101L, 0xeeee000000000101L),
                new Bits128(0x1111000000000102L, 0xeeee000000000102L),
                new Bits128(0x1111000000000103L, 0xeeee000000000103L),
                new Bits128(0x1111000000000104L, 0xeeee000000000104L),
                new Bits128(0x1111000000000105L, 0xeeee000000000105L));
    }

    private static VolatileBits childV() {
        return new VolatileBits(0x8100000000001001L, 0xe000000000003333L, 0xe000000000003333L, 0x8400000000001004L, 0x8500000000001005L, 0x8600000000001006L, 0x8700000000001007L,
                new Bits128(0x1111000000000100L, 0xeeee000000000100L),
                new Bits128(0x1111000000000101L, 0xeeee000000000101L),
                new Bits128(0x1111000000000102L, 0xeeee000000000102L),
                new Bits128(0x1111000000000103L, 0xeeee000000000103L),
                new Bits128(0x1111000000000104L, 0xeeee000000000104L),
                new Bits128(0x1111000000000105L, 0xeeee000000000105L));
    }

    private static VolatileBits postV() {
        return new VolatileBits(0x9000000000000000L, 0x9200000000002002L, 0x9300000000002003L, 0x9400000000002004L, 0x9500000000002005L, 0x9600000000002006L, 0x9700000000002007L,
                new Bits128(0x3333000000000200L, 0xcccc000000000200L),
                new Bits128(0x3333000000000201L, 0xcccc000000000201L),
                new Bits128(0x3333000000000202L, 0xcccc000000000202L),
                new Bits128(0x3333000000000203L, 0xcccc000000000203L),
                new Bits128(0x3333000000000204L, 0xcccc000000000204L),
                new Bits128(0x3333000000000205L, 0xcccc000000000205L));
    }

    private static NonvolatileBits rootN() {
        return new NonvolatileBits(0x8000000000000101L, 0x9000000000000202L, 0xa000000000000303L, 0xb000000000000404L, 0xcabcdeff00000505L, 0xd000000000000606L, 0xe000000000000707L, 0xf000000000000808L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static NonvolatileBits lowerN() {
        return new NonvolatileBits(0xe000000000003333L, 0x9000000000000202L, 0xa000000000000303L, 0xb000000000000404L, 0xcabcdeff00000505L, 0xd000000000000606L, 0xe000000000000707L, 0xf000000000000808L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static GovernmentCrtBoundary185Api.Entry genericEntry() {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE, T, childV(), rootN());
    }
    private static GovernmentCrtBoundary185Api.Entry rootEntry() {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE, ROOT_SP, rootV(), rootN());
    }
    private static QueueFp604Api.Normal normal(VolatileBits v, long rip, long sp,
            NonvolatileBits n, boolean df, QueueFp604Api.Mxcsr fp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v, rip, sp, n), df), fp);
    }
    private static void firstLower(KnownPageAllocateFp622.RetryCall frame,
            QueueFp604Api.Mxcsr unknown) {
        checkEqual(new GovernmentCrtBoundary185Api.Call(0x4223BAEL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x42420B8L,
                PRE, childV(), lowerN()), frame.original(), "all actual lower original185.Call fields");
        checkEqual(new GovernmentCrtBoundary185Api.Entry(IMAGE, 0x70007FA8L,
                childV(), lowerN()), frame.childEntry(), "full actual lower child Entry");
        check(frame.directionFlagSet(), "first actual lower receives current DF=true");
        check(frame.preMxcsr() == unknown && unknown.valueBits() == 0
                && unknown.knownMaskBits() == 0, "SAME explicit unknown FP, no default controls");
        check(frame.returnRipBits() == IMAGE + 0x4223BB3L, "actual BAE source continuation");
        check(frame.returnRipBits() - IMAGE - frame.original().callSiteRva() == 5,
                "source five-byte lower CALL");
    }
    private static void parentFrame(DefaultStaticFp648Api.CallFrame frame,
            QueueFp604Api.Mxcsr unknown) {
        checkEqual(new GovernmentCrtBoundary185Api.Call(0x8571D7L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4223B94L,
                0x70007FE0L, childV(), rootN()), frame.call(), "all actual D0 CALL fields");
        checkEqual(genericEntry(), frame.childEntry(), "actual D0 child full image/SP/V/N");
        check(frame.directionFlagSet() && frame.preMxcsr() == unknown,
                "D0 actual current DF and SAME unknown FP");
        check(frame.instructionLength() == 5 && frame.returnRipBits() == IMAGE + 0x8571DCL,
                "actual D0 source length and continuation");
    }
    private static void seedCommon(Ram memory) {
        memory.seedFill(0x70007F88L, 192, 90);
        memory.seedFill(0xB000L, 8, 204);
        memory.seedFill(0xE000000000003333L, 16, 221);
        memory.seedFill(0xD000000000002222L, 16, 238);
        memory.seedScalar(0x70008008L, 8, 0x140222222L);
    }
    /** Pure finite decoding of complete source-literal regions, never actual target bytes. */
    private static void region(Map<Long, Byte> map, long address, String hexadecimal) {
        byte[] bytes = HexFormat.of().parseHex(hexadecimal);
        for (int i = 0; i < bytes.length; i++) map.put(address + i, bytes[i]);
    }

    private static Map<Long, Byte> genericInitial() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x0000000070007f88L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5adc718540010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a22222240010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x000000000000b000L, "cccccccccccccccc");
        region(map, 0xe000000000003333L, "dddddddddddddddddddddddddddddddd");
        region(map, 0xd000000000002222L, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
        check(map.size() == 232, "exact owned byte extent");
        return map;
    }

    private static Map<Long, Byte> genericExpected() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x0000000070007f88L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ab33b2244010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a010100000000008038373635343332315a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a22222240010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x000000000000b000L, "11cccccccccccccc");
        region(map, 0xe000000000003333L, "dddddddddddddddddddddddddddddddd");
        region(map, 0xd000000000002222L, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
        check(map.size() == 232, "exact owned byte extent");
        return map;
    }

    private static Map<Long, Byte> wholeInitial() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x0000000070007f88L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a22222240010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x000000000000b000L, "cccccccccccccccc");
        region(map, 0xe000000000003333L, "dddddddddddddddddddddddddddddddd");
        region(map, 0xd000000000002222L, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
        check(map.size() == 232, "exact owned byte extent");
        return map;
    }

    private static Map<Long, Byte> badExpected() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x0000000070007f88L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ab33b2244010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a0101000000000080dc718540010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a28272625242322215a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x000000000000b000L, "41cccccccccccccc");
        region(map, 0xe000000000003333L, "dddddddddddddddddddddddddddddddd");
        region(map, 0xd000000000002222L, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
        check(map.size() == 232, "exact owned byte extent");
        return map;
    }

    private static List<Event> genericEvents() {
        return List.of(
                e("W64", 0x0000000070007fd0L, 0x8000000000000101L),
                e("BUDGET", 0x0000000004223baeL, 0xe000000000003333L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223bb3L),
                e("PORT_INVOKE", 0x0000000004223baeL, 0x00000000042420b8L),
                e("W8", 0x000000000000b000L, 0x0000000000000011L),
                e("W64", 0x0000000070007fd8L, 0x3132333435363738L),
                e("R64", 0x0000000070007fd0L, 0x8000000000000101L),
                e("R64", 0x0000000070007fd8L, 0x3132333435363738L));
    }

    private static List<Event> badEvents() {
        return List.of(
                e("W64", 0x0000000070007fd8L, 0x00000001408571dcL),
                e("W64", 0x0000000070007fd0L, 0x8000000000000101L),
                e("BUDGET", 0x0000000004223baeL, 0xe000000000003333L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223bb3L),
                e("PORT_INVOKE", 0x0000000004223baeL, 0x00000000042420b8L),
                e("W8", 0x000000000000b000L, 0x0000000000000041L),
                e("W64", 0x0000000070008008L, 0x2122232425262728L));
    }

    public static void genericFirstAllocationChangedStateFreshCalleeRetAlias() {
        Map<Long, Byte> initial = genericInitial();
        Map<Long, Byte> expected = genericExpected();
        List<Event> literal = genericEvents();
        Trace trace = new Trace();
        Ram memory = new Ram(trace);
        seedCommon(memory);
        // This materializes a caller precondition only; no D0 CALL or owned push is executed here.
        memory.seedScalar(T, 8, IMAGE + 0x8571DCL);
        checkFullBytes(initial, memory, "all232 direct-entry initial bytes");
        check(trace.size() == 0, "seeding is not a target event");
        QueueFp604Api.Mxcsr unknown = new QueueFp604Api.Mxcsr(0, 0);
        QueueFp604Api.Mxcsr acceptedFp = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Normal lowerOffer = normal(postV(), IMAGE + 0x4223BB3L,
                PRE, lowerN(), false, acceptedFp);
        QueueFp604Api.Normal expectedEntry = normal(postV(), GENERIC_RET_ALIAS,
                0x70007FE0L, rootN(), false, acceptedFp);
        int[] lowerCalls = new int[1];
        int[] budgetCalls = new int[1];
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, rawSize) -> {
            check(++budgetCalls[0] == 1, "finite first allocator budget only");
            check(pc == 0x4223BAEL && rawSize == SIZE, "full raw captured size budget argument");
            check(lowerCalls[0] == 0, "budget precedes actual lower CALL");
            trace.checkExactly(literal.subList(0, 1), "RBX save before budget; no eager callee RET read");
            trace.add(e("BUDGET", pc, rawSize));
        };
        KnownPageAllocateFp622.RetryCalls calls = frame -> {
            check(++lowerCalls[0] == 1 && budgetCalls[0] == 1, "one actual allocator lower");
            firstLower(frame, unknown);
            trace.checkExactly(literal.subList(0, 3), "actual lower push follows budget");
            trace.add(e("PORT_INVOKE", 0x4223BAEL, 0x42420B8L));
            memory.writeByte(MARKER, 0x11);
            memory.writeQword(T, GENERIC_RET_ALIAS);
            return lowerOffer;
        };
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(genericEntry(), true, unknown);
        QueueFp604Api.Outcome result = Retry60EntryFp649.execute(input, memory, calls, budget);
        if (!(result instanceof QueueFp604Api.Normal actual)) throw new AssertionError("generic entry must return Normal");
        checkEqual(expectedEntry, actual, "full generic actual284 NR/V/N/DF/currentFP");
        check(actual != lowerOffer, "entry Normal is a different frame from lower Normal");
        check(actual.postMxcsr() == acceptedFp && !actual.base().postDirectionFlagSet(),
                "accepted lower SAME partial FP and changed DF reach generic result");
        check(actual.base().normalReturn().volatileBits().raxBits() == 0x9000000000000000L,
                "full nonzero RAX survives even though low EAX is zero");
        check(actual.base().normalReturn().nonvolatileBits().r12Bits() == 0xCABCDEFF00000505L,
                "complete raw R12 retained without truncation");
        check(actual.base().normalReturn().returnRipBits() == GENERIC_RET_ALIAS
                && actual.base().normalReturn().returnRipBits() != IMAGE + 0x8571DCL,
                "fresh generic RET reports alias; no speculative caller guard or wholeD0 claim");
        check(lowerCalls[0] == 1 && budgetCalls[0] == 1, "no retry-handler or second allocator");
        trace.checkExactly(literal, "all8 direct-entry events and no parent RET");
        checkFullBytes(expected, memory, "all232 direct-entry bytes including padding and retained alias");
        check(memory.peekScalar(ROOT_SP, 8) == 0x140222222L, "root return slot unchanged and unexecuted");
    }

    public static void wholeAncestorNormalAcceptedButInnerGuardRejects() {
        Map<Long, Byte> initial = wholeInitial();
        Map<Long, Byte> expected = badExpected();
        List<Event> literal = badEvents();
        Trace trace = new Trace();
        Ram memory = new Ram(trace);
        seedCommon(memory);
        checkFullBytes(initial, memory, "all232 whole-entry initial bytes");
        QueueFp604Api.Mxcsr unknown = new QueueFp604Api.Mxcsr(0, 0);
        QueueFp604Api.Mxcsr rejectedFp = new QueueFp604Api.Mxcsr(0x200, 0x300);
        // Valid for the actual648 ancestor; independently wrong for all three inner622 fields.
        QueueFp604Api.Normal bad = normal(postV(), IMAGE + 0x8571DCL,
                0x70007FE0L, rootN(), false, rejectedFp);
        int[] parentCalls = new int[1];
        int[] lowerCalls = new int[1];
        int[] budgetCalls = new int[1];
        int[] foreignCalls = new int[1];
        int[] acceptingProbe = new int[1];
        boolean[] badReturned = new boolean[1];
        DefaultStaticFp648Api.CallFrame[] actualParent = new DefaultStaticFp648Api.CallFrame[1];
        IllegalArgumentException[] at649Boundary = new IllegalArgumentException[1];
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, rawSize) -> {
            check(++budgetCalls[0] == 1 && parentCalls[0] == 1 && lowerCalls[0] == 0,
                    "one actual BAE budget before lower push");
            check(pc == 0x4223BAEL && rawSize == SIZE, "same raw captured size budget");
            trace.checkExactly(literal.subList(0, 2), "actual D0 push and284 RBX save before budget");
            trace.add(e("BUDGET", pc, rawSize));
        };
        KnownPageAllocateFp622.RetryCalls calls = frame -> {
            check(++lowerCalls[0] == 1 && budgetCalls[0] == 1, "one actual lower callback");
            firstLower(frame, unknown);
            trace.checkExactly(literal.subList(0, 4), "actual D0 and lower push prefix");
            trace.add(e("PORT_INVOKE", 0x4223BAEL, 0x42420B8L));
            memory.writeByte(MARKER, 0x41);
            memory.writeQword(ROOT_SP, ROOT_RET_ALIAS);
            check(actualParent[0] != null, "captured actual D0 parent frame exists");
            actualParent[0].checkNormalReturn(bad); // ACCEPT only; do not pre-call the inner guard.
            acceptingProbe[0]++;
            check(bad.base().normalReturn().returnRipBits() != frame.returnRipBits()
                    && bad.base().normalReturn().callerRspBits() != frame.original().rspBits()
                    && !bad.base().normalReturn().nonvolatileBits().equals(frame.original().nonvolatileBits()),
                    "same offer is independently wrong for inner RIP, SP and complete N");
            badReturned[0] = true;
            return bad;
        };
        DefaultStaticFp648Api.Calls foreign = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                foreignCalls[0]++;
                throw new AssertionError("actual D0 must select649: " + frame);
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                foreignCalls[0]++;
                throw new AssertionError("no release tail in ancestor-guard scene: " + frame);
            }
        };
        DefaultStaticFp648Api.Calls bound = DefaultAllocateKnownRetry649.bind(memory, calls, budget, foreign);
        trace.checkExactly(List.of(), "binder has no Memory/budget/callback effects");
        checkFullBytes(initial, memory, "binder leaves all232 initial bytes");
        check(parentCalls[0] == 0 && lowerCalls[0] == 0 && budgetCalls[0] == 0
                && foreignCalls[0] == 0, "binder performs no callback or budget work");
        DefaultStaticFp648Api.Calls observed = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                check(++parentCalls[0] == 1, "one actual D0 parent CALL");
                parentFrame(frame, unknown);
                actualParent[0] = frame;
                try {
                    return bound.invoke(frame);
                } catch (IllegalArgumentException rejection) {
                    at649Boundary[0] = rejection;
                    throw rejection;
                }
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                throw new AssertionError("unexpected D0 tail: " + frame);
            }
        };
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(rootEntry(), true, unknown);
        QueueFp604Api.Outcome result = null;
        IllegalArgumentException caught = null;
        try {
            result = DefaultAllocateWithFp648.fromSlot08(input, memory, observed);
        } catch (IllegalArgumentException rejection) {
            caught = rejection;
        }
        check(result == null && caught != null && caught == at649Boundary[0]
                && caught.getClass() == IllegalArgumentException.class
                && "Return RIP mismatch".equals(caught.getMessage()),
                "actual inner622 guard rejects; SAME exception escapes whole648");
        check(acceptingProbe[0] == 1 && badReturned[0], "actual648 ancestor accepted that SAME bad Normal first");
        check(parentCalls[0] == 1 && lowerCalls[0] == 1 && budgetCalls[0] == 1
                && foreignCalls[0] == 0, "exact actual parent/lower/budget/foreign counts");
        trace.checkExactly(literal, "all7 bad-NR events; no284 POP/RET or D0 own RET");
        checkFullBytes(expected, memory, "all232 prefix bytes, saved stack and callback root alias retained");
        check(memory.peekScalar(ROOT_SP, 8) == ROOT_RET_ALIAS
                && memory.peekScalar(T, 8) == IMAGE + 0x8571DCL, "both return-slot prefix effects retained");
        // Exceptions expose no architectural poststate; rejectedFp/postDF/V are not credited as adopted.
    }

    public static int verify() {
        genericFirstAllocationChangedStateFreshCalleeRetAlias();
        wholeAncestorNormalAcceptedButInnerGuardRejects();
        return 2;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
