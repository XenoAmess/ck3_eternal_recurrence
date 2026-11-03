package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.StaticFixture648.Event;
import org.xar.ck3.control.g2.m2.nativecode.StaticFixture648.Ram;
import static org.xar.ck3.control.g2.m2.nativecode.StaticFixture648.e;
import static org.xar.ck3.control.g2.m2.nativecode.StaticFixture648.e128;

/** New whole638 witnesses translated from the independently frozen 09:51:47 UTC oracle.
 * Release648 was subsequently read for a separate peer review; no expectation was changed.
 * No model CONTENT or candidate allocator/binder body was consumed. Source-only submission. */
public final class Range16DefaultWholeBoundary648 {
    private Range16DefaultWholeBoundary648() { }
    private static final long IMAGE = 0x140000000L;
    private static final long SP = 0x70002008L;
    private static final long HEADER = 0x60000L;
    private static final long OLD = 0x30000L;
    private static final long SOURCE = 0x40000L;
    private static final long NEW = 0x90000L;
    private static final long MARKER = 0x52000L;
    private static final long ROOT_RIP = 0x140123456L;

    private static void check(boolean condition, String what) {
        if (!condition) throw new AssertionError(what);
    }
    private static void equal(Object actual, Object expected, String what) {
        if (!Objects.equals(actual, expected))
            throw new AssertionError(what + ": actual=" + actual + ", expected=" + expected);
    }

    private static VolatileBits rootV() {
        return new VolatileBits(0x0000000000000101L, 0x0000000000060000L, 0x0000000000000001L, 0x0000000000040000L, 0x0000000000040010L, 0x0000000000000106L, 0x0000000000000107L,
                new Bits128(0x0000000000000108L, 0xfffffffffffffef7L),
                new Bits128(0x0000000000000109L, 0xfffffffffffffef6L),
                new Bits128(0x000000000000010aL, 0xfffffffffffffef5L),
                new Bits128(0x000000000000010bL, 0xfffffffffffffef4L),
                new Bits128(0x000000000000010cL, 0xfffffffffffffef3L),
                new Bits128(0x000000000000010dL, 0xfffffffffffffef2L));
    }

    private static NonvolatileBits rootN() {
        return new NonvolatileBits(0x0000000000000201L, 0x0000000000000202L, 0x0000000000000203L, 0x0000000000000204L, 0x0000000000000205L, 0x0000000000000206L, 0x0000000000000207L, 0x0000000000000208L,
                new Bits128(0x0000000000000209L, 0xfffffffffffffdf6L));
    }

    private static VolatileBits innerV() {
        return new VolatileBits(0x0000000000051000L, 0x0000000000000020L, 0x0000000000000020L, 0x0000000000000008L, 0x0000000000040010L, 0x0000000000000106L, 0x0000000000000107L,
                new Bits128(0x000000003fc00000L, 0x0000000000000000L),
                new Bits128(0x0000000000000109L, 0xfffffffffffffef6L),
                new Bits128(0x000000000000010aL, 0xfffffffffffffef5L),
                new Bits128(0x000000000000010bL, 0xfffffffffffffef4L),
                new Bits128(0x000000000000010cL, 0xfffffffffffffef3L),
                new Bits128(0x000000000000010dL, 0xfffffffffffffef2L));
    }

    private static NonvolatileBits allocationN() {
        return new NonvolatileBits(0x0000000000040000L, 0x0000000000000001L, 0x0000000000040010L, 0x0000000000060000L, 0x0000000000000205L, 0x0000000000000002L, 0x0000000000000001L, 0x0000000000000002L,
                new Bits128(0x0000000000000209L, 0xfffffffffffffdf6L));
    }

    private static VolatileBits tailV() {
        return new VolatileBits(0x0000000000051000L, 0x0000000000030000L, 0x0000000000030000L, 0x0000000000000008L, 0x0000000000030000L, 0x0000000000000010L, 0x0000000000000a07L,
                new Bits128(0x99aabbccddeeff00L, 0x0123456789abcdefL),
                new Bits128(0x0000000000000a09L, 0xfffffffffffff5f6L),
                new Bits128(0x0000000000000a0aL, 0xfffffffffffff5f5L),
                new Bits128(0x0000000000000a0bL, 0xfffffffffffff5f4L),
                new Bits128(0x0000000000000a0cL, 0xfffffffffffff5f3L),
                new Bits128(0x0000000000000a0dL, 0xfffffffffffff5f2L));
    }

