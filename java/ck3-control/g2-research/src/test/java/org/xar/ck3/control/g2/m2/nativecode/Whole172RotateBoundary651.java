package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m3.add4range262.Add4Range262;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.WholeRotateFixture651.Event;
import org.xar.ck3.control.g2.m2.nativecode.WholeRotateFixture651.Ram;
import static org.xar.ck3.control.g2.m2.nativecode.WholeRotateFixture651.e;

/** Two finite owned-RAM failure prefixes at the actual whole172 entry. */
public final class Whole172RotateBoundary651 {
    private Whole172RotateBoundary651() { }
    private static final long IMAGE = 0x140000000L;
    private static final long ROOT_SP = 0x70008008L;

    private static void check(boolean ok, String why) {
        if (!ok) throw new AssertionError(why);
    }
    private static void equal(Object expected, Object actual, String why) {
        check(Objects.equals(expected, actual), why);
    }
    private static void same(Object expected, Object actual, String why) {
        check(expected == actual, why);
    }
    private static void prefix(List<Event> expected, int size, Ram ram, String why) {
        equal(expected.subList(0, size), ram.events, why);
    }
    private static void fullBytes(Map<Long, Byte> expected, Ram ram, String why) {
        check(expected.size() == 452, "all452 expected keys");
        equal(expected, ram.fullBytes(), why);
    }
    private static void region(Map<Long, Byte> map, long address, String hex) {
        byte[] raw = HexFormat.of().parseHex(hex);
        for (int i = 0; i < raw.length; i++) {
            check(map.put(address + i, raw[i]) == null, "disjoint literal regions");
        }
    }
    private static void fill(Ram ram, long address, int count, int value) {
        byte[] raw = new byte[count];
        java.util.Arrays.fill(raw, (byte)value);
        ram.seedBytes(address, raw);
    }
    private static QueueFp604Api.Normal normal(VolatileBits v, NonvolatileBits n,
            long rip, long sp, boolean df, QueueFp604Api.Mxcsr fp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v, rip, sp, n), df), fp);
    }
    private static void completeNormal(QueueFp604Api.Normal expected,
            QueueFp604Api.Outcome actual, String why) {
        check(actual instanceof QueueFp604Api.Normal, why + " complete Normal");
        QueueFp604Api.Normal offered = (QueueFp604Api.Normal) actual;
        equal(expected, offered, why + " complete V/XMM/N/RIP/SP/DF/FP");
        same(expected.postMxcsr(), offered.postMxcsr(), why + " SAME partial FP");
    }

    private static VolatileBits rootV() {
        return new VolatileBits(0x8100000000001001L, 0x0000000070007f80L, 0x0000000000020000L, 0x8400000000001004L, 0x8500000000001005L, 0x8600000000001006L, 0x8700000000001007L,
                new Bits128(0x1111000000000100L, 0xeeee000000000100L),
                new Bits128(0x1111000000000101L, 0xeeee000000000101L),
                new Bits128(0x1111000000000102L, 0xeeee000000000102L),
                new Bits128(0x1111000000000103L, 0xeeee000000000103L),
                new Bits128(0x1111000000000104L, 0xeeee000000000104L),
                new Bits128(0x1111000000000105L, 0xeeee000000000105L));
    }

    private static VolatileBits firstV() {
        return new VolatileBits(0x00000001454de260L, 0x0000000070007f90L, 0x0000000000000000L, 0x0000000000030000L, 0x0000000000030010L, 0x8600000000001006L, 0x8700000000001007L,
                new Bits128(0x1111000000000100L, 0xeeee000000000100L),
                new Bits128(0x1111000000000101L, 0xeeee000000000101L),
                new Bits128(0x1111000000000102L, 0xeeee000000000102L),
                new Bits128(0x1111000000000103L, 0xeeee000000000103L),
                new Bits128(0x1111000000000104L, 0xeeee000000000104L),
                new Bits128(0x1111000000000105L, 0xeeee000000000105L));
    }

    private static VolatileBits allocatorFrameV() {
        return new VolatileBits(0x0000000000060000L, 0x00000001454de260L, 0x0000000000000010L, 0x0000000000000008L, 0x0000000000030010L, 0x8600000000001006L, 0x8700000000001007L,
                new Bits128(0x0000000000000000L, 0x0000000000000000L),
                new Bits128(0x1111000000000101L, 0xeeee000000000101L),
                new Bits128(0x1111000000000102L, 0xeeee000000000102L),
                new Bits128(0x1111000000000103L, 0xeeee000000000103L),
                new Bits128(0x1111000000000104L, 0xeeee000000000104L),
                new Bits128(0x1111000000000105L, 0xeeee000000000105L));
    }

    private static VolatileBits allocatorOfferV() {
        return new VolatileBits(0x0000000000050000L, 0xa200000000001002L, 0xa300000000001003L, 0xa400000000001004L, 0xa500000000001005L, 0xa600000000001006L, 0xa700000000001007L,
                new Bits128(0x2222000000000200L, 0xdddd000000000200L),
                new Bits128(0x2222000000000201L, 0xdddd000000000201L),
                new Bits128(0x2222000000000202L, 0xdddd000000000202L),
                new Bits128(0x2222000000000203L, 0xdddd000000000203L),
                new Bits128(0x2222000000000204L, 0xdddd000000000204L),
                new Bits128(0x2222000000000205L, 0xdddd000000000205L));
    }

    private static VolatileBits freeFrameV() {
        return new VolatileBits(0x0000000000060000L, 0x00000001454de260L, 0x0000000000000000L, 0x0000000000000008L, 0x0000000000000000L, 0x0000000000000000L, 0xa700000000001007L,
                new Bits128(0x8877665544332211L, 0x00ffeeddccbbaa99L),
                new Bits128(0x2222000000000201L, 0xdddd000000000201L),
                new Bits128(0x2222000000000202L, 0xdddd000000000202L),
                new Bits128(0x2222000000000203L, 0xdddd000000000203L),
                new Bits128(0x2222000000000204L, 0xdddd000000000204L),
                new Bits128(0x2222000000000205L, 0xdddd000000000205L));
    }

    private static VolatileBits freeOfferV() {
        return new VolatileBits(0xb100000000001001L, 0xb200000000001002L, 0xb300000000001003L, 0xb400000000001004L, 0xb500000000001005L, 0xb600000000001006L, 0xb700000000001007L,
                new Bits128(0x3333000000000300L, 0xcccc000000000300L),
                new Bits128(0x3333000000000301L, 0xcccc000000000301L),
                new Bits128(0x3333000000000302L, 0xcccc000000000302L),
                new Bits128(0x3333000000000303L, 0xcccc000000000303L),
                new Bits128(0x3333000000000304L, 0xcccc000000000304L),
                new Bits128(0x3333000000000305L, 0xcccc000000000305L));
    }

    private static VolatileBits secondV() {
        return new VolatileBits(0x0000000000000004L, 0x0000000070007fa8L, 0x0000000000000000L, 0x0000000000040000L, 0x0000000000040010L, 0xb600000000001006L, 0xb700000000001007L,
                new Bits128(0x3333000000000300L, 0xcccc000000000300L),
                new Bits128(0x3333000000000301L, 0xcccc000000000301L),
                new Bits128(0x3333000000000302L, 0xcccc000000000302L),
                new Bits128(0x3333000000000303L, 0xcccc000000000303L),
                new Bits128(0x3333000000000304L, 0xcccc000000000304L),
                new Bits128(0x3333000000000305L, 0xcccc000000000305L));
    }

    private static VolatileBits copyFrameV() {
        return new VolatileBits(0x0000000000000000L, 0x0000000000000000L, 0x0000000000040000L, 0x0000000000000010L, 0x0000000000040010L, 0xb600000000001006L, 0xb700000000001007L,
                new Bits128(0x3333000000000300L, 0xcccc000000000300L),
                new Bits128(0x3333000000000301L, 0xcccc000000000301L),
                new Bits128(0x3333000000000302L, 0xcccc000000000302L),
                new Bits128(0x3333000000000303L, 0xcccc000000000303L),
                new Bits128(0x3333000000000304L, 0xcccc000000000304L),
                new Bits128(0x3333000000000305L, 0xcccc000000000305L));
    }

    private static VolatileBits copyNormalV() {
        return new VolatileBits(0x0000000000000000L, 0x0000000000000000L, 0x0000000000040000L, 0x0000000000000010L, 0x0000000000040010L, 0x0000000140000000L, 0xb700000000001007L,
                new Bits128(0x3333000000000300L, 0xcccc000000000300L),
                new Bits128(0x1112131401020304L, 0x3132333421222324L),
                new Bits128(0x1112131401020304L, 0x3132333421222324L),
                new Bits128(0x3333000000000303L, 0xcccc000000000303L),
                new Bits128(0x3333000000000304L, 0xcccc000000000304L),
                new Bits128(0x3333000000000305L, 0xcccc000000000305L));
    }

    private static VolatileBits rangeFrameV() {
        return new VolatileBits(0x0000000000000005L, 0x0000000000000000L, 0x0000000000000004L, 0x0000000000000014L, 0x0000000000000000L, 0x0000000140000000L, 0xb700000000001007L,
                new Bits128(0x3333000000000300L, 0xcccc000000000300L),
                new Bits128(0x1112131401020304L, 0x3132333421222324L),
                new Bits128(0x1112131401020304L, 0x3132333421222324L),
                new Bits128(0x3333000000000303L, 0xcccc000000000303L),
                new Bits128(0x3333000000000304L, 0xcccc000000000304L),
                new Bits128(0x3333000000000305L, 0xcccc000000000305L));
    }

    private static VolatileBits rangeNormalV() {
        return new VolatileBits(0x0000000000000010L, 0x00000000a1b2c3d4L, 0x0000000000000008L, 0x0000000000000008L, 0x0000000000000000L, 0x0000000140000000L, 0xb700000000001007L,
                new Bits128(0x3333000000000300L, 0xcccc000000000300L),
                new Bits128(0x1112131401020304L, 0x3132333421222324L),
                new Bits128(0x1112131401020304L, 0x3132333421222324L),
                new Bits128(0x3333000000000303L, 0xcccc000000000303L),
                new Bits128(0x3333000000000304L, 0xcccc000000000304L),
                new Bits128(0x3333000000000305L, 0xcccc000000000305L));
    }

    private static NonvolatileBits rootN() {
        return new NonvolatileBits(0x9100000000000101L, 0x9200000000000202L, 0x9300000000000303L, 0x9400000000000404L, 0x0000000100000004L, 0x9600000000000606L, 0x9700000000000707L, 0x9800000000000808L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static NonvolatileBits parentN() {
        return new NonvolatileBits(0x0000000000020000L, 0x9200000000000202L, 0x0000000000000000L, 0x0000000070007f80L, 0x0000000100000004L, 0x9600000000000606L, 0x9700000000000707L, 0x9800000000000808L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static NonvolatileBits allocatorN() {
        return new NonvolatileBits(0x0000000000030000L, 0x0000000000000001L, 0x0000000000030010L, 0x0000000070007f90L, 0x0000000100000004L, 0x0000000000000001L, 0x0000000000000000L, 0x0000000000000001L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static NonvolatileBits freeN() {
        return new NonvolatileBits(0x0000000000030010L, 0x0000000000000001L, 0x0000000000030010L, 0x0000000070007f90L, 0x0000000000050000L, 0x0000000000000001L, 0x0000000000000000L, 0x0000000000000001L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static NonvolatileBits addN() {
        return new NonvolatileBits(0x0000000000000000L, 0x9200000000000202L, 0x0000000000000000L, 0x0000000070007f80L, 0x0000000000000004L, 0x0000000000040000L, 0x0000000070007fa8L, 0x0000000000000010L,
                new Bits128(0x6666000000000606L, 0x9999000000000606L));
    }

    private static Map<Long, Byte> initialBytes() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x0000000070007f48L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a22222240010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x0000000000020000L, "eeeeeeeeeeeeeeeeddccbbaaeeeeeeee0000030000000000eeeeeeee01000000eeeeeeeeeeeeeeee0000040000000000eeeeeeee04000000eeeeeeeeeeeeeeee887766555feeeeeeeeeeeeeeeeeeeeee");
        region(map, 0x0000000000030000L, "112233445566778899aabbccddeeff00");
        region(map, 0x0000000000040000L, "04030201141312112423222134333231");
        region(map, 0x0000000000050000L, "cccccccccccccccccccccccccccccccc");
        region(map, 0x00000001454de260L, "0000060000000000");
        region(map, 0x0000000000060000L, "dddddddddddddddd00010070000000000002007000000000");
        region(map, 0x00000001449f64f0L, "0000c03f");
        region(map, 0x0000000000000000L, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaad4c3b2a1aaaaaaaaaaaaaaaaaaaaaaaa");
        check(map.size() == 452, "complete literal map");
        return map;
    }

    private static Map<Long, Byte> afterGuardBytes() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x0000000070007f48L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ab3099d40010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a807f0070000000001ed2ad40010000000000000000000000000000000000000060e24d45010000000000000000000000040000000500000008080000000000980707000000000097060600000000009600000200000000007c987243010000000400000000000092040000000100000006060000000000965a5a5a5a5a5a5a5a04040000000000942222224001000000010100000000009103030000000000935a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x0000000000020000L, "eeeeeeeeeeeeeeeeddccbbaaeeeeeeee0000030000000000eeeeeeee01000000eeeeeeeeeeeeeeee0000040000000000eeeeeeee04000000eeeeeeeeeeeeeeee887766555feeeeeeeeeeeeeeeeeeeeee");
        region(map, 0x0000000000030000L, "112233445566778899aabbccddeeff00");
        region(map, 0x0000000000040000L, "04030201141312112423222134333231");
        region(map, 0x0000000000050000L, "112233445566778899aabbccddeeff00");
        region(map, 0x00000001454de260L, "0000060000000000");
        region(map, 0x0000000000060000L, "dddddddddddddddd00010070000000000002007000000000");
        region(map, 0x00000001449f64f0L, "0000c03f");
        region(map, 0x0000000000000000L, "141312112423222134333231d4c3b2a104030201aaaaaaaaaaaaaaaaaaaaaaaa");
        check(map.size() == 452, "complete literal map");
        return map;
    }

    private static Map<Long, Byte> afterBudgetBytes() {
        Map<Long, Byte> map = new HashMap<>();
        region(map, 0x0000000070007f48L, "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5ab3099d40010000005a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a807f0070000000001ed2ad40010000000000000000000000000000000000000060e24d45010000000000000000000000040000000500000008080000000000980707000000000097060600000000009600000200000000007c987243010000000400000000000092040000000100000006060000000000965a5a5a5a5a5a5a5a04040000000000942222224001000000010100000000009103030000000000935a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a");
        region(map, 0x0000000000020000L, "eeeeeeeeeeeeeeeeddccbbaaeeeeeeee0000030000000000eeeeeeee01000000eeeeeeeeeeeeeeee0000040000000000eeeeeeee04000000eeeeeeeeeeeeeeee887766555feeeeeeeeeeeeeeeeeeeeee");
        region(map, 0x0000000000030000L, "112233445566778899aabbccddeeff00");
        region(map, 0x0000000000040000L, "04030201141312112423222134333231");
        region(map, 0x0000000000050000L, "112233445566778899aabbccddeeff00");
        region(map, 0x00000001454de260L, "0000060000000000");
        region(map, 0x0000000000060000L, "dddddddddddddddd00010070000000000002007000000000");
        region(map, 0x00000001449f64f0L, "0000c03f");
        region(map, 0x0000000000000000L, "04030201d4c3b2a1343332312423222114131211aaaaaaaaaaaaaaaaaaaaaaaa");
        check(map.size() == 452, "complete literal map");
        return map;
    }

    private static void seed(Ram ram) {
        fill(ram, 0x0000000070007f48L, 256, 90);
        fill(ram, 0x0000000000020000L, 80, 238);
        fill(ram, 0x0000000000030000L, 16, 0);
        fill(ram, 0x0000000000040000L, 16, 0);
        fill(ram, 0x0000000000050000L, 16, 204);
        fill(ram, 0x00000001454de260L, 8, 0);
        fill(ram, 0x0000000000060000L, 24, 221);
        fill(ram, 0x00000001449f64f0L, 4, 0);
        fill(ram, 0x0000000000000000L, 32, 170);
        ram.seed(0x0000000070008008L, 8, 0x0000000140222222L);
        ram.seed(0x0000000000020008L, 4, 0x00000000aabbccddL);
        ram.seed(0x0000000000020010L, 8, 0x0000000000030000L);
        ram.seed(0x000000000002001cL, 4, 0x0000000000000001L);
        ram.seed(0x0000000000020028L, 8, 0x0000000000040000L);
        ram.seed(0x0000000000020034L, 4, 0x0000000000000004L);
        ram.seed(0x0000000000020040L, 4, 0x0000000055667788L);
        ram.seed(0x0000000000020044L, 1, 0x000000000000005fL);
        ram.seed(0x0000000000030000L, 8, 0x8877665544332211L);
        ram.seed(0x0000000000030008L, 8, 0x00ffeeddccbbaa99L);
        ram.seed(0x0000000000040000L, 8, 0x1112131401020304L);
        ram.seed(0x0000000000040008L, 8, 0x3132333421222324L);
        ram.seed(0x00000001454de260L, 8, 0x0000000000060000L);
        ram.seed(0x0000000000060008L, 8, 0x0000000070000100L);
        ram.seed(0x0000000000060010L, 8, 0x0000000070000200L);
        ram.seed(0x00000001449f64f0L, 4, 0x000000003fc00000L);
        ram.seed(0x0000000000000010L, 4, 0x00000000a1b2c3d4L);
    }

    private static List<Event> allEvents() {
        return List.of(
                e("W64", 0x0000000070008010L, 0x9100000000000101L),
                e("W64", 0x0000000070008018L, 0x9300000000000303L),
                e("W64", 0x0000000070008000L, 0x9400000000000404L),
                e("W64", 0x0000000070007f80L, 0x00000001445648a0L),
                e("R32", 0x0000000000020008L, (long)(int)0x00000000aabbccddL),
                e("W32", 0x0000000070007f88L, (long)(int)0x00000000aabbccddL),
                e("W64", 0x0000000070007f98L, 0x0000000000000000L),
                e("W64", 0x0000000070007fa0L, 0x0000000000000000L),
                e("W64", 0x0000000070007f90L, 0x0000000000000000L),
                e("W64", 0x0000000070007f98L, 0x0000000000000000L),
                e("W64", 0x0000000070007fa0L, 0x00000001454de260L),
                e("R32", 0x000000000002001cL, (long)(int)0x0000000000000001L),
                e("R64", 0x0000000000020010L, 0x0000000000030000L),
                e("W64", 0x0000000070007fd8L, 0x000000014372984bL),
                e("W64", 0x0000000070007fd0L, 0x0000000000020000L),
                e("W64", 0x0000000070007fc8L, 0x0000000000000000L),
                e("W64", 0x0000000070007fc0L, 0x0000000070007f80L),
                e("W64", 0x0000000070007fb8L, 0x9700000000000707L),
                e("R32", 0x0000000070007f9cL, (long)(int)0x0000000000000000L),
                e("W64", 0x0000000070007fe0L, 0x9200000000000202L),
                e("R32", 0x0000000070007f98L, (long)(int)0x0000000000000000L),
                e("W64", 0x0000000070007fb0L, 0x9800000000000808L),
                e("R64", 0x0000000070007fa0L, 0x00000001454de260L),
                e("W64", 0x0000000070007fe8L, 0x0000000100000004L),
                e("W64", 0x0000000070007ff0L, 0x9600000000000606L),
                e("R32", 0x00000001449f64f0L, (long)(int)0x000000003fc00000L),
                e("R64", 0x00000001454de260L, 0x0000000000060000L),
                e("R64", 0x0000000000060008L, 0x0000000070000100L),
                e("W64", 0x0000000070007f88L, 0x00000001408c7134L),
                e("PORT_INVOKE", 0x00000000008c7131L, 0x0000000070000100L),
                e("R64", 0x0000000070007f90L, 0x0000000000000000L),
                e("BUDGET", 0x00000000008c7170L, 0x0000000000030000L),
                new Event("R128", 0x0000000000030000L, 0x8877665544332211L, 0x00ffeeddccbbaa99L, 0, 0),
                new Event("W128", 0x0000000000050000L, 0x8877665544332211L, 0x00ffeeddccbbaa99L, 0, 0),
                e("R64", 0x0000000070007f90L, 0x0000000000000000L),
                e("R32", 0x0000000070007f9cL, (long)(int)0x0000000000000000L),
                e("R64", 0x0000000070007fa0L, 0x00000001454de260L),
                e("R64", 0x00000001454de260L, 0x0000000000060000L),
                e("R64", 0x0000000000060010L, 0x0000000070000200L),
                e("W64", 0x0000000070007f88L, 0x00000001408c71daL),
                e("PORT_INVOKE", 0x00000000008c71d7L, 0x0000000070000200L),
                e("W64", 0x0000000070007f90L, 0x0000000000050000L),
                e("R64", 0x0000000070007fe8L, 0x0000000100000004L),
                e("W32", 0x0000000070007f98L, (long)(int)0x0000000000000001L),
                e("R64", 0x0000000070007ff0L, 0x9600000000000606L),
                e("W32", 0x0000000070007f9cL, (long)(int)0x0000000000000001L),
                e("R64", 0x0000000070007fe0L, 0x9200000000000202L),
                e("R64", 0x0000000070007fb0L, 0x9800000000000808L),
                e("R64", 0x0000000070007fb8L, 0x9700000000000707L),
                e("R64", 0x0000000070007fc0L, 0x0000000070007f80L),
                e("R64", 0x0000000070007fc8L, 0x0000000000000000L),
                e("R64", 0x0000000070007fd0L, 0x0000000000020000L),
                e("R64", 0x0000000070007fd8L, 0x000000014372984bL),
                e("W64", 0x0000000070007fb0L, 0x0000000000000000L),
                e("W64", 0x0000000070007fb8L, 0x0000000000000000L),
                e("W64", 0x0000000070007fa8L, 0x0000000000000000L),
                e("W64", 0x0000000070007fb0L, 0x0000000000000000L),
                e("W64", 0x0000000070007fb8L, 0x00000001454de268L),
                e("R64", 0x0000000000020028L, 0x0000000000040000L),
                e("R32", 0x0000000000020034L, (long)(int)0x0000000000000004L),
                e("W64", 0x0000000070007fd8L, 0x000000014372987cL),
                e("W64", 0x0000000070007fd0L, 0x0000000000020000L),
                e("W64", 0x0000000070007fc8L, 0x9600000000000606L),
                e("W64", 0x0000000070007fc0L, 0x9700000000000707L),
                e("W64", 0x0000000070007fb8L, 0x9800000000000808L),
                e("R32", 0x0000000070007fb4L, (long)(int)0x0000000000000000L),
                e("W64", 0x0000000070007fb0L, 0x0000000100000004L),
                e("R32", 0x0000000070007fb0L, (long)(int)0x0000000000000004L),
                e("W32", 0x0000000070007fe0L, (long)(int)0x0000000000000004L),
                e("R64", 0x0000000070007fa8L, 0x0000000000000000L),
                e("W64", 0x0000000070007f88L, 0x0000000140add1fcL),
                new Event("R128", 0x0000000000040000L, 0x1112131401020304L, 0x3132333421222324L, 0, 0),
                new Event("R128", 0x0000000000040000L, 0x1112131401020304L, 0x3132333421222324L, 0, 0),
                new Event("W128", 0x0000000000000000L, 0x1112131401020304L, 0x3132333421222324L, 0, 0),
                new Event("W128", 0x0000000000000000L, 0x1112131401020304L, 0x3132333421222324L, 0, 0),
                e("R64", 0x0000000070007f88L, 0x0000000140add1fcL),
                e("R32", 0x0000000070007fb4L, (long)(int)0x0000000000000001L),
                e("R64", 0x0000000070007fa8L, 0x0000000000000000L),
                e("W32", 0x0000000070007fb4L, (long)(int)0x0000000000000005L),
                e("W64", 0x0000000070007f88L, 0x0000000140add21eL),
                e("W64", 0x0000000070007f90L, 0x0000000000000000L),
                e("W64", 0x0000000070007f98L, 0x0000000000000000L),
                e("W64", 0x0000000070007f80L, 0x0000000070007f80L),
                e("W64", 0x0000000070007f58L, 0x00000001409d099dL),
                e("BUDGET", 0x0000000004220b49L, 0x0000000000000000L),
                e("R64", 0x0000000070007f58L, 0x00000001409d099dL),
                e("W64", 0x0000000070007f58L, 0x00000001409d09a8L),
                e("BUDGET", 0x0000000004220b49L, 0x0000000000000004L),
                e("R32", 0x0000000000000004L, (long)(int)0x0000000011121314L),
                e("R32", 0x0000000000000010L, (long)(int)0x00000000a1b2c3d4L),
                e("W32", 0x0000000000000004L, (long)(int)0x00000000a1b2c3d4L),
                e("W32", 0x0000000000000010L, (long)(int)0x0000000011121314L),
                e("BUDGET", 0x0000000004220b49L, 0x0000000000000008L),
                e("R32", 0x0000000000000008L, (long)(int)0x0000000021222324L),
                e("R32", 0x000000000000000cL, (long)(int)0x0000000031323334L),
                e("W32", 0x0000000000000008L, (long)(int)0x0000000031323334L),
                e("W32", 0x000000000000000cL, (long)(int)0x0000000021222324L),
                e("R64", 0x0000000070007f58L, 0x00000001409d09a8L),
                e("W64", 0x0000000070007f58L, 0x00000001409d09b3L),
                e("BUDGET", 0x0000000004220b49L, 0x0000000000000000L),
                e("R32", 0x0000000000000000L, (long)(int)0x0000000001020304L),
                e("R32", 0x0000000000000010L, (long)(int)0x0000000011121314L),
                e("W32", 0x0000000000000000L, (long)(int)0x0000000011121314L),
                e("W32", 0x0000000000000010L, (long)(int)0x0000000001020304L),
                e("BUDGET", 0x0000000004220b49L, 0x0000000000000004L),
                e("R32", 0x0000000000000004L, (long)(int)0x00000000a1b2c3d4L),
                e("R32", 0x000000000000000cL, (long)(int)0x0000000021222324L),
                e("W32", 0x0000000000000004L, (long)(int)0x0000000021222324L),
                e("W32", 0x000000000000000cL, (long)(int)0x00000000a1b2c3d4L),
                e("BUDGET", 0x0000000004220b49L, 0x0000000000000008L),
                e("R64", 0x0000000070007f58L, 0x00000001409d09b3L),
                e("R64", 0x0000000070007f98L, 0x0000000000000000L),
                e("R64", 0x0000000070007f90L, 0x0000000000000000L),
                e("R64", 0x0000000070007f80L, 0x0000000070007f80L),
                e("R64", 0x0000000070007f88L, 0x0000000140add21eL),
                e("R64", 0x0000000070007fb0L, 0x0000000500000004L),
                e("R64", 0x0000000070007fb8L, 0x9800000000000808L),
                e("R64", 0x0000000070007fc0L, 0x9700000000000707L),
                e("R64", 0x0000000070007fc8L, 0x9600000000000606L),
                e("R64", 0x0000000070007fd0L, 0x0000000000020000L),
                e("R64", 0x0000000070007fd8L, 0x000000014372987cL));
    }


    private static GovernmentCrtBoundary185Api.Call call(long site,
            GovernmentCrtBoundary185Api.TargetKind kind, long target, long pre,
            VolatileBits v, NonvolatileBits n) {
        return new GovernmentCrtBoundary185Api.Call(site, kind, target, pre, v, n);
    }
    private static GovernmentCrtBoundary185Api.Entry child(long sp, VolatileBits v, NonvolatileBits n) {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE, sp, v, n);
    }

    private static void exercise(boolean stopAtThirdBudget) {
        // Independent literal expectations and caller-defined offers precede bind/execute.
        Map<Long, Byte> initial = initialBytes();
        Map<Long, Byte> expectedBytes = stopAtThirdBudget ? afterBudgetBytes() : afterGuardBytes();
        List<Event> wholeLiteral = allEvents();
        List<Event> literal = stopAtThirdBudget ? List.copyOf(wholeLiteral.subList(0, 100)) : wholeLiteral;
        QueueFp604Api.Mxcsr inputFp = new QueueFp604Api.Mxcsr(0x1F80, 0xFFC0);
        QueueFp604Api.Mxcsr allocatorFp = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Mxcsr freeFp = new QueueFp604Api.Mxcsr(128, 192);
        QueueFp604Api.Normal allocatorOffer = normal(allocatorOfferV(), allocatorN(),
                0x1408C7134L, 0x70007F90L, false, allocatorFp);
        QueueFp604Api.Normal freeOffer = normal(freeOfferV(), freeN(),
                0x1408C71DAL, 0x70007F90L, true, freeFp);
        QueueFp604Api.Normal expectedFirstNormal = normal(freeOfferV(), parentN(),
                0x14372984BL, 0x70007FE0L, true, freeFp);
        QueueFp604Api.Normal expectedCopyNormal = normal(copyNormalV(), addN(),
                0x140ADD1FCL, 0x70007F90L, true, freeFp);
        QueueFp604Api.Normal expectedRangeNormal = normal(rangeNormalV(), addN(),
                0x140ADD21EL, 0x70007F90L, true, freeFp);
        GovernmentCrtBoundary185Api.TargetKind direct = GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
        GovernmentCrtBoundary185Api.TargetKind indirect = GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE;
        Element172Fp636Api.CallFrame firstFrame = new Element172Fp636Api.CallFrame(
                call(0x3729846L, direct, 0x8C70B0L, 0x70007FE0L, firstV(), parentN()),
                child(0x70007FD8L, firstV(), parentN()), true, inputFp, 5, 0x14372984BL);
        Element172Fp636Api.CallFrame secondFrame = new Element172Fp636Api.CallFrame(
                call(0x3729877L, direct, 0xADD0D0L, 0x70007FE0L, secondV(), parentN()),
                child(0x70007FD8L, secondV(), parentN()), true, freeFp, 5, 0x14372987CL);
        Range16Fp638Api.CallFrame allocatorFrame = new Range16Fp638Api.CallFrame(
                call(0x8C7131L, indirect, 0x70000100L, 0x70007F90L, allocatorFrameV(), allocatorN()),
                child(0x70007F88L, allocatorFrameV(), allocatorN()), true, inputFp, 3, 0x1408C7134L);
        Range16Fp638Api.CallFrame freeFrame = new Range16Fp638Api.CallFrame(
                call(0x8C71D7L, indirect, 0x70000200L, 0x70007F90L, freeFrameV(), freeN()),
                child(0x70007F88L, freeFrameV(), freeN()), false, allocatorFp, 3, 0x1408C71DAL);
        Add4Fp639Api.CallFrame copyFrame = new Add4Fp639Api.CallFrame(
                call(0xADD1F7L, direct, 0x4226860L, 0x70007F90L, copyFrameV(), addN()),
                child(0x70007F88L, copyFrameV(), addN()), true, freeFp, 5, 0x140ADD1FCL);
        Add4Fp639Api.CallFrame rangeFrame = new Add4Fp639Api.CallFrame(
                call(0xADD219L, direct, 0x9D0950L, 0x70007F90L, rangeFrameV(), addN()),
                child(0x70007F88L, rangeFrameV(), addN()), true, freeFp, 5, 0x140ADD21EL);
        UnsupportedOperationException sentinel = stopAtThirdBudget
                ? new UnsupportedOperationException("651-third-scalar-sentinel") : null;
        long[] budgetPcs = {0x8C7170L, 0x4220B49L, 0x4220B49L, 0x4220B49L,
                0x4220B49L, 0x4220B49L, 0x4220B49L};
        long[] budgetGuards = {0x30000L, 0, 4, 8, 0, 4, 8};
        int[] budgetPrefixes = {31, 84, 87, 92, 99, 104, 109};
        int[] parentCount = new int[1];
        int[] opaqueCount = new int[1];
        int[] addCount = new int[1];
        int[] budgetCount = new int[1];
        int[] foreignCount = new int[1];
        int[] tailCount = new int[1];
        int[] copyNormals = new int[1];
        int[] rangeNormals = new int[1];
        QueueFp604Api.Outcome[] firstReturned = new QueueFp604Api.Outcome[1];
        RuntimeException[] parentFailure = new RuntimeException[1];
        RuntimeException[] rangeFailure = new RuntimeException[1];
        Ram ram = new Ram();
        seed(ram);
        fullBytes(initial, ram, "all452 initial bytes");
        check(ram.events.isEmpty(), "seeding produces no events");
        GovernmentCrtBoundary185Api.LoopBudget budget = (pc, guard) -> {
            int turn = ++budgetCount[0];
            check(turn <= (stopAtThirdBudget ? 5 : 7), "bounded single shared budget");
            check(pc == budgetPcs[turn - 1] && guard == budgetGuards[turn - 1],
                    "literal source budget PC and fullraw cursor");
            prefix(literal, budgetPrefixes[turn - 1], ram, "complete pre-budget source prefix");
            ram.step(pc, guard);
            if (stopAtThirdBudget && turn == 5) throw sentinel;
        };
        Range16Fp638Api.Calls rangeCalls = frame -> {
            int turn = ++opaqueCount[0];
            check(turn <= 2 && parentCount[0] == 1 && addCount[0] == 0,
                    "only two actual first638 opaque calls");
            if (turn == 1) {
                equal(allocatorFrame, frame, "all allocator frame/entry/banks/DF/FP/RIP/SP fields");
                same(inputFp, frame.preMxcsr(), "SAME explicit input controls after real605/606/607");
                check(budgetCount[0] == 0, "no copy budget before allocator");
                prefix(literal, 29, ram, "allocator owned push before opaque offer");
                ram.events.add(e("PORT_INVOKE", 0x8C7131L, 0x70000100L));
                return allocatorOffer;
            }
            equal(freeFrame, frame, "all free current frame/entry/V/N/DF/FP/RIP/SP fields");
            same(allocatorFp, frame.preMxcsr(), "SAME accepted allocator partialFP at actualfree");
            check(budgetCount[0] == 1, "one real positive16 insertion budget beforefree");
            prefix(literal, 40, ram, "free push after actual insertion and fresh virtual reads");
            ram.events.add(e("PORT_INVOKE", 0x8C71D7L, 0x70000200L));
            return freeOffer;
        };
        FullCopyWithFp613.TailCalls unknownTails = frame -> {
            tailCount[0]++;
            throw new AssertionError("unexpected COPY tail: " + frame);
        };
        Add4Fp639Api.Calls foreign = frame -> {
            foreignCount[0]++;
            throw new AssertionError("unexpected Add4 foreign frame: " + frame);
        };
        Add4Fp639Api.Calls knownAdd = Add4Range262.withCopy(ram, budget, unknownTails, foreign);
        Add4Fp639Api.Calls observedAdd = frame -> {
            int turn = ++addCount[0];
            check(turn <= 2 && parentCount[0] == 2 && opaqueCount[0] == 2,
                    "two real639 calls after real first638 Normal");
            if (turn == 1) {
                equal(copyFrame, frame, "all actual ADD1F7 COPY call and child state");
                same(freeFp, frame.preMxcsr(), "SAME current partialB entering actualCOPY");
                prefix(literal, 71, ram, "complete COPY owned push prefix");
                QueueFp604Api.Outcome outcome = knownAdd.invoke(frame);
                completeNormal(expectedCopyNormal, outcome, "actual COPY complete return");
                copyNormals[0]++;
                prefix(literal, 76, ram, "both actual R128/W128 and COPY RET");
                return outcome;
            }
            equal(rangeFrame, frame, "all actual ADD219 range call and child state");
            same(freeFp, frame.preMxcsr(), "SAME partialB entering actual9D");
            check(copyNormals[0] == 1, "actualCOPY completed before range");
            prefix(literal, 80, ram, "fresh count/base/update and actual9D push");
            QueueFp604Api.Outcome outcome;
            try {
                outcome = knownAdd.invoke(frame);
            } catch (RuntimeException failure) {
                rangeFailure[0] = failure;
                throw failure;
            }
            check(!stopAtThirdBudget, "sentinel scene cannot finish9D");
            completeNormal(expectedRangeNormal, outcome, "actual9D complete return after three641 bodies");
            rangeNormals[0]++;
            prefix(literal, 115, ram, "three641 RETs then actual9D epilogue");
            return outcome;
        };
        Element172Fp636Api.Calls bound = Element172KnownLower640.bind(ram, budget, rangeCalls, observedAdd);
        check(ram.events.isEmpty(), "bindings add no events");
        fullBytes(initial, ram, "bindings add no RAM effects");
        check(parentCount[0] == 0 && opaqueCount[0] == 0 && addCount[0] == 0
                && budgetCount[0] == 0 && foreignCount[0] == 0 && tailCount[0] == 0,
                "bindings add no callback/budget effects");
        Element172Fp636Api.Calls observedParent = frame -> {
            int turn = ++parentCount[0];
            check(turn <= 2, "exactly two actual172 calls");
            if (turn == 1) {
                equal(firstFrame, frame, "complete actual first172 call/child/V/N/DF/FP/RIP/SP");
                same(inputFp, frame.preMxcsr(), "SAME initialFP at first172 call");
                prefix(literal, 14, ram, "actual172 first CALL push prefix");
                QueueFp604Api.Outcome outcome = bound.invoke(frame);
                completeNormal(expectedFirstNormal, outcome, "real positive16 first638 whole Normal");
                check(opaqueCount[0] == 2 && budgetCount[0] == 1 && addCount[0] == 0,
                        "actual allocator, positive16 copy and free consumed");
                prefix(literal, 53, ram, "complete first638 prologue/copy/commit/restore/RET");
                check(ram.peek(0x70007F90L, 8) == 0x50000L
                        && ram.peek(0x70007F98L, 4) == 1 && ram.peek(0x70007F9CL, 4) == 1,
                        "first16 really committed before later source aliases");
                firstReturned[0] = outcome;
                return outcome;
            }
            equal(secondFrame, frame, "complete actual second172 call/child/V/N/DF/FP/RIP/SP");
            same(freeFp, frame.preMxcsr(), "SAME accepted free partialB at second172 call");
            check(firstReturned[0] != null, "actual first638 Normal already returned");
            prefix(literal, 61, ram, "second header reset and actual172 CALL push");
            try {
                QueueFp604Api.Outcome unexpected = bound.invoke(frame);
                throw new AssertionError("second actual172 call unexpectedly returned: " + unexpected);
            } catch (RuntimeException failure) {
                parentFailure[0] = failure;
                throw failure;
            }
        };
        Element172Fp636Api.Input input = new Element172Fp636Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE, ROOT_SP, rootV(), rootN()), true, inputFp);
        RuntimeException caught = null;
        try {
            QueueFp604Api.Outcome unexpected = Element172FullState636.execute(input, ram, observedParent);
            throw new AssertionError("whole172 unexpectedly returned: " + unexpected);
        } catch (RuntimeException failure) {
            caught = failure;
        }
        check(caught != null, "actual whole172 exception");
        same(parentFailure[0], caught, "SAME actual second-call exception through whole172");
        if (stopAtThirdBudget) {
            same(sentinel, caught, "SAME original precreated third-budget exception");
            same(sentinel, rangeFailure[0], "SAME sentinel through actual641/261/260/262/259");
            check(caught.getClass() == UnsupportedOperationException.class
                    && "651-third-scalar-sentinel".equals(caught.getMessage()), "unchanged sentinel metadata");
            check(budgetCount[0] == 5 && rangeNormals[0] == 0,
                    "two641 Normals then third firstbudget; no9D Normal");
        } else {
            check(caught.getClass() == IllegalArgumentException.class
                    && "Nonvolatile mismatch".equals(caught.getMessage()), "actual late N guard rejection");
            StackTraceElement[] stack = caught.getStackTrace();
            check(stack.length >= 2
                    && stack[0].getClassName().equals("org.xar.ck3.control.g2.m2.nativecode.Element172Fp636Api$CallFrame")
                    && stack[0].getMethodName().equals("checkNormalReturn")
                    && stack[1].getClassName().startsWith("org.xar.ck3.control.g2.m2.nativecode.Element172KnownLower640$")
                    && stack[1].getMethodName().equals("invoke"), "actual640 second-frame guard origin");
            check(rangeFailure[0] == null && rangeNormals[0] == 1 && budgetCount[0] == 7,
                    "all three641 bodies and9D completed before actual640 rejects639 Normal");
        }
        check(parentCount[0] == 2 && opaqueCount[0] == 2 && addCount[0] == 2
                && copyNormals[0] == 1 && foreignCount[0] == 0 && tailCount[0] == 0,
                "bounded actual parent/opaque/COPY/range counts");
        check(firstReturned[0] != null, "same-instance positive16 completed in both cases");
        equal(literal, ram.events, "entire literal trace, exact order and no later effects");
        fullBytes(expectedBytes, ram, "all452 final bytes and exact owned key set");
        check(ram.peek(0x70007FB0L, 8) == 0x0000000500000004L,
                "source count update changed full savedR12 high32");
        check(ram.peek(0x70007F90L, 8) == 0 && ram.peek(0x70007F98L, 8) == 0
                && ram.peek(0x70007F80L, 8) == 0x70007F80L,
                "real9D homes and push overwrite earlierH16 and destinationvtable");
    }

    public static void wholePositive16And4RejectsRestoredR12() {
        exercise(false);
    }
    public static void wholePositive16And4ThrowsSameThirdBudgetSentinel() {
        exercise(true);
    }
    public static int verify() {
        wholePositive16And4RejectsRestoredR12();
        wholePositive16And4ThrowsSameThirdBudgetSentinel();
        return 2;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
