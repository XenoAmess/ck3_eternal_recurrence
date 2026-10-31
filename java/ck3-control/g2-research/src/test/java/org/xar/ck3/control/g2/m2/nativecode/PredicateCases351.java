package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PredicateData351.*;

/** Owner NONBLIND original81 literals after modeltarget read, no target-generated expected. */
public final class PredicateCases351 {
    private PredicateCases351() { }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("empty-second-vector", 0x1100000000L, List.of(
                new Step(Op.R32, List.of(0x110000001cL, 0x0L), 0L),
                new Step(Op.R64, List.of(0x1100000030L, 0x5500000000L), 0L),
                new Step(Op.R32, List.of(0x110000003cL, 0x0L), 0L)
            ), 0),
            new Scene("fresh-count1-to2-last-tag", 0x1100000000L, List.of(
                new Step(Op.R32, List.of(0x110000001cL, 0x1L), 0L),
                new Step(Op.R32, List.of(0x110000001cL, 0x2L), 0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x4400000000L), 0L),
                new Step(Op.R32, List.of(0x440000002cL, 0x0L), 0L)
            ), 1),
            new Scene("second-object-byte-flag", 0x1100000000L, List.of(
                new Step(Op.R32, List.of(0x110000001cL, 0x1L), 0L),
                new Step(Op.R32, List.of(0x110000001cL, 0x1L), 0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x4400000000L), 0L),
                new Step(Op.R32, List.of(0x440000000cL, 0xffffffffL), 0L),
                new Step(Op.R64, List.of(0x1100000030L, 0x5500000000L), 0L),
                new Step(Op.R32, List.of(0x110000003cL, 0x2L), 0L),
                new Step(Op.R8, List.of(0x5500000044L, 0x0L), 0L),
                new Step(Op.R8, List.of(0x550000008cL, 0xffL), 0L)
            ), 1),
            new Scene("flag-at-absolute-null-stillALzero", 0x1100000000L, List.of(
                new Step(Op.R32, List.of(0x110000001cL, 0x0L), 0L),
                new Step(Op.R64, List.of(0x1100000030L, 0x0L), 0L),
                new Step(Op.R32, List.of(0x110000003cL, 0x1L), 0L),
                new Step(Op.R8, List.of(0x44L, 0x1L), 0L)
            ), 0)
        );
    }
}
