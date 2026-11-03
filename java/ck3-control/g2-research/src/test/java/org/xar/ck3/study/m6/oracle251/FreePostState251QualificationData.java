package org.xar.ck3.study.m6.oracle251;

import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Independent finite data, not a producer, callback, memory adapter, or executable test.
 * SOURCE_ONLY: never compiled or run by this author. No future 251 API is assumed.
 * All post environments and stop snapshots below are explicit synthetic suppliers.
 * No FP arithmetic, kernel effect, native default, or natural stop reachability is claimed.
 */
public final class FreePostState251QualificationData {
    private FreePostState251QualificationData() { }

    public static final long I = 0x140000000L;
    public static final long S = 0xA008L;
    public static final long P = 0x9FE0L;
    public static final long C = 0x9FD8L;
    public static final long BLOCK = 0xB251008L;
    public static final long HEAP = 0xB251100L;
    public static final long DESTINATION = 0xB251200L;
    public static final long ARTIFICIAL_TARGET_FIRST = 0xBAD25101L;
    public static final long ARTIFICIAL_TARGET_THIRD = 0xBAD25102L;
    public static final long INITIAL_OUTER_RET = 0xDEAD2510L;
    public static final long SCRIPT_OUTER_RET = 0xDEAD2511L;
    public static final long SCRIPT_SAVED_RBX = 0xCAFE2511L;

    /** Own data label; this is not a proposed production input type. */
    public record Environment(boolean df, QueueFp604Api.Mxcsr mxcsr) { }
    public static final Environment E0 = new Environment(true, new QueueFp604Api.Mxcsr(0x6000, 0xFFC0));
    public static final Environment E1 = new Environment(false, new QueueFp604Api.Mxcsr(0x6001, 0xFFFF));
    public static final Environment E2 = new Environment(true, new QueueFp604Api.Mxcsr(0x6004, 0xFFFF));
    public static final Environment E3 = new Environment(false, new QueueFp604Api.Mxcsr(0x6020, 0xFFFF));
    public static final Environment E4 = new Environment(true, new QueueFp604Api.Mxcsr(0x6030, 0xFFFF));

    public static final NonvolatileBits ENTRY_N = new NonvolatileBits(
            0x251000B0L, 0x251000B1L, 0x251000B2L, 0x251000B3L,
            0xFEDCBA9825100012L, 0x25100013L, 0x25100014L, 0x25100015L,
            new Bits128(0x2510006000000001L, 0x2510006000000002L));
    public static final NonvolatileBits DESTINATION_N = new NonvolatileBits(
            DESTINATION, 0x251000B1L, 0x251000B2L, 0x251000B3L,
            0xFEDCBA9825100012L, 0x25100013L, 0x25100014L, 0x25100015L,
            new Bits128(0x2510006000000001L, 0x2510006000000002L));
    public static final NonvolatileBits FINAL_N = new NonvolatileBits(
            SCRIPT_SAVED_RBX, 0x251000B1L, 0x251000B2L, 0x251000B3L,
            0xFEDCBA9825100012L, 0x25100013L, 0x25100014L, 0x25100015L,
            new Bits128(0x2510006000000001L, 0x2510006000000002L));

    public static final VolatileBits NULL_ENTRY_V = v(
            0x1010101000000001L, 0L, 0x10100002L, 0x10100008L,
            0x10100009L, 0x10100010L, 0x10100011L, 0x1000L);
    public static final VolatileBits NONNULL_ENTRY_V = v(
            0x1010101000000001L, BLOCK, 0x10100002L, 0x10100008L,
            0x10100009L, 0x10100010L, 0x10100011L, 0x1000L);
    public static final VolatileBits NULL_FINAL_V = v(
            0L, 0L, 0x10100002L, 0x10100008L,
            0x10100009L, 0x10100010L, 0x10100011L, 0x1000L);
    public static final VolatileBits FIRST_CALL_V = v(
            0L, HEAP, 0L, BLOCK, 0x10100009L, 0x10100010L, 0x10100011L, 0x1000L);
    public static final VolatileBits FIRST_NORMAL_V = v(
            0xFACE251000000000L, 0x11110001L, 0x11110002L, 0x11110008L,
            0x11110009L, 0x11110010L, 0x11110011L, 0x1100L);
    public static final VolatileBits SECOND_NORMAL_V = v(
            DESTINATION, 0x22220001L, 0x22220002L, 0x22220008L,
            0x22220009L, 0x22220010L, 0x22220011L, 0x2200L);
    public static final VolatileBits THIRD_NORMAL_V = v(
            0x11223344FEDCBA98L, 0x33330001L, 0x33330002L, 0x33330008L,
            0x33330009L, 0x33330010L, 0x33330011L, 0x3300L);
    public static final VolatileBits FOURTH_CALL_V = v(
            0x11223344FEDCBA98L, 0x00000000FEDCBA98L, 0x33330002L, 0x33330008L,
            0x33330009L, 0x33330010L, 0x33330011L, 0x3300L);
    public static final VolatileBits FOURTH_NORMAL_V = v(
            0xAA55251089ABCDEFL, 0x44440001L, 0x44440002L, 0x44440008L,
            0x44440009L, 0x44440010L, 0x44440011L, 0x4400L);

