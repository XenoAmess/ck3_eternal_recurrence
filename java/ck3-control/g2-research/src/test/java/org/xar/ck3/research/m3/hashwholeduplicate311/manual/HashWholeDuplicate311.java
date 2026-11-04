package org.xar.ck3.research.m3.hashwholeduplicate311.manual;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.hashwholefp309.HashWholeFp309Api;
import org.xar.ck3.research.m3.hashwholefp310.HashWholeFp310;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

// The frozen host creation note below is historical; actual310 binding is appended below.
/**
 * SOURCE-ONLY preCandidate mechanical host. No target entry or outcome is invented here.
 * The independently frozen ORIGINAL-LITERAL-ORACLE311.md supplies the two finite cases.
 * Actual309/310 complete declarations are still required before adding their invocation.
 */
public final class HashWholeDuplicate311 {
    private HashWholeDuplicate311() { }

    private static final long IMAGE = 0x140000000L;
    private static final long ENTRY_SP = 0x8008L;
    private static final long CHILD_RET = 0x140C39CCFL;
    private static final Bits128 X6 = bits(0x666768696A6B6C6DL, 0x767778797A7B7C7DL);

    private static Bits128 bits(long low, long high) { return new Bits128(low, high); }

    private static NonvolatileBits incomingN() {
        return new NonvolatileBits(0xB1B2B3B4B5B6B7B8L, 0xC1C2C3C4C5C6C7C8L,
                0xD1D2D3D4D5D6D7D8L, 0xE1E2E3E4E5E6E7E8L,
                0x1213141516171819L, 0x232425262728292AL,
                0x3435363738393A3BL, 0x45464748494A4B4CL, X6);
    }

    private static VolatileBits incomingV(boolean heapInput) {
        return new VolatileBits(0x0102030405060708L, 0x1000L, 0x6000L,
                heapInput ? 0x8899AABB80000002L : 0x1122334489ABCDEFL, 0x3000L,
                0xA1A2A3A4A5A6A7A8L, 0x9192939495969798L,
                bits(0x1011121314151617L, 0x2021222324252627L),
                bits(0x3031323334353637L, 0x4041424344454647L),
                bits(0x5051525354555657L, 0x6061626364656667L),
                bits(0x7071727374757677L, 0x8081828384858687L),
                bits(0x9091929394959697L, 0xA0A1A2A3A4A5A6A7L),
                bits(0xB0B1B2B3B4B5B6B7L, 0xC0C1C2C3C4C5C6C7L));
    }

    private static VolatileBits expectedCallV(boolean heapInput) {
        VolatileBits v = incomingV(heapInput);
        return new VolatileBits(0x2000L, heapInput ? 0x4000L : 0x3000L,
                heapInput ? 0x2058L : 0x5000L, v.r8Bits(), heapInput ? 10L : 15L,
                v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(),
                v.xmm3(), v.xmm4(), v.xmm5());
    }

    private static NonvolatileBits expectedCallN(boolean heapInput) {
        return new NonvolatileBits(heapInput ? 0x2050L : 0x2078L, 0x7FD0L,
                0xD1D2D3D4D5D6D701L, 0x3000L, heapInput ? 16L : 15L,
                heapInput ? 0xFFFFFFFF80000002L : 0xFFFFFFFF89ABCDEFL,
                0x1000L, 0x6000L, X6);
    }

    private static VolatileBits foreignV(boolean heapInput) {
        return new VolatileBits(heapInput ? 0x8A8B8C8D8E8F00FFL : 0x7A7B7C7D7E7F0080L,
                0xAABBCCDDEEFF1020L, 0xBBDDFF1133557799L, 0x2468ACE013579BDFL,
                0xF0E1D2C3B4A59687L, 0x1029384756ABCDEFL, 0xFEDCBA6547382910L,
                bits(0x1111111111111111L, 0xEEEEEEEEEEEEEEEEL),
                bits(0x2222222222222222L, 0xDDDDDDDDDDDDDDDDL),
                bits(0x3333333333333333L, 0xCCCCCCCCCCCCCCCCL),
                bits(0x4444444444444444L, 0xBBBBBBBBBBBBBBBBL),
                bits(0x5555555555555555L, 0xAAAAAAAAAAAAAAAAL),
                bits(0x7777777777777777L, 0x8888888888888888L));
    }

