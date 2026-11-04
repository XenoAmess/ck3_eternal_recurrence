package org.xar.ck3.study.m6.activity264literal;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/**
 * Independent literal data from frozen activity entry 23FC970, not an executor.
 * Every address, register bit, RAM byte, DF/MXCSR value and child stop is an artificial fixture.
 * No producer output, native fault, natural actor/global, loaded parity or ABI guarantee is claimed.
 * XMM7..15 are not in the existing V/N carrier and are neither added nor inferred here.
 * RAM is little endian; events are exact once, in listed order and byte width.
 * Unknown initial RAM reads must fail. The stopped offer must propagate by object identity.
 * This source has not been compiled or executed. It has no dependency on a new 264 producer.
 */
public final class ActivityEntry264LiteralData {
    private ActivityEntry264LiteralData() { }

    public static final String ORACLE_SHA256 = "05a406505d8bcb48aa2259fb1324e1de4346466e0d6a85a6d35590de8b472218";
    public static final String ACTUAL_SHA256 = "f2897cfb2538a91134fa9944b55dd200a1a7510cc738e80dc82c3d7c58c997b4";
    public static final String SOURCE_RF_RANGE = "[0x23fc970,0x23fdc67)";

    public enum Access { READ, WRITE }
    public record RamLiteral(long addressBits, int widthBytes, long valueBits, String role) { }
    public record MemoryEvent(long instructionRva, Access operation, int widthBytes,
            long addressBits, long valueBits, String role) { }
    public record Branch(long instructionRva, String condition, boolean taken, Long takenTargetRva) { }
    public sealed interface Expectation permits NormalExpectation, StoppedExpectation { }
    public record NormalExpectation(QueueFp604Api.Normal value) implements Expectation { }
    public record ExpectedCall(GovernmentCrtBoundary185Api.Call beforePush,
            PostState240Api.Input childInputAfterPush, int instructionLength, long returnRipBits,
            boolean preDirectionFlagSet, QueueFp604Api.Mxcsr preMxcsr) { }
    /** offered is a fixture object; consumers must use assertSame/reference equality, not rebuild it. */
    public record StoppedExpectation(ExpectedCall call, QueueFp604Api.Stopped offered,
            boolean requireSameReference, boolean noNormalReturn, boolean noParentEpilogue,
            boolean noParentStateReplacement) implements Expectation { }
    public record Fixture(String caseId, PostState240Api.Input input,
            List<RamLiteral> initialRam, List<Long> sourcePC, List<Branch> branches,
            List<MemoryEvent> events, Expectation expected) { }

    // FFC0 is known; status bits 003F remain unknown. DF=true is an explicit fixture value.
    public static final QueueFp604Api.Mxcsr MXCSR_CONTROLS_ONLY =
            new QueueFp604Api.Mxcsr(0x8040, 0xffc0);

    public static final Bits128 X0 = new Bits128(0x0102030405060708L, 0x1112131415161718L);
    public static final Bits128 X1 = new Bits128(0x2122232425262728L, 0x3132333435363738L);
    public static final Bits128 X2 = new Bits128(0x4142434445464748L, 0x5152535455565758L);
    public static final Bits128 X3 = new Bits128(0x6162636465666768L, 0x7172737475767778L);
    public static final Bits128 X4 = new Bits128(0x8182838485868788L, 0x9192939495969798L);
    public static final Bits128 X5 = new Bits128(0xa1a2a3a4a5a6a7a8L, 0xb1b2b3b4b5b6b7b8L);
    public static final Bits128 X6 = new Bits128(0xc1c2c3c4c5c6c7c8L, 0xd1d2d3d4d5d6d7d8L);

    public static final VolatileBits EXTERNAL_INPUT_V = new VolatileBits(
            0x1020304050607080L, 0x0000000000400000L, 0x0000000000000000L,
            0x1122334455667788L, 0x2132435465768798L, 0x31425364758697a8L, 0x415263748596a7b8L,
            X0, X1, X2, X3, X4, X5);

