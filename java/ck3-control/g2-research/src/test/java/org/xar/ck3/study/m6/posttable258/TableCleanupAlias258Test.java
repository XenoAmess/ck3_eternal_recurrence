package org.xar.ck3.study.m6.posttable258;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full238.TransferFull238Api;
import org.xar.ck3.study.m6.postdefault255.DefaultFreeChain255;
import org.xar.ck3.study.m6.postentry242.WholeTransferPostState242;
import org.xar.ck3.study.m6.posterror256.Error32PostState256;
import org.xar.ck3.study.m6.posterror256.FreeKnownError256;
import org.xar.ck3.study.m6.postforward250.Known715PostForward250;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.posttable257.FreeKnownTable257;
import org.xar.ck3.study.m6.posttable257.TableDwordLeaf257;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;

/**
 * Owner100 single-scene manual; no compilation or execution claimed by this source.
 * Inputs and expectations mechanically projected from the independent frozen literal:
 * PRIVATE-LITERAL-ALIAS258-FROZEN.json SHA256
 * ff1ebaf97ddaf70ed585303d697c8d35d17b0b93d79125e8e8306b53eb03f37d.
 * Explicit artificial byte RAM/vtables/IAT and post-state supplies; no native data or FP defaults.
 * No runtime file, JSON or network input.
 * Seven existing port frames expose actual values. Known250 intercepts the first247
 * getter frame internally: its eighth fixture remains source-derived, with actual
 * push/read/RET trace and following second-frame input evidence. No hook is invented.
 */
