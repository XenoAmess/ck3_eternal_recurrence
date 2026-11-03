package org.xar.ck3.research.m3.add4range262.manual;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.Add4Fp639Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.add4range262.Add4Range262;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Finite manual witness. Oracle was frozen before reading 262.
 * Each case runs the complete 639 through 262: real qword COPY, ADD219, real
 * 260/261 and three actual scalar 641 calls on one bounded byte RAM object.
 * No native, hardware ABI, RFLAGS, upper-YMM, CPU/OS or performance qualification.
 * Native first execution is recorded separately from the author's source-only creation.
 */
public final class Add4RangeWhole262 {
    private Add4RangeWhole262() { }

    private static final long IMAGE = 0x140000000L;
    private static final long HEAD = 0x1000L;
    private static final long ARRAY = 0x2000L;
    private static final long SOURCE = 0x3000L;
    private static final long SP = 0x8008L;
    private static final long RETURN_RIP = 0x7777666655554444L;
    private static final long BX = 0xB0B0B0B0B0B0B0B0L;
    private static final long BP = 0xB1B1B1B1B1B1B1B1L;
    private static final long SI = 0xB2B2B2B2B2B2B2B2L;
    private static final long DI = 0xB3B3B3B3B3B3B3B3L;
    private static final long R12 = 0xB4B4B4B4B4B4B4B4L;
    private static final long R13 = 0xB5B5B5B5B5B5B5B5L;
    private static final long R14 = 0xB6B6B6B6B6B6B6B6L;
    private static final long R15 = 0xB7B7B7B7B7B7B7B7L;
    private static final long R11 = 0x1111111111111111L;
    private static final Bits128 X0 = new Bits128(0x0101010101010101L, 0x0202020202020202L);
    private static final Bits128 X1 = new Bits128(0x1111111111111111L, 0x1212121212121212L);
    private static final Bits128 X2 = new Bits128(0x2121212121212121L, 0x2222222222222222L);
    private static final Bits128 X3 = new Bits128(0x3131313131313131L, 0x3232323232323232L);
    private static final Bits128 X4 = new Bits128(0x4141414141414141L, 0x4242424242424242L);
    private static final Bits128 X5 = new Bits128(0x5151515151515151L, 0x5252525252525252L);
    private static final Bits128 X6 = new Bits128(0x6161616161616161L, 0x6262626262626262L);

    public static void main(String[] arguments) {
        insertionAtOne();
        insertionAtThree();
        System.out.println("Add4RangeWhole262: 2 finite whole cases completed");
    }

    public static void insertionAtOne() {
        runCase("index1", 1, QueueFp604Api.Mxcsr.exact(0xBEEF), true,
            new int[] { 0x10203040, 0xC1D2E3F4, 0x01234567, 0x8090A0B0, 0x55667788, 0xFEDCBA98 },
            new VolatileBits(0x200CL, 0x55667788L, 0x200CL, 0x200CL, 0x2000L,
                0x140000000L, 0x1111111111111111L, X0, X1, X2, X3, X4, X5),
            List.of(new Step(0x4220B49L, 0x2004L), new Step(0x4220B49L, 0x2008L),
                new Step(0x4220B49L, 0x2010L), new Step(0x4220B49L, 0x2004L),
                new Step(0x4220B49L, 0x2008L), new Step(0x4220B49L, 0x200CL)));
    }

    public static void insertionAtThree() {
        runCase("index3", 3, new QueueFp604Api.Mxcsr(0x8041, 0xC07F), false,
            new int[] { 0x10203040, 0x8090A0B0, 0x55667788, 0xC1D2E3F4, 0x01234567, 0xFEDCBA98 },
            new VolatileBits(0x2014L, 0xFEDCBA98L, 0x2010L, 0x2010L, 0x2000L,
                0x140000000L, 0x1111111111111111L, X0, X1, X2, X3, X4, X5),
            List.of(new Step(0x4220B49L, 0x200CL), new Step(0x4220B49L, 0x2010L),
                new Step(0x4220B49L, 0x200CL), new Step(0x4220B49L, 0x2010L)));
    }