    private static NonvolatileBits releaseN() {
        return new NonvolatileBits(0x0000000000040010L, 0x0000000000000001L, 0x0000000000040010L, 0x0000000000060000L, 0x0000000000090000L, 0x0000000000000002L, 0x0000000000000001L, 0x0000000000000002L,
                new Bits128(0x0000000000000209L, 0xfffffffffffffdf6L));
    }

    private static VolatileBits firstPostV() {
        return new VolatileBits(0x0000000000090000L, 0x0000000000000a02L, 0x0000000000000a03L, 0x0000000000000a04L, 0x0000000000000a05L, 0x0000000000000a06L, 0x0000000000000a07L,
                new Bits128(0x0000000000000a08L, 0xfffffffffffff5f7L),
                new Bits128(0x0000000000000a09L, 0xfffffffffffff5f6L),
                new Bits128(0x0000000000000a0aL, 0xfffffffffffff5f5L),
                new Bits128(0x0000000000000a0bL, 0xfffffffffffff5f4L),
                new Bits128(0x0000000000000a0cL, 0xfffffffffffff5f3L),
                new Bits128(0x0000000000000a0dL, 0xfffffffffffff5f2L));
    }

    private static VolatileBits secondPostV() {
        return new VolatileBits(0x0000000000000b01L, 0x0000000000000b02L, 0x0000000000000b03L, 0x0000000000000b04L, 0x0000000000000b05L, 0x0000000000000b06L, 0x0000000000000b07L,
                new Bits128(0x0000000000000b08L, 0xfffffffffffff4f7L),
                new Bits128(0x0000000000000b09L, 0xfffffffffffff4f6L),
                new Bits128(0x0000000000000b0aL, 0xfffffffffffff4f5L),
                new Bits128(0x0000000000000b0bL, 0xfffffffffffff4f4L),
                new Bits128(0x0000000000000b0cL, 0xfffffffffffff4f3L),
                new Bits128(0x0000000000000b0dL, 0xfffffffffffff4f2L));
    }

