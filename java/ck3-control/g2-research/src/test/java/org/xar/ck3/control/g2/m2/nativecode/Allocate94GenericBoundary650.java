package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.Generic94Fixture650.Event;
import org.xar.ck3.control.g2.m2.nativecode.Generic94Fixture650.Ram;
import static org.xar.ck3.control.g2.m2.nativecode.Generic94Fixture650.e;

/** Two generic94 owned-software-RAM witnesses, with explicit full lower outcomes. */
public final class Allocate94GenericBoundary650 {
    private Allocate94GenericBoundary650() { }
    private static final long IMAGE = 0x140000000L;

    private static void check(boolean ok, String why) {
        if (!ok) throw new AssertionError(why);
    }
    private static void equal(Object expected, Object actual, String why) {
        check(Objects.equals(expected, actual), why);
    }
    private static void same(Object expected, Object actual, String why) {
        check(expected == actual, why);
    }
    private static void prefix(List<Event> expected, int count, Ram ram, String why) {
        equal(expected.subList(0, count), ram.events, why);
    }
    private static void fullBytes(Map<Long, Byte> expected, Ram ram, String why) {
        check(expected.size() == 160, "complete160 expected byte keys");
        equal(expected, ram.fullBytes(), why);
    }
    private static void region(Map<Long, Byte> map, long address, String hex) {
        byte[] raw = HexFormat.of().parseHex(hex);
        for (int i = 0; i < raw.length; i++) {
            check(map.put(address + i, raw[i]) == null, "disjoint literal RAM regions");
        }
    }
    private static QueueFp604Api.Normal normal(VolatileBits v, NonvolatileBits n,
            long rip, long sp, boolean df, QueueFp604Api.Mxcsr fp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v, rip, sp, n), df), fp);
    }

    private static VolatileBits entryV() {
        return new VolatileBits(0x8100000000000101L, 0x0000000000000000L, 0x8300000000000103L, 0x8400000000000104L, 0x8500000000000105L, 0x8600000000000106L, 0x8700000000000107L,
                new Bits128(0x1100000000001000L, 0xee00000000002000L),
                new Bits128(0x1100000000001001L, 0xee00000000002001L),
                new Bits128(0x1100000000001002L, 0xee00000000002002L),
                new Bits128(0x1100000000001003L, 0xee00000000002003L),
                new Bits128(0x1100000000001004L, 0xee00000000002004L),
                new Bits128(0x1100000000001005L, 0xee00000000002005L));
    }

    private static VolatileBits heap1InV() {
        return new VolatileBits(0x0000000000000001L, 0xface00000000a101L, 0x0000000000000000L, 0x0000000000000001L, 0x8500000000000105L, 0x8600000000000106L, 0x8700000000000107L,
                new Bits128(0x1100000000001000L, 0xee00000000002000L),
                new Bits128(0x1100000000001001L, 0xee00000000002001L),
                new Bits128(0x1100000000001002L, 0xee00000000002002L),
                new Bits128(0x1100000000001003L, 0xee00000000002003L),
                new Bits128(0x1100000000001004L, 0xee00000000002004L),
                new Bits128(0x1100000000001005L, 0xee00000000002005L));
    }

    private static VolatileBits heap0OutV() {
        return new VolatileBits(0x0000000000000000L, 0xa200000000000302L, 0xa300000000000303L, 0xa400000000000304L, 0xa500000000000305L, 0xa600000000000306L, 0xa700000000000307L,
                new Bits128(0x2200000000003000L, 0xdd00000000004000L),
                new Bits128(0x2200000000003001L, 0xdd00000000004001L),
                new Bits128(0x2200000000003002L, 0xdd00000000004002L),
                new Bits128(0x2200000000003003L, 0xdd00000000004003L),
                new Bits128(0x2200000000003004L, 0xdd00000000004004L),
                new Bits128(0x2200000000003005L, 0xdd00000000004005L));
    }

    private static VolatileBits policyOutV() {
        return new VolatileBits(0xd00d000000000001L, 0xb200000000000402L, 0xb300000000000403L, 0xb400000000000404L, 0xb500000000000405L, 0xb600000000000406L, 0xb700000000000407L,
                new Bits128(0x3300000000005000L, 0xcc00000000006000L),
                new Bits128(0x3300000000005001L, 0xcc00000000006001L),
                new Bits128(0x3300000000005002L, 0xcc00000000006002L),
                new Bits128(0x3300000000005003L, 0xcc00000000006003L),
                new Bits128(0x3300000000005004L, 0xcc00000000006004L),
                new Bits128(0x3300000000005005L, 0xcc00000000006005L));
    }

    private static VolatileBits gateInV() {
        return new VolatileBits(0xd00d000000000001L, 0x0000000000000001L, 0xb300000000000403L, 0xb400000000000404L, 0xb500000000000405L, 0xb600000000000406L, 0xb700000000000407L,
                new Bits128(0x3300000000005000L, 0xcc00000000006000L),
                new Bits128(0x3300000000005001L, 0xcc00000000006001L),
                new Bits128(0x3300000000005002L, 0xcc00000000006002L),
                new Bits128(0x3300000000005003L, 0xcc00000000006003L),
                new Bits128(0x3300000000005004L, 0xcc00000000006004L),
                new Bits128(0x3300000000005005L, 0xcc00000000006005L));
    }

    private static VolatileBits gateOutV() {
        return new VolatileBits(0xe00e000000000001L, 0xc200000000000502L, 0xc300000000000503L, 0xc400000000000504L, 0xc500000000000505L, 0xc600000000000506L, 0xc700000000000507L,
                new Bits128(0x4400000000007000L, 0xbb00000000008000L),
                new Bits128(0x4400000000007001L, 0xbb00000000008001L),
                new Bits128(0x4400000000007002L, 0xbb00000000008002L),
                new Bits128(0x4400000000007003L, 0xbb00000000008003L),
                new Bits128(0x4400000000007004L, 0xbb00000000008004L),
                new Bits128(0x4400000000007005L, 0xbb00000000008005L));
    }

    private static VolatileBits heap2InV() {
        return new VolatileBits(0xe00e000000000001L, 0xbeef00000000a202L, 0x0000000000000000L, 0x0000000000000001L, 0xc500000000000505L, 0xc600000000000506L, 0xc700000000000507L,
                new Bits128(0x4400000000007000L, 0xbb00000000008000L),
                new Bits128(0x4400000000007001L, 0xbb00000000008001L),
                new Bits128(0x4400000000007002L, 0xbb00000000008002L),
                new Bits128(0x4400000000007003L, 0xbb00000000008003L),
                new Bits128(0x4400000000007004L, 0xbb00000000008004L),
                new Bits128(0x4400000000007005L, 0xbb00000000008005L));
    }

    private static VolatileBits heap2OutV() {
        return new VolatileBits(0x8000000000000000L, 0xd200000000000602L, 0xd300000000000603L, 0xd400000000000604L, 0xd500000000000605L, 0xd600000000000606L, 0xd700000000000607L,
                new Bits128(0x5500000000009000L, 0xaa0000000000a000L),
                new Bits128(0x5500000000009001L, 0xaa0000000000a001L),
                new Bits128(0x5500000000009002L, 0xaa0000000000a002L),
                new Bits128(0x5500000000009003L, 0xaa0000000000a003L),
                new Bits128(0x5500000000009004L, 0xaa0000000000a004L),
                new Bits128(0x5500000000009005L, 0xaa0000000000a005L));
    }

    private static NonvolatileBits entryN() {
        return new NonvolatileBits(0x0000000000000000L, 0x9200000000000202L, 0x9300000000000203L, 0x9400000000000204L, 0xcafe123400000205L, 0x9600000000000206L, 0x9700000000000207L, 0x9800000000000208L,
                new Bits128(0x1600000000002606L, 0xe900000000003606L));
    }

    private static NonvolatileBits lowerN() {
        return new NonvolatileBits(0x0000000000000001L, 0x9200000000000202L, 0x9300000000000203L, 0x9400000000000204L, 0xcafe123400000205L, 0x9600000000000206L, 0x9700000000000207L, 0x9800000000000208L,
                new Bits128(0x1600000000002606L, 0xe900000000003606L));
    }

    private static GovernmentCrtBoundary185Api.Entry entry() {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE, 0x72006008L, entryV(), entryN());
    }

    private static Map<Long, Byte> initialBytes() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x00000000000a2000L, "cccccccccccccccccccccccccccccccc");
        region(map, 0x0000000072005fb8L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ab33b2244010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x00000001443da768L, "00011100000000f0");
        region(map, 0x0000000145c5de30L, "01a100000000cefa");
        check(map.size() == 160, "complete160 literal RAM keys");
        return map;
    }

    private static Map<Long, Byte> normalBytes() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x00000000000a2000L, "61626364cccccccccccccccccccccccc");
        region(map, 0x0000000072005fb8L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ae4fd2444010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a0000000000000000b33b2244010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x00000001443da768L, "00022200000000e0");
        region(map, 0x0000000145c5de30L, "02a200000000efbe");
        check(map.size() == 160, "complete160 literal RAM keys");
        return map;
    }

    private static Map<Long, Byte> stoppedBytes() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x00000000000a2000L, "6172cccccccccccc8877665544332211");
        region(map, 0x0000000072005fb8L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ac2fd2444010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a0000000000000000b33b2244010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x00000001443da768L, "00022200000000e0");
        region(map, 0x0000000145c5de30L, "02a200000000efbe");
        check(map.size() == 160, "complete160 literal RAM keys");
        return map;
    }

    private static void seed(Ram ram) {
        ram.seedFill(0x0000000072005fb8L, 128, 90);
        ram.seedFill(0x00000000000a2000L, 16, 204);
        ram.seedScalar(0x0000000072006008L, 8, 0x0000000144223bb3L);
        ram.seedScalar(0x0000000145c5de30L, 8, 0xface00000000a101L);
        ram.seedScalar(0x00000001443da768L, 8, 0xf000000000110100L);
    }

    private static List<Event> normalEvents() {
        return List.of(
                e("W64", 0x0000000072006000L, 0x0000000000000000L),
                e("R64", 0x0000000145c5de30L, 0xface00000000a101L),
                e("R64", 0x00000001443da768L, 0xf000000000110100L),
                e("W64", 0x0000000072005fd8L, 0x000000014424fde4L),
                e("INVOKE", 0x000000000424fddeL, 0xf000000000110100L),
                e("W8", 0x00000000000a2000L, 0x0000000000000061L),
                e("W64", 0x0000000145c5de30L, 0xbeef00000000a202L),
                e("W64", 0x00000001443da768L, 0xe000000000220200L),
                e("BUDGET", 0x000000000424fdbdL, 0x0000000000000000L),
                e("W64", 0x0000000072005fd8L, 0x000000014424fdc2L),
                e("INVOKE", 0x000000000424fdbdL, 0x000000000424e250L),
                e("W8", 0x00000000000a2001L, 0x0000000000000062L),
                e("W64", 0x0000000072005fd8L, 0x000000014424fdceL),
                e("INVOKE", 0x000000000424fdc9L, 0x000000000424cffcL),
                e("W8", 0x00000000000a2002L, 0x0000000000000063L),
                e("R64", 0x0000000145c5de30L, 0xbeef00000000a202L),
                e("R64", 0x00000001443da768L, 0xe000000000220200L),
                e("W64", 0x0000000072005fd8L, 0x000000014424fde4L),
                e("INVOKE", 0x000000000424fddeL, 0xe000000000220200L),
                e("W8", 0x00000000000a2003L, 0x0000000000000064L),
                e("R64", 0x0000000072006000L, 0x0000000000000000L),
                e("R64", 0x0000000072006008L, 0x0000000144223bb3L));
    }

    private static List<Event> stoppedEvents() {
        return List.of(
                e("W64", 0x0000000072006000L, 0x0000000000000000L),
                e("R64", 0x0000000145c5de30L, 0xface00000000a101L),
                e("R64", 0x00000001443da768L, 0xf000000000110100L),
                e("W64", 0x0000000072005fd8L, 0x000000014424fde4L),
                e("INVOKE", 0x000000000424fddeL, 0xf000000000110100L),
                e("W8", 0x00000000000a2000L, 0x0000000000000061L),
                e("W64", 0x0000000145c5de30L, 0xbeef00000000a202L),
                e("W64", 0x00000001443da768L, 0xe000000000220200L),
                e("BUDGET", 0x000000000424fdbdL, 0x0000000000000000L),
                e("W64", 0x0000000072005fd8L, 0x000000014424fdc2L),
                e("INVOKE", 0x000000000424fdbdL, 0x000000000424e250L),
                e("W8", 0x00000000000a2001L, 0x0000000000000072L),
                e("W64", 0x00000000000a2008L, 0x1122334455667788L));
    }


    private static KnownHeapAllocateFp623.AllocateCall expectedFrame(long site,
            GovernmentCrtBoundary185Api.TargetKind kind, long target, VolatileBits v,
            boolean df, QueueFp604Api.Mxcsr fp) {
        NonvolatileBits n = lowerN();
        GovernmentCrtBoundary185Api.Call original = new GovernmentCrtBoundary185Api.Call(
                site, kind, target, 0x72005FE0L, v, n);
        GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                IMAGE, 0x72005FD8L, v, n);
        return new KnownHeapAllocateFp623.AllocateCall(original, child, df, fp);
    }
    private static void completeFrame(KnownHeapAllocateFp623.AllocateCall expected,
            KnownHeapAllocateFp623.AllocateCall actual, long literalRip, String why) {
        equal(expected, actual, why + " original/child/fullV/fullN/DF/FP");
        same(expected.preMxcsr(), actual.preMxcsr(), why + " SAME current FP");
        check(actual.returnRipBits() == literalRip, why + " actual5or6-byte continuation");
    }

    public static void zeroSizeRetriesFreshHeapAndIatThenReturnsFullState() {
        Map<Long, Byte> initial = initialBytes();
        Map<Long, Byte> expectedBytes = normalBytes();
        List<Event> literal = normalEvents();
        QueueFp604Api.Mxcsr u = new QueueFp604Api.Mxcsr(0, 0);
        QueueFp604Api.Mxcsr a = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Mxcsr b = new QueueFp604Api.Mxcsr(128, 192);
        QueueFp604Api.Mxcsr c = new QueueFp604Api.Mxcsr(256, 768);
        QueueFp604Api.Mxcsr d = new QueueFp604Api.Mxcsr(1024, 3072);
        QueueFp604Api.Normal h0 = normal(heap0OutV(), lowerN(), 0x14424FDE4L, 0x72005FE0L, false, a);
        QueueFp604Api.Normal policy = normal(policyOutV(), lowerN(), 0x14424FDC2L, 0x72005FE0L, true, b);
        QueueFp604Api.Normal gate = normal(gateOutV(), lowerN(), 0x14424FDCEL, 0x72005FE0L, false, c);
        QueueFp604Api.Normal h2 = normal(heap2OutV(), lowerN(), 0x14424FDE4L, 0x72005FE0L, true, d);
        QueueFp604Api.Normal expectedWhole = normal(heap2OutV(), entryN(),
                0x144223BB3L, 0x72006010L, true, d);
        GovernmentCrtBoundary185Api.TargetKind direct = GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
        GovernmentCrtBoundary185Api.TargetKind indirect = GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE;
        KnownHeapAllocateFp623.AllocateCall[] frames = {
                expectedFrame(0x424FDDEL, indirect, 0xF000000000110100L, heap1InV(), true, u),
                expectedFrame(0x424FDBDL, direct, 0x424E250L, heap0OutV(), false, a),
                expectedFrame(0x424FDC9L, direct, 0x424CFFCL, gateInV(), true, b),
                expectedFrame(0x424FDDEL, indirect, 0xE000000000220200L, heap2InV(), false, c)};
        long[] returnRips = {0x14424FDE4L, 0x14424FDC2L, 0x14424FDCEL, 0x14424FDE4L};
        int[] prefixes = {4, 10, 13, 18};
        int[] invokes = new int[1];
        int[] budgets = new int[1];
        Ram ram = new Ram();
        seed(ram);
        fullBytes(initial, ram, "normal all160 initial keys/bytes");
        check(ram.events.isEmpty(), "normal seeds have no events");
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, guard) -> {
            check(++budgets[0] == 1 && invokes[0] == 1, "one policy budget after null firstheap");
            check(pc == 0x424FDBDL && guard == 0, "literal policy budget PC/raw guard");
            prefix(literal, 8, ram, "budget follows all firstheap alias writes before policy push");
            ram.step(pc, guard);
        };
        KnownHeapAllocateFp623.AllocateCalls calls = frame -> {
            int turn = ++invokes[0];
            check(turn <= 4, "exact four reached generic94 ports");
            completeFrame(frames[turn - 1], frame, returnRips[turn - 1], "normal port " + turn);
            check(budgets[0] == (turn == 1 ? 0 : 1), "no firstheap/gate/secondheap budget");
            prefix(literal, prefixes[turn - 1], ram, "complete source prefix before opaque normal port");
            ram.events.add(e("INVOKE", frame.original().callSiteRva(), frame.original().targetBits()));
            if (turn == 1) {
                check(u.valueBits() == 0 && u.knownMaskBits() == 0 && !u.isExact(),
                        "explicit unknown input admitted without a default");
                ram.writeByte(0xA2000L, 0x61);
                ram.writeQword(0x145C5DE30L, 0xBEEF00000000A202L);
                ram.writeQword(0x1443DA768L, 0xE000000000220200L);
                return h0;
            }
            if (turn == 2) {
                ram.writeByte(0xA2001L, 0x62);
                return policy;
            }
            if (turn == 3) {
                check(frame.original().volatileBits().raxBits() == 0xD00D000000000001L
                        && (int)frame.original().volatileBits().raxBits() == 1,
                        "policy uses lowEAX1 while complete highRAX survives");
                ram.writeByte(0xA2002L, 0x63);
                return gate;
            }
            check(frame.original().volatileBits().raxBits() == 0xE00E000000000001L
                    && (int)frame.original().volatileBits().raxBits() == 1,
                    "gate uses lowEAX1; fresh secondheap retains all other current bits");
            ram.writeByte(0xA2003L, 0x64);
            return h2;
        };
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(entry(), true, u);
        QueueFp604Api.Outcome result = Allocate94EntryFp650.execute(input, ram, calls, budget);
        check(result instanceof QueueFp604Api.Normal, "generic94 whole Normal");
        QueueFp604Api.Normal actual = (QueueFp604Api.Normal)result;
        equal(expectedWhole, actual, "full wholeV/XMM/N/RIP/SP/DF/partialFP");
        same(d, actual.postMxcsr(), "SAME accepted final partialD");
        check(actual != h0 && actual != policy && actual != gate && actual != h2,
                "whole freshPOP/RET result is not a lower offer");
        check(actual.base().normalReturn().volatileBits().raxBits() == 0x8000000000000000L
                && (int)actual.base().normalReturn().volatileBits().raxBits() == 0,
                "heap fullRAX success despite lowEAX0");
        check(actual.base().normalReturn().nonvolatileBits().r12Bits() == 0xCAFE123400000205L,
                "full rawR12 restored without truncation");
        check(invokes[0] == 4 && budgets[0] == 1, "normal exact calls/budget");
        same(u, input.mxcsr(), "input unknown object unchanged");
        equal(literal, ram.events, "all22 source/opaque/budget events and no extra effects");
        fullBytes(expectedBytes, ram, "all160 final bytes including padding and both aliases");
    }

    public static void zeroSizePolicySameStoppedPreservesPrefix() {
        Map<Long, Byte> initial = initialBytes();
        Map<Long, Byte> expectedBytes = stoppedBytes();
        List<Event> literal = stoppedEvents();
        QueueFp604Api.Mxcsr u = new QueueFp604Api.Mxcsr(0, 0);
        QueueFp604Api.Mxcsr a = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Normal h0 = normal(heap0OutV(), lowerN(), 0x14424FDE4L, 0x72005FE0L, false, a);
        GovernmentCrtBoundary185Api.Entry chosenState = new GovernmentCrtBoundary185Api.Entry(
                IMAGE, 0x72005FD8L, heap0OutV(), lowerN());
        QueueFp604Api.Snapshot chosenSnapshot = new QueueFp604Api.Snapshot(
                chosenState, 0x424E250L, false, a);
        QueueFp604Api.Stopped offered = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE, chosenSnapshot, 0, 0x424FDBDL);
        KnownHeapAllocateFp623.AllocateCall firstFrame = expectedFrame(0x424FDDEL,
                GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                0xF000000000110100L, heap1InV(), true, u);
        KnownHeapAllocateFp623.AllocateCall policyFrame = expectedFrame(0x424FDBDL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x424E250L, heap0OutV(), false, a);
        int[] invokes = new int[1];
        int[] budgets = new int[1];
        Ram ram = new Ram();
        seed(ram);
        fullBytes(initial, ram, "stopped all160 initial keys/bytes");
        check(ram.events.isEmpty(), "stopped seeds have no events");
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, guard) -> {
            check(++budgets[0] == 1 && invokes[0] == 1, "one budget before stopped policy");
            check(pc == 0x424FDBDL && guard == 0, "stop exact policy budget");
            prefix(literal, 8, ram, "stop budget after firstheap alias effects before policy push");
            ram.step(pc, guard);
        };
        KnownHeapAllocateFp623.AllocateCalls calls = frame -> {
            int turn = ++invokes[0];
            check(turn <= 2, "no opaque port after policyStopped");
            if (turn == 1) {
                completeFrame(firstFrame, frame, 0x14424FDE4L, "stop firstheap");
                check(budgets[0] == 0 && u.valueBits() == 0 && u.knownMaskBits() == 0,
                        "stop initial unknownFP has no inferred controls");
                prefix(literal, 4, ram, "stop firstheap ownedpush and freshreads");
                ram.events.add(e("INVOKE", frame.original().callSiteRva(), frame.original().targetBits()));
                ram.writeByte(0xA2000L, 0x61);
                ram.writeQword(0x145C5DE30L, 0xBEEF00000000A202L);
                ram.writeQword(0x1443DA768L, 0xE000000000220200L);
                return h0;
            }
            completeFrame(policyFrame, frame, 0x14424FDC2L, "stopped policy currentfullframe");
            check(budgets[0] == 1, "stop follows exactly one realpolicybudget");
            prefix(literal, 10, ram, "stop policy ownedpush after budget");
            ram.events.add(e("INVOKE", frame.original().callSiteRva(), frame.original().targetBits()));
            ram.writeByte(0xA2001L, 0x72);
            ram.writeQword(0xA2008L, 0x1122334455667788L);
            return offered;
        };
        DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(entry(), true, u);
        QueueFp604Api.Outcome result = Allocate94EntryFp650.execute(input, ram, calls, budget);
        same(offered, result, "SAME precreated fullStopped at generic94 boundary");
        QueueFp604Api.Stopped actual = (QueueFp604Api.Stopped)result;
        same(chosenSnapshot, actual.snapshot(), "SAME chosen Snapshot");
        equal(chosenState, actual.snapshot().currentState(), "complete chosen image/SP/V/N/XMM snapshot");
        same(a, actual.snapshot().mxcsr(), "SAME accepted partialA_STOP");
        check(actual.reason() == QueueFp604Api.StopReason.MISSING_POST_STATE
                && actual.raisedConditionBits() == 0 && actual.originCallSiteRva() == 0x424FDBDL
                && actual.snapshot().instructionRva() == 0x424E250L
                && !actual.snapshot().directionFlagSet(), "all unchanged opaqueStopped metadata");
        check(invokes[0] == 2 && budgets[0] == 1, "no gate/heap2/error/extra budget afterStopped");
        same(u, input.mxcsr(), "fresh stop input unknown object unchanged");
        equal(literal, ram.events, "all13 stopped prefix events, no POP/RET or continuation");
        fullBytes(expectedBytes, ram, "all160 stopped bytes and retained callback effects");
    }

    public static int verify() {
        zeroSizeRetriesFreshHeapAndIatThenReturnsFullState();
        zeroSizePolicySameStoppedPreservesPrefix();
        return 2;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