    private static void runCase(String name, int index, QueueFp604Api.Mxcsr fp,
            boolean df, int[] finalArray, VolatileBits finalV, List<Step> finalSteps) {
        Ram memory = new Ram();
        memory.seedQword(HEAD, ARRAY);
        memory.seedDword(HEAD + 8, 8);
        memory.seedDword(HEAD + 12, 4);
        memory.seedQword(HEAD + 16, 0x4848484848484848L);
        memory.seedDword(ARRAY, 0x10203040);
        memory.seedDword(ARRAY + 4, 0x8090A0B0);
        memory.seedDword(ARRAY + 8, 0x55667788);
        memory.seedDword(ARRAY + 12, 0xFEDCBA98);
        memory.seedDword(SOURCE, 0xC1D2E3F4);
        memory.seedDword(SOURCE + 4, 0x01234567);
        memory.seedDword(IMAGE + 0x6090020L, 0x422696D);
        memory.seedQword(SP, RETURN_RIP);

        // Independent literal expected bytes are prepared before target execution.
        for (int i = 0; i < finalArray.length; i++) {
            memory.expectDword(ARRAY + 4L * i, finalArray[i]);
        }
        memory.expectDword(HEAD + 12, 6);
        memory.expectQword(SP - 8, BX);
        memory.expectQword(SP - 16, R13);
        memory.expectQword(SP - 24, R14);
        memory.expectQword(SP - 32, R15);
        memory.expectQword(SP - 40, R12);
        memory.expectDword(SP + 8, 6);
        memory.expectQword(SP - 80, IMAGE + 0xADD21EL);
        memory.expectQword(SP - 72, index);
        memory.expectQword(SP - 64, SI);
        memory.expectQword(SP - 88, DI);
        memory.expectQword(SP - 128, IMAGE + 0x9D09B3L);

        NonvolatileBits initialN = new NonvolatileBits(BX, BP, SI, DI, R12, R13, R14, R15, X6);
        VolatileBits initialV = new VolatileBits(0x0102030405060708L, HEAD, index,
            SOURCE, SOURCE + 8, 0x1010101010101010L, R11, X0, X1, X2, X3, X4, X5);
        var entry = new GovernmentCrtBoundary185Api.Entry(IMAGE, SP, initialV, initialN);
        var input = new QueueFp604Api.Input(new FullCopy437Api.Input(entry, df, memory::beforeStep), fp);

        FullCopyWithFp613.TailCalls unknownTails = frame -> {
            memory.unknownCopyTails++;
            throw new AssertionError(name + ": unexpected COPY tail " + frame);
        };
        Add4Fp639Api.Calls foreign = frame -> {
            memory.foreignCalls++;
            if (frame.call().callSiteRva() == 0xADD153L) memory.allocatorCalls++;
            else if (frame.call().callSiteRva() == 0xADD1B5L) memory.freeCalls++;
            else memory.otherForeignCalls++;
            throw new AssertionError(name + ": unexpected foreign call " + frame);
        };

        memory.running = true;
        QueueFp604Api.Outcome outcome = Add4Range262.execute(input, memory, unknownTails, foreign, 0x12345678L);
        memory.running = false;
        require(outcome instanceof QueueFp604Api.Normal, name + ": complete normal outcome");
        QueueFp604Api.Normal normal = (QueueFp604Api.Normal) outcome;
        var returned = normal.base().normalReturn();
        require(returned.volatileBits().equals(finalV), name + ": all represented V bits");
        require(returned.nonvolatileBits().equals(initialN), name + ": all represented N bits");
        require(returned.returnRipBits() == RETURN_RIP, name + ": final fresh RET");
        require(returned.callerRspBits() == 0x8010L, name + ": final caller RSP");
        require(normal.base().postDirectionFlagSet() == df, name + ": explicit DF");
        require(normal.postMxcsr() == fp, name + ": same explicit FP DATA object");
        require(memory.steps.equals(finalSteps), name + ": exact scalar641 loop admissions");
        require(memory.stack.equals(expectedStack(index)), name + ": every fresh stack access");
        require(memory.foreignCalls == 0 && memory.allocatorCalls == 0 && memory.freeCalls == 0
            && memory.otherForeignCalls == 0, name + ": foreign/allocator/free not reached");
        require(memory.unknownCopyTails == 0, name + ": unknown COPY tail not reached");
        require(memory.vectorReads == 0 && memory.vectorWrites == 0 && memory.nonTemporalEffects == 0
            && memory.sfenceEffects == 0 && memory.vzeroUpperEffects == 0 && memory.atomicEffects == 0,
            name + ": no unclaimed vector/fence/atomic effects");
        memory.checkEveryByte(name);
    }