    private static GovernmentCrtBoundary185Api.Entry rootEntry() {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE, SP, rootV(), rootN());
    }
    private static GovernmentCrtBoundary185Api.Entry innerEntry() {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE, SP - 0x80L, innerV(), allocationN());
    }
    private static QueueFp604Api.Normal normal(VolatileBits v, long rip, long rsp,
            NonvolatileBits n, boolean df, QueueFp604Api.Mxcsr fp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v, rip, rsp, n), df), fp);
    }
    private static void checkInner(DefaultStaticFp648Api.CallFrame frame) {
        equal(frame.call(), new GovernmentCrtBoundary185Api.Call(0x8571D7L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4223B94L,
                SP - 0x78L, innerV(), allocationN()), "all B94 CALL fields and V/N");
        equal(frame.childEntry(), innerEntry(), "all B94 child entry fields");
        check(frame.instructionLength() == 5, "B94 instruction length");
        check(frame.returnRipBits() == IMAGE + 0x8571DCL, "B94 fixed source continuation");
        check(frame.directionFlagSet(), "B94 current DF");
        // CVT1 and MUL1.5 are exact; CVTT1.5 raises masked precision (0x20).
        check(frame.preMxcsr().valueBits() == 0x1FA0, "B94 current numeric FP value");
        check(frame.preMxcsr().knownMaskBits() == 0xFFFF, "B94 exact current numeric FP mask");
    }
    private static void checkTail(DefaultStaticFp648Api.TailFrame frame,
            QueueFp604Api.Mxcsr firstFp) {
        equal(frame.transfer(), new GovernmentCrtBoundary185Api.Tail(0x8571C8L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x40EC530L,
                new GovernmentCrtBoundary185Api.Entry(IMAGE, SP - 0x50L,
                        tailV(), releaseN())), "all nonzero release tail fields and V/N");
        check(!frame.directionFlagSet(), "release receives first offered DF");
        check(frame.preMxcsr() == firstFp, "release receives SAME first offered FP");
        check(frame.preMxcsr().valueBits() == 8 && frame.preMxcsr().knownMaskBits() == 12,
                "release retains partial current FP");
    }

    /** Independent byte-map construction. Only literal seeds are copied into actual fixture RAM. */
    private static Map<Long, Byte> initialBytes() {
        Map<Long, Byte> m = new HashMap<>();
        fill(m, 0x0000000070001f08L, 352, 90);
        fill(m, 0x0000000000060000L, 24, 204);
        fill(m, 0x0000000000030000L, 48, 204);
        fill(m, 0x0000000000040000L, 48, 204);
        fill(m, 0x0000000000090000L, 64, 204);
        fill(m, 0x0000000000050000L, 16, 204);
        fill(m, 0x0000000000051000L, 32, 204);
        fill(m, 0x0000000000052000L, 16, 204);
        put(m, 0x0000000070002008L, 8, 0x0000000140123456L);
        put(m, 0x0000000000060000L, 8, 0x0000000000030000L);
        put(m, 0x0000000000060008L, 4, 0x0000000000000001L);
        put(m, 0x000000000006000cL, 4, 0x0000000000000001L);
        put(m, 0x0000000000060010L, 8, 0x0000000000050000L);
        put(m, 0x0000000000050000L, 8, 0x0000000000051000L);
        put(m, 0x0000000000051008L, 8, 0x00000001408571d0L);
        put(m, 0x0000000000051010L, 8, 0x00000001408571c0L);
        put(m, 0x00000001449f64f0L, 4, 0x000000003fc00000L);
        put(m, 0x0000000000030000L, 8, 0x1111222233334444L);
        put(m, 0x0000000000030008L, 8, 0x5555666677778888L);
        put(m, 0x0000000000040000L, 8, 0x99aabbccddeeff00L);
        put(m, 0x0000000000040008L, 8, 0x0123456789abcdefL);
        check(m.size() == 604, "literal owned byte count");
        return m;
    }
    private static void fill(Map<Long, Byte> m, long address, int count, int value) {
        for (int i = 0; i < count; i++) m.put(address + i, (byte) value);
    }
    private static void put(Map<Long, Byte> m, long address, int width, long value) {
        for (int i = 0; i < width; i++) m.put(address + i, (byte) (value >>> (8 * i)));
    }
    /** Folds a finite literal write list; it does not simulate target control flow or read actual RAM. */
    private static Map<Long, Byte> afterLiteralWrites(Map<Long, Byte> initial, List<Event> literal) {
        Map<Long, Byte> expected = new HashMap<>(initial);
        for (Event event : literal) {
            switch (event.kind()) {
                case "W8" -> put(expected, event.address(), 1, event.a());
                case "W32" -> put(expected, event.address(), 4, event.a());
                case "W64" -> put(expected, event.address(), 8, event.a());
                case "W128" -> {
                    put(expected, event.address(), 8, event.a());
                    put(expected, event.address() + 8, 8, event.b());
                }
                default -> { /* The literal read/budget entries have no byte-map effect. */ }
            }
        }
        check(expected.size() == 604, "all expected writes stay within owned bytes");
        return expected;
    }

    private static List<Event> normalTrace() {
        return List.of(
                e("W64", 0x0000000070002000L, 0x0000000000000201L),
                e("W64", 0x0000000070001ff8L, 0x0000000000000203L),
                e("W64", 0x0000000070001ff0L, 0x0000000000000204L),
                e("W64", 0x0000000070001fe8L, 0x0000000000000207L),
                e("R32", 0x000000000006000cL, 0x0000000000000001L),
                e("W64", 0x0000000070002010L, 0x0000000000000202L),
                e("R32", 0x0000000000060008L, 0x0000000000000001L),
                e("W64", 0x0000000070001fe0L, 0x0000000000000208L),
                e("R64", 0x0000000000060010L, 0x0000000000050000L),
                e("W64", 0x0000000070002018L, 0x0000000000000205L),
                e("W64", 0x0000000070002020L, 0x0000000000000206L),
                e("R32", 0x00000001449f64f0L, 0x000000003fc00000L),
                e("R64", 0x0000000000050000L, 0x0000000000051000L),
                e("R64", 0x0000000000051008L, 0x00000001408571d0L),
                e("W64", 0x0000000070001fb8L, 0x00000001408c7134L),
                e("W64", 0x0000000070001f88L, 0x00000001408571dcL),
                e("W8", 0x0000000000052000L, 0x0000000000000011L),
                e("R64", 0x0000000070001f88L, 0x00000001408571dcL),
                e("R64", 0x0000000070001fb8L, 0x00000001408c7134L),
                e("R64", 0x0000000000060000L, 0x0000000000030000L),
                e("BUDGET", 0x00000000008c7150L, 0x0000000000030000L),
                e128("R128", 0x0000000000030000L, new Bits128(0x1111222233334444L, 0x5555666677778888L)),
                e128("W128", 0x0000000000090000L, new Bits128(0x1111222233334444L, 0x5555666677778888L)),
                e("BUDGET", 0x00000000008c7170L, 0x0000000000040000L),
                e128("R128", 0x0000000000040000L, new Bits128(0x99aabbccddeeff00L, 0x0123456789abcdefL)),
                e128("W128", 0x0000000000090010L, new Bits128(0x99aabbccddeeff00L, 0x0123456789abcdefL)),
                e("R64", 0x0000000000060000L, 0x0000000000030000L),
                e("R32", 0x000000000006000cL, 0x0000000000000001L),
                e("R64", 0x0000000000060010L, 0x0000000000050000L),
                e("R64", 0x0000000000050000L, 0x0000000000051000L),
                e("R64", 0x0000000000051010L, 0x00000001408571c0L),
                e("W64", 0x0000000070001fb8L, 0x00000001408c71daL),
                e("W8", 0x0000000000052001L, 0x0000000000000022L),
                e("W64", 0x0000000070001fb8L, 0x00000001408c71daL),
                e("R64", 0x0000000070001fb8L, 0x00000001408c71daL),
                e("W64", 0x0000000000060000L, 0x0000000000090000L),
                e("R64", 0x0000000070002018L, 0x0000000000000205L),
                e("W32", 0x0000000000060008L, 0x0000000000000002L),
                e("R64", 0x0000000070002020L, 0x0000000000000206L),
                e("W32", 0x000000000006000cL, 0x0000000000000002L),
                e("R64", 0x0000000070002010L, 0x0000000000000202L),
                e("R64", 0x0000000070001fe0L, 0x0000000000000208L),
                e("R64", 0x0000000070001fe8L, 0x0000000000000207L),
                e("R64", 0x0000000070001ff0L, 0x0000000000000204L),
                e("R64", 0x0000000070001ff8L, 0x0000000000000203L),
                e("R64", 0x0000000070002000L, 0x0000000000000201L),
                e("R64", 0x0000000070002008L, 0x0000000140123456L));
    }

    private static List<Event> stoppedTrace() {
        return List.of(
                e("W64", 0x0000000070002000L, 0x0000000000000201L),
                e("W64", 0x0000000070001ff8L, 0x0000000000000203L),
                e("W64", 0x0000000070001ff0L, 0x0000000000000204L),
                e("W64", 0x0000000070001fe8L, 0x0000000000000207L),
                e("R32", 0x000000000006000cL, 0x0000000000000001L),
                e("W64", 0x0000000070002010L, 0x0000000000000202L),
                e("R32", 0x0000000000060008L, 0x0000000000000001L),
                e("W64", 0x0000000070001fe0L, 0x0000000000000208L),
                e("R64", 0x0000000000060010L, 0x0000000000050000L),
                e("W64", 0x0000000070002018L, 0x0000000000000205L),
                e("W64", 0x0000000070002020L, 0x0000000000000206L),
                e("R32", 0x00000001449f64f0L, 0x000000003fc00000L),
                e("R64", 0x0000000000050000L, 0x0000000000051000L),
                e("R64", 0x0000000000051008L, 0x00000001408571d0L),
                e("W64", 0x0000000070001fb8L, 0x00000001408c7134L),
                e("W64", 0x0000000070001f88L, 0x00000001408571dcL),
                e("W8", 0x0000000000052000L, 0x0000000000000011L));
    }

    public static void growthUsesBothKnownDefaultEntries() {
        Map<Long, Byte> initial = initialBytes();
        List<Event> literal = normalTrace();
        Map<Long, Byte> expected = afterLiteralWrites(initial, literal);
        Ram memory = new Ram();
        memory.bytes.putAll(initial);
        int[] callCounts = new int[3]; // B94, release tail, forbidden outer fallback
        int[] budgetCount = new int[1];
        QueueFp604Api.Mxcsr entryFp = QueueFp604Api.Mxcsr.exact(0x1F80);
        QueueFp604Api.Mxcsr firstFp = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Mxcsr secondFp = new QueueFp604Api.Mxcsr(0x40, 0xC0);
        // Both complete outcomes exist before the target; no bank is copied from an observed frame.
        QueueFp604Api.Normal first = normal(firstPostV(), IMAGE + 0x8571DCL,
                SP - 0x78L, allocationN(), false, firstFp);
        QueueFp604Api.Normal second = normal(secondPostV(), IMAGE + 0x8C71DAL,
                SP - 0x48L, releaseN(), true, secondFp);
        QueueFp604Api.Normal rootExpected = normal(secondPostV(), ROOT_RIP,
                SP + 8, rootN(), true, secondFp);
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, cursor) -> {
            check(++budgetCount[0] <= 2, "finite two-step copy budget");
            if (budgetCount[0] == 1) {
                check(pc == 0x8C7150L && cursor == OLD, "first actual copy budget");
            } else {
                check(pc == 0x8C7170L && cursor == SOURCE, "second actual copy budget");
            }
            check(callCounts[0] == 1 && callCounts[1] == 0, "budgets follow B94 and precede release");
            memory.step(pc, cursor);
        };
        QueueFp604Api.Input input = new QueueFp604Api.Input(
                new FullCopy437Api.Input(rootEntry(), true, budget), entryFp);
        check(input.base().budget() == budget && input.mxcsr() == entryFp, "original shared input objects");
        DefaultStaticFp648Api.Calls defaults = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                check(++callCounts[0] == 1 && callCounts[1] == 0, "one first actual B94 callback");
                check(budgetCount[0] == 0, "no copy budget before allocation");
                checkInner(frame);
                equal(memory.events, literal.subList(0, 16), "complete prefix before B94 effects");
                memory.writeByte(MARKER, 0x11);
                // This explicit opaque B94 port owns its callee RET; the carrier then owns its own RET.
                check(memory.readQword(SP - 0x80L) == IMAGE + 0x8571DCL, "B94 owned RET");
                return first;
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                check(++callCounts[1] == 1 && callCounts[0] == 1, "one real release tail after B94");
                check(budgetCount[0] == 2, "both real copies precede release");
                checkTail(frame, firstFp);
                equal(memory.events, literal.subList(0, 32), "no eager read before release tail");
                memory.writeByte(MARKER + 1, 0x22);
                memory.writeQword(SP - 0x50L, IMAGE + 0x8C71DAL);
                check(memory.readQword(SP - 0x50L) == IMAGE + 0x8C71DAL, "tail port owns fresh RET");
                return second;
            }
        };
        Range16Fp638Api.Calls forbidden = frame -> {
            callCounts[2]++;
            throw new AssertionError("Selected default route reached foreign638: " + frame);
        };
        Range16Fp638Api.Calls bound = Range16KnownDefault648.bind(memory, defaults, forbidden);
        equal(memory.events, List.of(), "bind has no RAM/budget events");
        equal(memory.fullBytes(), initial, "bind has no byte effects");
        check(callCounts[0] == 0 && callCounts[1] == 0 && callCounts[2] == 0
                && budgetCount[0] == 0, "bind has no calls or budgets");
        QueueFp604Api.Outcome result = Range16FullState638.execute(input, memory, bound, 0x3729846L);
        if (!(result instanceof QueueFp604Api.Normal actual)) throw new AssertionError("whole638 must finish normally");
        equal(actual, rootExpected, "full root V/N/RIP/SP/DF/MXCSR");
        check(actual.postMxcsr() == secondFp, "root carries SAME second offered partial FP");
        check(actual.base().postDirectionFlagSet(), "root carries second offered DF");
        equal(actual.base().normalReturn().nonvolatileBits(), rootN(), "all root N restored");
        check(callCounts[0] == 1 && callCounts[1] == 1 && callCounts[2] == 0
                && budgetCount[0] == 2, "exact nested call and budget counts");
        equal(memory.events, literal, "all47 normal events");
        equal(memory.fullBytes(), expected, "all604 normal bytes, including padding and retained pushes");
        check(memory.peek(HEADER, 8) == NEW && memory.peek(HEADER + 8, 4) == 2
                && memory.peek(HEADER + 12, 4) == 2, "actual committed header");
    }

    public static void allocatorChildStoppedPrefix() {
        Map<Long, Byte> initial = initialBytes();
        List<Event> literal = stoppedTrace();
        Map<Long, Byte> expected = afterLiteralWrites(initial, literal);
        Ram memory = new Ram();
        memory.bytes.putAll(initial);
        int[] callCounts = new int[3];
        int[] budgetCount = new int[1];
        QueueFp604Api.Mxcsr entryFp = QueueFp604Api.Mxcsr.exact(0x1F80);
        QueueFp604Api.Mxcsr stoppedFp = new QueueFp604Api.Mxcsr(8, 12);
        // A chosen complete foreign poststate, pre-created from source literals, not the observed frame.
        QueueFp604Api.Stopped offered = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(innerEntry(), 0x4223B94L, false, stoppedFp),
                0, 0x8571D7L);
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, cursor) -> {
            budgetCount[0]++;
            throw new AssertionError("Stopped inner child must precede every copy budget");
        };
        QueueFp604Api.Input input = new QueueFp604Api.Input(
                new FullCopy437Api.Input(rootEntry(), true, budget), entryFp);
        check(input.base().budget() == budget && input.mxcsr() == entryFp, "original stopped-case input objects");
        DefaultStaticFp648Api.Calls defaults = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                check(++callCounts[0] == 1 && callCounts[1] == 0, "one real inner B94 before Stop");
                check(budgetCount[0] == 0, "Stop callback precedes any budget");
                checkInner(frame);
                equal(memory.events, literal.subList(0, 16), "complete source push prefix before Stop write");
                memory.writeByte(MARKER, 0x11);
                return offered;
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                callCounts[1]++;
                throw new AssertionError("release tail reached after inner Stopped: " + frame);
            }
        };
        Range16Fp638Api.Calls forbidden = frame -> {
            callCounts[2]++;
            throw new AssertionError("foreign638 reached in selected stopped case: " + frame);
        };
        Range16Fp638Api.Calls bound = Range16KnownDefault648.bind(memory, defaults, forbidden);
        equal(memory.events, List.of(), "stopped-case bind has no events");
        equal(memory.fullBytes(), initial, "stopped-case bind has no byte effects");
        check(callCounts[0] == 0 && callCounts[1] == 0 && callCounts[2] == 0
                && budgetCount[0] == 0, "stopped-case bind has no calls/budgets");
        QueueFp604Api.Outcome result = Range16FullState638.execute(input, memory, bound, 0x3729846L);
        check(result == offered, "SAME preexisting Stopped across real18, binding648 and whole638");
        equal(offered.snapshot().currentState(), innerEntry(), "all independently chosen stopped V/N/image/SP");
        check(offered.snapshot().instructionRva() == 0x4223B94L && !offered.snapshot().directionFlagSet(),
                "explicit stopped PC and DF");
        check(offered.snapshot().mxcsr() == stoppedFp && stoppedFp.valueBits() == 8
                && stoppedFp.knownMaskBits() == 12, "SAME complete chosen stopped partial FP");
        check(offered.reason() == QueueFp604Api.StopReason.MISSING_POST_STATE
                && offered.raisedConditionBits() == 0 && offered.originCallSiteRva() == 0x8571D7L,
                "complete chosen stopped metadata");
        check(callCounts[0] == 1 && callCounts[1] == 0 && callCounts[2] == 0
                && budgetCount[0] == 0, "no copies/release/fallback after Stop");
        equal(memory.events, literal, "all17 Stop-prefix events, no inner or outer RET");
        equal(memory.fullBytes(), expected, "all604 prefix bytes and untouched new-buffer padding");
        check(memory.peek(HEADER, 8) == OLD && memory.peek(HEADER + 8, 4) == 1
                && memory.peek(HEADER + 12, 4) == 1, "no header commit after Stop");
    }

    public static int verify() {
        growthUsesBothKnownDefaultEntries();
        allocatorChildStoppedPrefix();
        return 2;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
