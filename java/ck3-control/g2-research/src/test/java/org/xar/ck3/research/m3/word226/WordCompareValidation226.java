package org.xar.ck3.research.m3.word226;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Finite exact-word observations only; no native execution or full CPU state. */
public final class WordCompareValidation226 {
    private WordCompareValidation226() { }
    private static int groups, invocations, events, wordReads, externalWordEffects, resultAssertions, finalCells;
    private record WordStep(String kind, long address, int value, Runnable after) { }
    private static final class Words implements WordCompare226Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<WordStep> expected = new ArrayList<>();
        private int cursor;
        private void put(long a, int word) {
            if (word < 0 || word > 0xFFFF) throw new AssertionError("Invalid unsigned WORD fixture");
            bytes.put(a, (byte) word);
            bytes.put(a + 1, (byte) (word >>> 8));
        }
        private int raw(long a) {
            Byte low = bytes.get(a), high = bytes.get(a + 1);
            if (low == null || high == null) throw new AssertionError("Missing WORD bytes " + Long.toHexString(a));
            return Byte.toUnsignedInt(low) | (Byte.toUnsignedInt(high) << 8);
        }
        void seedWord(long a, int word) { put(a, word); }
        void wantWord(long a, int value) { wantWord(a, value, null); }
        void wantWord(long a, int value, Runnable after) {
            expected.add(new WordStep("R16", a, value, after));
        }
        void wantOpaqueWord(long a, int value) {
            expected.add(new WordStep("E16", a, value, null));
        }
        private WordStep take(String kind, long a) {
            if (cursor >= expected.size()) throw new AssertionError("Extra " + kind);
            WordStep s = expected.get(cursor++);
            if (!s.kind().equals(kind) || s.address() != a)
                throw new AssertionError("Trace " + (cursor - 1) + " expected " + s.kind() + " got " + kind);
            events++;
            if (kind.equals("R16")) wordReads++; else externalWordEffects++;
            return s;
        }
        void opaqueWord(long a, int value) {
            WordStep s = take("E16", a);
            if (s.value() != value) throw new AssertionError("External WORD effect value");
            put(a, value);
        }
        @Override public int readWord16(long address) {
            WordStep s = take("R16", address);
            int observed = raw(address);
            if (observed != s.value()) throw new AssertionError("Observed WORD");
            if (s.after() != null) s.after().run();
            return observed;
        }
        @Override public long readPointer(long a) { throw new AssertionError("Forbidden 64-bit read"); }
        @Override public int readInt32(long a) { throw new AssertionError("Forbidden 32-bit read"); }
        @Override public void writeInt32(long a, int v) { throw new AssertionError("Forbidden body write32"); }
        @Override public void writeInt64(long a, long v) { throw new AssertionError("Forbidden body write64"); }
        void checkWord(long a, int expectedWord) {
            if (raw(a) != expectedWord) throw new AssertionError("Final fixture WORD");
            finalCells++;
        }
        void finish() {
            if (cursor != expected.size()) throw new AssertionError("Unconsumed " + (expected.size() - cursor));
        }
    }

    private static void verify(Words memory, long left, long right, long count,
            int expectedDifference, long expectedRemaining, long expectedRightCursor,
            Integer expectedObservedRightWord) {
        invocations++;
        WordCompare226Api.Result result = new WordCompare4246A60().execute(memory, left, right, count);
        boolean expectedReads = expectedObservedRightWord != null;
        if (result.difference32() != expectedDifference || result.remainingR8() != expectedRemaining
                || result.finalRightCursor() != expectedRightCursor || result.finalReadsOccurred() != expectedReads)
            throw new AssertionError("Result DATA tuple");
        if (expectedReads && result.finalRightWord() != expectedObservedRightWord.intValue())
            throw new AssertionError("Fresh right WORD DATA");
        // With no final reads, finalRightWord is unavailable: never invoke its accessor here.
        resultAssertions++;
        memory.finish();
    }
private static void boundaryAndFullCount() {
    // Scene 1: count 0, no reads
    {
        Words m = new Words();
        long left = 0x1000L, right = 0x2000L;
        verify(m, left, right, 0L, 0, 0L, right, null);
        groups++;
    }

    // Scene 2: count 1, immediate final reads, negative difference
    {
        Words m = new Words();
        long left = 0x3000L, right = 0x4000L;
        int lw = 0x0001, rw = 0x8000;
        m.seedWord(left, lw);
        m.seedWord(right, rw);
        m.wantWord(left, lw);
        m.wantWord(right, rw);
        verify(m, left, right, 1L, lw - rw, 0L, right, rw);
        groups++;
    }

    // Scene 3: full 64-bit count with high bit set, left NUL stops loop, final reads
    {
        Words m = new Words();
        long left = 0x500000000000L, right = 0x600000000000L;
        long count = 0x8000000000000000L; // high bit set, low 32 zero
        int lw = 0x0000, rw = 0x1234;
        m.seedWord(left, lw);
        m.seedWord(right, rw);
        m.wantWord(left, lw); // loop first left read, NUL -> jump to final
        m.wantWord(left, lw); // final left read
        m.wantWord(right, rw); // final right read
        verify(m, left, right, count, lw - rw, count - 1L, right, rw);
        groups++;
    }
}

