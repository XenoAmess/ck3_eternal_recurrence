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
 * Finite manual witness. Independent literal oracle was frozen first in
 * ORACLE-PRE-CANDIDATE262.json (0d617045ba09c78b32618d164efec8664c52ec5a88e80eb146deb5a1db64095d).
 * Both cases enter the new whole262 boundary, perform real COPY and the count store,
 * then enter actual 260/261/641. No lower callee is substituted.
 * A fault is supplied only through an actual public LoopBudget or Memory port.
 * No CPU/OS/native-memory fault equivalence or performance conclusion is claimed.
 */
public final class Add4RangeFailure262 {
    private Add4RangeFailure262() { }

    private static final long IMAGE = 0x140000000L;
    private static final long HEADER = 0x2000L, DATA = 0x3000L, SOURCE = 0x4000L;
    private static final long S = 0x9008L, P = 0x8fc0L, Q = 0x8fb8L, R = 0x8f88L;
    private static final long TABLE = IMAGE + 0x6090000L;
    private static final long ORIGIN = 0x166166L;
    private static final int A = 0x11223344, B = 0x55667788, C = 0x99aabbcc;
    private static final int D = 0xddeeff00, X = 0x0f1e2d3c, Y = 0x4b5a6978;
    private static final NonvolatileBits N = new NonvolatileBits(
        0x1111222233334444L, 0x2222333344445555L, 0x3333444455556666L,
        0x4444555566667777L, 0x5555666677778888L, 0x6666777788889999L,
        0x777788889999aaaaL, 0x88889999aaaabbbbL,
        new Bits128(0x9192939495969798L, 0xa1a2a3a4a5a6a7a8L));

    private record Event(String operation, long address, long bits) { }

    private static final class BudgetDenied extends UnsupportedOperationException {
        private static final long serialVersionUID = 1L;
        BudgetDenied() { super("owned scalar budget admission denied"); }
    }

    private static final class OwnedReadFault extends UnsupportedOperationException {
        private static final long serialVersionUID = 1L;
        OwnedReadFault() { super("owned actual reverse RET read failed"); }
    }

    /** Manual entry for the two finite public-port failure cases. */
    public static void main(String[] args) {
        budgetAfterCompletedFirstReverse();
        memoryFailureAtFirstReverseRet();
    }

    public static void budgetAfterCompletedFirstReverse() {
        BudgetDenied denied = new BudgetDenied();
        OwnedRam ram = new OwnedRam(3, 1, null);
        GovernmentCrtBoundary185Api.LoopBudget budget = (site, cursor) -> {
            ram.events.add(new Event("BUDGET", site, cursor));
            ram.budgetCalls++;
            if (ram.budgetCalls == 2) throw denied;
        };
        List<Event> oracle = literalPrefix(false);
        runWholeOnce(ram, budget, denied, oracle);
        require(ram.budgetCalls == 2, "budget case admissions");
        require(ram.faultCalls == 0, "budget case has no Memory fault");
        require(ram.peek(R, 8) == IMAGE + 0x9d09a8L, "second reverse CALL really pushed");
        requireData(ram, new int[] { A, C, B, X });
    }

    public static void memoryFailureAtFirstReverseRet() {
        OwnedReadFault fault = new OwnedReadFault();
        OwnedRam ram = new OwnedRam(4, 2, fault);
        GovernmentCrtBoundary185Api.LoopBudget budget = (site, cursor) -> {
            ram.events.add(new Event("BUDGET", site, cursor));
            ram.budgetCalls++;
        };
        List<Event> oracle = literalPrefix(true);
        runWholeOnce(ram, budget, fault, oracle);
        require(ram.budgetCalls == 2, "Memory case swap and center admissions");
        require(ram.faultCalls == 1, "one actual lower RET port failure");
        require(ram.peek(R, 8) == IMAGE + 0x9d099dL, "faulted RET bytes are the real first CALL return");
        requireData(ram, new int[] { A, D, C, B, X, Y });
    }

