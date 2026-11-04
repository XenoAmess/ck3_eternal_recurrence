package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * One fresh owned-memory budget-throw witness. Numerical literals come from the
 * separately frozen budget oracle; that oracle was written after model R1 and
 * is explicitly NOT generation-blind. Owner Test source, no model Java adopted.
 * No machine state is inferred or inspected after the ordinary Java throw.
 */
public final class Embedded32BudgetBoundary659 {
    private Embedded32BudgetBoundary659() { }

    public static void baNormalThenFirstBudgetThrowsSame() {
        final QueueFp604Api.Mxcsr rootFp = new QueueFp604Api.Mxcsr(0x2001, 0xa041);
        final QueueFp604Api.Mxcsr offeredFp = new QueueFp604Api.Mxcsr(0x0025, 0x003f);
        final Embedded32Fp659.CallFrame expectedFrame = expectedBaFrame(rootFp);
        final QueueFp604Api.Normal offered = explicitBaNormal(offeredFp);
        final FullCopy437Api.CallResult offeredBase = offered.base();
        final RuntimeException budgetThrow =
            new RuntimeException("budget659/first3727273 ordinary");
        final Map<Long, Byte> initialBytes = initialRam();
        final List<Map<Long, Byte>> expectedPrefixes = expectedRamPrefixes();
        final Map<Long, Byte> expectedTerminal = terminalRam();
        final Ram memory = new Ram(initialBytes);
        final List<Embedded32Fp659.CallFrame> frames = new ArrayList<>();
        final List<QueueFp604Api.Outcome> offers = new ArrayList<>();
        final int[] budgetCalls = {0};

        // This port exposes two arguments only. There is no budget Snapshot.
        final LoopBudget budget = (header, guard) -> {
            memory.mixed.add("B.enter(BB-same-root-budget," + hex64(header)
                + "," + hex64(guard) + ")");
            budgetCalls[0]++;
            equal(1, budgetCalls[0], "one budget invocation");
            equal(0x3727273L, header, "actual loop header");
            equal(0x40020L, guard, "actual first cursor");
            equal(1, frames.size(), "BA completed before budget");
            equal(1, offers.size(), "one Normal offer before budget");
            equal(14, memory.primitive.size(), "budget is after fourteen primitives");
            equal(expectedTerminal, memory.snapshot(), "RAM at budget entry");
            memory.mixed.add("B.throw(TB-ordinary-budget-runtimeexception)");
            throw budgetThrow;
        };
        final QueueFp604Api.Input input = new QueueFp604Api.Input(
            new FullCopy437Api.Input(rootEntry(), false, budget), rootFp);
        same(budget, input.base().budget(), "same root budget object");
        same(rootFp, input.mxcsr(), "same root partial FP object");
        check(!rootFp.isExact() && !offeredFp.isExact(), "both FP inputs are partial");
        check(rootFp != offeredFp, "two distinct explicit FP objects");
        equal(initialBytes, memory.snapshot(), "all initial owned bytes");
        equal(480, initialBytes.size(), "owned byte count");

        final Embedded32Fp659.Calls calls = actual -> {
            memory.mixed.add("C.enter(FB-BA-only-public-frame,"
                + hex64(actual.original().call().callSiteRva()) + ")");
            frames.add(actual);
            equal(1, frames.size(), "only the first BA port is reachable");
            equal(expectedFrame.original().call(), actual.original().call(),
                "complete Call: all seven V GPR, six XMM and all N");
            equal(expectedFrame.original().childEntry(), actual.original().childEntry(),
                "complete child Entry/image/SP/V/N");
            equal(expectedFrame.original(), actual.original(), "length/RET/DF and full original frame");
            equal(expectedFrame, actual, "complete typed BA frame");
            same(rootFp, actual.preMxcsr(), "BA gets the same current root FP object");
            equal(9, memory.primitive.size(), "owned BA return push precedes callback");
            equal(expectedPrefixes.get(8), memory.snapshot(), "full RAM at BA entry");
            same(offeredBase, offered.base(), "prebuilt complete base object");
            same(offeredFp, offered.postMxcsr(), "prebuilt offered partial FP object");
            check(offered.base().postDirectionFlagSet(), "explicit offered DF change");
            offers.add(offered);
            memory.mixed.add("C.return(BA,OB-BA-normal)");
            return offered;
        };

        RuntimeException caught = null;
        try {
            Embedded32Fp659.execute(input, memory, calls);
            throw new AssertionError("whole execute returned an Outcome after budget throw");
        } catch (RuntimeException actual) {
            caught = actual;
        }
        same(budgetThrow, caught, "ordinary exception is propagated unchanged");
        equal(RuntimeException.class, caught.getClass(), "plain RuntimeException class");
        equal("budget659/first3727273 ordinary", caught.getMessage(), "exception message");
        equal(1, budgetCalls[0], "one budget invocation, no next iteration");
        equal(List.of(expectedFrame), frames, "only one complete public frame");
        equal(1, offers.size(), "one opaque Normal return");
        same(offered, offers.get(0), "same complete offered outcome");
        equal(expectedPrimitiveTrace(), memory.primitive, "all fourteen primitive accesses");
        equal(expectedMixedTrace(), memory.mixed, "all eighteen mixed events, no suffix");
        equal(expectedPrefixes, memory.prefixes, "full 480-byte RAM after every primitive");
        equal(expectedTerminal.keySet(), memory.snapshot().keySet(), "terminal exact owned keyset");
        equal(expectedTerminal, memory.snapshot(), "terminal complete RAM without rollback");
        // No postthrow Normal/Stopped, Entry, V/N, DF or MXCSR getter exists here.
    }