public final class TableCleanupAlias258Test {
    private TableCleanupAlias258Test() { }
    private static final QueueFp604Api.Mxcsr M0 = new QueueFp604Api.Mxcsr(0x1F80, 0xFFC0);
    private static final QueueFp604Api.Mxcsr M1 = new QueueFp604Api.Mxcsr(0x3F82, 0xFFC2);
    private static final QueueFp604Api.Mxcsr M2 = new QueueFp604Api.Mxcsr(0x5F90, 0xFFD0);
    private static final QueueFp604Api.Mxcsr M3 = new QueueFp604Api.Mxcsr(0x7F89, 0xFFC9);
    private static final VolatileBits V_ROOT_V = new VolatileBits(0x9182736455463728L, 0x0000000000200000L, 0x0000000000210000L, 0x1111222233334444L, 0x2222333344445555L, 0x3333444455556666L, 0x4444555566667777L, new Bits128(0x1000000000000010L, 0x1000000000000020L), new Bits128(0x1000000000000011L, 0x1000000000000021L), new Bits128(0x1000000000000012L, 0x1000000000000022L), new Bits128(0x1000000000000013L, 0x1000000000000023L), new Bits128(0x1000000000000014L, 0x1000000000000024L), new Bits128(0x1000000000000015L, 0x1000000000000025L));
    private static final VolatileBits V_FIRST_OPAQUE_INPUT_V = new VolatileBits(0x0000000000000000L, 0x0000000000700000L, 0x0000000000000000L, 0x0000000000500000L, 0x0000000000410000L, 0x3333444455556666L, 0x4444555566667777L, new Bits128(0x1000000000000010L, 0x1000000000000020L), new Bits128(0x1000000000000011L, 0x1000000000000021L), new Bits128(0x1000000000000012L, 0x1000000000000022L), new Bits128(0x1000000000000013L, 0x1000000000000023L), new Bits128(0x1000000000000014L, 0x1000000000000024L), new Bits128(0x1000000000000015L, 0x1000000000000025L));
    private static final VolatileBits V_FIRST_OPAQUE_OFFER_V = new VolatileBits(0xFACEA11100000000L, 0x8100000000000002L, 0x8100000000000003L, 0x8100000000000004L, 0x8100000000000005L, 0x8100000000000006L, 0x8100000000000007L, new Bits128(0x8100000000000010L, 0x8100000000000020L), new Bits128(0x8100000000000011L, 0x8100000000000021L), new Bits128(0x8100000000000012L, 0x8100000000000022L), new Bits128(0x8100000000000013L, 0x8100000000000023L), new Bits128(0x8100000000000014L, 0x8100000000000024L), new Bits128(0x8100000000000015L, 0x8100000000000025L));
    private static final VolatileBits V_FC74_OFFER_V = new VolatileBits(0x0000000000600000L, 0x8200000000000002L, 0x8200000000000003L, 0x8200000000000004L, 0x8200000000000005L, 0x8200000000000006L, 0x8200000000000007L, new Bits128(0x8200000000000010L, 0x8200000000000020L), new Bits128(0x8200000000000011L, 0x8200000000000021L), new Bits128(0x8200000000000012L, 0x8200000000000022L), new Bits128(0x8200000000000013L, 0x8200000000000023L), new Bits128(0x8200000000000014L, 0x8200000000000024L), new Bits128(0x8200000000000015L, 0x8200000000000025L));
    private static final VolatileBits V_ACTUAL_ERROR_POST_V = new VolatileBits(0x0000000000600020L, 0x8200000000000002L, 0x8200000000000003L, 0x8200000000000004L, 0x8200000000000005L, 0x8200000000000006L, 0x8200000000000007L, new Bits128(0x8200000000000010L, 0x8200000000000020L), new Bits128(0x8200000000000011L, 0x8200000000000021L), new Bits128(0x8200000000000012L, 0x8200000000000022L), new Bits128(0x8200000000000013L, 0x8200000000000023L), new Bits128(0x8200000000000014L, 0x8200000000000024L), new Bits128(0x8200000000000015L, 0x8200000000000025L));
    private static final VolatileBits V_THIRD_OPAQUE_OFFER_V = new VolatileBits(0xDDAA55114424E399L, 0x8300000000000002L, 0x8300000000000003L, 0x8300000000000004L, 0x8300000000000005L, 0x8300000000000006L, 0x8300000000000007L, new Bits128(0x8300000000000010L, 0x8300000000000020L), new Bits128(0x8300000000000011L, 0x8300000000000021L), new Bits128(0x8300000000000012L, 0x8300000000000022L), new Bits128(0x8300000000000013L, 0x8300000000000023L), new Bits128(0x8300000000000014L, 0x8300000000000024L), new Bits128(0x8300000000000015L, 0x8300000000000025L));
    private static final VolatileBits V_ACTUAL_TABLE_INPUT_V = new VolatileBits(0xDDAA55114424E399L, 0x000000004424E399L, 0x8300000000000003L, 0x8300000000000004L, 0x8300000000000005L, 0x8300000000000006L, 0x8300000000000007L, new Bits128(0x8300000000000010L, 0x8300000000000020L), new Bits128(0x8300000000000011L, 0x8300000000000021L), new Bits128(0x8300000000000012L, 0x8300000000000022L), new Bits128(0x8300000000000013L, 0x8300000000000023L), new Bits128(0x8300000000000014L, 0x8300000000000024L), new Bits128(0x8300000000000015L, 0x8300000000000025L));
    private static final VolatileBits V_ACTUAL_TABLE_POST_V = new VolatileBits(0x0000000000000001L, 0x000000004424E399L, 0x0000000144423A68L, 0x0000000000000008L, 0x0000000144423A60L, 0x8300000000000006L, 0x8300000000000007L, new Bits128(0x8300000000000010L, 0x8300000000000020L), new Bits128(0x8300000000000011L, 0x8300000000000021L), new Bits128(0x8300000000000012L, 0x8300000000000022L), new Bits128(0x8300000000000013L, 0x8300000000000023L), new Bits128(0x8300000000000014L, 0x8300000000000024L), new Bits128(0x8300000000000015L, 0x8300000000000025L));
    private static final VolatileBits V_ACTUAL_ROOT_POST_V = new VolatileBits(0x0000000000200000L, 0x0000000000000000L, 0x0000000144423A68L, 0x0000000000000008L, 0x0000000144423A60L, 0x8300000000000006L, 0x0000000144423F20L, new Bits128(0x8300000000000010L, 0x8300000000000020L), new Bits128(0x8300000000000011L, 0x8300000000000021L), new Bits128(0x8300000000000012L, 0x8300000000000022L), new Bits128(0x8300000000000013L, 0x8300000000000023L), new Bits128(0x8300000000000014L, 0x8300000000000024L), new Bits128(0x8300000000000015L, 0x8300000000000025L));
    private static final VolatileBits V_CALL_0 = new VolatileBits(0x0000000000400000L, 0x0000000000300000L, 0x0000000000500000L, 0x0000000000000008L, 0x2222333344445555L, 0x3333444455556666L, 0x4444555566667777L, new Bits128(0x1000000000000010L, 0x1000000000000020L), new Bits128(0x1000000000000011L, 0x1000000000000021L), new Bits128(0x1000000000000012L, 0x1000000000000022L), new Bits128(0x1000000000000013L, 0x1000000000000023L), new Bits128(0x1000000000000014L, 0x1000000000000024L), new Bits128(0x1000000000000015L, 0x1000000000000025L));
    private static final VolatileBits V_CALL_2 = new VolatileBits(0x0000000000310000L, 0x0000000000310000L, 0x0000000000500000L, 0x0000000000000008L, 0x0000000000410000L, 0x3333444455556666L, 0x4444555566667777L, new Bits128(0x1000000000000010L, 0x1000000000000020L), new Bits128(0x1000000000000011L, 0x1000000000000021L), new Bits128(0x1000000000000012L, 0x1000000000000022L), new Bits128(0x1000000000000013L, 0x1000000000000023L), new Bits128(0x1000000000000014L, 0x1000000000000024L), new Bits128(0x1000000000000015L, 0x1000000000000025L));
    private static final VolatileBits V_POST_GETTER249 = new VolatileBits(0x0000000000310000L, 0x0000000000300000L, 0x0000000000500000L, 0x0000000000000008L, 0x2222333344445555L, 0x3333444455556666L, 0x4444555566667777L, new Bits128(0x1000000000000010L, 0x1000000000000020L), new Bits128(0x1000000000000011L, 0x1000000000000021L), new Bits128(0x1000000000000012L, 0x1000000000000022L), new Bits128(0x1000000000000013L, 0x1000000000000023L), new Bits128(0x1000000000000014L, 0x1000000000000024L), new Bits128(0x1000000000000015L, 0x1000000000000025L));
    private static final VolatileBits V_RELEASE_TAIL = new VolatileBits(0x0000000000310000L, 0x0000000000500000L, 0x0000000000500000L, 0x0000000000000008L, 0x0000000000410000L, 0x3333444455556666L, 0x4444555566667777L, new Bits128(0x1000000000000010L, 0x1000000000000020L), new Bits128(0x1000000000000011L, 0x1000000000000021L), new Bits128(0x1000000000000012L, 0x1000000000000022L), new Bits128(0x1000000000000013L, 0x1000000000000023L), new Bits128(0x1000000000000014L, 0x1000000000000024L), new Bits128(0x1000000000000015L, 0x1000000000000025L));
    private static final NonvolatileBits N_ROOT_N = new NonvolatileBits(0x1100000000000101L, 0x2200000000000202L, 0x3300000000000303L, 0x4400000000000404L, 0xABCDEF1200000505L, 0x6600000000000606L, 0x7700000000000707L, 0x8800000000000808L, new Bits128(0xC0C1C2C3C4C5C6C7L, 0xD0D1D2D3D4D5D6D7L));
    private static final NonvolatileBits N_AT715_CALL_N = new NonvolatileBits(0x1100000000000101L, 0x2200000000000202L, 0x0000000000200000L, 0x4400000000000404L, 0xABCDEF1200000505L, 0x6600000000000606L, 0x0000000000210000L, 0x8800000000000808L, new Bits128(0xC0C1C2C3C4C5C6C7L, 0xD0D1D2D3D4D5D6D7L));
    private static final NonvolatileBits N_INNER_BEFORE_CELL_N = new NonvolatileBits(0x0000000000500000L, 0x2200000000000202L, 0x0000000000200000L, 0x0000000000000008L, 0xABCDEF1200000505L, 0x6600000000000606L, 0x0000000000210000L, 0x8800000000000808L, new Bits128(0xC0C1C2C3C4C5C6C7L, 0xD0D1D2D3D4D5D6D7L));
    private static final NonvolatileBits N_INNER_AFTER_CELL_N = new NonvolatileBits(0x0000000000600020L, 0x2200000000000202L, 0x0000000000200000L, 0x0000000000000008L, 0xABCDEF1200000505L, 0x6600000000000606L, 0x0000000000210000L, 0x8800000000000808L, new Bits128(0xC0C1C2C3C4C5C6C7L, 0xD0D1D2D3D4D5D6D7L));
    private static final PostState240Api.Input ROOT = new PostState240Api.Input(new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423F48L, V_ROOT_V, N_ROOT_N), false, M0, 0x0000000025800001L);
    private record ExpectedFrame(long ownerEntryRva, GovernmentCrtBoundary185Api.Call call,
            GovernmentCrtBoundary185Api.Entry childEntry, int instructionLength, long returnRipBits,
            boolean preDf, QueueFp604Api.Mxcsr preMxcsr, long childOrigin, int sourceWriteOrdinal) { }
    // Index1 is source-derived, not a directly observed runtime frame.
    private static final ExpectedFrame[] FRAMES = {
        // 0: 715 cleanup
        new ExpectedFrame(0x00000000021A5050L, new GovernmentCrtBoundary185Api.Call(0x00000000021A508FL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, 0x0000000140855830L, 0x0000000144423AD0L, V_CALL_0, N_AT715_CALL_N), new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423AC8L, V_CALL_0, N_AT715_CALL_N), 3, 0x00000001421A5092L, false, M0, 0x00000000021A508FL, 14),
        // 1: 247 first actual getter
        new ExpectedFrame(0x0000000000855830L, new GovernmentCrtBoundary185Api.Call(0x000000000085584CL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, 0x000000014086E140L, 0x0000000144423AA0L, V_CALL_0, N_INNER_BEFORE_CELL_N), new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423A98L, V_CALL_0, N_INNER_BEFORE_CELL_N), 3, 0x000000014085584FL, false, M0, 0x000000000085584CL, 19),
        // 2: 247 second actual release14
        new ExpectedFrame(0x0000000000855830L, new GovernmentCrtBoundary185Api.Call(0x000000000085585BL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, 0x00000001408571C0L, 0x0000000144423AA0L, V_CALL_2, N_INNER_BEFORE_CELL_N), new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423A98L, V_CALL_2, N_INNER_BEFORE_CELL_N), 4, 0x000000014085585FL, false, M0, 0x000000000085585BL, 24),
        // 3: 251 first opaque
        new ExpectedFrame(0x000000000424E364L, new GovernmentCrtBoundary185Api.Call(0x000000000424E37AL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, 0x0000000140A10010L, 0x0000000144423A70L, V_FIRST_OPAQUE_INPUT_V, N_INNER_BEFORE_CELL_N), new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423A68L, V_FIRST_OPAQUE_INPUT_V, N_INNER_BEFORE_CELL_N), 6, 0x000000014424E380L, false, M0, 0x000000000424E37AL, 30),
        // 4: 251 second actual generic32
        new ExpectedFrame(0x000000000424E364L, new GovernmentCrtBoundary185Api.Call(0x000000000424E384L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x000000000423B18CL, 0x0000000144423A70L, V_FIRST_OPAQUE_OFFER_V, N_INNER_BEFORE_CELL_N), new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423A68L, V_FIRST_OPAQUE_OFFER_V, N_INNER_BEFORE_CELL_N), 5, 0x000000014424E389L, true, M1, 0x000000000424E384L, 31),
        // 5: generic32 inner opaqueFC74
        new ExpectedFrame(0x000000000423B18CL, new GovernmentCrtBoundary185Api.Call(0x000000000423B190L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x000000000424FC74L, 0x0000000144423A40L, V_FIRST_OPAQUE_OFFER_V, N_INNER_BEFORE_CELL_N), new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423A38L, V_FIRST_OPAQUE_OFFER_V, N_INNER_BEFORE_CELL_N), 5, 0x000000014423B195L, true, M1, 0x000000000423B190L, 32),
        // 6: 251 third opaque
        new ExpectedFrame(0x000000000424E364L, new GovernmentCrtBoundary185Api.Call(0x000000000424E38CL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, 0x0000000140A30030L, 0x0000000144423A70L, V_ACTUAL_ERROR_POST_V, N_INNER_AFTER_CELL_N), new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423A68L, V_ACTUAL_ERROR_POST_V, N_INNER_AFTER_CELL_N), 6, 0x000000014424E392L, false, M2, 0x000000000424E38CL, 35),
        // 7: 251 fourth actual alias table
        new ExpectedFrame(0x000000000424E364L, new GovernmentCrtBoundary185Api.Call(0x000000000424E394L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x000000000423B0D4L, 0x0000000144423A70L, V_ACTUAL_TABLE_INPUT_V, N_INNER_AFTER_CELL_N), new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000144423A68L, V_ACTUAL_TABLE_INPUT_V, N_INNER_AFTER_CELL_N), 5, 0x000000014424E399L, true, M3, 0x000000000424E394L, 36)
    };
    private static final QueueFp604Api.Normal OFFER_0 = normal(V_FIRST_OPAQUE_OFFER_V, 0x000000014424E380L, 0x0000000144423A70L, N_INNER_BEFORE_CELL_N, true, M1);
    private static final QueueFp604Api.Normal OFFER_1 = normal(V_FC74_OFFER_V, 0x000000014423B195L, 0x0000000144423A40L, N_INNER_BEFORE_CELL_N, false, M2);
    private static final QueueFp604Api.Normal OFFER_2 = normal(V_THIRD_OPAQUE_OFFER_V, 0x000000014424E392L, 0x0000000144423A70L, N_INNER_AFTER_CELL_N, true, M3);
    // Frozen source expectation only: internal249's Normal is not separately exposed by250.
    private static final QueueFp604Api.Normal EXPECTED_GETTER249 = normal(V_POST_GETTER249, 0x000000014085584FL, 0x0000000144423AA0L, N_INNER_BEFORE_CELL_N, false, M0);
    private static final QueueFp604Api.Normal EXPECTED_GENERIC32 = normal(V_ACTUAL_ERROR_POST_V, 0x000000014424E389L, 0x0000000144423A70L, N_INNER_BEFORE_CELL_N, false, M2);
    private static final QueueFp604Api.Normal EXPECTED_TABLE257 = normal(V_ACTUAL_TABLE_POST_V, 0x000000014424E399L, 0x0000000144423A70L, N_INNER_AFTER_CELL_N, true, M3);
    private static final QueueFp604Api.Normal EXPECTED_WHOLE251 = normal(V_ACTUAL_TABLE_POST_V, 0x000000014085585FL, 0x0000000144423AA0L, N_INNER_BEFORE_CELL_N, true, M3);
    private static final QueueFp604Api.Normal EXPECTED_FORWARD58 = normal(V_ACTUAL_TABLE_POST_V, 0x00000001421A5092L, 0x0000000144423AD0L, N_AT715_CALL_N, true, M3);
    private static final QueueFp604Api.Normal EXPECTED_WHOLE715 = normal(V_ACTUAL_ROOT_POST_V, 0x0000000140556670L, 0x0000000144423F50L, N_ROOT_N, true, M3);
    private record Seed(long address, int width, long value) { }
    private static final Seed[] SEEDS = {
        new Seed(0x0000000144423F48L, 8, 0x0000000140556670L), // root actual RET QWORD
        new Seed(0x0000000000200000L, 8, 0x0000000000500000L), // owned destination old block
        new Seed(0x0000000000200008L, 4, 0x0000000000000001L), // destination capacity
        new Seed(0x000000000020000CL, 4, 0x0000000000000000L), // destination count
        new Seed(0x0000000000200010L, 8, 0x0000000000300000L), // destination provider
        new Seed(0x0000000000210000L, 8, 0x0000000000510000L), // owned source base
        new Seed(0x0000000000210008L, 4, 0x0000000000000001L), // source capacity
        new Seed(0x000000000021000CL, 4, 0x0000000000000001L), // source count
        new Seed(0x0000000000210010L, 8, 0x0000000000300000L), // same source provider
        new Seed(0x0000000000300000L, 8, 0x0000000000400000L), // artificial provider vtable
        new Seed(0x0000000000400010L, 8, 0x0000000140855830L), // actual58 resolved cleanup target
        new Seed(0x0000000000400038L, 8, 0x000000014086E140L), // actual8B getter target
        new Seed(0x0000000000300408L, 8, 0x0000000000310000L), // getter explicit allocator pointer
        new Seed(0x0000000000310000L, 8, 0x0000000000410000L), // artificial allocator vtable
        new Seed(0x0000000000410010L, 8, 0x00000001408571C0L), // actual14B second target
        new Seed(0x0000000145C5DE30L, 8, 0x0000000000700000L), // explicit heap token; not actual global data
        new Seed(0x00000001443DA748L, 8, 0x0000000140A10010L), // explicit first opaque IAT target
        new Seed(0x00000001443DA738L, 8, 0x0000000140A30030L), // explicit third opaque IAT target
        new Seed(0x0000000000600020L, 8, 0xBADC0FFE55667788L), // owned error cell with distinct highDWORD
        new Seed(0x0000000144423A60L, 4, 0x000000000BADF00DL) // table key0 mismatch; row0 value unseeded
    };
    private record ExpectedRam(String operation, long address, long value, String source) { }
    private static final ExpectedRam[] EXPECTED_RAM = {
        new ExpectedRam("W8", 0x0000000144423F50L, 0x1100000000000101L, "21A5050"),
        new ExpectedRam("W8", 0x0000000144423F58L, 0x2200000000000202L, "21A5055"),
        new ExpectedRam("W8", 0x0000000144423F60L, 0x3300000000000303L, "21A505A"),
        new ExpectedRam("W8", 0x0000000144423F40L, 0x4400000000000404L, "21A505F"),
        new ExpectedRam("W8", 0x0000000144423F38L, 0xABCDEF1200000505L, "21A5060"),
        new ExpectedRam("W8", 0x0000000144423F30L, 0x6600000000000606L, "21A5062"),
        new ExpectedRam("W8", 0x0000000144423F28L, 0x7700000000000707L, "21A5064"),
        new ExpectedRam("W8", 0x0000000144423F20L, 0x8800000000000808L, "21A5066"),
        new ExpectedRam("R8", 0x0000000000200010L, 0x0000000000300000L, "21A5075"),
        new ExpectedRam("R8", 0x0000000000210010L, 0x0000000000300000L, "21A5079"),
        new ExpectedRam("R8", 0x0000000000300000L, 0x0000000000400000L, "21A5083"),
        new ExpectedRam("R8", 0x0000000000200000L, 0x0000000000500000L, "21A508C"),
        new ExpectedRam("R8", 0x0000000000400010L, 0x0000000140855830L, "21A508F target"),
        new ExpectedRam("W8", 0x0000000144423AC8L, 0x00000001421A5092L, "21A508F sourceCALL"),
        new ExpectedRam("W8", 0x0000000144423AD0L, 0x1100000000000101L, "855830"),
        new ExpectedRam("W8", 0x0000000144423AC0L, 0x4400000000000404L, "855835"),
        new ExpectedRam("R8", 0x0000000000300000L, 0x0000000000400000L, "855849"),
        new ExpectedRam("R8", 0x0000000000400038L, 0x000000014086E140L, "85584C target"),
        new ExpectedRam("W8", 0x0000000144423A98L, 0x000000014085584FL, "85584C sourceCALL"),
        new ExpectedRam("R8", 0x0000000000300408L, 0x0000000000310000L, "86E140"),
        new ExpectedRam("R8", 0x0000000144423A98L, 0x000000014085584FL, "86E147 RET"),
        new ExpectedRam("R8", 0x0000000000310000L, 0x0000000000410000L, "855858"),
        new ExpectedRam("R8", 0x0000000000410010L, 0x00000001408571C0L, "85585B target"),
        new ExpectedRam("W8", 0x0000000144423A98L, 0x000000014085585FL, "85585B sourceCALL"),
        new ExpectedRam("W4", 0x0000000144423AA8L, 0x0000000000000000L, "423543C"),
        new ExpectedRam("R4", 0x0000000144423AA8L, 0x0000000000000000L, "4235444"),
        new ExpectedRam("W8", 0x0000000144423A90L, 0x0000000000500000L, "424E369"),
        new ExpectedRam("R8", 0x0000000145C5DE30L, 0x0000000000700000L, "424E373"),
        new ExpectedRam("R8", 0x00000001443DA748L, 0x0000000140A10010L, "424E37A target"),
        new ExpectedRam("W8", 0x0000000144423A68L, 0x000000014424E380L, "424E37A sourceCALL"),
        new ExpectedRam("W8", 0x0000000144423A68L, 0x000000014424E389L, "424E384 sourceCALL"),
        new ExpectedRam("W8", 0x0000000144423A38L, 0x000000014423B195L, "423B190 sourceCALL"),
        new ExpectedRam("R8", 0x0000000144423A68L, 0x000000014424E389L, "423B1AB actualRET"),
        new ExpectedRam("R8", 0x00000001443DA738L, 0x0000000140A30030L, "424E38C target"),
        new ExpectedRam("W8", 0x0000000144423A68L, 0x000000014424E392L, "424E38C sourceCALL"),
        new ExpectedRam("W8", 0x0000000144423A68L, 0x000000014424E399L, "424E394 actualCALL writes table row1"),
        new ExpectedRam("R4", 0x0000000144423A60L, 0x000000000BADF00DL, "423B0E4 key0"),
        new ExpectedRam("R4", 0x0000000144423A68L, 0x000000004424E399L, "423B0E4 key1"),
        new ExpectedRam("R4", 0x0000000144423A6CL, 0x0000000000000001L, "423B113 value1"),
        new ExpectedRam("R8", 0x0000000144423A68L, 0x000000014424E399L, "423B118 actualRET shares row1"),
        new ExpectedRam("W4", 0x0000000000600020L, 0x0000000000000001L, "424E399"),
        new ExpectedRam("R8", 0x0000000144423A90L, 0x0000000000500000L, "424E39F POP RBX"),
        new ExpectedRam("R8", 0x0000000144423A98L, 0x000000014085585FL, "424E3A0 actualRET"),
        new ExpectedRam("R8", 0x0000000144423AD0L, 0x1100000000000101L, "85585F restoreRBX"),
        new ExpectedRam("R8", 0x0000000144423AC0L, 0x4400000000000404L, "855868 POP RDI"),
        new ExpectedRam("R8", 0x0000000144423AC8L, 0x00000001421A5092L, "855869 actualRET"),
        new ExpectedRam("W8", 0x0000000000200000L, 0x0000000000000000L, "21A5094"),
        new ExpectedRam("W8", 0x0000000000200008L, 0x0000000000000000L, "21A5097"),
        new ExpectedRam("R8", 0x0000000000210010L, 0x0000000000300000L, "21A509B"),
        new ExpectedRam("R8", 0x0000000000200010L, 0x0000000000300000L, "21A509F"),
        new ExpectedRam("R8", 0x0000000000210000L, 0x0000000000510000L, "21A50A5"),
        new ExpectedRam("W8", 0x0000000000200000L, 0x0000000000510000L, "21A50A8"),
        new ExpectedRam("W8", 0x0000000000210000L, 0x0000000000000000L, "21A50AB"),
        new ExpectedRam("R4", 0x000000000020000CL, 0x0000000000000000L, "21A50AE"),
        new ExpectedRam("R4", 0x000000000021000CL, 0x0000000000000001L, "21A50B1"),
        new ExpectedRam("W4", 0x000000000020000CL, 0x0000000000000001L, "21A50B5"),
        new ExpectedRam("W4", 0x000000000021000CL, 0x0000000000000000L, "21A50B8"),
        new ExpectedRam("R4", 0x0000000000200008L, 0x0000000000000000L, "21A50BC"),
        new ExpectedRam("R4", 0x0000000000210008L, 0x0000000000000001L, "21A50BF"),
        new ExpectedRam("W4", 0x0000000000200008L, 0x0000000000000001L, "21A50C3"),
        new ExpectedRam("W4", 0x0000000000210008L, 0x0000000000000000L, "21A50C6"),
        new ExpectedRam("R8", 0x0000000144423F50L, 0x1100000000000101L, "21A5302"),
        new ExpectedRam("R8", 0x0000000144423F58L, 0x2200000000000202L, "21A5306"),
        new ExpectedRam("R8", 0x0000000144423F60L, 0x3300000000000303L, "21A530A"),
        new ExpectedRam("R8", 0x0000000144423F20L, 0x8800000000000808L, "21A5311"),
        new ExpectedRam("R8", 0x0000000144423F28L, 0x7700000000000707L, "21A5313"),
        new ExpectedRam("R8", 0x0000000144423F30L, 0x6600000000000606L, "21A5315"),
        new ExpectedRam("R8", 0x0000000144423F38L, 0xABCDEF1200000505L, "21A5317"),
        new ExpectedRam("R8", 0x0000000144423F40L, 0x4400000000000404L, "21A5319"),
        new ExpectedRam("R8", 0x0000000144423F48L, 0x0000000140556670L, "21A531A actualRET")
    };
    private record Segment(long address, String hexBytes) { }
    private static final Segment[] FINAL_RAM = {
        new Segment(0x0000000000200000L, "000051000000000001000000010000000000300000000000"),
        new Segment(0x0000000000210000L, "000000000000000000000000000000000000300000000000"),
        new Segment(0x0000000000300000L, "0000400000000000"),
        new Segment(0x0000000000300408L, "0000310000000000"),
        new Segment(0x0000000000310000L, "0000410000000000"),
        new Segment(0x0000000000400010L, "3058854001000000"),
        new Segment(0x0000000000400038L, "40e1864001000000"),
        new Segment(0x0000000000410010L, "c071854001000000"),
        new Segment(0x0000000000600020L, "01000000fe0fdcba"),
        new Segment(0x00000001443DA738L, "3000a34001000000"),
        new Segment(0x00000001443DA748L, "1000a14001000000"),
        new Segment(0x0000000144423A38L, "95b1234401000000"),
        new Segment(0x0000000144423A60L, "0df0ad0b"),
        new Segment(0x0000000144423A68L, "99e3244401000000"),
        new Segment(0x0000000144423A90L, "00005000000000005f58854001000000"),
        new Segment(0x0000000144423AA8L, "00000000"),
        new Segment(0x0000000144423AC0L, "040400000000004492501a42010000000101000000000011"),
        new Segment(0x0000000144423F20L, "0808000000000088070700000000007706060000000000660505000012efcdab04040000000000447066554001000000010100000000001102020000000000220303000000000033"),
        new Segment(0x0000000145C5DE30L, "0000700000000000")
    };

    public static void main(String[] args) {
        if (args.length != 0) throw new IllegalArgumentException("This manual has exactly one noargs scene");
        actualDeepE394CallWritesTableRow1BeforeActualLeaf();
        System.out.println("TABLE_CLEANUP_ALIAS258_ONE_SCENE_OK directFrames=7 sourceDerivedFrames=1"
                + " machineCallPushes=8 sourceRamEvents=70 finalOwnedBytes=264");
    }

    private static void actualDeepE394CallWritesTableRow1BeforeActualLeaf() {
        ByteRam memory = new ByteRam();
        for (Seed seed : SEEDS) memory.seed(seed);
        require(memory.events.isEmpty(), "seed must not be a source RAM event");
        for (int i = 0; i < 8; i++)
            require(!memory.bytes.containsKey(0x0000000144423A68L + i), "row1 must start unowned");
        Probe probe = new Probe(memory);

        TableDwordLeaf257 actualTable = new TableDwordLeaf257();
        PostState240Api.EntryExecutor observedTable = (input, sameMemory) -> {
            probe.sameMemory(sameMemory);
            require(++probe.tableCalls == 1, "actual table must execute once");
            require(input == probe.lowerInputs[3], "table binder must pass original child Input");
            probe.input(7, input);
            QueueFp604Api.Outcome actual = actualTable.execute(input, sameMemory);
            probe.normalEquals(EXPECTED_TABLE257, actual, "actual table");
            return actual;
        };

        KnownAllocateErrorFp625.ErrorCalls fc74 = frame -> {
            require(++probe.fc74Calls == 1, "explicit FC74 offer once");
            probe.common(5, frame.original(), frame.childEntry(), frame.directionFlagSet(),
                    frame.preMxcsr(), frame.returnRipBits());
            // ErrorCall has no owner/origin/length field; those remain source-derived.
            return probe.offer(1);
        };
        Error32PostState256 actualError = new Error32PostState256(fc74);
        PostState240Api.EntryExecutor observedError = (input, sameMemory) -> {
            probe.sameMemory(sameMemory);
            require(++probe.errorCalls == 1, "actual generic32 must execute once");
            require(input == probe.lowerInputs[1], "error binder must pass original child Input");
            probe.input(4, input);
            QueueFp604Api.Outcome actual = actualError.execute(input, sameMemory);
            probe.normalEquals(EXPECTED_GENERIC32, actual, "actual generic32");
            return actual;
        };

        FreePostState251Api.Children opaqueFree = (frame, sameMemory) -> {
            probe.sameMemory(sameMemory);
            long site = frame.call().callSiteRva();
            if (site == 0x424E37AL) {
                require(frame == probe.lowerFrames[0], "first opaque original frame identity");
                require(++probe.firstCalls == 1, "explicit first offer once");
                return probe.offer(0);
            }
            if (site == 0x424E38CL) {
                require(frame == probe.lowerFrames[2], "third opaque original frame identity");
                require(++probe.thirdCalls == 1, "explicit third offer once");
                return probe.offer(2);
            }
            throw failure("unmatched Free251 child " + Long.toHexString(site));
        };
        FreePostState251Api.Children actualFreeChildren = FreeKnownTable257.bind(
                observedTable, FreeKnownError256.bind(observedError, opaqueFree));
        FreePostState251Api.Children observedFreeChildren = (frame, sameMemory) -> {
            probe.sameMemory(sameMemory);
            int lowerIndex = switch ((int) frame.call().callSiteRva()) {
                case 0x424E37A -> 0;
                case 0x424E384 -> 1;
                case 0x424E38C -> 2;
                case 0x424E394 -> 3;
                default -> throw failure("unexpected free source site");
            };
            int index = switch (lowerIndex) {
                case 0 -> 3;
                case 1 -> 4;
                case 2 -> 6;
                case 3 -> 7;
                default -> throw failure("unreachable lower index");
            };
            ExpectedFrame expected = FRAMES[index];
            equal(expected.ownerEntryRva(), frame.ownerEntryRva(), "free owner");
            equal(ROOT.entry().imageBaseBits(), frame.imageBaseBits(), "free image");
            equal(expected.instructionLength(), frame.instructionLength(), "free CALL length");
            equal(expected.childOrigin(), frame.childInput().originCallSiteRva(), "free child origin");
            probe.lowerFrames[lowerIndex] = frame;
            probe.lowerInputs[lowerIndex] = frame.childInput();
            probe.common(index, frame.call(), frame.childInput().entry(),
                    frame.childInput().directionFlagSet(), frame.childInput().mxcsr(), frame.returnRipBits());
            return actualFreeChildren.invoke(frame, sameMemory);
        };

        DefaultStaticFp648Api.Calls foreign648 = new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                probe.foreign648Invoke++;
                throw failure("unmatched648 invoke");
            }
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                probe.foreign648Tail++;
                throw failure("unmatched648 tail");
            }
        };
        PostVtable247Api.Children foreign247 = new PostVtable247Api.Children() {
            @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                probe.foreign247Invoke++;
                throw failure("unmatched247 invoke");
            }
            @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                probe.foreign247Tail++;
                throw failure("unmatched247 tail");
            }
        };
        PostVtable247Api.Children actualForwardChildren = DefaultFreeChain255.bind(
                observedFreeChildren, foreign648, foreign247);
        PostVtable247Api.Children observedForwardChildren = new PostVtable247Api.Children() {
            @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                probe.sameMemory(sameMemory);
                require(++probe.second247Calls == 1, "only second247 frame reaches supplied children");
                ExpectedFrame expected = FRAMES[2];
                equal(expected.ownerEntryRva(), frame.ownerEntryRva(), "247 owner");
                equal(ROOT.entry().imageBaseBits(), frame.imageBaseBits(), "247 image");
                equal(expected.instructionLength(), frame.instructionLength(), "247 length");
                equal(expected.childOrigin(), frame.childInput().originCallSiteRva(), "247 second actual origin");
                probe.common(2, frame.call(), frame.childInput().entry(),
                        frame.childInput().directionFlagSet(), frame.childInput().mxcsr(), frame.returnRipBits());
                QueueFp604Api.Outcome actual = actualForwardChildren.invoke(frame, sameMemory);
                // This is actual648's response. Its hidden tail forwards actual251 unchanged.
                // Test cannot separately observe that inner Normal object's identity or251 input origin.
                probe.normalEquals(EXPECTED_WHOLE251, actual, "actual648/251 response");
                return actual;
            }
            @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                throw failure("this scene reaches no247 tail");
            }
        };
        CallOutcome242Api.OutcomePort foreign242 = frame -> {
            probe.other715Calls++;
            throw failure("unmatched715 source CALL");
        };
        CallOutcome242Api.OutcomePort actual715Children = Known715PostForward250.bind(
                memory, observedForwardChildren, foreign242);
        CallOutcome242Api.OutcomePort observed715Children = frame -> {
            require(++probe.rootCleanupCalls == 1, "one actual715 cleanup callback");
            ExpectedFrame expected = FRAMES[0];
            equal(expected.ownerEntryRva(), frame.ownerEntryRva(), "715 owner");
            equal(ROOT.entry().imageBaseBits(), frame.imageBaseBits(), "715 image");
            equal(expected.instructionLength(), frame.instructionLength(), "715 length");
            equal(CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N, frame.normalRule(), "715 original N rule");
            probe.common(0, frame.call(), frame.childEntry(), frame.preDirectionFlagSet(),
                    frame.preMxcsr(), frame.returnRipBits());
            QueueFp604Api.Outcome actual = actual715Children.invoke(frame);
            probe.normalEquals(EXPECTED_FORWARD58, actual, "actual24758 response");
            return actual;
        };
        PostState240Api.FloatingStages noReachedStages = new PostState240Api.FloatingStages() {
            @Override public PostState240Api.VectorResult convertSignedDwords(PostState240Api.FpFrame frame) {
                probe.fpStages++;
                throw failure("unexpected CVTDQ2PS");
            }
            @Override public PostState240Api.VectorResult multiplyLowSingle(PostState240Api.FpFrame frame,
                    int multiplierRaw32) {
                probe.fpStages++;
                throw failure("unexpected MULSS");
            }
            @Override public PostState240Api.IntegerResult truncateLowSingle(PostState240Api.FpFrame frame) {
                probe.fpStages++;
                throw failure("unexpected CVTTSS2SI");
            }
        };
        TransferFull238Api.Budget budget = (site, cursor, end) -> {
            require(++probe.budgetCalls == 1, "this scene has one entry budget and no recursion/loop");
            equal(0x21A5050L, site, "actual whole715 entry budget");
            equal(ROOT.entry().rspBits(), cursor, "budget actual root SP");
            equal(0L, end, "source entry budget end");
        };
        WholeTransferPostState242 whole = new WholeTransferPostState242(
                noReachedStages, budget, observed715Children);
        QueueFp604Api.Outcome actualRoot = whole.transfer715(ROOT, memory);
        probe.normalEquals(EXPECTED_WHOLE715, actualRoot, "actual whole715");
        probe.finish();
        memory.assertCompleteTrace();
        memory.assertEightOwnedCalls();
        memory.assertFinalOwnedBytes();
    }

    private static final class Probe {
        private final ByteRam memory;
        private int observedFrames, observedMask, offers;
        private int tableCalls, errorCalls, fc74Calls, firstCalls, thirdCalls;
        private int second247Calls, rootCleanupCalls, budgetCalls, fpStages;
        private int foreign247Invoke, foreign247Tail, foreign648Invoke, foreign648Tail, other715Calls;
        private final FreePostState251Api.AlreadyPushedCallFrame[] lowerFrames =
                new FreePostState251Api.AlreadyPushedCallFrame[4];
        private final PostState240Api.Input[] lowerInputs = new PostState240Api.Input[4];
        private static final int[] DIRECT_ORDER = {0, 2, 3, 4, 5, 6, 7};
        private Probe(ByteRam memory) { this.memory = memory; }
        private void sameMemory(GovernmentCrtBoundary185Api.Memory actual) {
            require(actual == memory, "same byte RAM identity");
        }
        private void input(int index, PostState240Api.Input actual) {
            ExpectedFrame expected = FRAMES[index];
            equal(expected.childEntry(), actual.entry(), "entry full V/N/image/SP");
            equal(expected.preDf(), actual.directionFlagSet(), "entry explicit DF");
            require(actual.mxcsr() == expected.preMxcsr(), "entry same partial MXCSR object");
            equal(expected.childOrigin(), actual.originCallSiteRva(), "entry actual origin");
        }
        private void common(int index, GovernmentCrtBoundary185Api.Call call,
                GovernmentCrtBoundary185Api.Entry child, boolean df,
                QueueFp604Api.Mxcsr mxcsr, long ret) {
            require(observedFrames < DIRECT_ORDER.length, "no duplicate direct frame");
            equal(DIRECT_ORDER[observedFrames], index, "actual nested direct frame order");
            require((observedMask & (1 << index)) == 0, "direct frame only once");
            observedFrames++;
            observedMask |= 1 << index;
            ExpectedFrame expected = FRAMES[index];
            equal(expected.call(), call, "full preCALL tuple/V/N");
            equal(expected.childEntry(), child, "full post-push child Entry");
            equal(expected.preDf(), df, "actual child DF");
            require(mxcsr == expected.preMxcsr(), "actual child same partial MXCSR object");
            equal(expected.returnRipBits(), ret, "actual source RET value");
            equal(expected.sourceWriteOrdinal(), memory.events.size(), "frame after sole source CALL write");
            // Observer peek is pure and deliberately absent from the production trace.
            equal(expected.returnRipBits(), memory.peek(child.rspBits(), 8), "already-owned actual RET bytes");
        }
        private QueueFp604Api.Normal offer(int index) {
            equal(offers++, index, "explicit three opaque offer order");
            int before = memory.events.size();
            QueueFp604Api.Normal supplied = switch (index) {
                case 0 -> OFFER_0;
                case 1 -> OFFER_1;
                case 2 -> OFFER_2;
                default -> throw failure("unexpected explicit offer");
            };
            equal(before, memory.events.size(), "opaque supplier has zero RAM operations");
            return supplied;
        }
        private void normalEquals(QueueFp604Api.Normal expected, QueueFp604Api.Outcome actual,
                String label) {
            require(actual instanceof QueueFp604Api.Normal, label + " must finish Normal");
            QueueFp604Api.Normal normal = (QueueFp604Api.Normal) actual;
            equal(expected, normal, label + " full V/N/RIP/SP/DF/partialMX");
            require(normal.postMxcsr() == expected.postMxcsr(), label + " retains explicit MX object");
        }
        private void finish() {
            equal(7, observedFrames, "seven directly exposed port frames");
            equal(0xFD, observedMask, "source-derived getter frame is not faked as an exposed frame");
            equal(3, offers, "all three explicit offers used");
            equal(1, tableCalls, "actual table calls");
            equal(1, errorCalls, "actual generic32 calls");
            equal(1, fc74Calls, "explicit FC74 calls");
            equal(1, firstCalls, "explicit first calls");
            equal(1, thirdCalls, "explicit third calls");
            equal(1, second247Calls, "actual second247 callback");
            equal(1, rootCleanupCalls, "actual715 cleanup callback");
            equal(1, budgetCalls, "no known recursive call or loop");
            equal(0, fpStages, "zero reached FP stages");
            equal(0, foreign247Invoke, "no foreign247 invoke");
            equal(0, foreign247Tail, "no foreign247 tail");
            equal(0, foreign648Invoke, "no foreign648 invoke");
            equal(0, foreign648Tail, "no foreign648 tail");
            equal(0, other715Calls, "no other715 CALL");
        }
    }

    private record RamEvent(String operation, long address, long low, long high) { }

    /** One sparse little-endian byte store for all nine185 primitives; reads never mutate RAM. */
    private static final class ByteRam implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<RamEvent> events = new ArrayList<>();
        private void seed(Seed seed) {
            require(seed.width() == 4 || seed.width() == 8, "frozen seed width");
            for (int i = 0; i < seed.width(); i++)
                require(!bytes.containsKey(seed.address() + i), "duplicate initial owned byte");
            store(seed.address(), seed.width(), seed.value());
        }
        private long peek(long address, int width) {
            long value = 0L;
            for (int i = 0; i < width; i++) {
                Byte actual = bytes.get(address + i);
                if (actual == null) throw failure("missing RAM byte " + Long.toUnsignedString(address + i, 16));
                value |= (long) Byte.toUnsignedInt(actual) << (8 * i);
            }
            return value;
        }
        private void store(long address, int width, long value) {
            for (int i = 0; i < width; i++)
                bytes.put(address + i, (byte) (value >>> (8 * i)));
        }
        private long read(long address, int width) {
            long actual = peek(address, width);
            events.add(new RamEvent("R" + width, address, actual, 0L));
            return actual;
        }
        private void write(long address, int width, long value) {
            store(address, width, value);
            events.add(new RamEvent("W" + width, address, value, 0L));
        }
        @Override public int readDword(long address) { return (int) read(address, 4); }
        @Override public long readQword(long address) { return read(address, 8); }
        @Override public int readUnsignedByte(long address) { return (int) read(address, 1); }
        @Override public void writeDword(long address, int value) {
            write(address, 4, Integer.toUnsignedLong(value));
        }
        @Override public void writeQword(long address, long value) { write(address, 8, value); }
        @Override public void writeByte(long address, int value) { write(address, 1, value & 0xFFL); }
        @Override public Bits128 read128(long address) {
            long low = peek(address, 8), high = peek(address + 8L, 8);
            events.add(new RamEvent("R16", address, low, high));
            return new Bits128(low, high);
        }
        @Override public void write128(long address, Bits128 value) {
            store(address, 8, value.lowBits());
            store(address + 8L, 8, value.highBits());
            events.add(new RamEvent("W16", address, value.lowBits(), value.highBits()));
        }
        @Override public int lockedXaddDword(long address, int addend) {
            int old = (int) peek(address, 4);
            int next = old + addend;
            store(address, 4, Integer.toUnsignedLong(next));
            events.add(new RamEvent("X4", address, Integer.toUnsignedLong(old), Integer.toUnsignedLong(next)));
            return old;
        }
        private void assertCompleteTrace() {
            equal(EXPECTED_RAM.length, events.size(), "complete source RAM event count");
            for (int i = 0; i < EXPECTED_RAM.length; i++) {
                ExpectedRam expected = EXPECTED_RAM[i];
                RamEvent actual = events.get(i);
                String label = "RAM event " + (i + 1) + " at " + expected.source();
                equal(expected.operation(), actual.operation(), label + " width/direction");
                equal(expected.address(), actual.address(), label + " address");
                equal(expected.value(), actual.low(), label + " actual bits");
                equal(0L, actual.high(), label + " no unexpected wide operation");
            }
        }
        private void assertEightOwnedCalls() {
            for (ExpectedFrame frame : FRAMES) {
                int writes = 0;
                for (RamEvent event : events)
                    if (event.operation().equals("W8") && event.address() == frame.childEntry().rspBits()
                            && event.low() == frame.returnRipBits()) writes++;
                equal(1, writes, "each of eight unique source-owned CALL writes exactly once");
            }
            // Getter's full first frame is not exposed. Its actual push/read/RET events and
            // the checked second frame provide available dynamic evidence, not a synthetic frame.
            ExpectedFrame getter = FRAMES[1];
            RamEvent actualPush = events.get(getter.sourceWriteOrdinal() - 1);
            equal("W8", actualPush.operation(), "getter source push width");
            equal(getter.childEntry().rspBits(), actualPush.address(), "getter source push address");
            equal(getter.returnRipBits(), actualPush.low(), "getter source push bits");
            equal(getter.returnRipBits(), events.get(20).low(), "getter fresh actual RET read");
            equal("R8", events.get(20).operation(), "getter fresh RET width");
            equal(getter.childEntry().rspBits(), events.get(20).address(), "getter fresh RET address");
        }
        private void assertFinalOwnedBytes() {
            Set<Long> expectedAddresses = new HashSet<>();
            for (Segment segment : FINAL_RAM) {
                require((segment.hexBytes().length() & 1) == 0, "final segment hex width");
                for (int i = 0; i < segment.hexBytes().length() / 2; i++) {
                    long address = segment.address() + i;
                    require(expectedAddresses.add(address), "final segments do not overlap");
                    int expected = Integer.parseInt(segment.hexBytes().substring(i * 2, i * 2 + 2), 16);
                    // Pure observer peek: no source trace, mutation or missing-byte allocation.
                    equal(expected, peek(address, 1), "final owned byte " + Long.toHexString(address));
                }
            }
            equal(264, expectedAddresses.size(), "frozen final owned byte count");
            equal(264, bytes.size(), "no missing or additional final owned byte");
            equal(expectedAddresses, bytes.keySet(), "exact final ownership set");
            equal(70, events.size(), "final observer peeks leave source trace unchanged");
        }
    }

    private static QueueFp604Api.Normal normal(VolatileBits v, long rip, long rsp,
            NonvolatileBits n, boolean df, QueueFp604Api.Mxcsr mxcsr) {
        GovernmentCrtBoundary185Api.NormalReturn nr =
                new GovernmentCrtBoundary185Api.NormalReturn(v, rip, rsp, n);
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(nr, df), mxcsr);
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw failure(message);
    }
    private static void equal(long expected, long actual, String message) {
        if (expected != actual)
            throw failure(message + ": expected=0x" + Long.toHexString(expected)
                    + ", actual=0x" + Long.toHexString(actual));
    }
    private static void equal(boolean expected, boolean actual, String message) {
        if (expected != actual) throw failure(message + ": expected=" + expected + ", actual=" + actual);
    }
    private static void equal(Object expected, Object actual, String message) {
        if (!Objects.equals(expected, actual))
            throw failure(message + ": expected=" + expected + ", actual=" + actual);
    }
    private static AssertionError failure(String message) { return new AssertionError(message); }
}