    private static void runWholeOnce(OwnedRam ram, GovernmentCrtBoundary185Api.LoopBudget budget,
            RuntimeException expected, List<Event> oracle) {
        VolatileBits v = new VolatileBits(0x1011121314151617L, HEADER, 1L, SOURCE,
            SOURCE + ram.added * 4L, 0x2122232425262728L, 0x3132333435363738L,
            new Bits128(0x4142434445464748L, 0x5152535455565758L),
            new Bits128(0x6162636465666768L, 0x7172737475767778L),
            new Bits128(0x8182838485868788L, 0x9192939495969798L),
            new Bits128(0xa1a2a3a4a5a6a7a8L, 0xb1b2b3b4b5b6b7b8L),
            new Bits128(0xc1c2c3c4c5c6c7c8L, 0xd1d2d3d4d5d6d7d8L),
            new Bits128(0xe1e2e3e4e5e6e7e8L, 0xf1f2f3f4f5f6f7f8L));
        var input = new QueueFp604Api.Input(new FullCopy437Api.Input(
            new GovernmentCrtBoundary185Api.Entry(IMAGE, S, v, N), true, budget),
            QueueFp604Api.Mxcsr.exact(0x9fc5));
        Add4Fp639Api.Calls foreign = frame -> {
            ram.foreignCalls++;
            if (frame.call().callSiteRva() == 0xadd153L) ram.allocatorCalls++;
            if (frame.call().callSiteRva() == 0xadd1b5L) ram.freeCalls++;
            throw new AssertionError("unexpected foreign CALL " + frame.call().callSiteRva());
        };
        FullCopyWithFp613.TailCalls unknownTails = frame -> {
            ram.unknownTailCalls++;
            throw new AssertionError("unexpected COPY tail " + frame.original().transfer().jumpSiteRva());
        };
        RuntimeException escaped = null;
        try {
            Add4Range262.execute(input, ram, unknownTails, foreign, ORIGIN);
            throw new AssertionError("whole262 returned an Outcome instead of the exact port exception");
        } catch (RuntimeException actual) {
            escaped = actual;
        }
        require(escaped == expected, "port exception identity; wrapping/swallow/fallback forbidden");
        require(escaped.getClass() == expected.getClass(), "port exception exact class");
        require(ram.events.equals(oracle), "complete ordered port trace\nexpected=" + oracle + "\nactual=" + ram.events);
        ram.requireFullRamAfterLiteralWrites(oracle);
        require(ram.foreignCalls == 0 && ram.allocatorCalls == 0 && ram.freeCalls == 0,
            "all unvisited allocator/free/foreign callbacks must remain zero");
        require(ram.unknownTailCalls == 0 && ram.unsupportedPortCalls == 0,
            "unknown COPY tails and unvisited instruction effects must remain zero");
        require(ram.peek(HEADER, 8) == DATA, "container storage pointer unchanged");
        require(ram.peek(HEADER + 8, 4) == 8, "capacity unchanged");
        require(ram.peek(HEADER + 12, 4) == ram.oldCount + ram.added,
            "ADD207 count write survives the later exception");
        require(ram.peek(Q, 8) == IMAGE + 0xadd21eL, "ADD219 owns its actual return bytes");
        require(ram.events.stream().noneMatch(e -> e.operation().startsWith("RQ") &&
            (e.address() == S || e.address() == P + 0x20 || e.address() == P + 0x28 ||
             e.address() == P + 0x30 || e.address() == P + 0x38 || e.address() == P + 0x40)),
            "outer R12/POP restoration and final RET are unreachable");
        require(ram.events.stream().filter(e -> e.operation().equals("RQ") && e.address() == Q).count() == 1,
            "Q was read only by the earlier COPY RET, never by range RET after ADD219");
        require(ram.events.stream().noneMatch(e -> e.operation().startsWith("RQ") &&
            (e.address() == P || e.address() == P + 8 || e.address() == Q - 8)),
            "range RSI/RBX/RDI restoration is unreachable");
    }