    public static int verify() {
        baNormalThenFirstBudgetThrowsSame();
        return 1;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static Entry rootEntry() {
        return new Entry(0x0000000073000000L, 0x0000000000024000L,
        new VolatileBits(
            0x1101020304050607L,
            0x0000000000039000L,
            0x000000000003b000L,
            0x8401020304050607L,
            0x8508090a0b0c0d0eL,
            0x860f101112131415L,
            0x87161718191a1b1cL,
            new Bits128(0x2100010203040506L, 0x220708090a0b0c0dL),
            new Bits128(0x2310111213141516L, 0x241718191a1b1c1dL),
            new Bits128(0x2520212223242526L, 0x262728292a2b2c2dL),
            new Bits128(0x2730313233343536L, 0x283738393a3b3c3dL),
            new Bits128(0x2940414243444546L, 0x2a4748494a4b4c4dL),
            new Bits128(0x2b50515253545556L, 0x2c5758595a5b5c5dL)),
        new NonvolatileBits(
            0xb101020304050607L,
            0xb208090a0b0c0d0eL,
            0xb30f101112131415L,
            0xb4161718191a1b1cL,
            0xb51d1e1f20212223L,
            0xb62425262728292aL,
            0xb72b2c2d2e2f3031L,
            0xb832333435363738L,
            new Bits128(0xb9393a3b3c3d3e3fL, 0xba40414243444546L)));
    }

    private static Embedded32Fp659.CallFrame expectedBaFrame(QueueFp604Api.Mxcsr rootFp) {
        final Call call = new Call(0x00000000037271baL, TargetKind.DIRECT_RVA,
            0x0000000000889660L, 0x0000000000023fb8L,
            new VolatileBits(
            0x000000000003b010L,
            0x0000000000039010L,
            0x000000000003b000L,
            0x8401020304050607L,
            0x8508090a0b0c0d0eL,
            0x860f101112131415L,
            0x87161718191a1b1cL,
            new Bits128(0x2100010203040506L, 0x220708090a0b0c0dL),
            new Bits128(0x2310111213141516L, 0x241718191a1b1c1dL),
            new Bits128(0x2520212223242526L, 0x262728292a2b2c2dL),
            new Bits128(0x2730313233343536L, 0x283738393a3b3c3dL),
            new Bits128(0x2940414243444546L, 0x2a4748494a4b4c4dL),
            new Bits128(0x2b50515253545556L, 0x2c5758595a5b5c5dL)),
            new NonvolatileBits(
            0xb101020304050607L,
            0xb208090a0b0c0d0eL,
            0x0000000000039010L,
            0x0000000000000001L,
            0xb51d1e1f20212223L,
            0x0000000000048000L,
            0x0000000000039000L,
            0x000000000003b000L,
            new Bits128(0xb9393a3b3c3d3e3fL, 0xba40414243444546L)));
        final Entry child = new Entry(0x0000000073000000L, 0x0000000000023fb0L,
        new VolatileBits(
            0x000000000003b010L,
            0x0000000000039010L,
            0x000000000003b000L,
            0x8401020304050607L,
            0x8508090a0b0c0d0eL,
            0x860f101112131415L,
            0x87161718191a1b1cL,
            new Bits128(0x2100010203040506L, 0x220708090a0b0c0dL),
            new Bits128(0x2310111213141516L, 0x241718191a1b1c1dL),
            new Bits128(0x2520212223242526L, 0x262728292a2b2c2dL),
            new Bits128(0x2730313233343536L, 0x283738393a3b3c3dL),
            new Bits128(0x2940414243444546L, 0x2a4748494a4b4c4dL),
            new Bits128(0x2b50515253545556L, 0x2c5758595a5b5c5dL)),
        new NonvolatileBits(
            0xb101020304050607L,
            0xb208090a0b0c0d0eL,
            0x0000000000039010L,
            0x0000000000000001L,
            0xb51d1e1f20212223L,
            0x0000000000048000L,
            0x0000000000039000L,
            0x000000000003b000L,
            new Bits128(0xb9393a3b3c3d3e3fL, 0xba40414243444546L)));
        return new Embedded32Fp659.CallFrame(
            new Embedded32Copy581Api.CallFrame(call, child, false, 5, 0x00000000767271bfL), rootFp);
    }

    private static QueueFp604Api.Normal explicitBaNormal(QueueFp604Api.Mxcsr offeredFp) {
        final NormalReturn normalReturn = new NormalReturn(
            new VolatileBits(
            0xd101020304050607L,
            0xd208090a0b0c0d0eL,
            0xd30f101112131415L,
            0xd4161718191a1b1cL,
            0xd51d1e1f20212223L,
            0xd62425262728292aL,
            0xd72b2c2d2e2f3031L,
            new Bits128(0xe000010203040506L, 0xe10708090a0b0c0dL),
            new Bits128(0xe210111213141516L, 0xe31718191a1b1c1dL),
            new Bits128(0xe420212223242526L, 0xe52728292a2b2c2dL),
            new Bits128(0xe630313233343536L, 0xe73738393a3b3c3dL),
            new Bits128(0xe840414243444546L, 0xe94748494a4b4c4dL),
            new Bits128(0xea50515253545556L, 0xeb5758595a5b5c5dL)),
            0x00000000767271bfL, 0x0000000000023fb8L,
            new NonvolatileBits(
            0xb101020304050607L,
            0xb208090a0b0c0d0eL,
            0x0000000000039010L,
            0x0000000000000001L,
            0xb51d1e1f20212223L,
            0x0000000000048000L,
            0x0000000000039000L,
            0x000000000003b000L,
            new Bits128(0xb9393a3b3c3d3e3fL, 0xba40414243444546L)));
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(normalReturn, true), offeredFp);
    }