    private static VolatileBits expectedFinalV(boolean heapInput) {
        VolatileBits v = foreignV(heapInput);
        return new VolatileBits(0x6000L, v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(),
                v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(),
                v.xmm3(), v.xmm4(), v.xmm5());
    }

    private static NonvolatileBits expectedFinalN(boolean heapInput) {
        if (!heapInput) return incomingN();
        return new NonvolatileBits(0x9000000000000010L, 0x9000000000000020L,
                0x9000000000000030L, 0x9000000000000040L,
                0x9000000000000050L, 0x9000000000000060L,
                0x9000000000000070L, 0x9000000000000080L, X6);
    }

    private static Mxcsr inputFp(boolean heapInput) {
        return heapInput ? new Mxcsr(0x8010, 0x8050) : new Mxcsr(0x0004, 0x0045);
    }

    private static Mxcsr postFp(boolean heapInput) {
        return heapInput ? new Mxcsr(0x0042, 0x034F) : new Mxcsr(0x2001, 0xA041);
    }

    private static long finalRip(boolean heapInput) {
        return heapInput ? 0x140FEDCBAL : 0x140ABCDEFL;
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private record Event(String operation, long address, long a, long b, long c, long d) { }
    private static Event e(String operation, long address, long value) {
        return new Event(operation, address, value, 0L, 0L, 0L);
    }

    /** Mechanical little-endian byte storage only; no hash, equality or target emulation. */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long[] BASE = {0x1000L, 0x2000L, 0x3000L, 0x4000L,
                0x5000L, 0x6000L, 0x7F08L};
        private static final int[] SIZE = {0x40, 0xA0, 0x40, 0x40, 0x40, 0x20, 0x140};
        private final byte[][] bytes = new byte[SIZE.length][];
        private final List<Event> events = new ArrayList<>();
        private int thresholdReads;

        private Ram() {
            for (int i = 0; i < SIZE.length; i++) {
                bytes[i] = new byte[SIZE[i]];
                Arrays.fill(bytes[i], (byte) 0xA5);
            }
        }

        private int segment(long address, int width) {
            for (int i = 0; i < BASE.length; i++) {
                if (Long.compareUnsigned(address - BASE[i], SIZE[i] - (long) width) <= 0)
                    return i;
            }
            throw new AssertionError("Out of owned RAM: " + Long.toHexString(address) + "/" + width);
        }

        private long peek(long address, int width) {
            int s = segment(address, width);
            int at = (int) (address - BASE[s]);
            long value = 0L;
            for (int i = 0; i < width; i++)
                value |= (long) Byte.toUnsignedInt(bytes[s][at + i]) << (8 * i);
            return value;
        }

        private void seed(long address, int width, long value) {
            int s = segment(address, width);
            int at = (int) (address - BASE[s]);
            for (int i = 0; i < width; i++) bytes[s][at + i] = (byte) (value >>> (8 * i));
        }

        private void beforeRead(long address, int width) {
            if (address <= 0x101FL && address + width > 0x101CL) {
                thresholdReads++;
                events.add(e("FORBIDDEN_THRESHOLD_READ", address, width));
                throw new AssertionError("Duplicate path read the FP threshold");
            }
        }

        private long read(String operation, long address, int width) {
            beforeRead(address, width);
            long value = peek(address, width);
            events.add(e(operation, address, value));
            return value;
        }

        private void write(String operation, long address, int width, long value) {
            seed(address, width, value);
            events.add(e(operation, address, width == 8 ? value : value & ((1L << (8 * width)) - 1)));
        }

        private Ram snapshot() {
            Ram copy = new Ram();
            for (int i = 0; i < SIZE.length; i++)
                System.arraycopy(bytes[i], 0, copy.bytes[i], 0, SIZE[i]);
            return copy;
        }

        private void sameBytes(Ram expected) {
            for (int i = 0; i < SIZE.length; i++)
                check(Arrays.equals(bytes[i], expected.bytes[i]), "RAM segment " + i);
        }

        @Override public int readDword(long a) { return (int) read("RD", a, 4); }
        @Override public long readQword(long a) { return read("RQ", a, 8); }
        @Override public int readUnsignedByte(long a) { return (int) read("RB", a, 1); }
        @Override public int readUnsignedWord(long a) { return (int) read("RW", a, 2); }
        @Override public void writeDword(long a, int v) { write("WD", a, 4, Integer.toUnsignedLong(v)); }
        @Override public void writeQword(long a, long v) { write("WQ", a, 8, v); }
        @Override public void writeByte(long a, int v) { write("WB", a, 1, v); }
        @Override public void writeWord(long a, int v) { write("WW", a, 2, v); }

        @Override public int lockedXaddDword(long a, int increment) {
            beforeRead(a, 4);
            int previous = (int) peek(a, 4);
            seed(a, 4, Integer.toUnsignedLong(previous + increment));
            events.add(new Event("XADD", a, Integer.toUnsignedLong(previous),
                    Integer.toUnsignedLong(increment), 0L, 0L));
            return previous;
        }

        @Override public Bits128 read128(long a) {
            beforeRead(a, 16);
            Bits128 value = bits(peek(a, 8), peek(a + 8, 8));
            events.add(new Event("R128", a, value.lowBits(), value.highBits(), 0L, 0L));
            return value;
        }

        private void put128(String operation, long a, Bits128 v) {
            segment(a, 16);
            seed(a, 8, v.lowBits()); seed(a + 8, 8, v.highBits());
            events.add(new Event(operation, a, v.lowBits(), v.highBits(), 0L, 0L));
        }

        @Override public void write128(long a, Bits128 v) { put128("W128", a, v); }
        @Override public void write128NonTemporal(long a, Bits128 v) { put128("W128NT", a, v); }
        @Override public void sfence() { events.add(e("SFENCE", 0L, 0L)); }

        @Override public FullCopy437Api.Bits256 read256(long a) {
            beforeRead(a, 32);
            segment(a, 32);
            FullCopy437Api.Bits256 v = new FullCopy437Api.Bits256(
                    bits(peek(a, 8), peek(a + 8, 8)), bits(peek(a + 16, 8), peek(a + 24, 8)));
            events.add(new Event("R256", a, v.low().lowBits(), v.low().highBits(),
                    v.high().lowBits(), v.high().highBits()));
            return v;
        }

        private void put256(String operation, long a, FullCopy437Api.Bits256 v) {
            segment(a, 32);
            seed(a, 8, v.low().lowBits()); seed(a + 8, 8, v.low().highBits());
            seed(a + 16, 8, v.high().lowBits()); seed(a + 24, 8, v.high().highBits());
            events.add(new Event(operation, a, v.low().lowBits(), v.low().highBits(),
                    v.high().lowBits(), v.high().highBits()));
        }

        @Override public void write256(long a, FullCopy437Api.Bits256 v) { put256("W256", a, v); }
        @Override public void write256NonTemporal(long a, FullCopy437Api.Bits256 v) { put256("W256NT", a, v); }
    }