    /** Literal source-derived access matrices, not an alternative COPY/rotate implementation. */
    private static List<Event> literalPrefix(boolean memoryFault) {
        int oldCount = memoryFault ? 4 : 3;
        int added = memoryFault ? 2 : 1;
        List<Event> result = new ArrayList<>();
        result.add(e("WQ", S - 8, N.rbxBits()));
        result.add(e("WQ", S - 16, N.r13Bits()));
        result.add(e("WQ", S - 24, N.r14Bits()));
        result.add(e("WQ", S - 32, N.r15Bits()));
        result.add(e("RD", HEADER + 12, oldCount));
        result.add(e("WQ", P + 0x20, N.r12Bits()));
        result.add(e("RD", HEADER + 8, 8));
        result.add(e("WD", P + 0x50, oldCount + added));
        result.add(e("RQ", HEADER, DATA));
        result.add(e("WQ", Q, IMAGE + 0xadd1fcL));
        result.add(e("RD", TABLE + added * 16L, memoryFault ? 0x422696dL : 0x422697aL));
        if (memoryFault) {
            long sourceQword = Integer.toUnsignedLong(X) | (Integer.toUnsignedLong(Y) << 32);
            result.add(e("RQ", SOURCE, sourceQword));
            result.add(e("WQ", DATA + 16, sourceQword));
        } else {
            result.add(e("RD", SOURCE, Integer.toUnsignedLong(X)));
            result.add(e("WD", DATA + 12, Integer.toUnsignedLong(X)));
        }
        result.add(e("RQ", Q, IMAGE + 0xadd1fcL));
        result.add(e("RD", HEADER + 12, oldCount));
        result.add(e("RQ", HEADER, DATA));
        result.add(e("WD", HEADER + 12, oldCount + added));
        result.add(e("WQ", Q, IMAGE + 0xadd21eL));
        result.add(e("WQ", P, 1));
        result.add(e("WQ", P + 8, N.rsiBits()));
        result.add(e("WQ", Q - 8, N.rdiBits()));
        result.add(e("WQ", R, IMAGE + 0x9d099dL));
        result.add(e("BUDGET", 0x4220b49L, DATA + 4));
        result.add(e("RD", DATA + 4, Integer.toUnsignedLong(B)));
        result.add(e("RD", DATA + (memoryFault ? 12 : 8), Integer.toUnsignedLong(memoryFault ? D : C)));
        result.add(e("WD", DATA + 4, Integer.toUnsignedLong(memoryFault ? D : C)));
        result.add(e("WD", DATA + (memoryFault ? 12 : 8), Integer.toUnsignedLong(B)));
        if (memoryFault) {
            result.add(e("BUDGET", 0x4220b49L, DATA + 8));
            result.add(e("RQ_FAIL", R, IMAGE + 0x9d099dL));
        } else {
            result.add(e("RQ", R, IMAGE + 0x9d099dL));
            result.add(e("WQ", R, IMAGE + 0x9d09a8L));
            result.add(e("BUDGET", 0x4220b49L, DATA + 12));
        }
        return List.copyOf(result);
    }

    private static Event e(String operation, long address, long bits) {
        return new Event(operation, address, bits);
    }