    public static final VolatileBits ALIAS_INPUT_V = new VolatileBits(
            0x1020304050607080L, 0x0000000000100018L, 0x0000000000000000L,
            0x1122334455667788L, 0x2132435465768798L, 0x31425364758697a8L, 0x415263748596a7b8L,
            X0, X1, X2, X3, X4, X5);

    public static final VolatileBits STOP_INPUT_V = new VolatileBits(
            0x1020304050607080L, 0x0000000000400000L, 0x0000000000500000L,
            0x1122334455667788L, 0x2132435465768798L, 0x31425364758697a8L, 0x415263748596a7b8L,
            X0, X1, X2, X3, X4, X5);

    public static final VolatileBits EXTERNAL_NORMAL_V = new VolatileBits(
            0x0000000033456700L, 0x0000000000400000L, 0x0000000000000000L,
            0x1122334455667788L, 0x2132435465768798L, 0x31425364758697a8L, 0x415263748596a7b8L,
            X0, X1, X2, X3, X4, X5);

    public static final VolatileBits ALIAS_NORMAL_V = new VolatileBits(
            0x00000000000fff00L, 0x0000000000100018L, 0x0000000000000000L,
            0x1122334455667788L, 0x2132435465768798L, 0x31425364758697a8L, 0x415263748596a7b8L,
            X0, X1, X2, X3, X4, X5);

    public static final VolatileBits FIRST_CALL_V = new VolatileBits(
            0x000000014448d038L, 0x0000000000500000L, 0x00000000000ff990L,
            0x1122334455667788L, 0x2132435465768798L, 0x31425364758697a8L, 0x415263748596a7b8L,
            X0, X1, X2, X3, X4, X5);

    public static final NonvolatileBits INCOMING_N = new NonvolatileBits(
            0x88776655443322efL, 0x5566778811223344L, 0x0202020202020202L, 0x0303030303030303L,
            0x0404040404040404L, 0x0505050505050505L, 0x0606060606060606L, 0x0707070707070707L, X6);

    public static final NonvolatileBits ALIAS_INCOMING_N = new NonvolatileBits(
            0x00000000000fffc8L, 0x5566778811223344L, 0x0202020202020202L, 0x0303030303030303L,
            0x0404040404040404L, 0x0505050505050505L, 0x0606060606060606L, 0x0707070707070707L, X6);

    public static final NonvolatileBits FIRST_CALL_N = new NonvolatileBits(
            0x0000000000000000L, 0x00000000000ffa20L, 0x0000000000500000L, 0x0303030303030303L,
            0x0000000000000001L, 0x0000000000000000L, 0x0000000000400000L, 0x0707070707070707L, X6);