    private static Ram initialRam(boolean heapInput) {
        Ram ram = new Ram();
        ram.seed(0x1008L, 8, 0x2000L);
        ram.seed(0x1010L, 4, 0xDEADBEEFL);
        ram.seed(0x1014L, 4, 3L);
        ram.seed(0x1018L, 1, 0x7EL);
        ram.seed(0x101CL, 4, 0xDEADC0DEL);
        ram.seed(0x3000L, 8, 0x4000L);
        ram.seed(0x3018L, 8, heapInput ? 16L : 15L);
        ram.seed(heapInput ? 0x2054L : 0x207CL, 1, heapInput ? 0xFFL : 0x81L);
        ram.seed(heapInput ? 0x2058L : 0x2080L, 8, 0x5000L);
        ram.seed(heapInput ? 0x2070L : 0x2098L, 8, heapInput ? 15L : 16L);
        ram.seed(0x8008L, 8, 0x140101010L);
        return ram;
    }

    private static void foreignRamEffects(Ram ram, boolean heapInput) {
        if (heapInput) {
            ram.writeQword(0x8018L, 0x9000000000000010L);
            ram.writeQword(0x8000L, 0x9000000000000020L);
            ram.writeQword(0x7FF8L, 0x9000000000000030L);
            ram.writeQword(0x7FF0L, 0x9000000000000040L);
            ram.writeQword(0x7FE8L, 0x9000000000000050L);
            ram.writeQword(0x7FE0L, 0x9000000000000060L);
            ram.writeQword(0x7FD8L, 0x9000000000000070L);
            ram.writeQword(0x7FD0L, 0x9000000000000080L);
        }
        ram.writeQword(0x8008L, finalRip(heapInput));
    }