    private static void requireData(OwnedRam ram, int[] words) {
        for (int i = 0; i < words.length; i++)
            require(ram.peek(DATA + i * 4L, 4) == Integer.toUnsignedLong(words[i]), "literal partial DWORD data index " + i);
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    /** Finite independent byte storage. Every inherited method has an explicit implementation. */
    private static final class OwnedRam implements Add4Range262.Memory {
        private record Block(long base, byte[] bytes) { }
        private final List<Block> blocks = new ArrayList<>();
        private final List<byte[]> before = new ArrayList<>();
        private final List<Event> events = new ArrayList<>();
        private final int oldCount, added;
        private final OwnedReadFault retFault;
        private int budgetCalls, faultCalls, foreignCalls, allocatorCalls, freeCalls;
        private int unknownTailCalls, unsupportedPortCalls;

        OwnedRam(int oldCount, int added, OwnedReadFault retFault) {
            this.oldCount = oldCount;
            this.added = added;
            this.retFault = retFault;
            block(HEADER, 32, 11);
            block(DATA, 64, 29);
            block(SOURCE, 32, 47);
            block(0x8e00L, 0x240, 71);
            block(TABLE + added * 16L, 4, 97);
            seed(HEADER, 8, DATA);
            seed(HEADER + 8, 4, 8);
            seed(HEADER + 12, 4, oldCount);
            seed(DATA, 4, Integer.toUnsignedLong(A));
            seed(DATA + 4, 4, Integer.toUnsignedLong(B));
            seed(DATA + 8, 4, Integer.toUnsignedLong(C));
            if (oldCount == 4) seed(DATA + 12, 4, Integer.toUnsignedLong(D));
            seed(SOURCE, 4, Integer.toUnsignedLong(X));
            if (added == 2) seed(SOURCE + 4, 4, Integer.toUnsignedLong(Y));
            seed(TABLE + added * 16L, 4, added == 1 ? 0x422697aL : 0x422696dL);
            seed(S, 8, 0x123456789abcdef0L);
            for (Block block : blocks) before.add(block.bytes().clone());
        }

        private void block(long base, int size, int salt) {
            byte[] bytes = new byte[size];
            for (int i = 0; i < size; i++) bytes[i] = (byte)(1 + (i * 37 + salt) % 255);
            blocks.add(new Block(base, bytes));
        }

        private int blockIndex(long address, int width) {
            for (int i = 0; i < blocks.size(); i++) {
                Block block = blocks.get(i);
                long offset = address - block.base();
                if (offset >= 0 && offset <= block.bytes().length - width) return i;
            }
            throw new AssertionError("out-of-owned-RAM access " + Long.toHexString(address) + "/" + width);
        }

        private long peek(long address, int width) {
            Block block = blocks.get(blockIndex(address, width));
            int offset = (int)(address - block.base());
            long value = 0;
            for (int i = 0; i < width; i++) value |= (block.bytes()[offset + i] & 255L) << (i * 8);
            return value;
        }

        private void seed(long address, int width, long value) {
            Block block = blocks.get(blockIndex(address, width));
            int offset = (int)(address - block.base());
            for (int i = 0; i < width; i++) block.bytes()[offset + i] = (byte)(value >>> (i * 8));
        }

        private long read(String op, long address, int width) {
            long value = peek(address, width);
            events.add(e(op, address, value));
            return value;
        }

        private void write(String op, long address, int width, long value) {
            seed(address, width, value);
            events.add(e(op, address, width == 4 ? value & 0xffffffffL : value));
        }

        @Override public int readDword(long address) { return (int)read("RD", address, 4); }
        @Override public long readQword(long address) {
            if (retFault != null && address == R) {
                events.add(e("RQ_FAIL", address, peek(address, 8)));
                faultCalls++;
                throw retFault;
            }
            return read("RQ", address, 8);
        }
        @Override public int readUnsignedByte(long address) { return (int)read("RB", address, 1); }
        @Override public int readUnsignedWord(long address) { return (int)read("RW", address, 2); }
        @Override public void writeByte(long address, int value) { write("WB", address, 1, value & 255L); }
        @Override public void writeWord(long address, int value) { write("WW", address, 2, value & 65535L); }
        @Override public void writeDword(long address, int value) { write("WD", address, 4, Integer.toUnsignedLong(value)); }
        @Override public void writeQword(long address, long value) { write("WQ", address, 8, value); }

        private UnsupportedOperationException unvisited(String effect) {
            unsupportedPortCalls++;
            return new UnsupportedOperationException("unvisited public instruction effect " + effect);
        }
        @Override public int lockedXaddDword(long address, int addend) { throw unvisited("lockedXaddDword"); }
        @Override public Bits128 read128(long address) { throw unvisited("read128"); }
        @Override public void write128(long address, Bits128 value) { throw unvisited("write128"); }
        @Override public FullCopy437Api.Bits256 read256(long address) { throw unvisited("read256"); }
        @Override public void write256(long address, FullCopy437Api.Bits256 value) { throw unvisited("write256"); }
        @Override public void write128NonTemporal(long address, Bits128 value) { throw unvisited("write128NonTemporal"); }
        @Override public void write256NonTemporal(long address, FullCopy437Api.Bits256 value) { throw unvisited("write256NonTemporal"); }
        @Override public void sfence() { throw unvisited("sfence"); }
        @Override public void vzeroUpper() { throw unvisited("vzeroUpper"); }

        private void requireFullRamAfterLiteralWrites(List<Event> oracle) {
            List<byte[]> expected = new ArrayList<>();
            for (byte[] bytes : before) expected.add(bytes.clone());
            for (Event event : oracle) {
                int width = event.operation().equals("WD") ? 4 : event.operation().equals("WQ") ? 8 : 0;
                if (width == 0) continue;
                int index = blockIndex(event.address(), width);
                int offset = (int)(event.address() - blocks.get(index).base());
                for (int j = 0; j < width; j++) expected.get(index)[offset + j] = (byte)(event.bits() >>> (j * 8));
            }
            for (int i = 0; i < blocks.size(); i++)
                require(Arrays.equals(expected.get(i), blocks.get(i).bytes()), "complete RAM/canary region " + i);
        }
    }
}
