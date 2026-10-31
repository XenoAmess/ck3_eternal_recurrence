package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInitData291.*;

/** Owner ASM literals after target source read: nonblind, not target-generated. */
public final class EmbeddedInitCases291 {
    private EmbeddedInitCases291() { }
    public static List<Scene> scenes() {
        return List.of(new Scene("complete130-constructor", 0x1000000000L, 0x2000000000L, List.of(
            new Step(Op.W64, List.of(0x1000000000L, 0x0L)),
            new Step(Op.W32, List.of(0x1000000008L, 0x0L)),
            new Step(Op.W64, List.of(0x1000000010L, 0x1000000018L)),
            new Step(Op.W64, List.of(0x1000000018L, 0x200448d2a0L)),
            new Step(Op.W64, List.of(0x10000000e0L, 0x20054de2e0L)),
            new Step(Op.R64, List.of(0x1000000000L, 0x0L)),
            new Step(Op.W32, List.of(0x100000000cL, 0x0L)),
            new Step(Op.R64, List.of(0x1000000010L, 0x1000000018L)),
            new Step(Op.R64, List.of(0x1000000018L, 0x200448d2a0L)),
            new Step(Op.R64, List.of(0x200448d2b0L, 0x3000000010L)),
            new Step(Op.CALL10, List.of(0x3000000010L, 0x1000000018L, 0x0L, 0x8L)),
            new Step(Op.R64, List.of(0x1000000018L, 0x200448d2a0L)),
            new Step(Op.W64, List.of(0x1000000000L, 0x0L)),
            new Step(Op.W64, List.of(0x1000000008L, 0x0L)),
            new Step(Op.R64, List.of(0x200448d2c0L, 0x3000000020L)),
            new Step(Op.CALL20, List.of(0x3000000020L, 0x1000000018L, 0x1000000000L, 0x1000000008L))
        ), 0x1000000000L));
    }
}