    private static Ram expectedRam(Ram initial, boolean heapInput) {
        Ram ram = initial.snapshot();
        ram.seed(0x8018L, 8, 0xB1B2B3B4B5B6B7B8L);
        ram.seed(0x8000L, 8, 0xC1C2C3C4C5C6C7C8L);
        ram.seed(0x7FF8L, 8, 0xD1D2D3D4D5D6D7D8L);
        ram.seed(0x7FF0L, 8, 0xE1E2E3E4E5E6E7E8L);
        ram.seed(0x7FE8L, 8, 0x1213141516171819L);
        ram.seed(0x7FE0L, 8, 0x232425262728292AL);
        ram.seed(0x7FD8L, 8, 0x3435363738393A3BL);
        ram.seed(0x7FD0L, 8, 0x45464748494A4B4CL);
        ram.seed(0x7F58L, 8, 0x140C39CCFL);
        if (heapInput) {
            ram.seed(0x8018L, 8, 0x9000000000000010L);
            ram.seed(0x8000L, 8, 0x9000000000000020L);
            ram.seed(0x7FF8L, 8, 0x9000000000000030L);
            ram.seed(0x7FF0L, 8, 0x9000000000000040L);
            ram.seed(0x7FE8L, 8, 0x9000000000000050L);
            ram.seed(0x7FE0L, 8, 0x9000000000000060L);
            ram.seed(0x7FD8L, 8, 0x9000000000000070L);
            ram.seed(0x7FD0L, 8, 0x9000000000000080L);
        }
        ram.seed(0x8008L, 8, heapInput ? 0x140FEDCBAL : 0x140ABCDEFL);
        ram.seed(0x6000L, 8, heapInput ? 0x2050L : 0x2078L);
        ram.seed(0x6008L, 1, 0L);
        return ram;
    }