private static void progressionAndFreshFinalReads() {
    // Group 1: count=3. Entry test r8!=0 -> jne 7d -> sub r8 (3->2). Loop 1: read L0(1), R0(1) equal -> add ptrs -> sub r8 (2->1) -> jne loop. Loop 2: read L1(2), R1(2) equal -> add ptrs -> sub r8 (1->0) -> jne fails -> fall to 83. Final: read L2(3), R2(4). Diff 3-4=-1. Remaining 0. RightCursor 0x204. RightWord 4.
    Words m1 = new Words();
    m1.seedWord(0x100, 1); m1.seedWord(0x102, 2); m1.seedWord(0x104, 3);
    m1.seedWord(0x200, 1); m1.seedWord(0x202, 2); m1.seedWord(0x204, 4);

    m1.wantWord(0x100, 1); m1.wantWord(0x200, 1); // Loop 1
    m1.wantWord(0x102, 2); m1.wantWord(0x202, 2); // Loop 2
    m1.wantWord(0x104, 3); m1.wantWord(0x204, 4); // Final

    verify(m1, 0x100, 0x200, 3, -1, 0, 0x204, 4);
    groups++;

    // Group 2: count=5. Entry test r8!=0 -> jne 7d -> sub r8 (5->4). Loop 1: read L0(0). Test ax==0 -> je 83. Skip R0 read. Final: read L0(10) (changed by hook), R0(20). Diff 10-20=-10. Remaining 4. RightCursor 0x200. RightWord 20.
    Words m2 = new Words();
    m2.seedWord(0x100, 0);
    m2.seedWord(0x200, 20);

    m2.wantWord(0x100, 0, () -> m2.opaqueWord(0x100, 10)); // Initial left read, hook changes to 10
    m2.wantOpaqueWord(0x100, 10); // External effect

    m2.wantWord(0x100, 10); // Final left fresh
    m2.wantWord(0x200, 20); // Final right fresh

    verify(m2, 0x100, 0x200, 5, -10, 4, 0x200, 20);
    groups++;

    // Group 3: count=4. Entry test r8!=0 -> jne 7d -> sub r8 (4->3). Loop 1: read L0(1). Test ax!=0. Read R0(2). Cmp 1!=2 -> jne 83. Hook changes L0 to 0xFFFF, R0 to 0x8000. Final: read L0(0xFFFF), R0(0x8000). Diff 0xFFFF - 0x8000 = 0x7FFF (positive? No, 65535 - 32768 = 32767. Need negative diff. Let's swap: L0=0x8000, R0=0xFFFF. Diff 0x8000 - 0xFFFF = -32767. Or L0=0, R0=1? No, L0 must be nonzero to enter loop. Let's use L0=0x8000, R0=0xFFFF. Initial L0=1, R0=2. Hook changes L0 to 0x8000, R0 to 0xFFFF. Final diff 0x8000 - 0xFFFF = -32767. Remaining 3. RightCursor 0x200. RightWord 0xFFFF.
    Words m3 = new Words();
    m3.seedWord(0x100, 1);
    m3.seedWord(0x200, 2);

    m3.wantWord(0x100, 1); // Initial left
    m3.wantWord(0x200, 2, () -> { m3.opaqueWord(0x100, 0x8000); m3.opaqueWord(0x200, 0xFFFF); }); // Initial right, hook changes both
    m3.wantOpaqueWord(0x100, 0x8000); // External effect 1
    m3.wantOpaqueWord(0x200, 0xFFFF); // External effect 2

    m3.wantWord(0x100, 0x8000); // Final left fresh
    m3.wantWord(0x200, 0xFFFF); // Final right fresh

    verify(m3, 0x100, 0x200, 4, -32767, 3, 0x200, 0xFFFF);
    groups++;
}

    public static void main(String[] args) {
        boundaryAndFullCount();
        progressionAndFreshFinalReads();
        if (groups != 6 || invocations != 6 || resultAssertions != 6)
            throw new AssertionError("Finite scene count");
        System.out.println("groups=" + groups + " events=" + events + " wordReads=" + wordReads
                + " externalWordEffects=" + externalWordEffects + " resultTuples=" + resultAssertions
                + " finalCells=" + finalCells + " invocations=" + invocations);
    }

}
