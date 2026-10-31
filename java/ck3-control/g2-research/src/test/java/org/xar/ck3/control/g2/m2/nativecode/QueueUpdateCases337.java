package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.QueueUpdateData337.*;

/** Independent model338 literal values; owner only canonicalized protocol fields. */
public final class QueueUpdateCases337 {
    private QueueUpdateCases337() { }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("1", 0x1100000000L, 0x3300000000L, 0x7ff000000000L, List.of(
                new Step(Op.R8, List.of(0x110000004eL, 0xffL), 0x0L)
            )),
            new Scene("2", 0x1100000000L, 0x3300000000L, 0x7ff000000000L, List.of(
                new Step(Op.R8, List.of(0x110000004eL, 0x0L), 0x0L),
                new Step(Op.CLASSIFY, List.of(0x1100000000L), 0x0L),
                new Step(Op.R32, List.of(0x1100000048L, 0xffffffffL), 0x0L)
            )),
            new Scene("3", 0x1100000000L, 0x3300000000L, 0x7ff000000000L, List.of(
                new Step(Op.R8, List.of(0x110000004eL, 0x0L), 0x0L),
                new Step(Op.CLASSIFY, List.of(0x1100000000L), 0x1L),
                new Step(Op.R32, List.of(0x1100000048L, 0x0L), 0x0L)
            )),
            new Scene("4", 0x1100000000L, 0x3300000000L, 0x7ff000000000L, List.of(
                new Step(Op.R8, List.of(0x110000004eL, 0x0L), 0x0L),
                new Step(Op.CLASSIFY, List.of(0x1100000000L), 0x2L),
                new Step(Op.R32, List.of(0x1100000048L, 0xffffffffL), 0x0L),
                new Step(Op.R32, List.of(0x3305c9ff68L, 0x1L), 0x0L),
                new Step(Op.PAUSE, List.of(), 0x0L),
                new Step(Op.R32, List.of(0x3305c9ff68L, 0x0L), 0x0L),
                new Step(Op.CAS, List.of(0x3305c9ff68L, 0x0L, 0x1L), 0x7L),
                new Step(Op.PAUSE, List.of(), 0x0L),
                new Step(Op.R32, List.of(0x3305c9ff68L, 0x0L), 0x0L),
                new Step(Op.CAS, List.of(0x3305c9ff68L, 0x0L, 0x1L), 0x0L),
                new Step(Op.W64, List.of(0x7ff000000000L, 0x1100000000L), 0x0L),
                new Step(Op.QUEUE, List.of(0x3305468a68L, 0x7ff000000000L), 0x0L),
                new Step(Op.W8, List.of(0x110000004eL, 0x1L), 0x0L),
                new Step(Op.W32, List.of(0x3305c9ff68L, 0x0L), 0x0L)
            ))
        );
    }
}