    private static List<Event> expectedEvents(boolean heapInput) {
        List<Event> events = new ArrayList<>(List.of(
                e("WQ", 0x8018L, 0xB1B2B3B4B5B6B7B8L),
                e("WQ", 0x8000L, 0xC1C2C3C4C5C6C7C8L),
                e("WQ", 0x7FF8L, 0xD1D2D3D4D5D6D7D8L),
                e("WQ", 0x7FF0L, 0xE1E2E3E4E5E6E7E8L),
                e("WQ", 0x7FE8L, 0x1213141516171819L),
                e("WQ", 0x7FE0L, 0x232425262728292AL),
                e("WQ", 0x7FD8L, 0x3435363738393A3BL),
                e("WQ", 0x7FD0L, 0x45464748494A4B4CL),
                e("RD", 0x1014L, 3L), e("RQ", 0x1008L, 0x2000L),
                e("RB", heapInput ? 0x2054L : 0x207CL, heapInput ? 0xFFL : 0x81L),
                e("RQ", 0x3018L, heapInput ? 16L : 15L),
                e("RQ", heapInput ? 0x2070L : 0x2098L, heapInput ? 15L : 16L),
                e("RQ", heapInput ? 0x3000L : 0x2080L, heapInput ? 0x4000L : 0x5000L),
                e("WQ", 0x7F58L, 0x140C39CCFL)));
        if (heapInput) events.addAll(List.of(
                e("WQ", 0x8018L, 0x9000000000000010L),
                e("WQ", 0x8000L, 0x9000000000000020L),
                e("WQ", 0x7FF8L, 0x9000000000000030L),
                e("WQ", 0x7FF0L, 0x9000000000000040L),
                e("WQ", 0x7FE8L, 0x9000000000000050L),
                e("WQ", 0x7FE0L, 0x9000000000000060L),
                e("WQ", 0x7FD8L, 0x9000000000000070L),
                e("WQ", 0x7FD0L, 0x9000000000000080L)));
        events.add(e("WQ", 0x8008L, heapInput ? 0x140FEDCBAL : 0x140ABCDEFL));
        events.add(e("RQ", 0x7F58L, 0x140C39CCFL));
        events.add(e("WQ", 0x6000L, heapInput ? 0x2050L : 0x2078L));
        events.add(e("WB", 0x6008L, 0L));
        events.addAll(List.of(
                e("RQ", 0x8018L, heapInput ? 0x9000000000000010L : 0xB1B2B3B4B5B6B7B8L),
                e("RQ", 0x7FD0L, heapInput ? 0x9000000000000080L : 0x45464748494A4B4CL),
                e("RQ", 0x7FD8L, heapInput ? 0x9000000000000070L : 0x3435363738393A3BL),
                e("RQ", 0x7FE0L, heapInput ? 0x9000000000000060L : 0x232425262728292AL),
                e("RQ", 0x7FE8L, heapInput ? 0x9000000000000050L : 0x1213141516171819L),
                e("RQ", 0x7FF0L, heapInput ? 0x9000000000000040L : 0xE1E2E3E4E5E6E7E8L),
                e("RQ", 0x7FF8L, heapInput ? 0x9000000000000030L : 0xD1D2D3D4D5D6D7D8L),
                e("RQ", 0x8000L, heapInput ? 0x9000000000000020L : 0xC1C2C3C4C5C6C7C8L),
                e("RQ", 0x8008L, heapInput ? 0x140FEDCBAL : 0x140ABCDEFL)));
        return List.copyOf(events);
    }

