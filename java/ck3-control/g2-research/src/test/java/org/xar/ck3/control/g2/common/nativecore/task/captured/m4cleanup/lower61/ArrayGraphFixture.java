package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61;

import java.util.List;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.B374ReleaseGraph;

/** Literal finite inputs only, using existing strict memory without executing target cores. */
final class ArrayGraphFixture extends Lower61Fixture implements B374ReleaseGraph.SharedMemory {
    static final long COMMON = 0x610000000L;
    static final long FIRST = 0x110000001L;
    static final long SECOND = 0x110000002L;
    private record ArrayInput(long offset, int count) { }

    static ArrayGraphFixture create() {
        var inputs = FourGraphSeed.create();
        var f = new ArrayGraphFixture();
        f.qwords.putAll(inputs.qwords);
        f.dwords.putAll(inputs.dwords);
        f.firstEax = Integer.MIN_VALUE;
        f.qwords.put(FourGraphSeed.OBJECT + 0xF8L, 0L);
        for (var array : List.of(new ArrayInput(0L, 7), new ArrayInput(0x38L, 7),
                new ArrayInput(0x70L, 12), new ArrayInput(0xD0L, 12), new ArrayInput(0x130L, 2),
                new ArrayInput(0x160L, 7), new ArrayInput(0x198L, 7), new ArrayInput(0x1D0L, 12),
                new ArrayInput(0x230L, 12), new ArrayInput(0x290L, 2))) {
            for (int i = 0; i < array.count(); i++) {
                f.qwords.put(FourGraphSeed.T54 + array.offset() + i * 8L, COMMON);
            }
        }
        f.qwords.put(FourGraphSeed.T54, FIRST);
        f.qwords.put(FourGraphSeed.T54 + 8L, SECOND);
        f.qwords.put(FourGraphSeed.T54 + 0x140L, 0x210000001L);
        f.qwords.put(FourGraphSeed.T54 + 0x148L, 0x210000002L);
        f.qwords.put(FourGraphSeed.T54 + 0x150L, 0x210000003L);
        f.qwords.put(FourGraphSeed.T54 + 0x2A0L, 0x210000004L);
        f.qwords.put(FourGraphSeed.T54 + 0x2A8L, 0x210000005L);
        f.qwords.put(FourGraphSeed.T54 + 0x2B0L, 0x210000006L);
        f.qwords.put(FourGraphSeed.T54 + 0x2B8L, 0x210000007L);
        return f;
    }
}
