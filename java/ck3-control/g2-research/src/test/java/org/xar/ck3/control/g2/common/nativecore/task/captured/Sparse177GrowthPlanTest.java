package org.xar.ck3.control.g2.common.nativecore.task.captured;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;

import org.junit.jupiter.api.Test;

public final class Sparse177GrowthPlanTest {
    @Test
    public void fixedLiteralBoundariesPreserveSignedEntryAndDistanceThirtyTwo() {
        assertEquals(new SparseIntCells177Growth.NormalPlan(8, 5),
                SparseIntCells177Growth.plan(Integer.MIN_VALUE));
        assertEquals(new SparseIntCells177Growth.NormalPlan(8, 5),
                SparseIntCells177Growth.plan(-1));
        assertEquals(new SparseIntCells177Growth.NormalPlan(8, 5),
                SparseIntCells177Growth.plan(0));
        assertEquals(new SparseIntCells177Growth.NormalPlan(8, 5),
                SparseIntCells177Growth.plan(1));
        assertEquals(new SparseIntCells177Growth.NormalPlan(8, 5),
                SparseIntCells177Growth.plan(3));
        assertEquals(new SparseIntCells177Growth.NormalPlan(16, 6),
                SparseIntCells177Growth.plan(4));
        assertEquals(new SparseIntCells177Growth.NormalPlan(32, 7),
                SparseIntCells177Growth.plan(8));
        assertEquals(new SparseIntCells177Growth.NormalPlan(536870912, 31),
                SparseIntCells177Growth.plan(0x0FFFFFFF));
        assertEquals(new SparseIntCells177Growth.NormalPlan(1073741824, 32),
                SparseIntCells177Growth.plan(0x10000000));
        assertEquals(new SparseIntCells177Growth.NormalPlan(1073741824, 32),
                SparseIntCells177Growth.plan(0x10000001));
        assertEquals(new SparseIntCells177Growth.NormalPlan(1073741824, 32),
                SparseIntCells177Growth.plan(0x1FFFFFFF));
        assertSame(SparseIntCells177Growth.ErrorPlan.INSTANCE,
                SparseIntCells177Growth.plan(0x20000000));
        assertSame(SparseIntCells177Growth.ErrorPlan.INSTANCE,
                SparseIntCells177Growth.plan(0x20000001));
        assertSame(SparseIntCells177Growth.ErrorPlan.INSTANCE,
                SparseIntCells177Growth.plan(Integer.MAX_VALUE));
    }
}