    private static List<Access> expectedStack(int index) {
        return List.of(
            at('W', 8, -8, BX), at('W', 8, -16, R13), at('W', 8, -24, R14),
            at('W', 8, -32, R15), at('W', 8, -40, R12), at('W', 4, 8, 6),
            at('W', 8, -80, IMAGE + 0xADD1FCL), at('R', 8, -80, IMAGE + 0xADD1FCL),
            at('W', 8, -80, IMAGE + 0xADD21EL), at('W', 8, -72, index),
            at('W', 8, -64, SI), at('W', 8, -88, DI),
            at('W', 8, -128, IMAGE + 0x9D099DL), at('R', 8, -128, IMAGE + 0x9D099DL),
            at('W', 8, -128, IMAGE + 0x9D09A8L), at('R', 8, -128, IMAGE + 0x9D09A8L),
            at('W', 8, -128, IMAGE + 0x9D09B3L), at('R', 8, -128, IMAGE + 0x9D09B3L),
            at('R', 8, -64, SI), at('R', 8, -72, index), at('R', 8, -88, DI),
            at('R', 8, -80, IMAGE + 0xADD21EL), at('R', 8, -40, R12),
            at('R', 8, -32, R15), at('R', 8, -24, R14), at('R', 8, -16, R13),
            at('R', 8, -8, BX), at('R', 8, 0, RETURN_RIP));
    }

