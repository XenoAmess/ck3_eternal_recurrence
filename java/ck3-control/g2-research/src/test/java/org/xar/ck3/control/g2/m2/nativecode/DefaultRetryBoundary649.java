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

/** Owner fallback written after the rejected model END; author has read no model CONTENT
 * or649 implementation. The original six-scene private literal oracle remains unchanged.
 * These whole scenes use actual648 D0, NEW649 binding and actual284 lower boundaries.
 * The third method uses a separately frozen late-post-modelEND/parentCONTENT source append. */
public final class DefaultRetryBoundary649 {
    private DefaultRetryBoundary649() { }
    private static final long IMAGE = 0x140000000L;
    private static final long ROOT_SP = 0x70008008L;
    private static final long PRE = 0x70007FB0L;
    private static final long SIZE = 0xE000000000003333L;
    private static final long ROOT_ALIAS = 0x2122232425262728L;

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

    private static VolatileBits zeroV() {
        return new VolatileBits(0x0000000000000000L, 0x9200000000002002L, 0x9300000000002003L, 0x9400000000002004L, 0x9500000000002005L, 0x9600000000002006L, 0x9700000000002007L,
                new Bits128(0x3333000000000200L, 0xcccc000000000200L),
                new Bits128(0x3333000000000201L, 0xcccc000000000201L),
                new Bits128(0x3333000000000202L, 0xcccc000000000202L),
                new Bits128(0x3333000000000203L, 0xcccc000000000203L),
                new Bits128(0x3333000000000204L, 0xcccc000000000204L),
                new Bits128(0x3333000000000205L, 0xcccc000000000205L));
    }

    private static VolatileBits handlerInputV() {
        return new VolatileBits(0x0000000000000000L, 0xe000000000003333L, 0x9300000000002003L, 0x9400000000002004L, 0x9500000000002005L, 0x9600000000002006L, 0x9700000000002007L,
                new Bits128(0x3333000000000200L, 0xcccc000000000200L),
                new Bits128(0x3333000000000201L, 0xcccc000000000201L),
                new Bits128(0x3333000000000202L, 0xcccc000000000202L),
                new Bits128(0x3333000000000203L, 0xcccc000000000203L),
                new Bits128(0x3333000000000204L, 0xcccc000000000204L),
                new Bits128(0x3333000000000205L, 0xcccc000000000205L));
    }

    private static VolatileBits handlerOutputV() {
        return new VolatileBits(0xd00d000000000001L, 0xa200000000003002L, 0xa300000000003003L, 0xa400000000003004L, 0xa500000000003005L, 0xa600000000003006L, 0xa700000000003007L,
                new Bits128(0x5555000000000300L, 0xaaaa000000000300L),
                new Bits128(0x5555000000000301L, 0xaaaa000000000301L),
                new Bits128(0x5555000000000302L, 0xaaaa000000000302L),
                new Bits128(0x5555000000000303L, 0xaaaa000000000303L),
                new Bits128(0x5555000000000304L, 0xaaaa000000000304L),
                new Bits128(0x5555000000000305L, 0xaaaa000000000305L));
    }

    private static VolatileBits retryInputV() {
        return new VolatileBits(0xd00d000000000001L, 0xe000000000003333L, 0xa300000000003003L, 0xa400000000003004L, 0xa500000000003005L, 0xa600000000003006L, 0xa700000000003007L,
                new Bits128(0x5555000000000300L, 0xaaaa000000000300L),
                new Bits128(0x5555000000000301L, 0xaaaa000000000301L),
                new Bits128(0x5555000000000302L, 0xaaaa000000000302L),
                new Bits128(0x5555000000000303L, 0xaaaa000000000303L),
                new Bits128(0x5555000000000304L, 0xaaaa000000000304L),
                new Bits128(0x5555000000000305L, 0xaaaa000000000305L));
    }