    public static final GovernmentCrtBoundary185Api.Entry NULL_ENTRY =
            new GovernmentCrtBoundary185Api.Entry(I, S, NULL_ENTRY_V, ENTRY_N);
    public static final GovernmentCrtBoundary185Api.Entry NONNULL_ENTRY =
            new GovernmentCrtBoundary185Api.Entry(I, S, NONNULL_ENTRY_V, ENTRY_N);

    /** Explicit literal table. Unlike 437.CallFrame, this own data has no executable dispatch rule. */
    public record CallLiteral(
            GovernmentCrtBoundary185Api.Call beforeOwnedPush,
            GovernmentCrtBoundary185Api.Entry afterOwnedPush,
            Environment explicitInputEnvironment, int length, long returnRip) { }

    public static final CallLiteral CALL0 = call(0x424E37AL,
            GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, ARTIFICIAL_TARGET_FIRST,
            FIRST_CALL_V, ENTRY_N, E0, 6, 0x424E380L);
    public static final CallLiteral CALL1 = call(0x424E384L,
            GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x423B18CL,
            FIRST_NORMAL_V, ENTRY_N, E1, 5, 0x424E389L);
    public static final CallLiteral CALL2 = call(0x424E38CL,
            GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, ARTIFICIAL_TARGET_THIRD,
            SECOND_NORMAL_V, DESTINATION_N, E2, 6, 0x424E392L);
    public static final CallLiteral CALL3 = call(0x424E394L,
            GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x423B0D4L,
            FOURTH_CALL_V, DESTINATION_N, E3, 5, 0x424E399L);

    public static final QueueFp604Api.Normal NORMAL0 = normal(
            FIRST_NORMAL_V, ENTRY_N, I + 0x424E380L, P, E1);
    public static final QueueFp604Api.Normal NORMAL1 = normal(
            SECOND_NORMAL_V, ENTRY_N, I + 0x424E389L, P, E2);
    public static final QueueFp604Api.Normal NORMAL2 = normal(
            THIRD_NORMAL_V, DESTINATION_N, I + 0x424E392L, P, E3);
    public static final QueueFp604Api.Normal NORMAL3 = normal(
            FOURTH_NORMAL_V, DESTINATION_N, I + 0x424E399L, P, E4);
    public static final QueueFp604Api.Normal EXPECTED_NULL = normal(
            NULL_FINAL_V, ENTRY_N, INITIAL_OUTER_RET, 0xA010L, E0);
    public static final QueueFp604Api.Normal EXPECTED_FOUR_NORMAL = normal(
            FOURTH_NORMAL_V, FINAL_N, SCRIPT_OUTER_RET, 0xA010L, E4);

    /** Qword cells are literal supplied RAM, never a statement of current image contents. */
    public static final Map<Long, Long> INITIAL_QWORD_RAM = Map.of(
            I + 0x5C5DE30L, HEAP,
            I + 0x43DA748L, ARTIFICIAL_TARGET_FIRST,
            I + 0x43DA738L, ARTIFICIAL_TARGET_THIRD,
            S, INITIAL_OUTER_RET,
            S + 0x10L, 0x89ABCDEF76543210L,
            DESTINATION, 0x7654321013572468L,
            S - 8L, 0xA5A5251000000001L,
            C, 0xA5A5251000000002L);

    /** The only declared Q1 supplier RAM effects: first NORMAL callback writes these two cells. */
    public static final Map<Long, Long> FIRST_NORMAL_RAM_SCRIPT = Map.of(
            S - 8L, SCRIPT_SAVED_RBX,
            S, SCRIPT_OUTER_RET);

    public static final Map<Long, Long> NULL_FINAL_QWORD_RAM = Map.of(
            S, INITIAL_OUTER_RET,
            S + 0x10L, 0x89ABCDEF00000000L,
            S - 8L, 0xA5A5251000000001L,
            C, 0xA5A5251000000002L,
            DESTINATION, 0x7654321013572468L);
    public static final Map<Long, Long> FOUR_NORMAL_FINAL_QWORD_RAM = Map.of(
            S, SCRIPT_OUTER_RET,
            S + 0x10L, 0x89ABCDEF00000000L,
            S - 8L, SCRIPT_SAVED_RBX,
            C, I + 0x424E399L,
            DESTINATION, 0x7654321089ABCDEFL);

    public record NormalVector(String name, GovernmentCrtBoundary185Api.Entry entry,
            Environment inputEnvironment, Map<Long, Long> initialQwords,
            List<CallLiteral> calls, List<QueueFp604Api.Normal> suppliedNormals,
            Map<Long, Long> firstNormalRamScript,
            QueueFp604Api.Normal expectedNormal, Map<Long, Long> expectedFinalQwords) { }