    private static Access at(char operation, int width, long offset, long value) {
        return new Access(operation, width, SP + offset, value);
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private record Access(char operation, int width, long address, long value) { }
    private record Step(long pc, long cursor) { }

    private static final class Region {
        final long base;
        final byte[] actual;
        final byte[] expected;

        Region(long base, int size) {
            this.base = base;
            actual = new byte[size];
            expected = new byte[size];
            Arrays.fill(actual, (byte) 0xA5);
            Arrays.fill(expected, (byte) 0xA5);
        }
    }

    /** Mechanical storage only: no COPY, reverse, rotate or target-state model. */
    private static final class Ram implements Add4Range262.Memory {
        private final List<Region> regions = List.of(new Region(HEAD, 32), new Region(ARRAY, 64),
            new Region(SOURCE, 16), new Region(SP - 0x100L, 0x140),
            new Region(IMAGE + 0x6090020L, 4));
        private final List<Access> stack = new ArrayList<>();
        private final List<Step> steps = new ArrayList<>();
        private boolean running;
        private int operations;
        private int foreignCalls, allocatorCalls, freeCalls, otherForeignCalls, unknownCopyTails;
        private int vectorReads, vectorWrites, nonTemporalEffects, sfenceEffects, vzeroUpperEffects, atomicEffects;

        private Region region(long address, int width) {
            if (width < 1 || width > 32) throw new AssertionError("invalid mechanical width");
            for (Region region : regions) {
                long offset = address - region.base;
                if (address >= region.base && offset <= region.actual.length - width) return region;
            }
            throw new AssertionError("unmapped finite RAM access 0x" + Long.toHexString(address) + "/" + width);
        }

        private long peek(long address, int width) {
            if (width > 8) throw new AssertionError("scalar width");
            Region region = region(address, width);
            int offset = (int) (address - region.base);
            long result = 0;
            for (int i = 0; i < width; i++) result |= (region.actual[offset + i] & 255L) << (8 * i);
            return result;
        }

        private void put(long address, int width, long value, boolean expected) {
            if (width > 8) throw new AssertionError("scalar width");
            Region region = region(address, width);
            int offset = (int) (address - region.base);
            byte[] bytes = expected ? region.expected : region.actual;
            for (int i = 0; i < width; i++) bytes[offset + i] = (byte) (value >>> (8 * i));
        }

        private void charge() {
            if (running && ++operations > 512) throw new AssertionError("finite memory-operation budget");
        }

        private void note(char operation, int width, long address, long value) {
            charge();
            if (running && address >= SP - 0x100L && address <= SP + 0x40L - width) {
                stack.add(new Access(operation, width, address, value));
            }
        }

        private void beforeStep(long pc, long cursor) {
            if (steps.size() >= 16) throw new AssertionError("finite loop-step budget");
            steps.add(new Step(pc, cursor));
        }

        private void seedQword(long address, long value) { put(address, 8, value, false); put(address, 8, value, true); }
        private void seedDword(long address, int value) { put(address, 4, value, false); put(address, 4, value, true); }
        private void expectQword(long address, long value) { put(address, 8, value, true); }
        private void expectDword(long address, int value) { put(address, 4, value, true); }

        private void checkEveryByte(String name) {
            for (Region region : regions) {
                for (int i = 0; i < region.actual.length; i++) {
                    require(region.actual[i] == region.expected[i], name + ": byte 0x"
                        + Long.toHexString(region.base + i));
                }
            }
        }

        @Override public int readUnsignedByte(long address) {
            int value = (int) peek(address, 1); note('R', 1, address, value); return value;
        }
        @Override public int readUnsignedWord(long address) {
            int value = (int) peek(address, 2); note('R', 2, address, value); return value;
        }
        @Override public int readDword(long address) {
            long value = peek(address, 4); note('R', 4, address, value); return (int) value;
        }
        @Override public long readQword(long address) {
            long value = peek(address, 8); note('R', 8, address, value); return value;
        }
        @Override public void writeByte(long address, int value) {
            put(address, 1, value, false); note('W', 1, address, value & 255L);
        }
        @Override public void writeWord(long address, int value) {
            put(address, 2, value, false); note('W', 2, address, value & 65535L);
        }
        @Override public void writeDword(long address, int value) {
            put(address, 4, value, false); note('W', 4, address, Integer.toUnsignedLong(value));
        }
        @Override public void writeQword(long address, long value) {
            put(address, 8, value, false); note('W', 8, address, value);
        }
        private Bits128 peek128(long address) {
            region(address, 16); return new Bits128(peek(address, 8), peek(address + 8, 8));
        }
        private void put128(long address, Bits128 value) {
            region(address, 16); put(address, 8, value.lowBits(), false); put(address + 8, 8, value.highBits(), false);
        }
        private FullCopy437Api.Bits256 peek256(long address) {
            region(address, 32); return new FullCopy437Api.Bits256(peek128(address), peek128(address + 16));
        }
        private void put256(long address, FullCopy437Api.Bits256 value) {
            region(address, 32); put128(address, value.low()); put128(address + 16, value.high());
        }
        @Override public Bits128 read128(long address) {
            Bits128 value = peek128(address); vectorReads++; note('R', 16, address, value.lowBits()); return value;
        }
        @Override public FullCopy437Api.Bits256 read256(long address) {
            FullCopy437Api.Bits256 value = peek256(address); vectorReads++; note('R', 32, address, value.low().lowBits()); return value;
        }
        @Override public void write128(long address, Bits128 value) {
            put128(address, value); vectorWrites++; note('W', 16, address, value.lowBits());
        }
        @Override public void write256(long address, FullCopy437Api.Bits256 value) {
            put256(address, value); vectorWrites++; note('W', 32, address, value.low().lowBits());
        }
        @Override public void write128NonTemporal(long address, Bits128 value) {
            put128(address, value); vectorWrites++; nonTemporalEffects++; note('N', 16, address, value.lowBits());
        }
        @Override public void write256NonTemporal(long address, FullCopy437Api.Bits256 value) {
            put256(address, value); vectorWrites++; nonTemporalEffects++; note('N', 32, address, value.low().lowBits());
        }
        @Override public synchronized int lockedXaddDword(long address, int addend) {
            int old = (int) peek(address, 4); put(address, 4, old + addend, false);
            atomicEffects++; note('X', 4, address, Integer.toUnsignedLong(old)); return old;
        }
        @Override public void sfence() { charge(); sfenceEffects++; }
        @Override public void vzeroUpper() { charge(); vzeroUpperEffects++; }
    }
}