    private static VolatileBits secondOutputV() {
        return new VolatileBits(0x8000000000000000L, 0xb200000000004002L, 0xb300000000004003L, 0xb400000000004004L, 0xb500000000004005L, 0xb600000000004006L, 0xb700000000004007L,
                new Bits128(0x7777000000000400L, 0x8888000000000400L),
                new Bits128(0x7777000000000401L, 0x8888000000000401L),
                new Bits128(0x7777000000000402L, 0x8888000000000402L),
                new Bits128(0x7777000000000403L, 0x8888000000000403L),
                new Bits128(0x7777000000000404L, 0x8888000000000404L),
                new Bits128(0x7777000000000405L, 0x8888000000000405L));
    }

    private static NonvolatileBits rootN() {
        return new NonvolatileBits(0x8000000000000101L, 0x9000000000000202L, 0xa000000000000303L, 0xb000000000000404L, 0xcabcdeff00000505L, 0xd000000000000606L, 0xe000000000000707L, 0xf000000000000808L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static NonvolatileBits lowerN() {
        return new NonvolatileBits(0xe000000000003333L, 0x9000000000000202L, 0xa000000000000303L, 0xb000000000000404L, 0xcabcdeff00000505L, 0xd000000000000606L, 0xe000000000000707L, 0xf000000000000808L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static GovernmentCrtBoundary185Api.Entry rootEntry() {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE, ROOT_SP, rootV(), rootN());
    }
    private static GovernmentCrtBoundary185Api.Entry firstChildEntry() {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE, 0x70007FA8L, childV(), lowerN());
    }
    private static QueueFp604Api.Normal normal(VolatileBits v, long rip, long sp,
            NonvolatileBits n, boolean df, QueueFp604Api.Mxcsr fp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v, rip, sp, n), df), fp);
    }
    private static void parentFrame(DefaultStaticFp648Api.CallFrame frame, QueueFp604Api.Mxcsr unknown) {
        checkEqual(new GovernmentCrtBoundary185Api.Call(0x8571D7L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4223B94L,
                0x70007FE0L, childV(), rootN()), frame.call(), "all actual D0 CALL fields");
        checkEqual(new GovernmentCrtBoundary185Api.Entry(IMAGE, 0x70007FD8L,
                childV(), rootN()), frame.childEntry(), "all actual B94 entry fields");
        check(frame.directionFlagSet() && frame.preMxcsr() == unknown,
                "parent current DF and SAME explicit unknown FP");
        check(frame.instructionLength() == 5 && frame.returnRipBits() == IMAGE + 0x8571DCL,
                "actual parent source continuation/length");
    }
    private static void lowerFrame(KnownPageAllocateFp622.RetryCall frame, long site,
            long target, long continuation, VolatileBits v, boolean df, QueueFp604Api.Mxcsr fp) {
        checkEqual(new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, PRE, v, lowerN()),
                frame.original(), "full original lower185.Call and V/N");
        checkEqual(new GovernmentCrtBoundary185Api.Entry(IMAGE, 0x70007FA8L, v, lowerN()),
                frame.childEntry(), "full actual lower Entry");
        check(frame.directionFlagSet() == df && frame.preMxcsr() == fp,
                "exact current lower DF and SAME offered FP object");
        check(frame.returnRipBits() == continuation && continuation - IMAGE - site == 5,
                "actual five-byte lower source continuation");
    }
    private static void seed(Ram memory) {
        memory.seedFill(0x70007F88L, 192, 90);
        memory.seedFill(0xB000L, 8, 204);
        memory.seedFill(0xE000000000003333L, 16, 221);
        memory.seedFill(0xD000000000002222L, 16, 238);
        memory.seedScalar(ROOT_SP, 8, 0x140222222L);
    }
    private static void region(Map<Long, Byte> bytes, long address, String hex) {
        byte[] literal = HexFormat.of().parseHex(hex);
        for (int i = 0; i < literal.length; i++) bytes.put(address + i, literal[i]);
    }

    private static Map<Long, Byte> initialBytes() {
        Map<Long, Byte> bytes = new HashMap<>();
        region(bytes, 0x0000000070007f88L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a22222240010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(bytes, 0x000000000000b000L, "cccccccccccccccc");
        region(bytes, 0xe000000000003333L, "dddddddddddddddddddddddddddddddd");
        region(bytes, 0xd000000000002222L, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
        check(bytes.size() == 232, "complete owned RAM extent");
        return bytes;
    }

    private static Map<Long, Byte> normalBytes() {
        Map<Long, Byte> bytes = new HashMap<>();
        region(bytes, 0x0000000070007f88L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ab33b2244010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a0101000000000080dc718540010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a28272625242322215a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(bytes, 0x000000000000b000L, "121314cccccccccc");
        region(bytes, 0xe000000000003333L, "dddddddddddddddddddddddddddddddd");
        region(bytes, 0xd000000000002222L, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
        check(bytes.size() == 232, "complete owned RAM extent");
        return bytes;
    }

    private static Map<Long, Byte> stoppedBytes() {
        Map<Long, Byte> bytes = new HashMap<>();
        region(bytes, 0x0000000070007f88L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ab33b2244010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a0101000000000080dc718540010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a28272625242322215a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(bytes, 0x000000000000b000L, "22cccccccccccccc");
        region(bytes, 0xe000000000003333L, "dddddddddddddddddddddddddddddddd");
        region(bytes, 0xd000000000002222L, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
        check(bytes.size() == 232, "complete owned RAM extent");
        return bytes;
    }

    private static List<Event> normalEvents() {
        return List.of(
                e("W64", 0x0000000070007fd8L, 0x00000001408571dcL),
                e("W64", 0x0000000070007fd0L, 0x8000000000000101L),
                e("BUDGET", 0x0000000004223baeL, 0xe000000000003333L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223bb3L),
                e("PORT_INVOKE", 0x0000000004223baeL, 0x00000000042420b8L),
                e("W8", 0x000000000000b000L, 0x0000000000000012L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223ba7L),
                e("PORT_INVOKE", 0x0000000004223ba2L, 0x000000000424cffcL),
                e("W8", 0x000000000000b001L, 0x0000000000000013L),
                e("BUDGET", 0x0000000004223baeL, 0xe000000000003333L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223bb3L),
                e("PORT_INVOKE", 0x0000000004223baeL, 0x00000000042420b8L),
                e("W8", 0x000000000000b002L, 0x0000000000000014L),
                e("W64", 0x0000000070008008L, 0x2122232425262728L),
                e("R64", 0x0000000070007fd0L, 0x8000000000000101L),
                e("R64", 0x0000000070007fd8L, 0x00000001408571dcL),
                e("R64", 0x0000000070008008L, 0x2122232425262728L));
    }

    private static List<Event> stoppedEvents() {
        return List.of(
                e("W64", 0x0000000070007fd8L, 0x00000001408571dcL),
                e("W64", 0x0000000070007fd0L, 0x8000000000000101L),
                e("BUDGET", 0x0000000004223baeL, 0xe000000000003333L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223bb3L),
                e("PORT_INVOKE", 0x0000000004223baeL, 0x00000000042420b8L),
                e("W8", 0x000000000000b000L, 0x0000000000000022L),
                e("W64", 0x0000000070008008L, 0x2122232425262728L));
    }

    public static void wholeActualRetryKeepsFullRaxAndCurrentFp() {
        Map<Long, Byte> initial = initialBytes();
        Map<Long, Byte> expected = normalBytes();
        List<Event> literal = normalEvents();
        Trace trace = new Trace();
        Ram memory = new Ram(trace);
        seed(memory);
        checkFullBytes(initial, memory, "all232 initial normal bytes");
        QueueFp604Api.Mxcsr unknown = new QueueFp604Api.Mxcsr(0, 0);
        QueueFp604Api.Mxcsr a = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Mxcsr b = new QueueFp604Api.Mxcsr(128, 192);
        QueueFp604Api.Mxcsr c = new QueueFp604Api.Mxcsr(256, 768);
        QueueFp604Api.Normal first = normal(zeroV(), IMAGE + 0x4223BB3L, PRE, lowerN(), false, a);
        QueueFp604Api.Normal handler = normal(handlerOutputV(), IMAGE + 0x4223BA7L, PRE, lowerN(), true, b);
        QueueFp604Api.Normal second = normal(secondOutputV(), IMAGE + 0x4223BB3L, PRE, lowerN(), false, c);
        QueueFp604Api.Normal b94Expected = normal(secondOutputV(), IMAGE + 0x8571DCL,
                0x70007FE0L, rootN(), false, c);
        QueueFp604Api.Normal rootExpected = normal(secondOutputV(), ROOT_ALIAS, ROOT_SP + 8,
                rootN(), false, c);
        int[] parentCount = new int[1];
        int[] lowerCount = new int[1];
        int[] budgetCount = new int[1];
        int[] foreignCount = new int[1];
        QueueFp604Api.Outcome[] selected = new QueueFp604Api.Outcome[1];
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, rawSize) -> {
            int turn = ++budgetCount[0];
            check(turn <= 2 && pc == 0x4223BAEL && rawSize == SIZE, "two exact BAE raw-size budgets");
            if (turn == 1) {
                check(lowerCount[0] == 0 && parentCount[0] == 1, "first budget before allocator lower");
                trace.checkExactly(literal.subList(0, 2), "parent push and284 RBX save precede first budget");
            } else {
                check(lowerCount[0] == 2 && parentCount[0] == 1, "second budget follows accepted handler");
                trace.checkExactly(literal.subList(0, 9), "no budget for handler; second allocator not yet pushed");
            }
            trace.add(e("BUDGET", pc, rawSize));
        };
        KnownPageAllocateFp622.RetryCalls lower = frame -> {
            int turn = ++lowerCount[0];
            if (turn == 1) {
                check(budgetCount[0] == 1, "first allocation budget reached once");
                lowerFrame(frame, 0x4223BAEL, 0x42420B8L, IMAGE + 0x4223BB3L, childV(), true, unknown);
                trace.checkExactly(literal.subList(0, 4), "complete first allocator push prefix");
                trace.add(e("PORT_INVOKE", 0x4223BAEL, 0x42420B8L));
                memory.writeByte(0xB000L, 0x12);
                return first;
            }
            if (turn == 2) {
                check(budgetCount[0] == 1, "no extra budget before handler");
                lowerFrame(frame, 0x4223BA2L, 0x424CFFCL, IMAGE + 0x4223BA7L, handlerInputV(), false, a);
                trace.checkExactly(literal.subList(0, 7), "actual handler push after first zero allocation");
                trace.add(e("PORT_INVOKE", 0x4223BA2L, 0x424CFFCL));
                memory.writeByte(0xB001L, 0x13);
                return handler;
            }
            check(turn == 3 && budgetCount[0] == 2, "only third callback is second allocator");
            lowerFrame(frame, 0x4223BAEL, 0x42420B8L, IMAGE + 0x4223BB3L, retryInputV(), true, b);
            check(frame.original().volatileBits().raxBits() == 0xD00D000000000001L
                    && (int) frame.original().volatileBits().raxBits() == 1,
                    "handler TEST EAX requests retry while full high RAX survives");
            trace.checkExactly(literal.subList(0, 11), "second allocator push after its own budget");
            trace.add(e("PORT_INVOKE", 0x4223BAEL, 0x42420B8L));
            memory.writeByte(0xB002L, 0x14);
            memory.writeQword(ROOT_SP, ROOT_ALIAS);
            return second;
        };
        DefaultStaticFp648Api.Calls foreign = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                foreignCount[0]++;
                throw new AssertionError("D0 must select known649: " + frame);
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                foreignCount[0]++;
                throw new AssertionError("no release tail in whole retry scene: " + frame);
            }
        };
        DefaultStaticFp648Api.Calls bound = DefaultAllocateKnownRetry649.bind(memory, lower, budget, foreign);
        trace.checkExactly(List.of(), "normal bind adds no events");
        checkFullBytes(initial, memory, "normal bind adds no byte effects");
        check(parentCount[0] == 0 && lowerCount[0] == 0 && budgetCount[0] == 0
                && foreignCount[0] == 0, "normal bind adds no callback or budget");
        DefaultStaticFp648Api.Calls observed = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                check(++parentCount[0] == 1, "one actual D0 owned CALL");
                parentFrame(frame, unknown);
                QueueFp604Api.Outcome outcome = bound.invoke(frame);
                if (!(outcome instanceof QueueFp604Api.Normal b94)) throw new AssertionError("actual whole B94 Normal");
                checkEqual(b94Expected, b94, "complete actual284 return frame before D0 own RET");
                check(b94.postMxcsr() == c && b94 != second, "SAME final FP; whole B94 differs from lower Normal");
                selected[0] = outcome;
                return outcome;
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                throw new AssertionError("unexpected D0 tail: " + frame);
            }
        };
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(rootEntry(), true, unknown);
        QueueFp604Api.Outcome result = DefaultAllocateWithFp648.fromSlot08(input, memory, observed);
        if (!(result instanceof QueueFp604Api.Normal actual)) throw new AssertionError("whole D0 must finish Normal");
        checkEqual(rootExpected, actual, "all final root V/XMM/N/SP/RIP/DF/FP");
        check(actual.postMxcsr() == c && !actual.base().postDirectionFlagSet(), "SAME partialC and adopted final DF");
        check(actual.base().normalReturn().volatileBits().raxBits() == 0x8000000000000000L
                && (int) actual.base().normalReturn().volatileBits().raxBits() == 0,
                "full64 nonzero allocator success despite low EAX zero");
        check(actual.base().normalReturn().nonvolatileBits().r12Bits() == 0xCABCDEFF00000505L,
                "full raw nonvolatile R12 retained");
        check(selected[0] != null && parentCount[0] == 1 && lowerCount[0] == 3
                && budgetCount[0] == 2 && foreignCount[0] == 0, "exact Normal nested callback/budget counts");
        trace.checkExactly(literal, "all17 Normal events including actual284 POP/RET and fresh D0 RET alias");
        checkFullBytes(expected, memory, "all232 Normal bytes and untouched padding");
    }

    public static void wholeInnerStoppedKeepsSameIdentity() {
        Map<Long, Byte> initial = initialBytes();
        Map<Long, Byte> expected = stoppedBytes();
        List<Event> literal = stoppedEvents();
        Trace trace = new Trace();
        Ram memory = new Ram(trace);
        seed(memory);
        checkFullBytes(initial, memory, "all232 first-lower Stop initial bytes");
        QueueFp604Api.Mxcsr unknown = new QueueFp604Api.Mxcsr(0, 0);
        QueueFp604Api.Stopped offered = new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(firstChildEntry(), 0x42420B8L, true, unknown), 0, 0x4223BAEL);
        int[] parentCount = new int[1];
        int[] lowerCount = new int[1];
        int[] budgetCount = new int[1];
        int[] foreignCount = new int[1];
        QueueFp604Api.Outcome[] selected = new QueueFp604Api.Outcome[1];
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, rawSize) -> {
            check(++budgetCount[0] == 1 && lowerCount[0] == 0 && parentCount[0] == 1,
                    "one budget before first-lower Stop");
            check(pc == 0x4223BAEL && rawSize == SIZE, "first Stop raw-size budget");
            trace.checkExactly(literal.subList(0, 2), "D0 push and284 RBX save before Stop budget");
            trace.add(e("BUDGET", pc, rawSize));
        };
        KnownPageAllocateFp622.RetryCalls lower = frame -> {
            check(++lowerCount[0] == 1 && budgetCount[0] == 1, "FIRST actual BAE lower Stop");
            lowerFrame(frame, 0x4223BAEL, 0x42420B8L, IMAGE + 0x4223BB3L, childV(), true, unknown);
            trace.checkExactly(literal.subList(0, 4), "complete source push prefix before Stop effects");
            trace.add(e("PORT_INVOKE", 0x4223BAEL, 0x42420B8L));
            memory.writeByte(0xB000L, 0x22);
            memory.writeQword(ROOT_SP, ROOT_ALIAS);
            return offered;
        };
        DefaultStaticFp648Api.Calls foreign = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                foreignCount[0]++;
                throw new AssertionError("first Stop must select known649: " + frame);
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                foreignCount[0]++;
                throw new AssertionError("no tail after first Stop: " + frame);
            }
        };
        DefaultStaticFp648Api.Calls bound = DefaultAllocateKnownRetry649.bind(memory, lower, budget, foreign);
        trace.checkExactly(List.of(), "first Stop bind adds no events");
        checkFullBytes(initial, memory, "first Stop bind adds no byte effects");
        check(parentCount[0] == 0 && lowerCount[0] == 0 && budgetCount[0] == 0
                && foreignCount[0] == 0, "first Stop bind adds no callbacks/budget");
        DefaultStaticFp648Api.Calls observed = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                check(++parentCount[0] == 1, "one D0 parent before first Stop");
                parentFrame(frame, unknown);
                QueueFp604Api.Outcome outcome = bound.invoke(frame);
                check(outcome == offered, "SAME first-lower Stop through entry649 and binder649");
                selected[0] = outcome;
                return outcome;
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                throw new AssertionError("unexpected D0 tail after Stop: " + frame);
            }
        };
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(rootEntry(), true, unknown);
        QueueFp604Api.Outcome result = DefaultAllocateWithFp648.fromSlot08(input, memory, observed);
        check(result == offered && selected[0] == offered, "SAME precreated full Stop through whole D0");
        checkEqual(firstChildEntry(), offered.snapshot().currentState(), "complete independent Stop V/N/image/SP");
        check(offered.snapshot().instructionRva() == 0x42420B8L && offered.snapshot().directionFlagSet()
                && offered.snapshot().mxcsr() == unknown && offered.raisedConditionBits() == 0
                && offered.reason() == QueueFp604Api.StopReason.MISSING_POST_STATE
                && offered.originCallSiteRva() == 0x4223BAEL, "all chosen Stop metadata and SAME unknown FP");
        check(parentCount[0] == 1 && lowerCount[0] == 1 && budgetCount[0] == 1
                && foreignCount[0] == 0, "no retry/handler/budget/foreign continuation after first Stop");
        trace.checkExactly(literal, "all7 first-lower Stop events, no284 POP/RET or D0 own RET");
        checkFullBytes(expected, memory, "all232 first Stop prefix bytes and retained rootRET alias");
    }

    private static Map<Long, Byte> thirdStoppedBytes() {
        Map<Long, Byte> bytes = new HashMap<>();
        region(bytes, 0x0000000070007f88L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ab33b2244010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a0101000000000080dc718540010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a28272625242322215a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(bytes, 0x000000000000b000L, "121324cccccccccc");
        region(bytes, 0xe000000000003333L, "dddddddddddddddddddddddddddddddd");
        region(bytes, 0xd000000000002222L, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
        check(bytes.size() == 232, "complete late third-Stop owned extent");
        return bytes;
    }

    private static List<Event> thirdStoppedEvents() {
        return List.of(
                e("W64", 0x0000000070007fd8L, 0x00000001408571dcL),
                e("W64", 0x0000000070007fd0L, 0x8000000000000101L),
                e("BUDGET", 0x0000000004223baeL, 0xe000000000003333L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223bb3L),
                e("PORT_INVOKE", 0x0000000004223baeL, 0x00000000042420b8L),
                e("W8", 0x000000000000b000L, 0x0000000000000012L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223ba7L),
                e("PORT_INVOKE", 0x0000000004223ba2L, 0x000000000424cffcL),
                e("W8", 0x000000000000b001L, 0x0000000000000013L),
                e("BUDGET", 0x0000000004223baeL, 0xe000000000003333L),
                e("W64", 0x0000000070007fa8L, 0x0000000144223bb3L),
                e("PORT_INVOKE", 0x0000000004223baeL, 0x00000000042420b8L),
                e("W8", 0x000000000000b002L, 0x0000000000000024L),
                e("W64", 0x0000000070008008L, 0x2122232425262728L));
    }

    /** New late source append, frozen after model END/parent CONTENT; not one of original six. */
    public static void wholeThirdLowerStoppedKeepsAcceptedState() {
        Map<Long, Byte> initial = initialBytes();
        Map<Long, Byte> expected = thirdStoppedBytes();
        List<Event> literal = thirdStoppedEvents();
        Trace trace = new Trace();
        Ram memory = new Ram(trace);
        seed(memory);
        checkFullBytes(initial, memory, "all232 late third-Stop initial bytes");
        QueueFp604Api.Mxcsr unknown = new QueueFp604Api.Mxcsr(0, 0);
        QueueFp604Api.Mxcsr a = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Mxcsr b = new QueueFp604Api.Mxcsr(128, 192);
        QueueFp604Api.Normal first = normal(zeroV(), IMAGE + 0x4223BB3L, PRE, lowerN(), false, a);
        QueueFp604Api.Normal handler = normal(handlerOutputV(), IMAGE + 0x4223BA7L, PRE, lowerN(), true, b);
        // The full chosen third-lower snapshot is precreated from append literals, never an observed frame.
        QueueFp604Api.Stopped offered = new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(IMAGE, 0x70007FA8L,
                        retryInputV(), lowerN()), 0x42420B8L, true, b), 0, 0x4223BAEL);
        int[] parentCount = new int[1];
        int[] lowerCount = new int[1];
        int[] budgetCount = new int[1];
        int[] foreignCount = new int[1];
        QueueFp604Api.Outcome[] selected = new QueueFp604Api.Outcome[1];
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, rawSize) -> {
            int turn = ++budgetCount[0];
            check(turn <= 2 && pc == 0x4223BAEL && rawSize == SIZE, "two late-Stop raw-size BAE budgets");
            if (turn == 1) {
                check(lowerCount[0] == 0 && parentCount[0] == 1, "first budget before first allocation");
                trace.checkExactly(literal.subList(0, 2), "late-Stop first source saves before budget");
            } else {
                check(lowerCount[0] == 2 && parentCount[0] == 1, "second budget follows two accepted Normal offers");
                trace.checkExactly(literal.subList(0, 9), "late-Stop second budget before third lower push");
            }
            trace.add(e("BUDGET", pc, rawSize));
        };
        KnownPageAllocateFp622.RetryCalls lower = frame -> {
            int turn = ++lowerCount[0];
            if (turn == 1) {
                check(budgetCount[0] == 1, "one budget before zero allocator offer");
                lowerFrame(frame, 0x4223BAEL, 0x42420B8L, IMAGE + 0x4223BB3L, childV(), true, unknown);
                trace.checkExactly(literal.subList(0, 4), "late-Stop actual first allocation prefix");
                trace.add(e("PORT_INVOKE", 0x4223BAEL, 0x42420B8L));
                memory.writeByte(0xB000L, 0x12);
                return first;
            }
            if (turn == 2) {
                check(budgetCount[0] == 1, "handler owns no extra budget");
                lowerFrame(frame, 0x4223BA2L, 0x424CFFCL, IMAGE + 0x4223BA7L, handlerInputV(), false, a);
                trace.checkExactly(literal.subList(0, 7), "late-Stop actual handler prefix");
                trace.add(e("PORT_INVOKE", 0x4223BA2L, 0x424CFFCL));
                memory.writeByte(0xB001L, 0x13);
                return handler;
            }
            check(turn == 3 && budgetCount[0] == 2, "new Stop is THIRD lower after actual retry");
            lowerFrame(frame, 0x4223BAEL, 0x42420B8L, IMAGE + 0x4223BB3L, retryInputV(), true, b);
            check(frame.original().volatileBits().raxBits() == 0xD00D000000000001L
                    && (int) frame.original().volatileBits().raxBits() == 1,
                    "complete handler RAX retained after EAX1 retry branch");
            trace.checkExactly(literal.subList(0, 11), "late-Stop real third lower owned push");
            trace.add(e("PORT_INVOKE", 0x4223BAEL, 0x42420B8L));
            memory.writeByte(0xB002L, 0x24);
            memory.writeQword(ROOT_SP, ROOT_ALIAS);
            return offered;
        };
        DefaultStaticFp648Api.Calls foreign = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                foreignCount[0]++;
                throw new AssertionError("late third Stop must select known649: " + frame);
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                foreignCount[0]++;
                throw new AssertionError("no tail after late third Stop: " + frame);
            }
        };
        DefaultStaticFp648Api.Calls bound = DefaultAllocateKnownRetry649.bind(memory, lower, budget, foreign);
        trace.checkExactly(List.of(), "late third-Stop bind has no events");
        checkFullBytes(initial, memory, "late third-Stop bind has no byte effects");
        check(parentCount[0] == 0 && lowerCount[0] == 0 && budgetCount[0] == 0
                && foreignCount[0] == 0, "late third-Stop bind has no callbacks/budget");
        DefaultStaticFp648Api.Calls observed = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                check(++parentCount[0] == 1, "one actual D0 parent before late third Stop");
                parentFrame(frame, unknown);
                QueueFp604Api.Outcome outcome = bound.invoke(frame);
                check(outcome == offered, "SAME third-lower Stop through649 entry/binder");
                selected[0] = outcome;
                return outcome;
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                throw new AssertionError("unexpected D0 tail after late third Stop: " + frame);
            }
        };
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(rootEntry(), true, unknown);
        QueueFp604Api.Outcome result = DefaultAllocateWithFp648.fromSlot08(input, memory, observed);
        check(result == offered && selected[0] == offered, "SAME precreated third Stop through whole D0");
        checkEqual(new GovernmentCrtBoundary185Api.Entry(IMAGE, 0x70007FA8L, retryInputV(), lowerN()),
                offered.snapshot().currentState(), "independent complete third Stop entry/V/N");
        check(offered.snapshot().instructionRva() == 0x42420B8L && offered.snapshot().directionFlagSet()
                && offered.snapshot().mxcsr() == b && b.valueBits() == 128 && b.knownMaskBits() == 192,
                "third Stop retains SAME accepted handler partialB and DFtrue");
        check(offered.reason() == QueueFp604Api.StopReason.MISSING_POST_STATE
                && offered.raisedConditionBits() == 0 && offered.originCallSiteRva() == 0x4223BAEL,
                "complete chosen third Stop reason/conditions/origin without remap");
        check(parentCount[0] == 1 && lowerCount[0] == 3 && budgetCount[0] == 2
                && foreignCount[0] == 0, "two accepted Normal offers then terminal third-lower Stop");
        trace.checkExactly(literal, "all14 late third-Stop prefix events, no284 POP/RET or D0 own RET");
        checkFullBytes(expected, memory, "all232 late third-Stop bytes retain both Normal effects and final alias");
    }

    public static int verify() {
        wholeActualRetryKeepsFullRaxAndCurrentFp();
        wholeInnerStoppedKeepsSameIdentity();
        wholeThirdLowerStoppedKeepsAcceptedState();
        return 3;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