    public static final NormalVector ZERO_CALL = new NormalVector(
            "Q0_ZERO_CALL_BOTH_TAILS", NULL_ENTRY, E0, INITIAL_QWORD_RAM,
            List.of(), List.of(), Map.of(), EXPECTED_NULL, NULL_FINAL_QWORD_RAM);
    public static final NormalVector FOUR_CALL = new NormalVector(
            "Q1_FOUR_CALL_SYNTHETIC_FULL_OUTCOME", NONNULL_ENTRY, E0, INITIAL_QWORD_RAM,
            List.of(CALL0, CALL1, CALL2, CALL3), List.of(NORMAL0, NORMAL1, NORMAL2, NORMAL3),
            FIRST_NORMAL_RAM_SCRIPT, EXPECTED_FOUR_NORMAL, FOUR_NORMAL_FINAL_QWORD_RAM);

    private static final NonvolatileBits SYNTHETIC_DEEP_N = new NonvolatileBits(
            0x515100B0L, 0x515100B1L, 0x515100B2L, 0x515100B3L,
            0xDEAD251251510012L, 0x51510013L, 0x51510014L, 0x51510015L,
            new Bits128(0x5151006000000001L, 0x5151006000000002L));
    private static final VolatileBits SYNTHETIC_DEEP_V = v(
            0x51510000L, 0x51510001L, 0x51510002L, 0x51510008L,
            0x51510009L, 0x51510010L, 0x51510011L, 0x5150L);

    /** Exact synthetic supplied objects: eventual consumer must preserve identity, not reconstruct. */
    public static final QueueFp604Api.Stopped FIRST_SUPPLIED_STOP = stopped(
            0xD25137AL, 0x424E37AL);
    public static final QueueFp604Api.Stopped SECOND_SUPPLIED_STOP = stopped(
            0xD251384L, 0x424E384L);

    public record StopPrefix(String name, List<CallLiteral> callsThroughStopped,
            List<QueueFp604Api.Normal> precedingNormals,
            Map<Long, Long> firstNormalRamScript,
            QueueFp604Api.Stopped suppliedStopObject,
            Map<Long, Long> expectedCompletedPrefixQwords,
            List<Long> forbiddenLaterCallRvas,
            boolean destinationStoreForbidden, boolean epilogueAndOuterRetReadForbidden) { }

    public static final StopPrefix FIRST_STOP = new StopPrefix(
            "FIRST_STOP_SYNTHETIC_CHILD_CURRENT_SNAPSHOT", List.of(CALL0), List.of(), Map.of(),
            FIRST_SUPPLIED_STOP,
            Map.of(S, INITIAL_OUTER_RET, S + 0x10L, 0x89ABCDEF00000000L,
                    S - 8L, ENTRY_N.rbxBits(), C, I + 0x424E380L,
                    DESTINATION, 0x7654321013572468L),
            List.of(0x424E384L, 0x424E38CL, 0x424E394L), true, true);
    public static final StopPrefix SECOND_STOP = new StopPrefix(
            "SECOND_STOP_BEFORE_MOV_RBX_RAX", List.of(CALL0, CALL1), List.of(NORMAL0),
            FIRST_NORMAL_RAM_SCRIPT, SECOND_SUPPLIED_STOP,
            Map.of(S, SCRIPT_OUTER_RET, S + 0x10L, 0x89ABCDEF00000000L,
                    S - 8L, SCRIPT_SAVED_RBX, C, I + 0x424E389L,
                    DESTINATION, 0x7654321013572468L),
            List.of(0x424E38CL, 0x424E394L), true, true);

    // Data constructors only. None executes a held instruction or accesses RAM.
    private static VolatileBits v(long ax, long cx, long dx, long r8, long r9,
            long r10, long r11, long x) {
        // Exact fully specified 128-bit lanes; these values do not stand for absent inputs.
        return new VolatileBits(ax, cx, dx, r8, r9, r10, r11,
                new Bits128(x + 0x00L, x + 0x01L), new Bits128(x + 0x10L, x + 0x11L),
                new Bits128(x + 0x20L, x + 0x21L), new Bits128(x + 0x30L, x + 0x31L),
                new Bits128(x + 0x40L, x + 0x41L), new Bits128(x + 0x50L, x + 0x51L));
    }

    private static CallLiteral call(long site, GovernmentCrtBoundary185Api.TargetKind kind,
            long target, VolatileBits v, NonvolatileBits n, Environment environment,
            int length, long returnRva) {
        return new CallLiteral(new GovernmentCrtBoundary185Api.Call(site, kind, target, P, v, n),
                new GovernmentCrtBoundary185Api.Entry(I, C, v, n), environment, length, I + returnRva);
    }

    private static QueueFp604Api.Normal normal(VolatileBits v, NonvolatileBits n,
            long rip, long sp, Environment environment) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v, rip, sp, n), environment.df()),
                environment.mxcsr());
    }

    private static QueueFp604Api.Stopped stopped(long labelledSyntheticPc, long actualOriginCallSite) {
        return new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(
                        I, 0x9FA8L, SYNTHETIC_DEEP_V, SYNTHETIC_DEEP_N),
                        labelledSyntheticPc, false, new QueueFp604Api.Mxcsr(0x6008, 0xFFFF)),
                0, actualOriginCallSite);
    }
}