    private static void runCase(boolean heapInput) {
        Ram ram = initialRam(heapInput);
        Ram expected = expectedRam(ram, heapInput);
        Mxcsr preFp = inputFp(heapInput);
        Mxcsr postFp = postFp(heapInput);
        int[] budgetSteps = {0};
        int[] callCount = {0};
        GovernmentCrtBoundary185Api.LoopBudget budget = (header, address) -> {
            check(budgetSteps[0] == 0, "Extra budget step");
            check(header == 0xC39CB0L, "Unexpected budget header");
            check(address == (heapInput ? 0x2070L : 0x2098L), "Budget guard address");
            check(ram.events.size() == 12, "Budget must precede bucket-capacity read");
            budgetSteps[0]++;
        };
        GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                IMAGE, ENTRY_SP, incomingV(heapInput), incomingN());
        HashWholeFp309Api.Input input = new HashWholeFp309Api.Input(
                new QueueFp604Api.Input(new FullCopy437Api.Input(entry, heapInput, budget), preFp),
                0x311L);
        HashWholeFp309Api.Calls calls = (frame, sameMemory) -> {
            check(callCount[0] == 0, "Unexpected extra source call");
            callCount[0]++;
            check(sameMemory == ram, "Memory identity");
            check(frame.ownerInput() == input, "Owner input identity");
            check(frame.originCallSiteRva() == 0x311L, "Origin metadata");
            check(frame.budget() == budget && budgetSteps[0] == 1, "Budget identity/count");
            check(frame.directionFlagSet() == heapInput, "Call DF");
            check(frame.preMxcsr() == preFp, "Call partial MXCSR identity");
            check(frame.original().equals(new GovernmentCrtBoundary185Api.Call(
                    0xC39CCAL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x3F6D2B0L,
                    0x7F60L, expectedCallV(heapInput), expectedCallN(heapInput))), "Full original CALL");
            check(frame.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(
                    IMAGE, 0x7F58L, expectedCallV(heapInput), expectedCallN(heapInput))), "Full child entry");
            check(frame.instructionLength() == 5 && frame.returnRipBits() == CHILD_RET, "CALL route/RET");
            check(ram.events.equals(expectedEvents(heapInput).subList(0, 15)), "Exact source prefix");
            int[] pushedBytes = {0xCF, 0x9C, 0xC3, 0x40, 1, 0, 0, 0};
            for (int i = 0; i < pushedBytes.length; i++)
                check(ram.peek(0x7F58L + i, 1) == pushedBytes[i], "CALL push byte " + i);
            foreignRamEffects(ram, heapInput);
            long childRet = sameMemory.readQword(frame.childEntry().rspBits());
            check(childRet == CHILD_RET, "Actual child RET read");
            GovernmentCrtBoundary185Api.NormalReturn normal = new GovernmentCrtBoundary185Api.NormalReturn(
                    foreignV(heapInput), childRet, frame.childEntry().rspBits() + 8,
                    frame.childEntry().nonvolatileBits());
            return new HashWholeFp309Api.Forwarded(new QueueFp604Api.Normal(
                    new FullCopy437Api.CallResult(normal, !heapInput), postFp));
        };
        HashWholeFp309Api.Result result = HashWholeFp310.execute(input, ram, calls);
        check(result instanceof HashWholeFp309Api.Forwarded, "Whole result must be Forwarded");
        QueueFp604Api.Outcome outcome = ((HashWholeFp309Api.Forwarded) result).actual();
        check(outcome instanceof QueueFp604Api.Normal, "Whole result must be Normal");
        QueueFp604Api.Normal actual = (QueueFp604Api.Normal) outcome;
        GovernmentCrtBoundary185Api.NormalReturn normal = actual.base().normalReturn();
        check(normal.volatileBits().equals(expectedFinalV(heapInput)), "All final V");
        check(normal.nonvolatileBits().equals(expectedFinalN(heapInput)), "Fresh final N");
        check(normal.returnRipBits() == finalRip(heapInput), "Fresh parent RET");
        check(normal.callerRspBits() == 0x8010L, "Final caller SP");
        check(actual.base().postDirectionFlagSet() == !heapInput, "Actual post DF");
        check(actual.postMxcsr() == postFp && !actual.postMxcsr().isExact(), "Actual partial post MXCSR");
        check(callCount[0] == 1 && budgetSteps[0] == 1, "Finite call/budget counts");
        check(ram.thresholdReads == 0, "No FP threshold read");
        check(ram.events.size() == (heapInput ? 36 : 28), "Complete event count");
        check(ram.events.equals(expectedEvents(heapInput)), "Complete typed event sequence");
        ram.sameBytes(expected);
        check(ram.peek(0x6000L, 1) == (heapInput ? 0x50 : 0x78), "Output bucket low byte");
        check(ram.peek(0x6001L, 1) == 0x20, "Output bucket next byte");
        for (int i = 2; i < 8; i++) check(ram.peek(0x6000L + i, 1) == 0, "Output byte " + i);
        check(ram.peek(0x6008L, 1) == 0, "Duplicate flag");
    }

    public static void main(String[] args) {
        runCase(false);
        runCase(true);
    }
}