    private static Map<Long, Byte> initialRam() {
        return literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "404142434445464748494a4b4c4d4e4f"
                + "505152535455565758595a5b5c5d5e5f"
                + "606162636465666768696a6b6c6d6e6f"
                + "080706050403020178797a7b7c7d7e7f"
                + "808182838485868788898a8b8c8d8e8f"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            });
    }

    private static List<String> expectedPrimitiveTrace() {
        return List.of(
            "M.writeQword(0000000000023ff8,b30f101112131415)",
            "M.writeQword(0000000000023ff0,b72b2c2d2e2f3031)",
            "M.writeQword(0000000000023fe8,b832333435363738)",
            "M.writeQword(0000000000024018,b4161718191a1b1c)",
            "M.readDword(000000000003b01c)->00000001",
            "M.writeQword(0000000000023fe0,b51d1e1f20212223)",
            "M.writeQword(0000000000023fd8,b62425262728292a)",
            "M.readQword(000000000003b010)->0000000000048000",
            "M.writeQword(0000000000023fb0,00000000767271bf)",
            "M.readDword(000000000003901c)->00000003",
            "M.writeQword(0000000000024008,b101020304050607)",
            "M.writeQword(0000000000024010,b208090a0b0c0d0e)",
            "M.readQword(0000000000039010)->0000000000040000",
            "M.readQword(0000000000039010)->0000000000040000");
    }

    private static List<String> expectedMixedTrace() {
        return List.of(
            "M.writeQword(0000000000023ff8,b30f101112131415)",
            "M.writeQword(0000000000023ff0,b72b2c2d2e2f3031)",
            "M.writeQword(0000000000023fe8,b832333435363738)",
            "M.writeQword(0000000000024018,b4161718191a1b1c)",
            "M.readDword(000000000003b01c)->00000001",
            "M.writeQword(0000000000023fe0,b51d1e1f20212223)",
            "M.writeQword(0000000000023fd8,b62425262728292a)",
            "M.readQword(000000000003b010)->0000000000048000",
            "M.writeQword(0000000000023fb0,00000000767271bf)",
            "C.enter(FB-BA-only-public-frame,00000000037271ba)",
            "C.return(BA,OB-BA-normal)",
            "M.readDword(000000000003901c)->00000003",
            "M.writeQword(0000000000024008,b101020304050607)",
            "M.writeQword(0000000000024010,b208090a0b0c0d0e)",
            "M.readQword(0000000000039010)->0000000000040000",
            "M.readQword(0000000000039010)->0000000000040000",
            "B.enter(BB-same-root-budget,0000000003727273,0000000000040020)",
            "B.throw(TB-ordinary-budget-runtimeexception)");
    }

    private static List<Map<Long, Byte>> expectedRamPrefixes() {
        return List.of(
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "404142434445464748494a4b4c4d4e4f"
                + "505152535455565758595a5b5c5d5e5f"
                + "60616263646566671514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "808182838485868788898a8b8c8d8e8f"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "404142434445464748494a4b4c4d4e4f"
                + "505152535455565758595a5b5c5d5e5f"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "808182838485868788898a8b8c8d8e8f"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "404142434445464748494a4b4c4d4e4f"
                + "505152535455565738373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "808182838485868788898a8b8c8d8e8f"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "404142434445464748494a4b4c4d4e4f"
                + "505152535455565738373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "80818283848586871c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "404142434445464748494a4b4c4d4e4f"
                + "505152535455565738373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "80818283848586871c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "404142434445464748494a4b4c4d4e4f"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "80818283848586871c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "80818283848586871c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "202122232425262728292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "80818283848586871c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "bf7172760000000028292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "80818283848586871c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "bf7172760000000028292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020178797a7b7c7d7e7f"
                + "80818283848586871c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "bf7172760000000028292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020107060504030201b1"
                + "80818283848586871c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "bf7172760000000028292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020107060504030201b1"
                + "0e0d0c0b0a0908b21c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "bf7172760000000028292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020107060504030201b1"
                + "0e0d0c0b0a0908b21c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }),
            literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "bf7172760000000028292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020107060504030201b1"
                + "0e0d0c0b0a0908b21c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            }));
    }

    private static Map<Long, Byte> terminalRam() {
        return literalMap(new long[] {0x0000000000023f90L, 0x0000000000039000L, 0x000000000003b000L, 0x0000000000040000L, 0x0000000000048000L},
            new String[] {
                "000102030405060708090a0b0c0d0e0f"
                + "101112131415161718191a1b1c1d1e1f"
                + "bf7172760000000028292a2b2c2d2e2f"
                + "303132333435363738393a3b3c3d3e3f"
                + "40414243444546472a292827262524b6"
                + "232221201f1e1db538373635343332b8"
                + "31302f2e2d2c2bb71514131211100fb3"
                + "080706050403020107060504030201b1"
                + "0e0d0c0b0a0908b21c1b1a19181716b4"
                + "909192939495969798999a9b9c9d9e9f",
                "d0d1d2d3d4d5d6d7d8d9dadbdcdddedf"
                + "00000400000000000300000003000000"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef"
                + "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
                + "00112233445566778899aabbccddeeff"
                + "ffeeddccbbaa99887766554433221100",
                "909192939495969798999a9b9c9d9e9f"
                + "00800400000000000100000001000000"
                + "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
                + "b0b1b2b3b4b5b6b7b8b9babbbcbdbebf"
                + "c0c1c2c3c4c5c6c7c8c9cacbcccdcecf"
                + "e0e1e2e3e4e5e6e7e8e9eaebecedeeef",
                "01000000000000001011121314151617"
                + "18191a1b1c1d1e1f2021222324252627"
                + "02000000000000003031323334353637"
                + "38393a3b3c3d3e3f4041424344454647"
                + "03000000000000005051525354555657"
                + "58595a5b5c5d5e5f6061626364656667",
                "04000000000000007071727374757677"
                + "78797a7b7c7d7e7f8081828384858687"
            });
    }

    /** Decode literal bytes only; never evaluate target instructions or effects. */
    private static Map<Long, Byte> literalMap(long[] starts, String[] hex) {
        equal(starts.length, hex.length, "literal region count");
        final Map<Long, Byte> result = new LinkedHashMap<>();
        for (int region = 0; region < starts.length; region++) {
            check((hex[region].length() & 1) == 0, "complete literal byte pairs");
            for (int i = 0; i < hex[region].length() / 2; i++) {
                final int high = Character.digit(hex[region].charAt(2 * i), 16);
                final int low = Character.digit(hex[region].charAt(2 * i + 1), 16);
                check(high >= 0 && low >= 0, "literal hex digit");
                final long p = starts[region] + i;
                check(!result.containsKey(p), "disjoint owned regions");
                result.put(p, (byte) ((high << 4) | low));
            }
        }
        equal(480, result.size(), "complete literal owned domain");
        return Map.copyOf(result);
    }

    /**
     * This Test's own finite byte store. The scene permits only three ports;
     * every other declared port fails immediately and cannot synthesize effects.
     * This domain is owned software data, not a claim about OS/Native mappings.
     */
    private static final class Ram implements Embedded32Fp659.Memory {
        private final Map<Long, Byte> bytes;
        private final List<String> primitive = new ArrayList<>();
        private final List<String> mixed = new ArrayList<>();
        private final List<Map<Long, Byte>> prefixes = new ArrayList<>();

        private Ram(Map<Long, Byte> initial) {
            bytes = new LinkedHashMap<>(initial);
        }

        private Map<Long, Byte> snapshot() {
            return Map.copyOf(bytes);
        }

        private void requireWidth(long p, int width) {
            for (int i = 0; i < width; i++) {
                check(bytes.containsKey(p + i), "unowned Memory byte " + hex64(p + i));
            }
        }

        private long raw(long p, int width) {
            long bits = 0;
            for (int i = 0; i < width; i++) {
                bits |= (bytes.get(p + i) & 0xffL) << (8 * i);
            }
            return bits;
        }

        private void record(String event) {
            primitive.add(event);
            mixed.add(event);
            prefixes.add(snapshot());
        }

        @Override public int readDword(long p) {
            requireWidth(p, 4);
            final int value = (int) raw(p, 4);
            // Raw-width hex is the frozen oracle's event encoding; value remains Java int.
            record("M.readDword(" + hex64(p) + ")->" + hex32(value));
            return value;
        }

        @Override public long readQword(long p) {
            requireWidth(p, 8);
            final long value = raw(p, 8);
            record("M.readQword(" + hex64(p) + ")->" + hex64(value));
            return value;
        }

        @Override public void writeQword(long p, long value) {
            requireWidth(p, 8);
            for (int i = 0; i < 8; i++) {
                bytes.put(p + i, (byte) (value >>> (8 * i)));
            }
            record("M.writeQword(" + hex64(p) + "," + hex64(value) + ")");
        }

        @Override public int readUnsignedByte(long p) { throw unused("readUnsignedByte"); }
        @Override public int readUnsignedWord(long p) { throw unused("readUnsignedWord"); }
        @Override public void writeDword(long p, int v) { throw unused("writeDword"); }
        @Override public int lockedXaddDword(long p, int v) { throw unused("lockedXaddDword"); }
        @Override public void writeByte(long p, int v) { throw unused("writeByte"); }
        @Override public void writeWord(long p, int v) { throw unused("writeWord"); }
        @Override public Bits128 read128(long p) { throw unused("read128"); }
        @Override public void write128(long p, Bits128 v) { throw unused("write128"); }
        @Override public void write128NonTemporal(long p, Bits128 v) { throw unused("write128NonTemporal"); }
        @Override public FullCopy437Api.Bits256 read256(long p) { throw unused("read256"); }
        @Override public void write256(long p, FullCopy437Api.Bits256 v) { throw unused("write256"); }
        @Override public void write256NonTemporal(long p, FullCopy437Api.Bits256 v) { throw unused("write256NonTemporal"); }
        @Override public void sfence() { throw unused("sfence"); }
    }

    private static AssertionError unused(String port) {
        return new AssertionError("unexpected Memory port: " + port);
    }

    private static String hex64(long bits) {
        final String s = Long.toHexString(bits);
        return "0".repeat(16 - s.length()) + s;
    }

    private static String hex32(int bits) {
        final String s = Integer.toHexString(bits);
        return "0".repeat(8 - s.length()) + s;
    }

    private static void same(Object expected, Object actual, String label) {
        check(expected == actual, label);
    }

    private static void equal(Object expected, Object actual, String label) {
        check(Objects.equals(expected, actual), label);
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }
}
