package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

/** Literal normal-source witnesses; no native/type/loaded-world identity. */
public final class LoadHierarchyNonzero173Test {
    private static final long B = 0x100000000L;
    private static final long COL = 0x7000L;
    private static final long COMPLETE = 0x8000L;
    private static final long TARGET = B + 0x400L;
    private static final long SOURCE = B + 0x500L;
    private static final long DT = B + 0x1000L;
    private static final long DS = B - 0x1000L;
    private static final long DT2 = B + 0x2000L;
    private static final long DS2 = B - 0x2000L;
    private record Read(int width, long address, long value) { }

    private static final class Fixture implements LoadHierarchySearch173.Memory {
        private final ArrayDeque<Read> reads = new ArrayDeque<>();
        private Fixture(int count) {
            d(COL + 0x10L, 0x100).d(B + 0x10CL, 0x200).d(B + 0x108L, count);
        }
        private Fixture d(long address, int value) { reads.add(new Read(32, address, value)); return this; }
        private Fixture b(long address, int value) { reads.add(new Read(8, address, value)); return this; }
        private Fixture q(long address, long value) { reads.add(new Read(64, address, value)); return this; }
        private long read(int width, long address) {
            Read r = reads.remove();
            assertEquals(r.width(), width, "read width");
            assertEquals(r.address(), address, "read address");
            return r.value();
        }
        @Override public long readPointer(long address) { return read(64, address); }
        @Override public int readInt32(long address) { return (int) read(32, address); }
        @Override public int readUnsigned8(long address) { return (int) read(8, address); }
        @Override public void writeInt32(long address, int value) { throw new AssertionError("write32"); }
        @Override public void writeInt64(long address, long value) { throw new AssertionError("write64"); }
        private void done() { assertEquals(0, reads.size(), "unconsumed literal reads"); }
    }

    private static LoadRuntime4260e74.SearchCall call() {
        return new LoadRuntime4260e74.SearchCall(COMPLETE, COL, SOURCE, -7L, 0xBADL,
                OptionalLong.of(TARGET), OptionalLong.of(B));
    }

    private static Fixture targetThenSource968() {
        return new Fixture(2)
                .d(B + 0x200L, 0x1000).d(DT, 0x400).d(DT + 4L, 1)
                .d(DT, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x204L, -0x1000).d(DS, 0x500)
                .d(DS + 0xCL, -1).d(DS + 8L, -7);
    }

    private static Fixture sourceThenTarget968() {
        return new Fixture(2)
                .d(B + 0x200L, -0x1000).d(DS, 0x500)
                .b(SOURCE + 0x10L, 'S').b(TARGET + 0x10L, 'T')
                .d(DS, 0x500).d(DS + 0xCL, -1).d(DS + 8L, -7)
                .d(B + 0x204L, 0x1000).d(DT, 0x400);
    }

    @Test public void find968NonzeroSuccessAndFlags40UseExactReads() {
        Fixture success = targetThenSource968().b(DT + 0x14L, 0).b(DS + 0x14L, 0);
        assertEquals(DT, LoadHierarchySearch173.find968(call(), success));
        success.done();
        Fixture nested = targetThenSource968().b(DT + 0x14L, 0x40)
                .d(DT + 0x18L, 0x600).d(B + 0x60CL, 0x700)
                .d(B + 0x704L, 0x1200).b(B + 0x1214L, 1);
        assertEquals(0L, LoadHierarchySearch173.find968(call(), nested));
        nested.done();
    }

    @Test public void find968SourceFirstTestsNewTarget03AndRetainedSource01() {
        Fixture success = sourceThenTarget968().b(DT + 0x14L, 0).b(DS + 0x14L, 0);
        assertEquals(DT, LoadHierarchySearch173.find968(call(), success));
        success.done();
        Fixture badTarget = sourceThenTarget968().b(DT + 0x14L, 3);
        assertEquals(0L, LoadHierarchySearch173.find968(call(), badTarget));
        badTarget.done();
        Fixture badSource = sourceThenTarget968().b(DT + 0x14L, 0).b(DS + 0x14L, 1);
        assertEquals(0L, LoadHierarchySearch173.find968(call(), badSource));
        badSource.done();
    }

    private static Fixture targetThenSourceC28(int flags) {
        return new Fixture(2)
                .d(B + 0x200L, 0x1000).d(DT, 0x400).b(DT + 0x14L, flags).d(DT + 4L, 1)
                .d(DT, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x204L, -0x1000).d(DS, 0x500)
                .d(DS + 0xCL, -1).d(DS + 8L, -7);
    }

    @Test public void findC28FinalRsiAndNestedDwordThenFreshByteFlags() {
        Fixture selected = targetThenSourceC28(0).b(DT + 0x14L, 0).b(DS + 0x14L, 0)
                .d(DT + 0xCL, -1).d(DT + 8L, -11);
        assertEquals(DT, LoadHierarchySearch173.findC28(call(), selected));
        selected.done();
        Fixture nested = targetThenSourceC28(0x40).b(DT + 0x14L, 0x40)
                .d(DT + 0x18L, 0x600).d(B + 0x60CL, 0x700)
                .d(B + 0x704L, 0x1200).d(B + 0x1214L, 4).b(B + 0x1214L, 0);
        assertEquals(0L, LoadHierarchySearch173.findC28(call(), nested));
        nested.done();
    }

    @Test public void findC28CleanTargetSurvivesLaterDirtyTarget() {
        Fixture f = new Fixture(3)
                .d(B + 0x200L, 0x1000).d(DT, 0x400).b(DT + 0x14L, 0).d(DT + 4L, 0)
                .d(DT, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x204L, -0x1000).d(DS, 0x500)
                .b(SOURCE + 0x10L, 'S').b(TARGET + 0x10L, 'T')
                .d(DS, 0x500).d(DS + 0xCL, -1).d(DS + 8L, -7).b(DS + 0x14L, 0)
                .d(B + 0x208L, 0x2000).d(DT2, 0x400).b(DT2 + 0x14L, 2).d(DT2 + 4L, 0)
                .d(DT2, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S');
        assertEquals(DT, LoadHierarchySearch173.findC28(call(), f));
        f.done();
    }

    @Test public void findC28DifferentTargetOffsetsAreAmbiguousBeforeFinalSelection() {
        Fixture f = new Fixture(4)
                .d(B + 0x200L, 0x1000).d(DT, 0x400).b(DT + 0x14L, 0).d(DT + 4L, 1)
                .d(DT, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x204L, -0x1000).d(DS, 0x500).d(DS + 0xCL, -1).d(DS + 8L, -7)
                .b(DT + 0x14L, 0).b(DS + 0x14L, 0).d(DT + 0xCL, -1).d(DT + 8L, -11)
                .d(B + 0x208L, 0x2000).d(DT2, 0x400).b(DT2 + 0x14L, 0).d(DT2 + 4L, 1)
                .d(DT2, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x20CL, -0x2000).d(DS2, 0x500).d(DS2 + 0xCL, -1).d(DS2 + 8L, -7)
                .b(DT2 + 0x14L, 0).d(DT2 + 0xCL, -1).d(DT2 + 8L, 9);
        assertEquals(0L, LoadHierarchySearch173.findC28(call(), f));
        f.done();
    }
}