    public static final GovernmentCrtBoundary185Api.Entry EXTERNAL_ENTRY =
            new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000000100008L, EXTERNAL_INPUT_V, INCOMING_N);

    public static final GovernmentCrtBoundary185Api.Entry ALIAS_ENTRY =
            new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000000100008L, ALIAS_INPUT_V, ALIAS_INCOMING_N);

    public static final GovernmentCrtBoundary185Api.Entry STOP_ENTRY =
            new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x0000000000100008L, STOP_INPUT_V, INCOMING_N);

    public static final GovernmentCrtBoundary185Api.Entry FIRST_CHILD_ENTRY =
            new GovernmentCrtBoundary185Api.Entry(0x0000000140000000L, 0x00000000000ff918L, FIRST_CALL_V, FIRST_CALL_N);

    public static final PostState240Api.Input FIRST_CHILD_INPUT =
            new PostState240Api.Input(FIRST_CHILD_ENTRY, true, MXCSR_CONTROLS_ONLY, 0x23fc9dcL);

    public static final GovernmentCrtBoundary185Api.Call FIRST_CALL_BEFORE_PUSH =
            new GovernmentCrtBoundary185Api.Call(0x23fc9dcL,
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x3f57160L,
                    0x00000000000ff920L, FIRST_CALL_V, FIRST_CALL_N);

    public static final ExpectedCall FIRST_CALL = new ExpectedCall(
            FIRST_CALL_BEFORE_PUSH, FIRST_CHILD_INPUT, 5, 0x00000001423fc9e1L,
            true, MXCSR_CONTROLS_ONLY);

    public static final String FIRST_OPAQUE_STOP_IDENTITY_TOKEN = "ACT264_FIXTURE_OPAQUE_STOP_23FC9DC";

    // Artificial offered Stopped object: no opaque callee instructions or native fault are asserted.
    public static final QueueFp604Api.Stopped FIRST_OPAQUE_STOP_OFFER =
            new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                    new QueueFp604Api.Snapshot(FIRST_CHILD_ENTRY, 0x3f57160L, true, MXCSR_CONTROLS_ONLY),
                    0, 0x23fc9dcL);

    public static final Fixture NORMAL_EXTERNAL_TAG = new Fixture(
            "ACT264_NORMAL_EXTERNAL_TAG",
            new PostState240Api.Input(EXTERNAL_ENTRY, true, MXCSR_CONTROLS_ONLY, 0x1a8dc5cL),
            List.of(
                    new RamLiteral(0x0000000000100008L, 8, 0x0000000141a8dc61L, "fixture return slot supplied at whole-entry boundary"),
                    new RamLiteral(0x0000000000400000L, 8, 0x00000000334567efL, "fixture object-to-tag-base qword; no natural actor/vtable claim"),
                    new RamLiteral(0x0000000033456827L, 4, 0x11223344L, "fixture nonmatching tag dword")),
            List.of(
                    0x23fc970L, 0x23fc975L, 0x23fc976L, 0x23fc977L, 0x23fc978L, 0x23fc97aL,
                    0x23fc97cL, 0x23fc97eL, 0x23fc980L, 0x23fc988L, 0x23fc98fL, 0x23fc992L,
                    0x23fc995L, 0x23fc997L, 0x23fc99aL, 0x23fc9a0L, 0x23fc9a3L, 0x23fc9aaL,
                    0x23fc9b0L, 0x23fc9b3L, 0x23fdc05L, 0x23fdc07L, 0x23fdc0fL, 0x23fdc16L,
                    0x23fdc18L, 0x23fdc1aL, 0x23fdc1cL, 0x23fdc1eL, 0x23fdc1fL, 0x23fdc20L,
                    0x23fdc21L),
            List.of(
                    new Branch(0x23fc9aaL, "tag DWORD == 0x4744624f", false, null),
                    new Branch(0x23fc9b3L, "RDX == 0", true, 0x23fdc05L)),
            List.of(
                    new MemoryEvent(0x23fc970L, Access.WRITE, 8, 0x0000000000100018L, 0x88776655443322efL, "saved RBX"),
                    new MemoryEvent(0x23fc975L, Access.WRITE, 8, 0x0000000000100000L, 0x5566778811223344L, "PUSH RBP"),
                    new MemoryEvent(0x23fc976L, Access.WRITE, 8, 0x00000000000ffff8L, 0x0202020202020202L, "PUSH RSI"),
                    new MemoryEvent(0x23fc977L, Access.WRITE, 8, 0x00000000000ffff0L, 0x0303030303030303L, "PUSH RDI"),
                    new MemoryEvent(0x23fc978L, Access.WRITE, 8, 0x00000000000fffe8L, 0x0404040404040404L, "PUSH R12"),
                    new MemoryEvent(0x23fc97aL, Access.WRITE, 8, 0x00000000000fffe0L, 0x0505050505050505L, "PUSH R13"),
                    new MemoryEvent(0x23fc97cL, Access.WRITE, 8, 0x00000000000fffd8L, 0x0606060606060606L, "PUSH R14"),
                    new MemoryEvent(0x23fc97eL, Access.WRITE, 8, 0x00000000000fffd0L, 0x0707070707070707L, "PUSH R15"),
                    new MemoryEvent(0x23fc99aL, Access.WRITE, 4, 0x0000000000100020L, 0x00000000L, "RBP+600 equals incoming RSP+18; only four bytes written"),
                    new MemoryEvent(0x23fc9a0L, Access.READ, 8, 0x0000000000400000L, 0x00000000334567efL, "fresh qword load after prologue writes"),
                    new MemoryEvent(0x23fc9a3L, Access.READ, 4, 0x0000000033456827L, 0x11223344L, "fresh four-byte tag; alias fixture reads low DWORD of saved RBP"),
                    new MemoryEvent(0x23fdc07L, Access.READ, 8, 0x0000000000100018L, 0x88776655443322efL, "fresh saved RBX restore"),
                    new MemoryEvent(0x23fdc16L, Access.READ, 8, 0x00000000000fffd0L, 0x0707070707070707L, "POP R15"),
                    new MemoryEvent(0x23fdc18L, Access.READ, 8, 0x00000000000fffd8L, 0x0606060606060606L, "POP R14"),
                    new MemoryEvent(0x23fdc1aL, Access.READ, 8, 0x00000000000fffe0L, 0x0505050505050505L, "POP R13"),
                    new MemoryEvent(0x23fdc1cL, Access.READ, 8, 0x00000000000fffe8L, 0x0404040404040404L, "POP R12"),
                    new MemoryEvent(0x23fdc1eL, Access.READ, 8, 0x00000000000ffff0L, 0x0303030303030303L, "POP RDI"),
                    new MemoryEvent(0x23fdc1fL, Access.READ, 8, 0x00000000000ffff8L, 0x0202020202020202L, "POP RSI"),
                    new MemoryEvent(0x23fdc20L, Access.READ, 8, 0x0000000000100000L, 0x5566778811223344L, "POP RBP"),
                    new MemoryEvent(0x23fdc21L, Access.READ, 8, 0x0000000000100008L, 0x0000000141a8dc61L, "fresh RET slot; actual RSP increments by eight")),
            new NormalExpectation(new QueueFp604Api.Normal(
                    new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                            EXTERNAL_NORMAL_V, 0x0000000141a8dc61L,
                            0x0000000000100010L, INCOMING_N), true),
                    MXCSR_CONTROLS_ONLY)));

    public static final Fixture NORMAL_STACK_ALIAS = new Fixture(
            "ACT264_NORMAL_STACK_ALIAS",
            new PostState240Api.Input(ALIAS_ENTRY, true, MXCSR_CONTROLS_ONLY, 0x1a8dc5cL),
            List.of(
                    new RamLiteral(0x0000000000100008L, 8, 0x0000000141a8dc61L, "fixture return slot supplied at whole-entry boundary"),
                    new RamLiteral(0x0000000000100018L, 8, 0xcafebabedeadcafeL, "fixture sentinel overwritten before aliased object read"),
                    new RamLiteral(0x0000000000100000L, 8, 0x99aabbccddeeff00L, "fixture sentinel overwritten by PUSH RBP before aliased tag read")),
            List.of(
                    0x23fc970L, 0x23fc975L, 0x23fc976L, 0x23fc977L, 0x23fc978L, 0x23fc97aL,
                    0x23fc97cL, 0x23fc97eL, 0x23fc980L, 0x23fc988L, 0x23fc98fL, 0x23fc992L,
                    0x23fc995L, 0x23fc997L, 0x23fc99aL, 0x23fc9a0L, 0x23fc9a3L, 0x23fc9aaL,
                    0x23fc9b0L, 0x23fc9b3L, 0x23fdc05L, 0x23fdc07L, 0x23fdc0fL, 0x23fdc16L,
                    0x23fdc18L, 0x23fdc1aL, 0x23fdc1cL, 0x23fdc1eL, 0x23fdc1fL, 0x23fdc20L,
                    0x23fdc21L),
            List.of(
                    new Branch(0x23fc9aaL, "tag DWORD == 0x4744624f", false, null),
                    new Branch(0x23fc9b3L, "RDX == 0", true, 0x23fdc05L)),
            List.of(
                    new MemoryEvent(0x23fc970L, Access.WRITE, 8, 0x0000000000100018L, 0x00000000000fffc8L, "saved RBX"),
                    new MemoryEvent(0x23fc975L, Access.WRITE, 8, 0x0000000000100000L, 0x5566778811223344L, "PUSH RBP"),
                    new MemoryEvent(0x23fc976L, Access.WRITE, 8, 0x00000000000ffff8L, 0x0202020202020202L, "PUSH RSI"),
                    new MemoryEvent(0x23fc977L, Access.WRITE, 8, 0x00000000000ffff0L, 0x0303030303030303L, "PUSH RDI"),
                    new MemoryEvent(0x23fc978L, Access.WRITE, 8, 0x00000000000fffe8L, 0x0404040404040404L, "PUSH R12"),
                    new MemoryEvent(0x23fc97aL, Access.WRITE, 8, 0x00000000000fffe0L, 0x0505050505050505L, "PUSH R13"),
                    new MemoryEvent(0x23fc97cL, Access.WRITE, 8, 0x00000000000fffd8L, 0x0606060606060606L, "PUSH R14"),
                    new MemoryEvent(0x23fc97eL, Access.WRITE, 8, 0x00000000000fffd0L, 0x0707070707070707L, "PUSH R15"),
                    new MemoryEvent(0x23fc99aL, Access.WRITE, 4, 0x0000000000100020L, 0x00000000L, "RBP+600 equals incoming RSP+18; only four bytes written"),
                    new MemoryEvent(0x23fc9a0L, Access.READ, 8, 0x0000000000100018L, 0x00000000000fffc8L, "fresh qword load after prologue writes"),
                    new MemoryEvent(0x23fc9a3L, Access.READ, 4, 0x0000000000100000L, 0x11223344L, "fresh four-byte tag; alias fixture reads low DWORD of saved RBP"),
                    new MemoryEvent(0x23fdc07L, Access.READ, 8, 0x0000000000100018L, 0x00000000000fffc8L, "fresh saved RBX restore"),
                    new MemoryEvent(0x23fdc16L, Access.READ, 8, 0x00000000000fffd0L, 0x0707070707070707L, "POP R15"),
                    new MemoryEvent(0x23fdc18L, Access.READ, 8, 0x00000000000fffd8L, 0x0606060606060606L, "POP R14"),
                    new MemoryEvent(0x23fdc1aL, Access.READ, 8, 0x00000000000fffe0L, 0x0505050505050505L, "POP R13"),
                    new MemoryEvent(0x23fdc1cL, Access.READ, 8, 0x00000000000fffe8L, 0x0404040404040404L, "POP R12"),
                    new MemoryEvent(0x23fdc1eL, Access.READ, 8, 0x00000000000ffff0L, 0x0303030303030303L, "POP RDI"),
                    new MemoryEvent(0x23fdc1fL, Access.READ, 8, 0x00000000000ffff8L, 0x0202020202020202L, "POP RSI"),
                    new MemoryEvent(0x23fdc20L, Access.READ, 8, 0x0000000000100000L, 0x5566778811223344L, "POP RBP"),
                    new MemoryEvent(0x23fdc21L, Access.READ, 8, 0x0000000000100008L, 0x0000000141a8dc61L, "fresh RET slot; actual RSP increments by eight")),
            new NormalExpectation(new QueueFp604Api.Normal(
                    new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                            ALIAS_NORMAL_V, 0x0000000141a8dc61L,
                            0x0000000000100010L, ALIAS_INCOMING_N), true),
                    MXCSR_CONTROLS_ONLY)));

    public static final Fixture STOP_FIRST_OPAQUE = new Fixture(
            "ACT264_STOP_FIRST_OPAQUE",
            new PostState240Api.Input(STOP_ENTRY, true, MXCSR_CONTROLS_ONLY, 0x1a8dc5cL),
            List.of(
                    new RamLiteral(0x0000000000100008L, 8, 0x0000000141a8dc61L, "fixture return slot supplied at whole-entry boundary"),
                    new RamLiteral(0x0000000000400000L, 8, 0x00000000334567efL, "fixture object-to-tag-base qword; no natural actor/vtable claim"),
                    new RamLiteral(0x0000000033456827L, 4, 0x11223344L, "fixture nonmatching tag dword")),
            List.of(
                    0x23fc970L, 0x23fc975L, 0x23fc976L, 0x23fc977L, 0x23fc978L, 0x23fc97aL,
                    0x23fc97cL, 0x23fc97eL, 0x23fc980L, 0x23fc988L, 0x23fc98fL, 0x23fc992L,
                    0x23fc995L, 0x23fc997L, 0x23fc99aL, 0x23fc9a0L, 0x23fc9a3L, 0x23fc9aaL,
                    0x23fc9b0L, 0x23fc9b3L, 0x23fc9b9L, 0x23fc9c0L, 0x23fc9c5L, 0x23fc9cbL,
                    0x23fc9d0L, 0x23fc9d4L, 0x23fc9d9L, 0x23fc9dcL),
            List.of(
                    new Branch(0x23fc9aaL, "tag DWORD == 0x4744624f", false, null),
                    new Branch(0x23fc9b3L, "RDX == 0", false, null)),
            List.of(
                    new MemoryEvent(0x23fc970L, Access.WRITE, 8, 0x0000000000100018L, 0x88776655443322efL, "saved RBX"),
                    new MemoryEvent(0x23fc975L, Access.WRITE, 8, 0x0000000000100000L, 0x5566778811223344L, "PUSH RBP"),
                    new MemoryEvent(0x23fc976L, Access.WRITE, 8, 0x00000000000ffff8L, 0x0202020202020202L, "PUSH RSI"),
                    new MemoryEvent(0x23fc977L, Access.WRITE, 8, 0x00000000000ffff0L, 0x0303030303030303L, "PUSH RDI"),
                    new MemoryEvent(0x23fc978L, Access.WRITE, 8, 0x00000000000fffe8L, 0x0404040404040404L, "PUSH R12"),
                    new MemoryEvent(0x23fc97aL, Access.WRITE, 8, 0x00000000000fffe0L, 0x0505050505050505L, "PUSH R13"),
                    new MemoryEvent(0x23fc97cL, Access.WRITE, 8, 0x00000000000fffd8L, 0x0606060606060606L, "PUSH R14"),
                    new MemoryEvent(0x23fc97eL, Access.WRITE, 8, 0x00000000000fffd0L, 0x0707070707070707L, "PUSH R15"),
                    new MemoryEvent(0x23fc99aL, Access.WRITE, 4, 0x0000000000100020L, 0x00000000L, "RBP+600 equals incoming RSP+18; only four bytes written"),
                    new MemoryEvent(0x23fc9a0L, Access.READ, 8, 0x0000000000400000L, 0x00000000334567efL, "fresh qword load after prologue writes"),
                    new MemoryEvent(0x23fc9a3L, Access.READ, 4, 0x0000000033456827L, 0x11223344L, "fresh four-byte tag; alias fixture reads low DWORD of saved RBP"),
                    new MemoryEvent(0x23fc9c0L, Access.WRITE, 8, 0x00000000000ff990L, 0x000000014448d038L, "LEA address only; no pointee bytes read"),
                    new MemoryEvent(0x23fc9cbL, Access.WRITE, 4, 0x00000000000ff998L, 0x00000001L, "zero-extended R12D=1"),
                    new MemoryEvent(0x23fc9d0L, Access.WRITE, 1, 0x00000000000ff99cL, 0x00L, "BL=0; no writes to padding at +7D..+7F"),
                    new MemoryEvent(0x23fc9dcL, Access.WRITE, 8, 0x00000000000ff918L, 0x00000001423fc9e1L, "owned architectural CALL push before callback")),
            new StoppedExpectation(FIRST_CALL, FIRST_OPAQUE_STOP_OFFER, true, true, true, true));

    public static final List<Fixture> ALL = List.of(
            NORMAL_EXTERNAL_TAG, NORMAL_STACK_ALIAS, STOP_FIRST_OPAQUE);
}
